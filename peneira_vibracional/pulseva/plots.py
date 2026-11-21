"""Figuras de engenharia (matplotlib) no estilo de relatório técnico.

Codificação visual fixa em todas as figuras:
* cor = lado da máquina (L = azul, R = laranja); referências/contexto em cinza;
* linhas finas (≈1,2 pt), grade discreta, rótulos diretos nas séries de interesse;
* cores de status (ok/atenção/crítico) reservadas para limites de aceitação,
  sempre acompanhadas de símbolo + texto.
"""
from __future__ import annotations

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Polygon

from .metrics import CORNERS, PULSE_LIMITS, DEVIATION_STATUS, stroke_mm
from .tracking import amplitude_spectrum, order_spectrum

# ----------------------------------------------------------------------------- estilo
C_L = "#2a78d6"        # lado esquerdo
C_R = "#eb6834"        # lado direito
C_INK = "#0b0b0b"
C_INK2 = "#52514e"
C_MUTED = "#9a9892"
C_GRID = "#e4e3df"
C_SURF = "#fcfcfb"
C_OK, C_WARN, C_CRIT = "#0ca30c", "#fab219", "#d03b3b"
SIDE_COLOR = {"L": C_L, "R": C_R}


def use_style():
    matplotlib.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": C_INK2, "axes.linewidth": 0.6, "axes.labelcolor": C_INK,
        "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.labelsize": 8,
        "axes.grid": True, "grid.color": C_GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "xtick.color": C_INK2, "ytick.color": C_INK2, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "legend.frameon": False, "font.size": 8,
        "font.family": "DejaVu Sans", "lines.linewidth": 1.2, "savefig.dpi": 200,
        "savefig.bbox": "tight", "axes.spines.top": False, "axes.spines.right": False,
    })


use_style()


def _ac(an, name):
    """Sinal AC no referencial da máquina (N×3)."""
    from .metrics import SIDE_SIGN
    raw = an.record.sensors[name]
    return (raw - raw.mean(axis=0)) * SIDE_SIGN[name[0]]


def _ellipse_xy(P, n=361):
    th = np.linspace(0, 2 * np.pi, n)
    return (P[0] * np.exp(1j * th)).real, (P[1] * np.exp(1j * th)).real


def _rev_slice(s, k0=10, nrev=5):
    tr = s.track
    th = tr.theta
    a = np.searchsorted(th, th[tr.i0] + 2 * np.pi * k0)
    b = np.searchsorted(th, th[tr.i0] + 2 * np.pi * (k0 + nrev))
    return slice(a, b)


