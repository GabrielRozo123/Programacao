# Projeto Cerveja — Tanque Chiller (GreyLogix)

Estudo CFD de **estratificação térmica** em tanque de solução hidroalcoólica resfriada por
chiller. Cliente **GreyLogix** (via CAEXPERTS). Este repositório organiza o **novo cenário**
solicitado (reposicionamento de bocal + recirculação), separado do estudo preliminar já entregue.

> **Status (2026-07-08):** aguardando confirmações do cliente (via Pedro) para travar geometria
> e bocais do novo cenário. Método e dados de processo já consolidados. Geometria-base do tanque
> de 3.500 L já modelada (paramétrica). Ver `05_pendencias_e_perguntas.md`.

## Índice
| Doc | Conteúdo |
|---|---|
| [`01_contexto.md`](01_contexto.md) | Cliente, estudo preliminar (as-built), novo pedido, e a questão dos **dois tanques** |
| [`02_cenario_novo.md`](02_cenario_novo.md) | Especificação do novo cenário: baseline + 2 casos, objetivo, entregável |
| [`03_dados_processo.md`](03_dados_processo.md) | Fluido, condições de contorno e lógica de controle (do e-mail do cliente) |
| [`04_metodo_cfd.md`](04_metodo_cfd.md) | Modelos físicos + **como modelar a bomba de recirc sem malhá-la** |
| [`05_pendencias_e_perguntas.md`](05_pendencias_e_perguntas.md) | Perguntas ao cliente + log de respostas (preencher conforme chegam) |
| [`geometria/`](geometria/) | Modelo paramétrico do tanque TAG 3.500 L + `.step` + esquemático |
| [`referencias/`](referencias/) | Croquis, desenhos e medições de referência |

## Resumo em uma frase
O preliminar (tanque grande, ~69 m³) mostrou que há **estratificação significativa**; o novo
cenário avalia, no **tanque TAG 3.500 L**, se **subir a sucção do chiller (0,85 → 1,35 m)** e/ou
**adicionar uma bomba de recirculação (12 m³/h)** reduzem essa estratificação.

## Como este repositório é mantido
As informações chegam do cliente em lotes (via Pedro). Cada dado novo é registrado em
`05_pendencias_e_perguntas.md` (log datado) e propagado para o doc temático correspondente
(02/03/04) e para o script paramétrico de geometria. Nada é assumido silenciosamente:
suposições ficam marcadas como **[SUPOSTO]** até confirmação.
