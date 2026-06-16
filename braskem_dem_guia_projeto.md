# Braskem PE5 — DEM Screw Conveyor: Guia de Projeto
**Cliente:** Jeferson Diefenthaler — Braskem PE5 (RS)  
**Problema:** Embuchamento em 6 roscas helicoidais transportando PEAD úmido com hexano  
**Ferramenta:** Star-CCM+ 2506 — Discrete Element Method (DEM)  
**Reunião:** Quinta-feira 9h00  

---

## 1. MAPA TUTORIAL → CASO BRASKEM

### Seção 1 — Overview (DEM_Particle_Settling)
| Tutorial | Braskem |
|---|---|
| Domínio: caixa retangular (ar) | Domínio: calha cilíndrica U-trough + rosca helicoidal |
| Partículas: grãos de trigo esféricos | Partículas: pó PEAD (HDPE) esférico ou poliedral |
| Física: gravidade pura (sem fluido) | Física: gravidade + rotação da rosca + coesão hexano |
| Objetivo: partículas assentam no fundo | Objetivo: partículas transportadas ou embuchamento |

---

### Seção 2 — Generating the Volume Mesh
**Tutorial:**
- Surface Wrapper → Polyhedral Mesher na caixa
- Malha não precisa ser fina — partículas têm sua própria resolução analítica
- Base Size ≈ 5–10× diâmetro da partícula

**Braskem — o que muda:**
- Importar STEP da rosca (Python/CadQuery) → Star-CCM+
- Malhar apenas o **volume da calha** (trough), não a pá da rosca
- A rosca é **Moving Wall** (fronteira móvel, não malha volumétrica)
- Cell size mínimo: ≥ 3× D_partícula (para DEM funcionar corretamente)
- Recomendação: Base Size = 10 mm se D_p ≈ 2 mm

---

### Seção 3 — Selecting Physics Models
**Tutorial — modelos selecionados:**
```
Space:              Three Dimensional
Time:               Implicit Unsteady  ← DEM sempre transiente
Material:           Gas (ar como carrier, ou Solid para DEM-only)
Lagrangian:         Lagrangian Multiphase
DEM:                Discrete Element Method ✓
Gravity:            On ✓
```

**Braskem — modelos adicionais:**
```
Contact Model:      Hertz-Mindlin (base) → + JKR Cohesion (hexano)
Carrier phase:      DEM-only na fase 1 (sem acoplamento fluido)
                    Acoplamento fluido-DEM na fase 2 (drag do ar, se necessário)
```

**Sequência recomendada:**
1. Rodar DEM-only primeiro (sem fluido) → mais rápido, valida contatos
2. Adicionar JKR e verificar se clogging emerge
3. Adicionar carrier phase (ar) apenas se drag for relevante (partículas > 1mm, vel > 5 m/s)

---

### Seção 4 — Defining Lagrangian Phases
**Tutorial — parâmetros do grão de trigo:**
```
Shape:              Sphere
Density:            ~1300 kg/m³
Diameter:           3–5 mm (monodisperse)
Temperature:        isotérmico
```

**Braskem — parâmetros PEAD (HDPE):**
```
Shape:              Sphere (fase 1) / Polyhedra (fase 2 — mais preciso)
Density (ρ):        950 kg/m³
Diameter (D_p):     *** CONFIRMAR COM JEFERSON ***
                    Pellets normais: D50 ≈ 3–5 mm
                    Pó fino:         D50 ≈ 0.3–1 mm  ← mais coesivo
Young's Modulus:    E = 1.0 GPa (real) → reduzir para 10 MPa (soft sphere, 100× mais rápido)
Poisson's Ratio:    ν = 0.46
Restitution (e):    0.5–0.7 (impacto partialmente elástico)
Static friction:    μ_s = 0.3–0.5 (PEAD-PEAD seco)
Rolling friction:   μ_r = 0.01–0.05
```

**Soft Sphere Approximation — por que usar:**
- E real PEAD = 1 GPa → Δt_DEM ≈ 5×10⁻⁷ s (muito pequeno → CPU cara)
- E reduzido = 10 MPa → Δt_DEM ≈ 5×10⁻⁶ s (10× maior → 10× mais rápido)
- Válido quando: forças de coesão e atrito dominam sobre deformação elástica

