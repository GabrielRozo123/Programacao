# reactorkit: design brief for a 3D RANS model of a continuous stirred-tank melt pyrolysis reactor

Lead-engineer brief, 2026-10-09. Every number carries a confidence tag: **[H]** read in the source or exact algebra; **[M]** consistent across secondary sources, or reproduced by an independent calculation; **[U]** memory or own estimate; **[D]** derived here from the listed inputs. The scripts that produced the [D] numbers are in `/tmp/claude-0/-home-user-Programacao/381db60a-cc64-54cc-aefe-1e483b5b217d/scratchpad/brief/` (`opt.py`, `opt4.py`, `final.py`, `params.py`; the brief itself is `brief.md`). All publisher full texts were blocked by the proxy, so no [M] value was read in the original.

---

## 1. Decision

**Concept A: a continuous, jacketed, unbaffled stirred tank. It holds molten plastic fed from an extruder, and a close-clearance double helical ribbon stirs it. Vapours leave through the top and a residue bleed leaves at the bottom.**

Reasons, in order of weight:

1. **The physics reduces to something tractable on a Cartesian GPU code.** The reactor contains one continuous liquid phase, a dispersed vapour fraction and a nearly flat surface. In an unbaffled vessel with a coaxial impeller, the flow is *exactly steady in the impeller frame* (single rotating reference frame, SRF). The whole flow therefore becomes one steady RANS solve, and the flare code's Brinkman immersed boundary and fast-diagonalisation Poisson solver can be reused almost unchanged. Concepts B, C and D need granular, partially filled or Euler-Euler/DEM physics, with time steps of 1e-5 to 1e-6 s for the bed concepts. None of them fits a from-scratch Colab code.
2. **It matches industrial practice.** Plastic Energy TAC runs heated melt vessels (Almeria, Seville, 20 kt/y at Geleen [M]). Quantafuel Skive used a flue-gas-heated reactor box [M]. Pryme uses an extruder melt feed with an electrically heated reactor [M]. The Japanese municipal plants are 6-15 kt/y with 62 wt% oil [M]. The early literature is a CSTR melt literature: Kitaoka & Murata 1971; Murata et al. 2002 and 2004.
3. **It is new as CFD.** No published 3D CFD of a stirred molten-plastic pyrolyser was found [M]. Published plastic-pyrolysis CFD covers fluidised beds, spouted beds and kilns.
4. **It carries the right engineering message for a CFD consultancy:** *capacity is limited by wall heat transfer*. Throughput, bulk temperature and wall temperature (the coking risk) are all CFD outputs.

The decision matrix (industrial, tractable, Colab, validation, visual, each scored 1-5) gives A 21, C 17, B 13 and D 13 [U]. Concept C, the conical spouted bed, stays a possible "teaser" only.

### 1.1 Corrections from the verification step that change the design

