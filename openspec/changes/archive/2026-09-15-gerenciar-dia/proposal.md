## Why

O modelo `RegistroDiario` já pode ser gerado e serializado, mas os comandos `iniciar dia` e `finalizar dia` descritos no desenho do projeto ainda não existem. Sem esse ciclo de vida, o relatório precisa ser criado, validado e encerrado manualmente, e não aproveita o horário de sono registrado no dia anterior.

## What Changes

- Adicionar `iniciar dia` para criar o relatório YAML da data civil atual no fuso configurado.
- Identificar cada relatório diário pelo campo `data`, que SHALL ser único, e usar o nome local `RD-YYYY-MM-DD.yaml` para distinguir esse tipo de relatório.
- Consultar `fui_dormir` do registro anterior na database `diario_estudos`, collection `registros_diarios`, e preencher `dormi_dia_anterior` quando o documento existir.
- Tratar database, collection ou documento anterior inexistente como ausência normal de histórico, mantendo `dormi_dia_anterior: null`.
- Interromper o início sem criar arquivo quando houver falha de configuração, conexão, autenticação, consulta ou conteúdo remoto inválido.
- Adicionar `finalizar dia` para validar o relatório atual e recusar o encerramento enquanto houver tarefa ou sessão ativa.
- Preencher `fui_dormir` com a hora local atual e salvar atomicamente somente depois de todas as validações passarem.
- Manter fora do escopo qualquer escrita no MongoDB e o gerenciamento dos relatórios adicionais previstos para o futuro.

## Capabilities

### New Capabilities

- `gerenciamento-dia`: Ciclo local de início e finalização do registro diário, incluindo consulta somente de leitura ao histórico MongoDB.

### Modified Capabilities

- `configuracao-mongodb`: Adicionar configuração explícita e validada da database usada pela aplicação.

## Impact

- A CLI recebe os comandos `iniciar dia` e `finalizar dia`.
- Um novo serviço coordena `RegistroDiario`, o diretório `Relatórios`, o relógio/fuso, a verificação de atividade em andamento e a consulta remota.
- `.env.example` passa a documentar `MONGODB_DATABASE=diario_estudos`.
- A camada MongoDB passa a disponibilizar acesso à database configurada e à collection fixa `registros_diarios` sem realizar escritas; a criação futura de um índice único em `data` ficará para a persistência.
- Testes novos cobrem o fluxo com clientes simulados; a suíte automatizada não depende da rede nem do cluster real.
