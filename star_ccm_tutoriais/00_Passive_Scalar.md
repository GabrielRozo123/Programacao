# Referência 00 — Passive Scalar (escalar passivo)

> Fonte: *Simcenter STAR-CCM+ — Passive Scalars · Setting Up Passive Scalars · Passive Scalar Model
> Reference · Passive Scalars Model Control Reference · Using a Passive Scalar for Residence Time*.
> Notas nossas (28/09/2026). Usado no estudo de dispersão atmosférica (LD Celulose).

## O que é
Variável transportada pelo escoamento **sem afetar as propriedades do fluido** ("corante numérico").
Equação resolvida para cada escalar φ:

```
∂(ρφ)/∂t + ∇·(ρuφ) = ∇·[(μ/σ + μt/σt)∇φ] + Sφ
```

Como φ não realimenta o escoamento, **a equação é linear em φ sobre um campo de velocidade congelado**
→ superposição: `φ(x) = Σ Qi · fi(x)`. Resolve-se uma vez por fonte unitária e qualquer vazão sai por
escala. É o que torna barato varrer cenários de vazamento.

## Setup
1. `[contínuo] > Models > Optional Models > Passive Scalar` (exige Segregated ou Coupled Flow).
2. `Models > Passive Scalar > Passive Scalars > New` → renomear.
3. Propriedades do escalar:

| propriedade | recomendação | observação |
|---|---|---|
| **Clip** | `Below Min`, mínimo 0 | evita φ negativo por overshoot numérico |
| **Transport** | Convection and Diffusion | também: só convecção, só difusão, nenhum |
| **Turbulent Schmidt Number** | 0,7 (default) — **fazer sensibilidade 0,5–0,9** | único parâmetro livre; menor σt = pluma mais larga |
| Molecular Diffusivity | Schmidt number (default) | irrelevante em escoamento turbulento |
| Use GGDH | só com RST | |

4. Contornos: entradas de fluxo recebem `Physics Values > Passive Scalar` (fonte = 1, ar limpo = 0);
   paredes: `Wall Passive Scalar Option` = **Zero Flux** (default) · Specified Value · Specified Flux
   (fluxo **mássico**).
5. Fonte volumétrica (opcional): `Regions > [região] > Physics Conditions > Passive Scalar Source
   Option` = *Mass Flux* ou *Scalar Flux with Inferred Density*.
6. Solver: URF default 0,8.

## Dicas práticas
- **Trabalhar normalizado** (φ ~ O(1) na fonte) e converter no pós. Concentrações reais de 10⁻⁸
  brigam com a tolerância do solver.
- Conversão para ppm (volume) quando φ é fração mássica: `ppm = φ × (M_ar / M_espécie) × 10⁶`
  — criar como Field Function e plotar direto.

## Truque: idade do ar / tempo de residência
Escalar `ResidenceTimeAir`, paredes Zero Flux, e fonte de região *Mass Flux* via Field Function:

```
($ResidenceTimeAir > 1000) ? 0 : $Density
```

O `$Density` escala a fonte; o limite (1000 s) evita crescimento infinito em recirculações.
Mostra **onde o ar fica parado** — pátios, vãos, esteiras — que é onde contaminante se acumula.
