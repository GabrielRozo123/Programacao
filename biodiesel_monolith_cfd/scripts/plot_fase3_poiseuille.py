#!/usr/bin/env python3
"""
Figura do Capitulo 3 — verificacao hidrodinamica da Fase 3.

(a) perfil transversal de velocidade axial medido em x = 49 mm, sobreposto a
    solucao analitica de Poiseuille plano
(b) zoom na regiao de parede, mostrando a resolucao das camadas prismaticas

Entrada: results/perfil_velocidade_x49mm_raw.csv  (Line Probe, Direction [0,1,0])
Saida  : results/fig6_poiseuille_fase3.{pdf,png}
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "results" / "perfil_velocidade_x49mm_raw.csv"
SAIDA = RAIZ / "results" / "fig6_poiseuille_fase3"

AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA2, TINTA3 = "#0b0b0b", "#52514e", "#8a8984"
H, UB, RHO, W = 1.1e-3, 1.0e-3, 868.0, 5e-5
VIRGULA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def carregar():
    d = np.genfromtxt(ENTRADA, delimiter=",", skip_header=1)
    y, u = d[:, 0], d[:, 1]
    corte = np.flatnonzero(np.diff(u) != 0) + 1          # colapsa valores de celula
    g = np.split(np.arange(len(u)), corte)
    return (np.array([y[k].mean() for k in g]),
            np.array([u[k[0]] for k in g]))


def estilo(ax):
    ax.grid(True, color=TINTA3, alpha=0.22, linewidth=0.6)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA3)
        ax.spines[lado].set_linewidth(0.8)
    ax.tick_params(colors=TINTA2, labelsize=9, length=3, width=0.8)
    ax.xaxis.set_major_formatter(VIRGULA)
    ax.yaxis.set_major_formatter(VIRGULA)


def main():
    y, u = carregar()
    yf = np.linspace(0, H, 400)
    uf = 6 * UB * (yf / H) * (1 - yf / H)
    umed = np.trapezoid(u, y) / H
    mdot = RHO * umed * H * W

    fig, a = plt.subplots(1, 1, figsize=(6.4, 5.7))
    fig.patch.set_facecolor("#fcfcfb")
    a.set_facecolor("#fcfcfb")
    estilo(a)

    # ---- (a) perfil completo ----------------------------------------------
    a.plot(uf * 1e3, yf * 1e3, color=AZUL, linewidth=2.0, zorder=2,
           label="Poiseuille analítico")
    a.plot(u * 1e3, y * 1e3, "o", color=LARANJA, markersize=5.0, zorder=3,
           markeredgecolor="#fcfcfb", markeredgewidth=0.9, label="CFD (Star-CCM+)")
    a.set_xlim(0, 1.72)
    a.set_ylim(0, H * 1e3)
    a.set_xlabel("velocidade axial  $u_x$  [mm s$^{-1}$]", fontsize=9.5, color=TINTA2)
    a.set_ylabel("$y$  [mm]", fontsize=9.5, color=TINTA2)
    a.set_title("perfil em $x = 49$ mm", fontsize=10.5, color=TINTA,
                loc="left", pad=9)
    leg = a.legend(loc="upper right", fontsize=8.5, frameon=True,
                   facecolor="#fcfcfb", edgecolor=TINTA3)
    leg.get_frame().set_linewidth(0.6)
    for t in leg.get_texts():
        t.set_color(TINTA2)
    caixa = (f"$u_{{máx}}$   {u.max()*1e3:.4f} mm/s  (analítico {1.5*UB*1e3:.4f};  "
             f"{(u.max()/(1.5*UB)-1)*100:+.3f} %)\n"
             f"$\\bar{{u}}$      {umed*1e3:.4f} mm/s  (imposto {UB*1e3:.4f};  "
             f"{(umed/UB-1)*100:+.3f} %)\n"
             f"$\\dot{{m}}$      {mdot:.4e} kg/s  (solver 4.774e-08;  "
             f"{(mdot/4.774e-8-1)*100:+.3f} %)")
    fig.text(0.035, 0.015, caixa.replace(".", ","), fontsize=8.2, color=TINTA2,
             va="bottom", ha="left", linespacing=1.75)

    fig.suptitle("Verificação hidrodinâmica do canal monolítico",
                 fontsize=12, color=TINTA, x=0.03, ha="left", y=0.975)
    fig.text(0.03, 0.918,
             "Star-CCM+,   $Re = 0{,}182$,   "
             "perfil $u(y) = 6\\,\\bar{u}\\,(y/H)(1-y/H)$",
             fontsize=8.8, color=TINTA2, ha="left")

    fig.tight_layout(rect=(0.0, 0.135, 1.0, 0.90))
    for ext in ("pdf", "png"):
        fig.savefig(f"{SAIDA}.{ext}", dpi=200, facecolor=fig.get_facecolor())
    print(f"gravado: {SAIDA}.pdf / .png")
    print(f"  celulas na linha      {len(u)}")
    print(f"  u_max  {u.max():.6e}  ({(u.max()/(1.5*UB)-1)*100:+.3f} %)")
    print(f"  u_med  {umed:.6e}  ({(umed/UB-1)*100:+.3f} %)")
    print(f"  mdot   {mdot:.4e}  ({(mdot/4.774e-8-1)*100:+.3f} %)")


if __name__ == "__main__":
    main()
