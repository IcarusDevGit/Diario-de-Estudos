## Context

O projeto já possui cinco dataclasses geradas a partir dos esquemas JSON e uma camada de serialização YAML segura e atômica. Ainda não existe uma camada de aplicação nem um ponto de entrada de terminal para coordenar os arquivos que representam tarefas e pausas em andamento. Consulte `proposal.md` para a motivação e a especificação `gerenciamento-tarefas-pausas` para o contrato observável.

Os diretórios operacionais já presentes no repositório são `Tarefas/Tarefa em andamento`, `Tarefas/Pausas` e `Tarefas/Concluidas`. Os campos `inicio` e `fim` de tarefas e pausas são `datetime`; `duracao` é calculado e armazenado como texto `HH:MM:SS` conforme a capability `formato-duracao`.

## Goals / Non-Goals

**Goals:**

- Separar regras de ciclo de vida e acesso ao sistema de arquivos da interface de terminal.
- Tornar as transições testáveis com relógio, raiz de dados e configuração de fuso injetáveis.
- Preservar arquivos existentes diante de validação, gravação ou movimentação malsucedida.
- Reutilizar os modelos gerados e o contrato YAML já existentes.

**Non-Goals:**

- Alterar arquivos gerados, esquemas JSON ou o formato YAML.
- Implementar início/fim do dia, relatórios, banco de dados ou MongoDB.
- Editar interativamente os campos do YAML pelo comando.
- Suportar execução concorrente por múltiplos processos nesta primeira parte.

## Decisions

### Camada de serviço independente da CLI

Criar um módulo de serviço com operações explícitas para iniciar/finalizar tarefa e iniciar/finalizar pausa. Ele receberá a raiz do projeto e uma função de relógio, enquanto um módulo CLI baseado em `argparse` apenas traduz argumentos, resultados e exceções em texto e códigos de saída.

Isso permite testes determinísticos e evita acoplar regras de domínio ao terminal. A alternativa de implementar tudo diretamente nos handlers da CLI reduziria arquivos inicialmente, mas dificultaria testar falhas e reutilizar as operações.

### Arquivos ativos com nomes estáveis

Usar um único nome conhecido, `tarefa.yaml`, no diretório de tarefa em andamento e `pausa.yaml` no diretório de pausas. Mesmo assim, a descoberta validará todos os arquivos `.yaml` e `.yml` presentes: zero, um ou múltiplos arquivos serão tratados conforme a operação e múltiplos indicarão inconsistência.

Nomes estáveis simplificam descoberta e diagnóstico. A alternativa de gerar nomes por título ou timestamp para itens ativos cria ambiguidade desnecessária, já que o domínio permite somente um de cada.

### Nome imutável e não conflitante para concluídas

O destino concluído será derivado do instante de início e da classe, em forma segura para Windows, com sufixo numérico incremental se já existir. O caminho escolhido será definido antes da alteração e nunca substituirá um arquivo concluído.

Foi descartado usar somente `nome`, pois ele pode estar nulo, conter caracteres inválidos ou repetir-se; também foi descartado sobrescrever pelo timestamp, pois isso poderia destruir histórico.

### Fuso configurado pelo `.env` e cálculo por linha do tempo

A raiz do projeto conterá um `.env` local com `FUSO_HORARIO=UTC-03:00` e um `.env.example` versionado com a mesma chave. A camada de serviço lerá especificamente essa variável, sem importar automaticamente outras entradas para o ambiente do processo. Um parser restrito aceitará `UTC+HH:MM` e `UTC-HH:MM`, validará os limites de deslocamento suportados por `datetime.timezone` e produzirá um `timezone` de deslocamento fixo. Configuração ausente, duplicada ou inválida impedirá a operação antes da leitura ou escrita do estado.

O relógio padrão produzirá `datetime.now(fuso_configurado)`. Para calcular intervalos, os instantes serão normalizados pela linha do tempo UTC antes da subtração. A duração de cada pausa será formatada pelo utilitário compartilhado; a duração líquida da tarefa subtrairá os intervalos exatos das pausas e será arredondada uma única vez ao segundo antes da formatação `HH:MM:SS`.

Essa abordagem funciona no Windows sem banco IANA nem dependências como `tzdata` ou `python-dotenv`, e corresponde à decisão desta instância de usar um deslocamento fixo. A alternativa `ZoneInfo("America/Sao_Paulo")` preservaria regras históricas e futuras de horário legal, mas dependeria de dados de fuso que não estão disponíveis no ambiente atual.

### Transições em duas fases com compensação

Cada operação primeiro descobrirá e carregará todos os arquivos necessários, validará classes, campos temporais e cálculos, e preparará os novos conteúdos. Só depois iniciará as gravações. A gravação individual reutilizará `salvar_yaml`, que já faz substituição atômica.

Nas operações com múltiplos arquivos, o serviço manterá os bytes originais até concluir a transição. Se uma etapa posterior falhar, restaurará os arquivos já alterados por substituição atômica antes de reportar o erro. A remoção do arquivo de pausa e do arquivo ativo ocorrerá por último. Uma transação de banco de dados seria mais forte, porém contraria a persistência local e editável desta etapa.

### Pausa finalizada é parte da tarefa

O arquivo de pausa representa apenas o estado transitório. Após o encerramento, a instância completa de `Pausa` será anexada à lista da tarefa e o arquivo separado será excluído. Finalizar tarefa chamará a mesma transição de finalização de pausa quando necessário, evitando regras duplicadas.

## Risks / Trade-offs

- [Dois processos podem passar pela verificação de exclusividade ao mesmo tempo] → Documentar execução de processo único nesta parte e estruturar o serviço para permitir lock de arquivos posteriormente.
- [Falha extrema durante a janela entre duas substituições pode deixar arquivos divergentes] → Ordenar alterações para manter o arquivo de pausa até a tarefa estar persistida, usar substituições atômicas e executar recuperação na próxima operação quando o estado for diagnosticável.
- [YAML editado manualmente pode remover dados essenciais] → Validar classe e campos necessários à operação antes de qualquer escrita, apontando arquivo e campo inválido.
- [Nomes de diretório contêm espaços e acentos] → Construir caminhos com `pathlib.Path` e nunca interpretar caminhos por concatenação de comandos de shell.
- [Arquivos `.yml` adicionais podem surpreender a descoberta] → Tratar ambas as extensões como estado operacional deliberadamente e rejeitar multiplicidade em vez de ignorar conteúdo.
- [Um deslocamento fixo não acompanha futuras mudanças legais de fuso] → Manter o valor explícito no `.env`; uma futura migração para identificadores IANA poderá substituir apenas o resolvedor de configuração.

## Migration Plan

1. Adicionar `.env.example` e configurar o `.env` local com `FUSO_HORARIO=UTC-03:00`.
2. Adicionar a camada de serviço e seus testes sem alterar os arquivos existentes.
3. Adicionar a CLI e testes de integração em raiz temporária.
4. Validar compatibilidade com YAMLs produzidos pela serialização atual.
5. Disponibilizar os comandos; os diretórios vazios existentes não exigem migração.

Para rollback, remover os novos módulos de serviço/CLI. Como o formato persistido continua sendo o YAML existente, arquivos válidos criados por esta mudança permanecem legíveis pela camada de serialização atual.
