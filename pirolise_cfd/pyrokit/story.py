"""Segmentos de vídeo do reator: a fita girando em corte, com o campo escolhido e textos sobrepostos.

No referencial da fita a solução é estacionária; no laboratório ela só gira junto com a fita. Cada quadro
é então a mesma solução girada de Ω·t (em câmera lenta, para o olho acompanhar), com a câmera orbitando
devagar. Os textos (título, barra de cores, legendas e números grandes) são desenhados com PIL.
"""
from __future__ import annotations

import math

import numpy as np

from .video import FFmpegPipe, _caption_alpha, _font, br, draw_lower_third, even_captions


def colorbar_strip(cw, field, label, size, s, fmt="{:.0f}"):
    """Barra de cores vertical (PIL RGBA) com rótulo e valores do campo renderizado."""
    from PIL import Image, ImageDraw
    f = cw.fields[field]
    lut = (f["lut"].cpu().numpy() * 255).astype(np.uint8)
    h, w = int(360 * s), int(22 * s)
    im = Image.new("RGBA", (int(220 * s), h + int(90 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = np.repeat(lut[::-1][np.linspace(0, len(lut) - 1, h).astype(int)][:, None, :], w, 1)
    im.paste(Image.fromarray(col), (0, int(50 * s)))
    d.text((0, 0), br(label), font=_font(int(24 * s), True), fill=(236, 240, 246, 255))
    lo, hi = f["lo"], f["hi"]
    for k, frac in enumerate((1.0, 0.5, 0.0)):
        v = lo + frac * (hi - lo)
        v = 10 ** v if f["log"] else v
        txt = br(fmt.format(v)) if not f["log"] else br(f"{v:.0e}".replace("e-0", "e-").replace("e+0", "e"))
        y = int(50 * s) + int((1 - frac) * (h - 1))
        d.text((w + int(12 * s), y), txt, font=_font(int(20 * s)), fill=(200, 208, 220, 255), anchor="lm")
    return im


def render_rotation(cw, path, field, title="", subtitle="", kicker="", captions=None, cbar_label="",
                    cbar_fmt="{:.0f}", seconds=8.0, fps=30, size=(1920, 1080), turns=0.5, az0=-70.0, az1=-40.0,
                    el=24.0, ssaa=1.25, big=None, accent=(255, 176, 64), handle="", clean_path=None, progress=True):
    """Vídeo da fita girando `turns` voltas em `seconds` s com a câmera orbitando de az0 a az1.

    big: lista de (valor, rótulo) mostrados em destaque à direita (o resultado aparece logo de cara)."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    n = int(round(seconds * fps))
    caps = captions or []
    if caps and isinstance(caps[0], str):
        caps = even_captions(caps, seconds)
    static = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(static)
    y = int(40 * s)
    if kicker:
        d.text((int(60 * s), y), br(kicker).upper(), font=_font(int(24 * s), True), fill=accent + (255,))
        y += int(38 * s)
    if title:
        d.text((int(58 * s), y), br(title), font=_font(int(46 * s), True), fill=(236, 240, 246, 255))
    if subtitle:
        d.text((int(60 * s), y + int(62 * s)), br(subtitle), font=_font(int(24 * s)), fill=(150, 160, 175, 255))
    if cbar_label and field in cw.fields:
        static.alpha_composite(colorbar_strip(cw, field, cbar_label, size, s, cbar_fmt), (int(60 * s), int(330 * s)))
    if handle:
        d.text((W - int(60 * s), H - int(40 * s)), handle, font=_font(int(22 * s)), fill=(118, 126, 140, 255),
               anchor="rb")
    pipe = FFmpegPipe(path, size, fps, crf=16)
    clean = FFmpegPipe(clean_path, size, fps, crf=20) if clean_path else None
    for i in range(n):
        t = i / fps
        u = t / max(seconds, 1e-9)
        ease = 0.5 - 0.5 * math.cos(math.pi * u)
        theta = 2 * math.pi * turns * u
        az = az0 + (az1 - az0) * ease
        rgb = cw.render(field, theta=theta, az=az, el=el, size=size, ssaa=ssaa)
        if clean is not None:
            clean.write(rgb)
        im = Image.fromarray(rgb).convert("RGBA")
        im.alpha_composite(static)
        if big:
            dd = ImageDraw.Draw(im)
            x = W - int(70 * s)
            yb = int(250 * s)
            for k, (val, lab) in enumerate(big):
                a = float(np.clip((t - 0.25 - 0.35 * k) / 0.5, 0, 1) * np.clip((seconds - t) / 0.4, 0, 1))
                if a <= 0:
                    continue
                dd.text((x, yb + k * int(190 * s)), br(val), font=_font(int(88 * s), True),
                        fill=accent + (int(255 * a),), anchor="ra")
                dd.text((x, yb + k * int(190 * s) + int(104 * s)), br(lab), font=_font(int(28 * s)),
                        fill=(220, 226, 236, int(255 * a)), anchor="ra")
        if caps:
            text, a = _caption_alpha(caps, t)
            draw_lower_third(im, text, a, s, accent)
        pipe.write(np.asarray(im.convert("RGB")))
        if progress and (i % max(1, n // 10) == 0):
            print(f"  {path}: quadro {i + 1}/{n}", flush=True)
    if clean is not None:
        clean.close()
    return pipe.close()


def cover_image(cw, path, field, title, lines, size=(1920, 1080), theta=0.6, az=-55.0, el=24.0, ssaa=1.5,
                accent=(255, 176, 64), subtitle=""):
    """Capa (miniatura do post): o reator em corte à esquerda e, à direita, o título e o resultado
    principal em letras grandes."""
    from PIL import Image, ImageDraw
    from .video import _wrap_balanced
    W, H = size
    s = H / 1080.0
    rgb = cw.render(field, theta=theta, az=az, el=el, size=size, ssaa=ssaa, shift=0.17, dist=3.0 * cw.tank.T)
    im = Image.fromarray(rgb).convert("RGBA")
    d = ImageDraw.Draw(im)
    x = int(0.60 * W)
    f_t = _font(int(54 * s), True)
    y = int(90 * s)
    for ln in _wrap_balanced(d, br(title), f_t, int(0.37 * W)):
        d.text((x, y), ln, font=f_t, fill=(240, 244, 250, 255))
        y += int(64 * s)
    if subtitle:
        d.text((x, y + int(8 * s)), br(subtitle), font=_font(int(26 * s)), fill=(170, 180, 195, 255))
        y += int(40 * s)
    y += int(50 * s)
    for val, lab in lines:
        d.text((x, y), br(val), font=_font(int(96 * s), True), fill=accent + (255,))
        d.text((x, y + int(112 * s)), br(lab), font=_font(int(30 * s)), fill=(225, 230, 240, 255))
        y += int(200 * s)
    im.convert("RGB").save(path)
    return path
