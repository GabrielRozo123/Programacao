"""
compara_cfd_literatura.py
=========================
Pós-processamento da simulação Euler–Euler da coluna de bolhas (STAR-CCM+)
e comparação com correlações e dados experimentais da literatura.

Entradas
--------
1) Um CSV por velocidade superficial, exportado do STAR-CCM+
   (Plots → "Holdup Global" → botão direito → Export → CSV).
   Nome do arquivo: holdup_Ug<valor em cm/s>.csv, ex.: holdup_Ug2.csv
   O script usa a 1ª coluna que contém "Time" e a coluna cujo nome contém
   --coluna (padrão: "Holdup"); se não achar, usa a última coluna.

2) dados_experimentais.csv (opcional) com colunas:
       fonte, D_m, Ug_m_s, eps_G
   Linhas iniciadas por '#' são comentários.

Uso
---
    python compara_cfd_literatura.py --pasta star_exports --t-media 20
    python compara_cfd_literatura.py --pasta star_exports --D 0.15

Saídas: resultados/fig_cfd_vs_literatura.png, resultados/tabela_cfd.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import numpy as np

from projeto_coluna_bolhas import (Propriedades, holdup_akita_yoshida,
                                   holdup_deslizamento, holdup_hikita, holdup_reilly,
                                   u_terminal_mendelson)


def le_monitor_star(arq: Path, chave: str):
    """Lê o CSV exportado de um Monitor Plot do STAR-CCM+."""
    with open(arq, newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.reader(f))
    cab = [c.strip().strip('"') for c in linhas[0]]
    i_t = next(i for i, c in enumerate(cab) if "time" in c.lower())
    cand = [i for i, c in enumerate(cab) if chave.lower() in c.lower() and i != i_t]
    i_y = cand[0] if cand else len(cab) - 1
    dados = np.array([[float(r[i_t]), float(r[i_y])] for r in linhas[1:] if r and r[0].strip()])
    return dados[:, 0], dados[:, 1], cab[i_y]


def media_temporal(t, y, t_ini):
    """Média e desvio-padrão para t ≥ t_ini (média ponderada por Δt)."""
    m = t >= t_ini
    if m.sum() < 3:
        raise ValueError(f"poucos pontos após t = {t_ini} s (t_max = {t.max():.1f} s)")
    tt, yy = t[m], y[m]
    media = np.trapezoid(yy, tt) / (tt[-1] - tt[0])
    return media, yy.std()


def le_experimentais(arq: Path):
    if not arq.exists():
        return []
    out = []
    with open(arq, newline="", encoding="utf-8") as f:
        linhas = [l for l in f if l.strip() and not l.lstrip().startswith("#")]
    for r in csv.DictReader(linhas):
        out.append((r["fonte"], float(r["D_m"]), float(r["Ug_m_s"]), float(r["eps_G"])))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pasta", type=Path, default=Path("star_exports"))
    ap.add_argument("--coluna", default="Holdup")
    ap.add_argument("--t-media", type=float, default=20.0,
                    help="início da janela de média temporal [s]")
    ap.add_argument("--D", type=float, default=0.15)
    ap.add_argument("--exp", type=Path, default=Path("dados_experimentais.csv"))
    ap.add_argument("--out", type=Path, default=Path("resultados"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    p = Propriedades()

    # ---- CFD -------------------------------------------------------------
    cfd = []
    for arq in sorted(args.pasta.glob("holdup_Ug*.csv")):
        m = re.search(r"Ug([\d.p]+)", arq.stem)
        Ug = float(m.group(1).replace("p", ".")) / 100  # cm/s → m/s
        t, y, nome = le_monitor_star(arq, args.coluna)
        media, dp = media_temporal(t, y, args.t_media)
        cfd.append((Ug, media, dp, t.max()))
        print(f"{arq.name}: coluna '{nome}', t_max = {t.max():.1f} s → "
              f"εG = {media:.4f} ± {dp:.4f}")
        # estacionariedade: compara as médias das duas metades da janela
        tm = 0.5 * (args.t_media + t.max())
        try:
            m1, _ = media_temporal(t[t <= tm], y[t <= tm], args.t_media)
            m2, _ = media_temporal(t, y, tm)
            dif = 100 * (m2 - m1) / m1
            veredito = "OK (estatisticamente estacionário)" if abs(dif) < 2 else \
                "AINDA EVOLUINDO: rode mais tempo ou comece a média mais tarde"
            print(f"    1ª metade {m1:.4f} | 2ª metade {m2:.4f} | diferença {dif:+.1f}% → {veredito}")
        except ValueError:
            pass
    cfd.sort()

    with open(args.out / "tabela_cfd.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ug_m_s", "eps_CFD", "desvpad", "t_max_s",
                    "eps_AkitaYoshida", "eps_Hikita", "desvio_AY_%", "desvio_Hik_%"])
        for Ug, e, dp, tm in cfd:
            eAY = float(holdup_akita_yoshida(Ug, args.D, p))
            eHk = float(holdup_hikita(Ug, p))
            w.writerow([Ug, f"{e:.4f}", f"{dp:.4f}", f"{tm:.1f}", f"{eAY:.4f}", f"{eHk:.4f}",
                        f"{100*(e-eAY)/eAY:.1f}", f"{100*(e-eHk)/eHk:.1f}"])
            print(f"  Ug = {Ug*100:.1f} cm/s: CFD {e:.3f} | A&Y {eAY:.3f} "
                  f"({100*(e-eAY)/eAY:+.0f}%) | Hikita {eHk:.3f} ({100*(e-eHk)/eHk:+.0f}%)")

    exp = le_experimentais(args.exp)

    # ---- Figura ------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    U = np.linspace(0.002, 0.10, 200)
    fig, ax = plt.subplots(figsize=(6, 4.2), dpi=150)
    ax.plot(U * 100, holdup_akita_yoshida(U, args.D, p), color="0.35",
            label="Akita & Yoshida (1973)")
    ax.plot(U * 100, holdup_hikita(U, p), "--", color="0.35", label="Hikita et al. (1980)")
    ax.plot(U * 100, holdup_reilly(U, p), "-.", color="0.35", label="Reilly et al. (1986)")
    Uh = U[U <= 0.05]
    ax.plot(Uh * 100, holdup_deslizamento(Uh, U_inf=float(u_terminal_mendelson(5e-3, p))), ":",
            color="k", label="Homogêneo ideal, d = 5 mm (sem circulação)")

    marcadores = iter(["s", "^", "D", "v", "P", "X"])
    for fonte in dict.fromkeys(e[0] for e in exp):
        pts = np.array([(u, e) for f_, _, u, e in exp if f_ == fonte])
        ax.plot(pts[:, 0] * 100, pts[:, 1], next(marcadores), mfc="none",
                label=f"Exp.: {fonte}")

    if cfd:
        c = np.array(cfd)
        ax.errorbar(c[:, 0] * 100, c[:, 1], yerr=c[:, 2], fmt="o", color="tab:red",
                    capsize=3, ms=7, label="CFD Euler–Euler (STAR-CCM+)")

    ax.set_xlabel(r"$U_G$ [cm/s]")
    ax.set_ylabel(r"$\varepsilon_G$ global [–]")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 0.30)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.5, loc="upper left")
    ax.set_title(f"Retenção gasosa: CFD × literatura (D = {args.D:.2f} m)")
    fig.tight_layout()
    fig.savefig(args.out / "fig_cfd_vs_literatura.png")
    print(f"Figura salva em {args.out / 'fig_cfd_vs_literatura.png'}")


if __name__ == "__main__":
    main()
