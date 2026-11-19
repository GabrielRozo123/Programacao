"""
caso_co2_naoh.py
================
Estudo de caso: absorção reativa de CO2 puro em NaOH numa coluna de bolhas
semibatelada. Acopla HIDRODINÂMICA (εG, d_b → a, kL), CINÉTICA (rede de
reações do CO2 em meio alcalino) e EQUAÇÃO DE PROJETO (gás pistonado,
líquido bem misturado).

É o sistema-referência da literatura recente de colunas de bolhas reativas
(experimento de Darmana et al., 2007; simulações de Krauß & Rzehak, 2017/2018;
Liu et al., 2021; Michelson et al., 2023). Aqui ele é aplicado à NOSSA coluna
(D = 0,15 m, H0 = 0,9 m, U_G = 2 cm/s), com a hidrodinâmica vinda (i) da
correlação de Akita & Yoshida e (ii) do CFD validado.

Rede de reações (25 °C)
  CO2 + OH⁻ ⇌ HCO3⁻          k_OH: log10 k = 11,895 − 2382/T  [L/(mol·s)]  (Pohorecki & Moniuk, 1988)
  CO2 + H2O ⇌ HCO3⁻ + H⁺     k_w ≈ 0,03 s⁻¹ (lenta; importa a pH baixo)
  HCO3⁻ + OH⁻ ⇌ CO3²⁻ + H2O  instantânea (equilíbrio, pK2 = 10,33)
  pK1 = 6,35, pKw = 14,0 (diluição infinita; força iônica desprezada)

Transferência de massa com reação (teoria do filme)
  Ha = √(k_OH [OH⁻] D_CO2) / kL
  Ei = 1 + D_OH [OH⁻] / (2 D_CO2 C*)
  E  = van Krevelen–Hoftijzer(Ha, Ei)
  N  = kL (E C* − c_CO2,L)                 (aproximação; E → 1 a pH baixo)

Gás (CO2 puro, pistonado) — a bolha encolhe: a(z) ∝ F(z)
  dF/dz = −N a0 F/F0  ⇒  F(H) = F0 exp(−λ H_D),  λ = N a0 / F0
Líquido (bem misturado, Pe ≪ 1)
  dc/dt = F0 (1 − e^(−λ H_D)) / H0 − r,      db/dt = r      (b = HCO3⁻ + CO3²⁻)
  r = k_OH ([OH⁻] c − [HCO3⁻]/K_eq) + k_w (c − [H⁺][HCO3⁻]/K1)
  pH pelo balanço de cargas: [Na⁺] + [H⁺] = [OH⁻] + [HCO3⁻] + 2[CO3²⁻]

Uso:  python caso_co2_naoh.py            → resultados/caso_co2_naoh.json/.csv/.png
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from cinetica_projeto import fator_aumento
from projeto_coluna_bolhas import Propriedades, d32_akita_yoshida, holdup_akita_yoshida, kl_higbie

T = 298.15
R_GAS = 8.314
P = 101325.0                       # Pa (CO2 puro, ≈ 1 atm)
K_OH = 10 ** (11.895 - 2382 / T) * 1e-3   # m³/(mol·s)
K_W = 0.03                         # s⁻¹
K1 = 10 ** -6.35 * 1e3             # mol/m³
K2 = 10 ** -10.33 * 1e3            # mol/m³
KW = 1e-14 * 1e6                   # mol²/m⁶
K_EQ = K1 / KW                     # m³/mol   (CO2 + OH⁻ ⇌ HCO3⁻)
D_CO2, D_OH = 1.92e-9, 5.27e-9     # m²/s
C_STAR = 0.034 * 1e3 * (P / 101325)  # mol/m³ (kH = 0,034 mol/(L·atm))
C_G = P / (R_GAS * T)              # mol/m³ no gás
PH0 = 12.5
NA = 10 ** (PH0 - 14) * 1e3        # mol/m³ (NaOH = [OH⁻] inicial)

D, H0, UG = 0.15, 0.90, 0.02
F0 = UG * C_G                      # mol/(m²·s)


def fontes():
    p = Propriedades(D_A=D_CO2)
    e_ay = float(holdup_akita_yoshida(UG, D, p))
    return {
        "Correlação (Akita & Yoshida)": (e_ay, float(d32_akita_yoshida(UG, D, p))),
        "CFD validado": (0.0856, 5.0e-3),
    }


def especiacao(b):
    """[H⁺] pelo balanço de cargas, dado o carbono iônico b (mol/m³)."""
    def f(logh):
        h = 10 ** logh
        return NA + h - KW / h - b * (h + 2 * K2) / (h + K2)
    logh = brentq(f, -16, 3)       # [H⁺] em mol/m³ (pH = −log10(h/1000))
    h = 10 ** logh
    return h, KW / h, b * h / (h + K2), b * K2 / (h + K2)


def simula(eps, d, t_fim=120.0):
    p = Propriedades(D_A=D_CO2)
    kL = float(kl_higbie(d, UG / eps, p))
    a0 = 6 * eps / d
    HD = H0 / (1 - eps)

    def taxas(c, b):
        h, oh, hco3, _ = especiacao(b)
        Ha = np.sqrt(K_OH * max(oh, 0) * D_CO2) / kL
        Ei = 1 + D_OH * max(oh, 0) / (2 * D_CO2 * C_STAR)
        E = fator_aumento(Ha, Ei) if Ha > 1e-6 else 1.0
        N = kL * max(E * C_STAR - c, 0.0)
        lam = N * a0 / F0
        S = F0 * (1 - np.exp(-lam * HD)) / H0
        r = K_OH * (oh * c - hco3 / K_EQ) + K_W * (c - h * hco3 / K1)
        return S, r, dict(pH=-np.log10(h / 1e3), Ha=Ha, Ei=Ei, E=E, eta=1 - np.exp(-lam * HD),
                          OH=oh, c=c, b=b)

    def rhs(t, y):
        S, r, _ = taxas(max(y[0], 0), max(y[1], 0))
        return [S - r, r]

    ts = np.arange(0, t_fim + 1e-9, 1.0)
    sol = solve_ivp(rhs, (0, t_fim), [0.0, 0.0], method="BDF", t_eval=ts, rtol=1e-7, atol=1e-9)
    hist = [taxas(max(c, 0), max(b, 0))[2] | {"t": float(t)} for t, c, b in zip(sol.t, *sol.y)]
    return dict(kL=kL, a=a0, kLa=kL * a0, eps=eps, d=d, hist=hist)


def t_cruza(hist, ph):
    for h0, h1 in zip(hist, hist[1:]):
        if h0["pH"] >= ph > h1["pH"]:
            return h0["t"] + (h0["pH"] - ph) / (h0["pH"] - h1["pH"]) * (h1["t"] - h0["t"])
    return float("nan")


def main():
    out = Path(__file__).parent / "resultados"
    out.mkdir(exist_ok=True)
    print(f"k_OH = {K_OH:.2f} m³/(mol·s) | C* = {C_STAR:.1f} mol/m³ | [NaOH]0 = {NA:.1f} mol/m³ | F0 = {F0:.3f} mol/(m²·s)")
    res = {}
    for nome, (eps, d) in fontes().items():
        r = simula(eps, d)
        h = r["hist"]
        r["t_pH10"] = t_cruza(h, 10.0)
        r["t_pH8"] = t_cruza(h, 8.3)
        print(f"\n{nome}: εG = {eps:.3f}, d = {d*1e3:.2f} mm, a = {r['a']:.0f} 1/m, kL = {r['kL']:.2e} m/s, kLa = {r['kLa']:.4f} 1/s")
        print(f"  t=0: Ha = {h[0]['Ha']:.2f}, Ei = {h[0]['Ei']:.2f}, E = {h[0]['E']:.2f}, η = {h[0]['eta']:.2f}")
        print(f"  pH 10 em t = {r['t_pH10']:.1f} s | pH 8,3 em t = {r['t_pH8']:.1f} s | pH final (120 s) = {h[-1]['pH']:.2f}")
        res[nome] = r

    with open(out / "caso_co2_naoh.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)
    with open(out / "caso_co2_naoh.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fonte", "t_s", "pH", "Ha", "Ei", "E", "eficiencia_absorcao"])
        for nome, r in res.items():
            for h in r["hist"]:
                w.writerow([nome, h["t"], f"{h['pH']:.4f}", f"{h['Ha']:.4f}", f"{h['Ei']:.4f}", f"{h['E']:.4f}", f"{h['eta']:.4f}"])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4), dpi=150)
    for (nome, r), cor in zip(res.items(), ["0.45", "tab:blue"]):
        t = [h["t"] for h in r["hist"]]
        ax1.plot(t, [h["pH"] for h in r["hist"]], color=cor, lw=2, label=nome)
        ax2.plot(t, [h["E"] for h in r["hist"]], color=cor, lw=2, label=f"E — {nome}")
        ax2.plot(t, [h["Ha"] for h in r["hist"]], color=cor, lw=1, ls="--", label=f"Ha — {nome}")
    ax1.set_xlabel("t (s)"); ax1.set_ylabel("pH"); ax1.grid(alpha=0.3); ax1.legend(fontsize=8)
    ax2.set_xlabel("t (s)"); ax2.set_ylabel("E, Ha"); ax2.grid(alpha=0.3); ax2.legend(fontsize=7)
    fig.suptitle("CO2 puro em NaOH (pH 12,5) — D = 0,15 m, H0 = 0,9 m, U_G = 2 cm/s", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "fig_caso_co2_naoh.png")
    print(f"\nsalvo em {out}")


if __name__ == "__main__":
    main()
