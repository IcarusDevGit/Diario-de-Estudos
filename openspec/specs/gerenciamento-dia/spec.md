# Gerenciamento do Dia Specification

## Purpose

Permitir iniciar, preencher manualmente e finalizar com segurança o registro diário local, aproveitando o horário de sono do dia anterior armazenado no MongoDB.

## Requirements

### Requirement: Início do registro diário
O sistema SHALL oferecer `iniciar dia` para criar um YAML de `RegistroDiario` no diretório `Relatórios`, nomeado pela data civil atual como `RD-YYYY-MM-DD.yaml`. O prefixo `RD-` SHALL identificar o arquivo como relatório diário. O campo `data` SHALL receber a data atual no fuso configurado, enquanto campos ainda não informados SHALL conservar `null` ou o padrão do modelo.

#### Scenario: Iniciar o dia
- **WHEN** o usuário inicia o dia e ainda não existe relatório para a data atual
- **THEN** o sistema cria o YAML correspondente com `data` preenchida e campos manuais ainda desconhecidos representados como `null`

#### Scenario: Relatório atual já existe
- **WHEN** o usuário inicia o dia e o arquivo da data atual já existe
- **THEN** o comando falha sem sobrescrever nem alterar o relatório existente

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

### Requirement: Falha remota preserva o estado local
Falhas de configuração, seleção de servidor, autenticação ou consulta MongoDB SHALL interromper `iniciar dia` com mensagem acionável e sanitizada. Nenhuma dessas falhas SHALL criar ou alterar um relatório local, e a mensagem MUST NOT revelar a URI nem suas credenciais.

#### Scenario: Consulta MongoDB falha
- **WHEN** a consulta ao registro anterior falha por configuração, rede, autenticação ou erro do servidor
- **THEN** o comando retorna erro sanitizado, fecha o cliente criado e deixa `Relatórios` sem o novo arquivo

### Requirement: Validação anterior à finalização
O sistema SHALL oferecer `finalizar dia` e, antes de qualquer alteração, carregar o arquivo `Relatórios/RD-YYYY-MM-DD.yaml` da data atual como `RegistroDiario`, confirmar que seu campo `data` corresponde ao dia atual e validar que todos os campos com metadado `opcional: false` estejam preenchidos. Nesta capability, somente `RegistroDiario` SHALL ser considerado relatório necessário.

#### Scenario: Campos obrigatórios ausentes
- **WHEN** um ou mais campos obrigatórios do registro atual permanecem `null`
- **THEN** o comando falha listando os nomes dos campos ausentes e preserva o arquivo byte a byte

#### Scenario: Relatório ausente ou incompatível
- **WHEN** o arquivo da data atual não existe, é inválido, declara outra classe ou contém outra data
- **THEN** o comando falha identificando o arquivo ou a precondição sem criar nem modificar relatório

### Requirement: Ausência de atividade em andamento
O sistema SHALL recusar `finalizar dia` quando existir qualquer tarefa ou sessão em andamento. Estado inconsistente ou YAML inválido no diretório de atividade em andamento SHALL também impedir a finalização, sem modificar o relatório diário.

#### Scenario: Atividade ainda em andamento
- **WHEN** existe uma tarefa ou sessão ativa ao finalizar o dia
- **THEN** o comando falha identificando a atividade e preserva o relatório diário

#### Scenario: Diretório de atividade inconsistente
- **WHEN** o diretório de atividade em andamento contém múltiplos YAMLs ou um YAML inválido
- **THEN** o comando falha descrevendo a inconsistência e preserva o relatório diário

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

### Requirement: Resultado dos comandos de dia
Operações bem-sucedidas SHALL retornar código zero e informar o caminho do relatório afetado. Violações de precondição, configuração ou integração SHALL retornar código diferente de zero com mensagem acionável.

#### Scenario: Comando de dia bem-sucedido
- **WHEN** `iniciar dia` ou `finalizar dia` completa a transição solicitada
- **THEN** a CLI retorna código zero e imprime o caminho do relatório

#### Scenario: Comando de dia recusado
- **WHEN** uma precondição do comando de dia não é atendida
- **THEN** a CLI retorna código diferente de zero e explica a causa sem exibir segredos
