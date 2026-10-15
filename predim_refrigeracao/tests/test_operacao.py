"""Operação fora do projeto (casamento de componentes), pull-down e restrição de potência máxima."""
import copy
import json
import math

import numpy as np
import pytest

from predimref import EntradasProjeto, ErroProjeto, ParametrosProjeto, dimensionar
from predimref.gabinete import Uso, cargas_internas, transmissao
from predimref.operacao import ParametrosOperacao, modelo_do_projeto, ponto_operacao, simular_pulldown
from predimref.projeto import RestricaoPotencia

BASE = dict(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0)


def _dim(W=None, **kw):
    kw.setdefault("analise_sensibilidade", False)
    return dimensionar(EntradasProjeto(**BASE, potencia_max_compressor_W=W), ParametrosProjeto(**kw))


def _pd(res, **kw):
    po = copy.deepcopy(res.parametros.operacao)
    for k, v in kw.items():
        setattr(po, k, v)
    p = res.parametros
    return simular_pulldown(modelo_do_projeto(res), res.capacidade, p.gabinete, p.uso, p.garrafa, p.ciclo,
                            res.entradas.T_ambiente_C, res.entradas.T_alvo_C, po)


@pytest.fixture(scope="module")
def res():
    return _dim()


# ------------------------------------------------------------------------- ponto de operação
def test_ponto_operacao_reproduz_projeto(res):
    m = modelo_do_projeto(res)
    for chute in (None, (200.0, 400.0)):     # o segundo força a bissecção
        p = ponto_operacao(m, res.evaporador.T_ar_in, res.condensador.T_ar_in, res.evaporador.fator_umidade, chute)
        assert p.T_evap == pytest.approx(res.ciclo.T_evap, abs=2e-3)
        assert p.T_cond == pytest.approx(res.ciclo.T_cond, abs=2e-3)
        assert p.m == pytest.approx(res.balanco.m, rel=1e-4)
        assert p.Q_evap == pytest.approx(res.balanco.Q_evap, rel=1e-4)
        assert p.W_el == pytest.approx(res.balanco.W_el, rel=1e-4)
        assert p.Q_cond == pytest.approx(res.balanco.Q_cond, rel=1e-4)
        assert p.COP == pytest.approx(res.ciclo.COP, rel=1e-4)


def test_ponto_operacao_monotonico(res):
    g = res.pulldown.grade
    assert np.all(np.diff(g["T_ar"]) > 0)
    assert np.all(np.diff(g["Q_evap"]) > 0) and np.all(np.diff(g["T_evap"]) > 0) and np.all(np.diff(g["T_cond"]) > 0)


def test_formula_do_pico_ideal_citada_na_documentacao():
    """Confere a fórmula do docstring de ``operacao``: compressor ideal (sem espaço morto) com P_desc fixa,
    W ∝ P_s[(P_d/P_s)^((k−1)/k) − 1], tem máximo em r = k^(k/(k−1))."""
    k = 1.13
    r = np.linspace(1.5, 6.0, 2001)
    W = (1.0 / r) * (r ** ((k - 1) / k) - 1.0)
    assert r[np.argmax(W)] == pytest.approx(k ** (k / (k - 1)), rel=2e-3)


# ------------------------------------------------------------------------------- pull-down
def test_pulldown_conservacao_energia_do_produto(res):
    pd = res.pulldown
    Q_prod = pd.hA_produto_W_K * (pd.T_produto - pd.T_ar)
    E = np.trapezoid(Q_prod, pd.t)
    assert E == pytest.approx(pd.C_produto_J_K * (pd.T_produto_inicial - pd.T_alvo), rel=2e-3)
    assert pd.concluido and np.all(np.diff(pd.T_produto) < 0) and np.all(pd.T_ar < pd.T_produto)
    assert pd.C_produto_J_K * (pd.T_produto_inicial - pd.T_alvo) == pytest.approx(
        res.capacidade.n_garrafas * res.parametros.garrafa.energia_resfriamento(32.0, 2.5), rel=1e-12)


