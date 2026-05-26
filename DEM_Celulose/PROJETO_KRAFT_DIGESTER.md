# Digestor Kraft Kamyr — Simulação CFD
## Simcenter STAR-CCM+ | Meio Poroso → Transferência de Calor → EMP Sólido-Líquido

**Status:** Geometria pronta | Documentação completa (Fases 1–4)  
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

### Separação das zonas na geometria
Cada zona é um **corpo independente** no arquivo STEP. As faces nos planos:
- Z=2m → interface Cone_Inferior ↔ Zona_Lavagem
- Z=12m → interface Zona_Lavagem ↔ Zona_Cozimento
- Z=37m → interface Zona_Cozimento ↔ Zona_Impregn
- Z=42m → interface Zona_Impregn ↔ Cone_Superior

O STAR-CCM+ detecta automaticamente as faces coincidentes ao importar o STEP.

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
Gravidade        : [0, 0, -9.81] m/s²
```

### Fase 2 — Com temperatura
```
+ Segregated Fluid Temperature  ← adicionar ao physics continuum existente
  (NÃO usar Coupled Flow — esse é para gás compressível)
Cp (licor branco) : ~4000 J/kg·K
k  (licor branco) : ~0.6 W/m·K
T entrada         : 155–175°C (428–448 K)
```

### Fase 3 — Com reação de deslignificação
```
+ Segregated Species Transport
  Espécies: NaOH, Na2S, Lignina, Celulose
+ H-factor model (cinética de deslignificação)
```

### Fase 4 — Eulerian Multiphase (EMP) — cavacos + licor
```
Substitui o modelo poroso por duas fases reais coexistindo:

Material        : Multiphase
Multiphase Model: Eulerian Multiphase (EMP)
EMP Turbulence  : Mixture Turbulence
Time            : Implicit Unsteady (chips se movem ~1mm/s)

Fase 0 — Contínua (Licor Branco):
  Tipo : Liquid
  ρ    : 1080 kg/m³  |  μ : 3.5×10⁻⁴ Pa·s

Fase 1 — Dispersa (Cavacos de madeira):
  Tipo         : Solid (Granular)
  ρ_chips      : 600 kg/m³ (cavaco úmido)
  dp           : 6 mm
  Packing limit: 0.63

Phase Interaction → Drag: Gidaspow
  α_chips > 0.2 → regime Ergun (leito denso)
  α_chips < 0.2 → regime Wen-Yu (suspensão diluída)

Volume Fractions iniciais:
  Zona Lavagem     : α_chips = 0.55  (ε=0.45)
  Zona Cozimento   : α_chips = 0.60  (ε=0.40)
  Zona Impregnação : α_chips = 0.50  (ε=0.50)
  Cones (fluid)    : α_chips = 0.00

