# Notas — Tutorial "VOF: Tank Sloshing with Adaptive Meshing"

> Segundo tutorial de referência. Fornece o **kit de redução de custo** (AMR +
> Adaptive Time-Stepping + Multi-Stepping VOF) e a forma limpa de inicializar o
> nível de líquido (VOF Waves). Complementa notas_tutorial_vof_boiling.md.
> Atualizado: 2026-06-27 — 10 PDFs recebidos (tutorial sloshing completo).

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
  - ⚠️ **ARMADILHA: Vertical Direction aponta para CIMA = [0,0,1]** (contrário à gravidade),
    NÃO [0,0,-1]. Se inverter, o fluido pesado vai pro topo e o leve pro fundo (vapor
    embaixo) e a pressão hidrostática inverte. No caso LN₂: Vertical Direction=[0,0,1],
    Point On Water Level=[0,0,0.170]. Conferir sempre a scene de VF após inicializar.
  - dá **solução exata do campo de pressão** no 1º time-step.
- **Initial Conditions** via Field Functions geradas pela Flat Wave:
  - Pressure → Field Function → **Hydrostatic Pressure of Heavy Fluid of Flat Vof Wave 1**
  - Volume Fraction → Composite N-1 → Water → **Volume Fraction of Heavy Fluid of Flat Vof Wave 1**

### 4. Setting Up the Phase Interaction
- Phase Interaction Water/Air → renomeado "Surface Tension".
- Modelo: **Surface Tension Force** → Multiphase Material (auto).
- Valor água-ar: **0.072 N/m**. Ativar **Semi-implicit Surface Tension** (estabilidade p/ Δt maior).

### 5. Defining Tank Acceleration  (específico do sloshing — NÃO usamos)
- Sloshing é movido por componente horizontal **variável** da gravidade, via field function
  `X-acceleration` interpolada de tabela. `Reference Values > Gravity` = [${X-acceleration},0,-9.81].
- **No nosso caso:** gravidade **constante** [0,0,-9.81]. Não há aceleração imposta.
- 💡 Guardar a técnica: se um dia simularmos rollover disparado por movimento de navio
  (FSRU/embarcação), é exatamente assim que se impõe a aceleração do casco.

### 6. Setting Up Multi-Stepping  (valores concretos)
- `Solvers > Segregated VOF > Sub-Steps = 4`.
- Permite Δt global ~4× maior mantendo interface afiada (CFL efetivo = CFL_substep × 4).

### 7. Setting Up Adaptive Time-Stepping
- Adicionar modelo opcional **Adaptive Time-Step**.
- `Models > Adaptive Time-Step > Time-Step Providers > New > Free Surface Implicit Multi-Step`.
  - Cut-off Percentage = 0 (default).
- **Max time-step:** `Solvers > Implicit Unsteady > Time-Step = 2.0E-3 s`.
- **Min time-step:** `Solvers > Adaptive Time-Step > Minimum Time-Step = 1.0E-4 s`
  (ordem de grandeza abaixo do máximo).
- Initial Time-Step Option = **Auto** (derivado do provider em t=0).

### 8. Setting Up Adaptive Mesh Refinement (AMR)
- Adicionar modelo opcional **Adaptive Mesh**.
- `Models > Adaptive Mesh > Adaptive Mesh Criteria > New > Free Surface Mesh Refinement`.
- `Models > Adaptive Mesh` props:
  - **Transition Width = 5** (células de transição entre níveis; evita salto brusco grosso→fino).
  - **Limit Cell Size = Activated**, **Min Adaption Cell Size = 1.0E-6 m**.
  - Prism Cell Refinement = default.
- `Adaptive Mesh Criteria > Free Surface Mesh Refinement` props:
  - **Max Refinement Level = 2** (nº máx. de refinos; escolher o menor que resolve a feature).
  - **Enabled = Activated**.
- `Solvers > Adaptive Mesh > Trigger > Time-Step Frequency = 1` (refina a cada passo;
  recomendado quando se usa adaptive time-stepping, pois Δt é desconhecido a priori).
- `Regions > Tank > Physics Conditions > Adaption Option > Enable Adaption` = ligado.