def test_pulldown_concentrado_contra_ode(res):
    """Com hA → ∞ (produto = ar) o tempo da quadratura com PCHIP bate com a integração direta da EDO usando o
    modelo completo em cada passo (solve_ivp, RK45)."""
    from scipy.integrate import solve_ivp
    pd = _pd(res, hA_produto_W_K=1e7)
    m, p = modelo_do_projeto(res), res.parametros
    T_amb, T_f = 305.15, 275.65
    tr = transmissao(res.capacidade, p.gabinete, T_amb, T_f)
    Q_int = cargas_internas(p.uso)

    def dTdt(_, y):
        q = ponto_operacao(m, y[0] + p.ciclo.dT_retorno_evap, T_amb + p.ciclo.dT_recirculacao_cond, 1.0)
        return [-(q.Q_evap - tr["Q_total"] - tr["UA_total"] * (T_f - y[0]) - Q_int) / pd.C_produto_J_K]

    alvo = lambda _, y: y[0] - T_f  # noqa: E731
    alvo.terminal = True
    sol = solve_ivp(dTdt, (0.0, 3e5), [T_amb], events=alvo, rtol=1e-7, atol=1e-6)
    assert sol.t_events[0][0] == pytest.approx(pd.tempo_s, rel=3e-3)


def test_pulldown_respeita_requisito_quando_governa():
    """Pull-down governando (6 h) e produto = ar: a capacidade real cresce com o gabinete quente e a transmissão cai,
    então o tempo simulado fica abaixo de t_req/(1 + margem) (a carga de projeto é a do gabinete na T_alvo)."""
    r = _dim(uso=Uso(tempo_pulldown_h=6.0))
    assert r.carga.caso_governante.startswith("pull-down")
    pd = _pd(r, hA_produto_W_K=1e7)
    assert pd.tempo_h <= 6.0 / (1.0 + r.parametros.uso.margem_seguranca) * 1.001


def test_pico_inclui_partida_e_nao_depende_de_hA(res):
    a, b = _pd(res, h_produto_W_m2K=3.0), _pd(res, h_produto_W_m2K=10.0)
    assert a.tempo_h > b.tempo_h > res.pulldown.tempo_h * 0.5
    for pd in (a, b, res.pulldown):
        assert pd.W_pico >= pd.W_pico_trajetoria - 1e-9 and pd.W_pico >= pd.W_inicial - 1e-9
        assert pd.W_pico > res.balanco.W_el
    if a.pico_na_partida and b.pico_na_partida:
        assert a.W_pico == pytest.approx(b.W_pico, rel=1e-6)
    assert 1.05 < res.potencia["razao_pico_regime"] < 2.0


def test_pulldown_ambiente_mais_quente_aumenta_pico(res):
    q = _pd(res, T_ambiente_C=43.0)
    assert q.W_pico > res.pulldown.W_pico and q.tempo_h > res.pulldown.tempo_h


def test_pulldown_nao_concluido(res):
    m = modelo_do_projeto(res)
    m.deslocamento_m3 *= 0.2    # compressor 5× menor: a capacidade não vence o gabinete na T_alvo
    p = res.parametros
    pd = simular_pulldown(m, res.capacidade, p.gabinete, p.uso, p.garrafa, p.ciclo, 32.0, 2.5, ParametrosOperacao())
    assert not pd.concluido
    assert pd.T_alvo < pd.T_produto_equilibrio < pd.T_produto_inicial
    assert pd.T_produto[-1] == pytest.approx(pd.T_produto_equilibrio + 0.5)


def test_pulldown_entradas_invalidas(res):
    with pytest.raises(ErroProjeto):
        _pd(res, T_produto_inicial_C=2.7)
    with pytest.raises(ErroProjeto):
        _pd(res, hA_produto_W_K=-1.0)


# ------------------------------------------------------------------------- potência máxima
def test_limite_inativo(res):
    r = _dim(500.0)
    assert r.carga.Q_projeto == pytest.approx(res.carga.Q_projeto, rel=1e-9)
    assert r.potencia["atende"] and not r.potencia["limitado"]
    assert any(a.origem == "potência" and a.nivel == "INFO" for a in r.avisos)


