## 1. Seleção persistível

- [x] 1.1 Introduzir em `Python/persistencia_dia.py` uma estrutura que reúna o documento agregado e os caminhos exatos dos relatórios e atividades selecionados, preservando a interface necessária de `montar_retrato`, e verificar em testes que documento e caminhos correspondem à mesma data.
- [x] 1.2 Validar que todos os caminhos selecionados pertencem aos diretórios locais permitidos e verificar que arquivos de outra data, atividades em andamento, pausas transitórias e arquivos criados depois da seleção não entram na limpeza.

## 2. Limpeza retomável

- [x] 2.1 Implementar manifesto atômico de limpeza pendente por data, com caminhos relativos e validação contra caminhos absolutos, travessia e destinos fora de `Relatórios` e `Tarefas/Concluidas`, cobrindo leitura e escrita segura em testes.
- [x] 2.2 Implementar a remoção idempotente dos caminhos registrados e a exclusão do manifesto somente após todos estarem ausentes, verificando sucesso completo, arquivos já ausentes e erro com lista de remanescentes.
- [x] 2.3 Fazer `persistir dia` detectar primeiro um manifesto da data e retomar somente a limpeza, sem acessar o MongoDB nem reconstruir um retrato parcial, e verificar esse comportamento com mocks da collection e arquivos parcialmente removidos.

## 3. Integração com a persistência

- [x] 3.1 Criar o manifesto e iniciar a limpeza somente depois de o upsert terminar com sucesso, verificando que falhas de validação, configuração, índice, conexão ou escrita preservam byte a byte todos os arquivos e não deixam manifesto.
- [x] 3.2 Aplicar a limpeza aos caminhos automático e manual, verificando que um envio bem-sucedido remove somente relatórios e atividades concluídas da data e mantém todos os diretórios e arquivos fora da seleção.
- [x] 3.3 Cobrir interrupções entre confirmação, criação do manifesto e remoções, verificando que nenhuma repetição substitui no MongoDB um retrato completo por dados locais parciais.

## 4. Finalização e CLI

- [x] 4.1 Alterar `finalizar_dia` para retornar a data depois de persistência e limpeza bem-sucedidas, mantendo o caminho retornado por `iniciar_dia`, e verificar as saídas `YYYY-MM-DD` e os códigos da CLI.
- [x] 4.2 Propagar falhas de limpeza como erros acionáveis distintos de falhas remotas, preservando a finalização e sem expor credenciais, e verificar mensagens e estado local nos testes de gerenciamento do dia.

## 5. Verificação integrada

- [x] 5.1 Executar toda a suíte Python e corrigir regressões, verificando persistência idempotente, recuperação de falhas, início do dia seguinte pelo MongoDB e ciclos de tarefas e relatórios.
- [x] 5.2 Executar a validação estrita da mudança OpenSpec e `git diff --check`, confirmando coerência dos artefatos e ausência de problemas de formatação.
