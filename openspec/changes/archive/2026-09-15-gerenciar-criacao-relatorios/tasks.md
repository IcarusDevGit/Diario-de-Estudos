## 1. Evolução dos esquemas e classes

- [x] 1.1 Criar `relatorio.json` com `data`, `nome` e `notas`, fazer `RegistroDiario` herdar de `Relatorio` sem duplicar `data` e verificar os metadados e a hierarquia por testes dos esquemas.
- [x] 1.2 Adaptar expectativas que enumeram uma quantidade fixa de modelos, regenerar `Python/Classes/geradas.py` e verificar que todo esquema é exportado e que `RegistroDiario` herda de `Relatorio`.
- [x] 1.3 Verificar compatibilidade da dataclass herdada, incluindo criação de `Relatorio`, criação de `RegistroDiario` sem `nome` e `notas` e validação de campos e padrões.

## 2. Compatibilidade e serialização YAML

- [x] 2.1 Atualizar os testes de serialização polimórfica para cobrir `Relatorio`, campos herdados e textos UTF-8 em `nome` e `notas`.
- [x] 2.2 Garantir que YAMLs legados de `RegistroDiario` sem `nome` e `notas` continuem carregáveis como `None` e verificar ida e volta determinística sem reescrever arquivos existentes.
- [x] 2.3 Executar o verificador de classes geradas e os testes de esquemas e YAML, confirmando ausência de regressões nos outros modelos.

## 3. Criação de relatórios genéricos

- [x] 3.1 Implementar o serviço de criação que valide e normalize `nome`, resolva a data explícita ou a data atual pelo fuso configurado e construa `Relatorio(data, nome, notas=None)`, cobrindo nomes vazios e configuração temporal inválida.
- [x] 3.2 Implementar nomes `RG-YYYY-MM-DD-<slug>.yaml` com normalização segura, fallback e sufixos incrementais, verificando acentos, símbolos, nomes equivalentes e destinos já existentes sem sobrescrita.
- [x] 3.3 Salvar o relatório de forma validada e atômica, verificando sucesso, falhas de serialização/escrita e ausência de arquivo parcial.
- [x] 3.4 Integrar `criar relatorio NOME [--data YYYY-MM-DD]` à CLI, verificando parsing, data inválida, códigos de saída, mensagens acionáveis e caminho impresso no sucesso.

## 4. Integração com o retrato diário

- [x] 4.1 Alterar a seleção em `Relatórios` para aceitar somente `Relatorio` e subclasses da data do ciclo, verificando inclusão do genérico e exclusão de um modelo datado não relacionado.
- [x] 4.2 Preservar a exigência de exatamente um `RegistroDiario` finalizado e verificar que relatórios genéricos adicionais não alteram a identificação do ciclo.
- [x] 4.3 Verificar que `persistir dia --data` inclui o relatório genérico completo no retrato e mantém os arquivos locais inalterados, usando cliente MongoDB simulado e sem rede.

## 5. Verificação final

- [x] 5.1 Executar toda a suíte automatizada e o modo de verificação do gerador, corrigindo quaisquer regressões até ambos terminarem com sucesso.
- [x] 5.2 Executar um fluxo completo em diretório temporário — criar relatório com data padrão e explícita, provocar colisão, carregar os YAMLs e montar o retrato — verificando conteúdos e nomes resultantes.
- [x] 5.3 Executar a validação estrita do change OpenSpec e confirmar que proposal, design, specs e tarefas permanecem coerentes.
