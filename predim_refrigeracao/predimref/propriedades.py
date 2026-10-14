"""Propriedades termofísicas: refrigerante (CoolProp, equações de estado de referência) e ar úmido.

Por que CoolProp/HEOS: as equações de estado usadas são as mesmas de referência do NIST
REFPROP (p. ex. Lemmon, McLinden & Wagner 2009 para o propano; Bücker & Wagner 2006 para o
isobutano; Tillner-Roth & Baehr 1994 para o R134a), com modelos de transporte
(viscosidade, condutividade, tensão superficial) da literatura. Bell et al. (2014),
Ind. Eng. Chem. Res. 53, 2498-2508.

A interface de baixo nível (``AbstractState``) é usada por desempenho: cada chamada leva
poucos microssegundos, o que permite discretizar trocadores e capilar finamente.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import CoolProp
import CoolProp.CoolProp as CP

from .constantes import P_ATM

# Fluidos puros ou pseudo-puros (glide desprezível) aceitos. Misturas zeotrópicas
# (R407C, R448A, R449A...) exigiriam tratar o glide de temperatura e ficam de fora.
# R744 (CO2) opera transcrítico a 32 °C de ambiente e não é coberto por este ciclo subcrítico.
FLUIDOS_SUPORTADOS = {
    "R290": "propano (HC, A3)",
    "R600a": "isobutano (HC, A3)",
    "R1270": "propileno (HC, A3)",
    "R134a": "HFC (A1)",
    "R1234yf": "HFO (A2L)",
    "R1234ze(E)": "HFO (A2L)",
    "R152a": "HFC (A2)",
    "R404A": "HFC pseudo-puro (A1)",
    "R507A": "HFC azeotrópico (A1)",
    "R22": "HCFC (A1), legado",
    "R12": "CFC, legado (apenas validação com dados históricos)",
}

# Limite inferior de inflamabilidade [kg/m³] (ISO 817 / ASHRAE 34), usado nos limites de carga.
LFL_KG_M3 = {"R290": 0.038, "R600a": 0.043, "R1270": 0.046, "R152a": 0.130,
             "R1234yf": 0.289, "R1234ze(E)": 0.303}


@dataclass(frozen=True)
class Saturacao:
    """Propriedades de saturação a uma pressão (líquido 'l' e vapor 'v')."""
    P: float
    T: float
    hl: float
    hv: float
    rhol: float
    rhov: float
    sl: float
    sv: float
    mul: float
    muv: float
    kl: float
    kv: float
    cpl: float
    cpv: float
    sigma: float
    pr: float  # pressão reduzida P/Pc

    @property
    def hlv(self) -> float:
        return self.hv - self.hl

    @property
    def Prl(self) -> float:
        return self.cpl * self.mul / self.kl

    @property
    def Prv(self) -> float:
        return self.cpv * self.muv / self.kv

    @property
    def vl(self) -> float:
        return 1.0 / self.rhol

    @property
    def vv(self) -> float:
        return 1.0 / self.rhov


@dataclass(frozen=True)
class Estado:
    """Estado termodinâmico do refrigerante.

    ``x`` é o título termodinâmico (h - hl)/(hv - hl) quando P < Pc: pode ser < 0
    (líquido sub-resfriado) ou > 1 (vapor superaquecido). ``bifasico`` indica 0 < x < 1.
    Propriedades de transporte só são preenchidas fora da região bifásica.
    """
    P: float
    T: float
    h: float
    s: float
    rho: float
    x: float
    cp: Optional[float] = None
    mu: Optional[float] = None
    k: Optional[float] = None

    @property
    def bifasico(self) -> bool:
        return 0.0 < self.x < 1.0

    @property
    def v(self) -> float:
        return 1.0 / self.rho

    @property
    def Pr(self) -> Optional[float]:
        if self.cp is None:
            return None
        return self.cp * self.mu / self.k


class Fluido:
    """Refrigerante com acesso rápido a estados e saturação (SI)."""

    def __init__(self, nome: str, backend: str = "HEOS"):
        if nome not in FLUIDOS_SUPORTADOS:
            raise ValueError(
                f"Fluido '{nome}' não suportado. Opções: {', '.join(FLUIDOS_SUPORTADOS)}. "
                "R744 (transcrítico) e misturas zeotrópicas exigem outro modelo de ciclo."
            )
        self.nome = nome
        self._as = CoolProp.AbstractState(backend, nome)
        self.Tc = self._as.T_critical()
        self.Pc = self._as.p_critical()
        self.M = self._as.molar_mass()  # kg/mol
        self.Ttriplo = self._as.Ttriple()
        self.hidrocarboneto = "HC" in FLUIDOS_SUPORTADOS[nome]

    # ------------------------------------------------------------------ saturação
    def Psat(self, T: float) -> float:
        self._as.update(CoolProp.QT_INPUTS, 0.0, T)
        return self._as.p()

    def Tsat(self, P: float) -> float:
        self._as.update(CoolProp.PQ_INPUTS, P, 0.0)
        return self._as.T()

    def sat(self, P: float) -> Saturacao:
        """Propriedades de saturação (com cache, pressão arredondada a 0,1 Pa)."""
        return _sat_cache(self.nome, round(P, 1))

    # ------------------------------------------------------------------ estados
    def _estado_atual(self, P: float) -> Estado:
        a = self._as
        T, h, s, rho = a.T(), a.hmass(), a.smass(), a.rhomass()
        if P < self.Pc:
            sat = self.sat(P)
            x = (h - sat.hl) / sat.hlv
        else:
            x = -1.0 if T < self.Tc else 2.0
        if 0.0 < x < 1.0:
            return Estado(P, T, h, s, rho, x)
        try:
            cp, mu, k = a.cpmass(), a.viscosity(), a.conductivity()
        except ValueError:
            cp = mu = k = None
        return Estado(P, T, h, s, rho, x, cp, mu, k)

    def estado_PH(self, P: float, h: float) -> Estado:
        self._as.update(CoolProp.HmassP_INPUTS, h, P)
        return self._estado_atual(P)

    def estado_PT(self, P: float, T: float) -> Estado:
        """Estado monofásico por (P, T). Na saturação exata use ``estado_PQ``."""
        self._as.update(CoolProp.PT_INPUTS, P, T)
        return self._estado_atual(P)

    def estado_PS(self, P: float, s: float) -> Estado:
        self._as.update(CoolProp.PSmass_INPUTS, P, s)
        return self._estado_atual(P)

    def estado_PQ(self, P: float, Q: float) -> Estado:
        self._as.update(CoolProp.PQ_INPUTS, P, Q)
        st = self._estado_atual(P)
        if Q in (0.0, 1.0):
            # Estado saturado: o título calculado pode sair 1e-12 fora de [0,1]; fixa e
            # preenche transporte da fase saturada.
            sat = self.sat(P)
            if Q == 0.0:
                return Estado(P, st.T, sat.hl, sat.sl, sat.rhol, 0.0, sat.cpl, sat.mul, sat.kl)
            return Estado(P, st.T, sat.hv, sat.sv, sat.rhov, 1.0, sat.cpv, sat.muv, sat.kv)
        return st

    def estado_PX(self, P: float, x: float) -> Estado:
        """Estado por título termodinâmico (aceita x<0 ou x>1 via entalpia)."""
        sat = self.sat(P)
        return self.estado_PH(P, sat.hl + x * sat.hlv)

    def kappa(self, P: float, T: float) -> float:
        """Razão cp/cv do vapor (expoente isentrópico de gás ideal equivalente)."""
        self._as.update(CoolProp.PT_INPUTS, P, T)
        return self._as.cpmass() / self._as.cvmass()

    def __repr__(self) -> str:
        return f"Fluido({self.nome}, Tc={self.Tc - 273.15:.2f} °C, Pc={self.Pc / 1e5:.2f} bar)"


@lru_cache(maxsize=200_000)
def _sat_cache(nome: str, P: float) -> Saturacao:
    a = _as_cache(nome)
    a.update(CoolProp.PQ_INPUTS, P, 0.0)
    T = a.T()
    hl, rhol, sl = a.hmass(), a.rhomass(), a.smass()
    mul, kl, cpl = a.viscosity(), a.conductivity(), a.cpmass()
    try:
        sigma = a.surface_tension()
    except ValueError:
        sigma = float("nan")
    a.update(CoolProp.PQ_INPUTS, P, 1.0)
    hv, rhov, sv = a.hmass(), a.rhomass(), a.smass()
    muv, kv, cpv = a.viscosity(), a.conductivity(), a.cpmass()
    return Saturacao(P, T, hl, hv, rhol, rhov, sl, sv, mul, muv, kl, kv, cpl, cpv, sigma,
                     P / a.p_critical())


@lru_cache(maxsize=32)
def _as_cache(nome: str):
    return CoolProp.AbstractState("HEOS", nome)


# ============================================================================ ar
@dataclass(frozen=True)
class PropAr:
    rho: float
    cp: float
    mu: float
    k: float

    @property
    def Pr(self) -> float:
        return self.cp * self.mu / self.k


@lru_cache(maxsize=4096)
def ar_seco(T: float, P: float = P_ATM) -> PropAr:
    """Ar seco (Lemmon et al. 2000 via CoolProp). Usado nas correlações de transferência
    do lado do ar: a umidade altera cp e μ em menos de 1 % nas condições de projeto."""
    a = _as_cache("Air")
    a.update(CoolProp.PT_INPUTS, P, round(T, 3))
    return PropAr(a.rhomass(), a.cpmass(), a.viscosity(), a.conductivity())


def ar_umido(T: float, UR: float, P: float = P_ATM) -> dict:
    """Psicrometria rigorosa (ASHRAE RP-1485, Herrmann, Kretzschmar & Gatley 2009, via
    CoolProp HAPropsSI). Retorna entalpia e volume por kg de ar seco.

    Chaves: W [kg_v/kg_as], h [J/kg_as], v [m³/kg_as], rho_mist [kg_mistura/m³],
    Tdp [K], UR.
    """
    W = CP.HAPropsSI("W", "T", T, "P", P, "R", UR)
    h = CP.HAPropsSI("H", "T", T, "P", P, "W", W)
    v = CP.HAPropsSI("Vda", "T", T, "P", P, "W", W)
    Tdp = CP.HAPropsSI("Tdp", "T", T, "P", P, "W", W) if W > 0 else float("nan")
    return {"T": T, "UR": UR, "W": W, "h": h, "v": v, "rho_mist": (1.0 + W) / v, "Tdp": Tdp}


def calor_latente_agua(T: float) -> float:
    """Entalpia de vaporização da água [J/kg] (IAPWS-95 via CoolProp)."""
    Tq = min(max(T, 273.16), 373.0)
    return (CP.PropsSI("H", "T", Tq, "Q", 1, "Water") - CP.PropsSI("H", "T", Tq, "Q", 0, "Water"))
