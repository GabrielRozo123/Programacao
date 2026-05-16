"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.6.1 — 16/Mai/2026  ★ FIX BUG DO DOMO ★

CORREÇÃO v5.6.1 (sobre v5.6):
  ✅ build_fluid_domain() — o cut do domo usava uma caixa de 4·R_REACTOR
     (= 4,18 m) em XY, MENOR que o diâmetro da esfera (2·R_SPH = 4,44 m).
     Resultado: a esfera EXTRAPOLAVA a caixa por 13 cm de cada lado e
     sobravam pedaços não cortados, gerando aquela "bola esférica"
     flutuante no topo do reator no STAR-CCM+.
     Fix: trocar `sphere.cut(box_abaixo)` por `sphere.intersect(box_acima)`
     com box gigante (50 m) — garante que só sobre a calota acima de
     z_top_cyl, sem resíduos.

NOTA: este script gera arquivos com o mesmo prefixo FIORA_IC_v5_6_*.step,
      sobrescrevendo os anteriores (que estavam com bug).  Após rodar,
      reimporte no STAR-CCM+ via File > Import > Import CAD Model.

★ ATUALIZAÇÃO COMPLETA — VINÍCIUS 18:04 ★

ATUALIZAÇÕES v5.6 (sobre v5.5):
  1. ✅ TOPO REVERTIDO PARA CONVEXO (domo toroesférico bulging up).
     Vinícius 18:04: "Saída centralizada no eixo vertical, no ponto
     mais alto da tampa" — só é consistente com domo convexo, não com
     calota côncava (cuja borda é o ponto mais alto).  Memorial v1.0
     estava ambíguo; agora resolvido.
  2. ✅ SAÍDA CENTRAL DE BIOGÁS — DN100 no ápice do domo (eixo Z).
  3. ✅ SAÍDA LATERAL DE EFLUENTE — DN100, z=14,50 m (10 cm abaixo da
     borda superior), independente do DN50 do separador 95%.
  4. ✅ INCLINAÇÃO DOS BOCAIS atualizada: 7,0° (não 7,5°).
  5. ✅ ÂNGULO TANGENCIAL confirmado: 80° (com cenários alternativos
     70°/75°/85° comentados como opções de sensibilidade).
  6. ✅ Sentido de rotação confirmado: ANTI-HORÁRIO visto de cima.
  7. ✅ Composição do gás recirculado documentada para uso no BC:
     CH₄ 65% / CO₂ 34% / H₂S 1% / H₂ traço.
  8. ✅ Recirculação gás = 40% Q_biogás total, uniforme nos 12 difusores.

Mantidas todas as correções estruturais das versões anteriores.

ARQUIVOS GERADOS (6 STEP):
  • FIORA_IC_v5_6_fluid_domain.step  (cilindro + domo + biogás + DN50 + efluente)
  • FIORA_IC_v5_6_return_tube.step
  • FIORA_IC_v5_6_separators.step
  • FIORA_IC_v5_6_nozzles.step
  • FIORA_IC_v5_6_electrodes.step
  • FIORA_IC_v5_6_diffusers.step
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

# §2.2 Topo CONVEXO toroesférico (Vinícius 18:04) — saída no eixo central
TOP_DEPTH   = D_REACTOR / 8.0          # 0.261 m altura do domo acima do cilindro
H_CYL       = H_REACTOR - TOP_DEPTH    # altura do corpo cilíndrico
R_KNUCKLE   = 0.10 * D_REACTOR
R_SPH_TOP   = (R_REACTOR**2 + TOP_DEPTH**2) / (2.0 * TOP_DEPTH)

# Saída central de biogás no topo (Vinícius 18:04)
D_BIOGAS_OUT  = 0.100                  # DN100

# Saída lateral de efluente próxima ao topo (Vinícius 18:04)
D_EFFLUENT_OUT = 0.100                 # DN100, independente do DN50 do sep 95%
Z_EFFLUENT     = 14.50                 # 10 cm abaixo da borda (memorial diz 10-15 cm)
AZ_EFFLUENT    = 180.0                 # azimute lateral — diametralmente oposto aos DN50

# §5 Tubo de retorno DN100 (BAFFLE — arquivo separado)
D_RETURN_OUT  = 0.100
WALL_RETURN   = 0.004
D_RETURN_IN   = D_RETURN_OUT - 2.0 * WALL_RETURN
R_RETURN_OUT  = D_RETURN_OUT / 2.0
R_RETURN_IN   = D_RETURN_IN  / 2.0
Z_RETURN_BOT  = 1.0
Z_RETURN_TOP  = H_REACTOR - TOP_DEPTH - 0.05   # termina logo abaixo da borda do domo

