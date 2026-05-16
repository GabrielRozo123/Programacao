"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.3 — 16/Mai/2026   ★ ALINHADA AO MEMORIAL OFICIAL v1.0 ★

Reescrito após leitura do Memorial Descritivo de Geometria v1.0
(CAEXPERTS / Vinícius Alberoni, 16/05/2026). Substitui v5.2.

CORREÇÕES SOBRE v5.2:
  1. ✅ TOPO CÔNCAVO (não convexo!).  Memorial §2.2: "calota toroesférica
     côncava", centro 0,261 m ABAIXO do plano da borda.  Implementado
     com cut(esfera) e R_sph derivado para profundidade = D/8 exata.
  2. ✅ DN100 NÃO subtraído do fluid_domain — é tubo de PAREDE FINA (4mm)
     em arquivo STEP separado (return_tube.step), modelado como BAFFLE
     no STAR-CCM+ (memorial §5 e §10).
  3. ✅ Difusores REMOVIDOS da geometria.  Memorial §8: "não possui
     geometria CAD dedicada — Mass Flow Inlet criado no STAR-CCM+".
  4. ✅ Saídas DN50 todas a 0°.  Memorial §5.2: "Simplificação CFD:
     todos a 0°".
  5. ✅ Bocais com inclinação ASCENDENTE (+7,5°).  Memorial §3:
     "Inclinação ascendente: 7,5°".  v5.2 estava descendente.
  6. ✅ DN100 começa 1,0 m acima do fundo (memorial §5.1).
  7. ✅ Bocais cruzam a parede — mantido v5.2 (memorial §10 confirma:
     "face externa = Velocity Inlet").

ARQUIVOS GERADOS (5 STEP — conforme memorial §10):
  • FIORA_IC_v5_3_fluid_domain.step  (cilindro + topo côncavo + 4×DN50)
  • FIORA_IC_v5_3_return_tube.step   (DN100 parede fina 4 mm — baffle)
  • FIORA_IC_v5_3_separators.step    (8 meias-placas)
  • FIORA_IC_v5_3_nozzles.step       (6 bocais tangenciais)
  • FIORA_IC_v5_3_electrodes.step    (2 pares A/C)

INSTALAÇÃO: pip install cadquery
EXECUÇÃO:   python3 FIORA_IC_geometry_v5_3.py

Confidencial — Tecnologia Patenteada FIORA IC
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
R_KNUCKLE   = 0.10 * D_REACTOR         # 0.209 m (referência ASME)
# Raio esférico tal que a calota tenha base R_REACTOR e profundidade
# TOP_DEPTH exatamente:  R_sph = (R² + h²) / (2h)  ≈ 2.221 m
R_SPH_TOP   = (R_REACTOR**2 + TOP_DEPTH**2) / (2.0 * TOP_DEPTH)

# §5 Tubo de retorno DN100 (BAFFLE — arquivo separado)
D_RETURN_OUT  = 0.100                  # diâmetro externo
WALL_RETURN   = 0.004                  # parede 4 mm
D_RETURN_IN   = D_RETURN_OUT - 2.0 * WALL_RETURN
R_RETURN_OUT  = D_RETURN_OUT / 2.0
R_RETURN_IN   = D_RETURN_IN  / 2.0
Z_RETURN_BOT  = 1.0                    # 1,0 m acima do fundo (memorial §5.1)
Z_RETURN_TOP  = H_REACTOR              # vai até o topo

# §3 Bocais tangenciais (DN80, atravessam a parede)
N_NOZZLES         = 6
NOZZLE_D          = 0.080              # DN80
NOZZLE_L          = 0.300
NOZZLE_INCL_UP    = 7.5                # ° ASCENDENTE (memorial §3)
NOZZLE_Z          = 0.250              # altura do centro
NOZZLE_TANG_ANGLE = 80.0                # ° do eixo c/ a radial (quase tangencial,
                                       #   com componente radial p/ atravessar parede)

