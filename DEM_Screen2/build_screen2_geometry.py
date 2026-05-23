"""
Haver & Boecker Style Vibrating Screen — DEM Geometry v2
Build123d version (adapted from user code)

Coordinate system
  X : screen length  (feed at -X/high end, discharge at +X/low end)
  Y : screen width
  Z : vertical  →  gravity = [0, 0, -9.81] m/s² in STAR-CCM+

Screen is inclined 15° around Y axis (rotation of -15°):
  -X end rises in Z (feed / high end)
  +X end drops in Z (discharge / low end)

Parts exported
  Screen.step          → Solid Region  in STAR-CCM+
  Domain.step          → Particle Region in STAR-CCM+
  HB_Screen2_DEM.step  → combined assembly (optional import)
"""

from build123d import *
import math, os

output_dir = os.path.dirname(os.path.abspath(__file__))

# ================================================================
# 1. PARAMETERS
# ================================================================
L_screen  = 1000.0        # screen length [mm]  – X axis
W_screen  =  500.0        # screen width  [mm]  – Y axis
aperture  =   10.0        # square aperture [mm]
wire_t    =    3.0        # wire / bar thickness [mm]
spacing   = aperture + wire_t   # = 13 mm centre-to-centre
wall_h    =  100.0        # side-wall height [mm]
tilt_deg  =   15.0        # inclination angle [°]

# aperture grid (20 mm edge margin each side)
nx = int((L_screen - 20) / spacing)   # = 75 along length
ny = int((W_screen - 20) / spacing)   # = 36 along width
print(f"Aperture grid: {nx} × {ny} = {nx*ny} holes ({aperture:.0f} mm square)")

# ================================================================
# 2. SCREEN DECK  (perforated plate in XY plane, extruded +Z)
# ================================================================
print("Building screen deck ...")
with BuildPart() as deck_bp:
    with BuildSketch(Plane.XY):
        Rectangle(L_screen, W_screen)
        with GridLocations(spacing, spacing, nx, ny):
            Rectangle(aperture, aperture, mode=Mode.SUBTRACT)
    extrude(amount=wire_t)

# ================================================================
# 3. SIDE WALLS  (+Y and -Y edges, height = wall_h in Z)
# ================================================================
print("Building side walls ...")
with BuildPart() as walls_bp:
    with BuildSketch(Plane.XY):
        with Locations((0,  W_screen / 2 + wire_t / 2)):
            Rectangle(L_screen, wire_t)
    extrude(amount=wall_h)

    with BuildSketch(Plane.XY):
        with Locations((0, -(W_screen / 2 + wire_t / 2))):
            Rectangle(L_screen, wire_t)
    extrude(amount=wall_h)

# ================================================================
# 4. FEED CHUTE  (hollow box at high / feed end, tilted with screen)
#    Sits on top of the side walls: base at Z = wall_h + wire_t
# ================================================================
print("Building feed chute ...")
chute_z_base = wall_h + wire_t       # = 103 mm above deck base
chute_x_ctr  = -L_screen / 2 + 100  # = -400 mm (100 mm from feed end)

with BuildPart() as chute_bp:
    with BuildSketch(Plane.XY.offset(chute_z_base)):
        with Locations((chute_x_ctr, 0)):
            Rectangle(200, W_screen)
    extrude(amount=50.0)
    # hollow out — keep 10 mm walls
    top_face = chute_bp.faces().sort_by(Axis.Z)[-1]
    with BuildSketch(top_face):
        with Locations((chute_x_ctr, 0)):
            Rectangle(180, W_screen - 20)
    extrude(amount=-50.0, mode=Mode.SUBTRACT)

# ================================================================
# 5. APPLY 15° INCLINATION (all parts rotate together)
# ================================================================
print("Applying 15° inclination ...")
deck_t  = deck_bp.part.rotate(Axis.Y,  -tilt_deg)
walls_t = walls_bp.part.rotate(Axis.Y, -tilt_deg)
chute_t = chute_bp.part.rotate(Axis.Y, -tilt_deg)

# Combined Screen compound (→ Solid Region)
screen = Compound(children=[deck_t, walls_t, chute_t])

