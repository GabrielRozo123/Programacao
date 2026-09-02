# Coluna de bolhas de grande diâmetro — hidrodinâmica e quimissorção de CO₂ em NaOH

Estudo em duas fases, com dupla finalidade: validação publicável e material de apresentação para
disciplina de cinética e reatores.

---

## 0. As duas âncoras

| Fase | Referência | O que ancora |
|---|---|---|
| **1 — hidrodinâmica** | Ferrario, Varallo, Besagni & Mereu (2025), *Chem. Eng. Sci.* **302**, 120792 — **acesso aberto, CC BY** | holdup de gás, transição de regime, distribuição de tamanho de bolha |
| **2 — reação** | Darmana, Henket, Deen & Kuipers (2007), *Chem. Eng. Sci.* **62**, 2556–2575 | cinética, solubilidade, difusividade, k_L, fator de intensificação |

A Fase 1 valida o conjunto de fechamentos. A Fase 2 usa o mesmo conjunto para entregar o que
correlação nenhuma dá: **onde**, dentro do reator, a reação acontece.

---

## 1. A coluna (Ferrario et al., 2025)

| | |
|---|---|
| Diâmetro interno | **0,240 m** |
| Altura da coluna | **5,30 m** |
| Líquido acima do distribuidor | **3,00 m** (razão de aspecto 12,5) |
| Volume de líquido | 135,7 L |
| Modo | **batelada** — sem vazão de líquido |
| Fases | água de torneira + **ar** ou **CO₂** |
| Temperatura | 295,15 ± 1 K |
| Distribuidor | **aranha, 6 braços, furos de 2 mm** (grosseiro) |

### Coluna de grande diâmetro — verificado

```
D*_H = d_c / √(σ / g(ρ_l − ρ_g)) = 88,2        critério: > 52
```

O artigo reporta 88,13; o memorial reproduz 88,2. Acima do critério, **não existe regime de slug** —
o que descarta o artefato mais comum de coluna de laboratório.

### Condições e holdup de referência

Ajuste de Wallis do próprio artigo (Richardson–Zaki, n = 2), com `u∞ = 0,314 m/s` (ar) e
`0,292 m/s` (CO₂):

```
J_drift = u∞ ε (1−ε)²      e, em batelada,     J_drift = U_g (1−ε)
        →     U_g = u∞ ε (1−ε)
```

| U_g [m/s] | ε ar | ε CO₂ | Q_gás [NL/min] |
|---|---|---|---|
| 0,0037 | 0,0119 | 0,0128 | 10,0 |
| 0,0076 | 0,0248 | 0,0267 | 20,6 |
| 0,0115 | 0,0381 | 0,0411 | 31,2 |
| 0,0154 | 0,0517 | 0,0559 | 41,8 |
| 0,0193 | 0,0658 | 0,0712 | 52,4 |
| 0,0223 | 0,0769 | 0,0833 | 60,5 |

**Transição de regime medida:** `U_g,trans = 0,028 m/s`, com `ε_trans = 0,098` (ar) e `0,110` (CO₂).

Toda a faixa acima está **abaixo** da transição — regime poli-disperso homogêneo. Isso simplifica o
CFD de forma decisiva: não é preciso resolver estruturas induzidas por coalescência.

Incerteza experimental declarada: ε_g em média 4,1% (ar) e 3,3% (CO₂); U_g em 7,8%.

---

## 2. O achado que define a modelagem

A distribuição de tamanho de bolha medida é **bimodal** abaixo de U_g = 0,0154 m/s:

```
pico 1    d_eq = 0,67 mm
pico 2    d_eq = 4 a 6 mm
```

E o sinal da força de sustentação inverte em **d_cr = 5,2 mm** (Ziegenhein & Lucas, 2019):

| | sustentação | para onde migra |
|---|---|---|
| bolha < 5,2 mm | **positiva** | **parede** |
| bolha > 5,2 mm | **negativa** | **centro** |

As duas populações medidas **atravessam essa fronteira**. Elas vão para lados opostos da coluna.

> Um EMP de diâmetro único coloca todo o gás no mesmo lugar e erra o campo de holdup **por
> construção**, não por falta de malha. O caso exige no mínimo dois grupos de tamanho —
> AMUSIG multi-velocidade ou S-Gamma.