# §4 Separadores trifásicos
#   (% altura, inclinação placa, azimute saída DN50)
#   Memorial §5.2: simplificação CFD — todas as DN50 a 0°
SEPARATORS = [
    (0.20, 47.5, 0.0),
    (0.40, 52.5, 0.0),
    (0.60, 57.5, 0.0),
    (0.95, 57.5, 0.0),
]
SEP_THICK   = 0.008                    # 8 mm (memorial §4)
SEP_GAP_R   = R_RETURN_OUT + 0.025     # gap central > raio externo DN100
D_SEP_OUT   = 0.050                    # DN50

# §6 Eletrodos — 2 pares A/C
ELEC_H          = 2.400
ELEC_W          = 0.520
ELEC_THICK      = 0.008
ELEC_R_POS      = R_REACTOR * 0.65     # 0.68 m do centro
ELEC_Z_BOT      = 0.250                # 0,25 m do fundo (memorial §6)
ELEC_Z_CTR_REL  = ELEC_Z_BOT + ELEC_H/2.0 - H_REACTOR/2.0
PAIR_ANGLES     = [0.0, 180.0]
# Memorial §6: "gap máximo 30 mm".  Adotado FACE-A-FACE = 30 mm (limite).
ELEC_GAP_FACE   = 0.030


# ═══════════════════════════════════════════════════════
# DOMÍNIO FLUIDO  (cilindro + topo CÔNCAVO + furos DN50)
# DN100 é tubo separado — NÃO subtraído aqui.
# ═══════════════════════════════════════════════════════

def build_fluid_domain():
    """
    Cilindro de altura H_REACTOR + calota CÔNCAVA cortada no topo.
    Profundidade da concavidade = TOP_DEPTH no centro;
    a borda da calota toca a parede em z = +H/2.
    """
    print("  [1] Cilindro base...")
    cyl = cq.Workplane("XY").cylinder(H_REACTOR, R_REACTOR)

    print(f"  [1b] Calota côncava (cut) — R_sph={R_SPH_TOP:.3f} m, "
          f"profundidade={TOP_DEPTH:.3f} m...")
    # Esfera centrada acima do topo do cilindro.
    # Ápice INFERIOR da esfera em z = H/2 − TOP_DEPTH.
    # Centro da esfera em z_c = (H/2 − TOP_DEPTH) + R_sph.
    z_c = (H_REACTOR/2.0 - TOP_DEPTH) + R_SPH_TOP
    sphere = cq.Workplane("XY").sphere(R_SPH_TOP).translate((0, 0, z_c))
    fluid = cyl.cut(sphere)

    # Fillet de joelho na borda superior (aproxima toroesférico ASME).
    try:
        fluid = fluid.edges(">Z").fillet(R_KNUCKLE * 0.4)
        print(f"     joelho r_fillet={R_KNUCKLE*0.4:.3f} m aplicado")
    except Exception as e:
        print(f"     joelho ignorado ({e})")

    return fluid


def cut_dn50_outlets(fluid):
    """4 furos DN50 (um por separador) na parede lateral, todos a 0° (memorial)."""
    print("  [2] Furos DN50 (4 saídas)...")
    for pct, _tilt, az in SEPARATORS:
        z_rel = pct * H_REACTOR - H_REACTOR/2.0
        # Cilindro horizontal +X atravessando a parede em az.
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
# TUBO DE RETORNO DN100  (arquivo separado — BAFFLE)
# Parede fina (4 mm).  No STAR-CCM+ vira baffle no_slip.
# ═══════════════════════════════════════════════════════

def build_return_tube():
    """Cilindro anelar DN100 com 4 mm de parede (memorial §5.1)."""
    print(f"  [3] Tubo DN100 parede fina (DN_ext={D_RETURN_OUT*1000:.0f} mm, "
          f"esp={WALL_RETURN*1000:.0f} mm)...")
    H_tube = Z_RETURN_TOP - Z_RETURN_BOT
    z_ctr  = (Z_RETURN_TOP + Z_RETURN_BOT)/2.0 - H_REACTOR/2.0
    outer = cq.Workplane("XY").cylinder(H_tube, R_RETURN_OUT)
    inner = cq.Workplane("XY").cylinder(H_tube + 0.01, R_RETURN_IN)
    tube  = outer.cut(inner).translate((0, 0, z_ctr))
    print(f"     z_fundo={Z_RETURN_BOT:.2f} m  z_topo={Z_RETURN_TOP:.2f} m  "
          f"H={H_tube:.2f} m")
    return tube


