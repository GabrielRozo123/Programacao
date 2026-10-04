"""Gravação dos quadros da LES e renderização do vídeo final.

A LES grava, a cada `frame_dt` de tempo simulado, só o que o vídeo precisa (vista lateral luminosa,
envelope da chama, radiação no solo e séries temporais). O vídeo é montado depois, em segmentos:

  1. abertura (cartão de título);
  2. chama em zoom, em tela cheia ("câmera sintética");
  3. painel com a chama ampliada + validação ao vivo;
  4. varredura das direções do vento (rosa dos ventos do atlas → pegada de radiação girando →
     probabilidade de excedência acumulada);
  5. resumos.

Separar simulação e renderização permite refazer o vídeo (outro zoom, outra paleta) sem rodar a LES.
"""
from __future__ import annotations

import io
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from matplotlib import colors as mcolors
from matplotlib.animation import FFMpegWriter
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from scipy.ndimage import gaussian_filter, map_coordinates

from . import semiempirical as se
from .dashboard import API_LEVELS, BG, CHAM_C, FG, GRID, LES_C, MUTED, PANEL, PT_C, _style, frustum_outline_xz

FIRE = mcolors.LinearSegmentedColormap.from_list(
    "fogo", ["#000000", "#1a0303", "#5c0d05", "#a3240a", "#dd5410", "#f7941d", "#ffd15c", "#fff6d8"])
ENVELOPE_C = "#4dd0e1"
W, H_PX, DPI = 16, 9, 120


# ===================================================================== gravação
def _f16(a):
    """float16 sem estouro (máx. 65504): nos primeiros instantes a emissão normalizada por X_rad·Q fica
    concentrada em poucas células e a luminosidade projetada pode passar desse limite."""
    return np.clip(np.asarray(a, np.float32), -6.5e4, 6.5e4).astype(np.float16)


class Recorder:
    """Guarda os quadros da LES (float16) e os resultados médios finais."""

    def __init__(self, les, sc: se.Scenario, title: str, wind_label: str = ""):
        self.static = dict(
            xf=les.xf, zf=les.zf, xc=les.xc, zc=les.zc, yc=les.yc, rec_x=les.rec_x, rec_y=les.rec_y,
            tip=les.tip, Z_st=les.Z_st, X_rad=les.cfg.X_rad, Q=les.Q, u_ref=les.cfg.u_ref,
            receiver_z=les.cfg.receiver_z, summary=les.summary(), title=title, wind_label=wind_label,
            T_inf=sc.T_inf, RH=sc.RH)
        self.frames: list[dict] = []
        self._qsum = None
        self._nq = 0
        self.final: dict = {}

    def snap(self, les, e, q, averaging: bool, T=None):
        tot = float((e * les.vol).sum())
        scale = les.cfg.X_rad * les.Q / max(tot, 1e-30)
        ey = e * les.Dc[1]
        lum = (ey.sum(1) * scale / 1e3).float().cpu().numpy()      # kW/m² projetado
        # temperatura média na linha de visada, ponderada pela emissão (cor da chama no render HD)
        tl = None if T is None else ((ey * T).sum(1) / ey.sum(1).clamp(min=1e-30)).float().cpu().numpy()
        zp = les.Z.max(1).values.float().cpu().numpy()
        qg = les.q_grid(q) / 1e3
        if averaging:
            self._qsum = qg if self._qsum is None else self._qsum + qg
            self._nq += 1
        qmean = self._qsum / self._nq if self._nq else None
        h = les.history
        self.frames.append(dict(
            t=les.time, step=les.step_n, dt=les.dt, cfl=les._last_cfl, wall=les.wall,
            lum=_f16(lum), zp=_f16(zp), q=_f16(qg), tl=None if tl is None else _f16(tl),
            qmean=None if qmean is None else _f16(qmean), averaging=averaging,
            L=h["L"][-1], tilt=h["tilt"][-1], Lmean=les.mean_flame_length(), tiltmean=les.mean_tilt()))

    def finalize(self, les):
        n = max(les.avg_n, 1.0)
        self.final = dict(
            q_mean=les.q_grid(les.avg_q / n) / 1e3,
            I_proj=(les.avg_I / n).max(1).values.float().cpu().numpy(),
            T_proj=(les.avg_T / n).max(1).values.float().cpu().numpy(),
            L_mean=les.mean_flame_length(), tilt_mean=les.mean_tilt(), n_avg=les.avg_n,
            steps=les.step_n, wall=les.wall)

    # -------------------------------------------------------------- disco
    def save(self, path: str):
        keys = ["t", "step", "dt", "cfl", "wall", "L", "tilt", "Lmean", "tiltmean", "averaging"]
        out = {f"s_{k}": np.asarray(v) for k, v in self.static.items()}
        for k in keys:
            out[f"f_{k}"] = np.array([f[k] for f in self.frames], dtype=float)
        for k in ("lum", "zp", "q"):
            out[f"f_{k}"] = np.stack([f[k] for f in self.frames])
        if all(f.get("tl") is not None for f in self.frames):
            out["f_tl"] = np.stack([f["tl"] for f in self.frames])
        qm = [f["qmean"] if f["qmean"] is not None else np.full_like(f["q"], np.nan) for f in self.frames]
        out["f_qmean"] = np.stack(qm)
        for k, v in self.final.items():
            out[f"r_{k}"] = np.asarray(v)
        np.savez_compressed(path, **out)

    @classmethod
    def load(cls, path: str) -> "Recorder":
        d = np.load(path, allow_pickle=False)
        rec = cls.__new__(cls)
        rec.static = {k[2:]: (d[k].item() if d[k].ndim == 0 else d[k]) for k in d.files if k.startswith("s_")}
        A = {k: d[f"f_{k}"] for k in ("t", "step", "dt", "cfl", "wall", "L", "tilt", "Lmean", "tiltmean",
                                       "averaging", "lum", "zp", "q", "qmean", "tl") if f"f_{k}" in d.files}
        rec.frames = []
        for i in range(len(A["t"])):
            f = {k: float(A[k][i]) for k in ("t", "step", "dt", "cfl", "wall", "L", "tilt", "Lmean", "tiltmean")}
            f["averaging"] = bool(A["averaging"][i])
            f["lum"], f["zp"], f["q"] = A["lum"][i], A["zp"][i], A["q"][i]
            f["tl"] = A["tl"][i] if "tl" in A else None
            qm = A["qmean"][i]
            f["qmean"] = None if np.isnan(qm.astype(float)).all() else qm
            rec.frames.append(f)
        rec.final = {k[2:]: (d[k].item() if d[k].ndim == 0 else d[k]) for k in d.files if k.startswith("r_")}
        rec._qsum, rec._nq = None, 0
        return rec


