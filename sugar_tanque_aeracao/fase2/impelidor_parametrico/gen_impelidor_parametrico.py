"""
Impelidor PARAMÉTRICO (projeto Sugar/Ito — Fase 2).
Baseado no Agimix AGX-PBW800 (hidrofólio duplo, 3 pás/estágio, Ø800 mm, eixo Ø69,85 mm).

Parâmetros que o Ito pediu para varrer (Design Manager):
  - D_IMPELIDOR : diâmetro ponta-a-ponta [mm]
  - ANGULO_PA   : ângulo de passo da pá (do plano horizontal) [graus]
  - N_PAS       : número de pás por estágio

Gera:
  - impelidor_parametrico.step        (1 estágio — o que se varre no MRF)
  - impelidor_parametrico_duplo.step  (2 estágios — igual ao real, para conferência)
  - preview_impelidor.png             (render para checagem visual)

Uso rápido (varredura manual):
  python3 gen_impelidor_parametrico.py            # defaults (Ø800, 30°, 3 pás)
  python3 gen_impelidor_parametrico.py 700 24 4   # D=700, ângulo=24°, 4 pás
Unidades: mm. Importar no STAR em mm.
"""
import sys
import numpy as np
import cadquery as cq

# ================== PARÂMETROS (defaults = Agimix AGX-PBW800) ==================
D_IMPELIDOR = 800.0     # mm  (diâmetro ponta-a-ponta)      <-- VARRER
ANGULO_PA   = 30.0      # deg (passo da pá, do horizontal)  <-- VARRER
N_PAS       = 3         # pás por estágio                    <-- VARRER

# --- fixos (do impelidor real; ajustáveis) ---
SHAFT_D     = 69.85     # mm  eixo (Ø real)
HUB_D       = 130.0     # mm  cubo
HUB_H       = 90.0      # mm  altura do cubo
BLADE_THK   = 10.0      # mm  espessura da pá
CHORD_FRAC  = 0.19      # corda da pá = CHORD_FRAC * D  (~152 mm p/ D=800)
N_STAGES    = 2         # estágios no conjunto duplo
STAGE_SPACING = 3556.0  # mm  distância entre estágios (medido no impelidor real: inf z=-4296, sup z=-740)

# --- POSICIONAMENTO no MRF do reator (medido do impelidor_3pas.step real) ---
# Para gerar o impelidor JÁ ALINHADO ao MRF (importar e encaixar), sem transform no STAR.
POS_EIXO_X  = 327.0     # mm  eixo de rotação x
POS_EIXO_Y  = -6282.0   # mm  eixo de rotação y (reator)
POS_Z_CENTRO = -2518.0  # mm  z do centro entre os 2 estágios (inf -4296, sup -740)

# --- restrição de PROPORÇÃO FABRIL (Ito): D não pode ser desproporcional ao tanque ---
T_TANQUE    = 5080.0    # mm  diâmetro interno do REATOR (ID 5,08 m, do CAD real)
DT_CLASSICO = (0.25, 0.50)  # faixa clássica D/T de impelidores de tanque agitado

# CLI opcional: D  angulo  n_pas
if len(sys.argv) >= 2: D_IMPELIDOR = float(sys.argv[1])
if len(sys.argv) >= 3: ANGULO_PA   = float(sys.argv[2])
if len(sys.argv) >= 4: N_PAS       = int(sys.argv[3])


def _stage(D, angle, n_pas, chord):
    """Um estágio: cubo + n pás de passo 'angle' arranjadas a 360/n."""
    r_hub = HUB_D / 2.0
    r_tip = D / 2.0
    Lr = r_tip - r_hub                      # comprimento radial da pá
    r_mid = r_hub + Lr / 2.0                # raio do centro da pá

    # cubo
    hub = cq.Workplane("XY").circle(r_hub).extrude(HUB_H, both=True)

    # uma pá: placa (radial Lr x corda x espessura). Passo = girar sobre o eixo RADIAL (X),
    # tiltando a corda (Y->Z). Isso mantém a PONTA em D/2 para qualquer ângulo (Ø = Ø varrido).
    blade0 = (cq.Workplane("XY").box(Lr, chord, BLADE_THK)
              .translate((r_mid, 0, 0))
              .rotate((0, 0, 0), (1, 0, 0), angle))            # passo sobre eixo radial (X)

    stage = hub
    for k in range(n_pas):
        stage = stage.union(blade0.rotate((0, 0, 0), (0, 0, 1), k * 360.0 / n_pas))
    return stage


