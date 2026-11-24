# Coluna de bolhas reativa CO₂/NaOH: benchmark de Darmana et al. (2007)

| Arquivo | O que faz |
|---|---|
| `geometria/gera_geometria_darmana.py` → `coluna_darmana_200x1000x30.step` | Domínio de líquido de 200 × 1000 × 30 mm (mm; y vertical; origem no centro do fundo), com faces nomeadas (Aspersor 30 × 10 mm, Fundo, Topo, paredes) |
| `modelo_pontual.py` | Modelo pontual no sensor de pH (abordagem de Krauß & Rzehak 2016/2018): rede R_I/R_II/R_III com as constantes do Apêndice A de K&R 2018, k_L de Brauer, E de DeCoursey com E_a ajustado (Ap. B). Compara com o experimento digitalizado |
| `dados_literatura/*.csv` | pH × t (experimento E2 e DBM S2, Fig. 5) e d32/d₀ × z/H (Fig. 13), extraídos dos **vetores** do PDF |
| `resultados/constantes_star.json` | Constantes a 25 °C já nas unidades do STAR |
| `resultados/pontual_*` | Resultado do modelo pontual |

Resultado do modelo pontual: t(pH 8) = 167 s contra 162 s no experimento; RMSE do pH = 0,15; E_max = 1,51.
Sem a reação com água, 178 s. Com o E_a aproximado de Darmana, 178 s.

Guia de setup no STAR-CCM+: `Literatura/08_Coluna_Reativa_CO2_NaOH/SETUP_StarCCM_Darmana.md`.
