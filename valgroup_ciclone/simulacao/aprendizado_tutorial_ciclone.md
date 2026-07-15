# Aprendizado — Tutorial STAR "Anisotropic Flow: Cyclone Separator"

> Registro do tutorial oficial (STAR-CCM+ 21.02) + **o que muda para o nosso caso Valgroup**.
> O guia de setup FINAL (adaptado e verificado por análise multi-agente) fica na §4 (documento vivo).

## 1. O que o tutorial ensina (fiel)

### 1.1 Física (Continua > Physics 1)
`Three-Dimensional` · `Gas` · `Segregated Flow` · `Constant Density` · `Steady` · `Turbulent` →
`RANS` → `K-Omega Turbulence` → `SST (Menter) K-Omega` · `Wall Distance` · `All y+ Wall Treatment`.

> ⚠️ **Nota do próprio tutorial:** usa K-ω SST *"para limitar o tempo de simulação"*. O título diz
> "Anisotropic Flow" mas entrega K-ω (2 equações) como **atalho**. O swirl de ciclone é **anisotrópico
> de verdade** → o padrão-ouro é **RSM (Reynolds Stress Model)**. **Para nós, isso é decisão-chave** (§4).

### 1.2 Estratégia de convergência (importante!)
> "First run in **steady state WITHOUT curvature correction**, then run as **UNSTEADY for 0.5 s WITH
> curvature correction activated**."

O swirl não converge bem direto em transiente do zero. Recipe: **steady (estabiliza) → unsteady +
curvature correction (captura a precessão do núcleo do vórtice, PVC)**.

### 1.3 Região fluida (3D-CAD → Parts → Regions)
1. `3D-CAD Models > Cyclone` → botão direito → **New Geometry Part**.
2. Parts → multi-seleciona **Main Body** + **Outlet Pipe** → **Assign Parts to Regions**:
   - ✅ *Create a Region for Each Part*
   - ✅ *Create a Boundary for Each Part Surface*
3. **Duas regiões** (Main Body, Outlet Pipe). Tipos de fronteira:
   - `Inlet` → **Velocity Inlet** (fica vermelho)
   - `Outlet` → **Outlet** (fica verde)
   - Interface `Main Body/Outlet Pipe` → **Baffle Interface** (o vortex finder vira baffle).
4. Prism layers **só em paredes** (não nas fronteiras de escoamento).

### 1.4 Condições de contorno
- **Velocity Inlet:** perfil uniforme. Turbulência = **Intensity + Length Scale**.
  Tutorial: Intensidade **0,0045**, comprimento **0,000525 m**, Velocidade **10 m/s**.

### 1.5 Malha
Meshers: **Surface Remesher + Polyhedral + Advancing Layer** (poliédrica trata bem recirculação).
Default Controls: Base **12,5 mm** · Target 80% · Min 30% · **72 pts/círculo** · Growth 1,3 ·
**5 prism layers** · stretch 1,2 · prism total **0,012 m** · volume growth 1,1.
Refinos volumétricos (capturam o vórtice e o jato):
- **Cilindro no eixo** (raio 0,03 m, z −0,3→0,9) → 50% da base. *(resolve o núcleo do vórtice)*
- **Bloco na entrada** → 50% da base + prism total 0,008 m. *(resolve o jato de entrada)*

## 2. Traduzindo as escalas do tutorial → nosso ciclone
O ciclone do tutorial é ~da nossa escala (base 12,5 mm ≈ D_c/13). Para o **nosso D_c=163,3 mm**:
- Base ≈ **12–13 mm** (D_c/13) como ponto de partida; refina no núcleo e na entrada.
- Refino do **cilindro-eixo** com raio ≈ **0,3·D_c ≈ 25 mm**, cobrindo todo o comprimento do vórtice.
- **72 pts/círculo** e prism layers na parede — mantém.
- **y+**: com All y+ wall treatment, tolera y+ largo; mas para eficiência de coleta o near-wall importa
  (é onde a partícula sedimenta) → mirar prism adequado.

## 3. O que o tutorial NÃO tem (e nós PRECISAMOS)
O tutorial é "o passo inicial" — **single-phase, isotérmico, sem partículas**. Nosso estudo adiciona:

