"""
modelo_pontual.py
=================
Modelo "pontual" da absorção reativa de CO2 em NaOH no ponto de medição de pH
do experimento de Darmana et al. (2007), reproduzindo a abordagem de Krauß & Rzehak
(2016, 2018): sem dependência espacial, só as concentrações no líquido, com
hidrodinâmica imposta pelo experimento (α_G, d_b, u_rel).

Serve para (i) validar a química que vai para o STAR-CCM+ (constantes, fator de
aumento, rede de reações) antes do CFD e (ii) dimensionar o passo de tempo.

Química e propriedades: Apêndice A de Krauß & Rzehak (2018), Chem. Eng. Sci. 181, 199–214
  R_I   CO2 + OH⁻ ⇌ HCO3⁻               k_I+ (Pohorecki & Moniuk, 1988, com força iônica)
  R_II  HCO3⁻ + OH⁻ ⇌ CO3²⁻ + H2O       k_II+ = 1e4 m³/(kmol·s) (K&R: suficiente), K_II (Hikita et al.)
  R_III CO2 + H2O ⇌ HCO3⁻ + H⁺          k_III+ (Johnson, 1982), K_III (Edwards et al., 1978)
Transferência: Γ = E·k_L·a·(He·C_G − C_L)   (He = C_L/C_G no equilíbrio, com salting-out)
  k_L de Brauer: k_L = D/d·(2 + 0,015 Re^0,89 Sc^0,7)
  E de DeCoursey (1974) com E_a pelo ajuste explícito de Krauß & Rzehak (Apêndice B)

Uso:  python modelo_pontual.py      → resultados/pontual_*.csv/.png/.json
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

AQUI = Path(__file__).parent
T = 298.15            # K (não informada no experimento; K&R usam condições ambiente)
P = 101325.0          # Pa
R = 8.314
# --- propriedades do solvente (A.1–A.2) ---
MU_L = np.exp(3.184 + 570.6 / (T - 140)) * 1e-6          # Pa s
RHO_L = 997.05   # kg/m³ (IAPWS, 25 °C). A correlação (A.2) de K&R dá 966 kg/m³ a 298 K, valor implausível para água
# --- gás: CO2 puro ---
C_G = P / (R * T) / 1e3                                    # kmol/m³
# --- constantes de equilíbrio (A.12, A.13, A.16) ---
KW = 10 ** (-5840 / T + 55.21 - 22.48 * np.log10(T)) * RHO_L**2        # (kmol/m³)²
KIII = np.exp(-12090 / T + 235.5 - 36.78 * np.log(T)) * 1e-3 * RHO_L   # kmol/m³
KII_INF = 10 ** (1567 / T + 0.4134 - 0.006737 * T)                     # m³/kmol
K_III_MAIS = np.exp(-6.19e4 / T + 1247 - 183 * np.log(T))              # 1/s
K_II_MAIS = 1e4                                                         # m³/(kmol s)
# --- Henry e difusividades (A.4–A.8, tabelas A.1–A.3) ---
HE_W = 3.54e-7 * R * T * np.exp(2044 / T)                 # C_L/C_G, água pura
H_ION = dict(Na=0.1143, OH=0.0839, HCO3=0.0967, CO3=0.1423)
H_GAS = -0.0172 + (-0.338e-3) * (T - 298.15)
B_ION = dict(Na=-0.0857, OH=-0.1088, HCO3=-0.1150, CO3=-0.2450)
D_ION = {k: v[0] * 1e-9 * (T / v[1] - 1) ** v[2] for k, v in dict(
    Na=(5.391, 209.7, 1.619), OH=(26.65, 216.5, 1.658), HCO3=(7.016, 204.0, 2.394), CO3=(5.447, 210.3, 2.193)).items()}
D_CO2_W = 2.35e-6 * np.exp(-2119 / T)


def propriedades(c):
    """c = dict de concentrações (kmol/m³) → He, D_CO2, I."""
    He = HE_W * 10 ** (-sum((H_ION[i] + H_GAS) * c[i] for i in H_ION))
    D_co2 = D_CO2_W * (1 + 0.624 * sum(B_ION[i] * c[i] for i in B_ION))
    I = 0.5 * (c["Na"] + c["OH"] + c["HCO3"] + 4 * c["CO3"])
    return He, D_co2, I


def k_I_mais(I):
    return 10 ** (-2382 / T + 11.90) * 10 ** (0.221 * I - 0.016 * I**2)   # m³/(kmol s)


def K_II(c_na):
    s = np.sqrt(c_na)
    return KII_INF * 10 ** (1.01 * s / (1 + 1.27 * s) + 0.125 * c_na)


def kl_brauer(d, urel, D):
    Re = urel * d * RHO_L / MU_L
    Sc = MU_L / (RHO_L * D)
    return D / d * (2 + 0.015 * Re**0.89 * Sc**0.7)


def Ea_krauss(chi, delta):
    """Ajuste explícito de Krauß & Rzehak (Eqs. B.4–B.6) para o E_a do instantâneo de 2ª ordem."""
    if abs(delta - 1) < 1e-9:
        return 1 + chi / delta
    x = chi if delta > 1 else chi / np.sqrt(delta)
    lnx = np.log(np.expm1(x)) if x < 50 else x          # ln(exp(x) − 1), estável
    f = 1 + 0.5 * (delta - 1) * (2 / np.pi * np.arctan(0.2 * np.pi / 2 * lnx) + 1)
    return 1 + f * chi / delta


def E_decoursey(Ha, Ea):
    if Ea <= 1 + 1e-9:
        return 1.0
    a = Ea - 1
    return max(1.0, -Ha**2 / (2 * a) + np.sqrt(Ha**4 / (4 * a * a) + Ea * Ha**2 / a + 1))


AGUA = [True]


def taxas(c):
    """Fontes molares (kmol/m³/s) das espécies no líquido e diagnósticos."""
    He, D_co2, I = propriedades(c)
    kIp = k_I_mais(I)
    kIm = KW / KIII * kIp
    kIIm = K_II_MAIS / K_II(c["Na"])
    kIIIm = K_III_MAIS / KIII
    oh = max(c["OH"], 1e-14)
    RIp, RIm = kIp * c["CO2"] * oh, kIm * c["HCO3"]
    RIIp, RIIm = K_II_MAIS * c["HCO3"] * oh, kIIm * c["CO3"]
    RIIIp, RIIIm = K_III_MAIS * c["CO2"], kIIIm * c["HCO3"] * KW / oh
    if not AGUA[0]:
        RIIIp = RIIIm = 0.0
    S = dict(CO2=-RIp + RIm - RIIIp + RIIIm,
             OH=-RIp + RIm - RIIp + RIIm - RIIIp + RIIIm,
             HCO3=RIp - RIm - RIIp + RIIm + RIIIp - RIIIm,
             CO3=RIIp - RIIm, Na=0.0)
    return S, dict(He=He, D_co2=D_co2, I=I, kIp=kIp)


def simula(alpha_g=0.012, d=3.5e-3, urel=0.23, pH0=12.5, t_fim=250.0, modelo_E="krauss", reacao_agua=True):
    AGUA[0] = reacao_agua
    c0 = KW / 10 ** (-pH0)
    especies = ["CO2", "OH", "HCO3", "CO3", "Na"]
    y0 = [0.0, c0, 0.0, 0.0, c0]
    aL = 1 - alpha_g
    a = 6 * alpha_g / d

    def diag(y):
        c = dict(zip(especies, np.maximum(y, 0)))
        S, p = taxas(c)
        kL = kl_brauer(d, urel, p["D_co2"])
        CAi = p["He"] * C_G
        Ha = np.sqrt(p["kIp"] * p["D_co2"] * max(c["OH"], 0)) / kL
        delta = np.sqrt(D_ION["OH"] / p["D_co2"])
        chi = c["OH"] / (2 * CAi) * delta
        Ea = Ea_krauss(chi, delta) if modelo_E == "krauss" else 1 / delta + chi   # Eq. (37), usada por Darmana
        E = E_decoursey(Ha, Ea)
        gamma = E * kL * a * (CAi - c["CO2"])                 # kmol/(m³ reator·s)
        return c, S, dict(kL=kL, Ha=Ha, Ea=Ea, E=E, Gamma=gamma, He=p["He"],
                          pH=-np.log10(KW / max(c["OH"], 1e-20)))

    def rhs(t, y):
        c, S, g = diag(y)
        dy = [S[k] for k in especies]
        dy[0] += g["Gamma"] / aL
        return dy

    ts = np.arange(0, t_fim + 1e-9, 1.0)
    sol = solve_ivp(rhs, (0, t_fim), y0, method="LSODA", t_eval=ts, rtol=1e-8, atol=1e-14, max_step=0.5)
    hist = []
    for t, y in zip(sol.t, sol.y.T):
        c, S, g = diag(y)
        hist.append(dict(t=float(t), **{k: float(v) for k, v in c.items()}, **{k: float(v) for k, v in g.items()}))
    return hist


def le_csv(nome):
    with open(AQUI / "dados_literatura" / nome) as f:
        r = csv.DictReader(f)
        return [{k: float(v) for k, v in row.items()} for row in r]


def main():
    out = AQUI / "resultados"
    out.mkdir(exist_ok=True)
    exp = le_csv("pH_experimento_E2.csv")
    dbm = le_csv("pH_simulacao_DBM_S2.csv")
    casos = {
        "Krauß & Rzehak (E_a ajustado) + reação com água": dict(modelo_E="krauss"),
        "Sem a reação com água (só via OH⁻)": dict(modelo_E="krauss", reacao_agua=False),
        "E_a aproximado (Darmana)": dict(modelo_E="aprox"),
    }
    res = {nome: simula(**kw) for nome, kw in casos.items()}

    def t_cruza(h, ph, chave="pH"):
        for a, b in zip(h, h[1:]):
            if a[chave] >= ph > b[chave]:
                return a["t"] + (a[chave] - ph) / (a[chave] - b[chave]) * (b["t"] - a["t"])
        return float("nan")

    resumo = {}
    texp = np.array([e["t_s"] for e in exp]); pexp = np.array([e["pH"] for e in exp])
    for nome, h in res.items():
        t = np.array([x["t"] for x in h]); p = np.array([x["pH"] for x in h])
        erro = np.sqrt(np.mean((np.interp(texp, t, p) - pexp) ** 2))
        resumo[nome] = dict(t_pH10=t_cruza(h, 10), t_pH8=t_cruza(h, 8), t_pH7_5=t_cruza(h, 7.5),
                            RMSE_pH=float(erro), E_max=max(x["E"] for x in h), Ha0=h[0]["Ha"], Ea0=h[0]["Ea"],
                            kL=h[0]["kL"], He0=h[0]["He"])
    resumo["Experimento E2"] = dict(t_pH10=t_cruza([{"t": e["t_s"], "pH": e["pH"]} for e in exp], 10),
                                    t_pH8=t_cruza([{"t": e["t_s"], "pH": e["pH"]} for e in exp], 8),
                                    t_pH7_5=t_cruza([{"t": e["t_s"], "pH": e["pH"]} for e in exp], 7.5))
    for k, v in resumo.items():
        print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})
    (out / "pontual_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(out / "pontual_historico.csv", "w", newline="") as f:
        nome = list(res)[0]
        w = csv.DictWriter(f, fieldnames=list(res[nome][0].keys()))
        w.writeheader(); w.writerows(res[nome])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4), dpi=150)
    a1.plot(texp, pexp, "o", ms=2.5, color="k", label="Experimento E2 (Darmana et al., 2007)")
    a1.plot([d["t_s"] for d in dbm], [d["pH"] for d in dbm], ".", ms=1, color="0.6", label="Euler–Lagrange/LES (Darmana)")
    for (nome, h), cor in zip(res.items(), ["tab:blue", "tab:green", "tab:orange"]):
        a1.plot([x["t"] for x in h], [x["pH"] for x in h], color=cor, lw=2, label=f"Pontual: {nome}")
    a1.set_xlabel("t (s)"); a1.set_ylabel("pH"); a1.set_xlim(0, 250); a1.grid(alpha=.3); a1.legend(fontsize=7)
    h = res[list(res)[0]]
    t = [x["t"] for x in h]
    for k, cor in (("OH", "tab:blue"), ("CO3", "tab:green"), ("HCO3", "tab:red"), ("CO2", "k")):
        a2.plot(t, [x[k] for x in h], color=cor, label=k)
    a2b = a2.twinx(); a2b.plot(t, [x["E"] for x in h], ":", lw=2, color="tab:purple", label="E"); a2b.set_ylabel("E (pontilhado)")
    a2.set_xlabel("t (s)"); a2.set_ylabel("C (kmol/m³)"); a2.grid(alpha=.3); a2.legend(fontsize=7, loc="center right")
    fig.suptitle("Modelo pontual no sensor de pH (α_G = 1,2 %, d = 3,5 mm, u_rel = 0,23 m/s)", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "pontual_pH.png")


if __name__ == "__main__":
    main()
