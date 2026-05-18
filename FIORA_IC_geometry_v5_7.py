"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.7 — 16/Mai/2026  ★ ATUALIZAÇÕES VINÍCIUS — ÁUDIOS + CROQUIS ★

ATUALIZAÇÕES v5.7 (sobre v5.6):
  1. ✅ Saída lateral de efluente subiu para z = 14,30 m (era 14,20).
     Vinícius: "essa saída lateral aí que dá um nível dentro do reator,
     tem que ficar BEM NO TOPO MESMO".  Acima dos separadores trifásicos
     que devem ficar "mergulhados".
  2. ✅ DN50 dos separadores: agora são 3 (não 4).  Vinícius: "Não são
     quatro, são três saídas laterais [...] O separador trifásico de topo
     tem a saída dele em cima, direto, que sai direto no separador
     gás-líquido de metano".  Removido furo em z=13,87 m (separador 95%).
     O separador de topo descarrega diretamente na câmara de gás do domo.
  3. ✅ Tubo de retorno DN100 desce até z = 0,15 m do fundo (era 1,0 m).
     Vinícius: "em torno de 15 centímetros do fundo, bem coladinho ali,
     para ele já encontrar o efluente de alimentação entrando".
  4. ✅ Quantidade de separadores Λ por nível (croquis Vinícius):
        - 20% : 2 Λ
        - 40% : 4 Λ
        - 60% : 4 Λ
        - 95% : 4 Λ (saída interna, sem DN50 lateral)
     Antes era 1 Λ por nível.  Distribuição paralela ao longo de X,
     cada Λ ocupando uma faixa W_Λ = D/N do diâmetro.
  5. ✅ Λ do 95% sem saída lateral — gás capturado sobe naturalmente
     para o domo (modelagem simplificada: o tubo DN25 real é detalhe
     de tubulação externa, sem impacto no escoamento CFD interno).

Pontos confirmados sem mudança no CAD:
  • Bocais: 6× DN80, 60°, +7° asc., anti-horário, atravessam parede
  • Difusores: 12× DN250 no fundo, 6 setores × 2 (mesma config v5.6)
  • Eletrodos: 2 pares A/C, gap 30 mm face-a-face
  • Topo convexo, saída de biogás DN100 central no ápice
  • Composição gás recirc: CH₄ 65 / CO₂ 34 / H₂S 1 / H₂ traço

