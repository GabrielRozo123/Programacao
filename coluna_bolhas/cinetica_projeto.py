"""
cinetica_projeto.py
===================
Equações cinéticas de projeto da coluna de bolhas (reação gás–líquido),
com a hidrodinâmica vinda de 4 fontes: correlações, 2 experimentos e o CFD.

Reação:  A(g) + b B(l) → P   (taxa intrínseca  r = k2 C_A C_B,  k1 = k2 C_B)

  Ha  = √(k1 DA) / kL                         número de Hatta
  Ei  = 1 + DB C_B / (b DA C_A*)               fator de aumento instantâneo
  E   = f(Ha, Ei)  (van Krevelen–Hoftijzer)     fator de aumento

  Regime lento   (Ha < 0,3):   N·a = kLa (C* − C_L);   no seio: k1 εL C_L
  Regime rápido  (Ha > 3):     N·a = a C* √(k1 DA)     (independe de kL!)
  Instantâneo    (Ha > 10 Ei): N·a = kLa C* Ei

Projeto (gás pistonado, gás pouco solúvel → resistência no filme gasoso desprezível):
  U_G dC_G/dz = −K C_G/He   ⇒   X = 1 − exp(−K H / (He U_G))
  ⇒  H = He U_G ln[1/(1−X)] / K
  com  K = kLa·E                (rápido / instantâneo, C_L ≈ 0)
       K = 1/(1/kLa + 1/(k1 εL)) (lento, reação no seio, C_L local em regime pseudo-estacionário)

Exemplos (25 °C):
  1. O2 → biomassa/oxidação lenta no líquido (k1 = 0,05 1/s): regime LENTO.
  2. CO2 (10 % no ar) → NaOH 0,1 M (k_OH = 8×10³ m³/(kmol·s)): regime RÁPIDO.

Uso:  python cinetica_projeto.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from projeto_coluna_bolhas import (Propriedades, d32_akita_yoshida, holdup_akita_yoshida,
                                   kl_higbie)

D, UG, H0 = 0.15, 0.02, 0.90
P = Propriedades()

# Fontes da hidrodinâmica a U_G = 2 cm/s: (εG, d_b [m])
FONTES = {
    "Correlação (Akita & Yoshida)": (float(holdup_akita_yoshida(UG, D, P)),
                                     float(d32_akita_yoshida(UG, D, P))),
    "Exp. Besagni & Inzoli 2016 (spider)": (0.069, 3.5e-3),
    "Exp. Mudde et al. 2009 (agulhas)": (0.089, 4.25e-3),
    "CFD STAR-CCM+ (rodada 4)": (0.0856, 5.0e-3),
}

SISTEMAS = {
    "O2 + consumo lento (k1 = 0,05 1/s)": dict(DA=2.1e-9, He=31.5, k1=0.05, Ei=np.inf),
    "CO2 (10 %) + NaOH 0,1 M": dict(DA=1.9e-9, He=1.25, k1=8.0e3 * 0.1, DB=5.3e-9, CB=100.0,
                                   b=2, CAs=(0.10 * 101325 / (8.314 * 298)) / 1.25),
}


def fator_aumento(Ha, Ei):
    """van Krevelen–Hoftijzer (2ª ordem, filme):
        E = Ha·√((Ei−E)/(Ei−1)) / tanh(Ha·√((Ei−E)/(Ei−1)))
    Ei → ∞ recupera o pseudo-1ª ordem: E = Ha / tanh(Ha)."""
    if not np.isfinite(Ei):
        return Ha / np.tanh(Ha) if Ha > 1e-8 else 1.0
    lo, hi = 1.0, Ei
    for _ in range(200):
        E = 0.5 * (lo + hi)
        s = Ha * np.sqrt(max(Ei - E, 0.0) / (Ei - 1))
        g = (s / np.tanh(s) if s > 1e-8 else 1.0) - E
        lo, hi = (E, hi) if g > 0 else (lo, E)
    return 0.5 * (lo + hi)


def regime(Ha, Ei):
    if Ha < 0.3:
        return "lento"
    if np.isfinite(Ei) and Ha > 10 * Ei:
        return "instantâneo"
    return "rápido" if Ha > 3 else "intermediário"


def main():
    out = Path(__file__).parent / "resultados"
    out.mkdir(exist_ok=True)
    linhas = []
    for nome_s, s in SISTEMAS.items():
        Ei = s.get("Ei", None)
        if Ei is None:
            Ei = 1 + s["DB"] * s["CB"] / (s["b"] * s["DA"] * s["CAs"])
        print(f"\n=== {nome_s}  (Ei = {Ei:.1f}) ===")
        print(f"{'fonte da hidrodinâmica':38s} {'εG':>6} {'d[mm]':>6} {'a[1/m]':>7} "
              f"{'kL[m/s]':>9} {'kLa[1/s]':>9} {'Ha':>6} {'E':>6} {'regime':>12} "
              f"{'K[1/s]':>8} {'X(H=0,98m)':>10} {'H95%[m]':>8} {'V/V_corr':>8}")
        K_ref = None
        for nome_f, (eps, d) in FONTES.items():
            p = Propriedades(D_A=s["DA"])
            a = 6 * eps / d
            kL = float(kl_higbie(d, UG / eps, p))
            kla = kL * a
            Ha = np.sqrt(s["k1"] * s["DA"]) / kL
            E = fator_aumento(Ha, Ei)
            reg = regime(Ha, Ei)
            if reg == "lento":
                K = 1 / (1 / kla + 1 / (s["k1"] * (1 - eps)))
            else:
                K = kla * E
            H95 = s["He"] * UG * np.log(1 / 0.05) / K
            X_col = 1 - np.exp(-K * (H0 / (1 - eps)) / (s["He"] * UG))
            K_ref = K_ref or K
            Vrel = K_ref / K
            print(f"{nome_f:38s} {eps:6.3f} {d*1e3:6.2f} {a:7.1f} {kL:9.2e} {kla:9.4f} "
                  f"{Ha:6.3f} {E:6.2f} {reg:>12} {K:8.4f} {X_col:10.3f} {H95:8.2f} {Vrel:8.2f}")
            linhas.append([nome_s, nome_f, eps, d * 1e3, a, kL, kla, Ha, E, reg, K, H95,
                           X_col, Vrel])

    with open(out / "tabela_cinetica_projeto.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sistema", "fonte", "eps_G", "d_mm", "a_1_m", "kL_m_s", "kLa_1_s", "Ha", "E",
                    "regime", "K_1_s", "H_95pct_m", "X_coluna_H0.98m", "V_rel_correlacao"])
        for l in linhas:
            w.writerow([l[0], l[1]] + [f"{v:.4g}" if isinstance(v, float) else v for v in l[2:]])

    # ---- Figura: mapa de regimes E(Ha, Ei) + altura de projeto ------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150,
                                   gridspec_kw=dict(width_ratios=[1, 1.15]))
    Has = np.logspace(-2, 3, 300)
    for Ei, ls in [(np.inf, "-"), (200, "--"), (43, "-."), (10, ":")]:
        Es = [fator_aumento(h, Ei) for h in Has]
        ax1.loglog(Has, Es, ls, color="k", lw=1.2,
                   label="Ei → ∞ (pseudo-1ª ordem)" if not np.isfinite(Ei) else f"Ei = {Ei:g}")
    ax1.axvspan(1e-2, 0.3, color="tab:green", alpha=0.08)
    ax1.axvspan(3, 1e3, color="tab:red", alpha=0.08)
    ax1.text(0.012, 300, "LENTO\nE ≈ 1\nprojeto ∝ kLa, εL", fontsize=7.5, color="tab:green", va="top")
    ax1.text(0.5, 300, "interm.", fontsize=7.5, va="top")
    ax1.text(5, 300, "RÁPIDO\nE ≈ Ha\nprojeto ∝ a", fontsize=7.5, color="tab:red", va="top")
    ax1.text(400, 17, "INSTANTÂNEO\nE → Ei", fontsize=7, ha="center")
    for nome_s, cor in zip(SISTEMAS, ["tab:green", "tab:red"]):
        pts = [(l[7], l[8]) for l in linhas if l[0] == nome_s]
        ax1.plot([p[0] for p in pts], [p[1] for p in pts], "o", color=cor, ms=7,
                 mec="k", label=nome_s)
    ax1.set_xlabel("número de Hatta, Ha = √(k1·DA)/kL")
    ax1.set_ylabel("fator de aumento E")
    ax1.set_title("(a) Regimes de reação gás–líquido", fontsize=10)
    ax1.set_xlim(1e-2, 1e3)
    ax1.set_ylim(0.8, 500)
    ax1.grid(alpha=0.3, which="both")
    ax1.legend(fontsize=6.5, loc="center left")

    fontes = list(FONTES)
    x = np.arange(len(fontes))
    larg = 0.38
    for i, (nome_s, cor) in enumerate(zip(SISTEMAS, ["tab:green", "tab:red"])):
        Hs = [l[13] for l in linhas if l[0] == nome_s]
        b = ax2.bar(x + (i - 0.5) * larg, Hs, larg, color=cor, alpha=0.8, label=nome_s,
                    edgecolor="k", lw=0.5)
        for xi, h in zip(x + (i - 0.5) * larg, Hs):
            ax2.text(xi, h + 0.02, f"{h:.2f}", ha="center", fontsize=7)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f.replace(" (", "\n(") for f in fontes], fontsize=7)
    ax2.axhline(1, color="k", lw=0.8)
    ax2.set_ylim(0, 1.25)
    ax2.set_ylabel("volume de reator p/ a mesma conversão\n(relativo ao projeto por correlação)")
    ax2.set_title("(b) Mesma cinética, hidrodinâmica de fontes diferentes", fontsize=10)
    ax2.legend(fontsize=7, loc="upper right")
    ax2.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(out / "fig_cinetica_projeto.png")
    print(f"\nFigura salva em {out / 'fig_cinetica_projeto.png'}")


if __name__ == "__main__":
    main()
