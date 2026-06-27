# Notas — Tutorial Star-CCM+ "VOF: Boiling" → adaptação caso LN₂

> Registro do passo a passo do tutorial oficial (Star-CCM+ 20.06.007) e como adaptar
> para o estudo de BOG/rollover criogênico (caso de validação Seo & Jeong, LN₂, 201×213 mm).
> Atualizado: 2026-06-27 — tutorial COMPLETO (13 passos capturados).

---

## Visão geral do tutorial original
- **Problema:** água fervendo ao escoar sobre superfície aquecida (phase change).
- **Malha:** reaproveitada do tutorial "VOF: Gravity-Driven Flow", **escalada ÷10**
  (fator 0.1) → bocal ~50 mm.
- **Condições originais:**
  - Entrada (esquerda): água, **v = 1 m/s**, **T = 350 K**
  - Saída (direita): **T = 370 K**, pressão atmosférica
  - Fundo: **parede com T fixa = 540 K** (superfície aquecida)
  - Demais contornos: paredes sólidas **adiabáticas**
- **Objetivo didático:** mostrar impacto dos parâmetros do modelo de ebulição na
  transferência de calor.

---

## Passos cobertos pelos 5 PDFs recebidos

### 1. Converting to a Two-Dimensional Mesh
- Requisitos p/ conversão 2D: malha alinhada ao plano **X-Y**, com boundary em **Z = 0**.
- `Scenes > New > Mesh`; menu `Mesh > Convert to 2D...`; ativar "Delete 3D Regions After
  Conversion".
- Depois deletar `Continua > Physics 1` (recriado como "Physics 1 2D").

### 2. Scaling the Mesh
- `Mesh > Scale Mesh`, região `Default_Fluid 2D`, **Scale Factor = 0.1**.
- Extensão resultante: x[-0.40, 0.50] m, y[0, 0.40] m, z=0 (2D).
- `Mesh > Diagnostics` p/ checar.

### 3. Selecting the Physics Models  (continuum renomeado "Boiler")
Ordem de seleção:
- **Two Dimensional** (pré-selecionado)
- Time: **Implicit Unsteady**
- Material: **Multiphase** → Multiphase Interaction (auto)
- Multiphase Model: **Volume of Fluid (VOF)** → Segregated Flow (auto), Gradients (auto)
- Viscous Regime: **Turbulent** → RANS (auto) → **K-Epsilon** → Realizable K-Eps Two-Layer
  (auto) → Wall Distance (auto) → Two-Layer All y+ Wall Treatment (auto)
- Optional: **Segregated Multiphase Temperature**, **Gravity**

### 4. Setting the Material Properties (node "Phases")
- Fase 1 → renomear **H2O**: Material = **Liquid**, EOS = **Constant Density**
- Fase 2 → renomear **H2O (G)**: Material = **Gas**, EOS = **Constant Density**
- Substituir o Air padrão: `H2O (G) > Models > Gas > Air` → "Replace with" →
  Material Databases > Standard > Gases > **H2O (Water)**.
- Propriedades default servem ao tutorial.

---

### 5. Defining the Phase Interactions  ⭐ (modelo de mudança de fase)
- `Models > Multiphase Interaction > Phase Interactions` → New → **H2O / H2O (G)**
  (primária = líquido H2O, secundária = vapor H2O(G)).
- Modelos da interação, em ordem:
  - Optional: **VOF Boiling**
  - Boiling Models: **Rohsenow Boiling** → Multiphase Material (auto)
- Dica do tutorial: o fluxo de calor por ebulição é altamente não-linear em paredes onde
  T_parede faz parte da solução; **reduzir o Under-Relaxation Factor** do nó Rohsenow Boiling
  ajuda a convergência.

### 6. Setting Initial Conditions
- Volume Fraction = **[1.0, 0.0]** (100% líquido, 0% vapor inicialmente)
- Static Temperature = **350 K**

