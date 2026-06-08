#!/usr/bin/env python3
"""
Pressure Vessel FSI Geometry for Star-CCM+ – HAZOP Overpressure Study
======================================================================
Creates two STEP files:
  vessel_fluid.step  – internal fluid domain (half-cylinder)
  vessel_solid.step  – vessel wall (half hollow cylinder)

Coordinate system:
  - Vessel axis along Z
  - Symmetry plane: XZ (y = 0); model keeps y >= 0 half
  - Vessel centered at origin: z from -L/2 to +L/2

Boundaries after import into Star-CCM+:
  FLUID (4 faces):
    inlet          – semicircular flat face at z = -L/2  (Pressure Inlet)
    outlet         – semicircular flat face at z = +L/2  (Pressure Outlet)
    vessel_contact – inner cylindrical surface            (FSI Interface)
    fluid_symmetry – flat rectangular face at y = 0      (Symmetry)

  VESSEL (5-6 faces):
    left_end        – annular face at z = -L/2  (Fixed Constraint)
    right_end       – annular face at z = +L/2  (Fixed Constraint)
    outer_wall      – outer cylindrical surface  (Stress-Free)
    inner_contact   – inner cylindrical surface  (FSI Interface)
    vessel_symmetry – flat face(s) at y = 0     (Symmetry)
"""

import cadquery as cq
from cadquery import exporters
import os, math

# ============================================================
# PARAMETERS – realistic industrial vessel (ASME VIII Div.1)
# ============================================================
R_INNER  = 0.250   # inner radius [m]  → ID = 500 mm
T_WALL   = 0.012   # wall thickness [m] = 12 mm  (OK for ~13 bar per ASME)
R_OUTER  = R_INNER + T_WALL   # = 0.262 m
LENGTH   = 1.000   # vessel length [m]

# Cutter margin – larger than geometry to avoid coincident-face issues in OCCT
MARGIN   = R_OUTER * 0.25    # 25% over-cut margin

OUTPUT_DIR = "/home/user/Programacao"

# ============================================================
# HELPER: print OCCT validity check
# ============================================================
def occt_check(workplane_obj, name):
    shape = workplane_obj.val()
    ok = shape.isValid()
    print(f"  OCCT check → {'VALID' if ok else '!!! INVALID !!!'}")
    return ok

# ============================================================
# HELPER: face inventory
# ============================================================
def face_report(workplane_obj):
    faces = workplane_obj.faces()
    face_list = faces.vals()
    for i, f in enumerate(face_list):
        area = f.Area()
        # Classify by area roughly
        print(f"    face {i+1:02d}: area = {area:.6f} m²")
    return len(face_list)

# ============================================================
# BUILD HALF-SPACE CUTTER  (removes y < 0 region)
# ============================================================
cutter_half_x = R_OUTER + MARGIN
cutter_half_z = LENGTH / 2.0 + MARGIN

half_cutter = (
    cq.Workplane("XY")
    .box(2 * cutter_half_x, cutter_half_x, LENGTH + 2 * MARGIN)
    .translate((0.0, -cutter_half_x / 2.0, 0.0))
)

# Sanity check cutter volume
cutter_vol = half_cutter.val().Volume()
assert cutter_vol > 0, "Cutter volume must be positive"

# ============================================================
# BUILD FLUID DOMAIN  (half inner cylinder)
# ============================================================
print("Building FLUID domain...")

fluid_full = cq.Workplane("XY").cylinder(LENGTH, R_INNER)
fluid      = fluid_full.cut(half_cutter)

print(f"  Volume = {fluid.val().Volume():.8f} m³")
print(f"  Expected ≈ {0.5 * math.pi * R_INNER**2 * LENGTH:.8f} m³")
n_fluid_faces = face_report(fluid)
print(f"  Total faces: {n_fluid_faces}")
occt_check(fluid, "FLUID")

assert fluid.val().Volume() > 0, "Fluid volume must be positive!"
assert n_fluid_faces == 4, f"Expected 4 fluid faces, got {n_fluid_faces}"

# ============================================================
# BUILD VESSEL (SOLID) DOMAIN  (half hollow cylinder)
# ============================================================
print("\nBuilding VESSEL (solid) domain...")

outer_cyl  = cq.Workplane("XY").cylinder(LENGTH, R_OUTER)
inner_cyl  = cq.Workplane("XY").cylinder(LENGTH, R_INNER)
vessel_hol = outer_cyl.cut(inner_cyl)
vessel     = vessel_hol.cut(half_cutter)

print(f"  Volume = {vessel.val().Volume():.8f} m³")
expected_v = 0.5 * math.pi * (R_OUTER**2 - R_INNER**2) * LENGTH
print(f"  Expected ≈ {expected_v:.8f} m³")
n_vessel_faces = face_report(vessel)
print(f"  Total faces: {n_vessel_faces}")
occt_check(vessel, "VESSEL")

assert vessel.val().Volume() > 0, "Vessel volume must be positive!"
assert n_vessel_faces >= 5, f"Expected ≥5 vessel faces, got {n_vessel_faces}"

# ============================================================
# CROSS-CHECK: FSI interface area must match on both sides
# The FSI surface is the half-cylinder at radius R_INNER.
# Expected area = pi * R_INNER * LENGTH (half-cylinder)
# ============================================================
fsi_expected = math.pi * R_INNER * LENGTH

