## Why

Os arquivos locais de ciclos já consolidados permanecem indefinidamente em `Relatórios` e `Tarefas/Concluidas`, duplicando dados cujo destino definitivo é o MongoDB. A limpeza após confirmação remota encerra o ciclo de vida local e evita acúmulo, sem sacrificar a recuperação em caso de falha no envio.

## What Changes

- **BREAKING**: após um upsert confirmado no MongoDB, remover os relatórios e as atividades concluídas que compuseram exatamente o retrato persistido.
- Aplicar a mesma limpeza tanto à persistência automática de `finalizar dia` quanto ao comando manual `persistir dia`, inclusive quando este recupera uma finalização cujo envio anterior falhou.
- Preservar todos os arquivos locais quando a validação, configuração, conexão, índice ou escrita remota falhar.
- Nunca remover atividades em andamento, pausas transitórias, arquivos de outras datas nem diretórios de armazenamento.
- Rastrear os caminhos junto com o retrato para que a limpeza opere sobre a seleção validada, sem refazer a descoberta depois do upsert.
- Informar falhas de limpeza local após persistência remota, identificando os arquivos que permaneceram para permitir uma nova tentativa segura.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `persistencia-dia-mongodb`: substituir a preservação após sucesso por limpeza dos arquivos selecionados, mantendo a preservação integral antes da confirmação remota e definindo o comportamento de falha parcial da limpeza.
- `gerenciamento-dia`: ajustar o resultado de `finalizar dia` para refletir que o relatório finalizado é removido localmente após a persistência automática bem-sucedida.

## Impact

- Montagem e persistência do retrato em `Python/persistencia_dia.py`.
- Orquestração e retorno da finalização em `Python/gerenciamento_dia.py` e `Python/cli.py`.
- Testes de persistência, finalização e CLI.
- O MongoDB passa a ser a fonte definitiva de ciclos persistidos; após a limpeza, um novo `persistir dia --data` não poderá reconstruir esse ciclo a partir do armazenamento local.
- Nenhuma dependência externa nova é necessária.
