## MODIFIED Requirements

### Requirement: Definições estruturadas de campos
Cada entrada de `campos` SHALL ser um objeto com um `tipo` explícito. Atributos aplicáveis SHALL expressar opcionalidade, valor padrão, valor mínimo, valor máximo, passo numérico, cálculo derivado, unidade/formato e tipo dos itens de uma lista sem usar uma expressão textual livre. O atributo `passo` SHALL ser um número positivo aplicável somente a campos numéricos. Os campos `duracao` de `Tarefa` e `Pausa` SHALL ser textos calculados com unidade/formato `HH:MM:SS`.

#### Scenario: Lista tipada de pausas
- **WHEN** um consumidor lê o campo `pausas` de `Tarefa`
- **THEN** identifica separadamente o tipo `list`, o tipo de item `Pausa` e o valor padrão de lista vazia

#### Scenario: Campo calculado
- **WHEN** um consumidor lê `duracao` em `Tarefa` ou `Pausa`
- **THEN** identifica o campo como `str` calculado com unidade/formato `HH:MM:SS`, e não como um valor livre obrigatório

#### Scenario: Passo numérico inválido
- **WHEN** um esquema declara `passo` não positivo ou em um campo não numérico
- **THEN** a definição do esquema é rejeitada como incoerente

### Requirement: Limites das avaliações
Todos os campos de avaliação subjetiva de `RegistroDiario`, `SessaoEstudo` e `SessaoExercicio` SHALL ser números de ponto flutuante opcionais com mínimo 1, máximo 5 e passo 0,5 contado a partir do mínimo.

#### Scenario: Avaliação dentro do intervalo
- **WHEN** um consumidor valida uma avaliação igual a 1, 3 ou 5
- **THEN** o valor satisfaz os limites e o passo declarados pelo esquema

#### Scenario: Avaliação intermediária válida
- **WHEN** um consumidor valida uma avaliação igual a 1,5, 2,5, 3,5 ou 4,5
- **THEN** o valor satisfaz os limites e o passo declarados pelo esquema

#### Scenario: Avaliação fora do intervalo
- **WHEN** um consumidor valida uma avaliação menor que 1 ou maior que 5
- **THEN** o valor não satisfaz os limites declarados pelo esquema

#### Scenario: Avaliação fora do passo
- **WHEN** um consumidor valida uma avaliação dentro dos limites que não pertence a um incremento de 0,5 a partir de 1, como 2,3
- **THEN** o valor não satisfaz o passo declarado pelo esquema
