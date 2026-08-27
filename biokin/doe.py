"""Planejamento de experimentos para discriminar mecanismos.

Quando dois modelos empatam nos dados existentes, mais réplicas das
mesmas condições não resolvem — só reduzem a barra de erro de um empate.
O que resolve é escolher a condição em que os modelos **discordam mais**,
relativamente à incerteza com que cada um prevê.

Dois critérios:

**Hunter-Reiner** — maximiza a discrepância quadrática entre as previsões,
ponderada pelas probabilidades dos modelos. Simples, barato e já bastante
eficaz.

**Box-Hill** — maximiza a redução esperada da entropia de Shannon sobre as
probabilidades dos modelos, levando em conta tanto a discrepância entre
previsões quanto a incerteza de cada previsão (pelo método delta, sobre a
covariância dos parâmetros). Um ponto onde os modelos discordam muito mas
ambos preveem com enorme incerteza discrimina pouco; o Box-Hill sabe
disso, o Hunter-Reiner não.

Também há o critério **D-ótimo**, que não discrimina: ele refina os
parâmetros do modelo já escolhido. É o passo seguinte, depois que a
discriminação terminou.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .data import Experiment
from .discrimination import ModelScore
from .estimation import FitResult
from .reactor import MonolithOperation, simulate_batch, simulate_monolith
from .species import FLUID_SPECIES
from .synthetic import Condition


def _simulate_condition(
    fit: FitResult, cond: Condition, mode: str = "ideal"
) -> np.ndarray:
    """Perfil previsto por um modelo ajustado numa condição candidata."""
    values = fit.values_at(cond.T_K)
    pvec = np.array([values[n] for n in fit.network.param_names])
    C0 = cond.initial()
    t = np.asarray(cond.times_min, dtype=float)
    if cond.reactor == "monolith":
        op = MonolithOperation(
            velocity_m_s=cond.velocity_m_s, geometry=cond.geometry
        )
        return simulate_monolith(fit.network, pvec, C0, t, op, mode=mode)
    return simulate_batch(fit.network, pvec, C0, t, cond.catalyst_g_L)


def predict(
    fit: FitResult,
    cond: Condition,
    measured: tuple[str, ...],
    mode: str = "ideal",
) -> np.ndarray:
    """Vetor achatado das respostas medidas previstas pelo modelo."""
    idx = [FLUID_SPECIES.index(s) for s in measured]
    try:
        prof = _simulate_condition(fit, cond, mode)
    except Exception:  # noqa: BLE001 - condição fora do domínio do modelo
        return np.full(len(cond.times_min) * len(idx), np.nan)
    return prof[:, idx].ravel()


def prediction_covariance_diagonal(
    fit: FitResult,
    cond: Condition,
    measured: tuple[str, ...],
    mode: str = "ideal",
    rel_step: float = 1e-4,
) -> np.ndarray:
    """Variância de previsão por método delta: ``diag(G Σ G')``.

    ``G`` é a sensibilidade da resposta aos parâmetros, obtida por
    diferenças finitas, e ``Σ`` a covariância dos parâmetros estimados. É a
    incerteza que o modelo tem sobre a própria previsão naquela condição —
    a peça que distingue Box-Hill de Hunter-Reiner.
    """
    y0 = predict(fit, cond, measured, mode)
    if fit.std_errors is None or not np.all(np.isfinite(y0)):
        return np.zeros_like(y0)

    n_par = len(fit.x)
    G = np.zeros((len(y0), n_par))
    for i in range(n_par):
        step = rel_step * max(abs(fit.x[i]), 1.0)
        x_pert = fit.x.copy()
        x_pert[i] += step
        perturbed = FitResultView(fit, x_pert)
        y1 = predict(perturbed, cond, measured, mode)  # type: ignore[arg-type]
        if np.all(np.isfinite(y1)):
            G[:, i] = (y1 - y0) / step

    se = np.asarray(fit.std_errors)
    corr = fit.correlation
    if corr is None:
        cov = np.diag(se**2)
    else:
        cov = corr * np.outer(se, se)
    return np.clip(np.einsum("ij,jk,ik->i", G, cov, G), 0.0, None)


@dataclass
class FitResultView:
    """Vista de um ajuste com outro vetor de parâmetros.

    Evita copiar o ajuste inteiro só para perturbar um parâmetro no
    cálculo de sensibilidades.
    """

    base: FitResult
    x: np.ndarray

    def __post_init__(self) -> None:
        self.network = self.base.network
        self.parameterization = self.base.parameterization

    def values_at(self, T: float) -> dict[str, float]:
        return self.parameterization.values_at(self.x, T)


# ----------------------------------------------------------------------
@dataclass
class DesignScore:
    """Valor de um candidato experimental segundo cada critério."""

    condition: Condition
    hunter_reiner: float
    box_hill: float
    max_divergence: float
    n_responses: int

    @property
    def label(self) -> str:
        return self.condition.label


@dataclass
class DesignRanking:
    scores: list[DesignScore]
    criterion: str
    models: list[str] = field(default_factory=list)

    def table(self, top: int = 10) -> str:
        key = "box_hill" if self.criterion == "box_hill" else "hunter_reiner"
        rows = sorted(self.scores, key=lambda s: -getattr(s, key))[:top]
        best = getattr(rows[0], key) if rows else 1.0
        best = best if best > 0 else 1.0
        head = (
            f"{'#':>3s} {'condição':<26s} {'T [°C]':>7s} {'M:TG':>6s} "
            f"{'Box-Hill':>10s} {'Hunter-R':>10s} {'relativo':>9s}"
        )
        lines = [head, "-" * len(head)]
        for i, s in enumerate(rows, start=1):
            lines.append(
                f"{i:>3d} {s.label[:26]:<26s} {s.condition.T_K - 273.15:>7.1f} "
                f"{s.condition.molar_ratio:>6.1f} {s.box_hill:>10.4g} "
                f"{s.hunter_reiner:>10.4g} {getattr(s, key) / best:>9.3f}"
            )
        return "\n".join(lines)

    @property
    def best(self) -> DesignScore | None:
        key = "box_hill" if self.criterion == "box_hill" else "hunter_reiner"
        return max(self.scores, key=lambda s: getattr(s, key)) if self.scores else None


def discrimination_design(
    scores: list[ModelScore],
    candidates: list[Condition],
    measured: tuple[str, ...] = ("TG", "DG", "MG", "E", "G"),
    sigma: float = 0.02,
    criterion: str = "box_hill",
    mode: str = "ideal",
    top_models: int = 4,
) -> DesignRanking:
    """Ordena condições candidatas pelo poder de discriminar os modelos.

    ``scores`` deve vir de :func:`biokin.discrimination.rank_models`; só os
    ``top_models`` primeiros admissíveis entram no cálculo — modelos com
    probabilidade desprezível não mudam o planejamento e custam tempo.

    ``sigma`` é o desvio-padrão do erro experimental na escala das
    concentrações medidas. Ele calibra o quanto vale a pena discordar: uma
    divergência de 0,01 mol/L é decisiva se a análise tem precisão de
    0,002 mol/L e irrelevante se tem 0,05.
    """
    admissible = [s for s in scores if s.admissible][:top_models]
    if len(admissible) < 2:
        raise ValueError(
            "discriminação requer ao menos dois modelos admissíveis; "
            f"há {len(admissible)}"
        )
    pi = np.array([s.weight for s in admissible], dtype=float)
    pi = pi / pi.sum() if pi.sum() > 0 else np.full(len(admissible), 1.0 / len(admissible))

    out: list[DesignScore] = []
    s2 = sigma**2
    for cond in candidates:
        preds = [predict(s.fit, cond, measured, mode) for s in admissible]
        if any(not np.all(np.isfinite(p)) for p in preds):
            continue
        if criterion == "box_hill":
            var = [
                prediction_covariance_diagonal(s.fit, cond, measured, mode)
                for s in admissible
            ]
        else:
            var = [np.zeros_like(p) for p in preds]

        hr = 0.0
        bh = 0.0
        maxdiv = 0.0
        for i in range(len(admissible)):
            for j in range(i + 1, len(admissible)):
                d2 = (preds[i] - preds[j]) ** 2
                hr += float(pi[i] * pi[j] * d2.sum())
                maxdiv = max(maxdiv, float(np.sqrt(d2.max())))
                si, sj = var[i], var[j]
                # critério de Box-Hill, forma para resposta univariada
                # somada sobre as respostas independentes
                term = (si - sj) * (1.0 / (s2 + sj) - 1.0 / (s2 + si)) + d2 * (
                    1.0 / (s2 + si) + 1.0 / (s2 + sj)
                )
                bh += float(0.5 * pi[i] * pi[j] * np.sum(term))
        out.append(
            DesignScore(
                condition=cond,
                hunter_reiner=hr,
                box_hill=bh,
                max_divergence=maxdiv,
                n_responses=len(preds[0]),
            )
        )
    return DesignRanking(out, criterion, [s.model_id for s in admissible])


def d_optimal_design(
    fit: FitResult,
    candidates: list[Condition],
    measured: tuple[str, ...] = ("TG", "DG", "MG", "E", "G"),
    mode: str = "ideal",
    rel_step: float = 1e-4,
) -> list[tuple[Condition, float]]:
    """Ordena candidatos por ganho de precisão nos parâmetros (D-ótimo).

    Devolve ``log det(J'J)`` do experimento candidato isolado. Use depois
    da discriminação, para refinar o modelo vencedor — não para escolher
    entre modelos.
    """
    out: list[tuple[Condition, float]] = []
    y0_cache: dict[str, np.ndarray] = {}
    for cond in candidates:
        y0 = predict(fit, cond, measured, mode)
        if not np.all(np.isfinite(y0)):
            continue
        y0_cache[cond.label] = y0
        G = np.zeros((len(y0), len(fit.x)))
        for i in range(len(fit.x)):
            step = rel_step * max(abs(fit.x[i]), 1.0)
            xp = fit.x.copy()
            xp[i] += step
            y1 = predict(FitResultView(fit, xp), cond, measured, mode)  # type: ignore[arg-type]
            if np.all(np.isfinite(y1)):
                G[:, i] = (y1 - y0) / step
        M = G.T @ G
        sign, logdet = np.linalg.slogdet(M + 1e-12 * np.eye(M.shape[0]))
        out.append((cond, float(logdet) if sign > 0 else -np.inf))
    return sorted(out, key=lambda p: -p[1])


def candidate_grid(
    temperatures: tuple[float, ...] = (323.15, 333.15, 343.15, 353.15),
    molar_ratios: tuple[float, ...] = (3.0, 6.0, 9.0, 12.0, 20.0),
    catalyst_g_L: tuple[float, ...] = (5.0, 10.0, 20.0),
    spikes: tuple[tuple[float, float], ...] = ((0.0, 0.0), (0.4, 0.0), (0.0, 1.0)),
    times_min: np.ndarray | None = None,
    C_TG0: float = 0.9,
) -> list[Condition]:
    """Grade de condições candidatas em batelada.

    Inclui deliberadamente razões molares extremas (3:1 estequiométrico e
    20:1): é onde os denominadores LHHW mais divergem entre si, porque a
    cobertura por metanol varia de baixa a saturante.

    ``spikes`` são pares ``(C_G0, C_E0)`` de glicerol e éster adicionados à
    alimentação. Numa corrida que parte de óleo puro, glicerol e éster
    crescem juntos com a conversão — são colineares, e nenhuma técnica
    consegue atribuir a inibição a um ou a outro. Adicionar um deles de
    saída é o que torna os dois termos separáveis, e por isso essas
    condições costumam dominar o ranqueamento discriminatório.
    """
    t = np.array([0, 5, 10, 20, 30, 45, 60, 90, 120.0]) if times_min is None else times_min
    out: list[Condition] = []
    for T in temperatures:
        for ratio in molar_ratios:
            for w in catalyst_g_L:
                for cg, ce in spikes:
                    tag = ""
                    if cg > 0:
                        tag += f"-G{cg:g}"
                    if ce > 0:
                        tag += f"-E{ce:g}"
                    out.append(
                        Condition(
                            label=f"T{T - 273.15:.0f}-R{ratio:.0f}-w{w:.0f}{tag}",
                            T_K=T,
                            molar_ratio=ratio,
                            C_TG0=C_TG0,
                            C_G0=cg,
                            C_E0=ce,
                            catalyst_g_L=w,
                            times_min=t,
                        )
                    )
    return out
