"""
FIORA IC — Geometria CFD | STAR-CCM+
=====================================
Versão 5.2 — 16/Mai/2026   ★ CORREÇÕES SOBRE v5.1 ★

CORREÇÕES v5.2 (sobre v5.1):
  1. ✅ BOCAIS tangenciais: agora ATRAVESSAM a parede (50% fora / 50% dentro).
     Eixo definido por TANG_ANGLE_FROM_RADIAL → componente radial real
     garante penetração na casca. Antes os bocais ficavam totalmente fora.
  2. ✅ TOPO toroesférico: domo CONVEXO POR CIMA (união cilindro + calota),
     não mais cavidade invertida. R_sph derivado da fórmula correta para
     calota de altura TOP_DEPTH e base R_REACTOR.
  3. ✅ DIFUSORES: implementados (build_diffusers). Estavam declarados
     em parâmetros mas a função não existia.
  4. ✅ SAÍDAS DN50: distribuídas azimutalmente (não mais todas em +X).
     Cada separador ganhou um ângulo de saída independente.
  5. ✅ GAP eletrodos: parametrização explícita FACE-A-FACE
     (ELEC_GAP_FACE). C2C calculado = gap + espessura. Confirmar com
     Vinícius se a especificação é face-a-face ou centro-a-centro.
  6. ✅ Export via cq.exporters.export (idiomático).
  7. ✅ Fillet do joelho refeito (seletor `>Z` válido em vez de `>Z and |Z`).

INSTALAÇÃO: pip install cadquery
EXECUÇÃO:   python3 FIORA_IC_geometry_v5_2.py

Confidencial — Tecnologia Patenteada FIORA IC
"""

import math
import cadquery as cq

# ═══════════════════════════════════════════════════════
# PARÂMETROS — confirmados Vinícius 15/05/2026
# ═══════════════════════════════════════════════════════

D_REACTOR   = 2.090
H_REACTOR   = 14.600
R_REACTOR   = D_REACTOR / 2.0

# Topo toroesférico (altura = D/8)
TOP_DEPTH   = D_REACTOR / 8.0          # 0.261 m — altura do domo
R_KNUCKLE   = 0.10 * D_REACTOR         # 0.209 m — joelho (fillet)
# Raio da esfera derivado da geometria da calota:
#   R_sph² = R_base² + (R_sph − h)²  →  R_sph = (R² + h²) / (2h)
R_CROWN_REAL = (R_REACTOR**2 + TOP_DEPTH**2) / (2.0 * TOP_DEPTH)  # ≈ 2.22 m

# Tubo de retorno DN100 central
D_RETURN    = 0.100
R_RETURN    = D_RETURN / 2.0
H_RETURN    = H_REACTOR * 0.93

# Bocais tangenciais
N_NOZZLES               = 6
NOZZLE_D                = 0.080
NOZZLE_L                = 0.300
NOZZLE_INCL             = 7.5     # ° abaixo da horizontal (swirl descendente)
NOZZLE_Z                = 0.250   # altura do plano dos bocais
# Ângulo do EIXO do bocal em relação à direção RADIAL no plano XY.
#   0°  = bocal puramente radial
#   90° = bocal puramente tangente (não atravessa a parede ✗)
#   80° = quase-tangencial, com componente radial suficiente para
#         atravessar a parede em ~NOZZLE_L·cos(80°) ≈ 52 mm.
NOZZLE_TANG_ANGLE       = 80.0

# Separadores trifásicos — (% altura, inclinação placa, azimute saída DN50)
SEPARATORS = [
    (0.20, 47.5,   0.0),
    (0.40, 52.5,  90.0),
    (0.60, 57.5, 180.0),
    (0.95, 57.5, 270.0),
]
SEP_THICK   = 0.008
SEP_GAP_R   = R_RETURN + 0.025         # raio do gap central
D_SEP_OUT   = 0.050                    # DN50 saídas

