## Context

Ver `proposal.md` para a motivação. Hoje `montar_retrato` devolve somente o documento agregado, `persistir_dia` confirma o upsert e retorna a data, e `finalizar_dia` retorna o caminho do relatório que continuará existindo. A spec vigente também exige preservação byte a byte após sucesso. A limpeza precisa manter a fronteira de segurança já existente: nenhuma mutação local antes da confirmação remota.

Há um risco adicional em falhas parciais. Se alguns arquivos forem removidos depois do upsert e uma repetição reconstruir o retrato apenas com os arquivos restantes, o upsert por substituição apagará do MongoDB dados que já haviam sido persistidos. O desenho precisa distinguir “envio pendente” de “limpeza pendente”.

## Goals / Non-Goals

**Goals:**

- Vincular documento e caminhos em uma única seleção validada.
- Limpar somente após confirmação remota e permitir retomada segura de falhas locais.
- Manter a mesma semântica nos caminhos automático e manual.
- Produzir erros que distingam falha remota de falha de limpeza.

**Non-Goals:**

- Limpar arquivos de outras datas ou diretórios transitórios.
- Excluir os diretórios `Relatórios`, `Tarefas/Concluidas`, `Tarefas/Tarefa em andamento` ou `Tarefas/Pausas`.
- Oferecer restauração do MongoDB para YAML nesta mudança.
- Reter uma cópia local permanente depois da persistência.

## Decisions

### Retornar um retrato acompanhado dos caminhos selecionados

A montagem produzirá um valor estruturado contendo o documento e uma coleção imutável de caminhos de relatórios e atividades. A persistência usará o documento no upsert e exatamente os mesmos caminhos na limpeza. Caminhos serão resolvidos dentro dos diretórios permitidos e não serão redescobertos depois da operação remota.

Alternativa considerada: percorrer novamente os diretórios após o upsert é mais simples, mas cria uma janela em que arquivos novos ou alterados podem ser apagados sem terem sido persistidos.

### Registrar uma limpeza pendente antes de remover o primeiro arquivo

Depois de o upsert ser confirmado e antes da primeira remoção, o sistema gravará atomicamente um manifesto local por data contendo somente caminhos relativos validados da seleção. Se o manifesto não puder ser gravado, nenhum arquivo será removido e a operação falhará como limpeza pendente. Cada remoção será tolerante a arquivo já ausente; o manifesto será apagado somente quando todos os caminhos estiverem ausentes.

Uma execução posterior de `persistir dia` para essa data verificará primeiro o manifesto. Quando ele existir, retomará a limpeza sem montar outro retrato nem executar novo upsert. Isso impede que um conjunto local parcial substitua o documento completo no MongoDB.

O manifesto ficará em uma área interna dedicada na raiz do projeto, fora de `Relatórios` e `Tarefas`, e usará caminhos relativos. A leitura rejeitará caminhos absolutos, travessia com `..` ou destinos fora dos diretórios permitidos.

Alternativas consideradas:

- Excluir diretamente sem manifesto não permite retomada segura após falha parcial ou encerramento abrupto.
- Mover tudo para uma lixeira temporária antes de excluir exige rollback de múltiplos movimentos e ainda precisa de estado para recuperar interrupções.
- Manter os arquivos para sempre preserva a implementação atual, mas contradiz o objetivo confirmado.

### Tratar confirmação remota e limpeza como fases distintas

Erros anteriores à confirmação do upsert preservam integralmente os arquivos e não criam manifesto. Depois da confirmação, falhas são classificadas como limpeza local: o documento remoto não é revertido, o cliente é fechado normalmente e a mensagem lista os caminhos ainda existentes sem expor configuração do MongoDB.

### Retornar a data em comandos de ciclo concluído

Como o caminho do relatório deixa de existir após sucesso, `finalizar dia` passará a retornar a data do ciclo, alinhada ao retorno já usado por `persistir dia`. A CLI imprimirá `YYYY-MM-DD`. O retorno de `iniciar dia` continuará sendo o caminho do arquivo criado.

## Risks / Trade-offs

- [O manifesto adiciona estado operacional local] → usar formato mínimo, escrita atômica, validação estrita de caminhos e remoção assim que a limpeza concluir.
- [Queda do processo entre upsert e criação do manifesto deixa arquivos intactos] → repetir a persistência é seguro porque o retrato ainda está completo e o upsert é idempotente.
- [Queda depois da criação do manifesto] → a próxima execução detecta o manifesto e retoma apenas a limpeza.
- [Arquivo selecionado muda depois da montagem] → a limpeza ainda remove o caminho selecionado; reduzir a janela mantendo o fluxo síncrono e testar que arquivos novos, com outros caminhos, são preservados.
- [Mudança da saída da CLI pode afetar scripts] → documentar como alteração incompatível e testar explicitamente o novo valor `YYYY-MM-DD`.

## Migration Plan

1. Introduzir a seleção estruturada e manter os testes atuais de montagem do documento.
2. Implementar e testar o manifesto seguro e a rotina de limpeza retomável.
3. Integrar limpeza após confirmação no fluxo manual e automático.
4. Atualizar o retorno da finalização e os testes de CLI.
5. Executar a suíte completa e validação OpenSpec.

O rollback do código volta a preservar arquivos. Manifestos pendentes criados pela versão nova deverão ser concluídos antes do rollback ou removidos manualmente somente após confirmar que o documento correspondente existe no MongoDB.
