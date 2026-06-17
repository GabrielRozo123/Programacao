"""
Braskem PE5 — Geometria DEM Screw Conveyor
Dois casos: Rosca Padrão (standard) e Rosca com Cortes (cut-flight)

Exporta 3 STEP files:
  braskem_auger_casing.step          — calha + funil + coletor (igual para ambos)
  braskem_auger_rotor_standard.step  — eixo + pá helicoidal contínua
  braskem_auger_rotor_cutflight.step — eixo + pá com cortes a cada 90°

Estrutura igual ao tutorial Star-CCM+ DEM Particles in a Conveyor:
  Região Casing: volume onde as partículas PEAD existem
  Região Rotor:  superfície da rosca (Moving Wall Rotation no Star-CCM+)

Parâmetros marcados com *** = confirmar com Jeferson na reunião quinta-feira
"""

import cadquery as cq
import math
import os

# ============================================================
# PARÂMETROS — substituir após reunião com Jeferson
# ============================================================

# Rosca (auger)
D_SHAFT   = 30.0     # mm — diâmetro do eixo                     *** confirmar
D_SCREW   = 100.0    # mm — diâmetro externo da pá               *** confirmar
T_BLADE   = 4.0      # mm — espessura da pá
PITCH     = 100.0    # mm — passo da hélice (= D_SCREW = padrão) *** confirmar
N_TURNS   = 6        # número de voltas
L_SCREW   = N_TURNS * PITCH   # 600 mm — comprimento ativo da pá
L_SHAFT_EXTRA = 35.0 # mm — eixo se estende além da pá (cada lado)
L_TOTAL_SHAFT = L_SCREW + 2 * L_SHAFT_EXTRA  # 670 mm

# Calha (casing)
CLEARANCE   = 3.0   # mm — folga radial entre pá e calha
D_CASING_I  = D_SCREW + 2 * CLEARANCE   # 106 mm — diâmetro interno
T_CASING    = 6.0   # mm — espessura da parede da calha

# Funil de alimentação (hopper) — cilíndrico, perpendicular ao tubo
H_HOPPER      = 90.0   # mm — altura acima da superfície externa da calha
HOPPER_X      = L_SHAFT_EXTRA + PITCH * 0.75  # posição axial do centro do funil
HOPPER_R_INNER = 30.0  # mm — raio interno do funil (bore de partículas)

# Cilindro coletor (receiving hopper) na saída
D_RECEIVER  = 130.0  # mm
L_RECEIVER  = 70.0   # mm

# Parâmetros Cut-Flight
CUTS_PER_TURN  = 4    # cortes por volta → a cada 90° de rotação
CUT_FRACTION   = 0.45 # fração da pá removida por corte (45% → cortes bem visíveis)

# ============================================================
# COMPONENTES DA GEOMETRIA (eixo da rosca ao longo de Z)
# Rotação final: Z → X (match com tutorial Star-CCM+)
# ============================================================

def make_shaft():
    """Eixo cilíndrico central"""
    return (
        cq.Workplane("XY")
        .circle(D_SHAFT / 2)
        .extrude(L_TOTAL_SHAFT)
    )


def make_helical_blade_full():
    """
    Pá helicoidal CONTÍNUA.
    Loft de seções retangulares radiais: cada seção é um retângulo (inner_r→outer_r) × T_BLADE
    posicionado na ângulo/altura correta da hélice.
    """
    outer_r = D_SCREW / 2
    inner_r = D_SHAFT / 2

    n_secs = N_TURNS * 60  # 60 seções por volta → 360 total
    sections = []
    for i in range(n_secs + 1):
        t = i / n_secs
        angle = t * 2 * math.pi * N_TURNS
        z = L_SHAFT_EXTRA + t * L_SCREW
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        # Retângulo radial: p1(inner,z) → p2(outer,z) → p3(outer,z+T) → p4(inner,z+T)
        p1 = cq.Vector(inner_r * cos_a, inner_r * sin_a, z)
        p2 = cq.Vector(outer_r * cos_a, outer_r * sin_a, z)
        p3 = cq.Vector(outer_r * cos_a, outer_r * sin_a, z + T_BLADE)
        p4 = cq.Vector(inner_r * cos_a, inner_r * sin_a, z + T_BLADE)

        wire = cq.Wire.assembleEdges([
            cq.Edge.makeLine(p1, p2),
            cq.Edge.makeLine(p2, p3),
            cq.Edge.makeLine(p3, p4),
            cq.Edge.makeLine(p4, p1),
        ])
        sections.append(wire)

    return cq.Workplane().add(cq.Solid.makeLoft(sections))


