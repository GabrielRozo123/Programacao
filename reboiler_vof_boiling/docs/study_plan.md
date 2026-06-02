# Reboiler CFD — VOF + Boiling (STAR-CCM+)

## Contexto Industrial

Reboilers são trocadores de calor que vaporizam parcialmente a corrente de fundo de
colunas de destilação. Representam ~30% do consumo energético em refinarias e
plantas petroquímicas. O CFD com VOF + ebulição nucleada quantifica:

- **Distribuição do título de vapor (vapor quality)** ao longo do feixe de tubos
- **Ponto de DNB (Departure from Nucleate Boiling)** — risco de secagem da parede
- **Convecção natural do líquido** — padrão de circulação dentro do casco
- **Eficiência de transferência de calor** vs. correlação de Mostinski/Rohsenow

---

## Cenário Industrial Escolhido

**Tipo:** Kettle Reboiler (TEMA K) — configuração mais comum em refinarias  
**Fluido processo (casco):** n-Pentano (C₅H₁₂) líquido — corte de destilação de nafta  
**Fluido aquecimento (tubo):** Vapor d'água saturado (utilidade)

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Pressão de operação (casco) | 2,5 bar (abs) | Típico destilação nafta |
| T_sat C5 @ 2,5 bar | 63,5°C (336,6 K) | NIST Webbook |
| Temperatura parede tubo | 110°C (383 K) | ΔT_parede ≈ 46,5 K |
| Superheat ΔT = T_wall − T_sat | 46,5 K | Regime nucleado ativo |
| Fluxo de calor estimado | 80–120 kW/m² | Mostinski, 1963 |
| Velocidade de circulação | 0,05–0,2 m/s | Convecção natural |
| Diâmetro do tubo (OD) | 19,05 mm (¾") | TEMA std |
| Passo triangular | 23,8 mm (P/D = 1,25) | Typical |

**Por que n-Pentano?**
- T_sat acessível (não precisa de pressão muito alta)
- Propriedades bem documentadas no NIST
- Representativo de cortes de nafta (C4–C6) em unidades de fracionamento
- Risco real: HAZOP → "Mais temperatura" → superaquecimento → DNB → dano ao feixe

---

## Tutorial → Industrial: Mapa de Adaptações

| Parâmetro Tutorial | Valor Tutorial | Valor Industrial | Motivo |
|-------------------|----------------|-----------------|--------|
| Fluido | H₂O | n-C₅H₁₂ | Fluido de processo real |
| Pressão | 1 atm (101,3 kPa) | 250 kPa (2,5 bar) | Operação real |
| T_sat | 100°C | 63,5°C | Decorre da pressão |
| T_wall | 130°C (ΔT=30 K) | 110°C (ΔT=46,5 K) | Vapor saturado a 1,43 bar |
| Geometria | 2D axissimétrica | 2D transversal ao feixe | Pool boiling com tubos |
| Escoamento | Flow boiling (canal) | Pool boiling (circulação natural) | Kettle reboiler |
| Turbulência | k-ω SST | k-ω SST | Mantido |
| Modelo ebulição | RPI (Wall Boiling) | RPI ajustado literatura | Ajuste de Nnuc, Rdb para C5 |
| N_nuc | 10000 /m² (Cu polido) | 5000–15000 /m² | Aço inox → Jacob & Linzer |
| R_db | 0,6 mm (Cu polido) | 1,0–1,5 mm | Hidrocarboneto → Fritz (1935) |

---

## Geometria (2D Pool Boiling — Seção Transversal)

```
┌─────────────────────────────────────────────────────────┐  ← vapor outlet (top)
│                   ░░░░░░ vapor ░░░░░░                   │
│    ○     ○     ○     ○     ○     ○     ○     ○          │
│    ○     ○     ○     ○     ○     ○     ○     ○          │← liquid pool
│    ○     ○     ○     ○     ○     ○     ○     ○          │
│═══════════════════════════════════════════════════════  │
└─────────────────────────────────────────────────────────┘  ← liquid inlet (bottom/side)
        ↑ tubos aquecidos (T_wall = 110°C)
```

**Domínio:**
- Largura: 8 tubos × 23,8 mm passo = 190 mm
- Altura: 4 filas × 23,8 mm + 100 mm vapor space = 195 mm
- Profundidade: 2D (extrusão unitária em Z)

---

## Física e Modelos STAR-CCM+

| Categoria | Modelo |
|-----------|--------|
| Multifase | VOF Eulerian Multiphase |
| Fase primária | n-C₅H₁₂ liquid |
| Fase secundária | n-C₅H₁₂ vapor |
| Ebulição | RPI Wall Boiling Model |
| Turbulência | k-ω SST (duas fases) |
| Energia | Multiphase Temperature |
| Força | Gravity (9,81 m/s² ↓) + Surface Tension |
| Solver | Segregated, transient (pseudo-steady) |

---

## O que validar

| Grandeza CFD | Correlação | Referência |
|-------------|-----------|-----------|
| q_nucleate [kW/m²] | Rohsenow (1952) | Chen, 1966 |
| q_crit (CHF) | Kutateladze + Lienhard | API 521 heat input |
| Temperatura parede | DNB check | TEMA limits |
| Padrão de circulação | Qualitativo | Reboiler design guides |
| Void fraction | Drift-flux model | Zuber & Findlay, 1965 |

**Correlação Rohsenow (validação)**:

```
q = μ_l × h_fg × [g(ρ_l − ρ_v)/σ]^0.5 × [c_pl × ΔT_e / (C_sf × h_fg × Pr_l^n)]³
```

Onde para n-Pentano em aço inox: C_sf ≈ 0,0132, n = 1,7

---

## Progressão de Complexidade

| Fase | Geometria | Fluido | Objetivo |
|------|-----------|--------|---------|
| 1 (agora) | 2D pool boiling, 1 tubo | n-C₅H₁₂ | Validar RPI vs. Rohsenow |
| 2 | 2D feixe 3×3 tubos | n-C₅H₁₂ | Interação entre tubos, padrão de bolhas |
| 3 | 3D feixe kettle completo | n-C₅H₁₂ | Perfil de título de vapor, DNB map |

---

## Normas e Referências

- **TEMA** (Tubular Exchanger Manufacturers Association) — tipos e limites de projeto
- **API 521** — calor absorvido por reboilers em cenário de fire case
- **ASME Sec. VIII** — vasos de pressão (casco do kettle)
- **API RP 582** — soldagem e projeto de trocadores em refinarias
- **Rohsenow (1952)** — correlação fundamental de ebulição nucleada
- **Mostinski (1963)** — correlação reduzida para hidrocarbonetos
- **Chen (1966)** — combinação convecção + ebulição (flow boiling)
- **Hewitt, Shires & Bott (1994)** — Process Heat Transfer (referência de projeto)
