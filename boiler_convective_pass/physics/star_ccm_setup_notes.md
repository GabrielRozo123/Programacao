# STAR-CCM+ Physics Setup — Boiler Convective Pass

## Continua

### Flue Gas (fluid region)

| Physics Model | Selection |
|---------------|-----------|
| Space | 3-D |
| Time | Steady |
| Material | Gas Mixture (CO₂, H₂O, N₂, O₂) |
| Flow | Coupled / Segregated Flow |
| Turbulence | RANS k-ω SST |
| Energy | Segregated Fluid Energy |
| Radiation | P-1 (initial), Discrete Ordinates (refinement) |
| Particles | Lagrangian Multiphase — DPM (ash) |
| Erosion | Finnie or McLaury model on tube walls |

### Tube Wall (solid region — CHT)

| Physics Model | Selection |
|---------------|-----------|
| Material | Steel (SAE 1020, k=51 W/m·K) |
| Energy | Solid Energy |

### Water Side (tube inner — simplified)

Option A: Fixed wall temperature boundary (T_wall = T_saturation + ΔT_metal)
Option B: Full CHT with water continua (Segregated Flow + Energy, liquid water properties)

For initial validation: **Option A** (isothermal tube wall at T_sat ≈ 180°C = 453 K).

---

## Boundary Conditions

| Boundary | Type | Value |
|----------|------|-------|
| Inlet (gas) | Velocity Inlet | V = 4–18 m/s, T = 900 K, turbulence intensity 5%, L_turb=0.07·H |
| Outlet (gas) | Pressure Outlet | p_gauge = 0 Pa |
| Tube surfaces | Wall (isothermal or CHT) | T_wall = 453 K |
| Side walls (periodic) | Periodic | — |
| Top/Bottom (if 3D) | Symmetry or Periodic | — |

---

## Particle (DPM) Settings

| Parameter | Value |
|-----------|-------|
| Particle material | Fly ash (SiO₂, ρ=2200 kg/m³) |
| Size distribution | Rosin-Rammler: d_mean=50 μm, n=1.2 |
| Injection | Uniform from inlet face |
| Number of parcels | 5000–10000 |
| Coupling | One-way (dilute) |
| Wall interaction | Erosion (McLaury) + Sticking (fouling T-model) |

### Sticking Efficiency Model (Fouling)

```
η_stick = exp(-A · V_p) · F(T_p, T_wall)
```

where F = 1 when T_p > T_softening (particle partially molten → sticks).
For biomass ash: T_softening ≈ 900–1100 K (depends on K₂O content).

---

## Mesh Strategy

| Zone | Approach | Target y+ |
|------|----------|-----------|
| Tube surface | Prism layers (6–10 layers, growth 1.2) | y+ ≈ 1 |
| Near-tube wake | Polyhedral, refined | — |
| Far field | Polyhedral, coarser | — |

Recommended base cell size: 2–3 mm for D=38 mm tube.
Prism layer total thickness: 1.5 mm, first cell = 0.01 mm.

---

## Convergence Criteria

- Residuals: < 1×10⁻⁴ (continuity, momentum, k, ω)
- Energy residual: < 1×10⁻⁷
- Monitor: Nu on tube surfaces, Δp across domain — converged when change < 0.1%

---

## Post-Processing

1. Wall heat flux → compute Nu = h·D/k_gas (compare with Žukauskas)
2. Δp = p_inlet - p_outlet (compare with correlation)
3. Particle tracks → erosion contour on tube walls
4. Particle sticking rate → fouling deposition map
5. Temperature contours — identify hot/cold spots
