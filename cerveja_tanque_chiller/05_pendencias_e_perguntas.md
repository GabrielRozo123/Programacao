# 05 — Pendências e perguntas (documento vivo)

> Preencher a coluna **Resposta** conforme o cliente/Pedro retornar. Cada resposta deve ser
> propagada para o doc temático (02/03/04) e para o script paramétrico de geometria.

## Perguntas ao cliente (via Pedro) — ✅ RESPONDIDAS (16/07, diagrama EGISA 055.2254 + Gustavo)

| # | Pergunta | Status | Resposta |
|---|---|---|---|
| 1 | Baseline no **TAG 3.500 L** (não no ~69 m³)? Altura de líquido? | ✅ | **Sim, TAG 3.500 L** (Ø1659mm, EGISA 055.2254). **Altura de líquido = 1,53 m** do início da parede cilíndrica (ref. "0"). |
| 2 | Altura da **sucção ao chiller** (original ~0,85 m) e do **retorno**. DN. | 🟡 parcial | Sucção original **0,85 m** (confirmado, riscada no diagrama). **Retorno do chiller = no FUNDO** (junto à ref. 0). **⚠️ DN dos bocais ainda NÃO informado no diagrama.** |
| 3 | Nova sucção em **1,35 m** (mesmo DN)? Retorno permanece? | ✅ | **Sucção sobe para 1,35 m** (~50 cm acima). **Retorno permanece no fundo.** Mesmo DN. |
| 4 | **Recirc:** alturas de captação/retorno; DN; soma aos 12 do chiller? | ✅ (DN 🟡) | **Captação no FUNDO, retorno no TOPO**, **12 m³/h**. É um **2º circuito** (Gustavo: "segundo circuito de recirculação") → **somam** (2 bombas: 12 chiller + 12 recirc). **DN a confirmar.** |
| 5 | Condições de processo do e-mail original? | 🟡 assumir | Não re-informadas → **manter** as do e-mail original (70/30; entrada −5 °C; inicial +5 °C; 12 m³/h; iso 100 mm; chiller desliga a −5 °C). Confirmar se mudou. |
| 6 | Métrica do entregável? | 🟡 inferido | Objetivo: **"redução da estratificação" / "homogeneização da temperatura"** → métrica = **ΔT topo–fundo no tempo** (+ perfil vertical). Confirmar formato preferido. |

## ✅ AS DUAS SIMULAÇÕES DEFINIDAS (Gustavo via Pedro)
1. **Sim 1 — Baseline modificado:** igual ao preliminar, **só subindo a sucção do chiller de 0,85 → 1,35 m**
   (retorno do chiller fica no fundo). Objetivo: ver se reduz a estratificação.
2. **Sim 2 — Recirculação adicional:** sucção já em 1,35 m **+ 2º circuito de recirc** (bomba **12 m³/h**,
   **captação no fundo, retorno no topo**). Objetivo: ver o impacto na homogeneização.

Alturas (ref. "0" = início da parede cilíndrica, do diagrama EGISA):
- Líquido: **1,53 m** · Sucção chiller nova: **1,35 m** (antiga 0,85 m) · Retorno chiller: **fundo (~0)** ·
  Recirc: captação **fundo**, retorno **topo**.

## ⏳ Único pendente relevante: **DN dos bocais**
O diagrama não traz o DN dos bocais (sucção/retorno do chiller e da recirc). O **DN define a velocidade de
jato** → a mistura. **Pedir ao Pedro/EGISA.** Enquanto isso, adotar um DN típico [SUPOSTO] e marcar.

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
- **2026-07-16** — **Respostas recebidas** (Pedro/Gustavo + diagrama EGISA 055.2254). **2 simulações
  definidas** (Sim 1: sucção 0,85→1,35 m; Sim 2: + recirc 12 m³/h captação fundo/retorno topo). Alturas
  confirmadas (líquido 1,53 · sucção 1,35 · retorno chiller fundo · recirc fundo→topo). Geometria
  paramétrica atualizada com os 5 bocais (3.510 L). **Único pendente: DN dos bocais** (pedir à EGISA/Pedro).
