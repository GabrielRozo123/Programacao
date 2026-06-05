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

# ─── Verificação rápida ───────────────────────────────────────────────────────
for sp in SPECIES_ORDER:
    x0, v0 = axial[sp]
    print(f"  Axial  {sp}: x=[{x0[0]*1e3:.2f},{x0[-1]*1e3:.2f}] mm  "
          f"Y=[{v0[0]:.4f},{v0[-1]:.4f}]")
print()
for sp in SPECIES_ORDER:
    y0, v0 = outlet[sp]
    print(f"  Outlet {sp}: y=[{y0[0]*1e3:.3f},{y0[-1]*1e3:.3f}] mm  "
          f"Y=[{v0[0]:.4f},{v0[-1]:.4f}]")


# ═══════════════════════════════════════════════════════════════════════════════
#  FIGURA 1 — Perfil transversal na saída (x = 50 mm)
# ═══════════════════════════════════════════════════════════════════════════════
# Largura: 88 mm (coluna simples CEJ) = 3.465 inch
FIG1_W, FIG1_H = 3.465, 4.0

fig1, ax1 = plt.subplots(figsize=(FIG1_W, FIG1_H))

SP_OUTLET = ["TG", "MeOH", "DG", "MG", "FAME"]

for sp in SP_OUTLET:
    y_m, val = outlet[sp]
    y_dim    = y_m / Dh   # adimensional y/Dh

    # Exclui artefato de refluxo na parede inferior (y < 0.15 mm)
    mask = y_m >= 1.5e-4
    lw   = 1.5 if sp in ("TG", "MeOH") else 1.1

    ax1.plot(val[mask], y_dim[mask],
             color=C[sp], ls=LS[sp], lw=lw,
             label=rf"$Y_{{\mathrm{{{sp}}}}}$")

# Linha de referência: composição de alimentação
ax1.axvline(Y_TG_0, color=C["TG"],   ls=":", lw=0.7, alpha=0.5)
ax1.axvline(Y_OH_0, color=C["MeOH"], ls=":", lw=0.7, alpha=0.5)

ax1.set_xlabel(r"Fração mássica, $Y_i\;[\!-\!]$")
ax1.set_ylabel(r"$y/D_h\;[\!-\!]$")
ax1.set_xlim(-0.01, 1.05)
ax1.set_ylim(0.0, 1.02)
ax1.xaxis.set_minor_locator(AutoMinorLocator(5))
ax1.yaxis.set_minor_locator(AutoMinorLocator(5))
ax1.legend(loc="lower right", ncol=1)

# Anotações
ax1.text(0.90, 0.995, "Top\_Wall\n(catalisador)",
         ha="center", va="top", fontsize=7, style="italic",
         transform=ax1.get_xaxis_transform(), clip_on=False)
ax1.annotate("", xy=(0.0, 1.0), xytext=(-0.01, 0.94),
             xycoords=("data", "axes fraction"),
             textcoords=("data", "axes fraction"),
             arrowprops=dict(arrowstyle="->", lw=0.7))

ax1.text(0.02, 0.01, r"$\star$ artefato refluxo (excluído)",
         fontsize=6, color="0.5", transform=ax1.transAxes)

# ── Inset: zoom na camada catalítica (y/Dh > 0.95) ───────────────────────────
ax_ins = inset_axes(ax1, width="52%", height="30%",
                    loc="upper left",
                    bbox_to_anchor=(0.03, 0.06, 1, 1),
                    bbox_transform=ax1.transAxes,
                    borderpad=0)

YZOOM = 0.93
for sp in SP_OUTLET:
    y_m, val = outlet[sp]
    y_dim    = y_m / Dh
    mask     = y_dim >= YZOOM
    lw       = 1.4 if sp in ("TG", "MeOH") else 1.0
    ax_ins.plot(val[mask], y_dim[mask],
                color=C[sp], ls=LS[sp], lw=lw)

