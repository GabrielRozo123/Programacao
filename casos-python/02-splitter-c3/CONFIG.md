# Caso 02 — Splitter propeno/propano (C3 splitter)

Coluna binária propeno/propano em **modo rating**: fixados os estágios e as
especificações de operação, o modelo devolve purezas, cargas térmicas,
dimensionamento e economia anual. Modo rating porque é assim que a coluna
rigorosa do DWSIM se comporta — o que permite comparar ponto a ponto.

Este é o gêmeo rápido do caso DWSIM descrito em
[`docs/dwsim-splitter-c3.md`](../../docs/dwsim-splitter-c3.md).

## Por que o C3 splitter

É a separação onde o surrogate tem o maior retorno possível. Com α ≈ 1,12 a
coluna precisa de 150–250 estágios e refluxo de 12–20: a versão rigorosa é
lenta e o NSGA-III quer dezenas de milhares de avaliações. Aqui o surrogate
deixa de ser enfeite e passa a ser o que **viabiliza** a otimização.

E a economia tem um degrau real: propeno grau polímero (≥ 99,5 % mol) vale
US$ 1150/t, grau químico US$ 950/t, e fora de especificação vira GLP a
US$ 550/t. O ótimo encosta na especificação por cima — que é exatamente o
dilema de projeto de uma unidade de verdade.

## Caso base (valores padrão)

| Grandeza | Valor | Comentário |
|---|---|---|
| Pureza de topo | 98,51 % mol | **grau químico — não atinge polímero** |
| Pureza de fundo | 94,15 % mol propano | GLP |
| Recuperação de propeno | 98,02 % | |
| α no topo / no fundo | 1,0757 / 1,1736 | varia 9 % ao longo da coluna |
| Refervedor / condensador | 42,3 MW | dominante no OPEX |
| T topo / T fundo | 43,6 / 52,1 °C | calibrado contra o DWSIM |
| Diâmetro | 4,44 m | |
| Altura | 145 m em 3 cascos | splitters reais são cascos em série |
| N/Nmin | 3,34 | acima do típico — a coluna está sobredimensionada em estágios e ainda assim não fecha a especificação |
| R/Rmin | 1,25 | faixa típica 1,1–1,5 |
| CAPEX instalado | 41,4 MUSD | |
| OPEX | 11,7 MUSD/ano | ~96 % é vapor |
| Lucro | 15,3 MUSD/ano | derrubado pelo rebaixamento de grau |

## Duas decisões de modelagem que valem para qualquer caso

**Alimentação como fração, não como número de prato.** Se `estagio_alim` e
`N_estagios` forem variáveis independentes, o DOE gera combinações com
alimentação acima do topo. Usando `pos_alimentacao` ∈ [0,3; 0,7] como fração de
N, *toda* combinação é viável.

**Corte relativo ao propeno alimentado, não a D/F.** Com `D/F` fixo e `z_propeno`
variando, boa parte do domínio vira projeto impossível — com `z = 0,60` e
`D/F = 0,82` a pureza de topo não passa de 73 %, faça o que fizer. Definindo
`corte = D/(F·z)`, a recuperação fica entre 97 % e 99,9 % **para qualquer
composição de alimentação**:

| corte | z=0,60 | z=0,75 | z=0,90 |
|---|---|---|---|
| 0,975 | 96,9 % | 97,4 % | 97,5 % |
| 0,990 | 98,4 % | 98,9 % | 99,0 % |
| 1,000 | 99,3 % | 99,9 % | 100,0 % |

A lição é geral: **reparametrizar é mais barato que descartar pontos**. Num DOE
de 500 rodadas na nuvem, a diferença entre as duas formulações são centenas de
simulações jogadas fora.

## Variáveis de entrada

| Name | Cell | Unit | Type | Default | Min | Max | Step |
|---|---|---|---|---|---|---|---|
| N_estagios | `N_estagios` | - | Discrete | 200 | 100 | 260 | 10 |
| pos_alimentacao | `pos_alimentacao` | - | Continuous | 0.5 | 0.3 | 0.7 | — |
| razao_refluxo | `razao_refluxo` | - | Continuous | 15 | 8 | 24 | — |
| corte | `corte` | - | Continuous | 0.995 | 0.97 | 0.999 | — |
| pressao | `pressao` | bar | Continuous | 18 | 14 | 22 | — |
| z_propeno | `z_propeno` | - | Continuous | 0.75 | 0.6 | 0.9 | — |
| F_alimentacao | `F_alimentacao` | kmol/h | Fixed | 1000 | — | — | — |

## Variáveis de saída

