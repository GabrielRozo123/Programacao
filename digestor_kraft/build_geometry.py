#!/usr/bin/env python3
"""
Digestor Kraft Kamyr — Geometria Industrial 3D para STAR-CCM+
=============================================================
Digestor contínuo tipo Kamyr de grande porte, ~800-1000 ADT/dia

DADOS DA LITERATURA:
  Agarwal, P.K. et al. (2001) TAPPI Journal — CFD modelo Kamyr, D=4.5m
  Andrews, S.P. et al. (2018) Chem. Eng. Sci. 195:721-734 — CFD digestor contínuo
  Gustafson, R.R. et al. (1983) I&EC Process Des. Dev. 22:87–96 — perfil deslignificação
  Sixta, H. (2006) Handbook of Pulp, Wiley-VCH — condições operacionais
  Pougatch, K. et al. (2016) Comp. Chem. Eng. 87:219-236 — CFD multifásico digestor
  Decker, S.R. & Garner, B.L. (1980) TAPPI 63(11) — cinética Kraft
  Zhu, W. & Theliander, H. (2011) Nordic Pulp Paper Res. J. 26(1) — propriedades licor

GEOMETRIA — 5 REGIÕES:
  01_Cone_Inferior  : região fluida (saída polpa)   Z = 0.0 – 3.0 m
  02_Zona_Lavagem   : leito poroso ε=0.45          Z = 3.0 – 11.0 m
  03_Zona_Cozimento : leito poroso ε=0.40          Z = 11.0 – 33.0 m
  04_Zona_Impregn   : leito poroso ε=0.50          Z = 33.0 – 38.0 m
  05_Cone_Superior  : região fluida (entrada chips) Z = 38.0 – 41.0 m

BOUNDARIES POR REGIÃO (para atribuir no STAR-CCM+ após importação):
  ConeBot_Outlet          — Pressure Outlet  (face circular D=0.8m, Z=0)
  ConeBot_Wall            — Wall             (face lateral cônica)
  [interface auto]        — Contact In-Place (face D=4.5m, Z=3.0m)

  Wash_LiquorInlet_N[1-4] — Velocity Inlet   (faces externas dos 4 bocais, Z=7.0m)
  Wash_Wall               — Wall             (face lateral cilíndrica)
  [interfaces auto]       — Contact In-Place (faces D=4.5m, Z=3.0m e Z=11.0m)

  Cook_BlackLiquorExtract_N[1-4] — Pressure Outlet (faces bocais, Z=23.1m)
  Cook_Wall               — Wall             (face lateral cilíndrica)
  [interfaces auto]       — Contact In-Place (faces D=4.5m, Z=11.0m e Z=33.0m)

  Impreg_WhiteLiquorInlet_N[1-4] — Velocity Inlet (faces bocais, Z=35.5m)
  Impreg_Wall             — Wall             (face lateral cilíndrica)
  [interfaces auto]       — Contact In-Place (faces D=4.5m, Z=33.0m e Z=38.0m)

  ConeTop_ChipsInlet      — Velocity Inlet   (face circular D=1.2m, Z=41.0m)
  ConeTop_Wall            — Wall             (face lateral cônica)
  [interface auto]        — Contact In-Place (face D=4.5m, Z=38.0m)

COEFICIENTES DE ERGUN (equação de Darcy-Forchheimer, STAR-CCM+ Porous Resistance):
  Calculados para: dp=0.007m (cavacos), μ=3.5e-4 Pa·s, ρ=1080 kg/m³ a 170°C
  Fórmula: Pv = 150·μ·(1-ε)²/(dp²·ε³)   [kg/(m³·s)]  — viscous resistance
            Pi = 1.75·ρ·(1-ε)/(dp·ε³)    [kg/m⁴]      — inertial resistance

  Zona Impregnação (ε=0.50): Pv = 2.14e3 kg/(m³·s),  Pi = 1.08e6 kg/m⁴
  Zona Cozimento   (ε=0.40): Pv = 6.03e3 kg/(m³·s),  Pi = 2.53e6 kg/m⁴
  Zona Lavagem     (ε=0.45): Pv = 3.56e3 kg/(m³·s),  Pi = 1.63e6 kg/m⁴

TAMANHO DE MALHA RECOMENDADO (STAR-CCM+ Polyhedral Mesher):
  Base size    : 0.25 m  → ~250–350k células (simulação leve, boa para validação)
  Surface ctrl.: 10% base no interior das regiões
  Refine bocais: 0.05 m  → garante pelo menos 4 células no bocal D=0.20m
  Prism layers : 3 camadas, espessura total = 0.02 m (y+=30-300 para k-ε)
"""

from build123d import *
import os, math

# ================================================================
# PARÂMETROS GEOMÉTRICOS (baseados em Agarwal 2001, Andrews 2018)
# ================================================================

# Diâmetros
D_vessel = 4.5    # m  — seção cilíndrica principal
D_chips  = 1.2    # m  — abertura entrada cavacos (topo)
D_pulp   = 0.8    # m  — abertura saída polpa (fundo)
D_noz    = 0.20   # m  — diâmetro interno dos bocais laterais
L_noz    = 0.40   # m  — comprimento externo do bocal (além da parede)

