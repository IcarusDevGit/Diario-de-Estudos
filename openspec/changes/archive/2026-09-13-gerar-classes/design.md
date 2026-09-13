## Context

Os cinco esquemas versionados já descrevem classes, campos, tipos, padrões, limites e valores calculados. As sessões atualmente usam `classe_mae`, enquanto a especificação principal ainda registra `herda_de`. O diretório `Python/Classes/` existe, mas não contém implementação ou configuração de projeto Python.

## Goals / Non-Goals

**Goals:**

- Manter os JSONs como fonte única da estrutura dos modelos.
- Produzir código Python legível, estável e importável somente com a biblioteca padrão.
- Detectar erros de contrato antes de tocar no último artefato gerado válido.
- Permitir que instâncias representem o preenchimento parcial que será serializado como `null` em uma mudança futura.

**Non-Goals:**

- Serializar ou analisar YAML.
- Implementar regras de início, pausa, término, duração ou persistência.
- Validar se um modelo está pronto para MongoDB.
- Gerar ou executar comandos da aplicação.

## Decisions

### Gerar um único módulo de dataclasses

`Python/gerar_classes.py` lerá os esquemas e produzirá `Python/Classes/geradas.py`, além de um `Python/Classes/__init__.py` estável que reexporta os modelos. Um único módulo elimina ciclos de importação entre `Tarefa`, `Pausa` e sessões e permite ordenar classes base antes das derivadas.

O arquivo gerado terá cabeçalho de aviso e não receberá comportamento manual. Serviços e classes de domínio futuros deverão importar ou especializar os modelos gerados. Gerar um arquivo por classe foi rejeitado por adicionar resolução de imports sem benefício para o conjunto pequeno atual.

### Usar dataclasses da biblioteca padrão

As classes usarão `@dataclass(kw_only=True)`. Campos manuais serão anotados como `T | None` e usarão `None` quando não houver padrão explícito, permitindo arquivos parcialmente preenchidos. `padrao: []` será convertido em `field(default_factory=list)`. Campos `calculado: true` usarão `field(default=None, init=False)`.

Pydantic e ferramentas externas de geração foram rejeitados nesta etapa para manter instalação e execução simples. Restrições `minimo` e `maximo` serão verificadas em `__post_init__` quando o valor não for `None`.

### Validar um modelo intermediário antes de renderizar

O gerador seguirá quatro estágios:

```text
JSON --> normalizar --> validar grafo --> renderizar/compilar --> substituir
```

A validação cobrirá versão 1, identificadores, duplicidade, vocabulário de tipos, atributos compatíveis, referências de itens e herança, e ciclos. O código será renderizado integralmente em memória e compilado antes da escrita. A substituição usará arquivo temporário no mesmo diretório e `os.replace`, evitando artefatos parciais.

### Ordenar pelo grafo de dependências

Classes referenciadas como base serão emitidas antes das derivadas; empates serão resolvidos pelo nome da classe. Arquivos e campos serão processados de forma estável. Ciclos de herança serão erros. Referências de campo que não afetam herança poderão usar anotações postergadas.

### Oferecer geração e verificação no mesmo comando

`python Python/gerar_classes.py` atualizará o módulo quando necessário. `python Python/gerar_classes.py --check` renderizará o resultado esperado e o comparará byte a byte, sem escrever. Ambos validarão os esquemas e usarão códigos de saída apropriados para automação.

### Preservar opcional como metadado de fase futura

Nesta mudança, nulabilidade representa apenas o estado incompleto em memória. O valor de `opcional` será preservado nos metadados dos campos gerados, mas sua interpretação para encerramento do dia ou persistência ficará para a capability responsável por essa validação. Isso evita acoplar a geração estrutural a uma regra de ciclo de vida ainda não implementada.

## Risks / Trade-offs

- [Código gerado pode ser editado manualmente e depois sobrescrito] → Incluir cabeçalho explícito e concentrar extensões futuras fora de `geradas.py`.
- [Um único módulo crescerá com novos modelos] → Manter enquanto o domínio for pequeno; dividir somente quando houver custo concreto de manutenção.
- [Dataclasses não oferecem validação rica nativamente] → Gerar apenas verificações simples de limites e manter validações de processo em serviços futuros.
- [Alterar o contrato de herança quebra consumidores de `herda_de`] → Atualizar a especificação e rejeitar o nome antigo com mensagem de migração clara.
- [Formatação textual pode variar entre versões do gerador] → Cobrir determinismo e modo `--check` em testes.

## Migration Plan

1. Atualizar o contrato OpenSpec de herança para `classe_mae` e confirmar os esquemas existentes.
2. Criar o pacote Python e o gerador sem depender do módulo gerado previamente.
3. Gerar e compilar o primeiro `geradas.py` a partir dos cinco esquemas.
4. Executar testes de modelos válidos, inválidos, determinismo, preservação em falha e modo `--check`.
5. Para reverter, remover os arquivos Python adicionados; os esquemas permanecem utilizáveis como documentos independentes.
