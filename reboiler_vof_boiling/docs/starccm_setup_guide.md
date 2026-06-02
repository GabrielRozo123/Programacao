# STAR-CCM+ Setup — Reboiler VOF+Boiling (Phase 1: Single Tube)

## 1. Importar Geometria

1. File → Import → Import Surface/CAD Mesh
2. Importar `01_Fluid_Pool.step` → Region: **Fluid_Pool**
3. Importar `02_Tube_Wall.step` → Region: **Tube_Wall**
4. Atribuir interface CHT: Fluid_Pool ↔ Tube_Wall (inner tube surface)

---

## 2. Malha

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| Base size | 1,5 mm | ~OD/13 |
| Surface curvature | 36 pts/círculo | Resolução da bolha |
| Prism layers (parede) | 10 camadas, y⁺ < 1 | Wall boiling requer resolução |
| First cell thickness | 0,05 mm | ΔT_sup bem resolvido |
| Volume de refino (tubo ±3 mm) | 0,3 mm | Interface líq-vap ativa |

---

## 3. Modelos de Física — Região Fluido

### Ativar na ordem:

1. **Multiphase Model** → Eulerian Multiphase → VOF
2. **VOF** → Multiphase Interaction: ativar
3. **Phase 1 (primary):** n-C₅H₁₂ Liquid
4. **Phase 2 (secondary):** n-C₅H₁₂ Vapor
5. **Energy:** Multiphase Temperature (segregated)
6. **Turbulence:** K-Omega SST (Menter) — two-phase
7. **Body Force:** Gravity → g = 9.81 m/s² → direção: −Y (para baixo)
8. **Surface Tension:** Continuum Surface Force (CSF), σ = 0.0128 N/m (C5 @ 63°C)
9. **Wall Boiling:** RPI Model (Rohsenow–Pilch–Ivey)

---

## 4. Propriedades do Fluido — n-Pentano (C₅H₁₂)

### Fase Líquida @ 2,5 bar / T_sat = 63,5°C (336,6 K)

| Propriedade | Valor | Fonte |
|-------------|-------|-------|
| ρ_l | 601 kg/m³ | NIST Webbook |
| μ_l | 2,1 × 10⁻⁴ Pa·s | NIST |
| k_l | 0,107 W/(m·K) | NIST |
| cp_l | 2360 J/(kg·K) | NIST |
| h_fg | 340 kJ/kg | NIST |
| Pr_l | 4,63 | calculado |
| σ | 0,0128 N/m | NIST |

### Fase Vapor @ 2,5 bar / T_sat = 63,5°C

| Propriedade | Valor |
|-------------|-------|
| ρ_v | 7,85 kg/m³ |
| μ_v | 7,2 × 10⁻⁶ Pa·s |
| k_v | 0,016 W/(m·K) |
| cp_v | 1710 J/(kg·K) |

---

## 5. Parâmetros do Modelo RPI (Wall Boiling)

### Valores do tutorial (H₂O, Cu polido):
- N_nuc = 10.000 sites/m² (cobre polido, Han & Griffith, 1965)
- R_db = 0,6 mm

### Adaptação industrial (n-C₅H₁₂, aço inox 316L):

**Raio de departura de bolha (Fritz, 1935):**
```
R_db = 0,208 × θ_contact × √(σ / [g × (ρ_l − ρ_v)])
     = 0,208 × 35° × √(0,0128 / [9,81 × (601 − 7,85)])
     ≈ 1,2 mm
```
(θ_contact ≈ 35° para n-Pentano em aço inox — Pioro, 2004)

**Densidade de sítios de nucleação (Jacob & Linzer, 1961):**
```
N_nuc = C_s × (ΔT_e / ΔT_ref)^m
```
Para ΔT_e = 46,5 K, aço inox: N_nuc ≈ 8.000 sites/m²

### Valores a usar no STAR-CCM+:

| Parâmetro RPI | Valor a inserir |
|---------------|----------------|
| Nucleation Site Density | 8000 m⁻² |
| Bubble Departure Radius | 0,0012 m |
| Bubble Departure Frequency | auto (Jakob) |
| Area Influence Coeff. (K) | 4 (padrão Tolubinsky) |
| Quenching Relaxation | 0,8 |

---

## 6. Condições de Contorno

| Superfície | Tipo | Valor |
|-----------|------|-------|
| **Bottom** (entrada líquido) | Pressure Inlet | P = 250.000 Pa, T = 336,6 K, α_liq = 1,0 |
| **Top** (saída vapor) | Pressure Outlet | P = 250.000 Pa, T = 336,6 K, α_vap = 1,0 |
| **Left / Right** | Symmetry Plane | — |
| **Tube inner wall** | Temperature BC | T_wall = 383 K (110°C) |
| **CHT interface** | Coupled interface | automático |

---

## 7. Solver e Critério de Parada

### Solver (transient, pseudo-steady boiling):

| Parâmetro | Valor |
|-----------|-------|
| Time step | 5 × 10⁻⁴ s |
| Max inner iterations | 10 |
| Total time | 30 s (regime pseudo-estacionário) |
| URF — Velocidade | 0,7 |
| URF — Pressão | 0,3 |
| URF — Temperatura | 0,9 |
| URF — VOF | 0,5 |
| URF — Wall Heat Flux | 0,3 (não-linear!) |

---

## 8. Reports e Monitores

### Reports a criar:

| Report | Tipo | Superfície | Saída esperada |
|--------|------|-----------|---------------|
| q_boiling | Surface Average | Boundary Heat Flux | Tube outer wall | ~80–120 kW/m² |
| T_wall_avg | Surface Average | Static Temperature | Tube outer wall | 383 K |
| alpha_vapor_outlet | Surface Average | VOF (vapor) | Top outlet | 0,05–0,3 |
| Nu_boiling | Expression | `${q_boiling} / (${T_wall_avg} - 336.6) * ${TUBE_OD} / ${k_liq}` | — |

### Validação Rohsenow:
```
q_Rohsenow = μ_l × h_fg × [g(ρ_l − ρ_v)/σ]^0.5 × [cp_l × ΔT / (C_sf × h_fg × Pr^n)]^3
           = 2,1e-4 × 340000 × [9,81×(601−7,85)/0,0128]^0.5 × [2360×46,5/(0,0132×340000×4,63^1.7)]^3
           ≈ 95 kW/m²
```
Alvo: CFD dentro de ±20% da correlação Rohsenow.

---

## 9. Cenas (Scenes)

| Scene | Scalar | Objetivo |
|-------|--------|---------|
| VOF_Vapor | Volume Fraction (vapor) | Padrão de bolhas |
| Temperature | Static Temperature | Gradiente térmico |
| Velocity | Velocity Magnitude | Circulação natural |
| Heat_Flux | Boundary Heat Flux | Distribuição no tubo |