# Raios derivados
R        = D_vessel / 2    # 2.25 m
R_chips  = D_chips  / 2    # 0.60 m
R_pulp   = D_pulp   / 2    # 0.40 m
R_noz    = D_noz    / 2    # 0.10 m

# Alturas das zonas
h_cb  = 3.0    # m  Cone inferior   (região fluida)
h_was = 8.0    # m  Zona Lavagem    ε=0.45  (Gustafson 1983)
h_cok = 22.0   # m  Zona Cozimento  ε=0.40  (Andrews 2018)
h_imp = 5.0    # m  Zona Impregnação ε=0.50 (Sixta 2006)
h_ct  = 3.0    # m  Cone superior   (região fluida)

# Z absolutos (Z=0 na base do cone inferior = saída de polpa)
z_wash   = h_cb                   # 3.0  m — base Zona Lavagem
z_cook   = z_wash  + h_was        # 11.0 m — base Zona Cozimento
z_impreg = z_cook  + h_cok        # 33.0 m — base Zona Impregnação
z_top    = z_impreg + h_imp       # 38.0 m — base Cone Superior
z_total  = z_top   + h_ct         # 41.0 m — topo absoluto

# Z do centro de cada conjunto de bocais
z_noz_wash   = z_wash   + h_was * 0.50   #  7.0 m  — licor de lavagem
z_noz_cook   = z_cook   + h_cok * 0.55  # 23.1 m  — extração licor negro
z_noz_impreg = z_impreg + h_imp * 0.50  # 35.5 m  — licor branco

N_noz = 4   # bocais por nível, espaçados 90°

print("=" * 60)
print("DIGESTOR KRAFT KAMYR — DIMENSÕES")
print("=" * 60)
print(f"  Diâmetro interno (D_vessel): {D_vessel} m")
print(f"  Abertura entrada chips:      {D_chips} m")
print(f"  Abertura saída polpa:        {D_pulp} m")
print(f"  Diâmetro bocais laterais:    {D_noz} m")
print()
print(f"  Cone Inferior  : Z = {0.0:.1f} – {z_wash:.1f} m")
print(f"  Zona Lavagem   : Z = {z_wash:.1f} – {z_cook:.1f} m  (ε=0.45)")
print(f"  Zona Cozimento : Z = {z_cook:.1f} – {z_impreg:.1f} m  (ε=0.40)")
print(f"  Zona Impregn   : Z = {z_impreg:.1f} – {z_top:.1f} m  (ε=0.50)")
print(f"  Cone Superior  : Z = {z_top:.1f} – {z_total:.1f} m")
print(f"  Altura total:    {z_total:.1f} m")
print()
print(f"  Bocais lavagem:     Z = {z_noz_wash:.1f} m")
print(f"  Bocais extração:    Z = {z_noz_cook:.1f} m")
print(f"  Bocais licor branco: Z = {z_noz_impreg:.1f} m")
print("=" * 60)


# ================================================================
# FUNÇÃO AUXILIAR — BOCAIS RADIAIS
# ================================================================

def add_nozzles_to_part(builder_part, z_nozzle, n=N_noz, r_noz=R_noz, l_noz=L_noz, r_vessel=R):
    """
    Adiciona n bocais cilíndricos radiais ao BuildPart existente.
    Os bocais partem da parede do vaso (raio r_vessel) para fora (r_vessel + l_noz).
    O eixo de cada bocal aponta radialmente para fora.

    Rotações verificadas (convention build123d 0.10, Euler XYZ intrinsic):
      θ=  0° → (rx=  0, ry= 90, rz=0): cilindro Z → +X (radial ✓)
      θ= 90° → (rx=-90, ry=  0, rz=0): cilindro Z → +Y (radial ✓)
      θ=180° → (rx=  0, ry=-90, rz=0): cilindro Z → -X (radial ✓)
      θ=270° → (rx= 90, ry=  0, rz=0): cilindro Z → -Y (radial ✓)
    """
    # Tabela de rotações para n=4 bocais a 0°, 90°, 180°, 270°
    rot_table_4 = [
        (0,   90, 0),   # θ=  0° — aponta para +X
        (-90,  0, 0),   # θ= 90° — aponta para +Y
        (0,  -90, 0),   # θ=180° — aponta para -X
        (90,   0, 0),   # θ=270° — aponta para -Y
    ]
    with builder_part:
        for i in range(n):
            theta = i * (360.0 / n)
            a     = math.radians(theta)
            cx    = (r_vessel + l_noz / 2.0) * math.cos(a)
            cy    = (r_vessel + l_noz / 2.0) * math.sin(a)
            rx, ry, rz = rot_table_4[i % 4]
            with Locations(Location((cx, cy, z_nozzle), (rx, ry, rz))):
                Cylinder(r_noz, l_noz)


# ================================================================
# 01 — CONE INFERIOR  (região fluida, saída de polpa)
# ================================================================
print("Criando 01_Cone_Inferior...")
with BuildPart() as bp_cone_bot:
    with Locations((0, 0, 0)):
        Cone(R_pulp, R, h_cb, align=(Align.CENTER, Align.CENTER, Align.MIN))