Esse é o resultado técnico central da Fase 1, e ele é verificável: basta rodar o caso com diâmetro
único e com dois grupos, e comparar o perfil radial de holdup.

---

## 3. A reação (Darmana et al., 2007, Apêndice A)

```
CO₂(aq) + OH⁻  ⇌  HCO₃⁻       k₁,₁ / k₁,₂     ← etapa lenta, controla
HCO₃⁻   + OH⁻  ⇌  CO₃²⁻       k₂,₁ / k₂,₂     ← transferência de próton, ~10¹⁰
```

Fechamento completo, todo implementado em `memorial.py`:

| Grandeza | Fonte |
|---|---|
| `log k∞₁,₁ = 11,895 − 2382/T` | Pohorecki & Moniuk (1988) |
| `log(k₁,₁/k∞₁,₁) = 0,221 I − 0,016 I²` | idem, correção de força iônica |
| `D_w,CO₂ = 2,35×10⁻⁶ exp(−2119/T)` | Versteeg & van Swaaij (1988) |
| `D/D_w = 1 − 1,29×10⁻⁴ [OH⁻]` | Ratcliff & Holdcroft (1963) |
| `H_w = 3,59×10⁻⁷ R T exp(2044/T)` (adimensional) | Versteeg & van Swaaij (1988) |
| `log(H_w/H) = Σ(h_i + h_g)c_i` — *salting-out* | Weisenberger & Schumpe (1996) |
| `Sh = 2 + 0,015 Re^0,89 Sc^0,7` | Brauer (1981) |
| `E` a partir de `Ha` e `E∞` | Westerterp et al. (1984) |

### O número que decide o projeto

```
Ha = √(k₁,₁ · D_CO₂ · [OH⁻]) / k_L
```

Para bolha de 4 mm a 0,23 m/s, CO₂ puro a 1 atm, 293 K (`k_L = 2,43×10⁻⁴ m/s`):

| [NaOH] | pH | **Ha** | E∞ | **E** | H | regime |
|---|---|---|---|---|---|---|
| 0,032 | 12,50 | **2,33** | 1,3 | 1,29 | 0,878 | intermediária |
| 0,100 | 13,00 | **4,22** | 3,3 | 2,58 | 0,770 | **rápida — área manda** |
| 0,300 | 13,48 | **7,68** | 12,7 | 5,93 | 0,524 | rápida |
| 0,500 | 13,70 | **10,41** | 30,2 | 8,94 | 0,356 | rápida |
| 1,000 | 14,00 | **16,48** | 156,0 | 15,71 | 0,136 | rápida |

**O experimento E2 do Darmana parte de pH 12,5 e o pH cai durante a corrida.** O reator, portanto,
**atravessa regimes de Hatta ao longo do tempo**: começa com a reação no filme (área interfacial
manda, aumentar volume não adianta) e termina no seio (volume manda).

Nenhum modelo de reator ideal — mistura perfeita, dispersão axial, pistão — captura essa troca de
regime, porque todos assumem um único ambiente de reação. É esse o argumento da apresentação.

Repare também no `H`: o *salting-out* derruba a solubilidade do CO₂ em **6,5 vezes** entre água
quase pura e NaOH 1 M. Ignorar isso, como faz boa parte dos trabalhos, erra a força motriz por
ordem de grandeza.

---

## 4. Coluna do Darmana (Fase 2, geometria de validação)

Pseudo-2D, para permitir PIV e análise de imagem:

| | |
|---|---|
| Dimensões | **200 mm × 30 mm × 1500 mm** |
| Nível de líquido | 1000 mm |
| Distribuidor | **21 agulhas**, ID 1 mm, passo quadrado de 5 mm, no centro do fundo |
| Caso E1 | água bidestilada + N₂ — **sem reação** |
| Caso E2 | NaOH pH inicial 12,5 + **CO₂ puro** |
| Medidas | PIV (velocidade de bolha), pH transiente, holdup integral, BSD |

