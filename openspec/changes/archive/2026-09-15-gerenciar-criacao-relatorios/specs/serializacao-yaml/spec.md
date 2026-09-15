## MODIFIED Requirements

### Requirement: Serialização legível e completa
O sistema SHALL converter qualquer classe exposta pelo catálogo de modelos para um documento YAML UTF-8 contendo `classe` e todos os campos da dataclass, inclusive campos herdados, valores calculados e campos ainda não preenchidos. A ordem dos campos SHALL seguir a ordem da classe e valores ausentes SHALL aparecer como `null`.

#### Scenario: Tarefa ainda incompleta
- **WHEN** uma `Tarefa` com `fim` e `duracao` não definidos é serializada
- **THEN** o YAML identifica `classe: Tarefa` e representa ambos os campos como `null`

#### Scenario: Relatório genérico
- **WHEN** um `Relatorio` recém-criado é serializado
- **THEN** o YAML identifica `classe: Relatorio` e contém `data`, `nome` e `notas`

#### Scenario: Texto com caracteres portugueses
- **WHEN** nome ou notas contêm acentos
- **THEN** o YAML é gravado em UTF-8 legível, sem exigir sequências Unicode escapadas

### Requirement: Reconstrução do tipo concreto
O sistema SHALL usar o discriminador `classe` para reconstruir qualquer classe concreta exposta pelo catálogo de modelos. Classes ausentes ou desconhecidas SHALL ser rejeitadas, campos omitidos SHALL assumir os padrões definidos pela dataclass e a compatibilidade entre classe-base e especialização SHALL ser preservada.

#### Scenario: Reconstrução de sessão
- **WHEN** um YAML válido declara `classe: SessaoEstudo`
- **THEN** o resultado é uma instância de `SessaoEstudo`, incluindo os campos herdados de `Tarefa`

#### Scenario: Reconstrução de relatório diário legado
- **WHEN** um YAML válido declara `classe: RegistroDiario` sem os novos campos comuns anuláveis
- **THEN** o resultado é um `RegistroDiario` com `nome` e `notas` iguais a `None`

#### Scenario: Classe desconhecida
- **WHEN** o documento declara uma classe que não pertence ao registro de modelos permitido
- **THEN** a leitura falha e identifica o discriminador desconhecido
