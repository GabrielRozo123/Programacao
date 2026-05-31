"""
Aquatubular Boiler — Convective Pass Geometry
Inline (square pitch) arrangement — typical bagasse-fired industrial boiler

Reference boiler: ASME D-type, 10–30 t/h, 14 bar (abs) steam
Tube: 50.8 mm OD (2"), SA-192 seamless carbon steel, BWG 9 wall
Pitch: 101.6 mm × 101.6 mm square (ST/D = SL/D = 2.0)
Source: D-type boiler spec sheets (Cleaver-Brooks, Victory Energy);
        Žukauskas (1972) for crossflow validation.

STEP exports
  step/01_Gas_Domain.step  — flue gas flow region (box with tube bores subtracted)
  step/02_Tube_Wall.step   — solid tube walls for CHT (optional)

Boundary naming in STAR-CCM+ (after import → Parts → Boundaries):
  01_Gas_Domain (7 boundaries):
    Z = 0 face               → Gas_Inlet
    Z = DOMAIN_Z face        → Gas_Outlet
    X = 0 face               → Symmetry_Left
    X = DOMAIN_X face        → Symmetry_Right
    Y = 0 face               → Symmetry_Bottom  (or Periodic_1)
    Y = DOMAIN_Y face        → Symmetry_Top     (or Periodic_2)
    42 cylindrical surfaces  → Tube_Wall_Outer  (T_wall = 195 °C = T_sat at 14 bar)

  02_Tube_Wall (3 boundaries, CHT option):
    42 outer cylindrical surfaces   → Tube_Wall_Outer  (interface with gas)
    42 inner cylindrical surfaces   → Tube_Wall_Inner  (T = 195 °C, isothermal)
    Top + Bottom annular rings      → Tube_Ends        (symmetry/adiabatic)

CFD Physics target (no DPM):
    Turbulence  : k-ω SST (y+ < 1, 10–15 prism layers)
    Energy      : Segregated Fluid Energy
    Inlet       : T_gas = 900 °C, V = 8 m/s, flue gas (CO2+H2O+N2+O2)
    Tube walls  : T_wall = 195 °C (T_sat at 14 bar)
    Validation  : Nu_D vs. Žukauskas (1972), ΔP vs. Euler number correlation
"""

from pathlib import Path
from build123d import *

Path("step").mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  GEOMETRY PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# Tube dimensions (ASME SA-192, 2" OD, BWG 9)
TUBE_OD   = 50.8   # mm  outer diameter
TUBE_WALL = 3.76   # mm  wall thickness (BWG 9)
TUBE_ID   = TUBE_OD - 2 * TUBE_WALL  # 43.28 mm inner diameter

# Pitch — square inline (ST/D = SL/D = 2.0, standard for solid-fuel boilers)
ST = 101.6   # mm  transverse pitch  (perpendicular to gas flow, X direction)
SL = 101.6   # mm  longitudinal pitch (in gas flow direction, Z direction)

# Bank size
N_ROWS  = 14   # tube rows in gas flow direction (Z)
N_TRANS =  3   # tubes per row in transverse direction (X); symmetry BCs on ±X faces

# Domain height in tube-axis direction (Y); use symmetry or periodic BCs on ±Y faces
# Tubes run vertically (lower drum → upper drum); 300 mm slice is representative
SPAN = 300.0   # mm

# Flow development lengths
INLET_EXT  = 3 * SL   # mm  inlet face → first tube row centre  (≈ 3D upstream)
OUTLET_EXT = 4 * SL   # mm  last tube row centre → outlet face  (≈ 4D downstream)

# ─── Derived ──────────────────────────────────────────────────────────────────
DOMAIN_X = N_TRANS * ST                                  # 304.8 mm
DOMAIN_Y = SPAN                                           # 300.0 mm
DOMAIN_Z = INLET_EXT + (N_ROWS - 1) * SL + OUTLET_EXT   # 2032.0 mm

# Tube centre positions: (cx, cz) — N_TRANS × N_ROWS = 42 points
CENTERS = [
    ((i + 0.5) * ST,          # cx: 50.8, 152.4, 254.0 mm  (centred in pitch cells)
     INLET_EXT + j * SL)      # cz: 304.8, 406.4, … 1625.6 mm
    for j in range(N_ROWS)
    for i in range(N_TRANS)
]
assert len(CENTERS) == N_ROWS * N_TRANS

