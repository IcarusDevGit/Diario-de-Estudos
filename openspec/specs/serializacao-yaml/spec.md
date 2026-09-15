# Serialização YAML Specification

## Purpose

Permitir que instâncias dos modelos do diário sejam preenchidas manualmente em YAML e reconstruídas com segurança, sem perder tipos, valores nulos ou estruturas aninhadas.

## Requirements

### Requirement: Serialização legível e completa
O sistema SHALL converter qualquer uma das cinco classes de modelo para um documento YAML UTF-8 contendo `classe` e todos os campos da dataclass, inclusive valores calculados e campos ainda não preenchidos. A ordem dos campos SHALL seguir a ordem da classe e valores ausentes SHALL aparecer como `null`.

#### Scenario: Tarefa ainda incompleta
- **WHEN** uma `Tarefa` com `fim` e `duracao` não definidos é serializada
- **THEN** o YAML identifica `classe: Tarefa` e representa ambos os campos como `null`

#### Scenario: Texto com caracteres portugueses
- **WHEN** nome ou notas contêm acentos
- **THEN** o YAML é gravado em UTF-8 legível, sem exigir sequências Unicode escapadas

### Requirement: Reconstrução do tipo concreto
O sistema SHALL usar o discriminador `classe` para reconstruir a classe concreta exposta pelo pacote de modelos. Classes ausentes ou desconhecidas SHALL ser rejeitadas, e campos omitidos SHALL assumir os padrões definidos pela dataclass.

#### Scenario: Reconstrução de sessão
- **WHEN** um YAML válido declara `classe: SessaoEstudo`
- **THEN** o resultado é uma instância de `SessaoEstudo`, incluindo os campos herdados de `Tarefa`

#### Scenario: Classe desconhecida
- **WHEN** o documento declara uma classe que não pertence ao registro de modelos permitido
- **THEN** a leitura falha e identifica o discriminador desconhecido

### Requirement: Conversão de tipos escalares
O sistema SHALL validar e converter valores conforme as anotações e os metadados dos modelos. `date`, `time` e `datetime` SHALL usar textos ISO 8601; campos `time` com unidade/formato `HH:MM` SHALL ser gravados canonicamente com hora e minuto e sem segundos. Na leitura desses campos, `HH:MM` e o formato legado `HH:MM:SS` SHALL ser aceitos, descartando segundos e frações legados. Um `datetime` com deslocamento SHALL preservar esse deslocamento na ida e volta. Booleanos e números SHALL exigir seus tipos YAML correspondentes, sem coerção silenciosa a partir de textos.

#### Scenario: Valores temporais em ida e volta
- **WHEN** um modelo com data, hora e datetime com deslocamento é serializado e carregado novamente
- **THEN** a data e o datetime são preservados e o horário com formato `HH:MM` é preservado com precisão de minuto

#### Scenario: Horário canônico do relatório
- **WHEN** um campo de horário do relatório contém segundos ou microssegundos
- **THEN** sua representação YAML contém somente `HH:MM`, descartando a precisão inferior a minuto sem arredondar

#### Scenario: Horário legado do relatório
- **WHEN** um campo de horário do relatório é lido como `HH:MM:SS` ou com fração de segundo válida
- **THEN** o modelo conserva hora e minuto e uma nova serialização produz `HH:MM`

#### Scenario: Inteiro representado como texto
- **WHEN** um campo inteiro contém o texto `"4"` no YAML
- **THEN** a leitura falha com o caminho do campo em vez de convertê-lo implicitamente

### Requirement: Objetos aninhados
Listas tipadas SHALL ser serializadas e reconstruídas recursivamente. Cada objeto aninhado SHALL incluir seu próprio discriminador `classe`, e sua classe concreta SHALL ser compatível com o tipo de item declarado.

#### Scenario: Tarefa com pausas
- **WHEN** uma `Tarefa` contendo duas instâncias de `Pausa` é serializada e carregada
- **THEN** ela retorna com duas pausas equivalentes e tipadas como `Pausa`

#### Scenario: Item incompatível
- **WHEN** `pausas` contém um objeto cujo discriminador não representa `Pausa` ou uma subclasse válida
- **THEN** a leitura falha indicando o índice do item incompatível

### Requirement: Leitura segura e erros localizados
O leitor SHALL aceitar somente estruturas YAML seguras e SHALL rejeitar tags de construção arbitrária, raiz que não seja mapeamento, chaves duplicadas, chaves que não sejam texto, campos desconhecidos e valores incompatíveis. O erro SHALL identificar o arquivo quando disponível e o caminho lógico até o dado inválido.

#### Scenario: Chave duplicada
- **WHEN** um documento repete o mesmo campo
- **THEN** a leitura falha sem escolher silenciosamente um dos valores

#### Scenario: Campo desconhecido aninhado
- **WHEN** uma pausa contém um campo que não existe em `Pausa`
- **THEN** a leitura falha indicando um caminho como `$.pausas[0].campo`

#### Scenario: Tag insegura
- **WHEN** o YAML contém uma tag capaz de solicitar construção de objeto Python
- **THEN** a leitura falha sem instanciar ou executar o objeto solicitado

### Requirement: Gravação atômica e preservação em falha
Ao salvar em arquivo, o sistema SHALL concluir serialização e validação antes de substituir o destino e SHALL usar substituição atômica no mesmo diretório. Se qualquer etapa falhar, o arquivo anterior SHALL permanecer byte a byte inalterado.

#### Scenario: Substituição bem-sucedida
- **WHEN** um modelo válido é salvo sobre um arquivo existente
- **THEN** o destino passa a conter integralmente o novo YAML válido

#### Scenario: Falha antes da substituição
- **WHEN** o modelo contém um valor que não pode ser serializado pelo contrato
- **THEN** a operação falha e preserva integralmente o arquivo existente

### Requirement: Ida e volta estável
Para qualquer modelo válido suportado, serializar, carregar e serializar novamente SHALL produzir os mesmos dados e uma representação YAML determinística. O carregamento não SHALL compartilhar listas mutáveis entre instâncias.

#### Scenario: Segunda serialização
- **WHEN** um YAML produzido pelo sistema é carregado e serializado novamente
- **THEN** o segundo documento possui o mesmo conteúdo do primeiro

#### Scenario: Listas entre carregamentos
- **WHEN** o mesmo YAML de tarefa é carregado duas vezes
- **THEN** alterar a lista de pausas de uma instância não modifica a outra
