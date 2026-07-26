# 11 — A LEI MESTRA: pressão e velocidade são a MESMA condição

> Unifica as duas leituras que usamos até aqui. Fecha o diagnóstico do ejetor numa desigualdade só.

## A equação
No trecho de 4" a perda de carga é desprezível, então **a pressão na entrada de ar ≈ pressão de descarga
da bomba**. E essa pressão é ditada pela resistência do bico (laminar, Hagen-Poiseuille):

```
P_garganta = k · v_xarope           k = 128·µ·L·(A_4/N) / (π·D⁴)

   bico 7×Ø9  (instalado)   :  P[bar] = 21,3 · v[m/s]     → a 1,10 m/s = 23,5 bar
   bico 4×Ø15 (desenho novo):  P[bar] =  4,8 · v[m/s]     → a 1,10 m/s =  5,3 bar
```

## As duas leituras são a MESMA desigualdade
```
"o ar entra se v_xarope < v_corte"    ⟺    "o ar entra se P_ar > P_bomba"
                              ambas são:   P_ar > k · v_xarope
```

| Bico | v_corte @1 kgf | @2 kgf | @3 kgf |
|---|---|---|---|
| 7×Ø9 | 46 mm/s | 92 | 138 |
| 4×Ø15 | 203 mm/s | 405 | 608 |

*(projeto = 1100 mm/s → 8× a 24× acima de qualquer corte)*

## A diferença é só QUEM é a variável independente
| | variável imposta | resultado |
|---|---|---|
| **No nosso CFD** | v_xarope (Velocity Inlet) | a pressão saiu (23,5 bar) |
| **Na planta real** | a **curva da bomba** | o cruzamento define **v E P juntos** |

> ⚠️ **A lacuna:** impor a vazão faz o solver "inventar" a pressão necessária. Se a bomba não faz 24 bar,
> **esse ponto de operação não existe** — a vazão real é menor e a pressão também.
> **A pressão da bomba diz ONDE, na reta, o sistema realmente opera.**

## Os 2 dados que faltam (e fecham tudo)
1. **Pressão de descarga da bomba do ejetor** (bar / modelo / curva) — nunca informada; os 23,5 bar são
   dedução circular (saem de impormos os 130 m³/h).
2. **Pressão do ar QUE ALIMENTA O EJETOR** — os 1/2/3 kgf vêm da **Fase 1 (aerador)**. Marcus disse
   "*provavelmente* soprador". Se o ejetor tiver compressor de 6–7 bar, o quadro muda.

**Com esses dois números o diagnóstico fecha em 5 minutos, sem rodar mais CFD.**

## Figura
`lei_mestra_P_vs_v.png` — as duas retas (7×Ø9 e 4×Ø15), as linhas de ar 1/2/3 kgf, e o ponto de projeto.
**O ar entra onde a reta do bico passa ABAIXO da linha do ar.**
