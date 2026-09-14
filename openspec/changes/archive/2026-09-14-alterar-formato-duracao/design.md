## Context

Os esquemas de `Tarefa` e `Pausa` definem `duracao` como `float` com unidade `horas`; as classes geradas, o gerenciamento recém-implementado e seus testes seguem esse contrato. Existe ao menos um YAML concluído com durações decimais. Consulte `proposal.md` para a motivação e as duas delta specs para o novo comportamento.

## Goals / Non-Goals

**Goals:**

- Ter uma representação humana canônica sem perder suporte a durações acima de 24 horas.
- Centralizar formatação, análise, validação e aritmética de duração.
- Migrar dados legados de maneira explícita, repetível e segura.
- Manter esquemas, classes geradas, gerenciamento e artefatos OpenSpec coerentes.

**Non-Goals:**

- Aceitar múltiplos formatos de duração na operação normal.
- Preservar precisão inferior a um segundo.
- Alterar a representação de `inicio` ou `fim`.
- Inferir se um número legado estava em outra unidade que não horas.

## Decisions

### Texto canônico com horas não limitadas

`duracao` será `str | None` e usará `HH:MM:SS`: horas com no mínimo dois dígitos e sem limite artificial, minutos e segundos de `00` a `59`. Isso evita a limitação de 24 horas de um horário civil e é mais legível no YAML que horas decimais.

Foi descartado usar `datetime.time`, pois ele representa horário do dia e limita horas a 23. Também foi descartado manter segundos como número, pois não atende à legibilidade solicitada.

### Aritmética interna em microssegundos inteiros

Os intervalos entre datetimes serão obtidos como `timedelta`. A implementação trabalhará com microssegundos inteiros e aplicará arredondamento half-up: somar 500.000 microssegundos e usar divisão inteira por 1.000.000 para intervalos não negativos. Assim, `13,5` e `13,828065` tornam-se 14 segundos sem o arredondamento bancário de `round` nem imprecisão intermediária de ponto flutuante.

A tarefa líquida subtrairá os intervalos exatos das pausas do intervalo exato total e só então arredondará uma vez. Cada pausa será formatada separadamente a partir de seus próprios instantes. A validação comparará os textos armazenados com os valores canônicos recalculados dos timestamps.

### Esquemas como fonte da alteração de tipo

Os dois esquemas trocarão `tipo: float` por `tipo: str` e `unidade: horas` por `unidade: HH:MM:SS`. O gerador existente produzirá novamente as classes, evitando edição manual de `geradas.py`. Os testes de geração confirmarão tipo, metadado e determinismo.

### Migração separada da leitura comum

Um script dedicado analisará YAML seguro sem depender da nova dataclass, pois o carregador normal passará a rejeitar números onde espera texto. Ele percorrerá recursivamente apenas estruturas de modelos registrados, converterá campos `duracao` numéricos não negativos como horas decimais e validará textos já presentes como canônicos.

O cálculo legado usará `Decimal(str(valor)) * 3600` e arredondamento `ROUND_HALF_UP`. Isso evita ampliar erros binários do `float`. A migração será idempotente e terá `--check`; a execução padrão selecionará os YAMLs dos diretórios operacionais, aceitando também caminhos explícitos.

### Substituição atômica por arquivo

Cada arquivo será carregado por completo, convertido em memória, emitido em YAML determinístico e validado antes de uma substituição atômica no mesmo diretório. Um erro em um arquivo preservará seus bytes. A migração não promete transação conjunta entre vários arquivos; processará e reportará cada arquivo de forma independente para permitir correção e nova execução.

### Coordenação com a mudança de gerenciamento ativa

A aplicação atualizará o serviço e os testes de `gerenciar-tarefas-e-pausas` para o novo utilitário, e reconciliará seus artefatos ainda ativos substituindo referências a horas decimais por `HH:MM:SS`. A mudança de formato deverá ser aplicada antes que a mudança de gerenciamento seja arquivada.

## Risks / Trade-offs

- [Perda intencional de frações de segundo] → Aplicar uma regra única, documentada e testada de arredondamento half-up.
- [YAML legado deixa de carregar após regenerar as classes] → Entregar e executar a migração no mesmo conjunto de alterações antes de usar os comandos normalmente.
- [Texto permite valores sintaticamente inválidos na dataclass] → Centralizar validação no utilitário e exercê-la nas operações que consomem duração; a serialização continua estrita quanto ao tipo.
- [Migração parcial entre vários arquivos] → Reportar resultados por arquivo, manter cada substituição atômica e tornar a operação idempotente.
- [Conflito com a mudança ativa de gerenciamento] → Atualizar seus artefatos, código e testes antes da validação final das duas mudanças.

## Migration Plan

1. Criar e testar o utilitário de duração e o migrador sem alterar ainda os esquemas.
2. Executar o migrador em modo `--check` e registrar os arquivos legados encontrados.
3. Migrar os YAMLs existentes e verificar que uma segunda execução não produz alterações.
4. Alterar os esquemas, regenerar as classes e adaptar o gerenciamento/testes.
5. Reconciliar e validar estritamente as duas mudanças OpenSpec.
6. Executar toda a suíte de testes e o verificador de classes geradas.

Em rollback, restaurar esquemas, classes e código anteriores e converter textos `HH:MM:SS` de volta para horas decimais somente se ainda for necessário consumir os YAMLs com a versão antiga.
