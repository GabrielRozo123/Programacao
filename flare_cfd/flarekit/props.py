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

MW = {"O2": 31.998e-3, "N2": 28.014e-3, "CO2": 44.009e-3, "H2O": 18.015e-3, "SO2": 64.058e-3}
Y_O2_AIR = MW["O2"] / (MW["O2"] + 3.76 * MW["N2"])
M_AIR = 0.028965


def pressure_at_altitude(z: float) -> float:
    """Pressão da atmosfera padrão (ISA) na altitude z [m] acima do nível do mar [Pa]."""
    return P_ATM * (1.0 - 2.25577e-5 * z) ** 5.25588


@dataclass(frozen=True)
class Fuel:
    """Combustível puro ou mistura. nC, nH, nO, nN, nS são átomos por mol de combustível
    (fracionários numa mistura); X guarda a composição molar ((espécie, fração), ...)."""
    name: str
    nC: float
    nH: float
    M: float          # kg/mol
    LHV: float        # J/kg (PCI)
    gamma: float      # cp/cv a ~300 K
    soot_yield: float  # kg fuligem / kg combustível (informativo)
    cantera_name: str  # espécie do gri30 (combustível puro); "" para misturas
    nO: float = 0.0
    nN: float = 0.0
    nS: float = 0.0
    X: tuple = ()

    @property
    def is_mixture(self) -> bool:
        return len(self.X) > 0

    def composition(self) -> dict:
        """Frações molares {espécie: x} (nomes de SPECIES)."""
        return dict(self.X) if self.X else {CANTERA_TO_KEY.get(self.cantera_name, self.cantera_name): 1.0}

    def describe(self) -> str:
        comp = " · ".join(f"{k} {100 * v:.1f}%" for k, v in sorted(self.composition().items(),
                                                                   key=lambda kv: -kv[1]))
        return (f"{self.name}: {comp} | M = {1e3 * self.M:.2f} g/mol · PCI = {self.LHV / 1e6:.2f} MJ/kg · "
                f"γ = {self.gamma:.3f}")


@dataclass(frozen=True)
class SpeciesData:
    atoms: tuple       # (C, H, O, N, S)
    M: float           # kg/mol
    LHV_mol: float     # J/mol (PCI a 25 °C, H2O vapor, S → SO2)
    cp: float          # J/(mol K) a 298 K
    nasa: str          # nome no nasa_gas.yaml do Cantera
    soot_yield: float  # kg/kg (Tewarson, SFPE Handbook; aproximado, informativo)


# Propriedades a 25 °C dos polinômios NASA (Glenn) do Cantera (nasa_gas.yaml); PCI conferido em
# tests/test_flarekit.py contra o próprio Cantera.
SPECIES = {
    "H2":     SpeciesData((0, 2, 0, 0, 0), 2.016e-3, 241.8e3, 28.84, "H2", 0.0),
    "CH4":    SpeciesData((1, 4, 0, 0, 0), 16.043e-3, 802.6e3, 35.69, "CH4", 0.001),
    "C2H6":   SpeciesData((2, 6, 0, 0, 0), 30.070e-3, 1428.6e3, 52.50, "C2H6", 0.013),
    "C2H4":   SpeciesData((2, 4, 0, 0, 0), 28.054e-3, 1323.2e3, 42.89, "C2H4", 0.043),
    "C3H8":   SpeciesData((3, 8, 0, 0, 0), 44.097e-3, 2043.1e3, 73.59, "C3H8", 0.024),
    "C3H6":   SpeciesData((3, 6, 0, 0, 0), 42.081e-3, 1925.7e3, 64.43, "C3H6,propylene", 0.095),
    "nC4H10": SpeciesData((4, 10, 0, 0, 0), 58.124e-3, 2657.4e3, 98.66, "C4H10,n-butane", 0.029),
    "iC4H10": SpeciesData((4, 10, 0, 0, 0), 58.124e-3, 2648.2e3, 96.64, "C4H10,isobutane", 0.029),
    "C4H8":   SpeciesData((4, 8, 0, 0, 0), 56.108e-3, 2540.8e3, 85.56, "C4H8,1-butene", 0.095),
    "nC5H12": SpeciesData((5, 12, 0, 0, 0), 72.151e-3, 3271.7e3, 119.95, "C5H12,n-pentane", 0.030),
    "CO":     SpeciesData((1, 0, 1, 0, 0), 28.010e-3, 283.0e3, 29.14, "CO", 0.0),
    "H2S":    SpeciesData((0, 2, 0, 0, 1), 34.076e-3, 518.2e3, 34.19, "H2S", 0.0),
    "CO2":    SpeciesData((1, 0, 2, 0, 0), 44.009e-3, 0.0, 37.14, "CO2", 0.0),
    "N2":     SpeciesData((0, 0, 0, 2, 0), 28.014e-3, 0.0, 29.12, "N2", 0.0),
    "O2":     SpeciesData((0, 0, 2, 0, 0), 31.998e-3, 0.0, 29.38, "O2", 0.0),
    "H2O":    SpeciesData((0, 2, 1, 0, 0), 18.015e-3, 0.0, 33.59, "H2O", 0.0),
}
CANTERA_TO_KEY = {"C3H8": "C3H8", "CH4": "CH4", "C2H6": "C2H6", "H2": "H2"}