| Item | Tutorial | Nosso caso Valgroup |
|---|---|---|
| **Turbulência** | K-ω SST (por velocidade) | **RSM** (anisotrópico) — a decidir/verificar (§4) |
| **Fase discreta** | ❌ nenhuma | **Lagrangiana (char)** → grade efficiency por tamanho |
| **Acoplamento** | — | one-way vs **two-way** (~11% carga) — verificar |
| **Energia/Térmica** | ❌ isotérmico | **modelo de energia** → T_parede vs **orvalho** (pedido do cliente) |
| **Densidade do gás** | Constant Density | gás real/ideal p/ o gradiente térmico? |
| **Erosão** | ❌ | char abrasivo (Ti/Si) → avaliar erosão de parede |
| **Saída de sólidos** | — | base do cone: **trap** de partícula |
| **Validação** | — | vs **Lapple** (d*≈3,6µm, η, ΔP) + independência de malha |

## 4. Guia de setup ADAPTADO e VERIFICADO
> Consolidado de análise multi-agente (4 dimensões: turbulência, fase discreta, térmica, malha) +
> literatura de CFD de ciclone. **O tutorial é o ponto de partida; abaixo está o setup do NOSSO caso.**

### 4.1 Física (Continua) — o que muda vs o tutorial
`3D` · `Gas` → **Ideal Gas** (M=184 kg/kmol → reproduz ρ=3,946) *(tutorial: Constant Density)* ·
`Segregated Flow` · **`Segregated Fluid Temperature` (ENERGIA LIGADA)** *(tutorial: isotérmico)* ·
**`Implicit Unsteady` (URANS)** · Turbulent → RANS → **`Reynolds Stress Turbulence → Elliptic Blending
(EB-RSM)`** *(tutorial: K-ω SST)* · **Curvature Correction DESLIGADA** *(o RSM já responde à rotação;
o tutorial a liga PORQUE usa SST)*.

### 4.2 Turbulência — **RSM, não K-ω SST** (a decisão nº 1)
- **Por quê:** a eficiência é governada pelo **pico de velocidade tangencial** (v_t²/r). Modelos de
  viscosidade turbulenta (k-ε, k-ω SST — Boussinesq/isotrópicos) **achatam o vórtice de Rankine**,
  subestimam v_t → **erram ΔP E a curva de eficiência**. O RSM transporta as 6 tensões de Reynolds →
  captura a anisotropia. Padrão-ouro RANS p/ ciclone (Hoekstra, Slack, Elsayed & Lacor).
- **Modelo:** EB-RSM (integra até a parede — bom p/ o fluxo de calor do orvalho e a deposição).
  Alternativa robusta: SSG/Linear Pressure-Strain Two-Layer (se EB não convergir).
- **Receita de convergência:** init 2-eq (k-ε/k-ω, 1ª ordem, ~1000 it) → RSM steady 2ª ordem (só semeia;
  vai estacionar num **ciclo-limite** por causa do PVC — não é divergência) → **URANS-RSM**.
- **Numérica:** 2ª ordem upwind no momento (**NUNCA 1ª ordem** — borra o vórtice, é o erro nº1 de CFD de
  ciclone). BDF2 no tempo. **dt = 5e-5–1e-4 s** (CFL~1 no núcleo). **Média temporal ~15–20 tempos de
  residência** (~2–3 s; residência ~0,16 s), descartando ~0,2–0,3 s iniciais. *(O 0,5 s do tutorial é curto.)*
- **Convergência por MONITORES físicos:** ΔP, v_t em sondas radiais, desbalanço de massa <0,5%, η — não só resíduo.

### 4.3 Fase discreta (Lagrangiana) — **o que entrega a grade efficiency** (o tutorial não tem)
- **Modelo:** Lagrangian Multiphase, Material Particles, ρ_s=1500, esf. 0,8 (Haider-Levenspiel).
- **Forças:** Drag (Schiller-Naumann) + Gravity + **Turbulent Dispersion (DRW) — OBRIGATÓRIA** (sem ela os
  finos seguem a linha média → η **falsamente alta**) + Saffman-Mei (opcional, finos <10µm). Ignorar
  massa virtual/grad. pressão (ρ_s/ρ_g=380).
- **Acoplamento:** α_v bulk = 2,9e-4 (diluído, zona two-way de Elghobashi). **One-way primeiro** (curva de
  eficiência, campo do gás não muda) → **Two-way na produção** (11% carga amortece o swirl, reduz ΔP 5–15%).
