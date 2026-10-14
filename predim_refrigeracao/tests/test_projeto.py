import json

import pytest

from predimref import EntradasProjeto, ErroProjeto, ParametrosProjeto, dimensionar
from predimref.ciclo import ParametrosCiclo


@pytest.fixture(scope="module")
def res():
    return dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0))


def test_coerencia_global(res):
    b, c = res.balanco, res.ciclo
    assert abs(b.erro_balanco) < 1e-8
    assert abs(res.exergia["erro_fechamento"]) < 1e-8
    assert res.condensador.Q == pytest.approx(b.Q_cond, rel=3e-3)
    assert res.evaporador.Q == pytest.approx(b.Q_evap, rel=3e-3)
    assert res.ciclo.estados["4"].P == pytest.approx(res.evaporador.P_in, rel=1e-4)
    assert res.capilar.escolhido.m == pytest.approx(b.m)
    assert c.COP == pytest.approx(2.0)


def test_faixas_realistas(res):
    """Ordens de grandeza de um visi-cooler de 200 L a R290 (sanidade, não validação)."""
    assert 150 < res.carga.Q_projeto < 400
    assert 1.0 < res.compressor.deslocamento_cm3 < 5.0
    assert 0.5e-3 < res.capilar.escolhido.D < 1.2e-3
    assert 0.02 < res.carga_refrigerante["total_kg"] < 0.15
    assert 1.0 < res.energia["total_kWh_dia"] < 5.0


def test_json(res):
    d = res.para_dict()
    s = json.dumps(d)
    assert "amesim" in d and "capilar" in d["amesim"]
    assert d["amesim"]["capilar"]["comprimento_m"] == pytest.approx(res.capilar.escolhido.L)
    assert len(s) > 1000
    assert "resumo" not in d
    assert "CAPILAR" in res.resumo()


def test_cop_impossivel_com_sugestao():
    with pytest.raises(ErroProjeto, match="seriam necessários"):
        dimensionar(EntradasProjeto(COP=4.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0))


def test_garrafas_e_fluidos():
    for fluido in ("R600a", "R134a"):
        r = dimensionar(EntradasProjeto(COP=1.7, T_ambiente_C=32.0, T_alvo_C=3.0, n_garrafas=150, fluido=fluido),
                        ParametrosProjeto(analise_sensibilidade=False))
        assert r.capacidade.n_garrafas == 150
        assert r.capilar.escolhido.L > 0


def test_ihx_melhora_capacidade_especifica():
    e = EntradasProjeto(COP=2.0, T_ambiente_C=32.0, T_alvo_C=2.5, volume_interno_L=200.0)
    r0 = dimensionar(e, ParametrosProjeto(analise_sensibilidade=False))
    r1 = dimensionar(e, ParametrosProjeto(ciclo=ParametrosCiclo(eficacia_ihx=0.6), analise_sensibilidade=False))
    assert r1.ciclo.q_evap > r0.ciclo.q_evap
    assert r1.balanco.m < r0.balanco.m
