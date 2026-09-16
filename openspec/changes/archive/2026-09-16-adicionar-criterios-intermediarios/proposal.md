## Why

As avaliações subjetivas aceitam apenas números inteiros de 1 a 5, o que força o usuário a escolher entre descrições adjacentes mesmo quando sua percepção está entre elas. Permitir incrementos de meio ponto torna o registro mais fiel sem alterar a escala nem invalidar dados já existentes.

## What Changes

- Permitir avaliações subjetivas de 1 a 5 em incrementos de 0,5 nos registros diários e nas sessões de estudo e exercício.
- Representar essas avaliações como números de ponto flutuante nos esquemas e modelos gerados, preservando os limites inclusivos atuais.
- Declarar e validar no esquema um passo numérico de 0,5 para rejeitar valores intermediários não previstos, como 2,3.
- Aceitar na leitura YAML tanto notas inteiras legadas, como `3`, quanto notas decimais, como `3.5`, normalizando-as para o tipo do modelo.
- Manter a sintaxe numérica YAML com ponto decimal; a vírgula usada na descrição em português não será aceita como separador decimal no arquivo.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `esquemas-json`: alterar o contrato das avaliações subjetivas de inteiros para números com passo de 0,5 entre 1 e 5.
- `geracao-classes-python`: preservar o novo metadado de passo e gerar validação para incrementos numéricos permitidos.
- `serializacao-yaml`: aceitar inteiros legados ao carregar campos `float`, normalizá-los e validar o passo durante a ida e volta.

## Impact

- Esquemas em `Esquemas/registro-diario.json`, `Esquemas/sessão-estudo.json` e `Esquemas/sessão-exercicio.json`.
- Gerador e classes resultantes em `Python/gerar_classes.py` e `Python/Classes/geradas.py`.
- Conversão e validação numérica em `Python/serializacao_yaml.py`.
- Testes dos esquemas, geração de classes e serialização YAML.
- YAMLs existentes com avaliações inteiras permanecem compatíveis; não há dependência nova nem migração obrigatória de arquivos.
