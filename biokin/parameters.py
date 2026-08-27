"""Parametrização térmica e espaço de busca da regressão.

Dois cuidados numéricos que decidem se a regressão converge ou não:

*Reparametrização centrada.* Estimar ``k0`` e ``Ea`` da forma de Arrhenius
crua produz correlação próxima de 1 entre os dois — o fator pré-exponencial
é uma extrapolação para 1/T = 0, muito longe dos dados. Usa-se

    k(T) = k(T_ref) * exp[ -Ea/R * (1/T - 1/T_ref) ]

com ``T_ref`` no centro da faixa experimental. A mesma forma serve à
equação de van 't Hoff para as constantes de adsorção, trocando ``Ea`` por
``ΔH_ads``.

*Escala logarítmica.* ``k`` e ``K`` são positivos por construção. Estimar
``ln k`` e ``ln K`` impõe essa restrição sem barreiras artificiais e
equaliza a sensibilidade entre parâmetros de ordens de grandeza distintas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

#: Constante universal dos gases [J/(mol·K)].
R_GAS = 8.314462618

#: Tipos de parâmetro reconhecidos.
KIND_RATE = "k"  # constante de velocidade -> energia = Ea
KIND_ADSORPTION = "Kads"  # constante de adsorção -> energia = ΔH_ads
KIND_EQUILIBRIUM = "Keq"  # constante de equilíbrio -> energia = ΔH_r
KIND_EXPONENT = "exp"  # ordem de reação (modelos empíricos)


@dataclass
class ParamSpec:
    """Especificação de um parâmetro do modelo."""

    name: str
    kind: str
    value: float  # valor em T_ref (ou o próprio valor, se expoente)
    energy_kJ: float = 0.0  # Ea, ΔH_ads ou ΔH_r em kJ/mol
    fit_value: bool = True
    fit_energy: bool = False
    value_bounds: tuple[float, float] = (1e-12, 1e12)
    energy_bounds: tuple[float, float] = (-250.0, 400.0)

    @property
    def is_log(self) -> bool:
        return self.kind != KIND_EXPONENT

    def at(self, T: float, value: float, energy_kJ: float) -> float:
        """Valor do parâmetro em ``T`` a partir dos valores de referência."""
        if self.kind == KIND_EXPONENT:
            return value
        return value * math.exp(-energy_kJ * 1e3 / R_GAS * (1.0 / T - 1.0 / self._T_ref))

    _T_ref: float = 333.15


def default_spec(name: str, T_ref: float, non_isothermal: bool) -> ParamSpec:
    """Especificação inicial razoável, inferida do nome do parâmetro.

    As faixas refletem ordens de grandeza usuais em transesterificação em
    fase líquida (concentrações em mol/L, tempo em minuto).
    """
    if name.startswith("K_ads"):
        return ParamSpec(
            name,
            KIND_ADSORPTION,
            value=1.0,
            energy_kJ=-30.0,
            fit_energy=non_isothermal,
            value_bounds=(1e-6, 1e6),
            energy_bounds=(-150.0, 0.0),  # adsorção é exotérmica
            _T_ref=T_ref,
        )
    if name.startswith("Keq"):
        return ParamSpec(
            name,
            KIND_EQUILIBRIUM,
            value=3.0,
            energy_kJ=0.0,
            fit_energy=non_isothermal,
            value_bounds=(1e-4, 1e4),
            energy_bounds=(-100.0, 100.0),
            _T_ref=T_ref,
        )
    if name in ("n", "m") or name.startswith(("n_", "m_")):
        return ParamSpec(
            name,
            KIND_EXPONENT,
            value=1.0,
            fit_energy=False,
            value_bounds=(0.1, 3.0),
            _T_ref=T_ref,
        )
    # k, K_sr, K_form, K_dec ...
    kind = KIND_RATE if name.startswith("k") else KIND_ADSORPTION
    return ParamSpec(
        name,
        kind,
        value=1.0,
        energy_kJ=50.0 if kind == KIND_RATE else -20.0,
        fit_energy=non_isothermal,
        value_bounds=(1e-8, 1e8),
        energy_bounds=(0.0, 250.0) if kind == KIND_RATE else (-150.0, 150.0),
        _T_ref=T_ref,
    )


@dataclass
class Parameterization:
    """Coleção de :class:`ParamSpec` com empacotamento para o otimizador."""

    specs: list[ParamSpec]
    T_ref: float = 333.15

    def __post_init__(self) -> None:
        self.specs = [replace(s, _T_ref=self.T_ref) for s in self.specs]
        self._index = {s.name: i for i, s in enumerate(self.specs)}

    # -- construção --------------------------------------------------
    @classmethod
    def for_names(
        cls,
        names: list[str] | tuple[str, ...],
        T_ref: float = 333.15,
        non_isothermal: bool = False,
    ) -> "Parameterization":
        return cls([default_spec(n, T_ref, non_isothermal) for n in names], T_ref)

    def get(self, name: str) -> ParamSpec:
        return self.specs[self._index[name]]

    def update(self, name: str, **kwargs) -> None:
        i = self._index[name]
        self.specs[i] = replace(self.specs[i], **kwargs)

    # -- vetor de busca ----------------------------------------------
    @property
    def free_names(self) -> list[str]:
        out: list[str] = []
        for s in self.specs:
            if s.fit_value:
                out.append(f"ln({s.name})" if s.is_log else s.name)
            if s.fit_energy:
                out.append(f"E[{s.name}]")
        return out

    @property
    def n_free(self) -> int:
        return len(self.free_names)

    def pack(self) -> np.ndarray:
        x: list[float] = []
        for s in self.specs:
            if s.fit_value:
                x.append(math.log(s.value) if s.is_log else s.value)
            if s.fit_energy:
                x.append(s.energy_kJ)
        return np.asarray(x, dtype=float)

    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        lo: list[float] = []
        hi: list[float] = []
        for s in self.specs:
            if s.fit_value:
                if s.is_log:
                    lo.append(math.log(s.value_bounds[0]))
                    hi.append(math.log(s.value_bounds[1]))
                else:
                    lo.append(s.value_bounds[0])
                    hi.append(s.value_bounds[1])
            if s.fit_energy:
                lo.append(s.energy_bounds[0])
                hi.append(s.energy_bounds[1])
        return np.asarray(lo), np.asarray(hi)

    def unpack(self, x: np.ndarray) -> dict[str, tuple[float, float]]:
        """Vetor de busca -> ``{nome: (valor em T_ref, energia kJ/mol)}``."""
        out: dict[str, tuple[float, float]] = {}
        i = 0
        for s in self.specs:
            value = s.value
            energy = s.energy_kJ
            if s.fit_value:
                value = math.exp(x[i]) if s.is_log else x[i]
                i += 1
            if s.fit_energy:
                energy = x[i]
                i += 1
            out[s.name] = (value, energy)
        return out

    def values_at(self, x: np.ndarray, T: float) -> dict[str, float]:
        """Vetor de busca + temperatura -> valores dos parâmetros."""
        raw = self.unpack(x)
        return {s.name: s.at(T, *raw[s.name]) for s in self.specs}

    def is_isothermal(self) -> bool:
        return not any(s.fit_energy for s in self.specs)

    def describe(self, x: np.ndarray | None = None) -> str:
        raw = self.unpack(x) if x is not None else {
            s.name: (s.value, s.energy_kJ) for s in self.specs
        }
        lines = [f"{'parâmetro':>14s} {'valor(T_ref)':>14s} {'energia':>12s}"]
        for s in self.specs:
            v, e = raw[s.name]
            tag = {
                KIND_RATE: "Ea",
                KIND_ADSORPTION: "ΔH_ads",
                KIND_EQUILIBRIUM: "ΔH_r",
                KIND_EXPONENT: "—",
            }[s.kind]
            etxt = "—" if s.kind == KIND_EXPONENT else f"{e:8.1f} {tag}"
            lines.append(f"{s.name:>14s} {v:14.4g} {etxt:>12s}")
        return "\n".join(lines)
