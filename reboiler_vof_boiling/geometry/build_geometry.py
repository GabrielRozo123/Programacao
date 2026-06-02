"""
Reboiler VOF+Boiling — 2D Pool Boiling Cross-Section
Industrial scenario  : Kettle Reboiler TEMA K  |  n-Pentane at 2.5 bar
Tube side (utility)  : Saturated steam ~ 1.43 bar  |  T_wall = 110°C
Shell side (process) : n-C₅H₁₂ liquid  |  T_sat = 63.5°C  |  ΔT = 46.3 K

Geometry:
  3 columns × 4 rows = 10 full + 4 half-tubes ≡ 12 equivalent tubes
  Triangular staggered pitch  P/D = 1.25  (TEMA standard for reboilers)
  Periodic (symmetry) left/right walls  →  represents infinite bundle width
  Liquid pool below, vapor space above

STAR-CCM+ Boundaries after import (assign manually):
  Bottom face  → "Inlet"       P = 250 kPa, T = 336.7 K, alpha_liq = 1.0
  Top face     → "Outlet"      P = 250 kPa, T = 336.7 K, alpha_vap = 1.0
  Left face    → "Symmetry_L"
  Right face   → "Symmetry_R"
  Front face   → "Empty_F"     (2D — 1 cell, periodic or empty BC)
  Back face    → "Empty_B"
  Tube circles → "Tube_Wall"   T_wall = 383 K (110°C), no-slip

Reference: TEMA (2007), NIST n-Pentane saturation data
"""

from build123d import *
import math

# ─── TEMA K parameters ─────────────────────────────────────────────────────────
TUBE_OD_MM  = 19.05          # 3/4" standard TEMA tube
P_OVER_D    = 1.25           # pitch-to-diameter ratio (TEMA recommended for reboilers)
PT_MM       = TUBE_OD_MM * P_OVER_D          # transverse pitch = 23.8125 mm
PR_MM       = PT_MM * math.sin(math.radians(60))  # row pitch (equilateral) = 20.617 mm
TUBE_R_MM   = TUBE_OD_MM / 2                 # outer radius = 9.525 mm

N_COLS      = 3    # full tube columns
N_ROWS      = 4    # tube rows

# Pool margins
MARGIN_BOT_MM = 3.0 * TUBE_OD_MM   # 57.15 mm  — submerged liquid region
MARGIN_TOP_MM = 4.5 * TUBE_OD_MM   # 85.73 mm  — vapor disengagement space

# Extrusion for STEP export (2D slice)
DEPTH_MM    = 1.0

# ─── Derived domain dimensions ─────────────────────────────────────────────────
POOL_W_MM   = N_COLS * PT_MM        # 71.44 mm
Y_ROW_0     = MARGIN_BOT_MM + TUBE_R_MM               # 66.68 mm (first row center)
Y_ROW_LAST  = Y_ROW_0 + (N_ROWS - 1) * PR_MM         # 128.53 mm (last row center)
POOL_H_MM   = Y_ROW_LAST + TUBE_R_MM + MARGIN_TOP_MM  # 223.78 mm

# ─── Tube center positions — triangular staggered pitch ────────────────────────
#
#  Even rows (0, 2): 3 full tubes at  x = PT/2,  3PT/2,  5PT/2
#  Odd  rows (1, 3): 2 full tubes at  x = PT,    2PT
#                    2 half-tubes at  x = 0,      3PT   (periodic boundary)
#
# The half-tubes at x=0 and x=W are cut by the domain edge.
# With Symmetry BC on left/right, they represent a continuous infinite bundle.

tube_centers = []
for row in range(N_ROWS):
    y = Y_ROW_0 + row * PR_MM
    if row % 2 == 0:
        for col in range(N_COLS):
            tube_centers.append((PT_MM / 2.0 + col * PT_MM, y))
    else:
        for col in range(1, N_COLS):
            tube_centers.append((col * PT_MM, y))
        tube_centers.append((0.0, y))            # half-tube at left wall
        tube_centers.append((POOL_W_MM, y))      # half-tube at right wall

