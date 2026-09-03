# Texto do post — LinkedIn

Duas versões. A longa carrega o argumento sozinha; a curta deixa o carrossel
carregar. Gancho nas duas primeiras linhas (é o que aparece antes do "ver
mais"), sem link no corpo — o link do repositório vai no primeiro comentário.
Marcar AI4TECH e Prof. Nicolas Spogis como menções reais, não hashtag.

## Versão longa

Um décimo de ponto percentual de pureza vale 50 milhões de dólares por ano.

Não é força de expressão — é o que a simulação mediu.

Passei as últimas semanas com um splitter de propeno/propano, a destilação mais difícil que existe numa petroquímica. As duas moléculas fervem quase à mesma temperatura: são 240 estágios teóricos e refluxo 18,7 para separá-las.

Mas o que torna o caso interessante não é a coluna. É o preço.

Acima de 99,5 % de pureza o produto é grau polímero e vale US$ 1.150/t. Abaixo, é grau químico: US$ 950/t. O preço não é contínuo — tem um degrau. E a coluna não sabe disso. Numa unidade de 250 mil toneladas por ano, meio ponto de refluxo separa um lucro de 14 milhões de um de 65.

Modelei no DWSIM, calibrei um modelo rápido contra ele e rodei a esteira da AI4Tech Suite:

→ DOE por hipercubo latino, 1.000 pontos
→ Índices de Sobol via Random Forest — o que realmente move o resultado
→ Regressão simbólica, que reencontrou o balanço de energia da coluna sozinha
→ Surrogate por processo gaussiano
→ Otimização multiobjetivo NSGA-II
→ Decisão multicritério (TOPSIS e VIKOR) sobre a frente de Pareto

Três coisas que eu não esperava:

1️⃣ A maior influência isolada sobre o lucro não é o refluxo nem o número de estágios. É a composição da alimentação — a única variável que ninguém controla.

2️⃣ Das 100 soluções ótimas propostas pelo otimizador, 45 violavam a especificação quando reavaliadas no simulador rigoroso. Otimizar sobre modelo aproximado sem validar entrega quase metade de projeto que não funciona.

3️⃣ O projeto de maior lucro era o único que perdia grau polímero quando a alimentação empobrecia. Abrir mão de 100 mil dólares por ano de margem evita um risco de 50 milhões.

E é aqui que a conversa deixa de ser sobre uma coluna.

Uma planta tem dezenas de unidades acopladas — cada uma com seu degrau de preço, seu compromisso entre energia e pureza, seu distúrbio de carga. Otimizar unidade por unidade entrega a soma dos ótimos locais, que não é o ótimo da planta.

O que muda de escala não é a técnica. É o custeio. O otimizador melhora exatamente aquilo que você custeia e distribui de graça o que ficou fora da planilha. No meu caso foi o quarto casco da coluna. Numa planta inteira, é o header de vapor, a temperatura de retorno da água de resfriamento, a especificação de carga da unidade seguinte.

Resultado final, medido na coluna rigorosa e não previsto por modelo: 63,08 MUSD/ano contra 15,25 do ponto de partida. Quatro vezes o lucro, com 21 % mais energia.

Qual unidade da sua planta você acha que tem um degrau de preço escondido?

#EngenhariaQuímica #SimulaçãoDeProcessos #DWSIM #MachineLearning #Otimização

## Versão curta

Um décimo de ponto percentual de pureza vale 50 milhões de dólares por ano.

Acima de 99,5 % o propeno é grau polímero e vale US$ 1.150/t. Abaixo, é grau químico: US$ 950/t. O preço tem um degrau — e a coluna não sabe disso.

Modelei um splitter C3 no DWSIM, calibrei um modelo rápido contra ele e rodei DOE, índices de Sobol, regressão simbólica, surrogate e NSGA-II na AI4Tech Suite. Três achados que não esperava:

→ A maior influência sobre o lucro é a composição da alimentação: a única variável que ninguém controla.
→ Das 100 soluções ótimas, 45 violavam a especificação ao voltarem para o simulador rigoroso.
→ O projeto mais lucrativo era o único que perdia o grau com alimentação pobre.

Do ponto de partida ao projeto validado: 15,25 → 63,08 MUSD/ano.

Qual unidade da sua planta tem um degrau de preço escondido?

#EngenhariaQuímica #SimulaçãoDeProcessos #DWSIM #MachineLearning #Otimização

## De onde vem cada número

| Afirmação no texto | Origem |
|---|---|
| 240 estágios, refluxo 18,7 | projeto final validado no DWSIM |
| US$ 1.150/t e US$ 950/t | `PRECO_GRAU_POLIMERO` e `PRECO_GRAU_QUIMICO` |
| 250 mil t/ano de propeno | 749 kmol/h de destilado × 42,08 kg/kmol × 8 000 h |
| lucro de 14 para 65 milhões | varredura de refluxo: 14,33 em R = 16,872⁻ e 64,78 em 16,872⁺ |
| 50 milhões por décimo de ponto | o salto acima, 50,46 MUSD/ano |
| alimentação é a maior influência | índice de Sobol do lucro: 39,3 % contra 37,3 % do refluxo |
| 45 de 100 violavam | `docs/otimizacao-resultado.md` |
| 100 mil contra 50 milhões | 0,10 MUSD/ano de lucro nominal contra o degrau de grau |
| 15,25 → 63,08 MUSD/ano | projeto inicial (N=200, R=15) e final, ambos no gêmeo calibrado |
| 21 % mais energia | 40,8 → 49,6 MW de refervedor |

**O que o texto deliberadamente não faz:** estimar o ganho de uma planta
inteira. O estudo é de uma coluna. O argumento de escala é estrutural — a
técnica é a mesma, o que quebra é o custeio quando as unidades se acoplam —
e não numérico.
