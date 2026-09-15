A aplicação será usada por meio de códigos no terminal
Cada instância de uma classe será na verdade um arquivo .yaml, que terá seus parâmetros preenchidos manualmente
Relatórios serão criados dentro de uma pasta de mesmo nome
Tarefas serão criadas dentro da pasta de mesmo nome, sendo que a tarefa sendo atualmente executada ficará em Tarefas\Tarefas em andamento
Qualquer pausa iniciada ficará dentro de Tarefas/pausas
Opcional significa que o campo não pode subir para o banco de dados sem ser preenchido, não que precisa ser preenchido ao ser criado
herda_de foi mudado para classe_mae e deve permancer assim
Apenas uma tarefa e pausa pode estar em andamento por vez

Comandos:
1. Iniciar
- Dia
    Cria um Relatório diário, o campo data é automaticamente preenchido com a data atual (timezone Brasília)
    O campo dormi_dia_anterior é automaticamente preenchido com o valor do campo fui_dormir do relatório diário do dia anterior (informação é pega pelo MongoDB). Se o relatório do dia anterior não existir esse horário poderá ser preenchido manualmente
    
- Tarefa
    Cria uma Tarefa genérica
    O campo início é preenchido automaticamente com a hora atual

- Sessão
    Argumento que especifica sessão
    Executa o script para criar uma tarefa que é então enriquecido com os campos exclusivos da Sessão especificada

- Pausa
    Cria uma Pausa
    O campo início é preenchido automaticamente com a hora atual

2. Finalizar
- Dia
    Primeiro é validado se todos os relatórios necessários foram preenchidos, caso não será apresentado uma mensagem de erro especificando os relatórios e os campos que faltam ser preenchidos. Nesse caso o restante do comando não será executado
    Se alguma tarefa ainda estiver em andamento não será possível finalizar o dia, apresentando um erro mostrando que ainda há uma tarefa em andamento
    fui_dormir é preenchido com a hora atual

- Tarefa
    fim é preenchido com a hora atual
    o campo 'duracao' é preenchido automaticamente com o valor do campo ('fim' - 'inicio') - pausas
    Também usado para encerrar uma Sessão
    Encerra qualquer pausa em andamento

- Pausa
    fim é preenchido com a hora atual
    o campo 'duracao' é preenchido automaticamente com o valor do campo 'fim' - 'inicio' 

persistir-dia-no-mongodb
criar relatórios
    