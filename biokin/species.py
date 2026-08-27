"""Espécies químicas e estequiometria da transesterificação.

Convenção de nomes usada em todo o pacote:

    TG  triglicerídeo
    DG  diglicerídeo
    MG  monoglicerídeo
    M   metanol
    E   éster metílico (FAME / biodiesel)
    G   glicerol

Espécies de superfície carregam ``*``:  ``M*``, ``TG*`` ...
O sítio vago é ``*`` (mono-sítio) ou ``*1``/``*2`` (dual-sítio).
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Espécies fluidas do sistema, em ordem canônica.
FLUID_SPECIES: tuple[str, ...] = ("TG", "DG", "MG", "M", "E", "G")

#: Nomes legíveis (relatórios, gráficos).
SPECIES_LABEL: dict[str, str] = {
    "TG": "triglicerídeo",
    "DG": "diglicerídeo",
    "MG": "monoglicerídeo",
    "M": "metanol",
    "E": "éster metílico (FAME)",
    "G": "glicerol",
}


@dataclass(frozen=True)
class Reaction:
    """Uma das três etapas consecutivas da transesterificação."""

    name: str
    acyl_reactant: str  # TG, DG ou MG
    acyl_product: str  # DG, MG ou G
    stoich: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stoich:
            object.__setattr__(
                self,
                "stoich",
                {self.acyl_reactant: -1, "M": -1, self.acyl_product: +1, "E": +1},
            )


#: TG + M <-> DG + E ; DG + M <-> MG + E ; MG + M <-> G + E
REACTIONS: tuple[Reaction, ...] = (
    Reaction("R1", "TG", "DG"),
    Reaction("R2", "DG", "MG"),
    Reaction("R3", "MG", "G"),
)

#: Matriz estequiométrica nu[especie][reacao].
def stoich_matrix() -> dict[str, list[int]]:
    """Retorna ``{especie: [nu_R1, nu_R2, nu_R3]}``."""
    return {sp: [rx.stoich.get(sp, 0) for rx in REACTIONS] for sp in FLUID_SPECIES}


def overall_stoich() -> dict[str, int]:
    """Estequiometria global TG + 3 M <-> G + 3 E."""
    total: dict[str, int] = {}
    for rx in REACTIONS:
        for sp, nu in rx.stoich.items():
            total[sp] = total.get(sp, 0) + nu
    return {sp: nu for sp, nu in total.items() if nu != 0}


def is_surface(species: str) -> bool:
    """``True`` se a espécie for de superfície (contém ``*``)."""
    return "*" in species


def site_of(species: str) -> str:
    """Tipo de sítio ao qual a espécie de superfície pertence.

    ``'M*'`` -> ``'*'`` ; ``'TG*2'`` -> ``'*2'`` ; ``'*'`` -> ``'*'``.
    """
    if not is_surface(species):
        raise ValueError(f"{species!r} não é espécie de superfície")
    return species[species.index("*"):]


def adsorbate_of(species: str) -> str:
    """Parte fluida do nome de um adsorbato: ``'TG*2'`` -> ``'TG'``.

    Retorna string vazia para o sítio vago.
    """
    return species[: species.index("*")]
