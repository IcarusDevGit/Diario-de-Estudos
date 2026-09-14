# Formato de Duração Specification

## Purpose

Padronizar durações de tarefas e pausas em uma representação textual legível, validável e adequada a intervalos maiores que um dia.

## Requirements

### Requirement: Representação canônica da duração
Uma duração preenchida SHALL ser representada como texto `HH:MM:SS`, em que horas contém no mínimo dois dígitos e pode exceder 23, enquanto minutos e segundos contêm exatamente dois dígitos entre `00` e `59`. Uma duração ainda desconhecida SHALL permanecer `null`.

#### Scenario: Duração inferior a uma hora
- **WHEN** um intervalo finalizado possui quatorze segundos
- **THEN** sua duração é representada como `00:00:14`

#### Scenario: Duração superior a um dia
- **WHEN** uma duração totaliza vinte e sete horas, dois minutos e três segundos
- **THEN** ela é representada como `27:02:03`

#### Scenario: Duração ainda não calculada
- **WHEN** uma tarefa ou pausa ainda não foi finalizada
- **THEN** `duracao` permanece `null`

### Requirement: Arredondamento ao segundo mais próximo
Ao converter um intervalo temporal, o sistema SHALL arredondá-lo ao segundo inteiro mais próximo; frações iguais ou superiores a meio segundo SHALL avançar para o segundo seguinte. O arredondamento SHALL ocorrer uma única vez sobre o resultado final de cada duração calculada.

#### Scenario: Fração abaixo de meio segundo
- **WHEN** o intervalo calculado é `13,4` segundos
- **THEN** a duração resultante é `00:00:13`

#### Scenario: Meio segundo
- **WHEN** o intervalo calculado é `13,5` segundos
- **THEN** a duração resultante é `00:00:14`

#### Scenario: Fração acima de meio segundo
- **WHEN** o intervalo calculado é `13,828065` segundos
- **THEN** a duração resultante é `00:00:14`

### Requirement: Validação e aritmética de durações
O sistema SHALL validar estritamente o formato canônico e SHALL converter durações válidas para segundos inteiros ao realizar comparações, somas ou subtrações. Para uma tarefa, a duração líquida SHALL ser calculada a partir do intervalo real entre início e fim menos os intervalos reais das pausas, antes do arredondamento final.

#### Scenario: Texto fora do formato
- **WHEN** uma duração preenchida contém `1:2:3`, minutos iguais a `60`, sinal ou fração decimal
- **THEN** a validação falha identificando o campo inválido

#### Scenario: Duração líquida com pausas fracionárias
- **WHEN** uma tarefa e suas pausas possuem instantes com frações de segundo
- **THEN** o sistema subtrai os intervalos temporais exatos e arredonda apenas a duração líquida final

### Requirement: Migração explícita do formato legado
O sistema SHALL oferecer uma migração explícita que localize campos `duracao` numéricos em horas nos YAMLs selecionados, converta cada valor para segundos e produza o formato canônico com a regra de arredondamento. A leitura comum SHALL continuar rejeitando o formato numérico após a alteração do modelo.

#### Scenario: Migrar duração decimal existente
- **WHEN** a migração encontra `duracao: 0.003841129166666667`
- **THEN** ela substitui o valor por `duracao: 00:00:14`

#### Scenario: Arquivo já migrado
- **WHEN** a migração encontra somente durações canônicas ou `null`
- **THEN** ela não altera o arquivo e informa que nenhuma conversão foi necessária

#### Scenario: Conteúdo incompatível durante migração
- **WHEN** um YAML selecionado contém duração negativa, texto não canônico ou estrutura insegura
- **THEN** a migração falha identificando arquivo e campo sem alterar esse arquivo

### Requirement: Migração verificável e segura
A migração SHALL possuir um modo de verificação que reporte arquivos legados sem modificá-los. Na execução efetiva, cada arquivo SHALL ser completamente convertido e validado antes de substituir atomicamente seu conteúdo; uma falha SHALL preservar os bytes anteriores do arquivo afetado.

#### Scenario: Verificação sem escrita
- **WHEN** a migração é executada em modo de verificação sobre um YAML legado
- **THEN** ela retorna estado pendente e mantém o arquivo byte a byte inalterado

#### Scenario: Falha antes da substituição
- **WHEN** a conversão ou validação de um arquivo falha
- **THEN** o arquivo original permanece byte a byte inalterado
