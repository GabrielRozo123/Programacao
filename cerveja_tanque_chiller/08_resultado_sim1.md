# 08 — Resultado do Sim 1 (chiller, sucção 1,35 m — SEM recirc)

> Primeira rodada na workstation da CAE. Domínio: TAG 3.500 L (`cerveja_sim1_fluido.step`).
> Config: sucção do chiller a **1,35 m** + retorno frio no **fundo**, **sem recirculação**.
> ρ(T)=1082,88−0,55·T · paredes adiabáticas · Q=12 m³/h · **T_inicial +5 °C** · chiller retorna a **−5 °C**.

## Resultado (dos monitores)
| Métrica | Valor |
|---|---|
| **Pico de estratificação (ΔT topo−fundo)** | **9,6 °C** @ ~700 s (~12 min) |
| **Homogeneíza (ΔT → 0)** | **~2000 s (~33 min)** |
| T_bulk cruza 0 °C | ~1050 s (~18 min) |
| **T_bulk atinge −4,9 °C (99%)** | **3040 s** (transiente real — ver `12`; "−5 °C" é assíntota) — final **−4,999 °C** |
| **Duty do chiller** | **~−115 kW** (patamar) → **0** ao equilibrar |
| T_saída (p/ o chiller) final | **−4,89 °C** ≈ T_bulk (−5,0) |
| T_inicial | +5 °C |

## O que aconteceu (a física, em 3 fases)
1. **0–700 s — resfriando forte:** chiller remove ~115 kW constante. Frio (denso) se acumula no fundo →
   estratificação cresce até **9,6 °C**. A **T_saída segura em +5 °C** (a sucção a 1,35 m ainda puxa líquido
   quente do topo — assinatura da estratificação).
2. **700–2000 s — a frente de frio sobe:** ao chegar em 1,35 m, a T_saída despenca (justo no pico do ΔT).
   A camada quente do topo é consumida → **ΔT colapsa**; a taxa de resfriamento cai ao se aproximar do alvo.
3. **>2000 s — equilíbrio:** tanque uniforme a **−5 °C**. ΔT≈0, duty≈0. Cooldown **completo**.

Coerência: 12 m³/h × ~8 °C no loop ≈ ~110 kW (bate com o patamar). Cooldown de 3.500 L (+5→−5 °C) em
~35 min também fecha. Balanço de energia → 0 confirma equilíbrio térmico real (não é parada numérica).

## Comparação com o preliminar (a "estratificação observada")
| | Preliminar (~69 m³, sucção 0,85 m) | **Sim 1 (3.500 L, sucção 1,35 m)** |
|---|---|---|
| Estratificação | **Persistente** ~7,5 °C após 20 h | **Transitória**, pico 9,6 °C, some em ~33 min |
| T_bulk | travava em −0,5 °C (não atingia) | **−5,0 °C (alvo) atingido** |
| Camada quente (warm lid) | estagnada, nunca resolvia | **resolve** |
| Sensor de saída vs bulk | enganava (−4,3 vs −0,5) | **converge no fim** (−4,89 vs −5,0) |

### ⚠️ Cuidado com a comparação de TEMPOS
Os tanques têm **tamanhos diferentes** (~69 m³ vs 3,5 m³, ~20×). Boa parte da diferença de *velocidade*
é **tamanho**, não projeto. O ganho **defensável do projeto** é **qualitativo**: estratificação transitória
(vs persistente), cooldown completo até o alvo, e sensor de saída voltando a representar o bulk.

**Para isolar SÓ o efeito da altura da sucção:** rodar o mesmo tanque 3.500 L com a sucção antiga (0,85 m)
→ baseline do mesmo tanque. O `geometria/gen_sim_steps.py` tem `Z_SUC_BASE=850` pronto. *(Opcional.)*

## Recado pro controle (lição confirmada)
Durante o **cooldown** (primeiros ~30 min) há estratificação real → o sensor de **saída subestima o topo**;
**o T_topo é a referência** nessa fase. No **regime final**, saída ≈ bulk (−4,89 vs −5,0), então a saída
volta a ser confiável. (No preliminar isso **nunca** acontecia.)

## Próximo
**Sim 2 (+ recirculação fundo→topo):** esperado **picar menos** (a recirc mistura e ataca o warm lid antes).
Comparar: pico de ΔT, tempo de homogeneização e tempo até −5 °C, Sim 1 × Sim 2.
