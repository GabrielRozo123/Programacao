"""
figura_validacao_mudde.py
=========================
Validação do CFD 2D (aspersor uniforme, d = 5 mm, sem lift) contra o
experimento de Mudde et al. (2009) — coluna D = 0,15 m, 599 agulhas —
com os dados tabelados em Draw & Rzehak (2024), Tab. 2.

  (a) εG × J_G: experimento, CFD e duas referências teóricas (Draw & Rzehak, Eq. 9):
        · "bolhas pseudo-isoladas":      J = εG · w0                  (Eq. 7)
        · homogêneo com ∇p de mistura:   J = εG · w0 · √(1 − εG)      (Eq. 6)
  (b) paridade CFD × experimento (faixa ±10 %)
  (c) velocidade relativa w_rel = J/εG normalizada por w0 (efeito de enxame)

Uso:  python figura_validacao_mudde.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from compara_cfd_literatura import le_monitor_star

AQUI = Path(__file__).parent
PASTA = AQUI / "resultados_validacao_Mudde"
W0 = 0.232  # m/s, velocidade terminal de bolha isolada de 5 mm (Tomiyama/Mendelson)

# (arquivo, J_G [m/s], εG Mudde, rótulo)
CASOS = [
    ("holdup_Ug1.5.csv", 0.015, 0.061, "M1"),
    ("holdup_Ug1.7.csv", 0.017, 0.076, "M2"),
    ("holdup_Ug2.csv", 0.020, None, "rodada 2"),
    ("holdup_Ug2.5.csv", 0.025, 0.110, "M3"),
    ("holdup_Ug3.2.csv", 0.032, 0.160, "M4"),
    ("holdup_Ug3.9.csv", 0.039, 0.200, "M5"),
]
MUDDE = [(0.015, 0.061), (0.017, 0.076), (0.025, 0.11), (0.032, 0.16), (0.039, 0.20),
         (0.049, 0.25), (0.065, 0.42)]


def plato(t, y, janela=1.5, tol=0.002):
    """Média dos últimos `janela` s e se o sinal já estabilizou (inclinação < tol/s)."""
    m = t >= t.max() - janela
    inc = np.polyfit(t[m], y[m], 1)[0]
    return float(np.mean(y[m])), bool(abs(inc) < tol), float(inc), float(t.max())


def main():
    linhas = []
    print(f"{'caso':>9} {'J_G':>6} {'t_fim':>6} {'εG CFD':>7} {'estável?':>9} {'εG exp':>7} {'desvio':>7}")
    for arq, J, eexp, rot in CASOS:
        t, y, _ = le_monitor_star(PASTA / arq, "Holdup")
        e, ok, inc, tf = plato(t, y)
        if eexp is None:
            eexp = float(np.interp(J, [m[0] for m in MUDDE], [m[1] for m in MUDDE]))
        dev = 100 * (e - eexp) / eexp
        print(f"{rot:>9} {J:6.3f} {tf:6.1f} {e:7.4f} {'sim' if ok else 'NÃO':>9} {eexp:7.3f} {dev:+6.1f}%")
        linhas.append((rot, J, e, ok, eexp, dev))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4.3), dpi=150)
    Jm, em = np.array(MUDDE).T
    ax1.plot(Jm * 100, em, "s", mfc="none", mec="tab:blue", ms=7,
             label="Exp. Mudde et al. (2009), D = 0,15 m")
    eps = np.linspace(0, 0.45, 200)
    ax1.plot(eps * W0 * 100, eps, ":", color="0.4", label="bolhas pseudo-isoladas: J = εG·w0")
    ax1.plot(eps * W0 * np.sqrt(1 - eps) * 100, eps, "--", color="0.4",
             label="homogêneo, ∇p de mistura: J = εG·w0·√(1−εG)")
    for rot, J, e, ok, eexp, dev in linhas:
        ax1.plot(J * 100, e, "o", color="tab:red", mfc="tab:red" if ok else "white", ms=7)
    ax1.plot([], [], "o", color="tab:red", label="CFD 2D STAR-CCM+ (aberto = não estabilizado)")
    ax1.set_xlabel(r"$J_G$ [cm/s]")
    ax1.set_ylabel(r"$\varepsilon_G$ [–]")
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 0.45)
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=6.8, loc="upper left")
    ax1.set_title("(a) Retenção gasosa × vazão de gás", fontsize=10)

    for rot, J, e, ok, eexp, dev in linhas:
        ax2.plot(eexp, e, "o", color="tab:red", mfc="tab:red" if ok else "white", ms=7)
        ax2.annotate(rot, (eexp, e), textcoords="offset points", xytext=(5, -10), fontsize=7)
    x = np.linspace(0, 0.25, 10)
    ax2.plot(x, x, "k-", lw=0.8)
    ax2.fill_between(x, 0.9 * x, 1.1 * x, color="0.85", label="±10 %")
    ax2.set_xlabel(r"$\varepsilon_G$ experimental [–]")
    ax2.set_ylabel(r"$\varepsilon_G$ CFD [–]")
    ax2.set_xlim(0, 0.22)
    ax2.set_ylim(0, 0.22)
    ax2.set_aspect("equal")
    ax2.grid(alpha=0.3)
    ax2.legend(fontsize=7, loc="upper left")
    ax2.set_title("(b) Paridade CFD × experimento", fontsize=10)

    ax3.plot(em, Jm / em / W0, "s", mfc="none", mec="tab:blue", ms=7, label="Exp. Mudde (J/εG)/w0")
    for rot, J, e, ok, eexp, dev in linhas:
        ax3.plot(e, J / e / W0, "o", color="tab:red", mfc="tab:red" if ok else "white", ms=7)
    ax3.plot([], [], "o", color="tab:red", label="CFD (J/εG)/w0")
    ax3.plot(eps, np.sqrt(1 - eps), "--", color="0.4", label="√(1−εG) (∇p de mistura)")
    ax3.plot(eps, np.ones_like(eps), ":", color="0.4", label="bolhas pseudo-isoladas")
    ax3.set_xlabel(r"$\varepsilon_G$ [–]")
    ax3.set_ylabel(r"$w_{rel}/w_0$ [–]")
    ax3.set_xlim(0, 0.45)
    ax3.set_ylim(0.5, 1.2)
    ax3.grid(alpha=0.3)
    ax3.legend(fontsize=7, loc="lower left")
    ax3.set_title("(c) Velocidade relativa: efeito de enxame", fontsize=10)
    fig.tight_layout()
    out = AQUI / "resultados" / "fig_validacao_mudde.png"
    fig.savefig(out)
    print(f"Figura salva em {out}")


if __name__ == "__main__":
    main()
