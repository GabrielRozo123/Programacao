# Petrobras — Processo de Coqueamento (Refinaria Abreu e Lima / RNEST)

Cliente: **Petrobras** (contato Engº João Rui; e-mail via João Rui Barbosa de Alencar → Ricardo
Barros; cc Marcus Castro Neves, Gabriel Rozo). Dois cronogramas propostos, **dois estudos independentes**.

> **Status (2026-07-13):** reunião de aprofundamento hoje **13h**. Fase de *entendimento do problema*
> e escopo do CFD. Nada modelado ainda. Nosso escopo é **CFD** (o FEA fica com outro setor da CAEXPERTS).

## Os dois estudos
| # | Estudo | Nosso papel | Método | Valor | Prazo |
|---|---|---|---|---|---|
| 1 | **Resfriador — empenamento dos tubos** | **CFD** (escoamento + transf. de calor → exporta campo térmico p/ FEA) | STAR-CCM+ CHT | R$ 46.567 | 63 dias |
| 2 | **Fluxo de coque — entupimento no fundo do forno** | **DEM** (escoamento do coque, causas da obstrução, melhorias) | STAR-CCM+ DEM | R$ 34.917 | 56 dias |

## Pastas
- [`resfriador/`](resfriador/) — o estudo CFD do resfriador. Ver [`00_briefing_reuniao.md`](resfriador/00_briefing_reuniao.md).
- [`fluxo_coque/`](fluxo_coque/) — o estudo DEM (mesmo ferramental do Braskem PE5).

## Sinergias com o que já temos
- **Resfriador (CFD térmico):** se houver **condensação/vaporização** no resfriador, cai direto no
  que acabamos de estudar no `condensador_tubo_h` (previsão de `h` em mudança de fase).
- **Fluxo de coque (DEM):** mesmo motor DEM do **`braskem_pe5`** (screw conveyor / embuchamento) —
  calibração de partícula, escoamento granular, obstrução. Reaproveita metodologia.

## Log
- **2026-07-13** — Repo aberto. Dois cronogramas recebidos (e-mail João Rui). Briefing da reunião
  das 13h montado para o resfriador (nosso foco imediato). FEA fora do nosso escopo.