ax_ins.set_xlim(-0.01, 1.05)
ax_ins.set_ylim(YZOOM, 1.005)
ax_ins.set_xlabel(r"$Y_i$", fontsize=7, labelpad=1)
ax_ins.set_ylabel(r"$y/D_h$", fontsize=7, labelpad=2)
ax_ins.tick_params(labelsize=6)
ax_ins.xaxis.set_minor_locator(AutoMinorLocator(2))
ax_ins.yaxis.set_minor_locator(AutoMinorLocator(2))
ax_ins.set_title("Detalhe: camada catalisador", fontsize=6.5, pad=2)
mark_inset(ax1, ax_ins, loc1=1, loc2=3, fc="none", ec="0.5", lw=0.6)

fig1.tight_layout(pad=0.5)
for ext in ("pdf", "png"):
    fig1.savefig(OUT_DIR / f"fig1_perfil_transversal.{ext}")
print(f"\nFig 1 → {OUT_DIR}/fig1_perfil_transversal.[pdf|png]")


# ═══════════════════════════════════════════════════════════════════════════════
#  FIGURA 2 — Perfil axial na linha central (y = 0.55 mm)
# ═══════════════════════════════════════════════════════════════════════════════
# Notas sobre o dado:
#   x=0:        TG=0.880 (provável artefato BC de entrada – esperado 0.8217)
#   x~49mm:     pico de DG/FAME por refluxo na saída → excluir x > 47.5 mm
#   x=50mm:     composição de alimentação (backflow BC) → excluir
FIG2_W, FIG2_H = 3.465, 3.2

fig2, ax2 = plt.subplots(figsize=(FIG2_W, FIG2_H))

SP_AXIAL = ["TG", "MeOH", "DG", "FAME"]

for sp in SP_AXIAL:
    x_m, val = axial[sp]
    x_mm     = x_m * 1e3
    # Exclui: x<1mm (artefato entrada) e x>47.5mm (refluxo saída)
    mask     = (x_m >= 1.0e-3) & (x_m <= 47.5e-3)
    lw       = 1.5 if sp in ("TG", "MeOH") else 1.0
    ax2.plot(x_mm[mask], val[mask],
             color=C[sp], ls=LS[sp], lw=lw,
             label=rf"$Y_{{\mathrm{{{sp}}}}}$")

# Referências: composição de alimentação
ax2.axhline(Y_TG_0, color=C["TG"],   ls=":", lw=0.7, alpha=0.45, zorder=1)
ax2.axhline(Y_OH_0, color=C["MeOH"], ls=":", lw=0.7, alpha=0.45, zorder=1)
ax2.text(48.5, Y_TG_0 + 0.008, r"$Y_{TG}^{0}$",
         fontsize=7, color=C["TG"], ha="right", va="bottom")
ax2.text(48.5, Y_OH_0 + 0.008, r"$Y_{MeOH}^{0}$",
         fontsize=7, color=C["MeOH"], ha="right", va="bottom")

ax2.set_xlabel(r"Posição axial, $x\;[\mathrm{mm}]$")
ax2.set_ylabel(r"Fração mássica, $Y_i\;[\!-\!]$")
ax2.set_xlim(0, 50)
ax2.set_ylim(-0.01, 1.01)
ax2.xaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
ax2.xaxis.set_minor_locator(AutoMinorLocator(5))
ax2.yaxis.set_minor_locator(AutoMinorLocator(5))
ax2.legend(loc="center right", ncol=1)

# Anotação: conversão observada de TG
x_tg, v_tg = axial["TG"]
mask_bulk   = (x_tg >= 1e-3) & (x_tg <= 47.5e-3)
v_in  = v_tg[mask_bulk][0]
v_out = v_tg[mask_bulk][-1]
x_mid = (x_tg[mask_bulk][0] + x_tg[mask_bulk][-1]) * 0.5 * 1e3
conv  = (v_in - v_out) / v_in * 100
ax2.annotate(rf"$\Delta Y_{{TG}} \approx {v_in-v_out:.3f}$" + "\n"
             rf"$X_{{TG}} \approx {conv:.1f}\%$ (linha central)",
             xy=(x_tg[mask_bulk][-1]*1e3, v_out),
             xytext=(20, 0.60),
             fontsize=7,
             arrowprops=dict(arrowstyle="->", lw=0.7,
                             connectionstyle="arc3,rad=0.2"))

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
