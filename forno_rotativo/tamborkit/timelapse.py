"""Time-lapse da batelada: o corte do tambor na fornalha à esquerda e o gráfico que se atualiza à direita.

Como no flare (altura da chama ao vivo), o gráfico anda junto com a simulação: temperaturas (carga, casco,
vapor) em cima e massas acumuladas (óleo, gás, água, carvão) embaixo, com o cursor no instante mostrado.
A carga é desenhada com as partículas do DEM (lixo solto; carvão no fim) ou como poça de fundido, conforme
o estado calculado pelo modelo da batelada; as chamas são quadros da LES da fornalha.
"""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image, ImageDraw

from .scene import CrossSection, colorbar, draw_overlay, thermal_rgb
from .video import FFmpegPipe, _font, br, draw_lower_third

MATERIAL_RGB = {"filme": (225, 225, 215), "rigido": (70, 130, 200), "isopor": (245, 245, 245),
                "pet": (120, 200, 170), "organico": (150, 105, 60), "borracha": (40, 40, 40),
                "areia": (205, 185, 140), "carga": (180, 180, 170)}


def _interp_log(log, t_h, key):
    ts = np.array([r["t_h"] for r in log])
    return float(np.interp(t_h, ts, np.array([r[key] for r in log], float)))


def batch_events(log) -> list:
    """Marcos da batelada (para as legendas): fim da secagem, carga fundida, primeiro óleo, troca de
    combustível (o gás próprio assume) e fim."""
    t = np.array([r["t_h"] for r in log])
    agua = np.array([r["agua_kg"] for r in log])
    oleo = np.array([r["oleo_kg"] for r in log])
    melt = np.array([r["frac_fundido"] for r in log])
    qn = np.array([r["Q_ncg_kW"] for r in log]); qf = np.array([r["Q_fire_kW"] for r in log])

    def first(mask, default=None):
        i = np.argmax(mask)
        return float(t[i]) if mask.any() else default
    ev = [(0.0, "Partida: os queimadores ligam com GLP e o tambor começa a girar")]
    t_dry0 = first(np.array([r["T_carga"] for r in log]) > 98)
    if t_dry0:
        ev.append((t_dry0, "Secagem: a água do lixo segura a carga em 100 °C"))
    t_melt = first(melt > 0.4)
    if t_melt:
        ev.append((t_melt, "O plástico funde e a carga desaba: de 2/3 do tambor para uma poça"))
    t_oil = first(oleo > 0.01 * max(oleo[-1], 1))
    if t_oil:
        ev.append((t_oil, "Pirólise: as cadeias quebram e o vapor vira óleo no condensador"))
    t_sw = first((qn > 0.95 * qf) & (t > (t_oil or 0)))
    if t_sw:
        ev.append((t_sw, "O gás da própria pirólise assume o queimador; o excedente vai para o flare"))
    ev.append((float(t[-1]) * 0.93, "Fim: o gás para de sair; no tambor sobram carvão e cinzas"))
    ev.sort(key=lambda e: e[0])
    return ev


