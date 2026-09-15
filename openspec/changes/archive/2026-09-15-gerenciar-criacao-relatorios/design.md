## Context

O gerador já resolve herança por `classe_mae`, e a serialização descobre dinamicamente as classes exportadas. Porém, `RegistroDiario` ainda é uma raiz independente, alguns contratos enumeram cinco modelos e a seleção de relatórios no retrato aceita qualquer objeto com atributo `data`. A CLI não possui um grupo `criar`.

## Goals / Non-Goals

**Goals:**

- Introduzir uma raiz comum de relatórios sem invalidar YAMLs diários existentes.
- Criar relatórios genéricos por CLI com nome seguro, data previsível e gravação atômica.
- Fazer descoberta, serialização e persistência dependerem do catálogo e da hierarquia, não de contagens fixas.

**Non-Goals:**

- Criar comandos genéricos para instanciar qualquer futura subclasse.
- Finalizar, mover ou excluir relatórios genéricos.
- Alterar o formato agregado ou criar outra collection no MongoDB.
- Persistir imediatamente o relatório no momento de sua criação.

## Decisions

### `Relatorio` será base concreta com campos anuláveis compatíveis

O novo esquema declara `data`, `nome` e `notas`; `RegistroDiario` passa a declarar `classe_mae: Relatorio` e remove sua declaração duplicada de `data`. `nome` e `notas` terão padrão `null`, permitindo carregar YAMLs diários legados. O comando de criação aplica a regra mais forte de nome obrigatório apenas ao relatório genérico.

Alternativas descartadas: tornar a base abstrata impediria seu uso genérico; exigir `nome` em toda a hierarquia quebraria registros diários existentes ou imporia um dado sem utilidade ao ciclo.

### A CLI terá o grupo `criar`

O formato será `criar relatorio NOME [--data YYYY-MM-DD]`. A data explícita usa ISO civil; sem ela, o serviço obtém a data atual pela configuração `FUSO_HORARIO`. `notas` começa como `null` para edição manual posterior.

Alternativa descartada: `iniciar relatorio` sugere um ciclo de vida com finalização que não existe para esse modelo.

### Arquivos usarão prefixo `RG-`, slug e sufixo incremental

O nome base será `RG-YYYY-MM-DD-<slug>.yaml`. O slug normaliza Unicode para ASCII, converte sequências não alfanuméricas em hífens, remove hífens externos e usa um fallback seguro caso necessário. Colisões recebem `-2`, `-3` e assim por diante. A escolha e a criação deverão impedir sobrescrita mesmo diante de conflito observado durante a operação.

Alternativas descartadas: nomes livres permitem separadores e caminhos inválidos; UUID evita colisão, mas reduz a legibilidade operacional.

### A seleção para o retrato será nominalmente tipada

A montagem aceitará apenas instâncias de `Relatorio` e subclasses cuja `data` corresponda ao ciclo. A regra especial continua exigindo exatamente um `RegistroDiario` finalizado. Isso substitui a heurística `hasattr(modelo, "data")`, evitando incluir futuros modelos datados que não sejam relatórios.

## Risks / Trade-offs

- [Adicionar campos herdados altera novos YAMLs diários] → manter `nome` e `notas` anuláveis e testar leitura de arquivos legados sem essas chaves.
- [Dois processos podem escolher o mesmo sufixo] → usar criação exclusiva ou repetição controlada, sem sobrescrever destinos.
- [Nomes distintos podem gerar o mesmo slug] → tratar como colisão normal e aplicar sufixo incremental.
- [Relatório criado para ciclo já persistido não aparece automaticamente no Atlas] → manter `persistir dia --data` como mecanismo explícito de atualização.

## Migration Plan

1. Adicionar o esquema base e transferir `data` para ele.
2. Regenerar as classes e validar YAMLs diários existentes antes de integrar o comando.
3. Atualizar criação, serialização e seleção do retrato com testes sem rede.
4. Não reescrever arquivos legados; eles serão enriquecidos apenas quando forem novamente serializados.
5. Em rollback, restaurar os esquemas e classes anteriores; relatórios genéricos já criados deixam de ser carregáveis até a reaplicação da mudança, mas os registros diários permanecem recuperáveis.
