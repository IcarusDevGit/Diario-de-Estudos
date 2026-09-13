## 1. Contrato e estrutura Python

- [x] 1.1 Confirmar os cinco esquemas com `classe_mae` nas sessões e adicionar testes de contrato que rejeitem `herda_de`, versões incompatíveis e documentos malformados.
- [x] 1.2 Criar o pacote `Python/Classes`, o ponto de entrada `Python/gerar_classes.py` e a estrutura de testes usando somente a biblioteca padrão; verificar que os módulos básicos podem ser importados.

## 2. Leitura e validação dos esquemas

- [x] 2.1 Implementar carregamento UTF-8 e normalização dos documentos de `Esquemas/`; verificar com testes os cinco esquemas reais e erros JSON com indicação do arquivo.
- [x] 2.2 Validar versão, identificadores, classes duplicadas, tipos, atributos de campo e referências; verificar cada categoria com testes positivos e negativos.
- [x] 2.3 Ordenar classes pelo grafo de herança, rejeitando bases ausentes e ciclos; verificar que classes base precedem sessões independentemente da ordem dos arquivos.

## 3. Geração das dataclasses

- [x] 3.1 Renderizar imports, `__all__`, dataclasses e anotações para todos os tipos suportados; verificar nomes, campos e herança das cinco classes geradas.
- [x] 3.2 Renderizar `None` para campos manuais sem valor, fábricas para padrões mutáveis, metadados de `opcional` e campos calculados fora do construtor; verificar isolamento entre instâncias e assinatura dos construtores.
- [x] 3.3 Gerar validações de `minimo` e `maximo` para valores não nulos; verificar limites aceitos, rejeições e mensagens com classe e campo.

## 4. Escrita segura e verificação

- [x] 4.1 Compilar o conteúdo renderizado e substituir `Python/Classes/geradas.py` atomicamente somente após validação completa; verificar que uma falha preserva byte a byte um módulo válido anterior.
- [x] 4.2 Implementar `--check` sem escrita e códigos de saída distintos para atualizado, desatualizado e esquema inválido; verificar os três fluxos com testes.
- [x] 4.3 Garantir saída determinística e cabeçalho de arquivo gerado; verificar que duas gerações sucessivas produzem conteúdo idêntico.

## 5. Integração

- [x] 5.1 Gerar `Python/Classes/geradas.py` a partir dos esquemas reais e verificar compilação, importação e exposição das cinco classes por `Python.Classes`.
- [x] 5.2 Executar toda a suíte de testes e `python Python/gerar_classes.py --check`, corrigindo qualquer falha antes de concluir a mudança.
- [x] 5.3 Executar `openspec validate gerar-classes --strict` e revisar o diff para confirmar que YAML, CLI, regras de execução e MongoDB permaneceram fora do escopo.
