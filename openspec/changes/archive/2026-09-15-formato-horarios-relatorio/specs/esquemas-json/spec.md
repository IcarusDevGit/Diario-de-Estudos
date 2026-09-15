## MODIFIED Requirements

### Requirement: Tipos temporais coerentes
Os instantes de início e fim de tarefas e pausas SHALL usar `datetime`. A data civil do registro diário SHALL usar `date`, e os horários associados àquele dia SHALL usar `time` com unidade/formato `HH:MM` declarada no esquema.

#### Scenario: Intervalo que atravessa a meia-noite
- **WHEN** uma tarefa ou pausa começa em um dia e termina no dia seguinte
- **THEN** seus campos `inicio` e `fim` preservam data e hora suficientes para calcular a duração corretamente

#### Scenario: Horário do registro diário
- **WHEN** um consumidor lê um horário como `acordei` no registro diário
- **THEN** encontra o tipo `time` com unidade/formato `HH:MM`, enquanto o campo `data` possui o tipo `date`

