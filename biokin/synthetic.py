"""Geração de dados sintéticos com mecanismo verdadeiro conhecido.

Serve a dois propósitos, e é importante não confundi-los com um resultado
experimental:

1. **Validar o próprio pipeline.** Se a varredura não recupera o mecanismo
   que gerou os dados, o problema é do código ou do planejamento
   experimental — não adianta aplicá-lo a dados reais.
2. **Dimensionar o esforço experimental.** Variando ruído, número de
   pontos e faixa de condições, descobre-se *antes da bancada* quantos
   ensaios e que precisão analítica são necessários para separar os
   mecanismos candidatos.

Os valores por omissão produzem conversões e perfis compatíveis com
metanólise de óleo vegetal sobre catalisador básico sólido, mas são
inventados: não devem ser citados como parâmetros de nenhum sistema real.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .data import Dataset, Experiment
from .library import er_methoxide
from .lhhw import derive_rate_law
from .network import KineticNetwork, build_network
from .parameters import Parameterization
from .reactor import MonolithOperation, concentration_vector
from .species import FLUID_SPECIES
from .transport import MonolithGeometry

#: Espécies tipicamente quantificadas por CG (EN 14105). O metanol, em
#: excesso, raramente é titulado — fica como não medido.
DEFAULT_MEASURED: tuple[str, ...] = ("TG", "DG", "MG", "E", "G")

#: Mecanismo verdadeiro: Eley-Rideal via metóxido, inibição por glicerol,
#: reação superficial determinante.
TRUE_MODEL_ID = "ER-M[G]|RDS=sr"

#: Parâmetros verdadeiros em T_ref = 333,15 K.
TRUE_VALUES: dict[str, float] = {
    "k_1": 1.8e-3,
    "k_2": 4.5e-3,
    "k_3": 9.0e-3,
    "Keq_1": 3.0,
    "Keq_2": 2.0,
    "Keq_3": 5.0,
    "K_ads_M": 0.35,
    "K_ads_G": 4.0,
}

#: Energias verdadeiras [kJ/mol]: Ea para k, ΔH para K.
TRUE_ENERGIES: dict[str, float] = {
    "k_1": 52.0,
    "k_2": 46.0,
    "k_3": 41.0,
    "Keq_1": -8.0,
    "Keq_2": -6.0,
    "Keq_3": -10.0,
    "K_ads_M": -25.0,
    "K_ads_G": -45.0,
}

TRUE_T_REF = 333.15


def true_network() -> KineticNetwork:
    """Rede cinética do mecanismo verdadeiro."""
    mech = er_methoxide(("G",))
    idx = [i for i, s in enumerate(mech.steps) if s.label == "sr"][0]
    return build_network(derive_rate_law(mech, idx))


def true_parameterization(non_isothermal: bool = True) -> Parameterization:
    net = true_network()
    par = Parameterization.for_names(net.param_names, TRUE_T_REF, non_isothermal)
    for name in net.param_names:
        par.update(
            name, value=TRUE_VALUES[name], energy_kJ=TRUE_ENERGIES[name]
        )
    return par


# ----------------------------------------------------------------------
@dataclass
class Condition:
    """Uma condição experimental a simular."""

    label: str
    T_K: float
    molar_ratio: float  # metanol : triglicerídeo
    C_TG0: float = 0.9
    C_G0: float = 0.0  # glicerol adicionado à alimentação
    C_E0: float = 0.0  # éster adicionado à alimentação
    reactor: str = "batch"
    catalyst_g_L: float = 10.0
    times_min: np.ndarray = field(default_factory=lambda: np.array([]))
    velocity_m_s: float = 0.01
    geometry: MonolithGeometry | None = None

    def initial(self) -> np.ndarray:
        """Composição de alimentação.

        Glicerol ou éster adicionados de saída (``C_G0``, ``C_E0``) são o
        recurso que quebra a colinearidade entre produtos: numa corrida
        que parte de óleo puro, ``C_G`` e ``C_E`` crescem juntos e suas
        contribuições ao denominador não podem ser separadas.
        """
        return concentration_vector(
            {
                "TG": self.C_TG0,
                "M": self.molar_ratio * self.C_TG0,
                "G": self.C_G0,
                "E": self.C_E0,
            }
        )


def default_design(include_monolith: bool = True) -> list[Condition]:
    """Planejamento típico de um estudo cinético de bancada.

    Três temperaturas e três razões molares em batelada — o mínimo para
    separar dependência térmica de dependência de composição — mais
    corridas em monolito variando a velocidade, que é o que muda o tempo
    espacial sem mudar a composição de alimentação.
    """
    t_batch = np.array([0, 5, 10, 20, 30, 45, 60, 90, 120], dtype=float)
    conds: list[Condition] = []
    for T in (323.15, 333.15, 343.15):
        for ratio in (6.0, 9.0, 12.0):
            conds.append(
                Condition(
                    label=f"B-T{T - 273.15:.0f}-R{ratio:.0f}",
                    T_K=T,
                    molar_ratio=ratio,
                    times_min=t_batch,
                    catalyst_g_L=10.0,
                )
            )
    if include_monolith:
        geom = MonolithGeometry(length_m=0.30)
        for T in (333.15, 343.15):
            for u in (0.002, 0.005, 0.010):
                op_tau = geom.length_m / u / 60.0
                conds.append(
                    Condition(
                        label=f"M-T{T - 273.15:.0f}-u{u * 1e3:.0f}",
                        T_K=T,
                        molar_ratio=9.0,
                        reactor="monolith",
                        times_min=np.linspace(0.0, op_tau, 7),
                        velocity_m_s=u,
                        geometry=geom,
                    )
                )
    return conds


# ----------------------------------------------------------------------
def generate_dataset(
    conditions: list[Condition] | None = None,
    net: KineticNetwork | None = None,
    par: Parameterization | None = None,
    x: np.ndarray | None = None,
    relative_noise: float = 0.03,
    absolute_noise: float = 2e-3,
    measured: tuple[str, ...] = DEFAULT_MEASURED,
    monolith_mode: str = "ideal",
    seed: int = 20260827,
    name: str = "sintético",
) -> Dataset:
    """Simula o planejamento e adiciona ruído gaussiano heterocedástico.

    ``relative_noise`` representa a repetibilidade da cromatografia;
    ``absolute_noise`` é o piso de detecção, que domina nas espécies
    minoritárias. Essa combinação é o que se observa na prática e é bem
    mais realista que ruído puramente proporcional.
    """
    rng = np.random.default_rng(seed)
    conditions = conditions or default_design()
    net = net or true_network()
    par = par or true_parameterization()
    x = par.pack() if x is None else x

    idx_measured = [FLUID_SPECIES.index(s) for s in measured]
    experiments: list[Experiment] = []
    for cond in conditions:
        values = par.values_at(x, cond.T_K)
        pvec = np.array([values[n] for n in net.param_names])
        C0 = cond.initial()
        t = np.asarray(cond.times_min, dtype=float)

        if cond.reactor == "monolith":
            op = MonolithOperation(
                velocity_m_s=cond.velocity_m_s,
                geometry=cond.geometry or MonolithGeometry(),
            )
            from .reactor import simulate_monolith

            prof = simulate_monolith(net, pvec, C0, t, op, mode=monolith_mode)
            cat, operation = op.catalyst_g_L, op
        else:
            from .reactor import simulate_batch

            prof = simulate_batch(net, pvec, C0, t, cond.catalyst_g_L)
            cat, operation = cond.catalyst_g_L, None

        Y = np.full_like(prof, np.nan)
        for i in idx_measured:
            sigma = np.sqrt(
                (relative_noise * prof[:, i]) ** 2 + absolute_noise**2
            )
            Y[:, i] = np.maximum(prof[:, i] + rng.normal(0.0, sigma), 0.0)

        experiments.append(
            Experiment(
                label=cond.label,
                T_K=cond.T_K,
                C0=C0,
                t=t,
                Y=Y,
                reactor=cond.reactor,
                catalyst_g_L=cat,
                operation=operation,
            )
        )
    return Dataset(experiments, name=name)
