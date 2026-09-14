## Why

O projeto precisará acessar o cluster MongoDB Atlas já provisionado nas próximas etapas, mas ainda não possui driver, configuração validada nem uma forma segura e reproduzível de verificar a conectividade. Preparar essa fundação separadamente reduz o risco antes de introduzir persistência de dados.

## What Changes

- Adicionar a dependência oficial PyMongo para acesso síncrono ao MongoDB.
- Ler `MONGODB_URI` do `.env` local sem expor seu valor em logs ou mensagens de erro.
- Criar uma fábrica de `MongoClient` configurada com Stable API v1 e limites de tempo adequados para uma CLI.
- Disponibilizar um diagnóstico de conexão que executa `ping`, informa sucesso ou erro acionável e sempre encerra o cliente.
- Cobrir configuração, criação, diagnóstico e encerramento com testes que não acessam o cluster real.
- Manter fora do escopo bancos, coleções, índices e qualquer persistência ou consulta de dados de domínio.

## Capabilities

### New Capabilities

- `configuracao-mongodb`: Configuração segura do cliente MongoDB e diagnóstico de conectividade com o cluster.

### Modified Capabilities

Nenhuma.

## Impact

- `requirements.txt` passa a incluir PyMongo.
- `.env.example` documenta `MONGODB_URI` apenas com um placeholder sem credenciais.
- Uma nova camada Python concentra leitura de configuração e ciclo de vida do cliente.
- A CLI recebe um comando de diagnóstico, sem alterar os fluxos existentes de tarefas, sessões e pausas.
- O cluster Atlas é consultado apenas por `ping`; nenhum dado ou estrutura será criado nesta mudança.
