"""Validação ponta a ponta: a varredura recupera o mecanismo que gerou os dados.

Se este teste falhar, nenhuma conclusão tirada sobre dados reais é confiável.
Ele usa um catálogo reduzido para rodar em segundos; a varredura completa
está em ``python -m biokin demo``.
"""

import numpy as np
import pytest

from biokin.data import Dataset, read_csv, write_csv
from biokin.species import FLUID_SPECIES
from biokin.screening import ScreeningConfig, run_screening
from biokin.synthetic import TRUE_MODEL_ID, Condition, generate_dataset

KEQ_CONHECIDOS = {"Keq_1": 3.0, "Keq_2": 2.0, "Keq_3": 5.0}


@pytest.fixture(scope="module")
def dados_pequenos():
    """Seis corridas em batelada: duas temperaturas, três razões molares.

    Dimensionado para o mínimo que sustenta o ajuste isotérmico da
    regressão racional (mais de doze pontos diferenciais por
    temperatura), que é também o mínimo defensável na bancada.
    """
    t = np.array([0, 5, 10, 20, 40, 60, 90, 120.0])
    conds = [
        Condition(f"B-T{T - 273.15:.0f}-R{r:.0f}", T, r, times_min=t, catalyst_g_L=10.0)
        for T in (323.15, 343.15)
        for r in (6.0, 9.0, 12.0)
    ]
    return generate_dataset(conditions=conds, relative_noise=0.02, seed=7)


@pytest.fixture(scope="module")
def varredura(dados_pequenos):
    cfg = ScreeningConfig(
        families=("ER-M", "LH1"),
        inhibition_sets=((), ("G",)),
        fixed=KEQ_CONHECIDOS,
        n_refine=0,
        n_starts_differential=6,
        differential_budget_s=10.0,
        run_ml_baseline=False,
        run_sparse=True,
        run_design=False,
        seed=1,
    )
    return run_screening(dados_pequenos, cfg, verbose=False)


def test_varredura_encontra_o_mecanismo_verdadeiro(varredura):
    melhor = varredura.best
    assert melhor is not None
    assert melhor.model_id == TRUE_MODEL_ID, (
        f"melhor = {melhor.model_id}\n{varredura.differential.table()}"
    )


def test_termo_de_inibicao_por_glicerol_e_detectado(varredura):
    """O modelo sem inibição deve ajustar visivelmente pior."""
    por_id = {s.model_id: s for s in varredura.differential.scores}
    com = por_id["ER-M[G]|RDS=sr"]
    sem = por_id["ER-M[sem inib.]|RDS=sr"]
    assert com.fit.sse < sem.fit.sse
    assert com.aicc < sem.aicc


def test_regressao_esparsa_aponta_inibicao_por_produto(varredura):
    """A descoberta sem mecanismo detecta inibição por produto.

    Não se exige que aponte o glicerol especificamente: com todas as
    corridas partindo de óleo puro, glicerol e éster são colineares
    (ambos crescem com a conversão) e a informação para separá-los não
    existe no dado. A varredura mecanística acerta porque usa a
    estequiometria como estrutura adicional; a regressão esparsa, que não
    a usa, só pode identificar a combinação. Ver
    :func:`biokin.ml.surrogate.collinearity_report`.
    """
    assert varredura.rational is not None
    ativos = {
        nome
        for m in varredura.rational.models.values()
        for nome in m.active_denominator()
    }
    assert ativos & {"C_G", "C_E"}, f"nenhuma inibição por produto: {ativos}"


def test_colinearidade_e_diagnosticada(varredura):
    """Partindo todas as corridas de óleo puro, o par éster/glicerol acusa."""
    rel = varredura.collinearity
    assert rel is not None and not rel.ok
    pares = {frozenset((a, b)) for a, b, _ in rel.collinear_pairs}
    assert frozenset(("E", "G")) in pares


def test_dopar_a_alimentacao_quebra_a_colinearidade():
    """Adicionar glicerol e éster de saída torna os termos separáveis."""
    from biokin.ml.surrogate import collinearity_report, estimate_rate_table

    t = np.array([0, 10, 20, 40, 60, 90, 120.0])
    conds = [
        Condition(f"B-T{T - 273.15:.0f}-R{r:.0f}", T, r, times_min=t)
        for T in (323.15, 343.15)
        for r in (6.0, 12.0)
    ]
    conds += [
        Condition("B-dopG", 333.15, 9.0, C_G0=0.4, times_min=t),
        Condition("B-dopE", 333.15, 9.0, C_E0=1.0, times_min=t),
    ]
    rel = collinearity_report(estimate_rate_table(generate_dataset(conditions=conds, seed=7)))
    assert rel.ok, rel.report()


def test_parametros_recuperados_com_erro_aceitavel(varredura):
    from biokin.synthetic import true_parameterization

    fit = varredura.best.fit
    par = true_parameterization()
    verdadeiros = par.values_at(par.pack(), 333.15)
    ajustados = fit.values_at(333.15)
    for nome in ("k_1", "k_2", "k_3", "K_ads_M"):
        razao = ajustados[nome] / verdadeiros[nome]
        assert 0.5 < razao < 2.0, f"{nome}: razão ajustado/verdadeiro = {razao:.3f}"


