O intuito deste diário é fazer uma análise da performance dos meus estudos a partir de dados como:
-------------------------------------------------------------------------------------------------------------------------------------------

Dados relacionais
-Data (chave primária)
-Hora que acordei
-Hora que dormi no dia anterior
-Hora que levantei da cama
-Hora que fui dormir
-Término do café da manhã
-Horário de almoço
-Folga (boolean)
-Pontuação de 1 a 5, de acordo com critérios pré-estabelecidos:
    1. Concentração durante estudos 
        1 = Não me concentrei em nenhum momento 
        2 = Me concentrei em poucos momentos 
        3 = Tive distrações, mas me concentrei principalmente no estudo
        4 = Tive poucas distrações
        5 = Quase nenhuma distração, esqueci que o mundo existia pela maior parte do dia
    2. Performance durante exercício físico
        1 = Me senti cansado ou travado, não consegui me exercitar
        2 = Me exercitei muito pouco
        3 = Senti que poderia ter feito mais, mas satisfatório
        4 = Senti que me exercitei o suficiente
        5 = Superhomem
    3. Ativação mental
        1 = Cabeça não parou o dia inteiro, suspeitei ser esquizofrênico
        2 = Poucos momentos de silêncio mental
        3 = Escutei vozes, mas consegui trabalhar em paralelo com elas
        4 = Vários momentos de silêncio
        5 = Vozes da minha cabeça fizeram voto de silêncio
    4. Procrastinação
        1 = Não fiz absolutamente nada
        2 = Travado a maior parte do tempo, provavelmente fiz o começo de uma tarefa mas não concluí
        3 = Procrastinei, mas consegui concluir tarefas
        4 = Procrastinei muito pouco, iniciei tarefas rapidamente e em sequência
        5 = Pareceu até que eu sou normal
    5. Compulsão alimentar
        1 = Quis comer a padaria inteira, não me controlei
        2 = Quis comer a padaria inteira, me controlei mas me atrapalhou
        3 = Quis comer a padaria inteira, me controlei e não me atrapalhou ou atrapalhou pouco
        4 = Vontade passageira de comer fora da rotina, esqueci rápido
        5 = Disciplina robótica
    6. Estresse
        1 = Estresse extremo, explodi e agi por impulso
        2 = Me estressei bastante, não explodi mas posso ter sido grosso
        3 = Me estressei, mas não afetou meu comportamento
        4 = Leve estresse, boa parte do dia sem estresse algum
        5 = Smoke weed everyday
    7. Qualidade do sono
        1 = Demorei a dormir, acordei durante a noite e acordei mais cedo que o normal
        2 = Demorei a dormir, acordei durante a noite ou acordei mais cedo que o normal
        3 = Tive uma das três insônias, me afetou
        4 = Tive uma das três insônias, mas foi muito leve e não me afetou
        5 = Dormi como rei e acordei me sentindo completamente descansado
    8. Vontade de beber alcóol
        1 = Extrema necessidade de beber, bebi e passei do limite
        2 = Extrema necessidade de beber, bebi e fiquei próximo ao limite
        3 = Senti vontade de beber, não bebi ou bebi pouco
        4 = Leve vontade de beber, mas não senti nenhuma necessidade
        5 = Esqueci que alcóol existe
    9. Sexo e masturbação
        1 = Pensei em sexo o dia inteiro, me atrapalhou e me masturbei mais de uma vez
        2 = Pensei em sexo o dia inteiro, me atrapalhou
        3 = Pensei em sexo frequentemente e me atrapalhou um pouco
        4 = Pensei em sexo, não me atrapalhou
        5 = Casto e puro
    10. Motivação
        1 = Sem motivação para lazer, só perdi tempo com reels e shorts
        2 = Fiquei motivado somente para lazer
        3 = Fiquei motivado para lazer e estudo
        4 = Fiquei muito motivado para estudo
        5 = Fiquei motivado o dia inteiro, não queria parar de estudar

Calculadas:
-Quantidade de sessões de exercício físico
-Hora que comecei a estudar
-Quantidade de sessões de estudo
-------------------------------------------------------------------------------------------------------------------------------------------

Documentos
-Tarefas iniciadas e concluídas no dia
-Relatório de cada sessão de estudo
    Tempo cronometrado de cada sessão de estudo
-Relatório de cada sessão de exercício
    -Tempo de exercício físico
-Relatório geral do dia inteiro
-Relatório de trabalho
-Relatório de performance
-------------------------------------------------------------------------------------------------------------------------------------------

Se inicia um dia:
Um Relatório é gerado a partir de um modelo, contendo todos os dados relacionais a serem preenchidos durante o dia
Colunas novas podem ser adicionadas a qualquer momento, de forma modular

Cada Tarefa será um objeto novo. Assim que o objeto é criado será registrado o horário de início e um cronômetro, que pode ser pausado a qualquer momento.

Todos os Objetos serão tarefas. Apenas alguns, como sessão de estudo, terão classe própria. Outras tarefas como almoço, banho e outros serão tarefas genéricas com um campo de descrição para especificar o que é cada tarefa.

Objetos (Podem variar na quantidade por dia)
Tarefa (classe mãe)
Sessão de estudo
Sessão de exercício físico

Relatórios (Apenas um por dia)
Relatório diário (Todos os dados relacionais)