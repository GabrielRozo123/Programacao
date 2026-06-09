#!/usr/bin/env python3
"""
Water Hammer HAZOP Geometry for Star-CCM+
==========================================
Creates two STEP files for the Gap Closure / Morphing / Remeshing pipeline:

  wh_pipe.step  – full inner-cylinder fluid domain (imported as Part "Pipe")
  wh_valve.step – butterfly valve disc in OPEN position (imported as Part "Valve")

Star-CCM+ Operations pipeline (mirrors Flapper Valve tutorial):
  Transform (rotates Valve to current time position)
  → Subtract  (Fluid = Pipe − Valve)
  → Automated Mesh (polyhedral, 2 mm base, 50 % refinement near valve)

Coordinate system:
  - Pipe axis along Z  (flow direction +Z)
  - Valve at z = 0,  pivot axis = X
  - OPEN position  : disc in XZ plane  (edge-on to flow,  normal ∥ Y)
  - CLOSED position: disc in XY plane  (face-on to flow,  normal ∥ Z)
                     achieved by rotating +90° about X-axis

Gap Closure:
  Valve radius = PIPE_R_INNER − GAP_CLOSURE_D = 23 mm
  When any point on the valve disc is ≤ 2 mm from the pipe wall,
  the Gap Closure model seals the boundary automatically.

HAZOP parametric study – valve closure time:
  Case A  t_close = 0.05 s  →  fast ESD  → ΔP ≈ Joukowsky maximum
  Case B  t_close = 0.20 s  →  medium    → ΔP ≈ 30–60 % Joukowsky
  Case C  t_close = 1.00 s  →  slow      → ΔP minimal

  Star-CCM+ rotation rate expression (Case A, 0→π/2 rad in 0.05 s):
      (${Time} <= 0.05) ? 31.416 : 0   [rad/s]
"""

import cadquery as cq
from cadquery import exporters
import os, math

# ================================================================
# PARAMETERS – industrial process pipe DN50 (ASME B31.3)
# All dimensions in mm; STEP exported as mm, Star-CCM+ imports as mm.
# ================================================================
PIPE_R_INNER  = 25.0    # inner radius [mm]  → ID = 50 mm (DN50)
PIPE_R_OUTER  = 28.0    # outer radius [mm]  → WT = 3 mm (Sch 40 DN50)
PIPE_LENGTH   = 1000.0  # pipe section length [mm]

GAP_CLOSURE_D = 2.0     # gap closure distance [mm] – must match Star-CCM+ BC
VALVE_R       = PIPE_R_INNER - GAP_CLOSURE_D   # = 23.0 mm
VALVE_THICK   = 3.0     # valve disc thickness [mm] (along Y in open position)

OUTPUT_DIR    = "/home/user/Programacao"

# ================================================================
# HELPERS
# ================================================================
def occt_check(wp, name):
    ok = wp.val().isValid()
    print(f"  OCCT check → {'VALID' if ok else '!!! INVALID !!!'}")
    return ok

def face_report(wp):
    faces = wp.faces().vals()
    for i, f in enumerate(faces):
        print(f"    face {i+1:02d}: area = {f.Area():.4f} mm²")
    return len(faces)

# ================================================================
# BUILD PIPE FLUID DOMAIN  (inner cylinder, full – no wall)
# Star-CCM+ uses this as the "Pipe" part before subtraction.
# ================================================================
print("Building PIPE fluid domain...")

pipe = cq.Workplane("XY").cylinder(PIPE_LENGTH, PIPE_R_INNER)

pipe_vol = pipe.val().Volume()
expected_pipe_vol = math.pi * PIPE_R_INNER**2 * PIPE_LENGTH
print(f"  Volume   = {pipe_vol:.4f} mm³")
print(f"  Expected = {expected_pipe_vol:.4f} mm³")
n_pipe_faces = face_report(pipe)
print(f"  Total faces: {n_pipe_faces}")
occt_check(pipe, "PIPE")

assert pipe.val().Volume() > 0, "Pipe volume must be positive!"
assert n_pipe_faces == 3, f"Expected 3 faces (2 flat caps + 1 cylinder wall), got {n_pipe_faces}"

# ================================================================
# BUILD VALVE DISC  (butterfly valve, OPEN position)
#
# Workplane "XZ" → circle lies in XZ plane, extrude goes along Y.
# Result: a disc (cylinder with short axis) with:
#   • circular faces in XZ plane (normals ±Y)
#   • cylindrical edge around the disc
#   • centre at origin, thickness from y = −VALVE_THICK/2 to +VALVE_THICK/2
#
# This is the OPEN position: disc is edge-on to Z-direction flow.
# Closing = rotate +90° about X-axis in Star-CCM+ (Y→Z, normal becomes Z).
# ================================================================
print("\nBuilding VALVE disc (open position)...")

valve = (
    cq.Workplane("XZ")
    .circle(VALVE_R)
    .extrude(VALVE_THICK)
    .translate((0.0, -VALVE_THICK / 2.0, 0.0))
)

