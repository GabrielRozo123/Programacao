# Notas — Tutorial "VOF: Tank Sloshing with Adaptive Meshing"

> Segundo tutorial de referência. Fornece o **kit de redução de custo** (AMR +
> Adaptive Time-Stepping + Multi-Stepping VOF) e a forma limpa de inicializar o
> nível de líquido (VOF Waves). Complementa notas_tutorial_vof_boiling.md.
> Atualizado: 2026-06-27 — 5 PDFs recebidos.

---

## Caso do tutorial
- Água em **container 0.5 (L) × 0.02 (W) × 0.25 m (H)**, inicialmente em repouso na
  parte inferior; aceleração horizontal transiente → sloshing.
- VOF rastreia a interface água-ar; surgem gotas/bolhas.

---

## ⭐ Kit de REDUÇÃO DE CUSTO (o motivo de querermos este tutorial)

1. **AMR (Adaptive Mesh Refinement)** — refina/engrossa células dinamicamente perto da
   interface. Malha fina só onde importa → resolução de malha fina a custo reduzido.
2. **Adaptive Time-Stepping** — ajusta Δt automaticamente. Com AMR mudando o tamanho de
   célula, fixar Δt manualmente é inviável → usar time-step provider.
   - Provider recomendado: **Free Surface Implicit Multi-Step** (controla Δt p/ satisfazer
     o CFL do multi-stepping nas células perto da interface).
3. **Implicit Multi-Stepping VOF solver** — sub-passos na equação de fração volumétrica
   p/ manter interface afiada (HRIC) permitindo Δt de fluxo maior.

Contexto técnico:
- VOF usa esquema **HRIC** (High-Resolution Interface Capturing) p/ interface afiada.
- HRIC é limitado por um **CFL máximo**; se excede localmente, cai p/ upwind (1ª ordem)
  → interface "borrada". Multi-stepping reduz o CFL efetivo sem encolher o Δt global.

---

## Passos cobertos pelos 5 PDFs

### 1. Generating the Volume Mesh
- ⚠️ Tutorial usa **malha já definida** ("meshing models and mesh reference values already
  defined") → só clica **Generate Volume Mesh**.
- Lição: a malha é a **mais grossa possível** que ainda resolve a superfície livre;
  o AMR refina o resto. (NÃO ensina a montar a operação de malha do zero — lacuna!)

### 2. Selecting the Physics Models
- Three Dimensional, **Implicit Unsteady**, **VOF**, Segregated Flow (auto), Gradients (auto)
- Turbulent → K-Epsilon → Realizable Two-Layer (auto), Two-Layer All y+ (auto)
- Optional: **Gravity**, **VOF Waves** → VOF Wave Zone Distance (auto)

### 3. Defining the Water and Air Phases
- Fase **Water**: Liquid, Constant Density. Fase **Air**: Gas, Constant Density.
- **VOF Waves → New → Flat** (Flat Vof Wave 1):
  - propriedade-chave **Point On Water Level** = posição inicial da superfície (default [0,0,0]).
  - dá **solução exata do campo de pressão** no 1º time-step.
- **Initial Conditions** via Field Functions geradas pela Flat Wave:
  - Pressure → Field Function → **Hydrostatic Pressure of Heavy Fluid of Flat Vof Wave 1**
  - Volume Fraction → Composite N-1 → Water → **Volume Fraction of Heavy Fluid of Flat Vof Wave 1**

### 4. Setting Up the Phase Interaction
- Phase Interaction Water/Air → renomeado "Surface Tension".
- Modelo: **Surface Tension Force** → Multiphase Material (auto).
- Valor água-ar: **0.072 N/m**. Ativar **Semi-implicit Surface Tension** (estabilidade p/ Δt maior).

---

## Aplicação ao nosso caso LN₂ (síntese dos 2 tutoriais)

| Item | De qual tutorial | No nosso caso |
|---|---|---|
| Inicializar nível de líquido | Sloshing (VOF Waves Flat) | **VOF Wave Flat** em y=170 mm (80% de 213 mm) → init automático de P e VF |
| Refino de interface | Sloshing (AMR) | **AMR** na interface líquido-vapor |
| Controle de Δt | Sloshing (Adaptive Time-Step) | **Free Surface Implicit Multi-Step** |
| Phase change (evaporação) | Boiling (mas trocar Rohsenow) | **Evaporation/Condensation (Lee)** — do User Guide |
| Tensão superficial | Sloshing (0.072 N/m água) | **σ(LN₂) ≈ 0.0089 N/m** + Semi-implicit |
| Energia por fase | Boiling | **Segregated Multiphase Temperature** |
| Vapor compressível | (nenhum — ambos const. density) | **N₂ gás = Ideal Gas** (p/ ullage pressurizar em tanque fechado) |

### Plano de modelos físicos (continuum) p/ LN₂
- Three Dimensional, Implicit Unsteady, Gravity
- VOF + **HRIC**, Segregated Flow, Segregated Multiphase Temperature
- **VOF Waves** (Flat → nível inicial)
- **AMR** + **Adaptive Time-Stepping** (Free Surface Implicit Multi-Step) + Multi-Stepping VOF
- Turbulência: avaliar laminar vs K-ε (convecção natural fraca em LN₂)
- Fases: N₂ Liquid (const. density ou f(T)) + N₂ Gas (**Ideal Gas**)
- Phase Interaction: **Surface Tension (σ≈0.0089)** + **Evaporation/Condensation (Lee)**

---

## ⚠️ LACUNA EM ABERTO — geração de malha
Os DOIS tutoriais (Boiling e Sloshing) usaram malha **pré-definida**. Ainda falta o
workflow de **criar a operação de malha do zero** (Automated Mesh: Surface Remesher +
Trimmed/Polyhedral + Prism Layer + base size). Opções:
- (a) pegar o PDF "Parts-Based Meshing External Aerodynamics" (tem o workflow), ou
- (b) seguir direto pela orientação (workflow padrão é simples p/ um cilindro limpo).

## Pendente
- [ ] User Guide: página de **Evaporation/Condensation (Lee)** — coef. e T_sat
- [ ] Resolver a malha (Automated Mesh no cilindro)
- [ ] Definir σ(LN₂) e propriedades N₂ líq/gás (Ideal Gas no vapor)
- [ ] Montar VOF Wave Flat no nível y=170 mm
