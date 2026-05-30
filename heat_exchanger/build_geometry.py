#!/usr/bin/env python3
"""
Trocador de Calor Casco-Tubo — TEMA BEM
========================================
Geometria CHT para STAR-CCM+ — versão com BOUNDARIES JÁ IDENTIFICÁVEIS

Estratégia para facilitar o setup no STAR-CCM+:
  • Lado do TUBO: um único corpo fundido (header_in + 61 tubos + header_out)
      → apenas 2 faces a renomear: header_in_face  →  Tube_Oil_In
                                   header_out_face →  Tube_Oil_Out
  • Lado do CASCO: cilindro + bocais fusionados (1 corpo)
      → apenas 2 faces a renomear: nozzle_in_face  →  Shell_Water_In
                                   nozzle_out_face →  Shell_Water_Out

Total de renamings no STAR-CCM+: APENAS 4 boundaries

Arquivos (step/):
  01_Shell_Fluid.step   → domínio fluido do casco  (1 corpo — água)
  02_Tube_Fluid.step    → domínio fluido dos tubos  (1 corpo fundido — óleo)
  03_Tube_Wall.step     → parede sólida dos tubos   (61 anéis — aço)
  04_Baffles.step       → 6 defletores segmentais   (aço)
  05_Tubesheets.step    → 2 espelhos               (aço)
  06_Shell_Wall.step    → parede do casco           (aço)

Workflow STAR-CCM+ (após importar os 6 STEP files):
  1. Fechar 3D-CAD → Update 3D-CAD
  2. Assign Parts to Regions:
       01_Shell_Fluid                           → região "Water"
       02_Tube_Fluid                            → região "Oil"
       03_Tube_Wall + 04_Baffles +
       05_Tubesheets + 06_Shell_Wall            → região "Steel"
  3. Renomear 4 boundaries:
       Water region:
         - face circular em y ≈ +207mm, z ≈ 930mm → Shell_Water_In   (Mass Flow Inlet)
         - face circular em y ≈ -207mm, z ≈ 130mm → Shell_Water_Out  (Pressure Outlet)
       Oil region:
         - face circular grande em z = -10mm       → Tube_Oil_In     (Mass Flow Inlet)
         - face circular grande em z = +1070mm     → Tube_Oil_Out    (Pressure Outlet)
  4. Criar Contact Interfaces (In-Place, Coupled Thermal):
         Shell_Fluid ↔ Steel  (superfície OD dos tubos, z 30–1030 mm)
         Steel ↔ Oil          (superfície ID dos tubos, z 0–1060 mm)
  5. Configurar física e solver.

build123d == 0.10.0
"""

from build123d import (
    BuildPart, Cylinder, Box, Locations, Location,
    Align, Mode, export_step
)
import math, os

# ══════════════════════════════════════════════════════════════
# PARÂMETROS  (mm)
# ══════════════════════════════════════════════════════════════
DS        = 254.0        # Shell inner diameter
SHELL_TK  =   8.0        # Shell wall thickness
TUBE_OD   =  19.05       # Tube outer diameter  (3/4")
TUBE_ID   =  15.75       # Tube inner diameter
L_TUBE    = 1000.0       # Active tube length
PITCH     =  23.81       # Triangular pitch  (P/D = 1.25)
N_BAF     =   6          # Number of baffles
B_CUT_H   =  63.5        # Baffle cut height  (25 % of DS)
B_THICK   =   6.0        # Baffle thickness
TS_THICK  =  30.0        # Tubesheet thickness
NOZ_R     =  25.4        # Shell nozzle radius  (Ø50.8 mm)
NOZ_LEN   =  80.0        # Shell nozzle protrusion

# Derivados
L_TOTAL  = L_TUBE + 2*TS_THICK          # 1060 mm — total length
Z_SF_CEN = TS_THICK + L_TUBE/2          #  530 mm — shell fluid center
Z_NOZ_IN = TS_THICK + L_TUBE*0.90       #  930 mm — shell inlet nozzle z
Z_NOZ_OUT= TS_THICK + L_TUBE*0.10       #  130 mm — shell outlet nozzle z
NOZ_H    = DS/2 + NOZ_LEN               #  207 mm — nozzle total arm
CUT_Y    = DS/2 - B_CUT_H              #   63.5 mm — baffle cut y-plane

# Tube-fluid header (plenums que agrupam as 61 entradas/saídas)
H_HEAD   = 10.0   # mm — header height (thin plenum)
# R_HEAD calculado após os centros dos tubos

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "step")
os.makedirs(OUT, exist_ok=True)