---

### Seção 5 — Defining the DEM Particle Interaction (Hertz-Mindlin + JKR)
**Tutorial — parâmetros Hertz-Mindlin:**
```
Normal force:       Hertz (não-linear, usa E* e ν)
Tangential force:   Mindlin (incremento de escorregamento)
Damping:            Coef. restituição e = 0.6
Static friction:    μ_s (partícula-partícula e partícula-parede)
```

**Braskem — adicionar JKR Cohesion (hexano):**
```
Modelo:             JKR (Johnson-Kendall-Roberts)
Parâmetro chave:    Surface Energy  γ  [J/m²]

Valores de referência:
  PEAD seco:        γ ≈ 0.03–0.05 J/m²  (van der Waals)
  PEAD + hexano:    γ ≈ 0.05–0.20 J/m²  (ponte líquida)  ← FAIXA CRÍTICA

Equação JKR implementada no Star-CCM+:
  F_adh = −√(8π · γ_eff · E* · a³)
  onde a = raio da área de contato (função de F_normal e E*)
```

**Estudo paramétrico:**
```
γ = 0.03 J/m²  → partículas secas    → transporte normal ✓
γ = 0.08 J/m²  → levemente úmidas    → possível compactação
γ = 0.15 J/m²  → saturadas em hexano → embuchamento previsto 🚨
```

**Parâmetros parede (aço AISI 304):**
```
E_wall:   200 GPa → reduzir para 100 MPa (soft sphere)
ν_wall:   0.27
μ_wall:   0.2–0.4 (PEAD sobre aço polido)
```

---

### Seção 6 — Setting Reference Values
**Tutorial:** Pressão de referência = 101.325 Pa, T = 300 K  
**Braskem:** Pressão ambiente dentro do degasser (confirmar com Jeferson — pode ser levemente pressurizado ou a vácuo parcial para remover hexano)

---

### Seção 7 — Setting the Boundary Conditions
**Tutorial:** Paredes com condição DEM (e, μ), sem inlet/outlet para DEM-only  

**Braskem:**
```
Calha (trough wall):    Wall → DEM Interaction → E_steel, ν_steel, μ_PEAD-aço
Pá da rosca (blade):   Moving Wall → Motion: Rotation (ω rad/s) → DEM Interaction
Inlet (extremidade):    DEM Injector (configurado na próxima seção)
Outlet (extremidade):   Wall com DEM Escape (partículas saem → contadas no report)
```

---

### Seção 8 — Creating an Injector
**Tutorial:**
```
Tipo:       Point Injector ou Surface Injector
Taxa:       N partículas/s ou kg/s
Velocidade: v_inicial ≈ 0 (partículas caem por gravidade)
Duração:    Contínua (durante toda a simulação)
```

**Braskem:**
```
Tipo:           Surface Injector (na face de entrada da calha)
Taxa:           *** CONFIRMAR COM JEFERSON: kg/h de alimentação? ***
Velocidade:     v_inicial = 0 (alimentação por gravidade na entrada)
Temperatura:    isotérmico (sem troca de calor)
Distribuição:   Rosin-Rammler ou Normal centrada em D50
```

---

### Seção 9 — Solver Parameters and Stopping Criteria
**Tutorial — Δt crítico (DEM):**

O time step DEM é limitado pelo **Rayleigh Time**:
```
T_Rayleigh = π · R · √(ρ / G*)
onde:
  R  = raio da partícula [m]
  ρ  = densidade [kg/m³]
  G* = módulo de cisalhamento efetivo [Pa]

Para PEAD D_p = 2 mm (R = 0.001 m), E = 10 MPa (soft sphere), ν = 0.46:
  G  = E / (2(1+ν)) = 10e6 / 2.92 ≈ 3.42 MPa
  T_R = π × 0.001 × √(950 / 3.42e6) ≈ 1.66×10⁻⁴ s

  Δt_DEM = 10% × T_R ≈ 1.7×10⁻⁵ s  ✓ (razoável!)

Com E real = 1 GPa (soft = 10 MPa):
  Δt_DEM sem soft sphere ≈ 5×10⁻⁷ s  → 34× mais iterações → inviável
```

