"""Estruturas de dados experimentais e leitura/escrita em CSV.

Um :class:`Experiment` é uma corrida: condições iniciais, temperatura,
tipo de reator e a matriz de medidas. Espécies não medidas entram como
``NaN`` e simplesmente não contribuem para os resíduos — assim o mesmo
código serve a quem mede só o teor de éster por cromatografia e a quem
tem o perfil completo de glicerídeos.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .reactor import MonolithOperation, concentration_vector
from .species import FLUID_SPECIES


@dataclass
class Experiment:
    """Uma corrida experimental."""

    label: str
    T_K: float
    C0: np.ndarray
    t: np.ndarray
    Y: np.ndarray  # (n_pontos, n_espécies), NaN = não medido
    reactor: str = "batch"  # 'batch' | 'monolith'
    catalyst_g_L: float = 10.0
    operation: MonolithOperation | None = None
    sigma: np.ndarray | None = None  # desvio-padrão por espécie

    def __post_init__(self) -> None:
        self.C0 = np.asarray(self.C0, dtype=float)
        self.t = np.asarray(self.t, dtype=float)
        self.Y = np.asarray(self.Y, dtype=float)
        if self.Y.shape != (len(self.t), len(FLUID_SPECIES)):
            raise ValueError(
                f"[{self.label}] Y deve ter forma "
                f"{(len(self.t), len(FLUID_SPECIES))}, tem {self.Y.shape}"
            )
        if self.reactor == "monolith" and self.operation is None:
            self.operation = MonolithOperation()
        if self.reactor == "monolith":
            self.catalyst_g_L = self.operation.catalyst_g_L

    @property
    def n_obs(self) -> int:
        return int(np.isfinite(self.Y).sum())

    @property
    def measured_species(self) -> list[str]:
        return [
            s
            for i, s in enumerate(FLUID_SPECIES)
            if np.isfinite(self.Y[:, i]).any()
        ]

    def scale(self) -> np.ndarray:
        """Escala característica de cada espécie, para ponderação relativa.

        Sem isto, o triglicerídeo (~1 mol/L) domina os resíduos e o
        monoglicerídeo (~0,02 mol/L) não influencia o ajuste — justamente a
        espécie que mais discrimina mecanismos, por ser intermediária.
        """
        out = np.ones(len(FLUID_SPECIES))
        for i in range(len(FLUID_SPECIES)):
            col = self.Y[:, i]
            col = col[np.isfinite(col)]
            if col.size:
                m = float(np.nanmax(np.abs(col)))
                out[i] = m if m > 1e-9 else 1.0
        return out


@dataclass
class Dataset:
    """Conjunto de corridas analisadas em conjunto."""

    experiments: list[Experiment] = field(default_factory=list)
    name: str = "dados"

    def __len__(self) -> int:
        return len(self.experiments)

    def __iter__(self):
        return iter(self.experiments)

    @property
    def n_obs(self) -> int:
        return sum(e.n_obs for e in self.experiments)

    @property
    def temperatures(self) -> list[float]:
        return sorted({e.T_K for e in self.experiments})

    @property
    def is_non_isothermal(self) -> bool:
        return len(self.temperatures) > 1

    @property
    def T_ref(self) -> float:
        """Temperatura de referência: média harmônica em 1/T, no centro dos dados."""
        Ts = self.temperatures
        return 1.0 / float(np.mean([1.0 / T for T in Ts]))

    def summary(self) -> str:
        lines = [
            f"{self.name}: {len(self)} corridas, {self.n_obs} observações",
            f"  temperaturas: {', '.join(f'{T:.1f} K' for T in self.temperatures)}",
        ]
        for e in self.experiments:
            lines.append(
                f"  {e.label:<18s} {e.reactor:<9s} T={e.T_K:6.1f} K  "
                f"{len(e.t):2d} pontos  medido: {'/'.join(e.measured_species)}"
            )
        return "\n".join(lines)


# ----------------------------------------------------------------------
# I/O
# ----------------------------------------------------------------------
#: A alimentação vai em colunas próprias (``C0_*``) porque quase sempre se
#: conhece a composição carregada mesmo sem medi-la — tipicamente o metanol,
#: que está em excesso e raramente é titulado. Sem isso o balanço molar fica
#: indeterminado na leitura.
CSV_HEADER = [
    "experimento",
    "reator",
    "T_K",
    "catalisador_g_L",
    *[f"C0_{s}" for s in FLUID_SPECIES],
    "tempo_min",
    *[f"C_{s}" for s in FLUID_SPECIES],
]


def write_csv(dataset: Dataset, path: str | Path) -> None:
    """Grava o conjunto num CSV plano (um ponto por linha)."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_HEADER)
        for e in dataset.experiments:
            for k, tk in enumerate(e.t):
                w.writerow(
                    [
                        e.label,
                        e.reactor,
                        f"{e.T_K:.4f}",
                        f"{e.catalyst_g_L:.6g}",
                        *[f"{v:.6g}" for v in e.C0],
                        f"{tk:.6g}",
                        *[
                            "" if not math.isfinite(v) else f"{v:.6g}"
                            for v in e.Y[k]
                        ],
                    ]
                )


def read_csv(
    path: str | Path,
    name: str | None = None,
    operations: dict[str, MonolithOperation] | None = None,
) -> Dataset:
    """Lê um CSV no formato de :func:`write_csv`.

    A condição inicial de cada corrida é lida da linha de menor tempo; ela
    precisa portanto trazer as concentrações alimentadas (inclusive metanol).
    Células vazias significam "não medido".
    """
    path = Path(path)
    rows: dict[str, list[dict]] = {}
    with path.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            rows.setdefault(row["experimento"], []).append(row)

    experiments: list[Experiment] = []
    for label, group in rows.items():
        group.sort(key=lambda r: float(r["tempo_min"]))
        t = np.array([float(r["tempo_min"]) for r in group])
        Y = np.array(
            [
                [
                    float(r[f"C_{s}"]) if r.get(f"C_{s}", "").strip() else np.nan
                    for s in FLUID_SPECIES
                ]
                for r in group
            ]
        )
        first = group[0]
        if all(f"C0_{s}" in first for s in FLUID_SPECIES):
            C0 = np.array(
                [float(first.get(f"C0_{s}") or 0.0) for s in FLUID_SPECIES]
            )
        else:  # formato reduzido: usa o primeiro ponto medido
            C0 = np.nan_to_num(Y[0], nan=0.0)
        reactor = first.get("reator", "batch").strip() or "batch"
        experiments.append(
            Experiment(
                label=label,
                T_K=float(first["T_K"]),
                C0=C0,
                t=t,
                Y=Y,
                reactor=reactor,
                catalyst_g_L=float(first.get("catalisador_g_L") or 10.0),
                operation=(operations or {}).get(label),
            )
        )
    return Dataset(experiments, name=name or path.stem)


def make_experiment(
    label: str,
    T_K: float,
    C0: dict[str, float],
    t: np.ndarray,
    Y: np.ndarray,
    **kwargs,
) -> Experiment:
    """Atalho que aceita a condição inicial como dicionário de espécies."""
    return Experiment(
        label=label, T_K=T_K, C0=concentration_vector(C0), t=np.asarray(t), Y=Y, **kwargs
    )
