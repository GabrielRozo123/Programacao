# Fase 3 — Procedimento Completo de Construção (CaO / rota metílica)

**Projeto:** CFD de Reator Monolítico para Biodiesel
**Autor:** Gabriel Rozo | FEQ/UNICAMP
**Base experimental:** Melo, V.M. (2023) — CaO/biochar, metanólise de óleo de soja, 65 °C

> Este documento é o **caminho limpo**: só o que funcionou, na ordem certa.
> Os becos sem saída estão na seção 9 (Armadilhas), para não serem repetidos.

---

## 1. Modelo

Reação global em uma etapa, pseudo-primeira ordem em TG:

```
TG + 3 MeOH → 3 FAME + GL

r_parede = k_cat · σ · C_TG · η        [kmol/(m²·s)]
   k_cat = 5,302e-5 m³/(kg_cat·s)      ← da curva cinética de Melo (2023)
   σ     = ρ_washcoat · δ_washcoat     [kg_cat/m²]
   η     = fator de efetividade do washcoat
```

**Origem de k_cat** — Fig. 34a de Melo (2023), CaO puro, 1 %m, MeOH:óleo 4:1, 65 °C:
```
79 % em 1 h  →  k = 1,56 h⁻¹
95 % em 2 h  →  k = 1,50 h⁻¹        pseudo-1ª ordem confirmada

k_cat = k / (m_cat/V) = 4,167e-4 / 7,86 = 5,302e-5 m³/(kg_cat·s)
```

---

## 2. Geometria

```
Arquivo: geometry/canal_pseudo2d_050um.step
Dimensões: 50 mm (x) × 1,1 mm (y) × 0,05 mm (z)
```

Renomear as faces após importar:

| Face | Nome | Tipo |
|---|---|---|
| x = 0 | `Inlet` | Velocity Inlet |
| x = 50 mm | `Outlet` | Pressure Outlet |
| y = 0 | `Bottom_Wall` | Wall |
| y = 1,1 mm | `Top_Wall` | Wall (catalítica) |
| z = 0 **e** z = 0,05 mm | `Simetria` | **Symmetry Plane** |

A espessura de 50 µm existe só para forçar **1 célula em z**. As duas faces z são Symmetry, então o campo é invariante nessa direção — é um canal plano pseudo-2D.

---

## 3. Malha

```
Meshers:  Surface Remesher · Automatic Surface Repair · Trimmed Cell · Prism Layer

Default Controls:
   Base Size                      0.05 mm
   Surface Proximity              Number of Points in Gap = 1      ← CRÍTICO
   Prism Layer Controls           1 camada (padrão, fora do Top_Wall)

Custom Surface Control → [Canal.Top_Wall]:
   Number of Prism Layers         10
   Prism Layer Stretching         1.4
   Prism Layer Total Thickness    0.1 mm  (Absolute)
```

Resultado esperado: **~286.000 células**.

A primeira camada de prisma fica em **1,43 µm**, e as 6 primeiras cobrem 23 µm — resolução suficiente para a camada limite de concentração.

> **Por que gap = 1:** com as duas faces z a 0,05 mm uma da outra, o controle de proximidade padrão (2 pontos) interpreta isso como fresta e refina o domínio inteiro — gerou 1,1 M de células desnecessárias.

---

## 4. Física

```
Space              Three Dimensional
Time               Implicit Unsteady
Material           Liquid → Multi-Component Liquid
Flow               Segregated Flow
Viscous Regime     Laminar
Species            Segregated Species
Reaction           Non-reacting
Energy             DESLIGADA
```

A energia fica desligada porque `k_cat` é constante — a temperatura não entra em lugar nenhum. Religar só quando houver Ea para montar Arrhenius.

### Propriedades da mistura — constantes

```
Mixture → Material Properties:
   Density              Constant   868 kg/m³
   Dynamic Viscosity    Constant   0.0105 Pa·s
```

> **Por que constantes e não Volume/Mass-Weighted:** desacopla o escoamento da composição.
> Com as regras de mistura, erros na espécie realimentavam a densidade, que realimentava
> a velocidade, gerando refluxo espúrio no Outlet. A variação real de densidade entre
> TG (890) e FAME (850) é de ~4% — irrelevante para o campo de velocidade.

### Espécies — quatro, nesta ordem

