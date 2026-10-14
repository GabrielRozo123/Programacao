import math

import numpy as np
import pytest
from scipy.optimize import brentq
from scipy.special import i0, i1, k0, k1

from predimref.correlacoes import bifasico as bf
from predimref.correlacoes.lado_ar import GeometriaAletada, eficiencia_aleta_schmidt, wang_2000_j_f
from predimref.correlacoes.monofasico import fator_atrito_churchill, nusselt_gnielinski
from predimref.propriedades import Fluido


# ------------------------------------------------------------------ monofásico
def test_churchill_laminar():
    for Re in (100.0, 500.0, 1500.0):
        assert fator_atrito_churchill(Re, 0.0) == pytest.approx(64.0 / Re, rel=0.01)


@pytest.mark.parametrize("Re, eD", [(1e4, 0.0), (1e5, 1e-4), (1e6, 1e-3)])
def test_churchill_vs_colebrook(Re, eD):
    def colebrook(f):
        return 1 / math.sqrt(f) + 2.0 * math.log10(eD / 3.7 + 2.51 / (Re * math.sqrt(f)))
    f_c = brentq(colebrook, 1e-3, 0.2)
    assert fator_atrito_churchill(Re, eD) == pytest.approx(f_c, rel=0.03)


def test_gnielinski_vs_dittus_boelter():
    for Re, Pr in ((2e4, 0.7), (5e4, 3.0), (1e5, 5.0)):
        db = 0.023 * Re ** 0.8 * Pr ** 0.4
        assert nusselt_gnielinski(Re, Pr) == pytest.approx(db, rel=0.20)


def test_gnielinski_continuo_na_transicao():
    a, b = nusselt_gnielinski(2300.0, 3.0), nusselt_gnielinski(2300.001, 3.0)
    c, d = nusselt_gnielinski(9999.999, 3.0), nusselt_gnielinski(1e4, 3.0)
    assert a == pytest.approx(b, rel=1e-4) and c == pytest.approx(d, rel=1e-4)


# ------------------------------------------------------------------ lado do ar
def test_eficiencia_schmidt_vs_bessel_aleta_anular():
    """Schmidt (φ de raio equivalente) contra a solução exata da aleta anular (Incropera Tab. 3.5)."""
    for r2_r1 in (1.6, 2.2, 3.0):
        for mr1 in (0.1, 0.25, 0.4):
            r1 = 5e-3
            r2 = r2_r1 * r1
            m = mr1 / r1
            num = k1(m * r1) * i1(m * r2) - i1(m * r1) * k1(m * r2)
            den = i0(m * r1) * k1(m * r2) + k0(m * r1) * i1(m * r2)
            eta_exato = 2 * r1 / (m * (r2 ** 2 - r1 ** 2)) * num / den
            phi = (r2_r1 - 1.0) * (1.0 + 0.35 * math.log(r2_r1))
            eta_s = math.tanh(m * r1 * phi) / (m * r1 * phi)
            assert eta_s == pytest.approx(eta_exato, rel=0.03)


def test_eficiencia_aleta_limites():
    g = GeometriaAletada()
    assert eficiencia_aleta_schmidt(1e-9, g) == pytest.approx(1.0, abs=1e-6)
    assert eficiencia_aleta_schmidt(50.0, g) > eficiencia_aleta_schmidt(150.0, g)


def test_wang_j_fisicamente_coerente():
    """Com o termo 0,158 ln[N (Fp/Dc)^0,41] em P3, j é contínuo de N=1 para N=2 e quase
    independente de N em Re alto (comportamento dos dados de aletas planas)."""
    for Fp in (1.5e-3, 2.0e-3, 3.0e-3):
        js = []
        for N in (1, 2, 4, 6):
            g = GeometriaAletada(passo_aleta=Fp, n_fileiras=N)
            js.append(wang_2000_j_f(4000.0, g)[0])
        assert js[1] == pytest.approx(js[0], rel=0.15)
        assert max(js) / min(js) < 1.3
        g1 = GeometriaAletada(passo_aleta=Fp, n_fileiras=2)
        j, f = wang_2000_j_f(1500.0, g1)
        assert 0.005 < j < 0.03 and 0.01 < f < 0.1


# ------------------------------------------------------------------ bifásico
@pytest.fixture(scope="module")
def sat_cond():
    fl = Fluido("R290")
    return fl.sat(fl.Psat(318.15))


@pytest.fixture(scope="module")
def sat_evap():
    fl = Fluido("R290")
    return fl.sat(fl.Psat(265.65))


def test_shah_regimes(sat_cond):
    D = 8.8e-3
    h_alto, reg_alto = bf.condensacao_shah_2013(400.0, 0.6, D, sat_cond)
    h_baixo, reg_baixo = bf.condensacao_shah_2013(10.0, 0.3, D, sat_cond)
    assert reg_alto == "I" and reg_baixo == "III"
    assert 2000 < h_alto < 10000 and 300 < h_baixo < 3000
    # 2022 = 2013 para hidrocarbonetos
    assert bf.condensacao_shah_2022(100.0, 0.5, D, sat_cond, True) == bf.condensacao_shah_2013(100.0, 0.5, D, sat_cond)


def test_shah_hNu_usa_Re_da_fase_liquida(sat_cond):
    """h_Nu cresce com x (Re_LS = G(1−x)D/μ_l diminui), como no artigo de Shah (2009, eq. 9)."""
    _, h1, _, _ = bf._shah_hI_hNu(20.0, 0.2, 8.8e-3, sat_cond)
    _, h2, _, _ = bf._shah_hI_hNu(20.0, 0.8, 8.8e-3, sat_cond)
    assert h2 / h1 == pytest.approx((0.8 / 0.2) ** (1 / 3), rel=1e-6)


def test_ebulicao_cresce_com_G_e_q(sat_evap):
    D = 8.8e-3
    for corr in ("gungor_winterton_1987", "liu_winterton_1991"):
        f = (lambda G, q: bf.ebulicao_com_secagem(G, 0.5, D, q, sat_evap, 44.1, corr))
        assert f(200.0, 5000.0) > f(50.0, 5000.0)
        assert f(100.0, 20000.0) > f(100.0, 2000.0)


def test_secagem_tende_ao_vapor(sat_evap):
    D = 8.8e-3
    h1 = bf.ebulicao_com_secagem(50.0, 1.0, D, 3000.0, sat_evap, 44.1)
    assert h1 == pytest.approx(bf.h_vapor_saturado(50.0, D, sat_evap), rel=1e-9)


def test_msh_limites(sat_evap):
    D, G = 8.8e-3, 150.0
    A = bf.gradiente_atrito_msh(G, 0.0, D, sat_evap)
    B = bf.gradiente_atrito_msh(G, 1.0, D, sat_evap)
    xs = np.linspace(0, 1, 41)
    vals = [bf.gradiente_atrito_msh(G, x, D, sat_evap) for x in xs]
    assert B > A and max(vals) >= B  # máximo típico perto de x ≈ 0,85
    Re = G * D / sat_evap.mul
    assert A == pytest.approx((64 / Re if Re <= 1187 else 0.3164 * Re ** -0.25) * G ** 2 / (2 * sat_evap.rhol * D))


def test_fracao_vazio(sat_evap):
    for x in (0.05, 0.3, 0.7, 0.95):
        a_ra = bf.fracao_vazio_rouhani_axelsson(x, 100.0, sat_evap)
        a_h = bf.fracao_vazio_homogenea(x, sat_evap)
        assert 0.0 < a_ra < a_h < 1.0   # deslizamento => menos vazio que o homogêneo
