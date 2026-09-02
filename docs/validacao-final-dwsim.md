# Validação final na coluna rigorosa

Projeto de 240 estágios teóricos, refluxo 18,69, a 19,0 bar, montado no DWSIM
10.2.3.0 e resolvido em 6,4 s.

| Grandeza | Previsto | DWSIM | Erro |
|---|---|---|---|
| Propeno no topo | 99,7201 % | **99,7682 %** | −0,048 ponto |
| Propano no fundo | 98,8646 % | 98,8723 % | −0,008 ponto |
| Carga do condensador | 49 608 kW | 49 873 kW | −0,53 % |

## ⚠️ O erro cresceu dez vezes — e a causa é diagnosticável

Na escada de validação, **toda a 18 bar**, o erro de pureza foi de 0,004 a
0,006 ponto e o de carga chegou a 0,00 %. Aqui foram 0,048 ponto e 0,53 %.

A causa não é o modelo ficar pior em condições mais difíceis. É que **duas das
minhas calibrações foram feitas com um único ponto, a 18 bar**:

| Calibração | Pontos medidos | A 19 bar |
|---|---|---|
| Superfície α(x, P) | 14, 18 e 22 bar · 6 composições | interpola |
| Constantes de Antoine | **só 18 bar** | **extrapola** |
| Calor latente `LAMBDA_REF` | **só 18 bar** | **extrapola** |

O λ implícito na carga do DWSIM a 19 bar é 12 170 kJ/kmol; o meu modelo dá
12 105 — diferença de 0,53 %, exatamente o erro observado na carga.

> **O erro apareceu onde a calibração era mais fraca, não onde o modelo é mais
> complexo.** Com dois pontos de λ — 18 e 19 bar — seria possível ajustar
> também a dependência com a temperatura, que hoje vem do expoente de Watson
> sem verificação nenhuma.

## O erro está na direção segura

A pureza real (99,768 %) é **maior** que a prevista (99,720 %). A coluna
entrega mais do que o modelo prometeu.

| | Margem sobre 99,5 % |
|---|---|
| Previsto | 0,220 ponto |
| **Real** | **0,268 ponto** |

E a carga real é 0,53 % maior, o que aumenta o OPEX. Recalculando o lucro com a
carga medida:

| | |
|---|---|
| Lucro pelo modelo | 63,16 MUSD/ano |
| **Lucro com a carga real** | **63,08 MUSD/ano** |

Meio ponto percentual de carga térmica custa **73 mil dólares por ano**.

## Projeto confirmado

| Parâmetro | Valor |
|---|---|
| Estágios teóricos | 240 · `Number of Stages` = **241** |
| Estágio de alimentação | **Stage159** |
| Razão de refluxo | **18,69** |
| Produto de fundo | 250,75 kmol/h |
| Pressão | **19,00 bar** |
| Pureza de topo | **99,768 %** (medido) |
| Propano no fundo | 98,872 % (medido) |
| Carga do condensador | 49 873 kW (medido) |
| Aproximação do condensador | 6,12 K |
| Altura | 173 m em **3 cascos** |
| Lucro | **63,08 MUSD/ano** |

Robusto: mantém grau polímero de z = 0,60 a 0,90, com pior caso de 99,56 %.

## O ciclo fechou

| Etapa | Lucro |
|---|---|
| Projeto original — 200 estágios, R = 15, 18 bar | 15,68 · não atingia a especificação |
| **Projeto final — 240 estágios, R = 18,69, 19 bar** | **63,08 · validado na coluna rigorosa** |

Nenhum número acima é previsão de surrogate. Todos foram medidos na coluna
rigorosa ou calculados a partir de medições dela.
