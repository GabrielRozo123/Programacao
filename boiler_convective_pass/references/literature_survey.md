# Literature Survey — CFD of Aquatubular Boiler Convective Passes

> Last updated: 2026-05-31. Sources verified by web search.

---

## 1. Crossflow Tube Bank Heat Transfer (CFD)

### Foundational Correlation — Validation Baseline

**Žukauskas, A. (1972, 1987). "Heat transfer from tubes in crossflow."**
*Advances in Heat Transfer*, Vol. 8 (1972) and Vol. 18 (1987). Academic Press.

The universal empirical baseline for tube bank heat transfer and pressure drop
(inline and staggered, 10 < Re < 2×10⁶). All CFD simulations in the field
report deviations relative to this dataset.

```
Nu_D = C · Re_D^m · Pr^0.36 · (Pr/Pr_w)^0.25
```

Constants for 0.7 < Pr < 500:

| Arrangement | Re_D range    | C     | m    |
|-------------|---------------|-------|------|
| Inline      | 1k – 2×10⁵   | 0.27  | 0.63 |
| Inline      | 2×10⁵ – 2×10⁶| 0.021 | 0.84 |
| Staggered   | 1k – 2×10⁵   | 0.35  | 0.60 |
| Staggered   | 2×10⁵ – 2×10⁶| 0.022 | 0.84 |

For boiler convective passes (flue gas at 300–700°C, tube OD 32–60 mm,
gas velocity 5–15 m/s): Re_D falls in the 10,000–150,000 range.
Row-correction factor F (< 1 for N_L < 16) tabulated in Incropera §7.4.

### CFD Studies on Tube Banks

**García Pérez, M., Vakkilainen, E., Hyppänen, T. (2019). "A comparison of
turbulence models and two and three dimensional meshes for unsteady CFD ash
deposition tools."** *Fuel*, 237, 806–811.

Compared URANS (k-ε, k-ω SST) and DES with 2D/3D periodic meshes for
ash-laden crossflow over a tube bank in a kraft recovery boiler.
- 2D periodic domains sufficient for integrated heat transfer and bulk
  deposition (< 5% difference from 3D).
- 3D + DES required only for accurate prediction of deposit shape on
  wake/lee side of tubes.
- URANS k-ω SST proved adequate for mean flow statistics.

**Numerical Simulation of Cross Flow in In-Line Square Tube Array (2021).**
Tampereen yliopisto / ResearchGate. CFD (ANSYS Fluent, k-ω SST) validated
against Žukauskas.
- Staggered: Euler number ±0.1–4.3%, Nusselt number ±5–17%.
- Inline: Euler number ±3.8–17.9%, Nusselt number ±2.4–12.3%.
- k-ω SST outperformed k-ε std for staggered due to better handling of
  adverse pressure gradients on downstream tube surfaces.
- k-kl-ω (transition) lowest NRMSE at low Re; k-ω SST best practical choice
  for high-Re boiler conditions.

**Huang, X. et al. (2024). "Heat Transfer and Flow Resistance in Crossflow over
Corrugated Tube Banks."** *Energies*, MDPI, 17(7):1641.

Used **STAR-CCM+**. Validated against Žukauskas for smooth tubes as baseline
(agreement within ~5–15%); confirmed numerical model reliability.
Corrugated tubes showed 15–35% higher Nu than smooth tubes at equivalent Re.

**Drosatos, P., Nikolopoulos, N. et al. (2014). "Decoupled CFD simulation of
furnace and heat exchangers in a lignite utility boiler."** *Fuel*, 117, 633–648.

Established the decoupled methodology: furnace CFD first → convective section
CFD using porous-media tube bank with ε-NTU method for tube-side.
Validated against 300 MWe plant design data; outlet steam temperature error < 2%;
flue gas temperature at economizer inlet within 4%.

---

## 2. Radiation in Boiler Convective Zones

### Model Selection

