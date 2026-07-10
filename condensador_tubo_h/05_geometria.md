# 05 — Geometria (domínio 2D paramétrico)

## Conceito
Corte transversal 2D: um **tubo circular (parede fria)** imerso num **campo de vapor**, gravidade
apontando para baixo. O condensado forma um filme sobre o tubo e **escorre/desprende pela base**.
Domínio retangular ao redor do tubo, com entrada de vapor e saída.

```
        vapor (T_sat) entra
      ┌───────────────────────┐
      │        ( tubo )        │   ← parede fria T_wall < T_sat
      │       filme drena      │   g ↓
      └───────────────────────┘
             saída (condensado + vapor)
```

## Parâmetros — ✅ FIXADOS (geometria construída)
- `D_tubo` = **25,4 mm (1")** — padrão de condensador e na escala do experimento de validação.
- `W = H` = **254 mm (10·D)** — domínio amplo, sem confinar o filme/vapor.
- tubo centrado em **y = +30,5 mm** (0,12·H acima do meio) → espaço de drenagem embaixo.
- Ponto de operação: **T_sat = 100 °C (1 atm), ΔT = 25 K → T_parede = 75 °C** (ancorado no
  experimental ~26 K).
- Arquivo gerado: **`condenser_tube_2D.step`** (slab fino 1 mm p/ Convert to 2D no STAR).
- refino de parede: o filme é fino (dezenas–centenas de µm) → **prism layers finas** no tubo
  (resolver o filme é o que dá o `h`).

## Construção
- Reaproveitar o pipeline **cadquery** já validado (usado nos projetos sugar/cerveja).
- 2D: construir a seção, garantir alinhamento X-Y e fronteira em Z=0, e usar **Convert to 2D** no
  STAR (como no tutorial).
- Alternativa: como é um corte simples (retângulo − círculo), dá para gerar direto a superfície 2D.

## Nota de malha (o ponto crítico do estudo)
Resolver o filme de condensado exige **malha finíssima junto ao tubo** (célula ≪ espessura do
filme). Por isso:
- Prism layers com primeira célula de poucos µm no tubo;
- possivelmente **2D** (já é) para manter o custo viável;
- checar independência de malha via o **Specified y+ HTC** e refinamento sucessivo.

> Construo o `.step`/superfície assim que a revisão de literatura fixar `D_tubo`, `T_sat` e `ΔT`
> (para casar com um dataset de validação).
