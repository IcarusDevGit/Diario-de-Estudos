## MODIFIED Requirements

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

### Requirement: Documentos JSON válidos
Todos os arquivos com extensão `.json` em `Esquemas/` SHALL conter documentos JSON válidos, codificados em UTF-8, e não SHALL permanecer vazios.

#### Scenario: Validação sintática dos esquemas
- **WHEN** cada arquivo com extensão `.json` em `Esquemas/` é analisado por um parser JSON
- **THEN** todos são aceitos sem erro sintático

## ADDED Requirements

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
