"""Segmentos do vídeo e figuras do relatório: DEM em tempo real, chamas da LES, curvas e tabela de validação."""
from __future__ import annotations

import io
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
    from .phasedem import MATERIALS as _PM
    palette = dict(MATERIAL_RGB)
    palette.update({m[0]: m[3] for m in _PM})
    rgb_mat = np.array([palette.get(dem["names"][i], (30, 26, 24)) for i in dem["label"]], float)
    frames = dem["frames"]
    n = int(seconds * fps)
    caps = even_captions(list(captions), seconds) if captions else []
    pipe = FFmpegPipe(path, size, fps)
    for k in range(n):
        fr = frames[k % len(frames)]
        img = np.zeros((cs.H, cs.W, 3), np.float32) + np.array([14, 16, 22], np.float32)
        img = cs.drum_layer(img, np.full(36, 120.0), 0.0, wall_px=14 * s)
        act = np.asarray(fr.get("active", np.ones(len(fr["x"]), bool)), bool)
        rr = np.asarray(fr.get("r", dem["r"]), np.float32)
        img, _ = cs.bed_particles(img, fr["x"].astype(np.float32)[act], rr[act], rgb_mat[act])
        scene = draw_overlay(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), cs, fr["theta"])
        canvas = Image.new("RGBA", size, (12, 14, 20, 255))
        canvas.paste(scene, (int(60 * s), int(60 * s)))
        d = ImageDraw.Draw(canvas)
        y = _title(d, title, int(1080 * s), int(70 * s), s) + int(24 * s)
        present = set(dem["names"][i] for i in np.unique(dem["label"][np.asarray(frames[0].get("active", np.ones(len(dem["label"]), bool)), bool)]))
        for name, c in palette.items():
            if name not in present:
                continue
            d.ellipse([int(1090 * s), y, int(1112 * s), y + int(22 * s)], fill=tuple(int(v) for v in c))
            d.text((int(1125 * s), y - 2), {"filme": "filmes e sacolas (PEBD)", "rigido": "plástico rígido",
                                            "rigido_pe": "frascos e tampas (PEAD)", "rigido_pp": "tampas, cordas, redes (PP)",
                                            "pvc": "PVC (tubos, cabos)", "isopor": "isopor (EPS)",
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


# ------------------------------------------------- taxa de pirólise ao vivo (o "DTG" da batelada)
GROUP_STYLE = [("água", "#5fa8ff", "água (secagem)"), ("PVC", "#c9c9d6", "PVC → HCl"),
               ("celulósicos", "#b07a45", "papel, madeira"), ("PS", "#f2f2f2", "isopor (PS)"),
               ("PP", "#f0b840", "PP"), ("PE", "#7fb2ff", "PE (filmes, frascos)"), ("PET", "#7fd6b3", "PET"),
               ("borracha", "#8a8a8a", "borracha")]
GROUP_MSG = {"água": "Secagem: a água do lixo sai a 100 °C",
             "PVC": "O PVC solta HCl (≈ 250–320 °C), que vai para a fase aquosa",
             "celulósicos": "Papel e madeira viram gás, alcatrão e carvão (≈ 300–380 °C)",
             "PS": "O isopor (PS) volta a estireno (≈ 370–400 °C)",
             "PP": "O PP craqueia em óleo leve (≈ 400 °C)",
             "PE": "Filmes e frascos de PE: o grosso do óleo e da cera (≈ 410–430 °C)",
             "PET": "PET: ácidos e CO/CO₂; deixa carvão",
             "borracha": "Borracha: óleo e negro de fumo"}


class RatesChart:
    def __init__(self, log, size=(820, 760), dpi=100):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.plt, self.log, self.size, self.dpi = plt, log, size, dpi
        self.t = np.array([r["t_h"] for r in log])
        self.rates = np.array([[r[f"taxa_{g}"] for g, _, _ in GROUP_STYLE] for r in log])
        self.conv = np.array([[r[f"conv_{g}"] for g, _, _ in GROUP_STYLE] for r in log])
        self.rmax = float(self.rates.sum(1).max()) * 1.1

    def render(self, t_h):
        plt = self.plt
        W, H = self.size
        fig = plt.figure(figsize=(W / self.dpi, H / self.dpi), dpi=self.dpi)
        fig.patch.set_alpha(0.0)
        a1 = fig.add_axes([0.12, 0.47, 0.85, 0.45]); a2 = fig.add_axes([0.12, 0.08, 0.85, 0.28])
        k = int(np.searchsorted(self.t, t_h, side="right"))
        cols = [c for _, c, _ in GROUP_STYLE]
        labs = [lab for _, _, lab in GROUP_STYLE]
        a1.stackplot(self.t, self.rates.T, colors=cols, alpha=0.12)
        if k > 1:
            a1.stackplot(self.t[:k], self.rates[:k].T, colors=cols, labels=labs, alpha=0.95)
        for j, c in enumerate(cols):
            a2.plot(self.t, self.conv[:, j], color=c, lw=1, alpha=0.15)
            a2.plot(self.t[:k], self.conv[:k, j], color=c, lw=2.4)
        for ax in (a1, a2):
            ax.set_facecolor((0, 0, 0, 0)); ax.axvline(t_h, color="w", lw=1, alpha=0.5)
            ax.set_xlim(0, self.t[-1]); ax.tick_params(colors="w", labelsize=11); ax.grid(alpha=0.15)
            for sp in ax.spines.values():
                sp.set_color((1, 1, 1, 0.35))
        a1.set_ylim(0, self.rmax); a2.set_ylim(0, 1.02)
        a1.set_ylabel("taxa de reação (kg/h)", color="w", fontsize=13)
        a2.set_ylabel("convertido", color="w", fontsize=13)
        a2.set_xlabel("tempo de batelada (h)", color="w", fontsize=13)
        a1.legend(loc="upper left", fontsize=10, frameon=False, labelcolor="w", ncol=2)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", transparent=True, dpi=self.dpi)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf).convert("RGBA")


def render_rates_segment(drum, log, fase: dict, path, seconds=20.0, fps=30, size=(1920, 1080), title="",
                         subtitle=""):
    """Esquerda: os pedaços mudando de fase (DEM); direita: a taxa de pirólise por componente se atualizando."""
    from .scene import draw_phase_bed
    W, H = size
    s = H / 1080
    cs = CrossSection(drum, dict(half_width=0.78, z_bot=-0.78, z_top=0.78, wall=0.04), size=(int(960 * s), int(960 * s)))
    chart = RatesChart(log, size=(int(820 * s), int(740 * s)), dpi=int(100 * s))
    recs, label = fase["recs"], fase["label"]
    tb = np.array([r["t_b"] for r in recs]) / 3600.0
    t_end = float(log[-1]["t_h"])
    lt = np.array([r["t_h"] for r in log])
    n = int(seconds * fps)
    pipe = FFmpegPipe(path, size, fps)
    for k in range(n):
        t_h = t_end * k / max(n - 1, 1)
        rec = recs[int(np.argmin(np.abs(tb - t_h)))]
        img = np.zeros((cs.H, cs.W, 3), np.float32) + np.array([14, 16, 22], np.float32)
        img = cs.drum_layer(img, np.full(36, 130.0), 0.0, wall_px=14 * s)
        img = draw_phase_bed(cs, img, rec, label, mode="material")
        scene = draw_overlay(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), cs, rec["theta"])
        canvas = Image.new("RGBA", size, (12, 14, 20, 255))
        canvas.paste(scene, (int(40 * s), int(90 * s)))
        d = ImageDraw.Draw(canvas)
        _title(d, title, int(40 * s), int(18 * s), s, width=1800, size=34)
        if subtitle:
            d.text((int(42 * s), int(62 * s)), br(subtitle), font=_font(int(18 * s)), fill=(190, 195, 205))
        ch = chart.render(t_h)
        canvas.paste(ch, (int(1080 * s), int(190 * s)), ch)
        row = {kk: float(np.interp(t_h, lt, [r[kk] for r in log])) for kk in ("T_carga", "taxa_total", "oleo_kg")}
        conv_tot = 1 - sum(float(np.interp(t_h, lt, [r[f"m_{c}"] for r in log])) for c in
                           ("LDPE", "HDPE", "PP", "PS", "PET", "PVC", "CELL", "RUBa", "RUBb", "RUBc")) / \
            max(sum(log[0][f"m_{c}"] for c in ("LDPE", "HDPE", "PP", "PS", "PET", "PVC", "CELL", "RUBa", "RUBb", "RUBc")), 1e-9)
        big = [(br(f"{t_h:.1f} h"), "de batelada"), (f"{row['T_carga']:.0f} °C", "carga"),
               (f"{row['taxa_total']:.0f} kg/h", "taxa de pirólise"), (f"{100 * conv_tot:.0f} %", "convertido")]
        for i, (v, lab) in enumerate(big):
            xx = int((1100 + i * 200) * s)
            d.text((xx, int(96 * s)), v, font=_font(int(34 * s), True), fill=(255, 210, 120) if i == 2 else (245, 245, 245))
            d.text((xx, int(140 * s)), lab, font=_font(int(16 * s)), fill=(185, 190, 200))
        # legenda: o grupo que mais reage agora
        rates = {g: float(np.interp(t_h, lt, [r[f"taxa_{g}"] for r in log])) for g, _, _ in GROUP_STYLE}
        g_max = max(rates, key=rates.get)
        if rates[g_max] > 5.0:
            msg = GROUP_MSG[g_max]
        elif t_h < 0.5 * t_end:
            msg = "Aquecendo: os pedaços ainda estão inteiros"
        else:
            msg = "Fim: sobram carvão (pedaços escuros e grânulos) e areia"
        p = rec["pool"]
        info = br(f"poça de fundido: {p.get('mass', 0.0):.1f} kg na fatia · viscosidade {p['mu']:.2g} Pa·s") \
            if p.get("mass", 0.0) > 0.05 else ""
        if info:
            d.text((int(60 * s), int(1050 * s)), info, font=_font(int(18 * s)), fill=(210, 190, 160))
        draw_lower_third(canvas, msg, 1.0, s * 0.82, y_bottom=int(1060 * s), max_w=int(760 * s), x0=int(1080 * s))
        pipe.write(np.asarray(canvas.convert("RGB")))
    return pipe.close()


def render_flame_views(drum, flames_corte, flames_lateral, meta, path, Ts_C=500.0, seconds=9.0, fps=30,
                       size=(1920, 1080), title="", captions=(), info=()):
    """Chamas com base física em duas vistas: o corte (ao longo do eixo) e a lateral (os dois queimadores ao
    longo do tambor, vistos da parede dos queimadores, com o casco incandescente na frente das chamas de trás)."""
    W, H = size
    s = H / 1080
    cs = CrossSection(drum, BOX, size=(int(760 * s), int(760 * s)))
    Lx, zb, zt = meta["Lx"], meta["z_bot"], meta["z_top"]
    side_w = int(1080 * s)
    side_h = int(side_w * (zt - zb) / Lx)
    n = int(seconds * fps)
    caps = even_captions(list(captions), seconds) if captions else []
    pipe = FFmpegPipe(path, size, fps)
    for k in range(n):
        img, _ = cs.furnace_layer(T_refr_C=750.0, flame_img=flames_corte.render_on_grid(k, cs.Yw, cs.Zw))
        img = cs.drum_layer(img, np.full(36, Ts_C), 0.0, wall_px=10 * s)
        scene = draw_overlay(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), cs, 2 * math.pi * k / fps / 20)
        rgb, a = flames_lateral.render_image(k, (0.0, Lx, zb, zt), (side_w, side_h))
        side = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
        ds = ImageDraw.Draw(side)
        for xb in meta["burners_x"]:
            px = int(xb / Lx * side_w); pz = int((zt - meta["burner_z"]) / (zt - zb) * side_h)
            ds.rectangle([px - int(14 * s), pz - int(14 * s), px + int(14 * s), pz + int(14 * s)], outline=(160, 165, 175), width=2)
        canvas = Image.new("RGBA", size, (12, 14, 20, 255))
        canvas.paste(scene, (int(30 * s), int(150 * s)))
        canvas.paste(side, (int(810 * s), int(150 * s) + (int(760 * s) - side_h) // 2))
        d = ImageDraw.Draw(canvas)
        y = _title(d, title, int(40 * s), int(30 * s), s, width=1800, size=36)
        d.text((int(40 * s), int(118 * s)), "corte (ao longo do eixo)", font=_font(int(20 * s)), fill=(190, 195, 205))
        d.text((int(810 * s), int(118 * s)), "vista lateral: os dois queimadores ao longo do tambor",
               font=_font(int(20 * s)), fill=(190, 195, 205))
        for i, ln in enumerate(info):
            d.text((int(810 * s) + (i % 2) * int(540 * s), int(930 * s) + (i // 2) * int(40 * s)), br(ln),
                   font=_font(int(22 * s)), fill=(225, 225, 230))
        if caps:
            txt, al = _caption_alpha(caps, k / fps)
            draw_lower_third(canvas, txt, al, s * 0.8, y_bottom=int(1060 * s), max_w=int(740 * s), x0=int(30 * s))
        pipe.write(np.asarray(canvas.convert("RGB")))
    return pipe.close()
