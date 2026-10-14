import pytest

from predimref.avisos import Avisos, ErroProjeto
from predimref.ciclo import ParametrosCiclo, balanco, escala_dT_para_cop, exergia, resolver_ciclo
from predimref.compressor import ParametrosCompressor, dimensionar_compressor, eficiencia_volumetrica
from predimref.propriedades import Fluido

TE, TC = 265.65, 318.15


@pytest.fixture(scope="module")
def fl():
    return Fluido("R290")


@pytest.mark.parametrize("ihx", [0.0, 0.6])
def test_balanco_energia_e_exergia_fecham(fl, ihx):
    p = ParametrosCiclo(eficacia_ihx=ihx)
    c = resolver_ciclo(fl, TE, TC, p, 2.0, dP_cond=5e3, dP_evap=8e3)
    b = balanco(c, 250.0)
    assert abs(b.erro_balanco) < 1e-9
    assert b.Q_carcaca >= 0
    ex = exergia(c, b, 305.15, 275.65)
    assert abs(ex["erro_fechamento"]) < 1e-9
    assert all(v >= -1e-6 for v in ex["destruicao_W"].values())   # 2ª lei por componente
    assert ex["eta_II"] == pytest.approx(2.0 / (275.65 / (305.15 - 275.65)), rel=1e-9)


def test_cop_definicoes(fl):
    c = resolver_ciclo(fl, TE, TC, ParametrosCiclo(), 2.0)
    assert c.eta_global == pytest.approx(2.0 / c.COP_ciclo_ideal)
    assert c.eta_is == pytest.approx(c.eta_global / 0.72)
    assert c.COP_ciclo_ideal < c.COP_carnot_ciclo
    e = c.estados
    assert (e["2s"].h - e["1s"].h) / (e["2"].h - e["1s"].h) == pytest.approx(c.eta_is, rel=1e-9)


def test_cop_impossivel(fl):
    with pytest.raises(ErroProjeto, match="Carnot"):
        resolver_ciclo(fl, TE, TC, ParametrosCiclo(), 5.5)
    with pytest.raises(ErroProjeto, match="isentrópica"):
        resolver_ciclo(fl, TE, TC, ParametrosCiclo(), 4.2)


def test_avisos_eta(fl):
    av = Avisos()
    resolver_ciclo(fl, TE, TC, ParametrosCiclo(), 3.0, avisos=av)
    assert any("η_global" in a.mensagem for a in av)


def test_escala_dT(fl):
    p = ParametrosCiclo()
    s = escala_dT_para_cop(fl, 2.5, 275.65, 305.15, p, 0.55)
    c = resolver_ciclo(fl, 275.65 - s * p.dT_evap, 305.15 + s * p.dT_cond,
                       ParametrosCiclo(eta_global_sem_cop=0.55), None)
    assert c.COP == pytest.approx(2.5, rel=1e-3)
    assert 0 < s < 1


def test_compressor(fl):
    c = resolver_ciclo(fl, TE, TC, ParametrosCiclo(), 2.0)
    b = balanco(c, 250.0)
    r = dimensionar_compressor(fl, b.m, c.estados["1s"], c.estados["2"].P, b.W_el, c.estados["2"].T,
                               c.eta_global, ParametrosCompressor())
    V = r.deslocamento_cm3 * 1e-6 * 3500 / 60 * r.eta_v
    assert V * c.estados["1s"].rho == pytest.approx(b.m, rel=1e-9)
    assert 0.5 < r.eta_v < 0.95
    assert eficiencia_volumetrica(1.0, ParametrosCompressor(), 1.1) == pytest.approx(0.88)