### 7. Setting Boundary Conditions
- Renomear região `Default_Fluid 2D` → **Fluid**. Tipos de contorno:
  - Bottom = **Wall** (T fixa = **540 K**)
  - Left = **Velocity Inlet** (T=350 K, v=1 m/s, VF=[1,0])
  - Middle = **Wall**
  - Right = **Pressure Outlet** (T=370 K, VF=[1,0])
  - TopRight, TopLeft = **Wall**

### 8. Solver Parameters & Stopping Criteria
- Implicit Unsteady: **Time-Step = 0.01 s**
- Segregated Flow > Velocity: **URF = 0.8**
- Segregated VOF: **URF = 0.1**
- Stopping: **Maximum Physical Time = 3 s**, **Maximum Inner Iterations = 1**
  (time-marching com 1 iteração/passo).

### 9. Reporting, Monitoring, Plotting
- Report `Heat Transfer` na Bottom wall → renomear "Heat Flux (Bottom Wall)".
- `Create Monitor and Plot from Report` → eixo X = Iteration.
- Usado p/ avaliar convergência ao regime permanente.

### 10. Modifying the Boiling Model Parameters
- Rohsenow usa correlação empírica com 2 parâmetros: **C_qw** e **n_p**, que dependem da
  combinação líquido-superfície e do acabamento.
- Exemplo (cobre polido): `Rohsenow Boiling` → **C_qw = 0.0128**, **n_p = 1.7**.
- Reforça que Rohsenow é **específico de parede/acabamento** → confirma que não serve p/
  evaporação interfacial criogênica.

### 11. Running the Simulation
- `Solution > Clear Solution` → `Run`. Salvar ao terminar.

### 12. Visualizing the Solution
- Cena escalar 1: **Volume Fraction of H2O (G)** (fração de vapor), Contour = Smooth Filled.
- Cena escalar 2: **Temperature**.
- Abrir o monitor plot de heat flux.

### 13. Visualizing Results
- Inspecionar abas: fração de vapor, temperatura, perfil de heat flux.

---

## ⚠️ DECISÃO DE MODELO — mudança de fase (CONFIRMADO via User Guide)

O tutorial usa **Rohsenow Boiling** = ebulição nucleada **NA PAREDE** (placa a 540 K).
No nosso caso (BOG criogênico), a mudança de fase é **evaporação na INTERFACE
líquido-vapor** (superfície livre), por não-equilíbrio térmico — não ebulição de parede.

O Star-CCM+ (VOF) oferece **3 famílias** de mudança de fase — escolha confirmada nas refs:

| Modelo | Física | Fases | Veredito |
|---|---|---|---|
| Evaporation/Condensation | Raoult, **difusão de espécies**, equilíbrio na interface | **multicomponente** | ❌ exige gás carreador (água→ar); não é N₂ puro |
| VOF Boiling (Rohsenow/Transition) | ebulição **na parede** (nucleada/filme) | single-comp. | ❌ precisa parede quente; nosso ΔT é baixo |
| **Schrage Boiling/Condensation** | **cinético**, interface líq-vapor, **não-equilíbrio** | **single-comp.** | ✅ **ESCOLHIDO** |

→ **Modelo escolhido: Schrage Boiling/Condensation.** ("Lee" é nomenclatura do Fluent;
  no Star-CCM+ o modelo cinético interfacial equivalente é o Schrage / Hertz-Knudsen-Schrage.)

### Setup do Schrage (do User Guide "Modeling Boiling in VOF")
1. Continuum: VOF + **Gravity** + **Segregated Multiphase Temperature** (obrigatórios).
2. Duas fases **single-component**: N₂ líquido (primária) + N₂ vapor (secundária).
3. `Phase Interaction > Models > Optional Models` → **Schrage Boiling/Condensation**.
4. `Schrage Boiling/Condensation > Accommodation Coefficient` → coef. de acomodação
   (0 < σ ≤ 1; calibrável — começar próximo de 1 e ajustar p/ casar P(t) de Seo & Jeong).