| Espécie | Molecular Weight (g/mol) | Molecular Diffusivity (m²/s) |
|---|---|---|
| TG (óleo de soja) | 872,0 | **7.0e-11** |
| FAME | 292,0 | **7.0e-11** |
| GL | 92,09 | **7.0e-11** |
| MeOH | 32,04 | **7.0e-11** |

> **As quatro difusividades DEVEM ser iguais.** Ver seção 9.2 — é a correção mais
> importante de toda a Fase 3.

---

## 5. Field Functions

Criar nesta ordem. A coluna `Dimensions` é o que faz os reports saírem rotulados
corretamente (o Star-CCM+ usa **kmol** como unidade molar base, por isso os pesos
moleculares entram em g/mol = kg/kmol).

| # | Nome | Dimensions | Definition |
|---|---|---|---|
| 1 | `rho_washcoat` | Mass/Length³ | `1700` |
| 2 | `delta_washcoat` | Length | `1.0e-5` |
| 3 | `washcoat_factor` | Mass/Length² | `${rho_washcoat}*${delta_washcoat}` |
| 4 | `k_cat` | Length³/(Mass·Time) | `5.302e-5` |
| 5 | `eta_washcoat` | Dimensionless | `0.62` |
| 6 | `ramp_factor` | Dimensionless | `1.0` |
| 7 | `C_TG` | Quantity/Length³ | `${Density}*max(${MassFractionTG},0.0)/872` |
| 8 | `r_wall` | Quantity/(Length²·Time) | `${k_cat}*${washcoat_factor}*${C_TG}*${eta_washcoat}*${ramp_factor}` |
| 9 | `Flux_TG` | Mass/(Length²·Time) | `-872.0*${r_wall}` |
| 10 | `Flux_FAME` | Mass/(Length²·Time) | `876.0*${r_wall}` |
| 11 | `Flux_GL` | Mass/(Length²·Time) | `92.09*${r_wall}` |
| 12 | `Flux_MeOH` | Mass/(Length²·Time) | `-96.12*${r_wall}` |

**Conferência obrigatória** — os quatro coeficientes somam zero:
```
−872,00 − 96,12 + 876,00 + 92,09 = −0,03     (0,003 %)
```
Se não somarem, falta o fator 3 em FAME (3 × 292) ou em MeOH (3 × 32,04).

**O fator de efetividade** η = 0,62 vem do módulo de Thiele, com o D_h medido por
Fonseca (2026) para CaO/Al₂O₃:
```
k_v = k_cat · ρ_wc = 5,302e-5 × 1700 = 0,0901 s⁻¹
φ   = δ·√(k_v/D_h) = 1e-5 × √(0,0901/4,4e-12) = 1,43
η   = tanh(φ)/φ = 0,62
```

| δ do washcoat | φ | η |
|---|---|---|
| 20 µm | 2,86 | 0,35 |
| **10 µm** | 1,43 | **0,62** |
| 5 µm | 0,72 | 0,86 |

---

## 6. Condições de contorno e inicial

**Composição de alimentação** (MeOH:óleo = 4:1 molar, condição de Melo 2023):
```
massa TG   = 1 × 872,0 g  = 872,0
massa MeOH = 4 ×  32,04 g = 128,2
Y_TG   = 872,0/1000,2 = 0,8719
Y_MeOH = 128,2/1000,2 = 0,1281
```

```
Inlet
   Velocity Magnitude        0.001 m/s
   Species Mass Fraction     [TG 0.8719 | FAME 0 | GL 0 | MeOH 0.1281]

Outlet
   Pressure                  0 Pa
   Species Mass Fraction     [TG 0.8719 | FAME 0 | GL 0 | MeOH 0.1281]    ← IGUAL ao Inlet

Top_Wall
   Species Flux → Composite  TG→Flux_TG · FAME→Flux_FAME · GL→Flux_GL · MeOH→Flux_MeOH

Bottom_Wall
   Species Flux → Constant   [0.0, 0.0, 0.0, 0.0]

Simetria
   Type                      Symmetry Plane

Initial Conditions → Species Mass Fraction
   [TG 0.8719 | FAME 1.0E-10 | GL 1.0E-10 | MeOH 0.1281]                  ← IGUAL ao Inlet
```