def make_helical_blade_cutflight():
    """
    Pá helicoidal com CORTES a cada 90° (cut-flight screw).
    Pá base via loft de seções retangulares (geometria correta),
    depois subtrai cunhas nos gaps.
    """
    outer_r = D_SCREW / 2
    inner_r = D_SHAFT / 2

    # === Pá base com geometria correta (loft) ===
    n_secs = N_TURNS * 60
    sections = []
    for i in range(n_secs + 1):
        t = i / n_secs
        angle = t * 2 * math.pi * N_TURNS
        z = L_SHAFT_EXTRA + t * L_SCREW
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        p1 = cq.Vector(inner_r * cos_a, inner_r * sin_a, z)
        p2 = cq.Vector(outer_r * cos_a, outer_r * sin_a, z)
        p3 = cq.Vector(outer_r * cos_a, outer_r * sin_a, z + T_BLADE)
        p4 = cq.Vector(inner_r * cos_a, inner_r * sin_a, z + T_BLADE)

        wire = cq.Wire.assembleEdges([
            cq.Edge.makeLine(p1, p2),
            cq.Edge.makeLine(p2, p3),
            cq.Edge.makeLine(p3, p4),
            cq.Edge.makeLine(p4, p1),
        ])
        sections.append(wire)

    blade = cq.Workplane().add(cq.Solid.makeLoft(sections))

    # Parâmetros dos cortes
    segment_pitch = PITCH / CUTS_PER_TURN
    blade_h = segment_pitch * (1.0 - CUT_FRACTION)
    cut_h   = segment_pitch * CUT_FRACTION
    N_GAPS  = N_TURNS * CUTS_PER_TURN

    # Dimensões da cunha cortante
    cut_outer_r   = outer_r + 2.0   # ultrapassa a borda da pá
    cut_inner_r   = inner_r - 1.0   # corta até o eixo
    cutter_height = cut_h + T_BLADE * 3  # margem extra para corte limpo

    # Ângulo angular da cunha (no espaço XY)
    # cut_h axial corresponde a cut_h/PITCH × 360° de rotação da hélice
    cut_angle_deg = (cut_h / PITCH) * 360.0 * 1.6  # × 1.6 de margem

    for i in range(N_GAPS):
        # Centro axial do gap
        z_gap = L_SHAFT_EXTRA + i * segment_pitch + blade_h + cut_h / 2.0

        # Ângulo da hélice no centro do gap
        theta_deg = ((z_gap - L_SHAFT_EXTRA) / PITCH) * 360.0
        theta_rad = math.radians(theta_deg)

        # Constrói cunha como setor de anel (polígono aproximado)
        half_angle = math.radians(cut_angle_deg / 2.0)
        n_pts = 8  # pontos para aproximar o arco

        # Arco externo (outer_r, de theta-half a theta+half)
        outer_arc = [
            (cut_outer_r * math.cos(theta_rad - half_angle + j * 2 * half_angle / (n_pts - 1)),
             cut_outer_r * math.sin(theta_rad - half_angle + j * 2 * half_angle / (n_pts - 1)))
            for j in range(n_pts)
        ]
        # Arco interno (inner_r, de theta+half de volta a theta-half)
        inner_arc = [
            (cut_inner_r * math.cos(theta_rad + half_angle - j * 2 * half_angle / (n_pts - 1)),
             cut_inner_r * math.sin(theta_rad + half_angle - j * 2 * half_angle / (n_pts - 1)))
            for j in range(n_pts)
        ]

        pts = outer_arc + inner_arc

        cutter = (
            cq.Workplane("XY")
            .workplane(offset=z_gap - cutter_height / 2.0)
            .polyline(pts)
            .close()
            .extrude(cutter_height)
        )

        blade = blade.cut(cutter)

    return blade