Inlet chips (topo): α_chips=0.60, u_chips = −0.001 m/s (descendo)
Inlet licor (bocais): α_chips=0.00, u_licor = 0.5 m/s
```

> Diferença do tutorial (ar-água): usar Dispersed Multiphase topology
> e drag Gidaspow (Ergun+Wen-Yu) em vez de Multiple Flow Regimes + LSI.
> Tutoriais recebidos: Selecting Physics Models, Defining Phases,
> Setting Phase Interactions, Setting Inlet BCs, Mixture Settling.
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

## 5. PASSO A PASSO STAR-CCM+ COMPLETO

### 5.1 — Importar geometria
1. **File → Import → Import Surface/Volume Mesh** → selecionar `Digestor_Kraft.step`
2. Verificar que aparecem **9 corpos** no Object Tree:
   - Cone_Inferior, Zona_Lavagem, Zona_Cozimento, Zona_Impregn, Cone_Superior
   - Bocal_LB1, Bocal_LB2, Bocal_LN, Bocal_LL

### 5.2 — Assign Parts to Regions
- `Cone_Inferior` + `Cone_Superior` → **Fluid Region** (tipo padrão)
- `Zona_Lavagem` → **New Region** → Type: **Porous**
- `Zona_Cozimento` → **New Region** → Type: **Porous**
- `Zona_Impregn` → **New Region** → Type: **Porous**
- Bocais → **Boundaries** dentro das regiões correspondentes

### 5.3 — Physics Continuum
1. Right-click **Continua** → New Physics Continuum
2. Models a ativar (na ordem):
   - **Space:** Three Dimensional
   - **Time:** Steady
   - **Material:** Liquid ← **MUDAR de Gas!**
   - **Flow:** Segregated Flow
   - **Equation of State:** Constant Density (ρ = 1080 kg/m³)
   - **Turbulence:** K-Epsilon Turbulence
   - **K-Epsilon:** Standard K-Epsilon
   - **Wall Treatment:** High y+ Wall Treatment
   - **Optional:** Gravity (para convecção natural na Fase 2)
3. Desativar **Auto-select recommended physics** para evitar K-Epsilon Realizable

### 5.4 — Configurar propriedades do licor branco
```
Regions → [qualquer região] → Physics Continuum → Material → Liquid
  Density        : 1080 kg/m³
  Dynamic Viscosity: 3.5e-4 Pa·s
  (Fase 2) Specific Heat: 4000 J/kg·K
  (Fase 2) Thermal Conductivity: 0.6 W/m·K
