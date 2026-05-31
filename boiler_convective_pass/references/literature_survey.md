# Literature Survey — CFD of Aquatubular Boiler Convective Passes

> Status: Initial skeleton — to be populated after research agent completes.

## 1. Crossflow Tube Bank Heat Transfer (CFD)

### Foundational Correlations (Experimental Basis for Validation)

| Author | Year | Contribution |
|--------|------|-------------|
| Žukauskas, A. | 1972 | Tube bank heat transfer — Nu = C·Re^m·Pr^0.36·(Pr/Pr_w)^0.25. Cornerstone correlation. |
| Incropera et al. | 2006 | Textbook tabulation of C, m for staggered/inline; row correction factors. |
| VDI Wärmeatlas | 2010 | Extended correlations including pitch effects (ST/D, SL/D). |

### CFD Studies — Tube Banks

*(To be filled from research agent output)*

---

## 2. Radiation in Boiler Convective Zones

*(To be filled)*

Key models considered:
- **P-1**: Valid when optical thickness τ >> 1 (dense particle/gas media). Low computational cost. May overpredict radiation in optically thin zones.
- **Discrete Ordinates (DO/S2S)**: More accurate for mixed optically thick/thin zones. Higher cost.
- **WSGG** (Weighted Sum of Gray Gases): Used to compute gas absorption coefficient for CO₂+H₂O mixtures.

---

## 3. Ash Deposition / Fouling Models

*(To be filled)*

Key parameters:
- Sticking efficiency η (function of particle T and surface T)
- Critical sticking temperature T_stick
- Typical threshold velocity below which deposition dominates

---

## 4. Erosion Models

*(To be filled)*

Models implemented in STAR-CCM+:
- **Finnie (1960)**: E = k · V_p^n · f(α) — angle-dependent, ductile materials
- **McLaury (1996)**: Extension of Finnie with improved angle function
- **DNV RP-O501** (Haugen et al.): Widely used in oil/gas; applicable to boiler tubes

Typical fly-ash erosion conditions:
- d_p = 30–100 μm
- V_gas > 12 m/s → significant erosion
- Staggered arrangement → more uniform impaction distribution

---

## 5. STAR-CCM+ Specific References

*(To be filled)*

---

## 6. Validation Datasets

*(To be filled)*

---

## Notes on Simulation Strategy

Based on initial survey:

1. **Domain**: 2D periodic slice (one tube pitch) sufficient for bulk validation;
   3D for edge effects or if swirl/secondary flow matters.
2. **Turbulence**: k-ω SST preferred over k-ε for tube bank crossflow (better
   boundary layer resolution on tube surfaces, adverse pressure gradients).
3. **DPM coupling**: one-way for dilute ash (mass fraction < 1%); two-way if
   denser loading expected.
4. **Radiation**: P-1 acceptable for initial runs; refine with DO if near-tube
   temperature gradients are critical.
5. **Mesh**: y+ ≈ 1 on tube walls for k-ω SST (wall-resolved); structured
   O-grid around each tube recommended.
