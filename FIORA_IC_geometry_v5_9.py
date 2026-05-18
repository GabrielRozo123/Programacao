"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.9 — 16/Mai/2026  ★ FIX BUG: SEPARADORES Λ (PICO PARA CIMA) ★

CORREÇÃO v5.9 (sobre v5.8):
  ✅ Os sinais dos tilts das placas estavam INVERTIDOS desde a v5.7,
     gerando separadores em V (abertura para cima) em vez de Λ
     (pico para cima).  Isso seria desastroso: o gás escaparia em
     vez de ficar capturado no triângulo superior do Λ.

     Causa: a matriz de rotação em torno de +Y (regra da mão direita)
     leva o lado +X para BAIXO com θ>0, não para cima.  Eu havia
     assumido o oposto.  Sinais corrigidos:
       • Placa esquerda: −tilt  (era +tilt)
       • Placa direita : +tilt  (era −tilt)
     Agora as placas formam Λ corretamente (pico no centro, abertura
     para baixo) — captura gás na câmara superior interna do Λ.

Demais features mantidas da v5.8:
  ✅ Manifold de 4 ramais DN50 no retorno DN100
  ✅ Separadores 2/4/4/4 Λ por nível
  ✅ Bocais, eletrodos, difusores, topo, saídas — todos sem mudança