Confidencial — Tecnologia Patenteada FIORA IC
"""

import math
import cadquery as cq

# ═══════════════════════════════════════════════════════
# PARÂMETROS
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

# Saída lateral de efluente — ★ v5.7: subiu para z=14,30m ★
D_EFFLUENT_OUT = 0.100
Z_EFFLUENT     = 14.30                 # 3 cm abaixo do topo do cilindro (14,339)
AZ_EFFLUENT    = 180.0

# Tubo de retorno DN100 — ★ v5.7: desce até 0,15 m ★
D_RETURN_OUT  = 0.100
WALL_RETURN   = 0.004
D_RETURN_IN   = D_RETURN_OUT - 2.0 * WALL_RETURN
R_RETURN_OUT  = D_RETURN_OUT / 2.0
R_RETURN_IN   = D_RETURN_IN  / 2.0
Z_RETURN_BOT  = 0.15                   # ★ v5.7: 0,15m (era 1,0m)
Z_RETURN_TOP  = H_REACTOR - TOP_DEPTH - 0.05

# Bocais tangenciais
N_NOZZLES         = 6
NOZZLE_D          = 0.080
NOZZLE_L          = 0.300
NOZZLE_INCL_UP    = 7.0
NOZZLE_Z          = 0.250
NOZZLE_TANG_ANGLE = 80.0
NOZZLE_AZIMUTHS   = [i * 60.0 for i in range(N_NOZZLES)]

# Separadores trifásicos — ★ v5.7: 2/4/4/4 Λ por nível ★
# Formato: (% altura, inclinação placa, n_lambdas, tem_DN50_lateral, az_DN50)
SEPARATORS = [
    (0.20, 47.5, 2, True,  0.0),
    (0.40, 52.5, 4, True,  0.0),
    (0.60, 57.5, 4, True,  0.0),
    (0.95, 57.5, 4, False, None),      # ★ topo: sem DN50 lateral
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

# Composição gás (info para BC)
GAS_COMPOSITION = {"CH4": 0.65, "CO2": 0.34, "H2S": 0.01, "H2": 0.0}


# ═══════════════════════════════════════════════════════
# DOMÍNIO FLUIDO
# ═══════════════════════════════════════════════════════

def build_fluid_domain():
    """Cilindro + DOMO CONVEXO (intersect com box gigante = sem bug v5.6.1)."""
    print(f"  [1] Cilindro (H_cyl={H_CYL:.3f} m)...")
    cyl_ctr_z = -H_REACTOR/2.0 + H_CYL/2.0
    cyl = (cq.Workplane("XY").cylinder(H_CYL, R_REACTOR)
           .translate((0, 0, cyl_ctr_z)))

    print(f"  [2] Domo CONVEXO (R_sph={R_SPH_TOP:.3f} m, h={TOP_DEPTH:.3f} m)...")
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
        print(f"     joelho r_fillet={R_KNUCKLE*0.4:.3f} m aplicado")
    except Exception as e:
        print(f"     joelho ignorado ({e})")
    return fluid


def cut_top_biogas_outlet(fluid):
    """DN100 central no ápice do domo."""
    print(f"  [3] Saída de biogás DN{D_BIOGAS_OUT*1000:.0f} central no topo...")
    hole = (cq.Workplane("XY")
            .cylinder(0.30, D_BIOGAS_OUT/2.0)
            .translate((0, 0, H_REACTOR/2.0)))
    return fluid.cut(hole)


def cut_dn50_outlets(fluid):
    """3 furos DN50 (níveis 20/40/60%) — ★ v5.7: o 95% NÃO sai pela parede ★"""
    print("  [4] Furos DN50 (3× — apenas 20/40/60%, todos a 0°)...")
    for pct, _tilt, _n, has_dn50, az in SEPARATORS:
        if not has_dn50:
            print(f"     {pct*100:.0f}%: SEM DN50 lateral — saída interna p/ câmara de gás")
            continue
        z_rel = pct * H_REACTOR - H_REACTOR/2.0
        hole = (cq.Workplane("YZ")
                .circle(D_SEP_OUT/2.0)
                .extrude(0.20)
                .translate((R_REACTOR - 0.05, 0, 0))
                .rotate((0, 0, 0), (0, 0, 1), az)
                .translate((0, 0, z_rel)))
        fluid = fluid.cut(hole)
        print(f"     DN50 @ {pct*100:.0f}% z_rel={z_rel:+.2f} m  az={az:.0f}°")
    return fluid


def cut_effluent_outlet(fluid):
    """Saída de efluente DN100 — ★ v5.7: z=14,30m (bem no topo) ★"""
    print(f"  [5] Saída de efluente DN{D_EFFLUENT_OUT*1000:.0f} "
          f"@ z={Z_EFFLUENT:.2f} m  az={AZ_EFFLUENT:.0f}°...")
    z_rel = Z_EFFLUENT - H_REACTOR/2.0
    hole = (cq.Workplane("YZ")
            .circle(D_EFFLUENT_OUT/2.0)
            .extrude(0.25)
            .translate((R_REACTOR - 0.06, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), AZ_EFFLUENT)
            .translate((0, 0, z_rel)))
    return fluid.cut(hole)


# ═══════════════════════════════════════════════════════
# TUBO DE RETORNO — ★ v5.7: desce até 0,15 m ★
# ═══════════════════════════════════════════════════════

def build_return_tube():
    print(f"  [6] Tubo DN100 baffle (z=[{Z_RETURN_BOT:.2f}, {Z_RETURN_TOP:.2f}] m)...")
    H_tube = Z_RETURN_TOP - Z_RETURN_BOT
    z_ctr  = (Z_RETURN_TOP + Z_RETURN_BOT)/2.0 - H_REACTOR/2.0
    outer = cq.Workplane("XY").cylinder(H_tube, R_RETURN_OUT)
    inner = cq.Workplane("XY").cylinder(H_tube + 0.01, R_RETURN_IN)
    tube  = outer.cut(inner).translate((0, 0, z_ctr))
    return tube


# ═══════════════════════════════════════════════════════
# SEPARADORES Λ — ★ v5.7: 2/4/4/4 conjuntos por nível ★
# ═══════════════════════════════════════════════════════

def build_separators():
    """
    Cada nível tem N Λ paralelos ao longo de Y, distribuídos em X.
    Cada Λ: 2 meias-placas formando V invertido (pico no topo, abertura
    para baixo) — captura gás na região fechada superior do Λ.
    Largura de cada Λ: W_Λ = D / N.
    """
    print("  [7] Separadores Λ (★ v5.7: 2/4/4/4 conjuntos)...")

    clip_r   = R_REACTOR - 0.004
    clip_cyl = cq.Workplane("XY").cylinder(H_REACTOR * 1.2, clip_r)

    sep_list = []
    total_placas = 0

    for pct, tilt, n_lambdas, _has_dn50, _az in SEPARATORS:
        z_rel    = pct * H_REACTOR - H_REACTOR/2.0
        W_lambda = D_REACTOR / n_lambdas          # largura horizontal por Λ
        depth    = D_REACTOR * 1.6                # Y — extensão > diâmetro, será aparado
        tilt_rad = math.radians(tilt)

        print(f"     {pct*100:.0f}% (±{tilt}°): {n_lambdas} Λ × 2 placas = {2*n_lambdas} placas")

        for i in range(n_lambdas):
            # Centro de cada Λ no eixo X
            x_center_i = -R_REACTOR + W_lambda * (i + 0.5)

            # ─── Placa ESQUERDA do Λ (sobe da esquerda até o pico) ───
            # Construir como caixa centrada em (-W_lambda/4, 0, 0):
            # extremidade direita em x=0 (futuro pico), esquerda em x=-W_lambda/2.
            # Rotação +tilt em Y: lado esquerdo (x<0) desce, lado direito (x=0) fica em z=0.
            plate_L = (cq.Workplane("XY")
                       .box(W_lambda/2.0, depth, SEP_THICK)
                       .translate((-W_lambda/4.0, 0, 0))
                       .rotate((0, 0, 0), (0, 1, 0), tilt)
                       .translate((x_center_i, 0, z_rel)))

            # ─── Placa DIREITA do Λ (desce do pico para a direita) ───
            plate_R = (cq.Workplane("XY")
                       .box(W_lambda/2.0, depth, SEP_THICK)
                       .translate((W_lambda/4.0, 0, 0))
                       .rotate((0, 0, 0), (0, 1, 0), -tilt)
                       .translate((x_center_i, 0, z_rel)))

            try:
                sep_list.append(plate_L.intersect(clip_cyl))
                sep_list.append(plate_R.intersect(clip_cyl))
                total_placas += 2
            except Exception as e:
                sep_list.append(plate_L)
                sep_list.append(plate_R)
                total_placas += 2
                print(f"       ⚠ Λ_{i+1} clip falhou: {e}")

    print(f"     TOTAL: {total_placas} meias-placas (era 8 na v5.6, agora {total_placas})")
    return sep_list


# ═══════════════════════════════════════════════════════
# BOCAIS, ELETRODOS, DIFUSORES — sem mudança vs v5.6
# ═══════════════════════════════════════════════════════

def build_nozzles():
    print(f"  [8] Bocais DN80 ({N_NOZZLES}×, +{NOZZLE_INCL_UP}° asc., "
          f"α_tang={NOZZLE_TANG_ANGLE}°, anti-horário)...")
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
    print("  [9] Eletrodos — 2 pares A/C...")
    r_ext = ELEC_R_POS + ELEC_W/2.0
    r_int = ELEC_R_POS - ELEC_W/2.0
    assert r_ext < R_REACTOR
    assert r_int > R_RETURN_OUT

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
        anode = (base.rotate((0, 0, 0), (0, 0, 1), pair_angle)
                     .translate((ax, ay, ELEC_Z_CTR_REL)))

        bx = cx - (c2c/2.0) * tangent[0]
        by = cy - (c2c/2.0) * tangent[1]
        cathode = (base.rotate((0, 0, 0), (0, 0, 1), pair_angle)
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
print("FIORA IC v5.7 — Atualizações Vinícius (áudios + croquis)")
print("=" * 64)
print(f"  Reator       : D={D_REACTOR} m  H={H_REACTOR} m")
print(f"  Topo         : CONVEXO h={TOP_DEPTH:.3f} m")
print(f"  Biogás topo  : DN{D_BIOGAS_OUT*1000:.0f} central")
print(f"  Efluente lat.: DN{D_EFFLUENT_OUT*1000:.0f} @ z=14,30 m  az=180°  ★ v5.7")
print(f"  DN100 retorno: z=[{Z_RETURN_BOT:.2f}, {Z_RETURN_TOP:.2f}] m  ★ v5.7 desce até 0,15")
print(f"  Separadores  : 2/4/4/4 Λ — ★ v5.7 ({sum(2*s[2] for s in SEPARATORS)} placas)")
print(f"  DN50 laterais: 3 furos (20/40/60%) — sep. 95% sai internamente  ★ v5.7")
print(f"  Bocais       : 6× DN80, +{NOZZLE_INCL_UP}° asc, α={NOZZLE_TANG_ANGLE}°")
print(f"  Eletrodos    : 2 pares A/C, gap {ELEC_GAP_FACE*1000:.0f} mm")
print(f"  Difusores    : 12× DN{DIFF_D*1000:.0f} fundo")
print()

fluid = build_fluid_domain()
fluid = cut_top_biogas_outlet(fluid)
fluid = cut_dn50_outlets(fluid)
fluid = cut_effluent_outlet(fluid)
tube      = build_return_tube()
sep_list  = build_separators()
noz_list  = build_nozzles()
elec_list = build_electrode_pairs()
diff_list = build_diffuser_imprint_stubs()


def _union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out


# ═══════════════════════════════════════════════════════
# EXPORTAÇÃO
# ═══════════════════════════════════════════════════════
print("\nExportando STEP files...")

cq.exporters.export(fluid, "FIORA_IC_v5_7_fluid_domain.step")
print("  ✅ FIORA_IC_v5_7_fluid_domain.step")

cq.exporters.export(tube, "FIORA_IC_v5_7_return_tube.step")
print("  ✅ FIORA_IC_v5_7_return_tube.step")

cq.exporters.export(_union(sep_list), "FIORA_IC_v5_7_separators.step")
print(f"  ✅ FIORA_IC_v5_7_separators.step  ({len(sep_list)} placas)")

cq.exporters.export(_union(noz_list), "FIORA_IC_v5_7_nozzles.step")
print("  ✅ FIORA_IC_v5_7_nozzles.step")

cq.exporters.export(_union(elec_list), "FIORA_IC_v5_7_electrodes.step")
print("  ✅ FIORA_IC_v5_7_electrodes.step")

cq.exporters.export(_union(diff_list), "FIORA_IC_v5_7_diffusers.step")
print("  ✅ FIORA_IC_v5_7_diffusers.step")

print("\n" + "=" * 64)
print("v5.7 CONCLUÍDO")
print("=" * 64)
print("""
PRINCIPAIS MUDANÇAS vs v5.6:
  1. Saída efluente lateral subiu para z=14,30 m
  2. DN50 só nos níveis 20/40/60% (sep. 95% sai internamente)
  3. DN100 retorno desce até z=0,15 m
  4. Separadores: 2/4/4/4 Λ por nível (era 1/1/1/1)
  5. Total de meias-placas: 28 (era 8)

PENDENTE (informativo, não muda CAD):
  • Alimentação real entra por 1 tubo paralelo ao fundo que ramifica
    em 6 internamente. CFD continua modelando os 6 bocais individuais
    atravessando a parede (simplificação aceitável).

PRÓXIMO PASSO STAR-CCM+:
  Re-importar fluid_domain + separators (mudaram).  Refazer Unite
  com nozzles e Imprint com diffusers.
""")
