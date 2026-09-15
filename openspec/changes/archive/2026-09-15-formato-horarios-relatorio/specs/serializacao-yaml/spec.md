## MODIFIED Requirements

### Requirement: Conversão de tipos escalares
O sistema SHALL validar e converter valores conforme as anotações e os metadados dos modelos. `date`, `time` e `datetime` SHALL usar textos ISO 8601; campos `time` com unidade/formato `HH:MM` SHALL ser gravados canonicamente com hora e minuto e sem segundos. Na leitura desses campos, `HH:MM` e o formato legado `HH:MM:SS` SHALL ser aceitos, descartando segundos e frações legados. Um `datetime` com deslocamento SHALL preservar esse deslocamento na ida e volta. Booleanos e números SHALL exigir seus tipos YAML correspondentes, sem coerção silenciosa a partir de textos.

#### Scenario: Valores temporais em ida e volta
- **WHEN** um modelo com data, hora e datetime com deslocamento é serializado e carregado novamente
- **THEN** a data e o datetime são preservados e o horário com formato `HH:MM` é preservado com precisão de minuto

#### Scenario: Horário canônico do relatório
- **WHEN** um campo de horário do relatório contém segundos ou microssegundos
- **THEN** sua representação YAML contém somente `HH:MM`, descartando a precisão inferior a minuto sem arredondar

#### Scenario: Horário legado do relatório
- **WHEN** um campo de horário do relatório é lido como `HH:MM:SS` ou com fração de segundo válida
- **THEN** o modelo conserva hora e minuto e uma nova serialização produz `HH:MM`

#### Scenario: Inteiro representado como texto
- **WHEN** um campo inteiro contém o texto `"4"` no YAML
- **THEN** a leitura falha com o caminho do campo em vez de convertê-lo implicitamente

