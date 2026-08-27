"""Estimação de parâmetros por mínimos quadrados ponderados.

Decisões que fazem diferença prática na convergência:

*Ponderação relativa.* Os resíduos são divididos pela escala de cada
espécie. Sem isso o triglicerídeo domina a soma e os intermediários — que
são justamente os que carregam informação sobre o mecanismo — não pesam.

*Múltiplas partidas.* A superfície de mínimos quadrados de modelos LHHW é
notoriamente multimodal. Uma única partida encontra um mínimo local e o
ranqueamento de modelos passa a refletir a sorte do chute inicial, não a
qualidade dos modelos. Aqui se amostra o espaço de partida por sequência
de Sobol e se retém o melhor mínimo.

*Diagnóstico de identificabilidade.* Um ajuste excelente com matriz
``J'J`` mal condicionada significa parâmetros redundantes: o modelo tem
graus de liberdade que os dados não sustentam. Isso é reportado junto com
o ajuste, não escondido.
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import qmc, t as student_t

from .data import Dataset, Experiment
from .network import KineticNetwork
from .parameters import KIND_EXPONENT, Parameterization
from .reactor import IntegrationFailure, simulate_batch, simulate_monolith
from .species import FLUID_SPECIES

#: Valor atribuído a resíduos quando a integração falha.
PENALTY = 1e3


@dataclass
class FitResult:
    """Resultado da regressão de um modelo sobre um conjunto de dados."""

    model_id: str
    family: str
    rds_label: str
    network: KineticNetwork
    parameterization: Parameterization
    x: np.ndarray
    residuals: np.ndarray
    sse: float
    n_obs: int
    n_params: int
    success: bool
    message: str = ""
    std_errors: np.ndarray | None = None
    ci95: np.ndarray | None = None
    correlation: np.ndarray | None = None
    condition_number: float = float("inf")
    n_starts: int = 0
    elapsed_s: float = 0.0
    notes: str = ""

    @property
    def dof(self) -> int:
        return max(self.n_obs - self.n_params, 1)

    @property
    def mse(self) -> float:
        return self.sse / self.dof

    @property
    def rmse(self) -> float:
        return float(np.sqrt(self.sse / max(self.n_obs, 1)))

    @property
    def free_names(self) -> list[str]:
        return self.parameterization.free_names

    def values_at(self, T: float) -> dict[str, float]:
        return self.parameterization.values_at(self.x, T)

    def pvec_at(self, T: float) -> np.ndarray:
        v = self.values_at(T)
        return np.array([v[n] for n in self.network.param_names])

    @property
    def at_bound(self) -> np.ndarray:
        """Máscara dos parâmetros que pararam num limite da busca.

        Um parâmetro no limite não tem intervalo de confiança válido — a
        aproximação quadrática da verossimilhança pressupõe um mínimo
        interior. Em geral sinaliza que o termo é dispensável (o otimizador
        o está empurrando para zero ou para infinito) ou que os limites
        estão mal postos.
        """
        lo, hi = self.parameterization.bounds()
        tol = 1e-6 * np.maximum(np.abs(hi - lo), 1.0)
        return (self.x - lo < tol) | (hi - self.x < tol)

    @property
    def unidentifiable(self) -> np.ndarray:
        """Parâmetros cujo IC 95% é largo demais para ter significado.

        O limiar depende da natureza do parâmetro, porque as escalas não
        são comparáveis: ``ln k`` é adimensional, uma energia está em
        kJ/mol e uma ordem de reação é um número perto de 1.

        * logaritmos: intervalo maior que 2 — mais de um fator ~7 para cada
          lado, o que já não distingue mecanismos;
        * energias: intervalo maior que 30 kJ/mol ou que o próprio valor —
          nesse ponto nem o sinal está garantido;
        * expoentes: intervalo maior que 0,5 — não separa ordem 1 de ordem 2.
        """
        if self.ci95 is None:
            return np.ones(len(self.x), dtype=bool)
        out = np.zeros(len(self.x), dtype=bool)
        for i, nm in enumerate(self.free_names):
            ci = self.ci95[i]
            if nm.startswith("E["):
                out[i] = ci > max(30.0, abs(self.x[i]))
            elif nm.startswith("ln("):
                out[i] = ci > 2.0
            else:
                out[i] = ci > 0.5
        return out | self.at_bound

    @property
    def significant(self) -> np.ndarray:
        """Máscara dos parâmetros cujo IC 95% não contém zero.

        Para parâmetros estimados em escala logarítmica o teste é sobre o
        próprio logaritmo — um IC que cruza zero em ``ln K`` significa
        apenas ``K ~ 1``, o que é admissível. Por isso o critério só se
        aplica a energias e expoentes.
        """
        if self.ci95 is None:
            return np.ones(len(self.x), dtype=bool)
        out = np.ones(len(self.x), dtype=bool)
        for i, nm in enumerate(self.free_names):
            if nm.startswith("E["):
                out[i] = abs(self.x[i]) > self.ci95[i]
        return out

    def summary(self) -> str:
        lines = [
            f"{self.model_id}",
            f"  família {self.family} | RDS {self.rds_label} | "
            f"{self.n_params} parâmetros | {self.n_obs} obs",
            f"  SSE={self.sse:.5g}  RMSE={self.rmse:.4g}  "
            f"cond(J'J)={self.condition_number:.3g}",
        ]
        if self.std_errors is not None:
            bad = self.unidentifiable
            lines.append(
                f"  {'parâmetro':>16s} {'estimativa':>12s} {'± IC95%':>12s}   nota"
            )
            for i, nm in enumerate(self.free_names):
                note = ""
                if self.at_bound[i]:
                    note = "no limite da busca"
                elif bad[i]:
                    note = "não identificável"
                lines.append(
                    f"  {nm:>16s} {self.x[i]:12.4g} {self.ci95[i]:12.3g}   {note}"
                )
            n_bad = int(bad.sum())
            if n_bad:
                lines.append(
                    f"  {n_bad} de {len(self.x)} parâmetros mal determinados — "
                    "considere fixá-los ou simplificar o modelo"
                )
        return "\n".join(lines)


# ----------------------------------------------------------------------
# resíduos
# ----------------------------------------------------------------------
def _simulate(
    net: KineticNetwork, pvec: np.ndarray, exp: Experiment, mode: str
) -> np.ndarray:
    if exp.t[-1] <= 0:
        return np.tile(exp.C0, (len(exp.t), 1))
    if exp.reactor == "monolith":
        return simulate_monolith(net, pvec, exp.C0, exp.t, exp.operation, mode=mode)
    return simulate_batch(net, pvec, exp.C0, exp.t, exp.catalyst_g_L)


def build_residual_function(
    net: KineticNetwork,
    dataset: Dataset,
    par: Parameterization,
    mode: str = "ideal",
):
    """Devolve ``f(x) -> vetor de resíduos ponderados`` e seu comprimento."""
    masks = [np.isfinite(e.Y) for e in dataset]
    scales = [e.scale() for e in dataset]
    n_res = int(sum(m.sum() for m in masks))

    def residual(x: np.ndarray) -> np.ndarray:
        out: list[np.ndarray] = []
        for exp, mask, scale in zip(dataset, masks, scales):
            values = par.values_at(x, exp.T_K)
            pvec = np.array([values[n] for n in net.param_names])
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    prof = _simulate(net, pvec, exp, mode)
            except (IntegrationFailure, ValueError, ArithmeticError, OverflowError):
                return np.full(n_res, PENALTY)
            if not np.all(np.isfinite(prof)):
                return np.full(n_res, PENALTY)
            out.append(((prof - exp.Y) / scale)[mask])
        r = np.concatenate(out) if out else np.zeros(0)
        return np.where(np.isfinite(r), r, PENALTY)

    return residual, n_res


# ----------------------------------------------------------------------
# chutes iniciais
# ----------------------------------------------------------------------
def suggest_initial_values(dataset: Dataset) -> dict[str, float]:
    """Ordem de grandeza inicial para ``k`` e ``K_ads``, tirada dos dados.

    Estima a velocidade média de consumo de triglicerídeo e divide pelo
    produto de concentrações típico. Não pretende ser precisa — só evitar
    que a partida esteja dez ordens de grandeza longe, que é o que trava a
    convergência de modelos LHHW.
    """
    iTG, iM = FLUID_SPECIES.index("TG"), FLUID_SPECIES.index("M")
    rates, cprod = [], []
    for e in dataset:
        col = e.Y[:, iTG]
        ok = np.isfinite(col)
        if ok.sum() < 2 or e.t[-1] <= 0:
            continue
        dC = float(col[ok][0] - col[ok][-1])
        dt = float(e.t[ok][-1] - e.t[ok][0])
        if dt <= 0 or e.catalyst_g_L <= 0:
            continue
        rates.append(abs(dC) / (dt * e.catalyst_g_L))
        cprod.append(max(e.C0[iTG] * e.C0[iM], 1e-6))
    if not rates:
        return {"k": 1e-3, "K_ads": 0.2}
    k0 = float(np.median(np.asarray(rates) / np.asarray(cprod)))
    cM = float(np.median([e.C0[iM] for e in dataset])) or 1.0
    return {"k": max(k0, 1e-9), "K_ads": 1.0 / cM}


def make_parameterization(
    net: KineticNetwork,
    dataset: Dataset,
    non_isothermal: bool | None = None,
    fixed: dict[str, float] | None = None,
) -> Parameterization:
    """Parametrização com valores iniciais ancorados nos dados.

    ``fixed`` congela parâmetros num valor conhecido. O uso típico é fixar
    as constantes de equilíbrio: numa faixa de conversão longe do
    equilíbrio o termo reverso quase não influencia a velocidade, e tentar
    estimar ``Keq`` a partir desses dados produz intervalos de confiança
    largos que contaminam a comparação entre modelos. Quando se dispõe de
    ``Keq`` por via termodinâmica ou de ensaios longos até o equilíbrio,
    fixá-lo é a decisão correta.
    """
    non_iso = dataset.is_non_isothermal if non_isothermal is None else non_isothermal
    par = Parameterization.for_names(net.param_names, dataset.T_ref, non_iso)
    guess = suggest_initial_values(dataset)
    for spec in list(par.specs):
        if spec.kind == KIND_EXPONENT:
            continue
        if spec.name.startswith("k"):
            par.update(spec.name, value=guess["k"])
        elif spec.name.startswith("K_ads"):
            par.update(spec.name, value=guess["K_ads"])
        elif spec.name.startswith("Keq"):
            par.update(spec.name, value=3.0)
        else:  # K_sr, K_form, K_dec ...
            par.update(spec.name, value=1.0)
    for name, value in (fixed or {}).items():
        if name in net.param_names:
            par.update(name, value=value, fit_value=False, fit_energy=False)
    return par


def _start_points(
    par: Parameterization, n_starts: int, seed: int, spread: float = 3.0
) -> np.ndarray:
    """Pontos de partida por sequência de Sobol em torno do chute central.

    A busca é centrada no chute ancorado nos dados e alargada por ``spread``
    décadas naturais em escala logarítmica; energias varrem sua faixa
    admissível inteira.
    """
    x0 = par.pack()
    lo_hard, hi_hard = par.bounds()
    lo = np.maximum(x0 - spread, lo_hard)
    hi = np.minimum(x0 + spread, hi_hard)
    for i, nm in enumerate(par.free_names):
        if nm.startswith("E["):
            lo[i], hi[i] = lo_hard[i], hi_hard[i]
    lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)

    if n_starts <= 1:
        return x0[None, :]
    sampler = qmc.Sobol(d=len(x0), scramble=True, seed=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pts = sampler.random(n_starts - 1)
    return np.vstack([x0, lo + pts * (hi - lo)])


# ----------------------------------------------------------------------
# ajuste
# ----------------------------------------------------------------------
def fit_network(
    net: KineticNetwork,
    dataset: Dataset,
    mode: str = "ideal",
    n_starts: int = 8,
    seed: int = 0,
    max_nfev: int = 2000,
    non_isothermal: bool | None = None,
    fixed: dict[str, float] | None = None,
    x0: np.ndarray | None = None,
    time_budget_s: float = 60.0,
) -> FitResult:
    """Ajusta uma rede cinética ao conjunto de dados por regressão integral.

    ``x0`` semeia a busca. O uso previsto é passar a solução do ajuste
    diferencial: ela já está na bacia de atração correta, e a regressão
    integral — cara, porque integra a rede a cada avaliação — converge em
    poucas iterações em vez de partir do zero.

    ``time_budget_s`` limita o tempo gasto por modelo: numa varredura de
    dezenas de candidatos, um modelo patológico não pode consumir a
    varredura inteira.
    """
    t_start = time.perf_counter()
    par = make_parameterization(net, dataset, non_isothermal, fixed)
    residual, n_res = build_residual_function(net, dataset, par, mode)
    lo, hi = par.bounds()
    starts = _start_points(par, n_starts, seed)
    if x0 is not None and len(x0) == par.n_free:
        starts = np.vstack([np.asarray(x0, dtype=float)[None, :], starts])

    best = None
    used = 0
    for x0 in starts:
        if time.perf_counter() - t_start > time_budget_s and best is not None:
            break
        used += 1
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = least_squares(
                    residual,
                    np.clip(x0, lo, hi),
                    bounds=(lo, hi),
                    method="trf",
                    max_nfev=max_nfev,
                    xtol=1e-10,
                    ftol=1e-12,
                )
        except Exception:  # noqa: BLE001 - modelo patológico: descarta a partida
            continue
        if best is None or res.cost < best.cost:
            best = res

    elapsed = time.perf_counter() - t_start
    if best is None:
        return FitResult(
            model_id=net.model_id,
            family=net.family,
            rds_label=net.rds_label,
            network=net,
            parameterization=par,
            x=par.pack(),
            residuals=np.full(n_res, PENALTY),
            sse=float(PENALTY**2 * n_res),
            n_obs=n_res,
            n_params=par.n_free,
            success=False,
            message="nenhuma partida convergiu",
            n_starts=used,
            elapsed_s=elapsed,
        )

    r = np.asarray(best.fun)
    sse = float(np.sum(r**2))
    stats = _covariance(best.jac, sse, n_res, par.n_free)
    return FitResult(
        model_id=net.model_id,
        family=net.family,
        rds_label=net.rds_label,
        network=net,
        parameterization=par,
        x=np.asarray(best.x),
        residuals=r,
        sse=sse,
        n_obs=n_res,
        n_params=par.n_free,
        success=bool(best.success) and sse < (PENALTY**2 * n_res) * 0.5,
        message=str(best.message),
        std_errors=stats[0],
        ci95=stats[1],
        correlation=stats[2],
        condition_number=stats[3],
        n_starts=used,
        elapsed_s=elapsed,
        notes=net.notes,
    )


def _covariance(
    jac: np.ndarray, sse: float, n_obs: int, n_par: int
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, float]:
    """Covariância aproximada ``s^2 (J'J)^-1`` e diagnóstico de condição."""
    try:
        J = np.asarray(jac, dtype=float)
        JTJ = J.T @ J
        cond = float(np.linalg.cond(JTJ))
        dof = max(n_obs - n_par, 1)
        s2 = sse / dof
        cov = s2 * np.linalg.pinv(JTJ, rcond=1e-12)
        se = np.sqrt(np.clip(np.diag(cov), 0.0, None))
        ci = student_t.ppf(0.975, dof) * se
        with np.errstate(divide="ignore", invalid="ignore"):
            corr = cov / np.outer(se, se)
        corr = np.where(np.isfinite(corr), corr, 0.0)
        return se, ci, corr, cond
    except np.linalg.LinAlgError:
        return None, None, None, float("inf")


# ----------------------------------------------------------------------
# ajuste diferencial (triagem rápida)
# ----------------------------------------------------------------------
def build_differential_residual(net: KineticNetwork, table, par: Parameterization):
    """Resíduos contra velocidades extraídas dos dados, sem integrar ODE.

    O método diferencial compara a ``r`` calculada pelo modelo com a ``r``
    obtida por derivação dos perfis medidos. Custa cerca de três ordens de
    grandeza menos que a regressão integral, porque tira a integração
    numérica de dentro do laço do otimizador. Em troca herda o ruído
    amplificado pela diferenciação — por isso serve para *triagem*, e o
    ranqueamento final deve sair da regressão integral sobre os
    sobreviventes.
    """
    C = np.asarray(table.C, dtype=float)
    T = np.asarray(table.T, dtype=float)
    groups = [(t, np.flatnonzero(T == t)) for t in np.unique(T)]

    # Comparar dC/dt diretamente, em vez das velocidades obtidas por
    # pseudo-inversa, evita amplificar o ruído duas vezes e usa a
    # informação das seis espécies em vez de projetá-la em três.
    target = np.asarray(table.dCdt, dtype=float)
    scale = np.maximum(np.abs(target).max(axis=0), 1e-30)
    n_res = target.size
    nu_T = net.nu.T  # (3, n_espécies)

    def residual(x: np.ndarray) -> np.ndarray:
        out = np.empty_like(target)
        for temp, idx in groups:
            values = par.values_at(x, float(temp))
            pvec = np.array([values[n] for n in net.param_names])
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    out[idx] = net.rates_batch(C[idx], pvec) @ nu_T
            except (ValueError, ArithmeticError, OverflowError):
                return np.full(n_res, PENALTY)
        res = ((out - target) / scale).ravel()
        return np.where(np.isfinite(res), res, PENALTY)

    return residual, n_res


def fit_differential(
    net: KineticNetwork,
    dataset: Dataset,
    table,
    n_starts: int = 12,
    seed: int = 0,
    max_nfev: int = 3000,
    non_isothermal: bool | None = None,
    fixed: dict[str, float] | None = None,
    time_budget_s: float = 20.0,
) -> FitResult:
    """Triagem rápida de um modelo pelo método diferencial."""
    t_start = time.perf_counter()
    par = make_parameterization(net, dataset, non_isothermal, fixed)
    residual, n_res = build_differential_residual(net, table, par)
    lo, hi = par.bounds()
    starts = _start_points(par, n_starts, seed)

    best, used = None, 0
    for x0 in starts:
        if time.perf_counter() - t_start > time_budget_s and best is not None:
            break
        used += 1
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = least_squares(
                    residual,
                    np.clip(x0, lo, hi),
                    bounds=(lo, hi),
                    method="trf",
                    x_scale="jac",
                    max_nfev=max_nfev,
                    xtol=1e-10,
                    ftol=1e-12,
                )
        except Exception:  # noqa: BLE001 - modelo patológico: descarta a partida
            continue
        if best is None or res.cost < best.cost:
            best = res

    elapsed = time.perf_counter() - t_start
    if best is None:
        return FitResult(
            model_id=net.model_id,
            family=net.family,
            rds_label=net.rds_label,
            network=net,
            parameterization=par,
            x=par.pack(),
            residuals=np.full(n_res, PENALTY),
            sse=float(PENALTY**2 * n_res),
            n_obs=n_res,
            n_params=par.n_free,
            success=False,
            message="nenhuma partida convergiu",
            n_starts=used,
            elapsed_s=elapsed,
            notes="ajuste diferencial",
        )

    r = np.asarray(best.fun)
    sse = float(np.sum(r**2))
    se, ci, corr, cond = _covariance(best.jac, sse, n_res, par.n_free)
    return FitResult(
        model_id=net.model_id,
        family=net.family,
        rds_label=net.rds_label,
        network=net,
        parameterization=par,
        x=np.asarray(best.x),
        residuals=r,
        sse=sse,
        n_obs=n_res,
        n_params=par.n_free,
        success=bool(best.success) and sse < (PENALTY**2 * n_res) * 0.5,
        message=str(best.message),
        std_errors=se,
        ci95=ci,
        correlation=corr,
        condition_number=cond,
        n_starts=used,
        elapsed_s=elapsed,
        notes="ajuste diferencial",
    )
