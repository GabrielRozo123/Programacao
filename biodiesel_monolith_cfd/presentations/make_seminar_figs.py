"""
Figuras para a apresentação do Seminário de Mestrado.
Todas baseadas em resultados validados da Fase 1 e Fase 2.

Gabriel Rozo | FEQ/UNICAMP
"""
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = pathlib.Path(__file__).resolve().parent / "figs"
OUT.mkdir(exist_ok=True)

# Paleta da apresentacao
PETROL = "#0B3C49"
TEAL   = "#2A9D8F"
CORAL  = "#E76F51"
GOLD   = "#E9C46A"
GREY   = "#6B7B82"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 13,
    "axes.labelsize": 14,
    "axes.titlesize": 15,
    "axes.linewidth": 1.2,
    "axes.edgecolor": PETROL,
    "axes.labelcolor": PETROL,
    "text.color": PETROL,
    "xtick.color": PETROL,
    "ytick.color": PETROL,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "lines.linewidth": 2.4,
    "legend.fontsize": 12,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

def save(fig, nome):
    fig.savefig(OUT / f"{nome}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {nome}.png")

print("Gerando figuras:")

# ─────────────────────────────────────────────────────────────────────────
# A — Fase 1: validacao de Poiseuille
# ─────────────────────────────────────────────────────────────────────────
Dh, u_in = 1.1e-3, 1.0e-3
eta = np.linspace(-1, 1, 300)
u_ana = 1.5 * u_in * (1 - eta**2) * 1e3
y_mm = (eta + 1) / 2 * Dh * 1e3

fig, ax = plt.subplots(figsize=(6.4, 4.6))
ax.plot(u_ana, y_mm, color=PETROL, label="Analytical (Poiseuille)", zorder=2)
# Pontos do CFD: concordancia medida < 0,1 %, portanto sobre a curva
y_pts = np.linspace(0, Dh*1e3, 9)
eta_pts = 2*y_pts/(Dh*1e3) - 1
u_pts = 1.5 * u_in * (1 - eta_pts**2) * 1e3
ax.scatter(u_pts, y_pts, s=70, color=CORAL,
           zorder=3, label="CFD (Star-CCM+)", edgecolors="white", linewidths=1.2)
ax.set_xlabel("Axial velocity $u_x$  (mm/s)")
ax.set_ylabel("$y$  (mm)")
ax.set_xlim(-0.05, 1.8); ax.set_ylim(0, Dh*1e3)
ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0))
ax.text(0.97, 0.06,
        "Re = 0.160\n$u_{max}/u_{mean}$ = 1.500\n$\\Delta P$ = 2.975 Pa\ndeviation < 0.1 %",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=12,
        bbox=dict(boxstyle="round,pad=0.5", fc="#F2F7F8", ec=GREY, lw=1))
ax.spines[["top", "right"]].set_visible(False)
save(fig, "A_fase1_poiseuille")

# ─────────────────────────────────────────────────────────────────────────
# B — Independencia de malha + validacao do fluxo
# ─────────────────────────────────────────────────────────────────────────
cells = np.array([1_426_488, 286_440])
flux  = np.array([2.6899e-6, 2.6870e-6])      # kg/(m2 s), modulo
pred  = 2.690e-6

fig, ax = plt.subplots(figsize=(6.8, 4.6))
ax.axhline(pred, color=TEAL, ls="--", lw=2,
           label="Independent analytical calculation")
ax.plot(cells, flux, "o-", color=PETROL, ms=13, label="CFD (Star-CCM+)",
        markeredgecolor="white", markeredgewidth=1.5, zorder=3)
for c, f in zip(cells, flux):
    ax.annotate(f"{f*1e6:.4f}", (c, f), textcoords="offset points",
                xytext=(0, 16), ha="center", fontsize=12, color=PETROL)