**Critério de parada:**
```
Opção 1:  Tempo físico máximo = 10–30 s (suficiente para observar clogging)
Opção 2:  Max Particles = 50.000 (quando atingir → parar)
Opção 3:  Monitor: se Mass Flow Rate outlet = 0 por 5 s → clogging confirmado
```

---

### Seção 10 — Setting Up a Visualization Scene
**Tutorial:** Scalar Scene colorindo partículas por velocidade (m/s)

**Braskem — cenas recomendadas:**

| Cena | Colorir por | O que mostra |
|---|---|---|
| Particle Velocity | Velocidade (m/s) | Fluxo normal vs zona estagnada |
| Contact Force | Força de contato (N) | Onde está a maior pressão → ponto de clogging |
| Coordination Number | Nº de contatos/partícula | > 6 = compactado → embuchamento 🚨 |
| Particle Position (anim.) | Tempo | Evolução temporal do clogging |

---

### Seção 11 — Solution History + Running
**Tutorial:** Gravar posições a cada N timesteps → animação

**Braskem:**
```
Frequência:     a cada 0.05–0.1 s (captura a dinâmica do clogging)
Dados a gravar: Particle Position, Velocity, Contact Force, Coordination Number
Formato:        .simh → exportar como animação .mp4 para apresentação ao cliente
```

---

## TUTORIAL 2 — DEM PARTICLES IN A CONVEYOR (10 seções)

### T2-S1 — Overview
**Tutorial:** Geometria importada (não criada internamente); esteira inclinada transportando grãos para uma hopper de coleta
**Braskem:** Mesma lógica — importar STEP da rosca; calha horizontal em vez de esteira inclinada

### T2-S2 — Visualizing Imported Geometry and Surface Mesh
**Tutorial:** Verificar se a surface mesh importada não tem gaps, inverted faces ou free edges antes de malhar  
**Braskem — checklist ao importar o STEP:**
```
✓ Verificar se a hélice não tem gaps na junção com o eixo
✓ Verificar se a calha (trough) é uma superfície fechada
✓ Verificar orientação das normais (devem apontar para dentro do fluido)
✓ Reparar com Surface Repair Tool se necessário antes de avançar
```

### T2-S3 — Generating the Volume Mesh (Conveyor)
**Tutorial vs. Settling — diferença crítica:**
- Conveyor tem duas regiões: **Fluid Region** (volume) + **Motion Region** (superfície da esteira)
- A superfície da esteira NÃO é malhada volumetricamente — é apenas uma boundary
- Polyhedral + Surface Remesher, Base Size = 10–20mm para grãos ~5mm

**Braskem:**
```
Regions:
  [1] Trough Volume   → Polyhedral mesh (células onde as partículas existem)
  [2] Screw Blade     → Surface only (Moving Wall boundary — sem volume)
  [3] Shaft           → Surface only (Moving Wall — mesma rotação da pá)

Base size: 15 mm (se D_p ≈ 3 mm → razão ≈ 5× ✓)
Prism layers: NÃO necessário para DEM-only (sem camada limite viscosa)
```

### T2-S4 — Selecting Physics Models (Conveyor)
**Modelos adicionais vs. Settling:**
```
IGUAL ao Settling, MAS adiciona:
  ✓ Motion: Rotation    ← NOVO (não existia no Settling)
  ✓ Reference Frame: Lab Frame (inercial)
```
**Braskem:** selecionar **Rotation** (não Translation como na esteira do tutorial)

### T2-S5 — Defining Lagrangian Phases (Conveyor)
**Tutorial:** Usa distribuição de tamanho (não monodisperse):
```
Size Distribution:  Log-Normal ou Rosin-Rammler
D_mean:             ~4 mm (grão de trigo)
Spread parameter:   ~1.3
```
**Braskem:**
```
Distribution:     Rosin-Rammler (padrão industrial para pós)
D50:              *** aguardar Jeferson ***
n (spread):       ~1.5–2.5 (pó PEAD tem distribuição estreita)
D_min / D_max:    0.5× D50 a 2× D50
```