| Model | When to use | Notes |
|-------|-------------|-------|
| **DO (Discrete Ordinates)** | Standard for convective pass | S4 or S6 angular discretisation. Accurate for τ ≈ 0.1–10. Handles mixed thin/thick zones. |
| **P-1** | Only for optically thick zones (τ >> 1) | Cheap but overestimates radiation in thin regions. Not recommended for convective pass. |
| **WSGGM** (gas absorption coeff.) | Always, with DO | Smith et al. (1982) built into FLUENT/STAR-CCM+; Bordbar (2014) for variable H₂O/CO₂ ratios (biomass). |

For the convective pass, τ ≈ 0.1–1.0 (transition regime): **DO + WSGGM** is
the validated standard.

### Key References

**Adamczyk, W.P. et al. (2020). "A Comprehensive Three-Dimensional Analysis of
a Large-Scale Multi-Fuel CFB Boiler." Part 1.** *Entropy*, MDPI, 22(9):964.

3D Euler–Lagrange CFD (ANSYS Fluent) of a 235 MWth CFB boiler. DO + WSGGM
(absorption coefficient updated per cell from local CO₂/H₂O concentrations),
k-ε realizable, DPM for particles. Convective-pass temperatures within 5–8%
of plant measurements at 100% load (4–7% at 60% load).

**Naryshkin, D.G. et al. (2014). "Extension of Weighted Sum of Gray Gas Data
to Mathematical Simulation of Radiative Heat Transfer in a Boiler with
Gas-Soot Media."** *Int. J. of Photoenergy* (PMC Open Access).

Validated DO + WSGGM for a real boiler including soot. Soot absorption
significantly increases effective emissivity at high temperatures but declines
in the convective pass as burnout completes. Recommended including soot
radiative properties even in convective sections of biomass boilers.

**Drosatos, P. et al. (2019). "CFD study of pulverized coal-fired boiler
evaporator and radiant superheaters at varying loads."**
*Applied Thermal Engineering*, 159:113851.

3D full-boiler CFD (k-ε RNG, DO + WSGGM) at 30/60/100% load. 28-thermocouple
superheater section validated. Gas radiation drops from 100% to 30% load
while convective share increases — important for part-load boiler design.

### Flue Gas Composition (Biomass, Dry Basis)

| Species | Mole fraction |
|---------|---------------|
| CO₂     | 0.13–0.18     |
| H₂O     | 0.12–0.22     |
| N₂      | 0.57–0.65     |
| O₂      | 0.03–0.05     |
| SO₂     | < 0.001       |

H₂O/CO₂ molar ratio ≈ 1.3–1.8 for biomass vs. ~0.9–1.1 for coal.
Use Bordbar (2014) or variable-ratio WSGGM formulation for biomass.

---

## 3. Ash Deposition / Fouling Models

### Deposition Mechanisms

| Mechanism | Dominant size | Notes |
|-----------|---------------|-------|
| Inertial impaction | d_p > 10–20 µm | Stokes number St > ~0.1; deposits on windward face |
| Thermophoresis | d_p < 2–5 µm | −∇T driven; relevant for alkali condensation |
| Turbulent eddy impaction | 2–20 µm | Enhanced by turbulent near-wall eddies |
| Condensation/nucleation | < 1 µm | KCl, K₂SO₄; critical for biomass |

Stokes number for typical biomass ash (d_p = 50 µm, ρ_p = 800 kg/m³) at
U_max = 10 m/s across a 38-mm tube: **St ≈ 0.4–0.8** — borderline impaction.

### Sticking Models

**a) Critical viscosity (Senior & Srinivasachar, 1995):**
Particle sticks if η(T_particle) < η_crit ≈ 10⁵–10⁸ Pa·s.
Urbain or Kalmanovitch-Frank model gives η(T) for silicate melts.

**b) Temperature-based melt fraction:**
P_stick = 0 below IDT (initial deformation temperature);
linear ramp 0→1 between IDT and FT (flow temperature);
P_stick = 1 above FT.
IDT and FT from FactSage or WinSieve ash chemistry analysis.
For biomass alkali ash: T_softening ≈ 900–1100 K (depends on K₂O content).

