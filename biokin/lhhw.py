"""Derivação simbólica de equações de velocidade LHHW / Eley-Rideal.

Dado um :class:`~biokin.mechanism.Mechanism` e a escolha da etapa
determinante (RDS), o derivador:

1. escreve as relações de quase-equilíbrio das demais etapas;
2. resolve, em cadeia, as coberturas dos intermediários em função das
   frações de sítio vago;
3. fecha o balanço de sítios;
4. monta ``r = k (produto dos reagentes - produto dos produtos / K_rds)``;
5. impõe consistência termodinâmica substituindo
   ``K_rds = Keq / prod(K_i)`` sobre as demais etapas do ciclo.

O resultado é uma expressão fechada que se anula no equilíbrio químico,
condição que separa modelos cineticamente admissíveis de ajustes
puramente empíricos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Sequence

import sympy as sp

from .mechanism import Mechanism
from .species import adsorbate_of, is_surface, site_of


# ----------------------------------------------------------------------
# nomes de símbolos
# ----------------------------------------------------------------------
def _site_tag(site: str) -> str:
    """``'*'`` -> ``'s'`` ; ``'*2'`` -> ``'s2'``."""
    return "s" + site[1:]


def conc_symbol(species: str) -> sp.Symbol:
    """Concentração de uma espécie fluida."""
    return sp.Symbol(f"C_{species}", positive=True)


def coverage_symbol(species: str) -> sp.Symbol:
    """Cobertura fracionária de um adsorbato ou sítio vago."""
    if not is_surface(species):
        raise ValueError(f"{species!r} não é espécie de superfície")
    tag = _site_tag(site_of(species))
    ads = adsorbate_of(species)
    return sp.Symbol(f"th_{ads}_{tag}" if ads else f"thv_{tag}", positive=True)


def equilibrium_symbol(label: str) -> sp.Symbol:
    return sp.Symbol(f"K_{label}", positive=True)


RATE_CONSTANT = sp.Symbol("k", positive=True)
KEQ = sp.Symbol("Keq", positive=True)


def _activity(species: str) -> sp.Expr:
    return coverage_symbol(species) if is_surface(species) else conc_symbol(species)


def _side_product(side: dict[str, int]) -> sp.Expr:
    out: sp.Expr = sp.Integer(1)
    for name, nu in side.items():
        out *= _activity(name) ** nu
    return out


# ----------------------------------------------------------------------
# resultado
# ----------------------------------------------------------------------
@dataclass
class RateLaw:
    """Equação de velocidade derivada, em forma simbólica e numérica."""

    mechanism_name: str
    family: str
    rds_label: str
    expr: sp.Expr
    conc_symbols: tuple[sp.Symbol, ...]
    param_symbols: tuple[sp.Symbol, ...]
    coverages: dict[str, sp.Expr] = field(default_factory=dict)
    denominator_exponent: int = 1
    notes: str = ""

    # -- apresentação ------------------------------------------------
    @property
    def model_id(self) -> str:
        return f"{self.mechanism_name}|RDS={self.rds_label}"

    @property
    def param_names(self) -> tuple[str, ...]:
        return tuple(str(s) for s in self.param_symbols)

    @property
    def species_names(self) -> tuple[str, ...]:
        return tuple(str(s)[2:] for s in self.conc_symbols)

    def numerator_denominator(self) -> tuple[sp.Expr, sp.Expr]:
        num, den = sp.fraction(sp.together(self.expr))
        return sp.factor(num), sp.factor(den)

    def latex(self) -> str:
        num, den = self.numerator_denominator()
        return sp.latex(num / den)

    def pretty(self) -> str:
        num, den = self.numerator_denominator()
        return f"r = ({num}) / ({den})"

    # -- avaliação ---------------------------------------------------
    def lambdify(self) -> Callable:
        """Callable ``f(concentrações..., parâmetros...) -> r`` (vetorizado)."""
        args = list(self.conc_symbols) + list(self.param_symbols)
        return sp.lambdify(args, self.expr, modules="numpy")

    def substitute_species(self, mapping: dict[str, str]) -> "RateLaw":
        """Instancia a lei genérica para espécies concretas.

        ``{'A': 'TG', 'B': 'DG'}`` troca ``C_A -> C_TG`` e, junto, os
        parâmetros que carregam o nome da espécie (``K_ads_A -> K_ads_TG``).
        Assim a constante de adsorção do glicerol é literalmente o mesmo
        parâmetro nas três reações consecutivas.
        """
        subs: dict[sp.Symbol, sp.Symbol] = {
            conc_symbol(a): conc_symbol(b) for a, b in mapping.items()
        }
        for s in self.param_symbols:
            new_name = _rename_species_token(str(s), mapping)
            if new_name != str(s):
                subs[s] = sp.Symbol(new_name, positive=True)

        expr = self.expr.subs(subs, simultaneous=True)
        concs = tuple(
            sorted({s for s in expr.free_symbols if str(s).startswith("C_")}, key=str)
        )
        params = tuple(
            sorted(
                {s for s in expr.free_symbols if not str(s).startswith("C_")}, key=str
            )
        )
        return RateLaw(
            mechanism_name=self.mechanism_name,
            family=self.family,
            rds_label=self.rds_label,
            expr=expr,
            conc_symbols=concs,
            param_symbols=params,
            coverages={
                k: v.subs(subs, simultaneous=True) for k, v in self.coverages.items()
            },
            denominator_exponent=self.denominator_exponent,
            notes=self.notes,
        )

    def rename_parameters(self, suffix: str, keep: Sequence[str] = ()) -> "RateLaw":
        """Acrescenta ``suffix`` aos parâmetros, exceto os listados em ``keep``.

        Usado para montar a rede consecutiva: as constantes de adsorção são
        compartilhadas entre as três reações (mesma espécie, mesmo sítio),
        enquanto ``k`` e ``Keq`` são específicos de cada etapa.
        """
        subs, params = {}, []
        for s in self.param_symbols:
            if str(s) in keep:
                params.append(s)
                continue
            new = sp.Symbol(f"{s}{suffix}", positive=True)
            subs[s] = new
            params.append(new)
        return RateLaw(
            mechanism_name=self.mechanism_name,
            family=self.family,
            rds_label=self.rds_label,
            expr=self.expr.subs(subs, simultaneous=True),
            conc_symbols=self.conc_symbols,
            param_symbols=tuple(params),
            coverages=self.coverages,
            denominator_exponent=self.denominator_exponent,
            notes=self.notes,
        )


def _rename_species_token(name: str, mapping: dict[str, str]) -> str:
    """Substitui nomes de espécies usados como *token* num nome de parâmetro.

    ``K_ads_A`` com ``{'A': 'TG'}`` vira ``K_ads_TG``; ``K_adsorbed`` fica
    intacto, porque a troca só ocorre em fronteiras de token.
    """
    parts = name.split("_")
    return "_".join(mapping.get(part, part) for part in parts)


class DerivationError(RuntimeError):
    """O mecanismo não pôde ser resolvido pela cadeia de quase-equilíbrio."""


# ----------------------------------------------------------------------
# derivação
# ----------------------------------------------------------------------
def derive_rate_law(
    mech: Mechanism,
    rds_index: int,
    enforce_thermodynamic_consistency: bool = True,
) -> RateLaw:
    """Deriva a equação de velocidade de ``mech`` com RDS em ``rds_index``."""
    mech.validate()
    rds = mech.steps[rds_index]
    if not rds.in_cycle:
        raise DerivationError(
            f"etapa {rds.label!r} está fora do ciclo e não pode ser a RDS"
        )

    adsorbates = mech.surface_species()
    unknowns = {sp_: coverage_symbol(sp_) for sp_ in adsorbates}
    vacants = {s: coverage_symbol(s) for s in mech.sites()}

    # 1) relações de quase-equilíbrio (todas as etapas menos a RDS)
    pending: list[tuple[str, sp.Expr]] = []
    for i, st in enumerate(mech.steps):
        if i == rds_index:
            continue
        K = st.K()
        pending.append(
            (st.label, K * _side_product(st.reactants) - _side_product(st.products))
        )

    # 2) resolução em cadeia
    resolved: dict[sp.Symbol, sp.Expr] = {}
    target = set(unknowns.values())
    guard = 0
    while pending and (target - set(resolved)):
        guard += 1
        if guard > len(mech.steps) + 5:
            break
        progressed = False
        still: list[tuple[str, sp.Expr]] = []
        for label, eq in pending:
            eq_s = eq.subs(resolved, simultaneous=True) if resolved else eq
            free = (eq_s.free_symbols & target) - set(resolved)
            if len(free) == 1:
                sym = free.pop()
                sols = sp.solve(sp.Eq(eq_s, 0), sym, dict=False)
                if not sols:
                    still.append((label, eq))
                    continue
                resolved[sym] = sp.simplify(sols[0])
                progressed = True
            else:
                still.append((label, eq))
        pending = still
        if not progressed:
            break

    missing = [
        name for name, sym in unknowns.items() if sym not in resolved
    ]
    if missing:
        raise DerivationError(
            f"[{mech.name}|RDS={rds.label}] coberturas não determinadas pela "
            f"cadeia de quase-equilíbrio: {missing}. O mecanismo pode não ser "
            "linear (ciclo único) ou a RDS escolhida deixa o sistema aberto."
        )

    # propaga substituições até estabilizar (cadeias de dependência)
    for _ in range(len(resolved) + 1):
        new = {s: e.subs(resolved, simultaneous=True) for s, e in resolved.items()}
        if new == resolved:
            break
        resolved = new

    # 3) balanço de sítios
    balances, vac_syms = [], []
    for site, thv in vacants.items():
        total: sp.Expr = thv
        for name, sym in unknowns.items():
            if site_of(name) == site:
                total += resolved[sym]
        balances.append(sp.Eq(total, 1))
        vac_syms.append(thv)

    sol = sp.solve(balances, vac_syms, dict=True)
    if not sol:
        raise DerivationError(
            f"[{mech.name}|RDS={rds.label}] balanço de sítios sem solução"
        )
    vac_sol = _pick_physical_branch(sol, vac_syms)

    coverages = {
        name: sp.simplify(resolved[sym].subs(vac_sol, simultaneous=True))
        for name, sym in unknowns.items()
    }
    coverages.update(
        {site: sp.simplify(vac_sol[thv]) for site, thv in vacants.items()}
    )

    # 4) velocidade da etapa determinante
    K_rds = rds.K()
    rate = RATE_CONSTANT * (
        _side_product(rds.reactants) - _side_product(rds.products) / K_rds
    )

    # substitui coberturas ANTES do vínculo termodinâmico: o parâmetro
    # eliminado em (5) também aparece no balanço de sítios, e precisa ser
    # eliminado lá com o mesmo valor.
    rate = rate.subs(resolved, simultaneous=True).subs(vac_sol, simultaneous=True)

    # 5) consistência termodinâmica: Keq = prod(K_i^sigma) sobre o ciclo
    if enforce_thermodynamic_consistency:
        others: sp.Expr = sp.Integer(1)
        for i in mech.cycle_steps():
            if i != rds_index:
                others *= mech.steps[i].K()
        # K_rds pode ser uma expressão (ex.: 1/K_ads_B numa dessorção):
        # resolve-se K_rds = Keq / prod(outras) para o parâmetro que a compõe.
        free = sorted(K_rds.free_symbols, key=str)
        if len(free) != 1:
            raise DerivationError(
                f"K_expr da etapa determinante {rds.label!r} deve depender de "
                "um único parâmetro"
            )
        sol = sp.solve(sp.Eq(K_rds, KEQ / others), free[0], dict=False)
        if not sol:
            raise DerivationError(f"não foi possível impor Keq via {rds.label!r}")
        rate = rate.subs(free[0], sol[0])
        coverages = {
            name: sp.simplify(expr.subs(free[0], sol[0]))
            for name, expr in coverages.items()
        }

    rate = sp.cancel(sp.together(sp.simplify(rate)))

    concs = tuple(sorted({s for s in rate.free_symbols if str(s).startswith("C_")}, key=str))
    params = tuple(
        sorted(
            {
                s
                for s in rate.free_symbols
                if str(s).startswith(("K_", "k")) or s == KEQ
            },
            key=str,
        )
    )

    _, den = sp.fraction(sp.together(rate))
    return RateLaw(
        mechanism_name=mech.name,
        family=mech.family,
        rds_label=rds.label,
        expr=rate,
        conc_symbols=concs,
        param_symbols=params,
        coverages=coverages,
        denominator_exponent=_denominator_exponent(den),
        notes=mech.notes,
    )


def _pick_physical_branch(
    solutions: list[dict], vac_syms: list[sp.Symbol]
) -> dict[sp.Symbol, sp.Expr]:
    """Escolhe o ramo com todas as frações de sítio vago positivas.

    Com concentrações e constantes de adsorção positivas, apenas um ramo
    satisfaz ``0 < theta_v <= 1``; ramos espúrios (raízes negativas de
    balanços quadráticos) são descartados.
    """
    for candidate in solutions:
        if all(candidate.get(s, sp.Integer(-1)).is_positive is not False for s in vac_syms):
            return candidate
    return solutions[0]


def _denominator_exponent(den: sp.Expr) -> int:
    """Ordem do termo de adsorção (1 = mono-sítio, 2 = bimolecular, ...).

    Conta apenas os fatores polinomiais do tipo ``(1 + sum K_i C_i)``;
    fatores monomiais (``Keq``, constantes) não contribuem.
    """

    def order(factor: sp.Expr) -> int:
        if isinstance(factor, sp.Pow) and factor.exp.is_Integer:
            return int(factor.exp) * order(factor.base)
        return 1 if isinstance(factor, sp.Add) else 0

    den = sp.factor(den)
    factors = den.args if isinstance(den, sp.Mul) else (den,)
    return max(1, sum(order(f) for f in factors))


def derive_all(
    mech: Mechanism, enforce_thermodynamic_consistency: bool = True
) -> list[RateLaw]:
    """Deriva uma lei para cada escolha admissível de RDS.

    Escolhas que deixam o sistema indeterminado são descartadas
    silenciosamente — elas correspondem a mecanismos não lineares para os
    quais a hipótese de quase-equilíbrio em cadeia não se aplica.
    """
    laws = []
    for i in mech.rds_candidates():
        try:
            laws.append(derive_rate_law(mech, i, enforce_thermodynamic_consistency))
        except (DerivationError, NotImplementedError):
            continue
    return laws
