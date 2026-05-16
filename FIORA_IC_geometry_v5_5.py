"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.5 — 16/Mai/2026  ★ DIFUSORES ATUALIZADOS — VINÍCIUS 16:50 ★

ATUALIZAÇÃO v5.5 (sobre v5.4):
  Difusores reespecificados por Vinícius Alberoni em 16/05/2026 16:50:
    • Quantidade: 12 (não 4)
    • Localização: NO FUNDO, entre os bocais de alimentação
    • Tipo: disco de bolha fina DN225/DN250 → adotado DN250
    • Disposição: 6 setores × 2 difusores por setor
                  azimute dos setores: 30°/90°/150°/210°/270°/330°
                  (no meio dos pares de bocais 0/60/120/180/240/300°)
    • 2 difusores por setor → adotado disposição radial:
        - 1 interno  (r = 0,35 m)
        - 1 externo  (r = 0,80 m)
    • Vazão operacional: 2–4 Nm³/h por difusor
                         total: 24–48 Nm³/h
    • Bolha gerada:      1–3 mm
    • Blower:            ~2,0 kgf/cm² (info BC, não geometria)

Todas as correções da v5.4 mantidas para os demais componentes.

ARQUIVOS GERADOS (6 STEP):
  • FIORA_IC_v5_5_fluid_domain.step  (cilindro + topo côncavo + 4×DN50)
  • FIORA_IC_v5_5_return_tube.step   (DN100 parede fina 4 mm — baffle)
  • FIORA_IC_v5_5_separators.step    (8 meias-placas)
  • FIORA_IC_v5_5_nozzles.step       (6 bocais tangenciais)
  • FIORA_IC_v5_5_electrodes.step    (2 pares A/C)
  • FIORA_IC_v5_5_diffusers.step     (12 discos DN250 p/ Imprint no fundo)

