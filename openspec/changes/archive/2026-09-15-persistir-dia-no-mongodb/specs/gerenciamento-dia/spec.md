## MODIFIED Requirements

### Requirement: Início do registro diário
O sistema SHALL oferecer `iniciar dia` para criar um YAML de `RegistroDiario` no diretório `Relatórios`, nomeado pela data civil atual como `RD-YYYY-MM-DD.yaml`. Antes da criação, SHALL validar que não exista qualquer outro `RegistroDiario` aberto, inclusive de data anterior. O campo `data` SHALL receber a data atual no fuso configurado, enquanto campos ainda não informados SHALL conservar `null` ou o padrão do modelo.

#### Scenario: Iniciar o dia
- **WHEN** o usuário inicia o dia e não existe ciclo aberto nem relatório para a data atual
- **THEN** o sistema cria o YAML correspondente com `data` preenchida e campos manuais ainda desconhecidos representados como `null`

#### Scenario: Relatório atual já existe
- **WHEN** o usuário inicia o dia e o arquivo da data atual já existe
- **THEN** o comando falha sem sobrescrever nem alterar o relatório existente

#### Scenario: Ciclo anterior ainda aberto
- **WHEN** existe um `RegistroDiario` de outra data com `fui_dormir: null`
- **THEN** o comando recusa iniciar novo dia e identifica o ciclo pendente

### Requirement: Consulta do horário de sono anterior
Antes de criar o relatório, o sistema SHALL consultar na database configurada a collection `dias` pelo campo `data` igual à data anterior em formato `YYYY-MM-DD` e projetar o `RegistroDiario` do documento agregado. Quando existir exatamente um documento e exatamente um relatório diário, `fui_dormir` SHALL aceitar `HH:MM` ou o formato legado `HH:MM:SS` e SHALL preencher `dormi_dia_anterior` com precisão de minuto. A consulta SHALL ser somente de leitura e SHALL encerrar o cliente após terminar.

#### Scenario: Registro anterior encontrado
- **WHEN** existe exatamente um documento do dia anterior com um `RegistroDiario` e `fui_dormir` válido
- **THEN** o novo YAML recebe esse horário em `dormi_dia_anterior`

#### Scenario: Registro anterior legado encontrado
- **WHEN** o `RegistroDiario` anterior contém `fui_dormir` válido em `HH:MM:SS`
- **THEN** o novo YAML recebe hora e minuto sem arredondar pelos segundos

#### Scenario: Histórico ainda não existe
- **WHEN** a database, a collection ou o documento do dia anterior não existe
- **THEN** o novo YAML é criado com `dormi_dia_anterior: null`

#### Scenario: Histórico duplicado ou inválido
- **WHEN** há mais de um documento para a data, mais de um `RegistroDiario` no retrato ou `fui_dormir` não é válido
- **THEN** o comando falha identificando a inconsistência sem criar o YAML

### Requirement: Validação anterior à finalização
O sistema SHALL oferecer `finalizar dia` e localizar exatamente um `RegistroDiario` aberto, independentemente de sua data coincidir com a data civil atual. Antes de qualquer alteração, SHALL confirmar classe e coerência entre nome e campo `data` e validar que todos os campos com metadado `opcional: false` estejam preenchidos. Nesta capability, somente `RegistroDiario` SHALL ser considerado relatório necessário.

#### Scenario: Finalização depois da meia-noite
- **WHEN** o ciclo aberto possui data anterior à data civil atual
- **THEN** o comando finaliza esse ciclo em vez de procurar ou criar um relatório da data atual

#### Scenario: Campos obrigatórios ausentes
- **WHEN** um ou mais campos obrigatórios do registro aberto permanecem `null`
- **THEN** o comando falha listando os nomes dos campos ausentes e preserva o arquivo byte a byte

#### Scenario: Ciclo ausente ou inconsistente
- **WHEN** não existe ciclo aberto, existem múltiplos ciclos abertos ou um candidato é inválido
- **THEN** o comando falha identificando os arquivos ou a precondição sem modificar relatório

#### Scenario: Relatório ausente ou incompatível
- **WHEN** nenhum arquivo aberto representa um `RegistroDiario` válido ou seu nome e sua data divergem
- **THEN** o comando falha identificando o arquivo ou a precondição sem criar nem modificar relatório

### Requirement: Encerramento atômico do dia
Somente depois que todas as validações forem aprovadas, o sistema SHALL preencher `fui_dormir` com a hora e o minuto atuais no fuso configurado e substituir atomicamente o YAML do ciclo aberto. Depois da gravação local, SHALL tentar persistir o retrato no MongoDB. Um relatório cujo `fui_dormir` já esteja preenchido SHALL permanecer finalizado e não SHALL ter o horário substituído.

#### Scenario: Finalização bem-sucedida
- **WHEN** o ciclo aberto é válido, não há atividade em andamento e o MongoDB aceita o retrato
- **THEN** o sistema grava `fui_dormir`, persiste o ciclo e preserva todos os valores locais

#### Scenario: Dia já finalizado
- **WHEN** não existe ciclo aberto porque o relatório selecionado já possui `fui_dormir`
- **THEN** o comando falha sem substituir o horário existente e orienta o uso de `persistir dia` quando necessário

#### Scenario: Falha de gravação
- **WHEN** a serialização ou substituição do relatório falha
- **THEN** o arquivo anterior permanece inalterado e nenhuma persistência remota é tentada

#### Scenario: Falha de persistência remota
- **WHEN** o relatório foi finalizado localmente e o MongoDB recusa o retrato
- **THEN** o comando retorna erro e conserva o relatório finalizado para reenvio por `persistir dia`