# ══════════════════════════════════════════════════════════════
# CENTROS DOS TUBOS — rede triangular  (TEMA D-5)
# R_max = 96 mm → 61 tubos, clearance 22.2 mm  (TEMA R)
# ══════════════════════════════════════════════════════════════
def tube_centers():
    R_max = 96.0
    a1 = (PITCH, 0.0)
    a2 = (PITCH/2, PITCH*math.sqrt(3)/2)
    N  = int(DS/PITCH) + 2
    seen = {}
    for i in range(-N, N+1):
        for j in range(-N, N+1):
            x = i*a1[0] + j*a2[0]
            y = i*a1[1] + j*a2[1]
            if x**2 + y**2 <= R_max**2:
                k = (round(x, 1), round(y, 1))
                seen[k] = (round(x, 4), round(y, 4))
    return sorted(seen.values(), key=lambda p: p[0]**2 + p[1]**2)

CENTERS  = tube_centers()
R_HEAD   = max(math.sqrt(cx**2+cy**2) for cx,cy in CENTERS) + TUBE_ID/2 + 2.0
BAFFLE_ZS= [TS_THICK + (k+1)*L_TUBE/(N_BAF+1) for k in range(N_BAF)]

def save(part, name):
    path = os.path.join(OUT, name)
    export_step(part, path)
    print(f"  ✓  {name}")


# ══════════════════════════════════════════════════════════════
# CABEÇALHO
# ══════════════════════════════════════════════════════════════
print("=" * 62)
print("  TROCADOR CASCO-TUBO  —  Geração STAR-CCM+ (CHT)")
print("=" * 62)
print(f"  Tubos            : {len(CENTERS)}")
print(f"  R_HEADER         : {R_HEAD:.1f} mm  (cobre bundle inteiro)")
print(f"  Header height    : {H_HEAD:.0f} mm  (plenum fora dos tubesheets)")
print(f"  Z bocal entrada  : {Z_NOZ_IN:.0f} mm  (+Y)")
print(f"  Z bocal saída    : {Z_NOZ_OUT:.0f} mm  (-Y)")
print()


# ══════════════════════════════════════════════════════════════
# 01 — SHELL FLUID  (1 corpo — ÁGUA)
# ══════════════════════════════════════════════════════════════
# Corpo único: cilindro principal (DS/2 × L_TUBE)
#            + bocal entrada (+Y, z=930 mm)  ← Shell_Water_In
#            + bocal saída   (-Y, z=130 mm)  ← Shell_Water_Out
#            − 61 furos OD dos tubos
#
# STAR-CCM+ — faces a renomear nesta região:
#   • face circular em y=+207mm, z=930mm  →  "Shell_Water_In"   (Mass Flow Inlet)
#   • face circular em y=-207mm, z=130mm  →  "Shell_Water_Out"  (Pressure Outlet)
# ══════════════════════════════════════════════════════════════
print("[01] Shell Fluid (água)...")

with BuildPart() as sf:

    # Cilindro principal
    with Locations((0, 0, Z_SF_CEN)):
        Cylinder(radius=DS/2, height=L_TUBE)

    # Bocal entrada água — aponta em +Y  (rotation = -90° em X: Z → +Y)
    # Centro em (0, +NOZ_H/2, Z_NOZ_IN) → nozzle de y=0 até y=+NOZ_H
    with Locations((0, NOZ_H/2, Z_NOZ_IN)):
        Cylinder(radius=NOZ_R, height=NOZ_H, rotation=(-90, 0, 0))

    # Bocal saída água — aponta em -Y  (rotation = +90° em X: Z → -Y)
    # Centro em (0, -NOZ_H/2, Z_NOZ_OUT) → nozzle de y=0 até y=-NOZ_H
    with Locations((0, -NOZ_H/2, Z_NOZ_OUT)):
        Cylinder(radius=NOZ_R, height=NOZ_H, rotation=(90, 0, 0))

    # Subtrair os 61 tubos (OD) em lote
    locs_t = [Location((cx, cy, Z_SF_CEN)) for cx, cy in CENTERS]
    with Locations(*locs_t):
        Cylinder(radius=TUBE_OD/2, height=L_TUBE, mode=Mode.SUBTRACT)

save(sf.part, "01_Shell_Fluid.step")


# ══════════════════════════════════════════════════════════════
# 02 — TUBE FLUID  (1 corpo fundido — ÓLEO)
# ══════════════════════════════════════════════════════════════
# Corpo único fundido:
#   Header_In   : cilindro R_HEAD × H_HEAD  em z = -H_HEAD → 0
#   61 canais   : cilindros TUBE_ID/2 × L_TOTAL em z = 0 → L_TOTAL
#   Header_Out  : cilindro R_HEAD × H_HEAD  em z = L_TOTAL → L_TOTAL+H_HEAD
#
# A fusão (Mode.ADD) no OpenCASCADE une os corpos adjacentes num único sólido.
# Resultado: 1 corpo com apenas 2 faces "livres" de interesse:
#
# STAR-CCM+ — faces a renomear nesta região:
#   • face circular grande em z = -10mm      →  "Tube_Oil_In"   (Mass Flow Inlet)
#   • face circular grande em z = +1070mm    →  "Tube_Oil_Out"  (Pressure Outlet)
# ══════════════════════════════════════════════════════════════
print("[02] Tube Fluid (óleo — 61 tubos + headers)...")

