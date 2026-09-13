## Why

Os esquemas JSON já descrevem os modelos do diário, mas ainda não existe código Python que os transforme em classes utilizáveis. Automatizar essa geração evita duplicação manual, mantém os modelos alinhados aos esquemas e cria uma base tipada para as próximas partes do projeto.

## What Changes

- Criar um gerador Python que leia todos os arquivos de `Esquemas/`, valide seu contrato e produza classes `dataclass` determinísticas.
- Gerar `Pausa`, `Tarefa`, `SessaoEstudo`, `SessaoExercicio` e `RegistroDiario`, incluindo tipos, herança, valores padrão, campos opcionais, campos calculados e limites numéricos.
- Gerar o código em `Python/Classes/` com aviso de arquivo gerado e sem misturar comportamentos manuais futuros.
- Disponibilizar um modo de verificação que detecte quando o código gerado está desatualizado sem sobrescrevê-lo.
- Falhar com mensagens claras para esquemas inválidos e preservar o último código válido quando houver erro.
- **BREAKING**: oficializar `classe_mae` como metadado de herança no lugar de `herda_de`.
- Clarificar que nulabilidade na classe e obrigatoriedade antes da persistência são conceitos separados; a validação de persistência ficará fora desta mudança.

## Capabilities

### New Capabilities

- `geracao-classes-python`: Geração e verificação determinística de classes Python a partir dos esquemas JSON.

### Modified Capabilities

- `esquemas-json`: Substitui `herda_de` por `classe_mae` e explicita o contrato de nulabilidade consumido pelo gerador.

## Impact

- Adiciona código e testes sob `Python/` e gera modelos em `Python/Classes/`.
- Atualiza os esquemas de sessão e a especificação de esquemas para usar `classe_mae` de forma consistente.
- Não implementa leitura ou escrita YAML, comandos da aplicação, gerenciamento de tarefas, relatórios ou MongoDB.
- Não requer bibliotecas externas em tempo de execução; a implementação utiliza a biblioteca padrão do Python.
