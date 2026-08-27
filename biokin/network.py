"""Rede cinética das três transesterificações consecutivas.

A lei genérica ``A + M <-> B + E`` é instanciada três vezes:

    R1: TG + M <-> DG + E
    R2: DG + M <-> MG + E
    R3: MG + M <-> G  + E

Constantes de adsorção são **partilhadas**: ``K_ads_M`` é a mesma nas três
reações, porque é a mesma molécula no mesmo sítio. Só a constante de
velocidade, a constante da reação superficial e a constante de equilíbrio
recebem índice de reação. Sem essa partilha, o modelo LHHW completo teria
três denominadores independentes e nenhum conjunto realista de dados
conseguiria identificá-lo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .lhhw import RateLaw
from .species import FLUID_SPECIES, REACTIONS, stoich_matrix

#: Mapeamento genérico -> concreto para cada reação da série.
SPECIES_MAPS: tuple[dict[str, str], ...] = (
    {"A": "TG", "B": "DG"},
    {"A": "DG", "B": "MG"},
    {"A": "MG", "B": "G"},
)

#: Parâmetros partilhados entre as três reações (prefixos).
SHARED_PREFIXES: tuple[str, ...] = ("K_ads",)


def _is_shared(name: str) -> bool:
    return name.startswith(SHARED_PREFIXES)


@dataclass
class KineticNetwork:
    """Rede de três reações instanciada a partir de uma lei genérica."""

    model_id: str
    family: str
    rds_label: str
    laws: tuple[RateLaw, ...]
    param_names: tuple[str, ...]
    notes: str = ""
    species: tuple[str, ...] = FLUID_SPECIES
    nu: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))

    _funcs: list = field(default_factory=list, repr=False)
    _sp_idx: list = field(default_factory=list, repr=False)
    _pa_idx: list = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        sm = stoich_matrix()
        self.nu = np.array([sm[s] for s in self.species], dtype=float)  # (n_sp, 3)
        sp_pos = {s: i for i, s in enumerate(self.species)}
        pa_pos = {p: i for i, p in enumerate(self.param_names)}
        self._funcs, self._sp_idx, self._pa_idx = [], [], []
        for law in self.laws:
            self._funcs.append(law.lambdify())
            self._sp_idx.append(np.array([sp_pos[s] for s in law.species_names], dtype=int))
            self._pa_idx.append(np.array([pa_pos[p] for p in law.param_names], dtype=int))

    # ------------------------------------------------------------------
    @property
    def n_params(self) -> int:
        return len(self.param_names)

    def rates(self, C: np.ndarray, pvec: np.ndarray) -> np.ndarray:
        """Velocidades das três reações [mol/(g_cat·min)].

        ``C`` é o vetor de concentrações na ordem de :attr:`species`.
        Valores negativos, que a integração numérica pode produzir perto do
        zero, são truncados: são artefato do integrador, não química.
        """
        Cc = np.maximum(C, 0.0)
        out = np.empty(len(self.laws))
        for j, f in enumerate(self._funcs):
            args = [*Cc[self._sp_idx[j]], *pvec[self._pa_idx[j]]]
            out[j] = f(*args)
        return out

    def rhs(self, C: np.ndarray, pvec: np.ndarray) -> np.ndarray:
        """``dC/dt`` por unidade de massa de catalisador."""
        return self.nu @ self.rates(C, pvec)

    def rates_batch(self, Cs: np.ndarray, pvec: np.ndarray) -> np.ndarray:
        """Velocidades para uma matriz ``(n_pontos, n_espécies)``."""
        Cc = np.maximum(np.atleast_2d(Cs), 0.0)
        out = np.empty((Cc.shape[0], len(self.laws)))
        for j, f in enumerate(self._funcs):
            args = [*Cc[:, self._sp_idx[j]].T, *pvec[self._pa_idx[j]]]
            out[:, j] = np.broadcast_to(np.asarray(f(*args), dtype=float), (Cc.shape[0],))
        return out

    def describe(self) -> str:
        lines = [f"{self.model_id}  [{self.family}]"]
        if self.notes:
            lines.append(f"  {self.notes}")
        lines.append(f"  parâmetros ({self.n_params}): {', '.join(self.param_names)}")
        for rx, law in zip(REACTIONS, self.laws):
            lines.append(f"  {rx.name}: {law.pretty()}")
        return "\n".join(lines)


def build_network(law: RateLaw) -> KineticNetwork:
    """Instancia a lei genérica para as três reações consecutivas."""
    laws: list[RateLaw] = []
    for j, mapping in enumerate(SPECIES_MAPS, start=1):
        inst = law.substitute_species(mapping)
        keep = [p for p in inst.param_names if _is_shared(p)]
        laws.append(inst.rename_parameters(f"_{j}", keep=keep))

    names: list[str] = []
    for inst in laws:
        for p in inst.param_names:
            if p not in names:
                names.append(p)
    return KineticNetwork(
        model_id=law.model_id,
        family=law.family,
        rds_label=law.rds_label,
        laws=tuple(laws),
        param_names=tuple(sorted(names)),
        notes=law.notes,
    )
