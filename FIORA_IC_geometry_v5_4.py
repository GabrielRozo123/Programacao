"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.4 — 16/Mai/2026   ★ INCLUI DIFUSORES COMO FERRAMENTA DE IMPRINT ★

Mudança vs v5.3:
  ✅ Adicionado FIORA_IC_v5_4_diffusers.step — 4 pequenos cilindros
     DN60 que SERVEM COMO FERRAMENTA DE IMPRINT na parede do reator.
     Não representam o difusor físico (que é uma placa porosa de
     microfuros, modelada apenas como BC).  O fluxo é:
        1. Importar diffusers no STAR-CCM+
        2. Boolean Imprint (NÃO Unite, NÃO Subtract) entre diffusers
           e fluid_domain → cria 4 faces na parede
        3. Deletar os corpos diffusers (só interessam as faces criadas)
        4. Atribuir as 4 faces como Mass Flow Inlet (gás biogás)

  Posicionamento dos difusores (memorial §8):
     • z = 1,75 m do fundo (12% da altura útil)
     • azimute 0°, 90°, 180°, 270°
     • DN60 (Ø 60 mm — estimativa do memorial)

Todas as demais correções da v5.3 mantidas:
  - Topo CÔNCAVO (cut com esfera R_sph=2,221 m)
  - DN100 em arquivo separado como BAFFLE de parede fina (4 mm)
  - Saídas DN50 todas a 0°
  - Bocais com inclinação ASCENDENTE +7,5°
  - DN100 inicia em z=1,0 m

ARQUIVOS GERADOS (6 STEP):
  • FIORA_IC_v5_4_fluid_domain.step  (cilindro + topo côncavo + 4×DN50)
  • FIORA_IC_v5_4_return_tube.step   (DN100 parede fina 4 mm — baffle)
  • FIORA_IC_v5_4_separators.step    (8 meias-placas)
  • FIORA_IC_v5_4_nozzles.step       (6 bocais tangenciais)
  • FIORA_IC_v5_4_electrodes.step    (2 pares A/C)
  • FIORA_IC_v5_4_diffusers.step     (4 marcadores p/ Imprint — deletar após)

