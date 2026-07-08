# Parte 2 — Aerador · conteúdo pronto pra colar no PPTX
> Valores verificados (revisão adversarial de 4 lentes + crítico de completude). Caso 2 é **provisório** (não estacionário).

---

## SLIDE — Comparação de Pressão: 1 vs 2 kgf/cm²
**Kicker:** RESULTADOS · AERADOR — COMPARAÇÃO DE PRESSÃO

**Tabela (cole como tabela):**

| Métrica | 1 kgf/cm² | 2 kgf/cm² |
|---|---|---|
| Estado | ✅ convergido (~31s) | ⚠️ provisório (~38s) |
| SMD médio (domínio) | 2,39 mm | 2,44 mm* |
| Moda (pico) | 2,16 mm | 1,86 mm |
| D10 (ponta pequena) | 1,67 mm | 1,49 mm |
| D90 (cauda) | 3,16 mm | 3,53 mm |
| Fração < 200 µm (meta) | ≈ 0 % | ≈ 0 % |
| Dispersão (meio/topo) | nula | nula |

\* *indicativo — caso 2 ainda não estacionário*

**Frase-chave (caixa de destaque):**
> Dobrar a pressão **reestrutura** a distribuição (a ponta pequena desce, a cauda engorda) mas **não desloca a média nem gera bolha flotável**. A fração < 200 µm segue ≈ 0 % nos dois casos.

---

## SLIDE — Diagnóstico: por que a bolha é grande
**Kicker:** DIAGNÓSTICO · CAUSA-RAIZ

**1 · Bolha ~12× a meta**
- Bolha típica ~2,4 mm = **~12× a meta de 200 µm** e **~6–12× o floco (200–400 µm)**
- Até o D10 (~1,5 mm) é ~7–8× a meta
- Requisito do processo: bolha **menor** que o floco p/ aderir e flotar — aqui é o oposto

**2 · Gargalo = breakup SUPRIMIDO (não coalescência)**
- Viscosidade 6,5 Pa·s **resiste à deformação** → exige cisalhamento muito maior p/ quebrar
- Bulk de baixa turbulência → bolha travada no tamanho de formação do orifício
- *(A viscosidade inibe coalescência via drenagem lenta de filme; o problema é falta de quebra, não excesso de fusão)*

**3 · Sem dispersão**
- Re da pluma baixíssimo em 6,5 Pa·s → jato não gera circulação de tanque
- Ar confinado aos injetores, sem varrer o volume dos flocos

---

## SLIDE — Conclusão & Recomendação
**Kicker:** CONCLUSÃO · AERADOR

**Caixa central:**
> **A pressão de injeção NÃO é a alavanca.** Entre 1 e 2 kgf/cm² a bolha continua ~2,4 mm, a fração flotável ~0 % e o ar confinado aos injetores. Um gap de ~12× não se fecha com pressão.

**A alavanca real (recomendação de engenharia):**
- **(a) Reduzir a viscosidade** — temperatura / diluição do xarope
- **(b) Aumentar o cisalhamento na formação** — geometria do injetor / venturi

**Próximos passos:**
- Convergir o caso 2 (rodar até o SMD perto-injetor achatar) p/ fechar os deltas
- Caso 3 (3 kgf/cm²): baixa prioridade — extrapola o mesmo comportamento
- Verificar resolução de malha near-injector + convergência em Δt

**Ressalvas (rodapé pequeno):**
Caso 2 provisório (não estacionário); Δt=0,01 s, 1ª ordem, sem estudo de convergência em passo de tempo; "sem dispersão" observado até a parada.
