"""
analisa_LES.py
==============
Etapa F: LES (WALE, Euler–Euler, STAR-CCM+) × RANS (k-ε, etapa B) × experimento
(Darmana et al., 2007) na coluna reativa CO2/NaOH.

Entradas (monitores exportados do STAR):
  resultados_cfd/etapaF_LES/      pH_sensor, holdup, aG_sensor, d32_sensor, taxa_abs (.csv)
  resultados_cfd/etapaB_RANS_CO2/ HOLDUP, alphaG_sensor, taxa_abs, d32_eixo (.csv); pH_sensor.csv (opcional)
Troca N2 → CO2: t = 14 s no LES e t = 20 s no RANS. Todos os tempos são contados a partir da troca.

Saída: resultados_cfd/etapaF_LES/fig_validacao_LES.png  e  resumo_LES.json
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = Path(__file__).parent
LES = AQUI / "resultados_cfd" / "etapaF_LES"
RANS = AQUI / "resultados_cfd" / "etapaB_RANS_CO2"
LIT = AQUI / "dados_literatura"
T_LES, T_RANS = 14.0, 20.0
JANELA = (20.0, 89.0)          # médias: 20 s após a troca até o fim do trecho exportado (K&R: 20–95 s)
D0 = 5.5                       # mm, diâmetro de entrada
COR = {"exp": "#555555", "rans": "#d08c2a", "les": "#1f5fbf"}


def le(caminho):
    d = np.genfromtxt(caminho, delimiter=",", skip_header=1, usecols=(0, 1))
    d = d[np.isfinite(d).all(axis=1)]
    return d[np.argsort(d[:, 0])]


def janela(d, t0, a=JANELA[0], b=JANELA[1]):
    t = d[:, 0] - t0
    m = (t >= a) & (t < b)
    return float(d[m, 1].mean()), float(d[m, 1].std())


def espectro(d, t0, a=JANELA[0], b=JANELA[1]):
    t = d[:, 0] - t0
    m = (t >= a) & (t < b)
    ti = np.linspace(t[m][0], t[m][-1], m.sum())
    x = np.interp(ti, t[m], d[m, 1])
    x = (x - np.polyval(np.polyfit(ti, x, 1), ti)) * np.hanning(x.size)   # remove a tendência lenta
    f = np.fft.rfftfreq(x.size, ti[1] - ti[0])
    P = np.abs(np.fft.rfft(x)) ** 2
    return f, P / P[(f > 0.03) & (f < 1)].max()


def freq_dominante(f, P):
    k = (f > 0.03) & (f < 1)
    return float(f[k][np.argmax(P[k])])


def tempo_ate(d, t0, ph):
    t = d[:, 0] - t0
    m = t > 0
    abaixo = d[m, 1] <= ph
    return float(t[m][np.argmax(abaixo)]) if abaixo.any() else None


def main():
    les = {k: le(LES / f"{k}.csv") for k in ["pH_sensor", "holdup", "aG_sensor", "d32_sensor", "taxa_abs"]}
    rans = {"holdup": le(RANS / "HOLDUP.csv"), "aG_sensor": le(RANS / "alphaG_sensor.csv"),
            "taxa_abs": le(RANS / "taxa_abs.csv")}
    if (RANS / "pH_sensor.csv").exists():
        rans["pH_sensor"] = le(RANS / "pH_sensor.csv")
    exp = le(LIT / "pH_experimento_E2.csv")
    d32_exp = np.genfromtxt(LIT / "d32_axial_experimento_E2.csv", delimiter=",", skip_header=1)
    d32_rans = le(RANS / "d32_eixo.csv")
    d32_rans[:, 0] *= np.sqrt(3)          # line probe exportada com direção [10,10,10]

    res = {"janela_s_apos_troca": JANELA}
    res["holdup"] = {"exp": 0.012, "DBM": 0.016, "KR2018": 0.013,
                     "RANS": janela(rans["holdup"], T_RANS)[0], "LES": janela(les["holdup"], T_LES)[0]}
    fL, PL = espectro(les["aG_sensor"], T_LES)
    fR, PR = espectro(rans["aG_sensor"], T_RANS)
    res["f_pluma_Hz"] = {"exp": 0.10, "DBM": 0.15, "KR2018": 0.08,
                         "RANS": freq_dominante(fR, PR), "LES": freq_dominante(fL, PL),
                         "resolucao_Hz": 1 / (JANELA[1] - JANELA[0])}

    def absorvido(d, t0):
        t = d[:, 0] - t0
        m = (t >= 0) & (t <= JANELA[1])
        return float(np.trapezoid(d[m, 1], t[m]))

    res["CO2_absorvido_kmol"] = {"RANS": absorvido(rans["taxa_abs"], T_RANS), "LES": absorvido(les["taxa_abs"], T_LES)}
    res["d32_topo_sobre_d0"] = {"exp_z0.94": float(d32_exp[d32_exp[:, 0].argmax(), 1]),
                                "RANS": float(np.interp(0.98, d32_rans[:, 0], d32_rans[:, 1]) / D0),
                                "LES": janela(les["d32_sensor"], T_LES)[0] / D0}
    atrasos = {}
    for ph in [12.0, 11.5, 11.0, 10.5, 10.0, 9.0, 8.0]:
        te = float(np.interp(-ph, -exp[:, 1], exp[:, 0]))
        linha = {"exp": te}
        for nome, dd, t0 in [("LES", les.get("pH_sensor"), T_LES), ("RANS", rans.get("pH_sensor"), T_RANS)]:
            if dd is not None:
                tl = tempo_ate(dd, t0, ph)
                if tl is not None:
                    linha[nome] = tl
                    linha[nome + "_atraso_%"] = 100 * (tl - te) / te
        atrasos[str(ph)] = linha
    res["pH_tempo_s"] = atrasos

    # ---------- figura ----------
    fig, ax = plt.subplots(2, 2, figsize=(12, 9))
    a = ax[0, 0]
    a.plot(exp[:, 0], exp[:, 1], "o", ms=3, color=COR["exp"], label="Experimento (Darmana et al., 2007)")
    if "pH_sensor" in rans:
        a.plot(rans["pH_sensor"][:, 0] - T_RANS, rans["pH_sensor"][:, 1], "--", color=COR["rans"], lw=1.8, label="RANS k-ε")
    a.plot(les["pH_sensor"][:, 0] - T_LES, les["pH_sensor"][:, 1], color=COR["les"], lw=2, label="LES WALE")
    a.set(xlim=(0, None), ylim=(7.5, 12.8), xlabel="tempo desde a entrada de CO$_2$ (s)", ylabel="pH no sensor (y = 980 mm)")
    a.legend(frameon=False, fontsize=9)
    a.set_title("pH no topo da coluna")

    a = ax[0, 1]
    a.plot(rans["holdup"][:, 0] - T_RANS, 100 * rans["holdup"][:, 1], color=COR["rans"], lw=1.4, label="RANS k-ε")
    a.plot(les["holdup"][:, 0] - T_LES, 100 * les["holdup"][:, 1], color=COR["les"], lw=1.6, label="LES WALE")
    a.axhspan(1.2 * 0.8, 1.2 * 1.2, color=COR["exp"], alpha=0.15, label="Experimento 1,2 % ± 20 %")
    a.axhline(1.2, color=COR["exp"], lw=1)
    a.set(xlim=(-14, JANELA[1]), ylim=(0, 3), xlabel="tempo desde a entrada de CO$_2$ (s)", ylabel="α$_G$ integral (%)")
    a.legend(frameon=False, fontsize=9)
    a.set_title("Holdup de gás")

    a = ax[1, 0]
    a.plot(fR, PR, color=COR["rans"], lw=1.4, label=f"RANS: {res['f_pluma_Hz']['RANS']:.2f} Hz".replace(".", ","))
    a.plot(fL, PL, color=COR["les"], lw=1.6, label=f"LES: {res['f_pluma_Hz']['LES']:.2f} Hz".replace(".", ","))
    a.axvline(0.10, color=COR["exp"], lw=1.5, ls=":", label="Experimento: 0,10 Hz")
    a.set(xlim=(0, 0.8), ylim=(0, 1.05), xlabel="frequência (Hz)", ylabel="espectro de α$_G$ (normalizado)")
    a.legend(frameon=False, fontsize=9)
    a.set_title("Oscilação da pluma (α$_G$ no sensor)")

    a = ax[1, 1]
    a.plot(rans["taxa_abs"][:, 0] - T_RANS, 1e6 * rans["taxa_abs"][:, 1], color=COR["rans"], lw=1.4, label="RANS k-ε")
    a.plot(les["taxa_abs"][:, 0] - T_LES, 1e6 * les["taxa_abs"][:, 1], color=COR["les"], lw=1.6, label="LES WALE")
    a.set(xlim=(0, JANELA[1]), ylim=(0, None), xlabel="tempo desde a entrada de CO$_2$ (s)",
          ylabel="absorção de CO$_2$ (10$^{-6}$ kmol/s)")
    g = 100 * (res["CO2_absorvido_kmol"]["LES"] / res["CO2_absorvido_kmol"]["RANS"] - 1)
    a.text(0.97, 0.06, f"CO$_2$ absorvido em {JANELA[1]:.0f} s: LES {g:+.0f} % × RANS",
           transform=a.transAxes, ha="right", fontsize=10)
    a.legend(frameon=False, fontsize=9, loc="upper right")
    a.set_title("Taxa de absorção na coluna")

    for a in ax.flat:
        a.grid(alpha=0.3)
    fig.suptitle("Coluna de bolhas reativa CO$_2$/NaOH (Darmana et al., 2007): LES × RANS × experimento", fontsize=13)
    fig.tight_layout()
    fig.savefig(LES / "fig_validacao_LES.png", dpi=150)
    (LES / "resumo_LES.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
