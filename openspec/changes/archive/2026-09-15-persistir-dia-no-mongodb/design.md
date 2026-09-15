## Context

O sistema usa YAMLs locais como estado operacional, possui um `RegistroDiario` nomeado pela data civil e arquiva atividades concluídas em um diretório comum. A integração MongoDB atual é somente leitura e procura o sono anterior em `registros_diarios`. O novo fluxo cruza esquemas gerados, gerenciamento de tarefas, ciclo do dia, CLI e uma escrita remota que não pode participar da transação atômica do arquivo local.

## Goals / Non-Goals

**Goals:**

- Tornar o ciclo aberto uma noção compartilhada e independente da virada da meia-noite.
- Produzir um retrato determinístico e completo por data e persistir por upsert.
- Permitir recuperação segura quando a gravação local termina e a remota falha.
- Deixar a lista de relatórios extensível a modelos registrados futuros.

**Non-Goals:**

- Excluir YAMLs após o envio.
- Sincronizar mudanças do MongoDB de volta aos arquivos locais.
- Persistir atividades em andamento ou pausas transitórias.
- Migrar uma estrutura MongoDB anterior, pois o cluster ainda não contém esses documentos.

## Decisions

### 1. Ciclo aberto descoberto pelos relatórios locais

Uma função compartilhada examinará `Relatórios/RD-*.yaml`, validará classe, correspondência entre nome e `data` e considerará aberto o `RegistroDiario` com `fui_dormir` nulo. Operações que exigem ciclo aberto aceitarão exatamente um resultado; zero ou múltiplos serão estados acionáveis. Essa função ficará em um módulo sem dependência do gerenciador de tarefas, evitando importação circular.

Alternativa considerada: manter um arquivo separado de estado do ciclo. Foi rejeitada por duplicar informação e criar risco de divergência com o relatório.

### 2. Vínculo `dia` persistido na atividade

`Tarefa` ganhará `dia: date | None`; o valor nulo permite carregar legado, mas comandos novos sempre preencherão a data do ciclo aberto. Como sessões herdam `Tarefa`, recebem o mesmo vínculo. Pausas continuam aninhadas e não duplicam o campo.

Alternativa considerada: inferir o ciclo de toda atividade por `inicio` ou `fim`. Foi rejeitada porque uma atividade pode cruzar a meia-noite sem encerrar o ciclo em que começou.

### 3. Um documento por ciclo na collection `dias`

O documento terá esta forma estável:

```yaml
versao: 1
data: '2026-09-15'
relatorios:
  - classe: RegistroDiario
    data: '2026-09-15'
    fui_dormir: '23:40'
atividades:
  - classe: SessaoEstudo
    dia: '2026-09-15'
    inicio: '2026-09-15T23:30:00-03:00'
    fim: '2026-09-16T00:30:00-03:00'
```

Relatórios e atividades serão ordenados por caminho local antes da conversão para manter testes e reenvios determinísticos. A montagem usará a conversão primitiva já adotada pelo YAML. Em `Relatórios`, qualquer modelo registrado com atributo `data` igual ao ciclo será incluído; arquivos incompatíveis interrompem o envio em vez de serem ignorados silenciosamente.

### 4. Índice único e substituição idempotente

Antes do upsert, a persistência garantirá `create_index("data", unique=True)`. Em seguida usará `replace_one({"data": data_iso}, documento, upsert=True)`. Isso permite repetir o envio e substitui o retrato remoto pelo estado local completo, evitando mesclar arrays antigos.

Alternativa considerada: documentos separados por arquivo e transação. Foi rejeitada por aumentar a chance de estado parcial, exigir mais índices e dificultar relatórios futuros.

### 5. Arquivo local antes da escrita remota

`finalizar dia` concluirá e substituirá o YAML antes de montar e enviar o retrato. Se o MongoDB falhar, retornará erro, mas não tentará desfazer `fui_dormir`. `persistir dia` permitirá reenvio por data; sem `--data`, escolherá o `RegistroDiario` finalizado de maior data. Uma nova execução de `finalizar dia` não alterará um ciclo já encerrado.

Alternativa considerada: escrever remotamente antes do arquivo. Foi rejeitada porque uma falha local posterior deixaria um ciclo remoto finalizado sem fonte local equivalente.

### 6. Migração local separada

Um utilitário explícito migrará atividades sem `dia`. Para cada arquivo, converterá `inicio` ao fuso configurado e procurará exatamente um `RegistroDiario` com a mesma data. Somente associações inequívocas serão gravadas atomicamente; qualquer ambiguidade preservará o arquivo e produzirá erro. O fluxo normal não inferirá silenciosamente vínculos ausentes.

## Risks / Trade-offs

- [Falha remota depois do sucesso local] → Manter o relatório finalizado e oferecer upsert repetível por `persistir dia`.
- [Dois ciclos abertos por edição manual] → Recusar operações dependentes e listar os arquivos conflitantes.
- [Atividade legada sem vínculo] → Exigir migração explícita e nunca atribuir durante o envio.
- [Documento diário crescer com muitas atividades] → Aceitar o agregado enquanto o volume diário permanecer muito abaixo do limite BSON; reavaliar particionamento apenas com evidência real.
- [Novo relatório sem atributo `data`] → Rejeitar como incompatível com a agregação e exigir que futuros esquemas de relatório adotem esse contrato.

## Migration Plan

1. Adicionar `dia` ao esquema de `Tarefa` e regenerar classes mantendo leitura de YAML legado.
2. Implementar descoberta do ciclo e exigir ciclo aberto em novas atividades.
3. Executar e verificar a migração local das atividades existentes antes do primeiro envio.
4. Implementar montagem, índice, upsert, comando de recuperação e integração com a finalização.
5. Validar no Atlas o primeiro documento agregado e a unicidade por data.

O rollback pode remover a integração automática e a exigência de ciclo aberto. O campo `dia` adicional continua legível nos modelos gerados desta versão; voltar a uma classe anterior exigiria remover o campo dos YAMLs migrados ou manter compatibilidade temporária no leitor.
