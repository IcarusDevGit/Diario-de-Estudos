## Context

Os modelos são dataclasses geradas em `Python/Classes/geradas.py`, usam anotações postergadas, valores `None`, listas com fábrica e campos `init=False`. O projeto ainda não possui uma camada de persistência nem arquivo de dependências. Os YAMLs serão editados manualmente, mas também precisarão ser regravados por operações futuras.

## Goals / Non-Goals

**Goals:**

- Oferecer uma representação YAML previsível e confortável para edição manual.
- Reconstruir somente as classes geradas explicitamente permitidas.
- Produzir erros acionáveis para conteúdo alterado manualmente.
- Preservar arquivos existentes diante de falhas de conversão ou escrita.

**Non-Goals:**

- Preservar comentários ou estilo exato inseridos manualmente após uma regravação.
- Escolher diretórios, nomes ou estados de arquivos de tarefas e relatórios.
- Aplicar obrigatoriedade anterior ao MongoDB ou executar regras de ciclo de vida.
- Implementar comandos de terminal.

## Decisions

### Usar PyYAML com carregador seguro restrito

PyYAML será registrado em `requirements.txt` com versão principal limitada. A leitura derivará de `SafeLoader`, rejeitará chaves duplicadas e removerá a resolução implícita de timestamps; assim, valores temporais entram na camada de conversão como textos e seguem regras únicas. Tags Python e outros construtores inseguros permanecerão indisponíveis.

YAML escrito manualmente por um parser próprio foi rejeitado por exigir manutenção de uma gramática complexa. `ruamel.yaml` preservaria comentários, mas adicionaria complexidade que não é necessária enquanto os arquivos são pequenos e a perda de comentários na regravação está documentada.

### Separar normalização de YAML e construção de modelos

`Python/serializacao_yaml.py` exporá operações em texto e arquivo:

```text
modelo --> dados primitivos --> YAML --> arquivo
arquivo --> YAML seguro --> dados validados --> modelo
```

A conversão não dependerá de detalhes privados do gerador. Ela usará `dataclasses.fields`, `typing.get_type_hints` e o `__all__` de `Python.Classes` para construir um registro explícito de modelos permitidos.

### Usar um discriminador classe em cada objeto

Todo mapeamento que representa uma dataclass terá `classe` como primeira chave. Isso permite reconstruir sessões concretas quando o tipo esperado é `Tarefa` e torna os objetos aninhados autodescritivos. O discriminador deverá pertencer ao registro e ser igual ou derivado do tipo esperado.

Alternar o formato com base no caminho do arquivo foi rejeitado porque acoplaria serialização à organização de diretórios, prevista para outra mudança.

### Normalizar tipos antes de chamar a dataclass

- `str`, `bool`, `int` e `float` terão validação estrita; `bool` não será aceito como inteiro.
- `date`, `time` e `datetime` usarão `isoformat()` e os respectivos `fromisoformat()`.
- `None` será aceito para representar preenchimento pendente.
- Listas serão percorridas recursivamente e sempre reconstruídas como novas listas.
- Campos desconhecidos serão rejeitados; campos ausentes usarão o default/default_factory da dataclass.
- Campos `init=False`, como `duracao`, serão validados e atribuídos após a construção.

Os erros usarão caminhos iniciados por `$`, por exemplo `$.pausas[0].inicio`, e incluirão o caminho do arquivo nas APIs de leitura.

### Produzir YAML estável e legível

O dumper usará estilo em blocos, Unicode direto, ordem de inserção e terminação com quebra de linha. Datas e horas serão convertidas previamente em strings ISO para evitar representações dependentes dos resolvers YAML. Todos os campos serão emitidos, inclusive `None`, para servirem como formulário manual.

Não será feita tentativa de preservar comentários ou escolhas de aspas do usuário: uma operação de salvar normaliza o documento inteiro.

### Gravar com substituição atômica

O texto será construído por completo e validado por uma leitura de ida e volta antes da escrita. A gravação usará arquivo temporário no diretório de destino, `flush`, `fsync` e `os.replace`. Arquivos temporários serão removidos em falhas.

## Risks / Trade-offs

- [Regravar remove comentários e formatação manual] → Documentar a normalização e manter nomes e ordem de campos estáveis.
- [YAML aceita muitas construções implícitas] → Usar loader seguro, desativar timestamps implícitos e validar todos os valores depois do parse.
- [A dependência pode não estar instalada] → Declarar PyYAML em `requirements.txt` e produzir uma falha de importação clara.
- [Alterações futuras nas classes podem tornar YAMLs antigos incompatíveis] → Aceitar campos ausentes com defaults, rejeitar campos desconhecidos e tratar migração/versionamento em mudança futura quando necessário.
- [Substituição atômica não garante durabilidade absoluta em todos os sistemas] → Executar `fsync` do arquivo temporário e manter a operação no mesmo volume.

## Migration Plan

1. Adicionar e instalar a dependência PyYAML.
2. Implementar conversão de modelos para dados primitivos e YAML.
3. Implementar leitura segura, validação e reconstrução dos modelos.
4. Implementar operações atômicas de arquivo.
5. Cobrir modelos simples, sessões, pausas aninhadas, tipos temporais e falhas em testes.
6. Não migrar dados existentes, pois ainda não há instâncias YAML persistidas pelo sistema.
