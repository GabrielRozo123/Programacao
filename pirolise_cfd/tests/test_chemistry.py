"""Reator ideal 0-D, validação da química e geometria (NumPy × PyTorch)."""
import math

import numpy as np
import torch

from pyrokit import validation as V
from pyrokit.chemistry import FEEDS, solve_cstr
from pyrokit.geometry import ribbon_tank, standard_anchor_tank

VOL = math.pi * 0.4 ** 2 * 0.8
AREA = 2 * math.pi * 0.4 * 0.8 + math.pi * 0.4 ** 2


def test_cstr_mode_B_reference_point():
    r = solve_cstr(FEEDS["F3"], VOL, AREA, 300.0, T_wall=753.15)
    assert abs(r.T - 273.15 - 405.5) < 0.5
    assert abs(3600 * r.feed - 162.0) < 2.0
    # balanço de massa: alimentação = vapor + purga
    assert abs(r.feed - r.vapour - r.drain) / r.feed < 1e-6
    # a viscosidade do seio é a de uma cera fina (regime turbulento)
    assert 1e-3 < r.eta < 1e-2


def test_cstr_mode_A_consistent_with_mode_B():
    rb = solve_cstr(FEEDS["F3"], VOL, AREA, 300.0, T_wall=753.15)
    ra = solve_cstr(FEEDS["F3"], VOL, AREA, 300.0, feed_rate=rb.feed)
    assert abs(ra.T - rb.T) < 0.05
    assert abs(ra.T_wall - 753.15) < 0.5


def test_chemistry_checks_all_pass():
    assert all(c["ok"] for c in V.chemistry_checks())


def test_sdf_numpy_and_torch_agree():
    rng = np.random.default_rng(0)
    for tank in (ribbon_tank(), standard_anchor_tank()):
        P = (rng.random((5000, 3)) - [0.5, 0.5, 0.0]) * [tank.T, tank.T, tank.H_L]
        a = tank.impeller.sdf(P)
        b = tank.impeller.sdf(torch.tensor(P)).numpy()
        assert np.abs(a - b).max() < 1e-12