O caso E1 valida a hidrodinâmica isolada; o E2 acrescenta reação sobre a mesma geometria. Essa
separação é o que permite atribuir erro a hidrodinâmica ou a transferência de massa, e não aos dois
juntos.

> Os próprios autores registram que o modelo **subestima a transferência de massa global**, e
> atribuem isso ao fechamento de k_L. É um alvo declarado, não uma armadilha — e é exatamente o tipo
> de discrepância que rende discussão numa apresentação.

---

## 5. Pilha no STAR-CCM+

```
Eulerian Multiphase (EMP)              ← não é VOF nem MMP
     fase contínua: água
     fase dispersa: ar / CO₂

Distribuição de tamanho: AMUSIG multi-velocidade (≥ 2 grupos)   ← obrigatório, ver §2

Phase Interaction:
     Arrasto                Tomiyama
     Sustentação            Tomiyama   ← inverte de sinal em 5,2 mm; é o parâmetro central
     Dispersão turbulenta   Burns
     Massa virtual
     Lubrificação de parede

Turbulência: k-ε na fase contínua + turbulência induzida por bolha (Sato)
Topo: DEGASSING BOUNDARY  ← sai gás, não sai líquido
Implicit Unsteady — obrigatório (a pluma meandra)
```

### Custo

```
volume = π/4 × 0,24² × 3,0 = 0,136 m³ de líquido (domínio até 5,3 m)
célula de 10 mm  →  ~24 células no diâmetro
transiente, 100 s de tempo físico para estatística
```

De 1 a 3 dias por condição. Planejar **duas ou três velocidades superficiais**, não a curva inteira.

---

## 6. Entregáveis

### Para o LinkedIn
- campo de holdup mostrando a heterogeneidade que a correlação esconde
- vídeo da pluma meandrando
- curva ε_g × U_g sobreposta ao experimento

### Para a apresentação
- confronto CFD × modelos ideais de reator, com o erro quantificado
- mapa de Ha local e do fator de intensificação
- fração do volume do reator que efetivamente reage
- a troca de regime de Hatta ao longo da batelada

---

## 6.5. Resultados — Nível 0 (só arrasto), U_g = 0,0115 m/s

Estratégia adotada depois de o modelo completo (EMP + AMUSIG multi-speed + 5 grupos +
sustentação + dispersão + lubrificação + quebra + coalescência + turbulência induzida) divergir
45% do experimento **sem possibilidade de atribuir o erro**: dez submodelos acoplados para
reproduzir um escalar.

A saída foi **construir em degraus**, cada um validado contra uma medida específica.

### Nível 0 — o mínimo que pode produzir o alvo

```
EMP, duas fases
diâmetro FIXO de 4,5 mm  (lei de Tate a partir do furo de 2 mm)
Drag = Tomiyama, Contaminated
Gravity
k-ε de mistura

sem AMUSIG, sem sustentação, sem massa virtual, sem dispersão turbulenta,
sem lubrificação de parede, sem quebra, sem coalescência, sem turbulência induzida
```

Dois parâmetros no modelo inteiro: o diâmetro e a correlação de arrasto.

### Verificação — o solver contra a teoria

| grandeza | CFD | analítico |
|---|---|---|
| **Slip velocity** | **0,232910 a 0,233752 m/s** | **0,233 m/s** (Tomiyama, 4,5 mm) |

Uniforme em todo o domínio, **0,4% de espalhamento**, três algarismos significativos contra o
valor de bancada. Isso é **verificação**: o código resolve corretamente as equações escolhidas.

### Resultado

| | valor |
|---|---|
| ε (média volumétrica) | **0,04984** |
| u_gás = U_g/ε | 0,2316 m/s |
| velocidade do líquido | ±0,03 m/s — praticamente parado |
| perfil radial | plano, variação < 0,1% |

| contra | desvio |
|---|---|
| método do enxame (ε = 0,0409) | **+21,7%** |
| ajuste de Wallis (ε = 0,0381) | **+30,8%** |

### ⚠ O alvo experimental é uma faixa, não um ponto

Os **dois métodos do próprio artigo discordam em 7%**:

```
ajuste de Wallis   (u∞ = 0,314 m/s)   →   ε = 0,0381
método do enxame   (u   = 0,282 m/s)   →   ε = 0,0409
```

