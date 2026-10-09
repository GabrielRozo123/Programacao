"""Química da fase líquida: fechamento ψ + 3 classes (cisão aleatória com evaporação) e reator 0-D.

Em cada polímero i, por kg de líquido, transportam-se Y_i (massa derivada de i), Z_i = Y_i ψ_i (mols de
cadeias, aditivo na mistura) e as massas nas classes emaranhadas E_i1, E_i2, E_i3 (Mw ≥ 64, 16–64 e
4–16 kg/mol). A cisão aleatória rompe ligações à taxa k_c = f A exp(−E/RT) (o mesmo A, E da TGA, com o
fator f do mapeamento da cisão aparente na física); os fragmentos menores que N* = M*(T)/m0, o corte de
ebulição a T (Riazi), evaporam:

    S_v,i = ρ k_c N*² m0 Z_i                                  (vapor, kg/(m³ s))
    w_Z,i = ρ k_c Y_i/m0 − 2 S_v,i/(m0 N*)                     (cisões criam cadeias; vapor leva fragmentos)
    w_Y,i = −S_v,i (1 + s_C),   w_sólidos = s_C Σ S_v,i        (s_C: coque por kg de vapor)
    w_E1 = −r1 ρ E1,  w_E2 = ρ(r1 E1 − r2 E2),  w_E3 = ρ(r2 E2 − r3 E3)

e a massa molar ponderal sai das classes (Mw_i), governando a viscosidade. Conferido contra o balanço
populacional exato (massa retida 1–3%, Mw 13–16%) no documento de projeto (docs/design_brief_en.md).

O reator 0-D (tanque perfeitamente misturado, evaporativo, com nível constante e purga de sólidos)
dá a condição inicial do 3-D e a curva de capacidade: vazão processada e temperatura do fundido em
função da temperatura da parede.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import rheology as rh
from .kinetics import POLYMERS, R_GAS

M_LO = (64.0, 16.0, 4.0)          # limites inferiores das classes [kg/mol]
MBAR = tuple(1.848 * m for m in M_LO)


@dataclass(frozen=True)
class Closure:
    key: str
    f: float           # k_c = f k_app (cisão física por ligação)
    m0: float          # massa por ligação do esqueleto [kg/mol]
    Mw0: float         # [kg/mol]
    PDI0: float
    dH: float          # calor de gaseificação por kg de vapor (DSC, já inclui a dessorção) [J/kg]
    k_melt: float      # condutividade do fundido [W/(m K)]
    rheo: str

    @property
    def Mn0(self):
        return self.Mw0 / self.PDI0


CLOSURE = {
    "HDPE": Closure("HDPE", 0.0347, 0.014027, 150.0, 8.0, 920e3, 0.24, "HDPE"),
    "LDPE": Closure("LDPE", 0.0347, 0.014027, 200.0, 10.0, 920e3, 0.22, "LDPE"),
    "PP": Closure("PP", 0.053, 0.021, 300.0, 5.0, 1310e3, 0.17, "PP"),
}

S_CHAR = 0.005            # coque por kg de vapor
SOLIDS_TARGET = 0.10      # fração de sólidos mantida no líquido pela purga


@dataclass
class FeedSpec:
    name: str
    poly: dict                      # frações mássicas dos polímeros (base sem cinzas)
    ash: float = 0.0                # cinzas na entrada do reator (fração mássica)
    T_feed: float = 573.15          # fundido vindo da extrusora [K]
    note: str = ""

    def items(self):
        s = sum(self.poly.values())
        return [(CLOSURE[k], v / s) for k, v in self.poly.items()]

    def describe(self):
        s = sum(self.poly.values())
        return ", ".join(f"{k} {100 * v / s:.0f}%" for k, v in self.poly.items()) + \
            (f"; cinzas {100 * self.ash:.1f}%" if self.ash else "")


FEEDS = {
    "F1": FeedSpec("HDPE puro", {"HDPE": 1.0}, ash=0.002, note="caso de validação"),
    "F2": FeedSpec("PP puro", {"PP": 1.0}, ash=0.01),
    "F3": FeedSpec("poliolefinas pós-consumo (Brasil)", {"HDPE": 0.60, "LDPE": 0.05, "PP": 0.35}, ash=0.01,
                   note="São Carlos: HDPE 59,4 / LDPE 4,0 / PP 36,5 (Matos, 2006), renormalizado"),
}


# ------------------------------------------------------------------ cinética
def k_c(c: Closure, T):
    p = POLYMERS[c.key]
    return c.f * p.A * np.exp(-p.E / (R_GAS * np.asarray(T, dtype=float)))


def n_star(c: Closure, T, f_cut: float = 1.0):
    """Comprimento de corte (ligações do esqueleto) dos fragmentos que evaporam a T."""
    return f_cut * rh.boiling_cut_molar_mass(T) / 1000.0 / c.m0


def class_rates(c: Closure, T):
    kc = k_c(c, T)
    r1 = (kc / (2 * c.m0)) / (1.0 / 64.0 - 1.0 / c.Mw0)
    r2 = kc * M_LO[1] / (1.5 * c.m0)
    r3 = kc * M_LO[2] / (1.5 * c.m0)
    return r1, r2, r3


def Mw_of_state(c: Closure, Y, Z, E):
    """Massa molar ponderal [kg/mol] a partir de Y, Z e das massas das classes."""
    Y = np.maximum(Y, 1e-12)
    Es = sum(E)
    matrix = np.maximum(Y - Es, 1e-12)
    zm = np.maximum(Z - sum(2 * e / m for e, m in zip(E, MBAR)), 1e-12)
    Mn_m = matrix / zm
    return (sum(e * m for e, m in zip(E, MBAR)) + matrix * 1.5 * Mn_m) / Y


def vapour_rate(c: Closure, T, Y, Z, rho, f_cut=1.0):
    """S_v [kg/(m³ s)], com ψ limitado a 1/(N* m0)."""
    kc = k_c(c, T)
    ns = n_star(c, T, f_cut)
    Zc = np.minimum(Z, Y / (ns * c.m0))
    return rho * kc * ns ** 2 * c.m0 * Zc


def gas_selectivity(T):
    return 0.06 * np.exp(-(60e3 / R_GAS) * (1.0 / np.asarray(T, float) - 1.0 / 693.15))


def product_slate(T, f_cut=1.0):
    """Frações mássicas do vapor que sai do líquido: gás (C1–C4), óleo (C5–C20), cera (C21+), coque."""
    sG = gas_selectivity(T)
    Nc = rh.boiling_cut_molar_mass(T) * f_cut / 14.027
    oil_frac = (20 ** 2 - 4 ** 2) / max(Nc ** 2 - 4 ** 2, 1.0)
    rest = 1.0 - sG - S_CHAR
    return {"gás": float(sG), "óleo": float(rest * min(oil_frac, 1.0)),
            "cera": float(rest * max(1.0 - oil_frac, 0.0)), "coque": S_CHAR}


# --------------------------------------------------------------- propriedades
def liquid_density(c: Closure, T, Mn_kgmol):
    return rh.density(c.key, T, Mn_kgmol * 1000.0)


def liquid_viscosity(feed_items, states, T, gamma=0.0):
    """Viscosidade da mistura [Pa s]: η0 de cada polímero (Raju acima, cera POLYWAX abaixo) com
    média logarítmica pela massa, e Cross com os parâmetros do componente majoritário."""
    lnmix, wsum = 0.0, 0.0
    main = max(feed_items, key=lambda cw: cw[1])[0]
    for (c, _), st in zip(feed_items, states):
        Y, Z, E = st["Y"], st["Z"], st["E"]
        Mw = Mw_of_state(c, Y, Z, E) * 1000.0
        r = rh.RHEO[c.rheo]
        ent = rh.eta0(r, T, Mw)
        wax = 0.015 * (Mw / 1080.0) ** 1.9 * np.exp((27e3 / R_GAS) * (1.0 / T - 1.0 / 422.15))
        e0 = np.maximum(ent, wax)
        lnmix = lnmix + Y * np.log(np.maximum(e0, 1e-6))
        wsum = wsum + Y
    e0 = np.exp(lnmix / np.maximum(wsum, 1e-12))
    r = rh.RHEO[main.rheo]
    return rh.ETA_FLOOR + e0 / (1.0 + (e0 * gamma / r.tau_star) ** (1.0 - r.n))


# ---------------------------------------------------------------- reator 0-D
@dataclass
class CSTRResult:
    T: float                 # temperatura do fundido [K]
    feed: float              # vazão de alimentação [kg/s]
    vapour: float            # vapor [kg/s]
    drain: float             # purga de resíduo [kg/s]
    duty: float              # calor pela parede [W]
    holdup: float            # massa de líquido [kg]
    states: list = field(default_factory=list)
    Mw: float = 0.0          # massa molar ponderal média [kg/mol]
    Mn: float = 0.0
    eta: float = 0.0         # viscosidade [Pa s]
    rho: float = 0.0
    slate: dict = field(default_factory=dict)

    @property
    def residence_h(self):
        return self.holdup / self.feed / 3600.0


def _coefficients(feed: FeedSpec, T, f_cut=1.0):
    """Constantes de cada polímero que só dependem de T (calculadas uma vez por temperatura)."""
    out = []
    for c, w in feed.items():
        out.append((c, w, float(k_c(c, T)), float(n_star(c, T, f_cut)), [float(r) for r in class_rates(c, T)]))
    return out


def _species_given_s(feed: FeedSpec, T, Sf, s, rho, f_cut=1.0, co=None):
    """Estado de cada polímero para alimentação Sf e vapor total s [kg/(m³ s)] (sistema linear 2×2)."""
    out, Sv = [], []
    d = Sf - s
    for c, w, kc, ns, (r1, r2, r3) in (co or _coefficients(feed, T, f_cut)):
        a = rho * kc * ns ** 2 * c.m0
        Zf = w / c.Mn0
        # Y d + (1+s_C) a Z = Sf w ;  −(ρ k_c/m0) Y + (d + 2ρ k_c N*) Z = Sf Zf
        A11, A12, A21, A22 = d, (1 + S_CHAR) * a, -rho * kc / c.m0, d + 2 * rho * kc * ns
        det = A11 * A22 - A12 * A21
        Y = (Sf * w * A22 - A12 * Sf * Zf) / det
        Z = (A11 * Sf * Zf - A21 * Sf * w) / det
        if Z > Y / (ns * c.m0):                       # ψ no limite: cadeias já no tamanho de corte
            Y = Sf * w / (d + (1 + S_CHAR) * rho * kc * ns)
            Z = Y / (ns * c.m0)
        sv = a * min(Z, Y / (ns * c.m0))
        E1 = Sf * w / (d + rho * r1)
        E2 = rho * r1 * E1 / (d + rho * r2)
        E3 = rho * r2 * E2 / (d + rho * r3)
        out.append({"Y": Y, "Z": Z, "E": [E1, E2, E3]})
        Sv.append(sv)
    return out, Sv


def _steady_species(feed: FeedSpec, T, Sf, rho, f_cut=1.0, co=None):
    """Estado estacionário do tanque perfeitamente misturado: acha o vapor total s = Σ S_v,i(s) em [0, Sf)."""
    co = co or _coefficients(feed, T, f_cut)
    lo, hi = 0.0, Sf * (1 - 1e-9)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        _, Sv = _species_given_s(feed, T, Sf, mid, rho, f_cut, co)
        if sum(Sv) > mid:
            lo = mid
        else:
            hi = mid
    st, Sv = _species_given_s(feed, T, Sf, 0.5 * (lo + hi), rho, f_cut, co)
    return st, sum(Sv), Sv


def solve_cstr(feed: FeedSpec, volume: float, area: float, h_in: float, T_wall: float | None = None,
               feed_rate: float | None = None, rho: float = 620.0, cp: float = 3240.0, shaft_power: float = 0.0,
               f_cut: float = 1.0) -> CSTRResult:
    """Reator 0-D com nível constante. Modo B (padrão): dada a temperatura da parede, acha a vazão de
    alimentação e a temperatura do fundido; modo A: dada a vazão, acha a temperatura da parede."""
    ash = feed.ash
    items = feed.items()
    dH_mix = sum(w * c.dH for c, w in items)

    def at_T(T):
        # a vazão é tal que alimentação = vapor + purga (sólidos mantidos em SOLIDS_TARGET)
        co = _coefficients(feed, T, f_cut)

        def resid(Sf):
            st, Sv, _ = _steady_species(feed, T, Sf, rho, f_cut, co)
            F = Sf * volume
            V = Sv * volume
            D = (F * ash + S_CHAR * V) / SOLIDS_TARGET
            return F - V - D, st, Sv
        lo, hi = 1e-7, 10.0
        for _ in range(56):              # bisseção em log
            mid = math.sqrt(lo * hi)
            r, _, _ = resid(mid)
            if r > 0:
                hi = mid
            else:
                lo = mid
        Sf = math.sqrt(lo * hi)
        _, st, Sv = resid(Sf)
        F, V = Sf * volume, Sv * volume
        D = (F * ash + S_CHAR * V) / SOLIDS_TARGET
        sens = F * cp * (T - feed.T_feed)
        Q = sens + V * dH_mix - shaft_power
        return F, V, D, Q, st

    if feed_rate is not None:            # modo A
        lo, hi = 600.0, 760.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            F = at_T(mid)[0]
            if F > feed_rate:
                hi = mid
            else:
                lo = mid
        T = 0.5 * (lo + hi)
        F, V, D, Q, st = at_T(T)
        T_wall = T + Q / (h_in * area)
    else:                                # modo B
        lo, hi = 600.0, min(T_wall, 780.0)
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            F, V, D, Q, st = at_T(mid)
            if h_in * area * (T_wall - mid) > Q:
                lo = mid
            else:
                hi = mid
        T = 0.5 * (lo + hi)
        F, V, D, Q, st = at_T(T)
    res = CSTRResult(T=T, feed=F, vapour=V, drain=D, duty=Q, holdup=rho * volume, states=st)
    Ysum = sum(s["Y"] for s in st)
    res.Mw = sum(s["Y"] * Mw_of_state(c, s["Y"], s["Z"], s["E"]) for (c, _), s in zip(items, st)) / Ysum
    res.Mn = Ysum / sum(s["Z"] for s in st)
    res.eta = float(liquid_viscosity(items, st, T))
    res.rho = float(sum(s["Y"] * liquid_density(c, T, res.Mn) for (c, _), s in zip(items, st)) / Ysum)
    res.slate = product_slate(T, f_cut)
    res.T_wall = T_wall
    return res


def capacity_curve(feed: FeedSpec, volume, area, h_in, walls_C=(440, 460, 480, 500, 520, 540), **kw):
    """Vazão processada e temperatura do fundido em função da temperatura da parede."""
    return [solve_cstr(feed, volume, area, h_in, T_wall=Tw + 273.15, **kw) for Tw in walls_C]


def nagata_h(rho, N, d, mu, cp, k, T_vessel, mu_wall=None):
    """Coeficiente interno pela correlação de Nagata para fita helicoidal (Re > 1000):
    Nu = h T/k = 0,37 Re^(2/3) Pr^(1/3) (μ/μ_w)^0,14."""
    Re = rho * N * d ** 2 / mu
    Pr = cp * mu / k
    vis = 1.0 if mu_wall is None else (mu / mu_wall) ** 0.14
    return 0.37 * Re ** (2 / 3) * Pr ** (1 / 3) * vis * k / T_vessel, Re, Pr
