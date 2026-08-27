"""Varredura completa: da tabela de dados ao mecanismo mais provável.

O fluxo implementado aqui é o que torna a busca praticável. Uma regressão
integral (que integra a rede de EDOs a cada avaliação de resíduo) sobre
quarenta candidatos com dez parâmetros cada levaria horas. A saída é a
mesma que a prática experimental consagrou:

1. **Diagnóstico de transporte.** Antes de qualquer cinética: os dados
   podem ser lidos como intrínsecos? Se não, a discriminação roda no modo
   que inclui difusão, ou não roda.

2. **Extração de dados diferenciais.** Perfis suavizados, derivadas, e
   inversão da estequiometria.

3. **Referências sem mecanismo.** Rede neural (teto de desempenho) e
   regressão racional esparsa (forma funcional sugerida pelos dados).

4. **Triagem diferencial.** Todos os candidatos, ajustados ao dado
   diferencial. Barato: fração de segundo por modelo.

5. **Refino integral.** Só os sobreviventes, semeados pela triagem, com a
   regressão integral que é a que vale para o ranqueamento final.

6. **Discriminação e planejamento.** Critérios de informação, filtros
   termodinâmicos, e — se o topo estiver empatado — as condições
   experimentais que resolveriam o empate.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .data import Dataset
from .discrimination import ModelScore, Ranking, rank_models
from .doe import (
    DesignRanking,
    candidate_grid,
    d_optimal_design,
    discrimination_design,
)
from .estimation import FitResult, fit_differential, fit_network
from .library import DEFAULT_INHIBITION_SETS, FAMILIES, build_catalog, enumerate_rate_laws
from .ml.mlp import MLP
from .ml.sparse import (
    RationalConsensus,
    fit_rational_by_temperature,
    rational_library,
)
from .ml.surrogate import (
    CollinearityReport,
    RateTable,
    collinearity_report,
    estimate_rate_table,
)
from .network import KineticNetwork, build_network
from .species import FLUID_SPECIES
from .transport import TransportDiagnostics, diagnose


@dataclass
class ScreeningConfig:
    """Parâmetros da varredura."""

    families: tuple[str, ...] = tuple(FAMILIES)
    inhibition_sets: tuple[tuple[str, ...], ...] = DEFAULT_INHIBITION_SETS
    include_empirical: bool = True
    fixed: dict[str, float] | None = None
    mode: str = "ideal"  # 'ideal' | 'film' | 'full'
    n_starts_differential: int = 12
    n_starts_integral: int = 2
    n_refine: int = 6
    differential_budget_s: float = 15.0
    integral_budget_s: float = 240.0
    run_ml_baseline: bool = True
    run_sparse: bool = True
    run_design: bool = True
    max_design_candidates: int = 60
    """Teto de condições avaliadas no planejamento discriminatório.

    O critério de Box-Hill precisa da sensibilidade da previsão a cada
    parâmetro em cada condição, o que custa uma integração da rede por
    parâmetro por condição por modelo. A grade completa tem 180 condições;
    uma subamostra determinística cobre o espaço igualmente bem por uma
    fração do custo. Aumente se quiser a varredura exaustiva.
    """
    mlp_epochs: int = 2500
    ml_folds: int = 5
    seed: int = 0


@dataclass
class MLBaseline:
    """Desempenho da referência sem mecanismo."""

    r2_per_reaction: list[float] = field(default_factory=list)
    n_parameters: int = 0
    n_folds: int = 0
    hidden: tuple[int, ...] = ()

    @property
    def r2_mean(self) -> float:
        vals = [v for v in self.r2_per_reaction if np.isfinite(v)]
        return float(np.mean(vals)) if vals else float("nan")

    def report(self) -> str:
        per = "  ".join(
            f"R{j + 1}={v:.4f}" for j, v in enumerate(self.r2_per_reaction)
        )
        return (
            f"  rede neural {self.hidden} — {self.n_parameters} pesos, "
            f"validação cruzada em {self.n_folds} dobras\n"
            f"  R² fora da amostra: {per}\n"
            f"  R² médio = {self.r2_mean:.4f} — teto alcançável por uma função "
            "flexível sem estrutura mecanística. Um modelo cinético que chegue "
            "perto capturou o que há nos dados."
        )


@dataclass
class ScreeningResult:
    """Tudo o que a varredura produziu."""

    dataset: Dataset
    table: RateTable
    differential: Ranking
    integral: Ranking | None = None
    ml: MLBaseline | None = None
    rational: RationalConsensus | None = None
    design: DesignRanking | None = None
    refinement: list | None = None
    collinearity: CollinearityReport | None = None
    transport: dict[str, TransportDiagnostics] = field(default_factory=dict)
    n_candidates: int = 0
    elapsed_s: float = 0.0
    stage_times: dict[str, float] = field(default_factory=dict)

    @property
    def final(self) -> Ranking:
        return self.integral or self.differential

    @property
    def best(self) -> ModelScore | None:
        return self.final.best

    # ------------------------------------------------------------------
    def report(self, top: int = 12) -> str:
        L: list[str] = []
        add = L.append
        add("=" * 78)
        add(f"VARREDURA DE MECANISMOS — {self.dataset.name}")
        add("=" * 78)
        add(self.dataset.summary())
        add("")

        if self.transport:
            add("-" * 78)
            add("1. DIAGNÓSTICO DE TRANSPORTE")
            add("-" * 78)
            bad = [k for k, d in self.transport.items() if not d.intrinsic]
            for label, d in self.transport.items():
                add(f"  {label}:")
                add(d.report())
            if bad:
                add("")
                add(
                    f"  ATENÇÃO: {len(bad)} corrida(s) reprovaram nos critérios. "
                    "Os parâmetros estimados no modo 'ideal' serão aparentes, "
                    "não intrínsecos. Use mode='full' ou reduza a espessura do "
                    "washcoat / aumente a velocidade."
                )
            add("")

        add("-" * 78)
        add("2. DADOS DIFERENCIAIS")
        add("-" * 78)
        add(f"  {self.table.summary()}")
        if self.table.closure_error > 0.20:
            add(
                "  Fechamento estequiométrico ruim: as derivadas carregam muito "
                "ruído. Trate a triagem diferencial como indicativa apenas."
            )
        if self.collinearity is not None:
            add("")
            add(self.collinearity.report())
        add("")

        if self.ml is not None:
            add("-" * 78)
            add("3. REFERÊNCIA SEM MECANISMO (rede neural)")
            add("-" * 78)
            add(self.ml.report())
            add("")

        if self.rational is not None:
            add("-" * 78)
            add("4. FORMA FUNCIONAL DESCOBERTA (regressão racional esparsa)")
            add("-" * 78)
            add(self.rational.pretty())
            add("")
            teto = self.ml.r2_mean if self.ml is not None else None
            for line in self.rational.interpretation(teto).splitlines():
                add(f"  {line}")
            add("")

        add("-" * 78)
        add(f"5. TRIAGEM DIFERENCIAL — {self.n_candidates} candidatos")
        add("-" * 78)
        add(self.differential.table(top=top))
        add("")

        if self.integral is not None:
            add("-" * 78)
            add("6. REGRESSÃO INTEGRAL DOS SOBREVIVENTES")
            add("-" * 78)
            add(self.integral.table(top=top))
            add("")
            add(f"  {self.integral.verdict()}")
            add("")
            best = self.integral.best
            if best is not None:
                add("  Modelo vencedor:")
                for line in best.fit.summary().splitlines():
                    add(f"  {line}")
                add("")
                for line in best.admissibility.report().splitlines():
                    add(f"{line}")
                add(best.residuals.report())
                add("")
                add("  Equação de velocidade (reação 1):")
                add(f"    {best.fit.network.laws[0].pretty()}")
                add("")

        if self.design is not None:
            add("-" * 78)
            add("7. PRÓXIMOS EXPERIMENTOS (máximo poder discriminatório)")
            add("-" * 78)
            add(f"  modelos em disputa: {', '.join(self.design.models)}")
            add(self.design.table(top=8))
            add("")
        elif self.refinement:
            add("-" * 78)
            add("7. PRÓXIMOS EXPERIMENTOS (refino dos parâmetros, D-ótimo)")
            add("-" * 78)
            add(
                "  A discriminação está encerrada: um modelo concentra toda a\n"
                "  probabilidade. Estas são as condições que mais reduzem a\n"
                "  incerteza dos parâmetros dele."
            )
            add("")
            cabecalho = "log det(J'J)"
            add(
                f"  {'#':>3s} {'condição':<26s} {'T [°C]':>7s} {'M:TG':>6s} "
                f"{cabecalho:>13s}"
            )
            add("  " + "-" * 60)
            for i, (cond, valor) in enumerate(self.refinement[:8], start=1):
                add(
                    f"  {i:>3d} {cond.label[:26]:<26s} "
                    f"{cond.T_K - 273.15:>7.1f} {cond.molar_ratio:>6.1f} "
                    f"{valor:>13.2f}"
                )
            add("")

        add("=" * 78)
        if self.stage_times:
            partes = "  ".join(
                f"{nome} {t:.0f}s" for nome, t in self.stage_times.items()
            )
            add(f"tempo por etapa: {partes}")
        add(f"tempo total: {self.elapsed_s:.1f} s")
        return "\n".join(L)


# ----------------------------------------------------------------------
def transport_diagnostics(
    dataset: Dataset, fit: FitResult | None = None
) -> dict[str, TransportDiagnostics]:
    """Aplica os critérios de exclusão de gradientes às corridas em monolito.

    Sem um modelo ajustado, usa a velocidade observada estimada a partir do
    consumo médio de triglicerídeo — grosseira, mas suficiente: os critérios
    são de ordem de grandeza.
    """
    out: dict[str, TransportDiagnostics] = {}
    iTG = FLUID_SPECIES.index("TG")
    for exp in dataset:
        if exp.reactor != "monolith" or exp.operation is None:
            continue
        col = exp.Y[:, iTG]
        ok = np.isfinite(col)
        if ok.sum() < 2 or exp.t[ok][-1] <= 0:
            continue
        r_obs = abs(float(col[ok][0] - col[ok][-1])) / (
            float(exp.t[ok][-1] - exp.t[ok][0]) * exp.catalyst_g_L
        )
        C_bulk = float(exp.C0[iTG])

        def rate_of_C(c: float, _r=r_obs, _c0=C_bulk) -> float:
            return _r * (c / _c0) if _c0 > 0 else 0.0

        out[exp.label] = diagnose(
            rate_of_C,
            C_bulk,
            exp.operation.geometry,
            exp.operation.fluid,
            exp.operation.velocity_m_s,
        )
    return out


def ml_baseline(table: RateTable, cfg: ScreeningConfig) -> MLBaseline:
    """Teto de desempenho: rede neural com R² validado por k-dobras.

    O R² de treino de uma rede não serve de teto para nada. Com algumas
    dezenas de pontos diferenciais e centenas de pesos, ela memoriza os
    dados e reporta R² próximo de 1 sem capacidade de generalizar —
    comparar um modelo mecanístico contra esse número é comparar contra
    ruído decorado.

    Aqui a rede é dimensionada ao volume de dados (uma camada oculta com
    poucos neurônios) e avaliada em dobras que não participaram do
    treino. O número resultante é o que um modelo cinético precisa
    igualar para se dizer que capturou tudo o que há.
    """
    X = table.features(include_temperature=True)
    n = len(table)
    # aproximadamente um peso para cada três pontos
    largura = int(np.clip(n // (3 * (X.shape[1] + 2)), 3, 12))
    hidden = (largura,)
    k = min(cfg.ml_folds, max(2, n // 10))

    rng = np.random.default_rng(cfg.seed)
    dobras = np.array_split(rng.permutation(n), k)

    r2: list[float] = []
    n_par = 0
    for j in range(table.rates.shape[1]):
        y = table.rates[:, j]
        preditos = np.empty(n)
        for f in range(k):
            teste = dobras[f]
            treino = np.setdiff1d(np.arange(n), teste)
            rede = MLP(hidden=hidden, positive_output=False, l2=1e-3, seed=cfg.seed + f)
            rede.fit(X[treino], y[treino], epochs=cfg.mlp_epochs, lr=0.01)
            preditos[teste] = rede.predict(X[teste])
            n_par = rede.n_parameters
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2.append(1.0 - float(np.sum((y - preditos) ** 2)) / ss_tot if ss_tot > 0 else float("nan"))
    return MLBaseline(r2_per_reaction=r2, n_parameters=n_par, n_folds=k, hidden=hidden)


def sparse_discovery(table: RateTable) -> RationalConsensus:
    """Descobre a forma racional da primeira reação, temperatura a temperatura."""
    num, den = rational_library(acyl="TG", product="DG", reversible=True)
    return fit_rational_by_temperature(
        table.C, table.rates[:, 0], table.T, FLUID_SPECIES, num, den, fit_q=True
    )


# ----------------------------------------------------------------------
def run_screening(
    dataset: Dataset,
    config: ScreeningConfig | None = None,
    verbose: bool = True,
) -> ScreeningResult:
    """Executa a varredura completa sobre um conjunto de dados."""
    cfg = config or ScreeningConfig()
    t0 = time.perf_counter()

    stage: dict[str, float] = {}

    def log(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    def mark(nome: str, inicio: float) -> None:
        stage[nome] = time.perf_counter() - inicio

    t = time.perf_counter()
    log("· diagnóstico de transporte")
    transport = transport_diagnostics(dataset)
    mark("transporte", t)

    t = time.perf_counter()
    log("· extração de dados diferenciais")
    table = estimate_rate_table(dataset)
    log(f"  {table.summary()}")
    colin = collinearity_report(table)
    if not colin.ok:
        log(
            "  colinearidade entre "
            + ", ".join(f"{a}/{b}" for a, b, _ in colin.collinear_pairs)
        )

    mark("dados diferenciais", t)

    ml = None
    if cfg.run_ml_baseline:
        t = time.perf_counter()
        log("· referência sem mecanismo (rede neural)")
        ml = ml_baseline(table, cfg)
        log(f"  R² médio fora da amostra = {ml.r2_mean:.4f}")
        mark("rede neural", t)

    rational = None
    if cfg.run_sparse:
        t = time.perf_counter()
        log("· regressão racional esparsa")
        try:
            rational = sparse_discovery(table)
            log(
                f"  R² médio {rational.mean_r2:.3f} em {rational.n_temperatures} "
                f"temperaturas; denominador de consenso: "
                f"{', '.join(rational.consensus_denominator) or 'vazio'}"
            )
        except Exception as exc:  # noqa: BLE001 - dado insuficiente
            log(f"  não convergiu: {exc}")
        mark("regressão esparsa", t)

    t = time.perf_counter()
    log("· enumerando mecanismos candidatos")
    catalog = build_catalog(cfg.families, cfg.inhibition_sets)
    laws = enumerate_rate_laws(catalog, cfg.include_empirical)
    networks = [build_network(law) for law in laws]
    log(f"  {len(networks)} candidatos ({len(catalog)} mecanismos)")

    mark("enumeração", t)

    t = time.perf_counter()
    log("· triagem diferencial")
    diff_fits: list[FitResult] = []
    for i, net in enumerate(networks, start=1):
        fit = fit_differential(
            net,
            dataset,
            table,
            n_starts=cfg.n_starts_differential,
            seed=cfg.seed,
            fixed=cfg.fixed,
            time_budget_s=cfg.differential_budget_s,
        )
        diff_fits.append(fit)
        if verbose and (i % 10 == 0 or i == len(networks)):
            log(f"  {i}/{len(networks)} modelos")
    diff_rank = rank_models(diff_fits)
    mark("triagem diferencial", t)

    integral = None
    if cfg.n_refine > 0:
        survivors = [
            s for s in diff_rank.scores if s.admissible and s.fit.success
        ][: cfg.n_refine]
        if survivors:
            t = time.perf_counter()
            log(f"· regressão integral de {len(survivors)} sobreviventes")
            int_fits: list[FitResult] = []
            for i, s in enumerate(survivors, start=1):
                log(f"  {i}/{len(survivors)}  {s.model_id}")
                int_fits.append(
                    fit_network(
                        s.fit.network,
                        dataset,
                        mode=cfg.mode,
                        n_starts=cfg.n_starts_integral,
                        seed=cfg.seed,
                        fixed=cfg.fixed,
                        x0=s.fit.x,
                        time_budget_s=cfg.integral_budget_s,
                    )
                )
            integral = rank_models(int_fits)
            mark("regressão integral", t)

    design = None
    refinement = None
    final = integral or diff_rank
    admissiveis = [s for s in final.scores if s.admissible]
    if cfg.run_design and admissiveis:
        t = time.perf_counter()
        grade = candidate_grid()
        if len(grade) > cfg.max_design_candidates:
            passo = len(grade) / cfg.max_design_candidates
            grade = [grade[int(i * passo)] for i in range(cfg.max_design_candidates)]

        if len(admissiveis) >= 2 and admissiveis[0].weight <= 0.99:
            log("· planejamento discriminatório")
            try:
                design = discrimination_design(
                    final.scores, grade, criterion="box_hill", mode="ideal"
                )
            except Exception as exc:  # noqa: BLE001 - poucos modelos admissíveis
                log(f"  não aplicável: {exc}")
        else:
            # Um modelo concentra toda a probabilidade: não há o que
            # discriminar, e o critério de Box-Hill degenera (os pesos dos
            # rivais são numericamente nulos). O passo útil passa a ser
            # reduzir a incerteza dos parâmetros do vencedor.
            log("· planejamento de refino (D-ótimo)")
            try:
                refinement = d_optimal_design(admissiveis[0].fit, grade, mode="ideal")
            except Exception as exc:  # noqa: BLE001
                log(f"  não aplicável: {exc}")
        mark("planejamento", t)

    return ScreeningResult(
        dataset=dataset,
        table=table,
        differential=diff_rank,
        integral=integral,
        ml=ml,
        rational=rational,
        design=design,
        refinement=refinement,
        collinearity=colin,
        transport=transport,
        n_candidates=len(networks),
        elapsed_s=time.perf_counter() - t0,
        stage_times=stage,
    )
