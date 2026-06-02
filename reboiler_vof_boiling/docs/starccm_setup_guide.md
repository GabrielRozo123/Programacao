# STAR-CCM+ Setup — Reboiler VOF+Boiling (Phase 1)

**Cenário:** Pool boiling de n-Pentano em feixe de tubos (3 col × 4 fileiras, triangular)  
**Objetivo:** Validar fluxo de calor CFD vs. correlação de Rohsenow (±25%)

---

## 1. Importar Geometria

1. File → Import → Import Surface/CAD Mesh → `01_Fluid_Pool.step`
2. Region name: **Fluid_Pool**
3. Renomear boundaries conforme a tabela abaixo:

| Face no STEP | Rename para | Tipo de BC |
|---|---|---|
| Bottom (y = 0) | `Inlet` | Pressure Inlet |
| Top (y = 223.8 mm) | `Outlet` | Pressure Outlet |
| Left (x = 0) | `Symmetry_L` | Symmetry Plane |
| Right (x = 71.4 mm) | `Symmetry_R` | Symmetry Plane |
| Front / Back (z) | `Empty_F` / `Empty_B` | Empty |
| 12× círculos dos tubos | `Tube_Wall` | Temperature Wall |

> **Dica:** No STAR-CCM+, use *Select All Surfaces* no tree, filtre por área ≈ 0,0598 mm² (cada círculo extrudado 1 mm) para selecionar todos os tubos de uma vez.

---

## 2. Malha

| Parâmetro | Valor | Justificativa |
|---|---|---|
| Base size | 1,5 mm | ~OD/13 — adequado para VOF |
| Surface curvature | 36 pontos/círculo | Resolução de bolha em formação |
| Prism layers (Tube_Wall) | 12 camadas, razão 1,3 | y⁺ < 1 obrigatório para RPI |
| Espessura 1ª camada | 0,03 mm | Garante resolução ΔT na parede |
| Refino volumétrico (±4 mm dos tubos) | 0,4 mm | Interface líq-vap ativa |
| Células estimadas | ~60–120 k | Leve — viável em PC |

---

## 3. Modelos de Física — Região Fluido

Ativar na seguinte ordem (a ordem importa para dependências de modelo):

1. **Space** → Two Dimensional *(ou Three Dimensional + 1 célula em Z)*
2. **Time** → Implicit Unsteady *(transiente — ebulição é inerentemente não-estacionária)*
3. **Material** → Eulerian Multiphase → **VOF**
4. **Phase 1 (Primary):** n-C₅H₁₂ Liquid
5. **Phase 2 (Secondary):** n-C₅H₁₂ Vapor
6. **Flow** → Segregated Flow
7. **Energy** → Segregated Multiphase Temperature
8. **Turbulence** → K-Omega SST (Menter) *(two-phase)*
9. **Body Forces** → Gravity → g = 9,81 m/s², direção: −Y *(para baixo)*
10. **Multiphase Interaction** → Surface Tension Force (CSF) → σ = 0,0125 N/m
11. **Multiphase Interaction** → Wall Boiling → **RPI model**

---

## 4. Propriedades do Fluido — n-Pentano (NIST, P = 2,5 bar / T_sat = 63,5°C)

### Fase Líquida — n-C₅H₁₂ Liquid

| Propriedade | Símbolo | Valor | Unidade |
|---|---|---|---|
| Densidade | ρ_l | 597,0 | kg/m³ |
| Viscosidade dinâmica | μ_l | 1,96 × 10⁻⁴ | Pa·s |
| Condutividade térmica | k_l | 0,1050 | W/(m·K) |
| Calor específico | cp_l | 2358 | J/(kg·K) |
| Calor latente de vaporização | h_fg | 354 000 | J/kg |
| Tensão superficial | σ | 0,0125 | N/m |
| Número de Prandtl | Pr_l | 4,40 | — |

### Fase Vapor — n-C₅H₁₂ Vapor

