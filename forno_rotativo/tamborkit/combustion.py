"""Termoquímica da combustão na fornalha: fração de mistura, equilíbrio (Cantera) e β-PDF.

Mesma abordagem do flare (química rápida; estado φ(Z) por equilíbrio HP, limite rico de flamabilidade e
integração na β-PDF de Favre), agora com a perda de calor tratada à parte: a LES transporta o defeito de
entalpia h_d e usa T = T_ad(Z̃, s) − h_d/c_p (a fornalha perde calor para o tambor, que é o objetivo).

Combustíveis: GLP (propano) para a partida e o gás de pirólise das poliolefinas a 500 °C (rico em CH4,
seguido de C2–C3 e H2; composição de projeto [H] dentro das faixas de Calero 2023 e Honus 2018).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import betainc

P_ATM = 101325.0
R_U = 8.314462618
FUEL_X = {
    "GLP": {"C3H8": 1.0},
    "gas_pirolise": {"CH4": 0.45, "C2H6": 0.15, "C2H4": 0.15, "C3H8": 0.10, "H2": 0.10, "CO": 0.03, "CO2": 0.02},
}
_MW = {"C3H8": 44.097, "CH4": 16.043, "C2H6": 30.07, "C2H4": 28.054, "H2": 2.016, "CO": 28.01, "CO2": 44.01,
       "O2": 31.998, "N2": 28.014, "H2O": 18.015}
_CHO = {"C3H8": (3, 8, 0), "CH4": (1, 4, 0), "C2H6": (2, 6, 0), "C2H4": (2, 4, 0), "H2": (0, 2, 0),
        "CO": (1, 0, 1), "CO2": (1, 0, 2)}


def stoich(fuel_X: dict) -> dict:
    """Z_st, ar estequiométrico e produtos por kg de combustível."""
    tot = sum(fuel_X.values())
    X = {k: v / tot for k, v in fuel_X.items()}
    M = sum(X[k] * _MW[k] for k in X)
    nC = sum(X[k] * _CHO[k][0] for k in X)
    nH = sum(X[k] * _CHO[k][1] for k in X)
    nO = sum(X[k] * _CHO[k][2] for k in X)
    nO2 = nC + nH / 4 - nO / 2
    afr = nO2 * (_MW["O2"] + 3.76 * _MW["N2"]) / M
    return dict(Z_st=1 / (1 + afr), AFR=afr, M=M / 1000, nC=nC, nH=nH, nO2=nO2, X=X)


def state_relation(fuel_X: dict, T_fuel: float = 300.0, T_air: float = 300.0, n: int = 801,
                   phi_rich: float = 2.5) -> dict:
    """φ(Z) adiabático: T, ρ, M, x_H2O + x_CO2 e uma fuligem de relação de estado para o brilho da chama."""
    st = stoich(fuel_X)
    Zs = st["Z_st"]
    zb = min(4 * Zs, 0.5)
    Z = np.concatenate([np.linspace(0, zb, n // 2, endpoint=False), np.linspace(zb, 1, n - n // 2)])
    try:
        import cantera as ct
        gas = ct.Solution("gri30.yaml")
        gas.TPX = T_fuel, P_ATM, st["X"]
        hF, YF = gas.enthalpy_mass, gas.Y.copy()
        gas.TPX = T_air, P_ATM, {"O2": 1.0, "N2": 3.76}
        hA, YA = gas.enthalpy_mass, gas.Y.copy()
        Z_rich = phi_rich * Zs / (1 - Zs + phi_rich * Zs)
        gas.HPY = Z_rich * hF + (1 - Z_rich) * hA, P_ATM, Z_rich * YF + (1 - Z_rich) * YA
        gas.equilibrate("HP")
        h_r, Y_r = gas.enthalpy_mass, gas.Y.copy()
        T = np.empty_like(Z); M = np.empty_like(Z); pwc = np.empty_like(Z)
        iw, ic = gas.species_index("H2O"), gas.species_index("CO2")
        for i, z in enumerate(Z):
            if z <= Z_rich:
                gas.HPY = z * hF + (1 - z) * hA, P_ATM, z * YF + (1 - z) * YA
                if z > 1e-6:
                    gas.equilibrate("HP")
            else:
                w = (z - Z_rich) / (1 - Z_rich)
                gas.HPY = (1 - w) * h_r + w * hF, P_ATM, (1 - w) * Y_r + w * YF
            T[i] = gas.T; M[i] = gas.mean_molecular_weight / 1000; pwc[i] = gas.X[iw] + gas.X[ic]
        source = "Cantera (equilíbrio HP, gri30)"
    except Exception as e:   # noqa: BLE001
        cp = 1350.0
        lhv = 46e6
        burn = np.where(Z <= Zs, Z / Zs, (1 - Z) / (1 - Zs))
        T = T_air + (T_fuel - T_air) * Z + burn * Zs * lhv / cp
        M = np.full_like(Z, 0.0285)
        pwc = 0.21 * burn
        source = f"Burke–Schumann (Cantera indisponível: {type(e).__name__})"
    rho = P_ATM * M / (R_U * T)
    phi = (Z / np.maximum(1 - Z, 1e-12)) / (Zs / (1 - Zs))
    fv = 1e-6 * np.clip(np.minimum(phi - 1.0, (5.0 - phi) / 3.0), 0.0, 1.0)
    return dict(Z=Z, T=T, rho=rho, M=M, pwc=pwc, fv=fv, Z_st=Zs, AFR=st["AFR"], source=source,
                T_ad=float(np.interp(Zs, Z, T)))


def beta_table(sr: dict, nZ: int = 201, ns: int = 11, s_max: float = 0.8) -> dict:
    """Médias de Favre na β-PDF: ρ, ∂ρ/∂Z, T, p_wc e f_v em grade uniforme (Z̃, s)."""
    Zt = np.linspace(0, 1, nZ)
    s = np.linspace(0, s_max, ns)
    zf = np.linspace(0, 1, 2001)
    zm = 0.5 * (zf[1:] + zf[:-1])
    inv_rho = 1 / np.interp(zm, sr["Z"], sr["rho"])
    fields = {k: np.interp(zm, sr["Z"], sr[k]) for k in ("T", "pwc", "fv")}
    out = {k: np.zeros((nZ, ns)) for k in ("inv_rho", "T", "pwc", "fv")}
    for j, sj in enumerate(s):
        for i, z in enumerate(Zt):
            if sj > 1e-6 and 1e-6 < z < 1 - 1e-6:
                g = 1 / sj - 1
                w = np.diff(betainc(z * g, (1 - z) * g, zf))
                w = w / max(w.sum(), 1e-30)
                # média de Favre: φ̃ = ∫ φ P̃ dZ; ρ̄ = 1/∫(1/ρ) P̃ dZ
                out["inv_rho"][i, j] = w @ inv_rho
                for k in ("T", "pwc", "fv"):
                    out[k][i, j] = w @ fields[k]
            else:
                out["inv_rho"][i, j] = 1 / np.interp(z, sr["Z"], sr["rho"])
                for k in ("T", "pwc", "fv"):
                    out[k][i, j] = np.interp(z, sr["Z"], sr[k])
    rho = 1 / out["inv_rho"]
    return dict(Zt=Zt, s=s, rho=rho, drho=np.gradient(rho, Zt, axis=0), T=out["T"], pwc=out["pwc"],
                fv=out["fv"], Z_st=sr["Z_st"], T_ad=sr["T_ad"], rho_air=float(sr["rho"][0]), source=sr["source"])
