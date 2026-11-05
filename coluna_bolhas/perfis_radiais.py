"""
perfis_radiais.py
=================
Plota os perfis radiais médios no tempo exportados do STAR-CCM+
(XY Plot da line probe → Export CSV) para os slides:

  (a) fração de gás média  εG(r)
  (b) velocidade axial média da água  V_L(r)
      com a referência de Riquarts (1981) no eixo e a inversão em r/R ≈ 0,7

Uso:
    python perfis_radiais.py --alpha star_exports/perfil_alpha_Ug2.csv \
                             --vl star_exports/perfil_vL_Ug2.csv --Ug 0.02

O CSV do STAR tem 2 colunas: posição (m) e a grandeza. Se a posição vier
de −R a +R (3D), o script usa |r|.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from projeto_coluna_bolhas import Propriedades, vl_centro_riquarts


def le_xy(arq: Path):
    with open(arq, newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.reader(f))
    nomes = [c.strip().strip('"') for c in linhas[0]]
    xy = np.array([[float(r[0]), float(r[1])] for r in linhas[1:] if len(r) >= 2 and r[0].strip()])
    xy = xy[np.argsort(np.abs(xy[:, 0]))]
    return np.abs(xy[:, 0]), xy[:, 1], nomes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alpha", type=Path, required=True)
    ap.add_argument("--vl", type=Path, required=True)
    ap.add_argument("--Ug", type=float, default=0.02)
    ap.add_argument("--D", type=float, default=0.15)
    ap.add_argument("--out", type=Path, default=Path("resultados"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    R = a.D / 2

    r_a, alpha, _ = le_xy(a.alpha)
    r_v, vl, _ = le_xy(a.vl)
    vl0 = float(vl_centro_riquarts(a.Ug, a.D, Propriedades()))

    # média do perfil ponderada pela área (2πr dr) → εG "de seção"
    eps_secao = np.trapezoid(alpha * r_a, r_a) / np.trapezoid(r_a, r_a)
    troca = np.where(np.diff(np.sign(vl)) != 0)[0]
    r_inv = r_v[troca[0]] / R if len(troca) else float("nan")

    print(f"εG médio na seção (ponderado por área) = {eps_secao:.4f}")
    print(f"V_L no eixo: CFD = {vl[0]:.3f} m/s | Riquarts = {vl0:.3f} m/s")
    print(f"inversão do V_L em r/R = {r_inv:.2f} (literatura ≈ 0,7)")
    # conferência: em batelada a vazão líquida na seção ≈ 0 (ignora o fator 1−α)
    vazao = 2 * np.pi * np.trapezoid(vl * r_v, r_v)
    q_sobe = 2 * np.pi * np.trapezoid(np.clip(vl, 0, None) * r_v, r_v)
    print(f"vazão líquida na seção = {vazao:.2e} m³/s ({100*vazao/q_sobe:+.0f}% da vazão ascendente; ~0 é o esperado)")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8), dpi=150)
    ax1.plot(r_a / R, alpha, "o-", ms=3, color="tab:blue", label="CFD (média 20–60 s)")
    ax1.axhline(eps_secao, ls="--", color="0.4", lw=1,
                label=f"média na seção = {eps_secao:.3f}")
    ax1.set_xlabel("r/R [–]")
    ax1.set_ylabel(r"$\overline{\alpha}_G$ [–]")
    ax1.set_title("(a) Fração de gás")
    ax1.set_xlim(0, 1)
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=8)

    ax2.plot(r_v / R, vl, "o-", ms=3, color="tab:red", label="CFD (média 20–60 s)")
    ax2.plot(0, vl0, "k*", ms=12, label=f"Riquarts (1981): {vl0:.2f} m/s")
    ax2.axhline(0, color="k", lw=0.8)
    ax2.axvline(0.7, ls=":", color="0.4", label="inversão típica r/R ≈ 0,7")
    ax2.set_xlabel("r/R [–]")
    ax2.set_ylabel(r"$\overline{V}_{L,ax}$ [m/s]")
    ax2.set_title("(b) Velocidade axial da água")
    ax2.set_xlim(-0.03, 1)
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=8)

    fig.suptitle(f"Perfis radiais em z = 0,6 m — U_G = {a.Ug*100:g} cm/s", fontsize=10)
    fig.tight_layout()
    fig.savefig(a.out / f"fig_perfis_radiais_Ug{a.Ug*100:g}.png")
    print(f"Figura salva em {a.out / f'fig_perfis_radiais_Ug{a.Ug*100:g}.png'}")


if __name__ == "__main__":
    main()
