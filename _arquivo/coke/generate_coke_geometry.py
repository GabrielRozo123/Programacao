#!/usr/bin/env python3
"""
Coke Fouling CHT Geometry for Star-CCM+ – HAZOP Run-Length Study
=================================================================
Quasi-Steady-State (QSS) snapshots of a pyrolysis furnace radiant coil
tube with growing internal coke layer (approach: Rezaeimanesh et al. 2023,
Can. J. Chem. Eng.; coke properties: Ghent LCT group).

Creates STEP files for 3 snapshots (concentric bodies, conformal contact):

  Snapshot 1 – CLEAN      (t_coke =  0 mm):  coke1_fluid / coke1_steel
  Snapshot 2 – MID-RUN    (t_coke =  6 mm):  coke2_fluid / coke2_coke / coke2_steel
  Snapshot 3 – END-OF-RUN (t_coke = 12 mm):  coke3_fluid / coke3_coke / coke3_steel

Coordinate system:
  - Tube axis along Z, centered at origin:  z from -L/2 to +L/2
  - Flow direction +Z

Radial build-up (all cases share the same steel tube):
  fluid:  0 ........ R_FLUID  (= R_BORE - t_coke)
  coke :  R_FLUID .. R_BORE   (only snapshots 2 & 3)
  steel:  R_BORE ... R_STEEL_OUT

CRITICAL UNITS NOTE: CadQuery/OCCT works in mm. STEP exports as mm and
Star-CCM+ imports correctly in SI (m). No Scale Mesh needed (the imported
tube must show R = 0.05 m / L = 2.0 m — verify on import!).
"""

import cadquery as cq
from cadquery import exporters
import os, math

# ================================================================
# PARAMETERS – radiant coil tube, ethylene cracking service
# All dimensions in mm.
# ================================================================
R_BORE      = 50.0     # clean inner radius [mm]  → ID = 100 mm (DN100 coil)
T_STEEL     = 8.0      # tube wall thickness [mm] (HP40 centrifugally cast)
R_STEEL_OUT = R_BORE + T_STEEL   # = 58.0 mm
TUBE_LENGTH = 2000.0   # tube section length [mm]

SNAPSHOTS = [
    ("coke1", 0.0,  "CLEAN      (0 h run)"),
    ("coke2", 6.0,  "MID-RUN    (~350 h)"),
    ("coke3", 12.0, "END-OF-RUN (~700 h)"),
]

OUTPUT_DIR = "/home/user/Programacao"

# ================================================================
# HELPERS
# ================================================================
def occt_check(wp, name):
    ok = wp.val().isValid()
    print(f"    OCCT check [{name}] → {'VALID' if ok else '!!! INVALID !!!'}")
    assert ok, f"{name} failed OCCT validity check!"

def face_report(wp, label):
    faces = wp.faces().vals()
    for i, f in enumerate(faces):
        print(f"      face {i+1:02d}: area = {f.Area():12.2f} mm²")
    return len(faces)

def solid_cylinder(radius, length):
    """Full cylinder centered at origin, axis Z."""
    return cq.Workplane("XY").cylinder(length, radius)

def annulus(r_in, r_out, length):
    """Hollow cylinder (tube) centered at origin, axis Z."""
    outer = cq.Workplane("XY").cylinder(length, r_out)
    inner = cq.Workplane("XY").cylinder(length, r_in)
    return outer.cut(inner)

# ================================================================
# BUILD AND EXPORT EACH SNAPSHOT
# ================================================================
print("=" * 64)
print(" COKE FOULING QSS SNAPSHOTS – geometry generation")
print("=" * 64)

