## Why

Os esquemas atuais usam valores textuais pouco estruturados para descrever tipos e não registram herança, obrigatoriedade, validações ou campos calculados. É necessário torná-los uma fonte de dados inequívoca para que classes Python possam ser geradas e validadas de forma previsível.

## What Changes

- Reestruturar os cinco arquivos em `Esquemas/` com metadados de classe e definições estruturadas de campos.
- Declarar `SessaoEstudo` e `SessaoExercicio` como especializações de `Tarefa`.
- Representar listas, referências a outras classes, campos opcionais, valores padrão, limites e campos calculados sem depender de texto livre.
- Usar `datetime` nos intervalos de tarefas e pausas, mantendo `date` e `time` nos dados de calendário e horários do registro diário.
- Definir avaliações subjetivas com valores inteiros entre 1 e 5.
- Padronizar nomes de classes Python sem acentos, preservando os nomes atuais dos arquivos JSON.

## Capabilities

### New Capabilities

- `esquemas-json`: Define o formato declarativo e validável dos esquemas usados como fonte para modelos Python do diário de estudos.

### Modified Capabilities

Nenhuma.

## Impact

- Afeta os cinco arquivos JSON em `Esquemas/`.
- Estabelece o contrato de entrada para um futuro gerador de classes Python.
- Não adiciona dependências externas nem implementa o gerador nesta mudança.
- A estrutura anterior dos esquemas deixa de ser compatível com consumidores que esperem pares diretos de `campo: tipo`.
