"""
video_LES.py
============
Monta o vídeo do LES (formato 4:5, 1080 × 1350, bom para o LinkedIn) a partir dos
hardcopies PNG das cenas do STAR-CCM+ (V_alpha, V_pH, V_vort) e, opcionalmente,
da curva de pH no sensor (monitor exportado em CSV) contra o experimento de
Darmana et al. (2007).

Cada quadro:  título | três painéis (α_G, pH, vorticidade) | curva pH(t) que
"se desenha" até o instante do quadro.

Uso típico (no PC da CAExperts, com Python):
    pip install matplotlib imageio imageio-ffmpeg pillow
    python video_LES.py --pastas hc/V_alpha hc/V_pH hc/V_vort \
        --dt 0.1 --t-troca 8 --ph-csv pH_Sensor.csv --saida darmana_LES.mp4 --gif

Os PNGs de cada pasta são ordenados pelo ÚLTIMO número no nome do arquivo
(o STAR põe o passo ou o tempo no nome). O tempo de cada quadro é
t = t0 + i·dt, com dt = intervalo entre hardcopies (20 passos × 5 ms = 0,1 s).
"""
import argparse
import re
from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

AQUI = Path(__file__).parent
EXP_PH = AQUI / "dados_literatura" / "pH_experimento_E2.csv"


def ultimo_numero(p: Path) -> float:
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", p.stem)
    return float(nums[-1]) if nums else 0.0


def lista_pngs(pasta: Path):
    arqs = sorted(pasta.glob("*.png"), key=ultimo_numero)
    if not arqs:
        raise SystemExit(f"nenhum PNG em {pasta}")
    return arqs


def recorta_branco(img: np.ndarray, tol=245, margem=6) -> np.ndarray:
    """Remove a borda branca do hardcopy (mantém coluna + barra de cores)."""
    cinza = img[..., :3].mean(axis=2)
    ys, xs = np.where(cinza < tol)
    if ys.size == 0:
        return img
    y0, y1 = max(ys.min() - margem, 0), min(ys.max() + margem, img.shape[0])
    x0, x1 = max(xs.min() - margem, 0), min(xs.max() + margem, img.shape[1])
    return img[y0:y1, x0:x1]


