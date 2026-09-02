# MCDM sobre a frente de Pareto — TOPSIS e VIKOR

A pergunta que ficou em aberto: a escolha que fizemos **por argumento de
engenharia** — três cascos, robustez à alimentação pobre — é a mesma que um
método formal de decisão multicritério escolhe?

Resposta curta: **sim, mas só depois de consertar duas coisas** — e o caminho até
lá revelou um erro mais caro que a própria escolha.

## Como foi montado

Frente gerada com o gêmeo em Python (994 projetos viáveis de 6 000 amostrados por
hipercubo latino), não com o surrogate. Critérios de viabilidade: pureza de topo
≥ 99,7 %, aproximação do condensador ≥ 5 K, R/R_min ≥ 1,1.

Quatro critérios de decisão, dois deles **de fora dos objetivos da otimização**:

| Critério | Sentido | Origem |
|---|---|---|
| `lucro` (MUSD/ano) | máx | objetivo econômico |
| `pureza` com z = 0,60 | máx | robustez — *não era objetivo* |
| `Q_refervedor` (MW) | mín | energia — era objetivo |
| `n_cascos` | mín | construtibilidade — *não era objetivo* |

Quatro cenários de peso: entropia (dados decidem), iguais, econômico
(0,55/0,15/0,20/0,10) e robustez (0,25/0,45/0,15/0,15).

E duas frentes:

- **A** — nos objetivos que o NSGA-II usou: recuperação (máx) × Q (mín)
- **B** — nos objetivos econômicos: lucro (máx) × pureza no pior caso (máx)

## ⚠️ Achado 1 — a frente errada custa 1,7 MUSD/ano

O projeto de maior lucro entre os 994 viáveis vale **63,88 MUSD/ano**.

**Ele não está na frente A.** Na verdade, o nosso próprio projeto validado
(63,16 MUSD/ano) também não está: ele é **dominado por quatro soluções da frente
A — e todas as quatro valem menos dinheiro.**

| | Melhor lucro disponível |
|---|---|
| Dentro da frente A (recuperação × Q) | 62,19 MUSD/ano |
| Dentro da frente B (lucro × robustez) | **63,88 MUSD/ano** |
| Diferença | **1,69 MUSD/ano** |

Nenhum método de decisão aplicado sobre a frente A alcança o ótimo econômico,
porque **ele foi eliminado antes da decisão começar**.

A causa é física: o lucro **não é monótono na recuperação**. Passado o degrau de
grau polímero, subir recuperação custa refluxo e não paga nada — você compra
pureza pela qual ninguém está disposto a pagar. A direção "melhor" da frente A é
economicamente ao contrário a partir de certo ponto.

> Maximizar recuperação e minimizar energia é uma **procuração** para maximizar
> lucro. A procuração falha: dá para dominar nos dois indicadores e perder um
> milhão e setecentos mil dólares por ano.

## ⚠️ Achado 2 — o peso por entropia entregou 80 % da decisão ao critério mais grosseiro

| Frente | lucro | pureza | Q | **cascos** |
|---|---|---|---|---|
| A | 0,045 | 0,062 | 0,089 | **0,805** |
| B | 0,035 | 0,043 | 0,043 | **0,878** |

A entropia de Shannon premia o critério que mais **discrimina** entre as
alternativas. Um critério que assume só dois valores — 3 ou 4 cascos — tem
dispersão máxima depois da normalização min-max: metade em 0, metade em 1.

Resultado: o método "objetivo, guiado pelos dados" concentrou ~85 % do peso no
critério de resolução mais baixa da tabela. **Peso por entropia não mede
importância — mede variância.** Em painel com critérios discretos, ele quebra.

## ⚠️ Achado 3 — a normalização do TOPSIS anula o peso que você declarou

Este é o achado mais transferível dos três.

O TOPSIS normaliza dividindo cada coluna pela sua norma euclidiana. Amplitude que
sobra para cada critério na frente A:

| Critério | Faixa bruta | Amplitude após normalização vetorial | Após min-max |
|---|---|---|---|
| lucro | 56,11 → 62,19 | 0,0305 | 1,0000 |
| **pureza z=0,60** | 99,495 → 99,938 | **0,0013** | 1,0000 |
| Q refervedor | 41,63 → 57,20 | 0,0933 | 1,0000 |
| cascos | 3 → 4 | 0,0769 | 1,0000 |

