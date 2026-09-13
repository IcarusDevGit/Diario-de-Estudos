## Why

As classes Python já podem ser geradas a partir dos esquemas, mas ainda não há uma representação persistente que seja confortável para preenchimento manual. A serialização YAML cria essa ponte mantendo tipos, valores nulos e estruturas aninhadas recuperáveis pelo programa.

## What Changes

- Adicionar conversão bidirecional entre as dataclasses geradas e documentos YAML UTF-8.
- Incluir o discriminador `classe` no YAML para reconstruir automaticamente o tipo concreto, inclusive sessões especializadas.
- Representar campos ainda não preenchidos como `null` e preservar a ordem declarada dos campos para facilitar edição manual.
- Converter `date`, `time` e `datetime` por representações ISO 8601, preservando o deslocamento de fuso quando presente.
- Serializar e reconstruir objetos aninhados, incluindo a lista de pausas de uma tarefa.
- Validar raiz, classe, campos desconhecidos, tipos e estruturas aninhadas, produzindo erros com caminho até o valor inválido.
- Gravar arquivos de forma atômica e segura, sem substituir um YAML válido quando a conversão falhar.
- Adicionar a dependência PyYAML e testes de ida e volta, segurança, legibilidade e falhas.

## Capabilities

### New Capabilities

- `serializacao-yaml`: Conversão segura, editável e reversível entre modelos gerados e arquivos YAML.

### Modified Capabilities

Nenhuma.

## Impact

- Adiciona um módulo de serialização e seus testes sob `Python/`.
- Adiciona PyYAML como dependência de execução do projeto.
- Consome as classes expostas por `Python.Classes`, sem alterar o gerador ou os arquivos gerados.
- Não define diretórios ou nomes de instâncias, movimentação de tarefas, comandos CLI, regras de finalização ou integração com MongoDB.