> **Igualar Inlet, Outlet e IC elimina duas coisas:** a onda de lavagem no transiente,
> e o dano do refluxo caso ele ocorra no Outlet.

---

## 7. Solver

```
Segregated Species → Under-Relaxation Factor     0,2
Stopping Criteria  → Maximum Inner Iterations    30
Implicit Unsteady  → Time-Step                   0,005 s
                   → Temporal Discretization     1st-order
```

---

## 8. Procedimento de execução

### Etapa A — escoamento (espécies congeladas)

```
1. Solvers → Segregated Species → Expert → Solver Frozen ☑
2. Rodar até os resíduos de escoamento caírem abaixo de 1e-10
3. Conferir os três:
      Velocidade na Saída      = 0,001 m/s
      Queda de Pressão         ≈ 5,2 Pa
      SEM alerta "Reversed flow"
4. File → Save As → "Fase3_escoamento_convergido.sim"
```

### Etapa B — espécies (escoamento congelado)

```
5. Solvers → Segregated Flow    → Freeze Flow    ☑
6. Solvers → Segregated Species → Solver Frozen  ☐
7. Rodar
```

> **NUNCA dê `Initialize` depois do passo 5.** Ele apaga o campo de velocidade, e com
> o Freeze Flow ligado o escoamento fica congelado em zero. Custou-nos duas rodadas.

---

## 9. Armadilhas (todas encontradas na prática)

### 9.1 Arrays de fração mássica são posicionais

Ao mudar a lista de espécies (6 → 4), os arrays de **Inlet, Outlet e Initial Conditions**
não são remapeados. O Outlet ficou com a composição antiga e, pelo refluxo, injetava
fluido de composição errada no canal.

**Sempre conferir os três arrays após qualquer mudança na lista de espécies.**

### 9.2 Difusividades desiguais quebram a conservação de massa ⚠️

O achado mais importante da Fase 3.

A documentação Siemens afirma: *"solves transport equations for all species **and ensures
that all mass fractions sum to 1**"*. Ou seja, as N equações são resolvidas e depois o
resultado é **normalizado**.

Com a lei de Fick, a soma das frações só se conserva sozinha se `Σ Dᵢ·∇Yᵢ = 0`, o que
exige **todos os D iguais**. Com os valores físicos (D_MeOH/D_TG ≈ 97), a soma deriva a
cada passo, e a normalização redistribui o erro **proporcionalmente a Yᵢ** — despejando-o
na espécie majoritária.

Medido na prática:
```
dM_TG/dt com D desiguais  :  −3,8e-9 kg/s    (374 % de erro)
dM_TG/dt com D iguais     :  −9,1081e-10     (0,013 % de erro)
Integral de Flux_TG       :  −9,1069e-10
```

**Aproximação a declarar na dissertação:** difusividades igualadas à do triglicerídeo
para garantir conservação de massa na formulação de Fick. Justificável porque as demais
espécies estão em nível de ppm e não participam da lei de taxa (pseudo-1ª ordem só em TG),
e porque é o transporte de TG que governa o Damköhler.

**Alternativa rigorosa, para o futuro:** `Segregated Species → Expert → Multi-component
Diffusion = On`, que troca Fick por Maxwell-Stefan (conservativo por construção). Exige
difusividades binárias de todos os pares.

### 9.3 Verificação deve ser por inventário, não por média na saída

A média na saída é ponderada por vazão e subestima tudo que está perto da parede, onde a
velocidade tende a zero. Como as espécies têm distribuições espaciais diferentes, a
ponderação distorce a comparação entre elas.

```
mesma condição, medida de duas formas:
   razão ΔY_FAME/ΔY_TG pela média na saída  :  0,35
   razão dM_FAME/dM_TG pelo inventário      :  0,14
```

Só o inventário responde à pergunta certa.

### 9.4 Outras

| Armadilha | Sintoma | Correção |
|---|---|---|
| Surface Proximity padrão | 1,1 M células numa geometria fina | gap = 1 |
| Regras de mistura (Volume/Mass-Weighted) | refluxo espúrio no Outlet | densidade e viscosidade constantes |
| `Initialize` após Freeze Flow | velocidade congelada em zero, divergência | nunca inicializar depois |
| Temperatura fixa nas FFs de k | varredura de T sem efeito | trocar `393.15` por `${Temperature}` antes de varrer |

---

