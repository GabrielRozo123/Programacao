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

## Registro da reunião
| item | resposta / decisão |
|---|---|
| — | *(preencher após a reunião)* |
