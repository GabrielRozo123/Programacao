"""Reator, estequiometria e transporte."""

import numpy as np
import pytest

from biokin.library import er_methoxide
from biokin.lhhw import derive_rate_law
from biokin.network import build_network
from biokin.reactor import (
    MonolithOperation,
    concentration_vector,
    conversion,
    simulate_batch,
    simulate_monolith,
)
from biokin.species import FLUID_SPECIES, overall_stoich
from biokin.transport import (
    FluidProperties,
    MonolithGeometry,
    effectiveness_factor,
    generalized_thiele,
    sherwood_number,
    wilke_chang_diffusivity,
)


@pytest.fixture
def rede():
    mech = er_methoxide(("G",))
    i = [k for k, s in enumerate(mech.steps) if s.label == "sr"][0]
    return build_network(derive_rate_law(mech, i))


@pytest.fixture
def parametros(rede):
    valores = {
        "k_1": 1.8e-3, "k_2": 4.5e-3, "k_3": 9.0e-3,
        "Keq_1": 3.0, "Keq_2": 2.0, "Keq_3": 5.0,
        "K_ads_M": 0.35, "K_ads_G": 4.0,
    }
    return np.array([valores[n] for n in rede.param_names])


def test_estequiometria_global():
    assert overall_stoich() == {"TG": -1, "M": -3, "E": 3, "G": 1}


def test_adsorcao_compartilhada_entre_as_tres_reacoes(rede):
    """K_ads_M deve ser um único parâmetro, não três."""
    assert sum(n.startswith("K_ads_M") for n in rede.param_names) == 1
    assert sum(n.startswith("k_") for n in rede.param_names) == 3


def test_batelada_conserva_balancos(rede, parametros):
    """Grupos acila e esqueleto de glicerol devem se conservar."""
    C0 = concentration_vector({"TG": 0.9, "M": 8.1})
    t = np.linspace(0, 120, 25)
    prof = simulate_batch(rede, parametros, C0, t, 10.0)
    idx = {s: i for i, s in enumerate(FLUID_SPECIES)}

    acila = 3 * prof[:, idx["TG"]] + 2 * prof[:, idx["DG"]] + prof[:, idx["MG"]] + prof[:, idx["E"]]
    esqueleto = prof[:, idx["TG"]] + prof[:, idx["DG"]] + prof[:, idx["MG"]] + prof[:, idx["G"]]
    metanol = prof[:, idx["M"]] + prof[:, idx["E"]]

    assert np.allclose(acila, acila[0], rtol=1e-6)
    assert np.allclose(esqueleto, esqueleto[0], rtol=1e-6)
    assert np.allclose(metanol, metanol[0], rtol=1e-6)


def test_conversao_cresce_monotonamente(rede, parametros):
    C0 = concentration_vector({"TG": 0.9, "M": 8.1})
    prof = simulate_batch(rede, parametros, C0, np.linspace(0, 120, 30), 10.0)
    X = conversion(prof)
    assert np.all(np.diff(X) >= -1e-9)
    assert 0.0 <= X[-1] <= 1.0


def test_difusao_no_washcoat_reduz_conversao(rede, parametros):
    """O modo 'full' nunca pode converter mais que o 'ideal'."""
    op = MonolithOperation(velocity_m_s=0.01, geometry=MonolithGeometry(length_m=0.30))
    tau = np.linspace(0, op.max_space_time_min, 7)
    C0 = concentration_vector({"TG": 0.9, "M": 8.1})
    ideal = conversion(simulate_monolith(rede, parametros, C0, tau, op, "ideal"))[-1]
    full = conversion(simulate_monolith(rede, parametros, C0, tau, op, "full"))[-1]
    assert full <= ideal + 1e-9
    assert full > 0


def test_geometria_400_cpsi():
    """400 cpsi = 20 células por polegada -> passo de 1,27 mm."""
    g = MonolithGeometry(cell_density_cpsi=400.0)
    assert g.cell_pitch_m == pytest.approx(0.0254 / 20, rel=1e-9)
    assert 1500 < g.specific_surface_m2_m3 < 4000
    assert 0.0 < g.open_frontal_area < 1.0


def test_sherwood_tende_ao_assintotico():
    """Canal longo e vazão baixa: Sh -> 2,98."""
    assert sherwood_number(1e-6, 1.0, 1e-3, 10.0) == pytest.approx(2.98, rel=1e-3)
    # entrada curta e vazão alta aumentam Sh
    assert sherwood_number(50.0, 1000.0, 1e-3, 0.05) > 2.98


def test_efetividade_limites():
    assert effectiveness_factor(1e-12) == pytest.approx(1.0)
    assert effectiveness_factor(100.0) == pytest.approx(0.01, rel=1e-6)
    assert 0.0 < effectiveness_factor(1.0) < 1.0


def test_thiele_generalizado_bate_com_primeira_ordem():
    """Para cinética de 1ª ordem o módulo generalizado reduz ao clássico."""
    k, L, D, rho = 5.0, 3e-5, 1e-10, 1300.0
    phi = generalized_thiele(lambda c: k * c, 1.0, L, D, rho)
    # k está em L/(g_cat·min); a constante volumétrica em 1/s é
    #   k_v = k [L/(g·min)] · rho [g/m³] / (1000 L/m³) / (60 s/min)
    #       = k · rho[kg/m³] / 60
    k_vol = k * rho / 60.0
    esperado = L * np.sqrt(k_vol / D)
    assert phi == pytest.approx(esperado, rel=1e-3)


def test_wilke_chang_ordem_de_grandeza():
    """Triglicerídeo em metanol a 60 °C: ~1e-10 a 1e-9 m²/s."""
    D = wilke_chang_diffusivity(333.15, 6e-4)
    assert 1e-10 < D < 5e-9
