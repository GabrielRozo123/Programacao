"""Discriminação entre modelos cinéticos rivais.

Ajustar bem não basta. Um modelo LHHW com sete parâmetros quase sempre
ajusta melhor que um com três, e o mecanismo "vencedor" escolhido só pela
soma de quadrados é o mais flexível, não o mais verdadeiro. Este módulo
combina três filtros independentes:

**Parcimônia estatística** — AIC, AICc e BIC penalizam parâmetros. Os pesos
de Akaike convertem a diferença de AIC em probabilidade relativa de cada
modelo ser o melhor do conjunto examinado. Nunca em probabilidade de ser
*verdadeiro*: se o mecanismo real não está no catálogo, o peso vai para o
menos ruim.

**Admissibilidade físico-química** — regras de Boudart e Vannice. Uma
constante de adsorção que cresce com a temperatura, uma entropia de
adsorção positiva ou uma energia de ativação negativa condenam o modelo
independentemente do ajuste. É o critério que mais elimina candidatos na
prática, e o que mais convence uma banca.

**Estrutura dos resíduos** — um modelo correto deixa resíduos sem padrão.
Autocorrelação ao longo do tempo (Durbin-Watson) ou dependência sistemática
da conversão indicam forma funcional errada, mesmo com SSE baixo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from .estimation import FitResult
from .parameters import (
    KIND_ADSORPTION,
    KIND_EQUILIBRIUM,
    KIND_EXPONENT,
    KIND_RATE,
    R_GAS,
)

#: Faixa admissível para a entropia de adsorção em fase líquida [J/(mol·K)].
#: A regra clássica de Vannice é de fase gasosa; em fase líquida a molécula
#: já perde graus de liberdade translacionais ao solvatar, e o limite
#: superior é mais frouxo.
ENTROPY_BOUNDS_J_MOL_K = (-210.0, 0.0)

#: Acima deste condicionamento de ``J'J`` o modelo é sobreparametrizado.
CONDITION_LIMIT = 1e10


# ----------------------------------------------------------------------
# critérios de informação
# ----------------------------------------------------------------------
def aic(sse: float, n: int, p: int) -> float:
    """Critério de Akaike sob erros gaussianos de variância desconhecida."""
    if sse <= 0 or n <= 0:
        return float("inf")
    return n * math.log(sse / n) + 2.0 * p


def aicc(sse: float, n: int, p: int) -> float:
    """AIC com correção de amostra pequena (Hurvich-Tsai).

    Recomendado sempre que ``n/p < 40``, o que é a regra e não a exceção em
    estudos cinéticos de bancada.
    """
    base = aic(sse, n, p)
    denom = n - p - 1
    if denom <= 0:
        return float("inf")
    return base + 2.0 * p * (p + 1) / denom


def bic(sse: float, n: int, p: int) -> float:
    """Critério bayesiano de Schwarz; penaliza parâmetros mais que o AIC."""
    if sse <= 0 or n <= 0:
        return float("inf")
    return n * math.log(sse / n) + p * math.log(n)


def akaike_weights(values: list[float]) -> np.ndarray:
    """Pesos de Akaike: probabilidade relativa dentro do conjunto examinado."""
    arr = np.asarray(values, dtype=float)
    finite = np.isfinite(arr)
    out = np.zeros_like(arr)
    if not finite.any():
        return out
    d = arr[finite] - arr[finite].min()
    w = np.exp(-0.5 * d)
    out[finite] = w / w.sum()
    return out


def f_test_nested(
    sse_full: float, p_full: int, sse_reduced: float, p_reduced: int, n: int
) -> tuple[float, float]:
    """Teste F para modelos aninhados. Devolve ``(F, valor-p)``.

    Só é válido quando o modelo reduzido é caso particular do completo —
    por exemplo, a mesma família com e sem o termo de inibição por glicerol.
    """
    df1 = p_full - p_reduced
    df2 = n - p_full
    if df1 <= 0 or df2 <= 0 or sse_full <= 0:
        return float("nan"), float("nan")
    F = ((sse_reduced - sse_full) / df1) / (sse_full / df2)
    if not math.isfinite(F) or F < 0:
        return float("nan"), float("nan")
    return F, float(stats.f.sf(F, df1, df2))


# ----------------------------------------------------------------------
# admissibilidade físico-química
# ----------------------------------------------------------------------
@dataclass
class Admissibility:
    """Veredito das regras termodinâmicas sobre um ajuste."""

    ok: bool
    violations: list[str] = field(default_factory=list)
    entropies: dict[str, float] = field(default_factory=dict)

    def report(self) -> str:
        if self.ok:
            return "  admissível: todas as regras termodinâmicas satisfeitas"
        return "  INADMISSÍVEL:\n" + "\n".join(f"    - {v}" for v in self.violations)


def check_admissibility(
    fit: FitResult,
    entropy_bounds: tuple[float, float] = ENTROPY_BOUNDS_J_MOL_K,
    condition_limit: float = CONDITION_LIMIT,
) -> Admissibility:
    """Aplica as regras de Boudart-Vannice ao conjunto de parâmetros.

    Regras verificadas:

    * adsorção é exotérmica: ``ΔH_ads < 0``;
    * adsorção diminui a entropia: ``ΔS_ads < 0``, com
      ``ΔS_ads = R ln K_ref + ΔH_ads / T_ref``;
    * a perda de entropia não pode exceder a entropia disponível da
      espécie livre (limite inferior de ``entropy_bounds``);
    * energia de ativação positiva;
    * ordens de reação dentro de faixa física, para modelos empíricos;
    * ``J'J`` suficientemente condicionada para que os parâmetros
      signifiquem algo.
    """
    violations: list[str] = []
    entropies: dict[str, float] = {}
    raw = fit.parameterization.unpack(fit.x)
    T_ref = fit.parameterization.T_ref

    for spec in fit.parameterization.specs:
        value, energy = raw[spec.name]
        if spec.kind == KIND_ADSORPTION:
            if spec.fit_energy and energy > 0:
                violations.append(
                    f"{spec.name}: ΔH_ads = {energy:+.1f} kJ/mol > 0 "
                    "(adsorção endotérmica)"
                )
            dS = R_GAS * math.log(max(value, 1e-300)) + energy * 1e3 / T_ref
            entropies[spec.name] = dS
            if spec.fit_energy:
                if dS > entropy_bounds[1]:
                    violations.append(
                        f"{spec.name}: ΔS_ads = {dS:+.1f} J/(mol·K) > "
                        f"{entropy_bounds[1]:.0f} (adsorção aumenta a entropia)"
                    )
                elif dS < entropy_bounds[0]:
                    violations.append(
                        f"{spec.name}: ΔS_ads = {dS:+.1f} J/(mol·K) < "
                        f"{entropy_bounds[0]:.0f} (perda de entropia excessiva)"
                    )
        elif spec.kind == KIND_RATE:
            if spec.fit_energy and energy < 0:
                violations.append(
                    f"{spec.name}: Ea = {energy:+.1f} kJ/mol < 0"
                )
        elif spec.kind == KIND_EXPONENT:
            if not 0.0 <= value <= 3.0:
                violations.append(f"{spec.name}: ordem {value:.2f} fora de [0, 3]")
        elif spec.kind == KIND_EQUILIBRIUM and value <= 0:
            violations.append(f"{spec.name}: constante de equilíbrio não positiva")

    if not fit.success:
        violations.append("a regressão não convergiu")
    if fit.condition_number > condition_limit:
        violations.append(
            f"cond(J'J) = {fit.condition_number:.2g} > {condition_limit:.0g}: "
            "modelo sobreparametrizado para estes dados"
        )
    return Admissibility(not violations, violations, entropies)


# ----------------------------------------------------------------------
# diagnóstico de resíduos
# ----------------------------------------------------------------------
@dataclass
class ResidualDiagnostics:
    durbin_watson: float
    shapiro_p: float
    mean_residual: float
    max_abs_residual: float
    skewness: float = 0.0
    excess_kurtosis: float = 0.0
    n: int = 0

    @property
    def autocorrelated(self) -> bool:
        """DW longe de 2 indica resíduos correlacionados em série."""
        return not (1.5 < self.durbin_watson < 2.5)

    @property
    def skewed(self) -> bool:
        """Resíduos assimétricos: o modelo erra mais para um lado.

        É o diagnóstico que importa para a forma funcional — indica viés
        sistemático, tipicamente um termo faltando na lei de velocidade.
        """
        return abs(self.skewness) > 1.0

    @property
    def heavy_tailed(self) -> bool:
        """Caudas pesadas: alguns pontos muito distantes do modelo.

        Ao contrário da assimetria, não condena a forma funcional. Aponta
        pontos aberrantes — erro analítico, amostra contaminada, ponto fora
        da faixa de validade — que convém identificar e justificar antes de
        confiar nos intervalos de confiança.
        """
        return self.excess_kurtosis > 8.0

    @property
    def non_normal(self) -> bool:
        """Desvio de normalidade grande o bastante para importar.

        O teste de Shapiro-Wilk rejeita a normalidade para qualquer desvio,
        por menor que seja, quando a amostra é grande — com mil resíduos ele
        acusa quase sempre, e o alerta perde valor informativo. Aqui exige-se
        também um tamanho de efeito.
        """
        return self.shapiro_p < 0.01 and (self.skewed or self.heavy_tailed)

    def report(self) -> str:
        flags = []
        if self.autocorrelated:
            flags.append("autocorrelação: forma funcional suspeita")
        if self.skewed:
            flags.append("assimetria: viés sistemático, provável termo faltando")
        if self.heavy_tailed:
            flags.append("caudas pesadas: verifique pontos aberrantes")
        tail = ("  <- " + "; ".join(flags)) if flags else ""
        return (
            f"  Durbin-Watson={self.durbin_watson:.2f}  "
            f"assimetria={self.skewness:+.2f}  curtose={self.excess_kurtosis:+.2f}  "
            f"média={self.mean_residual:+.3g}{tail}"
        )


def residual_diagnostics(fit: FitResult) -> ResidualDiagnostics:
    r = np.asarray(fit.residuals, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 4:
        return ResidualDiagnostics(float("nan"), float("nan"), float("nan"), float("nan"))
    dw = float(np.sum(np.diff(r) ** 2) / max(np.sum(r**2), 1e-300))
    if float(np.ptp(r)) <= 0:  # resíduos constantes: normalidade não se aplica
        p, skew, kurt = float("nan"), 0.0, 0.0
    else:
        try:
            p = float(stats.shapiro(r[:5000]).pvalue)
        except Exception:  # noqa: BLE001 - amostra degenerada
            p = float("nan")
        skew = float(stats.skew(r))
        kurt = float(stats.kurtosis(r))  # já é o excesso de curtose
    return ResidualDiagnostics(
        dw, p, float(r.mean()), float(np.max(np.abs(r))), skew, kurt, len(r)
    )


# ----------------------------------------------------------------------
# ranqueamento
# ----------------------------------------------------------------------
@dataclass
class ModelScore:
    """Pontuação completa de um modelo candidato."""

    fit: FitResult
    aic: float
    aicc: float
    bic: float
    weight: float = 0.0
    delta_aicc: float = 0.0
    admissibility: Admissibility = None  # type: ignore[assignment]
    residuals: ResidualDiagnostics = None  # type: ignore[assignment]

    @property
    def model_id(self) -> str:
        return self.fit.model_id

    @property
    def admissible(self) -> bool:
        return self.admissibility.ok


@dataclass
class Ranking:
    """Tabela de modelos ordenada e com os filtros aplicados."""

    scores: list[ModelScore]
    criterion: str = "aicc"

    @property
    def admissible(self) -> list[ModelScore]:
        return [s for s in self.scores if s.admissible]

    @property
    def best(self) -> ModelScore | None:
        adm = self.admissible
        return adm[0] if adm else (self.scores[0] if self.scores else None)

    def table(self, top: int = 15, only_admissible: bool = False) -> str:
        rows = self.admissible if only_admissible else self.scores
        rows = rows[:top]
        head = (
            f"{'#':>3s} {'modelo':<34s} {'p':>3s} {'SSE':>10s} "
            f"{'AICc':>10s} {'ΔAICc':>8s} {'peso':>7s}  situação"
        )
        lines = [head, "-" * len(head)]
        for i, s in enumerate(rows, start=1):
            status = "admissível" if s.admissible else f"{len(s.admissibility.violations)} violações"
            if s.residuals is not None:
                if s.residuals.autocorrelated:
                    status += ", resíduos correlacionados"
                elif s.residuals.skewed:
                    status += ", resíduos assimétricos"
            lines.append(
                f"{i:>3d} {s.model_id[:34]:<34s} {s.fit.n_params:>3d} "
                f"{s.fit.sse:>10.4g} {s.aicc:>10.1f} {s.delta_aicc:>8.1f} "
                f"{s.weight:>7.3f}  {status}"
            )
        return "\n".join(lines)

    def evidence_ratio(self, i: int = 0, j: int = 1) -> float:
        """Razão de evidência entre dois modelos do ranking."""
        rows = self.scores
        if max(i, j) >= len(rows) or rows[j].weight <= 0:
            return float("inf")
        return rows[i].weight / rows[j].weight

    def verdict(self) -> str:
        """Leitura em texto do que a tabela permite concluir."""
        adm = self.admissible
        if not adm:
            return (
                "Nenhum candidato passou nos critérios termodinâmicos. Ou o "
                "mecanismo real está fora do catálogo, ou os dados estão "
                "disfarçados por transporte, ou a faixa experimental é "
                "estreita demais para determinar os parâmetros."
            )
        best = adm[0]
        if len(adm) == 1:
            return f"Único candidato admissível: {best.model_id}."
        if best.weight > 0.99:
            return (
                f"Discriminação encerrada: {best.model_id} concentra "
                f"praticamente toda a probabilidade (peso {best.weight:.4f}). "
                "Os demais candidatos estão descartados por estes dados. O "
                "passo seguinte não é discriminar e sim refinar — experimentos "
                "D-ótimos reduzem a incerteza dos parâmetros do modelo "
                "escolhido (biokin.doe.d_optimal_design)."
            )
        ratio = best.weight / adm[1].weight if adm[1].weight > 0 else float("inf")
        if ratio > 10:
            strength = "decisiva"
        elif ratio > 3:
            strength = "moderada"
        else:
            strength = "fraca"
        # Diferenças grandes de AICc produzem razões de evidência de muitas
        # ordens de grandeza; imprimi-las por extenso não informa nada além
        # de "muito maior que 10".
        razao = f"{ratio:.1f}" if ratio < 1e4 else f"> 10^{int(np.log10(ratio))}"
        txt = (
            f"Melhor candidato admissível: {best.model_id} "
            f"(peso {best.weight:.3f}). Evidência {strength} sobre o segundo "
            f"colocado, {adm[1].model_id} (razão {razao})."
        )
        if ratio <= 3:
            txt += (
                " Os dados atuais não separam os dois primeiros — é o caso de "
                "planejar experimentos discriminatórios (ver biokin.doe)."
            )
        return txt


def rank_models(
    fits: list[FitResult],
    criterion: str = "aicc",
    entropy_bounds: tuple[float, float] = ENTROPY_BOUNDS_J_MOL_K,
) -> Ranking:
    """Ordena os ajustes e aplica os filtros de admissibilidade.

    Os pesos de Akaike são calculados **apenas sobre os modelos
    admissíveis**: incluir modelos termodinamicamente impossíveis no
    denominador diluiria artificialmente a probabilidade dos válidos.
    """
    scores: list[ModelScore] = []
    for fit in fits:
        scores.append(
            ModelScore(
                fit=fit,
                aic=aic(fit.sse, fit.n_obs, fit.n_params),
                aicc=aicc(fit.sse, fit.n_obs, fit.n_params),
                bic=bic(fit.sse, fit.n_obs, fit.n_params),
                admissibility=check_admissibility(fit, entropy_bounds),
                residuals=residual_diagnostics(fit),
            )
        )

    key = {"aic": lambda s: s.aic, "aicc": lambda s: s.aicc, "bic": lambda s: s.bic}[
        criterion
    ]
    scores.sort(key=lambda s: (not s.admissible, key(s)))

    adm = [s for s in scores if s.admissible]
    if adm:
        weights = akaike_weights([key(s) for s in adm])
        best = min(key(s) for s in adm)
        for s, w in zip(adm, weights):
            s.weight = float(w)
            s.delta_aicc = key(s) - best
    for s in scores:
        if not s.admissible:
            s.delta_aicc = float("nan")
    return Ranking(scores, criterion)
