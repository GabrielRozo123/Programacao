"""Resultados finais: tabela de validação, figura-resumo (16:9) e composição do vídeo final."""
from __future__ import annotations

import math
import shutil
import subprocess

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from . import safety
from . import semiempirical as se
from .dashboard import API_LEVELS, BG, CHAM_C, FG, GRID, LES_C, MUTED, PANEL, PT_C, _style, br_figure, frustum_outline_xz


def validation_rows(les, sc: se.Scenario, refs: dict) -> list[dict]:
    ch = sc.cham if les.wind else sc.cham0
    Lm, tm = les.mean_flame_length(), les.mean_tilt()
    qm = (les.avg_q / max(les.avg_n, 1)).max().item() / 1e3
    xr = les.rec_x
    rec = np.stack([xr, np.zeros_like(xr), np.full_like(xr, les.cfg.receiver_z)], 1)
    q_ch = se.q_chamberlain(rec, ch, les.tip, sc.T_inf, sc.RH).max() / 1e3
    rows = [
        {"grandeza": "Comprimento da chama L [m]", "LES": Lm, "referência": ch.L_b, "fonte": "Chamberlain (1987)"},
        {"grandeza": "Inclinação da chama [°]", "LES": tm, "referência": ch.alpha, "fonte": "Chamberlain (1987)"},
        {"grandeza": "Fluxo máximo no solo [kW/m²]", "LES": qm, "referência": q_ch, "fonte": "Chamberlain (frustum)"},
    ]
    if not les.wind:
        rows += [
            {"grandeza": "L vs API 521 [m]", "LES": Lm, "referência": sc.L_api, "fonte": "API 521 (Beychok)"},
            {"grandeza": "L vs Delichatsios [m]", "LES": Lm, "referência": refs["delichatsios"]["L"],
             "fonte": "Delichatsios (1993)"},
            {"grandeza": "L vs Heskestad [m]", "LES": Lm, "referência": refs["L_heskestad"], "fonte": "Heskestad"},
        ]
    for r in rows:
        r["erro_%"] = 100.0 * (r["LES"] - r["referência"]) / r["referência"] if r["referência"] else float("nan")
    return rows


def print_validation(rows):
    print(f"{'Grandeza':34s} {'LES':>8s} {'Ref.':>8s} {'Erro':>8s}  Fonte")
    for r in rows:
        print(f"{r['grandeza']:34s} {r['LES']:8.2f} {r['referência']:8.2f} {r['erro_%']:7.1f}%  {r['fonte']}")


