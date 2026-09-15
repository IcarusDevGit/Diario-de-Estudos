## Purpose

Permitir criar pelo terminal relatórios genéricos datados, legíveis e editáveis, sem limitar a evolução para novos tipos especializados.

## ADDED Requirements

### Requirement: Criação de relatório genérico
O sistema SHALL oferecer `criar relatorio NOME [--data YYYY-MM-DD]` para criar uma instância de `Relatorio` em `Relatórios`. `nome` SHALL receber o argumento informado, `notas` SHALL iniciar como `null`, e `data` SHALL receber a data explícita ou, quando omitida, a data civil atual no fuso configurado.

#### Scenario: Criar relatório na data atual
- **WHEN** o usuário executa `criar relatorio "Revisão do projeto"` em uma configuração temporal válida
- **THEN** o YAML criado contém `classe: Relatorio`, a data local atual, o nome informado e `notas: null`

#### Scenario: Criar relatório para outra data
- **WHEN** o usuário executa `criar relatorio "Revisão" --data 2026-09-14`
- **THEN** o YAML criado possui `data: '2026-09-14'` independentemente da data civil atual

### Requirement: Nome obrigatório e significativo
O comando SHALL exigir que `NOME` contenha texto não vazio após remover espaços externos. Entrada ausente ou vazia SHALL ser recusada sem criar arquivo.

#### Scenario: Nome vazio
- **WHEN** o usuário informa um nome composto somente por espaços
- **THEN** o comando falha com mensagem acionável e não cria relatório

### Requirement: Nomeação segura sem sobrescrita
O arquivo SHALL usar o prefixo `RG-`, a data do relatório e uma representação normalizada do nome adequada a arquivo. Se o destino já existir, o sistema SHALL escolher deterministicamente um sufixo numérico livre e MUST NOT sobrescrever o relatório existente.

#### Scenario: Primeiro relatório com o nome
- **WHEN** não existe destino conflitante para o nome e a data
- **THEN** o sistema cria `RG-YYYY-MM-DD-<nome-normalizado>.yaml`

#### Scenario: Relatório homônimo
- **WHEN** já existe um relatório com o mesmo nome normalizado e a mesma data
- **THEN** o sistema cria outro arquivo com sufixo numérico sem alterar o anterior

### Requirement: Gravação validada e atômica
O relatório SHALL ser validado pelo contrato dos modelos e salvo atomicamente. Falhas de argumento, fuso, serialização ou escrita SHALL retornar código diferente de zero, identificar a causa e não deixar arquivo parcial.

#### Scenario: Criação bem-sucedida
- **WHEN** todos os dados e a configuração são válidos e o arquivo pode ser gravado
- **THEN** a CLI retorna código zero e informa o caminho criado

#### Scenario: Falha de criação
- **WHEN** a validação ou gravação falha
- **THEN** a CLI retorna código diferente de zero e nenhum relatório parcial permanece
