# Gerenciamento de Tarefas e Pausas Specification

## Purpose

Permitir o controle confiável, pelo terminal, do ciclo de vida de tarefas, sessões e pausas armazenadas localmente como arquivos YAML editáveis.

## Requirements

### Requirement: Início de tarefa ou sessão
O sistema SHALL oferecer comandos para iniciar uma `Tarefa`, uma `SessaoEstudo` ou uma `SessaoExercicio` somente quando existir exatamente um ciclo diário aberto. A atividade SHALL receber `dia` igual à data desse ciclo e `inicio` igual ao instante atual no fuso configurado, mesmo quando a data civil atual já for posterior à data do ciclo, e SHALL ser salva como YAML no diretório de tarefa em andamento. Os demais campos SHALL conservar os padrões do modelo para permitir preenchimento manual posterior.

#### Scenario: Iniciar tarefa genérica
- **WHEN** o usuário inicia uma tarefa, existe exatamente um ciclo aberto e não existe atividade em andamento
- **THEN** o sistema cria um YAML de `Tarefa` com `dia` e `inicio` preenchidos e campos ainda não informados preservados como valores padrão ou `null`

#### Scenario: Iniciar sessão específica
- **WHEN** o usuário inicia uma sessão de estudo ou de exercício durante um ciclo aberto
- **THEN** o sistema cria o YAML com a classe concreta solicitada, o vínculo ao ciclo e os campos herdados e próprios da sessão

#### Scenario: Atividade sem ciclo aberto
- **WHEN** o usuário tenta iniciar uma tarefa ou sessão sem exatamente um `RegistroDiario` aberto
- **THEN** o comando falha explicando o estado do ciclo e não cria atividade

#### Scenario: Atividade atravessa a meia-noite
- **WHEN** uma atividade começa em um ciclo e termina em data civil posterior antes que esse ciclo seja finalizado
- **THEN** seu campo `dia` continua sendo a data do ciclo em que foi iniciada

### Requirement: Exclusividade da tarefa em andamento
O sistema SHALL considerar qualquer arquivo YAML presente no diretório de tarefa em andamento como estado que precisa ser validado e SHALL permitir no máximo uma tarefa ou sessão ativa. Uma nova atividade não SHALL sobrescrever nem substituir uma atividade existente.

#### Scenario: Segunda tarefa recusada
- **WHEN** o usuário tenta iniciar uma atividade enquanto outra tarefa ou sessão está em andamento
- **THEN** o comando falha, identifica a atividade existente e não altera seus dados

#### Scenario: Múltiplos arquivos inconsistentes
- **WHEN** uma operação encontra mais de um arquivo no diretório de tarefa em andamento
- **THEN** ela falha informando o estado inconsistente sem escolher ou modificar um deles

### Requirement: Início e exclusividade de pausa
O sistema SHALL permitir iniciar uma `Pausa` somente quando houver exatamente uma tarefa ou sessão válida em andamento e nenhuma pausa ativa. O campo `inicio` SHALL receber o instante atual no fuso configurado, e a pausa SHALL ser salva como YAML separado no diretório de pausas.

#### Scenario: Iniciar pausa durante tarefa
- **WHEN** existe exatamente uma atividade em andamento e nenhuma pausa ativa
- **THEN** o sistema cria um YAML de `Pausa` com `inicio` preenchido

#### Scenario: Pausa sem tarefa
- **WHEN** o usuário tenta iniciar uma pausa sem atividade em andamento
- **THEN** o comando falha e não cria arquivo de pausa

#### Scenario: Segunda pausa recusada
- **WHEN** o usuário tenta iniciar uma pausa enquanto outra pausa está ativa
- **THEN** o comando falha e preserva integralmente a pausa existente

### Requirement: Finalização e incorporação de pausa
Ao finalizar uma pausa, o sistema SHALL preencher `fim` com o instante atual, calcular `duracao` no formato `HH:MM:SS` a partir do intervalo entre `inicio` e `fim`, anexar a pausa concluída à lista `pausas` da atividade em andamento e remover o arquivo transitório somente após salvar com sucesso a atividade atualizada.

#### Scenario: Pausa finalizada com sucesso
- **WHEN** existem exatamente uma atividade e uma pausa válidas em andamento
- **THEN** a pausa é incorporada à atividade com `fim` e `duracao` preenchidos e seu arquivo transitório deixa de existir

