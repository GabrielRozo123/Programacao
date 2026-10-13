# Tutorial 07 — Eulerian Multiple Flow Regimes: Pressurized Water Reactor

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: ✅ tutorial completo lido (seções 1–10: visão geral, modelos, fases, condições iniciais e
> referência, interação MFR, contornos, solver, monitor, cena, animação — 13/10/2026).

---

## 0. Por que este tutorial

Os tutoriais anteriores obrigavam a escolher: **VOF** (interface resolvida, tutorial 03) **ou**
**Euleriano disperso** (bolhas menores que a célula, tutoriais 01–02). Muitos equipamentos têm **as
duas coisas ao mesmo tempo**: bolhas num lugar, superfície livre em outro, gotas acima dela.
O **Multiple Flow Regimes (MFR)** junta os dois num só modelo:

| regime | o que é | como o MFR trata |
|---|---|---|
| **primeiro** | gás disperso no líquido (**bolhas**) | Euleriano disperso — líquido contínuo |
| **intermediário** | fases separadas por **interface de grande escala** (superfície livre, estratificado) | interface nítida, como VOF |
| **segundo** | líquido disperso no gás (**gotas**, spray) | Euleriano disperso — gás contínuo |

Analogia do próprio tutorial: é como LES — **o que é maior que a malha é resolvido, o que é menor é
modelado**.

## 1. O caso

| item | valor |
|---|---|
| Aplicação | **perna quente** (*hot leg*) de reator PWR Konvoi, **escala 1/3**, **2D** |
| Fenômeno | escoamento **contracorrente** ar–água: a água desce do gerador de vapor para o vaso, o ar sobe em sentido contrário e pode **limitar a vazão de água** (CCFL) |
| Geometria | trecho horizontal de **2,12 m × 0,25 m**; curva (raios 0,25 e 0,5 m); trecho ascendente de 0,23 m a **50°** com expansão de 7,5°; câmara de entrada do gerador (quarto de círculo) |
| Entradas | água no fundo do simulador do gerador de vapor; ar no topo do vaso |
| Regime | **muito transiente**, com todos os regimes presentes |
| Fases | água e ar, **sem mudança de fase**, densidade constante |

## 2. Modelos físicos

| grupo | modelo |
|---|---|
| Espaço / Tempo | Two Dimensional · **Implicit Unsteady** |
| Material | Multiphase (+ Multiphase Interaction) |
| Modelo | **Eulerian Multiphase (EMP)** — o MFR é definido depois, **na interação entre fases** |
| Regime | Turbulent → **Phasic Turbulence** |
| Opcionais | Gravity |

**Ajustes no nó EMP:**

| propriedade | valor | por quê |
|---|---|---|
| **Volume Fraction Convection** | **2nd-order** | menos difusão numérica → interface **nítida** (vale também para o escoamento) |
| Minimum Volume Fraction | **1×10⁻¹²** | robustez |

## 3. Fases

| fase | material | turbulência | equação de estado |
|---|---|---|---|
| **Water** | Liquid | **K-Omega → SST (Menter)** + All y+ | Constant Density |
| **Air** | Gas | **K-Omega → SST (Menter)** + All y+ | Constant Density |

> 💡 **Por que k-ω aqui:** dá melhor resultado em escoamento **confinado**, e o amortecimento de
> turbulência na interface (§5) **só é compatível com k-ω**. Nos tutoriais 01–02 (ebulição na
> parede) o líquido usava k-ε — a escolha da turbulência segue o modelo de interface que se precisa.

## 4. Condições iniciais e valores de referência

**Nível inicial por Field Function** (gerador de vapor parcialmente cheio):

```
Initial_VF_Water = ($${Centroid}[0] > 2.67) ? (($${Centroid}[1] < 0.230) ? 1.0 : 0.0) : 0.0
Initial_VF_Air   = 1.0 - ${Initial_VF_Water}
```

`Phases > Water / Air > Initial Conditions > Volume Fraction` → Method = Field Function.

> 💡 **Mesmo truque do tutorial 02** (condição por coordenada), agora para **inicializar um nível**.
> Serve para qualquer equipamento que parte com líquido até certa cota.

**Reference Density = 0 kg/m³.**

> ⚠️ **Diferente de todos os tutoriais anteriores** (01, 02, 04 usavam a densidade do líquido ou do
> fluido frio). No MFR **não há fase de referência clara** — qualquer uma pode estar dispersa na
> outra — e a razão de densidades é enorme (ordens de grandeza). Com referência zero, o termo de
> gravidade entra **completo** na quantidade de movimento, o que dá uma solução robusta e estável.
> Consequência: a pressão resolvida **inclui a hidrostática**.

## 5. A interação de múltiplos regimes

`Phase Interactions > New > Water > Air (Multiple Flow Regime)` — **primária = Water**,
**secundária = Air**. Renomear `Water-Air`.

**Modelos opcionais:** **Large Scale Interface Turbulence Damping** (+ *Large Scale Interface
Detection*, automático).

**Limites entre regimes** (fração volumétrica da fase secundária):
- **First Regime Terminus** — onde o regime de bolhas (água contínua) termina e começa o
  intermediário;
- **Second Regime Onset** — onde o intermediário termina e começa o de gotas (ar contínuo).

O tutorial **mantém os defaults** dos dois.

| nó | valor | observação |
|---|---|---|
| Interaction Area Density | default | adequado para ar–água |
| **Drag → Intermediate Regime** | **Strubelj-Tiselj** | quando se espera **interface grande**; *Blended* quando não |
| Interaction Length Scale → **First Dispersed Regime** | Constant, **1 mm** | tamanho típico das **bolhas** |
| Interaction Length Scale → **Second Dispersed Regime** | Constant, **0,5 mm** | tamanho típico das **gotas** |
| Turbulence Damping → primária e secundária (K-Omega) | **Egorov**, constante **500**, distância à interface = **Cell Volume** | a interface se comporta como **parede móvel**: forma-se uma camada-limite dos dois lados, e sem amortecimento o k-ω superestima a turbulência ali |