INSTALAÇÃO: pip install cadquery
EXECUÇÃO:   python3 FIORA_IC_geometry_v5_4.py
"""

import math
import cadquery as cq

# ═══════════════════════════════════════════════════════
# PARÂMETROS — Memorial Descritivo v1.0 (16/05/2026)
# Origem do mundo: centro do reator. z ∈ [−H/2, +H/2].
# ═══════════════════════════════════════════════════════

# §2.1 Corpo principal
D_REACTOR   = 2.090
H_REACTOR   = 14.600
R_REACTOR   = D_REACTOR / 2.0

# §2.2 Topo CÔNCAVO toroesférico — profundidade D/8
TOP_DEPTH   = D_REACTOR / 8.0          # 0.261 m
R_KNUCKLE   = 0.10 * D_REACTOR         # 0.209 m
R_SPH_TOP   = (R_REACTOR**2 + TOP_DEPTH**2) / (2.0 * TOP_DEPTH)   # ≈ 2.221 m

# §5 Tubo de retorno DN100 (BAFFLE — arquivo separado)
D_RETURN_OUT  = 0.100
WALL_RETURN   = 0.004
D_RETURN_IN   = D_RETURN_OUT - 2.0 * WALL_RETURN
R_RETURN_OUT  = D_RETURN_OUT / 2.0
R_RETURN_IN   = D_RETURN_IN  / 2.0
Z_RETURN_BOT  = 1.0
Z_RETURN_TOP  = H_REACTOR

# §3 Bocais tangenciais (DN80, atravessam a parede)
N_NOZZLES         = 6
NOZZLE_D          = 0.080
NOZZLE_L          = 0.300
NOZZLE_INCL_UP    = 7.5
NOZZLE_Z          = 0.250
NOZZLE_TANG_ANGLE = 80.0

# §4 Separadores trifásicos — DN50 todas a 0° (§5.2)
SEPARATORS = [
    (0.20, 47.5, 0.0),
    (0.40, 52.5, 0.0),
    (0.60, 57.5, 0.0),
    (0.95, 57.5, 0.0),
]
SEP_THICK   = 0.008
SEP_GAP_R   = R_RETURN_OUT + 0.025
D_SEP_OUT   = 0.050

# §6 Eletrodos — 2 pares A/C
ELEC_H          = 2.400
ELEC_W          = 0.520
ELEC_THICK      = 0.008
ELEC_R_POS      = R_REACTOR * 0.65
ELEC_Z_BOT      = 0.250
ELEC_Z_CTR_REL  = ELEC_Z_BOT + ELEC_H/2.0 - H_REACTOR/2.0
PAIR_ANGLES     = [0.0, 180.0]
ELEC_GAP_FACE   = 0.030

# §8 Difusores — MARCADORES PARA IMPRINT (não geometria real)
N_DIFF          = 4
DIFF_D          = 0.060                # DN60
DIFF_Z          = 1.75                 # 12% da altura útil (memorial §8)
DIFF_AZIMUTHS   = [0.0, 90.0, 180.0, 270.0]   # distribuídos a 90°
# Comprimento do "stub" de imprint: 50 mm dentro + 50 mm fora da parede
DIFF_STUB_LEN   = 0.100


# ═══════════════════════════════════════════════════════
# DOMÍNIO FLUIDO
# ═══════════════════════════════════════════════════════

def build_fluid_domain():
    """Cilindro + topo CÔNCAVO cortado por esfera."""
    print("  [1] Cilindro base + topo côncavo (cut)...")
    cyl = cq.Workplane("XY").cylinder(H_REACTOR, R_REACTOR)
    z_c = (H_REACTOR/2.0 - TOP_DEPTH) + R_SPH_TOP
    sphere = cq.Workplane("XY").sphere(R_SPH_TOP).translate((0, 0, z_c))
    fluid = cyl.cut(sphere)
    try:
        fluid = fluid.edges(">Z").fillet(R_KNUCKLE * 0.4)
        print(f"     joelho r_fillet={R_KNUCKLE*0.4:.3f} m aplicado")
    except Exception as e:
        print(f"     joelho ignorado ({e})")
    return fluid


def cut_dn50_outlets(fluid):
    """4 furos DN50, todos a 0° (memorial §5.2)."""
    print("  [2] Furos DN50 (4×, todas a 0°)...")
    for pct, _tilt, az in SEPARATORS:
        z_rel = pct * H_REACTOR - H_REACTOR/2.0
        hole = (cq.Workplane("YZ")
                .circle(D_SEP_OUT/2.0)
                .extrude(0.20)
                .translate((R_REACTOR - 0.05, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), az)
                .translate((0, 0, z_rel)))
        fluid = fluid.cut(hole)
        print(f"     DN50 @ {pct*100:.0f}% (z_rel={z_rel:+.2f} m) az={az:.0f}°")
    return fluid


# ═══════════════════════════════════════════════════════
# TUBO DE RETORNO DN100 — BAFFLE de parede fina
# ═══════════════════════════════════════════════════════

def build_return_tube():
    print(f"  [3] Tubo DN100 parede fina ({WALL_RETURN*1000:.0f} mm)...")
    H_tube = Z_RETURN_TOP - Z_RETURN_BOT
    z_ctr  = (Z_RETURN_TOP + Z_RETURN_BOT)/2.0 - H_REACTOR/2.0
    outer = cq.Workplane("XY").cylinder(H_tube, R_RETURN_OUT)
    inner = cq.Workplane("XY").cylinder(H_tube + 0.01, R_RETURN_IN)
    tube  = outer.cut(inner).translate((0, 0, z_ctr))
    print(f"     z=[{Z_RETURN_BOT:.2f}, {Z_RETURN_TOP:.2f}] m  H={H_tube:.2f} m")
    return tube


# ═══════════════════════════════════════════════════════
# SEPARADORES
# ═══════════════════════════════════════════════════════

def build_separators():
    print("  [4] Separadores (8 placas)...")
    clip_r   = R_REACTOR - 0.004
    clip_cyl = cq.Workplane("XY").cylinder(H_REACTOR * 1.2, clip_r)

    sep_list = []
    for pct, tilt, _az in SEPARATORS:
        z_rel = pct * H_REACTOR - H_REACTOR/2.0
        span  = R_REACTOR - SEP_GAP_R + 0.05
        depth = D_REACTOR * 1.05

        base = cq.Workplane("XY").box(span, depth, SEP_THICK)
        pL = base.rotate((0, 0, 0), (0, 1, 0),  tilt)
        pR = base.rotate((0, 0, 0), (0, 1, 0), -tilt)

        offset  = SEP_GAP_R + span/2.0
        plate_L = pL.translate((-offset, 0, z_rel))
        plate_R = pR.translate(( offset, 0, z_rel))

        try:
            sep_list.append(plate_L.intersect(clip_cyl))
            sep_list.append(plate_R.intersect(clip_cyl))
            print(f"     {pct*100:.0f}%: ±{tilt}° ✅")
        except Exception as e:
            sep_list.append(plate_L); sep_list.append(plate_R)
            print(f"     {pct*100:.0f}%: ±{tilt}° clip falhou ({e}) ⚠️")
    return sep_list


# ═══════════════════════════════════════════════════════
# BOCAIS — atravessam a parede, inclinação ASCENDENTE
# ═══════════════════════════════════════════════════════

def build_nozzles():
    print(f"  [5] Bocais DN80 ({N_NOZZLES}×, +{NOZZLE_INCL_UP}° ASCENDENTE)...")
    noz_list = []
    tang_rad = math.radians(NOZZLE_TANG_ANGLE)
    incl_rad = math.radians(NOZZLE_INCL_UP)

    for i in range(N_NOZZLES):
        a     = math.radians(i * (360.0 / N_NOZZLES))
        r_hat = (math.cos(a),  math.sin(a))
        t_hat = (-math.sin(a), math.cos(a))

        dx = -math.cos(tang_rad) * r_hat[0] + math.sin(tang_rad) * t_hat[0]
        dy = -math.cos(tang_rad) * r_hat[1] + math.sin(tang_rad) * t_hat[1]
        dz = +math.tan(incl_rad)
        mag = math.sqrt(dx*dx + dy*dy + dz*dz)
        dx /= mag;  dy /= mag;  dz /= mag

        cx = R_REACTOR * r_hat[0]
        cy = R_REACTOR * r_hat[1]
        cz = NOZZLE_Z - H_REACTOR/2.0

        noz = cq.Workplane("XY").cylinder(NOZZLE_L, NOZZLE_D/2.0)
        ang_rot = math.degrees(math.acos(max(-1.0, min(1.0, dz))))
        if ang_rot > 1e-3:
            ax_x, ax_y = -dy, dx
            noz = noz.rotate((0, 0, 0), (ax_x, ax_y, 0.0), ang_rot)
        noz_list.append(noz.translate((cx, cy, cz)))
        print(f"     bocal {i+1}: az={math.degrees(a):.0f}°")
    return noz_list


# ═══════════════════════════════════════════════════════
# ELETRODOS
# ═══════════════════════════════════════════════════════

def build_electrode_pairs():
    print("  [6] Eletrodos — 2 pares A/C...")
    r_ext = ELEC_R_POS + ELEC_W/2.0
    r_int = ELEC_R_POS - ELEC_W/2.0
    assert r_ext < R_REACTOR
    assert r_int > R_RETURN_OUT
    print(f"     verificação radial: r_int={r_int:.3f}  r_ext={r_ext:.3f}  "
          f"folga parede={R_REACTOR - r_ext:.3f} m")

    c2c = ELEC_GAP_FACE + ELEC_THICK
    plates = []
    for i, pair_angle in enumerate(PAIR_ANGLES):
        a       = math.radians(pair_angle)
        radial  = ( math.cos(a),  math.sin(a))
        tangent = (-math.sin(a),  math.cos(a))

        cx = ELEC_R_POS * radial[0]
        cy = ELEC_R_POS * radial[1]
        base = cq.Workplane("XY").box(ELEC_W, ELEC_THICK, ELEC_H)

        ax = cx + (c2c/2.0) * tangent[0]
        ay = cy + (c2c/2.0) * tangent[1]
        anode = (base.rotate((0, 0, 0), (0, 0, 1), pair_angle)
                     .translate((ax, ay, ELEC_Z_CTR_REL)))

        bx = cx - (c2c/2.0) * tangent[0]
        by = cy - (c2c/2.0) * tangent[1]
        cathode = (base.rotate((0, 0, 0), (0, 0, 1), pair_angle)
                       .translate((bx, by, ELEC_Z_CTR_REL)))

        plates.extend([anode, cathode])
        print(f"     par {i+1} @ {pair_angle:.0f}°  c2c={c2c*1000:.1f} mm")
    return plates


# ═══════════════════════════════════════════════════════
# DIFUSORES — marcadores radiais para IMPRINT (NÃO geometria física)
# ═══════════════════════════════════════════════════════

def build_diffuser_imprint_stubs():
    """
    4 cilindros pequenos DN60 atravessando a parede radialmente em
    z = 1,75 m, distribuídos a 0/90/180/270°.  Eixo radial perpendicular
    à parede.  Usados como ferramenta de Boolean Imprint no STAR-CCM+
    para criar 4 faces de Mass Flow Inlet — depois deletar os corpos.
    """
    print(f"  [7] Difusores ({N_DIFF}× stubs DN60 para Imprint @ z=1,75 m)...")
    z_rel = DIFF_Z - H_REACTOR/2.0
    stubs = []
    for az in DIFF_AZIMUTHS:
        # Stub radial: cilindro de eixo horizontal +X, atravessando a parede
        stub = (cq.Workplane("YZ")
                .circle(DIFF_D/2.0)
                .extrude(DIFF_STUB_LEN)
                # Centrado na parede (metade dentro, metade fora)
                .translate((R_REACTOR - DIFF_STUB_LEN/2.0, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), az)
                .translate((0, 0, z_rel)))
        stubs.append(stub)
        print(f"     difusor @ az={az:.0f}°  z={DIFF_Z:.2f} m  Ø={DIFF_D*1000:.0f} mm")
    return stubs


# ═══════════════════════════════════════════════════════
# MONTAGEM
# ═══════════════════════════════════════════════════════

print("=" * 64)
print("FIORA IC v5.4 — Memorial v1.0 + Difusores (Imprint)")
print("=" * 64)
print(f"  Reator      : D={D_REACTOR} m  H={H_REACTOR} m")
print(f"  Topo        : CÔNCAVO h={TOP_DEPTH:.3f} m  R_sph={R_SPH_TOP:.3f} m")
print(f"  DN100       : tubo BAFFLE Ø{D_RETURN_OUT*1000:.0f} mm  "
      f"esp {WALL_RETURN*1000:.0f} mm")
print(f"  Separadores : {len(SEPARATORS)} níveis — DN50 todas a 0°")
print(f"  Bocais      : {N_NOZZLES}× DN80, +{NOZZLE_INCL_UP}° ASCENDENTE")
print(f"  Eletrodos   : {len(PAIR_ANGLES)} pares A/C, gap {ELEC_GAP_FACE*1000:.0f} mm")
print(f"  Difusores   : {N_DIFF}× marcadores p/ Imprint @ z={DIFF_Z:.2f} m")
print()

fluid      = build_fluid_domain()
fluid      = cut_dn50_outlets(fluid)
tube       = build_return_tube()
sep_list   = build_separators()
noz_list   = build_nozzles()
elec_list  = build_electrode_pairs()
diff_list  = build_diffuser_imprint_stubs()


def _union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


# ═══════════════════════════════════════════════════════
# EXPORTAÇÃO — 6 STEP
# ═══════════════════════════════════════════════════════
print("\nExportando STEP files...")

cq.exporters.export(fluid, "FIORA_IC_v5_4_fluid_domain.step")
print("  ✅ FIORA_IC_v5_4_fluid_domain.step  (cilindro + topo côncavo + 4×DN50)")

cq.exporters.export(tube, "FIORA_IC_v5_4_return_tube.step")
print("  ✅ FIORA_IC_v5_4_return_tube.step   (DN100 parede fina — BAFFLE)")

cq.exporters.export(_union(sep_list), "FIORA_IC_v5_4_separators.step")
print("  ✅ FIORA_IC_v5_4_separators.step    (8 meias-placas Λ)")

cq.exporters.export(_union(noz_list), "FIORA_IC_v5_4_nozzles.step")
print("  ✅ FIORA_IC_v5_4_nozzles.step       (6 bocais tangenciais)")

cq.exporters.export(_union(elec_list), "FIORA_IC_v5_4_electrodes.step")
print("  ✅ FIORA_IC_v5_4_electrodes.step    (2 pares A/C)")

cq.exporters.export(_union(diff_list), "FIORA_IC_v5_4_diffusers.step")
print("  ✅ FIORA_IC_v5_4_diffusers.step     (4 stubs p/ Imprint — DELETAR após)")

print("\n" + "=" * 64)
print("v5.4 CONCLUÍDO")
print("=" * 64)
print(f"""
FLUXO NO STAR-CCM+ (após importar os 6 STEP):

  1. UNITE: fluid_domain  +  nozzles
        → cria os 6 canais de Velocity Inlet (líquido)

  2. IMPRINT: fluid_domain  +  diffusers       ← novidade v5.4
        → cria 4 faces elípticas pequenas na parede em z=1,75 m
        → renomear faces: Diffuser_1..4
        → atribuir Boundary Type = Mass Flow Inlet (gás)
        → DELETAR os corpos diffusers (já não servem)

  3. NÃO unir: return_tube, separators, electrodes
        → ficam como corpos separados → viram BAFFLES / WALLS internos

  4. Boundary Conditions (memorial §10.1):
        • 6 faces externas dos bocais   → Velocity Inlet (líquido)
        • Face topo do DN100            → Velocity Inlet (Q=350 m³/d, −Z)
        • 4 faces dos difusores         → Mass Flow Inlet (gás biogás)
        • 4 furos DN50                  → Pressure Outlet
        • Parede cilíndrica + topo      → No-slip Wall
        • Placas dos separadores        → Baffle No-slip
        • Parede do DN100               → Baffle No-slip
        • Placas dos eletrodos          → No-slip Wall (sólido inerte)
""")
