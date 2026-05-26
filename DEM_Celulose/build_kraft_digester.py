"""
Digestor Kraft Kamyr — Escala Industrial
Geometria CFD para Simcenter STAR-CCM+ (Meio Poroso Isotrópico)

Sistema de coordenadas:
  Z : eixo vertical (positivo = cima)
  Origem: centro do fundo do cone inferior (saída de polpa)

Zonas exportadas (partes separadas para STAR-CCM+):
  Cone_Inferior.step    → Fluid Region  (saída de polpa)
  Zona_Lavagem.step     → Porous Region (lavagem, ε=0.45)
  Zona_Cozimento.step   → Porous Region (cozimento, ε=0.40)
  Zona_Impregn.step     → Porous Region (impregnação, ε=0.50)
  Cone_Superior.step    → Fluid Region  (entrada de chips)
  Digestor_Kraft.step   → Montagem completa

Coeficientes de Ergun para licor branco + cavacos (dp=6mm):
  Equação STAR-CCM+: ΔP/L = -(Pi·|v| + Pv)·v
  Lavagem    (ε=0.45): Pi=1.90e6 kg/m⁴,  Pv=4.8e3 kg/m³s
  Cozimento  (ε=0.40): Pi=2.95e6 kg/m⁴,  Pv=8.2e3 kg/m³s
  Impregnação(ε=0.50): Pi=1.26e6 kg/m⁴,  Pv=2.9e3 kg/m³s
"""

from build123d import *
import os, math

output_dir = os.path.dirname(os.path.abspath(__file__))

# ================================================================
# 1. PARÂMETROS GEOMÉTRICOS (mm)
# ================================================================
D_cil      = 5500.0    # Diâmetro interno do cilindro principal [mm] = 5.5 m
R_cil      = D_cil / 2

# Alturas de cada zona (mm)
H_cone_bot = 2000.0    # Cone inferior (saída polpa)
H_wash     = 10000.0   # Zona de lavagem
H_cook     = 25000.0   # Zona de cozimento (maior zona)
H_impregn  =  5000.0   # Zona de impregnação (topo da cama)
H_cone_top =  3000.0   # Cone superior (entrada chips)

H_total = H_cone_bot + H_wash + H_cook + H_impregn + H_cone_top  # = 45 000 mm = 45 m

# Diâmetros dos cones
D_outlet = 800.0       # Saída de polpa (base do cone inferior)
D_inlet  = 1500.0      # Entrada de chips (topo do cone superior)

# ================================================================
# 2. POSIÇÕES DOS BOCAIS LATERAIS (Z medido da base)
# ================================================================
# Licor Branco (LB) — entra na base do cilindro (zona lavagem)
Z_lb_1 = H_cone_bot + 500.0    # 1ª entrada LB: 0.5 m acima do fundo
Z_lb_2 = H_cone_bot + 2000.0   # 2ª entrada LB: 2.0 m

# Extração de Licor Negro (LN) — sai na zona de cozimento
Z_ln   = H_cone_bot + H_wash + H_cook * 0.55   # ~55% da zona de cozimento

# Licor de Lavagem (LL) — entra na zona de lavagem
Z_ll   = H_cone_bot + H_wash * 0.70   # ~70% da zona de lavagem

D_nozzle = 300.0    # Diâmetro dos bocais [mm]
R_nozzle = D_nozzle / 2
L_nozzle = 600.0    # Comprimento dos bocais [mm]

# ================================================================
# 3. FUNÇÕES AUXILIARES
# ================================================================
def make_frustum(r_bot, r_top, height, z_offset=0.0, name=""):
    """Cone tronco por loft entre dois círculos."""
    print(f"  Construindo {name}  (R_bot={r_bot:.0f}→R_top={r_top:.0f} mm, H={height:.0f} mm)")
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            Circle(r_bot)
        with BuildSketch(Plane.XY.offset(height)):
            Circle(r_top)
        loft()
    return bp.part.move(Location((0, 0, z_offset)))


def make_zone(radius, height, z_offset=0.0, name=""):
    """Cilindro para uma zona do digestor."""
    print(f"  Construindo {name}  (R={radius:.0f} mm, H={height:.0f} mm, Z0={z_offset:.0f} mm)")
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            Circle(radius)
        extrude(amount=height)
    return bp.part.move(Location((0, 0, z_offset)))


def make_nozzle(radius_nozzle, length, z_pos, direction=(1, 0, 0), name=""):
    """Bocal cilíndrico lateral (usado como inlet/outlet)."""
    dx, dy, dz = direction
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            Circle(radius_nozzle)
        extrude(amount=length)
    # Rotacionar para direção radial e posicionar em Z
    nozzle = bp.part
    if direction == (1, 0, 0):
        nozzle = nozzle.rotate(Axis.Y, -90)
        nozzle = nozzle.move(Location((R_cil, 0, z_pos)))
    elif direction == (-1, 0, 0):
        nozzle = nozzle.rotate(Axis.Y, 90)
        nozzle = nozzle.move(Location((-R_cil, 0, z_pos)))
    elif direction == (0, 1, 0):
        nozzle = nozzle.rotate(Axis.X, 90)
        nozzle = nozzle.move(Location((0, R_cil, z_pos)))
    elif direction == (0, -1, 0):
        nozzle = nozzle.rotate(Axis.X, -90)
        nozzle = nozzle.move(Location((0, -R_cil, z_pos)))
    print(f"  Bocal {name}  em Z={z_pos:.0f} mm, dir={direction}")
    return nozzle

