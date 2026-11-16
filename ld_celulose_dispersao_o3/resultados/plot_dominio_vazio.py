"""
plot_dominio_vazio.py — perfis de U e k do teste do domínio vazio (entrada, centro, saída) contra Richards & Hoxey.

Uso: python3 plot_dominio_vazio.py <pasta com perfil_U.csv e perfil_k.csv> [--saida figura.png]
     (CSV exportados do STAR: Linha_Centro, Linha_entrada, Linha_Saída, coluna de altura + valor)
Os valores do STAR são por célula (constantes por trechos): cada trecho vira um ponto na altura média do trecho;
o trecho que começa em z = 0 é a 1ª célula (prisma de 2,5 m) e vai para o centro dela, 1,25 m.
"""
import argparse, csv, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("pasta")
ap.add_argument("--saida", default=None)
ap.add_argument("--uref", type=float, default=1.9)
ap.add_argument("--zref", type=float, default=10.0)
ap.add_argument("--z0", type=float, default=0.03)
ap.add_argument("--cmu", type=float, default=0.09)
ap.add_argument("--prisma", type=float, default=2.5, help="espessura da 1ª célula [m]")
a = ap.parse_args()

KAPPA = 0.42
us = KAPPA * a.uref / math.log((a.zref + a.z0) / a.z0)
k_teo = us ** 2 / math.sqrt(a.cmu)
U_teo = lambda z: us / KAPPA * math.log((z + a.z0) / a.z0)


def ler(arq):
    linhas = [l for l in csv.reader(open(arq, encoding="utf-8")) if l][1:]
    cols = {"entrada": 2, "centro": 0, "saída": 4}
    return {n: [(float(l[i]), float(l[i + 1])) for l in linhas] for n, i in cols.items()}


def trechos(pontos):  # agrupa valores iguais consecutivos (mesma célula)
    out, run = [], [pontos[0]]
    for z, v in pontos[1:]:
        if abs(v - run[-1][1]) < 1e-12:
            run.append((z, v))
        else:
            out.append(run); run = [(z, v)]
    out.append(run)
    res = []
    for r in out:
        z = a.prisma / 2 if r[0][0] == 0 else sum(p[0] for p in r) / len(r)
        res.append((z, r[0][1]))
    return res


U = ler(os.path.join(a.pasta, "perfil_U.csv"))
K = ler(os.path.join(a.pasta, "perfil_k.csv"))

SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COR = {"entrada": "#2a78d6", "centro": "#eb6834", "saída": "#1baf7a"}
MARK = {"entrada": "o", "centro": "s", "saída": "^"}

plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5.6), sharey=True)

zs = [10 ** (i / 50) for i in range(0, 132)]  # 1 a ~410 m
ax1.plot([U_teo(z) for z in zs], zs, color=INK, lw=2, ls="--", label="Richards & Hoxey (teórico)", zorder=3)
for n in ("entrada", "centro", "saída"):
    t = trechos(U[n])
    ax1.plot([v for _, v in t], [z for z, _ in t], ls="none", marker=MARK[n], ms=6, mfc="none", mew=1.4,
             color=COR[n], label=f"CFD, {n}", zorder=4)
ax1.set_xlabel("Velocidade U (m/s)")
ax1.set_ylabel("Altura z (m)")
ax1.set_title("Velocidade", loc="left", color=INK, fontsize=11)

ax2.axvspan(0.85, 1.15, color="#ebeae6", zorder=0, label="critério ±15 %")
ax2.axvline(1.0, color=INK, lw=2, ls="--", zorder=3)
for n in ("entrada", "centro", "saída"):
    t = trechos(K[n])
    ax2.plot([v / k_teo for _, v in t], [z for z, _ in t], ls="none", marker=MARK[n], ms=6, mfc="none", mew=1.4,
             color=COR[n], zorder=4)
ax2.set_xlabel("k / k teórico")
ax2.set_xlim(0.6, 1.3)
ax2.set_title("Energia cinética turbulenta", loc="left", color=INK, fontsize=11)
ax2.fill_betweenx([10, 70], 0.69, 0.86, color="#c3c2b7", alpha=0.6, lw=0, zorder=1)
ax2.text(0.69, 80, "rodadas 1 a 3\n(centro e saída)", color=INK2, fontsize=9, va="bottom")
ax2.text(1.06, 1.7, "pico na 2ª célula\n(+19 %)", color=INK2, fontsize=9, va="center")

from matplotlib.ticker import FuncFormatter
virg = lambda casas: FuncFormatter(lambda v, _: f"{v:.{casas}f}".replace(".", ","))
ax1.xaxis.set_major_formatter(virg(2))
ax2.xaxis.set_major_formatter(virg(1))
for ax in (ax1, ax2):
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_ylim(1, 400)
    ax.grid(True, which="major", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
fig.legend(h1 + h2, l1 + l2, loc="upper center", ncol=5, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.0))
br = lambda v: f"{v:g}".replace(".", ",")
fig.text(0.5, 0.005, f"Domínio vazio, rodada 4: modelo ABL do STAR, {br(a.uref)} m/s a {br(a.zref)} m, z₀ = {br(a.z0)} m, "
         f"Cμ = {br(a.cmu)}, 1000 iterações. k teórico = {k_teo:.4f} m²/s². Faixa cinza: k das rodadas 1 a 3 (0,69 a 0,86)."
         .replace("0.0", "0,0"), ha="center", color=INK2, fontsize=8.5)
fig.tight_layout(rect=(0, 0.03, 1, 0.94))
saida = a.saida or os.path.join(a.pasta, "perfis_U_k.png")
fig.savefig(saida, dpi=200)
print("figura:", saida)