"""

import math
import cadquery as cq

# ═══════════════════════════════════════════════════════
# PARÂMETROS (idênticos à v5.8 — só inverteu sinal dos tilts dos Λ)
# ═══════════════════════════════════════════════════════

D_REACTOR   = 2.090
H_REACTOR   = 14.600
R_REACTOR   = D_REACTOR / 2.0

# Topo CONVEXO toroesférico
TOP_DEPTH   = D_REACTOR / 8.0
H_CYL       = H_REACTOR - TOP_DEPTH
R_KNUCKLE   = 0.10 * D_REACTOR
R_SPH_TOP   = (R_REACTOR**2 + TOP_DEPTH**2) / (2.0 * TOP_DEPTH)

# Saída central de biogás
D_BIOGAS_OUT  = 0.100

# Saída lateral de efluente
D_EFFLUENT_OUT = 0.100
Z_EFFLUENT     = 14.30
AZ_EFFLUENT    = 180.0

# Tubo de retorno DN100 + manifold de 4 ramais  ★ v5.9 ★
D_RETURN_OUT  = 0.100
WALL_RETURN   = 0.004
D_RETURN_IN   = D_RETURN_OUT - 2.0 * WALL_RETURN
R_RETURN_OUT  = D_RETURN_OUT / 2.0
R_RETURN_IN   = D_RETURN_IN  / 2.0
Z_MANIFOLD    = 0.40                   # cota do manifold (onde saem os 4 ramais)
Z_RETURN_TOP  = H_REACTOR - TOP_DEPTH - 0.05

# Ramais DN50 (4× horizontais no manifold)  ★ v5.9 ★
D_BRANCH      = 0.050                   # DN50
WALL_BRANCH   = WALL_RETURN
R_BRANCH_OUT  = D_BRANCH / 2.0
R_BRANCH_IN   = R_BRANCH_OUT - WALL_BRANCH
L_BRANCH      = 0.70                    # comprimento de cada ramal
BRANCH_AZIMUTHS = [45.0, 135.0, 225.0, 315.0]

# Bocais tangenciais
N_NOZZLES         = 6
NOZZLE_D          = 0.080
NOZZLE_L          = 0.300
NOZZLE_INCL_UP    = 7.0
NOZZLE_Z          = 0.250
NOZZLE_TANG_ANGLE = 80.0
NOZZLE_AZIMUTHS   = [i * 60.0 for i in range(N_NOZZLES)]

# Separadores trifásicos — 2/4/4/4 Λ por nível
SEPARATORS = [
    (0.20, 47.5, 2, True,  0.0),
    (0.40, 52.5, 4, True,  0.0),
    (0.60, 57.5, 4, True,  0.0),
    (0.95, 57.5, 4, False, None),
]
SEP_THICK   = 0.008
D_SEP_OUT   = 0.050

# Eletrodos
ELEC_H, ELEC_W, ELEC_THICK = 2.400, 0.520, 0.008
ELEC_R_POS                 = R_REACTOR * 0.65
ELEC_Z_BOT                 = 0.250
ELEC_Z_CTR_REL             = ELEC_Z_BOT + ELEC_H/2.0 - H_REACTOR/2.0
PAIR_ANGLES                = [0.0, 180.0]
ELEC_GAP_FACE              = 0.030

# Difusores
N_DIFF             = 12
DIFF_D             = 0.250
DIFF_THICK         = 0.050
DIFF_SECTOR_AZ     = [30.0, 90.0, 150.0, 210.0, 270.0, 330.0]
DIFF_R_INNER       = 0.35
DIFF_R_OUTER       = 0.80

GAS_COMPOSITION = {"CH4": 0.65, "CO2": 0.34, "H2S": 0.01, "H2": 0.0}


# ═══════════════════════════════════════════════════════
# DOMÍNIO FLUIDO
# ═══════════════════════════════════════════════════════

def build_fluid_domain():
    print(f"  [1] Cilindro (H_cyl={H_CYL:.3f} m)...")
    cyl_ctr_z = -H_REACTOR/2.0 + H_CYL/2.0
    cyl = (cq.Workplane("XY").cylinder(H_CYL, R_REACTOR)
           .translate((0, 0, cyl_ctr_z)))

    print(f"  [2] Domo CONVEXO (R_sph={R_SPH_TOP:.3f} m)...")
    z_top_cyl = H_REACTOR/2.0 - TOP_DEPTH
    z_c       = z_top_cyl + TOP_DEPTH - R_SPH_TOP
    sphere    = cq.Workplane("XY").sphere(R_SPH_TOP).translate((0, 0, z_c))
    BIG = 50.0
    keep_above = (cq.Workplane("XY").box(BIG, BIG, BIG)
                  .translate((0, 0, z_top_cyl + BIG/2.0)))
    cap = sphere.intersect(keep_above)
    fluid = cyl.union(cap)
    try:
        fluid = (fluid.edges(cq.selectors.NearestToPointSelector(
                    (R_REACTOR, 0, z_top_cyl)))
                 .fillet(R_KNUCKLE * 0.4))
    except Exception:
        pass
    return fluid


def cut_top_biogas_outlet(fluid):
    print(f"  [3] Saída biogás DN{D_BIOGAS_OUT*1000:.0f} central topo...")
    hole = (cq.Workplane("XY")
            .cylinder(0.30, D_BIOGAS_OUT/2.0)
            .translate((0, 0, H_REACTOR/2.0)))
    return fluid.cut(hole)


def cut_dn50_outlets(fluid):
    print("  [4] Furos DN50 (3× — 20/40/60%)...")
    for pct, _tilt, _n, has_dn50, az in SEPARATORS:
        if not has_dn50:
            continue
        z_rel = pct * H_REACTOR - H_REACTOR/2.0
        hole = (cq.Workplane("YZ")
                .circle(D_SEP_OUT/2.0)
                .extrude(0.20)
                .translate((R_REACTOR - 0.05, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), az)
                .translate((0, 0, z_rel)))
        fluid = fluid.cut(hole)
    return fluid


def cut_effluent_outlet(fluid):
    print(f"  [5] Saída efluente DN100 @ z={Z_EFFLUENT:.2f} m...")
    z_rel = Z_EFFLUENT - H_REACTOR/2.0
    hole = (cq.Workplane("YZ")
            .circle(D_EFFLUENT_OUT/2.0)
            .extrude(0.25)
            .translate((R_REACTOR - 0.06, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), AZ_EFFLUENT)
            .translate((0, 0, z_rel)))
    return fluid.cut(hole)


# ═══════════════════════════════════════════════════════
# TUBO DE RETORNO + MANIFOLD DE 4 RAMAIS  ★ v5.9 ★
# ═══════════════════════════════════════════════════════

def _make_horizontal_branch(az_deg):
    """
    Cria um ramal DN50 horizontal saindo do centro do reator a
    z = Z_MANIFOLD, comprimento L_BRANCH na direção azimutal az_deg.
    Parede fina (R_BRANCH_OUT − R_BRANCH_IN).
    """
    # Tubo oco inicialmente vertical (eixo Z)
    outer_v = cq.Workplane("XY").cylinder(L_BRANCH, R_BRANCH_OUT)
    inner_v = cq.Workplane("XY").cylinder(L_BRANCH + 0.02, R_BRANCH_IN)
    tube_v  = outer_v.cut(inner_v)

    # Rotaciona para ficar horizontal (eixo X), centrado na origem
    tube_h = tube_v.rotate((0, 0, 0), (0, 1, 0), 90)
    # Translata em +X para começar em x=0 e estender até x=L_BRANCH
    tube_h = tube_h.translate((L_BRANCH/2.0, 0, 0))
    # Rotaciona em torno de Z pelo azimute
    tube_h = tube_h.rotate((0, 0, 0), (0, 0, 1), az_deg)
    # Translata verticalmente para a cota do manifold (frame centrado)
    z_man_rel = Z_MANIFOLD - H_REACTOR/2.0
    tube_h = tube_h.translate((0, 0, z_man_rel))
    return tube_h


def build_return_tube_with_manifold():
    """
    Tubo principal DN100 + manifold de 4 ramais DN50.
    Modelado como sólido único (parede fina) para virar baffle no STAR-CCM+.
    """
    print(f"  [6] Tubo retorno DN100 + 4 ramais DN50  ★ v5.9 ★")
    print(f"      Principal: z=[{Z_MANIFOLD:.2f}, {Z_RETURN_TOP:.2f}] m  "
          f"(Δz={Z_RETURN_TOP-Z_MANIFOLD:.2f} m)")
    print(f"      Manifold @ z={Z_MANIFOLD:.2f} m  → 4× DN{D_BRANCH*1000:.0f} "
          f"em az={BRANCH_AZIMUTHS}°  (L={L_BRANCH:.2f} m cada)")

    # Tubo principal vertical
    H_main      = Z_RETURN_TOP - Z_MANIFOLD
    z_main_ctr  = (Z_RETURN_TOP + Z_MANIFOLD)/2.0 - H_REACTOR/2.0
    outer_main = cq.Workplane("XY").cylinder(H_main, R_RETURN_OUT)
    inner_main = cq.Workplane("XY").cylinder(H_main + 0.02, R_RETURN_IN)
    main = outer_main.cut(inner_main).translate((0, 0, z_main_ctr))

    # 4 ramais DN50
    result = main
    for az in BRANCH_AZIMUTHS:
        branch = _make_horizontal_branch(az)
        result = result.union(branch)
        print(f"        ramal @ az={az:.0f}°  termina em "
              f"({L_BRANCH*math.cos(math.radians(az)):+.2f}, "
              f"{L_BRANCH*math.sin(math.radians(az)):+.2f}) m")

    return result


# ═══════════════════════════════════════════════════════
# SEPARADORES Λ (2/4/4/4)
# ═══════════════════════════════════════════════════════

def build_separators():
    print("  [7] Separadores Λ (2/4/4/4 conjuntos)...")
    clip_r   = R_REACTOR - 0.004
    clip_cyl = cq.Workplane("XY").cylinder(H_REACTOR * 1.2, clip_r)
    sep_list = []
    total_placas = 0
    for pct, tilt, n_lambdas, _has_dn50, _az in SEPARATORS:
        z_rel    = pct * H_REACTOR - H_REACTOR/2.0
        W_lambda = D_REACTOR / n_lambdas
        depth    = D_REACTOR * 1.6
        for i in range(n_lambdas):
            x_center_i = -R_REACTOR + W_lambda * (i + 0.5)
            plate_L = (cq.Workplane("XY")
                       .box(W_lambda/2.0, depth, SEP_THICK)
                       .translate((-W_lambda/4.0, 0, 0))
                       .rotate((0, 0, 0), (0, 1, 0), -tilt)
                       .translate((x_center_i, 0, z_rel)))
            plate_R = (cq.Workplane("XY")
                       .box(W_lambda/2.0, depth, SEP_THICK)
                       .translate((W_lambda/4.0, 0, 0))
                       .rotate((0, 0, 0), (0, 1, 0), +tilt)
                       .translate((x_center_i, 0, z_rel)))
            try:
                sep_list.append(plate_L.intersect(clip_cyl))
                sep_list.append(plate_R.intersect(clip_cyl))
                total_placas += 2
            except Exception:
                sep_list.append(plate_L)
                sep_list.append(plate_R)
                total_placas += 2
    print(f"      Total: {total_placas} meias-placas")
    return sep_list


# ═══════════════════════════════════════════════════════
# BOCAIS / ELETRODOS / DIFUSORES
# ═══════════════════════════════════════════════════════

def build_nozzles():
    print(f"  [8] Bocais DN80 ({N_NOZZLES}×)...")
    noz_list = []
    tang_rad = math.radians(NOZZLE_TANG_ANGLE)
    incl_rad = math.radians(NOZZLE_INCL_UP)
    for az_deg in NOZZLE_AZIMUTHS:
        a     = math.radians(az_deg)
        r_hat = (math.cos(a),  math.sin(a))
        t_hat = (-math.sin(a), math.cos(a))
        dx = -math.cos(tang_rad)*r_hat[0] + math.sin(tang_rad)*t_hat[0]
        dy = -math.cos(tang_rad)*r_hat[1] + math.sin(tang_rad)*t_hat[1]
        dz = +math.tan(incl_rad)
        mag = math.sqrt(dx*dx + dy*dy + dz*dz)
        dx /= mag; dy /= mag; dz /= mag
        cx = R_REACTOR * r_hat[0]
        cy = R_REACTOR * r_hat[1]
        cz = NOZZLE_Z - H_REACTOR/2.0
        noz = cq.Workplane("XY").cylinder(NOZZLE_L, NOZZLE_D/2.0)
        ang_rot = math.degrees(math.acos(max(-1.0, min(1.0, dz))))
        if ang_rot > 1e-3:
            ax_x, ax_y = -dy, dx
            noz = noz.rotate((0, 0, 0), (ax_x, ax_y, 0.0), ang_rot)
        noz_list.append(noz.translate((cx, cy, cz)))
    return noz_list


def build_electrode_pairs():
    print("  [9] Eletrodos (2 pares A/C)...")
    c2c = ELEC_GAP_FACE + ELEC_THICK
    plates = []
    for pair_angle in PAIR_ANGLES:
        a       = math.radians(pair_angle)
        radial  = ( math.cos(a),  math.sin(a))
        tangent = (-math.sin(a),  math.cos(a))
        cx = ELEC_R_POS * radial[0]
        cy = ELEC_R_POS * radial[1]
        base = cq.Workplane("XY").box(ELEC_W, ELEC_THICK, ELEC_H)
        ax = cx + (c2c/2.0) * tangent[0]
        ay = cy + (c2c/2.0) * tangent[1]
        anode = (base.rotate((0,0,0),(0,0,1), pair_angle)
                     .translate((ax, ay, ELEC_Z_CTR_REL)))
        bx = cx - (c2c/2.0) * tangent[0]
        by = cy - (c2c/2.0) * tangent[1]
        cathode = (base.rotate((0,0,0),(0,0,1), pair_angle)
                       .translate((bx, by, ELEC_Z_CTR_REL)))
        plates.extend([anode, cathode])
    return plates


def build_diffuser_imprint_stubs():
    print(f"  [10] Difusores (12× DN{DIFF_D*1000:.0f} no fundo)...")
    z_ctr_fundo = -H_REACTOR/2.0
    stubs = []
    for sector_az in DIFF_SECTOR_AZ:
        for r in (DIFF_R_INNER, DIFF_R_OUTER):
            a = math.radians(sector_az)
            cx = r * math.cos(a)
            cy = r * math.sin(a)
            disc = (cq.Workplane("XY")
                    .cylinder(DIFF_THICK, DIFF_D/2.0)
                    .translate((cx, cy, z_ctr_fundo)))
            stubs.append(disc)
    return stubs


# ═══════════════════════════════════════════════════════
# MONTAGEM
# ═══════════════════════════════════════════════════════

print("=" * 64)
print("FIORA IC v5.9 — Manifold de 4 ramais no retorno DN100")
print("=" * 64)
print(f"  Reator       : D={D_REACTOR} m  H={H_REACTOR} m")
print(f"  Retorno DN100: principal z=[{Z_MANIFOLD:.2f},{Z_RETURN_TOP:.2f}] + "
      f"manifold com 4×DN{D_BRANCH*1000:.0f} a z={Z_MANIFOLD:.2f}")
print(f"  Ramais       : az=45/135/225/315°  L={L_BRANCH:.2f} m  "
      f"(entre bocais, fora dos eletrodos)")
print()

fluid = build_fluid_domain()
fluid = cut_top_biogas_outlet(fluid)
fluid = cut_dn50_outlets(fluid)
fluid = cut_effluent_outlet(fluid)
tube      = build_return_tube_with_manifold()
sep_list  = build_separators()
noz_list  = build_nozzles()
elec_list = build_electrode_pairs()
diff_list = build_diffuser_imprint_stubs()


def _union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


print("\nExportando STEP files...")
cq.exporters.export(fluid, "FIORA_IC_v5_9_fluid_domain.step")
print("  ✅ FIORA_IC_v5_9_fluid_domain.step")
cq.exporters.export(tube, "FIORA_IC_v5_9_return_tube.step")
print("  ✅ FIORA_IC_v5_9_return_tube.step  (★ tubo + 4 ramais)")
cq.exporters.export(_union(sep_list), "FIORA_IC_v5_9_separators.step")
print("  ✅ FIORA_IC_v5_9_separators.step")
cq.exporters.export(_union(noz_list), "FIORA_IC_v5_9_nozzles.step")
print("  ✅ FIORA_IC_v5_9_nozzles.step")
cq.exporters.export(_union(elec_list), "FIORA_IC_v5_9_electrodes.step")
print("  ✅ FIORA_IC_v5_9_electrodes.step")
cq.exporters.export(_union(diff_list), "FIORA_IC_v5_9_diffusers.step")
print("  ✅ FIORA_IC_v5_9_diffusers.step")

print("\n" + "=" * 64)
print("v5.9 CONCLUÍDO — Manifold de 4 ramais implementado")
print("=" * 64)
print(f"""
MUDANÇA v5.9 vs v5.7:
  Antes (v5.7): tubo DN100 vertical único de z=14,29 → 0,15 m
  Agora (v5.9): tubo DN100 vertical de z=14,29 → 0,40 m + manifold
                com 4 ramais DN{D_BRANCH*1000:.0f} horizontais saindo
                em az=45/135/225/315° (L={L_BRANCH:.2f} m cada)

DECISÕES TÉCNICAS A CONFIRMAR COM VINÍCIUS:
  • Cota do manifold (adotei 0,40 m — pode ser mais baixo?)
  • Diâmetro dos ramais (adotei DN50 conservando área hidráulica)
  • Azimutes (45/135/225/315° — entre bocais, sem conflito com eletrodos)
  • Comprimento (0,70 m — vai até r=0,7m, folga 35cm da parede)

BC NO STAR-CCM+:
  Apenas a face superior do tubo principal continua sendo Inlet
  (Q=350 m³/d, dir −Z). Os 4 ramais são INTERIORES — descarregam
  livremente no domínio. Toda a estrutura é um único baffle no_slip.
""")
