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

# Funil de alimentação (hopper)
W_HOPPER    = 70.0  # mm — largura (direção Y)
L_HOPPER_AX = 80.0  # mm — comprimento na direção do eixo (X)
H_HOPPER    = 90.0  # mm — altura acima da calha
HOPPER_X    = L_SHAFT_EXTRA + PITCH * 0.75  # posição axial do centro do funil

# Cilindro coletor (receiving hopper) na saída
D_RECEIVER  = 130.0  # mm
L_RECEIVER  = 70.0   # mm

# Parâmetros Cut-Flight
CUTS_PER_TURN  = 4    # cortes por volta → a cada 90° de rotação
CUT_FRACTION   = 0.25 # fração da pá removida por corte (25% do segmento)

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
    Pá helicoidal CONTÍNUA (rosca padrão).
    Sweep de retângulo radial ao longo de hélice com isFrenet=True.
    """
    outer_r = D_SCREW / 2
    inner_r = D_SHAFT / 2
    mid_r   = (outer_r + inner_r) / 2.0
    blade_w = outer_r - inner_r

    path = cq.Wire.makeHelix(pitch=PITCH, height=L_SCREW, radius=mid_r)

    blade = (
        cq.Workplane("XZ")
        .rect(blade_w, T_BLADE)
        .sweep(path, isFrenet=True)
        .translate((0, 0, L_SHAFT_EXTRA))  # desloca para começar após a extensão do eixo
    )
    return blade


def make_helical_blade_cutflight():
    """
    Pá helicoidal com CORTES a cada 90° (cut-flight screw).

    Estratégia robusta: começa da pá CONTÍNUA (que funciona) e subtrai
    cunhas (wedge cutters) nas posições de gap da hélice.

    Para cada segmento de CUTS_PER_TURN por volta:
      - Pá ativa: cobre (1 - CUT_FRACTION) × segment_pitch axialmente
      - Gap (corte): cunha posicionada na posição angular da hélice
    """
    outer_r = D_SCREW / 2
    inner_r = D_SHAFT / 2
    mid_r   = (outer_r + inner_r) / 2.0

    # Começa com a pá contínua completa (geometria comprovada)
    path = cq.Wire.makeHelix(pitch=PITCH, height=L_SCREW, radius=mid_r)
    blade = (
        cq.Workplane("XZ")
        .rect(outer_r - inner_r, T_BLADE)
        .sweep(path, isFrenet=True)
        .translate((0, 0, L_SHAFT_EXTRA))
    )

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


def make_casing():
    """
    Calha cilíndrica (tubo oco).
    Comprimento = comprimento total do eixo (cobre toda a rosca).
    """
    r_outer = D_CASING_I / 2 + T_CASING
    r_inner = D_CASING_I / 2

    outer_cyl = (
        cq.Workplane("XY")
        .circle(r_outer)
        .extrude(L_TOTAL_SHAFT)
    )
    inner_cyl = (
        cq.Workplane("XY")
        .circle(r_inner)
        .extrude(L_TOTAL_SHAFT)
    )
    return outer_cyl.cut(inner_cyl)


def make_hopper():
    """
    Funil de alimentação: caixa retangular acima da calha,
    com abertura no topo e abertura na face inferior que comunica
    com o interior da calha.
    """
    r_casing = D_CASING_I / 2 + T_CASING

    # Corpo do funil
    hopper = (
        cq.Workplane("XZ")
        .workplane(offset=D_CASING_I / 2 + T_CASING)  # começa na parte superior da calha
        .rect(L_HOPPER_AX, W_HOPPER)
        .extrude(H_HOPPER)
        .translate((0, 0, HOPPER_X - L_HOPPER_AX / 2))  # posiciona axialmente
    )

    # Abertura na base do funil (comunica com a calha)
    # A abertura é um retângulo que subtrai a parede da calha
    opening = (
        cq.Workplane("XZ")
        .workplane(offset=r_casing - 0.1)  # ligeiramente abaixo da parede externa
        .rect(L_HOPPER_AX - 2 * T_CASING, W_HOPPER - 2 * T_CASING)
        .extrude(T_CASING + 0.2)  # perfura a parede da calha
        .translate((0, 0, HOPPER_X - L_HOPPER_AX / 2 + T_CASING))
    )

    return hopper


def make_receiver():
    """
    Cilindro coletor de partículas na saída (lado direito).
    Partículas saem da calha e caem neste coletor.
    """
    z_start = L_TOTAL_SHAFT  # inicia imediatamente após o final da calha
    return (
        cq.Workplane("XY")
        .workplane(offset=z_start)
        .circle(D_RECEIVER / 2)
        .extrude(L_RECEIVER)
    )


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

    print("Construindo casing (calha + funil + coletor)...")
    casing = make_casing()
    hopper = make_hopper()
    receiver = make_receiver()

    # Montagem do casing assembly (uma peça única para importar no Star-CCM+)
    casing_assembly = casing.union(hopper).union(receiver)

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
