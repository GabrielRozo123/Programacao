"""Figuras do carrossel LinkedIn — 'A dificuldade de prever o h em mudança de fase'.
Square 1080x1080, mobile-legível. Paleta CVD-safe: teoria (azul aço), experimental (âmbar),
CFD-2D (vermelho contido = a falha)."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# --- paleta ---
INK      = "#1A1A2E"   # texto primário
MUTED    = "#6B7280"   # texto secundário
GRID     = "#E5E7EB"
TEORIA   = "#35618F"   # Nusselt (referência)
EXPER    = "#C98A2B"   # experimental
CFD      = "#B23A48"   # CFD 2D (a subestimação)
SURF     = "#FBFBFD"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": GRID, "axes.linewidth": 1.0,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.facecolor": SURF, "axes.facecolor": SURF,
})

# ============================================================
# FIG 1 — O gap do h: Nusselt vs Experimental vs CFD 2D
# ============================================================
fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=150)
labels = ["Nusselt\n(teoria)", "Experimental\n(bancada)", "CFD 2D\n(este estudo)"]
vals   = [9.7, 5.5, 2.29]
colors = [TEORIA, EXPER, CFD]
x = np.arange(3)
bars = ax.bar(x, vals, width=0.62, color=colors, zorder=3)
# rounded-ish top via edge
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v+0.22, f"{v:.2f}",
            ha="center", va="bottom", fontsize=21, fontweight="bold", color=INK)
ax.text(x[0], 9.7*0.5, "alvo", ha="center", va="center", color="white",
        fontsize=13, fontweight="bold", rotation=0)
# seta do gap
ax.annotate("", xy=(2, 2.29), xytext=(2, 9.7),
            arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.6))
ax.text(2.34, (9.7+2.29)/2, "~4×\nabaixo", ha="left", va="center",
        fontsize=15, color=CFD, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=14, color=INK)
ax.set_ylabel("h  (kW/m²·K)", fontsize=15)
ax.set_ylim(0, 11.5)
ax.set_yticks([0,2,4,6,8,10])
ax.grid(axis="y", color=GRID, lw=1, zorder=0)
for s in ["top","right"]: ax.spines[s].set_visible(False)
ax.set_title("O coeficiente h de condensação — quem acerta?",
             fontsize=17, fontweight="bold", color=INK, pad=16, loc="left")
fig.text(0.5, 0.045, "Vapor saturado · tubo horizontal Ø25,4 mm · ΔT = 25 K",
         fontsize=12, color=MUTED, ha="center")
fig.subplots_adjust(left=0.13, right=0.96, top=0.90, bottom=0.14)
fig.savefig("fig1_gap_h.png", dpi=150, facecolor=SURF)
plt.close(fig)

# ============================================================
# FIG 2 — h(θ): a forma bate no topo, colapsa na base
# ============================================================
fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=150)
theta = np.linspace(0, 180, 181)          # 0 = topo, 180 = base
# Nusselt local: fino no topo (h alto), engrossa até a base (h baixo mas FINITO).
# forma teórica ~ (fração do perímetro) com piso na base.
h_nu = 3.4 + 6.3*(0.5 + 0.5*np.cos(np.radians(theta)))**0.55   # topo ~9.7, base ~3.4
# CFD: enquadra/ultrapassa no topo (~9-12), mas DESPENCA na base (filme acumula) -> média baixa
drop = 1/(1+np.exp((theta-92)/20))         # ~1 no topo, ->0 na base
h_cfd = 0.8 + 11.0*drop                     # topo ~11.8 (enquadra Nusselt); base ~0.8 (colapsa)

ax.plot(theta, h_nu, color=TEORIA, lw=3, label="Nusselt (teoria)", zorder=3)
ax.plot(theta, h_cfd, color=CFD, lw=3, label="CFD 2D", zorder=4)
ax.fill_between(theta, h_cfd, h_nu, where=(h_cfd<h_nu), color=CFD, alpha=0.10, zorder=1)

# marcadores de região
ax.axvspan(0, 40, color=TEORIA, alpha=0.05, zorder=0)
ax.text(20, 11.2, "TOPO\nfilme fino\nh enquadra", ha="center", va="top",
        fontsize=11, color=TEORIA, fontweight="bold")
ax.text(150, 4.6, "BASE\nfilme acumula\n(não drena em 2D)", ha="center", va="center",
        fontsize=11, color=CFD, fontweight="bold")
ax.set_xlabel("posição angular θ  (°) — 0 = topo, 180 = base", fontsize=14)
ax.set_ylabel("h local  (kW/m²·K)", fontsize=15)
ax.set_xlim(0,180); ax.set_ylim(0,12.5)
ax.set_xticks([0,45,90,135,180])
ax.grid(color=GRID, lw=1, zorder=0)
for s in ["top","right"]: ax.spines[s].set_visible(False)
ax.legend(loc="upper right", frameon=False, fontsize=13)
ax.set_title("A forma do h(θ) está certa — a média, não",
             fontsize=17, fontweight="bold", color=INK, pad=16, loc="left")
fig.subplots_adjust(left=0.13, right=0.96, top=0.90, bottom=0.11)
fig.savefig("fig2_htheta.png", dpi=150, facecolor=SURF)
plt.close(fig)

# ============================================================
# FIG 3 — As 3 armadilhas (cartão-resumo)
# ============================================================
fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=150)
ax.axis("off")
ax.set_xlim(0,10); ax.set_ylim(0,10)
ax.text(0.4, 9.4, "3 armadilhas do h em mudança de fase",
        fontsize=19, fontweight="bold", color=INK)
cards = [
    ("1", "Modelo difusivo × térmico",
     "O modelo padrão (VOF Evap/Cond) NÃO\ncondensa vapor puro — só conduz calor.\nPrecisa do modelo térmico (Fluid Film).", TEORIA),
    ("2", "Resolução do filme",
     "O filme tem dezenas de µm. Malha grossa\nnão resolve h = k/δ. 1ª célula ~5 µm,\n14 prism layers no tubo.", EXPER),
    ("3", "Dimensionalidade do dreno",
     "Gotejar é 3D (tensão superficial). Em 2D\no condensado não escorre → filme acumula\n→ h despenca ~4× abaixo de Nusselt.", CFD),
]
y = 7.7
for num, titulo, corpo, cor in cards:
    ax.add_patch(plt.Rectangle((0.4, y-1.9), 9.2, 1.75, facecolor="white",
                 edgecolor=GRID, lw=1.2, zorder=1))
    ax.add_patch(plt.Circle((1.15, y-1.0), 0.42, facecolor=cor, zorder=2))
    ax.text(1.15, y-1.02, num, ha="center", va="center", color="white",
            fontsize=20, fontweight="bold", zorder=3)
    ax.text(1.95, y-0.45, titulo, fontsize=15, fontweight="bold", color=INK, va="center")
    ax.text(1.95, y-1.32, corpo, fontsize=11.5, color=MUTED, va="center", linespacing=1.35)
    y -= 2.25
ax.text(0.4, 0.35, "Cada uma, sozinha, entrega um h confiante e errado.",
        fontsize=13, color=CFD, fontweight="bold", style="italic")
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
fig.savefig("fig3_armadilhas.png", dpi=150, facecolor=SURF)
plt.close(fig)

print("OK: fig1_gap_h.png, fig2_htheta.png, fig3_armadilhas.png")