INSTALAÇÃO: pip install cadquery
EXECUÇÃO:   python3 FIORA_IC_geometry_v5_5.py
"""

import math
import cadquery as cq

# ═══════════════════════════════════════════════════════
# PARÂMETROS — Memorial v1.0 + atualizações Vinícius 16/05
# Origem do mundo: centro do reator. z ∈ [−H/2, +H/2].
# ═══════════════════════════════════════════════════════

# §2.1 Corpo principal
D_REACTOR   = 2.090
H_REACTOR   = 14.600
R_REACTOR   = D_REACTOR / 2.0

# §2.2 Topo CÔNCAVO toroesférico (profundidade D/8)
TOP_DEPTH   = D_REACTOR / 8.0
R_KNUCKLE   = 0.10 * D_REACTOR
R_SPH_TOP   = (R_REACTOR**2 + TOP_DEPTH**2) / (2.0 * TOP_DEPTH)

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
# Azimutes dos bocais: 0°, 60°, 120°, 180°, 240°, 300°
NOZZLE_AZIMUTHS   = [i * (360.0 / N_NOZZLES) for i in range(N_NOZZLES)]

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

# §8 Difusores — ATUALIZADO Vinícius 16/05/2026 16:50
N_DIFF             = 12
DIFF_D             = 0.250                # DN250 (faixa DN225–DN250)
DIFF_THICK         = 0.050                # altura do stub p/ imprint
# Azimutes dos 6 setores (entre bocais):
DIFF_SECTOR_AZ     = [30.0, 90.0, 150.0, 210.0, 270.0, 330.0]
# Dois difusores por setor: disposição radial (1 interno + 1 externo)
DIFF_R_INNER       = 0.35
DIFF_R_OUTER       = 0.80
# Vazão (info para BC no STAR-CCM+): 2–4 Nm³/h por difusor → 24–48 Nm³/h total
DIFF_Q_UNIT_MIN    = 2.0      # Nm³/h por difusor
DIFF_Q_UNIT_MAX    = 4.0
DIFF_BUBBLE_MM     = (1.0, 3.0)
DIFF_BLOWER_P_KGF  = 2.0      # kgf/cm² nominal


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
        print(f"     DN50 @ {pct*100:.0f}% z_rel={z_rel:+.2f} m az={az:.0f}°")
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

    for az_deg in NOZZLE_AZIMUTHS:
        a     = math.radians(az_deg)
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
        print(f"     bocal @ az={az_deg:.0f}°")
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
    print(f"     r_int={r_int:.3f}  r_ext={r_ext:.3f}  "
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
# DIFUSORES — 12× discos DN250 no FUNDO (Vinícius 16/05 16:50)
# ═══════════════════════════════════════════════════════

def build_diffuser_imprint_stubs():
    """
    12 discos DN250 no FUNDO do reator, distribuídos em 6 setores
    (entre os bocais), 2 difusores por setor (1 interno + 1 externo).

    Cada disco é um cilindro fino (h=DIFF_THICK), centrado no plano
    do fundo (z = −H/2): metade dentro do fluid_domain, metade fora.
    O Boolean Imprint no STAR-CCM+ cria 12 faces circulares no fundo
    (aresta = perímetro do disco onde ele cruza z=−H/2).
    Essas faces viram Mass Flow Inlet.  Deletar os corpos após imprint.
    """
    print(f"  [7] Difusores ({N_DIFF}× discos DN{DIFF_D*1000:.0f} no fundo)...")
    print(f"     6 setores @ {DIFF_SECTOR_AZ}°  ×  2 por setor "
          f"(r={DIFF_R_INNER:.2f}/{DIFF_R_OUTER:.2f} m)")

    z_ctr_fundo = -H_REACTOR/2.0          # centro do disco no plano do fundo
    stubs = []

    # Sanity: não pode bater nos eletrodos
    r_ext_elec = ELEC_R_POS + ELEC_W/2.0  # 0,94 m
    r_int_elec = ELEC_R_POS - ELEC_W/2.0  # 0,42 m
    # Os eletrodos vão de z=0,25 a 2,65 m do fundo (z_rel=-7,05 a -4,65)
    # Os difusores estão em z=0 (z_rel=-7,30) → não há overlap vertical, ok.

    for sector_az in DIFF_SECTOR_AZ:
        for r in (DIFF_R_INNER, DIFF_R_OUTER):
            a = math.radians(sector_az)
            cx = r * math.cos(a)
            cy = r * math.sin(a)

            disc = (cq.Workplane("XY")
                    .cylinder(DIFF_THICK, DIFF_D/2.0)
                    .translate((cx, cy, z_ctr_fundo)))
            stubs.append(disc)

            # Sanity print
            zona = "INT" if r == DIFF_R_INNER else "EXT"
            # Verificar se cai sobre eletrodo (não deveria)
            tag_elec = ""
            if sector_az in (0, 180):  # mesma direção dos eletrodos
                tag_elec = "  ⚠️ checar conflito eletrodo"
            print(f"     setor {sector_az:>5.1f}°  {zona} r={r:.2f} m  "
                  f"centro=({cx:+.3f},{cy:+.3f}){tag_elec}")

    return stubs


# ═══════════════════════════════════════════════════════
# MONTAGEM
# ═══════════════════════════════════════════════════════

print("=" * 64)
print("FIORA IC v5.5 — Memorial v1.0 + Difusores Vinícius 16/05")
print("=" * 64)
print(f"  Reator      : D={D_REACTOR} m  H={H_REACTOR} m")
print(f"  Topo        : CÔNCAVO h={TOP_DEPTH:.3f} m")
print(f"  DN100       : BAFFLE Ø{D_RETURN_OUT*1000:.0f} mm  "
      f"esp {WALL_RETURN*1000:.0f} mm")
print(f"  Separadores : {len(SEPARATORS)} níveis — DN50 todas a 0°")
print(f"  Bocais      : {N_NOZZLES}× DN80, +{NOZZLE_INCL_UP}° ASCENDENTE")
print(f"  Eletrodos   : {len(PAIR_ANGLES)} pares A/C, gap {ELEC_GAP_FACE*1000:.0f} mm")
print(f"  Difusores   : {N_DIFF}× DN{DIFF_D*1000:.0f} discos no FUNDO  "
      f"(6 setores × 2)")
print(f"                {DIFF_Q_UNIT_MIN}–{DIFF_Q_UNIT_MAX} Nm³/h cada  "
      f"→ total {N_DIFF*DIFF_Q_UNIT_MIN:.0f}–{N_DIFF*DIFF_Q_UNIT_MAX:.0f} Nm³/h")
print(f"                bolha {DIFF_BUBBLE_MM[0]}–{DIFF_BUBBLE_MM[1]} mm  "
      f"| blower ~{DIFF_BLOWER_P_KGF} kgf/cm²")
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

cq.exporters.export(fluid, "FIORA_IC_v5_5_fluid_domain.step")
print("  ✅ FIORA_IC_v5_5_fluid_domain.step  (cilindro + topo côncavo + 4×DN50)")

cq.exporters.export(tube, "FIORA_IC_v5_5_return_tube.step")
print("  ✅ FIORA_IC_v5_5_return_tube.step   (DN100 parede fina — BAFFLE)")

cq.exporters.export(_union(sep_list), "FIORA_IC_v5_5_separators.step")
print("  ✅ FIORA_IC_v5_5_separators.step    (8 meias-placas Λ)")

cq.exporters.export(_union(noz_list), "FIORA_IC_v5_5_nozzles.step")
print("  ✅ FIORA_IC_v5_5_nozzles.step       (6 bocais tangenciais)")

cq.exporters.export(_union(elec_list), "FIORA_IC_v5_5_electrodes.step")
print("  ✅ FIORA_IC_v5_5_electrodes.step    (2 pares A/C)")

cq.exporters.export(_union(diff_list), "FIORA_IC_v5_5_diffusers.step")
print(f"  ✅ FIORA_IC_v5_5_diffusers.step     "
      f"({N_DIFF} discos DN{DIFF_D*1000:.0f} no fundo — DELETAR após Imprint)")

print("\n" + "=" * 64)
print("v5.5 CONCLUÍDO")
print("=" * 64)
print(f"""
FLUXO NO STAR-CCM+ (após importar os 6 STEP):

  1. UNITE: fluid_domain  +  nozzles
        → cria 6 canais de Velocity Inlet (líquido)

  2. IMPRINT: fluid_domain  +  diffusers
        → cria {N_DIFF} faces circulares (Ø{DIFF_D*1000:.0f} mm) no FUNDO
        → renomear faces: Diffuser_01..{N_DIFF:02d}
        → DELETAR os corpos diffusers após imprint

  3. NÃO unir: return_tube, separators, electrodes
        → ficam como corpos separados → viram BAFFLES / WALLS

  4. Boundary Conditions:
     • 6 faces externas dos bocais       → Velocity Inlet (líquido)
     • Face topo do DN100                → Velocity Inlet (Q=350 m³/d, −Z)
     • {N_DIFF} faces dos difusores (fundo)     → Mass Flow Inlet (gás)
            ṁ_total = {N_DIFF*DIFF_Q_UNIT_MIN:.0f}–{N_DIFF*DIFF_Q_UNIT_MAX:.0f} Nm³/h
            d_bolha = {DIFF_BUBBLE_MM[0]}–{DIFF_BUBBLE_MM[1]} mm
     • 4 furos DN50 (parede)             → Pressure Outlet
     • Parede cilíndrica + topo          → No-slip Wall
     • Placas dos separadores            → Baffle No-slip
     • Parede do DN100                   → Baffle No-slip
     • Placas dos eletrodos              → No-slip Wall (sólido inerte)

NOTA: setores 30°/150°/210°/330° estão a 30° dos eletrodos (par 0°/180°).
      Como os difusores estão em z=0 e os eletrodos em z≥0,25 m,
      NÃO há sobreposição vertical — sem conflito geométrico.
""")