# §3 Bocais tangenciais (DN80, atravessam a parede)
N_NOZZLES         = 6
NOZZLE_D          = 0.080
NOZZLE_L          = 0.300
NOZZLE_INCL_UP    = 7.0                # ° ASCENDENTE  ★ ATUALIZADO de 7,5 → 7,0
NOZZLE_Z          = 0.250
NOZZLE_TANG_ANGLE = 80.0               # ° caso base — cenários: 70/75/85
NOZZLE_AZIMUTHS   = [i * 60.0 for i in range(N_NOZZLES)]
# Sentido: ANTI-HORÁRIO visto de cima (Vinícius 18:04) — +t̂ = (−sin, cos) ✓

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

# §6 Eletrodos
ELEC_H, ELEC_W, ELEC_THICK = 2.400, 0.520, 0.008
ELEC_R_POS                 = R_REACTOR * 0.65
ELEC_Z_BOT                 = 0.250
ELEC_Z_CTR_REL             = ELEC_Z_BOT + ELEC_H/2.0 - H_REACTOR/2.0
PAIR_ANGLES                = [0.0, 180.0]
ELEC_GAP_FACE              = 0.030

# §8 Difusores — 12 discos DN250 no fundo (Vinícius 16:50)
N_DIFF             = 12
DIFF_D             = 0.250
DIFF_THICK         = 0.050
DIFF_SECTOR_AZ     = [30.0, 90.0, 150.0, 210.0, 270.0, 330.0]
DIFF_R_INNER       = 0.35
DIFF_R_OUTER       = 0.80
DIFF_Q_UNIT_MIN    = 2.0      # Nm³/h por difusor
DIFF_Q_UNIT_MAX    = 4.0
DIFF_BUBBLE_MM     = (1.0, 3.0)
DIFF_BLOWER_P_KGF  = 2.0

# Composição do gás recirculado (Vinícius 18:04) — info para BC
GAS_COMPOSITION = {"CH4": 0.65, "CO2": 0.34, "H2S": 0.01, "H2": 0.0}


# ═══════════════════════════════════════════════════════
# DOMÍNIO FLUIDO — cilindro + DOMO CONVEXO + furos
# ═══════════════════════════════════════════════════════

def build_fluid_domain():
    """Cilindro de altura H_CYL + calota CONVEXA toroesférica por cima."""
    print(f"  [1] Cilindro (H_cyl={H_CYL:.3f} m)...")
    cyl_ctr_z = -H_REACTOR/2.0 + H_CYL/2.0
    cyl = (cq.Workplane("XY")
           .cylinder(H_CYL, R_REACTOR)
           .translate((0, 0, cyl_ctr_z)))

    print(f"  [2] Domo CONVEXO (R_sph={R_SPH_TOP:.3f} m, h={TOP_DEPTH:.3f} m)...")
    z_top_cyl = H_REACTOR/2.0 - TOP_DEPTH
    z_c       = z_top_cyl + TOP_DEPTH - R_SPH_TOP    # centro da esfera ABAIXO do topo
    sphere    = cq.Workplane("XY").sphere(R_SPH_TOP).translate((0, 0, z_c))
    # ★ FIX v5.6.1: usar caixa MUITO maior em XY que a esfera (R_SPH > R_REACTOR!)
    # e fazer INTERSECT com meio-espaço acima de z_top_cyl em vez de cut abaixo.
    # Assim garantimos que só sobra a calota acima do topo do cilindro.
    BIG = 50.0
    keep_above = (cq.Workplane("XY").box(BIG, BIG, BIG)
                  .translate((0, 0, z_top_cyl + BIG/2.0)))
    cap = sphere.intersect(keep_above)
    fluid = cyl.union(cap)

    # Joelho ASME (fillet na junção cilindro/calota)
    try:
        fluid = (fluid.edges(cq.selectors.NearestToPointSelector(
                    (R_REACTOR, 0, z_top_cyl)))
                 .fillet(R_KNUCKLE * 0.4))
        print(f"     joelho r_fillet={R_KNUCKLE*0.4:.3f} m aplicado")
    except Exception as e:
        print(f"     joelho ignorado ({e})")

    return fluid