# ----------------------------------------------------------------------------- órbitas
def plot_orbit(ax, an, name, nrev=5, lim=4.0, show_text=True):
    s = an.sensors[name]
    a = _ac(an, name)
    sl = _rev_slice(s, nrev=nrev)
    ax.plot(a[sl, 0], a[sl, 1], color=C_MUTED, lw=0.6, alpha=0.9, label="medido (5 rotações)")
    ex, ey = _ellipse_xy(s.P[0])
    ax.plot(ex, ey, color=SIDE_COLOR[s.side], lw=1.6, label="componente 1×")
    th = np.radians(s.angle)
    ax.plot([-s.main_g * np.cos(th), s.main_g * np.cos(th)],
            [-s.main_g * np.sin(th), s.main_g * np.sin(th)], color=C_INK, lw=0.7, ls=(0, (3, 2)))
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xticks(np.arange(-lim, lim + 1, 1))
    ax.set_yticks(np.arange(-lim, lim + 1, 1))
    ax.axhline(0, color=C_INK2, lw=0.5)
    ax.axvline(0, color=C_INK2, lw=0.5)
    if s.side == "L":
        ax.invert_xaxis()   # vista pelo lado externo esquerdo (igual ao Pulse)
    if show_text:
        txt = (f"Main {s.main_g:.2f} g, {s.stroke_main:.1f} mm\n"
               f"X {s.g[0]:.2f}  Y {s.g[1]:.2f}  Z {s.g_report[2]:.2f} g\n"
               f"ângulo {s.angle:.1f}°, fase {s.phase_yx:.1f}°")
        ax.text(0.02, 0.98, txt, transform=ax.transAxes, va="top", ha="left", fontsize=6.3,
                color=C_INK, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
    ax.set_title(name, loc="left", color=SIDE_COLOR[s.side])
    return ax


def fig_orbit_summary(an):
    fig, axes = plt.subplots(4, 2, figsize=(7.2, 13.2))
    for i, (l, r) in enumerate(zip(("L4", "L3", "L2", "L1"), ("R4", "R3", "R2", "R1"))):
        for ax, n in ((axes[i, 0], l), (axes[i, 1], r)):
            if n in an.sensors:
                plot_orbit(ax, an, n)
            ax.set_xlabel("X (g)" + ("  ← eixo invertido: vista pelo lado esquerdo" if n[0] == "L" else ""),
                          fontsize=6.5)
            ax.set_ylabel("Y (g)")
    h, lab = axes[0, 1].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0))
    fig.suptitle(f"Órbitas X–Y por sensor ({an.rpm:.0f} RPM, {an.f_mean:.2f} Hz)",
                 y=1.015, fontsize=11, fontweight="bold")
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------------- relatório de um sensor
def fig_sensor_report(an, name, fmax=200.0):
    s = an.sensors[name]
    a = _ac(an, name)
    fs = an.record.fs
    fig = plt.figure(figsize=(8.0, 9.6))
    gs = fig.add_gridspec(4, 2, height_ratios=[1.35, 1, 1, 1], hspace=0.55, wspace=0.28,
                          top=0.93, bottom=0.06, left=0.1, right=0.97)
    ax0 = fig.add_subplot(gs[0, 0])
    plot_orbit(ax0, an, name, show_text=False)
    ax0.set_xlabel("X (g)")
    ax0.set_ylabel("Y (g)")
    ax0.set_title(f"Órbita {name}", loc="left")
    # tabela
    axt = fig.add_subplot(gs[0, 1])
    axt.axis("off")
    rows = [["Main G", f"{s.main_g:.2f} g"], ["Stroke", f"{s.stroke_main:.1f} mm"],
            ["Freq.", f"{s.f_mean:.2f} Hz ({60 * s.f_mean:.0f} RPM)"], ["Force angle", f"{s.angle:.1f}°"],
            ["Fase Y–X", f"{s.phase_yx:.1f}° ({s.rotation_sense})"]]
    t1 = axt.table(cellText=rows, colWidths=[0.42, 0.58], loc="upper center", cellLoc="left",
                   bbox=[0.0, 0.52, 1.0, 0.46])
    gr, sr = s.g_report, s.stroke_report
    rows2 = [["Eixo", "G-Force (g)", "Stroke (mm)", "RMS (g)"]] + [
        [ax, f"{gr[i]:.2f}", f"{sr[i]:.1f}", f"{s.rms_pk[i]:.2f}"] for i, ax in enumerate("XYZ")]
    t2 = axt.table(cellText=rows2, loc="lower center", cellLoc="center", bbox=[0.0, 0.0, 1.0, 0.42])
    for t in (t1, t2):
        t.auto_set_font_size(False)
        t.set_fontsize(7.5)
        for (r, c), cell in t.get_celld().items():
            cell.set_edgecolor(C_GRID)
            if (t is t2 and r == 0) or (t is t1 and c == 0):
                cell.set_text_props(fontweight="bold", color=C_INK)
                cell.set_facecolor("#f2f1ee")
    axt.text(0.0, 0.47, f"Kurtosis Z {s.z_kurtosis:.2f}; pico dominante de Z em {s.f_peak[2]:.1f} Hz "
             f"(componente 1×: {s.g[2]:.3f} g, {s.stroke[2]:.2f} mm)", fontsize=6.6, transform=axt.transAxes, color=C_INK2)
    # espectros
    f, amp = amplitude_spectrum(a, fs)
    sl = _rev_slice(s, k0=10, nrev=3)
    t = (np.arange(sl.stop - sl.start)) / fs * 1e3
    th = s.track.theta[sl]
    for i, axn in enumerate("XYZ"):
        axs = fig.add_subplot(gs[i + 1, 0])
        m = (f > 0.5) & (f <= fmax)
        axs.semilogy(f[m], amp[m, i], color=SIDE_COLOR[s.side], lw=0.7)
        axs.set_ylim(1e-4, 10)
        axs.set_xlim(0, fmax)
        h = s.f_mean * np.arange(1, int(fmax / s.f_mean) + 1)
        axs.set_xticks(h[::2])
        axs.set_xticklabels([f"{v:.1f}" for v in h[::2]], fontsize=6)
        axs.set_ylabel(f"{axn} (g pico)")
        if i == 0:
            axs.set_title("Espectro de amplitude (Hann)", loc="left", fontsize=8)
        if i == 2:
            axs.set_xlabel("Frequência (Hz)")
        # forma de onda
        axw = fig.add_subplot(gs[i + 1, 1])
        axw.plot(t, a[sl, i], color=C_MUTED, lw=0.8, label="medido")
        rec = (s.P[0, i] * np.exp(1j * th)).real
        axw.plot(t, rec, color=SIDE_COLOR[s.side], lw=1.2, label="1×")
        lim = 4 if i < 2 else 2
        axw.set_ylim(-lim, lim)
        axw.set_ylabel(f"{axn} (g)")
        if i == 0:
            axw.set_title("Forma de onda (3 rotações)", loc="left", fontsize=8)
            axw.legend(loc="upper right", ncol=2)
        if i == 2:
            axw.set_xlabel("Tempo (ms)")
    fig.suptitle(f"Relatório do sensor {name}", x=0.02, ha="left", y=0.995, fontsize=12, fontweight="bold")
    return fig


