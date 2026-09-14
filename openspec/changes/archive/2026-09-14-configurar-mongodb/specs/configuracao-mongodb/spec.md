## Purpose

Permitir que a aplicação configure com segurança o acesso ao MongoDB Atlas e verifique a conectividade antes que funcionalidades de persistência sejam introduzidas.

## ADDED Requirements

### Requirement: Configuração da conexão por ambiente
O sistema SHALL obter a conexão MongoDB exclusivamente da variável `MONGODB_URI` no arquivo `.env` da raiz selecionada. A configuração SHALL aceitar uma URI não vazia iniciada por `mongodb://` ou `mongodb+srv://` e SHALL rejeitar variável ausente, duplicada, vazia ou com esquema incompatível antes de tentar acessar a rede.

#### Scenario: URI válida
- **WHEN** o `.env` contém exatamente uma variável `MONGODB_URI` com esquema MongoDB aceito
- **THEN** o sistema disponibiliza a configuração para criar o cliente

#### Scenario: Configuração inválida
- **WHEN** `MONGODB_URI` está ausente, duplicada, vazia ou não usa um esquema MongoDB aceito
- **THEN** a operação falha com uma mensagem que identifica a variável sem iniciar uma conexão

### Requirement: Sigilo da credencial
O sistema SHALL tratar `MONGODB_URI` como segredo e MUST NOT incluir seu valor, usuário, senha ou host completo em saídas de sucesso, mensagens de erro ou representações textuais produzidas pela aplicação.

#### Scenario: Erro de conexão não revela URI
- **WHEN** a tentativa de conexão falha e a URI contém credenciais
- **THEN** a mensagem apresentada identifica a etapa da falha sem reproduzir a URI nem suas credenciais

#### Scenario: Diagnóstico bem-sucedido não revela destino
- **WHEN** o diagnóstico confirma a conectividade
- **THEN** a saída informa o sucesso sem exibir a URI

### Requirement: Cliente compatível e limitado no tempo
O sistema SHALL criar um cliente síncrono configurado para a Stable API v1 do MongoDB e com limite de seleção de servidor adequado ao uso interativo pelo terminal. Criar o cliente SHALL NOT executar operações de domínio nem criar bancos, coleções, índices ou documentos.

#### Scenario: Criação do cliente
- **WHEN** uma configuração válida é fornecida
- **THEN** o cliente é preparado com Stable API v1 e um limite explícito de seleção de servidor

#### Scenario: Nenhuma persistência durante configuração
- **WHEN** o cliente é criado sem executar o diagnóstico
- **THEN** nenhum comando de escrita ou preparação de estrutura é enviado ao MongoDB

### Requirement: Diagnóstico de conectividade
O sistema SHALL oferecer um comando de terminal para diagnosticar a conexão por meio do comando administrativo `ping`. O diagnóstico SHALL retornar código zero e mensagem concisa em caso de sucesso, ou código diferente de zero e mensagem acionável em caso de falha de configuração ou conexão.

#### Scenario: Ping bem-sucedido
- **WHEN** o usuário executa o diagnóstico com configuração válida e o cluster responde ao `ping`
- **THEN** o comando retorna código zero e informa que a conexão foi estabelecida

#### Scenario: Ping falha
- **WHEN** o cluster não pode ser selecionado, autenticado ou alcançado dentro do limite configurado
- **THEN** o comando retorna código diferente de zero e descreve a categoria da falha sem revelar dados sensíveis

### Requirement: Encerramento determinístico do cliente
O sistema SHALL encerrar o cliente MongoDB após todo diagnóstico, inclusive quando a criação da conexão ou o `ping` resultar em erro depois que o cliente tiver sido criado.

#### Scenario: Cliente fechado após sucesso
- **WHEN** o `ping` termina com sucesso
- **THEN** o cliente é fechado antes de o comando retornar

#### Scenario: Cliente fechado após falha
- **WHEN** ocorre uma falha depois da criação do cliente
- **THEN** o cliente é fechado antes de o erro ser informado
