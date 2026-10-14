"""Escoamento monofásico interno em tubos."""
from __future__ import annotations

import math


def fator_atrito_churchill(Re: float, rug_rel: float = 0.0) -> float:
    """Fator de atrito de Darcy, Churchill (1977), Chem. Eng. 84(24):91-92.

    Expressão única para laminar, transição e turbulento (rugoso), equivalente a
    Colebrook-White no turbulento (desvio < 1 %) e a 64/Re no laminar.
    """
    if Re <= 0:
        raise ValueError("Re deve ser positivo")
    A = (2.457 * math.log(1.0 / ((7.0 / Re) ** 0.9 + 0.27 * rug_rel))) ** 16
    B = (37530.0 / Re) ** 16
    return 8.0 * ((8.0 / Re) ** 12 + (A + B) ** -1.5) ** (1.0 / 12.0)


def fator_atrito_blasius_laminar(Re: float) -> float:
    """Fator de Darcy usado por Müller-Steinhagen & Heck (1986): 64/Re até Re = 1187 e
    Blasius 0,3164 Re^-0,25 acima (as duas expressões se cruzam em Re = 1187)."""
    return 64.0 / Re if Re <= 1187.0 else 0.3164 * Re ** -0.25


def nusselt_gnielinski(Re: float, Pr: float) -> float:
    """Nusselt médio totalmente desenvolvido, Gnielinski (1976), Int. Chem. Eng. 16:359-368,
    com fator de atrito de Filonenko f = (0,790 ln Re − 1,64)^-2.

    * Re ≤ 2300: laminar desenvolvido, Nu = 3,66 (parede isotérmica; conservador frente a
      4,36 de fluxo uniforme e ao aumento por desenvolvimento térmico na entrada).
    * 2300 < Re < 10⁴: interpolação linear de Gnielinski (2013), VDI Heat Atlas, G1 §4.
    * Re ≥ 10⁴: Gnielinski (válido 0,1 ≤ Pr ≤ 1000, até Re = 5·10⁶).
    """
    nu_lam = 3.66
    if Re <= 2300.0:
        return nu_lam

    def turb(re: float) -> float:
        f = (0.790 * math.log(re) - 1.64) ** -2
        return (f / 8.0) * (re - 1000.0) * Pr / (1.0 + 12.7 * math.sqrt(f / 8.0) * (Pr ** (2.0 / 3.0) - 1.0))

    if Re >= 1.0e4:
        return turb(Re)
    gamma = (Re - 2300.0) / (1.0e4 - 2300.0)
    return (1.0 - gamma) * nu_lam + gamma * turb(1.0e4)


def h_interno_monofasico(G: float, D: float, mu: float, k: float, Pr: float) -> float:
    """Coeficiente convectivo interno [W/m²K] para fluxo mássico G [kg/m²s]."""
    Re = G * D / mu
    return nusselt_gnielinski(Re, Pr) * k / D


def gradiente_pressao_monofasico(G: float, D: float, rho: float, mu: float, rug: float) -> float:
    """−dP/dz por atrito [Pa/m] (Darcy-Weisbach com Churchill)."""
    Re = G * D / mu
    f = fator_atrito_churchill(Re, rug / D)
    return f * G * G / (2.0 * rho * D)
