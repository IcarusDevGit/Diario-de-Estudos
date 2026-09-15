## MODIFIED Requirements

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

