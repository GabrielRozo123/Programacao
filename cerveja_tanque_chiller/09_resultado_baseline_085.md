# 09 — Resultado do Baseline (sucção 0,85 m — SEM recirc)

> Rodada na workstation da CAE. Domínio: `cerveja_baseline_085_fluido.step` (mesmo tanque 3.500 L do Sim 1,
> só que com a **sucção antiga a 0,85 m** + retorno no fundo, mesmo lado, sem recirc). Serve pra **isolar o
> efeito da altura da sucção** (comparar direto com o Sim 1 a 1,35 m, no mesmo tanque).
> Mesma física do Sim 1: ρ(T)=1082,88−0,55·T · paredes adiabáticas · Q=12 m³/h · T_inicial +5 °C · chiller −5 °C.

## Resultado (dos monitores CONFIÁVEIS)
| Métrica | Baseline **0,85 m** | Sim 1 **1,35 m** |
|---|---|---|
| Estado final (Line Probe eixo, 0→1,5 m) | **uniforme −5,0 °C** (−4,99999) | uniforme −5,0 °C |
| T_bulk atinge −5 °C | **~7000–8000 s (~2 h)** | ~2000–2500 s (~35–40 min) |
| Balanço de energia → 0 | ~7000–8000 s | ~2500 s |
| Estratificação persistente | **não** | não |

**➡️ Achado honesto: subir a sucção 0,85 → 1,35 m resfria o tanque ~3× mais rápido.** Os dois chegam a
**homogêneo −5 °C** — neste tanque de 3,5 m³ a estratificação **não persiste** em nenhum dos dois (diferente
do tanque grande ~69 m³ do preliminar, onde persistia). **A alavanca aqui é a VELOCIDADE de resfriamento,
não warm lid.** Mecanismo: *filling-box* — o frio (denso) enche de baixo pra cima; a sucção alta (1,35 m)
**toca a camada quente do topo** e a puxa pro chiller → resfria tudo mais rápido. A sucção baixa (0,85 m)
curto-circuita o frio de baixo e o topo só enche por acúmulo → ~3× mais lento.

## ⚠️ Lição de setup — o "falso achado" (probe quebrado)
O monitor de ΔT **pinou em 10 °C** e parecia estratificação permanente. **Era artefato.** A prova:
- **Line Probe** (T vs altura no eixo): **−5,0 °C uniforme** do fundo ao topo (varia só na 7ª casa decimal).
- **Sensor Alto = +5,000000 °C exato** (o valor INICIAL), e era um **"Maximum value report"**.

**Causa:** um *Maximum report* retorna a **célula mais quente** da parte. No baseline, a zona **acima de 0,85 m**
tem fluxo fraquíssimo → **uma célula solta perto da parede/canto ficou presa perto do +5 °C inicial** → o
Máximo agarrou essa outlier e ignorou que 99,99% do topo já estava a −5 °C. (No Sim 1, a 1,35 m, o topo é bem
varrido → sem célula parada → o Máximo funcionou, por isso o ΔT do Sim 1 saiu bonito.) O Sensor Baixo (Mínimo)
está OK porque o fundo é bem lavado pelo jato frio.

**Regra:** ❌ **nunca usar Maximum/Minimum report pra "temperatura num ponto"** — é frágil a uma célula parada.
✅ usar **Point Probe** (T interpolada no ponto) ou **Volume Average** de uma fatia fina. A **Line Probe** é a
fonte confiável da estratificação.

> O `Balanço de Energia` (`−ṁ·cp·(T_saída − 268,15)`) está bem definido — vai a zero quando a saída chega a
> −5 °C. A física da rodada está sólida; só o monitor de ponto (Máximo) que era frágil.

## Fecho da comparação (baseline → Sim 1 → Sim 2)
- **Baseline 0,85 m:** homogeneíza, ~2 h.
- **Sim 1 1,35 m:** homogeneíza, ~35–40 min (**~3× mais rápido** — o ganho da altura da sucção).
- **Sim 2 (1,35 m + recirc):** em andamento — ver se a recirc fundo→topo acelera ainda mais.
