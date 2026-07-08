# 05 — Pendências e perguntas (documento vivo)

> Preencher a coluna **Resposta** conforme o cliente/Pedro retornar. Cada resposta deve ser
> propagada para o doc temático (02/03/04) e para o script paramétrico de geometria.

## Perguntas ao cliente (via Pedro)

| # | Pergunta | Status | Resposta / data |
|---|---|---|---|
| 1 | **Geometria/baseline.** O novo cenário é no **TAG 3.500 L (Ø≈1,66 m)**, e não no tanque de ~69 m³ do preliminar? Confirmam que o **baseline (sucção a 0,85 m) será refeito neste tanque menor**? | ⏳ aguardando | — |
| 2 | **Bocais atuais (as-built do TAG 3.500 L).** DN e altura da **sucção ao chiller** (original ~0,85 m) e do **retorno do chiller**. | ⏳ aguardando | — |
| 3 | **Nova posição da sucção.** Confirmar sucção subindo para **1,35 m** (mesmo DN). O **retorno** permanece onde está? | ⏳ aguardando | — |
| 4 | **Recirculação.** Altura de **captação** e de **retorno** da bomba de 12 m³/h; **DN** dos bocais; e se os 12 m³/h **somam** aos 12 do chiller (duas bombas) ou é a mesma vazão. | ⏳ aguardando | — |
| 5 | **Condições de processo.** Seguem os dados do e-mail original (70/30; entrada −5 °C; inicial +5 °C; 12 m³/h; iso 100 mm; chiller desliga a −5 °C)? | ⏳ aguardando | — |
| 6 | **Entregável.** Métrica de estratificação: ΔT topo–fundo no tempo, tempo até homogeneizar, ou perfil vertical? | ⏳ aguardando | — |

## Suposições ativas (marcadas [SUPOSTO] nos docs) — validar quando possível
- Cone do fundo com altura ~0,27 m (ajuste para fechar 3.500 L ↔ 1,53 m no paramétrico → 3.510 L).
- DN dos bocais ainda indefinido (afeta a velocidade de jato e a mistura).
- Δt de produção a reavaliar para o tanque menor.

## Bloqueios
- **Geometria dos bocais** (posições + DN) trava o `.step` final e a definição das BCs.
- Sem a métrica (pergunta 6), o pós-processamento fica em aberto.

## O que já dá para adiantar sem o cliente
- [x] Geometria-base paramétrica do TAG 3.500 L (`geometria/`).
- [x] Método das BCs da recirculação documentado (`04_metodo_cfd.md`).
- [ ] Layout dos slides dos novos cenários (reaproveitando o bloco de física do slide 3).

## Log de recebimento de dados
> Registrar aqui, datado, cada lote de informação que chegar.

- **2026-07-08** — Repositório criado. Consolidados: contexto, dados de processo (e-mail original),
  método CFD e método da recirc. Geometria-base do TAG 3.500 L modelada. Perguntas 1–6 pendentes.
