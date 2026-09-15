## Why

O projeto já persiste múltiplos relatórios por ciclo, mas somente o relatório diário possui modelo e comando de criação. Uma base comum e um comando explícito permitirão registrar notas datadas agora e adicionar novos tipos de relatório no futuro sem manter uma lista fechada de classes nas especificações.

## What Changes

- Introduzir a classe concreta `Relatorio`, com `data`, `nome` e `notas`, utilizável diretamente e como base de relatórios especializados.
- Fazer `RegistroDiario` herdar de `Relatorio`, preservando o comportamento específico do ciclo diário.
- Adicionar `criar relatorio NOME [--data YYYY-MM-DD]`, usando por padrão a data atual no fuso configurado e criando um YAML editável em `Relatórios` com `notas: null`.
- Definir nomes determinísticos e não sobrescritos para arquivos de relatórios genéricos.
- Tornar os contratos de esquemas, geração e serialização extensíveis, sem declarar uma quantidade exata de modelos.
- Integrar relatórios por tipo-base ao retrato diário persistido no MongoDB.

## Capabilities

### New Capabilities

- `gerenciamento-relatorios`: criação segura de relatórios genéricos datados pela CLI e armazenamento local em YAML.

### Modified Capabilities

- `esquemas-json`: introduz a classe-base concreta `Relatorio`, a herança de `RegistroDiario` e remove enumerações fechadas de quantidade de esquemas.
- `geracao-classes-python`: passa a verificar e expor a nova hierarquia de relatórios sem limitar o catálogo de modelos.
- `serializacao-yaml`: inclui relatórios genéricos e especializados no contrato polimórfico extensível.
- `persistencia-dia-mongodb`: seleciona relatórios pelo tipo-base `Relatorio`, preservando a exigência específica de um `RegistroDiario` finalizado por ciclo.

## Impact

Serão afetados os esquemas JSON, as classes Python geradas, o registro de modelos YAML, a CLI, a criação e nomeação de arquivos em `Relatórios`, a montagem do retrato diário e os testes correspondentes. YAMLs existentes de `RegistroDiario` permanecem compatíveis porque o discriminador e os campos atuais serão preservados.