for tag, t_coke, label in SNAPSHOTS:
    print(f"\n>>> Snapshot {tag}: {label}  (t_coke = {t_coke} mm)")
    r_fluid = R_BORE - t_coke

    # ---- FLUID core --------------------------------------------------
    fluid = solid_cylinder(r_fluid, TUBE_LENGTH)
    v = fluid.val().Volume()
    v_exp = math.pi * r_fluid**2 * TUBE_LENGTH
    print(f"  FLUID  : R = {r_fluid:5.1f} mm | V = {v:.0f} mm³ (exp {v_exp:.0f})")
    nf = face_report(fluid, "fluid")
    assert nf == 3, f"Fluid must have 3 faces (inlet, outlet, wall); got {nf}"
    assert abs(v - v_exp) / v_exp < 1e-6
    occt_check(fluid, f"{tag}_fluid")

    # ---- COKE layer (only when t_coke > 0) ---------------------------
    coke = None
    if t_coke > 0:
        coke = annulus(r_fluid, R_BORE, TUBE_LENGTH)
        v = coke.val().Volume()
        v_exp = math.pi * (R_BORE**2 - r_fluid**2) * TUBE_LENGTH
        print(f"  COKE   : {r_fluid:5.1f} → {R_BORE:5.1f} mm | V = {v:.0f} mm³ (exp {v_exp:.0f})")
        nf = face_report(coke, "coke")
        assert nf == 4, f"Coke annulus must have 4 faces (2 rings + 2 cyl); got {nf}"
        assert abs(v - v_exp) / v_exp < 1e-6
        occt_check(coke, f"{tag}_coke")

    # ---- STEEL tube (identical in all snapshots) ---------------------
    steel = annulus(R_BORE, R_STEEL_OUT, TUBE_LENGTH)
    v = steel.val().Volume()
    v_exp = math.pi * (R_STEEL_OUT**2 - R_BORE**2) * TUBE_LENGTH
    print(f"  STEEL  : {R_BORE:5.1f} → {R_STEEL_OUT:5.1f} mm | V = {v:.0f} mm³ (exp {v_exp:.0f})")
    nf = face_report(steel, "steel")
    assert nf == 4, f"Steel annulus must have 4 faces; got {nf}"
    assert abs(v - v_exp) / v_exp < 1e-6
    occt_check(steel, f"{tag}_steel")

    # ---- Conformal-contact sanity: shared cylindrical surfaces -------
    # fluid outer surface area must equal coke inner surface area, etc.
    a_int1 = 2 * math.pi * r_fluid * TUBE_LENGTH   # fluid ↔ coke (or steel if clean)
    a_int2 = 2 * math.pi * R_BORE * TUBE_LENGTH    # coke ↔ steel
    print(f"  Interface areas: fluid-side {a_int1:.0f} mm² | bore-side {a_int2:.0f} mm²")

    # ---- Export -------------------------------------------------------
    files = [(f"{tag}_fluid.step", fluid), (f"{tag}_steel.step", steel)]
    if coke is not None:
        files.insert(1, (f"{tag}_coke.step", coke))
    for fname, wp in files:
        path = os.path.join(OUTPUT_DIR, fname)
        exporters.export(wp, path)
        print(f"  exported → {fname}  ({os.path.getsize(path)/1024:.1f} KB)")

# ================================================================
# REFERENCE CALCULATIONS (printed for documentation / validation)
# ================================================================
Q_FLUX   = 80.0e3    # W/m² – firebox radiant heat flux on steel outer wall
K_COKE   = 6.5       # W/m·K – pyrolytic coke (Ghent LCT / Plehiers)
K_STEEL  = 21.0      # W/m·K – HP40 (25Cr-35Ni) at ~900 °C
MDOT     = 0.20      # kg/s  – process gas (naphtha + dilution steam)
RHO_GAS  = 0.56      # kg/m³ – ideal gas, ~2 bar abs, ~1123 K, M ≈ 26 g/mol
T_BULK   = 850.0     # °C    – process gas bulk temperature

print("\n" + "=" * 64)
print(" ANALYTICAL PRE-CHECKS (cylindrical conduction, fixed mdot)")
print("=" * 64)
r3 = R_STEEL_OUT / 1000.0
r2 = R_BORE / 1000.0
L  = TUBE_LENGTH / 1000.0
q_lin = Q_FLUX * 2 * math.pi * r3          # W/m of tube

