# STATUS — Projeto Sugar (Ito) · onde paramos

> Nota de recall. Última atualização: 2026-07-14 (noite). **Apresentação ao Ito ENTREGUE — feedback positivo.**
> **Fase 2 em execução.** Próximo (15/07): **malhar + rodar o impelidor novo** (steady MRF) → torque.
> Ver `fase2/` e `fase2/impelidor_parametrico/execucao_star.md`.

## Estado geral
- **REATOR — 100% FECHADO.** Nq=0,345 · Np/est=0,76 · P=4,07 kW (rodada dedicada steady MRF).
- **AERADOR — sweep de pressão 1/2/3 kgf/cm² COMPLETO.** Conclusão blindada com 3 pontos:
  **a pressão NÃO é a alavanca.**
- **APRESENTAÇÃO AO ITO — ENTREGUE (14/07), feedback positivo.** Fabricante alega bolha 5 µm no
  nascimento vs CFD ~1,2 mm (física de formação em meio viscoso — reforça a conclusão).
- **FASE 2 — em execução:**
  - **Impelidor novo** Ø880/31,5°/4pás/120,2 rpm — ✅ **RODADO (16/07):** T=−786,6 N·m → **P=9,90 kW** (2,43× a
    base 4,07; dentro da meta <25 kW), Np/est~0,86. **Falta só o Nq** (report de vazão). Ver `execucao_star.md`.
  - **Ejetor** (venturi): metodologia fechada e verificada. Vazão motriz **130 m³/h confirmada** (Ito) → v_bico
    20–27 m/s, ainda laminar. Falta **σ ar-xarope** (Gabriel busca correlação de xarope de cana).

## Conclusão central do Aerador (o recado pro Ito)
Triplicar a pressão (1→3 kgf/cm²) não muda o essencial: bolha ~2,4–2,5 mm (**~12× a meta** de
200 µm e ~6–12× o floco), **fração flotável ~0** nos três, **zero dispersão**. A pressão só
**espalha** a distribuição (D10 desce, D90 sobe, std +37%) e até **engrossa** a bolha média.

**Causa-raiz:** breakup **suprimido** pela viscosidade (6,5 Pa·s) — a viscosidade resiste à quebra
(e *inibe* coalescência; o tamanho grande vem da falta de quebra, não do excesso de fusão).

**Alavanca real (recomendação):** (a) reduzir a viscosidade (temperatura/diluição) e/ou
(b) aumentar o cisalhamento na formação (geometria do injetor / venturi). **Pressão não.**

## Números do sweep (fonte: `simulacao/sweep_pressao_3casos.csv`)
| | 1 kgf | 2 kgf | 3 kgf |
|---|---|---|---|
| SMD médio (mm) | 2,392 | 2,437 | 2,526 |
| D10 / D90 (mm) | 1,67 / 3,16 | 1,49 / 3,53 | 1,43 / 3,57 |
| flotável <200µm | ~0 (3,4e-6%) | ~0 (1,3e-6%) | ~0 (9,8e-7%) |
| holdup de gás | 0,005% | 0,006% (0,0057) | 0,007% (0,0073) |
| estado | ✅ conv. (~31s) | ⚠️ quase (~38s) | ⚠️ quase (~35s) |

> **Holdup** = Volume Average de `Volume Fraction of Ar` em `Dominio.Aerador` (× 100). Praticamente
> plano nos três (ar confinado às lanças; pressão quase não mexe). Figuras do slide 6 completas:
> `apresentacao/hist_bolha_caso{1,2,3}.png` + `apresentacao/cards_caso{2,3}.png`.

## Onde está cada coisa
- **Relatório completo:** `relatorio_tecnico_preliminar.md`
- **Dados brutos:** `simulacao/caso{1,2,3}_*/` + `simulacao/sweep_pressao_3casos.csv`
- **Figuras p/ o deck:** `apresentacao/sweep_pressao_3curvas*.png`, `apresentacao/tabela_sweep_3casos.png`
- **Texto de slides:** `apresentacao/conteudo_parte2_aerador.md`
- **Deck:** `apresentacao/Projeto_Sugar_Aerador_Reator.pptx`

## Pendências (nenhuma bloqueia a apresentação)
- (Opcional) Convergir 100% os casos 2 e 3 (probe perto-injetor ainda desacelera) p/ cravar deltas finos.
- Refresh dos Artifacts HTML pros 3 casos (o `.html` do scratchpad é efêmero; reconstruir se precisar).
- Slide de diagnóstico: conferir que a linha "Raiz física comum" foi trocada (viscosidade **suprime
  breakup**, não "favorece coalescência") e o "8× o floco" → "~6–12×".

## Verificação
Conclusões submetidas a revisão adversarial (4 lentes + crítico de completude). Correções já
aplicadas no relatório: mecanismo (breakup suprimido), múltiplo 12× (não 8×), foco na cauda/D10.
