"""Modelos de reator: batelada e monolito de fluxo contínuo.

O monolito é tratado como canais paralelos idênticos em escoamento
pistonado, com o catalisador no washcoat da parede. Três níveis de
descrição, selecionáveis por ``mode``:

``ideal``     sem resistências de transporte — a cinética observada é a
              intrínseca. É o modo usado na regressão quando os critérios
              de Weisz-Prater/Mears autorizam.

``film``      resolve a concentração na superfície do washcoat a partir do
              balanço no filme externo. Custa uma solução não linear por
              ponto de integração.

``full``      filme externo mais fator de efetividade do washcoat. É o modo
              honesto quando os critérios reprovam, e o único em que faz
              sentido regredir parâmetros *intrínsecos* a partir de dados
              disfarçados por difusão.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root

from .network import KineticNetwork
from .species import FLUID_SPECIES
from .transport import (
    FluidProperties,
    MonolithGeometry,
    effective_diffusivity,
    effectiveness_factor,
    generalized_thiele,
    mass_transfer_coefficient,
)

#: Reagente-chave de cada uma das três reações consecutivas.
KEY_REACTANTS: tuple[str, ...] = ("TG", "DG", "MG")


class IntegrationFailure(RuntimeError):
    """A integração da rede não convergiu para os parâmetros dados."""


def concentration_vector(C0: dict[str, float]) -> np.ndarray:
    """Dicionário de concentrações -> vetor na ordem canônica."""
    return np.array([float(C0.get(s, 0.0)) for s in FLUID_SPECIES])


# ----------------------------------------------------------------------
# batelada
# ----------------------------------------------------------------------
def simulate_batch(
    net: KineticNetwork,
    pvec: np.ndarray,
    C0: np.ndarray,
    t_eval: np.ndarray,
    catalyst_g_L: float,
    rtol: float = 1e-8,
    atol: float = 1e-10,
) -> np.ndarray:
    """Reator de batelada perfeitamente agitado (ensaio de bancada).

    ``dC/dt = w_cat * nu · r(C)`` com ``w_cat`` em g_cat/L.
    Devolve matriz ``(len(t_eval), n_espécies)``.
    """

    def rhs(_t: float, C: np.ndarray) -> np.ndarray:
        return catalyst_g_L * net.rhs(C, pvec)

    t_eval = np.asarray(t_eval, dtype=float)
    sol = solve_ivp(
        rhs,
        (0.0, float(t_eval[-1])),
        C0,
        t_eval=t_eval,
        method="LSODA",
        rtol=rtol,
        atol=atol,
    )
    if not sol.success:
        raise IntegrationFailure(sol.message)
    return sol.y.T


# ----------------------------------------------------------------------
# monolito
# ----------------------------------------------------------------------
@dataclass
class MonolithOperation:
    """Condições de operação de um ensaio em monolito."""

    velocity_m_s: float = 0.01
    geometry: MonolithGeometry = None  # type: ignore[assignment]
    fluid: FluidProperties = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.geometry is None:
            self.geometry = MonolithGeometry()
        if self.fluid is None:
            self.fluid = FluidProperties()

    @property
    def catalyst_g_L(self) -> float:
        return self.geometry.catalyst_density_g_L

    @property
    def kc_av_per_min(self) -> float:
        kc = mass_transfer_coefficient(self.geometry, self.fluid, self.velocity_m_s)
        return kc * self.geometry.specific_surface_m2_m3 * 60.0

    @property
    def max_space_time_min(self) -> float:
        """Tempo espacial na saída do monolito [min]."""
        return self.geometry.length_m / self.velocity_m_s / 60.0


def _effectiveness_vector(
    net: KineticNetwork,
    C: np.ndarray,
    pvec: np.ndarray,
    op: MonolithOperation,
) -> np.ndarray:
    """Fator de efetividade de cada reação, pelo módulo de Thiele generalizado.

    A dependência da velocidade com o reagente-chave é varrida mantendo as
    demais concentrações no valor da superfície. É a aproximação usual: o
    metanol está em largo excesso e seu perfil dentro do washcoat é raso.
    """
    D_eff = effective_diffusivity(op.geometry, op.fluid)
    L = op.geometry.washcoat_thickness_m
    rho = op.geometry.washcoat_density_kg_m3
    sp_pos = {s: i for i, s in enumerate(net.species)}
    eta = np.ones(len(net.laws))
    for j, key in enumerate(KEY_REACTANTS):
        idx = sp_pos[key]

        def rate_of_C(c: float, _j: int = j, _idx: int = idx) -> float:
            Cx = C.copy()
            Cx[_idx] = c
            return float(net.rates(Cx, pvec)[_j])

        phi = generalized_thiele(rate_of_C, float(C[idx]), L, D_eff, rho)
        eta[j] = effectiveness_factor(phi)
    return eta


def _surface_concentrations(
    net: KineticNetwork,
    C_bulk: np.ndarray,
    pvec: np.ndarray,
    op: MonolithOperation,
    use_effectiveness: bool,
    guess: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Resolve o balanço no filme externo: ``k_c a_v (C_b - C_s) = w · nu·r(C_s)``."""
    kca = op.kc_av_per_min
    w = op.catalyst_g_L

    def residual(Cs: np.ndarray) -> np.ndarray:
        Cs = np.maximum(Cs, 0.0)
        eta = (
            _effectiveness_vector(net, Cs, pvec, op)
            if use_effectiveness
            else np.ones(len(net.laws))
        )
        return kca * (C_bulk - Cs) - w * (net.nu @ (eta * net.rates(Cs, pvec)))

    x0 = C_bulk if guess is None else guess
    sol = root(residual, x0, method="hybr", tol=1e-10)
    Cs = np.maximum(sol.x, 0.0) if sol.success else np.maximum(C_bulk, 0.0)
    eta = (
        _effectiveness_vector(net, Cs, pvec, op)
        if use_effectiveness
        else np.ones(len(net.laws))
    )
    return Cs, eta


