"""Catálogo de mecanismos candidatos para transesterificação heterogênea.

As famílias cobrem o que a literatura de biodiesel efetivamente propõe
para catalisadores sólidos:

``ER-M``   Eley-Rideal via metóxido superficial: o metanol adsorve no
           sítio básico, o metóxido ataca o glicerídeo *em solução*.
           É o mecanismo mais citado para CaO, MgO e hidrotalcitas.

``ER-M2``  Idem, mas resolvendo o intermediário tetraédrico adsorvido em
           duas etapas (formação e colapso). Permite testar se a etapa
           lenta é o ataque nucleofílico ou a quebra do intermediário.

``ER-A``   Eley-Rideal com o glicerídeo adsorvido e o metanol atacando da
           solução — cenário típico de catálise ácida (zircônia sulfatada,
           resinas, carbonos sulfonados).

``LH1``    Langmuir-Hinshelwood mono-sítio: ambos adsorvidos no mesmo tipo
           de sítio; reação superficial entre espécies vizinhas.

``LH2``    Langmuir-Hinshelwood dual-sítio: metanol no sítio básico,
           glicerídeo no sítio ácido — pares ácido-base de óxidos mistos.

A cada família se combinam (i) a escolha da etapa determinante e (ii) o
conjunto de espécies que competem pelos sítios sem reagir. O produto
cartesiano dessas escolhas é o espaço de modelos varrido pelo pacote.

As reações são escritas de forma genérica ``A + M <-> B + E`` e depois
instanciadas para ``TG->DG``, ``DG->MG`` e ``MG->G``.
"""

from __future__ import annotations

from itertools import product

import sympy as sp

from .lhhw import KEQ, RATE_CONSTANT, RateLaw, conc_symbol, derive_all
from .mechanism import Mechanism, Step

#: Espécies que podem competir pelos sítios sem participar do ciclo.
INHIBITOR_CANDIDATES: tuple[str, ...] = ("G", "E", "M", "A")

#: Conjuntos de inibidores varridos por omissão.
DEFAULT_INHIBITION_SETS: tuple[tuple[str, ...], ...] = (
    (),
    ("G",),
    ("G", "E"),
)


def _spectator(species: str, site: str = "*") -> Step:
    return Step(
        label=f"ads_{species}",
        reactants={species: 1, site: 1},
        products={f"{species}{site}": 1},
        in_cycle=False,
        can_be_rds=False,
        description=f"adsorção competitiva de {species} (espectador)",
    )


def _with_spectators(
    steps: tuple[Step, ...], inhibitors: tuple[str, ...], site: str = "*"
) -> tuple[Step, ...]:
    """Acrescenta adsorção espectadora, ignorando espécies já no ciclo."""
    already = {
        sp_[: sp_.index("*")]
        for st in steps
        for sp_ in st.species()
        if "*" in sp_ and sp_ != site
    }
    extra = tuple(_spectator(x, site) for x in inhibitors if x not in already)
    return steps + extra


OVERALL = {"A": -1, "M": -1, "B": 1, "E": 1}


# ----------------------------------------------------------------------
# famílias
# ----------------------------------------------------------------------
def er_methoxide(inhibitors: tuple[str, ...] = ("G",)) -> Mechanism:
    """Eley-Rideal: metóxido adsorvido ataca glicerídeo em solução."""
    steps = (
        Step("ads_M", {"M": 1, "*": 1}, {"M*": 1}, description="M + * <-> metóxido"),
        Step(
            "sr",
            {"M*": 1, "A": 1},
            {"B": 1, "E": 1, "*": 1},
            description="ataque nucleofílico ao glicerídeo em solução",
        ),
    )
    return Mechanism(
        name=f"ER-M[{'+'.join(inhibitors) or 'sem inib.'}]",
        family="ER-M",
        steps=_with_spectators(steps, inhibitors),
        overall=OVERALL,
        notes="metóxido superficial ataca glicerídeo em solução (sítio básico)",
        references=("Dossin et al., Appl. Catal. B 61 (2005) 35",),
    )


def er_methoxide_tetrahedral(inhibitors: tuple[str, ...] = ("G",)) -> Mechanism:
    """Eley-Rideal com intermediário tetraédrico adsorvido explícito."""
    steps = (
        Step("ads_M", {"M": 1, "*": 1}, {"M*": 1}, description="formação do metóxido"),
        Step(
            "form",
            {"M*": 1, "A": 1},
            {"I*": 1},
            description="ataque ao carbonilo -> intermediário tetraédrico",
        ),
        Step(
            "dec",
            {"I*": 1},
            {"B": 1, "E": 1, "*": 1},
            description="colapso do intermediário tetraédrico",
        ),
    )
    return Mechanism(
        name=f"ER-M2[{'+'.join(inhibitors) or 'sem inib.'}]",
        family="ER-M2",
        steps=_with_spectators(steps, inhibitors),
        overall=OVERALL,
        notes="intermediário tetraédrico resolvido; separa ataque de colapso",
        references=("Kouzu & Hidaka, Fuel 93 (2012) 1",),
    )


def er_glyceride(inhibitors: tuple[str, ...] = ("G", "M")) -> Mechanism:
    """Eley-Rideal: glicerídeo adsorvido, metanol ataca da solução."""
    steps = (
        Step(
            "ads_A",
            {"A": 1, "*": 1},
            {"A*": 1},
            description="adsorção/protonação do carbonilo",
        ),
        Step(
            "sr",
            {"A*": 1, "M": 1},
            {"B": 1, "E": 1, "*": 1},
            description="ataque do metanol em solução",
        ),
    )
    return Mechanism(
        name=f"ER-A[{'+'.join(inhibitors) or 'sem inib.'}]",
        family="ER-A",
        steps=_with_spectators(steps, inhibitors),
        overall=OVERALL,
        notes="glicerídeo adsorvido; típico de catálise ácida",
    )


