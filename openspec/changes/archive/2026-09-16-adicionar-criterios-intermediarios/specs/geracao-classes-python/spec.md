## MODIFIED Requirements

### Requirement: Mapeamento de tipos e metadados
O gerador SHALL mapear `str`, `bool`, `int`, `float`, `date`, `time`, `datetime` e listas tipadas para anotações Python equivalentes. Valores padrão mutáveis SHALL ser independentes entre instâncias; campos calculados SHALL ser excluídos da inicialização; limites e passos numéricos SHALL ser preservados nos metadados e validados para valores não nulos.

#### Scenario: Lista padrão independente
- **WHEN** duas instâncias de `Tarefa` são criadas
- **THEN** cada instância possui sua própria lista de pausas

#### Scenario: Campo calculado na inicialização
- **WHEN** uma instância de `Tarefa` ou `Pausa` é criada
- **THEN** `duracao` não é aceito como argumento de inicialização

#### Scenario: Avaliação fora dos limites
- **WHEN** uma classe recebe valor não nulo abaixo de `minimo` ou acima de `maximo`
- **THEN** a criação falha com uma mensagem que identifica classe, campo e restrição violada

#### Scenario: Avaliação fora do passo
- **WHEN** uma classe recebe valor não nulo que não corresponde a um incremento de `passo` a partir de `minimo`
- **THEN** a criação falha com uma mensagem que identifica classe, campo e passo violado

#### Scenario: Instância parcialmente preenchida
- **WHEN** um campo manual ainda não possui valor
- **THEN** a classe gerada permite representá-lo como `None`, deixando a obrigatoriedade de persistência para uma etapa futura
