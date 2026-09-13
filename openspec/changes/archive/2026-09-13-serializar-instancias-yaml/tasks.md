## 1. Dependência e estrutura

- [x] 1.1 Declarar PyYAML com limite de versão principal em `requirements.txt` e verificar que a instalação permite importar `yaml.safe_load` e `yaml.safe_dump`.
- [x] 1.2 Criar `Python/serializacao_yaml.py`, exceções públicas e estrutura de testes, verificando que o módulo importa os modelos por `Python.Classes` sem depender do gerador.

## 2. Modelo para YAML

- [x] 2.1 Implementar conversão recursiva de dataclasses para estruturas primitivas, emitindo `classe` primeiro e todos os campos na ordem declarada; verificar tarefa incompleta, sessão e pausas aninhadas.
- [x] 2.2 Converter `date`, `time` e `datetime` para ISO 8601 e rejeitar valores incompatíveis com as anotações; verificar Unicode, `null`, booleanos, números e deslocamento de fuso.
- [x] 2.3 Gerar texto YAML determinístico em blocos, com Unicode direto e quebra de linha final; verificar uma segunda serialização byte a byte idêntica.

## 3. YAML para modelo

- [x] 3.1 Implementar loader derivado de `SafeLoader` sem resolução implícita de timestamp e com rejeição de chaves duplicadas ou não textuais; verificar documentos válidos, duplicados e tags Python inseguras.
- [x] 3.2 Construir o registro permitido a partir de `Python.Classes.__all__` e reconstruir o tipo indicado por `classe`; verificar classes desconhecidas, discriminador ausente e herança de sessões.
- [x] 3.3 Validar campos escalares estritamente e converter textos ISO para tipos temporais; verificar erros localizados para textos numéricos, booleanos incorretos e datas/horas inválidas.
- [x] 3.4 Reconstruir listas e objetos aninhados com compatibilidade de tipo, campos ausentes usando defaults e campos `init=False` atribuídos após a criação; verificar pausas, índices de erro e listas independentes.
- [x] 3.5 Rejeitar raiz inválida e campos desconhecidos em qualquer nível, incluindo no erro o caminho lógico e, nas APIs de arquivo, o arquivo de origem.

## 4. Operações de arquivo

- [x] 4.1 Implementar leitura UTF-8 e gravação atômica com temporário no mesmo diretório, `flush`, `fsync` e `os.replace`; verificar substituição completa e remoção de temporários.
- [x] 4.2 Validar a ida e volta antes de substituir o destino e verificar que falhas de serialização, validação ou escrita preservam byte a byte o arquivo anterior.

## 5. Validação integrada

- [x] 5.1 Executar a suíte completa de geração e serialização, verificando ida e volta para as cinco classes e ausência de regressões no gerador.
- [x] 5.2 Executar `openspec validate serializar-instancias-yaml --strict` e revisar o diff para confirmar que diretórios operacionais, CLI, ciclo de vida e MongoDB permaneceram fora do escopo.
