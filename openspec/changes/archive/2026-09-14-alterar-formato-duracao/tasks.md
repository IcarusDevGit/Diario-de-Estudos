## 1. Utilitário de duração

- [x] 1.1 Criar funções para validar e converter `HH:MM:SS` em segundos inteiros, verificando horas acima de 23 e rejeição de horas curtas, minutos/segundos fora do limite, sinais e frações.
- [x] 1.2 Criar formatação de segundos inteiros e intervalos temporais para `HH:MM:SS`, verificando preenchimento com zeros, horas não limitadas e rejeição de valores negativos.
- [x] 1.3 Implementar arredondamento half-up por microssegundos inteiros, verificando explicitamente `13,4 → 00:00:13`, `13,5 → 00:00:14` e `13,828065 → 00:00:14`.

## 2. Migração do legado

- [x] 2.1 Implementar leitura segura e percurso restrito dos modelos YAML para localizar durações numéricas legadas, verificando caminhos de campos aninhados e rejeição de tags, estruturas, valores negativos e textos não canônicos.
- [x] 2.2 Implementar conversão de horas decimais com `Decimal` e `ROUND_HALF_UP`, verificando o exemplo legado `0.003841129166666667 → 00:00:14` sem imprecisão binária adicional.
- [x] 2.3 Implementar modo `--check`, seleção padrão dos diretórios operacionais e seleção por caminhos explícitos, verificando códigos de saída, relatórios por arquivo e ausência de escrita no modo de verificação.
- [x] 2.4 Implementar substituição atômica e idempotência por arquivo, verificando preservação byte a byte diante de falha e nenhuma alteração em uma segunda execução.
- [x] 2.5 Executar `--check` sobre os dados reais, migrar os YAMLs legados encontrados e verificar que nova execução de `--check` não encontra pendências.

## 3. Esquemas e classes geradas

- [x] 3.1 Alterar `duracao` em `tarefa.json` e `pausa.json` para `tipo: str` e `unidade: HH:MM:SS`, verificando sintaxe JSON e metadados dos dois campos.
- [x] 3.2 Regenerar `Python/Classes/geradas.py` pelo gerador existente e verificar que ambas as durações são `str | None`, calculadas e não aceitas na inicialização.
- [x] 3.3 Atualizar testes de esquemas, geração e serialização para o novo tipo, verificando round-trip de `null`, `00:00:14` e duração acima de 24 horas, além da rejeição de números legados.

## 4. Integração com gerenciamento

- [x] 4.1 Substituir cálculos em horas decimais pelo utilitário de duração no encerramento de pausas, verificando arredondamento e validação contra os timestamps.
- [x] 4.2 Calcular a duração líquida da tarefa com os intervalos temporais exatos das pausas antes de arredondar, verificando pausas fracionárias, virada de meia-noite e duração negativa.
- [x] 4.3 Atualizar todos os testes do gerenciamento e da CLI para `HH:MM:SS`, verificando tarefas sem pausa, pausas sequenciais, finalização durante pausa e preservação transacional.
- [x] 4.4 Reconciliar os artefatos ainda ativos de `gerenciar-tarefas-e-pausas` com o novo formato e verificar que não restam referências normativas a horas decimais.

## 5. Verificação final

- [x] 5.1 Executar o verificador determinístico das classes geradas e toda a suíte Python, confirmando ausência de regressões.
- [x] 5.2 Validar estritamente `alterar-formato-duracao` e `gerenciar-tarefas-e-pausas`, verificando que todas as tarefas aplicáveis estejam concluídas e os contratos sejam coerentes.