for tag, t_coke, label in SNAPSHOTS:
    r1 = (R_BORE - t_coke) / 1000.0
    A1 = math.pi * r1**2
    V1 = MDOT / (RHO_GAS * A1)
    # conduction ΔT across coke (cylindrical):
    dT_coke  = q_lin * math.log(r2 / r1) / (2 * math.pi * K_COKE) if t_coke > 0 else 0.0
    dT_steel = q_lin * math.log(r3 / r2) / (2 * math.pi * K_STEEL)
    # crude ΔP scaling vs clean case (fixed mdot, ΔP/L ∝ V²/D ∝ 1/D⁵):
    dp_ratio = (R_BORE / (R_BORE - t_coke)) ** 5
    print(f"\n  {tag} – {label}")
    print(f"    bore velocity      : {V1:7.1f} m/s")
    print(f"    ΔT across coke     : {dT_coke:7.1f} K")
    print(f"    ΔT across steel    : {dT_steel:7.1f} K")
    print(f"    TMT estimate       : {T_BULK + dT_coke + dT_steel + 50:7.0f} °C "
          f"(bulk + coke + steel + film)")
    print(f"    ΔP ratio vs clean  : {dp_ratio:7.2f} ×")

print(f"""
=============================================================
 STAR-CCM+ SETUP GUIDE  (per snapshot – CHT, steady state)
=============================================================
0. UNITS CHECK on import: tube outer R must read 0.058 m,
   length 2.0 m. If it reads 58 m → re-import, do NOT scale by hand.

1. Import the 2 (or 3) STEP files of one snapshot
   → assign each to its own Region (boundary mode: one per face).

2. Rename boundaries:
   FLUID : Inlet (z=-1 m) | Outlet (z=+1 m) | fluid_wall (cyl)
   COKE  : coke_inner (cyl) | coke_outer (cyl) | coke_ring_a/b (adiabatic)
   STEEL : steel_inner (cyl) | steel_outer (cyl) | steel_ring_a/b (adiabatic)

3. Interfaces (Creating Interfaces tutorial):
   Ctrl-select fluid_wall + coke_inner  → Create Interface > Contact
   Ctrl-select coke_outer + steel_inner → Create Interface > Contact
   (Snapshot 1: single interface fluid_wall + steel_inner)

4. Continua:
   FLUID : 3D | Steady | Gas | Segregated Flow | Ideal Gas |
           Segregated Fluid Temperature | k-ε Realizable
           M = 26 g/mol, cp = 2800 J/kg·K, μ = 3.0e-5 Pa·s, k = 0.10 W/m·K
   COKE  : 3D | Steady | Solid | Segregated Solid Energy
           k = {K_COKE} W/m·K, ρ = 1600 kg/m³, cp = 1500 J/kg·K
   STEEL : 3D | Steady | Solid | Segregated Solid Energy
           k = {K_STEEL} W/m·K, ρ = 7900 kg/m³, cp = 500 J/kg·K

5. Boundary conditions:
   Inlet       : Mass Flow Inlet, mdot = {MDOT} kg/s, T = {T_BULK} °C
   Outlet      : Pressure Outlet, 0 Pa (gauge), backflow T = {T_BULK} °C
   steel_outer : Wall > Thermal: Heat Flux = {Q_FLUX:.0f} W/m²
   all rings   : adiabatic (default)

6. Reference values / initial conditions:
   Reference Pressure = 200000 Pa (≈ 2 bar abs coil pressure)
   Initial T = {T_BULK} °C everywhere, initial V = [0,0,40] m/s in fluid

7. Reports → Monitors → Plots:
   - Maximum Temperature on STEEL region          → "TMT_max"
   - Pressure Drop: ΔP = P_inlet − P_outlet (Expression report)
   - Mass Flow Averaged outlet temperature
   Stopping: residuals < 1e-4 + TMT_max asymptotic (steady run)

8. HAZOP acceptance (per API 530 / HP40 service):
   TMT design limit ≈ 1050 °C — compare TMT_max across snapshots.
=============================================================
""")
print("All checks PASSED. STEP files ready.")