### T2-S6 — Defining the DEM Particle Interaction (Conveyor)
**Diferença vs. Settling:** o conveyor adiciona **interação partícula-parede específica para o material da esteira**
```
Contato particle-particle:   E_grain, ν_grain, e_pp, μ_s_pp
Contato particle-wall:       E_belt, ν_belt, e_pw, μ_s_pw   ← depende do material da esteira
```
**Braskem — dois contatos distintos:**
```
PEAD–PEAD:    E=10 MPa (soft), ν=0.46, e=0.6, μ_s=0.35, μ_r=0.02
PEAD–Aço:     E_eff = harmônica(E_PEAD, E_steel), ν_eff, e=0.5, μ_s=0.25, μ_r=0.01
Aço 304:      E=200 GPa → soft → 100 MPa, ν=0.27
```

### T2-S7 — Setting the Moving Conveyor Wall Condition ★ SEÇÃO MAIS CRÍTICA
**Tutorial (esteira inclinada):**
```
Boundary type:   Wall
Condition:       Moving Wall (Translating)
Velocity:        v_belt [m/s] na direção do transporte (ex: +X)
Frame:           Lab Frame
```
**Braskem — adaptação para rosca helicoidal:**
```
Boundary type:   Wall
Condition:       Moving Wall (ROTATING — não Translating)
Axis of rotation: vetor ao longo do eixo da rosca (ex: +X se rosca é horizontal em X)
Origin:           centroide do eixo (0, 0, 0) ou coordenada real
Angular velocity: ω [rad/s] = (rpm × 2π) / 60
                  Ex: 30 rpm → ω = 3.14 rad/s

Aplicar em:
  ✓ Screw Blade surface → ω = +ω_screw (horário ou anti-horário)
  ✓ Shaft surface       → ω = +ω_screw (mesmo valor)
  ✗ Trough (calha)      → Wall estacionária (sem velocidade)
```
**Por que funciona sem Mesh Motion:**
O DEM detecta contato partícula-parede e calcula a força tangencial usando a **velocidade relativa** entre a partícula e a superfície da parede. A parede "desliza" sob a partícula mesmo sem a malha se mover — mais eficiente computacionalmente que Morphing/Overset Mesh.

### T2-S8 — Creating an Injector (Conveyor)
**Tutorial:** Injector no topo da chute de alimentação
```
Type:         Surface Injector (na face de entrada)
Rate:         N particles/s (calculado de kg/s ÷ m_partícula)
Velocity:     v_initial ≈ 0 (caem por gravidade na chute)
Duration:     Continuous
Position:     Distribuição aleatória na face de injeção
```
**Braskem:**
```
Face de injeção:   Face transversal da calha na extremidade de alimentação
Rate:              Q_feed [kg/h] ÷ (ρ_PEAD × V_partícula) = N/s
                   Exemplo: 1000 kg/h, D_p=3mm → V_p=14.1mm³ → N ≈ 22.000 p/s
                   → reduzir para 1.000–5.000 p/s para simulação exploratory
Velocity:          0 m/s (PEAD cai na entrada por gravidade)
```

### T2-S9 — Solver Parameters and Stopping Criteria (Conveyor)
**Tutorial — diferença vs. Settling:**
- Com geometria em movimento, verificar que Δt_DEM é compatível com a velocidade da parede
- Partícula não deve "atravessar" a pá entre dois timesteps

**Critério adicional para geometria em movimento:**
```
Δx_wall = v_wall × Δt_DEM   deve ser << D_partícula
Ex: ω=30 rpm, R=0.1m → v_tip = 0.314 m/s
    Δt_DEM = 1.7×10⁻⁵ s → Δx_wall = 5.3×10⁻⁶ m = 0.005 mm  << D_p=3mm ✓
```
**Stopping criteria para Braskem:**
```
Primary:    Max Physical Time = 30 s (suficiente para observar 1–3 rotações completas)
Secondary:  Monitor: Mass Flow Rate (outlet) → se cair a 0 por 5s → clogging confirmado
Backup:     Max Particles = 100.000 (evitar memória excessiva)
```

