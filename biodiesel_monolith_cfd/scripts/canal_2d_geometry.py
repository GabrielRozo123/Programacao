"""
Canal representativo do monólito — geometria pseudo-2D (box extrudado fino)
Dimensões: L × Dh × t = 50 mm × 1,1 mm × 1 mm

  x → direção axial (escoamento)          [0, 50 mm]
  y → direção transversal (canal)          [0, 1,1 mm]
  z → espessura (1 célula de malha)        [0, 1 mm]

6 faces (renomear no STAR-CCM+ após importação):
  x = 0      → Inlet
  x = 50 mm  → Outlet
  y = 0      → Bottom_Wall
  y = 1,1 mm → Top_Wall
  z = 0      → Back_Sym   (Symmetry Plane)
  z = 1 mm   → Front_Sym  (Symmetry Plane)

Exporta: geometry/canal_3d.step
"""

from pathlib import Path

# ── Parâmetros ─────────────────────────────────────────────────────────────────
L_mm  = 50.0    # comprimento axial
Dh_mm =  1.1    # altura do canal (diâmetro hidráulico)
t_mm  =  1.0    # espessura pseudo-2D (1 célula de malha em z)

SCRIPT_DIR  = Path(__file__).resolve().parent
OUTPUT_STEP = SCRIPT_DIR.parent / "geometry" / "canal_3d.step"
OUTPUT_STEP.parent.mkdir(parents=True, exist_ok=True)

# ── Geometria (build123d) ──────────────────────────────────────────────────────
from build123d import BuildPart, Box, Align, export_step

with BuildPart() as canal:
    Box(L_mm, Dh_mm, t_mm,
        align=(Align.MIN, Align.MIN, Align.MIN))   # canto em (0,0,0)

export_step(canal.part, str(OUTPUT_STEP))

print(f"STEP exportado: {OUTPUT_STEP}")
print(f"  {L_mm} mm (x)  ×  {Dh_mm} mm (y)  ×  {t_mm} mm (z)")
print()
print("Faces a renomear no STAR-CCM+ (após importação):")
print(f"  x = 0        → Inlet")
print(f"  x = {L_mm:.0f}      → Outlet")
print(f"  y = 0        → Bottom_Wall")
print(f"  y = {Dh_mm}     → Top_Wall    ← parede catalítica (Fase 2)")
print(f"  z = 0        → Back_Sym    (Symmetry Plane)")
print(f"  z = {t_mm:.0f}        → Front_Sym   (Symmetry Plane)")