| Propriedade | Símbolo | Valor | Unidade |
|---|---|---|---|
| Densidade (gás ideal OK) | ρ_v | 7,76 | kg/m³ |
| Viscosidade dinâmica | μ_v | 7,1 × 10⁻⁶ | Pa·s |
| Condutividade térmica | k_v | 0,0160 | W/(m·K) |
| Calor específico | cp_v | 1720 | J/(kg·K) |

> **Fonte:** NIST WebBook, n-Pentane (CAS 109-66-0), saturation properties 2.5 bar.

---

## 5. Parâmetros do Modelo RPI — Derivação e Valores Corretos

### 5.1  Raio de Departura de Bolha (R_db) — Fritz (1935)

A correlação de Fritz para o **diâmetro** de saída de bolha é:

```
d_b = 0,0208 × β × √(σ / [g × (ρ_l − ρ_v)])
```

onde **β é o ângulo de contato em GRAUS** e o fator 0,0208 tem unidades de °⁻¹.

**Para n-Pentano em SS 316L (tubulação comercial):**
β ≈ 22° (hidrocarboneto leve molha bem o aço inox — Pioro, 2004)

```
d_b = 0,0208 × 22 × √(0,0125 / [9,81 × (597 − 7,76)])
    = 0,4576 × √(0,0125 / 5786,3)
    = 0,4576 × √(2,160 × 10⁻⁶)
    = 0,4576 × 1,470 × 10⁻³
    = 6,72 × 10⁻⁴ m  ≈  0,67 mm

R_db = d_b / 2 ≈ 0,34 mm  →  usar 0,35 mm no STAR-CCM+
```

> **Erro comum:** usar coeficiente 0,208 (dez vezes maior) resulta em R_db ≈ 6,7 mm — fisicamente absurdo para n-Pentano.

### 5.2  Densidade de Sítios de Nucleação (N_nuc)

Para superfície de aço inox 316L, tubulação industrial (Ra ≈ 0,4–1,6 μm):

| Referência | Expressão / Valor |
|---|---|
| Han & Griffith (1965) — cobre polido | N_nuc = 10 000 m⁻² |
| Lemmert & Chawla (1977) — água, aço | N_nuc = 210 × ΔT^1,805 |
| Krepper et al. (2007) — agua, ANSYS | N_nuc = 1000 m⁻² (mínimo) a 10⁶ m⁻² |
| **Recomendado para n-C₅H₁₂ em SS industrial** | **N_nuc = 30 000 m⁻²** |

Lemmert-Chawla adaptado a ΔT = 46,3 K:
`N_nuc = 210 × 46,3^1.805 ≈ 210 × 835 = 175 000 m⁻²`  ← correlação para H₂O
Para hidrocarboneto, reduz ~5–10×: **N_nuc ≈ 20 000–35 000 m⁻²** → usar **30 000 m⁻²**

### 5.3  Tabela de Parâmetros RPI para o STAR-CCM+

| Parâmetro RPI | Valor a Inserir | Observação |
|---|---|---|
| Nucleation Site Density | **30 000 m⁻²** | SS 316L industrial (Krepper 2007) |
| Bubble Departure Radius | **3,5 × 10⁻⁴ m** (0,35 mm) | Fritz (1935), β = 22°, n-C₅H₁₂ |
| Departure Frequency | auto (Jakob formula) | f = k_l × ΔT / (ρ_l × h_fg × R_db²) |
| Area Influence Coeff. K | 4,8 | Tolubinsky & Kostanchuk (1970) |
| Quenching Relaxation τ | 0,8 | Padrão STAR-CCM+ |

> **Sensibilidade:** ±50% em N_nuc muda q em ±15%. Após a simulação inicial, ajuste N_nuc para que q_CFD ≈ q_Rohsenow.

---

## 6. Condições de Contorno