def cut_top_biogas_outlet(fluid):
    """Furo DN100 central no ápice do domo (Vinícius 18:04)."""
    print(f"  [3] Saída de biogás DN{D_BIOGAS_OUT*1000:.0f} central no topo...")
    # Cilindro vertical descendo do topo, atravessando o domo
    hole = (cq.Workplane("XY")
            .cylinder(0.30, D_BIOGAS_OUT/2.0)
            .translate((0, 0, H_REACTOR/2.0)))
    return fluid.cut(hole)


def cut_dn50_outlets(fluid):
    """4 furos DN50 (separadores), todos a 0°."""
    print("  [4] Furos DN50 dos separadores (4×, todos a 0°)...")
    for pct, _tilt, az in SEPARATORS:
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
    """Saída lateral de efluente DN100 (Vinícius 18:04)."""
    print(f"  [5] Saída de efluente lateral DN{D_EFFLUENT_OUT*1000:.0f} "
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
# TUBO DE RETORNO DN100 — BAFFLE
# ═══════════════════════════════════════════════════════

def build_return_tube():
    print(f"  [6] Tubo DN100 parede fina ({WALL_RETURN*1000:.0f} mm)...")
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
    print("  [7] Separadores (8 placas)...")
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
            print(f"     {pct*100:.0f}%: ±{tilt}° clip falhou ({e})")
    return sep_list


# ═══════════════════════════════════════════════════════
# BOCAIS — atravessam a parede, inclinação 7° (Vinícius 18:04)
# ═══════════════════════════════════════════════════════

def build_nozzles():
    print(f"  [8] Bocais DN80 ({N_NOZZLES}×, +{NOZZLE_INCL_UP}° ASCENDENTE, "
          f"α_tang={NOZZLE_TANG_ANGLE}°)...")
    print(f"     Sentido: ANTI-HORÁRIO visto de cima  |  Cenários: 70/75/85°")
    noz_list = []
    tang_rad = math.radians(NOZZLE_TANG_ANGLE)
    incl_rad = math.radians(NOZZLE_INCL_UP)

    for az_deg in NOZZLE_AZIMUTHS:
        a     = math.radians(az_deg)
        r_hat = (math.cos(a),  math.sin(a))
        t_hat = (-math.sin(a), math.cos(a))           # anti-horário ✓

        dx = -math.cos(tang_rad) * r_hat[0] + math.sin(tang_rad) * t_hat[0]
        dy = -math.cos(tang_rad) * r_hat[1] + math.sin(tang_rad) * t_hat[1]
        dz = +math.tan(incl_rad)                       # ascendente
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
    print("  [9] Eletrodos — 2 pares A/C...")
    r_ext = ELEC_R_POS + ELEC_W/2.0
    r_int = ELEC_R_POS - ELEC_W/2.0
    assert r_ext < R_REACTOR
    assert r_int > R_RETURN_OUT
    print(f"     r_int={r_int:.3f}  r_ext={r_ext:.3f}  folga parede={R_REACTOR - r_ext:.3f}")

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
        anode = (base.rotate((0,0,0),(0,0,1), pair_angle)
                     .translate((ax, ay, ELEC_Z_CTR_REL)))

        bx = cx - (c2c/2.0) * tangent[0]
        by = cy - (c2c/2.0) * tangent[1]
        cathode = (base.rotate((0,0,0),(0,0,1), pair_angle)
                       .translate((bx, by, ELEC_Z_CTR_REL)))

        plates.extend([anode, cathode])
        print(f"     par {i+1} @ {pair_angle:.0f}°  c2c={c2c*1000:.1f} mm")
    return plates


# ═══════════════════════════════════════════════════════
# DIFUSORES — 12 discos DN250 no fundo
# ═══════════════════════════════════════════════════════

def build_diffuser_imprint_stubs():
    print(f"  [10] Difusores ({N_DIFF}× discos DN{DIFF_D*1000:.0f} no fundo)...")
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
            zona = "INT" if r == DIFF_R_INNER else "EXT"
            print(f"     setor {sector_az:>5.1f}°  {zona} r={r:.2f} m")
    return stubs


# ═══════════════════════════════════════════════════════
# MONTAGEM
# ═══════════════════════════════════════════════════════

print("=" * 64)
print("FIORA IC v5.6 — Memorial v1.0 + Atualizações Vinícius 16/05 18:04")
print("=" * 64)
print(f"  Reator       : D={D_REACTOR} m  H={H_REACTOR} m")
print(f"  Topo         : CONVEXO h={TOP_DEPTH:.3f} m  R_sph={R_SPH_TOP:.3f} m")
print(f"  Biogás (topo): DN{D_BIOGAS_OUT*1000:.0f} central no ápice")
print(f"  Efluente lat.: DN{D_EFFLUENT_OUT*1000:.0f} @ z={Z_EFFLUENT:.2f} m  "
      f"az={AZ_EFFLUENT:.0f}°")
print(f"  DN100 retorno: BAFFLE Ø{D_RETURN_OUT*1000:.0f} mm  "
      f"esp {WALL_RETURN*1000:.0f} mm")
print(f"  Separadores  : {len(SEPARATORS)} níveis — DN50 todas a 0°")
print(f"  Bocais       : {N_NOZZLES}× DN80, ANTI-HORÁRIO, "
      f"α_tang={NOZZLE_TANG_ANGLE}° + {NOZZLE_INCL_UP}° ascendente")
print(f"  Eletrodos    : {len(PAIR_ANGLES)} pares A/C, gap "
      f"{ELEC_GAP_FACE*1000:.0f} mm face-a-face")
print(f"  Difusores    : {N_DIFF}× DN{DIFF_D*1000:.0f} no fundo")
print(f"  Gás recirc.  : CH4 {GAS_COMPOSITION['CH4']*100:.0f}% / "
      f"CO2 {GAS_COMPOSITION['CO2']*100:.0f}% / "
      f"H2S {GAS_COMPOSITION['H2S']*100:.0f}% / H2 traço")
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
# EXPORTAÇÃO — 6 STEP
# ═══════════════════════════════════════════════════════
print("\nExportando STEP files...")

cq.exporters.export(fluid, "FIORA_IC_v5_6_fluid_domain.step")
print("  ✅ FIORA_IC_v5_6_fluid_domain.step  (cilindro+domo+biogás+DN50+efluente)")

cq.exporters.export(tube, "FIORA_IC_v5_6_return_tube.step")
print("  ✅ FIORA_IC_v5_6_return_tube.step   (DN100 baffle parede fina)")

cq.exporters.export(_union(sep_list), "FIORA_IC_v5_6_separators.step")
print("  ✅ FIORA_IC_v5_6_separators.step    (8 meias-placas Λ)")

cq.exporters.export(_union(noz_list), "FIORA_IC_v5_6_nozzles.step")
print("  ✅ FIORA_IC_v5_6_nozzles.step       (6 bocais 80°+7°)")

cq.exporters.export(_union(elec_list), "FIORA_IC_v5_6_electrodes.step")
print("  ✅ FIORA_IC_v5_6_electrodes.step    (2 pares A/C)")

cq.exporters.export(_union(diff_list), "FIORA_IC_v5_6_diffusers.step")
print(f"  ✅ FIORA_IC_v5_6_diffusers.step     ({N_DIFF} discos DN250)")

print("\n" + "=" * 64)
print("v5.6 CONCLUÍDO")
print("=" * 64)
print(f"""
NOVOS BOUNDARIES NO STAR-CCM+ (vs v5.5):
  + Face do topo do domo (anel ao redor do furo)  → Wall_Top
  + Face circular central no topo (Ø{D_BIOGAS_OUT*1000:.0f} mm)         → Outlet_Biogas (Pressure Outlet)
  + Face lateral DN100 em z=14,50 m                → Outlet_Effluent (Pressure Outlet)

MASS FLOW INLET DOS DIFUSORES — composição do gás:
  • CH₄ : 65%     ρ ≈ 0.668 kg/Nm³
  • CO₂ : 34%     ρ ≈ 1.842 kg/Nm³
  • H₂S :  1%     ρ ≈ 1.434 kg/Nm³
  • H₂  :  traço
  ρ_mistura ≈ 0,65×0,668 + 0,34×1,842 + 0,01×1,434 ≈ 1.075 kg/Nm³
  Vazão total = 0,40 × Q_biogás_total (variável de resposta da simulação)

CENÁRIOS DE SENSIBILIDADE (Vinícius):
  Trocar NOZZLE_TANG_ANGLE no topo do script:
    80° = caso base (atual)
    75° = sensibilidade 1
    70° = sensibilidade 2 (mais radial)
    85° = sensibilidade 3 (mais tangencial)
""")