# ----------------------------------------------------------------------------- relatório de fase
def _status(value, limit):
    if value <= limit:
        return "✓ OK", C_OK
    return "✗ acima", C_CRIT


def fig_phase_report(an, ref=None):
    fig = plt.figure(figsize=(8.0, 9.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.78, 1.05, 0.8], hspace=0.38, wspace=0.3,
                          top=0.94, bottom=0.06, left=0.1, right=0.97)

    # (a) esquema lateral com órbitas de deslocamento em escala
    axm = fig.add_subplot(gs[0, :])
    _machine_schematic(axm, an)

    # (b) ondas Y sincronizadas (fase de X = 0), uma rotação
    axw = fig.add_subplot(gs[1, 0])
    ang = np.linspace(0, 360, 361)
    th = np.radians(ang)
    for n, s in an.sensors.items():
        y = (s.Psync[1] * np.exp(1j * th)).real
        if n in CORNERS:
            axw.plot(ang, y, color=SIDE_COLOR[s.side], lw=1.4, ls="-" if n.endswith("1") else (0, (4, 2)))
        else:
            axw.plot(ang, y, color=C_MUTED, lw=0.7)
    for n, lab, a_pt, xy_txt in (("L4", "descarga (L4, R4)", 40, (70, 3.45)),
                                 ("L1", "alimentação (L1, R1)", 345, (205, 3.45))):
        s = an.sensors[n]
        yv = (s.Psync[1] * np.exp(1j * np.radians(a_pt))).real
        axw.annotate(lab, (a_pt, yv), xytext=xy_txt, fontsize=6.5, color=C_INK,
                     arrowprops=dict(arrowstyle="-", color=C_INK2, lw=0.5))
    axw.set_xlim(0, 360)
    axw.set_ylim(-4, 4)
    axw.set_xticks(range(0, 361, 90))
    axw.set_xlabel("Ângulo de rotação (°), referência no eixo X")
    axw.set_ylabel("Y 1× (g)")
    axw.set_title("Ondas Y sincronizadas pelo eixo X", loc="left")
    axw.text(0.99, 0.02, "azul: lado L; laranja: lado R; cinza: posições 2 e 3\nlinha contínua: posição 1; tracejada: posição 4",
             transform=axw.transAxes, ha="right", va="bottom", fontsize=6, color=C_INK2)

    # (c) órbita do centro
    axc = fig.add_subplot(gs[1, 1])
    for n in CORNERS:
        ex, ey = _ellipse_xy(an.sensors[n].Psync)
        axc.plot(ex, ey, color=SIDE_COLOR[n[0]], lw=0.7, alpha=0.55)
    c = an.center
    ex, ey = _ellipse_xy(c["phasors"])
    axc.plot(ex, ey, color=C_INK, lw=1.8)
    t = np.radians(c["angle"])
    axc.plot([-c["main_g"] * np.cos(t), c["main_g"] * np.cos(t)], [-c["main_g"] * np.sin(t), c["main_g"] * np.sin(t)],
             color=C_INK, lw=0.7, ls=(0, (3, 2)))
    axc.set_xlim(-4, 4)
    axc.set_ylim(-4, 4)
    axc.set_aspect("equal")
    axc.set_xlabel("X (g)")
    axc.set_ylabel("Y (g)")
    axc.set_title("Força no centro (média dos 4 cantos)", loc="left")
    axc.text(0.02, 0.98, f"Main {c['main_g']:.2f} g, {c['stroke_main']:.1f} mm\n"
             f"X {c['g'][0]:.2f} g ({c['stroke'][0]:.1f} mm)\nY {c['g'][1]:.2f} g ({c['stroke'][1]:.1f} mm)\n"
             f"ângulo {c['angle']:.1f}°, fase {c['phase']:.1f}°", transform=axc.transAxes, va="top",
             fontsize=6.3, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))

    # (d) desvios vs limites
    axd = fig.add_subplot(gs[2, :])
    _deviation_bars(axd, an, ref)
    fig.suptitle("Relatório de fase e corpo rígido", x=0.02, ha="left", y=0.995, fontsize=12, fontweight="bold")
    return fig