```

### 5.5 — Porosity Coefficients (para cada Porous Region)
Caminho: `Regions → Zona_Lavagem → Physics Values → Porous Inertial Resistance`
```
Porous Inertial Resistance → Isotropic Tensor → valor: Pi (ver tabela §4)
Porous Viscous Resistance  → Isotropic Tensor → valor: Pv (ver tabela §4)
```
Repetir para Zona_Cozimento e Zona_Impregn com seus respectivos Pi e Pv.

### 5.6 — Criar Interfaces entre regiões (CRÍTICO)
As interfaces fluid↔porous e porous↔porous precisam ser criadas manualmente.

**Procedimento (do tutorial Creating Interfaces):**
1. Multi-selecionar (Ctrl+click) as faces coincidentes dos dois lados:
   - `Fluid Region → Boundaries → [face superior do cone_inf]`
   - `Zona_Lavagem → Boundaries → [face inferior da lavagem]`
2. Right-click nos nós selecionados → **Create Interface**
3. Editar o nó **Interfaces → Interface 1**:
   - **Type:** `Contact Interface`
   - **Topology:** `In-place`
4. Repetir para todas as interfaces:

| Interface | Região A | Região B |
|---|---|---|
| Int_1 | Cone_Inferior (topo) | Zona_Lavagem (fundo) |
| Int_2 | Zona_Lavagem (topo) | Zona_Cozimento (fundo) |
| Int_3 | Zona_Cozimento (topo) | Zona_Impregn (fundo) |
| Int_4 | Zona_Impregn (topo) | Cone_Superior (fundo) |

> Ao inicializar o flow, estas boundaries substituem as wall boundaries originais.

### 5.7 — Boundary Conditions

**Turbulence Specification:** Method = **Intensity + Length Scale** (para todos os inlets)

| Boundary | Tipo | Velocidade | Turb. Intensity | Length Scale |
|---|---|---|---|---|
| Bocal_LB1 | Velocity Inlet | 0.5 m/s | 0.07 | 0.09 m |
| Bocal_LB2 | Velocity Inlet | 0.5 m/s | 0.07 | 0.09 m |
| Bocal_LL  | Velocity Inlet | 0.3 m/s | 0.07 | 0.09 m |
| Bocal_LN  | Pressure Outlet | 0 Pa (gauge) | — | — |
| Saída polpa (fundo cone inf) | Pressure Outlet | 0 Pa (gauge) | — | — |
| Entrada chips (topo cone sup) | Velocity Inlet | 0.001 m/s | 0.05 | 0.3 m |

> Length Scale ≈ 0.3 × D_nozzle = 0.3 × 0.3m = 0.09m (bocais laterais)
> Length Scale entrada chips ≈ 0.3 × D_digestor = 0.3 × 1.5m = 0.45m (ajustar)

---

## 6. MAPEAMENTO TUTORIAL → PROJETO

### Tutorial: Porous Resistance Isotropic Media

| Tutorial | Digestor Kraft | Mudança |
|---|---|---|
| Material: Gas (Air) | **Liquid** (White Liquor) | Mudar para Liquid |
| ρ = 1.2 kg/m³ | **ρ = 1080 kg/m³** | Propriedades do licor |
| Fluxo: 20 m/s | **~0.001–0.5 m/s** | Muito mais lento |
| Pi = 25 kg/m⁴ | **1.26–2.95×10⁶ kg/m⁴** | Ergun para cavacos |
| Pv = 1500 kg/m³s | **2.9–8.2×10³ kg/m³s** | Ergun para cavacos |
| 1 região porosa | **3 regiões** (ε diferente) | 3 porous regions |
| K-Epsilon Standard | **K-Epsilon Standard** | Igual ✓ |
| High y+ Wall | **High y+ Wall** | Igual ✓ |
| Turb. Intensity = 0.05 | **0.05–0.10** | Similar ✓ |
| Length Scale = 0.005 m | **0.09 m** | 0.3×D_nozzle |

### Tutorial: Conjugate Heat Transfer (Heated Fin)

| Tutorial CHT | Digestor Kraft (Fase 2) | Diferença |
|---|---|---|
| Coupled Flow (gás compressível) | **Segregated Flow** (líquido) | Não mudar para Coupled! |
| Coupled Solid Energy | **Segregated Fluid Temperature** | Adicionar ao Segregated Flow |
| Ideal Gas | **Constant Density** | Licor incompressível |
| Gravidade ativa (convecção natural) | **Gravidade [0,0,-9.81]** | Igual ✓ |
| Interface: Contact, In-place | **Contact Interface, In-place** | Igual ✓ |
| 2 Physics Continua (Fluid + Solid) | **1 Continuum** (apenas fluido) | Sem sólido separado |

---

## 7. TUTORIAIS NECESSÁRIOS

| Tutorial | Status | Fase |
|---|---|---|
| Porous Resistance: Isotropic Media | ✅ Recebido | 1 |
| Specifying Porosity Coefficients | ✅ Recebido | 1 |
| Setting Boundary Conditions (Porous) | ✅ Recebido | 1 |
| Creating Interfaces | ✅ Recebido | 1+2 |
| Conjugate Heat Transfer (Heated Fin) | ✅ Recebido | 2 |
| Multiphase / Species Transport | ⏳ Futuro | 3 |
| Eulerian Mixture Settling | ✅ Recebido | 4 |
| Selecting Physics Models (EMP) | ✅ Recebido | 4 |
| Defining Phases + Initial Conditions | ✅ Recebido | 4 |
| Setting up Phase Interactions (Drag) | ✅ Recebido | 4 |
| Setting Inlet BCs (volume fractions) | ✅ Recebido | 4 |

---

## 8. PRÓXIMOS PASSOS

- [x] Geometria criada (`build_kraft_digester.py`)
- [x] Coeficientes de Ergun calculados
- [x] Mapeamento tutorial ↔ projeto
- [x] Procedimento interfaces (Contact Interface, In-place)
- [x] Condições de contorno documentadas
- [ ] Gerar STEP files (rodar `python build_kraft_digester.py`)
- [ ] Importar no STAR-CCM+ e fazer mesh
- [ ] Configurar physics (Liquid, K-Epsilon Standard, Porous)
- [ ] Criar 4 interfaces Contact Interface In-place
- [ ] Configurar 3 regiões porosas com Pi/Pv diferentes
- [ ] Configurar 5 boundary conditions (3 inlets + 2 outlets)
- [ ] Rodar Fase 1 e validar perfil de pressão
- [ ] Fase 2: adicionar Segregated Fluid Temperature
