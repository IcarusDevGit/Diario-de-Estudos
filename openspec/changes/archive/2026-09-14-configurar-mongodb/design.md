## Context

O projeto é uma aplicação Python síncrona acionada pelo terminal. Atualmente, `requirements.txt` contém apenas PyYAML, a configuração local é lida de `.env` por código próprio e `.env`/`.env.*` já são ignorados, com exceção de `.env.example`. Não existe driver MongoDB, camada de conexão ou comando de diagnóstico. Consulte `proposal.md` para a motivação e `specs/configuracao-mongodb/spec.md` para o contrato observável.

O cluster MongoDB Atlas já foi criado e a URI real já foi armazenada localmente como `MONGODB_URI`. Essa URI é um segredo e não deve ser lida durante os testes nem aparecer em artefatos, logs ou exceções da aplicação.

## Goals / Non-Goals

**Goals:**

- Isolar configuração, criação e encerramento do cliente em um módulo reutilizável por mudanças futuras.
- Produzir falhas rápidas e acionáveis para uma ferramenta interativa.
- Permitir testes determinísticos por injeção ou simulação do cliente, sem DNS, rede ou credenciais reais.
- Integrar o diagnóstico ao padrão de código de saída já usado pela CLI.

**Non-Goals:**

- Selecionar ou validar `MONGODB_DATABASE`.
- Criar bancos, coleções, índices, validadores ou documentos.
- Persistir ou consultar `RegistroDiario`, tarefas, sessões ou pausas.
- Administrar usuários, senhas ou a IP Access List do Atlas pela aplicação.

## Decisions

### Usar PyMongo síncrono

Adicionar `pymongo` como driver oficial e usar `MongoClient`, pois toda a CLI atual é síncrona e executa operações curtas. Uma API assíncrona acrescentaria ciclo de eventos e interfaces paralelas sem benefício nesta etapa.

Alternativa considerada: `AsyncMongoClient`. Rejeitada agora por não haver concorrência nem infraestrutura assíncrona no projeto.

### Concentrar a integração em `Python/configuracao_mongodb.py`

O módulo conterá o erro de domínio, a leitura/validação de `MONGODB_URI`, a fábrica do cliente e o diagnóstico. O restante da aplicação não conhecerá detalhes de PyMongo além dessa fronteira. A fábrica aceitará substituição em testes para impedir conexões reais.

Alternativa considerada: colocar a lógica diretamente em `cli.py`. Rejeitada porque acoplaria parsing de terminal, segredo e driver, dificultando reutilização na persistência futura.

### Reutilizar o arquivo `.env` sem adicionar `python-dotenv`

Extrair um leitor pequeno e compartilhável ou reutilizar o padrão estrito existente, mantendo detecção de variável ausente, duplicada e vazia. Isso evita uma segunda dependência apenas para poucas chaves e preserva o comportamento atual de configuração por raiz.

O código nunca registrará a linha, o valor ou a exceção completa se ela puder conter a URI. A validação verificará somente presença e os prefixos `mongodb://` ou `mongodb+srv://`; autenticação e alcance serão verificados pelo `ping`.

Alternativa considerada: armazenar usuário e senha em variáveis separadas e montar a URI. Rejeitada porque o Atlas já fornece uma URI apropriada e a montagem exige codificação correta de credenciais e opções.

### Stable API v1 e timeout explícito

O cliente será criado com `ServerApi("1")` e `serverSelectionTimeoutMS=5000`. Cinco segundos equilibram resposta interativa e tolerância a uma conexão remota. O timeout ficará centralizado como constante para ajuste futuro.

Alternativa considerada: usar os padrões do driver. Rejeitada porque uma falha de rede pode manter a CLI aguardando por tempo excessivo e menos previsível.

### Diagnóstico por comando dedicado

A CLI receberá `diagnosticar mongodb`. O fluxo carregará a URI, criará o cliente, executará `client.admin.command({"ping": 1})` e fechará o cliente em `finally`. Sucesso retorna zero; erros de configuração ou PyMongo serão traduzidos para uma exceção de domínio sanitizada e retornarão código diferente de zero pelo tratamento já existente na CLI.

Alternativa considerada: testar automaticamente a conexão ao iniciar qualquer comando. Rejeitada porque tarefas e pausas continuam locais e não devem depender do Atlas.

### Testes unitários sem cluster

Os testes usarão diretórios temporários para `.env` e um cliente simulado com `admin.command` e `close`. Serão verificados os argumentos da fábrica, o comando `ping`, os códigos e mensagens da CLI, o fechamento em sucesso/falha e a ausência da URI nas saídas. Um teste real de Atlas permanece uma verificação manual explícita após a implementação.

## Risks / Trade-offs

- [Uma URI sintaticamente aceita ainda pode ter opções ou credenciais inválidas] → Delegar a validação completa ao driver durante o `ping` e apresentar erro sanitizado.
- [Cinco segundos podem ser curtos em redes lentas] → Manter o valor centralizado e ajustável em mudança futura, sem expô-lo inicialmente como configuração pública.
- [Capturar mensagens do driver pode vazar partes do destino] → Não encaminhar a mensagem original ao usuário; preservar encadeamento apenas para diagnóstico interno em testes/desenvolvimento.
- [Um mock pode divergir do Atlas real] → Complementar a suíte com execução manual do comando de diagnóstico usando o `.env` local, sem tornar a rede requisito dos testes automatizados.

## Migration Plan

1. Adicionar PyMongo e documentar somente o placeholder de `MONGODB_URI` em `.env.example`.
2. Introduzir o módulo isolado e seus testes.
3. Adicionar o comando de diagnóstico e testes de integração da CLI.
4. Executar a suíte automatizada sem rede e, opcionalmente, o diagnóstico manual contra o cluster configurado.

Rollback: remover o comando, o módulo e a dependência PyMongo; os fluxos locais existentes permanecem independentes e não exigem migração de dados.
