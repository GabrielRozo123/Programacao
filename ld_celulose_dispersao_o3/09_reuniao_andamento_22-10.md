# 09 — Reunião de acompanhamento com a LD Celulose — 22/10/2026, 16h

> Material: **Relatório de andamento nº 1** (7 páginas, PDF). Como tem figuras da planta (layout, 3D), fica em
> `_privado/relatorio_22-10/LD_O3_relatorio_andamento_01.pdf` — **não vai para o GitHub** (repositório público).
> Fonte do PDF: `_privado/relatorio_22-10/relatorio_andamento_01.html` + `figuras.py` (regerar: Chromium → PDF).

## Pauta (≈ 30 min)
1. **Resumo e situação das etapas** (§1) — dados ✅, meteorologia ✅, geometria ✅, domínio e malha ✅, física 🟡.
2. **Limpeza do 3D** (§2): > 40 mil peças → 65 obstáculos + 4 descargas; critérios (COST 732, AIJ, Ricci 2017,
   Thakur 2009), zonas de detalhe, método (nomes → classificação → primitivas → volume de ar), verificações.
3. **Descargas dos exaustores** (§3): 910/920 horizontais, 930/940 verticais sob a cobertura — achado que não estava nos
   documentos e muda a pluma.
4. **Domínio de 16 lados e malha** (§4): uma malha para todos os cenários; 6,56 M células, 100 % válida.
5. **Como o vazamento entra** (§5): fonte nas descargas, traçador normalizado → vazão de O₃ só no pós; combinações por soma.
6. **Perguntas** (§6) — pedir prazo de resposta, priorizando **A1** (vazão de O₃) e **A2** (lógica dos exaustores).
7. **Próximos passos** (§7): física + teste do domínio vazio → caso base → 6 cenários.

## Perguntas entregues (texto completo em `03` e no PDF)
| # | tema |
|---|---|
| A1 | vazão de O₃ no vazamento (típica e pior caso) e % de O₃ na corrente |
| A2 | quais exaustores ligam, quando e com que lógica; quais operam continuamente |
| A3 | PSVs dos geradores: para dentro ou para fora; ajuste e vazão |
| A4 | desenhos CVC00P0015–P0018 e densidade de projeto das curvas |
| B5 | norte da estação × norte verdadeiro × norte de projeto; altura do anemômetro |
| B6 | uso do solo e topografia ~1 km |
| C7 | limiares instantâneos ou média em janela |
| C8 | pessoas, passarelas, salas de controle, tomadas de HVAC, sensores existentes |
| D9 | prédio das prensas aberto ou fechado |

## Registro da reunião (realizada em 26/10/2026, ~28 min; gravação transcrita, trechos com ruído)
| item | resposta / decisão |
|---|---|
| Geometria limpa | **Sem críticas** ("acho que tá tranquilo"). |
| Cronograma | Marcus registrou o impacto da exportação do CAD no prazo. |
| **Fonte nova: chaminé do off-gás** | Faltava no modelo. Recebe o alívio das **PSVs dos vasos/geradores**: descarga de **4"** que entra num coletor comum de **10"** e sobe até a chaminé; sai com pressão bem baixa (muita perda no caminho). |
| PSV | Vaso opera a ~9,5–19,5 bar (áudio ruim); PSV ajustada em ~12–12,8 bar, fecha a ~12,5 bar. Vazão difícil de medir (abertura parcial da válvula). |
| **Concentração no off-gás** | **~13 %** de O₃ (Gabriel confirma a leitura; unidade a confirmar: massa em O₂?), contra ~0,2 ppm nos exaustores. Volume pequeno, mas **muito mais concentrado** que os exaustores: maior potencial de risco segundo a LD. |
| Exaustores | Volume grande, concentração baixa (**~0,2 ppm**, ligam a partir do alarme). Proposta da LD: condição 1 = concentração mínima de acionamento × vazão dos exaustores. |
| Vazão do off-gás | Estimar pelo diâmetro da descarga da PSV (4"), do coletor (10") e pressão de ajuste, com hipótese de abertura da literatura (API 520/521). |
| Edifícios a oeste | Retângulo mais a oeste = **sala de controle (SDCD/DCS)**; o seguinte = **CCM** (quadros elétricos). **São receptores com pessoas.** |
| Histórico de eventos | Em vazamentos já perceberam O₃ **além do CCM**, chegando ao **segundo nível**. |
| Ação CAE | Enviar **print da vista de cima, sem perspectiva**; a LD marca a chaminé e os locais onde já houve eventos (para comparar com as direções de vento simuladas). |
| Ação LD | Mandar o print/posição da chaminé do off-gás (já mostraram um print na reunião). |


## Versão em PowerPoint (pedido do Marcus, 22/10)
`_privado/relatorio_22-10/LD_O3_andamento_22-10.pptx` (13 slides, modelo CAE): capa, andamento, limpeza (comparação,
antes/depois, critérios), descargas, domínio e malha, como o vazamento entra, **cenários iniciais propostos**, perguntas,
próximos passos, **referências**, encerramento. Gerado por `build.py` sobre o modelo `Slides_Fire_Smoke_CAEXPERTS`.

**Cenários iniciais propostos** (análise meteorológica de 29/09, `cenarios_meteo.py`): 6 cenários = 3 campos de vento,
todos na direção dominante NNE (22,5°, 20,5 % das horas):
| campo | vento a 10 m | estabilidade | cenários |
|---|---|---|---|
| V1 típico | 1,9 m/s (média) | D | 1 e 2 (vazamento pequeno e grande) |
| V2 rajada | 13,6 m/s (máxima medida) | D | 3 e 4 |
| V3 fraco estável | 1,1 m/s | F (28,8 % das horas) | 5 e 6 (proposto) |

**27/10:** Marcus envia a apresentação à LD e encaminha as perguntas (inclusive a localização da chaminé).
