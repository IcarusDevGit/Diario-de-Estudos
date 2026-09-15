## 1. Esquema e classes geradas

- [x] 1.1 Adicionar `unidade: "HH:MM"` a todos os campos `time` de `Esquemas/registro-diario.json` e verificar em teste que o esquema declara o formato sem alterar `date`, `datetime` ou durações.
- [x] 1.2 Regenerar as classes Python e verificar que os campos de horário de `RegistroDiario` possuem o metadado `HH:MM`, enquanto durações continuam com `HH:MM:SS`.

## 2. Serialização YAML

- [x] 2.1 Tornar a conversão temporal sensível ao metadado do campo e verificar que `time` marcado como `HH:MM` é gravado com hora e minuto, truncando segundos e microssegundos sem arredondar.
- [x] 2.2 Aceitar `HH:MM`, `HH:MM:SS` e frações de segundo válidas na leitura dos campos marcados, normalizar o modelo para precisão de minuto e verificar rejeição de formatos inválidos com o caminho do campo.
- [x] 2.3 Verificar ida e volta determinística no formato canônico e confirmar em testes que datas, datetimes e durações mantêm o comportamento e a precisão existentes.

## 3. Gerenciamento do dia e MongoDB

- [x] 3.1 Atualizar a conversão de `fui_dormir` remoto para aceitar `HH:MM` e formatos legados com segundos, verificando truncamento ao minuto, valores inválidos, duplicidade e encerramento do cliente.
- [x] 3.2 Atualizar `finalizar dia` para zerar segundos e microssegundos antes da gravação e verificar que um instante como `23:41:59.999999` resulta em `fui_dormir: '23:41'` sem alterar os demais campos.
- [x] 3.3 Executar fluxos da CLI em diretório temporário e verificar que início com histórico novo ou legado e finalização produzem exclusivamente horários `HH:MM` no relatório.

## 4. Verificação final

- [x] 4.1 Executar o verificador de classes geradas e toda a suíte automatizada, confirmando ausência de regressões em tarefas, pausas, durações e gerenciamento do dia.
- [x] 4.2 Executar a validação estrita do change OpenSpec e verificar que os contratos de esquema, YAML e gerenciamento do dia permanecem coerentes.