- **Injeção — 2 campanhas:**
  - **(A) Grade efficiency:** injeções **MONODISPERSAS** (1/2/3/**3,6**/5/7/10/15/20/30/50/75 µm +150/425)
    → η_i = m_saída_pó/m_injetado por rodada (toda a física está em <20µm, pois d*≈3,6µm).
  - **(B) Produção (ΔP, erosão, η global):** Rosin-Rammler no inlet (d63≈120–150µm, n≈2, dmin 1µm,
    dmax ~500µm), 80 kg/h, >20.000 parcelas.
- **Partícula-parede:** corpo/cone = **REBOUND** (e_n≈0,85, e_t≈0,95) + rugosidade estocástica (Sommerfeld),
  **NÃO Trap** (trap lateral superestima η). **Saída de gás = ESCAPE (não-coletado)**; **ápice do cone =
  ESCAPE contado como COLETADO** (incluir **coto de hopper** p/ o vórtice não rearrastar).
- **Erosão:** OKA (ou DNV) nas paredes de aço → mm/ano nos hotspots (impacto do jato, cone, ápice). Só
  ranking relativo (char-mineral ≠ areia calibrada; incerteza fator 2–3).
- **Extração:** Lagrangian Mass Flow reports por fronteira; validar vs Lapple (d*~3,6µm; o CFD dá cut-size
  um pouco **maior** que Lapple por causa da dispersão turbulenta).

### 4.4 Térmica / condensação — **o pedido do Lucas** (o tutorial não tem)
- **Energia:** Segregated Fluid Temperature + Gradients. **Densidade: Ideal Gas M=184** (reproduz 3,946;
  **NÃO** Peng-Robinson no solver — VLE fica offline). Props: cp≈2500, k≈0,06, µ=2,5e-5 (Pr≈1), Pr_t=0,9.
- **BC de parede = CONVECTION com camadas (o item central):** aço 4mm (k=16) + **isolante paramétrico
  0/25/50/75mm** (k=0,06) + h_ext + T_amb=30°C. O solver **calcula T_parede** pelo balanço gás→aço→isolante→
  ambiente. **NÃO adiabática** (daria ~400°C, nunca prevê orvalho) e **NÃO temperatura fixa** (é o que queremos prever).
- **Inlet T=400°C**; ápice do cone = ponto mais frio. **Malha de parede y+≲1** (mais prisms que os 5 do tutorial).
- **Condensação = pós-processamento OFFLINE** (CFD monofásica não muda de fase): T_orvalho(p) via VLE
  (Aspen/DWSIM/CoolProp). Field function **`WallCondensationMargin = ${WallTemperature} − T_dew`**.
  **Entregáveis:** contorno de T_parede; contorno de (T_parede−T_dew) com limiar 0 (vermelho = condensa);
  min(T_parede) e fração de área abaixo do orvalho por fronteira; **curva de projeto: espessura de isolante
  × ΔT_min** → especifica o **isolamento mínimo** que mantém min(T_parede) ≥ T_dew **+15–20 K de margem**
  (não só ≥0 — o condensado com Cl 2,78% = HCl **corrói**).

### 4.5 Malha (redimensionada do tutorial p/ D_c=163mm)
- Meshers iguais (Surface Remesher + Polyhedral + Advancing Layer).
- **Base 3 mm** (tutorial 12,5); entrada/jato **2 mm** (~20 células em B_c=40,8); **cilindro de refino no
  núcleo do vórtice** (r≤D_e~40mm, **do vortex finder até a ponta do cone**, 1,0–1,5 mm — estendido vs o
  tutorial, pois os finos escapam pelo núcleo de fluxo reverso); lip do vortex finder + ponta do cone 1,0–1,5mm.
- **Prism: 12–15 camadas** (tutorial 5), 1ª célula ~7µm (**y+~1**), stretch 1,2, total 2–3mm, All y+.
- **Azimutal: 120–144 pts/círculo** (tutorial 72). 2ª ordem de convecção (poli não é alinhada ao swirl → difusão numérica de momento angular).
- **Contagem:** 2–4 M células (RSM/URANS); 10–20 M (LES, fallback de fidelidade dos finos).
- **Independência:** 3 malhas r≥1,3, GCI <5% em ΔP e d50; independência de **parcelas** (≥1e4–1e5 por bin).

### 4.6 Validação (âncoras)
- **ΔP** vs **36,5 mbar** (Lapple) · **d50 / curva η(d)** vs Lapple (d*≈3,6µm; η_i=1/(1+(d*/d)²)) ·
  **perfil de v_t** vs vórtice de Rankine/LDA (pico ~1,5–2·v_i perto de r~D_e/2).
