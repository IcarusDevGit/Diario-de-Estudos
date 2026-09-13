## MODIFIED Requirements

### Requirement: Metadados estruturais do esquema
Cada arquivo de esquema SHALL conter `versao`, `classe` e `campos`; um esquema que represente uma especialização SHALL também declarar `classe_mae`. Os nomes de classe SHALL ser identificadores Python sem acentos, incluindo exatamente `Pausa`, `Tarefa`, `SessaoEstudo`, `SessaoExercicio` e `RegistroDiario` para os cinco esquemas existentes.

#### Scenario: Identificação de uma classe base
- **WHEN** um consumidor lê `tarefa.json`
- **THEN** encontra a versão do formato, a classe `Tarefa` e suas definições em `campos`

#### Scenario: Identificação de uma especialização
- **WHEN** um consumidor lê `sessão-exercicio.json`
- **THEN** encontra a classe `SessaoExercicio` e a referência `classe_mae` para `Tarefa`

## ADDED Requirements

### Requirement: Nulabilidade durante o preenchimento
Os modelos derivados dos esquemas SHALL conseguir representar com `null` campos manuais ainda não preenchidos. O metadado `opcional` SHALL permanecer disponível para a futura política de validação anterior à persistência e não SHALL impedir a criação de um modelo parcial nesta capability.

#### Scenario: Campo manual sem valor
- **WHEN** um modelo é criado antes do preenchimento manual completo
- **THEN** qualquer campo manual sem valor pode ser representado como `null`

#### Scenario: Restrição aplicada a valor nulo
- **WHEN** um campo numérico limitado ainda possui valor `null`
- **THEN** os limites numéricos não rejeitam o estado parcial

