"""Testes com sinais sintéticos de resposta conhecida (não usam dados de campo).

Execute com:  python -m pytest -q tests
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pulseva as pv  # noqa: E402
from pulseva.io import Record  # noqa: E402
from pulseva.metrics import analyze_sensor, ellipse_from_amplitudes, relative_difference  # noqa: E402
from pulseva.tracking import track_rotation, order_phasors  # noqa: E402

FS = 800.0
N = 8000


def _theta(f0=12.2, dev=0.15, seed=0):
    """Fase de rotação com deriva lenta de velocidade (±dev Hz)."""
    t = np.arange(N) / FS
    f = f0 + dev * np.sin(2 * np.pi * 0.21 * t) + 0.5 * dev * np.sin(2 * np.pi * 0.47 * t + 1.0)
    return t, 2 * np.pi * np.cumsum(f) / FS, f


def _sensor(ax, ay, phase_deg, az=0.05, noise=0.02, seed=0, th=None, lag=0):
    rng = np.random.default_rng(seed)
    th = np.roll(th, lag)
    x = ax * np.cos(th)
    y = ay * np.cos(th - np.radians(phase_deg)) - 0.92
    z = az * np.cos(th + 0.3)
    return np.column_stack([x, y, z]) + noise * rng.standard_normal((N, 3))


def test_ellipse_matches_pulse_report_numbers():
    # L4 do relatório: X 1.99 g, Y 2.80 g, fase 34.9° -> Main 3.29 g, ângulo 56.4°
    el = ellipse_from_amplitudes(1.99, 2.80, 34.9)
    assert el["main"] == pytest.approx(3.29, abs=0.01)
    assert el["angle"] == pytest.approx(56.4, abs=0.15)
    # R1: X 2.37, Y 2.50, fase 10.6 -> 3.43 g, 46.5°
    el = ellipse_from_amplitudes(2.37, 2.50, 10.6)
    assert el["main"] == pytest.approx(3.43, abs=0.01)
    assert el["angle"] == pytest.approx(46.5, abs=0.15)


def test_stroke_formula():
    # 1.99 g a 11.90 Hz -> 7.0 mm (relatório Pulse)
    assert pv.stroke_mm(1.99, 11.90) == pytest.approx(6.98, abs=0.01)


def test_order_tracking_recovers_amplitude_under_speed_drift():
    t, th, f = _theta()
    acc = _sensor(2.5, 3.0, 30.0, th=th)
    s = analyze_sensor("R1", acc, FS)
    assert s.g[0] == pytest.approx(2.5, rel=0.005)
    assert s.g[1] == pytest.approx(3.0, rel=0.005)
    assert s.phase_yx == pytest.approx(30.0, abs=0.5)
    assert s.f_mean == pytest.approx(f[s.track.window].mean(), rel=0.002)
    # um ajuste de frequência fixa erraria bastante com essa deriva
    sl = s.track.window
    A = np.column_stack([np.cos(2 * np.pi * s.f_mean * t[sl]), np.sin(2 * np.pi * s.f_mean * t[sl])])
    c, *_ = np.linalg.lstsq(A, acc[sl, 0], rcond=None)
    assert np.hypot(*c) < 0.95 * 2.5


def test_left_side_mirroring():
    t, th, _ = _theta()
    acc = _sensor(2.5, 3.0, 30.0, th=th)
    acc_left = acc * np.array([-1, 1, -1])          # sensor espelhado no lado esquerdo
    sl = analyze_sensor("L1", acc_left, FS)
    sr = analyze_sensor("R1", acc, FS)
    assert sl.angle == pytest.approx(sr.angle, abs=0.1)
    assert sl.phase_yx == pytest.approx(sr.phase_yx, abs=0.1)


def test_rigid_body_pitch_and_unsynchronized_sensors():
    """Corpo rígido com pitch conhecido; sensores com atrasos de relógio diferentes."""
    t, th, _ = _theta(dev=0.05)
    ty, pitch = 2.6 * np.exp(-1j * np.radians(20)), 0.6 * np.exp(-1j * np.radians(80))
    sens = {}
    lags = {"L1": 0, "R1": 37, "L4": -11, "R4": 140, "L2": 5, "R2": -60, "L3": 90, "R3": 21}
    for i, (name, xpos) in enumerate([("L1", -1), ("R1", -1), ("L4", 1), ("R4", 1),
                                      ("L2", -0.33), ("R2", -0.33), ("L3", 0.33), ("R3", 0.33)]):
        y_ph = ty + pitch * xpos
        acc = _sensor(2.3, abs(y_ph), -np.degrees(np.angle(y_ph)), th=th, seed=i, lag=lags[name])
        if name[0] == "L":
            acc = acc * np.array([-1, 1, -1])
        sens[name] = acc
    rec = Record(path=Path("sintetico.xml"), meta={"Inclination": "18.0"}, fs=FS, sensors=sens)
    an = pv.analyze(rec)
    expected = relative_difference(2 * (ty - pitch), 2 * (ty + pitch))
    assert an.deviations["pitch"] == pytest.approx(expected, abs=0.3)
    assert an.deviations["roll"] < 0.5
    assert an.deviations["twist"] < 0.5
    assert an.center["g"][1] == pytest.approx(abs(ty), rel=0.01)


def test_defective_channel_is_flagged():
    t, th, _ = _theta()
    sens = {}
    for name in pv.SENSOR_ORDER:
        acc = _sensor(2.3, 2.6, 20, th=th, az=0.1, noise=0.05)
        if name[0] == "L":
            acc = acc * np.array([-1, 1, -1])
        sens[name] = acc
    sens["L1"][:, 2] = -14.8 + 0.01 * np.cos(th)        # canal travado, como no campo
    rec = Record(path=Path("sintetico.xml"), meta={}, fs=FS, sensors=sens)
    an = pv.analyze(rec)
    assert "L1" in an.excluded
    assert any(f.level == "crítico" and f.scope == "L1-Z" for f in an.findings)
