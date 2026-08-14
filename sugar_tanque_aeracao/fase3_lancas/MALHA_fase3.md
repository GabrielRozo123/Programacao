# Fase 3 · Aerador com 16 lanças — malha e refino

## 1. O número que decide tudo: Re = 9,5

| | |
|---|---|
| vazão por lança | 130 m³/h ÷ 16 = 8,13 m³/h |
| velocidade no injetor | **0,731 m/s** |
| **Re = ρvD/µ** = 1350·0,731·0,0627/6,5 | **9,52** |

O jato da lança é laminar por uma margem enorme (transição em Re ≈ 2300). Não há
camada cisalhante turbulenta, não há vórtices para capturar, não há break-up para
resolver. Os gradientes são difusivos e suaves.

**Consequência para a malha:** o refino não é exigido pela física — é exigido pela
*geometria*. O injetor tem Ø62,7 mm; com célula base de 40 mm ele pega 1,5 célula,
o que erra a área de entrada e faz o jato nascer quadrado. O refino existe para
dar ~6 células no diâmetro do injetor, e nada mais.

Corolário: **não use prism layer fino por causa de y+**. Não há lei de parede
relevante aqui — a camada limite viscosa é o escoamento inteiro. 2 camadas de
transição bastam para a precisão do gradiente na parede.

Bônus do mesmo número: a velocidade de Stokes de uma bolha de 0,2 mm é
0,0045 mm/s. Ela sobe 1,6 cm por hora. Isso confirma, por um caminho independente,
o que já reportamos ao Ito.

## 2. Cilindros de refino

Os `Refino_Injetor_1/2/3` existentes devem ser **apagados**: estão nas posições das
3 lanças originais (r = 305 mm, ponta em z = −5,2465), que não existem mais.

16 cilindros novos, R = 100 mm (≈3,2× o raio da lança), cobrindo 350 mm abaixo e
150 mm acima do disco do injetor. Total 0,2513 m³ = 1,26 % do domínio.

Macro pronto: **`CriaRefinoLancas.java`** → `File → Macro → Play Macro…`

| parte | Start Coordinate [m] | End Coordinate [m] | Radius [m] |
|---|---|---|---|
| refino_lanca_01 | 0,5750 · −0,4400 · −5,800 | 0,5750 · −0,4400 · −5,300 | 0,100 |
| refino_lanca_02 | 0,3159 · −0,0834 · −5,800 | 0,3159 · −0,0834 · −5,300 | 0,100 |
| refino_lanca_03 | −0,1034 · −0,2196 · −5,800 | −0,1034 · −0,2196 · −5,300 | 0,100 |
| refino_lanca_04 | −0,1034 · −0,6604 · −5,800 | −0,1034 · −0,6604 · −5,300 | 0,100 |
| refino_lanca_05 | 0,3159 · −0,7966 · −5,800 | 0,3159 · −0,7966 · −5,300 | 0,100 |
| refino_lanca_06 | 0,9388 · −0,2231 · −5,010 | 0,9388 · −0,2231 · −4,510 | 0,100 |
| refino_lanca_07 | 0,7042 · 0,1419 · −5,010 | 0,7042 · 0,1419 · −4,510 | 0,100 |
| refino_lanca_08 | 0,3096 · 0,3222 · −5,010 | 0,3096 · 0,3222 · −4,510 | 0,100 |
| refino_lanca_09 | −0,1199 · 0,2604 · −5,010 | −0,1199 · 0,2604 · −4,510 | 0,100 |
| refino_lanca_10 | −0,4478 · −0,0237 · −5,010 | −0,4478 · −0,0237 · −4,510 | 0,100 |
| refino_lanca_11 | −0,5700 · −0,4400 · −5,010 | −0,5700 · −0,4400 · −4,510 | 0,100 |
| refino_lanca_12 | −0,4478 · −0,8563 · −5,010 | −0,4478 · −0,8563 · −4,510 | 0,100 |
| refino_lanca_13 | −0,1199 · −1,1404 · −5,010 | −0,1199 · −1,1404 · −4,510 | 0,100 |
| refino_lanca_14 | 0,3096 · −1,2022 · −5,010 | 0,3096 · −1,2022 · −4,510 | 0,100 |
| refino_lanca_15 | 0,7042 · −1,0219 · −5,010 | 0,7042 · −1,0219 · −4,510 | 0,100 |
| refino_lanca_16 | 0,9388 · −0,6569 · −5,010 | 0,9388 · −0,6569 · −4,510 | 0,100 |

Os cilindros do anel externo ultrapassam a parede do cone; isso é irrelevante,
o mesher só usa a interseção com o domínio.

## 3. Receita de malha

**Trimmed Cell Mesher** — os 16 jatos são exatamente paralelos a z, então a célula
hexaédrica alinha com o escoamento e a difusão numérica cai. Poliédrica aqui só
gastaria célula.

| item | valor | por quê |
|---|---|---|
| Base Size | **40 mm** | 51 células no diâmetro do aerador |
| Volumetric Control (16 cilindros) | **10 mm** = 25 % da base | 2 níveis exatos do trimmer · 6,3 células no injetor |
| Custom Surface Size em `aerador.injetores` e `aerador.lancas` | target 8 mm, min 4 mm | o disco de Ø62,7 tem que fechar redondo |
| Surface Growth Rate | 1,2 | |
| Prism Layer | **2 camadas**, 12 mm total, stretch 1,5 | Re = 9,5 — não há y+ a perseguir |
| Prism Layer em `aerador.topo` | **desligado** | é outlet, não parede |

### Orçamento de células

| zona | volume | tamanho | células |
|---|---|---|---|
| refino dos injetores | 0,251 m³ | 10 mm | ~251 k |
| transição (automática do trimmer) | — | 20 mm | ~150 k |
| restante | 19,74 m³ | 40 mm | ~308 k |
| **total estimado** | 19,99 m³ | | **~0,7–0,8 M** |

Malha de transiente multifásico Euleriano perfeitamente rodável. Se quiser apertar,
8 mm no refino leva a ~1,0 M (7,8 células no injetor); acima disso não compra nada,
porque a física está limitada por Re = 9,5, não por resolução.

## 4. Passo de tempo

Com v = 0,731 m/s e célula de 10 mm, CFL = 1 exige Δt = 1,4e−2 s. O tempo de
residência é **9,2 min** (19,99 m³ ÷ 130 m³/h). Rodar até regime permanente em
transiente custaria ~40 000 passos a CFL 1.

Recomendação: **steady primeiro** (é laminar e o escoamento é bem-comportado),
e transiente só se for preciso mostrar o transitório de enchimento. Δt = 5e−3 s
com 5 inner iterations se for para transiente.
