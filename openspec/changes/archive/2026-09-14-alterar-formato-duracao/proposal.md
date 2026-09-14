## Why

Durações atualmente são persistidas como horas decimais, o que produz valores pouco legíveis como `0.003841129166666667`. Representá-las como `HH:MM:SS` torna o preenchimento e a conferência manual dos arquivos YAML imediatos e inequívocos.

## What Changes

- **BREAKING** Alterar `duracao` de `float` em horas decimais para `str` no formato `HH:MM:SS` nos modelos `Tarefa` e `Pausa`.
- Arredondar cada intervalo ao segundo inteiro mais próximo, usando meio segundo para cima.
- Permitir horas acumuladas acima de 23, mantendo ao menos dois dígitos para horas, minutos e segundos.
- Atualizar os esquemas JSON e regenerar as classes Python a partir deles.
- Adaptar o gerenciamento de tarefas e pausas para calcular, validar, somar e subtrair durações no novo formato.
- Migrar de forma explícita arquivos YAML existentes que ainda contenham duração numérica em horas, sem aceitar silenciosamente o formato legado na leitura comum.
- Preservar `null` para atividades e pausas ainda não finalizadas.

## Capabilities

### New Capabilities

- `formato-duracao`: Formatação, validação, aritmética e migração de durações textuais `HH:MM:SS`.

### Modified Capabilities

- `esquemas-json`: Alterar o contrato estrutural de `duracao` em `Tarefa` e `Pausa` de `float` em horas para `str` no formato `HH:MM:SS`.

## Impact

- Alterações em `Esquemas/tarefa.json` e `Esquemas/pausa.json`, seguidas da regeneração de `Python/Classes/geradas.py`.
- Novo utilitário de duração reutilizado pelo gerenciamento de tarefas e pausas.
- Atualização de `Python/gerenciamento_tarefas.py` e de seus testes.
- Migração do YAML já existente em `Tarefas/Concluidas` e suporte a execução segura da migração sobre outros arquivos legados.
- Arquivos YAML antigos com números em horas deixam de ser válidos para carregamento comum após a mudança e precisam passar pela migração.
- Nenhuma nova dependência externa prevista.
