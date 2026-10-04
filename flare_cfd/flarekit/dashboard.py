"""Painel ao vivo da LES e gravação do vídeo (MP4) quadro a quadro.

O mesmo quadro desenhado para o vídeo é mostrado no notebook enquanto o solver roda,
de modo que os gráficos acompanham a solução em tempo real.
"""
from __future__ import annotations

import io
import math
import re
import time

import numpy as np
from matplotlib import colors as mcolors
from matplotlib import text as mtext
from matplotlib import ticker
from matplotlib.animation import FFMpegWriter
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from . import semiempirical as se

BG, PANEL, FG, MUTED, GRID = "#0d1117", "#131a22", "#e6edf3", "#8b98a5", "#263241"
ACCENT, LES_C, CHAM_C, PT_C = "#f0a35e", "#ffb347", "#7fd1ff", "#b9c2cc"
API_LEVELS = [(1.58, "#6cc08f"), (4.73, "#e0b24a"), (6.31, "#f08a4b"), (9.46, "#f2766b")]


_DEC = re.compile(r"(?<=\d)\.(?=\d)")


def br(text: str) -> str:
    """Vírgula decimal (norma brasileira) em todo número de um texto: '6.8 m/s' → '6,8 m/s'."""
    return _DEC.sub(",", text) if isinstance(text, str) else text


class CommaFormatter(ticker.ScalarFormatter):
    """Rótulos de eixo com vírgula decimal."""

    def __call__(self, x, pos=None):
        return br(super().__call__(x, pos))


def br_figure(fig):
    """Converte para vírgula decimal todos os textos e rótulos numéricos de eixos de uma figura."""
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            fm = axis.get_major_formatter()
            if type(fm) is ticker.ScalarFormatter:
                axis.set_major_formatter(CommaFormatter())
        for tb in getattr(ax, "tables", []):
            for cell in tb.get_celld().values():
                cell.get_text().set_text(br(cell.get_text().get_text()))
    for t in fig.findobj(mtext.Text):
        s = t.get_text()
        if s and "." in s:
            t.set_text(br(s))
    return fig


def _style(ax, title=None):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    if title:
        ax.set_title(title, color=FG, fontsize=11, loc="left", pad=6, fontweight="bold")


def frustum_outline_xz(ch: se.Chamberlain, tip):
    """Trapézio do frustum de Chamberlain no plano y = 0 (vento em +x)."""
    base, ax, e1, _ = se.frustum_axis(ch, np.asarray(tip, float))
    top = base + ch.R_l * ax
    pts = [base - ch.W1 / 2 * e1, top - ch.W2 / 2 * e1, top + ch.W2 / 2 * e1, base + ch.W1 / 2 * e1,
           base - ch.W1 / 2 * e1]
    return np.array([[p[0], p[2]] for p in pts])