def _deviation_bars(ax, an, ref=None):
    keys = ["pitch", "roll", "yaw", "twist", "z"]
    labels = {"pitch": "Pitch", "roll": "Roll", "yaw": "Yaw", "twist": "Twist", "z": "Z lateral"}
    y = np.arange(len(keys))[::-1]
    h = 0.34 if ref else 0.5
    for i, k in enumerate(keys):
        v = an.deviations[k]
        lim = PULSE_LIMITS[k]
        ax.barh(y[i] + (h / 2 if ref else 0), v / lim * 100, height=h, color=C_L, lw=0)
        word = lambda val: "atende" if val <= lim else "não atende"
        txt = f"{v:.1f} % ({word(v)}; limite {lim:.0f} %)"
        if ref:
            vr = ref["deviations"][k]
            ax.barh(y[i] - h / 2, vr / lim * 100, height=h, color=C_MUTED, lw=0)
            txt += f"; Pulse {vr:.1f} %"
        alt = getattr(an, "deviations_alt", {}).get(k)
        if alt is not None and abs(alt - v) > 0.05:
            ax.plot(alt / lim * 100, y[i] + (h / 2 if ref else 0), marker="D", ms=4.5, color=C_CRIT, zorder=4)
            txt += f"\n◆ sem o canal defeituoso: {alt:.1f} % ({word(alt)})"
        ax.text(148, y[i], txt, va="center", fontsize=6.8, color=C_INK)
    ax.axvline(100, color=C_INK, lw=1.0)
    ax.text(101, y[-1] - 0.55, "limite", ha="left", va="center", fontsize=6.3, color=C_INK)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[k] for k in keys])
    ax.set_xlim(0, 360)
    ax.set_xticks([0, 25, 50, 75, 100, 125])
    ax.set_xlabel("Desvio em % do limite de aceitação do Pulse (100 = limite)")
    ax.grid(axis="y", visible=False)
    ttl = "Desvios de corpo rígido" + (" (azul: Python; cinza: relatório Pulse)" if ref else "")
    ax.set_title(ttl, loc="left")