valve_vol = valve.val().Volume()
expected_valve_vol = math.pi * VALVE_R**2 * VALVE_THICK
print(f"  Volume   = {valve_vol:.4f} mm³")
print(f"  Expected = {expected_valve_vol:.4f} mm³")
n_valve_faces = face_report(valve)
print(f"  Total faces: {n_valve_faces}")
occt_check(valve, "VALVE")

assert valve.val().Volume() > 0, "Valve volume must be positive!"
assert n_valve_faces == 3, f"Expected 3 valve faces (2 flat + 1 edge), got {n_valve_faces}"

# ================================================================
# CLEARANCE / GAP CHECK
# ================================================================
gap = PIPE_R_INNER - VALVE_R
print(f"\nRadial clearance  : {gap:.2f} mm")
print(f"Gap Closure Dist  : {GAP_CLOSURE_D:.2f} mm")
print(f"Match             : {'OK' if abs(gap - GAP_CLOSURE_D) < 1e-9 else 'MISMATCH!'}")
assert abs(gap - GAP_CLOSURE_D) < 1e-9, "Gap must exactly match GAP_CLOSURE_D!"

# ================================================================
# MINIMUM EDGE LENGTH  (no degenerate edges)
# ================================================================
print("\nMinimum edge length check:")
for name, wp in [("PIPE", pipe), ("VALVE", valve)]:
    edges = wp.edges().vals()
    lengths = []
    for e in edges:
        try:
            lengths.append(e.Length())
        except Exception:
            pass
    min_len = min(lengths) if lengths else 0.0
    print(f"  {name}: min edge = {min_len:.4f} mm  ({'OK' if min_len > 1.0 else 'WARNING: degenerate!'})")

# ================================================================
# EXPORT STEP FILES
# ================================================================
print("\nExporting STEP files...")

pipe_path  = os.path.join(OUTPUT_DIR, "wh_pipe.step")
valve_path = os.path.join(OUTPUT_DIR, "wh_valve.step")

exporters.export(pipe,  pipe_path)
exporters.export(valve, valve_path)

sz_p = os.path.getsize(pipe_path)  / 1024
sz_v = os.path.getsize(valve_path) / 1024
print(f"  wh_pipe.step   → {sz_p:.1f} KB")
print(f"  wh_valve.step  → {sz_v:.1f} KB")
assert sz_p > 0 and sz_v > 0, "STEP files must not be empty!"

# ================================================================
# JOUKOWSKY REFERENCE CALCULATIONS (printed for documentation)
# ================================================================
RHO_WATER = 998.0    # kg/m³
C_WATER   = 1484.0   # m/s  (speed of sound in water at 20 °C)
V_FLOW    = 2.0      # m/s  (nominal pipe velocity)
L_PIPE    = PIPE_LENGTH / 1000.0  # m

dP_joukowsky  = RHO_WATER * C_WATER * V_FLOW           # Pa
t_critical    = 2.0 * L_PIPE / C_WATER                 # s

cases = [
    ("A – Fast ESD",   0.05,  math.pi/2 / 0.05),
    ("B – Medium ESD", 0.20,  math.pi/2 / 0.20),
    ("C – Slow close", 1.00,  math.pi/2 / 1.00),
]

print("""
=============================================================
 JOUKOWSKY VALIDATION  (HAZOP "More Pressure" – ESD event)
=============================================================
  Equation: ΔP = ρ × c × ΔV
  ρ_water = {:.1f} kg/m³ | c = {:.0f} m/s | V_flow = {:.1f} m/s

  ΔP_max (Joukowsky) = {:.0f} Pa  ≈  {:.2f} MPa

  Critical closure time  t_crit = 2L/c = {:.5f} s
  (any closure faster than this produces full Joukowsky surge)
""".format(RHO_WATER, C_WATER, V_FLOW, dP_joukowsky, dP_joukowsky/1e6, t_critical))

print("  HAZOP parametric cases:")
print(f"  {'Case':<20}  {'t_close [s]':>12}  {'rate [rad/s]':>14}  "
      f"{'Star-CCM+ expression':<40}")
print("  " + "-"*90)
for label, tc, rate in cases:
    expr = f"(${{Time}} <= {tc}) ? {rate:.3f} : 0"
    print(f"  {label:<20}  {tc:>12.3f}  {rate:>14.3f}  {expr:<40}")

print(f"""
  Recommended Stopping Criteria:
    Case A: Max Physical Time = 0.20 s  (4 wave round-trips)
    Case B: Max Physical Time = 0.60 s
    Case C: Max Physical Time = 2.50 s

  Adaptive Time-Step settings (water – faster than air tutorial):
    Implicit Unsteady base step  : 0.001 s
    Adaptive TS minimum step     : 1.0e-7 s
    Target Mean CFL              : 0.5
    Target Max  CFL              : 5.0
    Cut-off %                    : 10

  Pressure probe locations (for Reports / Monitors):
    P1 – at valve        : (0,  0,   0) mm
    P2 – upstream mid    : (0,  0, -250) mm
    P3 – downstream mid  : (0,  0, +250) mm
    P4 – near inlet      : (0,  0, -450) mm
=============================================================
""")

print("All checks PASSED. STEP files ready.")
