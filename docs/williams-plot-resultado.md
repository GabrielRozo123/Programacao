# Williams Plot — o que ele disse, e o que eu errei

| | |
|---|---|
| Pontos no domínio de aplicabilidade | **984 / 1000 (98,4 %)** |
| h* (limite de alavancagem) | 0,018 |
| **Alta alavancagem** | **0** |
| **Resposta anômala** (\|σ\| > 3) | **16** |
| Ambos | 0 |
| Max \|σ\| | 23,01 |

## ❌ A previsão que eu fiz, e por que estava errada

Eu previ que a região de alta alavancagem cairia na faixa de 99,4 a 99,6 % de
pureza, onde só há 63 dos 1000 pontos. **Não há um único ponto de alta
alavancagem.**

O erro foi conceitual. **Alavancagem mede o quanto um ponto é extremo no espaço
de ENTRADA**, via matriz chapéu — não tem relação com densidade na saída. E o
limite bate exatamente com a fórmula padrão:

$$h^* = \\frac{3p}{n} = \\frac{3 \\times 6}{1000} = 0{,}018$$

**LHS distribui os pontos uniformemente no espaço de entrada por construção.**
Nenhum ponto é extrapolação em relação aos outros. Com DOE por LHS, o eixo de
alavancagem passa quase de graça — o eixo informativo é o de resíduo.

Eu confundi *"região escassa na saída"* com *"ponto extremo na entrada"*. São
coisas diferentes, e a faixa de 99,4–99,6 % é escassa na **saída**.

> **Lição para qualquer caso:** num DOE por LHS, alta alavancagem no Williams
> Plot é praticamente impossível. Se aparecer, suspeite do DOE, não do modelo.

## ✅ O que ele encontrou de verdade: 16 falhas dentro do domínio

Os 16 pontos anômalos têm **alavancagem normal** — o modelo erra em regiões
bem amostradas, não nas bordas. Isso é mais preocupante que extrapolação, e
tem explicação física.

Calculando a sensibilidade local $\\partial(\\text{pureza})/\\partial R$ nos 1000
pontos:

| | |
|---|---|
| Mediana | 0,284 ponto por unidade de R |
| Percentil 95 | 1,827 |
| Máximo | **2,817** (10× a mediana) |

E os 16 pontos de maior sensibilidade têm todos a mesma assinatura:

| | 16 mais sensíveis | Conjunto todo |
|---|---|---|
| R/Rmin médio | **1,006** | 1,375 |

**São colunas operando no refluxo mínimo** — no pinch, onde a pureza desaba com
qualquer redução de refluxo. Não é falta de dados: é **curvatura extrema num
lugar bem amostrado**. Nenhum modelo suave aproxima bem uma função que muda de
2,8 pontos por unidade de R.

## O remédio não é mais dados — é definir o domínio corretamente

R/Rmin = 1,00 significa **estágios infinitos**. Ninguém projeta coluna ali. A
prática padrão é R/Rmin entre **1,1 e 1,5**, e o nosso próprio projeto validado
opera em 1,25.

Ou seja: **a região onde o surrogate falha é uma região onde não se projeta.**

Duas consequências práticas:

1. **Declare o domínio de validade do surrogate:** válido para
   **R/Rmin ≥ 1,1**. Isso não é maquiar dado — é definir a faixa de
   aplicabilidade, que é exatamente o que o Williams Plot serve para
   estabelecer.

2. **Restrinja o otimizador à mesma faixa.** Adicionar `R_sobre_Rmin ≥ 1,1`
   como restrição faz duas coisas de uma vez: impõe boa prática de projeto e
   mantém o otimizador fora da região ruim do surrogate.

Não vale retreinar agora. 98,4 % no domínio já é bom, as falhas estão onde não
interessa, e a incerteza do GPR sinaliza esses casos de qualquer forma.
