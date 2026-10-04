"""Modelos semi-empíricos de chama e radiação (níveis N0–N1 do documento, seção 3).

Funções vetorizadas em NumPy. Servem de referência de validação para a LES e de
ferramenta de projeto (altura do flare, distâncias de segurança).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .props import G, M_AIR, P_ATM, R_U, Fuel, products_per_mol, radcal_ap, stoichiometry


# --------------------------------------------------------------------------- tip
def tip_conditions(fuel: Fuel, mdot: float, T_j: float, mach: float, p: float = P_ATM) -> dict:
    """Seção 3.1: gás ideal na pressão ambiente, Mach prescrito."""
    rho_j = p * fuel.M / (R_U * T_j)
    c_j = np.sqrt(fuel.gamma * R_U * T_j / fuel.M)
    u_j = mach * c_j
    d_j = np.sqrt(4 * mdot / (np.pi * rho_j * u_j))
    return {"rho_j": rho_j, "c_j": c_j, "u_j": u_j, "d_j": d_j, "Q": mdot * fuel.LHV}


def air_density(T_inf: float, p: float = P_ATM) -> float:
    return p * M_AIR / (R_U * T_inf)


# ---------------------------------------------------------------- comprimentos
def api_flame_length(Q: float) -> float:
    """Ajuste de Beychok à curva do API 521: L[m] = 0.00323·Q[W]^0.478."""
    return 0.0059 * 0.3048 * (3.412142 * Q) ** 0.478


def delichatsios_length(u_j, d_j, rho_j, rho_inf, Z_st, T_ad, T_inf) -> dict:
    """Seção 3.3: Froude da chama e L* (Delichatsios 1993; Schefer et al. 2006)."""
    Fr = u_j * Z_st**1.5 / ((rho_j / rho_inf) ** 0.25 * np.sqrt((T_ad - T_inf) / T_inf * G * d_j))
    Lstar = 13.5 * Fr**0.4 / (1 + 0.07 * Fr**2) ** 0.2 if Fr < 5 else 23.0
    dstar = d_j * np.sqrt(rho_j / rho_inf)
    return {"Fr_f": Fr, "L_star": Lstar, "d_star": dstar, "L": Lstar * dstar / Z_st}


def heskestad_length(Q: float, D: float) -> float:
    """Altura média de chamas de empuxo (Heskestad): L = 0.235 Q[kW]^(2/5) − 1.02 D."""
    return 0.235 * (Q / 1e3) ** 0.4 - 1.02 * D


def molina_xrad(fuel: Fuel, mdot, L, Z_st, T_ad, rho_f) -> dict:
    """Seção 3.4: X_rad = 9.45e-9 (τ_G a_p T_ad⁴)^0.47, τ_G em ms."""
    pr = products_per_mol(fuel)
    n_tot = sum(pr.values())
    x_CO2, x_H2O = pr["CO2"] / n_tot, pr["H2O"] / n_tot
    a_p = x_CO2 * radcal_ap("CO2", T_ad) + x_H2O * radcal_ap("H2O", T_ad)
    W_f = 0.17 * L
    tau = np.pi / 12 * rho_f * W_f**2 * L * Z_st / mdot * 1000.0
    return {"a_p": float(a_p), "tau_G_ms": float(tau), "X_rad": float(9.45e-9 * (tau * a_p * T_ad**4) ** 0.47)}


# --------------------------------------------------------------- Chamberlain
@dataclass
class Chamberlain:
    D_s: float
    W: float
    Y: float
    L_b0: float
    L_b: float
    R: float
    Ri_Lb0: float
    alpha: float      # graus
    K: float
    b: float
    R_l: float
    W1: float
    W2: float
    A: float
    F_s: float
    SEP: float        # W/m2
    Q: float


def radiant_fraction_factor(fuel: Fuel) -> float:
    """Correção aproximada de F_s pela composição (F_s de Chamberlain foi ajustado a gás natural).

    Usa a razão r = PCI molar (≈ PCI volumétrico) do combustível / PCI molar do CH4 e a tendência
    da tabela de fração radiante do API 521 (chamas de laboratório, maiores queimadores):
    H2 ≈ 0,70 × gás natural e butano ≈ 1,25 × gás natural → f = r^0,30 (r < 1) e r^0,19 (r ≥ 1).
    É uma interpolação de engenharia, não uma correlação publicada; f fica em [0,6; 1,35]."""
    r = fuel.LHV * fuel.M / 802.6e3
    f = r ** 0.30 if r < 1.0 else r ** 0.19
    return float(np.clip(f, 0.6, 1.35))


def chamberlain(fuel: Fuel, mdot: float, u_j: float, rho_j: float, rho_inf: float,
                u_w: float, theta_jv: float = 90.0, fs_factor: float = 1.0) -> Chamberlain:
    """Seção 3.7 (Chamberlain 1987). Ângulos em graus; u_w é o vento na altura do tip.
    fs_factor multiplica a fração radiante de superfície (1 = correlação original, gás natural)."""
    from scipy.optimize import brentq
    D_s = np.sqrt(4 * mdot / (np.pi * rho_inf * u_j))
    M = fuel.M
    # W = fração mássica de combustível na mistura estequiométrica com ar (definição de Chamberlain);
    # a correlação W(M) do artigo vale para alcanos; para misturas (H2, inertes...) usa-se Z_st exato
    W = stoichiometry(fuel)["Z_st"] if fuel.is_mixture else M / (15.816 * M + 0.0395)
    Ca = 0.024 * (G * D_s / u_j**2) ** (1 / 3)
    Cb, Cc = 0.2, (2.85 / W) ** (2 / 3)
    Y = brentq(lambda y: Ca * y ** (5 / 3) + Cb * y ** (2 / 3) - Cc, 1e-6, 1e6)
    L_b0 = Y * D_s
    L_b = L_b0 * (0.51 * np.exp(-0.4 * u_w) + 0.49) * (1 - 6.07e-3 * (theta_jv - 90))
    Ri = lambda ell: (G / (D_s**2 * u_j**2)) ** (1 / 3) * ell  # noqa: E731
    R = u_w / u_j
    base = (theta_jv - 90) * (1 - np.exp(-25.6 * R))
    if R <= 0.05:
        alpha = base + 8000 * R / Ri(L_b0)
    else:
        alpha = base + (134 + 1726 * np.sqrt(R - 0.026)) / Ri(L_b0)
    K = 0.185 * np.exp(-20 * R) + 0.015
    a_r = np.radians(alpha)
    b = L_b * np.sin(K * a_r) / np.sin(a_r) if abs(alpha) > 1e-9 else K * L_b
    R_l = np.sqrt(L_b**2 - b**2 * np.sin(a_r) ** 2) - b * np.cos(a_r)
    Cp = 1000 * np.exp(-100 * R) + 0.8
    W1 = D_s * (13.5 * np.exp(-6 * R) + 1.5) * (
        1 - (1 - np.sqrt(rho_inf / rho_j) / 15) * np.exp(-70 * Ri(D_s) * Cp * R))
    W2 = L_b * (0.18 * np.exp(-1.5 * R) + 0.31) * (1 - 0.47 * np.exp(-25 * R))
    A = np.pi / 4 * (W1**2 + W2**2) + np.pi / 2 * (W1 + W2) * np.sqrt(R_l**2 + ((W2 - W1) / 2) ** 2)
    F_s = (0.21 * np.exp(-0.00323 * u_j) + 0.11) * fs_factor
    Q = mdot * fuel.LHV
    return Chamberlain(D_s, W, Y, L_b0, L_b, R, Ri(L_b0), alpha, K, b, R_l, W1, W2, A, F_s, F_s * Q / A, Q)


def frustum_axis(ch: Chamberlain, tip: np.ndarray, wind_dir: np.ndarray = np.array([1.0, 0, 0])):
    """Centro da base, vetor do eixo (unitário) e base ortonormal do frustum de um tip vertical."""
    a_r = np.radians(ch.alpha)
    wd = wind_dir / np.linalg.norm(wind_dir)
    ax = np.sin(a_r) * wd + np.cos(a_r) * np.array([0, 0, 1.0])
    base = np.asarray(tip, float) + ch.b * np.array([0, 0, 1.0])
    e2 = np.cross(ax, wd); e2 = e2 / np.linalg.norm(e2) if np.linalg.norm(e2) > 1e-9 else np.array([0, 1.0, 0])
    e1 = np.cross(e2, ax)
    return base, ax, e1, e2


def frustum_panels(ch: Chamberlain, tip, n_ax: int = 48, n_th: int = 64, n_r: int = 12):
    """Painéis (centro, normal, área) da superfície lateral e dos dois discos."""
    base, ax, e1, e2 = frustum_axis(ch, tip)
    s = (np.arange(n_ax) + 0.5) / n_ax
    th = (np.arange(n_th) + 0.5) / n_th * 2 * np.pi
    S, TH = np.meshgrid(s, th, indexing="ij")
    r = (ch.W1 + (ch.W2 - ch.W1) * S) / 2
    slope = (ch.W2 - ch.W1) / 2 / ch.R_l
    radial = np.cos(TH)[..., None] * e1 + np.sin(TH)[..., None] * e2
    pts = base + (S[..., None] * ch.R_l) * ax + r[..., None] * radial
    nrm = radial - slope * ax
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    dA = r * (2 * np.pi / n_th) * (ch.R_l / n_ax) * np.sqrt(1 + slope**2)
    P, N, A = [pts.reshape(-1, 3)], [nrm.reshape(-1, 3)], [dA.ravel()]
    for frac, rad, sgn in ((0.0, ch.W1 / 2, -1.0), (1.0, ch.W2 / 2, 1.0)):
        rr = (np.arange(n_r) + 0.5) / n_r * rad
        RR, TT = np.meshgrid(rr, th, indexing="ij")
        c = base + frac * ch.R_l * ax
        p = c + RR[..., None] * (np.cos(TT)[..., None] * e1 + np.sin(TT)[..., None] * e2)
        P.append(p.reshape(-1, 3)); N.append(np.tile(sgn * ax, (p.size // 3, 1)))
        A.append((RR * (rad / n_r) * (2 * np.pi / n_th)).ravel())
    return np.vstack(P), np.vstack(N), np.concatenate(A)


def flame_box(ch: Chamberlain, H: float, grow: float = 1.2, pad: float = 3.0) -> dict:
    """Caixa que envolve a chama de Chamberlain (com folga) para a malha fina da LES:
    x a jusante, meia-largura em y e alturas relativas ao tip. A LES tende a inclinar e alongar
    um pouco a chama em relação a Chamberlain, por isso o fator `grow`."""
    tip = np.array([0.0, 0.0, H])
    base, ax, e1, _ = frustum_axis(ch, tip)
    top = base + ch.R_l * ax
    pts = np.array([base - ch.W1 / 2 * e1, base + ch.W1 / 2 * e1, top - ch.W2 / 2 * e1, top + ch.W2 / 2 * e1])
    rel = (pts - tip) * grow
    return {"x": (min(-pad, rel[:, 0].min() - pad), rel[:, 0].max() + pad),
            "y_half": max(6.0, 1.1 * ch.W2 / 2 + 2.0),
            "z": (-2.0, rel[:, 2].max() + pad)}


def flame_center_chamberlain(ch: Chamberlain, tip) -> np.ndarray:
    base, ax, *_ = frustum_axis(ch, tip)
    return base + 0.5 * ch.R_l * ax


# --------------------------------------------------------- transmissividade
def p_sat_water(T: float) -> float:
    """Pa, Antoine (TNO Yellow Book)."""
    return float(np.exp(23.18986 - 3816.42 / (T - 46.13)))


def tau_bagster(X, T_inf: float, RH: float):
    X = np.maximum(np.asarray(X, float), 1e-3)
    return np.minimum(1.0, 2.02 * (RH * p_sat_water(T_inf) * X) ** -0.09)


def tau_wayne(X, T_inf: float, RH: float, co2_ppm: float = 335.0):
    """Wayne (1991), como implementado no HyRAM+."""
    X = np.maximum(np.asarray(X, float), 1e-2)
    psat_mmHg = np.exp(20.386 - 5132.0 / T_inf)
    XH2O = RH * X * psat_mmHg * 2.88651e2 / T_inf
    XCO2 = X * 273.0 / T_inf * co2_ppm / 335.0
    lw, lc = np.log10(XH2O), np.log10(XCO2)
    return np.clip(1.006 - 0.01171 * lw - 0.02368 * lw**2 - 0.03188 * lc + 0.001164 * lc**2, 0.0, 1.0)


# --------------------------------------------------- fluxo nos receptores
def view_vector(receivers: np.ndarray, P: np.ndarray, N: np.ndarray, dA: np.ndarray,
                chunk: int = 512):
    """Seção 3.8: V = Σ cosβ_f dA/(π r²) ê (só a parte visível, cosβ_f > 0). F = n·V; F_max = |V|.
    Retorna V (n_rec, 3) e a distância média ponderada até a chama (para τ)."""
    receivers = np.atleast_2d(receivers)
    V = np.zeros_like(receivers, dtype=float)
    Xm = np.zeros(len(receivers))
    for i0 in range(0, len(receivers), chunk):
        r = receivers[i0:i0 + chunk]
        d = P[None, :, :] - r[:, None, :]
        dist = np.linalg.norm(d, axis=-1)
        e = d / dist[..., None]
        cos_f = np.maximum(-(e * N[None]).sum(-1), 0.0)
        w = cos_f * dA[None] / (np.pi * dist**2)
        V[i0:i0 + chunk] = (w[..., None] * e).sum(1)
        Xm[i0:i0 + chunk] = (w * dist).sum(1) / np.maximum(w.sum(1), 1e-30)
    return V, Xm


def q_chamberlain(receivers, ch: Chamberlain, tip, T_inf: float, RH: float,
                  normal: np.ndarray | None = None) -> np.ndarray:
    """Fluxo incidente [W/m2] pelo modelo de chama sólida; normal=None → pior orientação."""
    P, N, dA = frustum_panels(ch, tip)
    V, Xm = view_vector(np.asarray(receivers, float), P, N, dA)
    F = np.linalg.norm(V, axis=1) if normal is None else np.maximum(V @ np.asarray(normal, float), 0.0)
    return ch.SEP * F * tau_wayne(np.maximum(Xm - (ch.W1 + ch.W2) / 4, 1.0), T_inf, RH)


def q_point_source(receivers, center, F_rad: float, Q: float, T_inf: float, RH: float) -> np.ndarray:
    """Seção 3.5 (Hajek–Ludwig/API 521): q = τ F Q / (4π D²), pior orientação."""
    D = np.linalg.norm(np.atleast_2d(receivers) - np.asarray(center, float)[None], axis=1)
    return tau_wayne(D, T_inf, RH) * F_rad * Q / (4 * np.pi * D**2)


@dataclass
class Scenario:
    """Cenário do flare e todas as previsões semi-empíricas que servem de referência."""
    fuel: Fuel
    mdot: float = 12.6
    T_j: float = 311.0
    mach: float = 0.5
    H: float = 30.0
    u_w: float = 8.9
    T_inf: float = 298.15
    RH: float = 0.5
    p_atm: float = P_ATM     # pressão local (use props.pressure_at_altitude para sítios elevados)
    xrad_comp: bool = True   # corrige F_s de Chamberlain pela composição (radiant_fraction_factor)

    def __post_init__(self):
        self.tip = tip_conditions(self.fuel, self.mdot, self.T_j, self.mach, self.p_atm)
        self.rho_inf = air_density(self.T_inf, self.p_atm)
        self.fs_factor = radiant_fraction_factor(self.fuel) if self.xrad_comp else 1.0
        self.st = stoichiometry(self.fuel)
        self.Q = self.tip["Q"]
        self.L_api = api_flame_length(self.Q)
        self.cham = chamberlain(self.fuel, self.mdot, self.tip["u_j"], self.tip["rho_j"],
                                self.rho_inf, self.u_w, fs_factor=self.fs_factor)
        self.cham0 = chamberlain(self.fuel, self.mdot, self.tip["u_j"], self.tip["rho_j"],
                                 self.rho_inf, 0.0, fs_factor=self.fs_factor)
        self.tip_xyz = np.array([0.0, 0.0, self.H])

    def references(self, T_ad: float, rho_f: float | None = None) -> dict:
        """Correlações de referência. ρ_f padrão: produtos estequiométricos a T_ad (gás ideal)."""
        if rho_f is None:
            pr = products_per_mol(self.fuel)
            Mi = {"CO2": 44.009e-3, "H2O": 18.015e-3, "SO2": 64.058e-3, "N2": 28.014e-3}
            M_p = sum(pr[k] * Mi[k] for k in pr) / sum(pr.values())
            rho_f = self.p_atm * M_p / (R_U * T_ad)
        de = delichatsios_length(self.tip["u_j"], self.tip["d_j"], self.tip["rho_j"], self.rho_inf,
                                 self.st["Z_st"], T_ad, self.T_inf)
        mo = molina_xrad(self.fuel, self.mdot, de["L"], self.st["Z_st"], T_ad, rho_f)
        return {"delichatsios": de, "molina": mo, "L_api": self.L_api,
                "L_heskestad": heskestad_length(self.Q, self.tip["d_j"])}
