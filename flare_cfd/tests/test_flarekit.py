"""Testes das identidades algébricas e dos solvers (pytest -q)."""
import math

import numpy as np
import pytest
import torch

from flarekit import safety
from flarekit import semiempirical as se
from flarekit.les import FlareLES, LESConfig, stretched_faces
from flarekit.props import METHANE, PROPANE, beta_pdf_table, state_relation, stoichiometry


@pytest.fixture(scope="module")
def table():
    st = stoichiometry(PROPANE)
    sr = state_relation(PROPANE, 311.0, 298.15, 0.25, use_cantera=False)
    return beta_pdf_table(sr, st["Z_st"], nZ=101, ns=9)


def test_stoichiometry_propane():
    st = stoichiometry(PROPANE)
    assert st["s"] == pytest.approx(15.57, abs=0.01)
    assert st["Z_st"] == pytest.approx(0.0603, abs=1e-4)


def test_chamberlain_tilt_continuity_and_K():
    # os dois ramos da inclinação se encontram em R = 0.05 (coeficientes 134 e 1726)
    assert 8000 * 0.05 == pytest.approx(134 + 1726 * math.sqrt(0.05 - 0.026), rel=5e-3)
    sc = se.Scenario(PROPANE)
    assert sc.cham0.K == pytest.approx(0.2)
    assert sc.cham0.b == pytest.approx(0.2 * sc.cham0.L_b)
    # sem vento a base do frustum tem o diâmetro do tip
    assert sc.cham0.W1 == pytest.approx(sc.tip["d_j"], rel=1e-6)


def test_worked_example_values():
    sc = se.Scenario(PROPANE, H=50.0, xrad_comp=False)   # exemplo do documento: Chamberlain original
    c = sc.cham
    assert sc.L_api == pytest.approx(50.1, abs=0.2)
    assert c.L_b0 == pytest.approx(54.4, abs=0.2)
    assert c.L_b == pytest.approx(27.4, abs=0.2)
    assert c.alpha == pytest.approx(50.9, abs=0.2)
    assert c.SEP / 1e3 == pytest.approx(216, abs=2)


def test_point_source_inverse_square():
    q1 = se.q_point_source(np.array([[10.0, 0, 0]]), np.zeros(3), 0.3, 1e8, 298.15, 0.0001)
    q2 = se.q_point_source(np.array([[20.0, 0, 0]]), np.zeros(3), 0.3, 1e8, 298.15, 0.0001)
    assert q1[0] / q2[0] == pytest.approx(4.0, rel=0.05)


def test_beta_pdf_mean_preserved(table):
    # sem variância, ρ̃ coincide com a relação de estado; com variância, T̃ cai no pico (TCI)
    i = int(np.argmin(np.abs(table.Zt - table.Z_st)))
    assert table.T[i, 0] > table.T[i, -1]
    assert np.all(table.rho > 0)


def test_dose_escape_limit():
    d = safety.dose_escape(6310.0, 37.0, 5.0, 2.5, q_safe_W=1e-9)
    assert d["t_eff_s"] == pytest.approx(5.0 + 0.6 * 37.0 / 2.5, rel=1e-6)


def test_stretched_faces_monotonic():
    f = stretched_faces(-40, 130, -11 * 0.35, 86 * 0.35, 0.35, 1.1, 2.5)
    d = np.diff(f)
    assert f[0] == -40 and f[-1] == 130 and np.all(d > 0)
    assert np.isclose(f, 0.0).any()
    assert d.max() <= 2.5 * 1.6


def test_poisson_and_projection(table):
    les = FlareLES(LESConfig.preset("teste"), table, 1e8)
    H = torch.randn(les.nx, les.ny, les.nz)
    rhs = les.divergence(les._grad_face(H, 0), les._grad_face(H, 1), les._grad_face(H, 2))
    assert ((les.poisson(rhs) - H).norm() / H.norm()).item() < 1e-4
    u, v, w = les._apply_bc(torch.randn_like(les.u), torch.randn_like(les.v), torch.randn_like(les.w))
    D = 0.1 * torch.randn(les.nx, les.ny, les.nz)
    u, v, w, _ = les.project(u, v, w, D, 0.05)
    assert (les.divergence(u, v, w) - D).abs().max().item() < 1e-3
    assert w[:, :, 0].abs().max().item() == 0.0


def test_short_run_stable(table):
    les = FlareLES(LESConfig.preset("teste"), table, 12.6 * PROPANE.LHV)
    while les.time < 1.0:
        les.step()
    T, e, mask, q = les.diagnostics(True)
    assert torch.isfinite(T).all() and mask.any() and q.max().item() > 0


def test_zone_extents_flags_truncation():
    from flarekit import safety
    x = np.arange(-30.0, 31.0, 3.0)
    X, Y = np.meshgrid(x, x, indexing="ij")
    q = 12.0 * np.exp(-(X ** 2 + Y ** 2) / 400.0)       # q ≥ 1,58 até r ≈ 28 m: cabe na grade
    z = {d["nivel_kW_m2"]: d for d in safety.zone_extents(q, x, x)}
    assert not z[1.58]["truncado"] and not z[9.46]["truncado"]
    q2 = 12.0 * np.exp(-(X ** 2 + Y ** 2) / 4000.0)     # zona maior que a grade
    z2 = {d["nivel_kW_m2"]: d for d in safety.zone_extents(q2, x, x)}
    assert z2[1.58]["truncado"]