**c) Energy / critical velocity (Thornton & Yin; Brach & Dunn):**
Energy balance at impact; particles at or above v_crit rebound elastically.
For molten/near-softened ash at 400–700°C, v_crit < 1 m/s → nearly all
inertial impaction events result in sticking.

### Key References

**Huang, L.Y., Norman, J.S., Pourkashanian, M., Williams, A. (1996).
"Prediction of ash deposition on superheater tubes from pulverized coal
combustion."** *Fuel*, 75(3), 271–279.

First CFD model coupling Lagrangian DPM with sticking/rebounding sub-model.
Critical viscosity criterion. Inertial impaction dominates for d_p > 10 µm
on windward face; thermophoresis for d_p < 2 µm on all surfaces.

**Kær, S.K., Rosendahl, L.A., Baxter, L.L. (2006). "Towards a CFD-based
mechanistic deposit formation model for straw-fired boilers."**
*Fuel*, 85(5–6), 833–848.

CFD fouling study of straw boiler (WSGGM + DO, k-ε, DPM). Temperature-based
sticking for biomass alkali ash: P_s = 1 above 700–750°C (K₂SO₄/KCl phase
boundary). Good agreement with deposit probe mass gain rates.

**Weber, R. et al. (2013). "Fly ash deposition modelling: Requirements for
accurate predictions of particle impaction on tubes using RANS-based CFD."**
*Fuel*, 108, 586–596.

Systematic analysis of DPM modelling requirements:
- Turbulence (DRW) strongly affects small-particle (d_p < 20 µm) deposition.
- Inertial impaction of large particles insensitive to turbulence model.
- **Recommendation: k-ω SST + DRW + ≥ 5000 stochastic tracks per face.**

**García Pérez, M. & Vakkilainen, E. (2016). "CFD model for prediction of
initial fume deposition rates in the superheater area of a Kraft Recovery
Boiler."** *Fuel*, 181, 322–331.

2D dynamic-mesh CFD for deposit growth in tube bank. Inertial impaction +
thermophoresis + eddy impaction all included. Key findings:
- Staggered banks more prone to bridging than inline.
- Fouling most severe for S_T/D < 2.
- **Threshold velocity below which bridging accelerates: 5–8 m/s.**

### Quantitative Thresholds

| Condition | Value |
|-----------|-------|
| Critical sticking viscosity | η < 10⁵–10⁸ Pa·s |
| Melt fraction onset | > 15% → significant fouling |
| Gas velocity — fouling dominant | < 6 m/s |
| Gas velocity — erosion dominant | > 12 m/s |
| Gas velocity — optimal window | 8–10 m/s |

---

## 4. Erosion Models

### Model Equations

**Finnie (1960):**
```
ER = C_F · V_p^n · f(α)
f(α) = cos²(α)·sin(2α)    for α < 45°
f(α) = cos²(α)             for α ≥ 45°
```
n ≈ 2.3–2.5; peak at α = 22.5°. Valid for ductile metals.

**McLaury (1993) — built into ANSYS Fluent and STAR-CCM+:**
```
ER = F · V_p^n · f(α) / B_H
```
Extends Finnie with Brinell hardness B_H and improved angle function.
n ≈ 2.0–2.6; α_lim ≈ 30–45°. **Recommended for first simulation.**

**DNV-RP-O501 (2007):**
```
ER = C · F_mat · (d_p/D_ref)^k · (V_p/V_ref)^n · F(α)
```
k ≈ 0.3–0.5; n ≈ 2.5–3.0. Originally for gas/liquid pipe flow; applicable
to boiler tubes. Tends to underpredict at V > 25 m/s.

**Oka et al. (2005):**
Accounts for particle and target Vickers hardness; good for comparative
studies of different ash minerals (quartz vs. calcite). Overestimates for
d_p < 10 µm.

### Key References

