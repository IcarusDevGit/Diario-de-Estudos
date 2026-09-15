## Why

O ciclo diário hoje termina apenas em arquivos locais, impedindo consolidação e consulta histórica de todos os relatórios e atividades relacionados ao dia. Persistir um retrato completo e idempotente no MongoDB cria essa base sem abandonar os YAMLs como fonte local de preenchimento e recuperação.

## What Changes

- Introduzir um documento agregado por ciclo na collection `dias`, identificado por um índice único em `data`, contendo `versao`, todos os relatórios locais daquela data e todas as tarefas ou sessões associadas.
- Persistir automaticamente o retrato depois que `finalizar dia` salvar o relatório local, mantendo o YAML finalizado quando houver falha remota.
- Adicionar `persistir dia [--data YYYY-MM-DD]` para repetir com segurança um envio por upsert; sem data, usar o ciclo finalizado local mais recente.
- Tratar o dia como ciclo lógico: `finalizar dia` encontra o único `RegistroDiario` aberto mesmo após a meia-noite, e `iniciar dia` recusa criar outro enquanto houver ciclo aberto.
- **BREAKING**: exigir um ciclo diário aberto para iniciar tarefas ou sessões e associar automaticamente cada atividade ao campo `dia` do ciclo; pausas continuam incorporadas à atividade.
- Incluir todos os modelos válidos presentes em `Relatórios` cuja `data` corresponda ao ciclo, permitindo que novos tipos de relatório sejam incorporados futuramente sem mudar o formato agregado.
- Manter os arquivos locais após a persistência e oferecer migração explícita para atividades legadas sem `dia` quando a associação for inequívoca.
- Atualizar a consulta de sono anterior para ler o `RegistroDiario` dentro do documento agregado em `dias`.

## Capabilities

### New Capabilities

- `persistencia-dia-mongodb`: montagem, validação e upsert idempotente do retrato completo do ciclo diário, incluindo recuperação de falhas.

### Modified Capabilities

- `esquemas-json`: acrescentar a referência opcional de compatibilidade `dia` à classe base `Tarefa`.
- `gerenciamento-tarefas-pausas`: exigir ciclo aberto ao iniciar atividades e associá-las automaticamente ao dia lógico.
- `gerenciamento-dia`: localizar ciclos pelo estado aberto/finalizado, persistir automaticamente ao finalizar e consultar o novo documento agregado.

## Impact

Afeta os esquemas e classes geradas, gerenciamento de tarefas e do dia, CLI, integração PyMongo, testes e a estrutura remota. A collection de leitura passa de `registros_diarios` para `dias`; como a estrutura anterior ainda não possui dados, não é necessária migração remota. Os YAMLs locais existentes permanecem preservados, mas atividades sem `dia` precisam ser migradas antes de compor um retrato completo.
