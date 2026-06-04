# LinkedIn Post — Reboiler VOF+Boiling CFD (Fase 1)

---

## Versão PT-BR (recomendada)

---

🔬 **CFD de ebulição nucleada em reboiler industrial — primeiros resultados**

Finalizei a Fase 1 de uma simulação VOF + Wall Boiling (modelo RPI) de um kettle reboiler (TEMA K), usando **n-Pentano (C₅H₁₂)** como fluido de processo — representativo de cortes de nafta em unidades de destilação.

**Cenário industrial:**
- Pressão: 2,5 bar → T_sat = 63,5°C
- Parede do tubo: 110°C → ΔT = 46,5 K (regime nucleado ativo)
- Feixe: 3 colunas × 4 fileiras, passo triangular P/D = 1,25 (TEMA)

**O que o CFD capturou (t = 1,3 s de simulação transiente):**
- **Chaminés de vapor** entre colunas de tubos — canais preferenciais de subida de bolhas
- **Vapor blanketing assimétrico** — cobertura maior na parte superior dos tubos
- **Convecção natural** com V_max ≈ 1,24 m/s sem nenhum forçamento externo
- **Espaço de desengajamento de vapor** no topo (comportamento característico de kettle reboiler)

**Resultado quantitativo:**
- h_CFD ≈ 994 W/(m²·K) → q_wall ≈ 46 kW/m²
- Correlação Rohsenow (1952): h = 1953 W/(m²·K) → q = 91 kW/m²
- Desvio: −49% — **dentro do esperado para um run não calibrado**

O desvio se explica principalmente pelo coeficiente C_qw = 0,008 (padrão para água no RPI), que não reflete o comportamento do n-Pentano em aço inox 316L. A calibração com C_qw ≈ 0,016–0,024 (Pioro, 2004) é o próximo passo e deve trazer o resultado para a faixa ±25% da correlação.

**Ferramentas:** STAR-CCM+ (VOF + RPI Wall Boiling + k-ω SST), Python/build123d para geometria STEP, correlações de Rohsenow, Fritz (1935) e Mostinski (1963) para validação.

**Relevância industrial:** reboilers representam ~30% do consumo energético em refinarias. Identificar o ponto de DNB (Departure from Nucleate Boiling) via CFD permite quantificar margens de segurança que alimentam o HAZOP ("Mais temperatura" → superaquecimento → dano ao feixe).

---

Próximas fases:
→ Calibrar C_qw + rodar curva de ebulição (ΔT = 20, 30, 40, 46 K)
→ Feixe completo 3×6 + casco TEMA K
→ Mapa de título de vapor e margens de DNB

#CFD #HeatTransfer #ProcessEngineering #Reboiler #Refining #STARCCM #PoolBoiling #ChemicalEngineering

---

## Versão EN (alternativa)

---

🔬 **First results: VOF + nucleate boiling CFD of an industrial kettle reboiler**

Just completed Phase 1 of a pool boiling simulation (VOF + RPI Wall Boiling model) for a TEMA K kettle reboiler with **n-Pentane (C₅H₁₂)** — representative of naphtha cuts in distillation units.

**Setup:** 2.5 bar, T_sat = 63.5°C, T_wall = 110°C (ΔT = 46.5 K), 3×4 triangular tube bundle (P/D = 1.25 TEMA).

**What the CFD showed at t = 1.3 s:**
- Vapor chimneys between tube columns (preferential bubble rise paths)
- Asymmetric vapor blanketing (stronger at tube top than bottom)
- Natural circulation V_max ≈ 1.24 m/s with no forced flow
- Vapor disengagement space forming above the bundle (TEMA K behavior ✓)

**Numbers:** h_CFD = 994 W/(m²·K) vs. Rohsenow (1952) = 1953 W/(m²·K) → −49% deviation.
Expected for an uncalibrated RPI coefficient (C_qw = 0.008, water default). Calibration to C_qw ≈ 0.016–0.024 for n-C₅H₁₂/SS316L is the next step.

**Why it matters:** reboilers account for ~30% of energy consumption in refineries. CFD-based DNB margin quantification feeds directly into HAZOP analysis ("More temperature" deviation).

#CFD #HeatTransfer #PoolBoiling #Reboiler #ProcessEngineering #STARCCM #ChemicalEngineering