def test_ida_e_volta_pelo_csv(dados_pequenos, tmp_path):
    """Gravar e reler não pode alterar os dados nem a alimentação."""
    caminho = tmp_path / "dados.csv"
    write_csv(dados_pequenos, caminho)
    lido = read_csv(caminho)
    assert lido.n_obs == dados_pequenos.n_obs
    assert len(lido) == len(dados_pequenos)
    for a, b in zip(dados_pequenos, lido):
        assert np.allclose(a.C0, b.C0)
        assert np.allclose(a.t, b.t)
        assert np.allclose(a.Y, b.Y, equal_nan=True, rtol=1e-5)


def test_consenso_esparso_e_isotermico(varredura):
    """A regressão racional deve ser ajustada temperatura a temperatura.

    Seus coeficientes são k(T) e K(T): um único conjunto ajustado a várias
    temperaturas é erro de especificação, porque a velocidade muda por um
    fator de vários entre os extremos da faixa e nenhuma escolha de termos
    reconcilia isso.
    """
    cons = varredura.rational
    assert cons is not None
    assert cons.n_temperatures == len(varredura.dataset.temperatures)
    assert set(cons.models) == set(varredura.dataset.temperatures)


def test_teto_da_rede_neural_e_fora_da_amostra():
    """O R² de referência precisa ser validado, não de treino.

    Com dezenas de pontos e centenas de pesos, o R² de treino de uma rede
    chega perto de 1 sem capacidade nenhuma de generalizar — comparar um
    modelo cinético contra esse número é comparar contra ruído decorado.
    """
    from biokin.ml.surrogate import estimate_rate_table
    from biokin.screening import ScreeningConfig, ml_baseline

    dados = generate_dataset(relative_noise=0.05, seed=3)
    tabela = estimate_rate_table(dados)
    base = ml_baseline(tabela, ScreeningConfig(mlp_epochs=800, ml_folds=4))
    assert base.n_folds >= 2
    # a rede é dimensionada aos dados: nunca mais pesos que pontos
    assert base.n_parameters < len(tabela)
    # com 5% de ruído nos perfis, o teto fora da amostra fica longe de 1
    assert base.r2_mean < 0.98


def test_ponderacao_usa_incerteza_de_medida(dados_pequenos):
    """Pontos no piso de detecção não podem dominar o ajuste.

    Ponderar pelo máximo de cada espécie dentro da corrida quebra nas
    corridas de baixa conversão: ali o glicerol não passa do limite de
    detecção, o máximo da corrida é da ordem do próprio ruído analítico, e
    o ponto recebe peso enorme. A incerteza correta combina precisão
    relativa com piso de detecção.
    """
    referencia = dados_pequenos.reference_scale()
    exp = dados_pequenos.experiments[0]
    sigma = exp.uncertainty(referencia, rel_error=0.05, floor_fraction=0.01)

    assert sigma.shape == exp.Y.shape
    assert np.all(sigma > 0), "incerteza nula geraria divisão por zero"

    iG = FLUID_SPECIES.index("G")
    # no primeiro ponto o glicerol é nulo: a incerteza vem só do piso
    assert sigma[0, iG] == pytest.approx(0.01 * referencia[iG], rel=1e-9)
    # no último, o termo relativo já domina
    assert sigma[-1, iG] > sigma[0, iG]


def test_sigma_informado_pelo_usuario_prevalece(dados_pequenos):
    """Quem tem réplicas pode informar a incerteza e ela é respeitada."""
    exp = dados_pequenos.experiments[0]
    proprio = np.full_like(exp.Y, 0.007)
    exp.sigma = proprio
    try:
        obtido = exp.uncertainty(dados_pequenos.reference_scale())
        assert np.allclose(obtido, proprio)
    finally:
        exp.sigma = None


def test_residuos_ficam_quase_normais_com_a_ponderacao_correta():
    """A ponderação por incerteza deve remover as caudas pesadas.

    Com a ponderação por escala de corrida, os resíduos do conjunto
    sintético completo chegavam a curtose ~100, concentrada nas corridas
    em monolito de baixa conversão.
    """
    from scipy import stats

    from biokin.estimation import fit_differential, fit_network
    from biokin.ml.surrogate import estimate_rate_table
    from biokin.synthetic import true_network

    dados = generate_dataset()
    tabela = estimate_rate_table(dados)
    rede = true_network()
    diferencial = fit_differential(
        rede, dados, tabela, n_starts=6, seed=0, fixed=KEQ_CONHECIDOS, time_budget_s=15
    )
    integral = fit_network(
        rede,
        dados,
        n_starts=0,
        seed=0,
        fixed=KEQ_CONHECIDOS,
        x0=diferencial.x,
        time_budget_s=200,
    )
    r = integral.residuals
    assert abs(float(stats.skew(r))) < 1.5
    assert float(stats.kurtosis(r)) < 20.0