# Eletrodos — 2 pares A/C
ELEC_H          = 2.400
ELEC_W          = 0.520
ELEC_THICK      = 0.008
ELEC_R_POS      = R_REACTOR * 0.65
ELEC_Z_BOT      = 0.250
ELEC_Z_CTR      = ELEC_Z_BOT + ELEC_H/2.0 - H_REACTOR/2.0
PAIR_ANGLES     = [0.0, 180.0]
# Gap FACE-A-FACE (eletroquímica). Centro-a-centro = ELEC_GAP_FACE + ELEC_THICK.
# ★ Confirmar com Vinícius se a especificação 30 mm é face-a-face (default) ou c2c.
ELEC_GAP_FACE   = 0.030

# Difusores de fundo (alimentação de gás)
N_DIFF      = 4
DIFF_D      = 0.060
DIFF_L      = 0.060            # comprimento (atravessa o fundo)
DIFF_R_POS  = R_REACTOR * 0.55 # raio de implantação (entre eletrodos e parede)
DIFF_Z      = H_REACTOR * 0.04 # logo acima do fundo
DIFF_TILT   = 7.5              # ° de inclinação (5–10° conforme croqui)

# ═══════════════════════════════════════════════════════
# DOMÍNIO FLUIDO
# ═══════════════════════════════════════════════════════

def build_fluid_domain():
    """
    Domínio fluido = cilindro (altura H − TOP_DEPTH) + calota esférica no topo.
    Construção por UNIÃO (domo convexo p/ cima), não por subtração.
    Origem do mundo: centro geométrico do reator total (z ∈ [−H/2, +H/2]).
    """
    print("  [1] Cilindro base + calota toroesférica (união)...")

    H_cyl = H_REACTOR - TOP_DEPTH
    # Cilindro encostado no fundo do reator; topo do cilindro em z_top_cyl.
    cyl_center_z = -H_REACTOR/2.0 + H_cyl/2.0
    z_top_cyl    = cyl_center_z + H_cyl/2.0
    cyl = cq.Workplane("XY").cylinder(H_cyl, R_REACTOR).translate((0, 0, cyl_center_z))

    # Esfera centrada de modo que a calota acima de z_top_cyl tenha altura TOP_DEPTH.
    # Para uma esfera de raio R_CROWN_REAL com centro em (0,0, z_top_cyl − (R−h))
    # o topo (z_top_cyl − (R−h) + R) = z_top_cyl + h = z_top_cyl + TOP_DEPTH ✓
    sph_center_z = z_top_cyl - (R_CROWN_REAL - TOP_DEPTH)
    sphere = cq.Workplane("XY").sphere(R_CROWN_REAL).translate((0, 0, sph_center_z))

    # Aparar a esfera abaixo de z_top_cyl → fica só a calota superior.
    big = 4.0 * R_REACTOR
    cut_box = (cq.Workplane("XY")
               .box(big, big, big)
               .translate((0, 0, z_top_cyl - big/2.0)))
    cap = sphere.cut(cut_box)

    fluid = cyl.union(cap)

    # Fillet de joelho na junção cilindro/calota (aproxima toroesférico ASME).
    try:
        fluid = fluid.edges(cq.selectors.NearestToPointSelector((R_REACTOR, 0, z_top_cyl))) \
                     .fillet(R_KNUCKLE * 0.4)
        print(f"     joelho r_fillet={R_KNUCKLE*0.4:.3f} m aplicado")
    except Exception as e:
        print(f"     joelho ignorado ({e}) — calota simples mantida")

    return fluid


def subtract_return_tube(fluid):
    """Cavidade DN100 central (tubo de retorno)."""
    print("  [2] Cavidade DN100 central...")
    ret = (cq.Workplane("XY")
           .cylinder(H_RETURN, R_RETURN)
           .translate((0, 0, -H_REACTOR/2.0 + H_RETURN/2.0)))
    return fluid.cut(ret)


