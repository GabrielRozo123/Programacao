# Propriedades do Nitrogênio — N₂ líquido e vapor (para o caso CFD LN₂)

> O banco do Star-CCM+ traz N₂ apenas como gás. Estas são as propriedades a inserir
> manualmente (campos "Constant") para o N₂ líquido, mais as do vapor e auxiliares.
> Estado de referência: **saturação a 77,35 K (ponto de ebulição normal, 1 atm)**.
> Valores de referência padrão (cryogenic data, ~NIST). Atualizado: 2026-06-27.

---

## N₂ LÍQUIDO saturado @ 77,35 K, 1 atm  (fase N2_liquido, Constant Density)

| Propriedade (nó Star-CCM+) | Valor | Unidade SI |
|---|---|---|
| Density | **806.6** | kg/m³ |
| Dynamic Viscosity | **1.61e-4** | Pa·s |
| Specific Heat (cp) | **2042** | J/(kg·K) |
| Thermal Conductivity | **0.1396** | W/(m·K) |
| Speed of Sound | **853** | m/s |
| Molecular Weight | **28.0134** | kg/kmol |

Obs.: o nó do líquido pode pedir Speed of Sound (default 1500 = água; trocar por 853)
e Molecular Weight (28.0134) dependendo da EOS selecionada.

## N₂ VAPOR saturado @ 77,35 K  (fase N2_vapor, Ideal Gas)

| Propriedade | Valor | Unidade |
|---|---|---|
| Molecular Weight | 28.0134 | kg/kmol |
| Dynamic Viscosity | 5.46e-6 | Pa·s |
| Specific Heat (cp) | 1075 | J/(kg·K) |
| Thermal Conductivity | 7.3e-3 | W/(m·K) |
| Density | ~4.6 (calculada pelo Ideal Gas: ρ=PM/RT) | kg/m³ |

Obs.: densidade do vapor NÃO se digita — Ideal Gas calcula via ρ = P·M/(R·T).
Conferir apenas Molecular Weight = 28.0134.

## AUXILIARES (Schrage, tensão superficial, inicialização)

| Propriedade | Valor | Uso |
|---|---|---|
| T saturação (1 atm) | 77.35 K | Schrage / condição inicial |
| Calor latente de vaporização (h_lv) | 199.2 kJ/kg = 1.992e5 J/kg | Schrage (Clausius-Clapeyron) |
| Tensão superficial (σ) | 8.85e-3 N/m | Phase Interaction (Surface Tension) |
| Pressão de saturação @ 77.35 K | 101.325 kPa | referência (= 1 atm por definição NBP) |
| Temperatura crítica (Tc) | 126.2 K | Clausius-Clapeyron / Antoine |
| Pressão crítica (Pc) | 3.39 MPa | Clausius-Clapeyron / Antoine |
| Massa molar | 28.0134 kg/kmol | Ideal Gas (vapor) |

---

## Notas
- Para a **validação Seo & Jeong** (modelo de difusão térmica), líquido com densidade
  constante é adequado.
- Para o caso de **rollover** (aplicação La Spezia), trocar a densidade do líquido por
  função de T (Polynomial Density) para haver empuxo e inversão de camadas.
- Se a pressão do tanque variar muito durante a simulação, T_sat varia junto
  (Clausius-Clapeyron) — o Schrage Model Extrapolation cuida disso automaticamente.
