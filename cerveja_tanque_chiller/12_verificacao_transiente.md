# 12 — Verificação com os transientes completos (refino dos números)

> Análise dos CSVs de monitor (transiente). Refina/corrige os tempos de cooldown e fecha a checagem adiabática.
> Figura: `figuras/sim1_bulk_vs_cstr.png`.

## Prova do mecanismo — Sim 1 × CSTR ideal (dado bom: T_bulk do Sim 1 completo)
Sobrepondo o T_bulk do Sim 1 (CFD) à curva analítica do CSTR (`−5+10·e^(−t/1053)`), o Sim 1 **resfria mais
rápido que a mistura perfeita** — a prova direta do **resfriamento por deslocamento** (estratificação estável):

| Marco (T_bulk) | **Sim 1 (CFD)** | **Sim 2 (CFD)** | CSTR ideal |
|---|---|---|---|
| −4,0 °C | 1230 s | 2170 s | 2425 s |
| −4,5 °C | 1520 s | 2890 s | 3155 s |
| **−4,9 °C (99%)** | **3040 s** | **4930 s** | **4849 s** |

**Sim 1 bate o CSTR em ~37% (deslocamento). Sim 2 CAI EM CIMA do CSTR (~1,7% mais lento) → limite de mistura.**
Figuras: `figuras/tres_casos_vs_cstr.png` (os 3 × CSTR — o slide-mestre) e `figuras/sim1_bulk_vs_cstr.png`.

> **Correção da verificação:** as 3 lentes previram "Sim 2 um pouco mais rápido que o CSTR" — mas isso usou minha
> estimativa (~4000–4500 s) que estava rápida demais. O **dado real dá 4930 s ≈ CSTR (marginalmente mais lento)**.
> O núcleo (recirc → mistura → mais lento que o Sim 1) fica **ainda mais limpo**: o Sim 2 assenta **no** limite CSTR.

## ⚠️ Correção de números (transiente real vs. estimativa "de olho")
A estimativa anterior ("Sim 1 → −5 °C em ~2500 s") era do gráfico. **O dado real:** Sim 1 atinge **−4,9 °C
(99% resfriado) em 3040 s**. A **ordem e a física ficam idênticas** (Sim 1 < CSTR < Baseline; Sim 2 entre
Sim 1 e CSTR). Critério recomendado p/ comparar os casos: **tempo até T_bulk = −4,9 °C** (não "−5 °C", que é
assíntota). Sim 2 e Baseline ainda com estimativa (falta o T_bulk completo deles) — refinar quando exportados.

## Checagem adiabática da recirc (Sim 2) — RIGOROSA (transiente completo) ✅
Com `T_capta` e `T_retorno` no **mesmo intervalo (10–4990 s)**, sobrepostos (`figuras/sim2_adiabatica.png`):
- **T_retorno segue T_captação** curva a curva. Diferença: **média +6,8 mC**, pico ±461 mC (só nas oscilações
  iniciais, que amortecem), ~0 no fim. O offset médio de +7 mC é o **atraso de 1 passo de tempo** (o retorno
  carrega o valor um pouco mais quente da captação durante a descida) — não é vazamento.
- **Energia líquida da recirc** = ṁ·cp·∫(T_ret−T_capta)dt = **+0,38 MJ = +0,3 %** dos ~118 MJ removidos →
  **desprezível**. A recirc é **adiabática** (só mistura). ✅ *Fecha a checagem que estava pendente.*

## ⚠️ Anomalia de monitor — "Temperatura de Saída" do Sim 1 (NÃO usar)
O CSV `T_saida_sim_1` está **constante em −4,504 °C** enquanto o **T_bulk do Sim 1 no mesmo tempo é −4,999 °C**
(gap fixo de **+0,50 °C**). Inconsistente (tanque uniforme a −5 não pode ter sucção a −4,5 fixa) e **contradiz**
o `TempSaida_MassFlowAvg` antigo (−4,89 °C). **Diagnóstico:** report mal definido (provável leitura da Static
Temperature imposta no bocal de sucção, não do fluido). **Descartado da análise.** Para o gráfico T_saída×T_bulk
(opcional, não necessário): usar o `TempSaida_MassFlowAvg` correto, completo, + o `T_bulk` do Sim 2.

## Conclusão
**Estudo fechado.** Com os transientes completos do Sim 1 e Sim 2: o gráfico dos 3 casos × CSTR é a imagem
definitiva (Sim 1 deslocamento < Sim 2 ≈ CSTR < Baseline), e a **recirc adiabática está rigorosamente
confirmada** (+0,3 % de energia espúria). Única pendência opcional: T_bulk completo do **Baseline** p/ cravar
o ~7500 s com o mesmo critério — mas não altera nada.
