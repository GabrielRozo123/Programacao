# 10 — Resultado do Sim 2 (chiller 1,35 m + RECIRCULAÇÃO adiabática)

> Rodada na workstation. Domínio `cerveja_sim2_fluido.step`. Config: chiller (sucção 1,35 m + retorno fundo −5 °C,
> 12 m³/h) **+ 2º circuito de recirc ADIABÁTICO** (12 m³/h: capta no fundo ~0,1 m, devolve no topo ~1,43 m,
> T_retorno = T média-por-vazão da captação via field function → só **mistura**, não troca calor).
> ρ(T)=1082,88−0,55·T · paredes adiabáticas · T_inicial +5 °C. **Verificado por 3 lentes adversariais (coerente).**

## Resultado
| Métrica | Valor |
|---|---|
| **Pico de estratificação (ΔT topo−fundo)** | **4,7 °C @ ~500 s** (≈ **metade** do Sim 1) |
| Homogeneíza (ΔT → 0) | ~3000–3500 s |
| **T_bulk atinge o alvo (−5 °C)** | **~4000–4500 s** (final −4,992 °C) |
| Balanço de energia (chiller) | −115 kW → **0** (final −0,072 kW) em ~4500–5000 s |
| Oscilações no ΔT (1500–2500 s) | **Rayleigh-Taylor** (frio denso injetado no topo → overturning) |

## ⭐ O achado (contraintuitivo, mas VERIFICADO)
**A recirc REDUZ o pico de estratificação (9,6 → 4,7 °C) MAS deixa o resfriamento mais LENTO** (~4500 s vs
~2500 s do Sim 1). Não é bug — é **armazenamento térmico estratificado clássico**:
- Taxa de resfriamento = `ṁ·cp·(T_sucção + 5)`. Com retorno fixo em −5 °C, **quem manda é a T_sucção**.
- **Sim 1 (estratificado):** sucção alta puxa o **quente do topo** → T_sucção alta → **duty máximo** (deslocamento
  ≈ plug-flow, mais eficiente que misturar) → **mais rápido**.
- **Sim 2 (recirc):** homogeneíza → sucção vê ~T_bulk → duty cai → **mais lento** (tende ao limite CSTR).
- **Reduzir o pico E ficar mais lento são o MESMO mecanismo** (homogeneizar). Sem contradição.

## Verificação adversarial (3 lentes → todas "coerente")
- **Números:** duty inicial calc **113,5 kW** vs −115 obs (1,4%, arredondamento ρ/cp). τ_CSTR = V/Q = **1053 s**.
- **Enquadramento físico:** piso (deslocamento) = τ; teto (CSTR) ≈ 4849 s p/ −4,9 °C.
  **Sim 1 ~2500 s** < **Sim 2 ~4000–4500 s** < CSTR (4849 s) < **Baseline ~7500 s** (curto-circuito, pior que CSTR).
- **Artefato (vazamento de calor) REFUTADO:** um leak travaria o balanço num patamar e o tanque pararia **acima**
  de −5 °C. O observado (balanço→−0,07 kW, bulk→−4,992) **limita qualquer leak a <0,07 kW** (precisaria ~20–30 kW
  p/ o atraso 2×). E o Sim 2 é até um tiquinho **mais rápido que o CSTR ideal** → evidência de **mistura adiabática limpa**.

## Comparação final (baseline → Sim 1 → Sim 2)
| | Baseline 0,85 m | Sim 1 1,35 m | **Sim 2 1,35 m + recirc** |
|---|---|---|---|
| Pico ΔT | (probe bugado) | 9,6 °C | **4,7 °C (metade)** |
| T_bulk → −5 °C | ~7500 s | **~2500 s (mais rápido)** | ~4500 s |
| Regime | curto-circuito | deslocamento (plug-flow) | ~mistura (CSTR) |
| Estratificação | — | maior (transitória) | **menor** |

## 🎯 A leitura pro cliente (trade-off honesto)
**A recirc não acelera — ela UNIFORMIZA.** É uma escolha de projeto:
- **Prioridade = resfriar rápido** → **Sim 1 (sucção alta, sem recirc)**.
- **Prioridade = cerveja uniforme / sem gradiente térmico** → **recirc** (ΔT pela metade), custo ~2× mais lento.

Raising a sucção 0,85 → 1,35 m já resolve o problema original (persistência do preliminar) E acelera. A recirc é
o "nível a mais" de uniformidade, se o cliente priorizar isso.

## Checagens pra apertar o número antes da entrega (das lentes)
1. **Recirc adiabática:** plotar T de `recirc_retorno` e `recirc_captacao` vs tempo → devem coincidir; report
   `P_recirc = ṁ·cp·(T_ret−T_capta)` integrado ≈ 0.
2. **Fechamento de energia:** integrar o duty do chiller nas 3 sims → **~119,5 MJ** em todas (±5%).
3. **T_sucção(t) das 3** (= T_saída, mass-flow-avg em `succao_chiller`) sobreposta a T_bulk → prova do mecanismo.
4. **Δt=1 s foi herdado do tanque de 69 m³** (Courant no jato ~13) — teste Δt=0,5 s na janela das oscilações.
5. **Critério único de "resfriado"** (ex.: −4,99 °C) pros 3, p/ comparação justa.

> Nenhuma inverte o achado (ancorado no benchmark CSTR + fechamento na ponta) — são p/ robustez na apresentação.
