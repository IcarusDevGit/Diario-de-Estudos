## 1. Vínculo de atividades e ciclo compartilhado

- [x] 1.1 Adicionar `dia: date | None` ao esquema de `Tarefa`, regenerar as classes e verificar que tarefas e sessões herdam o campo enquanto YAMLs legados sem `dia` continuam carregáveis.
- [x] 1.2 Implementar uma consulta compartilhada dos `RegistroDiario` locais que valide nome, classe e data e identifique ciclos abertos e finalizados, verificando estados vazio, único, múltiplo e YAML inválido.
- [x] 1.3 Alterar `iniciar dia` para recusar qualquer ciclo anterior aberto antes da consulta MongoDB, verificando preservação dos arquivos e ausência de chamada remota.
- [x] 1.4 Exigir exatamente um ciclo aberto ao iniciar tarefa ou sessão e preencher `dia` com a data do ciclo, verificando atividade sem ciclo, ciclo inconsistente e atividade que cruza a meia-noite.
- [x] 1.5 Adaptar `finalizar dia` para operar sobre o único ciclo aberto independentemente da data civil atual, verificando finalização após meia-noite e recusa de estado ausente ou ambíguo.

## 2. Migração das atividades locais existentes

- [x] 2.1 Implementar utilitário de migração que associe atividade sem `dia` ao único `RegistroDiario` da data local de `inicio`, verificando tarefas, sessões, fuso configurado e preservação dos demais campos.
- [x] 2.2 Recusar migração ausente, ambígua ou de YAML inválido sem alterar o arquivo afetado e verificar mensagens acionáveis e gravação atômica.
- [x] 2.3 Executar a migração nos YAMLs operacionais existentes e verificar que toda atividade atual e concluída possui o `dia` esperado antes do primeiro envio.

## 3. Montagem do retrato diário

- [x] 3.1 Implementar seleção determinística de todos os modelos registrados em `Relatórios` cuja `data` corresponda ao ciclo e verificar inclusão polimórfica, ordenação e rejeição de arquivo incompatível.
- [x] 3.2 Selecionar atividades concluídas pelo campo `dia`, preservando classe concreta e pausas aninhadas, e verificar rejeição de atividade incompleta ou sem vínculo.
- [x] 3.3 Montar o documento `{versao, data, relatorios, atividades}` com os mesmos valores primitivos canônicos do YAML e verificar campos `null`, datas, horários `HH:MM`, datetimes com deslocamento e durações `HH:MM:SS`.
- [x] 3.4 Exigir exatamente um `RegistroDiario` finalizado no retrato e verificar que toda falha de montagem ocorre antes da criação do cliente MongoDB.

## 4. Persistência MongoDB

- [x] 4.1 Implementar persistência na collection `dias` garantindo índice único em `data` e usando `replace_one` com filtro de data e `upsert=True`, verificando chamadas exatas e reenvio sem duplicidade.
- [x] 4.2 Traduzir falhas PyMongo de índice ou escrita para erro sanitizado e sempre fechar o cliente, verificando que URI, usuário, senha e host não aparecem e que arquivos locais permanecem byte a byte inalterados.
- [x] 4.3 Atualizar a consulta de sono anterior para projetar e validar o `RegistroDiario` dentro do documento agregado em `dias`, verificando histórico ausente, válido, legado, duplicado e estruturalmente inconsistente sem escrita.

## 5. Finalização automática e recuperação pela CLI

- [x] 5.1 Integrar o envio depois da gravação local de `finalizar dia`, verificando sucesso completo, nenhuma chamada remota em falha local e preservação de `fui_dormir` quando o MongoDB falha.
- [x] 5.2 Implementar `persistir dia --data YYYY-MM-DD`, verificando seleção exata, validação do argumento e upsert repetível de ciclo já finalizado.
- [x] 5.3 Implementar `persistir dia` sem data usando o ciclo finalizado local mais recente, verificando ordenação por data e erro quando nenhum ciclo finalizado existe.
- [x] 5.4 Cobrir os fluxos completos da CLI em diretório temporário, verificando ciclo atravessando meia-noite, associação das atividades, documento completo, códigos de saída e mensagens sanitizadas.

## 6. Verificação final

- [x] 6.1 Executar o verificador de classes e toda a suíte automatizada sem rede, confirmando ausência de regressões em esquemas, YAML, tarefas, pausas, durações e gerenciamento do dia.
- [x] 6.2 Executar a validação estrita do change OpenSpec e verificar cobertura de todos os requisitos e cenários.
- [x] 6.3 Executar o primeiro envio contra o Atlas, verificar um único documento completo na database configurada e collection `dias`, repetir o envio e confirmar que a contagem permanece um para a data.

