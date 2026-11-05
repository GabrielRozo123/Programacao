"""
sensibilidade_diametro.py
=========================
Mostra por que o diâmetro de bolha (Interaction Length Scale no STAR-CCM+)
controla a retenção gasosa de um caso Euler–Euler monodisperso.

Velocidade terminal pelo arrasto de Tomiyama (sistema contaminado):
    C_D = max[ 24/Re (1 + 0,15 Re^0,687) ,  (8/3) Eo/(Eo + 4) ]
    U∞  = √( 4 g d Δρ / (3 ρL C_D) )
Retenção em coluna homogênea, sem circulação nem correção de enxame:
    εG ≈ U_G / U∞

Uso:  python sensibilidade_diametro.py --Ug 0.02 --eps-cfd 0.172
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from projeto_coluna_bolhas import G, Propriedades, holdup_akita_yoshida, holdup_hikita


def u_terminal_tomiyama(d, p: Propriedades):
    u = 0.2
    for _ in range(300):
        Re = p.rho_L * u * d / p.mu_L
        Eo = G * (p.rho_L - p.rho_G) * d**2 / p.sigma
        cd = max(24 / Re * (1 + 0.15 * Re**0.687), 8 / 3 * Eo / (Eo + 4))
        u = 0.5 * u + 0.5 * np.sqrt(4 * G * d * (p.rho_L - p.rho_G) / (3 * p.rho_L * cd))
    return u


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--Ug", type=float, default=0.02)
    ap.add_argument("--D", type=float, default=0.15)
    ap.add_argument("--eps-cfd", type=float, nargs="*", default=[],
                    help="εG do(s) CFD para marcar no gráfico")
    ap.add_argument("--out", type=Path, default=Path("resultados"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    p = Propriedades()

    d = np.linspace(0.5e-3, 8e-3, 150)
    U = np.array([u_terminal_tomiyama(x, p) for x in d])
    eps = a.Ug / U
    print(f"{'d [mm]':>7} {'U∞ [m/s]':>9} {'εG ≈ Ug/U∞':>11}")
    for x in [0.5, 1, 1.5, 2, 3, 4, 5, 6]:
        u = u_terminal_tomiyama(x * 1e-3, p)
        print(f"{x:7.1f} {u:9.3f} {a.Ug / u:11.3f}")
    for e in a.eps_cfd:
        i = np.argmin(np.abs(eps[d < 2.5e-3] - e))
        print(f"εG_CFD = {e:.3f} → equivale a bolhas de ≈ {d[i]*1e3:.1f} mm "
              f"(U_bolha = Ug/εG = {a.Ug/e:.3f} m/s)")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    ax.plot(d * 1e3, eps, color="tab:blue", label=r"$\varepsilon_G \approx U_G/U_\infty$ (Tomiyama)")
    ax.axhline(float(holdup_akita_yoshida(a.Ug, a.D, p)), ls="--", color="0.4",
               label="Akita & Yoshida (1973)")
    ax.axhline(float(holdup_hikita(a.Ug, p)), ls="-.", color="0.4", label="Hikita et al. (1980)")
    for e in a.eps_cfd:
        ax.axhline(e, color="tab:red", lw=1)
        ax.text(7.9, e + 0.005, f"CFD = {e:.3f}", color="tab:red", ha="right", fontsize=8)
    ax.set_xlabel("diâmetro de bolha d [mm]  (Interaction Length Scale)")
    ax.set_ylabel(r"$\varepsilon_G$ [–]")
    ax.set_ylim(0, 0.4)
    ax.set_xlim(0.5, 8)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title(f"Sensibilidade ao diâmetro de bolha — U_G = {a.Ug*100:g} cm/s", fontsize=10)
    fig.tight_layout()
    fig.savefig(a.out / "fig_sensibilidade_diametro.png")
    print(f"Figura salva em {a.out / 'fig_sensibilidade_diametro.png'}")


if __name__ == "__main__":
    main()
