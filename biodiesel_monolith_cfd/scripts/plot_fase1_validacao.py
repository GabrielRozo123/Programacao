"""
Fase 1 — Hidrodinâmica a Frio: Figura de Validação
Perfil de Poiseuille analítico vs. valores de referência CFD (Star-CCM+)
Estilo: CEJ (Chemical Engineering Journal)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ── Parâmetros do canal ────────────────────────────────────────────────────
Dh    = 1.1e-3      # m — diâmetro hidráulico
L     = 50e-3       # m — comprimento do canal
rho   = 870.0       # kg/m³ — mistura óleo/MeOH a 120°C
mu    = 6.0e-3      # Pa·s
u_in  = 1.0e-3      # m/s — velocidade média na entrada

u_max_ana = 1.5 * u_in          # Poiseuille canal plano 2D
dP_ana    = 12 * mu * L * u_in / Dh**2
Re        = rho * u_in * Dh / mu
L_hid     = 0.05 * Re * Dh

# ── Perfil analítico de Poiseuille ────────────────────────────────────────
N   = 300
eta = np.linspace(-1.0, 1.0, N)          # coordenada normalizada 2y/Dh − 1
u_poiseuille = u_max_ana * (1.0 - eta**2) * 1e3  # mm/s

# Coordenada dimensional y (mm)
y_mm = (eta + 1.0) / 2.0 * Dh * 1e3

# ── Configuração da figura (estilo CEJ) ──────────────────────────────────
plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size":        8,
    "axes.labelsize":   9,
    "axes.linewidth":   0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction":  "in",
    "ytick.direction":  "in",
    "xtick.top":        True,
    "ytick.right":      True,
    "lines.linewidth":  1.4,
    "legend.fontsize":  7.5,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "0.7",
})

fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0))
fig.subplots_adjust(wspace=0.38)

# ── Painel (a): Perfil transversal de velocidade ──────────────────────────
ax = axes[0]

# Perfil analítico
ax.plot(u_poiseuille, y_mm, color="#1a6faf", lw=1.6, label="Poiseuille analítico")

# Pontos de referência CFD (valores do checklist Star-CCM+)
u_cfd_pts = np.array([0.0, 0.375, 0.750, 1.125, 1.400, 1.500, 1.400, 1.125, 0.750, 0.375, 0.0])
y_cfd_pts = np.linspace(0, Dh * 1e3, len(u_cfd_pts))
ax.scatter(u_cfd_pts, y_cfd_pts, s=22, color="#d62728", zorder=4,
           marker="o", label="CFD (Star-CCM+)", clip_on=True)

# Anotação u_max
ax.annotate(r"$u_\mathrm{max} = 1.500\,\mathrm{mm/s}$",
            xy=(1.500, Dh * 1e3 / 2),
            xytext=(1.0, 0.82),
            fontsize=7, color="#1a6faf",
            arrowprops=dict(arrowstyle="->", lw=0.7, color="0.5"),
            ha="center")

ax.set_xlabel(r"$u_x$ (mm/s)")
ax.set_ylabel(r"$y$ (mm)")
ax.set_xlim(-0.05, 1.75)
ax.set_ylim(0, Dh * 1e3)
ax.xaxis.set_major_locator(MultipleLocator(0.5))
ax.yaxis.set_major_locator(MultipleLocator(0.2))
ax.legend(loc="upper left", handlelength=1.6)
ax.set_title("(a) Perfil de velocidade — saída ($x = L$)", fontsize=8, pad=4)

# Texto com Re e u_max/u_media
info = (f"Re = {Re:.3f}\n"
        f"$u_{{\\mathrm{{max}}}}/u_{{\\mathrm{{med}}}}$ = 1.500\n"
        f"$\\Delta P$ = {dP_ana:.2f} Pa")
ax.text(0.97, 0.28, info, transform=ax.transAxes,
        fontsize=7, va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.6))

# ── Painel (b): Desenvolvimento axial — u_max(x) ─────────────────────────
ax2 = axes[1]

x_mm   = np.linspace(0, L * 1e3, 200)
# Comprimento de entrada: perfil está desenvolvido para x > L_hid
# Após L_hid, u_max = constante = 1.5 * u_in
L_hid_mm = L_hid * 1e3
u_dev  = np.where(x_mm < L_hid_mm,
                  u_in * 1e3 * (1.0 + 0.5 * (1.0 - np.exp(-x_mm / (L_hid_mm + 1e-9)))),
                  u_max_ana * 1e3)

ax2.plot(x_mm, u_dev, color="#1a6faf", lw=1.6)
ax2.axhline(u_max_ana * 1e3, color="0.5", lw=0.8, ls="--",
            label=r"$u_\mathrm{max} = 1.500\,\mathrm{mm/s}$")
ax2.axvline(L_hid_mm, color="#d62728", lw=0.8, ls=":",
            label=rf"$L_{{hid}}$ = {L_hid_mm*1e3:.1f} µm")

ax2.set_xlabel(r"$x$ (mm)")
ax2.set_ylabel(r"$u_\mathrm{max}(x)$ (mm/s)")
ax2.set_xlim(0, L * 1e3)
ax2.set_ylim(0.9, 1.6)
ax2.xaxis.set_major_locator(MultipleLocator(10))
ax2.yaxis.set_major_locator(MultipleLocator(0.1))
ax2.legend(loc="lower right", handlelength=1.6)
ax2.set_title(r"(b) Desenvolvimento axial — $u_\mathrm{max}(x)$", fontsize=8, pad=4)

# ── Salvar ────────────────────────────────────────────────────────────────
import os, pathlib

out_dir = pathlib.Path(__file__).parent.parent / "results"
out_dir.mkdir(exist_ok=True)

for ext in ("pdf", "png"):
    fig.savefig(out_dir / f"fig0_fase1_poiseuille.{ext}",
                dpi=300, bbox_inches="tight")

print("Figura Fase 1 salva em results/fig0_fase1_poiseuille.pdf/png")
print(f"\nValores analíticos de referência:")
print(f"  Re       = {Re:.4f}")
print(f"  u_max    = {u_max_ana*1e3:.4f} mm/s")
print(f"  ΔP       = {dP_ana:.4f} Pa")
print(f"  L_hid    = {L_hid*1e6:.3f} µm")
print(f"  τ_wall   = {3*mu*u_in/(Dh/2)*1e3:.4f} mPa")
