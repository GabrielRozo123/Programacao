"""Fornalha em volta do tambor: modelo zonal de Hottel (gás bem misturado + refratário + casco).

A fornalha é a caixa de alvenaria/fibra cerâmica que envolve o tambor. Os queimadores (combustível
auxiliar no início, depois o gás não condensável da própria pirólise) queimam na câmara de combustão sob o
tambor; o gás quente sobe pelos dois corredores laterais (folga entre o casco e o refratário), junta-se no
topo e sai pela chaminé no fundo do tambor (x = L).

Em cada fatia axial há quatro zonas de gás — câmara (FB), lateral direita (SR), lateral esquerda (SL) e
topo (TP) — cada uma com um nó de refratário. Por zona, regime quase estacionário (o gás responde em
segundos; o casco e a carga, em minutos e horas):

  gás:        ṁ c_p (T_g − T_entra) = Q_liberado − Q_gás→casco − Q_gás→refratário
  refratário: Q_gás→refratário = Q_refratário→casco + U A_r (T_r − T_amb)
  casco (setor j): q_j = σ ε_g (1+ε_s)/2 (T_g⁴ − T_j⁴) + σ ε_rs (1 − ε_g)(T_r⁴ − T_j⁴) + h_c (T_g − T_j)

ε_g do gás de combustão pela soma ponderada de gases cinzas (WSGG, Smith, Shen & Friedman 1982, razão
p_H2O/p_CO2 = 1) com o comprimento médio de feixe L_m = 3,6 V/A; ε_rs = 1/(1/ε_r + 1/ε_s − 1).
A convecção é pequena (Re ~2400 no corredor, 2–6 W/m²K): o casco é aquecido sobretudo por radiação.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

SIGMA = 5.670374419e-8
CP_FG = 1250.0          # c_p médio dos gases de combustão, 300–1500 K [J/(kg K)]

# WSGG de Smith et al. (1982), p_w/p_c = 1: κ_i [1/(atm m)] e b_ij (a_i = Σ_j b_ij T^(j−1))
_WSGG_K = np.array([0.4303, 7.055, 178.1])
_WSGG_B = np.array([[5.150e-1, -2.303e-4, 0.9779e-7, -1.494e-11],
                    [0.7749e-1, 3.399e-4, -2.297e-7, 3.770e-11],
                    [1.907e-1, -1.824e-4, 0.5608e-7, -0.5122e-11]])

FUELS = {
    # PCI [J/kg], ar estequiométrico [kg/kg], (mols CO2 + H2O, mols O2 estequiométrico) por mol de combustível
    "GLP": dict(LHV=46.35e6, AFR=15.6, nCH=7.0, nO2=5.0, name="GLP (propano)"),
    "diesel": dict(LHV=42.8e6, AFR=14.5, nCH=25.0, nO2=18.5, name="óleo diesel"),
    "G_HC": dict(LHV=46.3e6, AFR=15.43, nCH=3.0, nO2=2.2, name="gás de pirólise (hidrocarbonetos)"),
    "G_OX": dict(LHV=8.0e6, AFR=2.2, nCH=1.0, nO2=0.35, name="gás de pirólise (CO/CO₂)"),
}


def wsgg_emissivity(T, pL):
    """Emissividade total do gás (H2O + CO2), T [K], pL = (p_w + p_c)·L [atm m]."""
    T = np.clip(np.asarray(T, float), 600.0, 2400.0)
    Tp = np.stack([np.ones_like(T), T, T ** 2, T ** 3], -1)
    a = Tp @ _WSGG_B.T                                 # [..., 3]
    return (a * (1 - np.exp(-_WSGG_K * np.asarray(pL, float)[..., None]))).sum(-1)


def flue_pwc(lam: float, fuel: str = "GLP") -> float:
    """Pressão parcial p_H2O + p_CO2 [atm] nos gases de combustão com excesso de ar λ."""
    f = FUELS[fuel]
    n_prod = f["nCH"] + (lam - 1) * f["nO2"] + 3.76 * lam * f["nO2"]
    return f["nCH"] / n_prod


@dataclass
class Furnace:
    gap: float = 0.20               # folga casco–refratário nos corredores [m]
    fb_height: float = 0.55         # altura da câmara de combustão abaixo do casco [m]
    fb_width: float = 2.0           # largura da câmara [m]
    burners_x: tuple = (1.2, 3.7)   # posições axiais dos queimadores [m]
    flame_sigma: float = 0.7        # espalhamento axial da liberação de calor de cada chama [m]
    axial_mix: float = 0.5          # fração da liberação/vazão distribuída uniformemente (mistura na câmara)
    Q_max: float = 465e3            # capacidade dos queimadores [W] (2 × 200 000 kcal/h, BLJ-3, não verificado)
    Q_min: float = 15e3             # chama piloto [W]
    lam: float = 1.3                # excesso de ar
    aux_fuel: str = "GLP"
    T_air: float = 298.15
    T_amb: float = 298.15
    eps_r: float = 0.85             # refratário / fibra cerâmica
    eps_s: float = 0.85             # casco oxidado (lado de fora)
    ins_thick: float = 0.15         # isolamento [m]
    k_ins: float = 0.12             # fibra cerâmica a ~600 °C [W/(m K)]
    h_out: float = 10.0             # convecção + radiação na face externa [W/(m² K)]
    h_conv: float = 5.0             # convecção gás → casco/refratário [W/(m² K)]
    # setores (ângulo φ = atan2(z, y) no referencial do laboratório) de cada zona, em graus
    zones: tuple = (("FB", -150.0, -30.0), ("SR", -30.0, 75.0), ("TP", 75.0, 105.0), ("SL", 105.0, 210.0))

    @property
    def U_ins(self) -> float:
        return 1.0 / (self.ins_thick / self.k_ins + 1.0 / self.h_out)

    def zone_of(self, phi_deg: np.ndarray) -> np.ndarray:
        """Índice da zona (0 FB, 1 SR, 2 TP, 3 SL) de cada ângulo de laboratório."""
        p = (np.asarray(phi_deg, float) + 150.0) % 360.0 - 150.0
        out = np.zeros(p.shape, int)
        for i, (_, a, b) in enumerate(self.zones):
            out[(p >= a) & (p < b)] = i
        return out

    def release_weights(self, xc: np.ndarray) -> np.ndarray:
        """Distribuição axial da liberação de calor (e da vazão de gases) entre as fatias."""
        g = sum(np.exp(-0.5 * ((xc - xb) / self.flame_sigma) ** 2) for xb in self.burners_x)
        g = g / g.sum()
        u = np.full_like(xc, 1.0 / len(xc))
        return self.axial_mix * u + (1 - self.axial_mix) * g


class FurnaceZones:
    """Resolve as zonas de gás e refratário de todas as fatias, dado o casco e a queima."""

    def __init__(self, fur: Furnace, R_out: float, L: float, xc: np.ndarray, phi_deg: np.ndarray):
        self.f = fur
        self.R, self.L, self.xc = R_out, L, xc
        self.nx, self.nphi = len(xc), len(phi_deg)
        dx = L / self.nx
        self.dx = dx
        self.zone = fur.zone_of(phi_deg)                            # zona de cada setor (lab)
        self.A_sec = 2 * math.pi * R_out / self.nphi * dx           # área de um setor numa fatia [m²]
        self.w = fur.release_weights(xc)
        # geometria de cada zona por fatia: área de refratário e comprimento médio de feixe
        arcs = np.array([(b - a) for _, a, b in fur.zones]) * math.pi / 180.0
        A_shell_z = arcs * R_out * dx
        g, H, W = fur.gap, fur.fb_height, fur.fb_width
        A_ref, V = np.zeros(4), np.zeros(4)
        # câmara: piso + paredes laterais da caixa abaixo do casco
        A_ref[0] = (W + 2 * (H + 0.3 * R_out)) * dx
        V[0] = (W * (H + 0.5 * R_out) - 0.5 * arcs[0] * R_out ** 2 * 0.6) * dx
        for i in (1, 2, 3):            # corredores e topo: anel de folga g
            A_ref[i] = arcs[i] * (R_out + g) * dx
            V[i] = 0.5 * arcs[i] * ((R_out + g) ** 2 - R_out ** 2) * dx
        self.A_ref, self.A_shell_z = A_ref, A_shell_z
        self.Lm = 3.6 * V / (A_ref + A_shell_z)
        self.eps_rs = 1.0 / (1.0 / fur.eps_r + 1.0 / fur.eps_s - 1.0)
        self.Tg = np.full((self.nx, 4), 900.0)
        self.Tr = np.full((self.nx, 4), 800.0)

    def _zone_solve(self, Tin, mdot, Qrel, Ts_list, Ash_list, Ar, Lm, pwc, Tg0, Tr0, iters=30):
        """Newton 2×2 (T_g, T_r) vetorizado; Ts_list [nx, ns], Ash_list [nx, ns] (áreas por setor)."""
        f = self.f
        Tg, Tr = Tg0.copy(), Tr0.copy()
        es = (1 + f.eps_s) / 2
        er = (1 + f.eps_r) / 2
        U = f.U_ins
        for _ in range(iters):
            eg = wsgg_emissivity(Tg, pwc * Lm)
            Ts4 = Ts_list ** 4
            # fluxos para o casco
            qg = SIGMA * eg[:, None] * es * (Tg[:, None] ** 4 - Ts4) + f.h_conv * (Tg[:, None] - Ts_list)
            qr = SIGMA * self.eps_rs * (1 - eg[:, None]) * (Tr[:, None] ** 4 - Ts4)
            Qgs = (qg * Ash_list).sum(1)
            Qrs = (qr * Ash_list).sum(1)
            Qgr = Ar * (SIGMA * eg * er * (Tg ** 4 - Tr ** 4) + f.h_conv * (Tg - Tr))
            F1 = mdot * CP_FG * (Tg - Tin) - Qrel + Qgs + Qgr
            F2 = Qgr - Qrs - Ar * U * (Tr - f.T_amb)
            # jacobiano (ε_g congelado na iteração)
            dqg = (SIGMA * eg[:, None] * es * 4 * Tg[:, None] ** 3 + f.h_conv) * Ash_list
            dQgr_g = Ar * (SIGMA * eg * er * 4 * Tg ** 3 + f.h_conv)
            dQgr_r = -Ar * (SIGMA * eg * er * 4 * Tr ** 3 + f.h_conv)
            dQrs_r = (SIGMA * self.eps_rs * (1 - eg[:, None]) * 4 * Tr[:, None] ** 3 * Ash_list).sum(1)
            J11 = mdot * CP_FG + dqg.sum(1) + dQgr_g
            J12 = dQgr_r
            J21 = dQgr_g
            J22 = dQgr_r - dQrs_r - Ar * U
            det = J11 * J22 - J12 * J21
            dTg = (-F1 * J22 + F2 * J12) / det
            dTr = (-F2 * J11 + F1 * J21) / det
            Tg = np.clip(Tg + np.clip(dTg, -300, 300), 250.0, 2600.0)
            Tr = np.clip(Tr + np.clip(dTr, -300, 300), 250.0, 2600.0)
            if np.max(np.abs(dTg)) + np.max(np.abs(dTr)) < 0.01:
                break
        eg = wsgg_emissivity(Tg, pwc * Lm)
        q = (SIGMA * eg[:, None] * es * (Tg[:, None] ** 4 - Ts_list ** 4) + f.h_conv * (Tg[:, None] - Ts_list)
             + SIGMA * self.eps_rs * (1 - eg[:, None]) * (Tr[:, None] ** 4 - Ts_list ** 4))
        loss = Ar * U * (Tr - f.T_amb)
        return Tg, Tr, q, loss, eg

    def solve(self, Ts_lab: np.ndarray, Q_fire: float, m_fuel_flue: float, pwc: float, phi_deg=None):
        """Ts_lab [nx, nphi] temperatura do casco em cada setor de laboratório.

        Q_fire: liberação total [W]; m_fuel_flue: vazão total de gases de combustão [kg/s].
        phi_deg: ângulo de laboratório atual de cada setor (o casco gira; padrão = ângulos da construção).
        Devolve q [nx, nphi] (fluxo da fornalha para o casco, W/m²) e um dicionário de diagnóstico."""
        f = self.f
        zone = self.zone if phi_deg is None else f.zone_of(phi_deg)
        q = np.zeros_like(Ts_lab)
        mdot = np.maximum(m_fuel_flue, 1e-4) * self.w
        Qrel = Q_fire * self.w
        loss = np.zeros((self.nx, 4))
        eg_all = np.zeros((self.nx, 4))
        order = [0, 1, 3, 2]                    # câmara → laterais → topo
        T_side_out = np.zeros((self.nx, 2))
        for zi in order:
            sel = zone == zi
            Ts = Ts_lab[:, sel]
            Ash = np.full(Ts.shape, self.A_sec)
            if zi == 0:
                Tin, md, Qr = np.full(self.nx, f.T_air), mdot, Qrel
            elif zi in (1, 3):
                Tin, md, Qr = self.Tg[:, 0], 0.5 * mdot, np.zeros(self.nx)
            else:
                # topo: recebe os dois corredores da fatia + o fluxo axial vindo das fatias anteriores
                Tg_top = np.zeros(self.nx); Tr_top = np.zeros(self.nx); q_top = np.zeros_like(Ts)
                ls, eg_t = np.zeros(self.nx), np.zeros(self.nx)
                m_up, T_up = 0.0, f.T_air
                for k in range(self.nx):
                    m_side = 0.5 * mdot[k]
                    m_in = m_up + 2 * m_side
                    Tin_k = (m_up * T_up + m_side * (self.Tg[k, 1] + self.Tg[k, 3])) / max(m_in, 1e-9)
                    tg, tr, qq, lo, eg = self._zone_solve(np.array([Tin_k]), np.array([m_in]), np.zeros(1),
                                                         Ts[k:k + 1], Ash[k:k + 1], self.A_ref[zi],
                                                         self.Lm[zi], pwc, self.Tg[k:k + 1, zi], self.Tr[k:k + 1, zi])
                    Tg_top[k], Tr_top[k], q_top[k], ls[k], eg_t[k] = tg[0], tr[0], qq[0], lo[0], eg[0]
                    m_up, T_up = m_in, tg[0]
                self.Tg[:, zi], self.Tr[:, zi] = Tg_top, Tr_top
                q[:, sel] = q_top
                loss[:, zi], eg_all[:, zi] = ls, eg_t
                self.T_flue = T_up
                continue
            tg, tr, qq, lo, eg = self._zone_solve(Tin, md, Qr, Ts, Ash, self.A_ref[zi], self.Lm[zi], pwc,
                                                 self.Tg[:, zi], self.Tr[:, zi])
            self.Tg[:, zi], self.Tr[:, zi] = tg, tr
            q[:, sel] = qq
            loss[:, zi], eg_all[:, zi] = lo, eg
        Q_shell = float((q * self.A_sec).sum())
        Q_flue = float(m_fuel_flue * CP_FG * (self.T_flue - f.T_air))
        diag = dict(Q_shell=Q_shell, Q_loss=float(loss.sum()), Q_flue=Q_flue, T_flue=float(self.T_flue),
                    Tg=self.Tg.copy(), Tr=self.Tr.copy(), eps_g=eg_all,
                    closure=(Q_fire - Q_shell - float(loss.sum()) - Q_flue) / max(Q_fire, 1.0))
        return q, diag


def fuel_mix(Q_fire: float, ncg: dict, aux: str, lam: float):
    """Divide a demanda de queima entre o gás de pirólise disponível e o auxiliar.

    ncg: {"G_HC": kg/s, "G_OX": kg/s} disponível. Devolve (uso {combustível: kg/s}, ṁ dos gases de combustão,
    p_wc, potência do gás de pirólise usada, potência que sobra para o flare)."""
    Q_ncg_avail = sum(ncg.get(k, 0.0) * FUELS[k]["LHV"] for k in ("G_HC", "G_OX"))
    Q_from_ncg = min(Q_ncg_avail, Q_fire)
    frac = Q_from_ncg / Q_ncg_avail if Q_ncg_avail > 0 else 0.0
    use = {k: ncg.get(k, 0.0) * frac for k in ("G_HC", "G_OX")}
    use[aux] = max(Q_fire - Q_from_ncg, 0.0) / FUELS[aux]["LHV"]
    m_fg = sum(m * (1 + lam * FUELS[k]["AFR"]) for k, m in use.items())
    # p_wc ponderada pela vazão de gases de cada combustível
    w = {k: m * (1 + lam * FUELS[k]["AFR"]) for k, m in use.items()}
    tot = sum(w.values())
    pwc = sum(w[k] * flue_pwc(lam, k) for k in w) / tot if tot > 0 else flue_pwc(lam, aux)
    return use, m_fg, pwc, Q_from_ncg, Q_ncg_avail - Q_from_ncg
