"""
Aquatubular Boiler — Convective Pass Geometry Parameters

All dimensions in millimeters unless noted.
Geometry will be built with build123d and exported as STEP for STAR-CCM+.

Two configurations studied:
    - Staggered (recommended for boilers — better heat transfer, more uniform erosion)
    - Inline (reference case for validation against Žukauskas inline correlation)
"""

# ─── Tube geometry ───────────────────────────────────────────────────────────
TUBE_OD    = 38.1          # mm — outer diameter (1.5 in nominal, common industrial)
TUBE_ID    = 33.4          # mm — inner diameter (wall thickness ~2.35 mm, Sch 40)
TUBE_L     = 400.0         # mm — tube length in domain (periodic → one pitch)

# ─── Pitch (staggered) ───────────────────────────────────────────────────────
# ST = transverse pitch (perpendicular to flow)
# SL = longitudinal pitch (in flow direction)
ST_D       = 2.0           # ST/D ratio — transverse
SL_D       = 1.75          # SL/D ratio — longitudinal
ST         = ST_D * TUBE_OD   # mm
SL         = SL_D * TUBE_OD   # mm

# Diagonal pitch (staggered only)
import math
SD         = math.sqrt(SL**2 + (ST/2)**2)   # mm

# ─── Bank dimensions ─────────────────────────────────────────────────────────
N_ROWS_TRANS  = 1          # tubes per row — periodic: model 1 tube width
N_ROWS_LONG   = 8          # number of tube rows in flow direction

# ─── Domain (periodic slice) ─────────────────────────────────────────────────
# Width  = ST  (one transverse pitch → periodic BC left/right)
# Height = N_ROWS_LONG * SL + inlet_ext + outlet_ext
INLET_EXT  = 3 * TUBE_OD  # mm — upstream development length
OUTLET_EXT = 5 * TUBE_OD  # mm — downstream recovery length
DOMAIN_W   = ST
DOMAIN_H   = N_ROWS_LONG * SL + INLET_EXT + OUTLET_EXT
DOMAIN_Z   = TUBE_L        # periodic in Z for 2D-like 3D simulation

# ─── Tube center positions (staggered) ───────────────────────────────────────
def tube_centers_staggered(n_rows: int = N_ROWS_LONG,
                            y_start: float = INLET_EXT + SL / 2) -> list:
    """
    Returns list of (x, y) tube center positions for staggered arrangement.
    x = transverse, y = streamwise (flow direction).
    Row 0 at y_start, alternating rows offset by ST/2 in x.
    """
    centers = []
    for row in range(n_rows):
        y = y_start + row * SL
        x_offset = (ST / 2) if (row % 2 == 1) else 0.0
        # In periodic domain (width=ST), one tube per row
        # Tube center at x=ST/2 for even rows, x=0 (or ST) for odd rows
        x = ST / 2 + x_offset
        if x >= ST:
            x -= ST
        centers.append((round(x, 4), round(y, 4)))
    return centers


def tube_centers_inline(n_rows: int = N_ROWS_LONG,
                         y_start: float = INLET_EXT + SL / 2) -> list:
    """Tube centers for inline arrangement — all at x=ST/2."""
    return [(ST / 2, round(y_start + row * SL, 4)) for row in range(n_rows)]


# ─── Print summary ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("CONVECTIVE PASS GEOMETRY PARAMETERS")
    print("=" * 60)
    print(f"  Tube OD / ID     : {TUBE_OD} / {TUBE_ID} mm")
    print(f"  ST/D, SL/D       : {ST_D}, {SL_D}")
    print(f"  ST, SL           : {ST:.2f}, {SL:.2f} mm")
    print(f"  SD (staggered)   : {SD:.2f} mm")
    print(f"  Number of rows   : {N_ROWS_LONG}")
    print(f"  Domain W x H     : {DOMAIN_W:.1f} x {DOMAIN_H:.1f} mm")
    print()
    print("Staggered tube centers (mm):")
    for i, (x, y) in enumerate(tube_centers_staggered()):
        print(f"  Row {i+1:2d}: x={x:7.2f}, y={y:7.2f}")
    print()
    V_approach = 10.0   # m/s
    V_max = V_approach * ST / (ST - TUBE_OD)
    Re = 1.225 * V_max * (TUBE_OD / 1000) / 1.81e-5   # air at ~700K approx
    print(f"At V_approach = {V_approach} m/s:")
    print(f"  V_max (at min area) = {V_max:.2f} m/s")
    print(f"  Re_D (approx)       = {Re:.0f}")