def _machine_schematic(ax, an, scale=2.5):
    """Vista lateral esquemática (referencial da máquina, ambos os lados vistos pelo
    lado direito) com a órbita de deslocamento 1× de cada sensor ampliada ``scale`` vezes."""
    L, H, gap = 200.0, 38.0, 10.0
    xs = {1: 22.0, 2: 74.0, 3: 126.0, 4: 178.0}
    ax.set_title(f"Órbitas de deslocamento 1× ampliadas {scale:.1f} vezes (posições esquemáticas, "
                 "ambos os lados no referencial da máquina)", loc="left", fontsize=8.5)
    for side, y0 in (("L", H + gap), ("R", 0.0)):
        ax.add_patch(Polygon([[0, y0], [L, y0], [L, y0 + H], [0, y0 + H]], closed=True, fc="#f4f3f0",
                             ec=C_MUTED, lw=0.6))
        ax.text(-3, y0 + H / 2, "Lado\nesquerdo" if side == "L" else "Lado\ndireito", va="center",
                ha="right", fontsize=7, color=SIDE_COLOR[side], fontweight="bold")
        for pos, x0 in xs.items():
            n = f"{side}{pos}"
            if n not in an.sensors:
                continue
            s = an.sensors[n]
            P = s.Psync[:2] * stroke_mm(1.0, s.f_mean) / 2   # amplitude de deslocamento (mm)
            ex, ey = _ellipse_xy(P)
            yc = y0 + H * 0.5
            ax.plot(x0 + ex * scale, yc + ey * scale, color=SIDE_COLOR[side], lw=1.4)
            ax.plot(x0, yc, "o", ms=2.2, color=C_INK)
            ax.text(x0 - 4, yc + 9, n, fontsize=7.5, fontweight="bold", color=C_INK, ha="right")
            ax.text(x0 + 3, y0 + 3.0, f"{s.stroke_main:.1f} mm\n{s.angle:.0f}°", ha="left", fontsize=6.2,
                    color=C_INK)
    ax.add_patch(FancyArrowPatch((L * 0.42, -6), (L * 0.58, -6), arrowstyle="-|>", mutation_scale=8,
                                 color=C_INK2, lw=0.8))
    ax.text(L * 0.5, -10.5, "sentido do fluxo (+X)", ha="center", fontsize=6.3, color=C_INK2)
    ax.text(0, -8, "alimentação", fontsize=6.5, color=C_INK2)
    ax.text(L, -8, "descarga", fontsize=6.5, color=C_INK2, ha="right")
    ax.set_xlim(-30, L + 2)
    ax.set_ylim(-13, 2 * H + gap + 2)
    ax.set_aspect("equal")
    ax.axis("off")


# ----------------------------------------------------------------------------- rotação e estabilidade
def fig_speed(an):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.0, 6.4), gridspec_kw={"hspace": 0.45})
    t = an.record.time()
    sp = an.speed
    i0 = int(round(sp["profile_t"][0] * an.record.fs))
    i1 = i0 + sp["profile_t"].size
    shifted = sorted(an.lags, key=lambda k: abs(an.lags[k][0]), reverse=True)[:2]
    for n, s in an.sensors.items():
        if n in shifted:
            continue
        a1.plot(t[i0:i1], 60 * s.track.f_inst[i0:i1], color=C_MUTED, lw=0.8)
    styles = ["-", (0, (4, 2))]
    for k, n in enumerate(shifted):
        s = an.sensors[n]
        a1.plot(t[i0:i1], 60 * s.track.f_inst[i0:i1], color=SIDE_COLOR[n[0]], lw=1.3, ls=styles[k],
                label=f"{n} (defasagem {an.lags[n][0] * 1e3:+.0f} ms)")
    a1.axhline(an.rpm, color=C_INK, lw=0.7, ls=(0, (3, 2)))
    a1.text(t[i0], an.rpm, f" média {an.rpm:.1f} RPM", va="bottom", fontsize=6.5, color=C_INK)
    a1.set_xlabel("Tempo (s), relógio de cada sensor")
    a1.set_ylabel("Rotação (RPM)")
    a1.set_title(f"Rotação instantânea (variação pico a pico de {sp['var_pp_pct']:.1f} %; "
                 f"(cinza: demais sensores)", loc="left")
    a1.legend(loc="lower left")
    # Main G por rotação nos cantos
    for n in ("L1", "L4", "R1", "R4"):
        s = an.sensors[n]
        from .metrics import ellipse_from_phasors
        mg = np.array([ellipse_from_phasors(r[0], r[1])["main"] for r in s.per_rev])
        a2.plot(np.arange(1, mg.size + 1), mg, color=SIDE_COLOR[n[0]], lw=1.1,
                ls="-" if n.endswith("1") else (0, (4, 2)), label=f"{n}  (σ = {mg.std(ddof=1):.3f} g)")
    a2.set_xlabel("Rotação nº")
    a2.set_ylabel("Main G por rotação (g)")
    a2.set_title("Estabilidade ciclo a ciclo nos cantos (contínua = alimentação, tracejada = descarga)",
                 loc="left")
    a2.legend(ncol=2, loc="lower right")
    return fig