Z_HEAD_IN_CEN  = -H_HEAD/2               # centro header_in  em z = -5 mm
Z_TUBE_CEN     = L_TOTAL/2               # centro dos tubos  em z = 530 mm
Z_HEAD_OUT_CEN = L_TOTAL + H_HEAD/2      # centro header_out em z = 1065 mm

with BuildPart() as tf:

    # Header de entrada (plenum exterior ao tubesheet frontal)
    # Face inferior em z = -H_HEAD = -10 mm  →  Tube_Oil_In
    with Locations((0, 0, Z_HEAD_IN_CEN)):
        Cylinder(radius=R_HEAD, height=H_HEAD)

    # 61 canais internos dos tubos — comprimento total L_TOTAL (passa pelos tubesheets)
    locs_t = [Location((cx, cy, Z_TUBE_CEN)) for cx, cy in CENTERS]
    with Locations(*locs_t):
        Cylinder(radius=TUBE_ID/2, height=L_TOTAL)

    # Header de saída (plenum exterior ao tubesheet traseiro)
    # Face superior em z = L_TOTAL + H_HEAD = 1070 mm  →  Tube_Oil_Out
    with Locations((0, 0, Z_HEAD_OUT_CEN)):
        Cylinder(radius=R_HEAD, height=H_HEAD)

save(tf.part, "02_Tube_Fluid.step")


# ══════════════════════════════════════════════════════════════
# 03 — TUBE WALL  (61 anéis de aço — parede dos tubos)
# ══════════════════════════════════════════════════════════════
# 61 anéis OD/ID, comprimento L_TOTAL (atravessa os tubesheets)
# Superfície interna  r = TUBE_ID/2 → interface CHT com Tube_Fluid
# Superfície externa  r = TUBE_OD/2 → interface CHT com Shell_Fluid
#   (z ∈ [30, 1030] mm — zona ativa)
# ══════════════════════════════════════════════════════════════
print("[03] Tube Wall (61 anéis de aço)...")

with BuildPart() as tw:
    locs_t = [Location((cx, cy, L_TOTAL/2)) for cx, cy in CENTERS]
    with Locations(*locs_t):
        Cylinder(radius=TUBE_OD/2, height=L_TOTAL)
    with Locations(*locs_t):
        Cylinder(radius=TUBE_ID/2, height=L_TOTAL, mode=Mode.SUBTRACT)

save(tw.part, "03_Tube_Wall.step")


# ══════════════════════════════════════════════════════════════
# 04 — BAFFLES  (6 defletores segmentais — aço)
# ══════════════════════════════════════════════════════════════
# Corte alternado: topo  (k par)  /  base  (k ímpar)
# CUT_Y = 63.5 mm  →  ponto de corte medido a partir do eixo Z
# Furos dos tubos: raio = TUBE_OD/2  (montagem sem folga)
# ══════════════════════════════════════════════════════════════
print("[04] Baffles (6 defletores segmentais)...")

with BuildPart() as baf:
    for k, z_baf in enumerate(BAFFLE_ZS):

        with Locations((0, 0, z_baf)):
            Cylinder(radius=DS/2 - 1.0, height=B_THICK)

        # Corte segmental
        if k % 2 == 0:
            # Remove y > +CUT_Y  →  corte no topo
            with Locations((0, CUT_Y, z_baf)):
                Box(DS + 20, DS, B_THICK + 2,
                    align=(Align.CENTER, Align.MIN, Align.CENTER),
                    mode=Mode.SUBTRACT)
        else:
            # Remove y < -CUT_Y  →  corte na base
            with Locations((0, -CUT_Y, z_baf)):
                Box(DS + 20, DS, B_THICK + 2,
                    align=(Align.CENTER, Align.MAX, Align.CENTER),
                    mode=Mode.SUBTRACT)

        # Furos dos tubos (lote)
        locs_baf = [Location((cx, cy, z_baf)) for cx, cy in CENTERS]
        with Locations(*locs_baf):
            Cylinder(radius=TUBE_OD/2, height=B_THICK + 2, mode=Mode.SUBTRACT)

save(baf.part, "04_Baffles.step")


# ══════════════════════════════════════════════════════════════
# 05 — TUBESHEETS  (2 espelhos — aço)
# ══════════════════════════════════════════════════════════════
# Frontal : z =  0   →  30 mm  (centro z =  15 mm)
# Traseiro: z = 1030 → 1060 mm (centro z = 1045 mm)
# Furos: raio = TUBE_OD/2  (encaixe preciso da parede dos tubos)
# ══════════════════════════════════════════════════════════════
print("[05] Tubesheets (2 espelhos)...")

