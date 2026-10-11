"""Testes do tamborkit (rodam em CPU em poucos minutos: pytest -q)."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tamborkit import feed as fd  # noqa: E402
from tamborkit.geometry import Drum, fill_half_angle  # noqa: E402


def test_dtg_peaks_and_k_temperatures():
    for k, tgt in (("HDPE", 475), ("LDPE", 465), ("PP", 455), ("PS", 420)):
        assert abs(fd.dtg_peak(k, 10) - tgt) < 10
    assert abs(fd.t_k1e3("PVC") - 251) < 15
    assert abs(fd.t_k1e3("HDPE") - 429) < 5


def test_kinetics_conserve_mass():
    st = fd.KineticState(fd.Charge().masses(), 1)
    st.p["H2O"][:] = 1.0                    # água fora do teste (sai pelo platô, não por reação)
    m0 = float(st.total()[0])
    out = 0.0
    for _ in range(400):
        prod, _, _ = st.react(np.array([773.15]), 10.0)
        out += sum(float(v[0]) for v in prod.values())
    assert abs(float(st.total()[0]) + out - m0) / m0 < 1e-9


def test_fill_angle():
    for f in (0.05, 0.3, 0.62):
        e = fill_half_angle(f)
        assert abs((e - math.sin(e) * math.cos(e)) / math.pi - f) < 1e-9


def test_batch_short_balances():
    from tamborkit.batch import BatchDrum, BatchConfig
    dr = Drum(R=0.70, L=4.9, rpm=0.8, n_lifters=6, lifter_h=0.12, lifter_t=0.012)
    b = BatchDrum(dr, fd.Charge(mass=1000.0, fill=0.65), cfg=BatchConfig(t_max_h=0.6))
    s = b.run(verbose=False)
    assert abs(s["fecho_massa"]) < 1e-4
    assert abs(s["fecho_casco"]) < 1e-3
    assert abs(s["fecho_fornalha"]) < 1e-3
    assert b.log[-1]["T_carga"] > 30.0


def test_static_runs_and_lags():
    from tamborkit.batch import BatchDrum, BatchConfig
    dr = Drum(R=0.70, L=4.9, rpm=0.8, n_lifters=6, lifter_h=0.12, lifter_t=0.012)
    rot = BatchDrum(dr, fd.Charge(mass=1000.0, fill=0.65), cfg=BatchConfig(t_max_h=1.0))
    est = BatchDrum(dr, fd.Charge(mass=1000.0, fill=0.65), cfg=BatchConfig(mode="estatico", t_max_h=1.0))
    rot.run(verbose=False); est.run(verbose=False)
    assert np.isfinite(est.T).all()
    assert est.log[-1]["T_carga"] < rot.log[-1]["T_carga"]          # parado aquece mais devagar
    assert est.log[-1]["T_casco_max"] > rot.log[-1]["T_casco_max"]  # e a mancha quente é maior


def test_dem_neighbour_list_complete():
    from tamborkit.dem import DrumDEM, DEMConfig
    dr = Drum(R=0.5, L=1.0, rpm=6.0, n_lifters=4, lifter_h=0.08, lifter_t=0.012)
    dem = DrumDEM(dr, DEMConfig(fill=0.3, d_mean=0.05, slab=0.32, device="cpu"))
    dem.settle(0.3)
    dem.spin_up()
    dem.run(0.3)
    x, r = dem.x, dem.r
    D = x[:, None] - x[None]
    D[..., 0] -= dem.Lx * torch.round(D[..., 0] / dem.Lx)
    ov = r[:, None] + r[None] - D.norm(dim=-1)
    ov.fill_diagonal_(-1)
    ii, jj = torch.nonzero(ov > 0, as_tuple=True)
    nb = {(i, int(j)) for i in range(dem.N) for j in dem.nb[i].tolist() if j >= 0}
    assert all((int(i), int(j)) in nb for i, j in zip(ii, jj))
    st = dem.stats()
    assert st.max_overlap < 0.15 and np.isfinite(st.torque_Nm)


def test_les_mass_conservation():
    from tamborkit.furnace_les import FurnaceLES, FurnaceLESConfig, _diff
    les = FurnaceLES(FurnaceLESConfig.preset("teste", delta=0.2, Q_fire=300e3))
    for _ in range(25):
        rho0 = les.rho.clone()
        les.step()
    F = les._mass_fluxes(les.u, les.v, les.w, les.rho)
    divF = sum(_diff(F[a], a) for a in range(3)) / les.h
    res = ((les.rho - rho0) / les.dt + divF - les.Sm) * les.fluid
    assert abs(float(res.sum()) * les.h ** 3) < 1e-3 * float(les.Sm.sum()) * les.h ** 3 + 1e-6


def test_scene_renders():
    from tamborkit.scene import CrossSection, splat_spheres
    dr = Drum(R=0.7, L=4.9, n_lifters=6, lifter_h=0.12)
    cs = CrossSection(dr, dict(half_width=1.0, z_bot=-1.3, z_top=0.95, wall=0.12), size=(320, 320))
    img, _ = cs.furnace_layer(600.0)
    img = cs.drum_layer(img, np.full(36, 450.0), 0.0)
    xyz = np.array([[0.1, 0.0, -0.5], [0.2, 0.05, -0.5]], np.float32)
    out, a = cs.bed_particles(img, xyz, np.array([0.05, 0.05], np.float32), np.array([[200, 50, 50], [50, 200, 50]], float))
    assert a.sum() > 50 and np.isfinite(out).all()


def test_phase_dem_short():
    """DEM com mudança de fase numa batelada curtíssima: massa segue o modelo, plásticos entram na poça."""
    from tamborkit.batch import BatchDrum, BatchConfig
    from tamborkit.phasedem import PhaseDEM, PhaseConfig, melt_viscosity
    dr = Drum(R=0.70, L=4.9, rpm=0.8, n_lifters=6, lifter_h=0.12, lifter_t=0.012)
    b = BatchDrum(dr, fd.Charge(mass=1000.0, fill=0.65), cfg=BatchConfig(t_max_h=10))
    b.run(verbose=False)
    pd = PhaseDEM(dr, fd.Charge(mass=1000.0, fill=0.65), b.log,
                  PhaseConfig(slab=0.32, rpm=3.0, n_rev=0.08, pre_rev=0.01, frames=8, pre_frames=2,
                              contact_time=0.012, device="cpu"))
    n0 = int(pd.active.sum())
    pd.settle(0.2)
    for t_h in (0.0, 2.5, 3.5, 6.0):
        pd.update_state(t_h * 3600)
        pd.step(20)
    assert int(pd.active.sum()) < n0                    # fundidos saíram do DEM para a poça
    m_bed = b.log[-1]["carga_kg"] * pd.pc.slab / dr.L
    m_dem = float(pd.m[pd.active > 0].sum()) + pd.pool.get("mass", 0.0)
    assert abs(m_dem - m_bed) / m_bed < 0.1
    assert melt_viscosity(473.15, 0.0) > 100 and melt_viscosity(693.15, 0.3) < 0.1


def test_flame_projection_synthetic():
    """Bolha quente com fuligem: imagem finita nas duas vistas; na lateral o tambor tapa o que está atrás."""
    from tamborkit.flames import FlameRenderer, incandescence_rgb
    assert incandescence_rgb(1100.0).sum() > incandescence_rgb(900.0).sum()
    nx, ny, nz, h = 20, 12, 14, 0.15
    xc = (np.arange(nx) + 0.5) * h; yc = -0.9 + (np.arange(ny) + 0.5) * h; zc = -1.0 + (np.arange(nz) + 0.5) * h
    X, Y, Z = np.meshgrid(xc, yc, zc, indexing="ij")
    T = 600 + 1300 * np.exp(-((X - 1.5) ** 2 + (Y + 0.5) ** 2 + (Z + 0.8) ** 2) / 0.08)
    fv = 0.3 * np.exp(-((X - 1.5) ** 2 + (Y + 0.5) ** 2 + (Z + 0.8) ** 2) / 0.08)
    fr = dict(t=0.0, T=T.astype(np.float16), fv=fv.astype(np.float16), q=np.zeros_like(T, np.float16),
              u=np.zeros_like(T, np.float16), v=np.zeros_like(T, np.float16), w=np.zeros_like(T, np.float16),
              fluid=np.ones_like(T, np.uint8))
    meta = dict(xc=xc, yc=yc, zc=zc, h=h, R_out=0.4, L_drum=2.5, half_width=0.9, z_bot=-1.0, z_top=1.1, Lx=3.0,
                burners_x=(1.5,), burner_z=-0.8, Q_fire=3e5, T_shell=773.0, T_refr=1000.0, Z_st=0.06, fv_scale=0.2,
                fluid=np.ones_like(T, np.uint8))
    data = dict(frames=[fr, fr], meta=meta)
    for view, ext in (("corte", (-0.9, 0.9, -1.0, 1.1)), ("lateral", (0.0, 3.0, -1.0, 1.1))):
        rgb, a = FlameRenderer(data, view=view, detail=0.0).render_image(0, ext, (96, 80))
        assert np.isfinite(rgb).all() and rgb.max() > 0.2
