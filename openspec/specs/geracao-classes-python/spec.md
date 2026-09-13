# Geração de Classes Python Specification

## Purpose

Permitir que os modelos Python do diário sejam reproduzidos automaticamente a partir dos esquemas JSON, com resultado tipado, validável e verificável sem manutenção duplicada.

## Requirements

### Requirement: Geração a partir de todos os esquemas
O gerador SHALL ler todos os documentos JSON de `Esquemas/` e produzir classes Python correspondentes em `Python/Classes/`. Cada classe gerada SHALL preservar o nome, os campos e a relação indicada por `classe_mae` no esquema de origem.

#### Scenario: Geração dos modelos existentes
- **WHEN** o gerador é executado com os cinco esquemas válidos do projeto
- **THEN** o módulo gerado expõe `Pausa`, `Tarefa`, `SessaoEstudo`, `SessaoExercicio` e `RegistroDiario`

#### Scenario: Herança de uma sessão
- **WHEN** `SessaoEstudo` declara `classe_mae` igual a `Tarefa`
- **THEN** a classe Python `SessaoEstudo` gerada herda de `Tarefa`

### Requirement: Mapeamento de tipos e metadados
O gerador SHALL mapear `str`, `bool`, `int`, `float`, `date`, `time`, `datetime` e listas tipadas para anotações Python equivalentes. Valores padrão mutáveis SHALL ser independentes entre instâncias; campos calculados SHALL ser excluídos da inicialização; limites numéricos SHALL ser validados para valores não nulos.

#### Scenario: Lista padrão independente
- **WHEN** duas instâncias de `Tarefa` são criadas
- **THEN** cada instância possui sua própria lista de pausas

#### Scenario: Campo calculado na inicialização
- **WHEN** uma instância de `Tarefa` ou `Pausa` é criada
- **THEN** `duracao` não é aceito como argumento de inicialização

#### Scenario: Avaliação fora dos limites
- **WHEN** uma classe recebe valor não nulo abaixo de `minimo` ou acima de `maximo`
- **THEN** a criação falha com uma mensagem que identifica classe, campo e restrição violada

#### Scenario: Instância parcialmente preenchida
- **WHEN** um campo manual ainda não possui valor
- **THEN** a classe gerada permite representá-lo como `None`, deixando a obrigatoriedade de persistência para uma etapa futura

### Requirement: Resultado determinístico e importável
As mesmas entradas SHALL produzir conteúdo idêntico e sintaticamente válido em execuções sucessivas, independentemente da ordem de enumeração dos arquivos. O módulo gerado SHALL ser importável e indicar claramente que não deve ser editado manualmente.

#### Scenario: Regeneração sem alterações
- **WHEN** o gerador é executado duas vezes sem mudanças nos esquemas
- **THEN** o conteúdo gerado após a segunda execução é idêntico ao conteúdo da primeira

#### Scenario: Importação do resultado
- **WHEN** a geração termina com sucesso
- **THEN** o módulo pode ser compilado e importado pelo Python sem erro

### Requirement: Validação antes da substituição
Antes de substituir o módulo existente, o gerador SHALL rejeitar JSON inválido, versão incompatível, nomes de classe duplicados ou inválidos, tipos desconhecidos, referências inexistentes, ciclos de herança e definições de campo incoerentes. Uma falha SHALL retornar estado diferente de zero, descrever o problema e preservar integralmente o último módulo gerado válido.

#### Scenario: Referência de classe inexistente
- **WHEN** um campo ou `classe_mae` referencia uma classe não declarada
- **THEN** a geração falha antes de alterar o módulo existente e identifica a referência inválida

#### Scenario: Código renderizado inválido
- **WHEN** o conteúdo renderizado não pode ser compilado
- **THEN** a geração falha e mantém o módulo anterior sem alterações

### Requirement: Verificação de desatualização
O gerador SHALL oferecer um modo de verificação que compare o resultado esperado com o módulo presente sem modificar arquivos. Esse modo SHALL terminar com sucesso quando estiver atualizado e com estado diferente de zero quando estiver ausente ou divergente.

#### Scenario: Módulo atualizado
- **WHEN** o modo de verificação é executado após uma geração bem-sucedida sem mudança nos esquemas
- **THEN** ele informa que o módulo está atualizado e não altera arquivos

#### Scenario: Esquema alterado após geração
- **WHEN** um esquema é modificado sem regenerar as classes
- **THEN** o modo de verificação informa que o módulo está desatualizado e retorna estado diferente de zero
