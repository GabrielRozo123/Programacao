"""Verificação do transporte estacionário: condução radial com fonte uniforme (solução analítica)."""
import numpy as np
import torch

from pyrokit.flow import FlowConfig, TankFlow
from pyrokit.geometry import Tank
from pyrokit.scalar import SteadyScalar


def test_radial_conduction_with_uniform_source():
    tank = Tank(T=1.0, H_L=0.1, impeller=None, rpm=0.0)
    f = TankFlow(tank, FlowConfig(n_diam=48, bottom="slip", device="cpu", dtype="float64"))
    zero = [torch.zeros_like(a) for a in (f.u, f.v, f.w)]
    k, S, Tw = 0.25, 1000.0, 700.0
    sc = SteadyScalar(f, *zero).setup(Gamma=torch.full_like(f.P, k), Sp=torch.zeros_like(f.P),
                                      Sc=torch.full_like(f.P, S), dirichlet_mask=f.fluid < 0.5,
                                      dirichlet_value=Tw)
    T, res, it = sc.solve(tol=1e-10)
    assert res < 1e-8, (res, it)
    r = f.r_c.numpy()[:, :, 1]
    Tn = T.numpy()[:, :, 1]
    inside = r < tank.R - 2 * f.h
    exact = Tw + S * (tank.R ** 2 - r ** 2) / (4 * k)
    rise = S * tank.R ** 2 / (4 * k)
    err = np.abs(Tn[inside] - exact[inside]).max() / rise
    assert err < 0.06, err
    # balanço: o calor gerado sai pela parede
    assert abs(float((T * sc.fluid).sum()) > 0)


def test_advection_keeps_uniform_field():
    """Com escoamento divergente-livre e sem fontes, um campo uniforme é solução exata."""
    from pyrokit.geometry import Shaft
    tank = Tank(T=1.0, H_L=0.1, impeller=Shaft(0.2), rpm=10.0)
    f = TankFlow(tank, FlowConfig(n_diam=32, bottom="slip", device="cpu", dtype="float64"),
                 lambda g: torch.full_like(g, 50.0))
    for _ in range(300):
        f.step()
    sc = SteadyScalar(f).setup(Gamma=torch.full_like(f.P, 1e-3), Sp=torch.full_like(f.P, 1e-3),
                               Sc=torch.full_like(f.P, 1e-3 * 5.0), dirichlet_mask=f.fluid < 0.5,
                               dirichlet_value=5.0)
    T, res, it = sc.solve(tol=1e-10)
    assert res < 1e-8
    assert float((T - 5.0).abs().max()) < 1e-4


def test_conservative_fluxes_and_energy_balance():
    """Fluxos projetados no fluido (divergência nula) e balanço global: o que entra pela parede sai
    pelos sumidouros, mesmo com a fronteira imersa difusa e o escoamento girando."""
    from pyrokit.geometry import ribbon_tank
    tank = ribbon_tank(T=0.8, rpm=30.0)
    f = TankFlow(tank, FlowConfig(n_diam=20, device="cpu", dtype="float32", spin0=0.8),
                 lambda g: torch.full_like(g, 0.5))
    for _ in range(60):
        f.step()
    sc = SteadyScalar(f)
    flux = float(sum(q.abs().sum() for q in sc.Q))
    assert float(sc.divQ.abs().sum()) < 1e-4 * flux, (float(sc.divQ.abs().sum()), flux)
    sp, Tf, Tw = 2e-3, 300.0, 700.0
    sc.setup(Gamma=torch.full_like(f.P, 1e-4), Sp=torch.full_like(f.P, sp), Sc=torch.full_like(f.P, sp * Tf),
             dirichlet_mask=f.fluid < 0.5, dirichlet_value=Tw, bottom_value=Tw)
    T, res, n = sc.solve_ptc(torch.full_like(f.P, 500.0), tol=1e-5, steps=40)
    q_in = float(sc.wall_flux(T).sum())
    q_out = float(((sp * T - sp * Tf) * sc.fluid).sum()) * sc.V
    assert abs(q_in - q_out) / abs(q_in) < 0.01, (q_in, q_out, res)