class LiveDashboard:
    def __init__(self, les, sc: se.Scenario, title: str, view_x=(-25.0, 95.0), view_z=(0.0, 80.0),
                 dpi: int = 120, live: bool = True):
        self.les, self.sc, self.live = les, sc, live
        self.fig = Figure(figsize=(16, 9), dpi=dpi, facecolor=BG)
        FigureCanvasAgg(self.fig)
        gs = GridSpec(3, 5, figure=self.fig, left=0.045, right=0.985, top=0.865, bottom=0.07,
                      hspace=0.45, wspace=0.5)
        self.ax_s = self.fig.add_subplot(gs[0:2, 0:3])
        self.ax_m = self.fig.add_subplot(gs[0:2, 3:5])
        self.ax_l = self.fig.add_subplot(gs[2, 0:2])
        self.ax_t = self.fig.add_subplot(gs[2, 2:4])
        self.ax_i = self.fig.add_subplot(gs[2, 4])
        self.fig.text(0.045, 0.952, title, color=FG, fontsize=17, fontweight="bold")
        self.sub = self.fig.text(0.045, 0.918, "", color=MUTED, fontsize=10.5)
        self.clock = self.fig.text(0.985, 0.95, "", color=ACCENT, fontsize=20, ha="right", fontweight="bold",
                                   family="monospace")
        ch = sc.cham if les.wind else sc.cham0
        self.ch = ch

        # ---- vista lateral: emissão luminosa integrada na linha de visada ("câmera sintética")
        ax = self.ax_s
        _style(ax, "Vista lateral: emissão luminosa integrada na linha de visada  ·  envelope Z̃ = Z_st")
        img0 = self._side_view(les.fields()[1])
        self.lum_norm = mcolors.PowerNorm(0.45, vmin=0.0, vmax=1.0)
        self.mesh = ax.pcolormesh(les.xf, les.zf, img0.T, cmap="inferno", norm=self.lum_norm, shading="flat",
                                  rasterized=True)
        cb = self.fig.colorbar(self.mesh, ax=ax, pad=0.01, fraction=0.035)
        cb.set_label("luminosidade relativa", color=MUTED); cb.ax.tick_params(colors=MUTED, labelsize=8)
        cb.outline.set_edgecolor(GRID)
        self.lum_cb = cb
        ax.add_patch(Rectangle((-0.6, 0), 1.2, les.tip[2], color="#5c6773", zorder=3))
        fr = frustum_outline_xz(ch, les.tip)
        ax.plot(fr[:, 0], fr[:, 1], ls="--", color=CHAM_C, lw=1.6, zorder=4, label="Chamberlain (1987)")
        ax.plot([], [], color="#4dd0e1", lw=1.4, label="LES: envelope da chama")
        self.flame_c = None
        self.vmax_hist = []
        ax.set_xlim(*view_x); ax.set_ylim(*view_z); ax.set_aspect("equal")
        ax.set_xlabel("x [m] (vento →)"); ax.set_ylabel("z [m]")
        ax.legend(loc="upper right", fontsize=9, facecolor=PANEL, edgecolor=GRID, labelcolor=FG)
        if les.wind:
            ax.annotate("", xy=(view_x[0] + 12, view_z[1] - 6), xytext=(view_x[0] + 2, view_z[1] - 6),
                        arrowprops=dict(arrowstyle="-|>", color=CHAM_C, lw=2))
            ax.text(view_x[0] + 2, view_z[1] - 11, f"{les.cfg.u_ref:.1f} m/s", color=CHAM_C, fontsize=9)

        # ---- mapa de radiação no solo
        ax = self.ax_m
        _style(ax, "Radiação incidente no solo (1,5 m) [kW/m²]")
        q0 = les.q_grid(les.q_inst) / 1e3
        self.norm = mcolors.PowerNorm(0.6, vmin=0.0, vmax=10.0)
        self.qmesh = ax.pcolormesh(les.rec_x, les.rec_y, q0.T, cmap="magma", norm=self.norm, shading="nearest",
                                   rasterized=True)
        cb = self.fig.colorbar(self.qmesh, ax=ax, pad=0.01, fraction=0.04)
        cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)
        for lev, c in API_LEVELS:
            cb.ax.axhline(lev, color=c, lw=2)
        self.q_cont = None
        ax.plot([0], [0], marker="^", color="white", ms=9, mec="black", zorder=5)
        ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
        ax.set_xlim(les.rec_x[0], les.rec_x[-1]); ax.set_ylim(les.rec_y[0], les.rec_y[-1])
        self.map_note = ax.text(0.02, 0.03, "", transform=ax.transAxes, color=FG, fontsize=9)
        handles = [Line2D([], [], color=c, lw=2, label=f"{lev:.2f}") for lev, c in API_LEVELS]
        ax.legend(handles=handles, title="API 521", loc="upper right", fontsize=8, title_fontsize=8,
                  facecolor=PANEL, edgecolor=GRID, labelcolor=FG).get_title().set_color(FG)

        # ---- fluxo ao longo do vento (y = 0) vs modelos semi-empíricos
        ax = self.ax_l
        _style(ax, "Fluxo no solo ao longo do vento (y = 0)")
        jl = int(np.argmin(np.abs(les.rec_y)))
        self.jl = jl
        xr = les.rec_x
        rec = np.stack([xr, np.zeros_like(xr), np.full_like(xr, les.cfg.receiver_z)], 1)
        self.q_cham_line = se.q_chamberlain(rec, ch, les.tip, sc.T_inf, sc.RH) / 1e3
        center = se.flame_center_chamberlain(ch, les.tip)
        self.q_pt_line = se.q_point_source(rec, center, les.cfg.X_rad, sc.Q, sc.T_inf, sc.RH) / 1e3
        ax.plot(xr, self.q_cham_line, "--", color=CHAM_C, lw=1.8, label="Chamberlain (frustum)")
        ax.plot(xr, self.q_pt_line, ":", color=PT_C, lw=1.8, label="Fonte pontual (API 521)")
        self.l_inst, = ax.plot(xr, np.zeros_like(xr), color=LES_C, lw=1.0, alpha=0.45, label="LES instantâneo")
        self.l_mean, = ax.plot(xr, np.zeros_like(xr), color=LES_C, lw=2.6, label="LES média")
        for lev, c in API_LEVELS:
            ax.axhline(lev, color=c, lw=0.8, alpha=0.6)
        ymax = 1.6 * max(self.q_cham_line.max(), self.q_pt_line.max())
        ax.set_ylim(0, ymax); ax.set_xlim(xr[0], xr[-1])
        ax.set_xlabel("x [m]"); ax.set_ylabel("q'' [kW/m²]")
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=8, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, ncol=2, loc="upper right")

        # ---- comprimento da chama no tempo
        ax = self.ax_t
        _style(ax, "Comprimento da chama no tempo")
        refL = ch.L_b
        ax.axhline(refL, color=CHAM_C, ls="--", lw=1.6, label=f"Chamberlain {refL:.1f} m")
        if not les.wind:
            ax.axhline(sc.L_api, color=PT_C, ls=":", lw=1.6, label=f"API 521 {sc.L_api:.1f} m")
        self.t_inst, = ax.plot([], [], color=LES_C, lw=1.0, alpha=0.5, label="LES instantâneo")
        self.t_mean, = ax.plot([], [], color=LES_C, lw=2.6, label="LES média (I = 0,5)")
        ax.set_ylim(0, 1.8 * refL); ax.set_xlabel("t [s]"); ax.set_ylabel("L [m]")
        ax.grid(color=GRID, lw=0.5)
        ax.legend(fontsize=8, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, loc="upper right")
        self.mean_hist_t, self.mean_hist_L = [], []

        # ---- painel de informações
        ax = self.ax_i
        ax.set_facecolor(PANEL); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(GRID)
        self.info = ax.text(0.04, 0.96, "", transform=ax.transAxes, va="top", color=FG, fontsize=8.4,
                            family="monospace", linespacing=1.45)
        self.writer = None
        self.handle = None

    def _side_view(self, e):
        """Emissão luminosa integrada em y (vista lateral, sem reabsorção), em unidades de X_rad·Q por
        área projetada; o painel mostra o valor relativo ao percentil 99,7 recente."""
        les = self.les
        tot = (e * les.vol).sum().clamp(min=1e-30)
        scale = les.cfg.X_rad * les.Q / tot
        col = (e * les.Dc[1]).sum(1) * scale / 1e3
        return col.float().cpu().numpy()

    # ------------------------------------------------------------------ vídeo
    def start_video(self, path: str, fps: int = 24):
        self.writer = FFMpegWriter(fps=fps, bitrate=9000, codec="libx264",
                                   extra_args=["-pix_fmt", "yuv420p", "-preset", "medium"])
        self.writer.setup(self.fig, path, dpi=self.fig.dpi)
        self.fps = fps

    def finish_video(self, hold_s: float = 2.5):
        if self.writer is not None:
            for _ in range(int(hold_s * self.fps)):
                self.writer.grab_frame(facecolor=BG)
            self.writer.finish()
            self.writer = None

    # --------------------------------------------------------------- quadro
    def update(self, T, e, mask, q, averaging: bool, sub: str = ""):
        les, ch = self.les, self.ch
        img = self._side_view(e)
        self.vmax_hist.append(float(np.percentile(img, 99.7)))
        vmax = max(np.median(self.vmax_hist[-30:]), 1e-6)
        self.mesh.set_array(np.clip(img / vmax, 0.0, 1.0).T.ravel())
        if self.flame_c is not None:
            self.flame_c.remove()
        Zp = les.Z.max(1).values.float().cpu().numpy()
        self.flame_c = self.ax_s.contour(les.xc, les.zc, Zp.T, levels=[les.Z_st], colors=["#4dd0e1"],
                                         linewidths=1.4)
        qg = les.q_grid(q) / 1e3
        qm = les.q_grid(les.avg_q / les.avg_n) / 1e3 if les.avg_n > 0 else None
        show = qm if (averaging and qm is not None) else qg
        self.qmesh.set_array(show.T.ravel())
        if self.q_cont is not None:
            self.q_cont.remove()
        levels = [lev for lev, _ in API_LEVELS if lev < show.max()]
        cols = [c for lev, c in API_LEVELS if lev < show.max()]
        self.q_cont = self.ax_m.contour(les.rec_x, les.rec_y, show.T, levels=levels, colors=cols, linewidths=1.8) \
            if levels else None
        self.map_note.set_text("média temporal" if (averaging and qm is not None) else "instantâneo")
        self.l_inst.set_ydata(qg[:, self.jl])
        if qm is not None:
            self.l_mean.set_ydata(qm[:, self.jl])
        h = les.history
        self.t_inst.set_data(h["t"], h["L"])
        if averaging and les.avg_n > 0:
            self.mean_hist_t.append(les.time)
            self.mean_hist_L.append(les.mean_flame_length())
            self.t_mean.set_data(self.mean_hist_t, self.mean_hist_L)
        self.ax_t.set_xlim(0, max(5.0, les.time * 1.05))
        Lm = les.mean_flame_length()
        tm = les.mean_tilt()
        qmax_m = float(qm.max()) if qm is not None else float("nan")
        fmt = lambda v, f="{:.1f}": "  —  " if not math.isfinite(v) else f.format(v)  # noqa: E731
        lines = [
            f"t     {les.time:6.2f} s",
            f"passo {les.step_n:6d}",
            f"Δt    {les.dt * 1e3:6.1f} ms  CFL {les._last_cfl:.2f}",
            f"wall  {les.wall:6.0f} s",
            "",
            "VALIDAÇÃO     LES   Cham.",
            f"L [m]      {fmt(Lm):>6} {ch.L_b:6.1f}",
            f"incl. [°]  {fmt(tm):>6} {ch.alpha:6.1f}",
            f"q máx      {fmt(qmax_m, '{:.2f}'):>6} {self.q_cham_line.max():6.2f}",
            "(q em kW/m², médias)",
            "",
            f"X_rad = {les.cfg.X_rad:.3f} (F_s)",
        ]
        self.info.set_text("\n".join(lines))
        self.clock.set_text(f"t = {les.time:5.1f} s")
        self.sub.set_text(sub)
        if self.writer is not None:
            self.writer.grab_frame(facecolor=BG)
        else:
            self.fig.canvas.draw()
        if self.live:
            self._show()

    def _show(self):
        try:
            from IPython.display import Image, display
        except ImportError:
            return
        buf = io.BytesIO()
        from PIL import Image as PILImage
        rgba = np.asarray(self.fig.canvas.buffer_rgba())
        PILImage.fromarray(rgba[..., :3]).save(buf, format="JPEG", quality=82)
        img = Image(data=buf.getvalue(), format="jpeg")
        if self.handle is None:
            self.handle = display(img, display_id=True)
        else:
            self.handle.update(img)

    def save_png(self, path: str):
        self.fig.savefig(path, dpi=self.fig.dpi, facecolor=BG)