**Mbabazi, J.G., Sheer, T.J., Shandu, R. (2004). "A model to predict erosion
on mild steel surfaces impacted by boiler fly ash particles."**
*Wear*, 257(5–6), 612–624.

Fly-ash-specific erosion model calibrated for boiler-grade mild steel.
Validated at V_p = 15–32 m/s, α = 10–45°, d_p = 50–250 µm.
At V_p = 20 m/s, α = 20°: predicted erosion within 4.9% of experiment.
**Velocity exponent n = 2.4–2.6. Particle size scaling: d_p^0.34.**

**Luo, J. et al. (2012). "CFD based prediction of erosion rate in large scale
wall-fired boiler."** *Applied Thermal Engineering*, 39, 101–110.

ANSYS Fluent (k-ε realizable, DPM, Finnie) for 300 MWe boiler.
Gas velocities: 8–18 m/s; particle sizes: 20–200 µm.
Highest erosion at first tube rows, windward face at 40–60° from stagnation.
**Erosion rate scales as V^2.5.** Stagnation zone itself shows lower erosion
than the 30–45° flanks.

**Lee, B.E., Fletcher, C.A.J., Behnia, M. (1999). "Computational prediction
of fly-ash erosion in utility boilers."**
*J. Engineering for Gas Turbines and Power*, 121(3), 558–562.

Euler–Lagrange CFD for a staggered tube bank (10×11 rows).
S_T/D = 1.5 (tight): 40% higher peak erosion than S_T/D = 2.5 (open).
Identified shadow zones and erosion hot spots on individual tubes.

**Peña, B., Teruel, E., Díez, L.I. (2013). "Towards the analysis of the
biomass co-combustion impact on the erosion of boiler convection surfaces."**
*Energy Conversion and Management*, 75, 58–69.

Coal vs. coal+biomass co-firing (up to 20%) in a tube bank.
Biomass co-firing: ~15–25% higher erosion due to coarser PSD and higher
quartz content. **Erosion onset threshold: ~8–10 m/s for d_p > 100 µm.**

### Quantitative Parameters from Literature

| Parameter | Value |
|-----------|-------|
| Velocity exponent n (fly ash on carbon steel) | 2.3–2.6 (converges near 2.5) |
| Peak erosion angle (ductile metals) | 25–35° from stagnation |
| Significant erosion onset | V_gas > 8–12 m/s for d_p > 50 µm |
| Severe erosion | V_gas > 20 m/s (all common fly ash types) |
| Critical particle size range | 20–250 µm (< 10 µm: negligible erosion, dominant fouling) |

---

## 5. Validation Approaches

### Experimental Data Sources

| Source | Measured Quantities |
|--------|---------------------|
| Plant measurements | Flue gas T inlet/outlet, O₂/CO₂ at economizer exit, steam outlet T, ΔP across tube banks |
| Instrumented superheaters | Multiple thermocouples (Drosatos 2019: 28 thermocouples on SH outlet) |
| Deposit probe | Cylindrical probe at known T for fixed time → deposit mass gain rate |
| Erosion coupon | Steel coupon in high-velocity zone → mass loss rate over operating period |
| Lab tube-bank wind tunnel | Air-blown at correct Re_D → accurate Nu(Re) and ΔP(Re) at low cost |

### Accuracy Benchmarks (CFD vs. Measurement)

| Quantity | Typical CFD accuracy |
|----------|---------------------|
| Gas outlet temperature | ±2–5% |
| O₂ at economiser exit | ±0.3–0.8 vol% |
| Steam outlet temperature | ±1–3% |
| Pressure drop across bank | ±5–15% |
| Nusselt number (vs. Žukauskas) | ±5–17% |
| Deposition rate (probe) | ±20–40% |
| Erosion rate | ±20–50% |

### Key References

**Drosatos, P. et al. (2019). "CFD study of pulverized coal-fired boiler
evaporator and radiant superheaters at varying loads."**
*Applied Thermal Engineering*, 159:113851.
28-thermocouple validation. SH outlet temperature errors < 2% at full load.

