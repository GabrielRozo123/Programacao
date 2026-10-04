"""Testes do módulo de vento (sem rede: respostas simuladas das APIs)."""
import math

import numpy as np
import pytest

from flarekit import semiempirical as se
from flarekit import wind
from flarekit.props import PROPANE


def _fake_lib():
    """.lib (WAsP) mínimo: 2 rugosidades, 2 alturas, 4 setores."""
    lines = ["GWA ponto <coordinates>-47.15,-22.75,0</coordinates>", "2 2 4", "0.03 0.30", "10 50"]
    for r, scale in ((0, 1.0), (1, 0.8)):
        lines.append("70 10 10 10" if r == 0 else "60 20 10 10")
        lines.append(" ".join(str(5.0 * scale) for _ in range(4)))   # A a 10 m
        lines.append("2 2 2 2")                                       # k a 10 m
        lines.append(" ".join(str(6.5 * scale) for _ in range(4)))   # A a 50 m
        lines.append("2.1 2.1 2.1 2.1")                               # k a 50 m
    return "\n".join(lines)


def test_parse_gwa_lib_and_sample():
    g = wind.parse_gwa_lib(_fake_lib())
    assert g["n_sectors"] == 4 and np.allclose(g["z0"], [0.03, 0.3]) and np.allclose(g["heights"], [10, 50])
    assert g["freq"][0].sum() == pytest.approx(1.0) and g["lat"] == pytest.approx(-22.75)
    s = wind.gwa_series(g, -22.75, -47.15, z0_site=0.3, n=20000)
    # classe z0 = 0,3: setor N com 60% → direções em [−45°, 45°)
    north = (s.D2 < 45) | (s.D2 >= 315)
    assert north.mean() == pytest.approx(0.6, abs=0.02)
    # média Weibull A·Γ(1 + 1/k)
    assert s.U2.mean() == pytest.approx(0.8 * 6.5 * math.gamma(1 + 1 / 2.1), rel=0.03)
    assert np.all(s.U2 >= s.U1 - 1e-9)


def test_parse_nasa_power_uses_uv_direction():
    keys = ["2023010100", "2023010101", "2023010102"]
    par = {"WS10M": dict(zip(keys, [3.0, -999.0, 4.0])), "WS50M": dict(zip(keys, [4.0, 5.0, 5.0])),
           "WD10M": dict(zip(keys, [0.0, 0.0, 0.0])), "WD50M": dict(zip(keys, [0.0, 0.0, 0.0])),
           # vento DE leste: sopra para oeste → u < 0, v = 0 → direção 90°
           "U10M": dict(zip(keys, [-3.0, -3.0, -4.0])), "V10M": dict(zip(keys, [0.0, 0.0, 0.0])),
           "U50M": dict(zip(keys, [-4.0, -5.0, -5.0])), "V50M": dict(zip(keys, [0.0, 0.0, 0.0]))}
    s = wind.parse_nasa_power({"properties": {"parameter": par}, "header": {"fill_value": -999.0}}, 0, 0)
    assert len(s.U1) == 2                       # a hora com fill value sai
    assert np.allclose(s.D1, 90.0) and np.allclose(s.D2, 90.0)


def test_direction_from_uv_convention():
    # vento do Norte sopra para o Sul: v < 0
    assert wind.direction_from_uv(0.0, -5.0) == pytest.approx(0.0)
    assert wind.direction_from_uv(-5.0, 0.0) == pytest.approx(90.0)
    assert wind.direction_from_uv(0.0, 5.0) == pytest.approx(180.0)


def test_parse_open_meteo_nulls():
    js = {"hourly": {"time": ["a", "b"], "wind_speed_10m": [2.0, None], "wind_speed_100m": [4.0, 5.0],
                     "wind_direction_10m": [120.0, 130.0], "wind_direction_100m": [125.0, 135.0]}}
    s = wind.parse_open_meteo(js, 0, 0)
    assert len(s.U1) == 1 and s.z2 == 100.0


def test_log_profile_fit_recovers_z0():
    z0 = 0.25
    U2 = np.full(100, 6.0)
    U1 = U2 * math.log(10 / z0) / math.log(50 / z0)
    fit = wind.fit_log_profile(U1, U2, 10, 50)
    assert fit["z0"] == pytest.approx(z0, rel=1e-6)


def test_rotation_convention():
    sc = se.Scenario(PROPANE, u_w=8.0)
    xd, qd, _ = wind.downwind_footprint(sc, 8.0, 100.0, 67)
    g = wind.SiteGrid.square(80.0, 81)
    for theta, (sE, sN) in ((0, (0, -1)), (90, (-1, 0)), (180, (0, 1)), (270, (1, 0))):
        q = wind.rotate_to_site(xd, xd, qd, g, theta)
        i, j = np.unravel_index(np.argmax(q), q.shape)
        # a pegada fica a jusante: oposta à direção de onde o vento vem
        assert np.sign(round(g.E[i])) == sE or (sE == 0 and abs(g.E[i]) < 4)
        assert np.sign(round(g.N[j])) == sN or (sN == 0 and abs(g.N[j]) < 4)


def test_exceedance_bounds_and_sectors():
    ser = wind.synthetic_series(-22.75, -47.15, n=3000)
    cl = wind.WindClimate.from_series(ser, 30.0)
    assert cl.freq.sum() + cl.calm == pytest.approx(1.0, abs=1e-9)
    sc = se.Scenario(PROPANE, u_w=6.0)
    maps = wind.exceedance_maps(sc, cl, wind.SiteGrid.square(60.0, 31))
    for L in wind.API_LEVELS:
        P = maps["P"][L]
        assert P.min() >= 0 and P.max() <= 1 + 1e-9
        assert np.allclose(maps["P_sector"][L].sum(0) + (P - maps["P_sector"][L].sum(0)), P)
    # níveis mais altos nunca têm probabilidade maior que os mais baixos
    assert np.all(maps["P"][1.58] + 1e-12 >= maps["P"][4.73])
    U, th = cl.design_wind("dominante_p90")
    assert wind.sector_name(th) == "SE" and U > 0
