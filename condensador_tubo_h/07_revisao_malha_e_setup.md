# 07 — Revisão: geometria, malha do filme e setup STAR

## A. Revisão da geometria (`condenser_tube_2D.step`)
**Veredito: sólida.** Corte 2D, tubo frio no vapor, dreno embaixo, gravidade p/ baixo.
- ✅ Tubo Ø25,4 mm centrado em y=+30,5 mm → ~152 mm de dreno embaixo, ~101 mm de vapor em cima.
- ✅ Domínio 254×254 mm (10·D) — longe o bastante p/ o far-field ser vapor imperturbado a T_sat.
- ⚠️ **Não é mudança de geometria, é de BC:** o domínio precisa de **suprimento de vapor (topo)**
  e **dreno (base)** — senão o vapor se esgota ao condensar. Ver setup abaixo.
- 💡 Opcional: 10·D é generoso; dá p/ apertar p/ ~6·D e economizar célula. Mantendo 10·D, deixe o
  **far-field grosso** (só refina perto do tubo) — não desperdiça malha.

## B. Malha para RESOLVER o filme (o ponto crítico)
O `h` só sai certo se o filme de condensado for resolvido. Da teoria (h = k_l/δ):

| Grandeza | Valor |
|---|---|
| Espessura média do filme δ = k_l/h | **69 µm** (topo ~metade, base mais grosso) |
| **Primeira célula (prism)** | **5 µm** → ~14 células na espessura média |
| **Nº de prism layers** | **14** (growth 1,2) → cobre ~296 µm (~4× o filme) |
| Tangencial no tubo | **0,5–1,0 mm** → 160–80 células ao redor |
| Regime do filme | Re ≈ 103 → **laminar** (Nusselt vale) |

- O critério aqui é **resolução geométrica do filme**, não y+ (o filme é laminar, lento).
- Verificar independência de malha refinando a 1ª célula (5 → 2,5 µm) e vendo se o `h` muda.

## C. Revisão do setup STAR — correções vs o tutorial de ebulição
O scaffold do `03_setup_star.md` veio do tutorial "Boiler". Para **condensação com o modelo
Evaporation/Condensation**, há correções importantes:

1. **FASES MULTI-COMPONENTE (correção principal).** O modelo Evap/Condensation **só funciona com
   fases multicomponentes** (doc STAR). Diferente do tutorial (fases de 1 componente):
   - **Gás = Multi-Component Gas:** H2O (vapor) + **Ar (inerte)**. Fase 1: fração de ar ~1e-4
     (quase zero). Fase 2 (NCG): aumentar a fração de ar.
   - **Líquido = Multi-Component Liquid:** H2O.
2. **Pressão de saturação** do H2O líquido: **Antoine** ou **Wagner** (ou Polinômio/Tabela) — define
   o equilíbrio na interface (Raoult). Calor latente automático via *Heat of Formation*.
3. **Interação de fases:** Evaporation/Condensation (Optional Models); Primária=líquido,
   Secundária=gás; **Connectivity** pareia H2O(líq)↔H2O(gás). Under-Relaxation da taxa p/ estabilizar.
4. **Condições de contorno** (≠ do tutorial de ebulição):
   - **Tubo:** Wall, **T = 75 °C** (T_parede fria).
   - **Topo:** suprimento de vapor — Pressure boundary (ou velocity inlet baixo) a **T_sat=100 °C**,
     VF gás=1, ar ~1e-4. Repõe o vapor consumido.
   - **Base:** **Pressure Outlet** (condensado + excesso de vapor saem).
   - **Laterais:** **Symmetry** (tubo único num banho).
5. **Condição inicial:** VF gás = 1 (tudo vapor), **T = T_sat = 100 °C**, ar ~1e-4.
6. **Turbulência → considerar LAMINAR** na validação. O filme (Re~103) e o vapor quase parado são
   laminares, e Nusselt é laminar. k-ε adicionaria transporte turbulento espúrio. *(Reavaliar p/
   NCG, onde pode haver convecção de vapor por empuxo.)*
7. **Passo de tempo:** Implicit Unsteady, **Δt pequeno** (~1e-3 s no arranque) — o filme forma
   rápido; ajustar vendo o monitor de `h` assentar.
8. **Reports:** `h` via field function **"Heat Transfer Coefficient" com T_ref = T_sat**; espessura
   do filme; q″ no tubo; **h(θ)** ao longo do perímetro; **Specified y+ HTC** p/ checar malha.

## Resumo acionável
- Geometria OK → importar e **malhar com 1ª célula 5 µm + 14 prisms** no tubo, far-field grosso.
- No setup, a correção que mais pega: **fases multicomponentes** (senão o modelo Evap/Cond nem liga).
- Rodar Fase 1 (vapor puro) e conferir **h → ~9,7 kW/m²·K (Nusselt)**. Bateu → modelo validado.