## 10. Verificação

### Reports obrigatórios

```
Volume Integral · Parts: Canal
   M_TG    ← m_TG   = ${Density}*${MassFractionTG}
   M_FAME  ← m_FAME = ${Density}*${MassFractionFAME}

Surface Integral · Parts: Canal: Top_Wall
   Flux_TG · Flux_FAME

Surface Average · Parts: Canal: Top_Wall
   r_wall_medio · CTG_parede

Mass Flow Averaged · Parts: Canal: Outlet
   as quatro frações mássicas
```

### O teste que vale mais que todos

```
dM_TG/dt    deve igualar   Integral(Flux_TG)
dM_FAME/dt  deve igualar   Integral(Flux_FAME)
razão |dM_FAME/dM_TG|  =  1,0046
```

Exporte os monitores `M_TG` e `M_FAME` e ajuste as inclinações numa janela comum.
**Qualquer desvio acima de ~5% indica problema**, não imprecisão numérica.

### Valores esperados

| Grandeza | Início (campo fresco) | Estacionário |
|---|---|---|
| Integral de Flux_TG | −1,06e-9 kg/s | −6,1e-10 kg/s |
| C_TG na parede | 0,868 kmol/m³ | ~0,52 kmol/m³ |
| C_parede/C_bulk | 1,00 | **~0,60** |
| Conversão de TG por passe | — | **~1,5 %** |
| Queda de pressão | 5,2 Pa | 5,2 Pa |

### Regime

```
Re  = 868 × 0,001 × 1,1e-3/0,0105             = 0,091
Sc  = 0,0105/(868 × 7,0e-11)                  = 172.800
Sh  = 1,85·(Re·Sc·Dh/L)^(1/3)                 = 13,0
k_m = 8,3e-7 m/s   →   J_max = 7,2e-4 mol/(m²·s)

Da = 4,85e-4/7,2e-4 = 0,68      ← REGIME MISTO
```

Esse é o resultado central da Fase 3: com o catalisador real (CaO, ~370× mais ativo que
o ZnAl₂O₄ extrapolado da Fase 2), o Damköhler sai de 0,003 para 0,68. O sistema entra no
regime em que a geometria do monólito tem função.

---

## 11. Pendências

```
□ FECHAR O BALANÇO GLOBAL (ver seção 12) — bloqueia qualquer publicação de resultado
□ Trocar 393.15 por ${Temperature} nas FFs de k, quando houver Ea (teste de invariância antes)
□ Definir se o monólito será rota metílica (Melo) ou etílica (Fonseca, 70 °C, 1:9)
□ Medir ρ_washcoat e δ_washcoat reais — o resultado é LINEAR no produto dos dois
□ Obter ρ e μ medidos da carga real do laboratório
□ Avaliar Multi-component Diffusion (Maxwell-Stefan) quando houver difusividades binárias
```

---

## 12. Registro das corridas e o balanço global em aberto

### 12.1 Corrida de 150 s (malha sem prism layers, entrada 4:1)

Reports em t = 150,045 s:

```
Y_TG parede (Surface Average, Top_Wall)   0,4909535
Y_TG bulk   (Volume Average, Canal)       0,8491793
Y_TG saída  (Mass Flow Average, Outlet)   0,8711881
Integral de Flux_TG (Top_Wall)           -5,953611e-10  kg/s
Surface Average de r_wall                 2,731014e-07  kmol/(m²·s)
Mass Flow Inlet / Outlet                 -4,774000e-08 / +4,773998e-08 kg/s
```

**Resultado central medido:**

```
C_parede/C_bulk = 0,4909535 / 0,8491793 = 0,5782
Da = 1/0,5782 − 1 = 0,73          (previsto a priori: 0,68)
```

Regime **misto** confirmado — nem cinético nem difusional. Com o CaO real, o Da sai
de 0,003 (Fase 2) para 0,73, e a geometria do monólito passa a ter função. Isso
inverte a conclusão que consta da apresentação de seminário v2.

**Achado de projeto — o canal é curto demais:**

```
Re = 0,182     Sc = 1,73e5     Re·Sc = 3,1e4
L_entrada,massa ≈ 0,05·D_h·Re·Sc = 3,46 m   vs   L_canal = 0,05 m   →  69×
δ_c(x=L) por Lévêque = 179 µm = 16 % da altura do canal
```