def lh_single_site(inhibitors: tuple[str, ...] = ("G",)) -> Mechanism:
    """Langmuir-Hinshelwood mono-sítio, produtos adsorvidos."""
    steps = (
        Step("ads_M", {"M": 1, "*": 1}, {"M*": 1}),
        Step("ads_A", {"A": 1, "*": 1}, {"A*": 1}),
        Step(
            "sr",
            {"M*": 1, "A*": 1},
            {"B*": 1, "E*": 1},
            description="reação entre espécies adsorvidas vizinhas",
        ),
        Step("des_B", {"B*": 1}, {"B": 1, "*": 1}, K_expr="1/K_ads_B"),
        Step("des_E", {"E*": 1}, {"E": 1, "*": 1}, K_expr="1/K_ads_E"),
    )
    return Mechanism(
        name=f"LH1[{'+'.join(inhibitors) or 'sem inib.'}]",
        family="LH1",
        steps=_with_spectators(steps, inhibitors),
        overall=OVERALL,
        notes="ambos adsorvidos no mesmo sítio; denominador quadrático",
    )


def lh_dual_site(inhibitors: tuple[str, ...] = ("G",)) -> Mechanism:
    """Langmuir-Hinshelwood dual-sítio (par ácido-base)."""
    steps = (
        Step("ads_M", {"M": 1, "*1": 1}, {"M*1": 1}, description="metanol no sítio básico"),
        Step("ads_A", {"A": 1, "*2": 1}, {"A*2": 1}, description="glicerídeo no sítio ácido"),
        Step(
            "sr",
            {"M*1": 1, "A*2": 1},
            {"E*1": 1, "B*2": 1},
            description="reação no par ácido-base",
        ),
        Step("des_E", {"E*1": 1}, {"E": 1, "*1": 1}, K_expr="1/K_ads_E"),
        Step("des_B", {"B*2": 1}, {"B": 1, "*2": 1}, K_expr="1/K_ads_B"),
    )
    # inibidores oxigenados competem pelo sítio básico
    return Mechanism(
        name=f"LH2[{'+'.join(inhibitors) or 'sem inib.'}]",
        family="LH2",
        steps=_with_spectators(steps, inhibitors, site="*1"),
        overall=OVERALL,
        notes="dois tipos de sítio; denominador é produto de dois termos",
    )


FAMILIES = {
    "ER-M": er_methoxide,
    "ER-M2": er_methoxide_tetrahedral,
    "ER-A": er_glyceride,
    "LH1": lh_single_site,
    "LH2": lh_dual_site,
}


# ----------------------------------------------------------------------
# modelos empíricos de referência
# ----------------------------------------------------------------------
def empirical_rate_laws() -> list[RateLaw]:
    """Modelos sem base mecanística, usados como referência.

    Se um modelo LHHW não superar estes, não há evidência nos dados que
    justifique falar em mecanismo — um resultado negativo que vale tanto
    quanto um positivo.
    """
    C_A, C_B, C_M, C_E = (conc_symbol(x) for x in ("A", "B", "M", "E"))
    n, m = sp.Symbol("n", positive=True), sp.Symbol("m", positive=True)

    ph = RateLaw(
        mechanism_name="PH-2ord",
        family="empírico",
        rds_label="—",
        expr=RATE_CONSTANT * (C_A * C_M - C_B * C_E / KEQ),
        conc_symbols=(C_A, C_B, C_E, C_M),
        param_symbols=(KEQ, RATE_CONSTANT),
        notes="pseudo-homogêneo de 2ª ordem reversível (sem catálise explícita)",
    )
    pl = RateLaw(
        mechanism_name="Potência",
        family="empírico",
        rds_label="—",
        expr=RATE_CONSTANT * C_A**n * C_M**m,
        conc_symbols=(C_A, C_M),
        param_symbols=(RATE_CONSTANT, m, n),
        notes="lei de potência irreversível com ordens ajustáveis",
    )
    return [ph, pl]


# ----------------------------------------------------------------------
# varredura
# ----------------------------------------------------------------------
def build_catalog(
    families: tuple[str, ...] = tuple(FAMILIES),
    inhibition_sets: tuple[tuple[str, ...], ...] = DEFAULT_INHIBITION_SETS,
) -> list[Mechanism]:
    """Produto cartesiano famílias x conjuntos de inibidores."""
    out: list[Mechanism] = []
    for fam, inh in product(families, inhibition_sets):
        mech = FAMILIES[fam](inh)
        mech.validate()
        out.append(mech)
    return out


def enumerate_rate_laws(
    catalog: list[Mechanism] | None = None,
    include_empirical: bool = True,
    enforce_thermodynamic_consistency: bool = True,
) -> list[RateLaw]:
    """Deriva todas as leis de velocidade candidatas do catálogo.

    Combinações redundantes (mesma expressão simbólica obtida por caminhos
    diferentes) são colapsadas: modelos algebricamente idênticos não são
    distinguíveis por dado nenhum, e mantê-los apenas inflaria a contagem.
    """
    catalog = build_catalog() if catalog is None else catalog
    laws: list[RateLaw] = []
    seen: set[str] = set()
    for mech in catalog:
        for law in derive_all(mech, enforce_thermodynamic_consistency):
            key = sp.srepr(sp.simplify(law.expr))
            if key in seen:
                continue
            seen.add(key)
            laws.append(law)
    if include_empirical:
        laws.extend(empirical_rate_laws())
    return laws
