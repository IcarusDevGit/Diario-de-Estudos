## Context

Ver `proposal.md` para a motivação. Atualmente, as 17 avaliações subjetivas são declaradas como `int` em três esquemas, o gerador transfere apenas limites mínimo e máximo para dataclasses, e a serialização exige correspondência exata entre o tipo Python anotado e o tipo do escalar YAML. A solução precisa preservar arquivos existentes que usam inteiros e continuar rejeitando coerção a partir de texto.

## Goals / Non-Goals

**Goals:**

- Expressar no esquema que avaliações usam a grade discreta de 1 a 5 com passo 0,5.
- Centralizar a regra de passo no gerador e nos metadados das classes, evitando validações específicas por nome de campo.
- Preservar a leitura de avaliações inteiras já armazenadas.
- Manter erros localizados e a ida e volta determinística do YAML.

**Non-Goals:**

- Aceitar qualquer precisão decimal entre 1 e 5.
- Interpretar vírgula como separador decimal em YAML.
- Migrar ou reescrever arquivos existentes automaticamente.
- Alterar descrições textuais dos critérios ou calcular médias e agregações.

## Decisions

### Declarar `tipo: float` e `passo: 0.5` em cada avaliação

O tipo comunica que valores fracionários são válidos, enquanto o novo metadado genérico `passo` expressa a grade discreta. O passo será contado a partir de `minimo`, portanto um campo com mínimo 1 e passo 0,5 aceita exatamente `1 + n * 0,5` dentro do máximo.

Alternativas consideradas:

- Usar apenas `float` com limites permitiria valores não desejados como 2,3.
- Enumerar os nove valores válidos duplicaria dados e tornaria o mecanismo menos reutilizável.
- Criar um tipo específico para avaliações acoplaria o gerador ao domínio, contrariando o modelo genérico dos esquemas.

### Validar o passo sem depender de igualdade ingênua de ponto flutuante

A validação verificará se a distância entre o valor e o mínimo corresponde, dentro de tolerância numérica apropriada, a um múltiplo inteiro do passo. Isso evita rejeições causadas pela representação binária de floats. O gerador emitirá a mesma regra usada na construção da dataclass, e a serialização consultará os metadados antes de gravar ou após converter um documento.

Alternativa considerada: usar `Decimal` eliminaria parte da imprecisão, mas introduziria um novo tipo no contrato, tratamento YAML adicional e complexidade desnecessária para incrementos de 0,5, que são exatamente representáveis em binário.

### Compatibilizar escalares YAML inteiros apenas quando o destino for `float`

Na desserialização, um campo anotado como `float` aceitará `int` ou `float`, excluindo explicitamente `bool`, e normalizará o resultado com `float(valor)`. Campos `int` continuarão estritos. Na serialização de modelos, o contrato permanecerá tipado como `float`; as classes geradas usarão floats para as avaliações.

Alternativa considerada: exigir que arquivos antigos fossem alterados de `3` para `3.0` criaria uma migração sem benefício funcional.

### Preservar `passo` como metadado gerado

O gerador aceitará `passo` somente em campos `int` ou `float`, exigirá número positivo e o incluirá nos metadados das dataclasses. Essa representação permite que tanto `__post_init__` quanto a serialização apliquem a mesma restrição declarativa.

## Risks / Trade-offs

- [Comparações numéricas podem sofrer erro de arredondamento] → validar o quociente contra o inteiro mais próximo com tolerância explícita e cobrir valores válidos e inválidos próximos em testes.
- [Aceitar inteiros para todo campo `float` amplia o comportamento do desserializador] → limitar a flexibilização exclusivamente ao destino `float`, manter booleanos e textos inválidos e documentar o contrato em testes.
- [Validação duplicada na dataclass e na serialização pode divergir] → gerar a validação a partir dos mesmos metadados e testar construção direta e ida e volta YAML.
- [YAML serializado pode representar uma nota inteira como `3.0`] → aceitar essa forma canônica; o valor semântico e a compatibilidade são preservados.

## Migration Plan

1. Ampliar e testar o contrato de esquema e o gerador.
2. Alterar os três esquemas de avaliações e regenerar as classes.
3. Ampliar a conversão YAML e seus testes de compatibilidade.
4. Executar toda a suíte e a verificação de classes geradas.

Não há migração de dados. Para rollback, revertem-se os esquemas, o gerador, as classes geradas e a serialização; arquivos que já contenham notas fracionárias deixarão de ser legíveis na versão anterior, mas arquivos inteiros permanecerão válidos.