### 9. Setting the Stopping Criteria
- **Maximum Inner Iterations = 15** (ativado).
- **Maximum Physical Time = 0.7 s** (ativado).
- Maximum Steps = desativado.

---

## Aplicação ao nosso caso LN₂ (síntese dos 2 tutoriais)

| Item | De qual tutorial | No nosso caso |
|---|---|---|
| Inicializar nível de líquido | Sloshing (VOF Waves Flat) | **VOF Wave Flat** em y=170 mm (80% de 213 mm) → init automático de P e VF |
| Refino de interface | Sloshing (AMR) | **AMR** na interface líquido-vapor |
| Controle de Δt | Sloshing (Adaptive Time-Step) | **Free Surface Implicit Multi-Step** |
| Phase change (evaporação) | Boiling (mas trocar Rohsenow) | **Schrage Boiling/Condensation** (single-comp., interfacial) |
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
- Phase Interaction: **Surface Tension (σ≈0.0089)** + **Schrage Boiling/Condensation**

---

### ⚠️ Escalas de tempo — diferença crítica vs sloshing
O sloshing roda **0.7 s** com Δt_max = 2e-3 s (dinâmica rápida da onda). A nossa
auto-pressurização é **lenta** (minutos a horas): o fator limitante deixa de ser o CFL da
onda e passa a ser o **acoplamento térmico/evaporação**.
→ No nosso caso o **Δt_max pode ser MUITO maior** (ordem de segundos), e o
  **Maximum Physical Time** será de minutos/horas. O Adaptive Time-Step cuida do ajuste,
  mas precisamos definir Δt_max coerente com a escala de evaporação, não de sloshing.

### Parâmetros AMR/solver sugeridos p/ LN₂ (ponto de partida)
| Parâmetro | Sloshing | LN₂ (chute inicial) |
|---|---|---|
| Segregated VOF Sub-Steps | 4 | 4 (manter) |
| Δt_max (Implicit Unsteady) | 2e-3 s | ~0.1–1 s (calibrar) |
| Δt_min (Adaptive Time-Step) | 1e-4 s | ~1e-3 s |
| AMR Transition Width | 5 | 5 (manter) |
| AMR Max Refinement Level | 2 | 2–3 |
| AMR Trigger Frequency | 1 | 1 (manter) |
| Max Physical Time | 0.7 s | minutos–horas (validação Seo & Jeong) |
| Max Inner Iterations | 15 | 10–15 |

## Refinamentos de AMR (das refs do User Guide)

- **HRIC exige CFL < 0.5** na interface → por isso AMR + Adaptive Time-Step.
- **Free Surface Mesh Refinement só refina PERTO da interface** — NÃO refina longe dela.
  ⚠️ **Crítico p/ nós:** o heat leak cria **camada-limite térmica/convectiva nas PAREDES**
  (longe da superfície livre). O AMR de superfície livre **ignora** essa região.
  → Resolver com: (a) **Prism Layers** + base mesh fina o suficiente na parede, e/ou
    (b) **User-Defined Mesh Adaption** adicional, e/ou (c) **Transition Width** maior.
- **Trigger:** só **Time Step** ou **Delta Time** (Iteration/Update Event NÃO suportados
  p/ free surface). Com adaptive time-stepping → refinar a cada **1–2 passos**.
- **Sharp Reconstruction** (opcional): `Models > Volume Of Fluid (VOF) >
  Adaptive Mesh Interpolation > Option = Sharp Reconstruction` — reduz "smearing" da
  interface ao refinar, mas é mais caro e exige interface bem resolvida na malha grossa.
- **Max Refinement Level:** começar em **2**; cada nível = metade do tamanho base.
  Subir incrementalmente só se necessário (contagem de células cresce rápido).
- **Resolution Criterion for Interface Detection:** sensibilidade p/ detectar a interface
  (valores maiores toleram interface mais "borrada").
- **Swept Distance Estimation Factor [up/down]:** default 1.5; aumentar se a interface
  "escapar" da zona refinada entre dois eventos de AMR.

## MALHA — receita (do tutorial Parts-Based Meshing, adaptada ao cilindro LN₂)