def summary_figure(les, sc: se.Scenario, refs: dict, path: str, title: str, dpi: int = 120,
                   subtitle: str | None = None):
    ch = sc.cham if les.wind else sc.cham0
    fig = Figure(figsize=(16, 9), dpi=dpi, facecolor=BG)
    FigureCanvasAgg(fig)
    gs = GridSpec(2, 3, figure=fig, left=0.085, right=0.985, top=0.86, bottom=0.06, hspace=0.34, wspace=0.30,
                  height_ratios=[1.2, 1.0])
    fig.text(0.045, 0.952, title, color=FG, fontsize=17, fontweight="bold")
    fig.text(0.045, 0.918, subtitle if subtitle is not None else
             f"Médias de {les.avg_n:.0f} quadros (t ≥ início da média) · {les.summary()}",
             color=MUTED, fontsize=10.5)

    # temperatura média + chama média (intermitência 0,5) + Chamberlain
    ax = fig.add_subplot(gs[0, 0])
    _style(ax, "Temperatura média (máx. em y) e chama média (I = 0,5)")
    Tm = (les.avg_T / les.avg_n).max(1).values.float().cpu().numpy()
    Im = (les.avg_I / les.avg_n).max(1).values.float().cpu().numpy()
    m = ax.pcolormesh(les.xf, les.zf, Tm.T, cmap="inferno", vmin=290, vmax=1500, shading="flat", rasterized=True)
    ax.contour(les.xc, les.zc, Im.T, levels=[0.5], colors=["#4dd0e1"], linewidths=2)
    fr = frustum_outline_xz(ch, les.tip)
    ax.plot(fr[:, 0], fr[:, 1], "--", color=CHAM_C, lw=1.8, label="Chamberlain (1987)")
    ax.plot([], [], color="#4dd0e1", lw=2, label="LES: chama média (I = 0,5)")
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((-0.6, 0), 1.2, les.tip[2], color="#5c6773"))
    # janela em volta da chama (frustum + região quente da LES), com um pedaço da chaminé
    hot = Tm > 0.5 * (Tm.max() + 300.0)
    xs, zs = list(fr[:, 0]) + [0.0], list(fr[:, 1]) + [float(les.tip[2])]
    if hot.any():
        ii, kk = np.nonzero(hot)
        xs += [les.xc[ii].min(), les.xc[ii].max()]
        zs += [les.zc[kk].max()]
    zt = float(les.tip[2])
    ztop = max(zs) + 8.0
    x0, x1 = min(-15.0, min(xs) - 8.0), max(xs) + 8.0
    zbot = max(0.0, zt - 0.35 * (ztop - zt) - 8.0)
    span = max(x1 - x0, 1.25 * (ztop - zbot))
    x1 = x0 + span
    zbot = max(0.0, min(zbot, ztop - span / 1.25))
    ax.set_xlim(x0, x1); ax.set_ylim(zbot, ztop); ax.set_aspect("equal")
    ax.set_xlabel("x [m]"); ax.set_ylabel("z [m]")
    ax.legend(fontsize=8.5, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, loc="upper left")
    cb = fig.colorbar(m, ax=ax, fraction=0.04, pad=0.01)
    cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)

    # radiação média no solo e zonas do API 521
    ax = fig.add_subplot(gs[0, 1:])
    _style(ax, "Radiação média no solo e zonas do API 521")
    qm = les.q_grid(les.avg_q / les.avg_n) / 1e3
    from matplotlib import colors as mcolors
    from .render import qnorm
    mm = ax.pcolormesh(les.rec_x, les.rec_y, qm.T, cmap="magma", norm=qnorm(max(float(qm.max()), 0.5)),
                       shading="nearest", rasterized=True)
    levels = [lev for lev, _ in API_LEVELS if lev < qm.max()]
    cols = [c for lev, c in API_LEVELS if lev < qm.max()]
    if levels:
        ax.contour(les.rec_x, les.rec_y, qm.T, levels=levels, colors=cols, linewidths=2)
    ax.plot([0], [0], marker="^", color="white", ms=9, mec="black")
    ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    cb = fig.colorbar(mm, ax=ax, fraction=0.03, pad=0.01)
    cb.ax.tick_params(colors=MUTED, labelsize=8); cb.outline.set_edgecolor(GRID)
    zones = safety.zone_extents(qm, les.rec_x, les.rec_y)

    # validação
    ax = fig.add_subplot(gs[1, 0])
    _style(ax, "Validação (LES vs. modelos de referência)")
    rows = validation_rows(les, sc, refs)
    short = {"Comprimento da chama L [m]": "L chama [m]", "Inclinação da chama [°]": "Inclinação [°]",
             "Fluxo máximo no solo [kW/m²]": "q máx [kW/m²]", "L vs API 521 [m]": "L × API [m]",
             "L vs Delichatsios [m]": "L × Delichatsios", "L vs Heskestad [m]": "L × Heskestad"}
    names = [short.get(r["grandeza"], r["grandeza"]) for r in rows]
    # razão LES/referência (grandezas de escalas muito diferentes no mesmo eixo)
    y = np.arange(len(rows))
    ratio = np.array([100.0 * r["LES"] / r["referência"] if r["referência"] else np.nan for r in rows])
    ax.barh(y, ratio, 0.55, color=[LES_C if abs(v - 100) <= 25 else "#f2766b" for v in ratio], zorder=3)
    ax.axvline(100, color=CHAM_C, lw=1.6, ls="--", label="referência = 100%")
    ax.axvspan(75, 125, color=CHAM_C, alpha=0.08)
    xmax = max(160.0, np.nanmax(ratio) * 1.45)
    for i, r in enumerate(rows):
        ax.text(min(ratio[i], xmax) + 0.02 * xmax, i, f"{r['LES']:.3g} vs {r['referência']:.3g} ({r['erro_%']:+.0f}%)",
                va="center", color=FG, fontsize=8.5, zorder=4)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("LES / referência [%]  (faixa sombreada: ±25%)")
    ax.set_yticks(y); ax.set_yticklabels(names, color=FG, fontsize=9)
    ax.set_ylim(len(rows) - 0.4, -0.9)
    ax.legend(fontsize=8, facecolor=PANEL, edgecolor=GRID, labelcolor=FG, loc="upper right")
    ax.grid(color=GRID, lw=0.5, axis="x")

    # segurança no ponto mais exposto
    def text_box(cell, lines):
        ax = fig.add_subplot(cell)
        ax.set_facecolor(PANEL); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(GRID)
        ax.text(0.05, 0.95, "\n".join(lines), transform=ax.transAxes, va="top", color=FG, fontsize=9.5,
                family="monospace", linespacing=1.5)

    i, j = np.unravel_index(np.argmax(qm), qm.shape)
    xq, yq, q0 = les.rec_x[i], les.rec_y[j], qm[i, j]
    center = se.flame_center_chamberlain(ch, les.tip)
    r0 = float(np.linalg.norm(center - np.array([xq, yq, les.cfg.receiver_z])))
    d1 = safety.dose_escape(q0 * 1e3, r0, 5.0, 2.5)
    d2 = safety.dose_escape(q0 * 1e3, r0, 30.0, 2.5)
    text_box(gs[1, 1], [
        "PONTO MAIS EXPOSTO NO SOLO",
        f"x = {xq:.0f} m, y = {yq:.0f} m: q = {q0:.2f} kW/m²",
        f"T aço exposto (regime): {safety.steel_temperature(q0 * 1e3):.0f} °C",
        "",
        "Dose com fuga a 2,5 m/s:",
        f" reage em 5 s : {d1['dose_TDU']:5.0f} TDU",
        f"   1º grau {100 * d1['queimadura 1º grau (Tsao & Perry)']:5.1f}%"
        f"  2º grau {100 * d1['queimadura 2º grau (Tsao & Perry)']:5.2f}%",
        f" reage em 30 s: {d2['dose_TDU']:5.0f} TDU",
        f"   1º grau {100 * d2['queimadura 1º grau (Tsao & Perry)']:5.1f}%"
        f"  2º grau {100 * d2['queimadura 2º grau (Tsao & Perry)']:5.2f}%",
        f"   fatal (TNO) {100 * d2['fatalidade (TNO Green Book)']:5.2f}%",
    ])
    zl = ["ZONAS API 521 (LES, média)", "", "nível       área [m²]  alcance [m]"]
    zl += [f"{z['nivel_kW_m2']:5.2f} kW/m² {'≥' if z.get('truncado') else ' '}{z['area_m2']:8.0f}"
           f"   {'≥' if z.get('truncado') else ' '}{z['raio_max_m']:6.0f}" for z in zones]
    if any(z.get("truncado") for z in zones):
        zl += ["", "≥: a zona passa da grade de", "   receptores (limite inferior)"]
    text_box(gs[1, 2], zl)
    br_figure(fig).savefig(path, dpi=dpi, facecolor=BG)
    return fig, rows, zones


def compose_video(main_mp4: str, summary_png: str, out_mp4: str, seconds: float = 6.0, fps: int = 24) -> str:
    """Anexa a figura-resumo ao fim do vídeo da simulação (ffmpeg)."""
    ff = shutil.which("ffmpeg")
    if ff is None:
        raise RuntimeError("ffmpeg não encontrado")
    cmd = [ff, "-y", "-i", main_mp4, "-loop", "1", "-t", f"{seconds}", "-framerate", f"{fps}", "-i", summary_png,
           "-filter_complex",
           "[0:v]scale=1920:1080,setsar=1,fps=%d[a];[1:v]scale=1920:1080,setsar=1,fps=%d,format=yuv420p[b];"
           "[a][b]concat=n=2:v=1:a=0[v]" % (fps, fps),
           "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "slow", out_mp4]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_mp4
