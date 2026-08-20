#!/usr/bin/env python3
"""
Grafico da varredura de contrapressao -- o entregavel do estudo.

Painel de cima:  vazao contra perda de carga. Mostra o ramo em raiz de dP e o
                 plato de estrangulamento. E o grafico que responde "a partir
                 de que contrapressao a valvula deixa de controlar a vazao".

Painel de baixo: pressao minima na vena contracta, em escala log, contra a
                 pressao de vapor. Mostra POR QUE a vazao trava.

Le os pontos medidos de ponto_de_operacao.py -- fonte unica de dados.
"""

import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ponto_de_operacao import (FL_CFD, KV_CATALOGO, KV_CFD, K_P1, MEDIDO,
                               P1_BAR, P_VAP, REF_P, RHO, ff, vazao)

OUTDIR = os.path.dirname(os.path.abspath(__file__))

AZUL = "#1f4e79"
CINZA = "#8c8c8c"
VERMELHO = "#c0392b"
LARANJA = "#d68910"


def curva_iec(kv, fl, n=400):
    """Curva de referencia da IEC 60534-2-1, com estrangulamento."""
    dps, qs = [], []
    mdot = 10.0
    for i in range(n):
        p2 = P1_BAR - (0.3 + 3.9 * i / (n - 1))
        for _ in range(40):
            p1 = P1_BAR * 1e5 - K_P1 * mdot ** 2
            q, _ = vazao(p1 / 1e5, p2, kv, fl)
            mdot = q / 3600.0 * RHO
        dps.append((p1 - p2 * 1e5) / 1e5)
        qs.append(q)
    return dps, qs


def main():
    # --- dados medidos ------------------------------------------------------
    dp_m = [(p1 - p2) / 1e5 for p2, p1, _, _ in MEDIDO]
    q_m = [mdot / RHO * 3600.0 for _, _, mdot, _ in MEDIDO]
    # os reports do solver saem RELATIVOS (Reference Pressure = 101 325 Pa)
    pmin_m = [pmin + REF_P for _, _, _, pmin in MEDIDO]

    dpc = FL_CFD ** 2 * (P1_BAR - ff() * P_VAP / 1e5)
    q_max = KV_CFD * FL_CFD * math.sqrt(P1_BAR - ff() * P_VAP / 1e5)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 9), sharex=True,
        gridspec_kw={"height_ratios": [1.35, 1], "hspace": 0.12})

    # ======================= PAINEL 1 -- vazao ==============================
    dps, qs = curva_iec(KV_CFD, FL_CFD)
    ax1.plot(dps, qs, "-", color=CINZA, lw=2.2, zorder=2,
             label=f"IEC 60534-2-1  ($K_v$ = {KV_CFD:.1f}, $F_L$ = {FL_CFD:.3f})")

    dp_cat = [0.3 + 3.9 * i / 199 for i in range(200)]
    ax1.plot(dp_cat, [KV_CATALOGO * math.sqrt(d) for d in dp_cat],
             ":", color=CINZA, lw=1.6, zorder=1,
             label=f"catálogo Bray, $K_v$ = {KV_CATALOGO:.0f} (sem cavitação)")

    ax1.axvline(dpc, color=LARANJA, lw=1.4, ls="--", zorder=1)
    ax1.annotate(f"estrangulamento previsto\n$\\Delta P$ = {dpc:.2f} bar"
                 f"  ·  Q = {q_max:.0f} m³/h\n"
                 "baixar mais a contrapressão\nnão aumenta a vazão",
                 xy=(dpc + 0.05, q_max), xytext=(dpc + 0.30, q_max - 38),
                 color=LARANJA, fontsize=10.5, ha="left", va="bottom",
                 arrowprops=dict(arrowstyle="->", color=LARANJA, lw=1.3,
                                 connectionstyle="arc3,rad=-0.25"))

    ax1.plot(dp_m, q_m, "o", color=AZUL, ms=9, zorder=5, mec="white", mew=1.4,
             label="CFD  ·  VOF + Schnerr-Sauer")

    ax1.set_ylabel("vazão   [m³/h]", fontsize=12)
    ax1.set_ylim(0, 115)
    ax1.legend(loc="upper left", fontsize=10.5, framealpha=0.95)
    ax1.grid(alpha=0.25)
    ax1.set_title("Válvula borboleta DN 100 estrangulada a 30°  —  água a 20 °C,"
                  "  montante fixo em 6,01 bar abs",
                  fontsize=12.5, pad=14)

    # ======================= PAINEL 2 -- pressao minima =====================
    ax2.axhline(P_VAP, color=VERMELHO, lw=1.8, zorder=2)
    ax2.annotate(f"pressão de vapor da água a 20 °C  =  {P_VAP:.0f} Pa",
                 xy=(3.05, P_VAP), xytext=(3.05, P_VAP * 1.30),
                 color=VERMELHO, fontsize=10.5, va="bottom", ha="left")
    ax2.axhspan(1e3, P_VAP, color=VERMELHO, alpha=0.09, zorder=0)

    dp_lin = [0.3 + 3.9 * i / 199 for i in range(200)]
    pmin_lin, dp_ok = [], []
    for d in dp_lin:
        p1 = P1_BAR * 1e5 - K_P1 * (KV_CFD * math.sqrt(d) / 3600 * RHO) ** 2
        v = p1 - d * 1e5 / FL_CFD ** 2
        if v > 1.5e3:
            dp_ok.append(d)
            pmin_lin.append(v)
    ax2.plot(dp_ok, pmin_lin, "-", color=CINZA, lw=2.2, zorder=2,
             label="$p_{vc} = p_1 - \\Delta P / F_L^2$")

    ax2.axvline(dpc, color=LARANJA, lw=1.4, ls="--", zorder=1)
    ax2.plot(dp_m, pmin_m, "o", color=AZUL, ms=9, zorder=5, mec="white", mew=1.4,
             label="CFD  ·  mínimo de pressão no domínio")

    ax2.set_yscale("log")
    ax2.set_ylim(1.2e3, 6e5)
    ax2.set_xlim(0.5, 4.1)
    ax2.set_xlabel("perda de carga na válvula   $\\Delta P$   [bar]", fontsize=12)
    ax2.set_ylabel("pressão na vena contracta   [Pa]", fontsize=12)
    ax2.legend(loc="lower left", fontsize=10.5, framealpha=0.95,
               bbox_to_anchor=(0.0, 0.10))
    ax2.grid(alpha=0.25, which="both")

    fig.text(0.5, 0.035,
             "Simcenter STAR-CCM+  ·  VOF + Schnerr-Sauer  ·  malha de 890 k "
             "células  ·  $K_v$ validado contra catálogo do fabricante (−1,8%)",
             ha="center", fontsize=9.5, color="#666666")

    path = os.path.join(OUTDIR, "curva_cavitacao.png")
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"gravado: {path}")
    print(f"pontos medidos: {len(MEDIDO)}")
    print(f"joelho previsto: dP = {dpc:.2f} bar, Q = {q_max:.1f} m3/h")


if __name__ == "__main__":
    main()