# ═══════════════════════════════════════════════════════
# SEPARADORES (mantido v5.2 — clip por intersecção)
# ═══════════════════════════════════════════════════════

def build_separators():
    """8 placas inclinadas (2 por nível × 4 níveis), clipadas ao cilindro."""
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
    """
    6 bocais DN80, espaçados 60°, eixo quase tangencial
    (NOZZLE_TANG_ANGLE c/ a radial), inclinação +7,5° ASCENDENTE.
    Centro do cilindro NA parede → metade fora (face = Velocity Inlet),
    metade dentro (descarga real).
    """
    print(f"  [5] Bocais DN80 ({N_NOZZLES}×, inclinação ASCENDENTE "
          f"+{NOZZLE_INCL_UP}°)...")
    noz_list = []
    tang_rad = math.radians(NOZZLE_TANG_ANGLE)
    incl_rad = math.radians(NOZZLE_INCL_UP)

    for i in range(N_NOZZLES):
        a    = math.radians(i * (360.0 / N_NOZZLES))
        r_hat = (math.cos(a),  math.sin(a))
        t_hat = (-math.sin(a), math.cos(a))

        # Direção do eixo (entrando no vaso):
        #   −cos(α)·r̂  (radial entrando)  + sin(α)·t̂  (tangencial anti-horário)
        #   +tan(incl)·ẑ                  (ASCENDENTE, memorial §3)
        dx = -math.cos(tang_rad) * r_hat[0] + math.sin(tang_rad) * t_hat[0]
        dy = -math.cos(tang_rad) * r_hat[1] + math.sin(tang_rad) * t_hat[1]
        dz = +math.tan(incl_rad)
        mag = math.sqrt(dx*dx + dy*dy + dz*dz)
        dx /= mag;  dy /= mag;  dz /= mag

        # Centro do bocal NA parede (metade fora, metade dentro)
        cx = R_REACTOR * r_hat[0]
        cy = R_REACTOR * r_hat[1]
        cz = NOZZLE_Z - H_REACTOR/2.0

        noz = cq.Workplane("XY").cylinder(NOZZLE_L, NOZZLE_D/2.0)
        ang_rot = math.degrees(math.acos(max(-1.0, min(1.0, dz))))
        if ang_rot > 1e-3:
            ax_x, ax_y = -dy, dx       # (0,0,1) × d
            noz = noz.rotate((0, 0, 0), (ax_x, ax_y, 0.0), ang_rot)
        noz_list.append(noz.translate((cx, cy, cz)))
        print(f"     bocal {i+1}: az={math.degrees(a):.0f}°  "
              f"d=({dx:+.2f},{dy:+.2f},{dz:+.2f})")
    return noz_list


# ═══════════════════════════════════════════════════════
# ELETRODOS — 2 pares A/C, gap face-a-face 30 mm
# ═══════════════════════════════════════════════════════