A camada-limite de concentração nunca se desenvolve. O núcleo sai praticamente na
composição de entrada, e a conversão por passe num canal de 50 mm é inerentemente
baixa. Argumento para canal mais longo, velocidade menor ou reciclo.

A cadeia de FF foi verificada à mão e fecha com 6 dígitos:

```
C_TG(parede) = 868 × 0,4909535/872            = 0,488701 kmol/m³
r_wall = 5,302e-5 × 0,017 × 0,488701 × 0,62   = 2,731014e-07   ✓ idêntico
872 × r_wall × 2,5e-6                          = 5,953611e-10   ✓ idêntico
```

### 12.2 O problema em aberto: o balanço global não fecha

```
(a) X_TG pela saída            = 0,0816 %
(c) X_TG pelo FAME na saída    = 0,0817 %      ← (a) e (c) concordam
(b) X_TG pelo fluxo de parede  = 1,4303 %      ← 17,5× maior
```

Balanço em t = 150 s, com ṁ medido (não estimado):

```
consumo na parede        -5,954e-10 kg/s
saída líquida (ṁ·ΔY)     -3,399e-11 kg/s
───────────────────────────────────────
dM_TG/dt exigido         -5,614e-10 kg/s
dM_TG/dt observado       -5,227e-11 kg/s
───────────────────────────────────────
não contabilizado         5,09e-10 kg/s   (85 %)
```

O déficit aparece em TG e FAME na proporção estequiométrica exata (1,00461), ou seja,
o solver aplica uma **fração** do fluxo pedido, igual para todas as espécies. A fração
degrada conforme a parede empobrece:

```
t ≈   1,5 s   →  0,997
t ≈  15   s   →  0,932
t ≈ 150   s   →  0,145     (Y_parede = 0,491)
```

Gradiente na parede: `∂Y/∂n = J/(ρD) = 2,381e-4/(868 × 7e-11) = 3920 m⁻¹`, o que dá
ΔY ≈ 0,055 através de uma célula de 14 µm — 11 % do valor de parede. Hipótese de
trabalho: resolução de malha junto à parede.

Descartado por inspeção: não existe field function de fluxo de espécie no contorno
(busca "bou" só retorna Boundary Index, Boundary Sliver Cell Indicator, etc.), então
não há como medir o fluxo aplicado diretamente.

### 12.3 Corrida com prism layers (entrada 6:1) — teste da hipótese

Prism layers em Top_Wall e Bottom_Wall: 15 camadas, 200 µm total, stretching 1,2
(primeira camada 2,8 µm).

```
Volume de malha confirmado : M_TG(t=0)/(ρ·Y₀) = 2,7502e-9 m³  vs 2,75e-9 geométrico ✓
Condição inicial           : Y_TG = 0,81941  = 6:1 molar ✓
Estequiometria             : 1,00461  (esperado 1,004587) ✓
```

**O teste falhou em dois pontos:**

```
ΔP_analítico (Poiseuille) = 12·µ·ū·L/H² = 5,21 Pa
ΔP malha sem prisms                     = 5,430 Pa   (+4,2 %)
ΔP malha com prisms                     = 5,463 Pa   (+4,8 %)   ← piorou
```

```
desvio do balanço, malha sem prisms, t ≈ 15 s   = -6,8 %
desvio do balanço, malha com prisms, t = 21 s   = -8,9 %   ← não melhorou
```

O ΔP não se moveu na direção do valor analítico, o que sugere que as prism layers
não foram efetivamente geradas. Verificar contagem de células e cena de malha junto
à parede antes de concluir que a hipótese de resolução está errada.

### 12.4 Armadilha reencontrada

O **array de espécies do Outlet** voltou a ficar defasado do Inlet na remontagem.
Com Inlet em 6:1 (Y_TG = 0,8194), o Outlet reportou Y_TG = 0,8695 — acima da
entrada, o que é impossível. A composição da saída é internamente consistente com
uma alimentação 4,08:1, isto é, com os valores antigos.

```
REGRA: ao mudar a composição do Inlet, mudar o array do Outlet no mesmo ato.
```

Essa é a segunda vez que essa armadilha custa uma corrida. Já consta da seção 9.

---

*Novembro/2026 | Gabriel Rozo — FEQ/UNICAMP*
