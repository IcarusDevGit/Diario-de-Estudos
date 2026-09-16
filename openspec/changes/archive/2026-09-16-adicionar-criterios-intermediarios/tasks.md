## 1. Contrato de esquemas e geração

- [x] 1.1 Ampliar a validação de definições em `Python/gerar_classes.py` para aceitar `passo` numérico positivo somente em campos `int` ou `float`, preservá-lo nos metadados e verificar casos válidos e inválidos em `Python/tests/test_gerar_classes.py`.
- [x] 1.2 Gerar a validação de incrementos a partir de `minimo` com tolerância numérica, mantendo limites e `None`, e verificar em testes a aceitação de 1, 1.5 e 5 e a rejeição de 0.5, 2.3 e 5.5.
- [x] 1.3 Alterar as 17 avaliações nos três esquemas aplicáveis para `tipo: float` e `passo: 0.5`, regenerar `Python/Classes/geradas.py` e verificar tipos, metadados e atualização determinística com o modo `--check`.

## 2. Compatibilidade e serialização YAML

- [x] 2.1 Adaptar `Python/serializacao_yaml.py` para aceitar e normalizar escalares `int` em destinos `float`, sem aceitar `bool` ou texto, e verificar que campos `int` existentes continuam estritos.
- [x] 2.2 Aplicar a validação do metadado `passo` durante a serialização e desserialização, com erros localizados, e verificar notas válidas de meio ponto e rejeições de 2.3, `"3.5"` e `"3,5"`.
- [x] 2.3 Cobrir em `Python/tests/test_serializacao_yaml.py` a leitura de YAML legado com nota inteira, a normalização para `float`, a ida e volta de 3.5 e a representação determinística do resultado.

## 3. Verificação integrada

- [x] 3.1 Executar toda a suíte de testes Python e corrigir regressões, verificando que criação de registros, sessões, persistência e serialização continuam funcionando com avaliações inteiras e intermediárias.
- [x] 3.2 Executar a validação estrita da mudança OpenSpec e a verificação de classes geradas, confirmando que especificações, artefatos e código gerado permanecem coerentes.
