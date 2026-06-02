"""
Reboiler VOF+Boiling — Phase 1: Single Tube Pool Boiling (2D)
Geometry: Single horizontal tube immersed in liquid n-C5H12 pool
Export: STEP files for STAR-CCM+

Industrial context: Kettle reboiler (TEMA K) tube in n-Pentane pool
Operating pressure: 2.5 bar | T_sat = 63.5°C | T_wall = 110°C
Tube: 3/4" OD = 19.05 mm, stainless steel 316L
"""

from build123d import *
import math

# ─── Parâmetros geométricos ──────────────────────────────────────────────────
TUBE_OD    = 19.05e-3      # m — 3/4" standard (TEMA)
TUBE_R     = TUBE_OD / 2
TUBE_WT    = 1.65e-3       # m — wall thickness, BWG 16

# Pool dimensions (fluid domain)
POOL_W     = 0.120         # m — 120 mm (6 × OD), symmetric
POOL_H     = 0.150         # m — 150 mm (below tube center: 60 mm, above: 90 mm)

# Tube center position
CX         = POOL_W / 2    # centered horizontally
CY         = 0.060         # 60 mm from bottom (3 × OD submersion)

# STEP extrusion depth (unit slice for 2D)
DEPTH      = 0.001         # 1 mm (treated as 2D in STAR-CCM+)

# ─── Fluid domain (pool region) ───────────────────────────────────────────────
# Rectangle minus the tube interior
with BuildPart() as fluid_domain:
    with BuildSketch(Plane.XZ) as sk_pool:
        Rectangle(POOL_W, POOL_H, align=(Align.MIN, Align.MIN))
        # Remove tube cross-section from fluid domain
        Circle(TUBE_R + TUBE_WT, align=Align.CENTER,
               mode=Mode.SUBTRACT).move(Location((CX, CY)))
    extrude(amount=DEPTH)

# ─── Tube wall solid region (CHT solid) ───────────────────────────────────────
with BuildPart() as tube_wall:
    with BuildSketch(Plane.XZ) as sk_tube:
        Circle(TUBE_R + TUBE_WT, align=Align.CENTER).move(Location((CX, CY)))
        Circle(TUBE_R, align=Align.CENTER,
               mode=Mode.SUBTRACT).move(Location((CX, CY)))
    extrude(amount=DEPTH)

# ─── Export STEP ──────────────────────────────────────────────────────────────
fluid_domain.part.export_step("01_Fluid_Pool.step")
tube_wall.part.export_step("02_Tube_Wall.step")

print("=" * 60)
print("REBOILER VOF+BOILING — Geometry Summary")
print("=" * 60)
print(f"  Tube OD          : {TUBE_OD*1000:.2f} mm  (3/4\" TEMA)")
print(f"  Tube wall thick  : {TUBE_WT*1000:.2f} mm  (BWG 16)")
print(f"  Tube ID          : {(TUBE_R - TUBE_WT)*2*1000:.2f} mm")
print(f"  Pool width       : {POOL_W*1000:.0f} mm  ({POOL_W/TUBE_OD:.1f} × OD)")
print(f"  Pool height      : {POOL_H*1000:.0f} mm")
print(f"  Tube center      : ({CX*1000:.0f}, {CY*1000:.0f}) mm")
print(f"  Submersion depth : {CY*1000:.0f} mm  ({CY/TUBE_OD:.1f} × OD)")
print(f"  Vapor space      : {(POOL_H-CY-TUBE_R-TUBE_WT)*1000:.0f} mm above tube")
print()
print("STEP files exported:")
print("  01_Fluid_Pool.step  — fluid region (VOF: liquid + vapor)")
print("  02_Tube_Wall.step   — tube solid (CHT, T_wall = 110°C)")
print()
print("STAR-CCM+ Import Checklist:")
print("  [ ] Import both regions; assign CHT interface")
print("  [ ] Fluid region: VOF Eulerian, n-C5H12 liq + vap")
print("  [ ] Solid region: conduction only, SS316L")
print("  [ ] Bottom face: pressure inlet (2.5 bar, T=336.6 K, alpha_liq=1.0)")
print("  [ ] Top face: pressure outlet (2.5 bar, T=336.6 K, alpha_vap=1.0)")
print("  [ ] Side faces: symmetry")
print("  [ ] Tube inner wall: T_wall = 383 K (110°C)")