Comparar contra um só seria escolher o que favorece. A faixa vai para o texto.

### O desvio está inteiramente explicado

```
CFD Nível 0   slip = 0,2333 m/s    ← bolha isolada, exato
coluna real          0,282 m/s     ← 21% mais rápido
```

Os 21,7% de erro no holdup **são** os 21% de aceleração coletiva que o modelo não possui — por
construção, já que todo modelo capaz de produzi-la foi removido. Não sobra resíduo inexplicado.

---

## 6.6. Histórico das rodadas — onde o estudo está

Todas em U_g = 0,0115 m/s, malha de 10 mm, 113 449 células, batelada.
Alvo experimental: **ε = 0,0381 (ajuste de Wallis) a 0,0408 (ajuste de enxame)**.

| rodada | o que mudou | ε | slip [m/s] | perfil radial |
|---|---|---|---|---|
| **Nível 0** | arrasto + gravidade, d_b = 4,5 mm | 0,049844 | 0,2329–0,2338 | liso |
| **Nível 1** | + sustentação, dispersão turbulenta, lubrificação de parede | 0,049853 | 0,2330–0,2331 | liso (0,02%) |
| **Nível 1b** | + semente radial na entrada (Field Function) | 0,049795 | 0,229–0,238 | estrutura só no fundo |
| **Nível 1c** | + Particle Induced Turbulence Source | 0,049604 | 0,220–0,239 | liso (0,02%) |
| **A** (remontagem) | idem 1c, montagem refeita do zero | 0,049430 | 0,233 | liso |
| **E** | S-Gamma dirigindo a Interaction Length Scale | ~0,0338 ⚠ | — | 0,5% na parede ⚠ |

⚠ A rodada E **não está convergida**: o acoplamento de duas vias só fechou aos 43 s, quando a
Interaction Length Scale passou de constante para o diâmetro de Sauter. O d₃₂ caiu de 30,6 para
18,8 mm e ainda derivava aos 59 s.

**Quatro rodadas, o holdup não se moveu: 0,0498 → 0,0496.** Isso não é fracasso —
cada uma respondeu uma pergunta, e as respostas convergem para a mesma causa.

### O que cada rodada estabeleceu

**Nível 0 — verificação exata.** Slip 0,2329–0,2338 contra Tomiyama analítico 0,2330.
Três algarismos significativos. O solver está certo; o modelo é que é incompleto.

**Nível 1 — resultado nulo, e o nulo tinha duas causas.** As três forças são todas
proporcionais a gradientes (F_L ∝ u_r × ∇×u_c, F_TD ∝ −∇α). Campo uniforme → gradientes
zero → forças zero → campo uniforme. Estado estável e degenerado, sem semente.
*A segunda causa só apareceu no Nível 1c.*

**Nível 1b — a semente funciona, mas não sobrevive.** A Field Function na entrada
criou estrutura radial pela primeira vez. Ela morre nos primeiros ~40 cm.

**Nível 1c — a turbulência estava desligada.** Balanço de energia (ver `balanco_energia.py`):
em batelada e regime permanente toda a potência do empuxo entra no líquido pelo arrasto e
tem de dissipar, o que dá 0,12 m²/s³ **sem CFD nenhum**. O caso reportava 4,3e-4 — fator 281.
Faltava `Particle Induced Turbulence Source`. Com ela ligada, ε_diss saltou 67× para
0,0285 m²/s³ e o holdup não se mexeu, como previsto.

### A rodada E cerca o alvo — a hipótese do diâmetro está confirmada

```
                              eps   vs enxame   vs Wallis
    A  d = 4,5 mm fixo    0.04943      +21,2%      +29,8%
           alvo enxame    0.04078           0      + 7,1%
           alvo Wallis    0.03807      − 6,6%           0
            E  S-Gamma    0.03380      −17,1%      −11,2%
```

**As duas rodadas cercam a faixa experimental.** O diâmetro não só é o lever certo — ele move o
holdup através do alvo inteiro. Nenhum outro candidato testado (contaminação, Simonnet, circulação)
chegava a 3% do necessário.