def test_limite_regime_ativo(res):
    r = _dim(100.0)
    assert r.balanco.W_el == pytest.approx(100.0, rel=1e-9)
    assert r.potencia["limitado"] and r.potencia["atende"]
    assert r.carga.caso_governante.startswith("limitado pela potência")
    assert r.carga.fator_umidade == pytest.approx(res.carga.fator_umidade, rel=1e-3)
    assert r.compressor.deslocamento_cm3 < res.compressor.deslocamento_cm3
    assert r.energia["fracao_ligado"] == pytest.approx(r.carga.Q_regime / r.carga.Q_projeto)
    assert r.pulldown.tempo_h > res.pulldown.tempo_h
    assert any("pico estimado" in a.mensagem for a in r.avisos)   # pico (≈ 1,3×) acima de 100 W
    # o balanço de umidade continua fechado com o compressor menor
    u = r.carga.infiltracao["umidade"]
    ev = r.evaporador
    from predimref.propriedades import ar_seco
    m_ar = ev.C_ar / ar_seco(ev.T_ar_in).cp
    remov = m_ar * (1 - math.exp(-u["NTU_ar"])) * (u["W_interno"] - u["W_superficie"]) * u["fracao_ligado"]
    assert remov == pytest.approx(r.carga.infiltracao["agua_kg_dia"] / 86400.0, rel=2e-2)


def test_limite_pico_ativo(res):
    rp = RestricaoPotencia(criterio="pico_pulldown")
    r = _dim(130.0, restricao_potencia=rp)
    assert 130.0 * (1 - rp.tolerancia) <= r.pulldown.W_pico <= 130.0 * (1 + 1e-6)
    assert r.potencia["W_criterio_W"] == pytest.approx(r.pulldown.W_pico)
    assert r.potencia["limitado"] and r.balanco.W_el < 130.0 / 1.2


def test_limite_sem_cop_iterativo():
    r = dimensionar(EntradasProjeto(COP=None, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0,
                                    potencia_max_compressor_W=90.0), ParametrosProjeto(analise_sensibilidade=False))
    assert 90.0 * 0.99 <= r.balanco.W_el <= 90.0 * (1 + 1e-6) and r.potencia["limitado"]


def test_limite_inviavel_informa_cop():
    with pytest.raises(ErroProjeto, match="inviável") as exc:
        _dim(60.0)
    assert "COP ≥" in str(exc.value) and "100 % ligado" in str(exc.value)


def test_modo_verificar(res):
    r = _dim(100.0, restricao_potencia=RestricaoPotencia(modo="verificar"))
    assert r.balanco.W_el == pytest.approx(res.balanco.W_el, rel=1e-9)
    assert r.potencia["atende"] is False
    assert any(a.nivel == "CRITICO" and a.origem == "potência" for a in r.avisos)


@pytest.mark.parametrize("W, rp", [(-5.0, RestricaoPotencia()), (float("nan"), RestricaoPotencia()),
                                   (100.0, RestricaoPotencia(criterio="pico")),
                                   (100.0, RestricaoPotencia(modo="otimizar"))])
def test_restricao_invalida(W, rp):
    with pytest.raises(ErroProjeto):
        _dim(W, restricao_potencia=rp)


def test_sem_simulacao_de_pulldown():
    r = _dim(simular_pulldown=False)
    assert r.pulldown is None and r.potencia == {}
    d = r.para_dict()
    assert d["pulldown"] is None and d["amesim"]["pulldown_estimado"] is None
    r2 = _dim(400.0, simular_pulldown=False, restricao_potencia=RestricaoPotencia(criterio="pico_pulldown"))
    assert r2.pulldown is not None and r2.potencia["atende"]


def test_exportacao(res):
    r = _dim(100.0)
    d = r.para_dict()
    json.dumps(d)
    assert d["entradas"]["potencia_max_compressor_W"] == 100.0
    assert d["potencia_compressor"]["limitado"] is True
    assert d["amesim"]["restricoes"]["criterio"] == "regime" and d["amesim"]["restricoes"]["atendida"] is True
    pe = d["amesim"]["pulldown_estimado"]
    assert pe["tempo_ate_T_alvo_s"] == pytest.approx(r.pulldown.tempo_s)
    cv = d["pulldown"]["curva"]
    assert len(cv["t_h"]) == len(cv["W_el_W"]) == len(cv["T_produto_C"])
    assert cv["T_produto_C"][0] == pytest.approx(32.0) and cv["T_produto_C"][-1] == pytest.approx(2.5, abs=1e-6)
    assert "PULL-DOWN ESTIMADO" in r.resumo() and "limite de potência 100 W" in r.resumo()
