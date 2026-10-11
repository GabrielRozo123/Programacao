"""Parado × girando: dois cortes lado a lado no mesmo instante da batelada (o tema da matéria da KINTEK).

Mesma carga, mesma fornalha e mesmo controle; só muda a rotação. No tambor parado a pilha só conduz calor:
a camada junto à parede quente funde, carboniza e isola, o miolo continua frio e o casco sob a chama
passa do limite do aço. Girando, cada volta renova o contato da carga com a parede e a temperatura fica
uniforme na seção.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from .scene import CrossSection, colorbar, thermal_rgb
from .video import FFmpegPipe, _font, br, draw_lower_third


def _snap_at(b, t_h):
    ts = np.array([sn["t"] / 3600 for sn in b.snaps])
    i = int(np.argmin(np.abs(ts - t_h)))
    return b.snaps[i], ts[i] >= t_h - 0.05 or i == len(ts) - 1


def bed_T_function(b, sn, mid):
    """T(σ) da carga na fatia do meio: σ = 0 na parede molhada, 1 na superfície livre."""
    T = b._slice_view(sn["T"])[mid] - 273.15
    if T.size == 1:
        return lambda sig: np.full_like(sig, T[0])
    v = b._slice_view(sn["vol"])[mid]
    c = np.cumsum(v) / max(v.sum(), 1e-12)
    centers = c - 0.5 * v / max(v.sum(), 1e-12)
    return lambda sig: np.interp(sig, centers, T)


def char_function(b, sn, mid):
    ch = b._slice_view(sn["char"])[mid]
    tot = b._slice_view(sn["total"])[mid]
    f = ch / np.maximum(tot, 1e-12)
    if f.size == 1:
        return lambda sig: np.full_like(sig, min(f[0] * 1.5, 0.9))
    v = b._slice_view(sn["vol"])[mid]
    c = np.cumsum(v) / max(v.sum(), 1e-12)
    centers = c - 0.5 * v / max(v.sum(), 1e-12)
    return lambda sig: np.clip(np.interp(sig, centers, f) * 1.5, 0, 0.9)


def draw_section(cs: CrossSection, b, sn, theta_vis=0.0, gas=None):
    mid = b.cfg.nx // 2
    img, _ = cs.furnace_layer(T_refr_C=float(np.mean(sn["Tr_fur"])) - 273.15, gas=gas)
    phi_lab = (b.phi0 + sn["theta"] + math.pi) % (2 * math.pi) - math.pi
    o = np.argsort(phi_lab)
    nphi = len(phi_lab)
    bins = (np.arange(nphi) + 0.5) * 2 * math.pi / nphi - math.pi
    Ts = np.interp(bins, phi_lab[o], sn["Ts"][mid][o] - 273.15, period=2 * math.pi)
    img = cs.drum_layer(img, Ts, 0.0, wall_px=12)
    img, _ = cs.bed_raster(img, float(sn["F"][mid]), float(sn["beta"][mid]), bed_T_function(b, sn, mid),
                           char_function(b, sn, mid))
    return img, float(Ts.max())


def render_compare(b_rot, b_est, path, seconds=18.0, fps=30, size=(1920, 1080), t_end_h=None, les=None):
    W, H = size
    s = H / 1080
    t_end = t_end_h or max(b_est.log[-1]["t_h"], b_rot.log[-1]["t_h"])
    box = dict(half_width=1.0, z_bot=-1.30, z_top=0.95, wall=0.17)
    cs = CrossSection(b_rot.drum, box, size=(int(820 * s), int(820 * s)))
    cbar = colorbar(int(520 * s), int(64 * s), s=s)
    pipe = FFmpegPipe(path, size, fps)
    n = int(seconds * fps)
    lr = np.array([r["t_h"] for r in b_rot.log]); le = np.array([r["t_h"] for r in b_est.log])
    for k in range(n):
        t_h = t_end * k / (n - 1)
        canvas = Image.new("RGBA", size, (12, 14, 20, 255))
        d = ImageDraw.Draw(canvas)
        d.text((int(40 * s), int(22 * s)), "Por que girar? Mesma carga, mesma fornalha, só muda a rotação",
               font=_font(int(36 * s), True), fill=(245, 245, 245))
        for j, (b, lab, ts_log) in enumerate(((b_est, "tambor parado", le), (b_rot, f"girando a {b_rot.rpm:.1f} rpm, 6 aletas".replace(".", ","), lr))):
            sn, _ = _snap_at(b, t_h)
            gas = None
            if les is not None and t_h <= ts_log[-1]:
                gain = float(np.clip(sn["Q_fire"] / les["Q"], 0.08, 1.2)) ** 0.6
                gas = (les["T"][k % len(les["T"])], les["yc"], les["zc"], gain)
            img, Tmax = draw_section(cs, b, sn, gas=gas)
            x0 = int((60 + j * 920) * s)
            canvas.paste(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), (x0, int(120 * s)))
            done = t_h > ts_log[-1] + 1e-6
            T_c = float(np.interp(min(t_h, ts_log[-1]), ts_log, [r["T_carga"] for r in b.log]))
            oil = float(np.interp(min(t_h, ts_log[-1]), ts_log, [r["oleo_kg"] for r in b.log]))
            Tsm = float(np.interp(min(t_h, ts_log[-1]), ts_log, [r["T_casco_max"] for r in b.log]))
            d.text((x0, int(90 * s)), lab, font=_font(int(28 * s), True), fill=(255, 205, 120) if j else (160, 200, 255))
            y = int(950 * s)
            d.text((x0, y), br(f"carga {T_c:.0f} °C · óleo {oil:.0f} kg"), font=_font(int(26 * s), True), fill=(240, 240, 240))
            hot = (255, 110, 100) if Tsm > 475 else (200, 205, 215)
            d.text((x0, y + int(36 * s)), br(f"casco no ponto mais quente: {Tsm:.0f} °C"), font=_font(int(22 * s)), fill=hot)
            if done:
                d.text((x0 + int(520 * s), int(90 * s)), br(f"terminou em {ts_log[-1]:.1f} h"), font=_font(int(26 * s), True),
                       fill=(140, 255, 160))
        d.text((int(1700 * s), int(14 * s)), br(f"{t_h:4.1f} h"), font=_font(int(48 * s), True), fill=(255, 255, 255))
        canvas.paste(cbar, (int(700 * s), int(1010 * s)), cbar)
        pipe.write(np.asarray(canvas.convert("RGB")))
    return pipe.close()
