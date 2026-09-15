## Context

O projeto já possui `RegistroDiario`, serialização YAML atômica, fuso e relógio injetáveis no gerenciador de tarefas, detecção validada de atividade ativa e uma fábrica síncrona de `MongoClient`. O diretório `Relatórios` existe apenas com `.gitkeep`, e a CLI ainda não possui comandos de dia. Consulte `proposal.md` para a motivação e os dois deltas em `specs/` para os contratos.

O MongoDB ainda não possui a database nem a collection da aplicação. Selecioná-las e consultar uma collection inexistente não cria estruturas; a primeira escrita pertence à mudança futura de persistência.

## Goals / Non-Goals

**Goals:**

- Manter o relatório como YAML editável durante todo o dia.
- Isolar consulta remota, regras de ciclo de vida e parsing da CLI.
- Fazer toda validação antes de modificar o relatório na finalização.
- Permitir testes determinísticos com relógio, fuso e cliente MongoDB simulados.
- Deixar a validação preparada para relatórios adicionais sem implementá-los agora.

**Non-Goals:**

- Inserir, atualizar ou remover documentos no MongoDB.
- Criar database, collection, índice único ou validador remoto.
- Gerenciar outros tipos de relatório.
- Alterar o ciclo de vida de tarefas, sessões ou pausas.

## Decisions

### Criar um serviço `GerenciadorDia`

Um novo módulo `Python/gerenciamento_dia.py` coordenará relógio/fuso, caminhos, serialização, validação, verificação de atividade e consulta ao histórico. A CLI apenas fará parsing e despacho. O serviço receberá suas dependências por injeção para que testes nunca usem a rede ou o relógio real.

Alternativa considerada: incorporar o fluxo ao `GerenciadorTarefas`. Rejeitada porque o relatório tem ciclo e dependência remota próprios; compartilhará utilitários sem tornar os dois domínios uma única classe.

### Um arquivo determinístico por data

O relatório atual ficará em `Relatórios/RD-YYYY-MM-DD.yaml`. O prefixo `RD-` identifica explicitamente o tipo de relatório, enquanto a data no fuso configurado elimina descoberta ambígua e permite coexistência dos relatórios de vários dias. Iniciar um dia cujo destino exista falha antes da consulta remota, preservando o arquivo.

Alternativa considerada: um arquivo transitório fixo e movimentação na finalização. Rejeitada porque `design.md` não prevê um diretório separado de concluídos para relatórios e a data já oferece identidade estável.

### Configuração separada para a database

`Python/configuracao_mongodb.py` ganhará leitura estrita de `MONGODB_DATABASE`, reutilizando a mesma política de `.env`: chave única, não vazia e sem exposição de segredos. `.env.example` usará `diario_estudos`; a collection `registros_diarios` será uma constante de domínio, não uma variável de ambiente.

Alternativa considerada: embutir o banco na URI. Rejeitada porque a URI atual serve à conexão/diagnóstico e separar o nome torna o destino explícito e testável.

### Consulta limitada a dois documentos

A consulta filtrará `data` pelo texto ISO da data anterior e projetará somente `fui_dormir`, limitando o resultado a dois documentos. Zero resultados significa histórico ausente; um resultado é validado; dois indicam violação da unicidade e falham. Esse limite evita escolher uma duplicata arbitrária enquanto o índice ainda não existe.

`data` é a identidade única do relatório diário no MongoDB. A mudança futura `persistir-dia-no-mongodb` criará um índice único em `registros_diarios.data` antes de gravar documentos. Esta mudança permanece somente de leitura e, portanto, não cria o índice nem qualquer estrutura remota.

Os formatos remotos serão `data: YYYY-MM-DD` e `fui_dormir: HH:MM:SS`, pois BSON não possui tipos nativos equivalentes a `date` e `time` do Python. O horário será convertido estritamente com ISO 8601 antes de entrar no modelo.

Alternativa considerada: `find_one`. Rejeitada porque esconderia duplicidade e tornaria o valor escolhido dependente da ordem do servidor.

### Ausência de estrutura não é erro; falha de consulta é

Uma database ou collection ainda inexistente produz zero documentos e, portanto, `dormi_dia_anterior=None`. Exceções de PyMongo serão convertidas em erro de domínio sanitizado, o cliente será fechado em `finally` e nenhum YAML será escrito. A URI nunca será incluída nas mensagens.

Alternativa considerada: continuar com `null` também em falhas de rede. Rejeitada porque confundiria ausência legítima de histórico com indisponibilidade e poderia criar relatório a partir de estado desconhecido.

### Validação orientada por metadados

Na finalização, `dataclasses.fields()` identificará todos os campos com `metadata["opcional"] == False`; cada um deverá estar diferente de `None`. Isso aplica a regra do esquema sem duplicar uma lista de campos no serviço e se adapta à regeneração da classe. Nesta mudança, o conjunto de relatórios necessários contém apenas o `RegistroDiario` atual.

A ordem será: carregar/validar classe e data, detectar dia já finalizado, validar campos obrigatórios, validar ausência de atividade, obter hora atual, atribuir `fui_dormir` e salvar atomicamente. Assim, qualquer erro anterior à gravação preserva os bytes; a serialização existente protege falhas durante a substituição.

Alternativa considerada: usar verdade/falsidade para validar preenchimento. Rejeitada porque `False` é valor válido para `folga`; somente `None` representa ausência.

### Expor uma consulta pública de atividade ativa

O gerenciador de tarefas disponibilizará uma operação de leitura que reutiliza sua descoberta e validação atuais. `GerenciadorDia` a chamará sem acessar métodos privados nem alterar arquivos. Qualquer atividade válida, YAML inválido ou multiplicidade impedirá o fechamento.

Alternativa considerada: duplicar a descoberta no novo serviço. Rejeitada porque produziria duas interpretações do mesmo estado operacional.

### Rejeitar segunda finalização

`fui_dormir` preenchido será o marcador local de dia finalizado. Uma nova execução falhará sem substituir o valor, evitando que um comando repetido altere o histórico do sono.

## Risks / Trade-offs

- [O contrato remoto precede a implementação de persistência] → Registrar formatos ISO nas specs e reutilizá-los obrigatoriamente na mudança futura.
- [O índice único ainda não existe durante esta mudança] → Detectar até dois resultados e falhar; `persistir-dia-no-mongodb` criará o índice único em `registros_diarios.data` antes da primeira gravação.
- [Metadados podem mudar após regeneração das classes] → Testar a seleção dos campos obrigatórios contra a classe gerada real.
- [A finalização perto da meia-noite pode mudar de data entre validação e gravação] → Capturar um único instante no início de cada comando e derivar dele data e hora.
- [A consulta remota torna `iniciar dia` dependente de rede] → Falhar rapidamente com o timeout já configurado e nunca produzir estado parcial.

## Migration Plan

1. Documentar `MONGODB_DATABASE=diario_estudos` e implementar sua leitura validada.
2. Adicionar a consulta somente de leitura e os testes com cliente simulado.
3. Implementar `GerenciadorDia` e os testes do ciclo local e de preservação em falhas.
4. Integrar os comandos à CLI e executar toda a suíte sem rede.
5. Verificar manualmente `iniciar dia` contra o cluster vazio, confirmando `dormi_dia_anterior: null` e nenhuma criação remota.

Rollback: remover os comandos e o novo serviço e retirar `MONGODB_DATABASE` da configuração documentada. Relatórios YAML já criados permanecem arquivos válidos e não exigem migração.