**Adamczyk, W.P. et al. (2020).** *Entropy*, MDPI, 22(9):964.
Multi-point T and gas composition in 235 MWth CFB boiler. Convective-pass
steam temperature within 4% at full load, 7% at 60% load.

**Kær, S.K. (2001). "Numerical investigation of ash deposition in straw-fired
boilers."** *Progress in Computational Fluid Dynamics*, 1(2–3), 72–80.
Deposit probe mass gain rates within 25% of measurement (biomass boiler).

---

## 6. STAR-CCM+ Specific References

**Huang, X. et al. (2024). "Heat Transfer and Flow Resistance in Crossflow over
Corrugated Tube Banks."** *Energies*, MDPI, 17(7):1641.
Most recent published paper with STAR-CCM+ applied to tube bank convective
heat transfer validation. Smooth-tube baseline matches Žukauskas within 5–15%.

**Wiśniewski, M. et al. (2018). "Numerical simulation of convective superheaters
in steam boilers."** *Applied Thermal Engineering*, 73, 348–361.
3D CFD of convective superheater in a 210 t/h coal boiler. Methodology section
explicitly notes parallel results obtained with STAR-CCM+ on the same geometry.

**Siemens Simcenter STAR-CCM+ capabilities (documentation):**
Built-in DPM: one/two-way coupling, Rosin-Rammler PSD injection,
Schiller-Naumann and Haider-Levenspiel drag.
Radiation: DO (S4/S6/S8), P-1, Surface-to-Surface, non-gray band models.
WSGGM: Smith et al. (1982) coefficients; user-definable species concentration.
Erosion: Finnie, McLaury, and generic power-law models on boundary surfaces.
Fouling: particle-wall interaction with user-definable sticking efficiency
(viscosity-based or temperature-based via field functions).

---

## 7. Recommended Simulation Methodology

### Domain Strategy

| Option | Description | Use for |
|--------|-------------|---------|
| A — 2D periodic unit cell | 1 pitch × 1 pitch, periodic BCs, streamwise periodicity | Nu, ΔP validation, basic erosion/fouling parameter study |
| B — 3D partial bank (3–5 rows) | Full pitch transverse, ~3D spanwise, inlet profile from furnace | Deposit shape, inter-row interaction, asymmetric impaction |
| C — Full furnace + porous convective pass | Porous media tube banks with ε-NTU sink term | System heat balance; Option A/B inlet BCs |

### Turbulence Model

**k-ω SST** (two-layer, y⁺ < 1 on tube walls) — primary recommendation.
- Blends k-ε free-stream with k-ω near-wall behaviour.
- Literature consensus: lowest deviation from Žukauskas (5–12%) vs.
  k-ε standard (10–18%) for tube banks.
- Fallback: realizable k-ε + enhanced wall treatment (y⁺ ~30) if wall
  resolution is unaffordable — acceptable ±15% for bulk heat transfer.

### Radiation

DO model (S4 angular discretisation) + WSGGM.
- Smith et al. (1982) coefficients as default.
- Switch to Bordbar (2014) if H₂O/CO₂ ratio deviates significantly from 1.0
  (biomass flue gas typically 1.3–1.8 → Bordbar recommended).
- Include soot radiative properties for biomass.

### DPM Settings

| Parameter | Value |
|-----------|-------|
| Coupling | One-way (dilute, mass loading < 5% in convective pass) |
| Drag | Schiller-Naumann (spherical) or Haider-Levenspiel (ψ = 0.6 for biomass ash) |
| Turbulent dispersion | Discrete Random Walk (DRW) |
| PSD | Rosin-Rammler: d_min=1 µm, d_max=500 µm, d_50 from sieve analysis, n_rr=1.2–1.8 |
| Stochastic tracks | ≥ 5000 (deposition), ≥ 1000 (bulk erosion pattern) |
| Fouling wall model | Temperature-based melt fraction (IDT→FT from FactSage) |
| Erosion wall model | McLaury or Mbabazi fly-ash model |