# ===================================================================== utilidades
def flame_view(rec: Recorder, ch: se.Chamberlain, pad: float = 6.0, aspect: float = 16 / 9,
               with_model: bool = True):
    """Janela de zoom em volta da chama: envelope médio da LES (I ≥ 0,2), unido ao frustum de Chamberlain
    quando with_model (painéis que desenham o frustum)."""
    s = rec.static
    fr = frustum_outline_xz(ch, s["tip"])
    xs, zs = list(fr[:, 0]), list(fr[:, 1])
    Ip = rec.final.get("I_proj")
    if Ip is not None:
        m = Ip >= 0.2
        if m.any():
            if not with_model:
                xs, zs = [0.0], [float(s["tip"][2])]
            ii, kk = np.nonzero(m)
            xs += [s["xc"][ii].min(), s["xc"][ii].max()]
            zs += [s["zc"][kk].min(), s["zc"][kk].max()]
    x0, x1 = min(xs) - pad, max(xs) + pad
    z0, z1 = min(zs) - pad, max(zs) + pad
    z1 += 0.15 * (z1 - z0)                          # folga no topo para título e relógio
    z0 = max(z0, s["tip"][2] - 0.45 * (z1 - z0))   # mostra um pedaço da chaminé
    cx, cz, w, h = 0.5 * (x0 + x1), 0.5 * (z0 + z1), x1 - x0, z1 - z0
    if w / h < aspect:
        w = h * aspect
    else:
        h = w / aspect
    return (cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2)


class Resampler:
    """Reamostra campos (nx, nz) da malha esticada para uma grade uniforme (zoom suave)."""

    def __init__(self, xc, zc, view, nx_out=960, nz_out=540, smooth=0.7):
        self.smooth = smooth   # filtro gaussiano (em células) antes da interpolação bilinear: suaviza os
        x0, x1, z0, z1 = view  # degraus de célula no zoom sem o "ringing" de uma spline cúbica
        self.xs = np.linspace(x0, x1, nx_out)
        self.zs = np.linspace(z0, z1, nz_out)
        ix = np.interp(self.xs, xc, np.arange(len(xc)))
        iz = np.interp(self.zs, zc, np.arange(len(zc)))
        IX, IZ = np.meshgrid(ix, iz, indexing="ij")
        self.coords = np.stack([IX, IZ])
        self.inside_x = (self.xs >= xc[0]) & (self.xs <= xc[-1])
        self.inside_z = (self.zs >= zc[0]) & (self.zs <= zc[-1])

    def __call__(self, f):
        f = np.asarray(f, dtype=np.float32)
        if self.smooth:
            f = gaussian_filter(f, self.smooth, mode="nearest")
        out = map_coordinates(f, self.coords, order=1, mode="nearest")
        out[~self.inside_x, :] = 0.0
        out[:, ~self.inside_z] = 0.0
        return out


class LumNorm:
    """Normalização da luminosidade pelo percentil 99,7 recente (evita cintilação de escala)."""

    def __init__(self, window: int = 40):
        self.hist, self.window = [], window

    def __call__(self, img):
        img = np.nan_to_num(np.asarray(img, np.float32), nan=0.0, posinf=0.0, neginf=0.0)
        self.hist.append(float(np.percentile(img, 99.7)))
        v = max(np.median(self.hist[-self.window:]), 1e-9)
        return np.clip(img / v, 0.0, 1.0)


