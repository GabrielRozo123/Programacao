"""
monta_animacao.py
=================
Monta vídeo (MP4) e GIF a partir dos hardcopies (PNG) salvos pelo
STAR-CCM+ durante a simulação. Opcionalmente junta duas cenas lado a lado
(ex.: fração de ar | velocidade da água) e escreve o tempo em cada quadro.

Uso:
    pip install imageio imageio-ffmpeg pillow
    python monta_animacao.py --cena1 frames/alpha --fps 20
    python monta_animacao.py --cena1 frames/alpha --cena2 frames/vel \
                             --dt-quadro 0.1 --t0 0 --saida coluna_Ug2

Os PNG de cada pasta são ordenados pelo número no nome do arquivo
(o STAR gera nomes como Scene_00001.png, Scene_00002.png, ...).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def lista_quadros(pasta: Path) -> list[Path]:
    arqs = [p for p in pasta.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")]

    def chave(p: Path):
        nums = re.findall(r"\d+", p.stem)
        return int(nums[-1]) if nums else 0

    arqs.sort(key=chave)
    if not arqs:
        raise SystemExit(f"nenhuma imagem em {pasta}")
    return arqs


def fonte(tam: int):
    for nome in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(nome, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def compoe(img1: Image.Image, img2: Image.Image | None, texto: str | None) -> Image.Image:
    img1 = img1.convert("RGB")
    if img2 is not None:
        img2 = img2.convert("RGB")
        h = max(img1.height, img2.height)
        tela = Image.new("RGB", (img1.width + img2.width, h), "white")
        tela.paste(img1, (0, 0))
        tela.paste(img2, (img1.width, 0))
    else:
        tela = img1
    if texto:
        d = ImageDraw.Draw(tela)
        f = fonte(max(18, tela.height // 30))
        d.text((15, 10), texto, fill="black", font=f, stroke_width=2, stroke_fill="white")
    # codec H.264 exige dimensões pares
    w, h = tela.size
    return tela.crop((0, 0, w - w % 2, h - h % 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cena1", type=Path, required=True, help="pasta com os PNG da cena 1")
    ap.add_argument("--cena2", type=Path, help="pasta com os PNG da cena 2 (lado a lado)")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--dt-quadro", type=float, default=0.1,
                    help="tempo físico entre quadros [s] (p/ escrever t na tela; 0 = não escreve)")
    ap.add_argument("--t0", type=float, default=0.0, help="tempo físico do 1º quadro [s]")
    ap.add_argument("--saida", default="animacao_coluna")
    ap.add_argument("--gif-largura", type=int, default=480,
                    help="largura do GIF (menor = arquivo menor)")
    a = ap.parse_args()

    q1 = lista_quadros(a.cena1)
    q2 = lista_quadros(a.cena2) if a.cena2 else None
    n = min(len(q1), len(q2)) if q2 else len(q1)
    print(f"{n} quadros → {n / a.fps:.1f} s de vídeo a {a.fps} fps")

    mp4 = imageio.get_writer(f"{a.saida}.mp4", fps=a.fps, codec="libx264",
                             quality=8, macro_block_size=1)
    quadros_gif = []
    for i in range(n):
        txt = f"t = {a.t0 + i * a.dt_quadro:5.1f} s" if a.dt_quadro > 0 else None
        img = compoe(Image.open(q1[i]), Image.open(q2[i]) if q2 else None, txt)
        mp4.append_data(np.asarray(img))
        if i % 2 == 0:  # GIF com metade dos quadros
            r = a.gif_largura / img.width
            quadros_gif.append(np.asarray(img.resize((a.gif_largura, int(img.height * r)))))
    mp4.close()
    imageio.mimsave(f"{a.saida}.gif", quadros_gif, duration=2 / a.fps, loop=0)
    print(f"gerado: {a.saida}.mp4 e {a.saida}.gif")


if __name__ == "__main__":
    main()