def simulate_monolith(
    net: KineticNetwork,
    pvec: np.ndarray,
    C0: np.ndarray,
    tau_eval: np.ndarray,
    op: MonolithOperation | None = None,
    mode: str = "ideal",
    rtol: float = 1e-8,
    atol: float = 1e-10,
) -> np.ndarray:
    """Monolito em escoamento pistonado.

    ``tau_eval`` é o tempo espacial ``z/u`` em minutos. Devolve as
    concentrações de seio ``(len(tau_eval), n_espécies)``.
    """
    if mode not in ("ideal", "film", "full"):
        raise ValueError(f"mode inválido: {mode!r}")
    op = op or MonolithOperation()
    w = op.catalyst_g_L

    if mode == "ideal":

        def rhs(_t: float, C: np.ndarray) -> np.ndarray:
            return w * net.rhs(C, pvec)

    else:
        use_eta = mode == "full"
        cache: dict[str, np.ndarray] = {}

        def rhs(_t: float, C: np.ndarray) -> np.ndarray:
            Cs, eta = _surface_concentrations(
                net, np.maximum(C, 0.0), pvec, op, use_eta, cache.get("Cs")
            )
            cache["Cs"] = Cs
            return w * (net.nu @ (eta * net.rates(Cs, pvec)))

    tau_eval = np.asarray(tau_eval, dtype=float)
    sol = solve_ivp(
        rhs,
        (0.0, float(tau_eval[-1])),
        C0,
        t_eval=tau_eval,
        method="LSODA",
        rtol=rtol,
        atol=atol,
    )
    if not sol.success:
        raise IntegrationFailure(sol.message)
    return sol.y.T


def conversion(profile: np.ndarray, species: str = "TG") -> np.ndarray:
    """Conversão fracionária de uma espécie ao longo do perfil."""
    i = FLUID_SPECIES.index(species)
    C0 = profile[0, i]
    return (C0 - profile[:, i]) / C0 if C0 > 0 else np.zeros(len(profile))


def fame_yield(profile: np.ndarray) -> np.ndarray:
    """Rendimento em éster metílico, base 3 mol de éster por mol de TG."""
    iE = FLUID_SPECIES.index("E")
    iTG = FLUID_SPECIES.index("TG")
    C_TG0 = profile[0, iTG]
    return profile[:, iE] / (3.0 * C_TG0) if C_TG0 > 0 else np.zeros(len(profile))
