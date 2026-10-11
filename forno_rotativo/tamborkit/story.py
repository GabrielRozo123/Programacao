"""Segmentos do vídeo e figuras do relatório: DEM em tempo real, chamas da LES, curvas e tabela de validação."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from .scene import CrossSection, colorbar, draw_overlay, thermal_rgb
from .timelapse import MATERIAL_RGB
from .video import FFmpegPipe, _font, _wrap, br, draw_lower_third, even_captions, _caption_alpha


def _title(d, text, x, y, s, width=800, size=36):
    f = _font(int(size * s), True)
    lines = _wrap(d, br(text), f, int(width * s))
    for i, ln in enumerate(lines):
        d.text((x, y + i * int(size * 1.25 * s)), ln, font=f, fill=(245, 245, 245))
    return y + len(lines) * int(size * 1.25 * s)

BOX = dict(half_width=1.0, z_bot=-1.30, z_top=0.95, wall=0.17)


def render_dem_segment(drum, dem: dict, path, seconds=9.0, fps=30, size=(1920, 1080), title="", captions=(),
                       speed_label=""):
    """Partículas do DEM (cores dos materiais) girando com o tambor e as aletas, em corte."""
    W, H = size
    s = H / 1080
    cs = CrossSection(drum, dict(half_width=0.80, z_bot=-0.80, z_top=0.80, wall=0.04), size=(int(980 * s), int(980 * s)))
    rgb_mat = np.array([MATERIAL_RGB.get(dem["names"][i], (180, 180, 170)) for i in dem["label"]], float)
    frames = dem["frames"]
    n = int(seconds * fps)
    caps = even_captions(list(captions), seconds) if captions else []
    pipe = FFmpegPipe(path, size, fps)
    for k in range(n):
        fr = frames[k % len(frames)]
        img = np.zeros((cs.H, cs.W, 3), np.float32) + np.array([14, 16, 22], np.float32)
        img = cs.drum_layer(img, np.full(36, 120.0), 0.0, wall_px=14 * s)
        x = fr["x"].astype(np.float32)
        img, _ = cs.bed_particles(img, x, dem["r"], rgb_mat)
        scene = draw_overlay(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), cs, fr["theta"])
        canvas = Image.new("RGBA", size, (12, 14, 20, 255))
        canvas.paste(scene, (int(60 * s), int(60 * s)))
        d = ImageDraw.Draw(canvas)
        y = _title(d, title, int(1080 * s), int(70 * s), s) + int(24 * s)
        for name, c in MATERIAL_RGB.items():
            if name not in dem["names"]:
                continue
            d.ellipse([int(1090 * s), y, int(1112 * s), y + int(22 * s)], fill=tuple(int(v) for v in c))
            d.text((int(1125 * s), y - 2), {"filme": "filmes e sacolas", "rigido": "plástico rígido", "isopor": "isopor (EPS)",
                                            "pet": "garrafas PET", "organico": "madeira, papel, coco", "borracha": "borracha",
                                            "areia": "areia e conchas"}.get(name, name), font=_font(int(22 * s)),
                   fill=(225, 228, 235))
            y += int(36 * s)
        st = dem.get("stats", {})
        lines = []
        if st:
            lines = [f"ângulo dinâmico do leito: {st['beta_deg']:.0f}°",
                     f"parede coberta pela carga: {100 * st['covered_frac']:.0f} % do perímetro",
                     f"cada ponto do casco passa {st['passive_contact_s'] * dem['rpm'] / 0.8:.0f} s sob a carga por volta",
                     f"em queda nas cortinas: {100 * st['airborne_frac']:.1f} % dos pedaços",
                     f"mistura (índice de Lacey) no trecho mostrado: {dem.get('lacey', float('nan')):.2f}"]
        for i, ln in enumerate(lines):
            d.text((int(1090 * s), int(470 * s) + i * int(44 * s)), br(ln), font=_font(int(25 * s)), fill=(240, 240, 240))
        if speed_label:
            for i, ln in enumerate(_wrap(d, br(speed_label), _font(int(20 * s)), int(780 * s))):
                d.text((int(1090 * s), int(740 * s) + i * int(26 * s)), ln, font=_font(int(20 * s)), fill=(170, 175, 185))
        if caps:
            txt, a = _caption_alpha(caps, k / fps)
            draw_lower_third(canvas, txt, a, s * 0.85, y_bottom=int(1030 * s), max_w=int(760 * s), x0=int(1070 * s))
        pipe.write(np.asarray(canvas.convert("RGB")))
    return pipe.close()


def render_flame_segment(drum, les: dict, path, Ts_C=500.0, seconds=8.0, fps=30, size=(1920, 1080), title="",
                         captions=(), info=()):
    """Chamas da LES (fatia no plano de um queimador) sob o tambor, com o casco a T_s."""
    W, H = size
    s = H / 1080
    cs = CrossSection(drum, BOX, size=(int(1000 * s), int(1000 * s)))
    n = int(seconds * fps)
    caps = even_captions(list(captions), seconds) if captions else []
    pipe = FFmpegPipe(path, size, fps)
    for k in range(n):
        T = les["T"][k % len(les["T"])]
        img, _ = cs.furnace_layer(T_refr_C=750.0, gas=(T, les["yc"], les["zc"]))
        img = cs.drum_layer(img, np.full(36, Ts_C), 0.0, wall_px=12 * s)
        scene = draw_overlay(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), cs, 2 * math.pi * k / fps / 20)
        canvas = Image.new("RGBA", size, (12, 14, 20, 255))
        canvas.paste(scene, (int(40 * s), int(50 * s)))
        d = ImageDraw.Draw(canvas)
        y = _title(d, title, int(1080 * s), int(70 * s), s) + int(30 * s)
        for i, ln in enumerate(info):
            d.text((int(1090 * s), y + i * int(46 * s)), br(ln), font=_font(int(26 * s)), fill=(235, 235, 235))
        if caps:
            txt, a = _caption_alpha(caps, k / fps)
            draw_lower_third(canvas, txt, a, s * 0.85, y_bottom=int(1030 * s), max_w=int(760 * s), x0=int(1070 * s))
        pipe.write(np.asarray(canvas.convert("RGB")))
    return pipe.close()


# ----------------------------------------------------------------- figuras
def _style(plt):
    plt.rcParams.update({"figure.facecolor": "#0c0e14", "axes.facecolor": "#0c0e14", "axes.edgecolor": "#888",
                         "axes.labelcolor": "w", "xtick.color": "w", "ytick.color": "w", "text.color": "w",
                         "font.size": 13, "axes.grid": True, "grid.alpha": 0.15})


def curves_figure(runs: dict, path, title="Temperatura da carga e óleo coletado"):
    """runs: {rótulo: log}."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _style(plt)
    fig, axs = plt.subplots(1, 2, figsize=(16, 7), dpi=120)
    cols = ["#ffb347", "#7fd3ff", "#b0ff7a", "#ff7a9c", "#d0a0ff"]
    for (lab, log), c in zip(runs.items(), cols):
        t = [r["t_h"] for r in log]
        axs[0].plot(t, [r["T_carga"] for r in log], color=c, lw=2.4, label=lab)
        axs[0].plot(t, [r["T_casco_max"] for r in log], color=c, lw=1.2, ls="--", alpha=0.8)
        axs[1].plot(t, [r["oleo_kg"] for r in log], color=c, lw=2.4, label=lab)
    axs[0].axhline(475, color="#ff5e5e", lw=0.8, alpha=0.6)
    axs[0].text(0.2, 482, "limite de serviço do aço do casco (Q345R)", color="#ff9e9e", fontsize=11)
    axs[0].set_ylabel("°C (cheia: carga; tracejada: ponto mais quente do casco)")
    axs[1].set_ylabel("óleo coletado (kg)")
    for ax in axs:
        ax.set_xlabel("tempo de batelada (h)")
        ax.legend(frameon=False)
    fig.suptitle(title, fontsize=18)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def validation_figure(rows, path, title="Validação"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _style(plt)
    n = len(rows)
    fig, ax = plt.subplots(figsize=(16, 0.52 * n + 1.6), dpi=110)
    ax.axis("off")
    k = sum(r["ok"] for r in rows)
    ax.set_title(br(f"{title}: {k} de {n} dentro do alvo"), fontsize=19, loc="left")
    for i, r in enumerate(rows):
        y = 1 - (i + 0.8) / (n + 0.5)
        v = r["modelo"]
        vs = br(f"{v:.3g}") + (f" {r['unidade']}" if r["unidade"] else "")
        ax.text(0.0, y, "✔" if r["ok"] else "✘", color="#7dff9a" if r["ok"] else "#ff7a7a", fontsize=15,
                transform=ax.transAxes, va="center")
        ax.text(0.03, y, r["grupo"], fontsize=12, color="#aab", transform=ax.transAxes, va="center")
        ax.text(0.16, y, br(r["item"]), fontsize=13, transform=ax.transAxes, va="center")
        ax.text(0.62, y, vs, fontsize=13, transform=ax.transAxes, va="center", color="#ffd27a")
        ax.text(0.74, y, br(f"alvo {r['alvo']}"), fontsize=12, transform=ax.transAxes, va="center", color="#ccd")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def flux_figure(flux: dict, les: dict, path):
    """Mapa de fluxo no casco (fatia × ângulo) e campo médio de T da LES num corte longitudinal."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _style(plt)
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.5), dpi=120)
    q = flux["q"] / 1e3
    im = axs[0].pcolormesh(flux["x"], flux["phi"], q.T, cmap="inferno", shading="nearest")
    axs[0].set_xlabel("posição ao longo do tambor (m)"); axs[0].set_ylabel("ângulo no casco (°; −90 = embaixo)")
    plt.colorbar(im, ax=axs[0], label="fluxo para o casco (kW/m²)")
    Tm = les["Tmean"]
    j = Tm.shape[1] // 2
    im2 = axs[1].pcolormesh(les["xc"], les["zc"], (Tm[:, j, :] - 273.15).T, cmap="inferno", shading="nearest",
                            vmin=200, vmax=1500)
    axs[1].set_xlabel("x (m)"); axs[1].set_ylabel("z (m)")
    axs[1].set_aspect("equal")
    plt.colorbar(im2, ax=axs[1], label="T média do gás (°C), plano y = 0")
    fig.suptitle("LES da fornalha: onde o calor entra no tambor", fontsize=17)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
