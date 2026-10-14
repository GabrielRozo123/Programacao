import pytest

from predimref.propriedades import Fluido, ar_umido


@pytest.mark.parametrize("fluido, tnb_c", [
    ("R290", -42.11),    # ponto de ebulição normal (NIST Chemistry WebBook)
    ("R600a", -11.75),
    ("R134a", -26.07),
])
def test_ponto_ebulicao_normal(fluido, tnb_c):
    fl = Fluido(fluido)
    assert fl.Tsat(101325.0) - 273.15 == pytest.approx(tnb_c, abs=0.1)


def test_estado_saturado_consistente():
    fl = Fluido("R290")
    P = 4e5
    sat = fl.sat(P)
    v = fl.estado_PQ(P, 1.0)
    l = fl.estado_PQ(P, 0.0)
    assert v.x == 1.0 and l.x == 0.0
    assert v.h == pytest.approx(sat.hv) and l.h == pytest.approx(sat.hl)
    m = fl.estado_PX(P, 0.4)
    assert m.x == pytest.approx(0.4, abs=1e-9) and m.bifasico


def test_titulo_fora_do_domo():
    fl = Fluido("R290")
    sub = fl.estado_PT(15e5, 300.0)
    sup = fl.estado_PT(4e5, 290.0)
    assert sub.x < 0 and sup.x > 1
    assert sub.mu is not None and sup.k is not None


def test_fluido_nao_suportado():
    with pytest.raises(ValueError):
        Fluido("R744")


def test_psicrometria():
    a = ar_umido(305.15, 0.6)
    # 32 °C e 60 % UR: W ≈ 0,0181 kg/kg e h ≈ 78,6 kJ/kg (carta psicrométrica ASHRAE)
    assert a["W"] == pytest.approx(0.0181, abs=3e-4)
    assert a["h"] / 1e3 == pytest.approx(78.6, abs=0.8)
