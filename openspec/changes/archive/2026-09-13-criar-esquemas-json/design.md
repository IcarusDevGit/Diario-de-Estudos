## Context

Os cinco arquivos existentes são JSONs pequenos usados como descrições de modelos. Três usam pares diretos de nome e tipo, enquanto os dois esquemas de sessão foram recentemente preenchidos. O texto livre `List (Object, tipo pausa)` e a ausência de metadados impedem que um consumidor interprete herança, validações e ciclo de vida sem regras externas.

## Goals / Non-Goals

**Goals:**

- Criar um formato uniforme, legível e suficiente para geração futura de modelos.
- Tornar explícitas as relações entre classes, os tipos compostos e as restrições.
- Preservar arquivos separados por conceito e os nomes atuais dos arquivos.
- Permitir representar entidades parcialmente preenchidas ao longo do dia.

**Non-Goals:**

- Implementar o gerador de classes Python.
- Implementar cronômetros, persistência ou envio ao MongoDB.
- Adotar o padrão JSON Schema ou adicionar uma biblioteca de validação externa.

## Decisions

### Usar uma DSL JSON mínima e versionada

Cada documento terá o formato geral:

```json
{
  "versao": 1,
  "classe": "NomeDaClasse",
  "herda_de": "ClasseBase",
  "campos": {
    "campo": {
      "tipo": "str",
      "opcional": true,
      "padrao": ""
    }
  }
}
```

`herda_de` existirá somente nas sessões. Um formato próprio pequeno é suficiente para o domínio atual e evita a complexidade de JSON Schema. A alternativa de manter strings compactas foi rejeitada porque exigiria interpretar uma gramática informal.

### Limitar o vocabulário de tipos

Os tipos escalares serão `str`, `bool`, `int`, `float`, `date`, `time` e `datetime`. Listas usarão `tipo: "list"` e `itens: "Pausa"`, mantendo tipo de coleção e referência separados.

Os nomes serão minúsculos e alinhados aos tipos Python, inclusive `bool` em vez de `Boolean`. Referências de modelo usarão o nome exato da classe.

### Separar ausência, padrão e cálculo

- `opcional: true` significa que o valor pode não estar presente ou ainda não ter sido informado.
- `padrao` fornece o valor inicial materializado, como `[]`, `false` ou `""`.
- `calculado: true` identifica um valor derivado que o consumidor não deve exigir como entrada.

Esses atributos não serão adicionados quando falsos ou inexistentes, reduzindo ruído. A alternativa de codificar opcionalidade no nome do tipo, como `datetime?`, foi rejeitada por voltar a exigir parsing textual.

### Usar datetime para intervalos e time para ocorrências do registro diário

`inicio` e `fim` de `Tarefa` e `Pausa` usarão `datetime`, permitindo duração correta ao atravessar a meia-noite. `RegistroDiario.data` usará `date`; os horários vinculados ao relatório usarão `time`, pois a data já é fornecida pelo documento diário.

### Declarar restrições de pontuação no próprio campo

As avaliações usarão `tipo: "int"`, `opcional: true`, `minimo: 1` e `maximo: 5`. Isso torna a restrição disponível para qualquer consumidor sem acoplá-la a uma implementação Python.

## Risks / Trade-offs

- [A DSL própria exige que consumidores implementem o contrato] → Manter a versão explícita e o vocabulário reduzido; planejar o gerador como uma mudança separada.
- [Valores padrão mutáveis como listas podem ser compartilhados por uma implementação ingênua] → O futuro gerador deverá transformar listas padrão em fábricas de valores.
- [Consumidores antigos não entendem a nova estrutura] → Fazer a alteração de forma atômica e validar todos os documentos antes de adotá-los.
- [O significado de `duracao` pode variar entre segundos, minutos e horas] → Adotar horas decimais nesta versão por compatibilidade com o tipo `float` atual e documentar a unidade no campo por meio de `unidade: "horas"`.

## Migration Plan

1. Reestruturar os cinco documentos preservando seus campos de domínio.
2. Validar a sintaxe JSON, nomes das classes, referências de herança e vocabulário de tipos.
3. Confirmar que campos temporais e avaliações obedecem às regras definidas.
4. Em caso de reversão, restaurar o formato simples anterior; não há dados persistidos que precisem ser migrados nesta etapa.
