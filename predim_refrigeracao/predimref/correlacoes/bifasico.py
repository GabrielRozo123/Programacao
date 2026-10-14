"""Escoamento bifásico em tubos horizontais lisos: condensação, ebulição, atrito, fração de vazio.

Convenções: G fluxo mássico total [kg/m²s], x título, D diâmetro interno [m],
``sat`` um objeto ``Saturacao`` na pressão local.
"""
from __future__ import annotations

import math

from ..constantes import G as g
from .monofasico import fator_atrito_blasius_laminar, nusselt_gnielinski

_X_MIN, _X_MAX = 1e-4, 1.0 - 1e-4


def _clip_x(x: float) -> float:
    return min(max(x, _X_MIN), _X_MAX)


# ============================================================================ condensação
def _shah_hI_hNu(G: float, x: float, D: float, sat) -> tuple[float, float, float, float]:
    """Termos comuns às correlações de Shah: h_I (eq. 2 de Shah 2022), h_Nu, Z e J_g.

    h_I  = h_LT [(1−x)^0,8 + 3,8 x^0,76 (1−x)^0,04 / p_r^0,38] (μ_l/14μ_v)^n ,  n = 0,0058 + 0,557 p_r
           (h_LT: Dittus-Boelter com todo o fluxo como líquido, Re_LT = G D/μ_l)
    h_Nu = 1,32 Re_LS^(−1/3) [ρ_l(ρ_l−ρ_v) g k_l³ / μ_l²]^(1/3) ,  Re_LS = G (1−x) D / μ_l
    Z = (1/x − 1)^0,8 p_r^0,4 ;  J_g = x G / [g D ρ_v (ρ_l − ρ_v)]^0,5
    """
    pr = sat.pr
    Re_LT = G * D / sat.mul
    h_LT = 0.023 * Re_LT ** 0.8 * sat.Prl ** 0.4 * sat.kl / D
    n = 0.0058 + 0.557 * pr
    h_I = h_LT * (sat.mul / (14.0 * sat.muv)) ** n * (
        (1.0 - x) ** 0.8 + 3.8 * x ** 0.76 * (1.0 - x) ** 0.04 / pr ** 0.38)
    Re_LS = G * (1.0 - x) * D / sat.mul
    h_Nu = 1.32 * Re_LS ** (-1.0 / 3.0) * (
        sat.rhol * (sat.rhol - sat.rhov) * g * sat.kl ** 3 / sat.mul ** 2) ** (1.0 / 3.0)
    Z = (1.0 / x - 1.0) ** 0.8 * pr ** 0.4
    Jg = x * G / math.sqrt(g * D * sat.rhov * (sat.rhol - sat.rhov))
    return h_I, h_Nu, Z, Jg


def condensacao_shah_2013(G: float, x: float, D: float, sat) -> tuple[float, str]:
    """Condensação em tubo horizontal, Shah (2013), ASHRAE Trans. 119(2), com os regimes:
    Regime I   : J_g ≥ 0,98 (Z + 0,263)^−0,62           → h = h_I
    Regime III : J_g ≤ 0,95 (1,254 + 2,27 Z^1,249)^−1     → h = h_Nu   (escoamento estratificado)
    Regime II  : demais casos                           → h = h_I + h_Nu
    Shah (2022), Int. J. Heat Mass Transfer 194:123069, recomenda esta forma para
    hidrocarbonetos em qualquer orientação (base de 2931 pontos, G de 1,2 a 1360 kg/m²s).
    Retorna (h [W/m²K], regime)."""
    x = _clip_x(x)
    h_I, h_Nu, Z, Jg = _shah_hI_hNu(G, x, D, sat)
    if Jg >= 0.98 * (Z + 0.263) ** -0.62:
        return h_I, "I"
    if Jg <= 0.95 / (1.254 + 2.27 * Z ** 1.249):
        return h_Nu, "III"
    return h_I + h_Nu, "II"


