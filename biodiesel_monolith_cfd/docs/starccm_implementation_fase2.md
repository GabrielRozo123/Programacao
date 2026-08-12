# STAR-CCM+ — Implementação Fase 2: Reação de Superfície (Transesterificação Heterogênea)
**Projeto Mestrado Gabriel Rozo | FEQ/UNICAMP | 2025–2027**

> **Referência cinética:** Allain, F. et al. (2015). *Chemical Engineering Journal*, 281, 654–664.
> DOI: [10.1016/j.cej.2015.07.075](https://doi.org/10.1016/j.cej.2015.07.075)
>
> Reator de leito fixo com catalisador sólido ZnAl₂O₄. Transesterificação de triolein + metanol.
> Modelo "Clássico" de segunda ordem reversível com três reações em série.

---

## Seção 1: Escolha do Modelo Cinético e Justificativa

### 1.1 Dois modelos avaliados no artigo

O artigo de Allain et al. (2015) propõe e ajusta dois modelos cinéticos distintos:

| Aspecto | Modelo Clássico (Eqs. 5–7) | Modelo Eley-Rideal (Eqs. 8–10) |
|---|---|---|
| Tipo | Segunda ordem reversível — lei de potência | Mecanismo de superfície com adsorção |
| Soma dos quadrados dos resíduos (LS) | **0,022** | 0,044 |
| Ajuste aos dados | **Melhor** | Pior (2× maior LS) |
| Número de parâmetros | 9 (k1⁰, k2⁰, k3⁰, Ea1, Ea2, Ea3, K1, K2, K3) | 12 (inclui K_A, K_G, K_MeOH) |
| Implementação no STAR-CCM+ | Mais simples | Mais complexa |

**Decisão: usar o Modelo Clássico.** Justificativa tripla:
1. Melhor ajuste estatístico (LS = 0,022 vs. 0,044 — redução de 50% no erro).
2. Menor número de parâmetros — menor risco de overfitting ao extrapolar para 120°C.
3. Implementação mais direta no STAR-CCM+ via Field Functions.

### 1.2 As três reações do Modelo Clássico

O sistema consiste em três reações reversíveis em série. Cada glicerídeo perde um ácido graxo para o metanol sequencialmente:

```
Reação 1:  TG  + MeOH  <-->  DG  + FAME     (triglicerídeo → diglicerídeo)
Reação 2:  DG  + MeOH  <-->  MG  + FAME     (diglicerídeo → monoglicerídeo)
Reação 3:  MG  + MeOH  <-->  GL  + FAME     (monoglicerídeo → glicerol)
```

**Expressão matemática da taxa (Equações 5–7 do artigo):**

```
r₁ = k₁⁰ · exp(-Ea₁/RT) · [ C_TG · C_MeOH  −  (1/K₁) · C_DG · C_FAME ]

r₂ = k₂⁰ · exp(-Ea₂/RT) · [ C_DG · C_MeOH  −  (1/K₂) · C_MG · C_FAME ]

r₃ = k₃⁰ · exp(-Ea₃/RT) · [ C_MG · C_MeOH  −  (1/K₃) · C_GL · C_FAME ]
```

Onde:
- `r_i` em mol·s⁻¹·kg_cat⁻¹ (base em massa de catalisador)
- `k_i⁰` em m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹ (fator pré-exponencial)
- `C_X` em mol·m⁻³ (concentrações volumétricas)
- `K_i` adimensional (constante de equilíbrio)

### 1.3 Parâmetros cinéticos (Tabelas 6 e 7 — modelo de concentrações, melhor ajuste)

| Parâmetro | Valor | Incerteza | Unidade |
|---|---|---|---|
| k₁⁰ | 1,26 × 10⁻² | ± 7,4 × 10⁻⁴ | m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹ |
| k₂⁰ | 8,88 × 10⁻⁶ | ± 2,8 × 10⁻⁶ | m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹ |
| k₃⁰ | 1,28 × 10⁻⁷ | ± 3,3 × 10⁻⁸ | m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹ |
| Ea₁ | 64,6 × 10³ | ± 2,4 × 10³ | J·mol⁻¹ |
| Ea₂ | 31,8 × 10³ | ± 1,5 × 10³ | J·mol⁻¹ |
| Ea₃ | 17,0 × 10³ | ± 2,4 × 10³ | J·mol⁻¹ |
| K₁ | 51,2 | ± 3,9 | — |
| K₂ | 53,1 | ± 4,6 | — |
| K₃ | 12,2 | ± 0,6 | — |

**Constantes de taxa calculadas por Arrhenius (Tabela 8 — validação cruzada):**

| T | k₁ (×10⁻¹⁰ m⁶/mol/kgcat/s) | k₂ (×10⁻⁹) | k₃ (×10⁻⁹) |
|---|---|---|---|
| 160°C | 2,1 (artigo: 2,1) | 1,3 (artigo: 1,3) | 1,1 (artigo: 1,1) |
| 185°C | 5,6 (artigo: 5,6) | 2,1 (artigo: 2,1) | 1,5 (artigo: 1,5) |
| 200°C | 9,3 (artigo: 9,3) | 2,7 (artigo: 2,7) | 1,7 (artigo: 1,7) |

**Extrapolação para T = 120°C (projeto):**

```
k₁(120°C) ≈ 1,26×10⁻² · exp(-64600 / (8,314 × 393,15)) ≈ 1,7×10⁻¹¹  m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹
k₂(120°C) ≈ 8,88×10⁻⁶ · exp(-31800 / (8,314 × 393,15)) ≈ 7,0×10⁻¹⁰  m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹
k₃(120°C) ≈ 1,28×10⁻⁷ · exp(-17000 / (8,314 × 393,15)) ≈ 4,8×10⁻¹⁰  m⁶·mol⁻¹·s⁻¹·kg_cat⁻¹
```

> **Atenção:** T = 120°C está **abaixo** da faixa experimental do artigo (140–220°C).
> Trata-se de extrapolação. A cinética a 120°C é ~17× mais lenta do que a 185°C para a reação 1.
> Mencionar explicitamente como limitação na dissertação.

---

## Seção 2: Conversão de Unidades para o STAR-CCM+

### 2.1 O problema: unidades incompatíveis

O artigo fornece taxas de reação em base de **massa de catalisador**:
```
r_artigo  [mol · kgcat⁻¹ · s⁻¹]   ←  base: reator de leito fixo
```

O STAR-CCM+ com Surface Reaction Boundary Condition exige taxas em base de **área de parede**:
```
r_wall    [mol · m⁻²_wall · s⁻¹]  ←  base: superfície catalítica do washcoat
```

### 2.2 Derivação do fator de conversão

A massa de catalisador por unidade de área de parede é dada pelo produto:

```
[kgcat / m²_wall] = ρ_washcoat [kg/m³] × δ_washcoat [m]
```

Onde:
- **ρ_washcoat = 1188 kg/m³** — densidade do catalisador ZnAl₂O₄ (Tabela 1 do artigo)
- **δ_washcoat = 20 × 10⁻⁶ m** — espessura do washcoat assumida (20 µm, típico de monólito cerâmico)

```
Fator = 1188 × 20×10⁻⁶ = 0,02376  kgcat/m²_wall
```

Portanto:

```
r_wall [mol/(m²_wall·s)] = r_vol [mol/(kgcat·s)] × 0,02376
```

### 2.3 Estequiometria e fluxos de espécie na parede

A conversão da taxa para fluxo de massa de espécie `[kg/(m²·s)]` usa os pesos moleculares:

| Espécie | M (kg/mol) | Reação 1 | Reação 2 | Reação 3 | Fluxo total na parede [kg/(m²·s)] |
|---|---|---|---|---|---|
| TG | 0,8854 | −1 | 0 | 0 | `−0,8854 × r1_wall` |
| DG | 0,6210 | +1 | −1 | 0 | `+0,6210 × (r1_wall − r2_wall)` |
| MG | 0,3570 | 0 | +1 | −1 | `+0,3570 × (r2_wall − r3_wall)` |
| MeOH | 0,0320 | −1 | −1 | −1 | `−0,0320 × (r1_wall + r2_wall + r3_wall)` |
| FAME | 0,2970 | +1 | +1 | +1 | `+0,2970 × (r1_wall + r2_wall + r3_wall)` |
| GL | 0,0920 | 0 | 0 | +1 | `+0,0920 × r3_wall` |

> **Verificação de balanço de massa:** a soma de todos os fluxos deve ser zero (sem geração líquida de massa). Checar após implementação: `Integral(Species Flux) ≈ 0` na parede catalítica.

---

## Seção 3: Passo a Passo STAR-CCM+ — Caminho Exato na Árvore

### 3.1 Pré-requisito: Fase 1 convergida

Antes de iniciar a Fase 2, a simulação de escoamento a frio (Fase 1) deve estar convergida com:
- Residuais de continuidade e momento < 1×10⁻⁶
- Perfil de velocidade de Poiseuille validado na saída (u_max ≈ 1,5 × u_média)

### PASSO 1 — Adicionar Espécies (Multi-Component Liquid)

**Caminho na árvore do STAR-CCM+:**

```
[Simulation Tree]
└── Continuum (nome do seu continuum, ex: "Fluid Physics")
    └── Physics Models
        └── [clicar em "Edit Models..." ou botão direito → "Edit"]
            ☑ Selecionar: Multi-Component Liquid
               → Confirmar → cria automaticamente o nó "Mixture"
```

**Adicionar as 6 espécies:**

```
Continuum → Models → Multi-Component Liquid → Mixture → Mixture Components
  → botão direito → "Add Component" → criar cada uma:

  Componentes (ordem sugerida — solvente por último):
    1. TG      (Triglyceride — triolein)
    2. DG      (Diglyceride)
    3. MG      (Monoglyceride)
    4. FAME    (Fatty Acid Methyl Ester)
    5. GL      (Glycerol)
    6. MeOH    (Methanol) ← declarar como componente "solvente" (base)
```

**Propriedades de cada componente (clicar em cada um e preencher):**

```
Para cada espécie em: Mixture → Mixture Components → [Nome] → Material Properties:

  TG (Triolein):
    Molecular Weight:     885,4 g/mol
    Diffusivity (Fickian): 1,27×10⁻¹⁰  m²/s   ← Tabela 12 corrigida para 120°C
    (Notar: D_TG_ref = 0,17×10⁻⁹ m²/s a 185°C, corrigido para 120°C via D∝T/µ)

  DG (Diglyceride):
    Molecular Weight:     621,0 g/mol
    Diffusivity:          2,90×10⁻⁹  m²/s

  MG (Monoglyceride):
    Molecular Weight:     357,0 g/mol
    Diffusivity:          1,15×10⁻⁸  m²/s

  MeOH (Methanol):
    Molecular Weight:      32,0 g/mol
    Diffusivity:           1,27×10⁻⁸  m²/s

  FAME (Methyl Oleate):
    Molecular Weight:     297,0 g/mol
    Diffusivity:           6,73×10⁻⁹  m²/s

  GL (Glycerol):
    Molecular Weight:      92,0 g/mol
    Diffusivity:           7,20×10⁻⁹  m²/s
```

> **Nota sobre difusão:** O STAR-CCM+ usa difusão de Fick para Multi-Component Liquid.
> Definir `Diffusivity` de cada componente individualmente em `Material Properties → Diffusivity`.
> Selecionar `Constant` e inserir o valor numérico.

**Condições de contorno de espécie na entrada (Inlet):**

**Derivação da composição de entrada (razão molar MeOH:TG = 6:1):**

```
6 mol MeOH : 1 mol TG

  massa TG   = 1 × 885,4 g/mol = 885,4 g
  massa MeOH = 6 ×  32,0 g/mol = 192,0 g
  massa total                   = 1077,4 g

  Y_TG   = 885,4 / 1077,4 = 0,8218
  Y_MeOH = 192,0 / 1077,4 = 0,1782
```

```
Boundaries → Inlet → Physics Conditions → Species:
  Mass Fraction TG:    0,8218
  Mass Fraction MeOH:  0,1782
  Mass Fraction DG:    0,00
  Mass Fraction MG:    0,00
  Mass Fraction FAME:  0,00
  Mass Fraction GL:    0,00
```

> **Atenção:** A soma das frações mássicas deve ser exatamente 1,0.
> Se usar 6 espécies, a última declarada é calculada como `1 − soma_das_outras`.
> Ou declarar explicitamente todas as 6 frações e verificar a soma no solver.

> **⚠️ Correção (v2):** versões anteriores deste documento traziam
> `Y_TG = 0,88 / Y_MeOH = 0,12`. Esses valores correspondem a uma razão
> molar de **3,77:1**, não aos 6:1 especificados no projeto — o metanol
> ficava 37% abaixo do previsto. Sempre derivar a fração mássica a partir
> da razão molar, nunca arredondar "de olho".

---

### PASSO 2 — Adicionar Equação de Energia (Fluid Temperature)

```
Continuum → Physics Models → Edit Models...
  ☑ Selecionar: Fluid Temperature
     → Confirmar → cria nó "Temperature" e solver de energia
```

**Propriedades térmicas do fluido:**

```
Continuum → Models → Liquid → [nome do fluido] → Material Properties:
  Thermal Conductivity: 0,17  W/(m·K)
  Specific Heat:        2000  J/(kg·K)
```

**Condição de contorno térmica na parede catalítica:**

O artigo de Allain et al. (2015) afirma explicitamente:
> *"Transesterification reactions are regularly considered isothermal in the literature as their standard reaction enthalpy are close to 0 J·K⁻¹"*

Portanto: **ΔH_rxn ≈ 0 → fonte de calor da reação é desprezível → parede isotérmica.**

```
Boundaries → Top Wall (parede catalítica) → Physics Conditions:
  Thermal Specification: Temperature Wall
  Temperature: 393,15 K  (120°C)
```

> **Simplificação justificada:** Com ΔH_rxn ≈ 0, a condição de parede isotérmica é fisicamente
> correta. Não é necessário implementar acoplamento CHT ou fonte de energia na parede.
> Isso simplifica significativamente a Fase 2.

---

### PASSO 3 — Criar as Field Functions de Concentração

As concentrações molares precisam ser calculadas a partir das frações mássicas e da densidade local.

**Caminho:**
```
[Simulation Tree]
└── Tools
    └── Field Functions
        → botão direito → "New" → "User Field Function"
```

**Criar 6 Field Functions de concentração (uma por espécie):**

```
Nome: C_TG
Tipo: Scalar
Definição:
  $$Density * $$MassFraction_TG / 0.8854

  → Unidade: mol/m³ = [kg/m³] × [-] / [kg/mol]
```

Repetir para cada espécie (substituir nome e peso molecular):

| Field Function | Expressão STAR-CCM+ | M (kg/mol) |
|---|---|---|
| C_TG | `$$Density * $$MassFraction_TG / 0.8854` | 0,8854 |
| C_DG | `$$Density * $$MassFraction_DG / 0.6210` | 0,6210 |
| C_MG | `$$Density * $$MassFraction_MG / 0.3570` | 0,3570 |
| C_MeOH | `$$Density * $$MassFraction_MeOH / 0.0320` | 0,0320 |
| C_FAME | `$$Density * $$MassFraction_FAME / 0.2970` | 0,2970 |
| C_GL | `$$Density * $$MassFraction_GL / 0.0920` | 0,0920 |

> **Sintaxe STAR-CCM+:**
> - `$$Density` → densidade local do fluido [kg/m³]
> - `$$MassFraction_NomeEspecie` → fração mássica da espécie (o nome deve bater
>   exatamente com o nome da espécie criada no Passo 1)
> - `$$Temperature` → temperatura local [K]

---

### PASSO 4 — Criar Field Functions das Constantes de Taxa

**Constante de taxa k₁ como função da temperatura:**

```
Nome: k1_T
Tipo: Scalar
Definição:
  1.26e-2 * exp(-64600.0 / (8.314 * $$Temperature))

  → Unidade: m6/(mol·kgcata·s)
  → A 120°C (393,15 K): k1 ≈ 1,7×10⁻¹¹
  → A 185°C (458,15 K): k1 ≈ 5,6×10⁻¹⁰  ← confere com Tabela 8 do artigo
```

```
Nome: k2_T
Tipo: Scalar
Definição:
  8.88e-6 * exp(-31800.0 / (8.314 * $$Temperature))

  → Unidade: m6/(mol·kgcata·s)
```

```
Nome: k3_T
Tipo: Scalar
Definição:
  1.28e-7 * exp(-17000.0 / (8.314 * $$Temperature))

  → Unidade: m6/(mol·kgcata·s)
```

---

### PASSO 5 — Criar Field Functions das Taxas Líquidas

**Taxa líquida de cada reação [mol/(kgcat·s)] — inclui termo reverso:**

```
Nome: r1_vol
Tipo: Scalar
Definição:
  $$k1_T * ($$C_TG * $$C_MeOH  -  (1.0/51.2) * $$C_DG * $$C_FAME)

  → K1 = 51,2  (Tabela 7 do artigo)
  → Unidade resultante: m6/(mol·kgcata·s) × mol²/m⁶ = mol/(kgcata·s)  CORRETO
```

```
Nome: r2_vol
Tipo: Scalar
Definição:
  $$k2_T * ($$C_DG * $$C_MeOH  -  (1.0/53.1) * $$C_MG * $$C_FAME)

  → K2 = 53,1
```

```
Nome: r3_vol
Tipo: Scalar
Definição:
  $$k3_T * ($$C_MG * $$C_MeOH  -  (1.0/12.2) * $$C_GL * $$C_FAME)

  → K3 = 12,2
```

**Converter para base de área de parede (multiplicar pelo fator 0,02376):**

```
Nome: r1_wall
Tipo: Scalar
Definição:
  $$r1_vol * 0.02376

  → Unidade: mol/(kgcata·s) × kgcata/m²_wall = mol/(m²_wall·s)
  → Fator = ρ_washcoat × δ_washcoat = 1188 × 20×10⁻⁶ = 0,02376
```

```
Nome: r2_wall
Tipo: Scalar
Definição:
  $$r2_vol * 0.02376
```

```
Nome: r3_wall
Tipo: Scalar
Definição:
  $$r3_vol * 0.02376
```

> **Importante — limitador numérico:** As taxas reversíveis podem ser negativas próximo ao
> equilíbrio (reação ocorrendo no sentido reverso). Isso é fisicamente correto e o solver
> de espécies do STAR-CCM+ consegue tratar fluxos negativos na parede. Se instabilidades
> ocorrerem nas primeiras iterações, adicionar um limitador temporário:
>
> `max($$r1_vol, -1.0e-6) * 0.02376`  (limita a taxa reversa máxima)
>
> Remover o limitador após estabilizar para não prejudicar a física.

---

### PASSO 6 — Aplicar Fluxos de Espécie na Parede Catalítica

**Caminho:**
```
[Simulation Tree]
└── Boundaries
    └── Top Wall  (parede com washcoat catalítico)
        └── Physics Conditions
            └── Species Conditions
                → Para cada espécie: selecionar "Specified Flux"
```

**Expressões de fluxo para cada espécie [kg/(m²·s)]:**

```
Boundaries → Top Wall → Physics Conditions → Species Conditions:

  TG   → Flux Type: Specified Flux
          Species Flux: -0.8854 * $$r1_wall
          (negativo = consumido na reação 1)

  DG   → Species Flux: 0.6210 * ($$r1_wall - $$r2_wall)
          (produzido na rxn 1, consumido na rxn 2)

  MG   → Species Flux: 0.3570 * ($$r2_wall - $$r3_wall)
          (produzido na rxn 2, consumido na rxn 3)

  MeOH → Species Flux: -0.0320 * ($$r1_wall + $$r2_wall + $$r3_wall)
          (consumido nas três reações)

  FAME → Species Flux: 0.2970 * ($$r1_wall + $$r2_wall + $$r3_wall)
          (produzido nas três reações)

  GL   → Species Flux: 0.0920 * $$r3_wall
          (produzido apenas na reação 3)
```

**Na parede inerte (Bottom Wall ou parede oposta sem catalisador):**
```
Boundaries → Bottom Wall → Physics Conditions → Species Conditions:
  → Para cada espécie: Flux Type = Zero Flux  (parede sem reação)
```

---

### PASSO 7 — Condições de Contorno Completas da Fase 2

```
┌─────────────────────────────────────────────────────────┐
│ INLET (Velocity Inlet):                                 │
│   Velocity: 1,0×10⁻³ m/s                               │
│   Temperature: 393,15 K                                 │
│   MassFraction_TG:   0,8218   (razão molar 6:1)         │
│   MassFraction_MeOH: 0,1782                             │
│   MassFraction_DG:   0,00                               │
│   MassFraction_MG:   0,00                               │
│   MassFraction_FAME: 0,00                               │
│   MassFraction_GL:   0,00                               │
├─────────────────────────────────────────────────────────┤
│ OUTLET (Pressure Outlet):                               │
│   Gauge Pressure: 0 Pa                                  │
│   Species: zero-gradient (padrão — não especificar)     │
│   Temperature: zero-gradient                            │
├─────────────────────────────────────────────────────────┤
│ TOP WALL (parede catalítica com washcoat):              │
│   Condição de velocidade: No-Slip                       │
│   Condição térmica: Temperature Wall → 393,15 K         │
│   Fluxo de espécie: Specified Flux (ver Passo 6)        │
├─────────────────────────────────────────────────────────┤
│ BOTTOM WALL (parede inerte) ou SYMMETRY:                │
│   Condição de velocidade: No-Slip ou Symmetry           │
│   Condição térmica: Adiabatic (padrão) ou Symmetry      │
│   Fluxo de espécie: Zero Flux para todas as espécies    │
└─────────────────────────────────────────────────────────┘
```

---

## Seção 4: Observações e Limitações Importantes

### 4.1 Extrapolação de temperatura — T = 120°C

**O artigo cobre T = 140–220°C. O projeto opera a T = 120°C.**

A extrapolação via Arrhenius implica:

```
k₁(120°C) / k₁(185°C) ≈ 1,7×10⁻¹¹ / 5,6×10⁻¹⁰ ≈ 0,030
→ a cinética a 120°C é ~33× mais lenta do que a 185°C para a reação 1
```

Isso tem implicações práticas:
- **Taxa de conversão baixa:** o canal de 50 mm pode ser insuficiente para conversão significativa.
- **Incerteza maior:** quanto mais distante do intervalo experimental, maior o erro de extrapolação.
- **Recomendação para a dissertação:** apresentar os resultados a 120°C como "cenário de projeto"
  e mostrar separadamente como variam com T (sensibilidade de T = 140°C a T = 200°C).

### 4.2 Entalpia de reação e tratamento isotérmico

**Allain et al. (2015) declara explicitamente que as reações de transesterificação são consideradas
isotérmicas na literatura, com ΔH_rxn ≈ 0 J·K⁻¹.**

Consequências para o CFD:
- Não é necessário implementar fonte de calor na equação de energia.
- A parede isotérmica (T_wall = 393,15 K) é a condição de contorno correta.
- A equação de energia pode até ser omitida na primeira versão da Fase 2 (simplificação válida).
- Se incluída, o campo de temperatura convergirá para T ≈ constante = 393 K ao longo do canal.

### 4.3 Difusão de TG — Sc_TG muito elevado

Da Tabela 12 corrigida para 120°C:
```
D_TG(120°C) ≈ 1,27×10⁻¹⁰  m²/s   (muito baixo — molécula grande, C57H104O6)

Sc_TG = μ_mix / (ρ_mix × D_TG)
      = 6,0×10⁻³ / (870 × 1,27×10⁻¹⁰)
      ≈ 54 000   → Sc_TG >> 1
```

Implicações para a malha e a física:
- Gradientes de concentração de TG **muito mais aguçados** na direção radial do que gradientes de velocidade.
- A camada de difusão de espécie é **muito mais fina** que a camada limite hidrodinâmica.
- **Necessidade de refinamento de malha:** o número de células na direção y (transversal) deve ser
  suficiente para resolver o gradiente de concentração próximo à parede catalítica.
- Estimativa: a camada de difusão de espécie cresce como `δ_c ∝ x^(1/3) × Sc^(-1/3)`.
  Para `Sc = 54000` e `Dh = 1,1 mm`, `δ_c ≈ Dh/Sc^(1/3) ≈ 30 µm` no início do canal.
  → Usar pelo menos 5 células nos primeiros 50 µm próximos à parede catalítica.

**Recomendação de malha para Fase 2:**
- Mínimo: 40 células na direção y com refinamento progressivo (razão ≈ 1,15 próximo à parede).
- Ideal: 60–80 células com razão 1,1, concentradas nos primeiros 10% do canal junto à parede.

### 4.4 Reação limitante — análise por constante de equilíbrio

| Reação | K_eq | Interpretação |
|---|---|---|
| Rxn 1: TG → DG | 51,2 | Favorável, mas menor K dentre as três |
| Rxn 2: DG → MG | 53,1 | Favorável — similar à Rxn 1 |
| Rxn 3: MG → GL | 12,2 | **Menor K** — mais limitada pelo equilíbrio |

A reação 3 (MG → GL + FAME) é a mais limitada pelo equilíbrio. Isso significa que:
- Conversão completa de MG em GL é **termodinamicamente restrita** a T = 120°C.
- Um excesso de metanol (maior razão molar MeOH:óleo) desloca o equilíbrio para a direita.
- Verificar conversão de MG na saída — se alta, o canal é adequado; se baixa, aumentar L ou razão molar.

---

## Seção 5: Estratégia de Convergência

### 5.1 Inicialização

```
1. Carregar solução da Fase 1 (hidrodinâmica convergida):
   File → Load → Field Data from Solution  (ou usar "Initialize from Previous Simulation")

2. Inicializar espécies com valores do inlet:
   Solution → Initialize:
     MassFraction_TG   = 0,8218  (uniforme no domínio inteiro)
     MassFraction_MeOH = 0,1782
     demais espécies   = 0,00
     Temperature       = 393,15 K (se equação de energia ativada)
```

### 5.2 URFs recomendados para a Fase 2

As reações são numericamente rígidas (*stiff*) porque k₁ varia exponencialmente com T.

```
Solvers → Segregated Species:
  Under-Relaxation Factor (URF): 0,5  (reduzir de 0,9 padrão para estabilidade)

Solvers → Segregated Energy (se ativado):
  URF: 0,9  (mais estável, pois ΔHrxn ≈ 0)

Solvers → Segregated Flow:
  URF Velocidade:  0,7  (manter padrão ou ligeiramente abaixo)
  URF Pressão:     0,3  (manter padrão)
```

### 5.3 Rampagem da taxa de reação (primeiras 50 iterações)

Para evitar divergência no início (quando a solução de espécie ainda não está estabelecida), usar
um fator de rampa que aumenta gradualmente a intensidade da taxa de reação:

```
1. Criar nova Field Function:
   Nome: ramp_factor
   Definição: min($$Iteration / 50.0,  1.0)
   → Vai de 0 na iteração 0 até 1,0 na iteração 50 (rampa linear)

2. Modificar r1_wall, r2_wall, r3_wall para incluir o fator:
   r1_wall = $$r1_vol * 0.02376 * $$ramp_factor
   r2_wall = $$r2_vol * 0.02376 * $$ramp_factor
   r3_wall = $$r3_vol * 0.02376 * $$ramp_factor

3. Rodar 100 iterações com o fator de rampa ativo.
4. Após convergência, remover o fator (voltar r_wall ao valor pleno) e continuar.
```

> **Nota:** `$$Iteration` é uma variável reservada do STAR-CCM+ que retorna o número da iteração atual.

### 5.4 Monitores de convergência recomendados

```
Reports → New Report → Surface Average:
  Nome: "Outlet_MassFrac_TG"
  Surface: Outlet
  Field Function: MassFraction_TG
  → Monitorar: deve diminuir à medida que a reação progride

Reports → New Report → Surface Average:
  Nome: "Outlet_MassFrac_FAME"
  Surface: Outlet
  Field Function: MassFraction_FAME
  → Monitorar: deve aumentar simetricamente

Reports → New Report → Surface Integral:
  Nome: "Wall_TotalRxnRate"
  Surface: Top Wall
  Field Function: r1_wall + r2_wall + r3_wall
  → Taxa total de reação na parede [mol/s por metro de profundidade em 2D]

Reports → New Report → Line Probe:
  Nome: "Axial_TG_Wall"
  Posição: linha ao longo da parede catalítica (y = H/2, x de 0 a L)
  Field Function: MassFraction_TG
  → Verificar o gradiente axial de TG — deve diminuir do inlet ao outlet
```

### 5.5 Critério de convergência

```
Residuais (Monitors → Residuals):
  Continuidade:    < 1×10⁻⁶
  X-Momentum:      < 1×10⁻⁶
  Y-Momentum:      < 1×10⁻⁶
  Energia:         < 1×10⁻⁷  (se ativada)
  Espécies (cada): < 1×10⁻⁵  (mais difícil — aceitável 1×10⁻⁴ em reações lentas)

Reports (estabilidade):
  Variação de MassFraction_TG na saída < 0,1% nas últimas 100 iterações → convergido
```

---

## Apêndice A: Resumo das Field Functions (ordem de criação)

| # | Nome | Dependências | Expressão |
|---|---|---|---|
| 1 | C_TG | $$Density, $$MassFraction_TG | `$$Density * $$MassFraction_TG / 0.8854` |
| 2 | C_DG | $$Density, $$MassFraction_DG | `$$Density * $$MassFraction_DG / 0.6210` |
| 3 | C_MG | $$Density, $$MassFraction_MG | `$$Density * $$MassFraction_MG / 0.3570` |
| 4 | C_MeOH | $$Density, $$MassFraction_MeOH | `$$Density * $$MassFraction_MeOH / 0.0320` |
| 5 | C_FAME | $$Density, $$MassFraction_FAME | `$$Density * $$MassFraction_FAME / 0.2970` |
| 6 | C_GL | $$Density, $$MassFraction_GL | `$$Density * $$MassFraction_GL / 0.0920` |
| 7 | k1_T | $$Temperature | `1.26e-2 * exp(-64600.0 / (8.314 * $$Temperature))` |
| 8 | k2_T | $$Temperature | `8.88e-6 * exp(-31800.0 / (8.314 * $$Temperature))` |
| 9 | k3_T | $$Temperature | `1.28e-7 * exp(-17000.0 / (8.314 * $$Temperature))` |
| 10 | r1_vol | C_TG, C_DG, C_MeOH, C_FAME, k1_T | `$$k1_T * ($$C_TG * $$C_MeOH - (1.0/51.2) * $$C_DG * $$C_FAME)` |
| 11 | r2_vol | C_DG, C_MG, C_MeOH, C_FAME, k2_T | `$$k2_T * ($$C_DG * $$C_MeOH - (1.0/53.1) * $$C_MG * $$C_FAME)` |
| 12 | r3_vol | C_MG, C_GL, C_MeOH, C_FAME, k3_T | `$$k3_T * ($$C_MG * $$C_MeOH - (1.0/12.2) * $$C_GL * $$C_FAME)` |
| 13 | r1_wall | r1_vol | `$$r1_vol * 0.02376` |
| 14 | r2_wall | r2_vol | `$$r2_vol * 0.02376` |
| 15 | r3_wall | r3_vol | `$$r3_vol * 0.02376` |
| 16 | ramp_factor | — | `min($$Iteration / 50.0, 1.0)` |

---

## Apêndice B: Checklist de Verificação Antes de Rodar

```
[ ] Fase 1 convergida — residuais < 1×10⁻⁶
[ ] Multi-Component Liquid ativado com 6 espécies
[ ] Pesos moleculares corretos em cada espécie
[ ] Difusividades da Tabela 12 (corrigidas para 120°C) inseridas
[ ] Fluid Temperature ativado (ou omitido se simplificação isotérmica pura)
[ ] 16 Field Functions criadas na ordem correta (concentrações → k_T → r_vol → r_wall)
[ ] Fluxos de espécie aplicados no Top Wall (6 expressões)
[ ] Fluxo zero aplicado no Bottom Wall para todas as espécies
[ ] Inlet: frações mássicas somam exatamente 1,0
[ ] URF de espécie = 0,5 (não usar padrão 0,9 em reações)
[ ] ramp_factor ativo para as primeiras 50-100 iterações
[ ] Monitores criados: MassFrac_TG e MassFrac_FAME na saída
[ ] Inicialização carregada da Fase 1
```

---

---

## Apêndice C: Dois Caminhos no STAR-CCM+ — Field Function vs. Surface Chemistry Model

### C.1 Visão geral dos dois caminhos disponíveis

Os tutoriais da Siemens apresentam um mecanismo nativo chamado **Surface Chemistry Model** com
um gestor de mecanismos (`Surface Mechanism Manager`). Entender quando usar cada abordagem
é fundamental para não implementar um caminho inadequado.

| Critério | **Caminho A: Field Function + Flux BC** | **Caminho B: Surface Mechanism Manager** |
|---|---|---|
| Tipo de reação | Leis de potência globais (modelo Clássico) | Mecanismos elementares com cobertura de sítio (θ) |
| Número de reações | Qualquer (nós usamos 3) | Qualquer, porém gerenciado pelo solver CVODE |
| Fase do fluido | **Líquido** (Multi-Component Liquid) ✅ | Projetado para **gás** (Multi-Component Gas) |
| Taxa de reação | Field Function customizada (expressão algébrica) | Arrhenius com checkboxes (LH, Reversible, Sticky…) |
| Cobertura de sítio (θ) | **Não necessário** (taxa global) | Equações de site fraction (θ_TG, θ_MeOH…) |
| Solver | Segregated Species (padrão) | CVODE (solver stiff especializado) |
| Site Density [kmol/m²] | **Não necessário** | Obrigatório |
| Complexidade de setup | Menor (tudo via Field Functions) | Maior (árvore extensa, declaração de espécies de superfície) |
| **Recomendação** | ✅ **USAR ESTE** para o nosso caso | ❌ Overengineering para taxa global LHHW em líquido |

**Conclusão: usar sempre o Caminho A (Field Function) para o modelo Clássico de Allain (2015).**

O Caminho B é necessário apenas se:
- A taxa for definida por *surface coverage* (equações diferenciais de θ sobre a superfície).
- O fluido for gás com química complexa (ex.: CH₄/Pt do tutorial da Siemens).
- Houver dezenas de reações elementares gerenciadas via arquivo Chemkin.

---

### C.2 Onde fica o Surface Mechanism Manager (para referência)

Caso queira explorar o Caminho B no futuro (ex.: modelo Eley-Rideal com adsorção explícita):

```
[Simulation Tree]
└── Continuum ("Fluid Physics")
    └── Models
        └── Surface Chemistry        ← ativar via "Edit Models..."
            └── Surface Mechanism Manager
                └── [Nome do Mecanismo]   ← clicar direito → "New Surface Mechanism"
                    ├── Gas/Liquid Species  ← TG, MeOH, DG, MG, FAME, GL
                    ├── Surface Species     ← sítios ativos (ex.: [*], TG*, MeOH*)
                    ├── Site Density: [kmol/m²]
                    └── Models
                        └── Reacting Surface
                            └── Reactions
                                └── [Reaction 1]
                                    └── Properties
                                        └── Reaction Coefficient
                                            └── Arrhenius Coefficients
                                                ├── Pre-Exponent A
                                                ├── Activation Energy Ea [J/mol]
                                                ├── Temperature Exponent Beta
                                                ├── ☑ Reversible (marcar para reações reversíveis)
                                                ├── ☑ Langmuir-Hinshelwood  ← relevante para Eley-Rideal
                                                ├── Motz-Wise Correction    (apenas gás)
                                                └── Bohm Correction         (apenas gás)
```

**Ativar Surface Mechanism Option na parede catalítica:**
```
Boundaries → Top Wall → Physics Conditions
  → Surface Mechanism Option: Enabled    ← obrigatório para que a parede seja reativa
```

---

### C.3 O checkbox "Langmuir-Hinshelwood" — quando usar

O painel Arrhenius Coefficients do Surface Mechanism Manager tem um checkbox
**"Langmuir-Hinshelwood"** que, quando marcado, modifica a expressão de taxa para incluir
termos de inibição no denominador.

**Para o Modelo Clássico de Allain (2015): NÃO marcar.**
- O Modelo Clássico é uma lei de potência de 2ª ordem sem denominador de inibição.
- Marcar incorretamente alteraria a forma funcional da expressão.

**Para o Modelo Eley-Rideal de Allain (2015): marcar.**
- O modelo ER tem termos `1 + KA·C_TG + KG·C_GL` no denominador — isso é a forma LH.
- Se implementando o ER via Surface Mechanism Manager, marcar o checkbox e inserir os
  parâmetros KA e KG nos campos correspondentes.

---

### C.4 Surface Washcoat Factor — localização exata

O `Surface Washcoat Factor` é um parâmetro do Caminho B (Surface Mechanism Manager) que
representa o aumento efetivo da área catalítica pelo washcoat sobre a área geométrica da parede.

**No Caminho A (nosso caso):** o efeito do washcoat está embutido no fator de conversão:
```
fator_conversão = ρ_washcoat × δ_washcoat = 1188 × 20e-6 = 0,02376 kgcat/m²_wall
→ Já incorporado nas Field Functions r1_wall, r2_wall, r3_wall
→ NÃO é necessário o parâmetro "Surface Washcoat Factor" da interface
```

**No Caminho B (referência futura):** localização na árvore:
```
Interfaces → [Nome da Interface Fluido-Parede]
  → Physics Values
      └── Surface Washcoat Factor: [valor adimensional]
          → Multiplica a área geométrica para obter a área efetiva do washcoat
          → Ex.: fator = 500 significa que o washcoat tem 500× mais área que a parede geométrica
```

Para converter o nosso fator `0,02376 kgcat/m²` em um Surface Washcoat Factor adimensional,
seria necessário dividir pela densidade areal do catalisador monolítico — mas isso é
desnecessário pois o Caminho A já trata isso algebricamente nas Field Functions.

---

### C.5 CVODE — solver para química stiff (Caminho B)

O tutorial "Methane Reformer" da Siemens usa o solver **CVODE** para integrar equações
de surface coverage (θ) que são numericamente stiff. No nosso caso:

```
Nosso sistema (Caminho A):
  - 3 equações algébricas de taxa (r1, r2, r3) — NÃO diferenciais
  - Segregated Species solver (padrão) é suficiente
  - URF = 0,5 para estabilidade (ver Seção 5.2)
  → CVODE NÃO é necessário
```

Se no futuro migrar para o Caminho B com cobertura de sítio, ativar CVODE em:
```
Solvers → Surface Chemistry Solver
  → Solver Type: CVODE
  → Absolute Tolerance: 1×10⁻¹⁰  (parâmetro padrão para stiff ODE)
```

---

## Apêndice D: Build123d — Geometria 2D do Canal (Fase 1)

Script Python para gerar o canal retangular 2D e exportar como STEP para o STAR-CCM+.

**Arquivo:** `scripts/canal_2d.py`

```python
# Canal representativo do monólito para Fase 1 (hidrodinâmica a frio)
# Dh = 1,1 mm (canal quadrado), L = 50 mm
# Exporta: canal_2d.step (importar no STAR-CCM+ como 2D geometry)

from build123d import *

# Parâmetros do canal
Dh = 1.1e-3    # m — diâmetro hidráulico
L  = 50.0e-3   # m — comprimento do canal

with BuildSketch() as sketch:
    Rectangle(L * 1000, Dh * 1000)   # build123d usa mm por padrão

# Exportar o contorno como STEP 2D
export_step(sketch.sketch, "canal_2d.step")
print(f"Canal exportado: {L*1000:.0f} mm × {Dh*1000:.1f} mm")
```

**No STAR-CCM+:**
```
File → Import → CAD Model → canal_2d.step
  → Confirmar importação como 2D
  → Renomear as 4 superfícies:
       Borda inferior (y=0):       "Bottom_Wall"   ou "Symmetry"
       Borda superior (y=Dh):      "Top_Wall"      (parede catalítica)
       Borda esquerda (x=0):       "Inlet"
       Borda direita  (x=L):       "Outlet"
```

---

*Documento gerado com base em Allain et al. (2015), CEJ 281, 654–664. DOI: 10.1016/j.cej.2015.07.075*  
*Tutoriais Siemens: "Surface Chemistry Terminology", "SurfaceChemistry on Baffle-Interface", "Methane Reformer with CVODE"*  
*Gabriel Rozo | FEQ/UNICAMP | 2025-2027*