# ----------------------------------------------------------------------------- método
def fig_method(an):
    """Por que rastreamento de ordem: amplitude Y por método."""
    fs = an.record.fs
    names = list(an.sensors)
    fixed, tracked, ref = [], [], []
    for n in names:
        s = an.sensors[n]
        a = _ac(an, n)[:, 1]
        sl = s.track.window
        tt = np.arange(a.size)[sl] / fs
        A = np.column_stack([np.ones_like(tt), np.cos(2 * np.pi * s.f_mean * tt), np.sin(2 * np.pi * s.f_mean * tt)])
        c, *_ = np.linalg.lstsq(A, a[sl], rcond=None)
        fixed.append(np.hypot(c[1], c[2]))
        tracked.append(s.g[1])
        ref.append(s.rms_pk[1])
    fixed, tracked, ref = map(np.array, (fixed, tracked, ref))
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    x = np.arange(len(names))
    ax.bar(x - 0.19, fixed, 0.36, color=C_MUTED, label="ajuste senoidal com frequência fixa")
    ax.bar(x + 0.19, tracked, 0.36, color=C_L, label="rastreamento de ordem (este trabalho)")
    ax.scatter(x, ref, marker="_", s=260, color=C_INK, zorder=3, label="√2 × RMS do sinal (limite superior)")
    for i in range(len(names)):
        ax.text(x[i] - 0.19, fixed[i] + 0.05, f"{(fixed[i] / ref[i] - 1) * 100:+.0f}%", ha="center", fontsize=6,
                color=C_INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("Amplitude Y 1× (g)")
    ax.set_ylim(0, 3.8)
    ax.legend(loc="upper left", ncol=3, bbox_to_anchor=(0, 1.16))
    ax.grid(axis="x", visible=False)
    return fig, {"fixed": fixed, "tracked": tracked, "rms": ref, "names": names}


# ----------------------------------------------------------------------------- validação
def fig_validation(cmp, an):
    fig, axes = plt.subplots(1, 3, figsize=(8.0, 3.2), gridspec_kw={"wspace": 0.42})
    panels = [("Stroke", "mm", "Stroke (mm)", (5.5, 13)), ("G-Force", "g", "G-Force @ f_ref (g)", (1.5, 3.8)),
              ("Ângulo", "°", "Force angle (°)", (35, 62))]
    for ax, (grp, unit, lab, lims) in zip(axes, panels):
        d = cmp[cmp["Grupo"] == grp]
        for side in "LR":
            m = d["Item"].str.startswith(side)
            ax.scatter(d.loc[m, "Pulse"], d.loc[m, "Python @ f_ref"], s=14, color=SIDE_COLOR[side],
                       label=f"lado {side}", zorder=3, edgecolor="white", linewidth=0.4)
        lo, hi = lims
        xx = np.linspace(lo, hi, 2)
        ax.plot(xx, xx, color=C_INK, lw=0.8)
        tol = 0.03 if unit != "°" else None
        if tol:
            ax.fill_between(xx, xx * (1 - tol), xx * (1 + tol), color=C_GRID, alpha=0.8, lw=0, zorder=0)
        else:
            ax.fill_between(xx, xx - 2, xx + 2, color=C_GRID, alpha=0.8, lw=0, zorder=0)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal")
        ax.set_xlabel(f"Relatório Pulse ({unit})")
        ax.set_ylabel(f"Python ({unit})")
        err = d["Δ (%)"].abs() if unit != "°" else d["Δ"].abs()
        ax.set_title(lab, loc="left", fontsize=8.5)
        ax.text(0.04, 0.96, f"faixa: ±{'3 %' if tol else '2°'}\nerro médio: "
                f"{err.mean():.1f}{' %' if unit != '°' else '°'}\nmáx.: {err.max():.1f}{' %' if unit != '°' else '°'}",
                transform=ax.transAxes, va="top", fontsize=6.3)
    axes[0].legend(loc="lower right")
    return fig


# ----------------------------------------------------------------------------- integridade e Z
def fig_integrity(an):
    names = list(an.sensors)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.3), gridspec_kw={"wspace": 0.3})
    mags = np.array([np.linalg.norm(an.record.sensors[n].mean(axis=0)) for n in names])
    x = np.arange(len(names))
    for i, n in enumerate(names):
        bad = n in an.excluded
        v = min(mags[i], 1.15)
        a1.bar(i, v, 0.6, color=C_CRIT if bad else SIDE_COLOR[n[0]], hatch="//" if bad else None,
               edgecolor="white", lw=0)
        if bad:
            a1.text(i + 0.4, 1.1, f"✗ {n}: |DC| = {mags[i]:.1f} g\n(eixo Z travado,\nbarra cortada)", ha="left",
                    va="center", fontsize=6.3, color=C_CRIT, fontweight="bold",
                    bbox=dict(fc="white", ec="none", pad=1.0))
        else:
            a1.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=6, color=C_INK)
    a1.axhline(1.0, color=C_INK, lw=0.9)
    a1.text(len(names) - 0.5, 1.005, "1 g esperado", ha="right", va="bottom", fontsize=6.5)
    a1.set_ylim(0.8, 1.15)
    a1.set_xticks(x)
    a1.set_xticklabels(names)
    a1.set_ylabel("|vetor DC| (g)")
    a1.set_title("Gravidade medida (calibração estática)", loc="left")
    a1.grid(axis="x", visible=False)
    tilts = [an.sensors[n].tilt_deg for n in names]
    a2.bar(x, tilts, 0.6, color=[SIDE_COLOR[n[0]] for n in names], lw=0)
    for i, v in enumerate(tilts):
        a2.text(i, v + (0.25 if v >= 0 else -0.25), f"{v:+.1f}°", ha="center", va="bottom" if v >= 0 else "top",
                fontsize=6)
    a2.axhline(0, color=C_INK, lw=0.7)
    a2.set_ylim(min(-2.5, min(tilts) - 1.5), max(tilts) + 1.5)
    a2.set_xticks(x)
    a2.set_xticklabels(names)
    a2.set_ylabel("Inclinação estática do eixo X (°)")
    a2.set_title("Montagem dos sensores (pela gravidade)", loc="left")
    a2.grid(axis="x", visible=False)
    return fig