def build(D, angle, n_pas, n_stages=1):
    chord = CHORD_FRAC * D
    r_shaft = SHAFT_D / 2.0

    if n_stages == 1:
        imp = _stage(D, angle, n_pas, chord)
        z_top = HUB_H + 200.0
        shaft = cq.Workplane("XY").circle(r_shaft).extrude(z_top, both=True)
        return imp.union(shaft)

    # duplo: 2 estágios no eixo + eixo longo (cobre o cilindro MRF inteiro c/ folga)
    total_h = STAGE_SPACING + 2 * HUB_H + 1400.0
    shaft = (cq.Workplane("XY").circle(r_shaft)
             .extrude(total_h).translate((0, 0, -total_h / 2.0)))
    assembly = shaft
    for j in range(n_stages):
        zc = -STAGE_SPACING / 2.0 + j * STAGE_SPACING
        assembly = assembly.union(_stage(D, angle, n_pas, chord).translate((0, 0, zc)))
    return assembly


def render(solid, path, title):
    """Render 3D simples (tessela + matplotlib) para checagem visual."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    verts, tris = solid.val().tessellate(0.5)
    P = np.array([[v.x, v.y, v.z] for v in verts])
    faces = [[P[a], P[b], P[c]] for (a, b, c) in tris]

    fig = plt.figure(figsize=(7, 7), dpi=110)
    ax = fig.add_subplot(111, projection="3d")
    coll = Poly3DCollection(faces, facecolor="#4C86C6", edgecolor=(0, 0, 0, 0.12), linewidths=0.2)
    ax.add_collection3d(coll)
    c = P.mean(axis=0)
    r = (P.max(axis=0) - P.min(axis=0)).max() / 2.0
    for setlim, ci in ((ax.set_xlim, c[0]), (ax.set_ylim, c[1]), (ax.set_zlim, c[2])):
        setlim(ci - r, ci + r)
    ax.view_init(elev=22, azim=35)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_box_aspect((1, 1, 1))
    try:
        ax.set_axis_off()
    except Exception:
        pass
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    tag = f"D{int(D_IMPELIDOR)}_ang{int(ANGULO_PA)}_n{N_PAS}"
    single = build(D_IMPELIDOR, ANGULO_PA, N_PAS, n_stages=1)
    cq.exporters.export(single, "impelidor_parametrico.step")

    duplo = build(D_IMPELIDOR, ANGULO_PA, N_PAS, n_stages=N_STAGES)
    cq.exporters.export(duplo, "impelidor_parametrico_duplo.step")

    # versão POSICIONADA no MRF do reator (importar e encaixar, sem transform no STAR)
    duplo_pos = duplo.translate((POS_EIXO_X, POS_EIXO_Y, POS_Z_CENTRO))
    cq.exporters.export(duplo_pos, "impelidor_parametrico_duplo_POSICIONADO.step")

    render(single, "preview_impelidor.png",
           f"Impelidor paramétrico — Ø{int(D_IMPELIDOR)}mm · {ANGULO_PA:g}° · {N_PAS} pás")

    r_tip = D_IMPELIDOR / 2.0
    dt = D_IMPELIDOR / T_TANQUE
    flag = "OK" if DT_CLASSICO[0] <= dt <= DT_CLASSICO[1] else "⚠️ FORA da faixa clássica"
    print(f"[{tag}]")
    print(f"  Ø = {D_IMPELIDOR:.1f} mm (r_ponta {r_tip:.1f}) · ângulo {ANGULO_PA:g}° · {N_PAS} pás/estágio")
    print(f"  D/T = {dt:.3f}  (T={T_TANQUE:.0f} mm; faixa clássica {DT_CLASSICO[0]}–{DT_CLASSICO[1]}) -> {flag}")
    print(f"  corda {CHORD_FRAC*D_IMPELIDOR:.1f} mm · cubo Ø{HUB_D} · eixo Ø{SHAFT_D}")
    print("  -> impelidor_parametrico.step (1 estágio)")
    print("  -> impelidor_parametrico_duplo.step (2 estágios)")
    print("  -> preview_impelidor.png")
