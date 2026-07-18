# 11 — Síntese do estudo (storyline pros slides) · Tanque Chiller GreyLogix

> Compilação dos achados das 3 simulações + verificação. Pensado como **roteiro de apresentação**.
> Detalhe de cada rodada: `08_resultado_sim1.md` · `09_resultado_baseline_085.md` · `10_resultado_sim2.md`.

## 1. O problema (o "porquê" — vem do preliminar)
No estudo preliminar (tanque grande ~69 m³), o resfriamento sofria de **estratificação severa e persistente**:
camada quente **estagnada no topo** (warm lid), resfriamento **~9× mais lento** que o ideal bem-misturado, e o
**sensor de saída enganava** (lia frio enquanto o topo continuava quente). **Objetivo do estudo:** entender e
mitigar essa estratificação no tanque de produção (**TAG 3.500 L**, líquido 1,53 m, Ø1,66 m).

## 2. O método (o "como")
CFD transiente (STAR-CCM+), monofásico, **buoyancy-driven** (ρ(T)=1082,88−0,55·T → frio afunda). Chiller: puxa
na sucção, resfria, devolve a **−5 °C no fundo**, 12 m³/h. Início +5 °C. Paredes adiabáticas. **3 configurações:**

| Sim | Config | O que testa |
|---|---|---|
| **Baseline** | sucção **0,85 m** (original), sem recirc | referência da posição antiga |
| **Sim 1** | sucção **1,35 m** (nova, mais alta), sem recirc | efeito de **subir a sucção** |
| **Sim 2** | sucção 1,35 m **+ recirc** 12 m³/h (fundo→topo) | efeito de **adicionar recirculação** |

## 3. Os resultados (o "o quê")
| Métrica | Baseline 0,85 m | **Sim 1** 1,35 m | **Sim 2** + recirc |
|---|---|---|---|
| T_bulk → −4,9 °C (99%) | ~7500 s* | **3040 s** ⚡ | ~4500 s* |
| Pico de estratificação (ΔT topo–fundo) | — | 9,6 °C | **4,7 °C** 🎯 |

> *Sim 1 = **transiente real** (`12_verificacao_transiente.md`); CSTR ideal = 4849 s → **Sim 1 bate a mistura em ~40%**.
> Baseline e Sim 2 ainda estimados (falta o T_bulk completo). Critério: T_bulk = −4,9 °C ("−5 °C" é assíntota).
| Estado final | uniforme −5 °C | uniforme −5 °C | uniforme −5 °C |
| Regime de resfriamento | **curto-circuito** | **deslocamento** (plug-flow) | **~mistura** (CSTR) |

## 4. Os 3 achados (o "e daí")
**Achado 1 — Subir a sucção (0,85 → 1,35 m) resolve.** Resfria **~3× mais rápido** que a posição original e
homogeneíza. A sucção baixa (0,85 m) faz **curto-circuito** (re-aspira o frio recém-injetado no fundo, deixa o
topo intocado) → o mais lento de todos.

**Achado 2 — A recirc UNIFORMIZA, mas NÃO acelera (contraintuitivo, verificado).** A recirc corta o pico de
estratificação **pela metade** (9,6 → 4,7 °C), mas o cooldown fica **~2× mais lento**. Não é bug — é
**armazenamento térmico estratificado**: com frio no fundo + sucção alta, a estratificação faz um resfriamento
por **deslocamento** (mais eficiente que misturar); a recirc homogeneíza → empurra pro limite de mistura perfeita
(CSTR), que é intrinsecamente mais lento.

**Achado 3 — O mecanismo é a T_sucção.** A velocidade do cooldown = `ṁ·cp·(T_sucção + 5)`. Estratificado (Sim 1):
a sucção puxa o quente do topo → duty máximo. Misturado (Sim 2): a sucção vê ~T_bulk → duty cai. *(Slide: plotar
T_sucção vs T_bulk — separadas no Sim 1, coladas no Sim 2.)*

## 5. A recomendação (o trade-off pro cliente)
| Prioridade do cliente | Recomendação |
|---|---|
| **Resfriar rápido** | **Sim 1** — sucção alta (1,35 m), **sem** recirc |
| **Cerveja uniforme** (sem gradiente térmico) | **Sim 2** — adicionar recirc (ΔT pela metade), custo ~2× mais lento |

Em ambos os casos, **subir a sucção de 0,85 → 1,35 m é ganho garantido** (resolve o problema original do preliminar).
A recirc é um **nível a mais de uniformidade**, se o processo exigir.

## 6. Robustez (verificação já feita + o que falta apertar)
- **Já verificado (3 lentes adversariais → coerente):** benchmark CSTR (τ=V/Q=1053 s) enquadra os 3 casos; duty
  inicial 113,5 kW calc vs 115 obs (1,4%); **hipótese de artefato (vazamento de calor) refutada** pela ponta
  (leak <0,07 kW). O achado do trade-off é **sólido**.
- **A apertar antes da entrega:** (1) recirc adiabática (T_retorno = T_captação, integral de P_recirc≈0);
  (2) fechamento de energia (∫duty ≈ 119,5 MJ nas 3); (3) T_sucção(t) vs T_bulk das 3; (4) sensibilidade de Δt
  (herdado do tanque de 69 m³, Courant no jato ~13); (5) critério único de "resfriado" (−4,99 °C).

## 7. Lições de método (pra não repetir)
- **Probe de ponto:** ❌ nunca *Maximum/Minimum report* (agarra célula parada → falso ΔT de 10 °C no baseline).
  ✅ Point Probe / Volume Average / Line Probe.
- **Verificar o contraintuitivo:** o achado "recirc mais lenta" foi checado contra o **benchmark CSTR** e o
  **fechamento de energia** antes de virar conclusão. Vale sempre pra resultado que contraria a intuição.

## Sugestão de sequência de slides
1. **O problema** (estratificação do preliminar) · 2. **O método** (3 configs) · 3. **Resultado 1:** subir a sucção
resolve (3× mais rápido) · 4. **Resultado 2:** recirc uniformiza mas é mais lenta (o gráfico T_sucção×T_bulk) ·
5. **O trade-off** e a recomendação · 6. **Robustez** (CSTR + energia).
