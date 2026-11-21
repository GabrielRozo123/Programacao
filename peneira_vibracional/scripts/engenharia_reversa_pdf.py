"""Engenharia reversa das definições do Pulse VA a partir do PDF vetorial do relatório.

O relatório Pulse é gerado com gráficos vetoriais: as curvas de onda (sinal bruto, 220 amostras),
órbitas (sinal filtrado, 401 amostras), órbitas Z–X/Z–Y e espectros (FFT de 4096 pontos, sem
janela, dB de amplitude normalizado ao pico) estão gravadas como coordenadas. Este script:

1. extrai esses sinais e converte coordenadas → unidades físicas;
2. confere os sinais extraídos contra as tabelas do próprio relatório (G-Force X/Y, fase Y–X, RMS);
3. testa estimadores candidatos para "G-Force Z";
4. testa por Monte Carlo (arredondamentos + incerteza de fase) as hipóteses para Yaw e desvio Z.

Uso:
    python scripts/engenharia_reversa_pdf.py relatorio_pulse.pdf referencia.json --out pasta/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf
from scipy.optimize import minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pulseva import plots as pl  # noqa: E402

CORNERS = ("L1", "R1", "L4", "R4")
ROWS = {165: "4", 300: "3", 435: "2", 570: "1"}


# ----------------------------------------------------------------------------- extração
def _pts(d):
    p = []
    for it in d["items"]:
        if it[0] == "l":
            if not p:
                p.append((it[1].x, it[1].y))
            p.append((it[2].x, it[2].y))
    return np.array(p)


def _nseg(d):
    return sum(len(it) - 1 for it in d["items"])


def extract(pdf_path):
    doc = pymupdf.open(pdf_path)
    sensors = {}
    for page in doc:
        spans = [s["text"] for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
        title = next((t for t in spans if t.startswith("Orbit Report")), None)
        if not title:
            continue
        name = title.split()[-1]
        d = {}
        for dr in page.get_drawings():
            n, r = _nseg(dr), dr["rect"]
            if n == 440:
                ax = "X" if r.y0 < 520 else ("Y" if r.y0 < 620 else "Z")
                d["wave_" + ax] = _pts(dr)[1:]
            elif n == 2048:
                ax = "X" if r.y0 < 520 else ("Y" if r.y0 < 620 else "Z")
                d["spec_" + ax] = _pts(dr)
        w = {"X": (470, 10), "Y": (570, 10), "Z": (670, 20)}
        tops = {"X": 430, "Y": 530, "Z": 630}
        rec = {f"wave_{a}": (w[a][0] - d[f"wave_{a}"][:, 1]) / w[a][1] for a in "XYZ"}
        for a in "XYZ":
            p = d[f"spec_{a}"]
            _, idx = np.unique(np.round(p[:, 0], 3), return_index=True)
            p = p[idx]
            rec[f"spec_f"] = (p[:, 0] - 80) / 1.1008
            rec[f"spec_{a}"] = 10 ** (-(p[:, 1] - tops[a]) / 0.8 / 20)   # amplitude relativa ao pico
        sensors[name] = rec
    # páginas de resumo: órbitas filtradas X–Y e Z–X (mesma janela de 401 amostras)
    for page in doc:
        spans = " ".join(s["text"] for b in page.get_text("dict")["blocks"] for l in b.get("lines", [])
                         for s in l["spans"])
        kind = "XY" if "Orbit Summary X-Y" in spans else ("ZX" if "Orbit Summary Z-X" in spans else None)
        if not kind:
            continue
        frames = [dr["rect"] for dr in page.get_drawings() if dr["items"][0][0] == "re"
                  and abs(dr["rect"].width - 120) < .5 and abs(dr["rect"].height - 120) < .5]
        for dr in page.get_drawings():
            if _nseg(dr) != 800:
                continue
            c = dr["rect"]
            cx, cy = (c.x0 + c.x1) / 2, (c.y0 + c.y1) / 2
            fr = next(f for f in frames if f.x0 <= cx <= f.x1 and f.y0 <= cy <= f.y1)
            name = ("L" if fr.x0 < 300 else "R") + ROWS[int(round(fr.y0))]
            p = _pts(dr)
            h, v = (p[:, 0] - (fr.x0 + 60)) / 15, ((fr.y0 + 60) - p[:, 1]) / 15
            if kind == "XY":
                sensors[name]["orb_X"], sensors[name]["orb_Y"] = h, v
            else:
                sensors[name]["orb_Z"] = h
    return sensors


# ----------------------------------------------------------------------------- análise
def phasor(x, per):
    n = np.arange(len(x))
    w = 2 * np.pi / per
    a = np.column_stack([np.ones(len(x)), np.cos(w * n), np.sin(w * n)])
    c, *_ = np.linalg.lstsq(a, x, rcond=None)
    return c[1] - 1j * c[2]


def analyze(sensors, ref):
    rows = []
    for s, d in sensors.items():
        per = minimize_scalar(lambda p: -abs(phasor(d["orb_Y"], p)), bounds=(30, 200), method="bounded").x
        X, Y, Z = (phasor(d[f"orb_{a}"], per) for a in "XYZ")
        # Referencial da máquina. Nas páginas de resumo o Pulse já desenha o lado L espelhado
        # (eixos com rótulos invertidos); o X extraído do painel X–Y precisa de sinal trocado e o Z
        # do painel Z–X já está no referencial da máquina. Evidência: com esta convenção os pares
        # L2/R2 e L4/R4 têm Z em fase (translação lateral de corpo rígido); com a oposta ficariam
        # em oposição de fase.
        if s[0] == "L":
            X = -X
        f, ez = d["spec_f"], d["spec_Z"] ** 2
        msk = f > 1
        k = np.flatnonzero(msk)[np.argmax(d["spec_Z"][msk])]
        peak = {m: np.sqrt(ez[k - m:k + m + 1].sum() / ez[msk].sum()) for m in (0, 1, 2, 3)}
        r = ref["sensors"][s]
        rows.append(dict(sensor=s, per=per, X=X, Y=Y, Z=Z, fz_peak=f[k], peak=peak,
                         gz_rep=r["g"][2], rmsz_rep=r["rms"][2], gx_rep=r["g"][0], gy_rep=r["g"][1],
                         rms_wave_z=np.sqrt(2) * d["wave_Z"].std()))
    return rows


def montecarlo(ref, zph, n=20000, seed=1):
    rng = np.random.default_rng(seed)
    S, ph = ref["sensors"], ref["phase_yx"]
    res = {k: [] for k in ("yaw_X", "yaw_Z", "Z_sumY", "Z_main")}
    for _ in range(n):
        u = lambda: rng.uniform(-.005, .005)
        X = {c: S[c]["g"][0] + u() for c in CORNERS}
        Y = {c: (S[c]["g"][1] + u()) * np.exp(-1j * np.radians(ph[c] + rng.uniform(-.05, .05))) for c in CORNERS}
        Z = {c: (S[c]["g"][2] + u()) * np.exp(1j * np.radians(zph[c] + rng.normal(0, 15))) for c in CORNERS}
        sy = abs(sum(Y.values()))
        res["yaw_X"].append(abs(X["L1"] + X["L4"] - X["R1"] - X["R4"]) / sum(X.values()) * 100)
        res["yaw_Z"].append(abs(Z["L1"] + Z["R1"] - Z["L4"] - Z["R4"]) / sy * 100)
        res["Z_sumY"].append(abs(sum(Z.values())) / sy * 100)
        res["Z_main"].append(abs(sum(Z.values())) / 4 / ref["center"]["main_g"] * 100)
    return {k: np.array(v) for k, v in res.items()}


def figure(rows, mc, ref, path):
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.45})
    names = [r["sensor"] for r in rows]
    x = np.arange(len(rows))
    gz = np.array([r["gz_rep"] for r in rows])
    rms = np.array([r["rmsz_rep"] for r in rows])
    a1.errorbar(x, gz, yerr=0.005, fmt="_", ms=14, color=pl.C_INK, lw=1.2, label="Pulse: G-Force Z (±arred.)")
    a1.scatter(x - 0.18, [abs(r["Z"]) for r in rows], s=22, color=pl.C_MUTED, label="componente 1× (extraída)", zorder=3)
    a1.scatter(x + 0.18, rms * np.array([r["peak"][2] for r in rows]), s=22, color=pl.C_L,
               label="pico dominante ±2 bins (espectro)", zorder=3)
    a1.set_xticks(x)
    a1.set_xticklabels(names)
    a1.set_ylabel("G-Force Z (g)")
    a1.set_title("G-Force Z: o Pulse usa o pico dominante, não o 1×", loc="left")
    a1.legend(loc="upper left", fontsize=7)
    keys = [("yaw_X", "Yaw = X esq. × dir.", 2.3), ("yaw_Z", "Yaw = Z alim. × desc. / |ΣY|", 2.3),
            ("Z_main", "Z = |Z médio| / Main", 3.9), ("Z_sumY", "Z = |ΣZ| / |ΣY|", 3.9)]
    for i, (k, lab, t) in enumerate(keys):
        lo, med, hi = np.percentile(mc[k], [2.5, 50, 97.5])
        ok = lo <= t <= hi
        col = pl.C_L if ok else pl.C_MUTED
        a2.plot([lo, hi], [i, i], color=col, lw=3, solid_capstyle="round")
        a2.plot(med, i, "o", color=col, ms=5)
        a2.plot(t, i, marker="|", ms=16, mew=2, color=pl.C_INK)
        a2.text(5.3, i, ("✓ compatível" if ok else "✗ excluída"), va="center", fontsize=7.5,
                color=pl.C_INK)
    a2.set_yticks(range(len(keys)))
    a2.set_yticklabels([k[1] for k in keys], fontsize=7.5)
    a2.set_xlim(0, 6.6)
    a2.set_xlabel("Desvio (%) — barra: IC 95 % Monte Carlo · traço preto: valor do Pulse")
    a2.set_title("Hipóteses para Yaw e Z", loc="left")
    a2.grid(axis="y", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("ref")
    ap.add_argument("--out", default="saida")
    a = ap.parse_args()
    ref = json.loads(Path(a.ref).read_text(encoding="utf-8"))
    sensors = extract(a.pdf)
    rows = analyze(sensors, ref)
    fs = 800.0
    print("Sensor | período (amostras) → f | X 1× / Pulse | Y 1× / Pulse | fase Y–X | Z 1× | G_Z Pulse | "
          "pico±0/±1/±2 bins → G_Z")
    for r in rows:
        ph = np.degrees(np.angle(r["X"]) - np.angle(r["Y"]))
        est = " / ".join(f"{r['rmsz_rep'] * r['peak'][m]:.3f}" for m in (0, 1, 2))
        print(f"{r['sensor']} | {r['per']:.2f} → {fs / r['per']:.2f} Hz | {abs(r['X']):.3f} / {r['gx_rep']:.2f} | "
              f"{abs(r['Y']):.3f} / {r['gy_rep']:.2f} | {ph:+.1f}° | {abs(r['Z']):.3f} | {r['gz_rep']:.2f} | {est} "
              f"(pico em {r['fz_peak']:.1f} Hz)")
    zph = {r["sensor"]: float(np.degrees(np.angle(r["Z"] / r["X"]))) for r in rows}
    mc = montecarlo(ref, zph)
    for k, v in mc.items():
        lo, med, hi = np.percentile(v, [2.5, 50, 97.5])
        print(f"{k:7s}: mediana {med:.2f} %  IC95% [{lo:.2f}, {hi:.2f}]")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    figure(rows, mc, ref, out / "engenharia_reversa_pulse.png")
    print("figura:", out / "engenharia_reversa_pulse.png")


if __name__ == "__main__":
    main()
