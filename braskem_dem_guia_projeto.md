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
| **Semana 2** | Tutorial 3: Liquid Absorption (JKR cohesion) | Semana 2 |
| **Semana 2** | Adicionar JKR no caso Braskem — caso seco vs úmido | Semana 2 |
| **Semana 3** | Estudo paramétrico γ (hexano) + rpm | Semana 3 |
| **Entrega** | Relatório + animação do embuchamento | A combinar com Jeferson |

---

## 5. MENSAGEM-CHAVE PARA JEFERSON (QUINTA)

> "A simulação DEM vai capturar exatamente o mecanismo do embuchamento: quando o hexano nas partículas de PEAD aumenta a coesão acima de um valor crítico, a rosca não consegue mais vencer a força de compactação. Isso nos dará um **mapa de operabilidade** — mostrando para quais combinações de rpm, taxa de alimentação e teor de hexano o conveyor opera de forma segura, e onde o embuchamento ocorre. A vantagem sobre testes físicos com hexano é óbvia: segurança + custo + parametrização rápida."

---

*Última atualização: 2026-06-16 | Gestor: Claude (IA) | Engenheiro responsável: Gabriel Hernandez Rozo*
