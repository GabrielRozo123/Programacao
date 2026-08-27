"""Camada de aprendizado: extração de taxas, rede neural, regressão esparsa."""

import numpy as np
import pytest

from biokin.ml.mlp import MLP
from biokin.ml.sparse import fit_rational_sparse, rational_library
from biokin.ml.surrogate import estimate_rate_table, reconstruct_unmeasured, smooth_profile
from biokin.species import FLUID_SPECIES
from biokin.synthetic import Condition, generate_dataset


def test_suavizacao_recupera_derivada_conhecida():
    t = np.linspace(0, 10, 40)
    y = 2.0 * np.exp(-0.3 * t)
    rng = np.random.default_rng(0)
    suave, deriv = smooth_profile(t, y + rng.normal(0, 0.01, t.size))
    esperado = -0.6 * np.exp(-0.3 * t)
    # nas bordas a spline é menos confiável; compara no miolo
    m = slice(5, -5)
    assert np.max(np.abs(deriv[m] - esperado[m])) < 0.05


def test_reconstrucao_de_metanol_por_balanco():
    """Metanol não medido deve sair do balanço com o éster."""
    d = generate_dataset(
        conditions=[Condition("t", 333.15, 9.0, times_min=np.linspace(0, 60, 7))],
        measured=("TG", "DG", "MG", "E", "G"),
        relative_noise=0.0,
        absolute_noise=0.0,
    )
    exp = d.experiments[0]
    iM, iE = FLUID_SPECIES.index("M"), FLUID_SPECIES.index("E")
    assert not np.isfinite(exp.Y[:, iM]).any(), "metanol deveria estar ausente"

    Y = reconstruct_unmeasured(exp)
    assert np.isfinite(Y[:, iM]).all()
    assert np.allclose(Y[:, iM] + Y[:, iE], exp.C0[iM] + exp.C0[iE], rtol=1e-9)


def test_tabela_de_taxas_fecha_a_estequiometria():
    """Sem ruído, a inversão da estequiometria deve fechar quase exatamente."""
    d = generate_dataset(relative_noise=0.0, absolute_noise=0.0)
    tabela = estimate_rate_table(d)
    assert len(tabela) > 30
    assert tabela.closure_error < 0.05
    assert np.all(tabela.rates[:, 0] > -1e-9), "r1 não pode ser negativa sem ruído"


def test_mlp_ajusta_forma_lhhw():
    """A rede deve reproduzir uma superfície de velocidade tipo LHHW."""
    rng = np.random.default_rng(0)
    X = rng.uniform(0.05, 1.0, size=(300, 2))
    def alvo(x):
        return 0.5 * x[:, 0] * x[:, 1] / (1 + 2 * x[:, 0] + 3 * x[:, 1]) ** 2

    rede = MLP(hidden=(20, 20), l2=1e-5, seed=1)
    rede.fit(X, alvo(X) + rng.normal(0, 1e-4, 300), epochs=2000, lr=0.02)
    Xt = rng.uniform(0.05, 1.0, size=(200, 2))
    assert rede.score(Xt, alvo(Xt)) > 0.99
    assert np.all(rede.predict(Xt) >= 0), "saída softplus deve ser não negativa"


def test_regressao_esparsa_recupera_lei_conhecida():
    """Deve achar os dois termos verdadeiros do denominador e excluir os falsos."""
    rng = np.random.default_rng(3)
    n = 400
    C = np.zeros((n, 6))
    C[:, 0] = rng.uniform(0.05, 1.0, n)  # TG
    C[:, 3] = rng.uniform(1.0, 10.0, n)  # M
    C[:, 4] = rng.uniform(0.0, 2.0, n)  # E  (falso: não deve entrar)
    C[:, 5] = rng.uniform(0.0, 0.8, n)  # G
    r = 0.02 * C[:, 0] * C[:, 3] / (1 + 0.35 * C[:, 3] + 4.0 * C[:, 5])
    r = r * (1 + rng.normal(0, 0.02, n))

    num, den = rational_library(acyl="TG", product="DG", reversible=False)
    m = fit_rational_sparse(C, r, FLUID_SPECIES, num, den, fit_q=True)

    assert m.r2 > 0.99
    ativos = set(m.active_denominator())
    assert ativos == {"C_M", "C_G"}, f"denominador encontrado: {ativos}"
    assert m.q == pytest.approx(1.0, abs=0.25)