O S-Gamma previu **d₃₂ = 18,8 mm sem nenhum parâmetro ajustado**, contra 14,1 a 16,9 mm exigidos
pelo holdup medido — excesso de 11 a 33%.

### Verificação cruzada: S-Gamma contra Martinez-Bazan

| | valor |
|---|---|
| ε_diss do modelo | 0,0285 m²/s³ |
| d_crit de Martinez-Bazan nessa dissipação | 17,1 mm |
| d₃₂ de equilíbrio do S-Gamma | 18,8 mm |

Duas formulações independentes — um método de momentos com kernels de Chesters e um critério
algébrico de quebra turbulenta — param no mesmo lugar, dentro de 10%. Isso é verificação, não
coincidência: o S-Gamma está parando onde a física de quebra diz que ele deve parar.

### E isso fecha a conta da dissipação

| d₃₂ [mm] | ε_diss necessária | origem |
|---|---|---|
| 14,1 | 0,0460 | exigido pelo ajuste de enxame |
| **16,9** | **0,0296** | exigido pelo ajuste de Wallis |
| 18,8 | 0,0226 | o que o modelo entrega hoje |
| 9,6 | 0,1211 | balanço mecânico total |

O alvo de Wallis exige ε_diss = 0,0296 e o modelo entrega **0,0285** — 4% de diferença. Ou seja,
contra esse ajuste o modelo é praticamente autoconsistente, e o fator 4 que sobrava contra o balanço
mecânico está explicado: a parcela da potência do arrasto que vira cascata turbulenta é justamente a
que a coluna precisa para sustentar bolhas de ~17 mm.

### A causa única: o diâmetro prescrito

Tudo converge para a Interaction Length Scale fixada em **4,5 mm** (lei de Tate, formação
no furo). Esse valor estraga **duas** coisas ao mesmo tempo — ver `diagnostico_slip.py`:

```
   4,5 mm cai no MÍNIMO da curva de velocidade terminal
       →  u_term = 0,233 m/s  →  holdup superestimado em 21 a 31%

   4,5 mm cai ABAIXO do diâmetro de inversão da sustentação (5,8 mm)
       →  C_L = +0,268  →  gás migra para a PAREDE, sem pluma central
```

Coluna de grande diâmetro tem pluma **central**, o que exige C_L **negativo**, o que
exige **d > 5,8 mm**. Não existe tempo de máquina que conserte isso com 4,5 mm fixo.

### Candidatos descartados, com número

| candidato | efeito | veredito |
|---|---|---|
| estado de contaminação | ramo de Eötvös domina a 4,5 mm nas 3 variantes | **inerte** |
| correção de enxame (Simonnet) | f → 1/(1−ε) em ε baixo: **−2,5%**, lado errado | **inerte até ε ≈ 0,2** |
| circulação (C₀ de Zuber-Findlay) | em batelada ⟨j⟩ = U_g, 20× menor que o slip; exigiria C₀ = 7,0 | **teto de ~1%** |
| **diâmetro** | 16 mm → u_term 0,296, ε 0,0405, C_L −0,27 | **único com magnitude** |

### Moda não é d₃₂ — a reconciliação com a BSD medida

O artigo mede modas de 0,67 e 4–6 mm. Isso é densidade de **número**. O arrasto responde
ao diâmetro de Sauter, que pesa d³/d² e é dominado pela **cauda**:

```
  n de 20 mm   % do número   % do volume     d10     d32
           0          0.0%          0.0%    2.83    4.92
         100          4.8%         86.5%    3.65   14.14
```

5% das bolhas em 20 mm carregam 87% do gás e levam o d₃₂ de 4,9 para 14 mm — **sem mexer
em nenhuma das duas modas medidas**. A BSD do artigo e um d₃₂ grande são compatíveis.

E o mesmo d₃₂ governa a área interfacial `a = 6ε/d₃₂` da Fase 2: errar d₃₂ por 3× erra
o k_L·a por 3×.

---

## 6.7. Próximo passo — varredura de diâmetro

A faixa defensável para o diâmetro máximo estável ficou entre **10 e 17 mm**, dependendo
de qual dissipação alimenta o critério de Martinez-Bazan:

| ε_diss usado | valor [m²/s³] | d_crit [mm] |
|---|---|---|
| medido com BIT (cascata turbulenta) | 0,0285 | 17,1 |
| balanço de energia (mecânica total) | 0,1197 | 9,6 |

Martinez-Bazan pede a flutuação **na escala da bolha**, que vem da cascata — logo 17 mm.
Mas o balanço mostra que a cascata é só 24% da dissipação mecânica, e essa diferença não
está fechada.

**Como a faixa é ampla, escolher um valor seria escolher o que dá certo.** Então a próxima
etapa não é um diâmetro:

> **Três rodadas, trocando só a Interaction Length Scale: 8, 12 e 16 mm.**

O entregável não é um ponto que bate — é a **curva ε(d)** cruzando a faixa experimental,
com a leitura *"a coluna se comporta como se o d₃₂ fosse X mm"*.

A varredura entrega **duas** observáveis pelo preço de uma:

1. **ε(d)** — onde cruza 0,0381–0,0408
2. **a pluma** — o C_L inverte entre 4,5 e 8 mm, então a estrutura radial deve *aparecer*
   em algum ponto da varredura. Se aparecer em 8 mm e não em 4,5, o mecanismo fica provado
   diretamente, sem argumento.

Registrar em cada rodada: monitor de ε, line probe radial de VF, cena de VF.

### Previsão falsificável, registrada antes de rodar

- **d₃₂ entre 15 e 18 mm reproduz o holdup** → a hipótese do diâmetro fecha, e o Nível 2
  ganha uma meta independente: **prever** esse d₃₂ sozinho.
- **holdup cai mas a pluma não aparece** → o problema é dispersão turbulenta alta demais.
- **nada muda** → a hipótese morre inteira e o erro é do arrasto.

Os três desfechos são publicáveis. É isso que separa verificação de ajuste de curva.

---

## 6.8. Depois da varredura

| nível | o que entra | valida contra |
|---|---|---|
| 2 | AMUSIG multi-speed, quebra (Martinez-Bazan), coalescência (Luo) | **BSD parede vs centro**, e o d₃₂ previsto contra o da varredura |
| Fase 2 | quimissorção CO₂/NaOH na coluna do Darmana | E1 hidrodinâmica (PIV), E2 reação (pH transiente nos primeiros 60 s) |

Faltam ainda as outras duas condições de U_g (0,0037 e 0,0223), a rodar **depois** que o
modelo estiver fechado — não antes.

---

## 7. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `memorial.py` | Fase 1 (hidrodinâmica) e Fase 2 (quimissorção), executável e comentado |
| `gerar_coluna.py` | Gera um STEP por condição, com altura = altura aerada |
| `diagnostico_slip.py` | De onde vem a diferença de holdup: descarta contaminação, Simonnet e circulação; isola o diâmetro; C_L de Tomiyama; moda vs d₃₂ |
| `balanco_energia.py` | Balanço de energia da coluna; detectou o BIT desligado; registra a rodada 1c |

---

## 8. Pendências

- **Varredura de diâmetro (8 / 12 / 16 mm)** — o próximo passo imediato.
- **O fator 4 na dissipação.** ε_diss medido com BIT é 24% do balanço mecânico. A leitura
  que sustento é que balanço = dissipação mecânica total e ε do modelo = parcela que vira
  cascata, e parte do trabalho do arrasto dissipa direto na interface. Vale conferir se o
  fechamento do STAR tem coeficiente inspecionável.
- **Figura 3 do Ferrario** — geometria do distribuidor aranha. O texto diz "6 braços de tubos
  de aço de 0,12 m de diâmetro", o que é impossível numa coluna de 0,24 m: 0,12 m é o **raio**,
  logo deve ser o comprimento do braço. Falta o **número de furos por braço** (presumidos 10).
- **Reports órfãos** da era AMUSIG (`d32_Centro`, `d32_Parede`, slip por grupo) — deletar,
  estão gerando "Non-finite value detected".
- Definir se a Fase 2 roda na coluna do Darmana (validação ponto a ponto) ou na do Ferrario
  (escala industrial, validação por correlação). **Decidido: Darmana**, E1 depois E2.