### T2-S10 — Solution History + Visualization (Conveyor)
**Tutorial:** Scalar Scene colorida por Particle Velocity — vê-se as partículas acelerando ao subir a esteira

**Braskem — cenas prioritárias:**
```
Cena 1 — Transport:        Partículas coloridas por velocidade axial (direção da rosca)
                           Azul=estagnado, Vermelho=transportado → onde para o fluxo?
Cena 2 — Compaction:       Partículas coloridas por Coordination Number
                           > 6 contatos simultâneos = compactado = zona de clogging 🚨
Cena 3 — Contact Force:    Força de contato total [N] por partícula
                           Picos de força = onde a rosca perde eficiência
Cena 4 — Animação:         Solution History a cada 0.05 s → .mp4 mostrando evolução
```

---

## TUTORIAL 2 — RESUMO EXECUTIVO: ADAPTAÇÃO PARA BRASKEM

| Aspecto | Tutorial (Esteira) | Braskem (Rosca) |
|---|---|---|
| Geometria | Esteira plana inclinada | Hélice + calha cilíndrica |
| Movimento | Translation v [m/s] | Rotation ω [rad/s] |
| Direção de transporte | Inclinação da esteira | Passo da hélice × rpm |
| Partículas | Grãos de trigo, D~4mm | PEAD, D~3mm (confirmar) |
| Contato partícula-parede | Borracha/aço da esteira | Aço 304 (trough + blade) |
| Clogging | Não modelado | Objetivo principal |

---

## TUTORIAL 3 — LIQUID ABSORPTION AND TRANSFER: SPRAY COATING (10 seções)

### T3-S1 a T3-S5 — (mapeados na sessão anterior)
Overview, Loading File, Physics Models, Coating Liquid Phase, Tablet Phase

### T3-S6 — Defining the DEM Phase Interactions ★★ CORAÇÃO DO MODELO
**Tutorial:** Define as interações entre TODOS os pares de fases:

```
Par 1: Tablet ↔ Tablet      → Hertz-Mindlin + LIQUID BRIDGE FORCE ★
Par 2: Tablet ↔ Droplet     → Absorption Model (líquido transfere da gota → filme)
Par 3: Tablet ↔ Wall        → Hertz-Mindlin apenas (sem ponte líquida na parede)
```

**Liquid Bridge Force — parâmetros do modelo:**
```
σ   (surface tension liquid-air):    [N/m]
θ   (contact angle liquid-solid):    [°]  ← parâmetro mais sensível
S_c (rupture distance):              gap máximo para existir ponte = f(V_liquid, θ)

Equação de força (modelo de Lian):
  F_bridge = π·σ·R_eff·(cos θ₁ + cos θ₂)·f(V_liq, gap)

Para hexano-PEAD:
  σ_hexano = 0.018 N/m
  θ_hexano-PEAD ≈ 5–10°  → cos θ ≈ 0.99 → FORÇA MÁXIMA 🚨
  S_c ≈ (V_liq)^(1/3) × (1 + θ/2)   (correlação de Lian et al.)
```

**Braskem — configuração dos 3 pares:**
```
PEAD ↔ PEAD (partícula-partícula):
  Contato base:    Hertz-Mindlin  (E=10 MPa soft, ν=0.46, e=0.6, μ_s=0.35)
  Coesão:          Liquid Bridge Force
    σ = 0.018 N/m  (hexano)
    θ = 8°         (hexano molha PEAD quase perfeitamente)
    V_liq:         calculado do teor de hexano inicial

PEAD ↔ Aço (partícula-parede, trough + blade):
  Contato base:    Hertz-Mindlin  (E_eff, ν_eff, e=0.5, μ_s=0.25)
  Coesão:          NENHUMA (hexano não forma ponte líquida com aço inox) ← simplificação válida

PEAD ↔ Hexano-Droplet:
  NÃO APLICÁVEL — hexano já está nas partículas, sem spray
```

### T3-S7 — Injecting the Coating Liquid Droplets
**Tutorial:** Spray nozzle injector com gotículas de ~200 μm, v_spray = 2–5 m/s  
**Braskem:** NÃO precisa de injetor de líquido — hexano já está nas partículas

