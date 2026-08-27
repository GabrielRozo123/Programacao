"""Representação declarativa de mecanismos catalíticos.

Um mecanismo é uma sequência de etapas elementares. Cada etapa é
reversível e recebe uma constante de equilíbrio ``K_<label>``.

Etapas do *ciclo catalítico* (``in_cycle=True``) devem somar, com número
estequiométrico 1, a reação global do mecanismo — isso é verificado em
:meth:`Mechanism.validate`. Etapas fora do ciclo representam adsorção de
espectadores/inibidores (glicerol, éster, água) em quase-equilíbrio.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp

from .species import adsorbate_of, is_surface, site_of


@dataclass(frozen=True)
class Step:
    """Etapa elementar ``reactants <-> products``.

    Coeficientes estequiométricos são inteiros positivos nos dois lados.
    """

    label: str
    reactants: dict[str, int]
    products: dict[str, int]
    in_cycle: bool = True
    can_be_rds: bool = True
    description: str = ""
    K_expr: str | None = None
    """Constante de equilíbrio da etapa, como expressão sympy.

    O padrão é ``K_<label>``. Etapas de dessorção devem declarar
    ``K_expr='1/K_ads_X'`` para que a constante de adsorção da espécie X
    seja *a mesma* onde quer que X apareça — inclusive nas outras reações
    da série consecutiva. É essa partilha que mantém o número de
    parâmetros tratável e o modelo fisicamente coerente.
    """

    def K(self) -> sp.Expr:
        """Constante de equilíbrio da etapa."""
        if self.K_expr is None:
            return sp.Symbol(f"K_{self.label}", positive=True)
        return sp.sympify(
            self.K_expr,
            locals={
                str(s): sp.Symbol(str(s), positive=True)
                for s in sp.sympify(self.K_expr).free_symbols
            },
        )

    def net(self) -> dict[str, int]:
        """Estequiometria líquida (produtos - reagentes)."""
        out: dict[str, int] = {}
        for sp, nu in self.reactants.items():
            out[sp] = out.get(sp, 0) - nu
        for sp, nu in self.products.items():
            out[sp] = out.get(sp, 0) + nu
        return {sp: nu for sp, nu in out.items() if nu != 0}

    def species(self) -> set[str]:
        return set(self.reactants) | set(self.products)

    def pretty(self) -> str:
        def side(d: dict[str, int]) -> str:
            return " + ".join(
                (f"{nu} {sp}" if nu != 1 else sp) for sp, nu in d.items()
            )

        return f"{side(self.reactants)} <-> {side(self.products)}"


@dataclass(frozen=True)
class Mechanism:
    """Conjunto de etapas elementares para *uma* reação global."""

    name: str
    family: str
    steps: tuple[Step, ...]
    overall: dict[str, int]
    notes: str = ""
    references: tuple[str, ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------
    def surface_species(self) -> list[str]:
        """Adsorbatos (exclui sítios vagos), em ordem de aparição."""
        seen: list[str] = []
        for st in self.steps:
            for sp in list(st.reactants) + list(st.products):
                if is_surface(sp) and adsorbate_of(sp) and sp not in seen:
                    seen.append(sp)
        return seen

    def sites(self) -> list[str]:
        """Tipos de sítio presentes (``'*'``, ``'*1'``, ...)."""
        seen: list[str] = []
        for st in self.steps:
            for sp in list(st.reactants) + list(st.products):
                if is_surface(sp):
                    s = site_of(sp)
                    if s not in seen:
                        seen.append(s)
        return seen

    def fluid_species(self) -> list[str]:
        seen: list[str] = []
        for st in self.steps:
            for sp in list(st.reactants) + list(st.products):
                if not is_surface(sp) and sp not in seen:
                    seen.append(sp)
        return seen

    def cycle_steps(self) -> list[int]:
        return [i for i, st in enumerate(self.steps) if st.in_cycle]

    def rds_candidates(self) -> list[int]:
        return [i for i, st in enumerate(self.steps) if st.in_cycle and st.can_be_rds]

    # ------------------------------------------------------------------
    def cycle_sum(self) -> dict[str, int]:
        """Soma das etapas do ciclo com número estequiométrico 1."""
        total: dict[str, int] = {}
        for i in self.cycle_steps():
            for sp, nu in self.steps[i].net().items():
                total[sp] = total.get(sp, 0) + nu
        return {sp: nu for sp, nu in total.items() if nu != 0}

    def validate(self) -> None:
        """Verifica fechamento do ciclo catalítico.

        Levanta ``ValueError`` se a soma das etapas do ciclo não reproduzir
        exatamente ``overall`` (todos os intermediários de superfície e
        sítios devem se cancelar).
        """
        total = self.cycle_sum()
        surf = {sp: nu for sp, nu in total.items() if is_surface(sp)}
        if surf:
            raise ValueError(
                f"[{self.name}] ciclo não fecha: espécies de superfície "
                f"remanescentes {surf}"
            )
        if total != {sp: nu for sp, nu in self.overall.items() if nu != 0}:
            raise ValueError(
                f"[{self.name}] soma do ciclo {total} != reação global "
                f"{self.overall}"
            )
        for st in self.steps:
            if not st.in_cycle and st.can_be_rds:
                raise ValueError(
                    f"[{self.name}] etapa fora do ciclo {st.label!r} não pode "
                    "ser etapa determinante"
                )

    def pretty(self) -> str:
        lines = [f"{self.name}  [{self.family}]"]
        if self.notes:
            lines.append(f"  {self.notes}")
        for st in self.steps:
            tag = "" if st.in_cycle else "  (espectador)"
            lines.append(f"  {st.label:>10s}: {st.pretty()}{tag}")
        return "\n".join(lines)
