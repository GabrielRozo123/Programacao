# Tutorial 07 — Eulerian Multiple Flow Regimes: Pressurized Water Reactor

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: 🟡 seções 1–5 lidas (visão geral, Physics Models, Phases, Initial Conditions and Reference
> Values, Multiple Flow Regime Phase Interaction — 13/10/2026). Restante a receber.

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

---

## Checklist reaproveitável (até aqui)
- [ ] Equipamento com bolhas **e** superfície livre **e/ou** gotas → **MFR** (EMP + interação
      *Multiple Flow Regime*).
- [ ] Transiente (*Implicit Unsteady*); convecção de fração volumétrica de **2ª ordem**.
- [ ] k-ω SST nas duas fases quando se usa amortecimento de turbulência na interface.
- [ ] Nível inicial por Field Function de coordenada.
- [ ] **Reference Density = 0** no MFR (pressão inclui a hidrostática).
- [ ] Drag intermediário **Strubelj-Tiselj** se houver interface grande.
- [ ] Tamanhos de bolha e de gota como parâmetros físicos, com sensibilidade quando importam.
- [ ] Amortecimento de turbulência na interface (Egorov) ligado.

## Seções seguintes
*(a receber)*