### T3-S8 — Injecting the Tablets ★ COMO DEFINIR O TEOR DE HEXANO INICIAL
**Tutorial:** Surface injector com parâmetro-chave:
```
Particle Phase:           Tablet
Initial Liquid Content:   f_liq [kg_liquid / kg_particle] ou volume fraction
Injection Rate:           N/s ou kg/s
```

**Braskem — como inicializar o hexano nas partículas:**
```
Na configuração do injector de PEAD:
  Initial Liquid Film Thickness:  δ₀  ou  Initial Liquid Mass Fraction: f_hex

Cálculo de δ₀ a partir do teor de hexano:
  f_hex = 0.01 (1% em massa)
  m_partícula = ρ_PEAD × (π/6) × D_p³  = 950 × (π/6) × (0.003)³ = 1.34×10⁻⁵ kg
  m_hexano    = f_hex × m_partícula      = 1.34×10⁻⁷ kg
  A_partícula = π × D_p²                 = 2.83×10⁻⁵ m²
  δ₀ = m_hexano / (ρ_hex × A_part)     = 1.34×10⁻⁷ / (659 × 2.83×10⁻⁵) ≈ 7.2 μm

Repetir para f_hex = 0.5%, 1%, 2%, 5% → estudo paramétrico do teor de hexano
```

### T3-S9 — Visualizing the Spray Coating → Cenas para Braskem
**Tutorial:** partículas coloridas por Liquid Film Thickness + coating uniformity

**Braskem — cenas prioritárias:**
```
Cena A — Liquid Film:        Cor = Liquid Film Thickness [μm]
  → Mostra onde hexano redistribui durante transporte
  → Partículas com filme espesso = mais propensas a formar pontes

Cena B — Bridge Force:       Cor = Liquid Bridge Force [N]
  → MAPA DE RISCO: onde as forças de coesão são máximas?
  → Zona de máxima força = ponto de iniciação do embuchamento

Cena C — Velocity Axial:     Cor = velocidade na direção do transporte [m/s]
  → Azul = estagnado = clogging começando
  → Vermelho = transportado normalmente

Cena D — Coordination Nº:   Cor = nº de contatos simultâneos por partícula
  → > 6 contatos = compactado = embuchamento confirmado 🚨

Animação: gravar todas as cenas como Solution History a cada 0.05 s
```

### T3-S10 — Running the Spray Coating Simulation
**Solver com LMP + DEM acoplados:**
```
A cada timestep:
  1. DEM: calcular forças de contato (Hertz-Mindlin + Liquid Bridge)
  2. LMP: transportar gotículas (NÃO necessário para Braskem)
  3. Liquid Film: redistribuir filme quando partículas entram em contato

Δt: ainda governado pelo Rayleigh time (DEM limita)
    Com soft sphere E=10 MPa, D_p=3mm → Δt ≈ 1.7×10⁻⁵ s ✓

Tempo de simulação:
  30 s físicos × (1/1.7×10⁻⁵) = 1.76×10⁶ timesteps
  Com 5.000 partículas: estimativa ~12h CPU em 16 cores
```

---

## TUTORIAL 3 — RESUMO EXECUTIVO

**O que o Liquid Bridge Force resolve que JKR não resolve:**

| Aspecto | JKR (Tutorial 1/2) | Liquid Bridge Force (Tutorial 3) |
|---|---|---|
| Parâmetro de entrada | γ [J/m²] — empírico | σ [N/m] + θ [°] — medíveis |
| Variação com teor de líquido | Não — γ fixo | Sim — força ∝ V_líquido |
| Redistribuição durante contato | Não | Sim — líquido transfere entre partículas |
| Ruptura da ponte | Não modelada | Sim — S_c calculado fisicamente |
| Adequação para Braskem | Exploratório | PRODUÇÃO ✓ |

---

## PROCEDIMENTO COMPLETO STAR-CCM+ PARA BRASKEM
### (Combinação dos 3 tutoriais em sequência operacional)

