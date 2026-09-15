## MODIFIED Requirements

### Requirement: Documento agregado do ciclo
O sistema SHALL representar cada ciclo como um documento com `versao`, `data`, `relatorios` e `atividades`. `relatorios` SHALL conter todo YAML válido do diretório `Relatórios` cujo modelo seja `Relatorio` ou uma especialização e possua `data` igual à data do ciclo. `atividades` SHALL conter toda `Tarefa`, `SessaoEstudo` ou `SessaoExercicio` concluída cujo campo `dia` seja igual àquela data. Pausas SHALL permanecer aninhadas em sua atividade, e valores ausentes SHALL permanecer `null`.

#### Scenario: Retrato completo
- **WHEN** um ciclo possui relatório diário, relatório genérico e duas atividades concluídas associadas
- **THEN** o documento contém os dois relatórios e as duas atividades com classes concretas, campos e pausas preservados

#### Scenario: Futuro tipo de relatório
- **WHEN** um novo modelo derivado de `Relatorio` possui YAML válido em `Relatórios`
- **THEN** ele pode integrar `relatorios` sem alterar a estrutura do documento do ciclo

#### Scenario: Modelo datado que não é relatório
- **WHEN** um modelo registrado possui campo `data`, mas não deriva de `Relatorio`
- **THEN** ele não é incluído em `relatorios`
