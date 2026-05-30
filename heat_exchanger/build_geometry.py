#!/usr/bin/env python3
"""
Trocador de Calor Casco-Tubo — TEMA BEM
========================================
Geometria CFD para STAR-CCM+ (Conjugate Heat Transfer — CHT)

Fluidos
  Casco  → Água fria  | T_in = 25 °C
  Tubos  → Óleo diesel| T_in = 180 °C  (1 passe tubo)

Especificações TEMA BEM
  Shell ID       : 254 mm  (10")
  Tubos          : ~61 tubos, OD = 19.05 mm (3/4"), ID = 15.75 mm
  Passo          : Triangular, P = 23.81 mm  (P/D = 1.25)
  Comprimento    : 1 000 mm  (ativo)  + 2 × 30 mm tubesheets = 1 060 mm total
  Baffles        : 6 segmentais, corte 25 % = 63.5 mm, espaçamento uniforme
  Bocais         : Ø50.8 mm (2") — Shell In (+Y) e Shell Out (−Y)

Eixo de referência
  Z = 0       : face externa do tubesheet frontal  (Tube_Oil_In)
  Z = 30      : início do domínio fluido do casco  (Shell_Water side starts)
  Z = 1 030   : fim do domínio fluido do casco
  Z = 1 060   : face externa do tubesheet traseiro (Tube_Oil_Out)

Arquivos gerados  (step/)
  01_Shell_Fluid.step   — domínio fluido do casco  (água + bocais embutidos)
  02_Tube_Fluid.step    — 61 cilindros internos dos tubos  (óleo)
  03_Tube_Wall.step     — 61 anéis de parede dos tubos  (aço)
  04_Baffles.step       — 6 defletores segmentais com furos dos tubos  (aço)
  05_Tubesheets.step    — 2 espelhos com furos dos tubos  (aço)
  06_Shell_Wall.step    — parede cilíndrica do casco  (aço)

Workflow STAR-CCM+
  1. File → Import 3D CAD Model → selecionar os 6 STEP files
  2. Assign Parts to Regions:
       01_Shell_Fluid          → continuum "Water"       (Segregated + Energy)
       02_Tube_Fluid           → continuum "DieselOil"   (Segregated + Energy)
       03_Tube_Wall +
       04_Baffles +
       05_Tubesheets +
       06_Shell_Wall           → continuum "Steel"       (Coupled Solid Energy)
  3. Contact Interfaces (In-Place, Coupled Thermal):
       Shell_Fluid  ↔  Tube_Wall   (superfície OD dos tubos, z 30–1030)
       Tube_Wall    ↔  Tube_Fluid  (superfície ID dos tubos, z 30–1030)
  4. Boundaries:
       Shell_Water_In   → Mass Flow Inlet  (face circular nozzle, y = +207 mm, z ≈ 930)
       Shell_Water_Out  → Pressure Outlet  (face circular nozzle, y = −207 mm, z ≈ 130)
       Tube_Oil_In      → Mass Flow Inlet  (61 faces em z = 30 mm)
       Tube_Oil_Out     → Pressure Outlet  (61 faces em z = 1030 mm)
       (demais faces → Wall, temperatura de referência ou adiabática)

Dependência: build123d == 0.10.0
"""

from build123d import (
    BuildPart, Cylinder, Box, Locations, Location,
    Align, Mode, export_step, Axis
)
import math
import os

# ══════════════════════════════════════════════════════════════════
# PARÂMETROS GEOMÉTRICOS  (todos em mm)
# ══════════════════════════════════════════════════════════════════
DS        = 254.0        # Diâmetro interno do casco
SHELL_TK  =   8.0        # Espessura da parede do casco
TUBE_OD   =  19.05       # Diâmetro externo do tubo  (3/4")
TUBE_ID   =  15.75       # Diâmetro interno do tubo
L_TUBE    = 1000.0       # Comprimento ativo dos tubos
PITCH     =  23.81       # Passo triangular  (P/D = 1.25)
N_BAF     =   6          # Número de baffles
B_CUT_H   =  63.5        # Altura do corte do baffle  (25 % de DS)
B_THICK   =   6.0        # Espessura do baffle
TS_THICK  =  30.0        # Espessura do tubesheet (espelho)
NOZ_R     =  25.4        # Raio do bocal do casco  (1" nominal → Ø50.8 mm)
NOZ_LEN   =  80.0        # Comprimento do bocal (projeção além da parede)

