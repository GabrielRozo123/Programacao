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
  - **Impelidor novo** Ø880/31,5°/4pás/120,2 rpm — ✅ **FECHADO (Nq convergido 21/07):** P=**9,90 kW** (2,43× base,
    40% do orçamento de 25 kW ✅) · **Nq=0,32** · Np/est~0,86 · **bombeamento +37%** (1.588 vs 1.158 m³/h) →
    mistura ~27% mais rápida. Upgrade **viável** (cabe no motor com folga). Ver `impelidor_parametrico/tabela_final_impelidor.md`.
  - **Ejetor** (venturi) — **Trilho 1 (analítico) FECHADO; Trilho 2 (CFD) espera geometria nova.** Ver
    **`ejetor/00_RESUMO_EJETOR.md`** (índice). Núcleo: laminar (Re~40); λ→0 → só **extensão/atomização** quebra;
    **σ=0,058** (literatura); a "1,3–2 m/s" é o **tubo** (não a bolha); borbulhar→mm (Tate), **<300 µm exige
    JATEAMENTO** e o **ar supersônico já está nele**; **bolha↓ = jato↑** (d∝1/U) → furo menor/bico convergente
    (justificado por literatura). **Proposta do bico entregue.** Falta: **STEP/x_t nativo** + cotas finas (cadista Ito).

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
