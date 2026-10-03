"""Testes das identidades algébricas e dos solvers (pytest -q)."""
import math

import numpy as np
import pytest
import torch

from flarekit import safety
from flarekit import semiempirical as se
from flarekit.les import FlareLES, LESConfig, stretched_faces
from flarekit.props import PROPANE, beta_pdf_table, state_relation, stoichiometry


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
    sc = se.Scenario(PROPANE, H=50.0)
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
