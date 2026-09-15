## Context

Os campos de horário de `RegistroDiario` usam `datetime.time`, e a serialização atual chama `isoformat()` sem considerar metadados, produzindo segundos. O mesmo serializador atende tarefas e pausas, cujos `datetime` e durações precisam manter a precisão atual. O histórico MongoDB também valida hoje somente `HH:MM:SS`.

## Goals / Non-Goals

**Goals:**

- Tornar `HH:MM` a representação canônica dos horários do relatório diário.
- Aplicar a regra por metadado do campo, evitando comportamento baseado no nome da classe ou do atributo.
- Ler relatórios e documentos MongoDB legados sem exigir migração antecipada.

**Non-Goals:**

- Alterar durações `HH:MM:SS`.
- Reduzir a precisão dos `datetime` de tarefas, sessões e pausas.
- Regravar em lote relatórios locais ou documentos MongoDB existentes.

## Decisions

### 1. Formato dirigido pelo esquema

Cada campo `time` de `registro-diario.json` receberá `unidade: "HH:MM"`, que o gerador já sabe transportar para os metadados da dataclass. A serialização consultará esse metadado. Isso evita uma exceção codificada para `RegistroDiario` e permite reutilizar a regra futuramente.

Alternativa considerada: serializar todo `time` como `HH:MM`. Foi rejeitada porque transformaria implicitamente qualquer novo campo `time`, mesmo quando segundos fossem relevantes.

### 2. Normalização na fronteira YAML

Ao serializar um campo marcado como `HH:MM`, será usada precisão de minutos. Ao desserializar, valores ISO válidos em `HH:MM`, `HH:MM:SS` ou com fração serão aceitos e normalizados para um `time` com segundo e microssegundo iguais a zero.

Alternativa considerada: preservar segundos internamente até a gravação. Foi rejeitada porque permitiria resultados diferentes entre o modelo em memória e sua representação persistida.

### 3. Truncamento, não arredondamento

Horários automáticos e legados terão segundos e microssegundos substituídos por zero. Um instante `23:41:59` corresponderá a `23:41`, pois o registro representa o minuto civil em que ocorreu, e não uma medição numérica a ser arredondada.

### 4. Mesmo contrato na fronteira MongoDB

A consulta do sono anterior aceitará o formato canônico e o legado e retornará um `time` normalizado. Novas persistências futuras deverão usar `HH:MM`, mas nenhuma escrita ou migração remota faz parte desta mudança.

## Risks / Trade-offs

- [Perda intencional da precisão legada] → Cobrir em testes que a normalização sempre trunca e documentar `HH:MM` como formato canônico.
- [Regressão em durações ou datetimes] → Manter a regra condicionada ao metadado `HH:MM` e executar toda a suíte existente.
- [Aceitação excessiva de ISO 8601] → Restringir explicitamente os formatos aceitos para horários do relatório e testar valores inválidos.

## Migration Plan

1. Atualizar o esquema e regenerar as classes.
2. Atualizar leitura e escrita YAML com compatibilidade legada.
3. Atualizar a consulta MongoDB e o preenchimento automático.
4. Validar relatórios novos e legados; não executar migração em lote.

O rollback restaura a serialização com segundos. Arquivos já normalizados continuam válidos em ISO 8601 e podem ser lidos pela versão anterior.