```
FASE 0 — Pré-processamento (Python/CadQuery)
  [ ] Gerar screw_blade.step  (hélice paramétrica)
  [ ] Gerar trough.step       (calha cilíndrica)
  [ ] Validar volume e geometria

FASE 1 — Star-CCM+: Importar e Malhar
  [ ] File → Import → Surface Mesh → selecionar ambos os STEPs
  [ ] Visualize + Surface Repair (verificar gaps, free edges)
  [ ] Assign regions: "Trough Volume" / "Screw Blade" (boundary only) / "Shaft" (boundary only)
  [ ] Mesh → Polyhedral + Surface Remesher
  [ ] Base Size = 15 mm (= 5× D_p se D50=3mm)
  [ ] Generate Volume Mesh

FASE 2 — Modelos Físicos
  [ ] Physics → Select Models:
      ✓ Three Dimensional
      ✓ Implicit Unsteady
      ✓ Lagrangian Multiphase
      ✓ Discrete Element Method (DEM)
      ✓ Liquid Film on Particles (LFP)
      ✓ Gravity (-9.81 m/s² em -Z)
      ✓ Rotation Motion

FASE 3 — Fase Lagrangiana (PEAD)
  [ ] Lagrangian → Add Phase → "PEAD_Phase"
  [ ] Material: PEAD (ρ=950, E=10 MPa soft, ν=0.46)
  [ ] Size Distribution: Rosin-Rammler (D50 de Jeferson)
  [ ] Initial Liquid Content: δ₀ calculado do teor de hexano

FASE 4 — Interações DEM
  [ ] DEM Interactions → Add:
      PEAD-PEAD: Hertz-Mindlin + Liquid Bridge Force
        σ = 0.018 N/m, θ = 8°
      PEAD-Wall: Hertz-Mindlin apenas
        E_wall=100 MPa (soft steel), ν=0.27, μ_s=0.25

FASE 5 — Condição de Contorno da Rosca
  [ ] Screw Blade boundary → Wall → Moving Wall → Rotation
  [ ] Axis: vetor do eixo da rosca
  [ ] ω = rpm_Braskem × 2π / 60   [rad/s]
  [ ] Shaft → mesma condição

FASE 6 — Injetor de Partículas
  [ ] Injectors → Add → Surface Injector
  [ ] Face: face de entrada da calha
  [ ] Rate: taxa de alimentação kg/h de Jeferson
  [ ] Initial Liquid Content: δ₀ do hexano

FASE 7 — Solver
  [ ] Δt_DEM = 1.7×10⁻⁵ s (soft sphere, D_p=3mm)
  [ ] Max Physical Time = 30 s
  [ ] Stopping: Mass Flow Rate outlet < 0.01× inlet por 5 s → clogging

FASE 8 — Cenas de Visualização
  [ ] Scalar Scene 1: Liquid Film Thickness
  [ ] Scalar Scene 2: Liquid Bridge Force
  [ ] Scalar Scene 3: Axial Velocity
  [ ] Scalar Scene 4: Coordination Number
  [ ] Solution History: todas as cenas, cada 0.05 s

FASE 9 — Rodar e Analisar
  [ ] Run → observar se ocorre clogging
  [ ] Variar teor hexano (0.5% / 1% / 2% / 5%)
  [ ] Variar rpm
  [ ] Gerar mapa de operabilidade
```

---

## AVALIAÇÃO: PRECISAMOS DE MAIS TUTORIAIS?

| Tutorial disponível | Necessário? | Motivo |
|---|---|---|
| **DEM Particle Settling** ✅ | SIM — feito | Base do DEM |
| **DEM Particles in a Conveyor** ✅ | SIM — feito | Moving Wall rotation |
| **Liquid Absorption** ✅ | SIM — feito | Liquid Bridge Force hexano |
| Arbitrarily Shaped Particles | Talvez — Fase 2 | Só se pellets forem cilíndricos |
| Coarse Grain Particles | Talvez — Fase 2 | Só se N_part > 100k e CPU insuficiente |
| Meshfree DEM: Excavator | NÃO | Solo/escavação, irrelevante |
| Flexible Fiber Model: Lawnmower | NÃO | Fibras, irrelevante |

