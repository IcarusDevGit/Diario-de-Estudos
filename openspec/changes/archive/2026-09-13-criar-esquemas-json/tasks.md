## 1. Estrutura dos esquemas

- [x] 1.1 Reestruturar `pausa.json` com versão, classe, campos `datetime`, fim opcional e duração calculada em horas; verificar que o documento é aceito por um parser JSON.
- [x] 1.2 Reestruturar `tarefa.json` com versão, classe, lista tipada de `Pausa`, padrões, fim opcional e duração calculada em horas; verificar que não restam expressões de tipo em texto livre.
- [x] 1.3 Reestruturar `sessão-estudo.json` com classe `SessaoEstudo`, herança de `Tarefa` e avaliações opcionais limitadas a 1..5; verificar nomes e restrições no documento analisado.
- [x] 1.4 Reestruturar `sessão-exercicio.json` com classe `SessaoExercicio`, herança de `Tarefa` e avaliações opcionais limitadas a 1..5; verificar que a classe possui exatamente o nome correto planejado.
- [x] 1.5 Reestruturar `registro-diario.json` com classe `RegistroDiario`, `date` para a data, `time` para horários, estado parcial e avaliações limitadas a 1..5; verificar os tipos e limites no documento analisado.

## 2. Validação integrada

- [x] 2.1 Analisar todos os arquivos `Esquemas/*.json` como UTF-8 e verificar que os cinco são documentos JSON válidos e não vazios.
- [x] 2.2 Verificar de forma automatizada que as classes são únicas, as sessões referenciam `Tarefa`, a lista de pausas referencia `Pausa` e todos os tipos pertencem ao vocabulário definido.
- [x] 2.3 Revisar o diff final para confirmar que somente os cinco esquemas planejados foram implementados e que todos os campos de domínio existentes foram preservados.
