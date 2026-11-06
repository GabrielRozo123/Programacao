"""
figura_resumo_rodadas.py
========================
Figura-resumo das rodadas CFD 2D axissimétricas (U_G = 2 cm/s) para o
seminário, a partir dos CSV em resultados_cfd_2D/:

  (a) εG global: 4 rodadas × correlações
  (b) fração de gás média  α(r) em z = 0,6 m
  (c) velocidade axial média da água  V_L(r) em z = 0,6 m

Gera também resultados_cfd_2D/resumo_rodadas.csv.

Uso:  python figura_resumo_rodadas.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from compara_cfd_literatura import le_monitor_star, media_temporal
from perfis_radiais import le_xy
from projeto_coluna_bolhas import (Propriedades, holdup_akita_yoshida, holdup_deslizamento,
                                   holdup_hikita, holdup_reilly, u_terminal_mendelson,
                                   vl_centro_riquarts)

PASTA = Path(__file__).parent / "resultados_cfd_2D"
D, R, UG = 0.15, 0.075, 0.02

# (prefixo, rótulo, início da média [s], cor)
RODADAS = [
    ("r1_d1mm_uniforme", "1: d = 1 mm, aspersor uniforme", 20, "tab:gray"),
    ("r2_d5mm_uniforme", "2: d = 5 mm, uniforme", 10, "tab:blue"),
    ("r3_d5mm_parabolico", "3: d = 5 mm, aspersor parabólico", 10, "tab:orange"),
    ("r4_d5mm_parabolico_lift", "4: idem + lift C_L = −0,05", 12, "tab:red"),
]


def main():
    p = Propriedades()
    linhas = []
    dados = []
    for pref, rot, t0, cor in RODADAS:
        t, y, _ = le_monitor_star(PASTA / f"{pref}_holdup.csv", "Holdup")
        eps, dp = media_temporal(t, y, t0)
        ra, a, _ = le_xy(PASTA / f"{pref}_alpha.csv")
        rv, v, _ = le_xy(PASTA / f"{pref}_vL.csv")
        troca = np.where(np.diff(np.sign(v)) != 0)[0]
        r_inv = rv[troca[0]] / R if len(troca) else float("nan")
        dados.append((rot, cor, eps, dp, ra, a, rv, v))
        linhas.append([rot, f"{eps:.4f}", f"{dp:.4f}", f"{v[0]:.3f}", f"{v.max():.3f}",
                       f"{v.min():.3f}", f"{r_inv:.2f}"])
        print(f"{rot:38s} εG = {eps:.4f} ± {dp:.4f} | V_L eixo {v[0]:+.3f}, "
              f"máx {v.max():+.3f}, mín {v.min():+.3f} m/s | inversão r/R = {r_inv:.2f}")

    with open(PASTA / "resumo_rodadas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rodada", "eps_G", "desvpad", "VL_eixo_m_s", "VL_max_m_s",
                    "VL_min_m_s", "r_inversao_R"])
        w.writerows(linhas)

    ref = {
        "Akita & Yoshida (1973)": float(holdup_akita_yoshida(UG, D, p)),
        "Hikita et al. (1980)": float(holdup_hikita(UG, p)),
        "Reilly et al. (1986)": float(holdup_reilly(UG, p)),
        "Homogêneo ideal (5 mm)": float(holdup_deslizamento(UG, U_inf=float(u_terminal_mendelson(5e-3, p)))),
    }

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150)

    # (a) barras de εG
    nomes = [d[0].split(":")[0] for d in dados] + ["A&Y", "Hikita", "Reilly", "Homog."]
    vals = [d[2] for d in dados] + list(ref.values())
    cores = [d[1] for d in dados] + ["0.75"] * 4
    ax1.bar(nomes, vals, color=cores, edgecolor="k", lw=0.5)
    ax1.axhspan(min(list(ref.values())[:3]), max(list(ref.values())[:3]),
                color="0.9", zorder=0, label="faixa das correlações")
    for i, v in enumerate(vals):
        ax1.text(i, v + 0.003, f"{v:.3f}", ha="center", fontsize=7)
    ax1.set_ylabel(r"$\varepsilon_G$ global [–]")
    ax1.set_title(r"(a) Retenção gasosa, $U_G$ = 2 cm/s", fontsize=10)
    ax1.set_xlabel("rodada CFD  |  correlações")
    ax1.legend(fontsize=7, loc="upper right")
    ax1.set_ylim(0, 0.2)
    ax1.tick_params(axis="x", labelrotation=35, labelsize=8)

    for rot, cor, eps, dp, ra, a, rv, v in dados:
        if rot.startswith("1"):
            continue  # 1 mm fica fora de escala nos perfis
        ax2.plot(ra / R, a, "-", color=cor, lw=1.8, label=rot)
        ax3.plot(rv / R, v, "-", color=cor, lw=1.8, label=rot)
    ax2.set_xlabel("r/R [–]")
    ax2.set_ylabel(r"$\overline{\alpha}_G$ [–]")
    ax2.set_title("(b) Fração de gás média (z = 0,6 m)", fontsize=10)
    ax2.set_xlim(0, 1)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=7)

    vl0 = float(vl_centro_riquarts(UG, D, p))
    ax3.plot(0, vl0, "k*", ms=11, label=f"Riquarts (1981), eixo: {vl0:.2f} m/s")
    ax3.axhline(0, color="k", lw=0.8)
    ax3.axvline(0.7, ls=":", color="0.4", label="inversão clássica r/R ≈ 0,7")
    ax3.set_xlabel("r/R [–]")
    ax3.set_ylabel(r"$\overline{V}_{L,ax}$ [m/s]")
    ax3.set_title("(c) Velocidade axial média da água (z = 0,6 m)", fontsize=10)
    ax3.set_xlim(-0.03, 1)
    ax3.grid(alpha=0.3)
    ax3.legend(fontsize=7, loc="lower left")

    fig.tight_layout()
    out = Path(__file__).parent / "resultados" / "fig_resumo_rodadas.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out)
    print(f"Figura salva em {out}")


if __name__ == "__main__":
    main()
