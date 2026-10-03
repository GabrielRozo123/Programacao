"""Critérios de segurança (seção 5 do documento): zonas do API 521, dose, probits, fuga e
temperatura de superfícies expostas."""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import erf

from .props import SIGMA

API_521 = [
    (9.46, "máximo com acesso de pessoal (poucos segundos, só fuga)"),
    (6.31, "ações de emergência de até ~30 s, sem abrigo"),
    (4.73, "ações de emergência de 2–3 min, sem abrigo"),
    (1.58, "exposição contínua com roupa adequada"),
]

PROBITS = {
    "queimadura 1º grau (Tsao & Perry)": (-39.83, 3.0186),
    "queimadura 2º grau (Tsao & Perry)": (-43.14, 3.0186),
    "fatalidade (TNO Green Book)": (-36.38, 2.56),
    "fatalidade (Eisenberg)": (-38.48, 2.56),
}


def probability(Y):
    return 0.5 * (1.0 + erf((np.asarray(Y) - 5.0) / math.sqrt(2.0)))


def dose_escape(q0_W: float, r0: float, t_react: float, u_esc: float, q_safe_W: float = 1580.0) -> dict:
    """Dose com reação e fuga radial (dedução da seção 5.2):
    D = q0^(4/3) {t_r + (3/5)(r0/u)[1 − (q_s/q0)^(5/6)]}."""
    frac = 0.0 if q0_W <= q_safe_W else 1.0 - (q_safe_W / q0_W) ** (5.0 / 6.0)
    t_eff = t_react + 0.6 * r0 / u_esc * frac
    D = t_eff * q0_W ** (4.0 / 3.0)
    out = {"t_eff_s": t_eff, "dose_TDU": D / 1e4}
    for name, (a, b) in PROBITS.items():
        out[name] = float(probability(a + b * math.log(D)))
    return out


def steel_temperature(q_inc_W: float, T_inf: float = 298.15, alpha: float = 0.9, eps: float = 0.9,
                      h: float = 15.0) -> float:
    """Placa fina isolada atrás, regime permanente: α q = h(T−T∞) + εσ(T⁴−T∞⁴). Retorna °C."""
    f = lambda T: alpha * q_inc_W - h * (T - T_inf) - eps * SIGMA * (T ** 4 - T_inf ** 4)  # noqa: E731
    return brentq(f, T_inf, 3000.0) - 273.15


def zone_extents(q_kW: np.ndarray, rec_x: np.ndarray, rec_y: np.ndarray, stack=(0.0, 0.0)) -> list[dict]:
    """Para cada nível do API 521: área no solo e distância máxima a partir do pé do flare."""
    dx = float(rec_x[1] - rec_x[0]) if len(rec_x) > 1 else 1.0
    dy = float(rec_y[1] - rec_y[0]) if len(rec_y) > 1 else 1.0
    RX, RY = np.meshgrid(rec_x, rec_y, indexing="ij")
    R = np.hypot(RX - stack[0], RY - stack[1])
    out = []
    for lev, desc in API_521:
        m = q_kW >= lev
        out.append({"nivel_kW_m2": lev, "descricao": desc, "area_m2": float(m.sum() * dx * dy),
                    "raio_max_m": float(R[m].max()) if m.any() else 0.0,
                    "x_min_m": float(RX[m].min()) if m.any() else float("nan"),
                    "x_max_m": float(RX[m].max()) if m.any() else float("nan")})
    return out