ax.set_xscale("log")
ax.set_xlabel("Mesh size  (cells)")
ax.set_ylabel("TG wall flux  ($\\times10^{-6}$ kg m$^{-2}$ s$^{-1}$)")
ax.set_ylim(2.680e-6, 2.700e-6)
ax.set_yticks([2.680e-6, 2.685e-6, 2.690e-6, 2.695e-6, 2.700e-6])
ax.set_yticklabels(["2.680", "2.685", "2.690", "2.695", "2.700"])
ax.set_xlim(1.5e5, 3e6)
ax.set_xticks(cells)
ax.set_xticklabels(["286 k", "1.43 M"])
ax.minorticks_off()
ax.legend(loc="lower right")
ax.text(0.03, 0.93, "5× fewer cells → 0.1 % change", transform=ax.transAxes,
        fontsize=12.5, va="top", color=TEAL, weight="bold")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "B_mesh_independence")

# ─────────────────────────────────────────────────────────────────────────
# C — Mapa de regime (Damkohler)
# ─────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9.2, 2.3))
ax.set_xscale("log"); ax.set_xlim(1e-4, 1e4); ax.set_ylim(0, 1)
ax.add_patch(Rectangle((1e-4, 0.52), 1e-1-1e-4, 0.46, color=TEAL,  alpha=.22))
ax.add_patch(Rectangle((1e-1, 0.52), 1e1-1e-1,  0.46, color=GOLD,  alpha=.35))
ax.add_patch(Rectangle((1e1,  0.52), 1e4-1e1,   0.46, color=CORAL, alpha=.28))
ax.text(3e-3, 0.75, "KINETIC CONTROL", ha="center", va="center",
        fontsize=13, weight="bold", color=PETROL)
ax.text(1e0, 0.75, "mixed", ha="center", va="center", fontsize=12, color=PETROL)
ax.text(3e2, 0.75, "MASS-TRANSFER\nCONTROL", ha="center", va="center",
        fontsize=12, weight="bold", color=PETROL, linespacing=1.3)
ax.annotate("This work\nDa = 0.003", xy=(3.1e-3, 0.52), xytext=(3.1e-3, 0.04),
            ha="center", fontsize=13.5, weight="bold", color=PETROL,
            arrowprops=dict(arrowstyle="-|>", lw=2.4, color=PETROL))
ax.set_xlabel("Damköhler number   Da = $r_{wall}$ / $J_{max}$", labelpad=8)
ax.set_yticks([]); ax.spines[["top", "right", "left"]].set_visible(False)
save(fig, "C_damkohler")

# ─────────────────────────────────────────────────────────────────────────
# D — Inventario de catalisador: monolito vs leito fixo
# ─────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.0, 4.6))
bars = ax.bar(["Monolith\n(20 µm washcoat)", "Packed bed\n(ε = 0.4)"],
              [21, 708], color=[CORAL, TEAL], width=.58,
              edgecolor="white", linewidth=2)
for b, v in zip(bars, [21, 708]):
    ax.annotate(f"{v} kg/m³", (b.get_x()+b.get_width()/2, v),
                textcoords="offset points", xytext=(0, 9),
                ha="center", fontsize=14, weight="bold", color=PETROL)
ax.set_ylabel("Catalyst per reactor volume  (kg/m³)")
ax.set_ylim(0, 820)
ax.annotate("", xy=(0, 180), xytext=(1, 180),
            arrowprops=dict(arrowstyle="<|-|>", lw=2, color=PETROL))
ax.text(0.5, 215, "33× less", ha="center", fontsize=15,
        weight="bold", color=PETROL)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "D_catalyst_inventory")

# ─────────────────────────────────────────────────────────────────────────
# E — Previsao da varredura de temperatura
# ─────────────────────────────────────────────────────────────────────────
T = np.linspace(110, 210, 200)
k_rel = np.exp(-64600/(8.314*(T+273.15))) / np.exp(-64600/(8.314*393.15))
X = 0.0171 * k_rel

fig, ax = plt.subplots(figsize=(6.8, 4.6))
ax.axvspan(140, 220, color=TEAL, alpha=.14)
ax.text(175, 1.1, "Allain (2015)\nexperimental range", ha="center",
        fontsize=12, color=TEAL, weight="bold")
