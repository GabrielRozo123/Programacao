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

## 7. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `memorial.py` | Todos os cálculos acima, executável e comentado |

---

## 8. Pendências

- **Figura 3 do Ferrario** — geometria do distribuidor aranha. O texto diz "6 braços de tubos de
  aço de 0,12 m de diâmetro", o que é impossível numa coluna de 0,24 m: 0,12 m é o **raio**, logo
  deve ser o comprimento do braço. Falta também o **número de furos por braço**.
- Definir se a Fase 2 roda na coluna do Darmana (validação ponto a ponto) ou na do Ferrario
  (escala industrial, validação por correlação).