n_full  = sum(1 for row in range(N_ROWS)
              for _ in (range(N_COLS) if row % 2 == 0 else range(1, N_COLS)))
n_half  = N_ROWS // 2 * 2     # 2 half-tubes per odd row
n_equiv = n_full + 0.5 * n_half

# ─── Fluid domain: pool rectangle minus tube cross-sections ────────────────────
with BuildPart() as fluid_part:
    with BuildSketch(Plane.XY) as sk:
        # Pool outer boundary — origin at bottom-left corner
        Rectangle(POOL_W_MM, POOL_H_MM, align=(Align.MIN, Align.MIN))
        # Subtract all tube circles (OCCT clips half-tubes at domain boundary)
        with Locations(*[(x, y) for x, y in tube_centers]):
            Circle(TUBE_R_MM, mode=Mode.SUBTRACT)
    extrude(amount=DEPTH_MM)

export_step(fluid_part.part, "01_Fluid_Pool.step")

# ─── Summary ───────────────────────────────────────────────────────────────────
hdr = "=" * 62
print(hdr)
print("  REBOILER VOF+BOILING — Geometry Summary")
print(hdr)
print(f"  Fluid            : n-C₅H₁₂  |  P = 2.5 bar  |  T_sat = 63.5°C")
print(f"  Tube             : {TUBE_OD_MM:.2f} mm OD  (3/4\", BWG 16, SS 316L)")
print(f"  Pitch            : triangular, P/D = {P_OVER_D:.2f}")
print(f"  PT (transverse)  : {PT_MM:.3f} mm")
print(f"  PR (row)         : {PR_MM:.3f} mm  (= PT × sin 60°)")
print(f"  Bundle           : {N_COLS} cols × {N_ROWS} rows")
print(f"  Full tubes       : {n_full}")
print(f"  Half-tubes       : {n_half}  (at Symmetry_L / Symmetry_R)")
print(f"  Equivalent tubes : {n_equiv:.0f}  per periodic cell")
print(f"  Domain width     : {POOL_W_MM:.2f} mm  ({POOL_W_MM/TUBE_OD_MM:.2f} × OD)")
print(f"  Domain height    : {POOL_H_MM:.2f} mm")
print(f"    • Liquid below : {MARGIN_BOT_MM:.1f} mm  ({MARGIN_BOT_MM/TUBE_OD_MM:.1f} × OD)")
print(f"    • Bundle span  : {Y_ROW_LAST - Y_ROW_0 + TUBE_OD_MM:.1f} mm")
print(f"    • Vapor above  : {MARGIN_TOP_MM:.1f} mm  ({MARGIN_TOP_MM/TUBE_OD_MM:.1f} × OD)")
print(f"  Extrusion depth  : {DEPTH_MM:.1f} mm  (2D unit slice)")
print()
print("  STEP exported    : 01_Fluid_Pool.step")
print()
print("  STAR-CCM+ Boundary Assignment:")
print("  ┌──────────────────────────┬──────────────────────────────────────┐")
print("  │ Face                     │ BC type / value                      │")
print("  ├──────────────────────────┼──────────────────────────────────────┤")
print("  │ Bottom (y = 0)           │ Pressure Inlet  P=250 kPa T=336.7 K │")
print("  │ Top    (y = H)           │ Pressure Outlet P=250 kPa T=336.7 K │")
print("  │ Left   (x = 0)           │ Symmetry Plane                       │")
print("  │ Right  (x = W)           │ Symmetry Plane                       │")
print("  │ Front  (z = 0)           │ Empty (2D)                           │")
print("  │ Back   (z = 1 mm)        │ Empty (2D)                           │")
print("  │ Tube circles (12×)       │ Temperature Wall  T = 383 K (110°C) │")
print("  └──────────────────────────┴──────────────────────────────────────┘")
print(hdr)