- Cross-checks: **Iozia-Leith** (físico) e **Muschelknautz** (captura o efeito da carga de 11%).

### 4.7 Riscos-chave (síntese)
1. **1ª ordem / núcleo grosso → borra o vórtice** → superestima d50, subestima η. *(Disciplina: 2ª ordem + refino do núcleo.)*
2. **Finos <20µm** são MUITO sensíveis à dispersão turbulenta e ao near-wall; RANS-RSM pode errar o cut-size → **sensibilidade RSM×LES nos finos.**
3. **T_orvalho dos tars** (MW~184) é a maior incerteza térmica → precisa da **composição/VLE**; reportar por faixa (~250–350°C) + sensibilidade.
4. **Trap × Escape na parede** muda η drasticamente → usar Rebound + destino na fronteira, nunca Trap lateral.
5. **PSD do char CARREADO** (mais fino, mal caracterizado) → η **global** incerto (a curva η(d) é robusta; o integrado não). *(Marcus vai mandar.)*
6. **Finos revestidos de tar** (condensação incipiente) podem **grudar e AUMENTAR** a η real vs prevista — não modelado, documentar.

### 4.8 Execução (rodar) — confirmado pelos tutoriais "Running Steady/Unsteady"
Os tutoriais oficiais **confirmam a receita steady → unsteady + curvature correction**. Adaptado p/ nós:

| Fase | Tutorial (SST) | **Nosso caso (RSM)** |
|---|---|---|
| **1. Steady** | Max Steps **1500** (semeia o unsteady) | RSM steady 2ª ordem até o **ciclo-limite** (PVC); salvar snapshot "Steady" p/ comparação |
| **2. Unsteady** | desliga Steady → **Implicit Unsteady**; **Curvature Correction = ON** (no SST) | Implicit Unsteady; **Curvature Correction = OFF** (o RSM já responde à rotação!) |
| **Δt** | 5e-4 s | **5e-5–1e-4 s** (ciclone menor, v maior → CFL~1 no núcleo) |
| **Inner iterations** | 8 | **5–10** (queda de ~3 ordens de resíduo/passo) |
| **URF (segregado)** | vel 0,9 · press 0,4 | **vel 0,5–0,7 · press 0,2–0,3** (RSM + tensões 0,4–0,6, mais conservador) |
| **Tempo físico** | 0,5 s | **2–3 s** (~15–20 tempos de residência p/ estatística de ΔP/η; descartar ~0,2–0,3 s iniciais) |
| **Paralelo** | 4 cores | mais (2–4 M células + fase discreta) |

**Ordem geral:** malha → **init 2-eq steady** → **RSM steady** (ciclo-limite) → **URANS-RSM** (converge ΔP/v_t)
→ **ligar energia + parede Convection** (campo térmico p/ orvalho) → **injetar partículas** (one-way curva →
two-way produção) sobre o campo já desenvolvido → média temporal → extrair η(d), ΔP, T_parede, erosão.

> ⚠️ **Diferença crítica vs o tutorial:** ele liga *Curvature Correction* porque usa **SST**. **Nós NÃO
> ligamos** (usamos RSM, que capta a curvatura pelos termos exatos). Ligar as duas seria redundante/inconsistente.

### 4.9 ⚠️ DEM × Lagrangiana — não confundir (o ciclone é LAGRANGIANO)
O char no ciclone é **DILUÍDO** (fração volumétrica α_v ≈ 0,029%) → **Lagrangian Multiphase (LMP/DPM)**,
com colisão partícula-partícula **desprezível**. **NÃO é DEM.**
- **DEM** (Discrete Element Method) = fluxo **DENSO**, colisão/contato partícula-partícula domina (ângulo de
  repouso, empacotamento). É o caso do **Braskem PE5** (rosca/embuchamento) e do **Petrobras** (fluxo de coque).
- **Lagrangiana/DPM** = fluxo **diluído**, partícula segue o gás com arrasto+dispersão, sem contato. É o ciclone.
- O tutorial "DEM Particles in a Conveyor" é ótimo para **Braskem/Petrobras** (e p/ entender injetores), mas o
  **modelo físico** do ciclone é LMP. O conceito de **Injector/Part Injector** é semelhante; a física de contato não.

### 4.10 Veredito da VERIFICAÇÃO ADVERSARIAL (4 afirmações-alicerce)
Cada afirmação atacada por 2 céticos (física + CFD/literatura). Resultado:

