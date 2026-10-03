"""Termoquímica do flare: estequiometria, relação de estado em Z e tabela com β-PDF.

A química é tratada no limite de fração de mistura (seção 3.2 e 4.4 do documento):
o estado local depende só de Z (equilíbrio via Cantera, ou Burke–Schumann se o
Cantera não estiver instalado). Na LES, as médias filtradas vêm da integração
na β-PDF com variância de submalha, o que inclui a interação turbulência–química
e a interação turbulência–radiação na emissão.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import betainc

R_U = 8.314462618        # J/(mol K)
SIGMA = 5.670374419e-8   # W/(m2 K4)
P_ATM = 101325.0         # Pa
G = 9.80665              # m/s2

MW = {"O2": 31.998e-3, "N2": 28.014e-3, "CO2": 44.009e-3, "H2O": 18.015e-3}
Y_O2_AIR = MW["O2"] / (MW["O2"] + 3.76 * MW["N2"])
M_AIR = 0.028965


@dataclass(frozen=True)
class Fuel:
    name: str
    nC: int
    nH: int
    M: float          # kg/mol
    LHV: float        # J/kg
    gamma: float      # cp/cv a ~300 K
    soot_yield: float  # kg fuligem / kg combustível (Tewarson, SFPE Handbook)
    cantera_name: str


PROPANE = Fuel("propano", 3, 8, 44.097e-3, 46.35e6, 1.13, 0.024, "C3H8")
METHANE = Fuel("metano", 1, 4, 16.043e-3, 50.03e6, 1.31, 0.001, "CH4")
ETHANE = Fuel("etano", 2, 6, 30.069e-3, 47.51e6, 1.19, 0.013, "C2H6")
FUELS = {f.name: f for f in (PROPANE, METHANE, ETHANE)}


def stoichiometry(fuel: Fuel) -> dict:
    """a = mols de O2 por mol de combustível; s = razão mássica ar/combustível; Z_st."""
    a = fuel.nC + fuel.nH / 4.0
    s = a * (MW["O2"] + 3.76 * MW["N2"]) / fuel.M
    return {"a": a, "s": s, "Z_st": 1.0 / (1.0 + s)}


def burke_schumann(fuel: Fuel, Z: np.ndarray) -> dict:
    """Frações mássicas de combustão completa (química infinitamente rápida)."""
    Z = np.asarray(Z, dtype=float)
    a = fuel.nC + fuel.nH / 4.0
    r_O2 = a * MW["O2"] / fuel.M
    r_CO2 = fuel.nC * MW["CO2"] / fuel.M
    r_H2O = 0.5 * fuel.nH * MW["H2O"] / fuel.M
    burned = np.minimum(Z, (1.0 - Z) * Y_O2_AIR / r_O2)   # kg combustível queimado / kg mistura
    Y = {
        "F": Z - burned,
        "O2": (1.0 - Z) * Y_O2_AIR - burned * r_O2,
        "N2": (1.0 - Z) * (1.0 - Y_O2_AIR),
        "CO2": burned * r_CO2,
        "H2O": burned * r_H2O,
    }
    Y["O2"] = np.maximum(Y["O2"], 0.0)
    Y["burned"] = burned
    return Y


def radcal_ap(species: str, T: np.ndarray) -> np.ndarray:
    """Coeficiente médio de Planck [1/(atm m)] — ajustes RADCAL da TNF Workshop."""
    t = 1000.0 / np.asarray(T, dtype=float)
    if species == "H2O":
        c = (-0.23093, -1.12390, 9.41530, -2.99880, 0.51382, -1.86840e-5)
    elif species == "CO2":
        c = (18.741, -121.310, 273.500, -194.050, 56.310, -5.8169)
    else:
        raise ValueError(species)
    return sum(ci * t**i for i, ci in enumerate(c))


def soot_kappa_coefficient(n: float = 1.57, k: float = 0.56) -> float:
    """κ_P,fuligem = C·f_v·T, com C = 3.83·C0/C2 (dedução da seção 4.6)."""
    C0 = 36 * np.pi * n * k / ((n**2 - k**2 + 2) ** 2 + 4 * n**2 * k**2)
    return 3.83 * C0 / 1.4388e-2


@dataclass
class StateRelation:
    """Estado em função de Z (sem flutuação): T, ρ, emissão, frações."""
    Z: np.ndarray
    T: np.ndarray
    rho: np.ndarray
    M: np.ndarray
    x_H2O: np.ndarray
    x_CO2: np.ndarray
    Y_F: np.ndarray
    Y_soot: np.ndarray
    kappa: np.ndarray
    emission: np.ndarray   # emissão luminosa da fuligem 4σκ_s T⁴ (f_v,max nominal = 1 ppm) [W/m3]
    T_ad_st: float
    source: str


def state_relation(fuel: Fuel, T_fuel: float, T_inf: float, chi_loss: float,
                   n: int = 2001, use_cantera: bool = True, p: float = P_ATM,
                   phi_rich: float = 2.5) -> StateRelation:
    """Relação de estado φ(Z).

    T_eq(Z) vem de equilíbrio HP (Cantera, gri30) ou de Burke–Schumann com c_p efetivo.
    A perda radiativa usa a abordagem de fração radiante constante (como no FDS):
    T(Z) = T_mix(Z) + (1 − χ)·(T_eq(Z) − T_mix(Z)).
    """
    st = stoichiometry(fuel)
    # malha em Z refinada perto de Z_st (onde tudo acontece)
    Zs = st["Z_st"]
    z1 = np.linspace(0.0, 3 * Zs, n // 2, endpoint=False)
    z2 = np.linspace(3 * Zs, 1.0, n - n // 2)
    Z = np.concatenate([z1, z2])
    Y = burke_schumann(fuel, Z)
    T_mix = None
    source = "Burke-Schumann"
    T_eq = None
    M_mix = None
    xH2O = xCO2 = None
    if use_cantera:
        try:
            import cantera as ct
            gas = ct.Solution("gri30.yaml")
            gas.TPX = T_fuel, p, {fuel.cantera_name: 1.0}
            hF, YF = gas.enthalpy_mass, gas.Y.copy()
            gas.TPX = T_inf, p, {"O2": 1.0, "N2": 3.76}
            hA, YA = gas.enthalpy_mass, gas.Y.copy()
            T_eq = np.empty_like(Z); T_mix = np.empty_like(Z); M_mix = np.empty_like(Z)
            xH2O = np.empty_like(Z); xCO2 = np.empty_like(Z)
            iH2O, iCO2 = gas.species_index("H2O"), gas.species_index("CO2")
            # Limite rico de flamabilidade (como o "rich flammability limit" dos códigos
            # comerciais): acima de Z_rich o equilíbrio prevê craqueamento irreal; a mistura
            # é tratada como o estado queimado em Z_rich misturado com combustível frio.
            Z_rich = phi_rich * Zs / (1 - Zs + phi_rich * Zs)
            gas.HPY = Z_rich * hF + (1 - Z_rich) * hA, p, Z_rich * YF + (1 - Z_rich) * YA
            gas.equilibrate("HP")
            h_r, Y_r = gas.enthalpy_mass, gas.Y.copy()
            for i, z in enumerate(Z):
                gas.HPY = z * hF + (1 - z) * hA, p, z * YF + (1 - z) * YA
                T_mix[i] = gas.T
                if z <= Z_rich:
                    if z > 1e-6:
                        gas.equilibrate("HP")
                else:
                    w = (z - Z_rich) / (1 - Z_rich)
                    gas.HPY = (1 - w) * h_r + w * hF, p, (1 - w) * Y_r + w * YF
                T_eq[i] = gas.T; M_mix[i] = gas.mean_molecular_weight / 1000.0
                xH2O[i] = gas.X[iH2O]; xCO2[i] = gas.X[iCO2]
            source = "Cantera (equilíbrio HP, gri30)"
        except Exception:  # noqa: BLE001 — sem Cantera, cai para Burke–Schumann
            T_eq = None
    if T_eq is None:
        cp_mix = 1100.0
        T_mix = (Z * T_fuel * 1700.0 + (1 - Z) * T_inf * 1005.0) / (Z * 1700.0 + (1 - Z) * 1005.0)
        cp_eff = 1420.0   # calibrado para reproduzir T_ad de alcanos leves (seção 3.2)
        T_eq = T_mix + Y["burned"] * fuel.LHV / cp_eff
        del cp_mix
        moles = {k: Y[k] / (fuel.M if k == "F" else MW[k]) for k in ("F", "O2", "N2", "CO2", "H2O")}
        ntot = sum(moles.values())
        M_mix = 1.0 / ntot
        xH2O, xCO2 = moles["H2O"] / ntot, moles["CO2"] / ntot
    T = T_mix + (1.0 - chi_loss) * (T_eq - T_mix)
    rho = p * M_mix / (R_U * T)
    # Fuligem por relação de estado (Sivathanu & Faeth 1990): só no lado rico da chama,
    # nula para φ ≤ 1, máxima em φ = 2, nula de novo em φ = 5. A emissão para os receptores
    # vem dessa zona luminosa; a potência total é escalada depois para X_rad·Q.
    phi = (Z / np.maximum(1 - Z, 1e-12)) / (Zs / (1 - Zs))
    f_shape = np.clip(np.minimum(phi - 1.0, (5.0 - phi) / 3.0), 0.0, 1.0)
    f_v = 1e-6 * f_shape
    Y_soot = f_v * 1800.0 / rho
    kappa_gas = (p / P_ATM) * (xH2O * radcal_ap("H2O", T) + xCO2 * radcal_ap("CO2", T))
    kappa = np.maximum(kappa_gas, 0.0) + soot_kappa_coefficient() * f_v * T
    emission = 4 * SIGMA * soot_kappa_coefficient() * f_v * T * T**4
    T_ad_st = float(np.interp(Zs, Z, T_eq))
    return StateRelation(Z, T, rho, M_mix, xH2O, xCO2, Y["F"], Y_soot, kappa, emission, T_ad_st, source)


@dataclass
class BetaPDFTable:
    """Tabela φ̃(Z̃, s) com s = Z''²/(Z̃(1−Z̃)) ∈ [0, s_max]. Grades uniformes (busca O(1) na GPU)."""
    Zt: np.ndarray
    s: np.ndarray
    rho: np.ndarray
    drho_dZ: np.ndarray
    T: np.ndarray
    emission: np.ndarray
    Y_F: np.ndarray
    Z_st: float
    T_ad_st: float
    rho_inf: float
    source: str


def beta_pdf_table(sr: StateRelation, Z_st: float, nZ: int = 401, ns: int = 17,
                   s_max: float = 0.8) -> BetaPDFTable:
    """Integra φ(Z) na β-PDF de Favre. Usa diferenças da função beta incompleta em
    cada intervalo, que é robusto mesmo quando a < 1 ou b < 1 (PDF singular nas bordas)."""
    Zt = np.linspace(0.0, 1.0, nZ)
    s = np.linspace(0.0, s_max, ns)
    zf = np.linspace(0.0, 1.0, 4001)
    zm = 0.5 * (zf[1:] + zf[:-1])
    inv_rho = 1.0 / np.interp(zm, sr.Z, sr.rho)
    T_m = np.interp(zm, sr.Z, sr.T)
    e_over_rho = np.interp(zm, sr.Z, sr.emission) * inv_rho
    YF_m = np.interp(zm, sr.Z, sr.Y_F)
    out = {k: np.zeros((nZ, ns)) for k in ("inv_rho", "T", "e_over_rho", "Y_F")}
    for j, sj in enumerate(s):
        for i, z in enumerate(Zt):
            var_ok = sj > 1e-6 and 1e-6 < z < 1 - 1e-6
            if not var_ok:
                w = None
            else:
                gam = 1.0 / sj - 1.0
                a, b = z * gam, (1 - z) * gam
                cdf = betainc(a, b, zf)
                w = np.diff(cdf)
                tot = w.sum()
                w = w / tot if tot > 0 else None
            if w is None:
                out["inv_rho"][i, j] = 1.0 / np.interp(z, sr.Z, sr.rho)
                out["T"][i, j] = np.interp(z, sr.Z, sr.T)
                out["e_over_rho"][i, j] = np.interp(z, sr.Z, sr.emission) * out["inv_rho"][i, j]
                out["Y_F"][i, j] = np.interp(z, sr.Z, sr.Y_F)
            else:
                out["inv_rho"][i, j] = w @ inv_rho
                out["T"][i, j] = w @ T_m
                out["e_over_rho"][i, j] = w @ e_over_rho
                out["Y_F"][i, j] = w @ YF_m
    rho = 1.0 / out["inv_rho"]
    drho = np.gradient(rho, Zt, axis=0)
    return BetaPDFTable(Zt, s, rho, drho, out["T"], rho * out["e_over_rho"], out["Y_F"],
                        Z_st, sr.T_ad_st, float(sr.rho[0]), sr.source)