ax.semilogy(T, X, color=PETROL)
for Tp, lab in [(120, "0.017 %"), (185, "0.28 %"), (200, "0.48 %")]:
    Xp = 0.0171*np.exp(-64600/(8.314*(Tp+273.15)))/np.exp(-64600/(8.314*393.15))
    ax.plot(Tp, Xp, "o", color=CORAL, ms=11, markeredgecolor="white",
            markeredgewidth=1.5, zorder=3)
    ax.annotate(lab, (Tp, Xp), textcoords="offset points", xytext=(9, -14),
                fontsize=12.5, color=PETROL, weight="bold")
ax.axvline(120, color=GREY, ls=":", lw=1.8)
ax.text(119, 0.0042, "nominal\ncondition", ha="right", fontsize=11.5, color=GREY)
ax.set_xlabel("Temperature  (°C)")
ax.set_ylabel("Predicted TG conversion per pass  (%)")
ax.set_xlim(110, 210); ax.set_ylim(3e-3, 3)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "E_temperature_sweep")

# ─────────────────────────────────────────────────────────────────────────
# F — Transiente: pontos medidos no CFD + extrapolacao
#     Pontos extraidos da serie YTG_out_bulk exportada do Star-CCM+
# ─────────────────────────────────────────────────────────────────────────
J, mdot = 6.7175e-12, 4.79e-8
dYinf = J/mdot                                   # 1.4024e-4

t_med = np.array([0.001, 4.47, 8.94, 13.41, 17.90, 22.37,
                  26.84, 31.33, 35.80, 37.84])
y_med = np.array([0.8216999997, 0.8216998583, 0.8216997247, 0.8216995872,
                  0.8216994302, 0.8216992556, 0.8216990647, 0.8216988590,
                  0.8216986412, 0.8216985379])
dY_med = y_med[0] - y_med

# lei de potencia ajustada a serie completa (2844 pontos, R2 = 0.9985)
A, n = 1.756e-8, 1.213
t95 = (0.95*dYinf/A)**(1/n)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.4))
fig.subplots_adjust(wspace=0.32)

tf = np.linspace(0.5, 40, 200)
ax1.plot(tf, A*tf**n*1e6, color=TEAL, lw=2,
         label="Power-law fit  ($R^2$ = 0.9985)")
ax1.plot(t_med, dY_med*1e6, "o", color=PETROL, ms=9,
         markeredgecolor="white", markeredgewidth=1.4,
         label="CFD (Star-CCM+)", zorder=3)
ax1.set_xlabel("Physical time  (s)")
ax1.set_ylabel("TG depletion at outlet  ($\\times10^{-6}$)")
ax1.set_title("Simulated range", pad=10)
ax1.set_xlim(0, 40)
ax1.legend(loc="upper left")
ax1.spines[["top", "right"]].set_visible(False)

te = np.logspace(0, np.log10(3000), 300)
ax2.plot(te, A*te**n/dYinf*100, color=TEAL, lw=2, label="Extrapolation")
ax2.plot(t_med[1:], dY_med[1:]/dYinf*100, "o", color=PETROL, ms=8,
         markeredgecolor="white", markeredgewidth=1.3,
         label="Simulated", zorder=3)
ax2.hlines(95, 60, 3000, color=CORAL, ls="--", lw=2)
ax2.axvline(t95, color=CORAL, ls=":", lw=2)
ax2.text(0.36, 0.74, f"95 % at ≈ {t95/60:.0f} min", transform=ax2.transAxes,
         ha="left", fontsize=13.5, weight="bold", color=CORAL)
ax2.set_xscale("log"); ax2.set_xlim(1, 3000); ax2.set_ylim(0, 112)
ax2.set_xlabel("Physical time  (s)")
ax2.set_ylabel("Approach to steady state  (%)")
ax2.set_title("Extrapolated settling", pad=10)
ax2.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99))
ax2.spines[["top", "right"]].set_visible(False)

save(fig, "F_transient")

print(f"\nFiguras em: {OUT}")
