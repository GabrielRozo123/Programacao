#!/usr/bin/env python3
"""
Figura do Capitulo 1 — resistencia difusional interna ao washcoat.

(a) fator de efetividade eta = tanh(phi)/phi
(b) taxa observada relativa, r_obs/r_max = tanh(phi), em funcao da espessura

A taxa observada por area de parede vale

    r_obs = eta * k_v * delta * C = C * sqrt(k_v * D_p) * tanh(phi)

ou seja, SATURA em C*sqrt(k_v*D_p); nao passa por maximo. O painel (b) mostra
onde esta o joelho da curva e quanto se ganha ao engrossar a camada.

Calibracao: phi = 1,44 para delta = 10 um  ->  sqrt(k_v/D_p) = 1,44e5 1/m

Saida: results/fig5_thiele_washcoat.{pdf,png}
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "results" / "fig5_thiele_washcoat"

AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA2, TINTA3 = "#0b0b0b", "#52514e", "#8a8984"

PHI_REF, DELTA_REF = 1.44, 10.0          # modulo de Thiele e espessura de referencia
BETA = PHI_REF / DELTA_REF               # phi por micrometro
VIRGULA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


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
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.2, 4.3))
    fig.patch.set_facecolor("#fcfcfb")
    for ax in (a, b):
        ax.set_facecolor("#fcfcfb")
        estilo(ax)

    # ---- (a) fator de efetividade -----------------------------------------
    phi = np.logspace(-1, 1.1, 400)
    eta = np.tanh(phi) / phi
    a.semilogx(phi, eta, color=AZUL, linewidth=2.0, solid_capstyle="round")
    a.plot([PHI_REF], [np.tanh(PHI_REF) / PHI_REF], "o", color=AZUL, markersize=6.5,
           markeredgecolor="#fcfcfb", markeredgewidth=1.5, zorder=5)
    a.set_xlim(0.1, 12)
    a.set_ylim(0, 1.05)
    a.set_xlabel("módulo de Thiele  $\\phi$", fontsize=9.5, color=TINTA2)
    a.set_ylabel("fator de efetividade  $\\eta$", fontsize=9.5, color=TINTA2)
    a.set_title("(a)  aproveitamento do catalisador", fontsize=10.5,
                color=TINTA, loc="left", pad=9)
    a.annotate("$\\phi = 1{,}44$\n$\\eta = 0{,}62$",
               xy=(PHI_REF, np.tanh(PHI_REF) / PHI_REF), xytext=(2.4, 0.74),
               fontsize=9, color=TINTA2, va="center",
               arrowprops=dict(arrowstyle="-", color=TINTA3, linewidth=0.8,
                               shrinkA=3, shrinkB=5))
    a.text(0.13, 0.13, "$\\delta_{wc} = 10$ µm", fontsize=8.5, color=TINTA3)

    # ---- (b) saturacao da taxa observada ----------------------------------
    d = np.linspace(0.2, 30, 500)
    r = np.tanh(BETA * d)
    b.plot(d, r, color=LARANJA, linewidth=2.0, solid_capstyle="round")
    b.axhline(1.0, color=TINTA3, linewidth=1.0, linestyle=(0, (4, 3)))
    for dd, cor in [(10.0, LARANJA), (15.0, TINTA3)]:
        b.plot([dd], [np.tanh(BETA * dd)], "o", color=cor, markersize=6.5,
               markeredgecolor="#fcfcfb", markeredgewidth=1.5, zorder=5)
    b.set_xlim(0, 30)
    b.set_ylim(0, 1.12)
    b.set_xlabel("espessura do washcoat  $\\delta_{wc}$  [µm]",
                 fontsize=9.5, color=TINTA2)
    b.set_ylabel("taxa observada  $r_{obs}/r_{max}$", fontsize=9.5, color=TINTA2)
    b.set_title("(b)  retorno de engrossar a camada", fontsize=10.5,
                color=TINTA, loc="left", pad=9)
    b.text(16.2, 1.045, "assíntota  $C\\,\\sqrt{k_v D_p}$",
           fontsize=8.5, color=TINTA2)
    b.annotate(f"10 µm → {np.tanh(BETA*10)*100:.0f} %",
               xy=(10, np.tanh(BETA * 10)), xytext=(1.5, 0.93),
               fontsize=9, color=TINTA2, va="center",
               arrowprops=dict(arrowstyle="-", color=TINTA3, linewidth=0.8,
                               shrinkA=3, shrinkB=5))
    b.annotate(f"15 µm → {np.tanh(BETA*15)*100:.0f} %",
               xy=(15, np.tanh(BETA * 15)), xytext=(17.2, 0.55),
               fontsize=9, color=TINTA2, va="center",
               arrowprops=dict(arrowstyle="-", color=TINTA3, linewidth=0.8,
                               shrinkA=3, shrinkB=5))

    fig.suptitle("Resistência difusional interna ao washcoat de CaO",
                 fontsize=12.5, color=TINTA, x=0.055, ha="left", y=0.975)
    fig.text(0.055, 0.905,
             "$\\phi = \\delta_{wc}\\sqrt{k_v/D_p}$ · "
             "$\\eta = \\tanh\\phi/\\phi$ · "
             "$D_p$ de Fonseca (2026) para CaO e CaO/Al$_2$O$_3$",
             fontsize=9, color=TINTA2, ha="left")

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.865))
    for ext in ("pdf", "png"):
        fig.savefig(f"{SAIDA}.{ext}", dpi=200, facecolor=fig.get_facecolor())

    print(f"gravado: {SAIDA}.pdf / .png")
    for dd in (5, 10, 15, 20, 25):
        p = BETA * dd
        print(f"  delta = {dd:2d} um   phi = {p:.2f}   eta = {np.tanh(p)/p:.3f}"
              f"   r_obs/r_max = {np.tanh(p)*100:5.1f} %")


if __name__ == "__main__":
    main()
