#!/usr/bin/env python3
"""
Figura da Fase 3 — camada-limite de concentracao medida no canal monolitico.

Tres paineis com o mesmo eixo vertical (distancia da parede catalitica):
  (a) fracao massica de TG            — o empobrecimento
  (b) velocidade axial                — o perfil de Poiseuille
  (c) contribuicao local a media ponderada por vazao, u*(Y_in - Y)

O painel (c) e o argumento da Nota II: o fluido mais empobrecido e o mais lento,
entao a regiao que carrega a informacao de conversao quase nao pesa na media
ponderada por vazao usada na fronteira de saida.

Entrada : results/perfil_camada_limite_x49mm.csv
Saida   : results/fig4_camada_limite_x49mm.{pdf,png}
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "results" / "perfil_camada_limite_x49mm.csv"
SAIDA = RAIZ / "results" / "fig4_camada_limite_x49mm"

# paleta validada (slots 1-3, modo claro) — ver docs do projeto
AZUL, LARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
TINTA, TINTA2, TINTA3 = "#0b0b0b", "#52514e", "#8a8984"

Y_IN = 0.8194
LIMITE_UM = 400.0  # janela vertical, micrometros


def carregar():
    d = np.genfromtxt(ENTRADA, delimiter=",", skip_header=4, names=True)
    dist = d["dist_parede_cat_m"] * 1e6  # µm
    ordem = np.argsort(dist)
    dist, Y = dist[ordem], d["Y_TG"][ordem]

    # A sonda tem resolucao maior que a malha: valores se repetem dentro de cada
    # celula. Colapsa cada repeticao num ponto no centroide, que e o dado real.
    corte = np.flatnonzero(np.diff(Y) != 0) + 1
    grupos = np.split(np.arange(len(Y)), corte)
    dist = np.array([dist[g].mean() for g in grupos])
    Y = np.array([Y[g[0]] for g in grupos])

    H, ub = 1.1e-3, 1e-3
    y = H - dist * 1e-6
    u = 6 * ub * (y / H) * (1 - y / H) * 1e3  # mm/s
    return dist, Y, u


VIRGULA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def estilo(ax):
    ax.xaxis.set_major_formatter(VIRGULA)
    ax.set_ylim(LIMITE_UM, 0)  # parede catalitica no topo
    ax.grid(True, color=TINTA3, alpha=0.22, linewidth=0.6)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA3)
        ax.spines[lado].set_linewidth(0.8)
    ax.tick_params(colors=TINTA2, labelsize=9, length=3, width=0.8)


def main():
    dist, Y, u = carregar()
    peso = u * (Y_IN - Y)
    pico = dist[np.argmax(peso)]
    delta = dist[np.argmax((Y_IN - Y) > 1e-4)] if np.any((Y_IN - Y) > 1e-4) else np.nan
    delta = dist[(Y_IN - Y) > 1e-4].max()

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 4.9), sharey=True)
    fig.patch.set_facecolor("#fcfcfb")
    for ax in axes:
        ax.set_facecolor("#fcfcfb")
        estilo(ax)

    # ---- (a) fracao massica de TG ------------------------------------------
    a = axes[0]
    a.plot(Y, dist, color=AZUL, linewidth=2.0, solid_capstyle="round")
    a.axvline(Y_IN, color=TINTA3, linewidth=1.0, linestyle=(0, (4, 3)))
    a.set_xlim(0.38, 0.86)
    a.set_xlabel("fração mássica de TG  [–]", fontsize=9.5, color=TINTA2)
    a.set_ylabel("distância da parede catalítica  [µm]", fontsize=9.5, color=TINTA2)
    a.set_title("(a)  empobrecimento", fontsize=10.5, color=TINTA, loc="left", pad=9)
    a.plot([Y[0]], [dist[0]], "o", color=AZUL, markersize=5.5,
           markeredgecolor="#fcfcfb", markeredgewidth=1.4, zorder=5)
    a.annotate(f"{Y[0]:.3f} na parede   (−{(1 - Y[0] / Y_IN) * 100:.0f} %)".replace(".", ","),
               xy=(Y[0], dist[0]), xytext=(0.425, 132),
               fontsize=8.5, color=TINTA2, va="center", ha="left",
               arrowprops=dict(arrowstyle="-", color=TINTA3, linewidth=0.8,
                               shrinkA=4, shrinkB=4,
                               connectionstyle="angle,angleA=0,angleB=90,rad=0"))
    a.text(0.812, 372, "alimentação 0,8194", fontsize=8.5, color=TINTA2,
           ha="right", va="center")

    # ---- (b) velocidade ----------------------------------------------------
    b = axes[1]
    b.plot(u, dist, color=LARANJA, linewidth=2.0, solid_capstyle="round")
    b.set_xlim(0, 1.55)
    b.set_xlabel("velocidade axial  [mm s$^{-1}$]", fontsize=9.5, color=TINTA2)
    b.set_title("(b)  transporte convectivo", fontsize=10.5, color=TINTA,
                loc="left", pad=9)
    i11 = int(np.argmin(np.abs(dist - 11.0)))
    b.plot([u[i11]], [dist[i11]], "o", color=LARANJA, markersize=5.5,
           markeredgecolor="#fcfcfb", markeredgewidth=1.4, zorder=5)
    b.annotate(f"{u[i11]:.3f} mm s⁻¹ a {dist[i11]:.0f} µm".replace(".", ",")
               + "\n4 % da velocidade do núcleo",
               xy=(u[i11], dist[i11]), xytext=(0.10, 238),
               fontsize=8.5, color=TINTA2, va="center", ha="left",
               arrowprops=dict(arrowstyle="-", color=TINTA3, linewidth=0.8,
                               shrinkA=4, shrinkB=4,
                               connectionstyle="angle,angleA=0,angleB=90,rad=0"))

    # ---- (c) peso na media ponderada por vazao -----------------------------
    c = axes[2]
    c.fill_betweenx(dist, 0, peso / peso.max(), color=AGUA, alpha=0.20, linewidth=0)
    c.plot(peso / peso.max(), dist, color=AGUA, linewidth=2.0, solid_capstyle="round")
    c.set_xlim(0, 1.12)
    c.set_xlabel("contribuição local  $u\\,(Y_{in}-Y)$  [normalizada]",
                 fontsize=9.5, color=TINTA2)
    c.set_title("(c)  peso na média por vazão", fontsize=10.5, color=TINTA,
                loc="left", pad=9)
    c.plot([1.0], [pico], "o", color=AGUA, markersize=5.5,
           markeredgecolor="#fcfcfb", markeredgewidth=1.4, zorder=5)
    c.annotate(f"máximo a {pico:.0f} µm da parede —\nnão na parede, onde a\nconversão de fato ocorre",
               xy=(1.0, pico), xytext=(0.09, 236),
               fontsize=8.5, color=TINTA2, va="center", ha="left",
               arrowprops=dict(arrowstyle="-", color=TINTA3, linewidth=0.8,
                               shrinkA=4, shrinkB=4,
                               connectionstyle="angle,angleA=0,angleB=90,rad=0"))

    # ---- rodape ------------------------------------------------------------
    fig.suptitle("Camada-limite de concentração no canal monolítico de CaO",
                 fontsize=12.5, color=TINTA, x=0.055, ha="left", y=0.975)
    fig.text(0.055, 0.905,
             f"Star-CCM+, x = 49 mm, t = 150 s · Da = 0,74 · Sc = 1,7×10⁵ · "
             f"camada empobrecida {delta:.0f} µm",
             fontsize=9, color=TINTA2, ha="left")

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.865))
    for ext in ("pdf", "png"):
        fig.savefig(f"{SAIDA}.{ext}", dpi=200, facecolor=fig.get_facecolor())
    print(f"gravado: {SAIDA}.pdf / .png")
    print(f"  camada empobrecida   {delta:.0f} µm")
    print(f"  pico da contribuicao {pico:.0f} µm da parede")
    print(f"  Y na parede          {Y[0]:.4f}")


if __name__ == "__main__":
    main()
