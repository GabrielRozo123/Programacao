"""
cfd_para_projeto.py
===================
Leva os resultados do CFD para as EQUAÇÕES DE PROJETO (cinética + TM) e
compara com o projeto feito só com correlações.

Parâmetros que o CFD fornece (por rodada):
  εG           → retenção gasosa (monitor Holdup Global)
  a = 6εG/d    → área interfacial específica
  kL (Higbie)  = 2√(DA·u_s/(π d)),  u_s = U_G/εG (velocidade do gás; líquido ≈ 0 na média)
  kLa = kL·a
  V_c          → velocidade de circulação (máx. de V_L no perfil radial)
  D_L ≈ 0,31·V_c·D   (Joshi, 1980 — modelo de circulação; conferir constante)

Projeto 1 — taxa global, líquido misturado, regime lento (Ha < 0,3):
  resistências em série:  1/k_ef = 1/kLa + 1/(k1 εL)
  r = k_ef · C*        → controle cinético (k1εL ≪ kLa) ou por TM (k1εL ≫ kLa)

Projeto 2 — fase líquida contínua, 1ª ordem, dispersão axial (Danckwerts):
  X(Da, Pe), Pe = u_L H / D_L

Uso:  python cfd_para_projeto.py [--k1 0.01] [--uL 0.005]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from compara_cfd_literatura import le_monitor_star, media_temporal
from perfis_radiais import le_xy
from projeto_coluna_bolhas import (DL_deckwer, Propriedades, conversao_adm_1a_ordem, hatta,
                                   holdup_akita_yoshida, kl_higbie, kla_akita_yoshida,
                                   kla_shah)

PASTA = Path(__file__).parent / "resultados_cfd_2D"
D, UG, H0 = 0.15, 0.02, 0.90
RODADAS = [  # prefixo, rótulo curto, d [m], início da média [s]
    ("r1_d1mm_uniforme", "CFD 1 (d=1 mm)", 1e-3, 20),
    ("r2_d5mm_uniforme", "CFD 2 (5 mm, unif.)", 5e-3, 10),
    ("r3_d5mm_parabolico", "CFD 3 (5 mm, parab.)", 5e-3, 10),
    ("r4_d5mm_parabolico_lift", "CFD 4 (5 mm, parab.+lift)", 5e-3, 12),
]


def k_ef(kla, k1, eps):
    """Constante global (resistências em série), por volume de dispersão [1/s]."""
    return 1.0 / (1.0 / kla + 1.0 / (k1 * (1 - eps)))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k1", type=float, default=0.01, help="cte. de 1ª ordem no líquido [1/s]")
    ap.add_argument("--uL", type=float, default=0.005, help="vel. superficial do líquido [m/s]")
    a = ap.parse_args()
    p = Propriedades()

    # ---- parâmetros: correlações -------------------------------------------
    casos = []
    eAY = float(holdup_akita_yoshida(UG, D, p))
    casos.append(dict(nome="Correlações (A&Y + Deckwer)", eps=eAY,
                      kla=float(kla_akita_yoshida(eAY, D, p)), DL=float(DL_deckwer(UG, D)),
                      a=np.nan, kL=np.nan, Vc=np.nan))
    casos.append(dict(nome="Shah (kLa) + Deckwer", eps=eAY, kla=float(kla_shah(UG)),
                      DL=float(DL_deckwer(UG, D)), a=np.nan, kL=np.nan, Vc=np.nan))

    # ---- parâmetros: CFD -----------------------------------------------------
    for pref, nome, d, t0 in RODADAS:
        t, y, _ = le_monitor_star(PASTA / f"{pref}_holdup.csv", "Holdup")
        eps, _ = media_temporal(t, y, t0)
        _, v, _ = le_xy(PASTA / f"{pref}_vL.csv")
        Vc = max(abs(v.max()), abs(v.min()))
        us = UG / eps
        kL = float(kl_higbie(d, us, p))
        area = 6 * eps / d
        casos.append(dict(nome=nome, eps=eps, a=area, kL=kL, kla=kL * area,
                          Vc=Vc, DL=max(0.31 * Vc * D, 1e-5)))

    # ---- Projeto 1 e 2 ----------------------------------------------------------
    linhas = []
    print(f"k1 = {a.k1} 1/s, u_L = {a.uL} m/s, U_G = {UG} m/s, D = {D} m\n")
    cab = (f"{'caso':30s} {'εG':>6} {'a[1/m]':>7} {'kLa[1/s]':>9} {'Ha':>6} "
           f"{'k1εL/kLa':>9} {'k_ef[1/s]':>10} {'D_L[m²/s]':>10} {'Pe':>6} {'X_ADM':>6}")
    print(cab)
    print("-" * len(cab))
    for c in casos:
        eps = c["eps"]
        kL_ref = c["kL"] if np.isfinite(c["kL"]) else float(kl_higbie(5e-3, 0.23, p))
        Ha = float(hatta(a.k1, kL_ref, p))
        kef = k_ef(c["kla"], a.k1, eps)
        H = H0 / (1 - eps)
        Pe = a.uL * H / c["DL"]
        Da = a.k1 * (1 - eps) * H / a.uL
        X = float(conversao_adm_1a_ordem(Da, Pe))
        c.update(Ha=Ha, kef=kef, Pe=Pe, Da=Da, X=X)
        print(f"{c['nome']:30s} {eps:6.3f} {c['a']:7.1f} {c['kla']:9.4f} {Ha:6.3f} "
              f"{a.k1*(1-eps)/c['kla']:9.2f} {kef:10.5f} {c['DL']:10.5f} {Pe:6.2f} {X:6.3f}")
        linhas.append([c["nome"], f"{eps:.4f}", f"{c['a']:.1f}", f"{c['kla']:.4f}", f"{Ha:.4f}",
                       f"{kef:.5f}", f"{c['DL']:.5f}", f"{Pe:.3f}", f"{X:.3f}"])
    Da0 = casos[0]["Da"]
    print(f"\nLimites (Da = {Da0:.2f}): CSTR X = {Da0/(1+Da0):.3f} | PFR X = {1-np.exp(-Da0):.3f}")

    out = Path(__file__).parent / "resultados"
    out.mkdir(exist_ok=True)
    with open(out / "tabela_cfd_para_projeto.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["caso", "eps_G", "a_1_m", "kLa_1_s", "Ha", "k_ef_1_s", "DL_m2_s", "Pe", "X_ADM"])
        w.writerows(linhas)

    # ---- Figura -------------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), dpi=150)
    k1s = np.logspace(-4, 1, 300)
    estilos = {"Correlações (A&Y + Deckwer)": ("0.4", "--"), "Shah (kLa) + Deckwer": ("0.4", ":"),
               "CFD 1 (d=1 mm)": ("tab:gray", "-"), "CFD 4 (5 mm, parab.+lift)": ("tab:red", "-")}
    for c in casos:
        if c["nome"] not in estilos:
            continue
        cor, ls = estilos[c["nome"]]
        ax1.loglog(k1s, k_ef(c["kla"], k1s, c["eps"]), ls, color=cor,
                   label=f"{c['nome']}: kLa = {c['kla']:.3f} 1/s")
    ax1.loglog(k1s, k1s * (1 - casos[-1]["eps"]), color="tab:green", lw=0.8, alpha=0.6,
               label=r"só cinética: $k_1\varepsilon_L$")
    ax1.axvline(a.k1, color="k", lw=0.6)
    ax1.text(a.k1 * 1.1, 1.2e-4, f"k1 do\nexemplo", fontsize=7)
    ax1.text(1.3e-4, 2.5e-3, "controle CINÉTICO\n(hidrodinâmica\nnão importa)", fontsize=7,
             color="tab:green", va="bottom")
    ax1.text(0.6, 3e-3, "controle por\nTRANSF. DE MASSA\n(projeto depende\nde εG, a, kL)",
             fontsize=7, color="tab:red", ha="center")
    ha03 = (0.3 * float(kl_higbie(5e-3, 0.23, p)))**2 / p.D_A
    ax1.axvspan(ha03, 10, color="0.85", zorder=0)
    ax1.text(ha03 * 1.1, 1.5e-4, "Ha > 0,3:\nreação\nno filme", fontsize=7)
    ax1.set_xlabel(r"constante cinética $k_1$ [1/s]")
    ax1.set_ylabel(r"$k_{ef}$ = taxa global / $C^*$ [1/s]")
    ax1.set_title("(a) Taxa global: cinética × transferência de massa", fontsize=10)
    ax1.set_xlim(1e-4, 10)
    ax1.set_ylim(1e-4, 1)
    ax1.grid(alpha=0.3, which="both")
    ax1.legend(fontsize=6.5, loc="upper left")

    Pes = np.logspace(-2, 2, 200)
    ax2.semilogx(Pes, conversao_adm_1a_ordem(Da0, Pes), "k-", lw=1.5,
                 label=f"dispersão axial, Da = {Da0:.2f}")
    ax2.axhline(Da0 / (1 + Da0), color="0.5", ls="--", lw=0.8, label="CSTR")
    ax2.axhline(1 - np.exp(-Da0), color="0.5", ls=":", lw=0.8, label="PFR")
    marc = {"Correlações (A&Y + Deckwer)": ("s", "0.3"), "CFD 2 (5 mm, unif.)": ("o", "tab:blue"),
            "CFD 3 (5 mm, parab.)": ("o", "tab:orange"), "CFD 4 (5 mm, parab.+lift)": ("o", "tab:red")}
    for c in casos:
        if c["nome"] in marc:
            m, cor = marc[c["nome"]]
            ax2.plot(c["Pe"], c["X"], m, color=cor, ms=8, label=f"{c['nome']}: X = {c['X']:.2f}")
    ax2.set_xlabel(r"Pe = $u_L H / D_L$")
    ax2.set_ylabel("conversão X")
    ax2.set_title("(b) Retromistura (D_L) → conversão", fontsize=10)
    ax2.grid(alpha=0.3, which="both")
    ax2.legend(fontsize=6.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "fig_cfd_para_projeto.png")
    print(f"Figura salva em {out / 'fig_cfd_para_projeto.png'}")


if __name__ == "__main__":
    main()
