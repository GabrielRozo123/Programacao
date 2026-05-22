"""
Haver & Boecker Style Industrial Vibrating Screen
DEM Simulation Geometry for Simcenter STAR-CCM+ (Meshfree DEM)

Coordinate system
  X : screen width direction
  Y : vertical, +Y is up, gravity = -Y
  Z : screen length direction (feed -> discharge)
  Deck top surface placed at Y = 0

Parts produced
  Screen.step  -> Solid Region in STAR-CCM+
  Domain.step  -> Particle Region in STAR-CCM+
  HB_VibScreen_DEM.step -> combined assembly (optional import)

Adapted from STAR-CCM+ Meshfree DEM tutorial (excavator shovel).
Reference equipment: Haver & Boecker TITAN series linear vibrating screen.
"""

import cadquery as cq
import os
import sys

# ================================================================
# 1. PARAMETERS (all in mm)
# ================================================================

# --- Screen deck aperture (wire/bar mesh) ---
ap      = 38.0          # square aperture opening [mm]
bar     = 4.0           # bar/wire width [mm]
pitch   = ap + bar      # centre-to-centre pitch = 42 mm

# Aperture grid counts
n_x     = 10            # apertures along X (width)
n_z     = 15            # apertures along Z (length)

# Deck geometry
t_deck  = 10.0          # deck plate thickness [mm]

# --- Frame ---
wall    = 12.0          # side-wall thickness [mm]
frame_H = 180.0         # frame height below deck bottom [mm]

# --- Derived screen dimensions ---
# Deck inner plate (including edge bars on all sides)
deck_W  = bar + n_x * pitch     # 4 + 10*42 = 424 mm
deck_L  = bar + n_z * pitch     # 4 + 15*42 = 634 mm
# Outer frame
frame_W = deck_W + 2 * wall     # 424 + 24  = 448 mm
frame_L = deck_L + 2 * wall     # 634 + 24  = 658 mm
H_total = t_deck + frame_H      # 10 + 180  = 190 mm

# --- Domain (Particle Region) ---
dom_margin  = 5.0               # clearance around frame footprint [mm]
dom_above   = 400.0             # domain height above deck top [mm]
dom_below   = H_total + 50.0    # 190 + 50 = 240 mm below deck top

dom_W   = frame_W + 2 * dom_margin   # 448 + 10 = 458 mm
dom_L   = frame_L + 2 * dom_margin   # 658 + 10 = 668 mm
dom_H   = dom_above + dom_below       # 400 + 240 = 640 mm
dom_cY  = (dom_above - dom_below) / 2.0   # = 80 mm  (domain centre Y)

# ================================================================
# 2. BUILD SCREEN BODY (single watertight solid)
#
# Strategy
#   a) Outer box  : frame_W x H_total x frame_L, top at Y=0
#   b) Inner void : deck_W x frame_H x deck_L, from Y=-t_deck to Y=-H_total
#      -> this hollows the frame below the deck plate
#   c) Apertures  : cut rarray of squares through the deck plate
# ================================================================

# (a) Outer solid block ─ top at Y=0, bottom at Y=-H_total
screen = (
    cq.Workplane("XY")
    .box(frame_W, H_total, frame_L)
    .translate((0, -H_total / 2.0, 0))
)

# (b) Interior void: hollows the space below the deck
#     Void Y range : Y = -t_deck  to  Y = -H_total
#     Void centre Y: -(t_deck + frame_H/2) = -(10 + 90) = -100 mm
void_cY = -(t_deck + frame_H / 2.0)
interior_void = (
    cq.Workplane("XY")
    .box(deck_W, frame_H, deck_L)
    .translate((0, void_cY, 0))
)
screen = screen.cut(interior_void)

# (c) Apertures through deck plate (from top face, depth = t_deck)
#     rarray is centred → aperture centres from -(n-1)/2*pitch to +(n-1)/2*pitch
#     Edge bars: (deck_W - (n_x-1)*pitch - ap) / 2 = bar = 4 mm  ✓
screen = (
    screen
    .faces(">Y")        # top face of the deck plate  (at Y = 0)
    .workplane()        # XZ workplane on top face, +Y normal
    .rarray(pitch, pitch, n_x, n_z)
    .rect(ap, ap)
    .cutBlind(-t_deck - 0.5)   # cut through deck + 0.5 mm into hollow → open aperture
)

print("[Screen] Solid built successfully.")

# ================================================================
# 3. BUILD DOMAIN BOX (Particle Region)
#     Y: dom_cY ± dom_H/2  =  (-240)  to  (+400)
# ================================================================
domain = (
    cq.Workplane("XY")
    .box(dom_W, dom_H, dom_L)
    .translate((0, dom_cY, 0))
)
print("[Domain] Box built successfully.")

# ================================================================
# 4. EXPORT
# ================================================================
output_dir = os.path.dirname(os.path.abspath(__file__))

screen_path = os.path.join(output_dir, "Screen.step")
domain_path = os.path.join(output_dir, "Domain.step")
assy_path   = os.path.join(output_dir, "HB_VibScreen_DEM.step")

cq.exporters.export(screen, screen_path)
print(f"[OK] Screen.step  -> {screen_path}")

cq.exporters.export(domain, domain_path)
print(f"[OK] Domain.step  -> {domain_path}")

# Combined assembly STEP (both bodies in one file with names)
assy = cq.Assembly()
assy.add(screen, name="Screen", color=cq.Color("gray"))
assy.add(domain, name="Domain", color=cq.Color(0.3, 0.6, 1.0, 0.15))
assy.save(assy_path)
print(f"[OK] HB_VibScreen_DEM.step -> {assy_path}")

# ================================================================
# 5. SUMMARY
# ================================================================
print()
print("=" * 62)
print("  HAVER & BOECKER VIBRATING SCREEN  –  GEOMETRY SUMMARY")
print("=" * 62)
print(f"  Aperture (square) : {ap:.0f} × {ap:.0f} mm")
print(f"  Bar width          : {bar:.0f} mm   |   Pitch : {pitch:.0f} mm")
print(f"  Grid               : {n_x} × {n_z} = {n_x*n_z} apertures")
print(f"  Deck plate         : {deck_W:.0f} × {deck_L:.0f} mm  (inner)")
print(f"  Deck thickness     : {t_deck:.0f} mm")
print(f"  Frame (outer)      : {frame_W:.0f} × {frame_L:.0f} mm")
print(f"  Frame height       : {frame_H:.0f} mm  (below deck)")
print(f"  Screen total H     : {H_total:.0f} mm")
print()
print(f"  Domain box         : {dom_W:.0f} × {dom_H:.0f} × {dom_L:.0f} mm (W×H×L)")
print(f"  Domain above deck  : {dom_above:.0f} mm")
print(f"  Domain below deck  : {dom_below:.0f} mm  (covers full frame + 50 mm)")
print()
print("  Files written:")
print(f"    Screen.step          ← assign as Solid Region")
print(f"    Domain.step          ← assign as Particle Region")
print(f"    HB_VibScreen_DEM.step ← combined assembly (optional)")
print("=" * 62)