def run_live(les, sc, title: str, t_end: float, t_avg: float, frame_dt: float = 0.1,
             video_path: str | None = "flare_les.mp4", live: bool = True, fps: int = 24,
             max_wall_s: float | None = None, log_every: int = 0):
    """Roda a LES até t_end, atualizando o painel a cada frame_dt (tempo físico) e gravando o vídeo."""
    dash = LiveDashboard(les, sc, title, live=live)
    if video_path:
        dash.start_video(video_path, fps=fps)
    sub = (f"{les.summary()}  ·  Smagorinsky + Z̃/β-PDF (equilíbrio) + fuligem  ·  "
           f"média a partir de t = {t_avg:.0f} s")
    next_frame = 0.0
    t_start = time.time()
    try:
        while les.time < t_end:
            les.step()
            if les.time >= next_frame:
                averaging = les.time >= t_avg
                T, e, mask, q = les.diagnostics(averaging)
                dash.update(T, e, mask, q, averaging, sub)
                next_frame += frame_dt
                if log_every and len(les.history["t"]) % log_every == 0:
                    print(f"t = {les.time:6.2f} s · L = {les.history['L'][-1]:5.1f} m · "
                          f"{les.wall / les.step_n * 1e3:5.0f} ms/passo", flush=True)
            if max_wall_s and time.time() - t_start > max_wall_s:
                print(f"Tempo de parede máximo atingido em t = {les.time:.1f} s.")
                break
    finally:
        dash.finish_video()
    return dash
