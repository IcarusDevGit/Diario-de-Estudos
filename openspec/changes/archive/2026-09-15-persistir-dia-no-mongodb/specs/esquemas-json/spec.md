## ADDED Requirements

### Requirement: Vínculo da atividade ao ciclo diário
A classe base `Tarefa` SHALL declarar o campo `dia` com tipo `date`, permitindo `null` exclusivamente para carregar atividades legadas anteriores à introdução do vínculo. Sessões SHALL herdar esse campo, e pausas SHALL permanecer vinculadas indiretamente por sua atividade.

#### Scenario: Tarefa associada
- **WHEN** um consumidor lê o esquema de `Tarefa`
- **THEN** encontra o campo `dia` e as sessões o recebem por herança

#### Scenario: Atividade legada
- **WHEN** um YAML anterior não possui `dia`
- **THEN** o modelo ainda pode ser carregado com `dia: null` para migração explícita

