# Aquatubular Boiler — Convective Pass CFD Simulation

## Objective

Simulate flue gas crossflow through the convective tube bank of a biomass-fired
water-tube boiler using STAR-CCM+. Quantify the competing effects of flue gas
velocity on thermal efficiency, fouling, erosion, and pressure drop.

## Physical Problem

In the convective passes of a water-tube boiler, hot flue gas flows across rows
of water-carrying tubes. Two failure modes bracket the design window:

| Regime | Velocity | Mechanism | Consequence |
|--------|----------|-----------|-------------|
| Low    | < 6 m/s  | Ash deposition (sticking) | Fouling → ΔT loss → efficiency drop |
| High   | > 12 m/s | Particle impact (fly-ash erosion) | Tube wall thinning → leaks |
| Optimal| 8–10 m/s | Balanced | Long service life + good heat transfer |

Reference: Žukauskas (1972), VDI Wärmeatlas (tube bank correlations).

## Fuel Context

Biomass-fired boiler (sugarcane bagasse or eucalyptus). Flue gas composition
(dry basis, approximate):
- CO₂: 13–15 %vol
- H₂O: 10–12 %vol
- N₂:  72–74 %vol
- O₂:   3–5  %vol
- SO₂: < 0.1 %vol (low for biomass)
- Fly ash: mean diameter 30–80 μm, density ~2200 kg/m³

## Simulation Scope

| Module | Model |
|--------|-------|
| Turbulence | k-ω SST (Re-Averaged) |
| Energy     | Segregated Fluid Energy |
| Radiation  | P-1 (optically thick zones) or DO |
| Particles  | Lagrangian DPM (one-way coupled) |
| Erosion    | Finnie / McLaury (tube wall) |
| Fouling    | Particle sticking efficiency (T-dependent) |

## Geometry Parameters (to be defined)

- Tube OD: 38.1 mm (1.5 in) — typical for industrial boilers
- Tube arrangement: staggered (recommended) vs. inline
- Transverse pitch ratio ST/D: 2.0–2.5
- Longitudinal pitch ratio SL/D: 1.5–2.0
- Number of tube rows: 6–10
- Domain: 2D periodic slice (1 tube pitch wide) or 3D sector

## Validation Target

Žukauskas correlation for tube banks in crossflow:

    Nu = C · Re^m · Pr^0.36 · (Pr/Pr_w)^0.25

Where C and m depend on tube arrangement and Re range.
Expected Δ between CFD and correlation: < 5 % for Nu, < 10 % for Δp.

## Directory Structure

```
boiler_convective_pass/
├── docs/               ← Project documentation and setup guides
├── geometry/           ← build123d scripts and STEP files
├── physics/            ← STAR-CCM+ physics setup notes and macros
├── validation/         ← Correlation scripts, comparison plots
├── references/         ← Literature survey and key papers
└── results/            ← Simulation results, post-processing
```