# ================================================================
# 4. CONSTRUÇÃO DAS ZONAS
# ================================================================
print()
print("=" * 64)
print("  DIGESTOR KRAFT KAMYR — CONSTRUÇÃO DA GEOMETRIA")
print("=" * 64)

z = 0.0  # Cursor de posição Z

cone_inf    = make_frustum(D_outlet/2, R_cil, H_cone_bot, z_offset=z, name="Cone Inferior")
z += H_cone_bot

zona_lav    = make_zone(R_cil, H_wash,    z_offset=z, name="Zona Lavagem")
z += H_wash

zona_coz    = make_zone(R_cil, H_cook,    z_offset=z, name="Zona Cozimento")
z += H_cook

zona_imp    = make_zone(R_cil, H_impregn, z_offset=z, name="Zona Impregnação")
z += H_impregn

cone_sup    = make_frustum(R_cil, D_inlet/2, H_cone_top, z_offset=z, name="Cone Superior")
z += H_cone_top

assert abs(z - H_total) < 1e-6, f"Erro altura total: {z} vs {H_total}"

# ================================================================
# 5. BOCAIS (inlets / outlets)
# ================================================================
nozzle_lb1 = make_nozzle(R_nozzle, L_nozzle, Z_lb_1,  direction=(1,  0, 0), name="Licor Branco 1")
nozzle_lb2 = make_nozzle(R_nozzle, L_nozzle, Z_lb_2,  direction=(-1, 0, 0), name="Licor Branco 2")
nozzle_ln  = make_nozzle(R_nozzle, L_nozzle, Z_ln,    direction=(1,  0, 0), name="Licor Negro (saída)")
nozzle_ll  = make_nozzle(R_nozzle, L_nozzle, Z_ll,    direction=(-1, 0, 0), name="Licor Lavagem")

# ================================================================
# 6. EXPORTAR
# ================================================================
print()
print("Exportando arquivos STEP...")

partes = {
    "Cone_Inferior" : cone_inf,
    "Zona_Lavagem"  : zona_lav,
    "Zona_Cozimento": zona_coz,
    "Zona_Impregn"  : zona_imp,
    "Cone_Superior" : cone_sup,
    "Bocal_LB1"     : nozzle_lb1,
    "Bocal_LB2"     : nozzle_lb2,
    "Bocal_LN"      : nozzle_ln,
    "Bocal_LL"      : nozzle_ll,
}

for nome, parte in partes.items():
    path = os.path.join(output_dir, f"{nome}.step")
    export_step(parte, path)
    print(f"  [OK] {nome}.step")

montagem = Compound(children=list(partes.values()))
assy_path = os.path.join(output_dir, "Digestor_Kraft.step")
export_step(montagem, assy_path)
print(f"  [OK] Digestor_Kraft.step  (montagem completa)")

# ================================================================
# 7. RESUMO
# ================================================================
print()
print("=" * 64)
print("  RESUMO — DIGESTOR KRAFT KAMYR INDUSTRIAL")
print("=" * 64)
print(f"  Diâmetro interno     : {D_cil/1000:.1f} m")
print(f"  Altura total         : {H_total/1000:.1f} m")
print()
print("  ZONAS (fundo → topo):")
h = 0.0
for nome_zona, altura in [
    ("Cone Inferior  [Fluid Region]"    , H_cone_bot),
    ("Zona Lavagem   [Porous Region]"   , H_wash),
    ("Zona Cozimento [Porous Region]"   , H_cook),
    ("Zona Impregnação[Porous Region]"  , H_impregn),
    ("Cone Superior  [Fluid Region]"    , H_cone_top),
]:
    print(f"    Z [{h/1000:.1f} – {(h+altura)/1000:.1f}] m  →  {nome_zona}")
    h += altura

print()
print("  COEFICIENTES POROUS — Equação de Ergun")
print("  (Licor branco, dp=6mm, T=165°C, ρ=1080 kg/m³, μ=3.5e-4 Pa·s)")
print()
print(f"  {'Zona':<20} {'ε':>6} {'Pi [kg/m⁴]':>14} {'Pv [kg/m³s]':>14}")
print(f"  {'-'*56}")
print(f"  {'Lavagem':<20} {'0.45':>6} {'1.90e6':>14} {'4.8e3':>14}")
print(f"  {'Cozimento':<20} {'0.40':>6} {'2.95e6':>14} {'8.2e3':>14}")
print(f"  {'Impregnação':<20} {'0.50':>6} {'1.26e6':>14} {'2.9e3':>14}")
print()
print("  STAR-CCM+ Physics:")
print("    Fluido      : Liquid — White Liquor")
print("    ρ           : 1080 kg/m³")
print("    μ           : 3.5×10⁻⁴ Pa·s  (@ 165°C)")
print("    Turbulência : K-Epsilon Standard  (High y+ Wall Treatment)")
print("    Regime      : Steady-State")
print()
print("  BOCAIS:")
print(f"    Licor Branco 1 : Z = {Z_lb_1/1000:.2f} m  (inlet, +X)")
print(f"    Licor Branco 2 : Z = {Z_lb_2/1000:.2f} m  (inlet, -X)")
print(f"    Licor Negro    : Z = {Z_ln/1000:.2f}  m  (outlet, +X)")
print(f"    Licor Lavagem  : Z = {Z_ll/1000:.2f}  m  (inlet, -X)")
print(f"    Saída Polpa    : Z = 0.00 m  (outlet, fundo do cone)")
print(f"    Entrada Chips  : Z = {H_total/1000:.2f} m  (inlet, topo do cone)")
print("=" * 64)
