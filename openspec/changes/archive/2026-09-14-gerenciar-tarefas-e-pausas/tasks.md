## 1. Estrutura e fundamentos

- [x] 1.1 Adicionar `.env.example`, configurar `FUSO_HORARIO=UTC-03:00` nesta instância e implementar leitura restrita do `.env` com parser de `UTC±HH:MM`, verificando valor válido e rejeição de configuração ausente, duplicada ou inválida sem alterar estado.
- [x] 1.2 Criar a camada de serviço com caminhos configuráveis para os três diretórios operacionais, relógio e fuso injetáveis, verificando em teste que a raiz temporária e o deslocamento configurado são usados.
- [x] 1.3 Implementar descoberta determinística de arquivos `.yaml` e `.yml` ativos, verificando em testes os estados zero, um e múltiplos arquivos sem modificar conteúdo inconsistente.
- [x] 1.4 Definir erros de domínio acionáveis e utilitários de validação de classe/estado, verificando que mensagens incluem o caminho do arquivo ou a precondição violada.

## 2. Ciclo de vida de tarefas e sessões

- [x] 2.1 Implementar início de `Tarefa`, `SessaoEstudo` e `SessaoExercicio` em `tarefa.yaml`, verificando classe concreta, instante com o deslocamento do `.env`, campos padrão e recusa sem sobrescrita quando já houver atividade.
- [x] 2.2 Implementar cálculo temporal pela linha do tempo UTC e em `HH:MM:SS`, verificando virada de meia-noite, mudança de deslocamento, arredondamento ao segundo e rejeição de fim anterior ao início.
- [x] 2.3 Implementar seleção de nome não conflitante para tarefas concluídas a partir do início e da classe, verificando compatibilidade com Windows e preservação de destinos preexistentes.

## 3. Ciclo de vida de pausas

- [x] 3.1 Implementar início de pausa em `pausa.yaml`, verificando que exige exatamente uma atividade válida, impede uma segunda pausa e preenche um datetime consciente do fuso.
- [x] 3.2 Implementar finalização, cálculo e incorporação da pausa na tarefa, verificando ordem da lista, duração e remoção do transitório apenas após a gravação bem-sucedida.
- [x] 3.3 Cobrir falhas durante a incorporação e restauração compensatória, verificando byte a byte que tarefa e pausa originais permanecem intactas.

## 4. Finalização e consistência transacional

- [x] 4.1 Implementar finalização de tarefa sem pausa ativa, verificando `fim`, duração líquida, preservação da classe/campos manuais e movimentação para `Tarefas/Concluidas`.
- [x] 4.2 Integrar encerramento automático de pausa à finalização de tarefa, verificando que a pausa é incorporada antes do cálculo líquido e que não resta arquivo transitório.
- [x] 4.3 Implementar preparação em duas fases e compensação das alterações de múltiplos arquivos, verificando por falhas simuladas que nenhuma atualização parcial fica observável.
- [x] 4.4 Validar YAMLs, classes e valores essenciais antes de gravar, verificando que conteúdo malformado, classe incompatível, durações inválidas e operações fora de ordem preservam o estado.

## 5. Interface de terminal

- [x] 5.1 Criar a CLI com comandos para iniciar tarefa, iniciar sessão de estudo/exercício, iniciar pausa, finalizar pausa e finalizar tarefa, verificando o parsing e o despacho de cada forma suportada.
- [x] 5.2 Mapear sucessos para código zero com caminho afetado e erros para código diferente de zero com mensagem acionável, verificando saídas e códigos em testes de integração.
- [x] 5.3 Executar fluxos completos da CLI em diretório temporário, verificando tarefa genérica, ambas as sessões, múltiplas pausas sequenciais e conclusão durante uma pausa.

## 6. Verificação final

- [x] 6.1 Executar toda a suíte de testes existente e nova, verificando que geração de classes, serialização YAML e gerenciamento de tarefas/pausas passam sem regressões.
- [x] 6.2 Executar a validação estrita da mudança OpenSpec e verificar que todos os requisitos e cenários permanecem cobertos pelas tarefas implementadas.
