"""Cards (tiles) escuros do slide 6 do Aerador — casos 2 e 3, no MESMO estilo do caso 1.
Painel vertical de 4 tiles: SMD medio / moda-mediana / bolha<200um / holdup de gas."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# --- cores clonadas do slide ---
BG    = "#15304C"   # fundo navy escuro
TILE  = "#1D3E62"   # tile navy
BORD  = "#2C577F"   # borda sutil
LABEL = "#9FB0C3"   # rotulo cinza-azulado
NUM   = "#FFFFFF"   # numero branco
MM    = "#B49BE0"   # unidade mm (lavanda)
PCT   = "#3FC1DB"   # unidade % (ciano)

CASOS = {
    2: dict(out="cards_caso2.png", tiles=[
        ("SMD MÉDIO (domínio)", "2,44", "mm", MM),
        ("MODA / MEDIANA",      "1,86 / 2,23", "mm", MM),
        ("BOLHA < 200 µm (meta)", "≈ 0", "%", PCT),
        ("HOLDUP DE GÁS",       "0,006", "%", PCT),
    ]),
    3: dict(out="cards_caso3.png", tiles=[
        ("SMD MÉDIO (domínio)", "2,53", "mm", MM),
        ("MODA / MEDIANA",      "1,90 / 2,32", "mm", MM),
        ("BOLHA < 200 µm (meta)", "≈ 0", "%", PCT),
        ("HOLDUP DE GÁS",       "0,007", "%", PCT),
    ]),
}

W, H = 9.0, 11.4          # polegadas (proporcao ~ painel do slide)
gap, mL, mR, mT, mB = 0.5, 0.5, 0.5, 0.5, 0.5
n = 4

for kgf, c in CASOS.items():
    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    th = (H - mT - mB - gap*(n-1)) / n     # altura de cada tile
    y = H - mT
    for label, num, unit, ucol in c["tiles"]:
        y0 = y - th
        ax.add_patch(FancyBboxPatch((mL, y0), W-mL-mR, th,
                     boxstyle="round,pad=0.02,rounding_size=0.14",
                     facecolor=TILE, edgecolor=BORD, linewidth=1.4, mutation_aspect=1))
        # rotulo (topo)
        ax.text(mL+0.42, y0+th-0.42, label, color=LABEL, fontsize=15,
                fontweight="bold", va="top", ha="left")
        # numero grande + unidade
        nfs = 40 if "/" not in num else 30
        t = ax.text(mL+0.42, y0+th*0.36, num, color=NUM, fontsize=nfs,
                    fontweight="bold", va="center", ha="left")
        fig.canvas.draw()
        bb = t.get_window_extent().transformed(ax.transData.inverted())
        ax.text(bb.x1+0.18, y0+th*0.30, unit, color=ucol, fontsize=17,
                fontweight="bold", va="center", ha="left")
        y = y0 - gap
    fig.savefig(c["out"], dpi=100, facecolor=BG)
    plt.close(fig)
    print(f"OK caso {kgf}: {c['out']}")