def condensacao_shah_2022(G: float, x: float, D: float, sat, hidrocarboneto: bool) -> tuple[float, str]:
    """Correlação melhorada de Shah (2022), Int. J. Heat Mass Transfer 194:123069, tubo horizontal.

    * hidrocarbonetos, ou Re_LT < 100: Shah (2013) (``condensacao_shah_2013``);
    * demais fluidos: We_GT = G² D/(ρ_v σ), Fr_LT = G²/(ρ_l² g D)
        Regime I  se We_GT > 100, Fr_LT > 0,026 e J_g ≥ 0,98 (Z + 0,263)^−0,62
        Regime III se Fr_LT > 0,026 e J_g ≤ 0,95 (1,254 + 2,27 Z^1,249)^−1
        Regime II nos demais casos;
      h_I pela eq. 2 se D > 6 mm, ou pela forma de Cavallini et al. (2006) se D ≤ 6 mm:
        h_I = h_LT [1 + 1,128 x^0,817 (ρ_l/ρ_v)^0,3685 (μ_l/μ_v)^0,2363 (1 − μ_v/μ_l)^2,144 Pr_l^−0,1]
    """
    x = _clip_x(x)
    Re_LT = G * D / sat.mul
    if hidrocarboneto or Re_LT < 100.0:
        return condensacao_shah_2013(G, x, D, sat)
    h_I, h_Nu, Z, Jg = _shah_hI_hNu(G, x, D, sat)
    if D <= 6.0e-3:
        h_LT = 0.023 * Re_LT ** 0.8 * sat.Prl ** 0.4 * sat.kl / D
        h_I = h_LT * (1.0 + 1.128 * x ** 0.817 * (sat.rhol / sat.rhov) ** 0.3685
                      * (sat.mul / sat.muv) ** 0.2363 * (1.0 - sat.muv / sat.mul) ** 2.144 * sat.Prl ** -0.1)
    We = G * G * D / (sat.rhov * sat.sigma)
    Fr = G * G / (sat.rhol ** 2 * g * D)
    if We > 100.0 and Fr > 0.026 and Jg >= 0.98 * (Z + 0.263) ** -0.62:
        return h_I, "I"
    if Fr > 0.026 and Jg <= 0.95 / (1.254 + 2.27 * Z ** 1.249):
        return h_Nu, "III"
    return h_I + h_Nu, "II"


def condensacao_shah_2009(G: float, x: float, D: float, sat) -> tuple[float, str]:
    """Shah (2009), HVAC&R Research 15(5):889-913, tubo horizontal: só regimes I e II, com o
    regime II recomendado pelo próprio autor apenas para Re_GT > 35 000 (mantida para referência)."""
    x = _clip_x(x)
    h_I, h_Nu, Z, Jg = _shah_hI_hNu(G, x, D, sat)
    if Jg >= 0.98 * (Z + 0.263) ** -0.62:
        return h_I, "I"
    return h_I + h_Nu, "II"


def condensacao_shah_1979(G: float, x: float, D: float, sat) -> tuple[float, str]:
    """Shah (1979), Int. J. Heat Mass Transfer 22:547-556 (referência clássica; o autor a
    recomendou só para Re_LT > 350, Re_GT > 35 000 e velocidade do vapor > 3 m/s)."""
    x = _clip_x(x)
    Re_LT = G * D / sat.mul
    h_LT = 0.023 * Re_LT ** 0.8 * sat.Prl ** 0.4 * sat.kl / D
    return h_LT * ((1 - x) ** 0.8 + 3.8 * x ** 0.76 * (1 - x) ** 0.04 / sat.pr ** 0.38), "-"


def condensacao_chato_1962(D: float, sat, dT_parede: float) -> tuple[float, str]:
    """Condensação estratificada em tubo horizontal a baixa vazão (Re_GT < 35 000),
    Chato (1962), ASHRAE J. 4(2):52-60 (forma de Nusselt com constante 0,555):
        h = 0,555 [ρ_l (ρ_l − ρ_v) g k_l³ h'_lv / (μ_l D ΔT_p)]^0,25 ,  h'_lv = h_lv + 3/8 c_p,l ΔT_p
    ΔT_p = T_sat − T_parede (calculado iterativamente a partir do fluxo de calor)."""
    dT = max(dT_parede, 0.05)
    hlv = sat.hlv + 0.375 * sat.cpl * dT
    return 0.555 * (sat.rhol * (sat.rhol - sat.rhov) * g * sat.kl ** 3 * hlv / (sat.mul * D * dT)) ** 0.25, "estratificado"