def mixture(name: str, comp: dict) -> Fuel:
    """Combustível a partir da composição molar {espécie: fração ou %} (normalizada para 1)."""
    bad = [k for k in comp if k not in SPECIES]
    if bad:
        raise ValueError(f"espécies desconhecidas: {bad}; use {sorted(SPECIES)}")
    tot = float(sum(comp.values()))
    if tot <= 0:
        raise ValueError("composição vazia")
    x = {k: float(v) / tot for k, v in comp.items() if v > 0}
    at = np.zeros(5)
    M = cp = lhv = soot = 0.0
    for k, xi in x.items():
        d = SPECIES[k]
        at += xi * np.asarray(d.atoms, float)
        M += xi * d.M
        cp += xi * d.cp
        lhv += xi * d.LHV_mol
    for k, xi in x.items():
        soot += xi * SPECIES[k].M / M * SPECIES[k].soot_yield
    if lhv <= 0:
        raise ValueError("a mistura não tem componentes combustíveis")
    gamma = cp / (cp - R_U)
    return Fuel(name, float(at[0]), float(at[1]), M, lhv / M, gamma, soot, "",
                nO=float(at[2]), nN=float(at[3]), nS=float(at[4]), X=tuple(sorted(x.items())))


def parse_composition(text: str) -> dict:
    """'H2: 20, CH4: 40, C2H6: 10' → {'H2': 20.0, 'CH4': 40.0, 'C2H6': 10.0}."""
    out = {}
    for part in text.replace(";", ",").split(","):
        if part.strip():
            k, v = part.split(":")
            out[k.strip()] = float(v)
    return out


PROPANE = Fuel("propano", 3, 8, 44.097e-3, 46.35e6, 1.13, 0.024, "C3H8")
METHANE = Fuel("metano", 1, 4, 16.043e-3, 50.03e6, 1.31, 0.001, "CH4")
ETHANE = Fuel("etano", 2, 6, 30.069e-3, 47.51e6, 1.19, 0.013, "C2H6")
FUELS = {f.name: f for f in (PROPANE, METHANE, ETHANE)}


# Composições de gás de tocha/refinaria (% molar). Não há composição medida pública da REPLAN;
# estas são referências abertas, para estudo ilustrativo (confira com dados da unidade).
FLARE_GAS_PRESETS = {
    # pontos médios das faixas da FISPQ "Gás Residual de Refinaria" (Acelen, ex-RLAM/Petrobras;
    # H2 12,5–52,5 · CH4 12,5–42,5 · C2 10–40 · C3 1,5–3,5 · C4 1,5–3,5 · C5 0–1 · N2+CO2 2–8 ·
    # CO 0,5–2,5 · H2S 0–1,2), com as frações agrupadas (C2, C3, inertes) divididas por estimativa
    "gás de refinaria típico (FISPQ ex-RLAM)": {
        "H2": 33.0, "CH4": 29.0, "C2H6": 15.0, "C2H4": 10.5, "C3H8": 1.5, "C3H6": 1.0,
        "nC4H10": 2.5, "nC5H12": 0.5, "N2": 3.5, "CO2": 1.5, "CO": 1.5, "H2S": 0.5},
    # média de gás de tocha "de uma planta típica" em Emam (2015), Petroleum & Coal — mais
    # pesada, rica em GLP (i-C5 somado ao n-C5)
    "gás de tocha médio de refinaria (Emam 2015)": {
        "CH4": 43.6, "C2H6": 3.66, "C3H8": 20.3, "nC4H10": 2.78, "iC4H10": 14.3, "nC5H12": 0.796,
        "C2H4": 1.05, "C3H6": 2.73, "C4H8": 0.696, "H2": 5.54, "CO": 0.186, "CO2": 0.713,
        "H2S": 0.256, "O2": 0.357, "N2": 1.30, "H2O": 1.14},
    # caso hipotético de despressurização de unidades de hidrogênio/hidrotratamento
    "rico em H2 (despressurização, hipotético)": {
        "H2": 75.0, "CH4": 15.0, "C2H6": 5.0, "C3H8": 3.0, "N2": 2.0},
}


def flare_gas(name: str) -> Fuel:
    """Combustível a partir de FLARE_GAS_PRESETS."""
    return mixture(name, FLARE_GAS_PRESETS[name])


