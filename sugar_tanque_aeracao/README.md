# [Sugar] — Tanque de Aeração + Tanques Reator A/B + Ejetor

> Novo projeto (kick-off 2026-07-01). Setor sucroalcooleiro ("Sugar" = codinome do cliente).
> Estudo a definir no kick-off — provável CFD de aeração/mistura gás-líquido em tanques
> com ejetores. Atualizado: 2026-06-30.

---

## Contatos
| Papel | Pessoa |
|---|---|
| Engenheiro externo (enviou arquivos) | **Jadir Batista** — JSA Consultoria e Projeto |
| Contato cliente / interlocutor | **Marcos Eduardo Katsuda Ito** (Marcus Ito) |
| CAExperts | **Marcus Castro Neves**, **Gabriel Rozo** |

## Kick-off
- **2026-07-01, 08:00–08:30** (Microsoft Teams) — "[Sugar] - Kick off Tanque de Aeração"

## Arquivos recebidos (e-mail Jadir Batista, JSA — "Tanques de reação, aeração e Ejetor")
Anexos a importar para `dados_cliente/` (são do e-mail, ainda não no repo):
- `Conjunto de Tanques Reator A e B e Tanque Aerador.iges`
- `Tanques Reação A e B e tanque Aerador.dwg`
- `Conjunto Ejetor.iges`
- `Conjunto Ejetor.dwg`

## Escopo (a confirmar no kick-off)
Sistema com **2 tanques reatores (A e B)** + **1 tanque aerador** + **ejetor(es)**.
Hipótese técnica (a validar): estudo CFD de **aeração/mistura gás-líquido** — o ejetor
injeta ar/gás no líquido (jet aeration / venturi), e o interesse provável é:
- eficiência de mistura / tempo de homogeneização
- transferência de O₂ (oxigenação) ou de gás
- zonas mortas / recirculação
- desempenho do ejetor (vazão induzida, dispersão de bolhas)

## Dados necessários (perguntar no kick-off)
- Objetivo do estudo (o que querem responder/otimizar?)
- Geometria: dimensões dos tanques (CAD ajuda), posição/quantidade de ejetores
- Fluido: água? mosto/caldo? viscosidade, densidade
- Ejetor: vazão de líquido motriz, vazão de ar/gás induzida, pressão, diâmetro do bocal
- Condições de operação: nível de líquido, temperatura, vazões de entrada/saída
- Regime: contínuo ou batelada? aeração contínua?
- Entregável esperado e prazo

## Status
- [x] Arquivos recebidos (Jadir/JSA) — importar CAD para `dados_cliente/`
- [ ] Kick-off 01/07 com Marcus Ito — definir escopo, objetivo, dados
- [ ] Revisão de literatura (jet aeration / ejetor / mistura em tanques)
- [ ] Proposta comercial (modelo CAExperts)
