# ✅ CHECKLIST do setup completo — Ciclone Valgroup (STAR-CCM+)

> Consolida os 12 tutoriais Siemens estudados + os ajustes de engenharia do nosso caso.
> Siga na ordem. ⚠️ = onde o nosso caso **difere do tutorial** (e por quê).

---

## FASE 0 — pronto ✅
- [x] Geometria importada (`ciclone_stairmand_Dc290_fluido.step`, mm)
- [x] Faces nomeadas: `Inlet` · `Outlet_gas` · `outlet_dust` · `Walls`
- [x] Região criada, 1 boundary por face
- [x] Malha: **486.990 células** · Face Validity **100% em 1,0** · Volume Change mín **1,1e-2**

---

## FASE 1 — Escoamento só GÁS (steady)

### 1.1 Modelos (`Continua → Physics 1 → Select Models`, nesta ordem)
```
Three Dimensional · Steady · Gas · Segregated Flow · Constant Density
Viscous Regime: Turbulent → RANS
   → K-Omega Turbulence → SST (Menter) → All y+ Wall Treatment
```
> ⚠️ O tutorial usa K-Omega **"to limit the simulation run time"**. Para o entregável final
> queremos **RSM** (§4.1). Estratégia: **K-Omega primeiro** (robusto) → depois RSM partindo dele.

### 1.2 Material do gás
`Physics 1 → Models → Gas → [Ar] → Material Properties`
- [ ] **Density (Constant) = 3,946 kg/m³**
- [ ] **Dynamic Viscosity (Constant) = 9,5e-5 Pa·s**

### 1.3 Condições de contorno — gás
| Boundary | Tipo | 100% | 50% |
|---|---|---|---|
| `Inlet` | **Velocity Inlet** | **15,23 m/s** | **7,62 m/s** |
| | Turbulence Specification | **Intensity + Length Scale** | idem |
| | Turbulence Intensity | **0,041** | **0,045** |
| | Turbulent Length Scale | **0,0058 m** | **0,0058 m** |
| `Outlet_gas` | **Pressure Outlet** | 0 Pa | 0 Pa |
| `outlet_dust` | ⚠️ **WALL** | — | — |
| `Walls` | Wall (no-slip) | — | — |

> ⚠️ **`outlet_dust` = WALL, não outlet.** Na planta há **airlock** (selado). Como Pressure Outlet
> o gás foge pelo fundo, o vórtice não fecha e a eficiência sai errada.

### 1.4 Solver e parada
- [ ] Under-Relaxation: **Velocity 0,6 · Pressure 0,3**
- [ ] `Stopping Criteria → Maximum Steps = 1500`
- [ ] **Novo critério por monitor:** `New Monitor Criterion → Continuity → Minimum Value 1,0e-4`
- [ ] Monitor de **ΔP** (`Inlet` − `Outlet_gas`) ⭐

### 1.5 ✅ VALIDAÇÃO — o marco do projeto
Comparar o **ΔP do CFD** com o **analítico: 29,3 mbar**.
Se ficarem na mesma ordem (±30%), **a base está validada** e podemos confiar no resto.

---

## FASE 2 — Partículas (Lagrangeano)

### 2.1 Ativar
- [ ] `Physics 1 → Select Models → Optional Models → **Lagrangian Multiphase**`
- [ ] `Lagrangian Phases → botão direito → New → **Free-stream Phase**`

### 2.2 Modelos da fase
| Group Box | Modelo |
|---|---|
| Particle Type | **Material Particles** *(traz Pressure Gradient Force + Spherical Particles)* |
| Material | **Solid** |
| Equation of State | **Constant Density** |
| Optional Particle Forces | **Drag Force** ⚠️ **+ Gravity** |
| | ⚠️ **+ Turbulent Dispersion** |
| Track Sampling | Track File |
| Optional Models | **Two-Way Coupling** |

> ⚠️ **Turbulent Dispersion e Gravity não estão no tutorial** (ele é um cotovelo simples).
> Sem dispersão os finos são captados demais; sem gravidade a queda no cone sai errada.

### 2.3 Propriedades
- [ ] `Solid → [material] → Density → Constant = **1500 kg/m³**`
  > ⚠️ Densidade da **PARTÍCULA**. Os 776,75 da planilha são **bulk** (com vazios) — subestimam a inércia.
- [ ] `Drag Force → Drag Coefficient Method = **Schiller-Naumann**` *(Re_p do nosso caso: 0,02–37 ✓)*
- [ ] Track File Vectors: Parcel Centroid · Particle Velocity

### 2.4 BCs das partículas
`Lagrangian Phases → Phase 1 → Boundary Conditions`

| Boundary | Active Mode | Valores |
|---|---|---|
| `Walls` | **Rebound** | ⚠️ Normal **0,8** · Tangencial **0,9** *(tutorial usa 1,0 = elástico perfeito)* |
| **`outlet_dust`** | **Escape** | ⭐ = **partícula CAPTURADA** |
| `Outlet_gas` | **Escape** | = partícula **PERDIDA** |