cone_bot = bp_cone_bot.part
print(f"  ✓  Z = 0.0 – {h_cb:.1f} m  |  D_bottom={D_pulp}m → D_top={D_vessel}m")


# ================================================================
# 02 — ZONA LAVAGEM  (leito poroso ε=0.45)
# ================================================================
print("Criando 02_Zona_Lavagem...")
with BuildPart() as bp_wash:
    with Locations((0, 0, z_wash + h_was / 2.0)):
        Cylinder(R, h_was)
add_nozzles_to_part(bp_wash, z_noz_wash)

zona_wash = bp_wash.part
print(f"  ✓  Z = {z_wash:.1f} – {z_cook:.1f} m  |  ε=0.45  |  bocais em Z={z_noz_wash:.1f}m")


# ================================================================
# 03 — ZONA COZIMENTO  (leito poroso ε=0.40)
# ================================================================
print("Criando 03_Zona_Cozimento...")
with BuildPart() as bp_cook:
    with Locations((0, 0, z_cook + h_cok / 2.0)):
        Cylinder(R, h_cok)
add_nozzles_to_part(bp_cook, z_noz_cook)

zona_cook = bp_cook.part
print(f"  ✓  Z = {z_cook:.1f} – {z_impreg:.1f} m  |  ε=0.40  |  bocais em Z={z_noz_cook:.1f}m")


# ================================================================
# 04 — ZONA IMPREGNAÇÃO  (leito poroso ε=0.50)
# ================================================================
print("Criando 04_Zona_Impregn...")
with BuildPart() as bp_impreg:
    with Locations((0, 0, z_impreg + h_imp / 2.0)):
        Cylinder(R, h_imp)
add_nozzles_to_part(bp_impreg, z_noz_impreg)

zona_impreg = bp_impreg.part
print(f"  ✓  Z = {z_impreg:.1f} – {z_top:.1f} m  |  ε=0.50  |  bocais em Z={z_noz_impreg:.1f}m")


# ================================================================
# 05 — CONE SUPERIOR  (região fluida, entrada de cavacos)
# ================================================================
print("Criando 05_Cone_Superior...")
with BuildPart() as bp_cone_top:
    with Locations((0, 0, z_top)):
        Cone(R, R_chips, h_ct, align=(Align.CENTER, Align.CENTER, Align.MIN))

cone_top = bp_cone_top.part
print(f"  ✓  Z = {z_top:.1f} – {z_total:.1f} m  |  D_bottom={D_vessel}m → D_top={D_chips}m")


# ================================================================
# EXPORTAÇÃO
# ================================================================
out_dir = os.path.join(os.path.dirname(__file__), "step")
os.makedirs(out_dir, exist_ok=True)

files = [
    (cone_bot,   "01_Cone_Inferior.step"),
    (zona_wash,  "02_Zona_Lavagem.step"),
    (zona_cook,  "03_Zona_Cozimento.step"),
    (zona_impreg,"04_Zona_Impregn.step"),
    (cone_top,   "05_Cone_Superior.step"),
]

print()
print("Exportando STEP...")
for solid, fname in files:
    fpath = os.path.join(out_dir, fname)
    export_step(solid, fpath)
    size_kb = os.path.getsize(fpath) / 1024
    print(f"  ✓  {fname:35s}  ({size_kb:.0f} KB)")

print()
print("=" * 60)
print("INSTRUÇÕES DE IMPORTAÇÃO NO STAR-CCM+")
print("=" * 60)
print("""
1. File > Import > Import CAD Model (ou Import Surface Mesh)
   → Importar todos os 5 arquivos STEP de uma vez
   → Marcar "Create Interfaces" para detecção automática
   → Usar unidade: metros

2. Após importação, renomear as Regions:
   Part "01_Cone_Inferior"  → Region: "Cone_Inferior"   (Fluid)
   Part "02_Zona_Lavagem"   → Region: "Zona_Lavagem"    (Porous)
   Part "03_Zona_Cozimento" → Region: "Zona_Cozimento"  (Porous)
   Part "04_Zona_Impregn"   → Region: "Zona_Impregn"    (Porous)
   Part "05_Cone_Superior"  → Region: "Cone_Superior"   (Fluid)

3. Para cada região, atribuir nomes às Boundaries:
   Ver docstring no topo deste arquivo.

4. Criar Interfaces (Contact → In-Place) entre:
   Cone_Inferior  ↔ Zona_Lavagem
   Zona_Lavagem   ↔ Zona_Cozimento
   Zona_Cozimento ↔ Zona_Impregn
   Zona_Impregn   ↔ Cone_Superior

5. Mesh (Polyhedral Mesher + Prism Layer Mesher):
   Base size:          0.25 m
   Prism layers:       3 camadas, thickness total = 0.02 m
   Surface ctrl bocal: 0.05 m (Custom Surface Control nas faces dos bocais)
   → Células esperadas: ~250–350k (simulação leve)
""")
print("Geometria completa!")