#### Scenario: Falha ao incorporar pausa
- **WHEN** a atividade não pode ser atualizada durante a finalização da pausa
- **THEN** o comando falha e preserva tanto o YAML original da atividade quanto o arquivo da pausa ativa

#### Scenario: Nenhuma pausa ativa
- **WHEN** o usuário solicita finalizar uma pausa e não existe pausa em andamento
- **THEN** o comando falha sem alterar a atividade atual

### Requirement: Finalização e arquivamento de tarefa
Ao finalizar uma tarefa ou sessão, o sistema SHALL finalizar e incorporar primeiro qualquer pausa ativa, preencher `fim`, calcular `duracao` no formato `HH:MM:SS` a partir do intervalo temporal exato entre `inicio` e `fim` menos os intervalos temporais exatos das pausas e mover o YAML concluído para `Tarefas/Concluidas`. A operação SHALL rejeitar resultado de duração negativa, arredondar somente o resultado líquido final ao segundo e SHALL preservar a classe concreta e todos os campos preenchidos manualmente.

#### Scenario: Finalizar tarefa sem pausa ativa
- **WHEN** o usuário finaliza uma atividade válida em andamento sem pausa ativa
- **THEN** o sistema preenche `fim` e `duracao`, remove o arquivo do diretório de andamento e cria o YAML equivalente no diretório de concluídas

#### Scenario: Finalizar tarefa durante pausa
- **WHEN** o usuário finaliza uma atividade enquanto existe uma pausa ativa
- **THEN** o sistema encerra e incorpora a pausa antes de calcular a duração líquida e arquivar a atividade

#### Scenario: Nenhuma tarefa ativa
- **WHEN** o usuário solicita finalizar uma tarefa sem atividade em andamento
- **THEN** o comando falha sem criar arquivo em `Tarefas/Concluidas`

#### Scenario: Destino concluído já existe
- **WHEN** o nome de destino calculado para a atividade concluída já está ocupado
- **THEN** o sistema escolhe um nome não conflitante sem sobrescrever o arquivo existente

### Requirement: Configuração e semântica temporal consistente
O sistema SHALL ler a variável `FUSO_HORARIO` do arquivo `.env` localizado na raiz do projeto e SHALL aceitar deslocamentos no formato `UTC±HH:MM`; nesta instância, o valor SHALL ser `UTC-03:00`. Todos os instantes automáticos SHALL ser datetimes conscientes desse deslocamento. Os cálculos SHALL usar a diferença real entre instantes, incluindo atividades que cruzem a meia-noite, e as durações SHALL seguir o formato canônico `HH:MM:SS`.

#### Scenario: Fuso configurado nesta instância
- **WHEN** o `.env` contém `FUSO_HORARIO=UTC-03:00`
- **THEN** os instantes automáticos são persistidos com o deslocamento `-03:00`

#### Scenario: Configuração ausente ou inválida
- **WHEN** `FUSO_HORARIO` está ausente ou não segue o formato e os limites aceitos
- **THEN** o comando falha com uma mensagem que identifica a variável sem criar ou alterar arquivos operacionais

#### Scenario: Tarefa cruza a meia-noite
- **WHEN** uma tarefa começa antes da meia-noite e termina no dia seguinte
- **THEN** sua duração usa o intervalo real entre os dois instantes em vez de subtrair apenas os horários locais

#### Scenario: Relógio anterior ao início
- **WHEN** o instante de finalização é anterior ao instante de início da tarefa ou pausa
- **THEN** a operação falha com uma mensagem temporal e preserva o estado anterior

### Requirement: Validação e preservação do estado
Antes de qualquer alteração, o sistema SHALL carregar e validar todos os arquivos envolvidos pelo contrato YAML e pela classe esperada. Operações inválidas SHALL retornar uma mensagem acionável e código de saída diferente de zero; operações bem-sucedidas SHALL retornar código zero. Nenhuma falha SHALL deixar uma atualização parcial observável entre os arquivos envolvidos.

#### Scenario: YAML ativo inválido
- **WHEN** uma operação encontra um YAML malformado ou de classe incompatível em um diretório operacional
- **THEN** o comando falha identificando o arquivo e não altera nenhum arquivo de estado

#### Scenario: Operação bem-sucedida pelo terminal
- **WHEN** um comando completa a transição solicitada
- **THEN** ele retorna código zero e informa o arquivo criado, atualizado ou movido

#### Scenario: Falha pelo terminal
- **WHEN** uma precondição da operação não é atendida
- **THEN** o comando retorna código diferente de zero e explica a precondição violada