class LiveChart:
    """Gráfico ao vivo (matplotlib) desenhado até o instante t."""

    def __init__(self, log, size=(820, 860), dpi=100):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.plt = plt
        self.log = log
        self.size, self.dpi = size, dpi
        self.t = np.array([r["t_h"] for r in log])
        g = lambda k: np.array([r[k] for r in log], float)  # noqa: E731
        self.series_T = [("carga (média)", g("T_carga"), "#ffb347"), ("casco do tambor", g("T_casco"), "#e8e8e8"),
                         ("ponto mais quente do casco", g("T_casco_max"), "#ff5e5e"),
                         ("vapor na saída", g("T_vapor"), "#7fd3ff")]
        self.series_m = [("óleo coletado", g("oleo_kg"), "#ffcc33"), ("água (fase aquosa)", g("aquoso_kg"), "#5fa8ff"),
                         ("gás não condensável", g("gas_kg"), "#b0ff7a"),
                         ("carvão (inclui o negro de fumo da borracha)", g("carvao_kg"), "#c0a080")]
        self.t_end = float(self.t[-1])
        self.Tmax = max(650.0, float(np.nanmax(g("T_casco_max"))) + 30)
        self.mmax = max(float(np.nanmax(s[1])) for s in self.series_m) * 1.08

    def render(self, t_h) -> Image.Image:
        plt = self.plt
        W, H = self.size
        fig = plt.figure(figsize=(W / self.dpi, H / self.dpi), dpi=self.dpi)
        fig.patch.set_alpha(0.0)
        axs = [fig.add_axes([0.13, 0.56, 0.84, 0.38]), fig.add_axes([0.13, 0.09, 0.84, 0.38])]
        k = np.searchsorted(self.t, t_h, side="right")
        for ax, series, ylab, ymax in ((axs[0], self.series_T, "temperatura (°C)", self.Tmax),
                                       (axs[1], self.series_m, "massa acumulada (kg)", self.mmax)):
            ax.set_facecolor((0, 0, 0, 0))
            for name, y, c in series:
                ax.plot(self.t, y, color=c, lw=1.0, alpha=0.18)
                ax.plot(self.t[:k], y[:k], color=c, lw=2.6, label=name)
                if k > 0:
                    ax.plot([self.t[k - 1]], [y[k - 1]], "o", color=c, ms=7)
            ax.axvline(t_h, color="w", lw=1, alpha=0.5)
            ax.set_xlim(0, self.t_end); ax.set_ylim(0, ymax)
            ax.set_ylabel(ylab, color="w", fontsize=13)
            ax.tick_params(colors="w", labelsize=11)
            for sp in ax.spines.values():
                sp.set_color((1, 1, 1, 0.35))
            ax.grid(alpha=0.15)
            leg = ax.legend(loc="upper left", fontsize=11, frameon=False, labelcolor="w", ncol=1)
            del leg
        axs[0].axhline(500, color="#ff9e9e", lw=0.8, ls="--", alpha=0.5)
        axs[1].set_xlabel("tempo de batelada (h)", color="w", fontsize=13)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", transparent=True, dpi=self.dpi)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf).convert("RGBA")