A pureza sobra com **0,0013 de amplitude — 72 vezes menos que Q**. Um critério
cuja faixa é estreita em relação ao seu valor absoluto fica mudo, e o peso
nominal multiplica um número que já é quase zero.

A consequência é concreta. No cenário **robustez**, com 45 % do peso declarado
sobre a pureza no pior caso, o TOPSIS-vetorial escolhe a solução de
**pior = 99,4950 %** — a única da frente que **perde grau polímero** na
alimentação pobre. Com quase metade do peso nominal sobre exatamente esse
critério.

Trocando a normalização por min-max, com os mesmos pesos, o TOPSIS passa a
escolher **pior = 99,9041 %**.

E a discordância entre os métodos era, em boa parte, artefato disso:

| Cenário | ρ(TOPSIS vetorial, VIKOR) | ρ(TOPSIS min-max, VIKOR) |
|---|---|---|
| iguais | +0,736 | +0,855 |
| econômico | +0,809 | **+0,991** |
| robustez | **−0,264** | **+0,755** |

> TOPSIS e VIKOR "discordam" muito menos do que a literatura sugere. O que
> discorda é a normalização vetorial com a min-max. O peso que você digita não é
> o peso que age — ele é multiplicado pelo coeficiente de variação do critério.

## O resultado, com os objetivos certos

Na frente B, os quatro cenários e os três métodos convergem quase todos para a
mesma região — e é **a região que tínhamos escolhido a mão**:

| | N | R | P (bar) | Lucro | Pior caso | Cascos |
|---|---|---|---|---|---|---|
| Escolha por engenharia (validada no DWSIM) | 240 | 18,69 | 19,00 | 63,16 | 99,5585 | 3 |
| **TOPSIS/VIKOR na frente B** | **250** | **17,70** | **18,77** | **63,82** | **99,5966** | **3** |

Mesmo número de cascos, mesma faixa de pressão, mesma faixa de refluxo. O método
formal **confirmou o julgamento de engenharia** — e ainda encontrou 0,66 MUSD/ano
a mais, com 0,04 ponto a mais de margem sobre o grau polímero e 2,2 MW a menos de
refervedor. Ele domina o nosso projeto em todos os quatro critérios.

Robustez do candidato ao longo de toda a faixa de alimentação:

| z | 0,60 | 0,65 | 0,70 | 0,75 | 0,80 | 0,85 | 0,90 |
|---|---|---|---|---|---|---|---|
| Pureza | 99,597 | 99,652 | 99,700 | 99,743 | 99,784 | 99,825 | 99,867 |

Grau polímero em toda a faixa.

## O que ainda não está confirmado

1. **O candidato não passou pelo DWSIM.** Nosso projeto atual passou. O erro
   conhecido do gêmeo a 19 bar é +0,048 ponto, na direção segura — mas o
   candidato opera a 18,77 bar com aproximação de condensador de **5,55 K**,
   contra 6,12 K do nosso. É justamente onde o modelo é mais frágil.
2. **A frente é grosseira.** 23 membros vindos de amostragem aleatória filtrada,
   não de um NSGA-II. Uma frente densa mudaria os escores, provavelmente não a
   região.
3. **O ganho não veio do MCDM.** Veio da amostragem. O que o MCDM fez foi
   *selecionar* esse ponto entre 994 — coisa que a frente de dois objetivos não
   permitia fazer.

## O que fica de método

**Decisão multicritério não conserta objetivo mal escolhido.** Ela ordena o que a
otimização deixou na mesa. Se o ótimo econômico foi dominado na frente, nenhum
peso o traz de volta.

**Peso declarado ≠ peso efetivo.** Antes de discutir pesos com o time, olhe a
amplitude de cada critério depois da normalização. Um critério medido em torno de
99,x % está desligado no TOPSIS-vetorial, com qualquer peso.

**Critério discreto quebra o peso por entropia.** Se a tabela tem "número de
cascos" ou "sim/não", o peso automático vai para lá.

**Quando os dois métodos concordam com o engenheiro, o valor não é a resposta — é
o argumento.** A escolha por três cascos já estava certa. O que o MCDM acrescentou
foi poder mostrar *sob quais pesos* ela continua certa.

## Reprodução

```bash
python3 ferramentas/rodar_mcdm.py
```

Gera `dados/mcdm-viaveis.csv` (994 projetos), `dados/mcdm-frente-pareto.csv`
(frente A) e `dados/mcdm-frente-economica.csv` (frente B). Sem dependências.