| Name | Cell | Unit | Papel |
|---|---|---|---|
| pureza_topo | `pureza_topo` | % mol | **restrição** (≥ 99,5) |
| pureza_fundo | `pureza_fundo` | % mol | resposta |
| recuperacao | `recuperacao` | % | **objetivo** (maximizar) |
| grau_produto | `grau_produto` | - | diagnóstico (2/1/0) |
| Q_refervedor | `Q_refervedor` | MW | **objetivo** (minimizar) |
| Q_condensador | `Q_condensador` | MW | resposta |
| T_condensador | `T_condensador` | °C | resposta |
| T_refervedor | `T_refervedor` | °C | resposta |
| precisa_refrig | `precisa_refrig` | - | **restrição** (= 0) |
| diametro | `diametro` | m | resposta |
| altura_total | `altura_total` | m | resposta |
| n_cascos | `n_cascos` | - | diagnóstico |
| alfa_topo | `alfa_topo` | - | diagnóstico |
| alfa_fundo | `alfa_fundo` | - | diagnóstico |
| N_min | `N_min` | - | diagnóstico (Fenske, média geométrica de α) |
| R_min | `R_min` | - | diagnóstico (Underwood) |
| R_sobre_Rmin | `R_sobre_Rmin` | - | diagnóstico |
| CAPEX | `CAPEX` | MUSD | resposta |
| CAPEX_anual | `CAPEX_anual` | MUSD/ano | resposta |
| OPEX | `OPEX` | MUSD/ano | **objetivo** (minimizar) |
| custo_total | `custo_total` | MUSD/ano | resposta |
| lucro | `lucro` | MUSD/ano | **objetivo** (maximizar) |
| convergiu | `convergiu` | - | diagnóstico |

## Validação local

```bash
python3 ferramentas/validar_caso.py casos-python/02-splitter-c3/simulate.py --n 300
```

Resultado esperado: 300/300 convergidos, ~22 ms por run. O DOE varre pureza de
85 % a 100 %, lucro de −81 a +82 MUSD/ano e cerca de 30 % dos projetos
exigindo refrigeração.

## α(x, P) calibrado contra o DWSIM

A volatilidade relativa **não é constante** e o modelo deixou de tratá-la como
tal. A superfície abaixo foi ajustada a seis medições de flash PVF no DWSIM
10.2.3.0 com Peng-Robinson.

**Com a composição, a 18 bar:**

| x propeno (líquido) | α medido |
|---|---|
| 0,00919 | 1,177690 |
| 0,04618 | 1,174670 |
| 0,48435 | 1,133423 |
| 0,74063 | 1,105152 |
| 0,94817 | 1,080285 |
| 0,98964 | 1,075116 |

Ajuste `ln α` quadrático em x, rms = 1,2 × 10⁻⁵. Um termo cúbico baixa o rms
para 3,7 × 10⁻⁶, mas o ganho é menor que a própria resolução dos dados — não
vale o parâmetro extra com seis pontos.

**Com a pressão, a x ≈ 0,74:**

| P (bar) | α medido |
|---|---|
| 14 | 1,119362 |
| 18 | 1,105152 |
| 22 | 1,092456 |

Linear, inclinação **−0,003363 por bar**, resíduos ~2,5 × 10⁻⁴.

```
α(x, P) = exp(0,164200 − 0,068679·x − 0,024311·x²) − 0,003363·(P − 18)
```

As medições vão de x = 0,009 a x = 0,990, cobrindo toda a faixa útil da coluna:
**a superfície não extrapola em nenhum ponto de operação.**

### Por que isso importa tanto

α cai de ~1,178 no fundo para ~1,076 no topo — quase 10 %. Como `N_min` é
proporcional a `1/ln α` e `ln α` é minúsculo nessa faixa, **separar no topo é
mais de 50 % mais difícil que no fundo**. Tratar α como constante era o maior
erro deste modelo, muito maior que o erro de 1 % corrigido antes.

O efeito no caso base é brutal: a pureza de topo caiu de 99,55 % para 98,51 %.
**O projeto deixou de atingir grau polímero** e o lucro despencou de 65,6 para
15,4 MUSD/ano, porque o produto foi rebaixado de US$ 1150/t para US$ 950/t.

### Validação da extrapolação

O ajuste feito só com os quatro primeiros pontos previa α nos dois pontos ricos
em propeno **antes** de eles serem medidos:

| x propeno | previsto | medido | erro |
|---|---|---|---|
| 0,948167 | 1,080221 | 1,080285 | −0,01 % |
| 0,989642 | 1,075035 | 1,075116 | −0,01 % |

A forma funcional estava certa, e a conclusão sobre o grau do produto se
confirmou.

### Antoine reancorado

Os dois pontos quase puros também expuseram um viés nas constantes de Antoine.
Extrapolando as medições a 18 bar ao componente puro:

| Componente | DWSIM | Antoine original | Viés |
|---|---|---|---|
| Propeno | 43,631 °C | 44,153 °C | +0,522 °C |
| Propano | 52,093 °C | 52,382 °C | +0,289 °C |

Ambos corriam quentes. O intercepto `A` foi reancorado (mantendo `B` e `C`,
o que preserva a forma da curva): propeno 4,182428 e propano 4,283326. A
ancoragem é de um ponto só, adequada na faixa estreita de 14 a 22 bar.

