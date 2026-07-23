# 07 — Setup da FÍSICA no STAR (nó de aeração, VOF)

> Escolha: **VOF (interface resolvida)** — mostra o jato e a **quebra primária** de forma HONESTA no meio
> laminar viscoso. **Não** usar EMP+S-Gamma com kernel de quebra turbulento (Re≈37 = laminar → kernel inválido).
> O tamanho fino (<300 µm) sai depois da **âncora VOF+AMR** + preditor analítico, não da malha global.

## 1. Modelos do Continuum (habilitar nesta ordem)
- Space → **Three Dimensional**
- Time → **Implicit Unsteady** (VOF é transiente)
- Material → **Multiphase**  →  **Volume of Fluid (VOF)**  (+ Eulerian Multiphase automático)
- Flow → **Segregated Flow**  ·  Segregated VOF
- Viscous → **Laminar**  ⚠️ (nada de turbulência — Re≈37)
- Optional → **Gravity** · **Surface Tension** · **Multiphase Interaction**
- (sem Energy — isotérmico por ora)

## 2. Fases (Eulerian Phases)
**Xarope (líquido):**
- Equation of State → **Constant Density**, ρ = **1300 kg/m³**
- Dynamic Viscosity → Constant, μ = **6,5 Pa·s** (Newtoniano)

**Ar (gás):**
- Equation of State → **Ideal Gas** (compressível — captura o subsônico→sônico)
- Dynamic Viscosity → 1,85e-5 Pa·s

## 3. Interação de fase (Xarope–Ar)
- VOF Phase Interaction
- **Surface Tension = 0,058 N/m** (literatura, doc `02`)
- Convecção da interface: **HRIC** (nítida)

## 4. Condições de contorno
| Boundary | Tipo | Valores |
|---|---|---|
| **Xarope_in** | Velocity Inlet | **1,10 m/s** normal (=32,5 m³/h/lança); VF: xarope=1, ar=0 |
| **Ar_in** | **Stagnation Inlet** | p_total = **98066 / 196130 / 294200 Pa** (1/2/3 kgf/cm²); VF: ar=1; T=300 K |
| **Outlet** | Pressure Outlet | pressão de jusante (0 rel. ou submersão); backflow VF xarope=1 |
| **Walls** | Wall | no-slip |

> ⚠️ **Referência de pressão:** confira gauge × absoluta. Se a referência do STAR for absoluta, some ~101325 Pa
> aos valores do ar. O sweep = **3 casos** (1/2/3 kgf), iguais aos da Fase 1 → comparável.

## 5. Gravidade (⚠️ parâmetro a confirmar)
- |g| = 9,81 m/s². **Direção** depende do sentido real de instalação (o desenho **não** marca entrada/saída).
  Importa para o **empuxo** das bolhas. 1º passo: alinhar g ao eixo do escoamento; confirmar com o Ito.

## 6. Solver / tempo / init
- **Time step:** Co<1 na zona do furo (~0,8 mm, ~20 m/s) → **Δt ≈ 2e-5 s** (ou Adaptive Time-Step, Co alvo ~0,5–1).
- Inner iterations: **5–10** por passo. Under-relax padrão (v 0,7 / p 0,3).
- **Init:** domínio cheio de **xarope** (VF_xarope=1), U=0, p hidrostática/0.
- **Robustez:** os primeiros tempos do transiente **são** o campo monofásico (pressão/deformação de graça,
  antes do ar chegar) → dali saem os achados do "Passo 1" (a garganta cai abaixo do suprimento do ar?).
  Se ficar instável no arranque, rodar um **steady monofásico** (só xarope) antes e usar como seed.

## 7. O que observar (ligado às sondas do doc 06)
- **Balanço de massa** (Xarope_in + Ar_in = Outlet) → critério de parada.
- **p_garganta** vs suprimento do ar (arraste viável?).
- **linha_eixo:** aceleração no furo, |U|~20 m/s, e a queda de pressão.
- **iso `VF_ar=0,5`:** o jato de ar **quebra** (ligamentos/estruturas finas) ou **canaliza** (bolha coerente)?
  — é a resposta do mecanismo (extensão/atomização × borbulhamento).
- **holdup** (Volume Average VF_ar na descarga).

## 8. Custo (honesto)
VOF transiente + μ alta + σ + Δt~2e-5 s é **caro**. Rodar primeiro **1 caso (ex.: 2 kgf)** até o jato
estabelecer/quebrar; depois os outros 2. Não precisa de segundos de tempo físico — dezenas de ms já
mostram o mecanismo de nascimento.
