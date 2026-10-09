"""Figuras do estudo (matplotlib, tema escuro, vírgula decimal) — 1920×1080 para o vídeo e o relatório."""
from __future__ import annotations

import math

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker

from .video import br

BG, PANEL, GRID, TXT, MUTED = "#0d1117", "#131a24", "#2a3442", "#e8edf4", "#8b95a5"
ACCENT, COOL, GOOD = "#ffb040", "#6fc3ff", "#7ee0a2"


class _Comma(ticker.ScalarFormatter):
    def __call__(self, x, pos=None):
        return br(super().__call__(x, pos))


def _style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=12)
    ax.grid(color=GRID, lw=0.6, alpha=0.6)
    for axis in (ax.xaxis, ax.yaxis):
        if type(axis.get_major_formatter()) is ticker.ScalarFormatter:
            axis.set_major_formatter(_Comma())
    if title:
        ax.set_title(br(title), color=TXT, fontsize=16, loc="left", pad=10, fontweight="bold")
    if xlabel:
        ax.set_xlabel(br(xlabel), color=MUTED, fontsize=13)
    if ylabel:
        ax.set_ylabel(br(ylabel), color=MUTED, fontsize=13)


def _fig(title, subtitle=None, size=(19.2, 10.8)):
    fig = plt.figure(figsize=size, dpi=100, facecolor=BG)
    fig.text(0.04, 0.935, br(title), color=TXT, fontsize=30, fontweight="bold")
    if subtitle:
        fig.text(0.04, 0.895, br(subtitle), color=MUTED, fontsize=17)
    return fig


def _save(fig, path):
    if path:
        fig.savefig(path, facecolor=fig.get_facecolor())
        plt.close(fig)
    return path or fig


# ------------------------------------------------------------ curva de capacidade
def capacity_figure(curve, cfd_point=None, path=None, coke_wall_C=520.0, title="Quanto plástico o reator processa",
                    subtitle=None):
    """curve: lista de CSTRResult (capacity_curve); cfd_point: kpis do reator 3D."""
    Tw = np.array([c.T_wall - 273.15 for c in curve])
    F = np.array([3600 * c.feed for c in curve])
    Tb = np.array([c.T - 273.15 for c in curve])
    Q = np.array([c.duty / 1e3 for c in curve])
    fig = _fig(title, subtitle or "reator ideal 0-D (linhas) e CFD 3D (ponto) · carga pós-consumo, parede aquecida")
    ax1 = fig.add_axes([0.06, 0.12, 0.40, 0.70])
    ax2 = fig.add_axes([0.54, 0.12, 0.38, 0.70])
    _style(ax1, "Vazão de plástico", "temperatura da parede [°C]", "kg/h")
    ax1.plot(Tw, F, color=ACCENT, lw=3.5)
    ax1.fill_between(Tw, 0, F.max() * 1.15, where=Tw >= coke_wall_C, color="#ff6b6b", alpha=0.12)
    ax1.text(coke_wall_C + 2, F.max() * 1.07, "risco de coque\nna parede", color="#ff9b9b", fontsize=12, va="top")
    _style(ax2, "Temperatura do fundido e calor", "temperatura da parede [°C]", "°C")
    ax2.plot(Tw, Tb, color=COOL, lw=3.5, label="fundido")
    ax2b = ax2.twinx()
    ax2b.plot(Tw, Q, color=GOOD, lw=2.5, ls="--", label="calor pela camisa")
    ax2b.tick_params(colors=MUTED, labelsize=12)
    ax2b.set_ylabel("kW", color=MUTED, fontsize=13)
    ax2b.yaxis.set_major_formatter(_Comma())
    for s in ax2b.spines.values():
        s.set_color(GRID)
    if cfd_point is not None:
        ax1.plot([cfd_point["T_wall_C"]], [cfd_point["feed_kgph"]], "o", ms=16, color="white", mec=ACCENT, mew=3,
                 zorder=5)
        ax1.annotate(br(f"CFD 3D: {cfd_point['feed_kgph']:.0f} kg/h"), (cfd_point["T_wall_C"], cfd_point["feed_kgph"]),
                     xytext=(-190, 30), textcoords="offset points", color=TXT, fontsize=15, fontweight="bold",
                     arrowprops=dict(arrowstyle="-", color=MUTED))
        ax2.plot([cfd_point["T_wall_C"]], [cfd_point["T_bulk_C"]], "o", ms=16, color="white", mec=COOL, mew=3, zorder=5)
        ax2.annotate(br(f"CFD 3D: {cfd_point['T_bulk_C']:.1f} °C"), (cfd_point["T_wall_C"], cfd_point["T_bulk_C"]),
                     xytext=(-210, 25), textcoords="offset points", color=TXT, fontsize=15, fontweight="bold",
                     arrowprops=dict(arrowstyle="-", color=MUTED))
    ax1.set_ylim(0, F.max() * 1.15)
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    leg = ax2.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=13, facecolor=PANEL, edgecolor=GRID)
    for t in leg.get_texts():
        t.set_color(TXT)
    return _save(fig, path)


