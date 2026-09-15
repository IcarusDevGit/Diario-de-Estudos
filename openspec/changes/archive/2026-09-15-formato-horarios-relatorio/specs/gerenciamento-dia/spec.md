## MODIFIED Requirements

### Requirement: Consulta do horário de sono anterior
Antes de criar o relatório, o sistema SHALL consultar na database configurada a collection `registros_diarios` pelo campo `data` igual à data anterior em formato `YYYY-MM-DD`. O campo `data` SHALL identificar unicamente um relatório diário na collection. Quando existir exatamente um documento, seu campo `fui_dormir` SHALL ser um horário ISO `HH:MM` ou um horário legado `HH:MM:SS` válido e SHALL preencher `dormi_dia_anterior` com precisão de minuto, descartando segundos sem arredondar. A consulta SHALL ser somente de leitura e SHALL encerrar o cliente após terminar.

#### Scenario: Registro anterior encontrado
- **WHEN** existe exatamente um documento do dia anterior com `fui_dormir` válido em `HH:MM`
- **THEN** o novo YAML recebe esse horário em `dormi_dia_anterior`

#### Scenario: Registro anterior legado encontrado
- **WHEN** existe exatamente um documento do dia anterior com `fui_dormir` válido em `HH:MM:SS`
- **THEN** o novo YAML recebe hora e minuto em `dormi_dia_anterior`, sem arredondar pelos segundos

#### Scenario: Histórico ainda não existe
- **WHEN** a database, a collection ou o documento do dia anterior não existe
- **THEN** o novo YAML é criado com `dormi_dia_anterior: null`

#### Scenario: Histórico duplicado ou inválido
- **WHEN** há mais de um documento para a data anterior ou `fui_dormir` não contém um horário ISO aceito
- **THEN** o comando falha identificando a inconsistência sem criar o YAML

### Requirement: Encerramento atômico do dia
Somente depois que todas as validações forem aprovadas, o sistema SHALL preencher `fui_dormir` com a hora e o minuto atuais no fuso configurado, descartando segundos e microssegundos sem arredondar, e substituir atomicamente o mesmo YAML. Um relatório cujo `fui_dormir` já esteja preenchido SHALL ser considerado finalizado e não SHALL ter o horário substituído por uma nova execução.

#### Scenario: Finalização bem-sucedida
- **WHEN** o registro atual é válido, seus campos obrigatórios estão preenchidos, `fui_dormir` está `null` e não há atividade em andamento
- **THEN** o sistema grava `fui_dormir` como `HH:MM` no minuto local atual e preserva todos os valores preenchidos manualmente

#### Scenario: Dia já finalizado
- **WHEN** `fui_dormir` já está preenchido no registro atual
- **THEN** o comando falha informando que o dia já foi finalizado e não altera o horário existente

#### Scenario: Falha de gravação
- **WHEN** a serialização ou substituição do relatório finalizado falha
- **THEN** o arquivo anterior permanece byte a byte inalterado