### Workflow Automated Mesh (genérico, do tutorial aero)
1. `Geometry > Operations > New > Mesh > Automated Mesh`.
2. Selecionar a part (no nosso caso **ln2_tank_3d**).
3. Meshers a ativar:
   - Surface Meshers: **Surface Remesher**
   - Optional Surface: **Automatic Surface Repair** (não essencial p/ CAD limpo)
   - Core Volume: **Trimmed Cell Mesher** (hexa-dominante; bom p/ interface horizontal)
   - Optional Boundary Layer: **Prism Layer Mesher**
4. `Meshers > Surface Remesher > Minimum Face Quality = 0.1`.
5. `Default Controls > Prism Layer Controls`: **Number of Prism Layers = 5**,
   **Boundary March Angle = 85°**.
6. `Default Controls > Base Size` (valor base) e Surface Growth Rate = Fast.
7. (Opcional) `Custom Controls > New > Surface Control` p/ refinar/engrossar superfícies
   específicas (% do base size em Minimum/Target Surface Size).
8. `Operations > Automated Mesh > Execute` p/ gerar a malha.

### Adaptação ao cilindro LN₂ (D=201 mm, H=213 mm)
| Controle | Aero (carro) | Nosso LN₂ |
|---|---|---|
| Part | Fluid Volume | **ln2_tank_3d** |
| Core mesher | Trimmed | **Trimmed** (interface líq-vapor ~horizontal casa bem com hexa) |
| Base Size | 0.02 m | **~0.005 m (5 mm)** → ~40 células no diâmetro, ~43 na altura |
| Prism Layers | 5 | **5** (essencial! camada-limite térmica do heat leak na parede) |
| Boundary March Angle | 85° | 85° |
| Min Face Quality | 0.1 | 0.1 |

### Por que Prism Layers importam tanto aqui (liga ao alerta de AMR)
O Free Surface AMR **não refina na parede**. A camada-limite térmica/convectiva gerada pelo
heat leak fica nas paredes (fundo, parede_lateral, topo). Os **5 prism layers** resolvem
exatamente essa região → sem eles, o fluxo de calor entrando no líquido fica subestimado e
a taxa de auto-pressurização P(t) sai errada. Aplicar prism layers nas **3 paredes**.

### Estimativa de custo
Base 5 mm em cilindro 201×213 mm → ~50–70k células base (3D) + prism + AMR local na
interface (Max Level 2). Totalmente factível na máquina. Se pesar, subir base p/ 6–8 mm.

## ⚠️ ARMADILHA CRIOGÊNICA — Minimum Allowable Temperature (clamp)

Sintoma na 1ª rodada: T_bulk travou em **exatamente 100,0 K** (−173,15 °C) mesmo
inicializando em 77,35 K, e a pressão disparou para ~720 kPa em 0,07 s.

Causa: `LN2 > Reference Values > Minimum Allowable Temperature` tem **default ~100 K**.
LN₂ a 77,35 K fica ABAIXO do piso → o solver clampa o líquido para 100 K. A 101 kPa,
líquido a 100 K está **superaquecido** (Tsat=77 K) → flash instantâneo → pressão sobe
até Psat(100 K)≈720 kPa. Self-consistent, mas partindo da T errada.

Correção: **Minimum Allowable Temperature = 50 K** (folga abaixo da operação criogênica).
SEMPRE baixar esse piso em simulação criogênica (LN₂, LNG, LH₂). Conferir T_bulk após
inicializar: deve ler a T de operação, não 100 K.

Mitigações p/ a rodada definitiva (refino, não a causa):
- Δt máx (Implicit Unsteady) 0.1 → **1e-3 s** (resolve transiente de partida)
- Accommodation Coefficient do Schrage 0.01 → **1e-4** (desacelera evaporação)

## Pendente
- [x] Modelo de mudança de fase definido: **Schrage Boiling/Condensation** (ver
      notas_tutorial_vof_boiling.md). Evaporation/Condensation descartado (multicomp.).
- [ ] Resolver a malha (Automated Mesh no cilindro: + Prism Layers p/ camada-limite parede)
- [ ] Definir σ(LN₂) e propriedades N₂ líq/gás (Ideal Gas no vapor)
- [ ] Montar VOF Wave Flat no nível y=170 mm
- [ ] Accommodation Coefficient do Schrage (calibrar vs Seo & Jeong)
