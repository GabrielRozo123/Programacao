"""Critérios de informação, admissibilidade termodinâmica e ranqueamento."""

import numpy as np
import pytest

from biokin.data import Dataset
from biokin.discrimination import (
    aic,
    aicc,
    akaike_weights,
    bic,
    check_admissibility,
    f_test_nested,
    rank_models,
)
from biokin.estimation import FitResult, make_parameterization
from biokin.network import build_network
from biokin.library import er_methoxide
from biokin.lhhw import derive_rate_law
from biokin.synthetic import generate_dataset


def _fit_falso(sse, n_params, dataset, energias=None, cond=1e3):
    """Constrói um FitResult sintético para testar só os critérios."""
    mech = er_methoxide(("G",))
    i = [k for k, s in enumerate(mech.steps) if s.label == "sr"][0]
    net = build_network(derive_rate_law(mech, i))
    par = make_parameterization(net, dataset, non_isothermal=True)
    x = par.pack()
    if energias:
        nomes = par.free_names
        for nome, valor in energias.items():
            x[nomes.index(nome)] = valor
    n_obs = 200
    return FitResult(
        model_id=f"teste-p{n_params}",
        family="ER-M",
        rds_label="sr",
        network=net,
        parameterization=par,
        x=x,
        residuals=np.full(n_obs, np.sqrt(sse / n_obs)),
        sse=sse,
        n_obs=n_obs,
        n_params=n_params,
        success=True,
        std_errors=np.full(len(x), 0.1),
        ci95=np.full(len(x), 0.2),
        correlation=np.eye(len(x)),
        condition_number=cond,
    )


@pytest.fixture(scope="module")
def dados():
    return generate_dataset(relative_noise=0.0, absolute_noise=0.0)


def test_criterios_penalizam_parametros():
    """Com o mesmo SSE, mais parâmetros devem pontuar pior."""
    assert aic(1.0, 200, 8) > aic(1.0, 200, 5)
    assert bic(1.0, 200, 8) > bic(1.0, 200, 5)
    # BIC penaliza mais que AIC quando n é grande
    assert bic(1.0, 200, 8) - bic(1.0, 200, 5) > aic(1.0, 200, 8) - aic(1.0, 200, 5)


def test_aicc_corrige_amostra_pequena():
    assert aicc(1.0, 20, 8) > aic(1.0, 20, 8)
    # com n grande a correção some
    assert aicc(1.0, 100000, 8) == pytest.approx(aic(1.0, 100000, 8), rel=1e-4)


def test_pesos_de_akaike_somam_um():
    w = akaike_weights([100.0, 102.0, 110.0])
    assert w.sum() == pytest.approx(1.0)
    assert w[0] > w[1] > w[2]
    # diferença de 2 no AIC -> razão de evidência e^1
    assert w[0] / w[1] == pytest.approx(np.exp(1.0), rel=1e-6)


def test_teste_f_detecta_melhoria_significativa():
    F, p = f_test_nested(sse_full=1.0, p_full=8, sse_reduced=2.0, p_reduced=6, n=200)
    assert F > 0 and p < 0.001
    # melhoria irrisória não deve ser significativa
    _, p2 = f_test_nested(sse_full=1.0, p_full=8, sse_reduced=1.001, p_reduced=6, n=200)
    assert p2 > 0.05


def test_adsorcao_endotermica_e_rejeitada(dados):
    """ΔH_ads positivo viola a termodinâmica de adsorção."""
    fit = _fit_falso(1.0, 10, dados, energias={"E[K_ads_M]": +40.0})
    adm = check_admissibility(fit)
    assert not adm.ok
    assert any("ΔH_ads" in v for v in adm.violations)


def test_energia_de_ativacao_negativa_e_rejeitada(dados):
    fit = _fit_falso(1.0, 10, dados, energias={"E[k_1]": -30.0})
    adm = check_admissibility(fit)
    assert not adm.ok
    assert any("Ea" in v for v in adm.violations)


def test_sobreparametrizacao_e_rejeitada(dados):
    fit = _fit_falso(1.0, 10, dados, cond=1e14)
    adm = check_admissibility(fit)
    assert not adm.ok
    assert any("sobreparametrizado" in v for v in adm.violations)


def test_modelo_saudavel_e_admissivel(dados):
    fit = _fit_falso(1.0, 10, dados)
    adm = check_admissibility(fit)
    assert adm.ok, adm.violations


def test_ranqueamento_prefere_o_parcimonioso(dados):
    """SSE praticamente igual: vence o de menos parâmetros."""
    gordo = _fit_falso(0.999, 14, dados)
    gordo.model_id = "gordo"
    magro = _fit_falso(1.000, 8, dados)
    magro.model_id = "magro"
    r = rank_models([gordo, magro])
    assert r.best.model_id == "magro"
    assert r.best.weight > 0.5


def test_inadmissiveis_nao_diluem_os_pesos(dados):
    """Modelos reprovados ficam fora do denominador dos pesos de Akaike."""
    bom1 = _fit_falso(1.0, 8, dados)
    bom1.model_id = "bom1"
    bom2 = _fit_falso(1.2, 8, dados)
    bom2.model_id = "bom2"
    ruim = _fit_falso(0.5, 8, dados, energias={"E[k_1]": -30.0})
    ruim.model_id = "ruim"
    r = rank_models([bom1, bom2, ruim])
    assert sum(s.weight for s in r.admissible) == pytest.approx(1.0)
    assert r.scores[-1].model_id == "ruim", "inadmissível deve ir para o fim"
