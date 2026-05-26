# Digestor Kraft Kamyr — Simulação CFD
## Simcenter STAR-CCM+ | Meio Poroso Isotrópico

**Status:** Geometria pronta | Aguardando PDF Heat Transfer  
**Última atualização:** 2026-05-26

---

## 1. DESCRIÇÃO DO PROCESSO

O digestor Kamyr contínuo é o coração do processo Kraft de produção de celulose:

```
    ──────────       ← Entrada chips (topo, Z=45m)
   /          \      ← Cone superior
  │            │     ← Zona Impregnação (Z=40–45m, ε=0.50)
  │  cavacos   │     ← Zona Cozimento   (Z=12–40m, ε=0.40)
  │  + licor   │     → Extração Licor Negro (Z~27m)
  │            │     ← Zona Lavagem     (Z=2–12m,  ε=0.45)
   \          /      ← Cone inferior
    ──────────       ← Saída polpa (Z=0)
```

**Reação principal:**
- Madeira (lignina + celulose) + NaOH + Na₂S → Polpa + Licor Negro
- T = 155–175°C | P = 7–10 bar | Tempo residência = 1–3 h

---

## 2. GEOMETRIA (build123d)

**Arquivo:** `build_kraft_digester.py`

| Componente | Dimensão | Tipo STAR-CCM+ |
|---|---|---|
| Cone inferior | D: 0.8→5.5m, H=2m | Fluid Region |
| Zona Lavagem | D=5.5m, H=10m | Porous Region |
| Zona Cozimento | D=5.5m, H=25m | Porous Region |
| Zona Impregnação | D=5.5m, H=5m | Porous Region |
| Cone superior | D: 5.5→1.5m, H=3m | Fluid Region |
| 4 bocais laterais | D=0.3m, L=0.6m | Boundaries |

**Total:** D=5.5m, H=45m (escala industrial real)

---

## 3. FÍSICA DO MODELO

### Fase 1 — Hidrodinâmica (sem reação)
```
Material         : Liquid — White Liquor
ρ                : 1080 kg/m³
μ                : 3.5×10⁻⁴ Pa·s  (@ 165°C)
Regime           : Steady-State
Escoamento       : Segregated Flow
Turbulência      : K-Epsilon Standard (High y+ Wall Treatment)
Porosidade       : Isotropic Media (Ergun equation)
```

### Fase 2 — Com temperatura
```
+ Segregated Fluid Temperature
+ Heat Transfer (tutorial pendente)
Temperatura entrada : 155–175°C
```

### Fase 3 — Com reação de deslignificação
```
+ Segregated Species Transport
  Espécies: NaOH, Na2S, Lignina, Celulose
+ H-factor model (cinética de deslignificação)
```

---

## 4. COEFICIENTES DE ERGUN CALCULADOS

**Equação STAR-CCM+:** ΔP/L = -(Pi·|v| + Pv)·v

| Zona | ε | Pi [kg/m⁴] | Pv [kg/m³s] |
|---|---|---|---|
| Lavagem | 0.45 | 1.90×10⁶ | 4.8×10³ |
| Cozimento | 0.40 | 2.95×10⁶ | 8.2×10³ |
| Impregnação | 0.50 | 1.26×10⁶ | 2.9×10³ |

**Parâmetros usados:**
- dp = 6 mm (diâmetro equivalente dos cavacos)
- ρ = 1080 kg/m³ (licor branco @ 165°C)
- μ = 3.5×10⁻⁴ Pa·s (licor branco @ 165°C)

---

## 5. MAPEAMENTO TUTORIAL → PROJETO

### Tutorial: Porous Resistance Isotropic Media

| Tutorial | Digestor Kraft | Mudança |
|---|---|---|
| Material: Gas (Air) | **Liquid** (White Liquor) | Mudar para Liquid |
| ρ = 1.2 kg/m³ | **ρ = 1080 kg/m³** | Propriedades do licor |
| Fluxo: 20 m/s | **~0.001–0.01 m/s** | Muito mais lento |
| Pi = 25 kg/m⁴ | **1.26–2.95×10⁶ kg/m⁴** | Ergun para cavacos |
| Pv = 1500 kg/m³s | **2.9–8.2×10³ kg/m³s** | Ergun para cavacos |
| 1 região porosa | **3 regiões** (ε diferente) | 3 porous regions |
| K-Epsilon Standard | **K-Epsilon Standard** | Igual ✓ |
| High y+ Wall | **High y+ Wall** | Igual ✓ |
| Turbulence Intensity = 0.05 | **0.05–0.10** | Similar ✓ |

### Passo a passo STAR-CCM+ (com base no tutorial):

1. **Importar geometria:** `Digestor_Kraft.step`
2. **Assign Parts to Regions:**
   - `Cone_Inferior` + `Cone_Superior` → **Fluid Region**
   - `Zona_Lavagem` → **Porous Region** (Type: Porous)
   - `Zona_Cozimento` → **Porous Region** (Type: Porous)
   - `Zona_Impregn` → **Porous Region** (Type: Porous)
3. **Physics Continuum:**
   - Material: Liquid (mudar de Gas!)
   - Segregated Flow + Constant Density
   - Steady-State
   - Turbulent: K-Epsilon Standard (desativar auto-select)
4. **Porosity Coefficients** (para cada região):
   - Porous Inertial Resistance → Isotropic Tensor
   - Porous Viscous Resistance → Isotropic Tensor
5. **Boundary Conditions:**
   - Bocal_LB1, Bocal_LB2: Velocity Inlet
   - Bocal_LL: Velocity Inlet  
   - Bocal_LN: Pressure Outlet
   - Saída polpa (base cone inf): Pressure Outlet
   - Entrada chips (topo cone sup): Velocity Inlet

---

## 6. TUTORIAIS NECESSÁRIOS

| Tutorial | Status | Fase |
|---|---|---|
| Porous Resistance: Isotropic Media | ✅ Recebido | 1 |
| Heat Transfer (conjugado) | ⏳ Pendente | 2 |
| Multiphase / Species Transport | ⏳ Futuro | 3 |

---

## 7. PRÓXIMOS PASSOS

- [x] Geometria criada (`build_kraft_digester.py`)
- [x] Coeficientes de Ergun calculados
- [x] Mapeamento tutorial ↔ projeto
- [ ] Receber tutorial Heat Transfer
- [ ] Gerar STEP files (rodar Python)
- [ ] Importar no STAR-CCM+ e fazer mesh
- [ ] Configurar physics (Liquid, K-Epsilon, Porous)
- [ ] Configurar 5 regiões com diferentes Pi, Pv
- [ ] Rodar Fase 1 e validar perfil de pressão