# ================================================================
# 6. DOMAIN BOX  (→ Particle Region)
#
# After -15° rotation around Y the tilted-screen bounding box is:
#   Z_low  ≈ -(L/2)·sin(15°)                    ≈ -129 mm  (discharge deck)
#   Z_high ≈ +(L/2)·sin(15°) + wall_h·cos(15°)  ≈ +226 mm  (feed wall top)
#
# Domain adds:
#   space_above : injection zone above feed chute
#   space_below : undersize collection zone
# ================================================================
rad  = math.radians(tilt_deg)
z_low  = -(L_screen / 2) * math.sin(rad)                         # ≈ -129 mm
z_high = (L_screen / 2) * math.sin(rad) + wall_h * math.cos(rad) # ≈ +226 mm

margin_xy   = 100.0   # clearance around screen footprint [mm]
space_above = 500.0   # injection / flight zone above screen [mm]
space_below = 200.0   # undersize collection below low end [mm]

dom_X = L_screen + 2 * margin_xy                    # 1200 mm
dom_Y = W_screen + 2 * wire_t + 2 * margin_xy       #  706 mm
dom_Z = (z_high - z_low) + space_above + space_below #  855 mm

# Domain bottom at z_low - space_below, top at z_high + space_above
dom_z_bot = z_low  - space_below   # ≈ -329 mm
dom_z_top = z_high + space_above   # ≈ +726 mm
dom_z_ctr = (dom_z_bot + dom_z_top) / 2  # ≈ +199 mm

with BuildPart() as domain_bp:
    Box(dom_X, dom_Y, dom_Z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER))

domain = domain_bp.part.move(Location((0, 0, dom_z_ctr)))

# ================================================================
# 7. EXPORT
# ================================================================
screen_path = os.path.join(output_dir, "Screen.step")
domain_path = os.path.join(output_dir, "Domain.step")
assy_path   = os.path.join(output_dir, "HB_Screen2_DEM.step")

export_step(screen, screen_path)
print(f"[OK] Screen.step")

export_step(domain, domain_path)
print(f"[OK] Domain.step")

combined = Compound(children=[screen, domain])
export_step(combined, assy_path)
print(f"[OK] HB_Screen2_DEM.step")

# ================================================================
# 8. SUMMARY
# ================================================================
print()
print("=" * 64)
print("  HB VIBRATING SCREEN v2  —  GEOMETRY SUMMARY")
print("=" * 64)
print(f"  Screen:    {L_screen:.0f} × {W_screen:.0f} mm | Inclination: {tilt_deg:.0f}°")
print(f"  Aperture:  {aperture:.0f} × {aperture:.0f} mm | Wire: {wire_t:.0f} mm | Pitch: {spacing:.0f} mm")
print(f"  Grid:      {nx} × {ny} = {nx*ny} apertures")
print(f"  Screen Z:  [{z_low:.0f}, {z_high:.0f}] mm  (discharge to feed wall top)")
print()
print(f"  Domain:    {dom_X:.0f} × {dom_Y:.0f} × {dom_Z:.0f} mm  (X × Y × Z)")
print(f"  Domain Z:  [{dom_z_bot:.0f}, {dom_z_top:.0f}] mm")
print()
print("  ── STAR-CCM+ Setup ────────────────────────────────────")
print("  Screen  →  Solid Region")
print("  Domain  →  Particle Region")
print("  Gravity:   [0.0, 0.0, -9.81] m/s²  (Z is vertical)")
print()
print("  Injection Volume (New Shape Part > Block in STAR-CCM+):")
print(f"    X: [{chute_x_ctr-90:.0f}, {chute_x_ctr+90:.0f}] mm  (above feed chute)")
print(f"    Y: [-200, +200] mm")
print(f"    Z: [{z_high+60:.0f}, {z_high+360:.0f}] mm  (300 mm above feed end)")
print()
print("  Particle sizes for 10 mm aperture:")
print("    Undersize: d = 7 mm   (passes through 10 mm aperture)")
print("    Oversize:  d = 13 mm  (retained — just above aperture)")
print("=" * 64)
