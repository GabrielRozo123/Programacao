# Tutorial 08 — Eulerian: Aeration Tank Degassing

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: 🟡 seções 1–5 lidas (visão geral, Loading and Meshing, Physics Models, Phases, Phase
> Interactions — 13/10/2026). **A seção-chave (contorno de degaseificação) ainda não veio.**

---

## 0. Por que este tutorial

Num tanque com gás borbulhando, a superfície livre pode ser tratada de dois jeitos:
1. **resolver a superfície** (VOF / Multiple Flow Regimes — tutoriais 03 e 07): caro, transiente;
2. **substituir a superfície por um contorno de degaseificação**: uma "parede" **permeável só ao
   gás**. O gás sai na taxa em que chega; o líquido fica. Barato, **regime permanente** possível.

Este tutorial ensina o segundo jeito.

## 1. O caso

| item | valor |
|---|---|
| Tanque | **0,5 m (comprimento) × 0,1 m (largura) × 0,3 m (altura)**, cheio de água |
| Entrada de ar | placa perfurada com **4 % de área aberta**, ar a **5 m/s** nos furos |
| Modelo da placa | *Velocity Inlet* com **fração volumétrica de ar = 0,04** |
| Topo | **parede permeável à fase** (*phase-permeable wall*): só o ar passa |
| Modelo | **Eulerian Multiphase**, regime **permanente**, turbulento |
| Forças de interação | arrasto, **dispersão turbulenta**, **massa virtual** |
| Resultado | fração de ar no tanque e **vazão de ar no contorno de degaseificação** (calculada pelo STAR); vazão de água pelo topo = **zero** |

> 💡 **Truque da placa perfurada: velocidade do furo + fração = área aberta.** Entrar com 5 m/s (a
> velocidade real nos furos) e fração 0,04 (a área aberta) preserva **as duas coisas**:
> - vazão mássica: `ρ·0,04·5` = a vazão real;
> - quantidade de movimento: `ρ·0,04·5²` = a dos jatos reais.
>
> Entrar com a velocidade superficial (0,2 m/s) em 100 % da área acertaria a vazão mas daria **25×
> menos quantidade de movimento**. Vale para qualquer distribuidor perfurado: **preservar massa e
> quantidade de movimento**, não só massa. *(A conferir na seção de contornos: que velocidade a água
> recebe na entrada — para não injetar água junto, o esperado é velocidade zero para a fase água.)*

> 📌 **Régua de balanço:** em regime permanente, **vazão de ar que entra = vazão de ar no contorno de
> degaseificação**, e a vazão de água pelo topo tem de ser zero. É o critério de convergência mais
> direto deste tipo de caso.

## 2. Arquivo inicial e malha

`File > Load` → `aerationTank_start.sim` (geometria, operações de malha e regiões já prontas) →
`Geometry > Operations > Automated Mesh > Execute` → malha **poliédrica** → salvar como
`aerationTank_run.sim`.

## 3. Modelos físicos

| grupo | modelo |
|---|---|
| Espaço / Tempo | 3D · **Steady** |
| Material | Multiphase (+ Multiphase Interaction) |
| Modelo | **Eulerian Multiphase (EMP)** |
| Regime | Turbulent |
| Turbulência EMP | **Mixture Turbulence** (não *Phasic*) |
| RANS | K-Epsilon, Two-Layer All y+ |
| Opcionais | **Gravity** (empuxo das bolhas) |

> 💡 **Mixture × Phasic Turbulence.** *Mixture*: **um** k-ε para a mistura — mais barato e robusto
> quando o gás é disperso e em fração moderada. *Phasic* (tutoriais 01, 02, 07): turbulência **por
> fase** — necessária quando as fases têm dinâmicas muito diferentes ou há interface grande com
> amortecimento.

## 4. Fases

| fase | material | equação de estado |
|---|---|---|
| **Water** | Liquid | Constant Density |
| **Air** | Gas | Constant Density |

Propriedades **padrão** das duas.

## 5. Interação entre fases

`Phase Interactions > New > Water > Air (Continuous-Dispersed)` → renomear `Water-Air`. Água contínua,
ar disperso, **bolhas de 1 mm**.

| modelo / nó | valor | por quê |
|---|---|---|
| **Virtual Mass Force** (+ coeficiente, automático) | ligado | trabalho da bolha para deslocar o líquido ao redor |
| **Turbulent Dispersion Force** | ligado | espalhamento das bolhas pelos turbilhões |
| Interaction Length Scale | Constant, **1 mm** | diâmetro da bolha |
| Drag Coefficient | **Tomiyama** | recomendado para bolhas; cobre larga faixa de propriedades e diâmetros; **exige gravidade**; tem **3 níveis de contaminação** do líquido |
| Surface Tension | **0,072 N/m** (ativada automaticamente pelo Tomiyama) | ar–água a temperatura ambiente |

> ⚠️ **Tensão superficial é default de ar–água a ~20 °C.** Para água/vapor em pressão alta é bem
> menor (0,026–0,030 N/m a 30–40 bar — ver `props_agua_saturada.py`). O Tomiyama usa esse valor: em
> outro sistema, **trocar**.

> 💡 **Nível de contaminação do Tomiyama** muda a velocidade de subida da bolha: líquido "limpo" →
> bolha sobe mais rápido; contaminado (água de processo, industrial) → mais devagar, mais gás retido.
> Escolha física que afeta a fração de vazio — anotar qual foi usada.

---

## Checklist reaproveitável (até aqui)
- [ ] Superfície livre com borbulhamento **sem** precisar da forma da superfície → **contorno de
      degaseificação** (permanente, barato).
- [ ] Distribuidor perfurado: **velocidade do furo + fração = área aberta** (massa **e** quantidade
      de movimento corretas).
- [ ] Balanço: gás que entra = gás que sai na degaseificação; líquido pelo topo = 0.
- [ ] Mixture Turbulence para bolhas dispersas em fração moderada; Phasic quando as fases divergem.
- [ ] Tomiyama + gravidade; **tensão superficial do sistema real**; nível de contaminação declarado.
- [ ] Massa virtual e dispersão turbulenta ligadas em escoamento de bolhas.

## Seções seguintes
*(a receber — inclusive o contorno de degaseificação)*