def fig_z_spectra(an, fmax=200.0):
    fig, axes = plt.subplots(4, 2, figsize=(8.0, 7.4), sharex=True, sharey=True,
                             gridspec_kw={"hspace": 0.35, "wspace": 0.12})
    for i, (l, r) in enumerate(zip(("L4", "L3", "L2", "L1"), ("R4", "R3", "R2", "R1"))):
        for ax, n in ((axes[i, 0], l), (axes[i, 1], r)):
            s = an.sensors[n]
            f, amp = amplitude_spectrum(_ac(an, n)[:, 2], an.record.fs)
            m = (f > 0.5) & (f <= fmax)
            bad = n in an.excluded
            ax.semilogy(f[m], amp[m, 0], color=C_CRIT if bad else SIDE_COLOR[n[0]], lw=0.6)
            for h in range(1, int(fmax / s.f_mean) + 1):
                ax.axvline(h * s.f_mean, color=C_GRID, lw=0.6, zorder=0)
            ax.set_ylim(1e-4, 1)
            k = np.argmin(np.abs(f - s.f_peak[2]))
            ax.plot(f[k], amp[k, 0], "o", ms=4, color=C_INK, zorder=4)
            lab = (f"{n}-Z: G-Force {s.g_pulse[2]:.3f} g em {s.f_peak[2]:.1f} Hz; 1× {s.g[2]:.3f} g; "
                   f"RMS {s.rms_pk[2]:.2f} g")
            if bad:
                lab = f"{n}-Z  ✗ canal travado em {an.record.sensors[n][:, 2].mean():.1f} g"
            ax.set_title(lab, loc="left", fontsize=7, fontweight="normal",
                         color=C_CRIT if bad else C_INK)
    for ax in axes[-1]:
        ax.set_xlabel("Frequência (Hz)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Z (g pico)")
    fig.suptitle("Eixo lateral Z: conteúdo de banda larga e componente 1× pequena", x=0.02, ha="left", fontsize=11,
                 fontweight="bold", y=0.995)
    return fig


