## Why

Os modelos e a serialização YAML já existem, mas ainda não há um fluxo de terminal que controle o ciclo de vida de tarefas, sessões e pausas. Esta mudança torna possível iniciar e finalizar essas atividades com horários consistentes, exclusividade de itens em andamento e movimentação segura dos arquivos.

## What Changes

- Adicionar comandos de terminal para iniciar uma tarefa genérica ou uma sessão de estudo/exercício, preenchendo `inicio` automaticamente no fuso definido por `FUSO_HORARIO` no `.env` da raiz do projeto.
- Persistir a atividade atual como YAML em `Tarefas/Tarefa em andamento`, mantendo no máximo uma tarefa ou sessão em andamento.
- Adicionar comandos para iniciar e finalizar uma pausa, mantendo no máximo uma pausa em andamento em `Tarefas/Pausas`.
- Ao finalizar uma pausa, calcular sua duração, incorporá-la à tarefa atual e remover o arquivo transitório da pausa.
- Ao finalizar uma tarefa ou sessão, encerrar primeiro eventual pausa ativa, calcular a duração líquida em `HH:MM:SS` e mover o YAML para `Tarefas/Concluidas`.
- Rejeitar estados inconsistentes, dados YAML inválidos e operações fora de ordem com mensagens acionáveis, preservando os arquivos anteriores em caso de falha.
- Manter o gerenciamento do dia, relatórios e integração com MongoDB fora deste escopo.

## Capabilities

### New Capabilities

- `gerenciamento-tarefas-pausas`: Ciclo de vida via terminal de tarefas, sessões e pausas persistidas em YAML, incluindo exclusividade, cálculos de duração, incorporação de pausas e arquivamento de tarefas concluídas.

### Modified Capabilities

Nenhuma. A serialização YAML existente será consumida sem alterar seu contrato.

## Impact

- Novo ponto de entrada de linha de comando e nova camada de serviço em `Python/`.
- Leitura e gravação nos diretórios `Tarefas/Tarefa em andamento`, `Tarefas/Pausas` e `Tarefas/Concluidas`.
- Reutilização das classes geradas e de `Python/serializacao_yaml.py`.
- Leitura de `FUSO_HORARIO` no `.env`, com `UTC-03:00` configurado nesta instância e um `.env.example` versionado.
- Uso da biblioteca padrão (`argparse`, `datetime`, `pathlib`) sem nova dependência externa prevista.
- Novos testes de unidade e integração para comandos, transições de estado, cálculos e recuperação diante de erros.
