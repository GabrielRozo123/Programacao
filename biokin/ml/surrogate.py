"""Extração de velocidades de reação a partir de perfis de concentração.

Converte dados *integrais* (concentração contra tempo) em dados
*diferenciais* (velocidade contra composição), que é a forma em que o
mecanismo se manifesta diretamente. Duas etapas:

1. **Suavização.** Diferenciar dados ruidosos amplifica o ruído; um perfil
   com 3 % de erro produz derivadas com 30 % ou mais. Usa-se spline
   suavizadora com parâmetro escolhido por validação cruzada generalizada,
   que decide sozinha quanto suavizar.

2. **Inversão da estequiometria.** Com ``dC/dt = w · nu · r`` e ``nu`` de
   posto 3, as três velocidades saem por mínimos quadrados:
   ``r = pinv(nu) · (dC/dt) / w``. Nenhum modelo cinético é assumido — só a
   estequiometria, que é conhecida.

O resíduo dessa inversão é informativo por si só: se ``nu·r`` não
reproduz ``dC/dt``, os balanços materiais não fecham e há problema
analítico antes de qualquer discussão de mecanismo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import make_smoothing_spline

from ..data import Dataset, Experiment
from ..species import FLUID_SPECIES, stoich_matrix


def smooth_profile(
    t: np.ndarray, y: np.ndarray, lam: float | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Suaviza um perfil e devolve ``(valores suavizados, derivadas)``.

    ``lam=None`` deixa a validação cruzada generalizada escolher a
    suavização. Com menos de quatro pontos, cai para diferenças finitas.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 4:
        if ok.sum() < 2:
            return y.copy(), np.zeros_like(y)
        d = np.gradient(y[ok], t[ok])
        out_y, out_d = np.full_like(y, np.nan), np.full_like(y, np.nan)
        out_y[ok], out_d[ok] = y[ok], d
        return out_y, out_d

    spline = make_smoothing_spline(t[ok], y[ok], lam=lam)
    deriv = spline.derivative()
    return spline(t), deriv(t)


def reconstruct_unmeasured(exp: Experiment) -> np.ndarray:
    """Completa espécies não medidas usando os balanços materiais.

    Dois balanços são sempre válidos na metanólise:

    * **grupos acila**: ``3·TG + 2·DG + MG + E`` é conservado;
    * **metanol/éster**: cada mol de éster formado consome um de metanol,
      logo ``C_M = C_M0 - (C_E - C_E0)``.

    O esqueleto de glicerol dá um terceiro: ``TG + DG + MG + G`` conservado.
    Com eles se recupera o metanol (quase nunca titulado) e, se faltar, uma
    das espécies gliceroladas.
    """
    Y = exp.Y.copy()
    idx = {s: i for i, s in enumerate(FLUID_SPECIES)}
    C0 = exp.C0

    # metanol a partir do éster
    iM, iE = idx["M"], idx["E"]
    if not np.isfinite(Y[:, iM]).all() and np.isfinite(Y[:, iE]).any():
        est = C0[iM] - (Y[:, iE] - C0[iE])
        Y[:, iM] = np.where(np.isfinite(Y[:, iM]), Y[:, iM], est)

    # esqueleto de glicerol: TG + DG + MG + G = constante
    backbone = [idx[s] for s in ("TG", "DG", "MG", "G")]
    total = float(sum(C0[i] for i in backbone))
    for k in range(Y.shape[0]):
        missing = [i for i in backbone if not np.isfinite(Y[k, i])]
        if len(missing) == 1:
            known = sum(Y[k, i] for i in backbone if i != missing[0])
            Y[k, missing[0]] = max(total - known, 0.0)
    return Y


@dataclass
class RateTable:
    """Dados diferenciais reunidos de todo o conjunto experimental."""

    C: np.ndarray  # (n, n_espécies) concentrações suavizadas
    T: np.ndarray  # (n,) temperatura
    rates: np.ndarray  # (n, 3) velocidades específicas mol/(g·min)
    dCdt: np.ndarray  # (n, n_espécies) derivadas por massa de catalisador
    residual: np.ndarray  # (n,) resíduo do fechamento estequiométrico
    labels: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.T)

    @property
    def closure_error(self) -> float:
        """Fração de ``dC/dt`` que a estequiometria não explica.

        As derivadas vivem num espaço de dimensão igual ao número de
        espécies, mas a estequiometria só admite três direções. O que
        sobra é ruído de diferenciação (ou erro analítico). Valores muito
        acima de ~20 % indicam que os dados diferenciais servem para
        triagem, não para estimativa final de parâmetros.
        """
        denom = float(np.median(np.linalg.norm(self.dCdt, axis=1)))
        if denom <= 0:
            return float("nan")
        return float(np.median(np.abs(self.residual)) / denom)

    def features(self, include_temperature: bool = True) -> np.ndarray:
        """Matriz de entrada para os modelos de aprendizado."""
        if include_temperature:
            return np.column_stack([self.C, 1.0e3 / self.T])
        return self.C

    def summary(self) -> str:
        return (
            f"{len(self)} pontos diferenciais | "
            f"erro de fechamento {100 * self.closure_error:.1f}% | "
            f"r1 ∈ [{self.rates[:, 0].min():.3g}, {self.rates[:, 0].max():.3g}]"
        )


def estimate_rate_table(
    dataset: Dataset,
    lam: float | None = None,
    drop_endpoints: bool = True,
    complete_balances: bool = True,
) -> RateTable:
    """Constrói a tabela de velocidades a partir dos perfis medidos.

    ``drop_endpoints`` descarta o primeiro e o último ponto de cada corrida:
    a derivada de uma spline é menos confiável nas bordas, onde não há
    dados dos dois lados.

    Para corridas em monolito com limitação difusional, as velocidades
    obtidas são as *observadas* (``eta·r``), não as intrínsecas. Isso é
    coerente com o uso previsto — comparar modelos sobre o mesmo dado —
    mas os parâmetros daí extraídos são aparentes.
    """
    nu = np.array([stoich_matrix()[s] for s in FLUID_SPECIES], dtype=float)
    nu_pinv = np.linalg.pinv(nu)

    Cs, Ts, Rs, Ds, res, labels = [], [], [], [], [], []
    for exp in dataset:
        Y = reconstruct_unmeasured(exp) if complete_balances else exp.Y
        if len(exp.t) < 3 or exp.catalyst_g_L <= 0:
            continue
        smooth = np.zeros_like(Y)
        deriv = np.zeros_like(Y)
        usable = np.ones(len(exp.t), dtype=bool)
        for i in range(Y.shape[1]):
            col = Y[:, i]
            if np.isfinite(col).sum() < 2:
                smooth[:, i] = exp.C0[i]
                deriv[:, i] = 0.0
                continue
            s, d = smooth_profile(exp.t, col, lam)
            smooth[:, i] = np.where(np.isfinite(s), s, exp.C0[i])
            deriv[:, i] = np.where(np.isfinite(d), d, 0.0)

        if drop_endpoints and len(exp.t) > 4:
            usable[0] = usable[-1] = False

        dCdt = deriv / exp.catalyst_g_L
        r = dCdt @ nu_pinv.T  # (n, 3)
        closure = np.linalg.norm(dCdt - r @ nu.T, axis=1)

        for k in np.flatnonzero(usable):
            Cs.append(np.maximum(smooth[k], 0.0))
            Ts.append(exp.T_K)
            Rs.append(r[k])
            Ds.append(dCdt[k])
            res.append(closure[k])
            labels.append(f"{exp.label}@{exp.t[k]:g}")

    if not Cs:
        raise ValueError("nenhuma corrida com pontos suficientes para diferenciar")
    return RateTable(
        C=np.array(Cs),
        T=np.array(Ts),
        rates=np.array(Rs),
        dCdt=np.array(Ds),
        residual=np.array(res),
        labels=labels,
    )
