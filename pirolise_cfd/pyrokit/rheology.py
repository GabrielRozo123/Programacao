"""Reologia e propriedades térmicas do fundido que craqueia (literatura aberta; ver README).

Viscosidade (modelo de Cross com superposição tempo–temperatura e dependência da massa molar):

    η(γ̇, T, Mw) = η_piso + η0 / [1 + (η0 γ̇ / τ*)^(1−n)],      η0 = η_ref(Mw) · a_T(T)
    η_ref = K Mw^α  (Mw ≥ Mc)   ou   K Mc^α (Mw/Mc)  (Mw < Mc, regime de Rouse)
    a_T = exp[(Ea/R)(1/T − 1/T_ref)]

com Mw = Mn [2 + (PDI0 − 2)(Mn/Mn0)] (a cisão aleatória leva a polidispersão a 2). HDPE: K = 3,4e−15,
α = 3,6 a 190 °C (Raju et al. 1979), Mc = 3 800 g/mol, Ea = 27 kJ/mol; PP: η_ref = 1,45e−6 (Mw/1000)^3,745
a 230 °C, Ea = 42 kJ/mol; PS: K = 3,9e−15, α = 3,4 a 200 °C, Ea ≈ 55 kJ/mol (300–450 °C). n e τ*: faixas
típicas de bancos de dados de injeção. Misturas: média logarítmica ponderada pela massa.

Propriedades: densidade de Zoller & Walsh (isóbaras de Tait), cp do ATHAS (Wunderlich), condutividade
de fundido indo para a de cera líquida quando Mn cai abaixo de Mc.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

R_GAS = 8.314462618


@dataclass(frozen=True)
class Rheo:
    K: float          # η_ref = K Mw^α  [Pa s, Mw em g/mol]
    alpha: float
    Mc: float         # massa molar crítica de emaranhamento [g/mol]
    Tref: float       # [K]
    Ea: float         # energia de ativação de fluxo [J/mol]
    n: float          # índice de pseudoplasticidade (Cross)
    tau_star: float   # [Pa]
    Mw0: float        # massa molar ponderal da resina [g/mol]
    PDI0: float

    @property
    def Mn0(self):
        return self.Mw0 / self.PDI0


RHEO = {
    "HDPE": Rheo(3.4e-15, 3.6, 3800.0, 463.15, 27e3, 0.35, 2e4, 150e3, 8.0),
    "LDPE": Rheo(3.4e-15, 3.6, 3800.0, 463.15, 55e3, 0.30, 3e4, 200e3, 10.0),
    "PP": Rheo(1.45e-6 * 1000.0 ** -3.745, 3.745, 7000.0, 503.15, 42e3, 0.30, 2e4, 300e3, 5.0),
    "PS": Rheo(3.9e-15, 3.4, 33000.0, 473.15, 55e3, 0.25, 3e4, 280e3, 2.5),
    "PET": Rheo(3.4e-15, 3.6, 3800.0, 553.15, 60e3, 0.70, 1e5, 40e3, 2.0),
}

ETA_FLOOR = 2e-4     # hidrocarboneto líquido quente [Pa s]
ETA_MAX = 1e5


def Mw_of_Mn(r: Rheo, Mn):
    """Massa molar ponderal a partir da numérica sob cisão aleatória [g/mol]."""
    Mn = np.asarray(Mn, dtype=float)
    return Mn * (2.0 + (r.PDI0 - 2.0) * np.clip(Mn / r.Mn0, 0.0, 1.0))


def eta0(r: Rheo, T, Mw, xp=np):
    """Viscosidade a taxa nula [Pa s] (T em K, Mw em g/mol). xp: numpy ou torch."""
    Mw = xp.clip(Mw, 1.0, None) if xp is np else Mw.clamp(min=1.0)
    above = r.K * Mw ** r.alpha
    below = r.K * r.Mc ** r.alpha * (Mw / r.Mc)
    ref = xp.where(Mw >= r.Mc, above, below)
    aT = xp.exp((r.Ea / R_GAS) * (1.0 / T - 1.0 / r.Tref))
    return ref * aT


def viscosity(r: Rheo, gamma, T, Mw, xp=np):
    """Modelo de Cross com piso [Pa s]."""
    e0 = eta0(r, T, Mw, xp)
    if xp is np:
        e = ETA_FLOOR + e0 / (1.0 + (e0 * np.asarray(gamma) / r.tau_star) ** (1.0 - r.n))
        return np.clip(e, ETA_FLOOR, ETA_MAX)
    e = ETA_FLOOR + e0 / (1.0 + (e0 * gamma / r.tau_star) ** (1.0 - r.n))
    return e.clamp(ETA_FLOOR, ETA_MAX)


# ------------------------------------------------------------- propriedades
def density(key: str, T, Mn=None):
    """Massa específica do líquido [kg/m³] (T em K); abaixo de 2 kg/mol tende à de alcanos líquidos."""
    Tc = np.asarray(T, dtype=float) - 273.15
    if key in ("HDPE", "LDPE"):
        rho = 1000.0 / (1.1595 + 8.0e-4 * Tc)
    elif key == "PP":
        rho = 738.6 / (1.0 + 6.7e-4 * (Tc - 230.0))
    elif key == "PS":
        rho = 1000.0 / (0.9287 * np.exp(5.131e-4 * Tc))
    else:
        rho = 1300.0 * (1.0 - 6e-4 * (Tc - 25.0))
    if Mn is not None:
        f = np.clip(np.asarray(Mn, dtype=float) / 2000.0, 0.0, 1.0)
        rho = f * rho + (1 - f) * 610.0
    return rho


def heat_capacity(key: str, T):
    """cp do líquido [J/(kg K)]."""
    T = np.asarray(T, dtype=float)
    if key in ("HDPE", "LDPE"):
        return (17.48 + 0.0412 * T) / 0.014027
    return {"PP": 3000.0, "PS": 2300.0, "PET": 1900.0}.get(key, 2800.0) * np.ones_like(T)


def conductivity(key: str, Mn=None, Mc=3800.0):
    """Condutividade térmica [W/(m K)]: fundido → cera líquida quando Mn < Mc."""
    k_melt = {"HDPE": 0.24, "LDPE": 0.22, "PP": 0.17, "PS": 0.16, "PET": 0.20}.get(key, 0.2)
    if Mn is None:
        return k_melt
    return 0.10 + (k_melt - 0.10) * np.clip(np.asarray(Mn, dtype=float) / Mc, 0.0, 1.0)


def boiling_cut_molar_mass(T):
    """Massa molar [g/mol] do n-alcano que ferve a T (1 atm), pela correlação de Riazi:
    Tb = 1070 − exp(6,98291 − 0,02013 M^(2/3)). Frações mais leves saem como vapor."""
    T = np.asarray(T, dtype=float)
    return ((6.98291 - np.log(1070.0 - T)) / 0.02013) ** 1.5


def normal_boiling_point(M):
    """Tb [K] do n-alcano de massa molar M [g/mol] (Riazi)."""
    return 1070.0 - np.exp(6.98291 - 0.02013 * np.asarray(M, dtype=float) ** (2.0 / 3.0))
