"""
figura_2D_vs_3D.py
==================
Compara a rodada 4 (2D axissimétrico) com o caso 3D (mesma física: aspersor
parabólico, d = 5 mm, lift −0,05) e com os experimentos, a U_G = 2 cm/s.

No 3D, os perfis vêm de 2 diâmetros (Radial_x e Radial_y) = 4 raios; o perfil
médio é a média dos 4 raios em cada |r| e a faixa sombreada mostra a dispersão
entre eles (indicador de convergência estatística da média temporal).

Uso:  python figura_2D_vs_3D.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from compara_cfd_literatura import le_monitor_star, media_temporal
from perfis_radiais import le_xy
from projeto_coluna_bolhas import Propriedades, holdup_akita_yoshida, vl_centro_riquarts

AQUI = Path(__file__).parent
R, D, UG = 0.075, 0.15, 0.02


def le_raios(arqs):
    """Lê perfis de −R a +R e devolve r, média dos raios, mín e máx entre raios."""
    import csv
    curvas = []
    for a in arqs:
        with open(a, newline="", encoding="utf-8-sig") as f:
            ln = list(csv.reader(f))
        xy = np.array([[float(p), float(q)] for p, q in ln[1:] if p.strip()])
        for lado in (xy[xy[:, 0] <= 0], xy[xy[:, 0] >= 0]):
            r = np.abs(lado[:, 0])
            o = np.argsort(r)
            curvas.append((r[o], lado[o, 1]))
    rg = np.linspace(0, 0.0745, 60)
    M = np.array([np.interp(rg, r, v) for r, v in curvas])
    return rg, M.mean(0), M.min(0), M.max(0)


def main():
    p = Propriedades()
    d2, d3 = AQUI / "resultados_cfd_2D", AQUI / "resultados_cfd_3D"
    t, y, _ = le_monitor_star(d2 / "r4_d5mm_parabolico_lift_holdup.csv", "Holdup")
    e2, _ = media_temporal(t, y, 12)
    t, y, _ = le_monitor_star(d3 / "r5_3D_parabolico_lift_holdup.csv", "Hold")
    e3, s3 = media_temporal(t, y, 15)
    print(f"εG 2D = {e2:.4f} | εG 3D = {e3:.4f} ± {s3:.4f} (t até {t.max():.1f} s)")

    ra2, a2, _ = le_xy(d2 / "r4_d5mm_parabolico_lift_alpha.csv")
    rv2, v2, _ = le_xy(d2 / "r4_d5mm_parabolico_lift_vL.csv")
    r3, a3, a3min, a3max = le_raios([d3 / "r5_3D_alpha_x.csv", d3 / "r5_3D_alpha_y.csv"])
    _, v3, v3min, v3max = le_raios([d3 / "r5_3D_vL_x.csv", d3 / "r5_3D_vL_y.csv"])
    i0 = np.where(np.diff(np.sign(v3)) != 0)[0]
    print(f"3D: V_L eixo {v3[0]:+.3f} m/s, mín {v3.min():+.3f}; inversão r/R ≈ "
          f"{r3[i0[0]]/R if len(i0) else float('nan'):.2f}; α eixo {a3[0]:.3f}, parede {a3[-1]:.3f}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150)
    nomes = ["CFD 2D\n(rod. 4)", "CFD 3D", "Exp. Mudde\n(agulhas)", "Exp. Besagni\n(spider)",
             "Akita &\nYoshida"]
    vals = [e2, e3, 0.089, 0.069, float(holdup_akita_yoshida(UG, D, p))]
    cores = ["tab:red", "tab:purple", "tab:blue", "tab:green", "0.6"]
    ax1.bar(nomes, vals, color=cores, edgecolor="k", lw=0.5)
    for i, v in enumerate(vals):
        ax1.text(i, v + 0.002, f"{v:.3f}", ha="center", fontsize=8)
    ax1.set_ylabel(r"$\varepsilon_G$ global [–]")
    ax1.set_ylim(0, 0.11)
    ax1.tick_params(axis="x", labelsize=7)
    ax1.set_title(r"(a) Retenção gasosa, $U_G$ = 2 cm/s", fontsize=10)

    ax2.plot(ra2 / R, a2, color="tab:red", lw=1.8, label="CFD 2D axissimétrico")
    ax2.fill_between(r3 / R, a3min, a3max, color="tab:purple", alpha=0.2, label="3D: faixa entre 4 raios")
    ax2.plot(r3 / R, a3, color="tab:purple", lw=1.8, label="CFD 3D (média dos raios)")
    ax2.set_xlabel("r/R [–]")
    ax2.set_ylabel(r"$\overline{\alpha}_G$ [–]")
    ax2.set_title("(b) Fração de gás média, z = 0,6 m", fontsize=10)
    ax2.set_xlim(0, 1)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=7)

    ax3.plot(rv2 / R, v2, color="tab:red", lw=1.8, label="CFD 2D axissimétrico")
    ax3.fill_between(r3 / R, v3min, v3max, color="tab:purple", alpha=0.2, label="3D: faixa entre 4 raios")
    ax3.plot(r3 / R, v3, color="tab:purple", lw=1.8, label="CFD 3D (média dos raios)")
    vl0 = float(vl_centro_riquarts(UG, D, p))
    ax3.plot(0, vl0, "k*", ms=11, label=f"Riquarts (1981): {vl0:.2f} m/s")
    ax3.axhline(0, color="k", lw=0.8)
    ax3.axvline(0.7, ls=":", color="0.4", label="inversão clássica r/R ≈ 0,7")
    ax3.set_xlabel("r/R [–]")
    ax3.set_ylabel(r"$\overline{V}_{L,z}$ [m/s]")
    ax3.set_title("(c) Velocidade axial média da água, z = 0,6 m", fontsize=10)
    ax3.set_xlim(-0.03, 1)
    ax3.grid(alpha=0.3)
    ax3.legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    out = AQUI / "resultados" / "fig_2D_vs_3D.png"
    fig.savefig(out)
    print(f"Figura salva em {out}")


if __name__ == "__main__":
    main()
