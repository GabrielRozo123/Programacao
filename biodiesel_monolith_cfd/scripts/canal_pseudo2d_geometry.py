"""
Canal representativo do monólito — geometria pseudo-2D FINA
Gera versões com espessura reduzida em z para forçar 1 célula de malha
nessa direção, eliminando o desperdício computacional do canal_3d original
(que tinha 1 mm em z e ~40 células redundantes).

  x → direção axial (escoamento)     [0, 50 mm]
  y → direção transversal do canal   [0, 1,1 mm]
  z → espessura pseudo-2D            [0, t]     ← 1 célula

Faces a renomear no STAR-CCM+ após importação:
  x = 0      → Inlet
  x = 50 mm  → Outlet
  y = 0      → Bottom_Wall     (parede inerte, fluxo zero)
  y = 1,1 mm → Top_Wall        (parede catalítica — washcoat)
  z = 0      → Simetria        (Symmetry Plane)
  z = t      → Simetria        (Symmetry Plane — mesma boundary)

Regra: usar Base Size >= espessura para garantir 1 célula em z.

Gabriel Rozo | FEQ/UNICAMP | 2025-2027
"""

from pathlib import Path
from build123d import BuildPart, Box, Align, export_step

# ── Parâmetros do canal ───────────────────────────────────────────────────
L_mm  = 50.0    # comprimento axial      (Firth 2014 / projeto)
Dh_mm =  1.1    # altura do canal        (400 CPSI, Dh = 1,1 mm)

# Espessuras a gerar — escolher no STAR-CCM+ conforme o Base Size adotado
ESPESSURAS_mm = [0.05, 0.10]

OUT_DIR = Path(__file__).resolve().parent.parent / "geometry"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Canal: {L_mm} mm (x) x {Dh_mm} mm (y)")
print()

for t_mm in ESPESSURAS_mm:
    with BuildPart() as canal:
        Box(L_mm, Dh_mm, t_mm, align=(Align.MIN, Align.MIN, Align.MIN))

    nome = f"canal_pseudo2d_{int(t_mm*1000):03d}um.step"
    caminho = OUT_DIR / nome
    export_step(canal.part, str(caminho))

    # Estimativa de células com Base Size = espessura
    nx = int(L_mm  / t_mm)
    ny = int(Dh_mm / t_mm)
    print(f"{nome}")
    print(f"   espessura z : {t_mm} mm = {t_mm*1000:.0f} um")
    print(f"   Base Size recomendado : {t_mm} mm  -> 1 celula em z")
    print(f"   malha nucleo estimada : {nx} (x) x {ny} (y) x 1 (z) = {nx*ny:,} celulas")
    print()

print("Comparacao com a malha 3D atual: 1.426.488 celulas")
