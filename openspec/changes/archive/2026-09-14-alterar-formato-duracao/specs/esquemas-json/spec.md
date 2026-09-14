## MODIFIED Requirements

### Requirement: Definições estruturadas de campos
Cada entrada de `campos` SHALL ser um objeto com um `tipo` explícito. Atributos aplicáveis SHALL expressar opcionalidade, valor padrão, valor mínimo, valor máximo, cálculo derivado, unidade/formato e tipo dos itens de uma lista sem usar uma expressão textual livre. Os campos `duracao` de `Tarefa` e `Pausa` SHALL ser textos calculados com unidade/formato `HH:MM:SS`.

#### Scenario: Lista tipada de pausas
- **WHEN** um consumidor lê o campo `pausas` de `Tarefa`
- **THEN** identifica separadamente o tipo `list`, o tipo de item `Pausa` e o valor padrão de lista vazia

#### Scenario: Campo calculado
- **WHEN** um consumidor lê `duracao` em `Tarefa` ou `Pausa`
- **THEN** identifica o campo como `str` calculado com unidade/formato `HH:MM:SS`, e não como um valor livre obrigatório
