## 1. Configuração e acesso ao histórico

- [x] 1.1 Adicionar `MONGODB_DATABASE=diario_estudos` a `.env.example` e implementar leitura estrita da variável sem afetar o diagnóstico que depende somente da URI, verificando valores válido, ausente, duplicado e vazio em testes.
- [x] 1.2 Implementar a consulta somente de leitura a `diario_estudos.registros_diarios` pelo identificador único `data` em formato ISO, com projeção de `fui_dormir` e limite defensivo de dois resultados, verificando em testes os filtros e a ausência de operações de escrita ou criação de índice.
- [x] 1.3 Converter `fui_dormir` remoto de `HH:MM:SS` para `time` e verificar histórico ausente, resultado único válido, valor ausente/inválido e documentos duplicados.
- [x] 1.4 Traduzir falhas PyMongo para erro sanitizado e fechar o cliente em sucesso ou falha, verificando que URI, credenciais e host não aparecem nas saídas.

## 2. Início do dia

- [x] 2.1 Criar `GerenciadorDia` com raiz, relógio, fuso e consulta injetáveis, verificando que um único instante determina a data atual e o caminho `Relatórios/RD-YYYY-MM-DD.yaml`.
- [x] 2.2 Implementar `iniciar_dia` com consulta ao dia anterior e criação atômica de `RegistroDiario`, verificando preenchimento de `data`, propagação de `dormi_dia_anterior` e manutenção dos demais campos em `null` ou no padrão.
- [x] 2.3 Recusar relatório já existente antes de consultar o MongoDB, verificando que o arquivo é preservado byte a byte e que a dependência remota não é chamada.
- [x] 2.4 Cobrir falhas de configuração, conexão, consulta e conteúdo remoto, verificando que nenhum YAML novo ou parcial é criado.

## 3. Finalização do dia

- [x] 3.1 Expor no gerenciador de tarefas uma consulta pública e não mutante da atividade ativa, verificando os estados vazio, atividade válida, múltiplos YAMLs e YAML inválido.
- [x] 3.2 Implementar carregamento do relatório atual com validação de classe e data, verificando relatório ausente, YAML inválido, classe incompatível e data divergente sem alterar arquivos.
- [x] 3.3 Implementar validação por metadados dos campos com `opcional: false`, verificando que todos os campos `None` são listados e que valores falsos válidos, como `folga: false`, são aceitos.
- [x] 3.4 Recusar finalização com atividade ativa ou estado de tarefas inconsistente, verificando preservação byte a byte do relatório diário.
- [x] 3.5 Preencher `fui_dormir` somente após todas as validações e salvar atomicamente, verificando hora no fuso, preservação dos campos manuais e do arquivo anterior em falha de gravação.
- [x] 3.6 Recusar nova finalização quando `fui_dormir` já estiver preenchido, verificando que o horário original não é substituído.

## 4. Interface de terminal

- [x] 4.1 Adicionar `iniciar dia` e `finalizar dia` ao parser e despacho da CLI, verificando uso da raiz selecionada e ausência de regressões nos demais comandos.
- [x] 4.2 Mapear sucessos para código zero e caminho do relatório e falhas para código diferente de zero com mensagem acionável e sanitizada, verificando stdout e stderr em testes de integração.
- [x] 4.3 Executar fluxos completos da CLI em diretório temporário, verificando início sem histórico, início com horário anterior, preenchimento manual, bloqueio por tarefa ativa e finalização bem-sucedida.

## 5. Verificação final

- [x] 5.1 Executar toda a suíte automatizada sem rede e verificar que configuração MongoDB, serialização e gerenciamento de tarefas, pausas e dia passam sem regressões.
- [x] 5.2 Executar a validação estrita do change OpenSpec e verificar que todos os requisitos e cenários estão cobertos pelas tarefas implementadas.
- [x] 5.3 Executar `iniciar dia` contra o cluster real ainda sem histórico, verificando criação local com `dormi_dia_anterior: null` e confirmando no Atlas que database, collection e documentos não foram criados pela consulta.