**CONCLUSÃO: os 3 tutoriais são suficientes para a Fase 1 do projeto Braskem.**

---

## 2. PARÂMETROS CRÍTICOS — CONFIRMAR COM JEFERSON (QUINTA)

### Geometria da rosca
| Parâmetro | Estimativa inicial | Confirmar |
|---|---|---|
| Diâmetro externo (D_screw) | ~200 mm | ✓ |
| Diâmetro do eixo (D_shaft) | ~60 mm | ✓ |
| Passo (pitch) | ≈ D_screw | ✓ |
| Comprimento total (L) | ~3 m | ✓ |
| Folga pá-calha (clearance) | ~5 mm | ✓ |
| Ângulo de inclinação | ~0° (horizontal) | ✓ |

### Partículas PEAD
| Parâmetro | Estimativa | Confirmar |
|---|---|---|
| D50 (pellets) | 3–5 mm | ✓ |
| D50 (pó fino) | < 1 mm | ✓ — qual a faixa problemática? |
| Teor de hexano | desconhecido | ✓ — % em massa ou saturado? |
| Temperatura das partículas | ambiente | ✓ — ou ainda quente do processo? |

### Operação
| Parâmetro | Estimativa | Confirmar |
|---|---|---|
| Rotação da rosca (rpm) | desconhecida | ✓ |
| Taxa de alimentação | desconhecida | ✓ — kg/h |
| Clogging: onde na rosca? | desconhecido | ✓ — entrada, meio, saída? |
| Clogging: partida ou operação? | desconhecido | ✓ |
| Condição interna (P, T, N₂?) | desconhecida | ✓ |

---

## 3. GEOMETRIA — PYTHON/CADQUERY (PRONTO PARA GERAR)

Após confirmar D_screw, D_shaft, pitch e L com Jeferson, gerar:

```python
# Parâmetros a confirmar:
D_SCREW = 200.0   # mm — diâmetro externo da pá
D_SHAFT = 60.0    # mm — diâmetro do eixo
PITCH   = 200.0   # mm — passo da hélice
N_TURNS = 10      # número de voltas (L = N_TURNS × PITCH)
D_TROUGH = 205.0  # mm — calha interna (D_SCREW + 2 × clearance)

# Gera: eixo cilíndrico + pá helicoidal (sweep de disco ao longo de hélice)
# Exporta: screw_blade.step + trough.step
```

---

## 4. CRONOGRAMA DO PROJETO

| Fase | Ação | Quando |
|---|---|---|
| **Prep reunião** | Tutorial 1: DEM Particle Settling (completo) | Antes de quinta |
| **Reunião quinta** | Coletar parâmetros de Jeferson | Quinta 9h |
| **Pós-reunião** | Gerar geometria em CadQuery com dados reais | Quinta tarde |
| **Semana 1** | Tutorial 2: DEM Particles in a Conveyor | Próxima semana |
| **Semana 1** | Importar geometria Braskem no Star-CCM+ | Próxima semana |
| **Semana 2** | Tutorial 3: Liquid Absorption (Liquid Bridge Force) | Semana 2 |
| **Semana 2** | Adicionar Liquid Bridge Force no caso Braskem | Semana 2 |
| **Semana 3** | Estudo paramétrico γ (hexano) + rpm | Semana 3 |
| **Entrega** | Relatório + animação do embuchamento | A combinar com Jeferson |

---

## 5. MENSAGEM-CHAVE PARA JEFERSON (QUINTA)

> "A simulação DEM vai capturar exatamente o mecanismo do embuchamento: quando o hexano nas partículas de PEAD aumenta a coesão acima de um valor crítico, a rosca não consegue mais vencer a força de compactação. Isso nos dará um **mapa de operabilidade** — mostrando para quais combinações de rpm, taxa de alimentação e teor de hexano o conveyor opera de forma segura, e onde o embuchamento ocorre. A vantagem sobre testes físicos com hexano é óbvia: segurança + custo + parametrização rápida."

---

*Última atualização: 2026-06-16 (Tutorial 3 completo — 3 tutoriais absorvidos) | Gestor: Claude (IA) | Engenheiro responsável: Gabriel Hernandez Rozo*
