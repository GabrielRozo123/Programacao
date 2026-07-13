"""Histogramas de tamanho de bolha p/ o slide 6 (Aerador) — casos 2 e 3 kgf/cm2,
no MESMO estilo do caso 1 (hist_bolha_caso1.png). Le os CSVs do STAR e plota."""
import numpy as np
import matplotlib.pyplot as plt

# --- cores do caso 1 (clonadas) ---
BAR   = "#2CB5D6"   # cyan das barras
EDGE  = "#1799B5"   # borda teal
META  = "#F5A623"   # laranja tracejado (meta 200 um)
SMDC  = "#B39DDB"   # roxo (SMD medio)
TICK  = "#1F7A96"   # cor dos numeros dos eixos
GRID  = "#E8E8E8"

CASOS = {
    2: dict(csv="../simulacao/caso2_2kgf/histograma_2.csv", smd=2.437, out="hist_bolha_caso2.png"),
    3: dict(csv="../simulacao/caso3_3kgf/histograma_3.csv", smd=2.526, out="hist_bolha_caso3.png"),
}

for kgf, c in CASOS.items():
    d = np.genfromtxt(c["csv"], delimiter=",", skip_header=1)
    x, y = d[:,0], d[:,1]
    w = np.median(np.diff(x)) * 0.92          # largura da barra (~ espacamento do bin)

    fig, ax = plt.subplots(figsize=(15, 8), dpi=100)
    ax.bar(x, y, width=w, color=BAR, edgecolor=EDGE, linewidth=1.1, zorder=3)

    # meta de projeto (200 um = 0,2 mm)
    ax.axvline(0.2, color=META, ls=(0,(6,4)), lw=3.2, zorder=4)
    ax.annotate("meta de projeto\n< 200 µm", xy=(0.2, 12.2), xytext=(0.62, 12.2),
                va="center", ha="left", fontsize=17, fontweight="bold", color=META,
                arrowprops=dict(arrowstyle="->", color=META, lw=2))
    # SMD medio
    smd = c["smd"]
    ax.axvline(smd, color=SMDC, lw=3.2, zorder=4)
    ax.annotate(f"SMD médio\n{smd:.2f}".replace(".", ",")+" mm",
                xy=(smd, 10.3), xytext=(smd+0.55, 10.9),
                va="center", ha="left", fontsize=17, fontweight="bold", color=SMDC,
                arrowprops=dict(arrowstyle="->", color=SMDC, lw=2))

    ax.set_xlim(0, max(4.4, x.max()+0.2))
    ax.set_ylim(0, max(14.5, y.max()*1.08))
    ax.set_xticks(np.arange(0, 4.6, 0.5))
    ax.grid(axis="both", color=GRID, lw=1, zorder=0)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color(GRID)
    ax.tick_params(colors=TICK, labelsize=16, length=0)
    for t in ax.get_xticklabels()+ax.get_yticklabels():
        t.set_color(TICK); t.set_fontweight("bold")

    fig.subplots_adjust(left=0.06, right=0.98, top=0.97, bottom=0.08)
    fig.savefig(c["out"], dpi=100, facecolor="white")
    plt.close(fig)
    print(f"OK caso {kgf}: {c['out']}")

print("\n=== NUMEROS DAS TILES (preencher no PPT) ===")
sweep = np.genfromtxt("../simulacao/sweep_pressao_3casos.csv", delimiter=",", names=True)
for row in sweep:
    kgf = int(row["pressao_kgfcm2"])
    print(f"[{kgf} kgf/cm2]  SMD={row['SMD_medio_mm']:.2f} | moda={row['moda_mm']:.2f} | "
          f"mediana={row['mediana_mm']:.2f} | D10={row['D10_mm']:.2f} | D90={row['D90_mm']:.2f} | "
          f"flotavel<200um={row['flotavel_pct']:.1e}%")
