# 08 — Resultado, lições e fechamento (o `h` de condensação na prática)

> **Fechamento do estudo (2026-07-12).** Estudo conduzido em 2D, com objetivo de **prever o `h`
> de condensação filmwise** e confrontá-lo com Nusselt. Este documento consolida o que funcionou,
> o que falhou, **por quê**, e a lição para projeto. É também a base da narrativa de divulgação
> (LinkedIn) — o ponto do estudo é justamente mostrar **como é difícil prever o `h` com precisão**
> em mudança de fase.

## O caso
Tubo horizontal Ø25,4 mm, parede fria a **75 °C**, imerso em vapor saturado a **100 °C** (1 atm),
ΔT = 25 K. Domínio 2D 254×254 mm, gravidade para baixo. Alvo teórico:

- **Nusselt (1916), tubo limpo:** `h ≈ 9,7 kW/m²·K` (q″ ≈ 243 kW/m²), filme δ ≈ 69 µm, Re_filme ≈ 103 (laminar).
- **Experimental (vapor atmosférico, tubo horizontal, literatura):** `h ≈ 5,5 kW/m²·K` — já **abaixo**
  de Nusselt (assinatura provável de NCG/ar residual em bancada real).

## A jornada (as três armadilhas do `h`)

### Armadilha 1 — o modelo "óbvio" não condensa vapor puro
Primeiro modelo ligado: **VOF Evaporation/Condensation** (o padrão). Ele é **limitado por difusão**:
a taxa de mudança de fase depende do gradiente de espécie junto à interface (equilíbrio de Raoult).
Em **vapor puro** não há gradiente de espécie → **não condensa**. O que se observou foi apenas
**condução transiente** (q″ decaindo com ~1/√t), sem filme. 

> **Lição de projeto:** o nome do modelo ("Evaporation/Condensation") não garante que ele modele
> o *seu* regime. Modelo difusivo serve para condensação **na presença de incondensável**; para
> **vapor saturado puro** ele é o modelo errado. Rodar dias e entregar um `h` que na verdade é só
> condução é uma falha silenciosa — não há erro na tela.

### Armadilha 2 — modelo certo, `h` ainda 4× abaixo
Troca para o modelo correto: **Fluid Film com *Thermal Limitation*** (regime saturado/limitado por
condução no filme) + **Shell Region** no tubo + densidade de nucleação. Aí **condensou de verdade**,
formou filme e saiu um `h`. Resultado:

| Grandeza | Nusselt | Experimental | **CFD 2D (este estudo)** |
|---|---|---|---|
| `h` médio | 9,7 kW/m²·K | ~5,5 kW/m²·K | **2,29 kW/m²·K** |
| Espessura do filme | ~69 µm | — | **~294 µm (~4×)** |

O `h` médio ficou **~4× abaixo de Nusselt** e ~2,4× abaixo do experimental. O modelo não estava
"errado" — o filme estava **acumulando**.

### Armadilha 3 — o achado: o `h` está amarrado ao **dreno**, e o dreno é 3D
O filme engrossou ~4× porque **o condensado não tem por onde escorrer num tubo liso em 2D**:
- **Gotejar** (dripping) é um fenômeno **tridimensional** governado por **tensão superficial** —
  a gota cresce na geratriz inferior e se destaca *na direção do eixo do tubo*, que **não existe
  no corte 2D**.
- **Edge Stripping** (o mecanismo do STAR para arrancar filme de uma quina) exige um **canto
  geométrico** (Minimum Corner Angle ~10°) — o tubo é liso, não tem quina.
- As saídas de borda da shell são as **bordas frontal/traseira** (direção Z), não a base do tubo.

Ou seja: **em 2D não existe caminho físico de drenagem para o condensado do tubo.** O filme só pode
engrossar, e um filme grosso ⇒ `h = k/δ` baixo. **A física do `h` está acoplada à física do dreno**,
e essa física não cabe num corte 2D.

## O que foi de fato validado (honestamente)
- ✅ **Forma do `h(θ)`**: o perfil angular reproduz Nusselt — **`h` alto no topo** (filme fino) e
  **baixo na base** (filme acumulado). A física local está certa.
- ✅ **`h` local no topo (~9–12 kW/m²·K)** **enquadra o Nusselt** (9,7) — onde o filme é fino, o
  número bate.
- ⚠️ **`h` médio (2,29 kW/m²·K)** **não** bate: é dominado pela base inundada, artefato da
  impossibilidade de dreno em 2D. **Quantitativo comprometido pela dimensionalidade.**

## Veredito
O CFD **acerta a física e a forma** do `h`, mas o **número médio exige 3D** (uma fatia fina do
tubo onde a gota efetivamente goteja). A conclusão que interessa ao projetista:

> **Prever o `h` de condensação com precisão é genuinamente difícil.** Três armadilhas — (1) modelo
> difusivo vs térmico, (2) resolução do filme, (3) a **dimensionalidade do dreno** — cada uma
> entrega, sozinha, um `h` **confiante e errado**. O `h` "de tabela" esconde todas as três.

## Encaminhamento
- **Fechado em 2D** para fins de divulgação: validação **qualitativa** (forma + topo) + a
  **limitação 2D** como a lição central.
- **Caminho para o número** (trabalho futuro, se necessário): **fatia 3D** do tubo → o dreno
  ocorre → `h` médio deve convergir para Nusselt; depois **injetar NCG** e medir a queda rumo aos
  ~5,5 kW/m²·K experimentais (a assinatura industrial do gás não-condensável).

## Parâmetros do caso (registro)
- Água a T_f = 87,5 °C: ρ_l = 967, μ_l = 3,24e-4, k_l = 0,673, c_pl = 4205.
- Vapor a 100 °C: ρ_v = 0,598, h_fg = 2257 kJ/kg.
- Modelo final: Fluid Film + Thermal Limitation + Shell Region; URF da taxa 0,3–0,5;
  Linearize Film/Gas Energy Source ligados (estabilidade).
