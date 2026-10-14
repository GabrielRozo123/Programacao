import pytest

from predimref.avisos import Avisos, ErroProjeto
from predimref.gabinete import (Gabinete, Garrafa, Uso, calcular_carga, infiltracao,
                                resolver_capacidade, transmissao)


def test_cp_choi_okos():
    agua = Garrafa(acucar_g_por_L=0.0, densidade_bebida=1000.0)
    assert agua.cp_bebida(20.0) == pytest.approx(4180.0, rel=0.003)
    refri = Garrafa()
    assert 3850 < refri.cp_bebida(15.0) < 3990


def test_conversao_litros_garrafas_ida_e_volta():
    g, gab = Garrafa(), Gabinete()
    c1 = resolver_capacidade(400.0, None, g, gab, Avisos())
    c2 = resolver_capacidade(None, c1.n_garrafas, g, gab, Avisos())
    assert c2.volume_interno_L == pytest.approx(400.0, rel=0.01)
    assert c1.n_garrafas * g.volume_nominal_L < 400.0   # líquido < volume do gabinete


def test_333_garrafas_nao_cabem_em_200_L():
    av = Avisos()
    resolver_capacidade(200.0, 333, Garrafa(), Gabinete(), av)
    niveis = [a.nivel for a in av]
    assert "CRITICO" in niveis
    assert any("volume de líquido" in a.mensagem for a in av)


def test_sem_capacidade():
    with pytest.raises(ErroProjeto):
        resolver_capacidade(None, None, Garrafa(), Gabinete(), Avisos())


def test_transmissao_parede_plana_sem_bordas():
    """Com fatores de forma desprezíveis (caixa grande) o UA tende a A/R de parede plana."""
    gab = Gabinete(dimensoes_internas_m=(10.0, 10.0, 10.0), fator_pontes_termicas=1.0,
                   esp_base_m=0.05, dT_compartimento_maquina=0.0)
    cap = resolver_capacidade(None, 10, Garrafa(), gab, Avisos())
    tr = transmissao(cap, gab, 305.15, 275.15)
    R = 1 / gab.h_interno + 0.05 / gab.k_isolamento + 1 / gab.h_externo
    UA_plano = 5 * 100.0 / R
    UA_paredes = sum(f.UA for f in tr["faces"])
    assert UA_paredes == pytest.approx(UA_plano, rel=0.03)


def test_infiltracao_limitada_pelo_volume_livre():
    g, gab = Garrafa(), Gabinete()
    av = Avisos()
    cap = resolver_capacidade(200.0, None, g, gab, av)
    inf = infiltracao(cap, Uso(), 305.15, 0.6, 275.65, av)
    assert inf["limitado_por_volume"]
    m_max = cap.volume_ar_livre_L * 1e-3 * 1.2
    assert inf["m_ar_abertura"] < m_max
    assert 0 < inf["Q_latente"] < inf["Q_media"]


def test_carga_total_e_caso_governante():
    g, gab, uso = Garrafa(), Gabinete(), Uso()
    av = Avisos()
    cap = resolver_capacidade(200.0, None, g, gab, av)
    c = calcular_carga(cap, gab, uso, g, 32.0, 0.6, 2.5, av)
    assert c.Q_projeto == pytest.approx(max(c.Q_requerida_regime, c.Q_pulldown) * 1.10)
    assert c.fator_umidade >= 1.0
    with pytest.raises(ErroProjeto):
        calcular_carga(cap, gab, uso, g, 2.0, 0.6, 5.0, av)
