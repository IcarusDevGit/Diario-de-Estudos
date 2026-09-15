## Why

Os segundos dos horários do relatório diário não acrescentam informação útil à análise e tornam o preenchimento manual mais detalhado do que o necessário. Uma representação canônica em `HH:MM` deixa os relatórios mais simples sem reduzir a precisão relevante.

## What Changes

- Declarar `HH:MM` como formato dos campos `time` de `RegistroDiario` nos esquemas JSON e nos metadados gerados.
- Serializar esses horários sempre com dois dígitos para hora e minuto, omitindo segundos.
- Aceitar na leitura tanto o novo formato `HH:MM` quanto o legado `HH:MM:SS`, descartando os segundos legados e normalizando a próxima gravação para `HH:MM`.
- Descartar segundos e microssegundos dos horários automáticos do relatório, sem arredondar para o minuto seguinte.
- Consultar e validar `fui_dormir` do MongoDB sob o mesmo contrato de compatibilidade.
- Manter inalterados os formatos de duração `HH:MM:SS` e os `datetime` usados por tarefas, sessões e pausas.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `esquemas-json`: definir o formato `HH:MM` nos campos de horário de `RegistroDiario`.
- `serializacao-yaml`: produzir a forma canônica `HH:MM` e controlar a compatibilidade de leitura dos horários do relatório.
- `gerenciamento-dia`: normalizar horários automáticos e históricos remotos para precisão de minuto.

## Impact

Afeta `Esquemas/registro-diario.json`, as classes geradas, a serialização YAML, o gerenciamento do dia, seus testes e o contrato de leitura do campo `fui_dormir` no MongoDB. A normalização remove a precisão de segundos dos horários legados; os demais modelos temporais permanecem inalterados.