def le_csv_2col(caminho: Path):
    """Lê as duas primeiras colunas numéricas de um CSV (export de monitor do STAR ou dados)."""
    dados = np.genfromtxt(caminho, delimiter=",", skip_header=1, usecols=(0, 1))
    dados = dados[np.isfinite(dados).all(axis=1)]
    return dados[np.argsort(dados[:, 0])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pastas", nargs="+", required=True, help="pastas de hardcopy, uma por painel")
    ap.add_argument("--titulos", nargs="+",
                    default=["Fração de gás  α$_G$", "pH do líquido", "Vorticidade (água)"])
    ap.add_argument("--t0", type=float, default=0.0, help="tempo do primeiro hardcopy (s)")
    ap.add_argument("--dt", type=float, default=0.1, help="intervalo entre hardcopies (s)")
    ap.add_argument("--t-troca", type=float, default=8.0, help="instante da troca N2 → CO2 (s)")
    ap.add_argument("--ph-csv", type=Path, help="monitor pH_Sensor exportado (tempo, pH)")
    ap.add_argument("--ph-rans-csv", type=Path, help="pH_Sensor do RANS (opcional)")
    ap.add_argument("--t-troca-rans", type=float, default=20.0)
    ap.add_argument("--passo", type=int, default=1, help="usar 1 a cada N quadros")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--saida", type=Path, default=Path("darmana_LES.mp4"))
    ap.add_argument("--gif", action="store_true", help="também gera um GIF (1 a cada 3 quadros, 540 px)")
    ap.add_argument("--legenda", default="Coluna de bolhas reativa CO$_2$/NaOH  ·  LES Euler–Euler (WALE)  ·  STAR-CCM+")
    a = ap.parse_args()

    listas = [lista_pngs(Path(p)) for p in a.pastas]
    n = min(len(l) for l in listas)
    if len({len(l) for l in listas}) > 1:
        print(f"aviso: pastas com números diferentes de quadros; usando {n}")
    idx = list(range(0, n, a.passo))
    titulos = (a.titulos + [""] * len(listas))[: len(listas)]

    ph = le_csv_2col(a.ph_csv) if a.ph_csv else None
    ph_rans = le_csv_2col(a.ph_rans_csv) if a.ph_rans_csv else None
    exp = le_csv_2col(EXP_PH) if EXP_PH.exists() else None

    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor="white")
    tem_curva = ph is not None
    gs = fig.add_gridspec(2 if tem_curva else 1, len(listas),
                          height_ratios=[3.2, 1] if tem_curva else [1],
                          left=0.04, right=0.96, top=0.885, bottom=0.06, hspace=0.18, wspace=0.04)
    eixos = [fig.add_subplot(gs[0, k]) for k in range(len(listas))]
    for ax, tit in zip(eixos, titulos):
        ax.set_axis_off()
        ax.set_title(tit, fontsize=15, pad=8)
    fig.text(0.5, 0.965, a.legenda, ha="center", va="center", fontsize=15, weight="bold")
    txt_t = fig.text(0.5, 0.937, "", ha="center", va="center", fontsize=14, color="#333")

    if tem_curva:
        axc = fig.add_subplot(gs[1, :])
        if exp is not None:
            axc.plot(exp[:, 0], exp[:, 1], "o", ms=3, color="#888", label="Experimento (Darmana et al., 2007)")
        if ph_rans is not None:
            axc.plot(ph_rans[:, 0] - a.t_troca_rans, ph_rans[:, 1], "--", lw=1.6, color="#d08c2a", label="RANS k-ε")
        (linha,) = axc.plot([], [], lw=2.4, color="#1f5fbf", label="LES WALE")
        (ponto,) = axc.plot([], [], "o", ms=7, color="#1f5fbf")
        tmax = max(ph[-1, 0] - a.t_troca, exp[-1, 0] if exp is not None else 0)
        axc.set_xlim(0, tmax * 1.02)
        axc.set_ylim(7.5, 13)
        axc.set_xlabel("tempo desde a entrada de CO$_2$ (s)", fontsize=12)
        axc.set_ylabel("pH no sensor", fontsize=12)
        axc.grid(alpha=0.3)
        axc.legend(loc="lower left", fontsize=10, frameon=False)

    imagens = [None] * len(listas)
    escritor = imageio.get_writer(a.saida, fps=a.fps, codec="libx264", quality=8,
                                  macro_block_size=2, pixelformat="yuv420p")
    quadros_gif = []
    for j, i in enumerate(idx):
        t = a.t0 + i * a.dt
        for k, (ax, lst) in enumerate(zip(eixos, listas)):
            img = recorta_branco(np.asarray(Image.open(lst[i]).convert("RGB")))
            if imagens[k] is None:
                imagens[k] = ax.imshow(img)
            else:
                imagens[k].set_data(img)
                imagens[k].set_extent((-0.5, img.shape[1] - 0.5, img.shape[0] - 0.5, -0.5))
        fase = "N$_2$ (desenvolvimento da pluma)" if t < a.t_troca else f"CO$_2$ há {t - a.t_troca:5.1f} s"
        txt_t.set_text(f"t = {t:6.1f} s   ·   {fase}")
        if tem_curva:
            m = ph[:, 0] <= t
            tt = ph[m, 0] - a.t_troca
            yy = ph[m, 1]
            ok = tt >= 0
            linha.set_data(tt[ok], yy[ok])
            ponto.set_data(tt[ok][-1:], yy[ok][-1:])
        fig.canvas.draw()
        quadro = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        escritor.append_data(quadro)
        if a.gif and j % 3 == 0:
            quadros_gif.append(Image.fromarray(quadro).resize((540, 675), Image.LANCZOS))
        if j % 100 == 0:
            print(f"quadro {j + 1}/{len(idx)}  t = {t:.1f} s")
    escritor.close()
    print("vídeo:", a.saida.resolve())
    if a.gif and quadros_gif:
        g = a.saida.with_suffix(".gif")
        quadros_gif[0].save(g, save_all=True, append_images=quadros_gif[1:],
                            duration=int(1000 * 3 / a.fps), loop=0, optimize=True)
        print("gif:", g.resolve())


if __name__ == "__main__":
    main()
