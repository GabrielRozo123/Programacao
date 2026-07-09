# 01 — Contexto e objetivo

## A motivação (por que este estudo)
Em projetos com **mudança de fase**, o coeficiente de transferência de calor `h` de condensação é
tratado de forma pobre: usa-se um valor tabelado genérico, ou pior, ignora-se a **degradação** que
acontece na operação real. Consequência: condensadores super/subdimensionados, e surpresas em
campo. O objetivo aqui é mostrar que **CFD prevê o `h` de condensação** — local e médio — e que
essa previsão é confiável (validada) e sensível às condições industriais.

## Objetivo técnico
1. **Prever o `h` de condensação filmwise** num tubo horizontal frio, resolvendo o filme de
   condensado em VOF, e extrair `h(θ)` (local, ao longo da circunferência) e `h_méd`.
2. **Validar** o `h` do tubo limpo contra a teoria de **Nusselt (1916)** — âncora analítica exata.
3. **Quantificar a degradação industrial do `h`:**
   - **Gás não-condensável (NCG):** poucos % de ar podem cortar o `h` pela metade (camada de
     resistência difusiva na interface). É *a* dor de condensador (in-leakage de ar).
   - **Inundação (inundation):** condensado dos tubos superiores afogando os inferiores (banco).

## O que há de inédito
- Reproduzir Nusselt em CFD é conhecido; o **valor está em quantificar a queda do `h` com NCG em
  CFD resolvido** e entregar a curva `h/h₀ × %NCG` de forma industrial — pouco explorado e
  diretamente útil para projeto.
- Ancoragem dupla: **Nusselt** (tubo limpo) + correlações de NCG (**Rose, Dehbi,
  Sparrow-Minkowycz**) para o regime degradado.

## Escopo e faseamento
- **Fase 1 (núcleo):** tubo horizontal único, vapor limpo → `h` vs Nusselt. Materiais e condições
  **industriais reais** desde já (não um caso acadêmico).
- **Fase 2 (flagship):** injeção de NCG → curva de degradação do `h`.
- **Fase 3 (extensão):** banco de tubos / inundação — provavelmente via modelo de **filme fino
  (Fluid Film)** para viабilizar o custo.

## Relevância industrial
Condensação filmwise em bancos de tubos é o coração de todo **condensador casco-e-tubo**
(potência/turbina a vapor, refrigeração, processo). O `h` correto define a área do trocador — e a
degradação por NCG é a causa nº 1 de perda de desempenho em campo.