def _writer(fig, path, fps):
    w = FFMpegWriter(fps=fps, codec="libx264", bitrate=12000,
                     extra_args=["-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "16"])
    w.setup(fig, path, dpi=DPI)
    return w


def qnorm(qmax: float) -> mcolors.PowerNorm:
    """Escala de cor para fluxo no solo [kW/m²] ajustada ao máximo (tochas altas ficam bem abaixo de 10)."""
    for v in (1, 2, 3, 5, 8, 10, 15, 20, 30, 50, 100):
        if v >= 1.1 * qmax:
            break
    return mcolors.PowerNorm(0.6, 0, v)


def _fit_text(fig, txt, max_frac: float, min_size: float = 7.0):
    """Reduz a fonte de um texto até caber em max_frac da largura da figura."""
    r = fig.canvas.get_renderer()
    while txt.get_fontsize() > min_size and txt.get_window_extent(r).width > max_frac * fig.bbox.width:
        txt.set_fontsize(txt.get_fontsize() - 0.5)
    return txt


def _new_fig():
    fig = Figure(figsize=(W, H_PX), dpi=DPI, facecolor=BG)
    FigureCanvasAgg(fig)
    return fig


def _wind_arrow(ax, label, x=0.03, y=0.93, length=0.10, fontsize=12):
    """Seta do vento (sempre da esquerda para a direita na vista lateral), em coordenadas do eixo."""
    ax.annotate("", xy=(x + length, y), xytext=(x, y), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=CHAM_C, lw=2.5), zorder=6)
    ax.text(x, y - 0.025, label, color=CHAM_C, fontsize=fontsize, va="top", transform=ax.transAxes, zorder=6)


# ===================================================================== segmentos
def render_title(path: str, title: str, subtitle: str, credit: str = "", seconds: float = 3.0, fps: int = 30,
                 note: str = ""):
    fig = _new_fig()
    _fit_text(fig, fig.text(0.5, 0.58, title, ha="center", color=FG, fontsize=40, fontweight="bold"), 0.94)
    _fit_text(fig, fig.text(0.5, 0.48, subtitle, ha="center", color=LES_C, fontsize=20), 0.94)
    if credit:
        fig.text(0.5, 0.38, credit, ha="center", color=MUTED, fontsize=14)
    if note:
        _fit_text(fig, fig.text(0.5, 0.08, note, ha="center", color=MUTED, fontsize=13, style="italic"), 0.94)
    w = _writer(fig, path, fps)
    for _ in range(int(seconds * fps)):
        w.grab_frame(facecolor=BG)
    w.finish()
    return path


def render_hero(rec: Recorder, ch: se.Chamberlain, path: str, title: str, subtitle: str, fps: int = 30,
                every: int = 1, view=None):
    """Chama em tela cheia, ampliada: vista lateral da emissão luminosa da LES."""
    s = rec.static
    view = view or flame_view(rec, ch, pad=4.0, with_model=False)   # zoom só na chama da LES
    rs = Resampler(s["xc"], s["zc"], view)
    norm = LumNorm()
    fig = _new_fig()
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("black")
    ax.set_axis_off()
    im = ax.imshow(np.zeros((len(rs.zs), len(rs.xs))), origin="lower", extent=view, cmap=FIRE,
                   norm=mcolors.PowerNorm(0.5, 0, 1), interpolation="bilinear", aspect="equal")
    ax.set_xlim(view[0], view[1]); ax.set_ylim(view[2], view[3])
    tip = s["tip"]
    ax.add_patch(Rectangle((-0.45, view[2] - 5), 0.9, tip[2] - view[2] + 5, color="#59616b", zorder=4))
    if s["u_ref"] > 0:
        _wind_arrow(ax, "vento", x=0.03, y=0.80, length=0.08, fontsize=14)
    fig.text(0.03, 0.93, title, color=FG, fontsize=26, fontweight="bold")
    fig.text(0.03, 0.885, subtitle, color=MUTED, fontsize=15)
    clock = fig.text(0.97, 0.93, "", color=LES_C, fontsize=26, ha="right", family="monospace", fontweight="bold")
    readout = fig.text(0.97, 0.885, "", color=FG, fontsize=15, ha="right", family="monospace")
    fig.text(0.97, 0.03, "LES 3D · emissão luminosa integrada na linha de visada (câmera sintética)",
             color=MUTED, fontsize=12, ha="right")
    # barra de escala de 10 m
    sb_x = view[1] - 0.03 * (view[1] - view[0]) - 10.0     # canto inferior direito, longe da chaminé
    sb_z = view[2] + 0.09 * (view[3] - view[2])
    ax.plot([sb_x, sb_x + 10], [sb_z, sb_z], color=FG, lw=3, zorder=6)
    ax.text(sb_x + 5, sb_z + 0.02 * (view[3] - view[2]), "10 m", color=FG, fontsize=13, ha="center", zorder=6)
    w = _writer(fig, path, fps)
    for f in rec.frames[::every]:
        im.set_data(norm(rs(f["lum"])).T)
        clock.set_text(f"t = {f['t']:5.1f} s")
        readout.set_text(f"L = {f['L']:4.1f} m")
        w.grab_frame(facecolor=BG)
    w.finish()
    return path


class ZoomDashboard:
    """Painel com a chama ampliada (2/3 da tela) + mapa, fluxo no solo e comprimento da chama."""

    def __init__(self, rec: Recorder, sc: se.Scenario, ch: se.Chamberlain, title: str, subtitle: str, view=None,
                 t_end: float | None = None):
        s = rec.static
        self.rec, self.ch, self.t_end = rec, ch, t_end
        self.view = view or flame_view(rec, ch, aspect=1.2)
        self.rs = Resampler(s["xc"], s["zc"], self.view, 720, 600)
        self.norm = LumNorm()
        fig = self.fig = _new_fig()
        gs = GridSpec(3, 3, figure=fig, left=0.035, right=0.985, top=0.875, bottom=0.07, hspace=0.5, wspace=0.28,
                      width_ratios=[1, 1, 0.95])
        self.ax = fig.add_subplot(gs[:, 0:2])
        self.ax_m = fig.add_subplot(gs[0, 2])
        self.ax_l = fig.add_subplot(gs[1, 2])
        self.ax_t = fig.add_subplot(gs[2, 2])
        fig.text(0.035, 0.955, title, color=FG, fontsize=18, fontweight="bold")
        _fit_text(fig, fig.text(0.035, 0.918, subtitle, color=MUTED, fontsize=11), 0.95)
        self.clock = fig.text(0.985, 0.95, "", color=LES_C, fontsize=22, ha="right", family="monospace",
                              fontweight="bold")
        # chama
        ax = self.ax
        _style(ax, "LES: emissão luminosa (câmera sintética) · envelope Z̃ = Z_st · Chamberlain (1987)")
        v = self.view
        self.im = ax.imshow(np.zeros((len(self.rs.zs), len(self.rs.xs))), origin="lower", extent=v, cmap=FIRE,
                            norm=mcolors.PowerNorm(0.5, 0, 1), interpolation="bilinear", aspect="equal")
        tip = s["tip"]
        ax.add_patch(Rectangle((-0.45, v[2] - 5), 0.9, tip[2] - v[2] + 5, color="#59616b", zorder=4))
        fr = frustum_outline_xz(ch, tip)
        ax.plot(fr[:, 0], fr[:, 1], "--", color=CHAM_C, lw=1.8, zorder=5, label="Chamberlain (1987)")
        ax.plot([], [], color=ENVELOPE_C, lw=1.6, label="LES: envelope da chama")
        ax.set_xlim(v[0], v[1]); ax.set_ylim(v[2], v[3])
        ax.set_xlabel("x [m] (a jusante)"); ax.set_ylabel("z [m]")
        ax.legend(loc="upper right", fontsize=10, facecolor=PANEL, edgecolor=GRID, labelcolor=FG)
        if s["u_ref"] > 0:
            _wind_arrow(ax, s.get("wind_label") or f"{s['u_ref']:.1f} m/s")
        self.env = None
        self.box = ax.text(0.015, 0.03, "", transform=ax.transAxes, color=FG, fontsize=11, family="monospace",
                           va="bottom", bbox=dict(facecolor=PANEL, edgecolor=GRID, alpha=0.85, pad=6), zorder=7)
        # mapa no solo (escala de cor pelo maior fluxo previsto: LES média, Chamberlain ou fonte pontual)
        xr = s["rec_x"]
        recp = np.stack([xr, np.zeros_like(xr), np.full_like(xr, float(s["receiver_z"]))], 1)
        self.q_ch = se.q_chamberlain(recp, ch, tip, sc.T_inf, sc.RH) / 1e3
        self.q_pt = se.q_point_source(recp, se.flame_center_chamberlain(ch, tip), float(s["X_rad"]), sc.Q,
                                      sc.T_inf, sc.RH) / 1e3
        q_ref = max(self.q_ch.max(), self.q_pt.max(),
                    float(np.nanmax(rec.final["q_mean"])) if rec.final.get("q_mean") is not None else 0.0)
        ax = self.ax_m
        _style(ax, "Radiação no solo [kW/m²]")
        q0 = rec.frames[0]["q"].astype(float)
        self.qmesh = ax.pcolormesh(s["rec_x"], s["rec_y"], q0.T, cmap="magma",
                                   norm=qnorm(1.3 * q_ref), shading="nearest", rasterized=True)
        cb = fig.colorbar(self.qmesh, ax=ax, pad=0.01, fraction=0.04)
        cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)
        for lev, c in API_LEVELS:                       # níveis do API 521 marcados na barra de cores
            cb.ax.axhline(lev, color=c, lw=2)
        ax.plot([0], [0], marker="^", color="white", ms=7, mec="black", zorder=5)
        ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
        self.qc = None
        self.map_note = ax.text(0.02, 0.04, "", transform=ax.transAxes, color=FG, fontsize=8)
        # fluxo ao longo do vento
        ax = self.ax_l
        _style(ax, "Fluxo no solo, y = 0 [kW/m²]")
        ax.plot(xr, self.q_ch, "--", color=CHAM_C, lw=1.6, label="Chamberlain")
        ax.plot(xr, self.q_pt, ":", color=PT_C, lw=1.6, label="API 521 (pontual)")
        self.l_i, = ax.plot(xr, np.zeros_like(xr), color=LES_C, lw=0.9, alpha=0.45)
        self.l_m, = ax.plot(xr, np.zeros_like(xr), color=LES_C, lw=2.4, label="LES média")
        for lev, c in API_LEVELS:
            ax.axhline(lev, color=c, lw=0.7, alpha=0.6)
        ax.set_xlim(xr[0], xr[-1]); ax.set_ylim(0, 1.6 * q_ref)
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=7.5, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, ncol=3, loc="upper right")
        self.jl = int(np.argmin(np.abs(s["rec_y"])))
        # comprimento da chama
        ax = self.ax_t
        _style(ax, "Comprimento da chama [m]")
        ax.axhline(ch.L_b, color=CHAM_C, ls="--", lw=1.6, label=f"Chamberlain {ch.L_b:.1f} m")
        self.t_i, = ax.plot([], [], color=LES_C, lw=0.9, alpha=0.5)
        self.t_m, = ax.plot([], [], color=LES_C, lw=2.4, label="LES média")
        ax.set_ylim(0, 1.8 * ch.L_b); ax.set_xlabel("t [s]")
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=8, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, loc="upper right")
        self.ts, self.Ls, self.tm, self.Lm = [], [], [], []

    def draw(self, i: int):
        f = self.rec.frames[i]
        s = self.rec.static
        ch = self.ch
        self.im.set_data(self.norm(self.rs(f["lum"])).T)
        if self.env is not None:
            self.env.remove()
        zp = f["zp"].astype(float)
        self.env = self.ax.contour(s["xc"], s["zc"], zp.T, levels=[s["Z_st"]], colors=[ENVELOPE_C],
                                   linewidths=1.5, zorder=5)
        show = f["qmean"] if (f["averaging"] and f["qmean"] is not None) else f["q"]
        show = show.astype(float)
        self.qmesh.set_array(show.T.ravel())
        if self.qc is not None:
            self.qc.remove()
        lv = [(l, c) for l, c in API_LEVELS if l < show.max()]
        self.qc = self.ax_m.contour(s["rec_x"], s["rec_y"], show.T, levels=[l for l, _ in lv],
                                    colors=[c for _, c in lv], linewidths=1.5) if lv else None
        self.map_note.set_text("média temporal" if f["averaging"] else "instantâneo")
        self.l_i.set_ydata(f["q"].astype(float)[:, self.jl])
        if f["qmean"] is not None:
            self.l_m.set_ydata(f["qmean"].astype(float)[:, self.jl])
        self.ts.append(f["t"]); self.Ls.append(f["L"])
        self.t_i.set_data(self.ts, self.Ls)
        if f["averaging"] and math.isfinite(f["Lmean"]):
            self.tm.append(f["t"]); self.Lm.append(f["Lmean"])
            self.t_m.set_data(self.tm, self.Lm)
        fmt = lambda v, p="{:5.1f}": "  —  " if not math.isfinite(v) else p.format(v)  # noqa: E731
        qmax = float(f["qmean"].astype(float).max()) if f["qmean"] is not None else float("nan")
        self.box.set_text("\n".join([
            "              LES   Chamberlain",
            f"L [m]       {fmt(f['Lmean'])}   {ch.L_b:5.1f}",
            f"incl. [°]   {fmt(f['tiltmean'])}   {ch.alpha:5.1f}",
            f"q máx [kW/m²] {fmt(qmax, '{:4.2f}')}   {self.q_ch.max():4.2f}",
        ]))
        self.ax_t.set_xlim(0, max(self.t_end or 0.0, 1.02 * f["t"], 5.0))
        self.clock.set_text(f"t = {f['t']:5.1f} s")

    def render(self, path: str, fps: int = 30, every: int = 1):
        w = _writer(self.fig, path, fps)
        for i in range(0, len(self.rec.frames), every):
            self.draw(i)
            w.grab_frame(facecolor=BG)
        w.finish()
        return path

    def png(self, i: int = -1) -> bytes:
        self.draw(i % len(self.rec.frames))
        self.fig.canvas.draw()
        buf = io.BytesIO()
        from PIL import Image as PILImage
        PILImage.fromarray(np.asarray(self.fig.canvas.buffer_rgba())[..., :3]).save(buf, format="JPEG", quality=85)
        return buf.getvalue()


