## 1. Dependência e configuração segura

- [x] 1.1 Adicionar PyMongo a `requirements.txt` com faixa de versão compatível e verificar que a instalação e a importação do driver funcionam no ambiente do projeto.
- [x] 1.2 Adicionar a chave `MONGODB_URI` a `.env.example` usando somente um placeholder e verificar que `.env` e variantes reais continuam ignorados pelo Git.
- [x] 1.3 Implementar leitura estrita de `MONGODB_URI` a partir do `.env` da raiz selecionada e verificar em testes os casos válido, ausente, duplicado, vazio e com esquema incompatível, sem efetuar conexão.

## 2. Cliente e diagnóstico MongoDB

- [x] 2.1 Criar `Python/configuracao_mongodb.py` com erro de domínio e fábrica injetável de `MongoClient`, verificando em testes o uso de Stable API v1 e `serverSelectionTimeoutMS=5000`.
- [x] 2.2 Implementar diagnóstico por `admin.command({"ping": 1})`, verificando com cliente simulado que nenhuma operação de banco, coleção ou escrita é executada.
- [x] 2.3 Garantir o fechamento do cliente em sucesso e em falhas posteriores à criação, verificando em testes que `close()` é chamado exatamente uma vez em cada fluxo.
- [x] 2.4 Sanitizar erros de configuração e do driver, verificando que URI, usuário, senha e host usados nos testes não aparecem em mensagens nem em representações públicas produzidas pelo módulo.

## 3. Interface de terminal

- [x] 3.1 Adicionar `diagnosticar mongodb` ao parser e ao despacho da CLI, verificando que o comando usa a raiz selecionada e não interfere nos comandos existentes.
- [x] 3.2 Mapear diagnóstico bem-sucedido para código zero e mensagem concisa e falhas para código diferente de zero com mensagem acionável, verificando saída padrão e saída de erro em testes de integração.
- [x] 3.3 Verificar por testes de CLI que nenhuma saída de sucesso ou falha revela a URI configurada ou partes sensíveis dela.

## 4. Verificação final

- [x] 4.1 Executar toda a suíte automatizada sem acesso à rede e verificar que os testes de configuração MongoDB e os fluxos existentes passam sem regressões.
- [x] 4.2 Executar a validação estrita do change OpenSpec e verificar que todos os requisitos e cenários estão cobertos pelas tarefas implementadas.
- [x] 4.3 Executar manualmente `diagnosticar mongodb` com o `.env` local, verificando conexão real ao cluster sem criar dados e sem registrar a URI.