| Boundary | Tipo STAR-CCM+ | Valores |
|---|---|---|
| `Inlet` (y = 0) | Pressure Inlet | P = 250 000 Pa · T = 336,7 K · α_liq = 1,0 |
| `Outlet` (y = H) | Pressure Outlet | P = 250 000 Pa · T = 336,7 K · α_vap = 1,0 |
| `Symmetry_L` | Symmetry Plane | — |
| `Symmetry_R` | Symmetry Plane | — |
| `Empty_F / Empty_B` | Empty (2D) | — |
| `Tube_Wall` | Temperature Wall | T = **383,15 K** (110,0°C) · Wall Boiling: RPI |

---

## 7. Solver e Critério de Parada

| Parâmetro | Valor | Motivo |
|---|---|---|
| Time step Δt | 5 × 10⁻⁴ s | ~0,25 × τ_bolha típico |
| Max inner iterations/step | 10 | Convergência por passo |
| Total time | 30 s | Regime pseudo-estacionário |
| URF — Velocidade | 0,7 | — |
| URF — Pressão | 0,3 | — |
| URF — Temperatura | 0,9 | — |
| URF — Volume Fraction | 0,5 | Interface VOF |
| URF — Wall Heat Flux | **0,3** | Não-linear — nunca usar 1,0! |

---

## 8. Reports e Monitores de Validação

| Report | Tipo | Superfície / Expression | Saída esperada |
|---|---|---|---|
| `q_wall` | Surface Average | Boundary Heat Flux · `Tube_Wall` | 76–91 kW/m² |
| `T_wall` | Surface Average | Static Temperature · `Tube_Wall` | 383 K |
| `alpha_v_out` | Surface Average | VOF vapor · `Outlet` | 0,05–0,30 |
| `h_boil` | Expression | `${q_wall} / (${T_wall} - 336.7)` | 1640–1960 W/(m²K) |

### Alvo de Validação — Correlação Rohsenow (1952)

Parâmetros: C_sf = 0,0200 (n-C₅H₁₂ em SS comercial), n = 1,7

```
A = μ_l × h_fg = 1,96e-4 × 354 000 = 69,38

B = [g(ρ_l − ρ_v)/σ]^0.5
  = [9,81 × (597 − 7,76) / 0,0125]^0.5
  = [462 000]^0.5 = 679,7  m⁻¹

C = [cp_l × ΔT / (C_sf × h_fg × Pr^n)]^3
  = [2358 × 46,3 / (0,0200 × 354 000 × 4,40^1.7)]^3
  = [109 175 / 87 820]^3
  = 1,243^3 = 1,923

q_Rohsenow = A × B × C = 69,38 × 679,7 × 1,923 ≈ 90 700 W/m²
```

**q_Rohsenow ≈ 91 kW/m²**  
**Alvo CFD: 68–114 kW/m² (±25%)**  
Mostinski (1963) como segunda referência: q_Mostinski ≈ 76 kW/m²  
**Faixa de consenso literatura: 76–91 kW/m²**

---

## 9. Cenas (Scenes)

| Scene | Field Function | Objetivo |
|---|---|---|
| `VOF_Vapor` | Volume Fraction (vapor) | Padrão de bolhas e coalescência |
| `Temperature` | Static Temperature | Gradiente térmico no pool |
| `Velocity` | Velocity Magnitude | Circulação natural |
| `Heat_Flux` | Boundary Heat Flux | Distribuição ao longo dos tubos |
| `Wall_Superheat` | Expression: `StaticTemp - 336.7` | Mapa de ΔT local |

---

## 10. Progressão após Validação

| Fase | Mudança | Novo objetivo |
|---|---|---|
| 2 | ΔT parametrico: 20 / 30 / 40 / 46 K | Curva de ebulição CFD vs. Rohsenow |
| 3 | Feixe 3×6 + geometria de casco TEMA K | Mapa de título de vapor, DNB detection |
| 4 | CHT: vapor condensando no tubo interno | Resistência térmica real da parede |
