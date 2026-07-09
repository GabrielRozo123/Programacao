# Condensação Filmwise em Tubo — Previsão do coeficiente **h** (CFD industrial)

Estudo CFD de **condensação filmwise** de vapor num tubo horizontal frio, com foco em
**prever o coeficiente de transferência de calor `h`** — a grandeza que projetos de mudança de
fase frequentemente subestimam ou ignoram. Ferramenta: Simcenter STAR-CCM+ (VOF + mudança de fase).

> **Status (2026-07-09):** repositório aberto. Setup e método definidos a partir do tutorial de
> ebulição (adaptado para condensação). **Pendente:** travar o modelo de condensação (aguardando a
> lista de opções do STAR), o fluido/material e o ponto de operação. Ver `06_pendencias.md`.

## A tese em uma frase
CFD **prevê o `h` de condensação** (local e médio), validável contra a teoria de Nusselt no tubo
limpo — e, diferente da tabela de projeto, **captura a degradação industrial** do `h`
(gás não-condensável, inundação). O `h` correto é `h = q″ / (T_sat − T_parede)`.

## Índice
| Doc | Conteúdo |
|---|---|
| [`01_contexto_e_objetivo.md`](01_contexto_e_objetivo.md) | Motivação (h ignorado), objetivo, o que há de inédito |
| [`02_fisica_e_metodo.md`](02_fisica_e_metodo.md) | VOF mudança de fase, virada ebulição→condensação, **definição do h** |
| [`03_setup_star.md`](03_setup_star.md) | O scaffold do tutorial (todos os settings) adaptado p/ condensação |
| [`04_validacao_nusselt.md`](04_validacao_nusselt.md) | Teoria de Nusselt, o `h` alvo, plano de validação |
| [`05_geometria.md`](05_geometria.md) | Domínio 2D paramétrico (tubo frio no campo de vapor) |
| [`06_pendencias.md`](06_pendencias.md) | Decisões abertas + log (documento vivo) |
| [`referencias/`](referencias/) | Resumos de literatura e da documentação STAR (sem PDFs proprietários) |

## Abordagem
**Direto industrial** (materiais e condições reais), com o **instante de tubo limpo** da própria
rodada servindo de **checagem contra Nusselt** — rigor sem desvio acadêmico. Depois: degradação
por NCG (flagship) e, se escalar para banco de tubos, o modelo de filme fino (Fluid Film).
