## MODIFIED Requirements

### Requirement: Encerramento atômico do dia
Somente depois que todas as validações forem aprovadas, o sistema SHALL preencher `fui_dormir` com a hora e o minuto atuais no fuso configurado e substituir atomicamente o YAML do ciclo aberto. Depois da gravação local, SHALL tentar persistir o retrato no MongoDB. Após confirmação remota, SHALL concluir a limpeza local definida pela persistência do ciclo. Um relatório cujo `fui_dormir` já esteja preenchido SHALL permanecer finalizado e não SHALL ter o horário substituído.

#### Scenario: Finalização bem-sucedida
- **WHEN** o ciclo aberto é válido, não há atividade em andamento e o MongoDB aceita o retrato
- **THEN** o sistema grava `fui_dormir`, persiste o ciclo e remove os relatórios e atividades concluídas incluídos no retrato

#### Scenario: Dia já finalizado
- **WHEN** não existe ciclo aberto porque o relatório selecionado já possui `fui_dormir`
- **THEN** o comando falha sem substituir o horário existente e orienta o uso de `persistir dia` quando necessário

#### Scenario: Falha de gravação
- **WHEN** a serialização ou substituição do relatório finalizado falha
- **THEN** o arquivo anterior permanece inalterado e nenhuma persistência remota é tentada

#### Scenario: Falha de persistência remota
- **WHEN** o relatório foi finalizado localmente e o MongoDB recusa o retrato
- **THEN** o comando retorna erro e conserva todos os arquivos selecionados para reenvio por `persistir dia`

#### Scenario: Falha de limpeza depois da persistência
- **WHEN** o MongoDB aceita o retrato mas a limpeza local não termina
- **THEN** o comando retorna erro de limpeza sem desfazer a finalização nem a persistência confirmada

### Requirement: Resultado dos comandos de dia
Operações bem-sucedidas SHALL retornar código zero. `iniciar dia` SHALL informar o caminho do relatório criado, enquanto `finalizar dia` SHALL informar a data do ciclo persistido e limpo. Violações de precondição, configuração, integração ou limpeza SHALL retornar código diferente de zero com mensagem acionável.

#### Scenario: Comando de dia bem-sucedido
- **WHEN** `iniciar dia` completa a criação ou `finalizar dia` completa persistência e limpeza
- **THEN** a CLI retorna código zero e imprime, respectivamente, o caminho criado ou a data do ciclo

#### Scenario: Comando de dia recusado
- **WHEN** uma precondição do comando de dia não é atendida
- **THEN** a CLI retorna código diferente de zero e explica a causa sem exibir segredos
