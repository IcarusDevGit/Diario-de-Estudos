## MODIFIED Requirements

### Requirement: Configuração da conexão por ambiente
O sistema SHALL obter a conexão MongoDB da variável `MONGODB_URI` e o nome da database da variável `MONGODB_DATABASE`, ambas no arquivo `.env` da raiz selecionada. A configuração SHALL aceitar uma URI não vazia iniciada por `mongodb://` ou `mongodb+srv://` e um nome de database não vazio; nesta instância, `MONGODB_DATABASE` SHALL ser `diario_estudos`. O sistema SHALL rejeitar qualquer variável necessária ausente, duplicada, vazia ou incompatível antes de tentar acessar a rede.

#### Scenario: URI válida
- **WHEN** o `.env` contém exatamente uma variável `MONGODB_URI` com esquema MongoDB aceito
- **THEN** o sistema disponibiliza a configuração para criar o cliente

#### Scenario: Configuração inválida
- **WHEN** `MONGODB_URI` está ausente, duplicada, vazia ou não usa um esquema MongoDB aceito
- **THEN** a operação falha com uma mensagem que identifica a variável sem iniciar uma conexão

#### Scenario: Database válida
- **WHEN** o `.env` contém exatamente `MONGODB_DATABASE=diario_estudos`
- **THEN** o sistema disponibiliza esse nome para selecionar a database da aplicação

#### Scenario: Database ausente ou inválida
- **WHEN** `MONGODB_DATABASE` está ausente, duplicada ou vazia
- **THEN** uma operação que depende da database falha identificando a variável sem consultar o MongoDB