def cut_dn50_outlets(fluid):
    """Furos DN50 na parede do reator — agora distribuídos azimutalmente."""
    print("  [3] Furos DN50 (4 saídas, ângulos independentes)...")
    for pct, _tilt, az in SEPARATORS:
        z_rel = pct * H_REACTOR - H_REACTOR/2.0
        ang   = math.radians(az)
        # Eixo do furo: radial saindo do centro no azimute az
        # Cria cilindro horizontal na direção +X e rotaciona em torno de Z.
        hole = (cq.Workplane("YZ")
                .circle(D_SEP_OUT/2.0)
                .extrude(0.20)                          # comprimento radial do furo
                .translate((R_REACTOR - 0.05, 0, 0))    # centrado um pouco dentro da parede
                .rotate((0, 0, 0), (0, 0, 1), az)
                .translate((0, 0, z_rel)))
        fluid = fluid.cut(hole)
        print(f"     DN50 @ z={pct*100:.0f}% (z_rel={z_rel:+.2f} m)  az={az:.0f}°")
    return fluid


# ═══════════════════════════════════════════════════════
# SEPARADORES (intersecção booleana com casca — mantido v5.1)
# ═══════════════════════════════════════════════════════

def build_separators():
    """8 placas inclinadas, aparadas ao cilindro interno."""
    print("  [4] Separadores (intersecção booleana ao cilindro)...")

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

        offset = SEP_GAP_R + span/2.0
        plate_L = pL.translate((-offset, 0, z_rel))
        plate_R = pR.translate(( offset, 0, z_rel))

        try:
            sep_list.append(plate_L.intersect(clip_cyl))
            sep_list.append(plate_R.intersect(clip_cyl))
            print(f"     {pct*100:.0f}%: ±{tilt}° → aparado ✅")
        except Exception as e:
            sep_list.append(plate_L)
            sep_list.append(plate_R)
            print(f"     {pct*100:.0f}%: ±{tilt}° → clip falhou ({e}) ⚠️")

    return sep_list


# ═══════════════════════════════════════════════════════
# BOCAIS — CORRIGIDOS: atravessam a parede
# ═══════════════════════════════════════════════════════

def build_nozzles():
    """
    6 bocais tangenciais.  CORREÇÃO v5.2:
      • Eixo do bocal = mistura RADIAL (entrando) + TANGENCIAL,
        controlada por NOZZLE_TANG_ANGLE.
      • Centro do cilindro do bocal posicionado NA parede (R_REACTOR),
        de modo que ~50% fica fora (face Inlet do BC) e ~50% dentro
        (descarga real no domínio).
      • Componente vertical −tan(NOZZLE_INCL) cria swirl descendente.
    """
    print("  [5] Bocais tangenciais (6×, atravessam a parede)...")
    noz_list = []
    tang_rad = math.radians(NOZZLE_TANG_ANGLE)
    incl_rad = math.radians(NOZZLE_INCL)

    for i in range(N_NOZZLES):
        a    = math.radians(i * (360.0 / N_NOZZLES))
        r_hat = (math.cos(a),  math.sin(a))      # radial saindo
        t_hat = (-math.sin(a), math.cos(a))      # tangencial (sentido de rotação)

        # Direção de entrada (vetor unitário do eixo do bocal):
        #   componente radial entrando (−r_hat) modulada por cos(tang_angle)
        #   componente tangencial (+t_hat) modulada por sin(tang_angle)
        dx = -math.cos(tang_rad) * r_hat[0] + math.sin(tang_rad) * t_hat[0]
        dy = -math.cos(tang_rad) * r_hat[1] + math.sin(tang_rad) * t_hat[1]
        dz = -math.tan(incl_rad)             # descendente
        mag = math.sqrt(dx*dx + dy*dy + dz*dz)
        dx /= mag;  dy /= mag;  dz /= mag

        # Centro do bocal NA parede → metade fora, metade dentro
        cx = R_REACTOR * r_hat[0]
        cy = R_REACTOR * r_hat[1]
        cz = NOZZLE_Z - H_REACTOR/2.0

        # Cilindro inicialmente alinhado a +Z; rotacionar para alinhar a d.
        # Eixo de rotação = (0,0,1) × d ; ângulo = acos(d·z) = acos(dz)
        noz = cq.Workplane("XY").cylinder(NOZZLE_L, NOZZLE_D/2.0)
        ang_rot = math.degrees(math.acos(max(-1.0, min(1.0, dz))))
        if ang_rot > 1e-3:
            ax_x, ax_y = -dy, dx       # (0,0,1) × (dx,dy,dz) = (−dy, dx, 0)
            noz = noz.rotate((0, 0, 0), (ax_x, ax_y, 0.0), ang_rot)
        noz_list.append(noz.translate((cx, cy, cz)))

        print(f"     bocal {i+1}: az={math.degrees(a):.0f}°  "
              f"d=({dx:+.2f},{dy:+.2f},{dz:+.2f})  centro=({cx:+.2f},{cy:+.2f})")

    return noz_list