Z_TS_F = TS_THICK/2
Z_TS_R = TS_THICK + L_TUBE + TS_THICK/2

with BuildPart() as ts:
    for z_ts in [Z_TS_F, Z_TS_R]:
        with Locations((0, 0, z_ts)):
            Cylinder(radius=DS/2, height=TS_THICK)
    locs_ts = [
        Location((cx, cy, z_ts))
        for z_ts in [Z_TS_F, Z_TS_R]
        for cx, cy in CENTERS
    ]
    with Locations(*locs_ts):
        Cylinder(radius=TUBE_OD/2, height=TS_THICK + 2, mode=Mode.SUBTRACT)

save(ts.part, "05_Tubesheets.step")


# ══════════════════════════════════════════════════════════════
# 06 — SHELL WALL  (parede cilíndrica — aço)
# ══════════════════════════════════════════════════════════════
print("[06] Shell Wall (parede do casco)...")

with BuildPart() as sw:
    with Locations((0, 0, L_TOTAL/2)):
        Cylinder(radius=DS/2 + SHELL_TK, height=L_TOTAL)
        Cylinder(radius=DS/2,            height=L_TOTAL, mode=Mode.SUBTRACT)

save(sw.part, "06_Shell_Wall.step")


# ══════════════════════════════════════════════════════════════
# GUIA DE SETUP NO STAR-CCM+
# ══════════════════════════════════════════════════════════════
print()
print("=" * 62)
print("  VERIFICAÇÃO E GUIA STAR-CCM+")
print("=" * 62)
print()
print("  GEOMETRIA:")
print(f"    Tubos                  : {len(CENTERS)}")
print(f"    Bundle Ø               : {2*(max(math.sqrt(cx**2+cy**2) for cx,cy in CENTERS)+TUBE_OD/2):.1f} mm")
print(f"    Header entrada (Oil)   : z = {-H_HEAD:.0f} mm  →  z = 0 mm")
print(f"    Tubos ativos (Oil)     : z = 0 mm   →  z = {L_TOTAL:.0f} mm")
print(f"    Header saída  (Oil)    : z = {L_TOTAL:.0f} mm  →  z = {L_TOTAL+H_HEAD:.0f} mm")
print(f"    Shell fluid (Water)    : z = {TS_THICK:.0f} mm  →  z = {TS_THICK+L_TUBE:.0f} mm")
print(f"    Bocal entrada (Water)  : y = +{NOZ_H:.0f} mm, z = {Z_NOZ_IN:.0f} mm")
print(f"    Bocal saída   (Water)  : y = -{NOZ_H:.0f} mm, z = {Z_NOZ_OUT:.0f} mm")
print()
print("  INTERFACES CHT (coincidentes):")
print(f"    Shell_Fluid ↔ Tube_Wall: r = {TUBE_OD/2:.4f} mm, z ∈ [30, 1030] mm  ✓")
print(f"    Tube_Wall ↔ Tube_Fluid : r = {TUBE_ID/2:.4f} mm, z ∈ [0, {L_TOTAL:.0f}] mm  ✓")
print()
print("  ┌──────────────────────────────────────────────────────┐")
print("  │  STAR-CCM+ — APENAS 4 BOUNDARIES A RENOMEAR:        │")
print("  ├──────────────────────────────────────────────────────┤")
print("  │  Região Water (01_Shell_Fluid):                      │")
print(f"  │    face y=+{NOZ_H:.0f}mm, z={Z_NOZ_IN:.0f}mm → Shell_Water_In       │")
print(f"  │    face y=-{NOZ_H:.0f}mm, z={Z_NOZ_OUT:.0f}mm → Shell_Water_Out      │")
print("  │                                                      │")
print("  │  Região Oil (02_Tube_Fluid):                        │")
print(f"  │    face maior em z=-{H_HEAD:.0f}mm         → Tube_Oil_In        │")
print(f"  │    face maior em z=+{L_TOTAL+H_HEAD:.0f}mm       → Tube_Oil_Out       │")
print("  └──────────────────────────────────────────────────────┘")
print()
print("  COMO RENOMEAR no STAR-CCM+:")
print("  1. Simulation tree → Regions → Water → Boundaries")
print("     → clique dir. na boundary do bocal +Y → Rename → Shell_Water_In")
print("     → clique dir. na boundary do bocal -Y → Rename → Shell_Water_Out")
print("  2. Regions → Oil → Boundaries")
print("     → clique dir. na boundary do header frontal → Tube_Oil_In")
print("     → clique dir. na boundary do header traseiro → Tube_Oil_Out")
print()
print(f"  Arquivos: {OUT}")
print("=" * 62)
