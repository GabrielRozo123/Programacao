# Regressão simbólica — a equação redescoberta

Experimento com gabarito: rodamos Symbolic Regression sobre `Q_refervedor`,
para o qual conhecemos a fórmula exata do modelo. Dados:
[`dados/sr-q-refervedor.csv`](../dados/sr-q-refervedor.csv), 1000 pontos,
800 treino / 200 validação, operadores restritos a `+ − × ÷`, MAXSIZE 20,
loss MSE.

## O gabarito

```
Q [MW] = (R + 1) · (corte_pct/100) · z · F · λ(P) / 3600 / 1000
```

com `λ(P)` vindo do escalonamento de Watson sobre a temperatura de saturação
dada por Antoine — duas correlações não-lineares encadeadas.

## O que ela encontrou

```
Q = (1,0011 + razao_refluxo) · z_propeno
    · corte_pct · (0,046753 − 0,0006907 · pressao)
```

### Termo a termo

| Estrutura verdadeira | O que ela achou | Erro |
|---|---|---|
| `(R + 1)` | `(razao_refluxo + 1,0011)` | **0,11 %** |
| `× z` | `× z_propeno` | exato |
| `× corte_pct` | `× corte_pct` | exato |
| `× λ(P)` | `× (0,046753 − 0,0006907·P)` | ver abaixo |

### O termo de pressão

Ela **linearizou o calor latente**. Como `Q = (R+1)·corte_pct·z·k(P)`, o λ
implícito é `360000·k(P)`:

| P (bar) | λ do modelo | λ da equação | Erro |
|---|---|---|---|
| 14 | 13 363,5 | 13 350,0 | −0,10 % |
| 16 | 12 851,7 | 12 852,6 | +0,01 % |
| 18 | 12 352,3 | 12 355,3 | +0,02 % |
| 20 | 11 859,4 | 11 858,0 | −0,01 % |
| 22 | 11 367,5 | 11 360,7 | −0,06 % |

Menos de 0,1 % de erro em toda a faixa. **Ela recuperou o comportamento de
Watson + Antoine, encadeados, sem nunca ter visto nenhum dos dois** — só
observando 1000 valores de carga térmica.

## ✅ O teste de controle passou

`N_estagios` e `pos_alimentacao` foram deixadas no arquivo **de propósito**.
Elas não entram na fórmula, e sabíamos disso por três caminhos: a álgebra do
modelo, os índices de Sobol (0,1 % cada) e o gráfico X-vs-y (faixa vertical
sem tendência).

**Nas dez soluções da frente de Pareto, elas aparecem zero vezes.** A busca as
descartou sozinha. Não houve overfitting — e isso é consequência direta de ter
restringido os operadores a `+ − × ÷`: sem `sin`, `exp` e `pow`, a busca não
tinha com que fabricar ajuste espúrio.

## A frente de Pareto redescobriu a decomposição de variância

A solução de **complexidade 9** é:

```
Q = (razao_refluxo + 1,0418) · z_propeno · 3,3695     →  R² = 0,9736
```

Ela **descartou** `corte_pct` e `pressao`. E isso tinha sido previsto antes de
rodar, a partir dos índices de Sobol:

| | |
|---|---|
| `razao_refluxo` + `z_propeno` (Sobol S₁) | 82,6 % + 15,0 % = **97,6 %** |
| R² da equação de complexidade 9 | **97,36 %** |

Praticamente o mesmo número. A frente de Pareto é, na prática, uma
**decomposição de variância legível**: cada degrau de complexidade compra a
próxima fatia de variância explicada.

## A equação em notação de engenharia

Com `corte_pct = 100σ`, a equação descoberta se escreve:

$$Q = (R + 1)\,\sigma\,z\,(4{,}6753 - 0{,}06907\,P) \qquad [\text{MW}]$$

| Símbolo | Grandeza | Unidade |
|---|---|---|
| $Q$ | carga do refervedor | MW |
| $R$ | razão de refluxo | – |
| $\sigma$ | corte, $D/(F z)$ | – |
| $z$ | fração molar de propeno na alimentação | mol/mol |
| $P$ | pressão de operação | bar |

Válida para $F = 1000$ kmol/h; para outra vazão, multiplique por $F/1000$.

Conferência no ponto base ($R=15$, $\sigma=0{,}995$, $z=0{,}75$, $P=18$):

| | |
|---|---|
| Equação | 40,979 MW |
| Modelo rigoroso | 40,969 MW |

### E o termo de pressão é o calor latente disfarçado

$$\lambda(P) = 3600\,(4{,}6753 - 0{,}06907\,P) \qquad [\text{kJ/kmol}]$$

| P (bar) | Equação | Modelo |
|---|---|---|
| 14 | 13 350,0 | 13 363,5 |
| 18 | 12 355,3 | 12 352,3 |
| 22 | 11 360,7 | 11 367,5 |

Substituindo de volta, a equação inteira colapsa em:

$$Q = \frac{V\,\lambda(P)}{3600}, \qquad V = (R+1)\,\sigma\,z\,F$$

**A regressão simbólica não achou uma correlação empírica — achou o balanço de
energia.** "O refervedor ferve o tráfego de vapor." É a definição de
refervedor, recuperada de mil observações de carga térmica.

## Por que isso importa além da curiosidade

Um surrogate de rede neural com R² = 0,999 é uma caixa-preta: você confia ou
não. Uma **equação** de quatro termos pode ser:

- **conferida** contra a física — foi o que fizemos acima;
- **auditada** por quem não treinou o modelo;
- **colocada numa planilha** ou num CLP, sem runtime de ML;
- **extrapolada com critério**, porque a forma funcional é conhecida.

E o custo foi restringir os operadores. Se `sin`, `exp` e `pow` estivessem
ligados — como vinham por padrão — a busca teria material para ajustar ruído
numérico da ordem de 10⁻¹³ e devolver um monstro ilegível com R² igualmente
alto.

**A restrição de operadores não foi uma limitação. Foi o que produziu o
resultado.**
