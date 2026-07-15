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

## 4. Guia de setup ADAPTADO e VERIFICADO (documento vivo)
> Preenchido a partir do workflow de adaptação+verificação (RSM vs K-ω, acoplamento, térmica, malha).
> *(Em processamento — será consolidado aqui.)*

## Fonte
Tutorial oficial STAR-CCM+ 21.02: *Anisotropic Flow: Cyclone Separator* (Selecting Physics Models,
Creating the Fluid Region, Setting Boundary Conditions, Generating the Volume Mesh). Companheiro:
*3D-CAD: Cyclone Separator* (geometria — nós geramos a nossa via `gen_ciclone_lapple.py`).
