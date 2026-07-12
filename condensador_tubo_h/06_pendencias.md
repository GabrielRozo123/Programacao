# 06 — Pendências e decisões (documento vivo)

## Decisões abertas (bloqueiam o setup final)
| # | Decisão | Status | Nota |
|---|---|---|---|
| 1 | ~~Modelo de condensação~~ → **VOF Evaporation/Condensation** | ✅ | Limitado por difusão (interface em equilíbrio, Raoult) → `h` emerge, sem coef. de ajuste. **NCG = espécie inerte nativa** (multicomponente). Ver `02_fisica_e_metodo.md`. |
| 2 | **Fluido** | ✅ | Vapor d'água / água, atmosférico. |
| 3 | **Material do tubo** | ⏳ | Real de condensador: CuNi 90/10, titânio ou inox. Afeta condução se formos conjugados. |
| 4 | **Ponto de operação** | ✅ | T_sat=100°C (1 atm), ΔT=25 K → T_parede=75 °C. Alvo Nusselt h≈9,7 kW/m²·K. |
| 5 | **D do tubo** | ✅ | 25,4 mm (1"). Geometria 2D construída (`geometria/condenser_tube_2D.step`). |
| 6 | **NCG desde já ou depois** | 🟢 | Fase 1 vapor puro (valida Nusselt) → Fase 2 injeta NCG (flagship). |
| 7 | **Tubo único vs banco** | 🟢 | Único primeiro; banco (inundação) só na Fase 3, provável Fluid Film. |

## Decisões já tomadas (registradas)
- **Definição do `h`:** `h = q″/(T_sat − T_parede)` via field function "Heat Transfer Coefficient"
  com **T_ref = T_sat** (não o Local HTC, mesh-dependent). Verificação de malha via Specified y+ HTC.
  Fonte: doc STAR de HTC. Ver `02_fisica_e_metodo.md`.
- **Abordagem:** direto industrial; o instante de tubo limpo serve de checagem Nusselt embutida.
- **Base de setup:** tutorial VOF "Boiler", invertido para condensação (parede fria, vapor inicial).

## Próximos passos
1. Receber e classificar as **opções de condensação do STAR** (decisão 1).
2. **Revisão de literatura** (deep research): fixar dataset de validação (D, T_sat, ΔT, h medido),
   Nusselt, e correlações de NCG (Rose/Dehbi/Sparrow) — resolve decisões 4 e 5 e confirma novidade.
3. Construir a **geometria** paramétrica com os valores fixados.
4. Montar o setup STAR (scaffold do `03_`) com o modelo escolhido e rodar a validação.

## Log
- **2026-07-09** — Repo criado. Consolidados: contexto/objetivo, física+método (incl. definição do
  `h` a partir do doc de HTC do STAR), setup do tutorial adaptado, plano de validação Nusselt,
  geometria. Pendências 1, 3, 4, 5 em aberto.
- **2026-07-09** — Decisão #1 RESOLVIDA: modelo **VOF Evaporation/Condensation** (limitado por
  difusão, NCG = espécie inerte nativa). Revisão de literatura disparada (deep research) para fixar
  dataset de validação, condições de operação e correlações de NCG.
- **2026-07-11** — Decisão #1 **REVISTA**: VOF difusivo **não condensa vapor puro** (sem gradiente
  de espécie). Trocado para **Fluid Film + Thermal Limitation** + Shell Region no tubo. Condensou.
- **2026-07-12** — **ESTUDO FECHADO em 2D.** `h(θ)` reproduz a forma de Nusselt e o `h` local no
  topo enquadra o alvo (9,7 kW/m²·K), mas o `h` médio = **2,29 kW/m²·K (~4× abaixo)** por
  **acúmulo do filme**: o condensado não drena num tubo liso em 2D (gotejar/edge-stripping são 3D).
  Validação **qualitativa** aceita; quantitativo exige **fatia 3D** (trabalho futuro). Registro
  completo em `08_resultado_e_licoes.md`. Material de divulgação (carrossel LinkedIn) em `linkedin/`.
