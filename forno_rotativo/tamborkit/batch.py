"""Batelada completa do tambor rotativo: fornalha → casco girando → carga → vapores → condensador → queimador.

Escalas de tempo (pesquisa R5): contato ~ms ≪ chama ~s ≪ volta do tambor 75 s ~ residência do vapor 1–4 min
< inércia do casco 3–10 min ≪ batelada 6–8 h. O modelo avança no relógio lento (Δt ~2 s) e trata como
quase estacionários a fornalha (zonas de Hottel) e o espaço livre (escoamento pistonado dos vapores).

Carga (dois modos, mesma química e mesma fornalha):
  * "rotativo": a cada volta a carga renova o contato com a parede; em cada fatia axial o leito é bem
    misturado na seção (a mistura leva poucas voltas, ≪ batelada — verificado pelo DEM) e a parede coberta
    troca calor pelo modelo de penetração (Tscheng & Watkinson 1979; Schlünder & Mollekopf 1984):
        1/h_wb = 1/h_contato + 1/h_pen,   h_pen = 2 √(k ρ c / (π t_c)),   t_c = 2ε/Ω;
    as aletas entram como aletas térmicas (eficiência tanh(mL)/mL) e como cortina que intercepta a radiação.
  * "estatico": tambor parado; a carga é uma pilha que só conduz calor (camadas lagrangianas da parede até a
    superfície, área variando do arco molhado à corda), com a mancha quente do casco fixa sobre a chama.

Parede exposta ↔ superfície da carga: radiosidade entre os setores do casco (cordas inscritas) e a corda do
leito, fatores de forma pelas cordas cruzadas de Hottel. Espaço livre: vapores em escoamento pistonado até a
saída (x = L), convecção com parede e carga, craqueamento secundário (cera → óleo → gás + aromáticos + coque;
alcatrão → gás/coque). Condensador: óleo (O, W, A, OX, TAR), fase aquosa (H2O, HCl) e gás não condensável,
que volta ao queimador; o excedente vai para o flare.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from . import feed as fd
from .furnace import Furnace, FurnaceZones, fuel_mix, FUELS, SIGMA
from .geometry import Drum, fill_half_angle

T0 = 298.15
# espaço livre: craqueamento secundário (pesquisa, brief §3.7; Shafizadeh–Chin para o alcatrão)
K_O = (1.0e16, 300e3)              # óleo → gás/aromáticos/coque
K_W_FACTOR = 3.0                   # k_cera = 3 k_óleo
O_CRACK = {"G_HC": 0.60, "A": 0.30, "COKE": 0.10}
K_TAR_GAS = (3.09e6, 93.3e3)
K_TAR_CHAR = (1.0e5, 107.5e3)
MW_LUMP = {"G_HC": 0.025, "G_OX": 0.033, "O": 0.15, "W": 0.40, "A": 0.10, "OX": 0.12, "TAR": 0.10,
           "H2O": 0.018, "HCl": 0.0365, "N2": 0.028}
CP_VAP = 2200.0
# grupos de componentes para o gráfico da taxa de pirólise (na ordem em que reagem)
GROUPS = {"água": ["H2O"], "PVC": ["PVC", "PVCr"], "celulósicos": ["CELL"], "PS": ["PS"], "PP": ["PP"],
          "PE": ["LDPE", "HDPE"], "PET": ["PET"], "borracha": ["RUBa", "RUBb", "RUBc"]}


@dataclass
class BedModel:
    """Parâmetros da troca de calor interna (valores de projeto [H] e faixas da literatura)."""
    h_contact: tuple = (30.0, 150.0, 70.0)     # parede→pedaços soltos / fundido / carvão [W/(m² K)] [H]
    beta_deg: tuple = (32.0, 4.0, 33.0)        # ângulo dinâmico: soltos (DEM: 32°) / fundido / carvão
    curtain: tuple = (0.25, 0.08, 0.30)        # área extra de cortina / área da superfície (com aletas) [H/DEM]
    d_pore: tuple = (0.02, 0.002, 0.004)       # tamanho de poro para a radiação no leito [m]
    eps_wall_in: float = 0.80                  # casco por dentro (com depósitos)
    eps_bed: float = 0.90
    h_fb: float = 6.0                          # convecção no espaço livre [W/(m² K)]
    D_ax: float = 2.0e-4                       # dispersão axial do leito girando [m²/s] [H]
    purge: float = 2.0e-4                      # N2 de purga/vedação [kg/s]
    eps_out: float = 0.85


@dataclass
class Control:
    setpoint_C: float = 500.0                  # "500 graus" (UFRJ): parede média do tambor
    variable: str = "parede"                   # "parede" (casco médio) ou "carga"
    T_shell_max_C: float = 650.0               # limite do aço do casco (Q345R ≤ 475 °C de serviço; alarme)
    Kp: float = 4000.0                         # W/K
    Ti: float = 900.0                          # s
    ramp_K_min: float = 2.5                    # rampa de partida do setpoint (protege o casco e a vedação) [H]
    ncg_recycle: bool = True


@dataclass
class BatchConfig:
    mode: str = "rotativo"
    nx: int = 7
    nphi: int = 36
    n_layers: int = 24
    dt: float = 2.0
    t_max_h: float = 10.0
    end_frac: float = 0.03                     # fim: produção < 3 % do pico (e carga > 400 °C)
    log_every: float = 30.0                    # s
    snap_every: float = 300.0                  # s
    wall: float = 0.012
    rho_s: float = 7850.0
    cp_s: float = 560.0
    k_s: float = 40.0
    bed: BedModel = field(default_factory=BedModel)
    control: Control = field(default_factory=Control)


# ------------------------------------------------------------------ geometria
def crossed_strings(P1, P2, Q1, Q2):
    """F(P→Q) entre segmentos 2D num recinto convexo (cordas cruzadas de Hottel). Arrays [..., 2]."""
    d = lambda a, b: np.linalg.norm(a - b, axis=-1)  # noqa: E731
    L = d(P1, P2)
    cross = d(P1, Q2) + d(P2, Q1)
    uncross = d(P1, Q1) + d(P2, Q2)
    return np.abs(cross - uncross) / (2 * np.maximum(L, 1e-12))


def arc_overlap(a0, a1, b0, b1):
    """Comprimento angular de [a0, a1] ∩ [b0, b1] (rad), com ângulos já desembrulhados."""
    out = 0.0
    for s in (-2 * math.pi, 0.0, 2 * math.pi):
        out = out + np.clip(np.minimum(a1, b1 + s) - np.maximum(a0, b0 + s), 0.0, None)
    return out


class BatchDrum:
    def __init__(self, drum: Drum, charge: fd.Charge, furnace: Furnace | None = None,
                 cfg: BatchConfig | None = None, rpm: float | None = None):
        self.drum, self.charge = drum, charge
        self.fur = furnace or Furnace()
        self.cfg = cfg or BatchConfig()
        c = self.cfg
        self.rotating = c.mode == "rotativo"
        self.rpm = (drum.rpm if rpm is None else rpm) if self.rotating else 0.0
        self.Omega = 2 * math.pi * self.rpm / 60.0
        R, L = drum.R, drum.L
        self.R, self.L = R, L
        self.dx = L / c.nx
        self.xc = (np.arange(c.nx) + 0.5) * self.dx
        self.dphi = 2 * math.pi / c.nphi
        self.phi0 = -math.pi + (np.arange(c.nphi) + 0.5) * self.dphi   # ângulo no referencial do tambor
        self.A_sec = R * self.dphi * self.dx
        self.R_out = R + c.wall
        self.A_out = self.R_out * self.dphi * self.dx
        self.zones = FurnaceZones(self.fur, self.R_out, L, self.xc, np.degrees(self.phi0))
        # casco
        self.Ts = np.full((c.nx, c.nphi), T0)
        self.m_s = c.rho_s * c.wall * self.A_sec
        # aletas como aletas térmicas
        if drum.n_lifters:
            m_fin = math.sqrt(2 * 60.0 / (c.k_s * drum.lifter_t))
            eta = math.tanh(m_fin * drum.lifter_h) / (m_fin * drum.lifter_h)
            self.fin = drum.n_lifters * 2 * drum.lifter_h * eta / (2 * math.pi * R)
        else:
            self.fin = 0.0
        if not self.rotating:
            self.fin *= 0.5        # parado: só as aletas que ficaram dentro da pilha ajudam
        # carga
        m = charge.masses()
        n = c.nx if self.rotating else c.nx * c.n_layers
        per = {k: v / n for k, v in m.items()}
        self.kin = fd.KineticState(per, n)
        st1 = fd.KineticState(m, 1)
        V_raw = float(st1.volume(np.array([T0]))[0])
        self.loose_scale = V_raw / (charge.fill * drum.volume())
        self.T = np.full(n, T0)
        self.Tg = np.full(c.nx, T0)
        self.m_charge0 = sum(m.values())
        self.m0_comp = dict(m)
        # contabilidade
        self.t, self.theta = 0.0, 0.0
        self.prod = {k: 0.0 for k in fd.LUMPS + ["COKE"]}
        self.cum = {k: 0.0 for k in ["oleo", "aquoso", "gas", "coque", "Q_fire", "Q_aux", "Q_ncg", "Q_flare",
                                     "Q_shell", "Q_flue", "Q_loss", "Q_in_drum", "Q_rxn", "Q_evap", "aux_kg",
                                     "Q_vap_out"]}
        self.Q_fire = 0.3 * self.fur.Q_max
        self.I_err = 0.0
        self.ncg_rate = {"G_HC": 0.0, "G_OX": 0.0}
        self.peak_rate = 0.0
        self.log, self.snaps = [], []
        self.done = False
        self.E_shell0 = self._shell_energy()
        self.H_bed0 = self._bed_enthalpy()

    # -------------------------------------------------------------- utilidades
    def _shell_energy(self):
        return float((self.m_s * self.cfg.cp_s * (self.Ts - T0)).sum())

    def _bed_enthalpy(self):
        return float(np.sum(self.kin.enthalpy(self.T)))

    def _slice_view(self, a):
        """Array por volume do leito → [nx, n_l] (estático) ou [nx, 1]."""
        return a.reshape(self.cfg.nx, -1)

    def bed_geometry(self):
        """Por fatia: enchimento F, meio ângulo ε, ângulo do leito β, centro do arco coberto φ_c."""
        c, b = self.cfg, self.cfg.bed
        V = self._slice_view(self.kin.volume(self.T, self.loose_scale)).sum(1)
        F = np.clip(V / (math.pi * self.R ** 2 * self.dx), 1e-4, 0.95)
        eps = np.array([fill_half_angle(f) for f in F])
        Tm = self._slice_view(self.T).mean(1)
        lo, me, re = (self._slice_view(a).mean(1) for a in self.kin.state_fractions(self.T))
        if self.rotating:
            beta = np.radians(lo * b.beta_deg[0] + me * b.beta_deg[1] + re * b.beta_deg[2])
        else:
            beta = np.zeros(c.nx)
        phic = -math.pi / 2 + beta
        return dict(V=V, F=F, eps=eps, beta=beta, phic=phic, frac=(lo, me, re), Tm=Tm)

    # -------------------------------------------------------- radiação interna
    def _radiation(self, phi_lab, geo, Tbs):
        """Radiosidade por fatia entre setores expostos do casco e a superfície da carga.

        Devolve q_rad [nx, nphi] (perda de cada setor por radiação, W/m² de setor) e Q_bed [nx] (W)."""
        c, b = self.cfg, self.cfg.bed
        nx, nphi = c.nx, c.nphi
        R = self.R
        q_out = np.zeros((nx, nphi))
        Qb = np.zeros(nx)
        for k in range(nx):
            pc = geo["phic"][k]
            mid = pc + (phi_lab - pc + math.pi) % (2 * math.pi) - math.pi      # janela [φc − π, φc + π)
            a0, a1 = mid - 0.5 * self.dphi, mid + 0.5 * self.dphi
            c0, c1 = pc - geo["eps"][k], pc + geo["eps"][k]
            # parte exposta de cada setor: o intervalo do setor menos o arco coberto (maior pedaço)
            lo = np.where((a0 >= c0) & (a0 < c1), c1, a0)
            hi = np.where((a1 > c0) & (a1 <= c1), c0, a1)
            cov_mid = (a0 < c0) & (a1 > c1)
            hi = np.where(cov_mid, c0, hi)
            exp_len = np.clip(hi - lo, 0.0, None)
            exp_len = np.where((a0 >= c0) & (a1 <= c1), 0.0, exp_len)
            P1 = np.stack([R * np.cos(lo), R * np.sin(lo)], -1)
            P2 = np.stack([R * np.cos(hi), R * np.sin(hi)], -1)
            B1 = np.array([R * math.cos(c0), R * math.sin(c0)])
            B2 = np.array([R * math.cos(c1), R * math.sin(c1)])
            Ps = np.concatenate([P1, B2[None]], 0)
            Pe = np.concatenate([P2, B1[None]], 0)
            n = nphi + 1
            Lseg = np.linalg.norm(Pe - Ps, axis=-1)
            Lseg[:nphi] = np.where(exp_len > 1e-6, Lseg[:nphi], 0.0)
            F = crossed_strings(Ps[:, None], Pe[:, None], Ps[None], Pe[None])
            np.fill_diagonal(F, 0.0)
            F[:, Lseg == 0] = 0.0
            F[Lseg == 0, :] = 0.0
            rs = F.sum(1, keepdims=True)
            F = np.where(rs > 0, F / np.maximum(rs, 1e-12), 0.0)
            eps = np.full(n, b.eps_wall_in); eps[-1] = b.eps_bed
            T = np.concatenate([self._shell_lab_T[k], [Tbs[k]]])
            Eb = SIGMA * T ** 4
            Amat = np.eye(n) - (1 - eps)[:, None] * F
            J = np.linalg.solve(Amat, eps * Eb)
            qnet = eps / (1 - eps) * (Eb - J)                 # W/m² da superfície (positivo = perde)
            Qnet = qnet * Lseg * self.dx
            q_out[k] = Qnet[:nphi] / self.A_sec
            Qb[k] = -Qnet[-1]
        return q_out, Qb

    # ------------------------------------------------------------- um passo
    def step(self):
        c, b, cn = self.cfg, self.cfg.bed, self.cfg.control
        dt = c.dt
        nx, nphi = c.nx, c.nphi
        geo = self.bed_geometry()
        phi_lab = self.phi0 + self.theta                                   # ângulo de laboratório dos setores
        phi_wrapped = (phi_lab + math.pi) % (2 * math.pi) - math.pi
        # cobertura de cada setor
        cov = np.zeros((nx, nphi))
        for k in range(nx):
            c0, c1 = geo["phic"][k] - geo["eps"][k], geo["phic"][k] + geo["eps"][k]
            cov[k] = arc_overlap(phi_wrapped - 0.5 * self.dphi, phi_wrapped + 0.5 * self.dphi, c0, c1) / self.dphi
        self._shell_lab_T = self.Ts
        # ---- queima e fornalha
        use, m_fg, pwc, Q_ncg_used, Q_flare = fuel_mix(self.Q_fire, self.ncg_rate if cn.ncg_recycle else {},
                                                       self.fur.aux_fuel, self.fur.lam)
        q_f, fdiag = self.zones.solve(self.Ts, self.Q_fire, m_fg, pwc, np.degrees(phi_wrapped))
        # ---- carga: propriedades e coeficientes
        lo, me, re = geo["frac"]
        Tb_sl = self._slice_view(self.T)
        T_bot = Tb_sl[:, 0]
        T_top = Tb_sl[:, -1]
        h_c = lo * b.h_contact[0] + me * b.h_contact[1] + re * b.h_contact[2]
        d_pore = lo * b.d_pore[0] + me * b.d_pore[1] + re * b.d_pore[2]
        curt = (lo * b.curtain[0] + me * b.curtain[1] + re * b.curtain[2]) if (self.rotating and self.drum.n_lifters) else 0.0
        if self.rotating:
            kb = self.kin.conductivity(self.T, d_piece=np.repeat(d_pore, len(self.T) // nx))
            mass = self.kin.total()
            Vb = self.kin.volume(self.T, self.loose_scale)
            rho_b = mass / np.maximum(Vb, 1e-9)
            cp_b = self.kin.heat_capacity(self.T) / np.maximum(mass, 1e-9)
            t_c = np.maximum(2 * geo["eps"] / max(self.Omega, 1e-9), 1.0)
            h_pen = 2 * np.sqrt(kb * rho_b * cp_b / (math.pi * t_c))
            h_wb = 1.0 / (1.0 / h_c + 1.0 / h_pen)
        else:
            # primeira camada: contato em série com meia espessura de condução
            k0 = self.kin.conductivity(self.T, d_piece=np.repeat(d_pore, c.n_layers))
            k0 = self._slice_view(k0)[:, 0]
            t0 = self._layer_geom(geo)["t"][:, 0]
            h_wb = 1.0 / (1.0 / h_c + 0.5 * t0 / np.maximum(k0, 1e-3))
        h_wb_eff = h_wb * (1 + self.fin)
        # ---- trocas internas por setor
        q_bed = cov * h_wb_eff[:, None] * (self.Ts - T_bot[:, None])        # W/m² de setor
        q_rad, Q_rad_bed = self._radiation(phi_wrapped, geo, T_top)
        Q_curt = curt * np.clip(Q_rad_bed, 0.0, None)                       # cortina intercepta mais radiação
        q_rad_c = q_rad.copy()
        pos = np.clip(q_rad, 0.0, None) * (1 - cov)
        share = pos / np.maximum(pos.sum(1, keepdims=True), 1e-12)
        q_rad_c += share * (Q_curt / self.A_sec)[:, None]
        exposed = 1 - cov
        q_fb = exposed * b.h_fb * (self.Ts - self.Tg[:, None])
        q_in = q_bed + q_rad_c + q_fb                                        # sai do casco para dentro
        # condução no aço (circunferencial e axial)
        ks, w = c.k_s, c.wall
        ds = self.R * self.dphi
        lap = (np.roll(self.Ts, 1, 1) + np.roll(self.Ts, -1, 1) - 2 * self.Ts) / ds ** 2
        Tpx = np.vstack([self.Ts[:1], self.Ts, self.Ts[-1:]])
        lap += (Tpx[2:] + Tpx[:-2] - 2 * self.Ts) / self.dx ** 2
        dTs = dt * (self.A_out * q_f - self.A_sec * q_in + ks * w * self.A_sec * lap) / (self.m_s * c.cp_s)
        # ---- energia que entra na carga
        Q_wall = (q_bed * self.A_sec).sum(1)
        A_surf = 2 * self.R * np.sin(geo["eps"]) * self.dx
        Q_conv_top = b.h_fb * A_surf * (self.Tg - T_top)
        Q_top = Q_rad_bed + Q_curt + Q_conv_top
        # ---- química
        prod, heat, rx_rates = self.kin.react(self.T, dt)
        if self.rotating:
            Q = Q_wall + Q_top
            # dispersão axial
            C = self.kin.heat_capacity(self.T)
            Tp = np.concatenate([self.T[:1], self.T, self.T[-1:]])
            Q_ax = b.D_ax * (C / (self.dx ** 2)) * (Tp[2:] + Tp[:-2] - 2 * self.T)
            Q = Q + Q_ax
            self.T = self.T + (Q * dt - heat) / np.maximum(C, 1e-6)
        else:
            # condução implícita entre camadas (camadas que fundem ficam finas: explícito seria instável)
            G = self._conductances(geo)                       # [nx, n_l − 1]
            C = self._slice_view(self.kin.heat_capacity(self.T))
            S = -self._slice_view(heat) / dt
            S[:, 0] += Q_wall
            S[:, -1] += Q_top
            self.T = self._implicit_layers(self._slice_view(self.T), C, G, S, dt).reshape(-1)
        # ---- umidade: platô a 100 °C
        mw = self.kin.mass("H2O")
        over = (self.T > 373.15) & (mw > 0)
        Cn = self.kin.heat_capacity(self.T)
        evap = np.where(over, np.minimum(mw, Cn * (self.T - 373.15) / fd.COMPONENTS["H2O"].dH), 0.0)
        self.T = np.where(over, self.T - evap * fd.COMPONENTS["H2O"].dH / np.maximum(Cn, 1e-6), self.T)
        m0w = self.kin.m0["H2O"]
        self.kin.p["H2O"] = np.where(m0w > 0, np.clip(1 - (mw - evap) / np.maximum(m0w, 1e-30), 0, 1), 1.0)
        prod["H2O"] = prod["H2O"] + evap
        # ---- casco
        self.Ts = self.Ts + dTs
        # ---- espaço livre: vapores da fatia k, pistonado até a saída
        gen = {k: self._slice_view(v).sum(1) / dt for k, v in prod.items()}    # kg/s por fatia
        gen_tot = sum(gen.values())
        flow = {k: 0.0 for k in fd.LUMPS + ["N2"]}
        flow["N2"] = b.purge
        Tg_in = T0
        A_exp = (exposed * self.A_sec).sum(1)
        Tw_exp = (exposed * self.A_sec * self.Ts).sum(1) / np.maximum(A_exp, 1e-9)
        Vfb = math.pi * self.R ** 2 * self.dx * (1 - geo["F"])
        coke = 0.0
        Q_gas_heat = 0.0
        for k in range(nx):
            m_in = sum(flow.values())
            hA_w, hA_b = b.h_fb * A_exp[k], b.h_fb * A_surf[k]
            mcp_in, mcp_gen = m_in * CP_VAP, gen_tot[k] * CP_VAP
            Tg = (mcp_in * Tg_in + mcp_gen * T_top[k] + hA_w * Tw_exp[k] + hA_b * T_top[k]) / \
                (mcp_in + mcp_gen + hA_w + hA_b)
            self.Tg[k] = Tg
            for lump in fd.LUMPS:
                flow[lump] = flow[lump] + gen[lump][k]
            # residência na fatia e craqueamento
            mtot = sum(flow.values())
            Mmix = mtot / max(sum(flow[s] / MW_LUMP[s] for s in flow), 1e-12)
            rho = 101325.0 * Mmix / (8.314 * Tg)
            tau = Vfb[k] * rho / max(mtot, 1e-9)
            kO = K_O[0] * math.exp(-K_O[1] / (8.314 * Tg))
            dO = flow["O"] * (1 - math.exp(-kO * tau))
            dW = flow["W"] * (1 - math.exp(-K_W_FACTOR * kO * tau))
            flow["W"] -= dW
            flow["O"] += dW - dO
            for p_, y in O_CRACK.items():
                if p_ == "COKE":
                    coke += dO * y
                else:
                    flow[p_] += dO * y
            k1 = K_TAR_GAS[0] * math.exp(-K_TAR_GAS[1] / (8.314 * Tg))
            k2 = K_TAR_CHAR[0] * math.exp(-K_TAR_CHAR[1] / (8.314 * Tg))
            dT_ = flow["TAR"] * (1 - math.exp(-(k1 + k2) * tau))
            flow["TAR"] -= dT_
            flow["G_OX"] += dT_ * k1 / (k1 + k2)
            coke += dT_ * k2 / (k1 + k2)
            Tg_in = Tg
        Q_gas_heat = (sum(flow.values()) - b.purge) * CP_VAP * (Tg_in - T0)
        self.T_vap_out = Tg_in
        # ---- condensador e reciclo do gás
        oil = sum(flow[k] for k in fd.CONDENSABLE)
        aq = flow["H2O"] + flow["HCl"]
        gas = flow["G_HC"] + flow["G_OX"]
        self.ncg_rate = {"G_HC": flow["G_HC"], "G_OX": flow["G_OX"]}
        for k in fd.LUMPS:
            self.prod[k] += flow[k] * dt
        self.prod["COKE"] += coke * dt
        self.kin.add("CHAR", np.full(self.kin.n, coke * dt / self.kin.n))   # o coque fica no tambor
        cu = self.cum
        cu["oleo"] += oil * dt; cu["aquoso"] += aq * dt; cu["gas"] += gas * dt; cu["coque"] += coke * dt
        cu["Q_fire"] += self.Q_fire * dt
        cu["Q_ncg"] += Q_ncg_used * dt; cu["Q_aux"] += (self.Q_fire - Q_ncg_used) * dt
        cu["Q_flare"] += Q_flare * dt
        cu["aux_kg"] += use.get(self.fur.aux_fuel, 0.0) * dt
        cu["Q_shell"] += fdiag["Q_shell"] * dt; cu["Q_flue"] += fdiag["Q_flue"] * dt
        cu["Q_loss"] += fdiag["Q_loss"] * dt
        cu["Q_in_drum"] += float((q_in * self.A_sec).sum()) * dt
        cu["Q_rxn"] += float(heat.sum()); cu["Q_evap"] += float(evap.sum()) * fd.COMPONENTS["H2O"].dH
        cu["Q_vap_out"] += Q_gas_heat * dt
        # ---- controle da queima (PI com anti-windup e limite do casco)
        T_ctrl = float(self.Ts.mean()) if cn.variable == "parede" else float(self.T.mean())
        T_sp = min(cn.setpoint_C + 273.15, T0 + 40.0 + cn.ramp_K_min * self.t / 60.0) if cn.ramp_K_min > 0 \
            else cn.setpoint_C + 273.15
        err = T_sp - T_ctrl
        Ts_max = float(self.Ts.max())
        if Ts_max > cn.T_shell_max_C + 273.15:
            err = min(err, (cn.T_shell_max_C + 273.15 - Ts_max) * 3.0)
        Q_try = cn.Kp * (err + self.I_err / cn.Ti)
        if self.fur.Q_min < Q_try < self.fur.Q_max or (Q_try >= self.fur.Q_max and err < 0) or \
                (Q_try <= self.fur.Q_min and err > 0):
            self.I_err += err * dt
        self.Q_fire = float(np.clip(cn.Kp * (err + self.I_err / cn.Ti), self.fur.Q_min, self.fur.Q_max))
        # ---- avanço do tempo
        self.t += dt
        self.theta += self.Omega * dt
        rate = oil + gas
        self.peak_rate = max(self.peak_rate, rate)
        self._rx = {k: float(np.sum(v)) for k, v in rx_rates.items()}
        self._rx["H2O"] = float(np.sum(evap)) / dt
        self._last = dict(geo=geo, q_f=q_f, q_in=q_in, cov=cov, fdiag=fdiag, h_wb=h_wb, rates=dict(oil=oil, aq=aq,
                          gas=gas, coke=coke), use=use, Q_ncg=Q_ncg_used, Q_flare=Q_flare, Q_rad_bed=Q_rad_bed,
                          Q_wall=Q_wall, Q_curt=Q_curt, phi_lab=phi_wrapped)
        if (self.t > 3600 and rate < c.end_frac * self.peak_rate and self.peak_rate > 0
                and float((self.kin.total() * self.T).sum() / max(self.kin.total().sum(), 1e-9)) > 673.15):
            self.done = True

    # ---------------------------------------------- pilha estática: camadas
    def _layer_geom(self, geo):
        """Espessura e áreas das interfaces das camadas (da parede para a superfície), por fatia."""
        c = self.cfg
        R = self.R
        eps = geo["eps"]
        S = 2 * eps * R                     # arco molhado
        W = 2 * R * np.sin(eps)             # superfície livre
        Aseg = R ** 2 * (eps - np.sin(eps) * np.cos(eps))
        Heq = 2 * Aseg / np.maximum(S + W, 1e-9)
        v = self._slice_view(self.kin.volume(self.T, self.loose_scale)) / self.dx       # área por camada
        v = v / np.maximum(v.sum(1, keepdims=True), 1e-12) * Aseg[:, None]
        acum = np.concatenate([np.zeros((c.nx, 1)), np.cumsum(v, 1)], 1)
        a = (W - S) / (2 * np.maximum(Heq, 1e-9))
        # S s + a s² = acum → s
        disc = np.sqrt(np.maximum(S[:, None] ** 2 + 4 * a[:, None] * acum, 0.0))
        s = np.where(np.abs(a[:, None]) > 1e-9, (-S[:, None] + disc) / (2 * a[:, None] + 1e-30),
                     acum / np.maximum(S[:, None], 1e-9))
        A_if = S[:, None] + 2 * a[:, None] * s
        return dict(t=np.diff(s, axis=1), s=s, A=A_if, S=S, W=W, Heq=Heq)

    @staticmethod
    def _implicit_layers(T, C, G, S, dt):
        """(C/dt)(T' − T) = G_{i−1}(T'_{i−1} − T'_i) + G_i(T'_{i+1} − T'_i) + S (Thomas vetorizado)."""
        nl = T.shape[1]
        a = np.zeros_like(T); b = C / dt; cc = np.zeros_like(T); d = C / dt * T + S
        b[:, :-1] += G; b[:, 1:] += G
        a[:, 1:] = -G; cc[:, :-1] = -G
        cp_, dp_ = np.zeros_like(T), np.zeros_like(T)
        cp_[:, 0] = cc[:, 0] / b[:, 0]; dp_[:, 0] = d[:, 0] / b[:, 0]
        for i in range(1, nl):
            den = b[:, i] - a[:, i] * cp_[:, i - 1]
            cp_[:, i] = cc[:, i] / den
            dp_[:, i] = (d[:, i] - a[:, i] * dp_[:, i - 1]) / den
        x = np.zeros_like(T)
        x[:, -1] = dp_[:, -1]
        for i in range(nl - 2, -1, -1):
            x[:, i] = dp_[:, i] - cp_[:, i] * x[:, i + 1]
        return x

    def _conductances(self, geo):
        c = self.cfg
        lg = self._layer_geom(geo)
        lo, me, re = geo["frac"]
        d_pore = lo * c.bed.d_pore[0] + me * c.bed.d_pore[1] + re * c.bed.d_pore[2]
        k = self._slice_view(self.kin.conductivity(self.T, d_piece=np.repeat(d_pore, c.n_layers)))
        t = np.maximum(lg["t"], 1e-5)
        kf = 2 * k[:, 1:] * k[:, :-1] / (k[:, 1:] + k[:, :-1])
        return lg["A"][:, 1:-1] * self.dx * kf / (0.5 * (t[:, 1:] + t[:, :-1]))

    def _conduction(self, geo):
        c = self.cfg
        lg = self._layer_geom(geo)
        lo, me, re = geo["frac"]
        d_pore = lo * c.bed.d_pore[0] + me * c.bed.d_pore[1] + re * c.bed.d_pore[2]
        k = self._slice_view(self.kin.conductivity(self.T, d_piece=np.repeat(d_pore, c.n_layers)))
        T = self._slice_view(self.T)
        t = np.maximum(lg["t"], 1e-5)
        kf = 2 * k[:, 1:] * k[:, :-1] / (k[:, 1:] + k[:, :-1])
        G = lg["A"][:, 1:-1] * self.dx * kf / (0.5 * (t[:, 1:] + t[:, :-1]))
        flux = G * (T[:, :-1] - T[:, 1:])          # da camada i para i+1
        Q = np.zeros_like(T)
        Q[:, :-1] -= flux
        Q[:, 1:] += flux
        return Q.reshape(-1)

    # ---------------------------------------------------------------- saída
    def record(self):
        g = self._last["geo"]
        fd_ = self._last["fdiag"]
        r = self._last["rates"]
        mass = self.kin.total()
        T_mw = float((mass * self.T).sum() / max(mass.sum(), 1e-9))
        st = dict(t_h=self.t / 3600, T_carga=T_mw - 273.15,
                  T_carga_min=float(self.T.min()) - 273.15, T_carga_max=float(self.T.max()) - 273.15,
                  T_casco=float(self.Ts.mean()) - 273.15, T_casco_max=float(self.Ts.max()) - 273.15,
                  T_vapor=self.T_vap_out - 273.15, T_fumos=fd_["T_flue"] - 273.15,
                  T_camara=float(fd_["Tg"][:, 0].mean()) - 273.15,
                  enchimento=float(g["F"].mean()), Q_fire_kW=self.Q_fire / 1e3,
                  Q_ncg_kW=self._last["Q_ncg"] / 1e3, Q_aux_kW=(self.Q_fire - self._last["Q_ncg"]) / 1e3,
                  Q_flare_kW=self._last["Q_flare"] / 1e3, Q_casco_kW=fd_["Q_shell"] / 1e3,
                  Q_parede_carga_kW=float(self._last["Q_wall"].sum()) / 1e3,
                  Q_rad_carga_kW=float(self._last["Q_rad_bed"].sum() + self._last["Q_curt"].sum()) / 1e3,
                  h_wb=float(np.mean(self._last["h_wb"])),
                  oleo_kg=self.cum["oleo"], aquoso_kg=self.cum["aquoso"], gas_kg=self.cum["gas"],
                  coque_kg=self.cum["coque"], carvao_kg=float(np.sum(self.kin.mass("CHAR") + self.kin.mass("CB"))),
                  cinzas_kg=float(np.sum(self.kin.mass("INERT"))),
                  carga_kg=float(np.sum(self.kin.total())), agua_kg=float(np.sum(self.kin.mass("H2O"))),
                  vazao_oleo_kg_h=r["oil"] * 3600, vazao_gas_kg_h=r["gas"] * 3600,
                  frac_fundido=float(np.mean(g["frac"][1])), aux_kg=self.cum["aux_kg"],
                  HCl_kg=self.prod["HCl"])
        # taxa de reação (kg/h de componente consumido) e conversão de cada grupo: o "DTG" da batelada
        rx = getattr(self, "_rx", {})
        for g, keys in GROUPS.items():
            st[f"taxa_{g}"] = 3600.0 * sum(rx.get(k, 0.0) for k in keys)
            m0 = sum(self.m0_comp[k] for k in keys)
            st[f"conv_{g}"] = 1.0 - sum(float(np.sum(self.kin.mass(k))) for k in keys) / m0 if m0 > 0 else 1.0
        st["taxa_total"] = sum(st[f"taxa_{g}"] for g in GROUPS if g != "água")
        for k in fd.ORDER:
            st[f"m_{k}"] = float(np.sum(self.kin.mass(k)))
        self.log.append(st)
        return st

    def snapshot(self):
        g = self._last["geo"]
        snap = dict(t=self.t, theta=self.theta, Ts=self.Ts.copy(), T=self.T.copy(), F=g["F"].copy(),
                    eps=g["eps"].copy(), beta=g["beta"].copy(), frac=[a.copy() for a in g["frac"]],
                    q_f=self._last["q_f"].copy(), Tg_fur=self._last["fdiag"]["Tg"].copy(),
                    Tr_fur=self._last["fdiag"]["Tr"].copy(), Q_fire=self.Q_fire, Tg=self.Tg.copy(),
                    char=self.kin.mass("CHAR") + self.kin.mass("CB"), total=self.kin.total(),
                    vol=self.kin.volume(self.T, self.loose_scale))
        self.snaps.append(snap)
        return snap

    def run(self, verbose: bool = True, callback=None):
        c = self.cfg
        n_log = max(int(round(c.log_every / c.dt)), 1)
        n_snap = max(int(round(c.snap_every / c.dt)), 1)
        i = 0
        t0 = time.time()
        while self.t < c.t_max_h * 3600 and not self.done:
            self.step()
            i += 1
            if i % n_log == 0 or i == 1:
                st = self.record()
                if callback:
                    callback(self, st)
            if i % n_snap == 0 or i == 1:
                self.snapshot()
            if verbose and i % int(round(1800 / c.dt)) == 0:
                st = self.log[-1]
                print(f"  {st['t_h']:4.1f} h  carga {st['T_carga']:5.0f} °C  casco {st['T_casco']:5.0f} °C "
                      f"(máx {st['T_casco_max']:4.0f})  queima {st['Q_fire_kW']:4.0f} kW "
                      f"(gás próprio {st['Q_ncg_kW']:4.0f})  óleo {st['oleo_kg']:5.0f} kg  "
                      f"enchimento {100 * st['enchimento']:4.1f} %  [{time.time() - t0:4.0f} s]", flush=True)
        self.record(); self.snapshot()
        return self.summary()

    def summary(self) -> dict:
        m0 = self.m_charge0
        cu = self.cum
        char = float(np.sum(self.kin.mass("CHAR") + self.kin.mass("CB")))
        ash = float(np.sum(self.kin.mass("INERT")))
        left = float(np.sum(self.kin.total())) - char - ash
        out = dict(duracao_h=self.t / 3600, oleo=cu["oleo"] / m0, aquoso=cu["aquoso"] / m0, gas=cu["gas"] / m0,
                   carvao=char / m0, cinzas=ash / m0, nao_convertido=left / m0, coque_kg=cu["coque"],
                   oleo_kg=cu["oleo"], gas_kg=cu["gas"], carvao_kg=char, cinzas_kg=ash)
        out["fecho_massa"] = (cu["oleo"] + cu["aquoso"] + cu["gas"] + float(np.sum(self.kin.total())) -
                              cu["coque"] - m0) / m0
        out["Q_queima_GJ"] = cu["Q_fire"] / 1e9
        out["Q_aux_GJ"] = cu["Q_aux"] / 1e9
        out["aux_kg"] = cu["aux_kg"]
        out["aux_GJ_por_t"] = cu["Q_aux"] / 1e9 / (m0 / 1000)
        out["Q_gas_proprio_GJ"] = cu["Q_ncg"] / 1e9
        out["Q_flare_GJ"] = cu["Q_flare"] / 1e9
        out["eficiencia_fornalha"] = cu["Q_shell"] / max(cu["Q_fire"], 1)
        # balanço de energia da fornalha e do tambor
        out["fecho_fornalha"] = (cu["Q_fire"] - cu["Q_shell"] - cu["Q_flue"] - cu["Q_loss"]) / max(cu["Q_fire"], 1)
        dE_shell = self._shell_energy() - self.E_shell0
        out["fecho_casco"] = (cu["Q_shell"] - cu["Q_in_drum"] - dE_shell) / max(cu["Q_shell"], 1)
        T_end = self.T
        return out