class BatchScene:
    """Quadros do time-lapse: corte + gráfico + números + legendas."""

    def __init__(self, batch, dem_sets: dict, les_frames=None, size=(1920, 1080), fps=30, seconds=40.0,
                 vis_rev_s=6.0, title="Pirólise em batelada num tambor rotativo", subtitle=""):
        self.b = batch
        self.log, self.snaps = batch.log, batch.snaps
        self.size, self.fps, self.seconds = size, fps, seconds
        self.W, self.H = size
        s = self.H / 1080
        self.s = s
        self.cs = CrossSection(batch.drum, dict(half_width=1.0, z_bot=-1.30, z_top=0.95, wall=0.12),
                               size=(int(1000 * s), int(960 * s)))
        self.chart = LiveChart(self.log, size=(int(800 * s), int(690 * s)), dpi=int(100 * s))
        self.dem = dem_sets
        self.les = les_frames          # dict(T=[n, ny, nz], yc, zc, Q)
        self.vis_rev_s = vis_rev_s
        self.events = batch_events(self.log)
        self.t_end = float(self.log[-1]["t_h"])
        self.title, self.subtitle = title, subtitle
        self.cbar = colorbar(int(430 * s), int(60 * s), s=s)
        for k, d in self.dem.items():
            d["rgb_mat"] = np.array([MATERIAL_RGB.get(d["names"][i], (180, 180, 170)) for i in d["label"]], float)

    # --------------------------------------------------------------- estado
    def _snap(self, t_h):
        ts = np.array([sn["t"] / 3600 for sn in self.snaps])
        i = int(np.clip(np.searchsorted(ts, t_h), 1, len(ts) - 1))
        a = (t_h - ts[i - 1]) / max(ts[i] - ts[i - 1], 1e-9)
        return self.snaps[i - 1] if a < 0.5 else self.snaps[i]

    def _bed_particles(self, key, frame_idx, F, beta, T_bed_C, Ts_lab_C, char, phi_lab, mat_w):
        """Partículas de um quadro do DEM: mantém as mais baixas até o enchimento F do modelo da batelada."""
        d = self.dem[key]
        fr = d["frames"][frame_idx % len(d["frames"])]
        x = fr["x"].astype(np.float32)
        theta_dem = fr["theta"]
        # gira o quadro do DEM para alinhar as aletas com o ângulo visual
        r = d["r"].astype(np.float32)
        nrm = np.array([-math.sin(beta), math.cos(beta)], np.float32)
        hgt = x[:, 1] * nrm[0] + x[:, 2] * nrm[1]
        F_dem = d["fill"]
        keep_n = int(np.clip(F / max(F_dem, 1e-6), 0.02, 1.0) * len(x))
        order = np.argsort(hgt)[:keep_n]
        xs, rs = x[order], r[order]
        # cor: material no início → temperatura ao aquecer → escurece ao carbonizar; mais quente junto à parede
        dw = self.b.drum.R - np.hypot(xs[:, 1], xs[:, 2])
        ph = np.arctan2(xs[:, 2], xs[:, 1])
        Tw = np.interp(ph, phi_lab, Ts_lab_C, period=2 * math.pi)
        Tp = T_bed_C + (Tw - T_bed_C) * np.exp(-np.clip(dw, 0, None) / 0.04) * 0.6
        col = thermal_rgb(Tp)
        col = (1 - mat_w) * d["rgb_mat"][order] + mat_w * col
        col = col * (1 - 0.82 * char)
        return xs, rs, col, theta_dem

    # ---------------------------------------------------------------- quadro
    def frame(self, k: int) -> np.ndarray:
        n = int(self.seconds * self.fps)
        t_h = self.t_end * k / max(n - 1, 1)
        sn = self._snap(t_h)
        g = lambda key: _interp_log(self.log, t_h, key)  # noqa: E731
        cs = self.cs
        b = self.b
        mid = b.cfg.nx // 2
        # casco no referencial do laboratório
        phi_mat = b.phi0
        phi_lab = (phi_mat + sn["theta"] + math.pi) % (2 * math.pi) - math.pi
        order = np.argsort(phi_lab)
        Ts_lab = (sn["Ts"][mid] - 273.15)[order]
        phi_sorted = phi_lab[order]
        theta_vis = 2 * math.pi * (k / self.fps) / self.vis_rev_s
        # ---- fornalha e chamas
        gas = None
        if self.les is not None:
            T = self.les["T"][k % len(self.les["T"])]
            Q = max(g("Q_fire_kW") * 1e3, 1.0)
            scale = float(np.clip(Q / self.les["Q"], 0.08, 1.2))
            gas = (T, self.les["yc"], self.les["zc"], scale ** 0.6)
        T_ref = float(np.mean(sn["Tr_fur"])) - 273.15
        img, _ = cs.furnace_layer(T_refr_C=T_ref, gas=gas)
        # casco (desenhado no laboratório: o padrão térmico fica parado; as aletas giram)
        nphi = len(Ts_lab)
        phi_bins = (np.arange(nphi) + 0.5) * 2 * math.pi / nphi - math.pi
        Ts_bins = np.interp(phi_bins, phi_sorted, Ts_lab, period=2 * math.pi)
        img = cs.drum_layer(img, Ts_bins, 0.0, wall_px=10 * self.s)
        # ---- carga
        lo, me, re = (float(sn["frac"][i][mid]) for i in range(3))
        F = float(sn["F"][mid])
        beta = float(sn["beta"][mid])
        T_bed = float(np.mean(b._slice_view(sn["T"])[mid])) - 273.15
        char_m = float(sn["char"][min(mid, len(sn["char"]) - 1)])
        tot_m = float(sn["total"][min(mid, len(sn["total"]) - 1)])
        char = np.clip(char_m / max(tot_m, 1e-9), 0, 1)
        mat_w = float(np.clip((T_bed - 35.0) / 50.0, 0, 1))
        layers = []
        if "solto" in self.dem and (lo > 0.25 or me < 0.35) and re < 0.65:
            xs, rs, col, th_dem = self._bed_particles("solto", k, F, beta, T_bed, Ts_lab, char * 0.5, phi_sorted, mat_w)
            w = float(np.clip((lo + 0.2 - me) / 0.4, 0, 1)) if me > 0.2 else 1.0
            layers.append(("p", xs, rs, col, w))
        if me >= 0.2 and re < 0.75:
            w = float(np.clip((me - 0.2) / 0.3, 0, 1))
            layers.append(("pool", F, beta, T_bed, char, w))
        if "carvao" in self.dem and re >= 0.45:
            xs, rs, col, th_dem = self._bed_particles("carvao", k, F, beta, T_bed, Ts_lab, min(char * 1.6, 0.9),
                                                      phi_sorted, 1.0)
            w = float(np.clip((re - 0.45) / 0.25, 0, 1))
            layers.append(("p", xs, rs, col, w))
        for L_ in layers:
            if L_[0] == "p":
                _, xs, rs, col, w = L_
                new, a = cs.bed_particles(img.copy(), xs, rs, col)
            else:
                _, F_, beta_, Tb_, ch_, w = L_
                new, m = cs.pool(img.copy(), F_, beta_ * 0.3, Tb_, ch_)
            img = img * (1 - w) + new * w
        canvas = Image.new("RGBA", self.size, (12, 14, 20, 255))
        scene = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        scene = draw_overlay(scene, cs, theta_vis)
        canvas.paste(scene, (int(40 * self.s), int(92 * self.s)))
        # ---- gráfico ao vivo
        ch = self.chart.render(t_h)
        canvas.paste(ch, (int(1095 * self.s), int(180 * self.s)), ch)
        d = ImageDraw.Draw(canvas)
        s = self.s
        d.text((int(36 * s), int(18 * s)), br(self.title), font=_font(int(34 * s), True), fill=(245, 245, 245))
        if self.subtitle:
            d.text((int(38 * s), int(60 * s)), br(self.subtitle), font=_font(int(18 * s)), fill=(190, 195, 205))
        # números grandes
        big = [(f"{t_h:4.1f} h".replace(".", ","), "de batelada"), (f"{g('T_carga'):.0f} °C", "carga"),
               (f"{g('oleo_kg'):.0f} kg", "de óleo"), (f"{g('Q_fire_kW'):.0f} kW", "queima")]
        x0 = int(1110 * s)
        for i, (v, lab) in enumerate(big):
            xx = x0 + int(i * 200 * s)
            d.text((xx, int(96 * s)), v, font=_font(int(36 * s), True), fill=(255, 210, 120) if i == 2 else (245, 245, 245))
            d.text((xx, int(142 * s)), lab, font=_font(int(16 * s)), fill=(185, 190, 200))
        frac_ncg = g("Q_ncg_kW") / max(g("Q_fire_kW"), 1e-6)
        fuel = "gás da própria pirólise" if frac_ncg > 0.9 else ("GLP + gás de pirólise" if frac_ncg > 0.1 else "GLP (partida)")
        d.text((int(44 * s), int(1056 * s)), f"queimador: {fuel}   ·   giro do tambor ilustrativo no time-lapse".replace(".", ","),
               font=_font(int(17 * s)), fill=(200, 205, 215))
        canvas.paste(self.cbar, (int(560 * s), int(985 * s)), self.cbar)
        # legenda do marco atual (embaixo do gráfico)
        cur = [e for e in self.events if e[0] <= t_h + 1e-6]
        if cur:
            draw_lower_third(canvas, cur[-1][1], 1.0, s * 0.82, y_bottom=int(1060 * s), max_w=int(760 * s),
                             x0=int(1080 * s))
        return np.asarray(canvas.convert("RGB"))

    def render(self, path: str) -> str:
        n = int(self.seconds * self.fps)
        pipe = FFmpegPipe(path, self.size, self.fps)
        for k in range(n):
            pipe.write(self.frame(k))
        return pipe.close()