# ═══════════════════════════════════════════════════════
# DIFUSORES DE FUNDO  (novo em v5.2)
# ═══════════════════════════════════════════════════════

def build_diffusers():
    """
    N_DIFF tubos no fundo, espaçados radialmente, levemente inclinados
    (5–10°) para distribuir o gás de alimentação.  Eixo aponta para cima
    com pequena componente radial-tangencial.
    """
    print(f"  [6] Difusores ({N_DIFF}× no fundo, tilt {DIFF_TILT}°)...")
    diff_list = []
    tilt_rad  = math.radians(DIFF_TILT)

    for i in range(N_DIFF):
        a = math.radians(i * (360.0 / N_DIFF))
        r_hat = (math.cos(a),  math.sin(a))
        t_hat = (-math.sin(a), math.cos(a))

        # Eixo: predominantemente +Z, inclinado para a tangente
        dx = math.sin(tilt_rad) * t_hat[0]
        dy = math.sin(tilt_rad) * t_hat[1]
        dz = math.cos(tilt_rad)
        # Centro do difusor logo acima do fundo
        cx = DIFF_R_POS * r_hat[0]
        cy = DIFF_R_POS * r_hat[1]
        cz = DIFF_Z - H_REACTOR/2.0

        diff = cq.Workplane("XY").cylinder(DIFF_L, DIFF_D/2.0)
        ang_rot = math.degrees(math.acos(max(-1.0, min(1.0, dz))))
        if ang_rot > 1e-3:
            ax_x, ax_y = -dy, dx
            diff = diff.rotate((0, 0, 0), (ax_x, ax_y, 0.0), ang_rot)
        diff_list.append(diff.translate((cx, cy, cz)))
        print(f"     difusor {i+1}: az={math.degrees(a):.0f}°  r_pos={DIFF_R_POS:.2f} m")

    return diff_list


# ═══════════════════════════════════════════════════════
# ELETRODOS — gap face-a-face explícito
# ═══════════════════════════════════════════════════════

def build_electrode_pairs():
    """
    2 pares A/C.  CORREÇÃO v5.2: gap interpretado como FACE-A-FACE.
    Distância centro-a-centro = ELEC_GAP_FACE + ELEC_THICK.
    """
    print("  [7] Eletrodos — 2 pares A/C...")

    r_ext = ELEC_R_POS + ELEC_W/2.0
    r_int = ELEC_R_POS - ELEC_W/2.0
    assert r_ext < R_REACTOR, f"Eletrodo toca a parede: r_ext={r_ext:.3f} > R={R_REACTOR}"
    assert r_int > R_RETURN,  f"Eletrodo toca DN100:    r_int={r_int:.3f} < R_ret={R_RETURN}"
    print(f"     verificação radial: r_int={r_int:.3f}  r_ext={r_ext:.3f}  (folga parede "
          f"{R_REACTOR - r_ext:.3f} m)")

    c2c = ELEC_GAP_FACE + ELEC_THICK       # centro-a-centro real
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
                     .translate((ax, ay, ELEC_Z_CTR)))

        bx = cx - (c2c/2.0) * tangent[0]
        by = cy - (c2c/2.0) * tangent[1]
        cathode = (base.rotate((0, 0, 0), (0, 0, 1), pair_angle)
                       .translate((bx, by, ELEC_Z_CTR)))

        plates.extend([anode, cathode])
        print(f"     par {i+1} @ {pair_angle:.0f}°  c2c={c2c*1000:.1f} mm "
              f"(face-a-face {ELEC_GAP_FACE*1000:.0f} mm)")

    return plates


