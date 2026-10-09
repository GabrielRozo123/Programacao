"""Renderização 3D (ray marching das SDFs) num quadro pequeno."""
import numpy as np

from pyrokit.geometry import ribbon_tank
from pyrokit.render3d import Cutaway


def test_cutaway_small_frame():
    tk = ribbon_tank()
    n = 16
    h = tk.T / n
    xc = (np.arange(n + 4) + 0.5) * h - (n + 4) * h / 2
    zc = (np.arange(n) + 0.5) * tk.H_L / n
    X, Y, Z = np.meshgrid(xc, xc, zc, indexing="ij")
    cw = Cutaway(tk, xc, xc, zc, device="cpu")
    cw.set_field("T", 400 + 10 * Z, vmin=400, vmax=408)
    im = cw.render("T", theta=0.3, size=(96, 54), ssaa=1.0, max_steps=80)
    assert im.shape == (54, 96, 3) and im.dtype == np.uint8
    assert im.std() > 10                      # há geometria e campo, não só o fundo