| Afirmação | Veredito | Refinamento |
|---|---|---|
| **RSM necessário** (vs K-ω SST) | ✅ SUPPORTED / ⚠️ UNCERTAIN | "necessário" é **forte demais**. RSM é o **mínimo recomendado** p/ fidelidade; mas o tutorial usa **SST + Curvature Correction (SST-CC)** — opção legítima e barata (2 EDPs vs 6), às vezes competitiva na literatura. **→ ESTRATÉGIA DE BRACKETING:** rodar **EB-RSM (workhorse) E SST-CC (sanidade)**. Concordam em d50 → aceitar RANS. Divergem nos **finos <20µm** → **escalar p/ LES/DES** de verificação. |
| **Two-way a 11% de carga** | ✅ SUPPORTED (2 lentes) | α_v=2,9e-4 firmemente na zona two-way (Elghobashi). **Vigiar α_v LOCAL na corda/cone** — pode cruzar 1e-3 (four-way) → DDPM/CFD-DEM só nessas zonas. |
| **Bulk 450°C ≠ sem condensação** (parede mais fria) | ✅ SUPPORTED — "irrefutável" (2 lentes) | Mesmo mecanismo de **cold-end / orvalho ácido** (economizadores, tar dew-point fouling). Confirma energia + parede Convection + VLE offline. **← é a resposta técnica ao Humberto.** |
| **Transiente/URANS pro PVC** | ✅ SUPPORTED (2 lentes) | PVC é intrinsecamente transiente; steady não o captura. **dt deve resolver a frequência do PVC** (f~St·v_i/D_c, St~0,5 → ~20–40 passos/período). |

**Refinamentos da verificação a NÃO esquecer:**
- ⚠️ **RANS-RSM SUPERESTIMA a coleta de finos <10–20µm** (subestima as flutuações RMS) — é a **MAIOR incerteza**
  da grade efficiency, e é **exatamente onde está o char carreado**. → planejar **LES/DES de verificação nos finos**.
- **ΔP:** padronizar a definição (estática × total, incluir/excluir o outlet pipe) **antes** de comparar com os 36,5 mbar.
- **Bracketing** EB-RSM × SST-CC é a forma honesta de reportar a incerteza de modelo de turbulência ao cliente.
- **Plano de convergência em rampa** (nunca acoplar tudo): 2-eq steady → RSM steady (ciclo-limite) → URANS-RSM
  isotérmico → +energia/ideal-gas → +LMP one-way → +two-way. *(Detalhe no §4.8.)*

## 5. Estado / pendências
- ✅ Geometria (`gen_ciclone_lapple.py` → `ciclone_lapple_fluido.step`), dimensionamento Lapple, matriz revisada.
- ✅ Guia de setup adaptado **e VERIFICADO** (veredito no §4.10 — SUPPORTED_WITH_CAVEAT, bracketing RSM×SST-CC).
- ✅ **Composição do gás recebida** (GC-MS: HC C7–C15, alceno-dominante, MW~124–184) → base p/ µ/cp/k/orvalho.
  Ver [`../dados_cliente/dados_recebidos_15jul.md`](../dados_cliente/dados_recebidos_15jul.md).
- ⚠️ **Reconciliar com a planilha dos colegas:** vazão de gás **800 vs 1900 kg/h** (muda D_c 163→265mm!), µ
  (2,5e-5 vs 9,5e-5), ρ_s (eles usaram o **bulk** 776,8 — errado). T de operação ~343°C (TT-209), não 400. Ver o doc.
- ⏳ **Ainda pendente:** **PSD do char CARREADO** (Marcus) · **T_orvalho via VLE** (calcular com a composição GC) ·
  ρ_s real da partícula · material (Cl → liga anti-HCl).

> **Nota de processo:** workflow multi-agente **CONCLUÍDO** (16/16 agentes): 4 adaptações + verificação
> adversarial (§4.10) + síntese. As 4 afirmações-alicerce **sobreviveram** (3 SUPPORTED, 1 SUPPORTED-com-nuance
> = bracketing RSM×SST-CC). Síntese consolidada acima. Confiança: turbulência 0,85 · fase discreta 0,80 ·
> térmica 0,72 · malha (alta).

## Fonte
Tutorial oficial STAR-CCM+ 21.02: *Anisotropic Flow: Cyclone Separator* (Selecting Physics Models,
Creating the Fluid Region, Setting Boundary Conditions, Generating the Volume Mesh). Companheiro:
*3D-CAD: Cyclone Separator* (geometria — nós geramos a nossa via `gen_ciclone_lapple.py`).
