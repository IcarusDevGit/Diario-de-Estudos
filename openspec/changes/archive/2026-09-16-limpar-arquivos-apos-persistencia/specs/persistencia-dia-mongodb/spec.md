## MODIFIED Requirements

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