def make_casing_assembly():
    """
    Calha DEM completa para Star-CCM+.

    Funil CILÍNDRICO perpendicular ao tubo:
      - A interseção de dois cilindros perpendiculares cria bordas ELÍPTICAS na junção,
        exatamente como a geometria de referência do tutorial Star-CCM+ (Casing.step).
      - Isso produz o efeito "soldado" (welded) na entrada do funil.

    Estrutura de fronteiras (boundary conditions no Star-CCM+):
      Tube Wall     → Wall + DEM Interaction (E_aço, μ_PEAD-aço)
      Hopper Wall   → Wall + DEM Interaction (idem)
      Left Cap      → Wall (fundo esquerdo — inlet endcap)
      Escape Cap    → Wall com DEM Escape (face de saída do coletor)

    Coordenadas (pré-rotação Z→-X):
      Workplane("XZ") normal = -Y  →  funil cresce em -Y
      gravity = +Y no solver Star-CCM+ (funil aparece "acima" na cena)
    """
    r_inner = D_CASING_I / 2        # 53 mm
    r_outer = r_inner + T_CASING    # 59 mm
    hopper_r_out = HOPPER_R_INNER + T_CASING  # 36 mm — raio externo do funil

    # ─── 1. Sólidos exteriores (antes de escavar) ───────────────────────────

    solid_tube = (
        cq.Workplane("XY")
        .circle(r_outer)
        .extrude(L_TOTAL_SHAFT)
    )

    # Funil cilíndrico: penetra 2 mm dentro da parede do tubo para garantir
    # interseção volumétrica limpa → borda elíptica na junção (look "soldado")
    solid_hopper = (
        cq.Workplane("XZ")
        .workplane(offset=r_outer - 2.0)   # Y = -(r_outer-2) = -57 mm
        .center(0, HOPPER_X)
        .circle(hopper_r_out)
        .extrude(H_HOPPER + 2.0)           # −Y até Y = -(r_outer + H_HOPPER) = -149 mm
    )

    casing_solid = solid_tube.union(solid_hopper)

    # ─── 2. Voids (bore interno) ─────────────────────────────────────────────

    void_tube = (
        cq.Workplane("XY")
        .circle(r_inner)
        .extrude(L_TOTAL_SHAFT)
    )

    # Bore do funil: começa 1 mm dentro do bore do tubo (Y=-52mm) e vai até
    # o topo do funil (Y=-149mm). Isso corta a parede do tubo na posição do funil
    # (Y=-53..−59mm) criando a abertura circular que conecta os dois volumes.
    void_hopper = (
        cq.Workplane("XZ")
        .workplane(offset=r_inner - 1.0)          # Y = -(r_inner-1) = -52 mm
        .center(0, HOPPER_X)
        .circle(HOPPER_R_INNER)
        .extrude(H_HOPPER + T_CASING + 1.0)       # 97 mm → até Y = -149 mm
    )

    casing = casing_solid.cut(void_tube).cut(void_hopper)

    # ─── 3. Tampa esquerda (inlet endcap em Z=0) ────────────────────────────
    left_cap = (
        cq.Workplane("XY")
        .circle(r_inner)
        .extrude(T_CASING)
        .cut(
            cq.Workplane("XY")
            .circle(D_SHAFT / 2 + 1.0)
            .extrude(T_CASING)
        )
    )
    casing = casing.union(left_cap)

    # ─── 4. Coletor OCO com face de escape ──────────────────────────────────
    # Bore contínuo com a calha (r_inner=53mm). Tampa traseira (T_CASING) = DEM Escape.
    receiver = (
        cq.Workplane("XY")
        .workplane(offset=L_TOTAL_SHAFT)
        .circle(D_RECEIVER / 2)
        .extrude(L_RECEIVER)
        .cut(
            cq.Workplane("XY")
            .workplane(offset=L_TOTAL_SHAFT)
            .circle(r_inner)
            .extrude(L_RECEIVER - T_CASING)
        )
    )
    casing = casing.union(receiver)

    return casing


def assemble_rotor(blade):
    """Une eixo + pá"""
    shaft = make_shaft()
    return shaft.union(blade)


def rotate_to_horizontal(shape):
    """
    Rotaciona de Z-axis (como construído) para X-axis (como no tutorial Star-CCM+).
    Rotação de 90° em torno do eixo Y.
    """
    return shape.rotate((0, 0, 0), (0, 1, 0), -90)


# ============================================================
# MONTAGEM E EXPORTAÇÃO
# ============================================================