def build_electrode_pairs():
    """2 pares A/C; gap interpretado como FACE-A-FACE (memorial §6: máx 30 mm)."""
    print("  [6] Eletrodos — 2 pares A/C...")
    r_ext = ELEC_R_POS + ELEC_W/2.0
    r_int = ELEC_R_POS - ELEC_W/2.0
    assert r_ext < R_REACTOR, f"Eletrodo toca parede: r_ext={r_ext:.3f} > R={R_REACTOR}"
    assert r_int > R_RETURN_OUT, (
        f"Eletrodo toca DN100: r_int={r_int:.3f} < R_ret={R_RETURN_OUT}")
    print(f"     verificação radial: r_int={r_int:.3f} m  r_ext={r_ext:.3f} m  "
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
        print(f"     par {i+1} @ {pair_angle:.0f}°  c2c={c2c*1000:.1f} mm "
              f"(face-a-face {ELEC_GAP_FACE*1000:.0f} mm)")
    return plates


# ═══════════════════════════════════════════════════════
# MONTAGEM
# ═══════════════════════════════════════════════════════

print("=" * 64)
print("FIORA IC v5.3 — Alinhada ao Memorial Oficial v1.0")
print("=" * 64)
print(f"  Reator      : D={D_REACTOR} m  H={H_REACTOR} m  "
      f"V={math.pi/4*D_REACTOR**2*H_REACTOR:.1f} m³")
print(f"  Topo        : CÔNCAVO h={TOP_DEPTH:.3f} m  R_sph={R_SPH_TOP:.3f} m  (CUT)")
print(f"  DN100       : tubo BAFFLE ext={D_RETURN_OUT*1000:.0f} mm  "
      f"parede {WALL_RETURN*1000:.0f} mm  z=[{Z_RETURN_BOT},{Z_RETURN_TOP}] m")
print(f"  Separadores : {len(SEPARATORS)} níveis — DN50 todas a 0° (memorial)")
print(f"  Bocais      : {N_NOZZLES}× DN80 tangenciais, +{NOZZLE_INCL_UP}° ASCENDENTE")
print(f"  Eletrodos   : {len(PAIR_ANGLES)} pares A/C, gap face-a-face "
      f"{ELEC_GAP_FACE*1000:.0f} mm")
print(f"  Difusores   : SEM geometria CAD (Mass Flow Inlet no STAR-CCM+)")
print()

fluid     = build_fluid_domain()
fluid     = cut_dn50_outlets(fluid)
tube      = build_return_tube()
sep_list  = build_separators()
noz_list  = build_nozzles()
elec_list = build_electrode_pairs()


def _union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


# ═══════════════════════════════════════════════════════
# EXPORTAÇÃO — 5 STEP (conforme memorial §10)
# ═══════════════════════════════════════════════════════
print("\nExportando STEP files...")

cq.exporters.export(fluid, "FIORA_IC_v5_3_fluid_domain.step")
print("  ✅ FIORA_IC_v5_3_fluid_domain.step  (cilindro + topo côncavo + 4×DN50)")

cq.exporters.export(tube, "FIORA_IC_v5_3_return_tube.step")
print("  ✅ FIORA_IC_v5_3_return_tube.step   (DN100 parede fina — BAFFLE)")

cq.exporters.export(_union(sep_list), "FIORA_IC_v5_3_separators.step")
print("  ✅ FIORA_IC_v5_3_separators.step    (8 meias-placas Λ)")

cq.exporters.export(_union(noz_list), "FIORA_IC_v5_3_nozzles.step")
print("  ✅ FIORA_IC_v5_3_nozzles.step       (6 bocais tangenciais)")

cq.exporters.export(_union(elec_list), "FIORA_IC_v5_3_electrodes.step")
print("  ✅ FIORA_IC_v5_3_electrodes.step    (2 pares A/C)")

print("\n" + "=" * 64)
print("v5.3 CONCLUÍDO — alinhada ao Memorial Descritivo v1.0")
print("=" * 64)
print("""
PRINCIPAIS MUDANÇAS vs v5.2:
  • Topo agora CÔNCAVO (cut), conforme memorial §2.2
  • DN100 isolado em return_tube.step (baffle de parede fina 4 mm)
  • Difusores REMOVIDOS (memorial §8 — só BC no STAR-CCM+)
  • Saídas DN50 todas a 0° (memorial §5.2)
  • Bocais com inclinação ASCENDENTE +7,5° (memorial §3)
  • DN100 começa em z=1,0 m (memorial §5.1)

BOUNDARY CONDITIONS (memorial §10.1):
  • 6 faces externas dos bocais       → Velocity Inlet (líquido)
  • Face topo do DN100                → Velocity Inlet (Q=350 m³/d, −Z)
  • 4 difusores (criar no STAR-CCM+)  → Mass Flow Inlet (gás)
  • 4 furos DN50                      → Pressure Outlet (P_rel=0)
  • Parede cilíndrica + topo          → No-slip Wall
  • 8 placas separadoras              → Baffle No-slip (ambos lados)
  • Parede do DN100                   → Baffle No-slip
  • 4 placas eletrodos                → No-slip Wall (sólidos inertes)

VERIFICAÇÕES NO STAR-CCM+:
  □ Importar os 5 .step
  □ Conferir topo CÔNCAVO (não convexo)
  □ Conferir que DN100 fica DENTRO do fluid_domain (não subtraído)
  □ Cada bocal mostra face externa redonda → Inlet BC
  □ Tools > Geometry Check → zero erros
""")
