"""analisa_etapaA.py: etapa A (RANS, N2), com FFT da pluma, retenção média e perfis em y = 750 mm × Darmana (2007)."""
import csv, json
from pathlib import Path
import numpy as np

AQUI = Path(__file__).parent
R = AQUI / "resultados_cfd" / "etapaA_RANS_N2"
L = AQUI / "dados_literatura"


def serie(nome):
    with open(R / nome) as f:
        rows = list(csv.reader(f))[1:]
    a = np.array([[float(x) for x in r[:2]] for r in rows if r])
    return a[:, 0], a[:, 1]


def lit(nome):
    with open(L / nome) as f:
        rows = list(csv.reader(f))[1:]
    return np.array([[float(x) for x in r] for r in rows]).T


def main():
    t, v = serie("VG_PIV.csv")
    th, h = serie("HOLDUP.csv")
    m = th >= 20
    hold = dict(media=float(h[m].mean()), desvio=float(h[m].std()), min=float(h[m].min()), max=float(h[m].max()))
    # FFT em malha uniforme (20–80 s)
    dt = 0.01
    tu = np.arange(20, t.max(), dt)
    vu = np.interp(tu, t, v) - np.interp(tu, t, v).mean()
    win = np.hanning(len(vu))
    A = np.abs(np.fft.rfft(vu * win)); f = np.fft.rfftfreq(len(vu), dt)
    i = np.argmax(A[1:]) + 1
    # refinamento parabólico do pico
    y0, y1, y2 = A[i - 1], A[i], A[i + 1]
    fpk = f[i] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (f[1] - f[0])
    # períodos por cruzamentos ascendentes da média
    cz = tu[1:][(vu[:-1] < 0) & (vu[1:] >= 0)]
    per = np.diff(cz)
    with open(R / "LINHA_750.csv") as fh:
        rows = list(csv.reader(fh))[1:]
    P = np.array([[float(x) for x in r] for r in rows if r])
    x = P[:, 0] + 0.1; vg = P[:, 1]; ag = P[:, 3]
    xe, ve = lit("vG_lateral_750_N2_experimento_E1.csv")
    xs, vs = lit("vG_lateral_750_N2_DBM_S1.csv")
    xa, aa = lit("alphaG_lateral_750_N2_DBM_S1.csv")
    vint = np.interp(xe, x, vg)
    perf = dict(vG_centro_sim=float(vg[np.argmin(abs(x - 0.1))]), vG_pico_exp=float(ve.max()),
                RMSE_vG=float(np.sqrt(np.mean((vint - ve) ** 2))), erro_rel_medio=float(np.mean(abs(vint - ve)) / ve.mean()),
                alphaG_centro_sim=float(ag[np.argmin(abs(x - 0.1))]), alphaG_centro_DBM=float(aa.max()),
                assimetria_vG=float((vg[x < 0.1].mean() - vg[x > 0.1].mean()) / vg.mean()))
    res = dict(holdup=hold, f_FFT_Hz=float(fpk), f_cruzamentos_Hz=float(1 / per.mean()), periodo_medio_s=float(per.mean()),
               periodo_desvio_s=float(per.std()), n_ciclos=int(len(per)), perfil_750=perf)
    print(json.dumps(res, indent=1))
    (R / "resumo_etapaA.json").write_text(json.dumps(res, indent=1))

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(11, 7.5), dpi=150)
    a = ax[0, 0]; a.plot(t, v, lw=0.8, color="tab:blue"); a.axvspan(20, t.max(), color="0.9", zorder=0)
    a.set_xlabel("t (s)"); a.set_ylabel("v_G,y no ponto PIV (m/s)"); a.set_title("Oscilação da pluma: (−50, 500, 0) mm", fontsize=9); a.grid(alpha=.3)
    a = ax[0, 1]; a.plot(f, A / A.max(), color="tab:blue"); a.axvline(0.17, color="k", ls="--", label="Experimento: 0,17 Hz")
    a.axvline(0.14, color="tab:red", ls=":", label="Krauß & Rzehak (RANS): 0,14 Hz")
    a.set_xlim(0, 1); a.set_xlabel("f (Hz)"); a.set_ylabel("amplitude normalizada"); a.legend(fontsize=7)
    a.set_title(f"FFT 20–80 s: pico em {fpk:.3f} Hz", fontsize=9); a.grid(alpha=.3)
    a = ax[1, 0]; a.plot(x, vg, color="tab:blue", lw=2, label="Este trabalho: EE/RANS (STAR)")
    a.plot(xe, ve, "o", color="k", label="Experimento E1 (Darmana)"); a.plot(xs, vs, "--", color="0.5", label="EL/LES (Darmana)")
    a.set_xlabel("x (m), a partir da parede"); a.set_ylabel("v_G,y médio (m/s)"); a.set_title("Velocidade média do gás, y = 750 mm (20–80 s)", fontsize=9)
    a.legend(fontsize=7); a.grid(alpha=.3)
    a = ax[1, 1]; a.plot(x, ag, color="tab:blue", lw=2, label="Este trabalho"); a.plot(xa, aa, "--", color="0.5", label="EL/LES (Darmana)")
    a.set_xlabel("x (m), a partir da parede"); a.set_ylabel("α_G médio"); a.set_title(f"Fração de gás, y = 750 mm | holdup integral {100*hold['media']:.2f} % (exp. 2,3 %)", fontsize=9)
    a.legend(fontsize=7); a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(R / "fig_etapaA.png")


if __name__ == "__main__":
    main()