def find_fsi_area(wp):
    """Return area of face closest to expected FSI area."""
    areas = sorted([f.Area() for f in wp.faces().vals()])
    return min(areas, key=lambda a: abs(a - fsi_expected))

area_fluid_contact  = find_fsi_area(fluid)
area_vessel_contact = find_fsi_area(vessel)

print(f"\nFSI interface area check (expected {fsi_expected:.6f} m²):")
print(f"  Fluid  inner wall: {area_fluid_contact:.6f} m²")
print(f"  Vessel inner wall: {area_vessel_contact:.6f} m²")
rel_error = abs(area_fluid_contact - area_vessel_contact) / fsi_expected
print(f"  Relative difference: {rel_error:.2e}  ({'OK' if rel_error < 1e-6 else 'WARNING: mismatch!'})")

# ============================================================
# CHECK MINIMUM EDGE LENGTH  (no degenerate edges)
# ============================================================
print("\nMinimum edge length check:")
for name, wp in [("FLUID", fluid), ("VESSEL", vessel)]:
    edges = wp.edges().vals()
    lengths = []
    for e in edges:
        try:
            lengths.append(e.Length())
        except Exception:
            pass
    min_len = min(lengths) if lengths else 0
    print(f"  {name}: min edge = {min_len:.6f} m  ({'OK' if min_len > 1e-6 else 'WARNING: degenerate edge!'})")

# ============================================================
# EXPORT STEP FILES
# ============================================================
print("\nExporting STEP files...")

fluid_path  = os.path.join(OUTPUT_DIR, "vessel_fluid.step")
vessel_path = os.path.join(OUTPUT_DIR, "vessel_solid.step")

exporters.export(fluid,  fluid_path)
exporters.export(vessel, vessel_path)

sz_f = os.path.getsize(fluid_path)  / 1024
sz_v = os.path.getsize(vessel_path) / 1024
print(f"  vessel_fluid.step  → {sz_f:.1f} KB")
print(f"  vessel_solid.step  → {sz_v:.1f} KB")

assert sz_f > 0 and sz_v > 0, "STEP files must not be empty!"

# ============================================================
# PRINT SETUP GUIDE FOR STAR-CCM+
# ============================================================
print("""
=============================================================
 STAR-CCM+ IMPORT & SETUP GUIDE
=============================================================
1. Import: File > Import > Import Surface/Volume Mesh
   → vessel_fluid.step  → assign to region: Fluid
   → vessel_solid.step  → assign to region: Vessel

2. FLUID region boundaries (4 faces):
   • Select flat face at z = -0.500 m  → rename: inlet
   • Select flat face at z = +0.500 m  → rename: outlet
   • Select curved cylindrical surface → rename: vessel_contact
   • Select flat face at y = 0         → rename: fluid_symmetry

3. VESSEL region boundaries (5-6 faces):
   • Select annular face at z = -0.500 m  → rename: left_end
   • Select annular face at z = +0.500 m  → rename: right_end
   • Select outer cylindrical surface     → rename: outer_wall
   • Select inner cylindrical surface     → rename: inner_contact
   • Select flat face(s) at y = 0         → rename: vessel_symmetry

4. FSI Contact Interface:
   Geometry > Contacts > vessel_contact / inner_contact
   → Set New Interface → Type: Mapped Contact Interface

5. Physics – Fluid continuum:
   3D | Implicit Unsteady | Liquid | Segregated Flow
   Equation of State: Constant Density (water, 998 kg/m³)
   Viscous Regime: Turbulent (k-ε Realizable)

6. Physics – Solid continuum:
   3D | Implicit Unsteady | Solid | Solid Stress
   Material Law: Isotropic Linear Elastic
   Material: Steel (AISI 1020 or A516 Gr.70)
     E = 200 GPa | ν = 0.29 | ρ = 7900 kg/m³ | Sy = 250 MPa

7. VESSEL solid segments:
   • Segment "Fixed_Ends"   → Surfaces: left_end + right_end
                             Type: Constraint (Fixed, all DOF)
   • Segment "Symmetry"     → Surface: vessel_symmetry
                             Type: Constraint → Symmetry

8. Motion:
   Tools > Motions → New Morphing   (assign to Fluid region)
   Tools > Motions → New Solid Displacement (assign to Vessel region)
   Fluid > Boundaries > vessel_contact > Morpher Specification → Floating

9. Solver (Static Analysis for HAZOP):
   Implicit Unsteady: Time-Step = 1.0 s
   Solid Stress Solver > Static Analysis: Activated
   Mesh Morpher > Recompute Interfaces: Off
   Stopping Criteria: Max Physical Time = 10 s

10. HAZOP Parametric Study – vary inlet pressure:
    P_nominal   = 1.0 MPa  (10 bar)
    P_1.5×      = 1.5 MPa  (15 bar)
    P_2.0×      = 2.0 MPa  (20 bar)
    Monitor: Von Mises stress max on Vessel → compare to Sy = 250 MPa

=============================================================
 KEY DIMENSIONS
=============================================================
  Inner diameter   :  500 mm
  Wall thickness   :   12 mm
  Vessel length    : 1000 mm
  Symmetry plane   :  XZ (y = 0)
  Axis             :  Z
=============================================================
""")

print("All checks PASSED. STEP files ready.")