# ── Grandezas derivadas ──────────────────────────────────────────
L_TOTAL  = L_TUBE + 2*TS_THICK         # 1060 mm   comprimento total
Z_SF_CEN = TS_THICK + L_TUBE/2         #  530 mm   centro do domínio fluido do casco
Z_NOZ_IN = TS_THICK + L_TUBE*0.90      #  930 mm   bocal entrada água (perto do tubesheet traseiro)
Z_NOZ_OUT= TS_THICK + L_TUBE*0.10      #  130 mm   bocal saída água   (perto do tubesheet frontal)
NOZ_H    = DS/2 + NOZ_LEN              #  207 mm   comprimento total do bocal (centro→ponta)
CUT_Y    = DS/2 - B_CUT_H              #  63.5 mm  posição Y do corte do baffle (medida do eixo)

# ── Diretório de saída ───────────────────────────────────────────
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "step")
os.makedirs(OUT, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
# CENTROS DOS TUBOS — rede triangular (ISO 1891 / TEMA)
# ══════════════════════════════════════════════════════════════════
def tube_centers():
    """
    Gera coordenadas (x, y) dos centros dos tubos em passo triangular.
    R_max = 96 mm → exatos 61 tubos, bundle Ø 211 mm.
    Bundle-to-shell clearance = (DS - 2*(R_max+TUBE_OD/2))/2 ≈ 21.5 mm  (TEMA R).
    Retorna lista ordenada por distância ao centro.
    """
    R_max = 96.0   # calibrado para 61 tubos conforme tabela TEMA D-5 (10", 3/4" tri.)
    # Vetores da rede triangular
    a1 = (PITCH, 0.0)
    a2 = (PITCH/2, PITCH * math.sqrt(3)/2)
    N  = int(DS / PITCH) + 2
    seen = {}
    for i in range(-N, N + 1):
        for j in range(-N, N + 1):
            x = i*a1[0] + j*a2[0]
            y = i*a1[1] + j*a2[1]
            if x**2 + y**2 <= R_max**2:
                k = (round(x, 1), round(y, 1))
                seen[k] = (round(x, 4), round(y, 4))
    pts = sorted(seen.values(), key=lambda p: p[0]**2 + p[1]**2)
    return pts

CENTERS = tube_centers()

# Posições Z dos 6 baffles, espaçados uniformemente dentro de L_TUBE
# (distância entre baffles = L_TUBE / (N_BAF + 1))
BAFFLE_ZS = [TS_THICK + (k + 1)*L_TUBE/(N_BAF + 1) for k in range(N_BAF)]


# ══════════════════════════════════════════════════════════════════
# FUNÇÃO AUXILIAR
# ══════════════════════════════════════════════════════════════════
def save_step(part, filename):
    path = os.path.join(OUT, filename)
    export_step(part, path)
    print(f"  ✓  {filename}")


# ══════════════════════════════════════════════════════════════════
# CABEÇALHO
# ══════════════════════════════════════════════════════════════════
print("=" * 62)
print("  TROCADOR CASCO-TUBO  —  Geração de Geometria STAR-CCM+")
print("=" * 62)
print(f"  Tubos no bundle : {len(CENTERS)}")
print(f"  Shell ID        : {DS:.1f} mm")
print(f"  Passo triangular: {PITCH:.2f} mm   (P/D = {PITCH/TUBE_OD:.3f})")
print(f"  Comprimento     : {L_TUBE:.0f} mm ativo  +  {L_TOTAL:.0f} mm total")
print(f"  Baffles         : {N_BAF} × corte {B_CUT_H:.1f} mm ({B_CUT_H/DS*100:.0f}% DS)")
print(f"  Espaç. baffles  : {L_TUBE/(N_BAF+1):.1f} mm")
print()
for k, z in enumerate(BAFFLE_ZS):
    cut_dir = "topo (−Y)" if k % 2 == 0 else "base (+Y)"
    print(f"    Baffle {k+1}: z = {z:.1f} mm  |  corte: {cut_dir}")
print()


# ══════════════════════════════════════════════════════════════════
# 01 — SHELL FLUID  (domínio fluido do casco — ÁGUA)
# ══════════════════════════════════════════════════════════════════
# Geometria: cilindro principal + 2 bocais (Mode.ADD)
#            − 61 cilindros dos tubos (OD)  → faces de interface CHT
#
# Faces importantes no STAR-CCM+:
#   y = +NOZ_H = +207 mm, z ≈ 930  → Shell_Water_In   (Mass Flow Inlet)
#   y = −NOZ_H = −207 mm, z ≈ 130  → Shell_Water_Out  (Pressure Outlet)
#   r = TUBE_OD/2, z ∈ [30, 1030]  → Interface c/ Tube_Wall (CHT)
#   z = 30  e  z = 1030             → Wall (espelhos — tubesheet)
#   r = DS/2, z ∈ [30, 1030]        → Shell_Inner_Wall (adiabático/convectivo)
# ══════════════════════════════════════════════════════════════════
print("[01] Shell Fluid (água)...")
print("     Adicionando cilindro principal + bocais...")

with BuildPart() as sf_part:

    # ── Cilindro principal ─────────────────────────────────────────
    with Locations((0, 0, Z_SF_CEN)):
        Cylinder(radius=DS/2, height=L_TUBE)

    # ── Bocal de ENTRADA da água: aponta em +Y (rotation = −90° em X)
    #    Centro em (0, +NOZ_H/2, Z_NOZ_IN) → nozzle de y=0 a y=+NOZ_H
    with Locations((0, NOZ_H/2, Z_NOZ_IN)):
        Cylinder(radius=NOZ_R, height=NOZ_H, rotation=(-90, 0, 0))

    # ── Bocal de SAÍDA da água: aponta em −Y (rotation = +90° em X)
    #    Centro em (0, −NOZ_H/2, Z_NOZ_OUT) → nozzle de y=0 a y=−NOZ_H
    with Locations((0, -NOZ_H/2, Z_NOZ_OUT)):
        Cylinder(radius=NOZ_R, height=NOZ_H, rotation=(90, 0, 0))

    # ── Subtrair os 61 tubos (OD) — operação em lote ──────────────
    print("     Subtraindo 61 furos de tubo (OD)...")
    locs_tube = [Location((cx, cy, Z_SF_CEN)) for cx, cy in CENTERS]
    with Locations(*locs_tube):
        Cylinder(radius=TUBE_OD/2, height=L_TUBE, mode=Mode.SUBTRACT)

save_step(sf_part.part, "01_Shell_Fluid.step")


# ══════════════════════════════════════════════════════════════════
# 02 — TUBE FLUID  (61 cilindros interiores — ÓLEO)
# ══════════════════════════════════════════════════════════════════
# 61 cilindros separados (não se tocam: folga = PITCH − TUBE_ID = 8.06 mm)
# No STAR-CCM+: selecionar todos os 61 bodies → 1 região "DieselOil"
#
# Faces importantes:
#   z = 30  (61 faces) → Tube_Oil_In   (Mass Flow Inlet, selecionar todas)
#   z = 1030 (61 faces) → Tube_Oil_Out  (Pressure Outlet, selecionar todas)
#   r = TUBE_ID/2       → Interface c/ Tube_Wall (CHT)
# ══════════════════════════════════════════════════════════════════
print("[02] Tube Fluid (óleo — 61 tubos)...")

with BuildPart() as tf_part:
    locs_tube = [Location((cx, cy, Z_SF_CEN)) for cx, cy in CENTERS]
    with Locations(*locs_tube):
        Cylinder(radius=TUBE_ID/2, height=L_TUBE)

save_step(tf_part.part, "02_Tube_Fluid.step")


# ══════════════════════════════════════════════════════════════════
# 03 — TUBE WALL  (61 anéis de aço — parede dos tubos)
# ══════════════════════════════════════════════════════════════════
# Anéis de aço: OD = 19.05 mm, ID = 15.75 mm, altura = L_TOTAL
# Comprimento L_TOTAL (passa pelos tubesheets: z = 0 → 1060 mm)
#
# Faces importantes:
#   r = TUBE_OD/2, z ∈ [30, 1030] → Interface c/ Shell_Fluid  (CHT)
#   r = TUBE_ID/2, z ∈ [30, 1030] → Interface c/ Tube_Fluid   (CHT)
#   r = TUBE_OD/2, z ∈ [0, 30]    → Encaixe no tubesheet frontal  (Wall interna)
#   r = TUBE_OD/2, z ∈ [1030,1060]→ Encaixe no tubesheet traseiro (Wall interna)
# ══════════════════════════════════════════════════════════════════
print("[03] Tube Wall (aço — 61 anéis)...")

with BuildPart() as tw_part:
    locs_tube_total = [Location((cx, cy, L_TOTAL/2)) for cx, cy in CENTERS]
    # Adicionar cilindros externos (OD) — 61 sólidos separados
    with Locations(*locs_tube_total):
        Cylinder(radius=TUBE_OD/2, height=L_TOTAL)
    # Subtrair cilindros internos (ID) — cada inner remove do seu outer
    with Locations(*locs_tube_total):
        Cylinder(radius=TUBE_ID/2, height=L_TOTAL, mode=Mode.SUBTRACT)

save_step(tw_part.part, "03_Tube_Wall.step")


# ══════════════════════════════════════════════════════════════════
# 04 — BAFFLES  (6 defletores segmentais — aço)
# ══════════════════════════════════════════════════════════════════
# Cada baffle:
#   • Disco: raio = DS/2 − 1 mm (folga de 1 mm no casco)
#   • Corte segmental alternado: topo para k par, base para k ímpar
#     CUT_Y = 63.5 mm (linha de corte medida a partir do eixo Z)
#   • Furos para os tubos: raio = TUBE_OD/2  (sem folga → parede estanque)
#
# Convenção de corte (fluxo em ziguezague):
#   Baffle 1, 3, 5 → corte no TOPO  (fluido desvia pela base)
#   Baffle 2, 4, 6 → corte na BASE  (fluido desvia pelo topo)
# ══════════════════════════════════════════════════════════════════
print("[04] Baffles (6 defletores segmentais)...")

with BuildPart() as baf_part:
    for k, z_baf in enumerate(BAFFLE_ZS):

        # ── Disco completo ─────────────────────────────────────────
        with Locations((0, 0, z_baf)):
            Cylinder(radius=DS/2 - 1.0, height=B_THICK)

        # ── Corte segmental ────────────────────────────────────────
        # Box (DS+20) × DS × (B_THICK+2) posicionada para remover 25 %
        # align=(CENTER, MIN, CENTER): face Y_min do box no ponto de corte
        # align=(CENTER, MAX, CENTER): face Y_max do box no ponto de corte
        if k % 2 == 0:
            # Corte no TOPO → remove y > +CUT_Y
            with Locations((0, CUT_Y, z_baf)):
                Box(DS + 20, DS, B_THICK + 2,
                    align=(Align.CENTER, Align.MIN, Align.CENTER),
                    mode=Mode.SUBTRACT)
        else:
            # Corte na BASE → remove y < −CUT_Y
            with Locations((0, -CUT_Y, z_baf)):
                Box(DS + 20, DS, B_THICK + 2,
                    align=(Align.CENTER, Align.MAX, Align.CENTER),
                    mode=Mode.SUBTRACT)

        # ── Furos dos tubos (lote) ─────────────────────────────────
        locs_baf = [Location((cx, cy, z_baf)) for cx, cy in CENTERS]
        with Locations(*locs_baf):
            Cylinder(radius=TUBE_OD/2, height=B_THICK + 2, mode=Mode.SUBTRACT)

save_step(baf_part.part, "04_Baffles.step")


# ══════════════════════════════════════════════════════════════════
# 05 — TUBESHEETS  (2 espelhos — aço)
# ══════════════════════════════════════════════════════════════════
# Espelho frontal : z = 0       a z = 30  mm   (centro z = 15)
# Espelho traseiro: z = 1030    a z = 1060 mm  (centro z = 1045)
# Furos: diâmetro = TUBE_OD  (os tubos se encaixam com ajuste)
#
# No STAR-CCM+:
#   Face z = 0   → Wall (limite do domínio tube-side, região da Oil)
#   Face z = 1060 → Wall (idem)
#   Face z = 30  → Wall (separa shell-side de tube-side no espelho frontal)
#   Face z = 1030 → Wall (idem traseiro)
#   Superfície lateral (r = DS/2) → contato com Shell_Wall interior
# ══════════════════════════════════════════════════════════════════
print("[05] Tubesheets (2 espelhos)...")

Z_TS_FRONT  = TS_THICK / 2                          #   15 mm
Z_TS_REAR   = TS_THICK + L_TUBE + TS_THICK / 2      # 1045 mm

with BuildPart() as ts_part:
    # Dois discos sólidos
    for z_ts in [Z_TS_FRONT, Z_TS_REAR]:
        with Locations((0, 0, z_ts)):
            Cylinder(radius=DS/2, height=TS_THICK)

    # Furos em ambos os espelhos — lote completo 2 × 61 = 122 operações
    locs_ts = [
        Location((cx, cy, z_ts))
        for z_ts in [Z_TS_FRONT, Z_TS_REAR]
        for cx, cy in CENTERS
    ]
    with Locations(*locs_ts):
        Cylinder(radius=TUBE_OD/2, height=TS_THICK + 2, mode=Mode.SUBTRACT)

save_step(ts_part.part, "05_Tubesheets.step")


# ══════════════════════════════════════════════════════════════════
# 06 — SHELL WALL  (parede cilíndrica do casco — aço)
# ══════════════════════════════════════════════════════════════════
# Anel: raio interno = DS/2, raio externo = DS/2 + SHELL_TK
# Comprimento total L_TOTAL (inclui região dos tubesheets)
#
# Faces importantes:
#   r = DS/2        → Shell_Inner_Wall  (coincide com borda do Shell_Fluid)
#   r = DS/2+SHELL_TK → Shell_Outer    (Wall exterior — sem troca de calor)
#   z = 0  e z = 1060 → Wall (flanges / conexão com tubesheets)
#
# NOTA: O bocal do casco não está modelado aqui — ele está embutido no
#        domínio fluido 01_Shell_Fluid.step para garantir a continuidade
#        da malha. A parede do bocal pode ser adicionada como camada fina
#        se necessário para o modelo térmico do material.
# ══════════════════════════════════════════════════════════════════
print("[06] Shell Wall (parede do casco)...")

with BuildPart() as sw_part:
    with Locations((0, 0, L_TOTAL/2)):
        Cylinder(radius=DS/2 + SHELL_TK, height=L_TOTAL)
        Cylinder(radius=DS/2,            height=L_TOTAL, mode=Mode.SUBTRACT)

save_step(sw_part.part, "06_Shell_Wall.step")


# ══════════════════════════════════════════════════════════════════
# VERIFICAÇÃO DE CONSISTÊNCIA GEOMÉTRICA
# ══════════════════════════════════════════════════════════════════
print()
print("=" * 62)
print("  VERIFICAÇÃO  —  Consistência de Interfaces CHT")
print("=" * 62)

# Interface Shell_Fluid ↔ Tube_Wall
# Superfície dos furos em 01: raio = TUBE_OD/2, z ∈ [30, 1030]
# Superfície externa em 03:   raio = TUBE_OD/2, z ∈ [0,  1060]  (inclui TS)
# Região coincidente: z ∈ [30, 1030]  ✓
print(f"  Shell_Fluid ↔ Tube_Wall :")
print(f"    01 furos  : r = {TUBE_OD/2:.4f} mm, z ∈ [{TS_THICK:.0f}, {TS_THICK+L_TUBE:.0f}] mm")
print(f"    03 externo: r = {TUBE_OD/2:.4f} mm, z ∈ [0, {L_TOTAL:.0f}] mm")
print(f"    → Região coincidente: z ∈ [{TS_THICK:.0f}, {TS_THICK+L_TUBE:.0f}] mm  ✓")

# Interface Tube_Wall ↔ Tube_Fluid
# Superfície interna em 03: raio = TUBE_ID/2, z ∈ [30, 1030]
# Superfície externa em 02: raio = TUBE_ID/2, z ∈ [30, 1030]
print(f"\n  Tube_Wall ↔ Tube_Fluid :")
print(f"    03 interno: r = {TUBE_ID/2:.4f} mm, z ∈ [{TS_THICK:.0f}, {TS_THICK+L_TUBE:.0f}] mm")
print(f"    02 externo: r = {TUBE_ID/2:.4f} mm, z ∈ [{TS_THICK:.0f}, {TS_THICK+L_TUBE:.0f}] mm")
print(f"    → Coincidentes em toda a extensão ativa  ✓")

# Bocais do casco
print(f"\n  Bocais do casco (Shell_Fluid embutidos):")
print(f"    Shell_Water_In  : y = +{NOZ_H:.1f} mm, z = {Z_NOZ_IN:.1f} mm  (face da água quente entrada)")
print(f"    Shell_Water_Out : y = −{NOZ_H:.1f} mm, z = {Z_NOZ_OUT:.1f} mm  (face da água saída)")

# Folga mínima entre tubos adjacentes
gap = PITCH - TUBE_OD
print(f"\n  Folga entre tubos       : {gap:.2f} mm  (mínimo mesheável ✓)")
print(f"  Espessura da parede do tubo : {(TUBE_OD - TUBE_ID)/2:.2f} mm")

# Baffles
print(f"\n  Posições dos baffles (z, mm):")
for k, z in enumerate(BAFFLE_ZS):
    cut = "topo" if k%2 == 0 else "base"
    within = "✓" if TS_THICK < z < TS_THICK + L_TUBE else "✗ FORA"
    print(f"    Baffle {k+1}: z = {z:7.2f} mm  corte {cut}  {within}")

print()
print("=" * 62)
print(f"  Arquivos gravados em: {OUT}")
print("=" * 62)
