#!/usr/bin/env python3
"""
Figuras de publicação — Fase 2: Transporte de Espécies no Reator Monolítico.
Estilo Chemical Engineering Journal (coluna simples, fonte serifada, 300 DPI).

Probe data exportada do STAR-CCM+ (formato: colunas alternadas posição/valor):
  - Axial:     probe na linha central (y=0.55mm), x de 0 a 50mm (200 pts)
  - Transversal: probe na saída (x=50mm), y de 0 a 1.1mm (100 pts)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
import pathlib, sys

# ─── Paths ───────────────────────────────────────────────────────────────────
UPLOAD_DIR = pathlib.Path("/root/.claude/uploads/d70de078-8943-45fb-b502-4acdf429217f")
OUT_DIR    = pathlib.Path("/home/user/Programacao/biodiesel_monolith_cfd/results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

AXIAL_CSV  = UPLOAD_DIR / "9a9f97b4-Fracao_massica_axial.csv"
OUTLET_CSV = UPLOAD_DIR / "0e389788-Fracao_massica_eixo_y.csv"

# ─── Estilo global (CEJ) ─────────────────────────────────────────────────────
mpl.rcParams.update({
    "font.family":        "serif",
    "font.serif":         ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset":   "stix",
    "font.size":          9,
    "axes.labelsize":     9,
    "axes.titlesize":     9,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.fontsize":    7.5,
    "legend.frameon":     True,
    "legend.framealpha":  0.90,
    "legend.edgecolor":   "0.75",
    "legend.handlelength": 2.5,
    "lines.linewidth":    1.3,
    "axes.linewidth":     0.7,
    "xtick.major.width":  0.7,
    "ytick.major.width":  0.7,
    "xtick.minor.width":  0.4,
    "ytick.minor.width":  0.4,
    "xtick.direction":    "in",
    "ytick.direction":    "in",
    "xtick.major.size":   4.0,
    "ytick.major.size":   4.0,
    "xtick.minor.size":   2.0,
    "ytick.minor.size":   2.0,
    "xtick.top":          True,
    "ytick.right":        True,
    "figure.dpi":         150,          # screen preview
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "savefig.pad_inches": 0.04,
})

# ─── Paleta de cores (Wong, 2011 — acessível para daltônicos) ─────────────────
C = {
    "TG":   "#0072B2",   # azul
    "MeOH": "#E69F00",   # âmbar
    "DG":   "#009E73",   # verde
    "MG":   "#D55E00",   # vermelho-laranja
    "FAME": "#CC79A7",   # rosa
    "GL":   "#56B4E9",   # azul-claro
}
LS = {
    "TG":   "-",
    "MeOH": "--",
    "DG":   "-.",
    "MG":   (0, (3, 1, 1, 1, 1, 1)),   # traço-ponto-ponto
    "FAME": (0, (5, 1)),                # traço longo
    "GL":   ":",
}

# ─── Constantes físicas ───────────────────────────────────────────────────────
Dh       = 1.1e-3   # diâmetro hidráulico [m]
L        = 50e-3    # comprimento do canal [m]
Y_TG_0   = 0.8217   # fração mássica TG na alimentação
Y_OH_0   = 0.1783   # fração mássica MeOH na alimentação

SPECIES_ORDER = ["DG", "FAME", "GL", "MeOH", "MG", "TG"]


# ─── Parser ──────────────────────────────────────────────────────────────────
def parse_starccm(filepath, species_order):
    """
    STAR-CCM+ exporta colunas alternadas: (pos, Y_sp1, pos, Y_sp2, ...).
    Retorna dict: {sp: (pos_array_sorted, val_array_sorted)}.
    """
    df = pd.read_csv(filepath, header=0)
    data = {}
    for i, sp in enumerate(species_order):
        pos  = df.iloc[:, 2*i].values.astype(float)
        vals = df.iloc[:, 2*i+1].values.astype(float)
        idx  = np.argsort(pos)
        data[sp] = (pos[idx], vals[idx])
    return data


axial  = parse_starccm(AXIAL_CSV,  SPECIES_ORDER)
outlet = parse_starccm(OUTLET_CSV, SPECIES_ORDER)


# ═══════════════════════════════════════════════════════════════════════════════
#  FIGURA 1 — Perfil transversal na saída (x = 50 mm)
#  Dois painéis: (a) perfil completo  |  (b) detalhe camada catalítica
#  Largura: 180 mm (dupla coluna CEJ) = 7.087 inch
# ═══════════════════════════════════════════════════════════════════════════════
FIG1_W, FIG1_H = 7.087, 3.5

fig1, (ax1a, ax1b) = plt.subplots(
    1, 2, figsize=(FIG1_W, FIG1_H),
    gridspec_kw={"width_ratios": [1, 1], "wspace": 0.38}
)

# Máscara: exclui artefato de refluxo na parede inferior (y < 0.15 mm)
YMASK = 1.5e-4
YZOOM = 0.956   # início do zoom (y/Dh)

# ── Painel (a): perfil completo — apenas TG e MeOH ───────────────────────────
for sp in ("TG", "MeOH"):
    y_m, val = outlet[sp]
    mask     = y_m >= YMASK
    ax1a.plot(val[mask], y_m[mask] / Dh,
              color=C[sp], ls=LS[sp], lw=1.5,
              label=rf"$Y_{{\mathrm{{{sp}}}}}$")

# Referências de alimentação
ax1a.axvline(Y_TG_0, color=C["TG"],   ls=":", lw=0.8, alpha=0.55)
ax1a.axvline(Y_OH_0, color=C["MeOH"], ls=":", lw=0.8, alpha=0.55)
ax1a.text(Y_TG_0 + 0.01, 0.06, r"$Y_{TG}^{0}$",
          fontsize=7, color=C["TG"], va="bottom")
ax1a.text(Y_OH_0 + 0.01, 0.06, r"$Y_{MeOH}^{0}$",
          fontsize=7, color=C["MeOH"], va="bottom")

# Destaque zona catalítica
ax1a.axhspan(YZOOM, 1.005, color="0.92", zorder=0)
ax1a.text(0.50, (YZOOM + 1.0) / 2,
          "Detalhe\nem (b)", fontsize=7, ha="center", va="center",
          color="0.4", style="italic")

ax1a.set_xlabel(r"Fração mássica, $Y_i\;[-]$")
ax1a.set_ylabel(r"$y/D_h\;[-]$")
ax1a.set_xlim(0.0, 1.0)
ax1a.set_ylim(0.0, 1.02)
ax1a.xaxis.set_minor_locator(AutoMinorLocator(5))
ax1a.yaxis.set_minor_locator(AutoMinorLocator(5))
ax1a.legend(loc="center", bbox_to_anchor=(0.5, 0.45), ncol=1)
ax1a.set_title(r"(a) Perfil completo — $x/L = 1$", fontsize=9, pad=4)

# ── Painel (b): detalhe camada catalítica ─────────────────────────────────────
SP_ZOOM = ["TG", "MeOH", "DG"]
LW_ZOOM = {"TG": 1.5, "MeOH": 1.5, "DG": 1.2}

for sp in SP_ZOOM:
    y_m, val = outlet[sp]
    y_dim    = y_m / Dh
    mask     = y_dim >= YZOOM
    ax1b.plot(val[mask], y_dim[mask],
              color=C[sp], ls=LS[sp], lw=LW_ZOOM[sp],
              label=rf"$Y_{{\mathrm{{{sp}}}}}$")

# Anotação: espessura da camada limite de concentração
# δ_c ≈ 37 µm (onde TG começa a cair, verificado nos dados)
delta_c = 37e-6   # m
y_delta = (Dh - delta_c) / Dh  # y/Dh onde começa a depleção
ax1b.annotate(
    "", xy=(0.82, 1.0), xytext=(0.82, y_delta),
    arrowprops=dict(arrowstyle="<->", lw=0.9, color="0.3")
)
ax1b.text(0.85, (1.0 + y_delta) / 2,
          r"$\delta_c \approx 37\,\mu\mathrm{m}$",
          fontsize=7, color="0.3", va="center")

ax1b.set_xlabel(r"Fração mássica, $Y_i\;[-]$")
ax1b.set_ylabel(r"$y/D_h\;[-]$")
ax1b.set_xlim(0.0, 1.0)
ax1b.set_ylim(YZOOM, 1.005)
ax1b.xaxis.set_minor_locator(AutoMinorLocator(5))
ax1b.yaxis.set_minor_locator(AutoMinorLocator(4))
ax1b.legend(loc="lower left", ncol=1)
ax1b.set_title(r"(b) Camada catalítica (Top\_Wall)", fontsize=9, pad=4)

# Nota de rodapé da figura
fig1.text(0.01, -0.02,
          r"Nota: y/D_h < 0.14 excluído (artefato de refluxo na saída). "
          r"Condição: T = 120 °C, P = 8 bar, razão molar MeOH:TG = 6:1.",
          fontsize=6.5, color="0.5", va="top")

fig1.tight_layout(pad=0.5)
for ext in ("pdf", "png"):
    fig1.savefig(OUT_DIR / f"fig1_perfil_transversal.{ext}")
print(f"\nFig 1 → {OUT_DIR}/fig1_perfil_transversal.[pdf|png]")


# ═══════════════════════════════════════════════════════════════════════════════
#  FIGURA 2 — Perfil axial na linha central (y = 0.55 mm)
# ═══════════════════════════════════════════════════════════════════════════════
# Exclui: x < 1 mm (zona de entrada) e x > 47.5 mm (refluxo na saída)
FIG2_W, FIG2_H = 3.465, 3.2

fig2, ax2 = plt.subplots(figsize=(FIG2_W, FIG2_H))

SP_AXIAL = ["TG", "MeOH", "DG", "FAME"]

for sp in SP_AXIAL:
    x_m, val = axial[sp]
    x_mm     = x_m * 1e3
    mask     = (x_m >= 1.0e-3) & (x_m <= 47.5e-3)
    lw       = 1.5 if sp in ("TG", "MeOH") else 1.1
    ax2.plot(x_mm[mask], val[mask],
             color=C[sp], ls=LS[sp], lw=lw,
             label=rf"$Y_{{\mathrm{{{sp}}}}}$")

# Referências de alimentação: linhas pontilhadas com label à esquerda
ax2.axhline(Y_TG_0,  color=C["TG"],   ls=":", lw=0.8, alpha=0.50, zorder=1)
ax2.axhline(Y_OH_0,  color=C["MeOH"], ls=":", lw=0.8, alpha=0.50, zorder=1)
ax2.text(1.5, Y_TG_0 + 0.015,  r"$Y_{TG}^{\,0}=0.822$",
         fontsize=7, color=C["TG"],   va="bottom")
ax2.text(1.5, Y_OH_0 + 0.015,  r"$Y_{MeOH}^{\,0}=0.178$",
         fontsize=7, color=C["MeOH"], va="bottom")

ax2.set_xlabel(r"Posição axial, $x\;[\mathrm{mm}]$")
ax2.set_ylabel(r"Fração mássica, $Y_i\;[-]$")
ax2.set_xlim(0, 50)
ax2.set_ylim(0.0, 1.0)
ax2.xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
ax2.xaxis.set_minor_locator(AutoMinorLocator(5))
ax2.yaxis.set_minor_locator(AutoMinorLocator(5))

# Legenda no espaço vazio central (entre as curvas de TG e MeOH)
ax2.legend(loc="center", bbox_to_anchor=(0.55, 0.50), ncol=1,
           handlelength=2.2, handletextpad=0.5)

fig2.tight_layout(pad=0.5)
for ext in ("pdf", "png"):
    fig2.savefig(OUT_DIR / f"fig2_perfil_axial.{ext}")
print(f"Fig 2 → {OUT_DIR}/fig2_perfil_axial.[pdf|png]")


# ═══════════════════════════════════════════════════════════════════════════════
#  FIGURA 3 (opcional) — Intermediários: perfil axial escala logarítmica
# ═══════════════════════════════════════════════════════════════════════════════
FIG3_W, FIG3_H = 3.465, 2.8

fig3, ax3 = plt.subplots(figsize=(FIG3_W, FIG3_H))

SP_INTER = ["DG", "MG", "FAME", "GL"]
label_map = {"DG":"DG","MG":"MG","FAME":"FAME","GL":"GL"}

for sp in SP_INTER:
    x_m, val = axial[sp]
    x_mm     = x_m * 1e3
    mask     = (x_m >= 1.0e-3) & (x_m <= 47.5e-3)
    val_plot = np.clip(val[mask], 1e-12, None)   # evita log(0)
    ax3.semilogy(x_mm[mask], val_plot,
                 color=C[sp], ls=LS[sp], lw=1.2,
                 label=rf"$Y_{{\mathrm{{{label_map[sp]}}}}}$")

ax3.set_xlabel(r"Posição axial, $x\;[\mathrm{mm}]$")
ax3.set_ylabel(r"Fração mássica, $Y_i\;[\!-\!]$")
ax3.set_xlim(0, 50)
ax3.set_ylim(1e-12, 1.0)
ax3.xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
ax3.xaxis.set_minor_locator(AutoMinorLocator(5))
ax3.legend(loc="upper left", ncol=1)

fig3.tight_layout(pad=0.5)
for ext in ("pdf", "png"):
    fig3.savefig(OUT_DIR / f"fig3_intermediarios_axial.{ext}")
print(f"Fig 3 → {OUT_DIR}/fig3_intermediarios_axial.[pdf|png]")

plt.show()
print("\nConcluído.")
