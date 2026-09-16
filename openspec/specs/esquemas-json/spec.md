# Esquemas JSON Specification

## Purpose

Definir esquemas JSON estruturados e validáveis que descrevam os modelos do diário e possam servir como entrada inequívoca para consumidores como geradores de classes Python.

## Requirements

### Requirement: Metadados estruturais do esquema
Cada arquivo de esquema SHALL conter `versao`, `classe` e `campos`; um esquema que represente uma especialização SHALL também declarar `classe_mae`. Os nomes de classe SHALL ser identificadores Python sem acentos. O catálogo SHALL incluir as classes fundamentais `Relatorio`, `RegistroDiario`, `Pausa`, `Tarefa`, `SessaoEstudo` e `SessaoExercicio`, sem limitar a inclusão futura de novos modelos.

#### Scenario: Identificação de uma classe base
- **WHEN** um consumidor lê `tarefa.json`
- **THEN** encontra a versão do formato, a classe `Tarefa` e suas definições em `campos`

#### Scenario: Identificação de uma especialização
- **WHEN** um consumidor lê `sessão-exercicio.json`
- **THEN** encontra a classe `SessaoExercicio` e a referência `classe_mae` para `Tarefa`

#### Scenario: Catálogo ampliado
- **WHEN** um novo esquema válido é adicionado a `Esquemas`
- **THEN** o contrato não exige atualizar uma quantidade fixa de classes

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

### Requirement: Tipos temporais coerentes
Os instantes de início e fim de tarefas e pausas SHALL usar `datetime`. A data civil do registro diário SHALL usar `date`, e os horários associados àquele dia SHALL usar `time` com unidade/formato `HH:MM` declarada no esquema.

#### Scenario: Intervalo que atravessa a meia-noite
- **WHEN** uma tarefa ou pausa começa em um dia e termina no dia seguinte
- **THEN** seus campos `inicio` e `fim` preservam data e hora suficientes para calcular a duração corretamente

#### Scenario: Horário do registro diário
- **WHEN** um consumidor lê um horário como `acordei` no registro diário
- **THEN** encontra o tipo `time` com unidade/formato `HH:MM`, enquanto o campo `data` possui o tipo `date`

### Requirement: Estado incompleto representável
Campos que somente são conhecidos após preenchimento ou finalização SHALL ser opcionais. Coleções e valores com um padrão natural SHALL declarar esse padrão no esquema.

#### Scenario: Tarefa em andamento
- **WHEN** uma tarefa é criada antes de ser finalizada
- **THEN** o esquema permite que `fim` esteja ausente e define `pausas` como uma lista inicialmente vazia

#### Scenario: Registro diário parcialmente preenchido
- **WHEN** o relatório do dia ainda não foi concluído
- **THEN** horários e avaliações ainda desconhecidos podem permanecer ausentes

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

### Requirement: Documentos JSON válidos
Todos os arquivos com extensão `.json` em `Esquemas/` SHALL conter documentos JSON válidos, codificados em UTF-8, e não SHALL permanecer vazios.

#### Scenario: Validação sintática dos esquemas
- **WHEN** cada arquivo com extensão `.json` em `Esquemas/` é analisado por um parser JSON
- **THEN** todos são aceitos sem erro sintático

### Requirement: Nulabilidade durante o preenchimento
Os modelos derivados dos esquemas SHALL conseguir representar com `null` campos manuais ainda não preenchidos. O metadado `opcional` SHALL permanecer disponível para a futura política de validação anterior à persistência e não SHALL impedir a criação de um modelo parcial nesta capability.

#### Scenario: Campo manual sem valor
- **WHEN** um modelo é criado antes do preenchimento manual completo
- **THEN** qualquer campo manual sem valor pode ser representado como `null`

#### Scenario: Restrição aplicada a valor nulo
- **WHEN** um campo numérico limitado ainda possui valor `null`
- **THEN** os limites numéricos não rejeitam o estado parcial

### Requirement: Vínculo da atividade ao ciclo diário
A classe base `Tarefa` SHALL declarar o campo `dia` com tipo `date`, permitindo `null` exclusivamente para carregar atividades legadas anteriores à introdução do vínculo. Sessões SHALL herdar esse campo, e pausas SHALL permanecer vinculadas indiretamente por sua atividade.

#### Scenario: Tarefa associada
- **WHEN** um consumidor lê o esquema de `Tarefa`
- **THEN** encontra o campo `dia` e as sessões o recebem por herança

#### Scenario: Atividade legada
- **WHEN** um YAML anterior não possui `dia`
- **THEN** o modelo ainda pode ser carregado com `dia: null` para migração explícita

### Requirement: Hierarquia de relatórios
O esquema `Relatorio` SHALL declarar `data` como `date`, `nome` como `str` anulável e `notas` como `str` anulável. `RegistroDiario` SHALL declarar `Relatorio` como `classe_mae`, herdar esses campos e manter seus campos específicos. A nulabilidade herdada de `nome` SHALL preservar a leitura de registros diários anteriores, enquanto a criação de um relatório genérico SHALL exigir nome no respectivo comando.

#### Scenario: Relatório genérico
- **WHEN** um consumidor lê o esquema de `Relatorio`
- **THEN** encontra os campos `data`, `nome` e `notas`

#### Scenario: Relatório diário especializado
- **WHEN** um consumidor lê o esquema de `RegistroDiario`
- **THEN** encontra `classe_mae: Relatorio` e obtém `data`, `nome` e `notas` por herança

#### Scenario: Registro diário legado
- **WHEN** um YAML de `RegistroDiario` anterior não contém `nome` nem `notas`
- **THEN** o modelo pode ser carregado com esses campos como `null`