| Item in research | Verified / corrected | Consequence |
|---|---|---|
| Bulk melt at 440 C with 260 kg hold-up, 110 kg/h and X = k tau/(1+k tau) | That formula does not apply when the product leaves as vapour: the hold-up sets the temperature. 260 kg at 110 kg/h settles at about 400-407 C [D]. At 440 C the hold-up would be about 33 kg | The bulk temperature is an **output**. The default mode is a prescribed wall temperature with level control |
| Degraded bulk viscosity 1e-2 to 1 Pa s (concept), 1 Pa s (numerics) | 1e-3 to 1e-2 Pa s, central **3e-3 Pa s** (population balance) [D] | The melt bulk is **turbulent**: Re about 5e4, Pr about 90. RANS k-omega SST applies in the melt, not only in the freeboard. Only the fresh-feed plume is creeping flow |
| h_i 200-300 W/m2K at a 500-530 C wall | With mu about 3e-3, h_i is about **316 W/m2K** (Nagata) [D] | At 110 kg/h the wall needs only about 450 C. A wall at 480 C gives about 170 kg/h |
| Duty 47 kW (vaporisation counted twice, cp 2.7) | The DSC 920 J/g is already a heat of gasification, and cp is 3.1-3.3 kJ/(kg K) | 36 kW at 110 kg/h for F1 [D] |
| rho 750, k 0.15 (numerics placeholders) | Bulk rho about 620 kg/m3, k about 0.11 W/(m K); feed melt 715 kg/m3 at 300 C | The feed is about 15% **denser** and sinks, so compositional buoyancy is needed |
| A single 1/Pn scalar for viscosity | Underpredicts the viscosity of a fresh/bulk mixture by 440x | Replaced, see the next row |
| A single Mw scalar with sink -k_c Mw^2/(2 m0) (the verifier's fix) | **Also wrong in a CSTR.** It gives a steady Mw of 7.2 kg/mol against 1.9 kg/mol from the age integral and population balance [D], about 10x too viscous, because it cannot carry the young long-chain tail | Use the **psi + 3-class closure** (section 4.4). It reproduces the exact population balance: hold-up within 1-3%, Mw within 13-16% [D] |
| Ribbon Nu = 0.37 Re^0.92 | This is a transcription error; the correct form is 0.37 Re^(2/3) Pr^(1/3) Vi^0.14 | Used as the validation band |
| Paravisc Kp = 424.7 as the V1 target | Wrong geometry | Target **Kp about 269** (correlation, constants [U]) ±20%, below the Couette bound of 653 |
| Secondary cracking constants | Fail Mastral 2002 and Elordi 2011 above 600 C | **Disabled.** Negligible at 550 C or below (less than 0.5 percentage points of gas) |
| Heats PP 1.0, PS 0.8, PET 0.4 MJ/kg | Stoliarov DSC gives PP 1.31, PS 1.00, PET 1.80 MJ/kg | Corrected in the energy equation |
| PET authors "Dubdub & Al-Yaari" | Alhulaybi & Dubdub, Polymers 15 (2023) 3010 | Citation fixed |

---

## 2. Geometry and operating point (pilot/demo scale, about 1-2 kt/y)

### 2.1 Vessel and internals

| Quantity | Value | Note |
|---|---|---|
| Vessel ID D | 0.80 m | Shell 1.20 m. Flat bottom in the CFD; the real vessel has a torispherical bottom |
| Liquid level H_L | 0.80 m (H_L/D = 1) | V_liq = 0.402 m3 |
| Wetted heated area | 2.513 m2 (side 2.011 + bottom 0.503) | Free surface 0.503 m2 |
| Freeboard | 0.40 m | Separate one-way RANS solve |
| Impeller | double helical ribbon, nb = 2, **d = 0.72 m (d/D = 0.90)** | Wall clearance c = 40 mm (c/d = 0.056), pitch 0.72 m, width 0.072 m, thickness 20 mm, height 0.72 m, bottom clearance 40 mm, shaft Ø80 mm, support arms at z = 0.06 and 0.74 m |
| Speed | **30 rpm** (20-60) | Tip speed 1.13 m/s; the wall moves at 1.257 m/s in the SRF. The ribbon pumps down at the wall and up at the shaft |
| Comparison impeller | anchor, same d, 72 mm blades plus a bottom arm | The showpiece "anchor vs ribbon" result |
| Feed | DN50 melt pipe discharging at the liquid surface, r = 0.20 m | In the SRF it becomes a ring source. The lab-frame transient keeps the real point inlet |
| Vapour outlet | DN100 on the top head, r = 0.25 m | Off-axis, because the drive shaft is on the axis |
| Drain | DN50, bottom, on the axis | Residue bleed (solids control) |
| Wall | 12 mm 316L, k about 18 W/(m K) [U] | The default BC is prescribed inner-wall temperature |

The clearance was opened from c/D = 0.025 (concept) to c/D = 0.05 so that the gap is 6.2 cells on the 128^3 production grid. At c/D = 0.025 it would be about 3 cells. Wall scrapers are not resolved geometrically (open question Q1).

### 2.2 Operating modes and design point

- **Mode B, the default (plant-like):** prescribed inner-wall temperature T_w, constant level (rigid lid), and the feed rate iterated so that feed = vapour + char + drain. Outputs: throughput, T_bulk, wall heat-flux map and hot spots.
- **Mode A, a check:** prescribed feed 110 kg/h at constant level. Output: the wall temperature needed.

Design inputs:

- p = 1.05 bar(a)
- N2 purge 1 kg/h [U]
- Feed melt at 300 C
- Hold-up 0.402 m3 × 620 kg/m3 × (1 - 0.05 gas) = **237 kg**
- Residue bleed set so that the hold-up holds 10 wt% inert solids: drain = (ash + char)/0.10, giving 7% of feed for F1 and 15% for F3 [D]. The solids target is open question Q7.

**Capacity curve from the 0-D model using the CFD closures [D]** (h_i = 316 W/m2K from Nagata ribbon, mu_bulk = 3.2e-3 Pa s, dH = 920 kJ/kg for PE and 1310 for PP):

| T_w (C) | F3 T_bulk (C) | F3 feed (kg/h) | F3 duty (kW) | F1 T_bulk (C) | F1 feed (kg/h) |
|---|---|---|---|---|---|
| 440 | 398.1 | 99 | 33 | 403.4 | 89 |
| 460 | 402.8 | 134 | 45 | 408.5 | 124 |
| **480 (default)** | **406.5** | **171 (1.37 kt/y)** | **58 (23 kW/m2)** | 412.5 | 161 |
| 500 | 409.7 | 209 | 72 | 415.8 | 199 |
| 520 | 412.3 | 247 | 86 | 418.6 | 238 |
| 540 | 414.7 | 286 | 100 | 421.0 | 277 |

Mode A for F1 at 110 kg/h gives T_bulk 406.5 C, T_w 452 C and Q 35.8 kW [D].

These numbers are consistent with the literature. Murata's continuous stirred PE reactors ran at 400-420 C with 0.3-1 kg/(kg h) [U numbers]; the closure gives 0.28-1.0 1/h at 400-420 C [D]. The Mitsui patent covers 400-450 C [M]. The bulk temperature rises only about 4 K per 20 K of wall, so throughput, not bulk temperature, is what the wall controls. This is the headline plot. Mean residence time at the default is 237/171 = 1.4 h. The kinetic time 1/k_app(HDPE, 406 C) is about 3,800 s.

Other design figures:

- Re_bulk = rho N d^2/mu = 620 × 0.5 × 0.518/3.2e-3 ≈ **5.1e4**; Pr ≈ 93 [D]
- Vapour: M ≈ 180 g/mol (C13 number mean), rho_v = 3.2 kg/m3 at 407 C, surface superficial velocity 0.027 m/s, DN100 outlet 1.8 m/s, Re 4.7e4 [D]
- Forced-vortex bound on the surface dip: Omega^2 R^2/(2g) = 0.080 m (10% of H_L); Fr = 0.018
- Laminar Kp (correlation) 269; Couette bound 653; Metzner-Otto ks = 34 - 144 c/d = 26.0

---

## 3. Default feeds

| ID | Composition (wt%) | Ash at reactor inlet | Role |
|---|---|---|---|
| F1 | HDPE 100 (Mw0 150 kg/mol, PDI 8) | 0.2 | Validation case, with the richest kinetics and rheology data |
| F2 | PP 100 (Mw0 300 kg/mol, PDI 5) | 1.0 | PP contrast case: cracks about 20 K lower, faster |
| **F3** | **HDPE 60 / LDPE 5 / PP 35** (São Carlos polyolefins 59.4/4.0/36.5 renormalised, Matos 2006 [H]) | 1.0 (1.5 as received; sensitivity 0-5) | **Headline case** |
| F4 | HDPE 50 / LDPE 5 / PP 30 / PS 15 | 1.0 | Two mechanisms: random scission plus unzipping. The guard warns because PS exceeds 7% |
| F5 | PE 30.6 / PP 17.6 / PS 8.6 / PET 39.0 / PVC 4.1 | n/a | "Do-not-feed" guard demonstration only: Cl 2.31 wt% (23,100 ppm), O 13 wt% |

- **Element basis** (exact repeat units) [H]: PE and PP are C 85.63 / H 14.37; PS is C 92.26 / H 7.74; PET is C 62.50 / H 4.20 / O 33.30; PVC is C 38.44 / H 4.84 / Cl 56.73.
- **HHV** [M]: PE/PP 46.4, PS 41.6, PET 22.9, PVC 18.0 MJ/kg. Post-consumer bomb values are PE/PP about 44.5 and PS 41.2.
- **Feed-quality guard** (AEPW/Eunomia 2022 [M]): PVC at most 1, PET+EVOH+PA at most 5, PS at most 7, PE+PP at least 85, moisture at most 7, total contaminants at most 15 wt%. The guard also prints the Cl and O carried in, against the steam-cracker limits Cl 3 ppm and O 100 ppm (Kusenberg 2022 [M]).
- **Exclusions:** PVC and PET are excluded by design. PVC releases up to 0.583 kg HCl per kg at 250-350 C. PET brings 33 wt% O, TPA/benzoic-acid sublimates and about 15-20% char.
- Moisture at the reactor inlet is 0 because it flashes off in the extruder vent.

---

## 4. Governing equations and closures

### 4.1 Frame, mass and momentum (liquid)

Whole-domain SRF, with relative velocity **w** and Omega = 2 pi N e_z:

```
dw/dt + div(w⊗w) = -grad(P)/rho0 + div[nu_eff (grad w + grad w^T)] - 2 Omega×w
                   + ((rho_m - rho0)/rho0) (g + Omega^2 r_perp) - (chi/eta_B)(w - w_s)
div w = 0
P = p - rho0 g·x - 0.5 rho0 |Omega×x|^2
w_s = 0 on the impeller,  w_s = -Omega×x on the shell and bottom
rho_m = (1 - alpha) rho_l(T, Mn, Y_feed)
```

- rho0 = 620 kg/m3.
- nu_eff = mu(gamma_dot, T, Mw)/rho0 + nu_t, with mu capped in momentum (section 4.3).
- Boussinesq-type: constant rho0 in inertia and continuity, full rho_m in the gravity and centrifugal body force. This captures the thermal and compositional buoyancy of the 715 kg/m3 feed rope against the 620 kg/m3 bulk (about 15% contrast; see the risks).
- The feed and vapour volume sources, about 4e-5 1/s, are ignored in momentum and kept in the scalars.
- Optional MRF (absolute velocity, smoothed rotating-zone indicator) handles baffled or off-axis cases (Rushton/PBT validation).
- A lab-frame moving-mask time-accurate mode is used only for verification (SRF vs moving mask) and the plume video.

### 4.2 Turbulence

- **k-omega SST** (Menter 2003 constants: beta* 0.09, a1 0.31, sigma_k1 0.85, sigma_w1 0.5, beta1 0.075, sigma_k2 1.0, sigma_w2 0.856, beta2 0.0828, gamma1 5/9, gamma2 0.44).
- Production limiter 10 beta* k omega.
- **Rotation-curvature correction** f_r1 (c_r1 1, c_r2 2, c_r3 1, clipped to [0, 1.25]), because unbaffled vessels are swirl-dominated.
- Sc_t = 0.7, Pr_t = 0.85.
- Wall distance comes exactly from the analytic signed-distance function (SDF).
- Regime rule on the local Metzner-Otto Re: laminar below 200, both laminar and SST between 200 and 2e4 (the spread is reported), SST above 2e4. The bulk (Re about 5e4) is SST. The feed rope (eta 1e2 to 7e3 Pa s, Re 0.2-4) laminarises on its own, because nu_t is much smaller than nu there.
- Sensitivity runs: standard k-epsilon, and laminar-everywhere.

### 4.3 Rheology mu(gamma_dot, T, Mw)

Cross model with a temperature shift and Mw dependence:

```
mu = eta_floor + eta0 / [1 + (eta0*gamma_dot/tau_star)^(1-n)],   eta_floor = 2e-4 Pa s
eta0_i(T, Mw) = max( K Mw^alpha , eta_wax(Mw) ) * aT(T)
eta_wax       = 0.015 Pa s * (Mw/1080)^1.9   at 149 C
                 (POLYWAX-anchored; crosses the Raju line at about 7.5 kg/mol)
aT            = exp[(Ea/R)(1/T - 1/Tref)]
blend:  ln eta0_mix = sum_i w_i ln eta0_i
```

| Polymer | K, alpha, Tref | Ea (kJ/mol) | Mc (g/mol) | n | tau* (Pa) |
|---|---|---|---|---|---|
| PE | 3.4e-15, 3.6, 463.15 K (Raju 1979 [U]; MFI check [M]) | 27 [M] | 3,800 | 0.35 | 2e4 |
| LDPE | as PE | 55; 27 once Mw is below 20 k (long-chain branching destroyed) | 3,800 | 0.30 | 3e4 |
| PP | 1.45e-6 (Mw/1000)^3.745 at 503.15 K [M] | 42 [M] | 10,000 | 0.30 | 2e4 |
| PS | 3.9e-15, 3.4, 473.15 K; WLF C1g 13.7, C2g 50 K, Tg 373 K [U] | (55 for 300-450 C) | 33,000 | 0.25 | 3e4 |

Expected values [D]:

- Bulk at 406 C: Mw about 2.2 kg/mol, eta about **3.2e-3 Pa s** (exact population balance gives 2.5e-3).
- Fresh HDPE feed at 300 C: eta0 = 3.8e3 Pa s.
- PP feed at 300 C: 805 Pa s.

Numerical handling:

- Cap mu in momentum at **30 Pa s** by default (RKL2 needs 7 stages at 128^3). Sensitivity runs at 3, 30 and 300 Pa s need 3, 7 and 22 stages.
- gamma_dot_min = 1e-2 1/s.
- Picard update in ln mu with relaxation 0.5, converged when |Δ ln mu| < 0.02.
- An optional Krieger-Dougherty suspension factor (phi_max 0.6) for ash and char.

### 4.4 Liquid-phase chemistry: psi + 3-class closure (derived here, verified against an exact population balance)

Random scission happens per backbone C-C bond:

```
k_c,i(T) = f_i A_i exp(-E_i/RT)
```

- A_i and E_i are the TGA-validated RS-L2 apparent set: HDPE 5.2e14 /s and 238 kJ/mol; LDPE 1.92e13 and 215; PP 6.98e10 and 179; PS 4.1e11 and 180.
- f = 0.0347 for PE. This comes from the L = 20 C2 cut mapping (Δalpha < 0.02).
- f = 0.053 for PP, calibrated here so that the closure reproduces Tpeak = 455 C.
- m0 per backbone bond: PE 0.014027, PP 0.021, PS 0.052 kg/mol.

**Volatile cut** (Riazi n-paraffin correlation, 1 atm):

```
N*_i = f_cut M*(T)/m0,i,   M*(T) = [(6.98291 - ln(1070 - T[K]))/0.02013]^1.5 g/mol
```

This gives M* = 359 g/mol (C25) at 407 C. f_cut = 1 by default; the sensitivity value 1.2 shifts T_bulk by only -2.4 K.

**Transported specific scalars per polymer i** (per kg liquid): Y_i (liquid derived from i), Z_i = Y_i psi_i (moles of chains per kg; *additive, so mixing is exact*) and E_i1, E_i2, E_i3 (mass in the entangled classes Mw ≥ 64 / 16-64 / 4-16 kg/mol). Inert solids Y_s (ash + char) are also transported.

Sources (W in kg/(m3 s)):

```
S_v,i  = rho0 k_c,i N*_i^2 m0,i Z_i
         (evaporation; linear in Z; psi_i capped at 1/(N* m0))
w_Z,i  = rho0 k_c,i Y_i/m0,i - 2 S_v,i/(m0,i N*_i)
         (scission creates chains; vapour removes fragments of mean length N*/2)
w_Y,i  = -S_v,i (1 + s_C)
w_s    = s_C sum_i S_v,i
w_E1   = -r1 rho0 E1;   w_E2 = rho0(r1 E1 - r2 E2);   w_E3 = rho0(r2 E2 - r3 E3)
r1     = (k_c/2m0)/(1/64 - 1/Mw0)
r_k    = k_c M_lo,k/(1.5 m0)        (M_lo = 16, 4 kg/mol)
Mw_i   = [sum_k E_k Mbar_k + (Y_i - sum E)(1.5 Mn_m)]/Y_i
Mbar_k = 1.848 M_lo
Mn_m   = (Y_i - sum E)/(Z_i - sum 2 E_k/Mbar_k)
```

The transport equation, in non-conservative form consistent with div w = 0:

```
rho0 (dphi/dt + w·grad phi) = div(rho0 Gamma_eff grad phi) + w_phi + S_f (phi_f - phi) + S_v,tot phi
Gamma_eff = nu_t/Sc_t      (molecular diffusion about 1e-9 m2/s, negligible)
```

The feed brings Y_i,f = w_i, Z_f = 1/Mn0 and E1_f = Y_f. The drain is a mass sink at local composition.

**Check against the exact chain-length population balance** (0-D evaporative CSTR, HDPE, F = 110 kg/h, 390-450 C [D]): hold-up within 1-3%, Mn within 2%, Mw 13-16% high, mass fraction above 4 kg/mol within 12%. For 260 kg the two give T_bulk 406.3 C (closure) against 406.4 C (exact). The steady psi = 1/(2 N* m0) gives a bulk Mn of about 700 g/mol and a vapour number-mean of 180 g/mol, matching the verifier's population balance (Mn 680, vapour 183). With N* = 40 (TGA conditions), the closure reproduces the RS-L2 TGA curve for HDPE: Tpeak 475.0 against 475.2 C, max |Δalpha| = 0.022.

**Why this structure:** mass-weighted mixing of fresh feed (150 kg/mol) and bulk (about 2 kg/mol) is linear only in quantities with linear sources. Z (chain moles) and the class masses qualify. 1/Pn and a single Mw with a quadratic sink do not (see 1.1).

**PS (F4 only):** mass loss uses RS-L2 apparent kinetics directly. Transport Y_PS and x_PS with dx/dt = k(1-x) and S_v = rho0 Y 2kx/(1+x). Products are styrene 0.65, aromatic oil 0.33 and gas 0.02 [U]. The PS-PE interaction option is k_PE,eff = k exp(gamma w_PS), with gamma = 0 by default and 1 as an option [M direction].

**PET (guard only):** first order with A = 2.59e13 /s, E = 210 kJ/mol and char 0.15. It is not in the CFD feeds.

### 4.5 Vapour products

Vapour leaves the liquid through S_v. Its lumps are computed from the fragment rule (random scission of long chains gives fragments uniform in length below N*, so mass ∝ length):

- **Gas (C1-C4):** s_G(T) = 0.06 exp[-(60 kJ/mol/R)(1/T - 1/693.15 K)]. This is a calibration knob [U] for end-chain and beta-scission chemistry that random scission alone misses; pure random scission would give only 2-3% gas, falling with T.
- **Oil (C5-C20)** and **vapour wax (C21 up to N*)** from (1 - s_G - s_C) split by (20^2 - 4^2)/(N*^2 - 4^2).
- **Char:** s_C = 0.005 kg per kg of vapour (range 0.005-0.03).

At 407 C the vapour slate is gas 0.049 / oil 0.568 / vapour wax 0.378 / char 0.005 [D]. The condenser and reflux decide the final oil/wax cut, so the brief reports the reactor-outlet vapour slate and compares only the bands (section 7).

Freeboard secondary cracking stays **off**. With the constants k_W = 3.9e12 exp(-230 kJ/mol/RT) and k_O = 1.3e12 exp(-230 kJ/mol/RT), it changes gas by less than 0.5 percentage points at 550 C or below and fails above 600 C.

### 4.6 Energy (liquid)

```
rho0 cp (dT/dt + w·grad T) = div[(k + rho0 cp nu_t/Pr_t) grad T] + Phi + S_f cp (T_f - T)
                             - sum_i S_v,i dH_i + h_wf (T_w - T) delta_Gamma
Phi = 2 mu S:S + rho0 beta* k omega
```

- **dH_i is the open-pan DSC heat of gasification per kg vaporised** (Stoliarov & Walters [M]): PE 920 ±120, PP 1310 ±70, PS 1000 ±90, PET 1800 kJ/kg. The F3 mixture is 1056 kJ/kg. This value already includes product desorption, so do **not** add a separate latent heat.
- The thermochemical cross-check gives 5.6 mol of scissions per kg of vapour × 83.1 kJ/mol + 200 ±50 kJ/kg desorption = 667 kJ/kg [D], within 30% of the DSC value. Run a ±30% sensitivity on dH.
- Solve for T' = T - 700 K so that FP32 resolves 0.01 K.
- cp(T): PE (17.48 + 0.0412 T_K)/0.014027 J/(kg K), i.e. 3.24 kJ/(kg K) at 406 C; PP 3.0; PS 2.3.
- k blends from melt to oligomer: k = 0.11 + (k_melt - 0.11) min(1, Mn/Mc), with k_melt = 0.24 (PE), 0.17 (PP) and 0.16 (PS) W/(m K) [U].
- rho_l: the PE, PP and PS Tait isobars, blended toward 610 kg/m3 for Mn in 500-2000 g/mol.

### 4.7 Vapour bubbles (drift flux, two-way coupled)

```
d(alpha)/dt + div[alpha (w + u_b e_z)] = S_v,tot/rho_v
u_b = min(0.25 m/s, Stokes(d_b = 4 mm, mu))
alpha <= 0.3; the lid is open to gas outflow
```

- Buoyancy enters through rho_m.
- Expected alpha is about 0.11 near the surface [D].
- **Foam-risk flag:** alpha > 0.3, or eta > 1 Pa s where S_v > 0 (the feed rope).
- Lagrangian bubbles are for the video only.

### 4.8 Wall heat transfer (immersed boundary)

- **Diffuse Robin source** h_wf (T_w - T) delta_Gamma, where delta_Gamma = |grad chi_wall| smoothed over 2 cells and checked so that ∫delta_Gamma dV = 2.513 m2 within 1%. The term is implicit (diagonal).
- **Turbulent branch** (default, bulk Pr about 90): u_tau from Spalding's law (kappa 0.41, B 5.2; 3-5 Newton iterations; valid for any y+ on the staircase), then **Kader** T+ with Pr_t 0.85, and h_wf = rho cp u_tau/T+. Sensitivity: Jayatilleke (+33% resistance at Pr 1e4).
- **Laminar branch** where local eta > 0.1 Pa s (the feed rope touching the wall): a Lévêque model, h = 0.807 k (gamma_w/(alpha L))^(1/3).
- No-flux on the impeller: face diffusivity and mass flux are set to zero for chi_face > 0.5.
- **Alternatives:** flue-gas jacket Robin with h_out 30-80 W/(m2 K) plus a coke resistance of 1-2e-3 m2K/W, or hot oil at 500-1500 W/(m2 K).
- The coking-risk map shows T_w - T_bulk and the area fraction with T_wall,fluid-side > 500 C [U threshold, Q4].

### 4.9 Free surface and freeboard

- **Rigid free-slip lid** at H_L.
- Diagnostic: eta_s = (p_lid - mean p_lid)/(rho g). The lid is accepted if max |eta_s| is below 0.05 H_L = 40 mm. The forced-vortex bound is 80 mm, so the check is real.
- If it fails, a **reshaped lid** (axisymmetric, from p_lid) is iterated 2-3 times. This is cheap, because the surface is steady and axisymmetric in the SRF.
- **Freeboard:** separate steady SST solve (96×96×64), one-way coupled. The inflow flux map comes from the melt-surface S_v and alpha; the gas is ideal with M = 180 g/mol, mu = 1.2e-5 Pa s and k = 0.045 W/(m K); the outlet is DN100 (Re 4.7e4). Its purpose is the vapour-path visual and showing that vapour residence time and secondary cracking are negligible.

---

## 5. Numerical strategy and grid

**Discretisation:**

- Uniform MAC grid in a cubic box (0.8 m + 4 cells).
- Pseudo-transient RK2 with 3rd-order upwind momentum advection.
- **RKL2 super-time-stepping** for the full variable-viscosity stress (stages from (s^2 + s - 2)/4 ≥ dt/dt_FE, safety 0.8).
- **Implicit pointwise Brinkman** (eta_B = 1e-3 dt) with 4^3-supersampled analytic masks. Solids are at least 2.5 cells thick.
- **Fast-diagonalisation Poisson solver from flarekit**, all-Neumann, with the zero mode removed and TF32 off.
- SST k and omega by TVD with implicit sinks.
- Impeller torque from the penalisation force, sum (x × rho0 (w* - w**)/dt)_z dV.

**Steady scalars** (T, Y_i, Z_i, E_ik, Y_s):

- Psi-tc backward Euler with SER (dtau0 = 1 s, growth ≤ 2x, cap 1e5 s).
- BiCGSTAB with Jacobi preconditioning (rtol 1e-3, max 300), batched over species.
- Deferred-correction van Leer.
- A **global-mean (CSTR-mode) coarse correction** after each step [U benefit].

**Coupling** (outer Picard loop, 4-8 iterations):

1. Run the 0-D model (closure plus exact population balance) to set uniform initial fields and the feed.
2. Flow solve with frozen mu, rho_m and alpha: 30 revolutions at 64^3 from a core in solid-body rotation at 0.6 Omega, then 5 revolutions at each finer grid. Converged when torque changes less than 0.5% per revolution and ||Δw||/||w|| < 1e-3 per revolution.
3. Steady scalars on the frozen w, nu_t.
4. Update mu (log-relaxed by 0.5), rho_m and alpha. Iterate the feed (Mode B) or the wall temperature (Mode A).
5. Stop when the KPIs change less than 0.5%. The KPIs are T_bulk, feed, Q_wall, max T_w - T_b, torque and Mw_bulk.
6. One-way freeboard solve.
7. Post-processing.

**Time scales:** impeller period 2 s; dt = 2.57e-3 s at 128^3 (779 steps per revolution); mixing about 1-2 min; residence 1.4 h; kinetics about 1 h. The flow and the chemistry are separated, and only the flow is time-marched.

**Presets:**

| Preset | Cells | dx | Gap cells | dt | Peak memory [U] |
|---|---|---|---|---|---|
| teste | 64^3 (0.26 M) | 13.3 mm | 3.0 | 5.3e-3 s | <1 GB |
| **gpu** (T4) | 128^3 (2.1 M) | 6.45 mm | 6.2 | 2.57e-3 s | about 4 GB |
| gpu_fino (T4) | 160^3 (4.1 M) | 5.13 mm | 7.8 | 2.04e-3 s | about 8 GB |
| gpu_ultra (A100) | 256^3 (16.8 M) | 3.17 mm | 12.6 | 1.26e-3 s | about 32 GB |

- Mesh study (GCI, Celik 2008, Fs 1.25): 96/128/170^3, ratio 1.33.
- Runtime estimate: 20-40 min at 128^3 on a T4 [U], to be measured in a benchmark cell. Opt-in torch.compile.
- Checkpoints go to Google Drive every 2 revolutions and after each outer iteration.

**Video at no extra CFD cost:**

- Reconstruct the lab frame from the steady SRF field, u_lab(x,t) = R(Omega t)[w + Omega×x](R(-Omega t)x), with a rigidly rotating ribbon iso-surface.
- 1e5 RK4 tracer "pellets" on the GPU.
- Poincaré sections for the anchor and the ribbon.
- An optional lab-frame transient of 20-30 s with the real point feed inlet, started from the SRF solution, to show the spiralling, sinking cold rope.

---

## 6. Package and notebook (same style as flarekit)

**Package `reactorkit/`:**

- `geometry.py`: SDFs for vessel, ribbon, anchor and arms; face masks; STL export for a STAR-CCM+ cross-check.
- `props.py`: rho, cp, k, Riazi M*, HHV/Boie, feed definition, guard.
- `rheology.py`
- `kinetics.py`: RS-L2 for TGA, plus the psi/class closure.
- `cstr0d.py`: closure, exact population balance and capacity curve.
- `flow.py`: SRF/MRF, RK2, RKL2, Brinkman, Poisson, SST-CC.
- `wallmodels.py`: Spalding, Kader, Jayatilleke, Lévêque, diffuse Robin.
- `scalars.py`: Psi-tc + BiCGSTAB, global correction, RTD mode.
- `bubbles.py`
- `freeboard.py`
- `validation.py`: every validation case, each printing PASS/FAIL with its tolerance.
- `render.py` / `hd.py`: lab-frame reconstruction, tracers, wall maps, 1080p H.264 video.

**Notebook order:**

1. Setup and benchmark
2. Feeds and guard
3. 0-D model and capacity curve
4. L0 verification
5. L1 component validation
6. L2 chemistry validation
7. Production run (F3, T_w 480 C)
8. Sweeps over T_w and impeller
9. Mesh study
10. Figures and video

---

## 7. Validation ladder (summary; full list in validation_plan)

- **L0, code verification:** Taylor-Green; SRF null test; Newtonian and power-law Couette; Brinkman viscous heating; diffuse-area and Robin annulus; MMS; CSTR/PFR/RTD; Ghia; de Vahl Davis.
- **L1, components:**
  - laminar Kp of the ribbon, 269 ±20%, below 653;
  - ks 26 ±20%;
  - Rushton laminar Kp 70 and turbulent Np 5.0 ±15%;
  - SRF equal to the moving-mask result within 3%;
  - h within ±30% of Nagata;
  - balances;
  - lid deflection;
  - GCI;
  - mu-cap sensitivity.
- **L2, chemistry and properties:**
  - TGA Tpeak table, with the 10 K/min point marked as calibration;
  - Westerhout PS 410.9 C and HDPE 474.0 C, PET 680 K at 2 K/min, Kissinger;
  - isothermal Westerhout rates;
  - closure against the exact population balance;
  - Murata/Kitaoka plausibility;
  - ISO 1133 densities, Riazi Tb, POLYWAX;
  - dH thermochemistry;
  - HHV.
- **L3, system:**
  - CFD against the 0-D model (T_bulk within 3 K, feed within 10%);
  - product-slate bands: gas 4-10, liquid 85-93, char 0.5-4 wt%, labelled "calibrated";
  - commercial yields used only as narrative: Plastic Energy 0.66-0.70 t/t, Sapporo 62 wt%.

---

## 8. Outputs for the event

1. **Capacity curve:** throughput and T_bulk against T_wall, with the coking band.
2. **Wall maps:** T_w - T_b and the local heat flux, with hot spots behind the ribbon flights.
3. **Feed rope:** the sinking, spiralling cold viscous rope (the "frozen" region where eta > 1 Pa s), with the viscosity contrast spanning 6 decades.
4. **Mw field:** fresh plume against cracked bulk.
5. **Vapour and foam:** alpha iso-surface and foam-risk map.
6. **Anchor against ribbon:** mixing, Poincaré sections and h.
7. **Freeboard:** vapour streamlines to the outlet.
8. **Cut-away video** with the rotating ribbon and tracers.
9. **Validation dashboard:** PASS/FAIL table and GCI.

---

## 9. Dropped or demoted inputs

These are not used as values:

- concept T_bulk 440 C and X = k tau/(1+k tau);
- mu_bulk 0.01-1 Pa s, and Jaydev 2024 (1-1000 Pa s, hydrogenolysis) as an analogue;
- the 1/Pn-only and single-Mw viscosity scalars;
- Nu ∝ Re^0.92; the ribbon pair 4.2 Re^(1/3) / 0.4 Re^(1/2); "a = 0.3-0.6";
- Paravisc 424.7 as a target; anchor ks = 4 pi; fixed anchor ks 20-30;
- secondary cracking above 550 C; PP Ea 62 kJ/mol (Kavade 2025); Jiang 2022 rate constants;
- KIT 23-34 kJ/g;
- semi-batch 4.1/91.2/4.7; reflux 96.3% at 380 C; Onwudili 89.5/10/0.5 as pass/fail (kept as a trend only); Elordi "67-80";
- the 47 kW duty; cp 2.7; rho 750; k 0.15.

These are kept as plausibility bands only:

- the Murata 2002 numbers;
- the Kp correlation constants;
- the ribbon laminar heat-transfer forms.
