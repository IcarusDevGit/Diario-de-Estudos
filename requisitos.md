Projeto CLI em Python. Todos os relatórios e tarefas serão arquivos de texto, para facilitar o preenchimento, que serão criados durante o dia a partir de esquemas pré-estabelecidos.

Esses modelos serão criados de forma modular a partir de esquemas, podendo ser modificados a qualquer momento.

Modelos:
-Relatório diário com os dados relacionais
-Tarefas genéricas
-Sessões (tarefas mais complexas)
    Sessões de estudo
    Sessões de exercício físico
-Relatórios

Cada tarefa, quando gerada, armazenará seu horário de início e quando finalizada armazenará seu horário de término. Haverá também a possibilidade de pausar a tarefa, que serão armazenadas em uma lista de pausas. O tempo total da tarefa será calculado somando os tempos de todas as pausas e subtraindo do tempo final.
Sessões será filha de Tarefas, herdando todas as suas colunas e adicionando as suas próprias.

Ao final do dia os arquivos serão movidos para o MongoDB

Comandos:
1. Iniciar dia
    - Cria um relatório diário para ser preenchido
2. Finalizar dia
    - Move os arquivos para o MongoDB
3. Nova tarefa
    - Cria um novo arquivo json referente à uma tarefa, esquema genérico
4. Nova sessão
    - Cria uma sessão (tarefa especializada), esquema específico e exclusivo para cada tipo de sessão

Esquemas:
Schema de dados de um relatório ou tarefa em um arquivo json, com a estrutura "nome do dado": tipo_de_dado
