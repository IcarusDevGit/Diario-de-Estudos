# Persistência do Dia no MongoDB Specification

## Purpose

Persistir no MongoDB um retrato completo, recuperável e idempotente de cada ciclo diário, reunindo os relatórios e atividades locais relacionados.

## Requirements

### Requirement: Documento agregado do ciclo
O sistema SHALL representar cada ciclo como um documento com `versao`, `data`, `relatorios` e `atividades`. `relatorios` SHALL conter todo YAML válido do diretório `Relatórios` cujo modelo seja `Relatorio` ou uma especialização e possua `data` igual à data do ciclo. `atividades` SHALL conter toda `Tarefa`, `SessaoEstudo` ou `SessaoExercicio` concluída cujo campo `dia` seja igual àquela data. Pausas SHALL permanecer aninhadas em sua atividade, e valores ausentes SHALL permanecer `null`.

#### Scenario: Retrato completo
- **WHEN** um ciclo possui relatório diário, relatório genérico e duas atividades concluídas associadas
- **THEN** o documento contém os dois relatórios e as duas atividades com classes concretas, campos e pausas preservados

#### Scenario: Futuro tipo de relatório
- **WHEN** um novo modelo derivado de `Relatorio` possui YAML válido em `Relatórios`
- **THEN** ele pode integrar `relatorios` sem alterar a estrutura do documento do ciclo

#### Scenario: Modelo datado que não é relatório
- **WHEN** um modelo registrado possui campo `data`, mas não deriva de `Relatorio`
- **THEN** ele não é incluído em `relatorios`

### Requirement: Validação integral antes do envio
Antes de acessar a rede, o sistema SHALL carregar e validar todos os arquivos selecionados, exigir um `RegistroDiario` finalizado para a data e rejeitar YAML inválido, classe incompatível, data divergente, atividade incompleta ou atividade sem associação inequívoca. Uma falha local SHALL impedir qualquer escrita MongoDB.

#### Scenario: Atividade incompleta
- **WHEN** uma atividade selecionada não possui `fim` ou `duracao`
- **THEN** a persistência falha identificando o arquivo sem acessar o MongoDB

#### Scenario: Relatório diário não finalizado
- **WHEN** `fui_dormir` permanece `null` no `RegistroDiario` selecionado
- **THEN** o envio é recusado sem operação remota

### Requirement: Upsert idempotente e unicidade
O sistema SHALL persistir o retrato na collection `dias` da database configurada por substituição com upsert filtrada por `data`. A collection SHALL possuir índice único em `data`, e repetir o envio da mesma data SHALL atualizar o documento existente sem criar duplicidade.

#### Scenario: Primeiro envio
- **WHEN** ainda não existe documento para a data
- **THEN** o sistema garante o índice único e cria exatamente um documento

#### Scenario: Reenvio do ciclo
- **WHEN** já existe documento para a data
- **THEN** o sistema substitui seu retrato pelo estado local atual e mantém um único documento

### Requirement: Persistência automática e recuperação
Depois de salvar localmente uma finalização válida, `finalizar dia` SHALL tentar persistir o ciclo automaticamente e, após confirmação remota, concluir a limpeza dos arquivos selecionados. O sistema SHALL também oferecer `persistir dia` com `--data YYYY-MM-DD` opcional; quando omitida, SHALL selecionar o ciclo finalizado local com data mais recente. A persistência manual bem-sucedida SHALL executar a mesma limpeza e SHALL retomar uma limpeza pendente da data sem substituir o documento remoto por um retrato local parcial.

#### Scenario: Finalização envia o ciclo
- **WHEN** a finalização local, a persistência remota e a limpeza terminam com sucesso
- **THEN** a CLI retorna sucesso, informa a data persistida e os arquivos selecionados não permanecem no armazenamento local

#### Scenario: Recuperação sem data explícita
- **WHEN** o usuário executa `persistir dia` e existem ciclos locais finalizados
- **THEN** o ciclo de data mais recente é enviado idempotentemente e seus arquivos selecionados são removidos após confirmação

#### Scenario: Recuperação com data
- **WHEN** o usuário executa `persistir dia --data 2026-09-15`
- **THEN** somente o ciclo local daquela data é selecionado para envio e limpeza

#### Scenario: Retomada de limpeza pendente
- **WHEN** uma tentativa anterior confirmou o upsert mas não removeu todos os arquivos selecionados
- **THEN** uma nova persistência da data retoma somente a limpeza registrada, sem reconstruir nem substituir o documento remoto com os arquivos restantes

### Requirement: Falha remota preserva dados locais
Falhas de configuração, índice, autenticação, conexão ou escrita SHALL produzir erro acionável e sanitizado, fechar o cliente criado e MUST NOT apagar, mover ou reverter arquivos locais. Se a falha ocorrer após `finalizar dia`, o relatório SHALL permanecer finalizado e apto a reenvio.

#### Scenario: MongoDB falha após finalização local
- **WHEN** o YAML finalizado foi salvo e a escrita remota falha
- **THEN** o comando retorna erro sem revelar credenciais e todos os arquivos selecionados permanecem em seus locais, incluindo o relatório com `fui_dormir`

#### Scenario: Falha fecha cliente
- **WHEN** qualquer operação remota falha depois da criação do cliente
- **THEN** o cliente é fechado antes de o erro ser retornado

### Requirement: Preservação dos arquivos locais
Antes da confirmação do upsert, o sistema SHALL manter inalterados todos os relatórios e atividades concluídas selecionados. Depois da confirmação, SHALL remover exatamente esses arquivos e preservar arquivos de outras datas, atividades em andamento, pausas transitórias e os diretórios de armazenamento. A seleção de caminhos SHALL ser a mesma usada para montar o documento, sem nova descoberta entre envio e limpeza. Uma falha de limpeza SHALL ser reportada com os caminhos remanescentes e SHALL conservar estado suficiente para retomar a limpeza sem reenviar um retrato parcial.

#### Scenario: Envio bem-sucedido
- **WHEN** o upsert termina com sucesso e todos os arquivos selecionados podem ser removidos
- **THEN** somente esses arquivos deixam de existir e os diretórios e arquivos não selecionados permanecem inalterados

#### Scenario: Arquivos criados depois da seleção
- **WHEN** um novo arquivo local aparece depois da montagem do retrato e antes da limpeza
- **THEN** ele não é removido porque não pertence à seleção que originou o documento persistido

#### Scenario: Falha durante a limpeza
- **WHEN** o upsert foi confirmado mas um ou mais arquivos selecionados não podem ser removidos
- **THEN** o comando retorna erro identificando os caminhos remanescentes e registra a limpeza pendente para retomada segura

#### Scenario: Falha anterior à confirmação
- **WHEN** qualquer etapa falha antes de o MongoDB confirmar o upsert
- **THEN** nenhum arquivo selecionado é removido ou movido

### Requirement: Migração explícita de atividades legadas
O sistema SHALL oferecer uma migração local para preencher `dia` em atividades legadas sem esse campo somente quando existir exatamente um relatório diário cuja data civil corresponda à data local de `inicio`. A migração SHALL recusar associações ausentes ou ambíguas e SHALL salvar cada arquivo atomicamente.

#### Scenario: Associação legada inequívoca
- **WHEN** uma atividade sem `dia` começou em data que possui exatamente um `RegistroDiario`
- **THEN** a migração preenche essa data em `dia` preservando os demais campos

#### Scenario: Associação ambígua
- **WHEN** não é possível determinar exatamente um ciclo pela data local de `inicio`
- **THEN** o arquivo permanece inalterado e a migração informa que exige correção manual
