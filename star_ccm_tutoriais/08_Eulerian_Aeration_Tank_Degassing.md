# Tutorial 08 — Eulerian: Aeration Tank Degassing

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: ✅ tutorial completo lido (seções 1–10: visão geral, malha, modelos, fases, interação,
> condições iniciais e gravidade, contornos, cenas e relatórios, execução, resultados — 13/10/2026).

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
> quantidade de movimento**, não só massa. A água entra com **velocidade zero** (§7), para não injetar
> líquido junto.

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

## 6. Condições iniciais e gravidade

| nó | valor |
|---|---|
| Water → Initial Volume Fraction | **1,0** (tanque cheio, sem ar) |
| Gravity | `[0; −9,81; 0]` m/s² |
| **Reference Density** | **997,561 kg/m³** = densidade da fase **contínua** (água) |

> 📌 **Densidade de referência — a regra que fecha a série de tutoriais:**
> - **Contínuo-disperso** (01, 02, 08): densidade da fase **contínua** (o líquido).
> - **Multiple Flow Regimes** (07): **zero** — não há fase contínua definida.
> - **Monofásico com empuxo** (04): densidade do fluido **frio/ambiente**.

## 7. Contornos — o contorno de degaseificação

### Topo: `Degassing Outlet`
1. `Degassing Outlet > Phase Conditions > Air > Type = **Phase Permeable**` → o ar sai; **para a
   água, o contorno é parede**.
2. *Tangential Velocity Specification* = Vector → *Relative Velocity* = **[0; 0; 5] m/s** — uma
   "tampa móvel" que **arrasta a água** em +z, para criar uma corrente no tanque (as bolhas são
   levadas na direção do escoamento enquanto sobem).

O STAR garante **gás que entra = gás que sai** e calcula a fração de gás interna pela continuidade.

### Fundo: `Gas Inlet` (placa perfurada)
| fase | velocidade | fração volumétrica |
|---|---|---|
| Water | **0,0 m/s** | 0,96 |
| Air | **5,0 m/s** | **0,04** |

✅ Confirma o truque da §1: velocidade do furo + fração = área aberta, e **velocidade zero para a
água** para não injetar líquido.

> ⚠️ **A água "vê" o contorno de degaseificação como parede.** O default de parede é **não
> deslizamento**, e uma superfície livre real **não tem atrito**. Aqui o tutorial usa a parede para
> impor uma corrente (tampa a 5 m/s). Em equipamento onde o contorno representa uma superfície livre
> parada, conferir a opção de **deslizamento (slip)** para o líquido. Senão aparece uma camada-limite
> artificial logo abaixo da "superfície" que freia a circulação.

## 8. Cenas e relatórios

| item | configuração |
|---|---|
| Cena *Volume Fraction of Air* | plano de corte, *Smooth Filled*, **máximo 0,2**, vista lateral (+X, Up +Y) |
| Cena *Mass Flow Rate of Air* | no `Degassing Outlet`, vista de topo — **onde** o ar sai |
| Relatórios **Phase Mass Flow** | `Air Mass Flow Out` e `Water Mass Flow Out` no `Degassing Outlet` → monitores num **gráfico único** |

## 9. Solver e execução

Regime **permanente**, **6 000 iterações**.

| solver | URF | tolerância AMG |
|---|---|---|
| Segregated EMP Flow → Phase Coupled Velocity | implícito **0,3** · explícito 1,0 | **0,001** |
| Segregated EMP Flow → Pressure | **0,1** | **0,001** |
| Volume Fraction | implícito **0,1** · explícito 1,0 | **0,001** |

> 💡 **Receita do EMP permanente:** relaxações baixas **e** tolerância do AMG mais apertada (0,001)
> ajudam a convergir. Mesma família de ajustes do EMP transiente do tutorial 07.

## 10. Resultados

- As bolhas sobem e são **levadas pela corrente**; saem pela parede permeável. A água fica no tanque.
- No topo, a saída de ar se concentra no **lado de jusante** da pluma.
- **Vazão de ar que sai = 2,8×10⁻⁴ kg/s = vazão que entra**; **vazão de água pelo topo = 0**.

> 💡 **Régua de volta:** 2,8×10⁻⁴ kg/s = ρ_ar·0,04·5·A → com ρ_ar = 1,184 kg/m³ (default),
> **A ≈ 11,8 cm²** de placa perfurada (ex.: faixa de ~12 mm na largura de 0,1 m). Conferir a área da
> entrada é o jeito de checar que o balanço reportado bate com o imposto.

---

## Checklist reaproveitável
- [ ] Superfície livre com borbulhamento **sem** precisar da forma da superfície → **contorno de
      degaseificação** (*Phase Permeable* para o gás; parede para o líquido), regime permanente.
- [ ] Contorno de degaseificação representando superfície livre parada → **deslizamento (slip) para
      o líquido**, não parede com atrito.
- [ ] Distribuidor perfurado: **velocidade do furo + fração = área aberta**, velocidade **zero** para
      a outra fase.
- [ ] Balanço: gás que entra = gás que sai na degaseificação (relatórios *Phase Mass Flow*); líquido
      pelo topo = 0.
- [ ] Reference Density = fase contínua (contínuo-disperso) · 0 (MFR) · fluido frio (monofásico).
- [ ] Mixture Turbulence para bolhas dispersas em fração moderada; Phasic quando as fases divergem.
- [ ] Tomiyama + gravidade; **tensão superficial do sistema real**; nível de contaminação declarado.
- [ ] Massa virtual e dispersão turbulenta ligadas em escoamento de bolhas.
- [ ] EMP permanente: URFs 0,1–0,3 e tolerância AMG 0,001.
- [ ] Cena da vazão de gás **no** contorno de saída: mostra **onde** o gás sai.