5. `[liquid phase] > Material Properties > Saturation Pressure` → método
   **Schrage Model Extrapolation** (default; usa Clausius-Clapeyron + calor latente).
   - Alternativas p/ p_sat: Antoine, Wagner, Polynomial(T), Table(T).
6. Definir calor latente de vaporização (via entalpias) e T_sat (~77.4 K @ 1 atm p/ LN₂).

→ Rohsenow só entraria em ebulição de parede (boilover em incêndio / heat flux alto).

---

## ADAPTAÇÕES para o nosso caso (LN₂, Seo & Jeong)

| Item | Tutorial (água) | Nosso caso (LN₂) |
|---|---|---|
| Geometria | placa/bocal 2D escalado | cilindro **201 mm × 213 mm, 6,75 L** |
| Dimensionalidade | 2D plano | **2D-axissimétrico** (cilindro vertical) |
| Fluido | H₂O líq. + H₂O(G) | **N₂ líquido + N₂ gasoso** (banco Standard) |
| Densidade | constante | avaliar densidade f(T) p/ empuxo (ou Boussinesq) |
| Parede de calor | T fixa 540 K | **fluxo de calor** (heat leak) — Seo & Jeong testam vários |
| Entrada/saída | inlet 1 m/s / outlet atm | **tanque fechado** (sem inlet/outlet); ullage pressuriza |
| Turbulência | K-ε turbulento | provável **laminar** (convecção natural fraca em LN₂) — avaliar Ra |
| Estado inicial | preenchido | **estratificado**: 2 camadas (Δρ/ΔT) p/ rollover, OU fill ~uniforme p/ self-press |
| Validação | qualitativa | comparar **P(t)** com curvas de Seo & Jeong |

### Pontos de atenção
- O tutorial usa **densidade constante** nas duas fases — para rollover/estratificação
  precisamos de **empuxo** (densidade f(T) ou Boussinesq), senão não há overturn.
- "Segregated Multiphase Temperature" é essencial (resolve energia por fase).
- Gravity ON é obrigatório.
- Falta ver (próximos PDFs): qual **modelo de ebulição/phase change** (Lee? Saturation?),
  parâmetros de troca de massa, stopping criteria e setup do solver.

---

### Adaptações dos passos 5–9
| Passo tutorial | Água | Nosso caso LN₂ |
|---|---|---|
| Phase interaction | Rohsenow Boiling | **Schrage Boiling/Condensation** na interface |
| Initial Conditions | VF=[1,0], T=350 K | VF estratificada por altura; T inicial ~77–80 K (sat. LN₂) |
| BCs | inlet/outlet + parede 540 K | **paredes fechadas** com **heat flux** (Seo & Jeong: vários valores) |
| Solver | Δt=0.01 s, t=3 s | Δt maior; **t físico = minutos a horas** (self-press. é lenta) |
| Monitor | heat flux na parede | **Pressão do ullage P(t)** + T(z) (validar vs Seo & Jeong) |
| Cenas | VF de vapor + Temperatura | VF de vapor (BOG gerado) + T(z); + perfil P(t) |
| Param. modelo | C_qw, n_p (Rohsenow) | coef. do modelo Lee (HTC de evap./cond.) |

## Pendente
- [x] Tutorial VOF: Boiling capturado por completo (13 passos)
- [x] Modelo de phase change DECIDIDO: **Schrage Boiling/Condensation** (interfacial,
      single-component, não-equilíbrio) — confirmado via User Guide. Não é Rohsenow
      (wall) nem Evaporation/Condensation (multicomponente). Ver decisão acima.
- [ ] Montar geometria LN₂ (201×213 mm) — 3D (preferência do usuário) ✓ já importada
- [ ] Trocar materiais para N₂ líq/gás (vapor = Ideal Gas)
- [ ] Inicialização via VOF Wave Flat + parede com heat flux
- [ ] Phase interaction: Schrage + Accommodation Coefficient + p_sat (Clausius-Clapeyron)
- [ ] Monitor de P(t) do ullage; validar vs Seo & Jeong