def test_mixture_properties_and_conservation():
    from flarekit.props import (MW, SPECIES, Y_O2_AIR, burke_schumann, mixture, parse_composition,
                                pressure_at_altitude)
    # mistura de uma espécie reproduz o combustível puro
    p = mixture("propano", {"C3H8": 1.0})
    assert stoichiometry(p)["Z_st"] == pytest.approx(stoichiometry(PROPANE)["Z_st"], rel=1e-3)
    assert p.LHV == pytest.approx(PROPANE.LHV, rel=2e-3)
    # composição com inertes, CO e H2S: frações, átomos e conservação de massa em Burke–Schumann
    comp = parse_composition("H2: 20, CH4: 40, C2H6: 10, C3H6: 5, nC4H10: 4, CO: 3, CO2: 2, N2: 14, H2S: 2")
    f = mixture("gás de tocha", comp)
    assert sum(v for _, v in f.X) == pytest.approx(1.0)
    assert f.nS == pytest.approx(0.02) and f.nN == pytest.approx(0.28) and f.nO == pytest.approx(0.07)
    M = sum(v / 100 * SPECIES[k].M for k, v in comp.items())
    assert f.M == pytest.approx(M)
    Z = np.linspace(0, 1, 501)
    Y = burke_schumann(f, Z)
    tot = sum(Y[k] for k in ("F", "O2", "N2", "CO2", "H2O", "SO2"))
    assert np.allclose(tot, 1.0, atol=1e-9)
    # o O2 do ar acaba exatamente em Z_st
    Zs = stoichiometry(f)["Z_st"]
    Yst = burke_schumann(f, np.array([Zs]))
    assert Yst["O2"][0] == pytest.approx(0.0, abs=1e-9) and Yst["F"][0] == pytest.approx(0.0, abs=1e-9)
    assert Y_O2_AIR > 0
    assert pressure_at_altitude(600.0) == pytest.approx(94322.0, rel=2e-3)
    del MW


def test_species_lhv_against_cantera():
    ct = pytest.importorskip("cantera")
    from flarekit.props import SPECIES
    lib = {sp.name: sp for sp in ct.Species.list_from_file("nasa_gas.yaml")}
    names = sorted({d.nasa for d in SPECIES.values()} | {"SO2"})
    gas = ct.Solution(thermo="ideal-gas", species=[lib[n] for n in names])

    def h(n):
        gas.TPX = 298.15, ct.one_atm, {n: 1.0}
        return gas.enthalpy_mole / 1e3
    for k, d in SPECIES.items():
        C, H, O, N, S = d.atoms
        lhv = h(d.nasa) + (C + H / 4 + S - O / 2) * h("O2") - C * h("CO2") - H / 2 * h("H2O") - S * h("SO2")
        assert lhv == pytest.approx(d.LHV_mol, abs=1.5e3), k


def test_mixture_equilibrium_and_scenario():
    pytest.importorskip("cantera")
    from flarekit.props import mixture, pressure_at_altitude
    f = mixture("gás", {"H2": 25, "CH4": 45, "C2H6": 10, "C3H8": 10, "N2": 8, "H2S": 2})
    sr = state_relation(f, 311.0, 298.15, 0.0, n=401)
    assert "mistura" in sr.source and 2150 < sr.T_ad_st < 2350
    # a mesma chama a 600 m de altitude: ar menos denso, mesmo T_ad (aprox.)
    p = pressure_at_altitude(600.0)
    sc0 = se.Scenario(f, H=115.0, u_w=7.0)
    sc1 = se.Scenario(f, H=115.0, u_w=7.0, p_atm=p)
    assert sc1.rho_inf == pytest.approx(sc0.rho_inf * p / 101325.0)
    # Chamberlain usa W = Z_st exato para misturas
    assert sc0.cham.W == pytest.approx(stoichiometry(f)["Z_st"])


def test_radiant_fraction_factor_anchors():
    from flarekit.props import mixture
    f = se.radiant_fraction_factor
    assert f(METHANE) == pytest.approx(1.0, abs=1e-3)
    assert f(mixture("h2", {"H2": 1})) == pytest.approx(0.70, abs=0.02)       # API 521: H2 ≈ 0,7 × GN
    assert f(mixture("c4", {"nC4H10": 1})) == pytest.approx(1.25, abs=0.02)   # API 521: butano ≈ 1,25 × GN
    sc0 = se.Scenario(PROPANE, xrad_comp=False)
    sc1 = se.Scenario(PROPANE)
    assert sc1.cham.F_s == pytest.approx(sc0.cham.F_s * f(PROPANE))
    assert sc1.cham.L_b == pytest.approx(sc0.cham.L_b)                        # só a radiação muda


def test_lean_mixture_grid_and_input_validation():
    from flarekit.props import mixture, parse_composition
    f = mixture("gás pobre", {"CO": 50, "CO2": 10, "N2": 40})          # Z_st ≈ 0,46 > 1/3
    sr = state_relation(f, 311.0, 298.15, 0.0, n=401, use_cantera=False)
    assert np.all(np.diff(sr.Z) > 0) and sr.Z[-1] == pytest.approx(1.0)
    assert parse_composition("H2: 33, C2H4: 10,5; N2=3.5%") == {"H2": 33.0, "C2H4": 10.5, "N2": 3.5}
    with pytest.raises(ValueError):
        parse_composition("H2 20")
    with pytest.raises(ValueError):
        mixture("ar contaminado", {"H2": 10, "O2": 10, "N2": 80})
    with pytest.raises(ValueError):
        mixture("negativo", {"CH4": 100, "N2": -5})