# ============================================================================ ebulição
def ebulicao_gungor_winterton_1987(G: float, x: float, D: float, q: float, sat) -> float:
    """Ebulição convectiva saturada, Gungor & Winterton (1987), Chem. Eng. Res. Des. 65:148-156.

    h = E·h_l ;  h_l = 0,023 Re_l^0,8 Pr_l^0,4 k_l/D com Re_l = G(1−x)D/μ_l
    E = 1 + 3000 Bo^0,86 + 1,12 [x/(1−x)]^0,75 (ρ_l/ρ_v)^0,41 ,  Bo = q/(G h_lv)
    Tubo horizontal com Fr_lo = G²/(ρ_l² g D) < 0,05: E ← E · Fr_lo^(0,1 − 2 Fr_lo)
    (correção de estratificação: parte superior do tubo seca em fluxos mássicos baixos).
    """
    x = _clip_x(x)
    Re_l = G * (1.0 - x) * D / sat.mul
    h_l = 0.023 * Re_l ** 0.8 * sat.Prl ** 0.4 * sat.kl / D
    Bo = max(q, 0.0) / (G * sat.hlv)
    E = 1.0 + 3000.0 * Bo ** 0.86 + 1.12 * (x / (1.0 - x)) ** 0.75 * (sat.rhol / sat.rhov) ** 0.41
    Fr = G * G / (sat.rhol ** 2 * g * D)
    if Fr < 0.05:
        E *= Fr ** (0.1 - 2.0 * Fr)
    return E * h_l


def ebulicao_nucleada_cooper(q: float, pr: float, M_kg_kmol: float, Rp_um: float = 1.0) -> float:
    """Ebulição nucleada em piscina, Cooper (1984), Adv. Heat Transfer 16:157-239.
    h = 55 p_r^(0,12 − 0,2 log10 Rp) (−log10 p_r)^−0,55 M^−0,5 q^0,67 (q em W/m², M em kg/kmol)."""
    return (55.0 * pr ** (0.12 - 0.2 * math.log10(Rp_um)) * (-math.log10(pr)) ** -0.55
            * M_kg_kmol ** -0.5 * max(q, 1.0) ** 0.67)


def ebulicao_liu_winterton_1991(G: float, x: float, D: float, q: float, sat, M_kg_kmol: float) -> float:
    """Liu & Winterton (1991), Int. J. Heat Mass Transfer 34(11):2759-2766.

    h² = (F h_lo)² + (S h_nb)² ; h_lo Dittus-Boelter com o fluxo total como líquido;
    F = [1 + x Pr_l (ρ_l/ρ_v − 1)]^0,35 ; S = [1 + 0,055 F^0,1 Re_lo^0,16]^−1 ; h_nb de Cooper.
    Horizontal com Fr_lo < 0,05: F ← F·Fr_lo^(0,1−2Fr_lo), S ← S·Fr_lo^0,5.
    """
    x = _clip_x(x)
    Re_lo = G * D / sat.mul
    h_lo = 0.023 * Re_lo ** 0.8 * sat.Prl ** 0.4 * sat.kl / D
    F = (1.0 + x * sat.Prl * (sat.rhol / sat.rhov - 1.0)) ** 0.35
    S = 1.0 / (1.0 + 0.055 * F ** 0.1 * Re_lo ** 0.16)
    Fr = G * G / (sat.rhol ** 2 * g * D)
    if Fr < 0.05:
        F *= Fr ** (0.1 - 2.0 * Fr)
        S *= Fr ** 0.5
    h_nb = ebulicao_nucleada_cooper(q, sat.pr, M_kg_kmol)
    return math.sqrt((F * h_lo) ** 2 + (S * h_nb) ** 2)