def build_and_export(output_dir="."):
    os.makedirs(output_dir, exist_ok=True)

    print("Construindo pá padrão (contínua)...")
    blade_std = make_helical_blade_full()
    rotor_std = assemble_rotor(blade_std)

    print("Construindo pá cut-flight (com cortes a cada 90°)...")
    blade_cf = make_helical_blade_cutflight()
    rotor_cf = assemble_rotor(blade_cf)

    print("Construindo casing (calha + funil + abertura + coletor)...")
    casing_assembly = make_casing_assembly()

    # Rotaciona tudo para orientação horizontal (X-axis)
    rotor_std_h     = rotate_to_horizontal(rotor_std)
    rotor_cf_h      = rotate_to_horizontal(rotor_cf)
    casing_h        = rotate_to_horizontal(casing_assembly)

    # Exporta STEP
    path_std    = os.path.join(output_dir, "braskem_auger_rotor_standard.step")
    path_cf     = os.path.join(output_dir, "braskem_auger_rotor_cutflight.step")
    path_casing = os.path.join(output_dir, "braskem_auger_casing.step")

    print(f"Exportando: {path_std}")
    cq.exporters.export(rotor_std_h, path_std)

    print(f"Exportando: {path_cf}")
    cq.exporters.export(rotor_cf_h, path_cf)

    print(f"Exportando: {path_casing}")
    cq.exporters.export(casing_h, path_casing)

    print("\n=== Geometria exportada com sucesso ===")
    print(f"  Rosca padrão:     {path_std}")
    print(f"  Cut-flight:       {path_cf}")
    print(f"  Casing/calha:     {path_casing}")

    print("\n=== Resumo dimensional ===")
    print(f"  D_shaft   = {D_SHAFT} mm")
    print(f"  D_screw   = {D_SCREW} mm")
    print(f"  D_casing  = {D_CASING_I:.1f} mm (folga = {CLEARANCE} mm por lado)")
    print(f"  Pitch     = {PITCH} mm")
    print(f"  N_turns   = {N_TURNS}")
    print(f"  L_ativo   = {L_SCREW} mm")
    print(f"  L_shaft   = {L_TOTAL_SHAFT:.0f} mm total")
    print(f"  T_blade   = {T_BLADE} mm")
    print(f"  Cortes/volta = {CUTS_PER_TURN} (a cada 90°)")
    print(f"  Fração cortada = {CUT_FRACTION*100:.0f}% por segmento")
    print(f"  Funil: cilíndrico Ø{HOPPER_R_INNER*2:.0f}mm bore × H={H_HOPPER}mm (junção elíptica)")

    print("\n=== Instruções Star-CCM+ ===")
    print("1. File → Import → Surface Mesh → importar OS 3 STEP files")
    print("2. Geometry Scene: verificar gaps e erros na superfície")
    print("3. Assign Regions:")
    print("   - braskem_auger_casing → Region 'Casing' (volume mesh)")
    print("   - braskem_auger_rotor_standard → Region 'Rotor' (surface only, Moving Wall)")
    print("4. Mesh: Polyhedral, Base Size = 15mm (= 5× D_p para D50=3mm)")
    print("5. Physics: DEM + LFP + Implicit Unsteady + Gravity + Rotation Motion")
    print("6. Moving Wall: Rotor boundaries → Rotation, ω = rpm × 2π/60")


# ============================================================
# VALIDAÇÃO GEOMÉTRICA
# ============================================================

def print_geometry_checks():
    """Verifica parâmetros antes de gerar"""
    print("=== Verificações geométricas ===")

    clearance_ratio = CLEARANCE / (D_SCREW / 2)
    print(f"  Folga/Raio = {clearance_ratio:.3f} ({CLEARANCE}mm / {D_SCREW/2}mm)")
    if clearance_ratio < 0.05:
        print("  AVISO: folga < 5% do raio — malha pode ter problemas")
    else:
        print("  OK: folga adequada para malha")

    pitch_ratio = PITCH / D_SCREW
    print(f"  Pitch/Diâmetro = {pitch_ratio:.2f} (padrão industrial = 0.8–1.2)")

    segment_pitch = PITCH / CUTS_PER_TURN
    blade_h = segment_pitch * (1 - CUT_FRACTION)
    cut_h   = segment_pitch * CUT_FRACTION
    print(f"\n  Cut-flight:")
    print(f"    Altura do segmento ativo = {blade_h:.1f} mm")
    print(f"    Altura do corte (gap)    = {cut_h:.1f} mm")
    print(f"    Ângulo ativo por corte   = {(1-CUT_FRACTION)*90:.1f}°")
    print(f"    Ângulo do gap por corte  = {CUT_FRACTION*90:.1f}°")

    # Rayleigh timestep estimate (soft sphere)
    E_soft = 10e6   # Pa
    nu = 0.46
    rho = 950.0     # kg/m3
    Dp = 0.003      # m (D50 = 3mm estimado)
    G_soft = E_soft / (2 * (1 + nu))
    R = Dp / 2
    T_rayleigh = math.pi * R * math.sqrt(rho / G_soft)
    dt_dem = 0.1 * T_rayleigh
    print(f"\n  Estimativa de timestep DEM (D50=3mm, E_soft=10MPa):")
    print(f"    T_Rayleigh = {T_rayleigh*1e6:.1f} μs")
    print(f"    Δt_DEM     = {dt_dem*1e6:.1f} μs ({dt_dem:.2e} s)")


if __name__ == "__main__":
    print_geometry_checks()
    print()
    build_and_export(output_dir=".")