def render_still(src_png: str, path: str, seconds: float = 5.0, fps: int = 30):
    """Segmento de vídeo a partir de uma imagem fixa (1920×1080)."""
    ff = shutil.which("ffmpeg")
    subprocess.run([ff, "-y", "-loop", "1", "-framerate", str(fps), "-t", f"{seconds}", "-i", src_png,
                    "-vf", "scale=1920:1080,setsar=1,format=yuv420p", "-c:v", "libx264", "-crf", "16",
                    "-preset", "medium", path], check=True, capture_output=True)
    return path


def assemble(segments: list[str], out: str, fps: int = 30, size: tuple = (1920, 1080), crf: int = 16) -> str:
    """Concatena os segmentos em um MP4 final na resolução `size` (os de outra resolução são reescalados
    com Lanczos, preservando o aspecto)."""
    ff = shutil.which("ffmpeg")
    if ff is None:
        raise RuntimeError("ffmpeg não encontrado")
    segs = [p for p in segments if p and Path(p).exists()]
    cmd = [ff, "-y"]
    for p in segs:
        cmd += ["-i", p]
    W, H = size
    chains = "".join(f"[{i}:v]scale={W}:{H}:flags=lanczos:force_original_aspect_ratio=decrease,"
                     f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{i}];"
                     for i in range(len(segs)))
    cmd += ["-filter_complex", chains + "".join(f"[v{i}]" for i in range(len(segs)))
            + f"concat=n={len(segs)}:v=1:a=0[v]", "-map", "[v]", "-c:v", "libx264", "-crf", str(crf),
            "-preset", "slow", "-tune", "film", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


class RecordedLES:
    """Substitui o objeto FlareLES a partir de um flare_quadros.npz (refazer figuras e vídeo sem rodar a LES):
    expõe só o que validation_rows, summary_figure e as células do notebook usam."""

    def __init__(self, rec: Recorder):
        import torch
        from types import SimpleNamespace
        s, f = rec.static, rec.final
        n = float(f.get("n_avg", 1.0)) or 1.0
        self.rec = rec
        self.wind = float(s["u_ref"]) > 0
        self.tip, self.rec_x, self.rec_y = np.asarray(s["tip"]), np.asarray(s["rec_x"]), np.asarray(s["rec_y"])
        self.xf, self.zf, self.xc, self.zc = (np.asarray(s[k]) for k in ("xf", "zf", "xc", "zc"))
        self.avg_n = n
        self.avg_q = torch.from_numpy(np.asarray(f["q_mean"], float) * 1e3 * n).reshape(-1)
        self.avg_T = torch.from_numpy(np.asarray(f["T_proj"], float)[:, None, :] * n)
        self.avg_I = torch.from_numpy(np.asarray(f["I_proj"], float)[:, None, :] * n)
        self.cfg = SimpleNamespace(receiver_z=float(s["receiver_z"]), X_rad=float(s["X_rad"]))
        self.dev = SimpleNamespace(type="cuda" if "CUDA" in str(s["summary"]) else "cpu")
        self.step_n = int(f.get("steps", 0))
        self.wall = float(f.get("wall", 0.0))

    def mean_flame_length(self):
        return float(self.rec.final["L_mean"])

    def mean_tilt(self):
        return float(self.rec.final["tilt_mean"])

    def q_grid(self, q):
        return q.reshape(len(self.rec_x), len(self.rec_y)).cpu().numpy()

    def summary(self):
        return str(self.rec.static["summary"])


def run_and_record(les, sc: se.Scenario, title: str, t_end: float, t_avg: float, frame_dt: float = 0.1,
                   live_every: int = 5, dash_title: str = "", dash_sub: str = "", wind_label: str = "",
                   log_every: int = 50):
    """Roda a LES gravando um quadro a cada frame_dt; mostra o painel ao vivo a cada live_every quadros."""
    rec = Recorder(les, sc, title, wind_label)
    ch = sc.cham if les.wind else sc.cham0
    handle = None
    dash = None
    next_frame = 0.0
    try:
        from IPython.display import Image, display
    except ImportError:
        display = None
    try:
        while les.time < t_end:
            les.step()
            if les.time >= next_frame:
                averaging = les.time >= t_avg
                T, e, mask, q = les.diagnostics(averaging)
                rec.snap(les, e, q, averaging, T)
                next_frame += frame_dt
                n = len(rec.frames)
                if live_every and n % live_every == 0 and display is not None:
                    if dash is None:
                        dash = ZoomDashboard(rec, sc, ch, dash_title or title, dash_sub, t_end=t_end)
                    img = Image(data=dash.png(n - 1), format="jpeg")
                    if handle is None:
                        handle = display(img, display_id=True)
                    else:
                        handle.update(img)
                if log_every and n % log_every == 0:
                    print(f"t = {les.time:6.2f} s · L = {les.history['L'][-1]:5.1f} m · "
                          f"{les.wall / les.step_n * 1e3:5.0f} ms/passo", flush=True)
    except (KeyboardInterrupt, FloatingPointError, RuntimeError) as exc:
        # interrompido (ou divergiu): mantém os quadros já gravados para o vídeo
        print(f"LES interrompida em t = {les.time:.1f} s ({type(exc).__name__}: {exc}); seguindo com "
              f"{len(rec.frames)} quadros", flush=True)
    rec.finalize(les)
    return rec


# ===================================================================== vento
SPEED_COLORS = ["#1b3a5c", "#245b8a", "#2f7fb8", "#4aa3d8", "#7cc4ea", "#b5e0f6", "#e8f6ff"]


def _rose(ax, cl, highlight: int | None = None):
    from .wind import SECTORS, SPEED_EDGES
    ax.set_facecolor(PANEL)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    th = np.radians(np.arange(16) * 22.5)
    width = np.radians(22.5) * 0.9
    bottom = np.zeros(16)
    nb = cl.freq.shape[1]
    bars = []
    for b in range(nb):
        f = 100 * cl.freq[:, b]
        lab = (f"{SPEED_EDGES[b]:.1f}–{SPEED_EDGES[b + 1]:.0f}" if np.isfinite(SPEED_EDGES[b + 1])
               else f"> {SPEED_EDGES[b]:.0f}")
        bars.append(ax.bar(th, f, width=width, bottom=bottom, color=SPEED_COLORS[b % len(SPEED_COLORS)],
                           edgecolor=PANEL, lw=0.5, label=lab))
        bottom = bottom + f
    ax.set_xticks(th)
    ax.set_xticklabels(SECTORS, color=FG, fontsize=8)
    ax.tick_params(axis="y", colors=MUTED, labelsize=7)
    ax.grid(color=GRID, lw=0.6)
    ax.spines["polar"].set_color(GRID)
    hl = None
    if highlight is not None:
        hl = ax.bar([th[highlight]], [bottom[highlight] * 1.06], width=width * 1.05, bottom=0, fill=False,
                    edgecolor="white", lw=2.2)
    return bottom, hl


def _site_map(ax, grid, title):
    _style(ax, title)
    ax.set_aspect("equal")
    ax.set_xlabel("E [m]"); ax.set_ylabel("N [m]")
    ax.plot([0], [0], marker="^", color="white", ms=8, mec="black", zorder=6)
    R = grid.E.max()
    ax.annotate("N", xy=(0.93, 0.95), xytext=(0.93, 0.83), xycoords="axes fraction", color=FG, ha="center",
                fontsize=11, fontweight="bold", arrowprops=dict(arrowstyle="-|>", color=FG, lw=1.8))
    ax.set_xlim(-R, R); ax.set_ylim(-R, R)


def _zoom_radius(maps, level: float = 1.58) -> float:
    """Raio do mapa a mostrar: 1,3 × alcance da envoltória no menor nível API (mín. 40 m); se nenhum
    nível é atingido (tocha alta), usa o alcance de metade do fluxo máximo."""
    grid = maps["grid"]
    EE, NN = np.meshgrid(grid.E, grid.N, indexing="ij")
    env = maps["envelope"]
    m = env >= (level if env.max() >= level else 0.5 * env.max())
    r = float(np.hypot(EE, NN)[m].max()) if m.any() else 0.0
    return float(min(grid.E.max(), max(40.0, 10.0 * math.ceil(1.3 * r / 10.0))))


def sweep_level(maps) -> float | None:
    """Maior nível do API 521 (entre 4,73 e 1,58 kW/m²) com probabilidade > 0 em algum ponto; None se
    nenhum é atingido no solo."""
    for L in (4.73, 1.58):
        if L in maps["P"] and maps["P"][L].max() > 0:
            return L
    return None


def render_wind_sweep(cl, maps, les_down, path: str, U_les: float, title: str, level: float | None = None,
                      seconds: float = 14.0, hold: float = 2.5, fps: int = 30):
    """Varredura das direções: rosa dos ventos, pegada da LES girando e P(q ≥ nível) acumulada
    (nível automático; se nenhum nível do API 521 é atingido, mostra o máximo acumulado de q)."""
    from .wind import SECTORS, rotate_to_site
    grid = maps["grid"]
    xd, qd = les_down
    level = level if level is not None else sweep_level(maps)
    Psec = maps["P_sector"][level] if level is not None else None
    fig = _new_fig()
    gs = GridSpec(1, 3, figure=fig, left=0.03, right=0.975, top=0.83, bottom=0.08, wspace=0.28,
                  width_ratios=[0.9, 1, 1])
    fig.text(0.03, 0.94, title, color=FG, fontsize=18, fontweight="bold")
    fig.text(0.03, 0.895, f"{cl.series.source} · {cl.series.period} · perfil log z0 = {cl.z0:.2f} m · "
             f"vento na altura do tip ({cl.H:.0f} m)", color=MUTED, fontsize=11)
    ax_r = fig.add_subplot(gs[0, 0], projection="polar")
    ax_r.set_title("Rosa dos ventos [% do tempo]", color=FG, fontsize=11, fontweight="bold", pad=18)
    _, hl = _rose(ax_r, cl, 0)
    leg = ax_r.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), fontsize=8, ncol=4, facecolor=PANEL,
                      edgecolor=GRID, labelcolor=FG, title="velocidade no tip [m/s]", title_fontsize=8)
    leg.get_title().set_color(MUTED)
    ax_f = fig.add_subplot(gs[0, 1])
    _site_map(ax_f, grid, f"Pegada da LES ({U_les:.1f} m/s) girando com o vento [kW/m²]")
    q0 = rotate_to_site(xd, xd, qd, grid, 0.0)
    qn = qnorm(max(float(qd.max()), 0.3))
    m1 = ax_f.pcolormesh(grid.E, grid.N, q0.T, cmap="magma", norm=qn, shading="nearest", rasterized=True)
    cb = fig.colorbar(m1, ax=ax_f, fraction=0.045, pad=0.02)
    cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)
    ax_p = fig.add_subplot(gs[0, 2])
    if level is not None:
        _site_map(ax_p, grid, f"P(q ≥ {level:.2f} kW/m²) acumulada [%]")
        Pmax = max(1e-6, 100 * float(maps["P"][level].max()))
        m2 = ax_p.pcolormesh(grid.E, grid.N, np.ma.masked_all((len(grid.N), len(grid.E))), cmap="YlOrRd",
                             norm=mcolors.Normalize(0, Pmax), shading="nearest", rasterized=True)
    else:
        _site_map(ax_p, grid, "q máximo acumulado nas direções [kW/m²]")
        m2 = ax_p.pcolormesh(grid.E, grid.N, np.zeros((len(grid.N), len(grid.E))), cmap="magma", norm=qn,
                             shading="nearest", rasterized=True)
        note = ("nenhum nível do API 521 (≥ 1,58 kW/m²)\né atingido no solo" if maps["envelope"].max() < 1.58
                else "P = 0 nas classes de vento; só a envoltória\n(vento máximo observado) atinge 1,58 kW/m²")
        ax_p.text(0.03, 0.04, note, transform=ax_p.transAxes, color=FG, fontsize=9.5,
                  bbox=dict(facecolor=PANEL, edgecolor=GRID, alpha=0.85, pad=4))
    q_acc = np.zeros((len(grid.E), len(grid.N)))
    cb = fig.colorbar(m2, ax=ax_p, fraction=0.045, pad=0.02)
    cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)
    Rz = _zoom_radius(maps)
    for a in (ax_f, ax_p):
        a.set_xlim(-Rz, Rz); a.set_ylim(-Rz, Rz)
    lab = fig.text(0.5, 0.78, "", color=LES_C, fontsize=17, fontweight="bold", ha="center")
    arrow = [None]
    cont = [None, None]
    w = _writer(fig, path, fps)
    n = int(seconds * fps)
    for i in range(n + int(hold * fps)):
        theta = 360.0 * min(i, n - 1) / n
        kr = int((theta + 11.25) // 22.5)          # sem "dar a volta": controla o acúmulo
        k = kr % 16
        q = rotate_to_site(xd, xd, qd, grid, theta)
        m1.set_array(q.T.ravel())
        if cont[0] is not None:
            cont[0].remove()
        qs = float(maps.get("q_solar", 0.0))      # mesmo critério dos mapas de probabilidade
        lv = [(L - qs, c) for L, c in API_LEVELS if 0 < L - qs < q.max()]
        cont[0] = ax_f.contour(grid.E, grid.N, q.T, levels=[L for L, _ in lv], colors=[c for _, c in lv],
                               linewidths=1.5) if lv else None
        done = 16 if i >= n else min(16, kr + 1)
        if cont[1] is not None:
            cont[1].remove()
        if Psec is not None:
            Pacc = 100 * Psec[:done].sum(0)
            m2.set_array(np.ma.masked_less(Pacc, 0.05).T.ravel())
            lv = [p for p in (1, 5, 10, 20) if p < Pacc.max()]
            cont[1] = ax_p.contour(grid.E, grid.N, Pacc.T, levels=lv, colors="white", linewidths=0.9) if lv else None
        else:
            q_acc = np.maximum(q_acc, q)
            m2.set_array(q_acc.T.ravel())
            cont[1] = None
        if hl is not None:
            hl.remove()
        tops = 100 * cl.freq.sum(1)
        hl = ax_r.bar([np.radians(22.5 * k)], [tops[k] * 1.08], width=np.radians(22.5) * 0.95, bottom=0,
                      fill=False, edgecolor="white", lw=2.2)
        if arrow[0] is not None:
            arrow[0].remove()
        R = Rz
        th = math.radians(theta)
        dE, dN = -math.sin(th), -math.cos(th)
        arrow[0] = ax_f.annotate("", xy=(0.55 * R * dE, 0.55 * R * dN), xytext=(-0.85 * R * dE, -0.85 * R * dN),
                                 arrowprops=dict(arrowstyle="-|>", color=CHAM_C, lw=2.2, alpha=0.9))
        lab.set_text(f"vento de {SECTORS[k]} ({theta:5.1f}°) · {100 * cl.sector_freq[k]:4.1f}% do tempo")
        w.grab_frame(facecolor=BG)
    w.finish()
    return path


def risk_summary_figure(cl, maps, sc, path: str, title: str):
    """Resumo do clima de vento e das zonas probabilísticas (PNG 1920×1080)."""
    grid = maps["grid"]
    fig = _new_fig()
    fig.text(0.035, 0.955, title, color=FG, fontsize=18, fontweight="bold")
    d = cl.describe().split("\n")
    fig.text(0.035, 0.918, "  ·  ".join(d[:2]), color=MUTED, fontsize=10)
    fig.text(0.035, 0.893, "  ·  ".join(d[2:]), color=MUTED, fontsize=10)
    gl = GridSpec(2, 1, figure=fig, left=0.045, right=0.29, top=0.80, bottom=0.07, hspace=0.42,
                  height_ratios=[1.15, 1])
    ax = fig.add_subplot(gl[0], projection="polar")
    ax.set_title("Rosa dos ventos na altura do tip [% do tempo]", color=FG, fontsize=11, fontweight="bold",
                 pad=22)
    _rose(ax, cl, cl.dominant_sector)
    ax = fig.add_subplot(gl[1])
    _style(ax, "Perfil de camada limite (lei log)")
    z = np.linspace(max(cl.z0 * 2, 1.0), max(120.0, 1.5 * cl.H), 200)
    s = cl.series
    ax.plot(cl.profile(z), z, color=LES_C, lw=2.2, label=f"lei log, z0 = {cl.z0:.2f} m")
    ax.plot([s.U1.mean(), s.U2.mean()], [s.z1, s.z2], "o", color=CHAM_C, ms=8, label="médias dos dados")
    ax.axhline(cl.H, color=PT_C, ls=":", lw=1.4, label=f"tip ({cl.H:.0f} m)")
    ax.set_xlabel("U médio [m/s]"); ax.set_ylabel("z [m]"); ax.grid(color=GRID, lw=0.5)
    ax.legend(fontsize=8.5, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, loc="upper left")
    gr = GridSpec(2, 2, figure=fig, left=0.35, right=0.975, top=0.845, bottom=0.035, hspace=0.16, wspace=0.22,
                  height_ratios=[3.6, 1])
    env = maps["envelope"]
    Rz = _zoom_radius(maps)
    reached = [L for L in (4.73, 1.58) if maps["P"][L].max() > 0]
    # tochas altas podem não atingir nenhum nível no solo: aí mostram-se os próprios fluxos
    panels = (["P4.73", "P1.58"] if len(reached) == 2 else ["P1.58", "env"] if reached else ["env", "mean"])
    qn = qnorm(max(float(env.max()), 0.5))
    for j, kind in enumerate(panels):
        ax = fig.add_subplot(gr[0, j])
        if kind.startswith("P"):
            L = float(kind[1:])
            _site_map(ax, grid, f"P(q ≥ {L:.2f} kW/m²) com o flare queimando [%]")
            P = 100 * maps["P"][L]
            m = ax.pcolormesh(grid.E, grid.N, np.ma.masked_less(P, 0.05).T, cmap="YlOrRd", shading="nearest",
                              rasterized=True, vmin=0, vmax=max(1.0, float(P.max())))
            lv = [p for p in (1, 5, 10, 20, 50) if p < P.max()]
            if lv:
                cs = ax.contour(grid.E, grid.N, P.T, levels=lv, colors="white", linewidths=1.0)
                ax.clabel(cs, fmt="%d%%", fontsize=8, colors="white")
            if env.max() > L:
                ax.contour(grid.E, grid.N, env.T, levels=[L], colors=[CHAM_C], linewidths=1.8, linestyles="--")
            ax.plot([], [], "--", color=CHAM_C, label="envoltória (pior direção)")
            ax.plot([], [], color="white", lw=1.0, label="isolinhas de P [%]")
        else:
            field = env if kind == "env" else maps["q_mean"]
            _site_map(ax, grid, "q máximo em qualquer direção [kW/m²]" if kind == "env"
                      else "q médio ponderado pela rosa dos ventos [kW/m²]")
            m = ax.pcolormesh(grid.E, grid.N, field.T, cmap="magma", norm=qn, shading="nearest", rasterized=True)
            lv = [(l, c) for l, c in API_LEVELS if l < field.max()]
            if lv:
                ax.contour(grid.E, grid.N, field.T, levels=[l for l, _ in lv], colors=[c for _, c in lv],
                           linewidths=1.6)
            ax.plot([], [], color="none", label=f"máximo: {field.max():.2f} kW/m²")
        ax.set_xlim(-Rz, Rz); ax.set_ylim(-Rz, Rz)
        cb = fig.colorbar(m, ax=ax, fraction=0.045, pad=0.02)
        cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)
        ax.legend(loc="lower left", fontsize=8.5, facecolor=PANEL, edgecolor=GRID, labelcolor=FG)
    EE, NN = np.meshgrid(grid.E, grid.N, indexing="ij")
    Rr = np.hypot(EE, NN)

    def reach(mask):
        return float(Rr[mask].max()) if mask.any() else 0.0

    def edge(mask):   # a zona encosta na borda do mapa: o alcance é só um limite inferior
        return bool(mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any())

    rows, cells = [], []
    for lev, _ in API_LEVELS:
        ms = (env >= lev, maps["P"][lev] >= 0.01, maps["P"][lev] >= 0.10)
        rows.append((lev, *(reach(m) for m in ms)))
        cells.append([f"{lev:.2f}"] + [("≥ " if edge(m) else "") + f"{reach(m):.0f}" for m in ms])
    ax = fig.add_subplot(gr[1, :])
    ax.set_axis_off()
    tb = ax.table(cellText=cells, colLabels=["nível [kW/m²]", "envoltória [m]", "P ≥ 1% [m]", "P ≥ 10% [m]"],
                  loc="center", cellLoc="center", colLoc="center", bbox=[0.0, 0.0, 0.55, 1.0])
    tb.auto_set_font_size(False)
    tb.set_fontsize(10)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_facecolor(PANEL if r else "#1d2733")
        cell.get_text().set_color(API_LEVELS[r - 1][1] if (c == 0 and r) else FG)
    qs = float(maps.get("q_solar", 0.0))
    crit = (f"com a radiação do flare + {qs:.2f} kW/m² de solar" if qs > 0
            else "só com a radiação do flare (sem solar)")
    ax.text(0.58, 0.5, "Alcance máximo (a partir da base do flare) em que o nível\n"
            "é atingido: na pior direção (envoltória, até a maior velocidade\n"
            f"observada, {maps.get('U_max', 0.0):.1f} m/s) e com probabilidade ≥ 1% / ≥ 10% do\n"
            "tempo de queima, ponderada pela rosa. Níveis do API 521\n"
            f"comparados {crit}.",
            transform=ax.transAxes, color=MUTED, fontsize=9.5, va="center")
    fig.savefig(path, dpi=DPI, facecolor=BG)
    return rows
