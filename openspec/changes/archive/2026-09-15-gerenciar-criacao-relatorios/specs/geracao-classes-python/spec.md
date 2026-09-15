## MODIFIED Requirements

### Requirement: Geração a partir de todos os esquemas
O gerador SHALL ler todos os documentos JSON de `Esquemas/` e produzir classes Python correspondentes em `Python/Classes/`. Cada classe gerada SHALL preservar o nome, os campos e a relação indicada por `classe_mae` no esquema de origem, sem depender de uma quantidade fixa de modelos.

#### Scenario: Geração dos modelos existentes
- **WHEN** o gerador é executado com todos os esquemas válidos do projeto
- **THEN** o módulo gerado expõe cada classe declarada, incluindo `Relatorio`, `RegistroDiario`, `Pausa`, `Tarefa`, `SessaoEstudo` e `SessaoExercicio`

#### Scenario: Herança de uma sessão
- **WHEN** `SessaoEstudo` declara `classe_mae` igual a `Tarefa`
- **THEN** a classe Python `SessaoEstudo` gerada herda de `Tarefa`

#### Scenario: Herança de relatório diário
- **WHEN** `RegistroDiario` declara `classe_mae` igual a `Relatorio`
- **THEN** a classe Python `RegistroDiario` gerada herda os campos comuns de `Relatorio`