# ---------------------------------------------------------------- cortes 2D
def _plane(f, q, axis="y"):
    """Fatia vertical que passa pelo eixo (plano x–z, média das duas linhas centrais em y)."""
    q = np.asarray(q)
    j = q.shape[1] // 2
    return 0.5 * (q[:, j - 1, :] + q[:, j, :])


def sections_figure(reactor, path=None, title="Por dentro do reator", subtitle=None):
    """Plano vertical pelo eixo (referencial da fita): temperatura, massa molar e viscosidade, velocidade."""
    f = reactor.flow
    fl = (f.fluid > 0.5).cpu().numpy()
    x = f.xc
    z = f.zc
    T = reactor.T.cpu().numpy() - 273.15
    Mw = _bulk_Mw(reactor)
    eta = reactor._mu(f.gamma).cpu().numpy()
    ul, vl, wl = [a.cpu().numpy() for a in f.lab_velocity_centers()]
    U = np.sqrt(ul ** 2 + vl ** 2 + wl ** 2)
    m = _plane(f, fl) > 0.5
    fig = _fig(title, subtitle or "corte vertical pelo eixo, no referencial que gira com a fita")
    panels = [("Temperatura", T, "inferno", "°C", None),
              ("Massa molar média (Mw)", Mw, "viridis", "kg/mol", None),
              ("Viscosidade", np.log10(np.maximum(eta, 1e-6)), "magma", "log₁₀ Pa s", None),
              ("Velocidade (laboratório)", U, "cividis", "m/s", None)]
    ext = [x[0], x[-1], 0.0, reactor.tank.H_L]
    R = reactor.tank.R
    for k, (name, q, cmap, unit, _) in enumerate(panels):
        ax = fig.add_axes([0.04 + 0.24 * k, 0.10, 0.20, 0.72])
        P = np.where(m, _plane(f, q), np.nan)
        vals = P[np.isfinite(P)]
        lo, hi = np.percentile(vals, 1), np.percentile(vals, 99.5)
        im = ax.imshow(P.T, origin="lower", extent=ext, cmap=cmap, vmin=lo, vmax=hi, interpolation="bilinear",
                       aspect="equal")
        if name.startswith("Velocidade"):
            jj = slice(None, None, 3)
            Wp = _plane(f, wl)
            Up = _plane(f, ul)
            X, Z = np.meshgrid(x, z, indexing="ij")
            ax.quiver(X[jj, jj], Z[jj, jj], np.where(m, Up, 0)[jj, jj], np.where(m, Wp, 0)[jj, jj], color="white",
                      alpha=0.55, scale=6.0, width=0.004)
        _style(ax, name)
        ax.set_xlim(-R * 1.02, R * 1.02)
        ax.set_ylim(0, reactor.tank.H_L)
        ax.set_xticks([-R, 0, R])
        ax.set_xticklabels([br(f"{-R:.1f}"), "0", br(f"{R:.1f}")])
        ax.set_xlabel("r [m]", color=MUTED, fontsize=12)
        if k == 0:
            ax.set_ylabel("altura [m]", color=MUTED, fontsize=12)
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.05, pad=0.08)
        cb.ax.tick_params(colors=MUTED, labelsize=11)
        cb.ax.xaxis.set_major_formatter(_Comma())
        cb.set_label(br(unit), color=MUTED, fontsize=12)
        cb.outline.set_edgecolor(GRID)
    return _save(fig, path)


