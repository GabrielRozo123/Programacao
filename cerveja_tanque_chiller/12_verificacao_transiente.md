# 12 — Verificação com os transientes completos (refino dos números)

> Análise dos CSVs de monitor (transiente). Refina/corrige os tempos de cooldown e fecha a checagem adiabática.
> Figura: `figuras/sim1_bulk_vs_cstr.png`.

## Prova do mecanismo — Sim 1 × CSTR ideal (dado bom: T_bulk do Sim 1 completo)
Sobrepondo o T_bulk do Sim 1 (CFD) à curva analítica do CSTR (`−5+10·e^(−t/1053)`), o Sim 1 **resfria mais
rápido que a mistura perfeita** — a prova direta do **resfriamento por deslocamento** (estratificação estável):

| Marco (critério único) | **Sim 1 (CFD)** | CSTR ideal |
|---|---|---|
| T_bulk = −4,0 °C | 1230 s | 2425 s |
| T_bulk = −4,5 °C | 1520 s | 3155 s |
| **T_bulk = −4,9 °C (99%)** | **3040 s** | **4849 s** |
| T_bulk = −4,95 °C | 3900 s | 5579 s |
| T_bulk = −4,99 °C | 5880 s | 7274 s |

**Sim 1 bate o limite CSTR em ~40%.** Este gráfico substitui (com vantagem) o T_saída×T_bulk que planejávamos.

## ⚠️ Correção de números (transiente real vs. estimativa "de olho")
A estimativa anterior ("Sim 1 → −5 °C em ~2500 s") era do gráfico. **O dado real:** Sim 1 atinge **−4,9 °C
(99% resfriado) em 3040 s**. A **ordem e a física ficam idênticas** (Sim 1 < CSTR < Baseline; Sim 2 entre
Sim 1 e CSTR). Critério recomendado p/ comparar os casos: **tempo até T_bulk = −4,9 °C** (não "−5 °C", que é
assíntota). Sim 2 e Baseline ainda com estimativa (falta o T_bulk completo deles) — refinar quando exportados.

## Checagem adiabática da recirc (Sim 2) — evidência boa, parcial
Na junção das janelas exportadas:
- `T_capta(12320 s) = −4,999483 °C` · `T_retorno(12330 s) = −4,999486 °C` → **diferença 2,3 µC**, com atraso
  de **1 passo de tempo** (Δt=10 s). Confirma `T_retorno(t) = T_capta(t−Δt)` → **acoplamento adiabático OK**.
- **Ressalva:** as janelas (`T_capta` 8560–12320 s · `T_retorno` 12330–16250 s) **não se sobrepõem** no transiente,
  então é a confirmação num ponto de junção (+ o argumento de energia na ponta), não a curva completa sobreposta.

## ⚠️ Anomalia de monitor — "Temperatura de Saída" do Sim 1 (NÃO usar)
O CSV `T_saida_sim_1` está **constante em −4,504 °C** enquanto o **T_bulk do Sim 1 no mesmo tempo é −4,999 °C**
(gap fixo de **+0,50 °C**). Inconsistente (tanque uniforme a −5 não pode ter sucção a −4,5 fixa) e **contradiz**
o `TempSaida_MassFlowAvg` antigo (−4,89 °C). **Diagnóstico:** report mal definido (provável leitura da Static
Temperature imposta no bocal de sucção, não do fluido). **Descartado da análise.** Para o gráfico T_saída×T_bulk
(opcional, não necessário): usar o `TempSaida_MassFlowAvg` correto, completo, + o `T_bulk` do Sim 2.

## Conclusão
O **núcleo do estudo permanece sólido e agora com números refinados**. O gráfico Sim 1 × CSTR é a imagem
definitiva do mecanismo. Pendências são **opcionais** (transientes completos do Sim 2/Baseline p/ padronizar os
tempos) — não alteram o achado.