def fig_order_spectrum(an, max_order=8.0):
    """Espectro de ordens médio dos 8 sensores, que evidencia as ordens fracionárias 0,5× e 1,5×."""
    from .metrics import KV_ONE_PERIOD
    accX, accY = [], []
    for n, s in an.sensors.items():
        o, amp = order_spectrum(_ac(an, n)[:, :2], s.track, n_per_rev=64)
        accX.append(np.interp(np.linspace(0, max_order, 2001), o, amp[:, 0]))
        accY.append(np.interp(np.linspace(0, max_order, 2001), o, amp[:, 1]))
    oo = np.linspace(0, max_order, 2001)
    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    ax.semilogy(oo, np.mean(accX, axis=0), color=C_MUTED, lw=0.8, label="X (média dos 8 sensores)")
    ax.semilogy(oo, np.mean(accY, axis=0), color=C_INK, lw=1.0, label="Y (média dos 8 sensores)")
    for k in (0.5, 1.5, 2.5):
        ax.axvline(k, color=C_CRIT, lw=0.7, ls=(0, (2, 2)))
    sub = np.array([s.sub[:, 1] for s in an.sensors.values()])
    ax.text(0.55, 0.3, f"0,5×\n{sub[:, 0].mean():.2f} g", color=C_CRIT, fontsize=6.5)
    ax.text(1.55, 0.3, f"1,5×\n{sub[:, 1].mean():.2f} g", color=C_CRIT, fontsize=6.5)
    ax.set_xlim(0, max_order)
    ax.set_ylim(1e-4, 10)
    ax.set_xticks(np.arange(0, max_order + 0.01, 0.5))
    ax.set_xticklabels([f"{v:g}×" if v % 1 == 0 else "" for v in np.arange(0, max_order + 0.01, 0.5)])
    ax.set_xlabel("Ordem (múltiplos da rotação)")
    ax.set_ylabel("Amplitude (g pico)")
    kv = an.throw["kv_horizontal_ref"]
    ax.set_title(f"Espectro de ordens médio dos 8 sensores (linhas tracejadas: ordens fracionárias; "
                 f"K_v = {kv:.2f})", loc="left", fontsize=8.5)
    ax.legend(loc="upper right")
    return fig


#: Em modo publicação (relatório LaTeX) os títulos gerais das figuras são omitidos (a legenda do
#: documento cumpre esse papel) e todos os números usam vírgula decimal.
PUBLICATION = False


def _localize(fig):
    """Vírgula decimal em textos, legendas e marcas dos eixos."""
    import re
    from matplotlib.text import Text
    from matplotlib.ticker import FixedFormatter, FuncFormatter, ScalarFormatter
    dec = re.compile(r"(?<=\d)\.(?=\d)")
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            fm = axis.get_major_formatter()
            if isinstance(fm, FixedFormatter):
                fm.seq = [dec.sub(",", str(t)) for t in fm.seq]
            elif isinstance(fm, ScalarFormatter):
                axis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:g}".replace(".", ",").replace("-", "−")))
    for t in fig.findobj(Text):
        txt = t.get_text()
        if txt and "$" not in txt:
            t.set_text(dec.sub(",", txt))


def save(fig, path):
    if PUBLICATION and getattr(fig, "_suptitle", None) is not None:
        fig._suptitle.set_text("")
    _localize(fig)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path
