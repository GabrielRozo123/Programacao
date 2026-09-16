"""Arrasto e velocidade terminal de gotas em gas.

Este modulo existe por um motivo especifico: dar o numero analitico contra o qual
o rastreamento lagrangiano do Simcenter STAR-CCM+ tem que bater ANTES de qualquer
resultado de eficiencia ser levado a serio.

Se uma gota solta em gas parado nao reproduzir a velocidade terminal calculada
aqui, usando a MESMA lei de arrasto selecionada no solver, o problema e de
configuracao (unidades, gravidade, acoplamento, passo de tempo) e nao de fisica.

Convencao de unidades: SI em todo o modulo.
    d     [m]        diametro da gota
    rho   [kg/m3]    massa especifica
    mu    [Pa.s]     viscosidade dinamica do gas
    sigma [N/m]      tensao interfacial
    v     [m/s]      velocidade
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterable

from scipy.optimize import brentq

G = 9.80665  # aceleracao da gravidade padrao [m/s2]


# ---------------------------------------------------------------------------
# Leis de arrasto
# ---------------------------------------------------------------------------
# Os nomes abaixo espelham as opcoes do STAR-CCM+ em
#   Phase Model -> Lagrangian Phase -> Drag Force -> Drag Coefficient Method.
# Use aqui exatamente a mesma que voce marcou no solver.


def cd_stokes(Re: float) -> float:
    """Arrasto de Stokes. Valido so para Re << 1 (escoamento reptante)."""
    if Re <= 0.0:
        return math.inf
    return 24.0 / Re


def cd_schiller_naumann(Re: float) -> float:
    """Schiller-Naumann. E o padrao do STAR-CCM+ para particulas esfericas.

    Cd = 24/Re * (1 + 0.15 Re^0.687)   para Re <= 1000
    Cd = 0.44                          para Re >  1000
    """
    if Re <= 0.0:
        return math.inf
    if Re <= 1000.0:
        return (24.0 / Re) * (1.0 + 0.15 * Re**0.687)
    return 0.44


def cd_newton(Re: float) -> float:
    """Regime de Newton, Cd constante. Referencia de sanidade para Re alto."""
    return 0.44


LEIS_DE_ARRASTO: dict[str, Callable[[float], float]] = {
    "stokes": cd_stokes,
    "schiller-naumann": cd_schiller_naumann,
    "newton": cd_newton,
}


def regime_de_escoamento(Re: float) -> str:
    """Rotulo do regime, para o relatorio nao esconder qual faixa foi usada."""
    if Re < 0.1:
        return "Stokes (Re < 0,1)"
    if Re < 1.0:
        return "quase-Stokes (0,1 <= Re < 1)"
    if Re < 1000.0:
        return "intermediario / Allen (1 <= Re < 1000)"
    return "Newton (Re >= 1000)"


# ---------------------------------------------------------------------------
# Velocidade terminal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Terminal:
    """Resultado do balanco peso-empuxo-arrasto de uma gota isolada."""

    d: float          # diametro da gota [m]
    v_t: float        # velocidade terminal [m/s]
    Re: float         # Reynolds da particula [-]
    Cd: float         # coeficiente de arrasto [-]
    regime: str
    lei: str

    @property
    def d_um(self) -> float:
        return self.d * 1e6

    def __str__(self) -> str:
        return (
            f"d = {self.d_um:7.1f} um -> v_t = {self.v_t:7.4f} m/s "
            f"(Re = {self.Re:8.2f}, Cd = {self.Cd:7.3f}, {self.regime})"
        )


def velocidade_terminal(
    d: float,
    rho_g: float,
    rho_l: float,
    mu_g: float,
    lei: str = "schiller-naumann",
    g: float = G,
) -> Terminal:
    """Velocidade terminal de uma gota de liquido caindo em gas parado.

    Resolve o balanco de forcas

        (pi/6) d^3 (rho_l - rho_g) g  =  Cd (pi/8) d^2 rho_g v_t^2

    ou seja

        v_t = sqrt( 4 g d (rho_l - rho_g) / (3 Cd(Re) rho_g) ),  Re = rho_g v_t d / mu_g

    que e implicito em v_t porque Cd depende de Re. Resolvido por Brent sobre o
    residuo f(v) = v - v_calculado(v), que muda de sinal exatamente uma vez.

    Este e o caso de teste do STAR-CCM+: uma gota, gas parado, gravidade ligada,
    acoplamento de uma via. O valor assintotico do tracking tem que bater com o
    v_t retornado aqui dentro de ~1%.
    """
    if d <= 0.0:
        raise ValueError("diametro da gota deve ser positivo")
    if rho_l <= rho_g:
        raise ValueError("rho_l deve ser maior que rho_g (gota mais densa que o gas)")

    cd = LEIS_DE_ARRASTO[lei]
    delta_rho = rho_l - rho_g

    def v_calculado(v: float) -> float:
        Re = rho_g * v * d / mu_g
        return math.sqrt(4.0 * g * d * delta_rho / (3.0 * cd(Re) * rho_g))

    def residuo(v: float) -> float:
        return v - v_calculado(v)

    # Abaixo do limite de Stokes o residuo e negativo; muito acima ele e positivo.
    lo, hi = 1e-9, 1.0
    while residuo(hi) < 0.0 and hi < 1e4:
        hi *= 10.0
    if residuo(hi) < 0.0:  # pragma: no cover - fisicamente inalcancavel
        raise RuntimeError("nao foi possivel enquadrar a raiz da velocidade terminal")

    v_t = brentq(residuo, lo, hi, xtol=1e-12, rtol=1e-12, maxiter=200)
    Re = rho_g * v_t * d / mu_g
    return Terminal(d=d, v_t=v_t, Re=Re, Cd=cd(Re), regime=regime_de_escoamento(Re), lei=lei)


def velocidade_terminal_stokes(
    d: float, rho_g: float, rho_l: float, mu_g: float, g: float = G
) -> float:
    """Forma fechada de Stokes, v_t = g d^2 (rho_l - rho_g) / (18 mu_g).

    Util so como verificacao de limite: para gotas de 10-50 um em gas leve a
    baixa pressao ela coincide com a solucao iterativa; acima disso superestima.
    """
    return g * d**2 * (rho_l - rho_g) / (18.0 * mu_g)


def diametro_para_velocidade_terminal(
    v_alvo: float,
    rho_g: float,
    rho_l: float,
    mu_g: float,
    lei: str = "schiller-naumann",
    g: float = G,
) -> float:
    """Inverso de `velocidade_terminal`: qual gota tem v_t igual a `v_alvo`.

    E com esta funcao que se extrai o diametro de gota escondido dentro do fator
    K de Souders-Brown (ver souders_brown.diametro_de_gota_implicito).
    """
    if v_alvo <= 0.0:
        raise ValueError("velocidade alvo deve ser positiva")

    def residuo(log_d: float) -> float:
        d = math.exp(log_d)
        return velocidade_terminal(d, rho_g, rho_l, mu_g, lei=lei, g=g).v_t - v_alvo

    lo, hi = math.log(1e-8), math.log(5e-2)  # 0,01 um ate 50 mm
    if residuo(lo) > 0.0 or residuo(hi) < 0.0:
        raise ValueError(
            f"v_alvo = {v_alvo:.4g} m/s fora da faixa coberta por gotas de 0,01 um a 50 mm"
        )
    return math.exp(brentq(residuo, lo, hi, xtol=1e-12, rtol=1e-12, maxiter=200))


# ---------------------------------------------------------------------------
# Estabilidade da gota
# ---------------------------------------------------------------------------


def numero_de_weber(d: float, v_rel: float, rho_g: float, sigma: float) -> float:
    """We = rho_g v_rel^2 d / sigma. Razao inercia aerodinamica / tensao superficial."""
    return rho_g * v_rel**2 * d / sigma


def diametro_maximo_estavel(
    v_rel: float, rho_g: float, sigma: float, we_critico: float = 12.0
) -> float:
    """Maior gota que sobrevive a um campo com velocidade relativa `v_rel`.

    Acima do Weber critico a gota quebra. We_c ~ 12 e o valor classico para
    quebra em saco (bag breakup) de gota em corrente gasosa; a literatura
    reporta de 10 a 14 conforme o mecanismo. Confira o valor na referencia que
    voce for citar.

    Consequencia pratica para o CFD: nao adianta injetar gotas de 2000 um na
    boca do bocal se o cisalhamento do jato as quebra em 300 um. O limite
    superior da Rosin-Rammler deve respeitar este numero.
    """
    if v_rel <= 0.0:
        return math.inf
    return we_critico * sigma / (rho_g * v_rel**2)


def tabela_de_velocidades_terminais(
    diametros_um: Iterable[float],
    rho_g: float,
    rho_l: float,
    mu_g: float,
    lei: str = "schiller-naumann",
) -> list[Terminal]:
    """Tabela pronta para colar no caso de verificacao do STAR-CCM+."""
    return [
        velocidade_terminal(d_um * 1e-6, rho_g, rho_l, mu_g, lei=lei)
        for d_um in diametros_um
    ]