# ═══════════════════════════════════════════════════════
# MONTAGEM
# ═══════════════════════════════════════════════════════

print("=" * 64)
print("FIORA IC v5.2 — Geometria Corrigida")
print("=" * 64)
print(f"  Reator      : D={D_REACTOR} m  H={H_REACTOR} m  "
      f"V={math.pi/4*D_REACTOR**2*H_REACTOR:.1f} m³")
print(f"  Topo        : domo h={TOP_DEPTH:.3f} m  R_sph={R_CROWN_REAL:.3f} m  (UNIÃO)")
print(f"  Retorno     : DN100 central")
print(f"  Separadores : {len(SEPARATORS)} níveis — saídas DN50 em "
      f"{[s[2] for s in SEPARATORS]}°")
print(f"  Bocais      : {N_NOZZLES}× tang. (ângulo c/ radial = {NOZZLE_TANG_ANGLE}°)")
print(f"  Difusores   : {N_DIFF}× no fundo (tilt {DIFF_TILT}°)")
print(f"  Eletrodos   : {len(PAIR_ANGLES)} pares A/C, gap face-a-face "
      f"{ELEC_GAP_FACE*1000:.0f} mm")
print()

# Domínio fluido
fluid = build_fluid_domain()
fluid = subtract_return_tube(fluid)
fluid = cut_dn50_outlets(fluid)

# Sólidos internos / externos
sep_list  = build_separators()
noz_list  = build_nozzles()
diff_list = build_diffusers()
elec_list = build_electrode_pairs()


def _union(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.union(p)
    return out

# ═══════════════════════════════════════════════════════
# EXPORTAÇÃO
# ═══════════════════════════════════════════════════════
print("\nExportando STEP files...")

cq.exporters.export(fluid, "FIORA_IC_v5_2_fluid_domain.step")
print("  ✅ FIORA_IC_v5_2_fluid_domain.step  (cilindro+domo+DN100+4×DN50)")

cq.exporters.export(_union(sep_list), "FIORA_IC_v5_2_separators.step")
print("  ✅ FIORA_IC_v5_2_separators.step    (8 placas inclinadas)")

cq.exporters.export(_union(noz_list), "FIORA_IC_v5_2_nozzles.step")
print("  ✅ FIORA_IC_v5_2_nozzles.step       (6 bocais ATRAVESSANDO a parede)")

cq.exporters.export(_union(diff_list), "FIORA_IC_v5_2_diffusers.step")
print(f"  ✅ FIORA_IC_v5_2_diffusers.step     ({N_DIFF} difusores de fundo)")

cq.exporters.export(_union(elec_list), "FIORA_IC_v5_2_electrodes.step")
print("  ✅ FIORA_IC_v5_2_electrodes.step    (2 pares A/C, gap face-a-face)")

print("\n" + "=" * 64)
print("v5.2 CONCLUÍDO")
print("=" * 64)
print("""
PRINCIPAIS MUDANÇAS vs v5.1:
  • Bocais agora atravessam a parede (50% fora / 50% dentro)
  • Topo é DOMO (união), não mais cavidade invertida
  • Difusores adicionados (estavam faltando)
  • Saídas DN50 distribuídas em 0/90/180/270°
  • Gap eletrodos explicitamente FACE-A-FACE

VERIFICAÇÕES NO STAR-CCM+:
  □ Importar os 5 .step
  □ Conferir que cada bocal mostra DUAS faces de tampa:
      - face externa (z>parede)  → Inlet BC
      - face interna (dentro)    → fica interna após Subtract com fluid
  □ Tools > Geometry Check → zero erros
  □ Espessura do anel parede-eletrodo (≥ 100 mm) p/ isolamento
""")