def h_vapor_saturado(G: float, D: float, sat) -> float:
    """Vapor monofásico com o fluxo total (limite x → 1), Gnielinski."""
    Re = G * D / sat.muv
    return nusselt_gnielinski(Re, sat.Prv) * sat.kv / D


def ebulicao_com_secagem(G, x, D, q, sat, M_kg_kmol, correlacao="gungor_winterton_1987", x_di=0.90):
    """Coeficiente de ebulição com tratamento de secagem de parede (dryout) para x > x_di:
    interpolação linear entre h(x_di) e o vapor saturado em x = 1, no espírito do modelo de
    névoa de Wojtan, Ursenbacher & Thome (2005), Int. J. Heat Mass Transfer 48:2970-2985.
    Sem isso as correlações de ebulição superestimam h perto de x = 1."""
    def h_tp(xx):
        if correlacao == "gungor_winterton_1987":
            return ebulicao_gungor_winterton_1987(G, xx, D, q, sat)
        if correlacao == "liu_winterton_1991":
            return ebulicao_liu_winterton_1991(G, xx, D, q, sat, M_kg_kmol)
        raise ValueError(f"correlação de ebulição desconhecida: {correlacao}")

    if x <= x_di:
        return h_tp(x)
    h_di = h_tp(x_di)
    h_v = h_vapor_saturado(G, D, sat)
    w = (min(x, 1.0) - x_di) / (1.0 - x_di)
    return h_di + w * (h_v - h_di)


# ============================================================================ atrito
def gradiente_atrito_msh(G: float, x: float, D: float, sat) -> float:
    """−dP/dz por atrito bifásico [Pa/m], Müller-Steinhagen & Heck (1986),
    Chem. Eng. Process. 20:297-308:
        (dP/dz) = Λ (1−x)^(1/3) + B x³ ,  Λ = A + 2(B − A) x
    A e B: gradientes só-líquido e só-vapor com o fluxo total (64/Re ou Blasius)."""
    x = min(max(x, 0.0), 1.0)
    Re_lo = G * D / sat.mul
    Re_vo = G * D / sat.muv
    A = fator_atrito_blasius_laminar(Re_lo) * G * G / (2.0 * sat.rhol * D)
    B = fator_atrito_blasius_laminar(Re_vo) * G * G / (2.0 * sat.rhov * D)
    lam = A + 2.0 * (B - A) * x
    return lam * (1.0 - x) ** (1.0 / 3.0) + B * x ** 3


def fracao_vazio_rouhani_axelsson(x: float, G: float, sat) -> float:
    """Fração de vazio, Rouhani & Axelsson (1970) na forma para tubos horizontais
    (Steiner 1993, VDI Heat Atlas), usada também por Wojtan et al. (2005):
    α = (x/ρ_v) {[1 + 0,12(1−x)](x/ρ_v + (1−x)/ρ_l) + 1,18(1−x)[gσ(ρ_l−ρ_v)]^0,25 / (G ρ_l^0,5)}^−1
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    sigma = sat.sigma if math.isfinite(sat.sigma) else 0.0
    termo = ((1.0 + 0.12 * (1.0 - x)) * (x / sat.rhov + (1.0 - x) / sat.rhol)
             + 1.18 * (1.0 - x) * (g * sigma * (sat.rhol - sat.rhov)) ** 0.25 / (G * sat.rhol ** 0.5))
    return (x / sat.rhov) / termo


def fracao_vazio_homogenea(x: float, sat) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return 1.0 / (1.0 + (1.0 - x) / x * sat.rhov / sat.rhol)


def fluxo_momento_especifico(x: float, alpha: float, sat) -> float:
    """[x²/(ρ_v α) + (1−x)²/(ρ_l (1−α))] — ΔP_acel = G² Δ(·) no modelo de fases separadas."""
    x = min(max(x, 0.0), 1.0)
    if x <= 0.0:
        return 1.0 / sat.rhol
    if x >= 1.0:
        return 1.0 / sat.rhov
    return x * x / (sat.rhov * alpha) + (1.0 - x) ** 2 / (sat.rhol * (1.0 - alpha))
