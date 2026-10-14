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


# ------------------------------------------------------------------ modo de eficácia
def _cond(caso, **kw):
    fl, c, b = caso
    e = c.estados
    p = condensador_padrao()
    for k, v in kw.items():
        setattr(p, k, v)
    return dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, p)


def _evap(caso, sa=5.0, **kw):
    fl, c, b = caso
    e = c.estados
    p = evaporador_padrao()
    for k, v in kw.items():
        setattr(p, k, v)
    return dimensionar_evaporador(fl, b.m, e["3i"].h, e["1"].P, sa, 275.65, p, 1.05)


@pytest.mark.parametrize("eps, trocadores", [(0.4, "ce"), (0.65, "ce"), (0.8, "c")])
def test_eficacia_atingida(caso, eps, trocadores):
    rs = ([_cond(caso, eficacia=eps)] if "c" in trocadores else []) + (
        [_evap(caso, eficacia=eps)] if "e" in trocadores else [])
    for r in rs:
        assert r.eficacia == pytest.approx(eps, abs=1e-3)
        assert r.eficacia_alvo == eps
        assert 0.3 <= r.velocidade_face <= 4.0 and 1 <= r.n_fileiras <= 6
        # definição: ε = ΔT_ar / (T_sat − T_ar,entrada)
        assert abs(r.T_ar_out - r.T_ar_in) / abs(r.T_sat_ref - r.T_ar_in) == pytest.approx(r.eficacia, rel=1e-12)
        assert 0 < r.eficacia_Qmax <= 1.0


def test_eficacia_monotona_em_V_e_N(caso):
    eps = {}
    for N in (2, 4):
        for V in (0.8, 1.6):
            pc = condensador_padrao()
            pc.geometria.n_fileiras = N
            pc.velocidade_face = V
            fl, c, b = caso
            e = c.estados
            eps[(N, V)] = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, pc).eficacia
    assert eps[(2, 0.8)] > eps[(2, 1.6)] and eps[(4, 0.8)] > eps[(4, 1.6)]   # cai com V
    assert eps[(4, 0.8)] > eps[(2, 0.8)] and eps[(4, 1.6)] > eps[(2, 1.6)]   # sobe com N


def test_eficacia_menor_que_limite_ntu_uniforme(caso):
    """Evaporador só bifásico (SA = 0): cada trecho tem ε = 1 − exp(−NTU_trecho); pela desigualdade
    de Jensen a eficácia global não supera 1 − exp(−NTU_global) e fica próxima dela."""
    r = _evap(caso, sa=0.0, eficacia=0.6)
    lim = 1.0 - math.exp(-r.NTU)
    assert r.eficacia <= lim + 1e-9
    assert r.eficacia == pytest.approx(lim, rel=0.05)
    assert set(r.zonas) == {"evaporação"}


def test_eficacia_inviavel(caso):
    # a 0,8 o evaporador (tubo 3/8", 1 circuito, G ≈ 14 kg/m²s) não chega com até 6 fileiras
    with pytest.raises(ErroProjeto, match="inatingível"):
        _evap(caso, eficacia=0.8)
    with pytest.raises(ErroProjeto, match="inatingível"):
        _evap(caso, eficacia=0.97)
    with pytest.raises(ErroProjeto):
        _cond(caso, eficacia=1.2)


def test_fileiras_fixas(caso):
    p = condensador_padrao()
    p.eficacia, p.fileiras_automaticas = 0.65, False
    p.geometria.n_fileiras = 4
    fl, c, b = caso
    e = c.estados
    r = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, p)
    assert r.n_fileiras == 4 and not r.fileiras_escolhidas_automaticamente
    assert r.eficacia == pytest.approx(0.65, abs=1e-3)
    # a dica (N, V) de uma solução anterior leva à mesma solução
    r2 = dimensionar_condensador(fl, b.m, e["2"].P, e["2"].h, 3.0, 305.15, p, (r.n_fileiras, r.velocidade_face))
    assert r2.velocidade_face == pytest.approx(r.velocidade_face, rel=1e-3)


def test_sem_eficacia_mantem_modo_velocidade(caso):
    r = _cond(caso)
    assert r.eficacia_alvo is None and r.velocidade_face == condensador_padrao().velocidade_face
    assert 0 < r.eficacia < 1