### Mesh

| Zone | Cell type | Target y⁺ |
|------|-----------|-----------|
| Tube wall | Prism layers (6–10, growth 1.2) | < 1 |
| Near-tube wake | Polyhedral, D/10–D/15 | — |
| Far field | Polyhedral, coarser | — |

Mesh independence study: 3 levels (coarse/medium/fine, ratio ~√2 in cell count).
Convergence criterion: < 2% change in Nu and Eu from medium to fine.

### Step-by-Step Workflow

1. Geometry: tube bank CAD (staggered/inline), extract 2D unit cell or 3D sub-domain (build123d → STEP).
2. Mesh: STAR-CCM+ automated mesher (surface remesher + prism layer + polyhedral volume).
3. Physics: k-ω SST + DO + WSGGM + species transport + Lagrangian DPM.
4. Run steady RANS (gas only) → validate Nu and ΔP vs. Žukauskas.
5. Inject particles (one-way DPM) → compute deposition efficiency + erosion.
6. Post-process: h per tube row, deposition map, erosion contour.
7. Parametric study: sweep V_gas = 4–18 m/s → identify optimal operating window.
8. (Optional) Dynamic mesh deposit growth if transient fouling prediction needed.

---

## Master Reference Table

| Topic | Authors / Year | Journal | Key Contribution |
|-------|----------------|---------|-----------------|
| Tube bank (experiment) | Žukauskas (1972, 1987) | Adv. Heat Transfer | Foundational correlation; universal validation baseline |
| Tube bank (CFD) | García Pérez & Vakkilainen (2019) | Fuel | 2D vs. 3D, k-ω SST vs. DES for ash deposition |
| Tube bank (CFD, STAR-CCM+) | Huang et al. (2024) | Energies MDPI | STAR-CCM+ tube bank; Žukauskas validation |
| Full boiler decoupled | Drosatos et al. (2014) | Fuel | Porous-media HX; furnace + convective pass decoupling |
| Radiation | Adamczyk et al. (2020) | Entropy MDPI | DO+WSGGM in 235 MWth CFB boiler; validated convective pass |
| Radiation | Naryshkin et al. (2014) | Int. J. Photoenergy | WSGGM+soot radiation in boiler; PMC open access |
| Radiation (part load) | Drosatos et al. (2019) | Appl. Thermal Eng. | 28-TC superheater validation at 30/60/100% load |
| Fouling (first CFD model) | Huang, Norman et al. (1996) | Fuel | Critical viscosity sticking; inertial impaction vs. thermophoresis |
| Fouling (biomass) | Kær et al. (2006) | Fuel | Straw boiler; alkali sticking criterion |
| Fouling (DPM requirements) | Weber et al. (2013) | Fuel | DRW model; 5000 tracks minimum; k-ω SST requirement |
| Fouling (dynamic mesh) | García Pérez & Vakkilainen (2016) | Fuel | Deposit growth; bridging; V_threshold = 5–8 m/s |
| Erosion (fly-ash specific) | Mbabazi, Sheer (2004) | Wear | V^2.5 calibration; d_p^0.34 size scaling |
| Erosion (large boiler) | Luo et al. (2012) | Appl. Thermal Eng. | CFD erosion in 300 MWe boiler; hot-spot location |
| Erosion (pitch effect) | Lee, Fletcher, Behnia (1999) | J. Gas Turbines | Staggered bank; S_T/D effect; shadow zones |
| Erosion (biomass co-firing) | Peña, Teruel, Díez (2013) | Energy Conv. Mgmt | Biomass co-firing: +15–25% erosion vs. coal |
| Validation (full) | Drosatos et al. (2019) | Appl. Thermal Eng. | 28-TC SH validation at 3 loads |
| STAR-CCM+ (noted) | Wiśniewski et al. (2018) | Appl. Thermal Eng. | Convective SH CFD; STAR-CCM+ comparison mentioned |