def lhv_volumetric(fuel: Fuel, T: float = 273.15, p: float = P_ATM) -> float:
    """PCI por volume de gás nas condições (T, p) [J/m³]; padrão: Nm³ (0 °C, 1 atm)."""
    return fuel.LHV * fuel.M * p / (R_U * T)


def o2_demand(fuel: Fuel) -> float:
    """mols de O2 por mol de combustível (C → CO2, H → H2O, S → SO2, descontando o O do combustível)."""
    return fuel.nC + fuel.nH / 4.0 + fuel.nS - fuel.nO / 2.0


def products_per_mol(fuel: Fuel) -> dict:
    """Mols de produtos da combustão estequiométrica com ar, por mol de combustível."""
    a = o2_demand(fuel)
    return {"CO2": fuel.nC, "H2O": fuel.nH / 2.0, "SO2": fuel.nS, "N2": 3.76 * a + fuel.nN / 2.0}


def stoichiometry(fuel: Fuel) -> dict:
    """a = mols de O2 por mol de combustível; s = razão mássica ar/combustível; Z_st."""
    a = o2_demand(fuel)
    s = a * (MW["O2"] + 3.76 * MW["N2"]) / fuel.M
    return {"a": a, "s": s, "Z_st": 1.0 / (1.0 + s)}


def burke_schumann(fuel: Fuel, Z: np.ndarray) -> dict:
    """Frações mássicas de combustão completa (química infinitamente rápida)."""
    Z = np.asarray(Z, dtype=float)
    pr = products_per_mol(fuel)
    r_O2 = o2_demand(fuel) * MW["O2"] / fuel.M
    r_CO2 = pr["CO2"] * MW["CO2"] / fuel.M
    r_H2O = pr["H2O"] * MW["H2O"] / fuel.M
    r_SO2 = pr["SO2"] * MW["SO2"] / fuel.M
    r_N2f = fuel.nN / 2.0 * MW["N2"] / fuel.M                 # N2 que já vem no combustível
    burned = np.minimum(Z, (1.0 - Z) * Y_O2_AIR / r_O2)   # kg combustível queimado / kg mistura
    Y = {
        "F": Z - burned,
        "O2": (1.0 - Z) * Y_O2_AIR - burned * r_O2,
        "N2": (1.0 - Z) * (1.0 - Y_O2_AIR) + burned * r_N2f,
        "CO2": burned * r_CO2,
        "H2O": burned * r_H2O,
        "SO2": burned * r_SO2,
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


# produtos e radicais do equilíbrio quando o combustível é uma mistura (base NASA do Cantera)
_EQ_SPECIES = ["N2", "O2", "H2O", "CO2", "CO", "H2", "OH", "H", "O", "NO", "N", "CH4", "C2H2,acetylene"]
_EQ_SULFUR = ["SO2", "SO", "S", "S2", "H2S", "COS"]


def _cantera_gas(fuel: Fuel):
    """Fase gasosa do Cantera para o equilíbrio: gri30 para combustível puro; para misturas, um
    conjunto reduzido de espécies da base NASA (cobre C4/C5, olefinas e H2S, que o gri30 não tem)."""
    import cantera as ct
    if not fuel.is_mixture:
        return ct.Solution("gri30.yaml"), {fuel.cantera_name: 1.0}, "gri30"
    comp = fuel.composition()
    names = list(_EQ_SPECIES) + (list(_EQ_SULFUR) if fuel.nS > 0 else [])
    names += [SPECIES[k].nasa for k in comp if SPECIES[k].nasa not in names]
    lib = {sp.name: sp for sp in ct.Species.list_from_file("nasa_gas.yaml")}
    gas = ct.Solution(thermo="ideal-gas", species=[lib[n] for n in names])
    return gas, {SPECIES[k].nasa: x for k, x in comp.items()}, "base NASA, mistura"


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
            gas, X_fuel, mech = _cantera_gas(fuel)
            gas.TPX = T_fuel, p, X_fuel
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
            source = f"Cantera (equilíbrio HP, {mech})"
        except Exception:  # noqa: BLE001 — sem Cantera, cai para Burke–Schumann
            T_eq = None
    if T_eq is None:
        cp_mix = 1100.0
        T_mix = (Z * T_fuel * 1700.0 + (1 - Z) * T_inf * 1005.0) / (Z * 1700.0 + (1 - Z) * 1005.0)
        cp_eff = 1420.0   # calibrado para reproduzir T_ad de alcanos leves (seção 3.2)
        T_eq = T_mix + Y["burned"] * fuel.LHV / cp_eff
        del cp_mix
        moles = {k: Y[k] / (fuel.M if k == "F" else MW[k]) for k in ("F", "O2", "N2", "CO2", "H2O", "SO2")}
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
