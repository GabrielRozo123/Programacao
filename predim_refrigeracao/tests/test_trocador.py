import copy
import math

import pytest

from predimref.avisos import ErroProjeto
from predimref.ciclo import ParametrosCiclo, balanco, resolver_ciclo
from predimref.propriedades import Fluido
from predimref.trocador import (_eps_cruzado, condensador_padrao, dimensionar_condensador,
                                dimensionar_evaporador, evaporador_padrao)


@pytest.fixture(scope="module")
def caso():
    fl = Fluido("R290")
    c = resolver_ciclo(fl, 265.65, 318.15, ParametrosCiclo(), 2.0)
    b = balanco(c, 250.0)
    return fl, c, b


def test_eps_limites():
    assert _eps_cruzado(1.0, 1e12, 1.0) == pytest.approx(1 - math.exp(-1.0), rel=1e-6)   # C_r → 0
    for C_ref, C_ar in ((1.0, 3.0), (3.0, 1.0), (1.0, 1.0)):
        e = _eps_cruzado(50.0, C_ref, C_ar)
        assert 0 < e <= 1.0
    # continuidade na troca de C_min
    assert _eps_cruzado(2.0, 1.0, 1.0 + 1e-9) == pytest.approx(_eps_cruzado(2.0, 1.0 + 1e-9, 1.0), rel=1e-6)


def test_condensador_energia_e_ar(caso):
    fl, c, b = caso
    e = c.estados
    r = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, condensador_padrao())
    Q_ref = b.m * (e["2"].h - e["3"].h)
    assert r.Q == pytest.approx(Q_ref, rel=2e-3)
    # balanço do ar em cada trecho: Q = Ċ'_ar L ΔT_ar com Ċ'_ar (por metro) igual em todos os trechos
    Ca = [s.Q / (s.L * (s.T_ar_out - 305.15)) for s in r.segmentos]
    assert max(Ca) == pytest.approx(min(Ca), rel=1e-9)
    assert set(r.zonas) == {"dessuperaquecimento", "condensação", "sub-resfriamento"}
    assert r.L_adotado >= r.L_requerido * 1.10 - 1e-9
    assert r.T_ar_in < r.T_ar_out < fl.Tsat(r.P_in)


def test_condensador_independe_da_malha(caso):
    fl, c, b = caso
    e = c.estados
    p20, p60 = condensador_padrao(), condensador_padrao()
    p60.n_segmentos = 60
    L20 = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, p20).L_requerido
    L60 = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, p60).L_requerido
    assert L20 == pytest.approx(L60, rel=0.01)


def test_evaporador_pressao_e_superaquecimento(caso):
    fl, c, b = caso
    e = c.estados
    r = dimensionar_evaporador(fl, b.m, e["3i"].h, e["1"].P, 5.0, 275.65, evaporador_padrao(), 1.05)
    assert r.P_out == pytest.approx(e["1"].P, abs=2.0)
    assert r.segmentos[-1].h_out == pytest.approx(e["1"].h, rel=1e-6)
    assert r.Q == pytest.approx(b.m * (e["1"].h - e["3i"].h), rel=2e-3)
    assert r.T_ar_out < r.T_ar_in


def test_evaporador_mais_circuitos_menor_dp(caso):
    fl, c, b = caso
    e = c.estados
    p1, p2 = evaporador_padrao(), evaporador_padrao()
    p2.n_circuitos = 2
    r1 = dimensionar_evaporador(fl, b.m * 6, e["3i"].h, e["1"].P, 5.0, 275.65, p1)
    r2 = dimensionar_evaporador(fl, b.m * 6, e["3i"].h, e["1"].P, 5.0, 275.65, p2)
    assert r2.dP_ref < r1.dP_ref


def test_trecho_impossivel(caso):
    fl, c, b = caso
    e = c.estados
    with pytest.raises(ErroProjeto):
        dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 14.0, 305.15, condensador_padrao())


def test_correlacoes_alternativas(caso):
    fl, c, b = caso
    e = c.estados
    Ls = {}
    for corr in ("shah_2022", "shah_2013", "shah_2009", "shah_1979", "chato_1962"):
        p = condensador_padrao()
        p.correlacao_bifasico = corr
        Ls[corr] = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, p).L_requerido
    assert Ls["shah_2022"] == pytest.approx(Ls["shah_2013"])   # hidrocarboneto
    assert max(Ls.values()) / min(Ls.values()) < 1.6
    pe = copy.deepcopy(evaporador_padrao())
    pe.correlacao_bifasico = "liu_winterton_1991"
    assert dimensionar_evaporador(fl, b.m, e["3i"].h, e["1"].P, 5.0, 275.65, pe).L_requerido > 0
