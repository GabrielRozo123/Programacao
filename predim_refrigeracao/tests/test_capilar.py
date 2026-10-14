import pytest

from predimref.capilar import (ParametrosCapilar, comprimento_capilar, dimensionar_capilar,
                               vazao_capilar)
from predimref.propriedades import Fluido

# Li, Lin & Chen (1990), Int. J. Refrig. 13(3):181-186: R12, D = 0,66 mm, L = 1,5 m, e/D = 0,003
# (condições conforme reproduzidas por Wongwises et al. 2002, ScienceAsia 28:71-76, Tab. 1)
LI_1990 = [(31.40, 9.67e5, 1.13e-3), (23.40, 7.17e5, 0.844e-3)]


@pytest.mark.parametrize("Ti, Pi, m_exp", LI_1990)
def test_validacao_li_1990(Ti, Pi, m_exp):
    fl = Fluido("R12")
    p = ParametrosCapilar(rugosidade_m=0.003 * 0.66e-3)
    h = fl.estado_PT(Pi, Ti + 273.15).h
    m = vazao_capilar(fl, 0.66e-3, 1.5, Pi, h, 1.5e5, p)
    assert m == pytest.approx(m_exp, rel=0.05)
    assert m <= m_exp * 1.01   # HEM sem metaestabilidade não deve superestimar a vazão


def test_convergencia_malha():
    fl = Fluido("R290")
    h = fl.estado_PT(15.34e5, 315.15).h
    Ls = [comprimento_capilar(fl, 0.83e-3, 0.711e-3, 15.34e5, h, 3.75e5, ParametrosCapilar(n_passos=n)).L
          for n in (150, 300, 1200)]
    assert Ls[1] == pytest.approx(Ls[2], rel=2e-3)


def test_problema_inverso():
    fl = Fluido("R290")
    h = fl.estado_PT(15.34e5, 315.15).h
    p = ParametrosCapilar()
    r = comprimento_capilar(fl, 0.83e-3, 0.787e-3, 15.34e5, h, 3.75e5, p)
    m = vazao_capilar(fl, 0.787e-3, r.L, 15.34e5, h, 3.75e5, p)
    assert m == pytest.approx(0.83e-3, rel=1e-5)


def test_flash_propano_abaixo_de_psat():
    """Para o propano a ~42 °C, Tβ > 1: o líquido esfria na expansão isentálpica e o flash
    acontece abaixo de P_sat(T_in) — e não há blocagem espúria no ponto de flash."""
    fl = Fluido("R290")
    T_in = 315.15
    h = fl.estado_PT(15.34e5, T_in).h
    r = comprimento_capilar(fl, 0.83e-3, 1.016e-3, 15.34e5, h, 3.75e5, ParametrosCapilar())
    assert r.P_flash < fl.Psat(T_in)
    assert r.L_bifasico > 0 and r.x_saida > 0.2


def test_blocagem_com_contrapressao_baixa():
    fl = Fluido("R600a")
    h = fl.estado_PT(6.0e5, 313.15).h
    r = comprimento_capilar(fl, 1.0e-3, 0.8e-3, 6.0e5, h, 0.3e5, ParametrosCapilar())
    assert r.blocado and r.P_saida > 0.3e5
    # acima da pressão crítica de saída a vazão não depende da contrapressão
    p = ParametrosCapilar()
    m1 = vazao_capilar(fl, 0.8e-3, 2.0, 6.0e5, h, 0.3e5, p)
    m2 = vazao_capilar(fl, 0.8e-3, 2.0, 6.0e5, h, 0.2e5, p)
    assert m1 == pytest.approx(m2, rel=1e-4)


def test_selecao():
    fl = Fluido("R290")
    h = fl.estado_PT(15.34e5, 315.15).h
    sel = dimensionar_capilar(fl, 0.83e-3, 15.34e5, h, 3.75e5, ParametrosCapilar())
    assert 1.0 <= sel.escolhido.L <= 5.0
    Ls = [c.L for c in sel.candidatos]
    assert Ls == sorted(Ls)   # L cresce com D
    assert sel.sensibilidade["vazao_rel_D_menos_tol"] < 0 < sel.sensibilidade["vazao_rel_D_mais_tol"]