> 💡 **Os dois tamanhos característicos são parâmetros físicos de verdade**, não ajustes numéricos:
> bolha controla o arrasto e a subida do gás no líquido; **gota controla quanto líquido o gás
> carrega** (arraste). Em problema de arraste de líquido, o tamanho de gota merece **sensibilidade**.

## 6. Condições de contorno

| fronteira | fase | velocidade | fração volumétrica |
|---|---|---|---|
| **Air_Inlet** (topo do vaso) | Air | **15 m/s** | 1,0 |
| **Water_Inlet** (fundo do gerador de vapor) | Water | **3 m/s** | 1,0 |

Saídas no default.

## 7. Solver e critérios de parada

| nó | valor | por quê |
|---|---|---|
| Volume Fraction → AMG Linear Solver → **Cycle Type** | **Flex Cycle** (em vez de V) | campo de fração **mais nítido** que num contínuo-disperso comum → convergência melhor |
| Implicit Unsteady → Time-Step | **0,01 s** | |
| Segregated EMP Flow → Phase Coupled Velocity | URF implícito **0,1** · explícito 0,5 | |
| Segregated EMP Flow → Pressure | URF **0,1** | |
| Volume Fraction | URF implícito **0,2** · explícito 0,5 | |
| K-Omega Turbulence / Turbulent Viscosity | URF **0,2** · razão máxima 10⁸ | |
| **Maximum Inner Iterations** | **25** | |
| Maximum Physical Time | **8 s** (800 passos) | Maximum Steps desligado |

> 💡 **Transiente "de verdade" × pseudo-transiente.** Aqui são **25 iterações internas por passo**:
> cada passo converge e o tempo tem significado físico (o bloqueio periódico do canal é o resultado).
> No tutorial 03 (VOF) era **1** iteração por passo — o tempo era só relaxação até o permanente.
> **URFs baixos (0,1–0,2) + muitas iterações internas** é a receita de robustez do EMP transiente.

> ⚠️ **Courant do ar:** a 15 m/s e Δt = 0,01 s o ar anda **15 cm por passo** — da ordem da altura do
> canal (25 cm). O implícito tolera, mas o detalhe da interface depende do passo. Em estudo real:
> **teste de passo de tempo** (metade do Δt, mesma resposta estatística?).

**Custo de referência:** 800 passos × 25 iterações = **20 000 iterações** para 8 s de um caso 2D.

## 8. Monitor da altura da interface

1. `Derived Parts > New > Section > Plane Section` → *Input* = região → origem **[2,15; 0; 0] m**
   (no trecho horizontal) → *No Displayer*. No 2D, o "plano" é uma **linha vertical**.
2. `Reports > New > Metrics > **Line Integral**` → renomear `Interface Height` → *Field Function* =
   **Volume Fraction of Water** → *Parts* = a seção.
3. *Create Monitor and Plot from Report*.

> 💡 **∫ α_água dy ao longo de uma vertical = altura de água "colapsada"** — a altura que a água
> teria se as bolhas fossem retiradas. Ideia poderosa: é **exatamente o que um transmissor de nível
> por ΔP mede**. Comparando com a altura onde a mistura realmente chega, mede-se o **inchamento do
> nível** dentro da simulação.

## 9. Cena e imagens para animação

*Scalar Scene* → **Volume Fraction of Water**, **Auto Range Off**, **0 a 1**, *Smooth Filled*,
**64 níveis** na barra de cores. `Attributes > Update`: **Save To File** ligado, *Trigger* = **Time
Step**, **frequência 5** → um `.png` a cada 5 passos. *Initialize Solution* para ver o nível inicial.

## 10. Animação

As imagens viram animação num programa externo (ex.: `animate`/ImageMagick no Linux; qualquer editor
de vídeo). O que se vê: o **bloqueio periódico** do canal pelo acúmulo de água — comportamento típico
de escoamento contracorrente.

> 💡 Animação é o jeito de mostrar a um cliente um fenômeno **intermitente** que nenhuma imagem parada
> captura (golfadas, oscilação de nível, arraste em rajadas). Definir a gravação **antes** de rodar —
> não dá para gerar depois sem salvar a solução a cada passo.

---

## Checklist reaproveitável
- [ ] Equipamento com bolhas **e** superfície livre **e/ou** gotas → **MFR** (EMP + interação
      *Multiple Flow Regime*).
- [ ] Transiente (*Implicit Unsteady*); convecção de fração volumétrica de **2ª ordem**.
- [ ] k-ω SST nas duas fases quando se usa amortecimento de turbulência na interface.
- [ ] Nível inicial por Field Function de coordenada.
- [ ] **Reference Density = 0** no MFR (pressão inclui a hidrostática).
- [ ] Drag intermediário **Strubelj-Tiselj** se houver interface grande.
- [ ] Tamanhos de bolha e de gota como parâmetros físicos, com sensibilidade quando importam.
- [ ] Amortecimento de turbulência na interface (Egorov) ligado.
- [ ] AMG da fração volumétrica em **Flex Cycle**; URFs baixos (0,1–0,2) + ~25 iterações internas.
- [ ] Teste de passo de tempo quando o Courant da fase rápida passa de ~1.
- [ ] **Line Integral** da fração de líquido numa vertical = nível colapsado (o que o ΔP mede).
- [ ] Escala de cor fixa 0–1 e gravação de `.png` por passo **antes** de rodar, para animação.