# ─── Summary ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("BOILER CONVECTIVE PASS — GEOMETRY PARAMETERS")
print("=" * 60)
print(f"  Tube OD / ID / wall : {TUBE_OD} / {TUBE_ID:.2f} / {TUBE_WALL} mm")
print(f"  Pitch ST = SL       : {ST} mm  (ST/D = {ST/TUBE_OD:.2f})")
print(f"  Arrangement         : Inline (square pitch)")
print(f"  Tube rows × per row : {N_ROWS} × {N_TRANS} = {len(CENTERS)} tubes")
print(f"  Domain (X×Y×Z)      : {DOMAIN_X:.1f} × {DOMAIN_Y:.1f} × {DOMAIN_Z:.1f} mm")
print(f"  Inlet ext / Outlet  : {INLET_EXT:.1f} / {OUTLET_EXT:.1f} mm")

# ═══════════════════════════════════════════════════════════════════════════════
#  01 — GAS DOMAIN
#  Box (0→DX, 0→DY, 0→DZ) with 42 tube bores subtracted.
#  Tube axis = Y direction (rotation=(-90,0,0) rotates default Z-axis to +Y).
# ═══════════════════════════════════════════════════════════════════════════════
print("\nBuilding 01_Gas_Domain …")

locs_tubes = [Location((cx, DOMAIN_Y / 2, cz)) for cx, cz in CENTERS]

with BuildPart() as gas:
    # Outer rectangular box — minimum corner at world origin
    Box(DOMAIN_X, DOMAIN_Y, DOMAIN_Z,
        align=(Align.MIN, Align.MIN, Align.MIN))

    # Subtract all tube bores in one operation
    with Locations(*locs_tubes):
        Cylinder(radius=TUBE_OD / 2, height=DOMAIN_Y,
                 rotation=(-90, 0, 0), mode=Mode.SUBTRACT)

export_step(gas.part, "step/01_Gas_Domain.step")
print("  ✓  step/01_Gas_Domain.step")

# ═══════════════════════════════════════════════════════════════════════════════
#  02 — TUBE WALL (solid steel annuli, optional CHT body)
#  42 annular cylinders: OD = TUBE_OD, ID = TUBE_ID, height = DOMAIN_Y.
#  Build each tube individually to guarantee clean boolean subtraction.
# ═══════════════════════════════════════════════════════════════════════════════
print("Building 02_Tube_Wall …")

with BuildPart() as twall:
    for cx, cz in CENTERS:
        loc = Location((cx, DOMAIN_Y / 2, cz))
        with Locations(loc):
            # Outer cylinder
            Cylinder(radius=TUBE_OD / 2, height=DOMAIN_Y,
                     rotation=(-90, 0, 0))
            # Subtract inner bore → annular section
            Cylinder(radius=TUBE_ID / 2, height=DOMAIN_Y,
                     rotation=(-90, 0, 0), mode=Mode.SUBTRACT)

export_step(twall.part, "step/02_Tube_Wall.step")
print("  ✓  step/02_Tube_Wall.step")

# ─── Boundary naming guide ────────────────────────────────────────────────────
print()
print("─" * 60)
print("STAR-CCM+ BOUNDARY NAMING GUIDE")
print("─" * 60)
print()
print("01_Gas_Domain.step — 7 boundaries:")
print(f"  Z = 0 face             → Gas_Inlet")
print(f"  Z = {DOMAIN_Z:.1f} face      → Gas_Outlet")
print(f"  X = 0 face             → Symmetry_Left")
print(f"  X = {DOMAIN_X:.1f} face    → Symmetry_Right")
print(f"  Y = 0 face             → Symmetry_Bottom")
print(f"  Y = {DOMAIN_Y:.1f} face    → Symmetry_Top")
print(f"  {len(CENTERS)} cylindrical surfaces → Tube_Wall_Outer")
print()
print("02_Tube_Wall.step — 3 boundaries (CHT):")
print(f"  42 outer cyl. surfaces → Tube_Wall_Outer  (interface Gas↔Steel)")
print(f"  42 inner cyl. surfaces → Tube_Wall_Inner  (T = 195 °C = T_sat @ 14 bar)")
print(f"  Annular end faces      → Tube_Ends        (symmetry / adiabatic)")
print()
print("─" * 60)
print("CFD BOUNDARY CONDITIONS SUMMARY")
print("─" * 60)
print(f"  Gas_Inlet  : Velocity Inlet  V = 8 m/s, T = 900 °C")
print(f"  Gas_Outlet : Pressure Outlet p = 0 Pa (gauge)")
print(f"  Tube_Wall_Outer : Wall — isothermal T = 195 °C  (or CHT interface)")
print(f"  Symmetry_*  : Symmetry plane")
print(f"  Symmetry_Top/Bottom : Symmetry (or Periodic pair in Y)")
