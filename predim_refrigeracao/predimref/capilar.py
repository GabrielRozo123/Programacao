"""Tubo capilar adiabático: modelo homogêneo de equilíbrio (HEM) com blocagem crítica.

Equações (escoamento 1-D, regime permanente, adiabático, horizontal):
  massa:      G = ṁ / A = constante
  energia:    h + G² v² / 2 = h₀ = h_in + G² v_in² / 2
  quantidade de movimento:  −dP = f G² v / (2D) dL + G² dv

Região líquida (sub-resfriada, incompressível): perda de entrada (1 + K) G² v_l / 2 e
    L_liq = 2 D ρ_l (P₁ − P_sat(T_in)) / (f_l G²)
Região bifásica: integração em pressão a partir do ponto de flash; em cada pressão o título
sai da equação da energia (raiz de uma quadrática em x) e dL da quantidade de movimento.
Blocagem (escoamento crítico): quando −dv/dP ≥ 1/G² o numerador (−dP − G² dv) se anula,
dL/dP → 0 e a entropia passa por um máximo (linha de Fanno). Se isso ocorre antes de atingir
a pressão do evaporador, o capilar está blocado e seu comprimento é o comprimento até a
seção crítica (a expansão final ocorre fora do tubo).

Viscosidade bifásica: McAdams (1/μ = x/μ_v + (1−x)/μ_l), Cicchitti (μ = xμ_v + (1−x)μ_l) ou
Dukler (μ = ρ_tp[x v_v μ_v + (1−x) v_l μ_l]); fator de atrito de Churchill.

O HEM despreza o atraso de vaporização (líquido metaestável), o que tende a dar comprimentos
um pouco menores que os reais para a mesma vazão (ver validacao/ com dados de Li et al. 1990).
Referências: Stoecker & Jones (1982) cap. 11; Bittle & Pate (1994) ASHRAE Trans. 100:52-64;
Wongwises et al. (2002) ScienceAsia 28:71-76; Hermes, Melo & Knabben (2010) Appl. Therm. Eng.
30:449-457; ASHRAE Handbook—Refrigeration, cap. "Refrigerant-Control Devices".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from scipy.optimize import brentq

from .avisos import ErroProjeto
from .correlacoes.monofasico import fator_atrito_churchill
from .propriedades import Fluido

SERIE_POLEGADA_IN = (0.026, 0.028, 0.031, 0.036, 0.040, 0.042, 0.049, 0.054, 0.059, 0.064, 0.070, 0.075, 0.080)
SERIE_METRICA_MM = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0)


@dataclass
class ParametrosCapilar:
    serie: str = "polegada"                 # "polegada" (comercial na América Latina) ou "metrica"
    diametros_mm: Optional[tuple] = None    # sobrepõe a série
    rugosidade_m: float = 0.75e-6
    K_entrada: float = 0.5                  # contração abrupta
    modelo_viscosidade: str = "mcadams"
    L_min: float = 1.0
    L_max: float = 5.0
    L_alvo: float = 2.5
    n_passos: int = 300
    tolerancia_diametro_mm: float = 0.0127  # ±0,0005"

    def diametros(self) -> list:
        if self.diametros_mm is not None:
            return [d * 1e-3 for d in self.diametros_mm]
        if self.serie == "metrica":
            return [d * 1e-3 for d in SERIE_METRICA_MM]
        return [d * 25.4e-3 for d in SERIE_POLEGADA_IN]


def viscosidade_bifasica(x: float, sat, modelo: str) -> float:
    if modelo == "mcadams":
        return 1.0 / (x / sat.muv + (1.0 - x) / sat.mul)
    if modelo == "cicchitti":
        return x * sat.muv + (1.0 - x) * sat.mul
    if modelo == "dukler":
        vv, vl = sat.vv, sat.vl
        return (x * vv * sat.muv + (1.0 - x) * vl * sat.mul) / (x * vv + (1.0 - x) * vl)
    raise ValueError(f"modelo de viscosidade desconhecido: {modelo}")


@dataclass
class ResultadoCapilar:
    D: float
    m: float
    G: float
    L: float
    L_liquido: float
    L_bifasico: float
    blocado: bool
    P_saida: float          # pressão na seção de saída (crítica se blocado)
    x_saida: float
    T_saida: float
    P_flash: float
    perfil: dict = field(default_factory=dict)


def _estado_hem(fl: Fluido, P: float, h0: float, G: float, modelo: str):
    sat = fl.sat(P)
    vf, vg = sat.vl, sat.vv
    vfg = vg - vf
    a = 0.5 * G * G * vfg * vfg
    b = sat.hlv + G * G * vf * vfg
    c = sat.hl + 0.5 * G * G * vf * vf - h0
    x = (-b + math.sqrt(b * b - 4.0 * a * c)) / (2.0 * a) if a > 0 else -c / b
    x = max(x, 0.0)
    v = vf + x * vfg
    s = sat.sl + x * (sat.sv - sat.sl)
    return x, v, s, viscosidade_bifasica(x, sat, modelo), sat.T


def comprimento_capilar(fl: Fluido, m: float, D: float, P_in: float, h_in: float, P_out: float,
                        p: ParametrosCapilar, guardar_perfil: bool = False) -> ResultadoCapilar:
    A = math.pi * D * D / 4.0
    G = m / A
    eD = p.rugosidade_m / D
    e_in = fl.estado_PH(P_in, h_in)
    h0 = h_in + 0.5 * (G / e_in.rho) ** 2
    perfil = {"L": [], "P": [], "T": [], "x": [], "v": [], "s": []} if guardar_perfil else {}
    L_liq = 0.0
    if e_in.x < 0.0:   # líquido sub-resfriado
        v_l = 1.0 / e_in.rho
        P1 = P_in - (1.0 + p.K_entrada) * G * G * v_l / 2.0
        if P1 <= P_out:
            raise ErroProjeto("vazão alta demais para o capilar: a perda de entrada já excede ΔP disponível")

        # O líquido escoa de forma isentálpica (adiabático, energia cinética ~constante). O flash
        # ocorre onde h_l(P) + G² v_l(P)²/2 = h₀. Não é P_sat(T_in): para Tβ > 1 (propano perto de
        # 40 °C) o líquido esfria na expansão e o flash acontece abaixo de P_sat(T_in).
        def g_flash(P):
            sat = fl.sat(P)
            return sat.hl + 0.5 * G * G * sat.vl ** 2 - h0

        if g_flash(P1) <= 0.0:
            P_flash = P1
        elif g_flash(P_out) >= 0.0:
            P_flash = None   # o líquido chega ao evaporador sem vaporizar no tubo
        else:
            P_flash = brentq(g_flash, P_out, P1, xtol=1e-3, rtol=1e-12)
        P_lim = P_out if P_flash is None else P_flash
        sat_lim = fl.sat(P_lim)
        mu_l = 0.5 * (e_in.mu + sat_lim.mul)
        v_lm = 0.5 * (v_l + sat_lim.vl)
        f_l = fator_atrito_churchill(G * D / mu_l, eD)
        L_liq = 2.0 * D * (P1 - P_lim) / (f_l * G * G * v_lm)
        if guardar_perfil:
            T_lim = fl.estado_PH(P_lim, h_in).T
            for LL, PP, TT in ((0.0, P_in, e_in.T), (0.0, P1, e_in.T), (L_liq, P_lim, T_lim)):
                perfil["L"].append(LL); perfil["P"].append(PP); perfil["T"].append(TT)
                perfil["x"].append(0.0); perfil["v"].append(v_l); perfil["s"].append(e_in.s)
        if P_flash is None:
            return ResultadoCapilar(D, m, G, L_liq, L_liq, 0.0, False, P_out, 0.0, sat_lim.T, P_out, perfil)
    else:              # entrada já bifásica (sem sub-resfriamento)
        P_flash = P_in - (1.0 + p.K_entrada) * G * G * e_in.v / 2.0
        if P_flash <= P_out:
            raise ErroProjeto("vazão alta demais para o capilar (entrada bifásica)")

    P = P_flash
    x, v, s, mu, T = _estado_hem(fl, P, h0, G, p.modelo_viscosidade)
    L = L_liq
    dP = (P_flash - P_out) / p.n_passos
    tol = max(1.0, 1e-7 * P_flash)
    blocado = False
    if guardar_perfil:
        for k, val in zip(("L", "P", "T", "x", "v", "s"), (L, P, T, x, v, s)):
            perfil[k].append(val)
    while True:
        P2 = max(P - dP, P_out)
        x2, v2, s2, mu2, T2 = _estado_hem(fl, P2, h0, G, p.modelo_viscosidade)
        num = (P - P2) - G * G * (v2 - v)
        if num <= 0.0 or s2 < s - 1e-9:
            if dP <= tol:
                blocado = True
                break
            dP *= 0.25
            continue
        v_m = 0.5 * (v + v2)
        f = fator_atrito_churchill(G * D / (0.5 * (mu + mu2)), eD)
        L += 2.0 * D * num / (f * G * G * v_m)
        P, x, v, s, mu, T = P2, x2, v2, s2, mu2, T2
        if guardar_perfil:
            for k, val in zip(("L", "P", "T", "x", "v", "s"), (L, P, T, x, v, s)):
                perfil[k].append(val)
        if P <= P_out * (1.0 + 1e-12):
            break
    return ResultadoCapilar(D, m, G, L, L_liq, L - L_liq, blocado, P, x, T, P_flash, perfil)


def vazao_capilar(fl: Fluido, D: float, L: float, P_in: float, h_in: float, P_out: float,
                  p: ParametrosCapilar) -> float:
    """Vazão mássica [kg/s] de um capilar dado (D, L) — problema inverso, por bissecção de Brent."""
    def f(m):
        try:
            return comprimento_capilar(fl, m, D, P_in, h_in, P_out, p).L - L
        except ErroProjeto:
            return -L
    lo, hi = 1e-6, 1e-4
    while f(hi) > 0:
        lo, hi = hi, hi * 2.0
        if hi > 1.0:
            raise ErroProjeto("não foi possível delimitar a vazão do capilar")
    while f(lo) < 0:
        lo /= 2.0
    return brentq(f, lo, hi, xtol=1e-9, rtol=1e-7)


@dataclass
class SelecaoCapilar:
    escolhido: ResultadoCapilar
    candidatos: list
    sensibilidade: dict
    avisos: list


def dimensionar_capilar(fl: Fluido, m: float, P_in: float, h_in: float, P_out: float,
                        p: ParametrosCapilar) -> SelecaoCapilar:
    candidatos, av = [], []
    for D in p.diametros():
        try:
            candidatos.append(comprimento_capilar(fl, m, D, P_in, h_in, P_out, p))
        except ErroProjeto:
            continue
    if not candidatos:
        raise ErroProjeto("nenhum diâmetro da série consegue passar a vazão pedida")
    validos = [c for c in candidatos if p.L_min <= c.L <= p.L_max]
    if validos:
        esc = min(validos, key=lambda c: abs(c.L - p.L_alvo))
    else:
        esc = min(candidatos, key=lambda c: abs(math.log(c.L / p.L_alvo)))
        av.append(f"nenhum diâmetro dá comprimento entre {p.L_min} e {p.L_max} m; escolhido o mais próximo "
                  f"(D = {esc.D * 1e3:.3f} mm, L = {esc.L:.2f} m)")
    esc = comprimento_capilar(fl, m, esc.D, P_in, h_in, P_out, p, guardar_perfil=True)
    tol = p.tolerancia_diametro_mm * 1e-3
    sens = {}
    for nome, Dx in (("D_menos_tol", esc.D - tol), ("D_mais_tol", esc.D + tol)):
        try:
            sens[nome] = comprimento_capilar(fl, m, Dx, P_in, h_in, P_out, p).L
        except ErroProjeto:
            sens[nome] = float("nan")
    m_menos = vazao_capilar(fl, esc.D - tol, esc.L, P_in, h_in, P_out, p)
    m_mais = vazao_capilar(fl, esc.D + tol, esc.L, P_in, h_in, P_out, p)
    sens["vazao_rel_D_menos_tol"] = m_menos / m - 1.0
    sens["vazao_rel_D_mais_tol"] = m_mais / m - 1.0
    if esc.blocado:
        av.append(f"escoamento blocado na saída do capilar (P_crit = {esc.P_saida / 1e5:.3f} bar > "
                  f"P_evap = {P_out / 1e5:.3f} bar): vazão insensível à pressão do evaporador.")
    return SelecaoCapilar(esc, candidatos, sens, av)