Consequência prática: o limiar de refrigeração — o ponto em que o condensador
cai abaixo de 40 °C e a água de resfriamento deixa de servir — se desloca de
16,42 para **16,61 bar**, dentro da faixa do DOE.

## O projeto que realmente atinge grau polímero

Com α(x, P) calibrado, **N = 200 e R = 15 não fecham a especificação** — param
em 98,51 %. Varrendo o refluxo mínimo necessário para 99,5 % em cada número de
estágios (z = 0,75, P = 18 bar, corte = 0,995):

| N | R mínimo | Q refervedor (MW) | Diâmetro (m) | Custo (MUSD/ano) | Lucro (MUSD/ano) |
|---|---|---|---|---|---|
| 150 | 26,25 | 72,0 | 5,79 | 26,11 | 56,52 |
| 175 | 22,33 | 61,7 | 5,36 | 23,38 | 59,25 |
| 200 | 20,19 | 56,0 | 5,11 | 21,89 | 60,74 |
| 250 | 17,66 | 49,3 | 4,79 | 20,32 | 62,31 |
| **275** | **16,85** | **47,2** | **4,69** | **20,16** | **62,47** |
| **300** | **16,28** | **45,7** | **4,61** | **19,96** | **62,67** |
| 350 | 15,43 | 43,4 | 4,50 | 20,04 | 62,59 |
| 400 | 14,85 | 41,9 | 4,42 | 20,13 | 62,50 |

O ótimo fica em torno de **N = 275–300 com R ≈ 16,3**, rendendo 62,7 MUSD/ano
contra 15,3 do projeto original. Duas leituras que valem mais que o número:

- **A 200 estágios o refluxo tem de subir de 15 para 20,2** para fechar a
  especificação, e o refervedor sai de 42 para 56 MW. Estágio e refluxo são
  substitutos, e o preço de economizar aço é energia — para sempre.
- **O ótimo é chatíssimo de plano.** De N = 250 a N = 400 o lucro varia menos
  de 0,6 %. Isso é típico de destilação e tem consequência prática: a escolha
  final não sai da economia, sai de restrição de altura, de layout ou de
  perda de carga — coisas que este modelo não vê e o DWSIM vê.

## Roteiro na plataforma

1. **DOE** — LHS com 500 pontos. Não use Full Factorial: com 6 variáveis ativas
   e `N_estagios` discreto, o fatorial explode sem cobrir o interior.
2. **Analysis** — a pergunta interessante é `pressao → lucro`. Espere
   correlação linear fraca: o efeito da pressão é não-monotônico, porque baixar
   a pressão aumenta α (menos estágios) mas empurra o condensador para
   refrigeração. HSIC e ξ de Chatterjee enxergam isso; Pearson não.
3. **Surrogate** — treine sobre `pureza_topo`, `Q_refervedor` e `lucro`.
   `lucro` é o alvo difícil: tem degrau nos limites de 99,5 % e 92 % de pureza.
   Compare quem aprende o degrau.
4. **Validation** — Williams Plot, procurando os pontos na fronteira de grau.
5. **Optimization** — NSGA-II com dois objetivos: maximizar `lucro`, minimizar
   `Q_refervedor`. Restrições: `pureza_topo ≥ 99,5` e `precisa_refrig = 0`.
6. **MCDM** — TOPSIS sobre o Pareto, variando os pesos entre lucro e energia.
7. **Validação cruzada** — leve os 5 melhores pontos do Pareto para o DWSIM
   rigoroso e meça o erro do atalho. Esta etapa é o que separa o estudo sério
   da demonstração bonita.

## Limitações declaradas

Nenhuma destas hipóteses vale exatamente — e é por isso que o DWSIM existe
neste projeto:

- α constante ao longo da coluna, corrigido só pela pressão. O valor rigoroso
  varia com a composição.
- Fluxo molar constante (CMO): ignora o balanço de energia estágio a estágio.
- Perda de carga desprezada. Numa coluna de 145 m com 235 pratos, a perda real
  é de vários bar e altera α no fundo.
- Custos são estimativas fatoradas de ordem de grandeza, úteis para **comparar**
  alternativas. Viabilidade exige estimativa formal.

## Extensões

- Condição térmica da alimentação `q` como variável: pré-aquecer troca carga do
  refervedor por área de trocador.
- **Bomba de calor por recompressão de vapor.** O condensador está a 44 °C e o
  refervedor a 52 °C — 8 K de diferença. Comprimir o vapor de topo para aquecer
  o fundo elimina quase todo o vapor de baixa. É assim que muitos splitters C3
  modernos operam, e o payback costuma ser de poucos anos. Como projeto de
  otimização, é excelente: troca-se OPEX de vapor por OPEX de eletricidade mais
  CAPEX de compressor.
- Coluna de parede dividida, se houver um terceiro componente na alimentação.