def _bulk_Mw(reactor):
    import torch
    num = sum(s["Y"] * reactor._Mw(c, s) for (c, _), s in zip(reactor.items, reactor.state))
    den = sum(s["Y"] for s in reactor.state).clamp(min=1e-12)
    return (num / den).cpu().numpy()


# ----------------------------------------------------------------- mapa de parede
def wall_map_figure(reactor, path=None, title="Onde o calor entra", subtitle=None):
    """Fluxo de calor local na parede lateral, desenrolada (ângulo × altura), no referencial da fita."""
    import torch
    f = reactor.flow
    sc = reactor._last_sc
    q = sc.wall_flux(reactor.T) * reactor.cfg.rho0 * reactor.cp0          # W por célula
    fl = reactor.flm > 0
    side = fl & (f.r_c > reactor.tank.R - 1.5 * f.h) & (q > 0)
    X, Y = f._t(f.P_c[..., 0]), f._t(f.P_c[..., 1])
    th = torch.atan2(Y, X)[side].cpu().numpy()
    zz = f._t(f.P_c[..., 2])[side].cpu().numpy()
    qq = q[side].cpu().numpy()
    nth, nz = 48, f.nz
    H2, xe, ye = np.histogram2d(th, zz, bins=[nth, nz], range=[[-math.pi, math.pi], [0, reactor.tank.H_L]], weights=qq)
    A = 2 * math.pi * reactor.tank.R * reactor.tank.H_L / (nth * nz)           # área de cada célula do mapa
    qmap = H2 / A / 1e3                                                          # kW/m²
    fig = _fig(title, subtitle or "fluxo de calor na parede lateral, desenrolada (ângulo × altura), em kW/m²")
    ax = fig.add_axes([0.06, 0.12, 0.80, 0.70])
    im = ax.imshow(qmap.T, origin="lower", extent=[-180, 180, 0, reactor.tank.H_L], aspect="auto", cmap="inferno",
                   interpolation="bicubic")
    _style(ax, None, "ângulo em relação à fita [°]", "altura [m]")
    cax = fig.add_axes([0.88, 0.12, 0.018, 0.70])
    cb = fig.colorbar(im, cax=cax)
    cb.ax.tick_params(colors=MUTED, labelsize=12)
    cb.ax.yaxis.set_major_formatter(_Comma())
    cb.set_label("kW/m²", color=MUTED, fontsize=13)
    cb.outline.set_edgecolor(GRID)
    return _save(fig, path)


# --------------------------------------------------------------------- TGA
def tga_figure(path=None, title="Cinética: termogravimetria a 10 K/min", subtitle=None):
    from . import kinetics as kin
    fig = _fig(title, subtitle or "cisão aleatória (L = 2), E de Aboulkas et al. (2010); marcas = picos da literatura")
    ax = fig.add_axes([0.07, 0.12, 0.88, 0.70])
    _style(ax, None, "temperatura [°C]", "taxa de perda de massa [%/°C]")
    colors = {"HDPE": ACCENT, "LDPE": "#ffd27a", "PP": COOL, "PS": "#c49bff", "PET": GOOD}
    for key, col in colors.items():
        p = kin.POLYMERS[key]
        T, a, d = kin.tga(p, 10.0)
        ax.plot(T - 273.15, 100 * d, color=col, lw=3, label=f"{key} ({p.name})")
        ax.axvline(p.tpeak_10, color=col, lw=1, ls=":", alpha=0.8)
    ax.set_xlim(330, 560)
    leg = ax.legend(fontsize=13, facecolor=PANEL, edgecolor=GRID, loc="upper left")
    for t in leg.get_texts():
        t.set_color(TXT)
    return _save(fig, path)
