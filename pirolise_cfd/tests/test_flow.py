"""Verificação do escoamento: Couette circular entre o eixo (gira com o agitador) e o vaso (parado)."""
import math

import numpy as np
import torch

from pyrokit.flow import FlowConfig, TankFlow
from pyrokit.geometry import Shaft, Tank


def _run(mu_fn, n_steps, n_diam=40, rpm=10.0, r1=0.2):
    tank = Tank(T=1.0, H_L=0.1, impeller=Shaft(r_shaft=r1), rpm=rpm)
    f = TankFlow(tank, FlowConfig(n_diam=n_diam, rho=1000.0, bottom="slip", device="cpu", dtype="float64"), mu_fn)
    for _ in range(n_steps):
        f.step()
        f.record()
    return tank, f


def _theta_profile(tank, f):
    ul, vl, _ = f.lab_velocity_centers()
    X, Y = f.P_c[..., 0], f.P_c[..., 1]
    r = np.hypot(X, Y)
    ut = ((-Y * ul.numpy() + X * vl.numpy()) / np.maximum(r, 1e-9))[:, :, f.nz // 2]
    return r[:, :, f.nz // 2], ut


def test_newtonian_couette_profile_and_torque():
    mu = 50.0
    tank, f = _run(lambda g: torch.full_like(g, mu), 2500)
    R, r1, w = tank.R, tank.impeller.r_shaft, tank.omega
    B = w * r1 ** 2 * R ** 2 / (R ** 2 - r1 ** 2)
    A = -w * r1 ** 2 / (R ** 2 - r1 ** 2)
    r, ut = _theta_profile(tank, f)
    band = (r > r1 + 2 * f.h) & (r < R - 2 * f.h)
    exact = A * r[band] + B / r[band]
    err = np.abs(ut[band] - exact).max() / (w * r1)
    assert err < 0.06, err
    T_exact = 4 * math.pi * mu * B * tank.H_L
    T_sim = np.mean(f.history["torque"][-200:])
    assert abs(T_sim / T_exact - 1) < 0.08, (T_sim, T_exact)
    # equilíbrio de torques: o que o eixo entrega, a parede retira
    T_wall = np.mean(f.history["torque_wall"][-200:])
    assert abs(T_sim + T_wall) / T_sim < 0.06


def test_power_law_couette_torque():
    K, n = 40.0, 0.6
    tank, f = _run(lambda g: K * (g + 1e-3) ** (n - 1), 4500)   # converge com a malha: +13/+5,5/+3,2 % (32/48/64)
    R, r1, w = tank.R, tank.impeller.r_shaft, tank.omega
    T_exact = 2 * math.pi * tank.H_L * K * (2 * w / (n * (r1 ** (-2 / n) - R ** (-2 / n)))) ** n
    T_sim = np.mean(f.history["torque"][-200:])
    assert abs(T_sim / T_exact - 1) < 0.12, (T_sim, T_exact)


def test_wall_function_vessel_brakes_spinning_liquid():
    """Lei de parede no vaso (RANS): sem agitador, o líquido girando perde momento angular só pela parede,
    e a área em que a tensão é aplicada é a do cilindro real."""
    import math
    from pyrokit.turbulence import SST
    tank = Tank(T=0.8, H_L=0.4, impeller=None, rpm=30.0)
    f = TankFlow(tank, FlowConfig(n_diam=20, rho=640.0, device="cpu", spin0=0.9, vessel_ibm="wallfn"),
                 lambda g: torch.full_like(g, 3e-3))
    f.turb = SST(f)
    area = float(f.delta_w.sum()) * f.vol
    assert abs(area / (2 * math.pi * tank.R * tank.H_L) - 1) < 1e-6
    L0 = f.angular_momentum()
    for _ in range(80):
        f.step()
    L1 = f.angular_momentum()
    assert torch.isfinite(f.u).all()
    assert f.torque_wall < 0 and L1 < L0           # a parede (parada no laboratório) freia o líquido