> ⚠️ **Restituição:** o tutorial usa 1,0 (rebote perfeito) → a partícula quica de volta ao gás →
> **subestima a captura**. Valores reais char/aço ficam em 0,7–0,9. **Rodar 0,8/0,9 e testar
> sensibilidade com 1,0** — a diferença entra como incerteza no relatório.

### 2.5 Injetores — a curva de eficiência
`Injectors → New` (um por classe de tamanho)

**Configuração comum a todos:**
- [ ] Type = **Part Injector** · Inputs = boundary **`Inlet`** · Lagrangian Phase = Phase 1
- [ ] `Conditions → Flow Rate Specification = **Mass Flow Rate**`
- [ ] `Conditions → Flow Rate Distribution Method = **Per Injector**`
- [ ] `Conditions → Velocity Specification Method = **Magnitude + Direction**`
- [ ] `Values → Velocity Magnitude = **15,23 m/s**` (7,62 a 50%)

**Um injetor por classe** (massa igual — 80 kg/h ÷ 8):

| Injetor | Particle Diameter | Mass Flow Rate (100%) | (50%) |
|---|---|---|---|
| `inj_001um` | **1,0e-6 m** | **0,002778 kg/s** | 0,001389 |
| `inj_002um` | 2,0e-6 m | 0,002778 | 0,001389 |
| `inj_005um` | 5,0e-6 m | 0,002778 | 0,001389 |
| `inj_010um` | 1,0e-5 m | 0,002778 | 0,001389 |
| `inj_020um` | 2,0e-5 m | 0,002778 | 0,001389 |
| `inj_050um` | 5,0e-5 m | 0,002778 | 0,001389 |
| `inj_075um` | 7,5e-5 m | 0,002778 | 0,001389 |
| `inj_150um` | 1,5e-4 m | 0,002778 | 0,001389 |
| **soma** | | **0,022222 kg/s = 80 kg/h** ✓ | 40 kg/h |

### 2.6 🚨 O AJUSTE MAIS CRÍTICO — Maximum Residence Time
`Solvers → Lagrangian Multiphase → Steady → **Maximum Residence Time**`

| | valor |
|---|---|
| Tutorial | 0,1 s |
| Residência do gás no nosso ciclone | **V/Q = 61,8 L / 128,1 L/s = 0,48 s** |
| **NOSSO valor** | ⚠️ **10 s** (≈21× a residência) |

> **Por quê:** 0,1 s seria **1/5 da residência do gás** — a partícula seria **deletada antes de ser
> capturada** → **eficiência artificialmente baixa**. É um erro clássico e silencioso.
> **Verificar depois:** quantas parcelas terminaram por limite de tempo. Se for mais que uns poucos %, aumentar.

### 2.7 Relatórios da eficiência
Para cada classe: `Reports → New → Lagrangian Mass Flow` em `outlet_dust` e em `Outlet_gas`.
```
η_classe = ṁ(outlet_dust) / ṁ(injetado)
```
- [ ] Plotar **η × d** → **a curva de eficiência de coleta** = entregável principal ⭐

---

## FASE 3 — Visualização
- [ ] **Scalar Scene**: `Total Pressure` no plano de corte, color map **blue-red balanced**
- [ ] **Streamlines**: seed na boundary `Inlet` · Mode **Ribbons** · colorido por Velocity ·
      `2nd Order Integrator → Maximum Propagation = **15**` · Opacity do corpo 0,3
- [ ] **Particle Tracks**: cena com as trajetórias coloridas por diâmetro/velocidade

---

## FASE 4 — Refinamentos (depois da base validada)

### 4.1 RSM
Trocar K-Omega por **Reynolds Stress Turbulence**, inicializando do campo K-Omega.
Comparar ΔP e perfil de velocidade tangencial.

### 4.2 Transiente + Curvature Correction
- [ ] Desativar `Steady` → **Implicit Unsteady**
- [ ] `SST (Menter) K-Omega → Curvature Correction = **On**`
- [ ] ⚠️ **Time-Step = 2,0e-4 s** *(tutorial: 5e-4 — o nosso ciclone é maior)*
- [ ] Under-Relaxation: **Velocity 0,9 · Pressure 0,4** *(maiores que no steady)*
- [ ] Max Inner Iterations **5–8** · **Max Physical Time ≥ 1,5 s** *(3 residências; tutorial usa 0,5 s = só 1)*

### 4.3 CHT (requisito do e-mail do Lucas)
Verificar **T_parede > 250°C** (orvalho dos pesados C12–C15). Precisa da **espessura de parede**
(corrosão HCl + erosão do char mineral) — a calcular.

### 4.4 Erosão
Char com **21% de minerais** (Ti 14,9 + Si 3,5 + Fe 3,2) → mapa de desgaste do cone.

---

## 📌 As 4 armadilhas deste caso (resumo)
1. **`outlet_dust` como outlet** → gás foge pelo fundo, eficiência errada. **Use WALL + Escape.**
2. **Maximum Residence Time curto** → partícula deletada antes de captar. **10 s, não 0,1.**
3. **ρ_s = 776,75 (bulk)** → subestima a inércia. **Use 1500 (partícula).**
4. **Sem Turbulent Dispersion** → finos captados demais. **Ligar.**
