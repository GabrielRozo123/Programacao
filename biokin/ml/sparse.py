"""Regressão racional esparsa: descobrir a forma da lei de velocidade.

Toda lei LHHW tem a forma

    r = N(C) / D(C)^q ,   D(C) = 1 + sum_j b_j g_j(C)

O que distingue um mecanismo de outro é *quais* termos ``g_j`` aparecem no
denominador (quais espécies competem pelos sítios) e com que expoente. Em
vez de enumerar mecanismos e testar um a um, aqui se estima essa estrutura
diretamente dos dados.

O truque, na linha do SINDy para não linearidades racionais, é que para
``q = 1`` o problema é linear nos coeficientes depois de multiplicar pelo
denominador:

    r · (1 + sum_j b_j g_j) = sum_i a_i f_i
    =>  r = sum_i a_i f_i - sum_j b_j (r · g_j)

Isso permite usar mínimos quadrados com limiarização sequencial (STLSQ)
para *selecionar* os termos. A linearização, porém, pondera cada ponto por
``D(C)``, o que enviesa os coeficientes. Por isso a seleção linear é
apenas o primeiro passo: os coeficientes finais são reajustados por
mínimos quadrados não lineares sobre o resíduo verdadeiro ``r - N/D^q``,
sem viés.

Este módulo **não substitui** a derivação mecanística: ele devolve uma
forma funcional, não um mecanismo. O uso correto é como filtro — a
estrutura encontrada indica quais famílias do catálogo merecem atenção, e
quais termos de inibição têm suporte nos dados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
from scipy.optimize import least_squares


@dataclass
class Feature:
    """Um termo da biblioteca: nome legível e função que o avalia."""

    name: str
    func: Callable[[dict[str, np.ndarray]], np.ndarray]

    def __call__(self, cols: dict[str, np.ndarray]) -> np.ndarray:
        return self.func(cols)


def _prod(*names: str) -> Callable[[dict[str, np.ndarray]], np.ndarray]:
    def f(cols: dict[str, np.ndarray]) -> np.ndarray:
        out = np.ones_like(next(iter(cols.values())))
        for n in names:
            out = out * cols[n]
        return out

    return f


def rational_library(
    acyl: str = "TG",
    product: str = "DG",
    inhibitors: Sequence[str] = ("M", "TG", "DG", "MG", "G", "E"),
    reversible: bool = True,
) -> tuple[list[Feature], list[Feature]]:
    """Biblioteca padrão de termos para numerador e denominador.

    O numerador cobre as formas que as famílias mecanísticas produzem:
    bimolecular (Langmuir-Hinshelwood e Eley-Rideal), monomolecular
    (adsorção ou dessorção determinante) e o termo reverso.

    O denominador cobre a competição de cada espécie pelos sítios.
    """
    num = [
        Feature(f"C_{acyl}·C_M", _prod(acyl, "M")),
        Feature(f"C_{acyl}", _prod(acyl)),
        Feature("C_M", _prod("M")),
    ]
    if reversible:
        num.append(Feature(f"C_{product}·C_E", _prod(product, "E")))
    den = [Feature(f"C_{s}", _prod(s)) for s in inhibitors]
    return num, den


def _design(
    features: list[Feature], C: np.ndarray, species: Sequence[str]
) -> np.ndarray:
    cols = {s: C[:, i] for i, s in enumerate(species)}
    return np.column_stack([f(cols) for f in features]) if features else np.zeros((len(C), 0))


def _ridge(A: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    n = A.shape[1]
    return np.linalg.solve(A.T @ A + alpha * np.eye(n), A.T @ y)


def stlsq(
    A: np.ndarray, y: np.ndarray, threshold: float, alpha: float = 1e-8, n_iter: int = 20
) -> np.ndarray:
    """Mínimos quadrados com limiarização sequencial.

    A cada passo zera os coeficientes abaixo do limiar (em escala
    normalizada) e reajusta os restantes. Converge em poucas iterações e
    devolve uma solução esparsa — que é o objetivo: um denominador com
    todos os termos possíveis ajusta bem e não diz nada.
    """
    xi = _ridge(A, y, alpha)
    active = np.ones(A.shape[1], dtype=bool)
    for _ in range(n_iter):
        small = np.abs(xi) < threshold
        if not small.any() or (~small).sum() == 0:
            break
        new_active = active & ~small
        if new_active.sum() == 0 or np.array_equal(new_active, active):
            break
        active = new_active
        xi = np.zeros(A.shape[1])
        xi[active] = _ridge(A[:, active], y, alpha)
    return xi


@dataclass
class RationalModel:
    """Lei racional descoberta a partir dos dados."""

    numerator: list[Feature]
    denominator: list[Feature]
    a: np.ndarray
    b: np.ndarray
    q: float = 1.0
    species: tuple[str, ...] = ()
    r2: float = float("nan")
    n_terms: int = 0
    selection_r2: float = float("nan")

    def predict(self, C: np.ndarray) -> np.ndarray:
        N = _design(self.numerator, C, self.species) @ self.a
        D = 1.0 + _design(self.denominator, C, self.species) @ self.b
        D = np.where(np.abs(D) < 1e-12, np.sign(D) * 1e-12 + 1e-12, D)
        return N / D**self.q

    def pretty(self, tol: float = 1e-12) -> str:
        def side(feats: list[Feature], coefs: np.ndarray, lead_one: bool) -> str:
            terms = ["1"] if lead_one else []
            for f, c in zip(feats, coefs):
                if abs(c) > tol:
                    terms.append(f"{c:+.4g}·{f.name}")
            return " ".join(terms) if terms else "0"

        num = side(self.numerator, self.a, False)
        den = side(self.denominator, self.b, True)
        power = "" if abs(self.q - 1.0) < 1e-6 else f"^{self.q:.2f}"
        return f"r = ({num}) / ({den}){power}"

    def active_denominator(self, tol: float = 1e-12) -> list[str]:
        """Espécies que o ajuste manteve no denominador."""
        return [f.name for f, c in zip(self.denominator, self.b) if abs(c) > tol]

    def interpretation(self) -> str:
        """Leitura mecanística da estrutura encontrada."""
        active = self.active_denominator()
        if not active:
            return (
                "Denominador vazio: nenhuma inibição detectável. Compatível "
                "com cobertura baixa dos sítios (regime de lei de potência)."
            )
        q = self.q
        order = (
            "mono-sítio (expoente 1): compatível com Eley-Rideal ou com "
            "adsorção/dessorção determinante"
            if abs(q - 1) < 0.3
            else "bimolecular (expoente ~2): compatível com Langmuir-Hinshelwood, "
            "reação superficial determinante"
        )
        return (
            f"Denominador de ordem {q:.2f} — {order}.\n"
            f"Espécies com competição detectada pelos sítios: "
            f"{', '.join(active)}."
        )


def fit_rational_sparse(
    C: np.ndarray,
    r: np.ndarray,
    species: Sequence[str],
    numerator: list[Feature] | None = None,
    denominator: list[Feature] | None = None,
    thresholds: Sequence[float] = (0.001, 0.005, 0.02, 0.05, 0.1, 0.2),
    q_values: Sequence[float] = (1.0, 2.0),
    fit_q: bool = False,
    weights: np.ndarray | None = None,
) -> RationalModel:
    """Descobre a lei racional que melhor explica ``r(C)``.

    Varre limiares de esparsidade e expoentes de denominador, seleciona a
    estrutura por AIC corrigido — de modo que termos só entram se pagarem
    seu custo — e reajusta os coeficientes sem o viés da linearização.
    """
    C = np.atleast_2d(np.asarray(C, dtype=float))
    r = np.asarray(r, dtype=float).ravel()
    species = tuple(species)
    if numerator is None or denominator is None:
        num_def, den_def = rational_library()
        numerator = numerator or num_def
        denominator = denominator or den_def

    Phi_N = _design(numerator, C, species)
    Phi_D = _design(denominator, C, species)
    w = np.ones(len(r)) if weights is None else np.asarray(weights, dtype=float)

    # normalização de colunas: sem ela o limiar de esparsidade compara
    # coeficientes de termos com escalas muito diferentes
    scale_N = np.maximum(np.abs(Phi_N).max(axis=0), 1e-30)
    scale_D = np.maximum(np.abs(Phi_D).max(axis=0), 1e-30)
    r_scale = float(np.max(np.abs(r))) or 1.0

    A = np.column_stack([Phi_N / scale_N, -(r[:, None] * Phi_D) / scale_D / r_scale])
    A = A * w[:, None]
    y = (r / r_scale) * w
    n_num = Phi_N.shape[1]

    best: RationalModel | None = None
    best_aicc = float("inf")
    n = len(r)

    for thr in thresholds:
        xi = stlsq(A, y, thr)
        a0 = xi[:n_num] / scale_N * r_scale
        b0 = xi[n_num:] / scale_D
        if not np.any(np.abs(a0) > 0):
            continue
        keep_a = np.abs(a0) > 0
        keep_b = np.abs(b0) > 0

        for q in q_values:
            model, aicc_val = _refine(
                numerator,
                denominator,
                a0,
                b0,
                keep_a,
                keep_b,
                q,
                C,
                r,
                species,
                fit_q,
                n,
            )
            if model is not None and aicc_val < best_aicc:
                best_aicc = aicc_val
                pred = model.predict(C)
                ss_tot = float(np.sum((r - r.mean()) ** 2))
                model.r2 = (
                    1.0 - float(np.sum((r - pred) ** 2)) / ss_tot
                    if ss_tot > 0
                    else float("nan")
                )
                best = model

    if best is None:
        raise RuntimeError("nenhuma estrutura racional pôde ser ajustada")
    return best


def _refine(
    numerator: list[Feature],
    denominator: list[Feature],
    a0: np.ndarray,
    b0: np.ndarray,
    keep_a: np.ndarray,
    keep_b: np.ndarray,
    q: float,
    C: np.ndarray,
    r: np.ndarray,
    species: tuple[str, ...],
    fit_q: bool,
    n: int,
) -> tuple[RationalModel | None, float]:
    """Reajusta os coeficientes selecionados sobre o resíduo verdadeiro."""
    Phi_N = _design(numerator, C, species)[:, keep_a]
    Phi_D = _design(denominator, C, species)[:, keep_b]
    n_a, n_b = int(keep_a.sum()), int(keep_b.sum())
    if n_a == 0:
        return None, float("inf")

    x0 = np.concatenate([a0[keep_a], b0[keep_b], [q] if fit_q else []])
    r_scale = float(np.max(np.abs(r))) or 1.0

    def residual(x: np.ndarray) -> np.ndarray:
        a = x[:n_a]
        b = x[n_a : n_a + n_b]
        qq = x[-1] if fit_q else q
        D = 1.0 + (Phi_D @ b if n_b else 0.0)
        D = np.where(D < 1e-9, 1e-9, D)
        return ((Phi_N @ a) / D**qq - r) / r_scale

    lo = np.concatenate(
        [np.full(n_a, -np.inf), np.zeros(n_b), [0.5] if fit_q else []]
    )
    hi = np.concatenate(
        [np.full(n_a, np.inf), np.full(n_b, np.inf), [3.0] if fit_q else []]
    )
    try:
        sol = least_squares(
            residual, np.clip(x0, lo, hi), bounds=(lo, hi), max_nfev=4000
        )
    except Exception:  # noqa: BLE001 - estrutura degenerada
        return None, float("inf")

    sse = float(np.sum((sol.fun * r_scale) ** 2))
    p = n_a + n_b + (1 if fit_q else 0)
    if sse <= 0 or n - p - 1 <= 0:
        return None, float("inf")
    aicc_val = n * np.log(sse / n) + 2 * p + 2 * p * (p + 1) / (n - p - 1)

    a_full = np.zeros(len(numerator))
    b_full = np.zeros(len(denominator))
    a_full[keep_a] = sol.x[:n_a]
    b_full[keep_b] = sol.x[n_a : n_a + n_b]
    model = RationalModel(
        numerator=numerator,
        denominator=denominator,
        a=a_full,
        b=b_full,
        q=float(sol.x[-1]) if fit_q else q,
        species=species,
        n_terms=p,
    )
    return model, float(aicc_val)
