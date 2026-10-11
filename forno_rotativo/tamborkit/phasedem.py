"""DEM com mudança de fase do lixo ao longo de toda a batelada (acoplado em uma via ao modelo da batelada).

Cada partícula é um pedaço de um material do lixo, com a massa real que ele representa na fatia simulada:
filme de PEBD, frasco de PEAD, tampa/rede de PP, isopor (PS expandido), garrafa PET, tubo de PVC, papel/
madeira, borracha e areia/conchas. O modelo da batelada continua mandando no calor e na química (temperatura da
carga e conversão de cada componente ao longo do tempo); o DEM mostra o que isso faz com os pedaços:

  * secagem: a água sai (massa) sem mudar a forma;
  * plásticos que fundem (PEBD ~110 °C, PEAD ~130, PS amolece ~100–150, PP ~165, PET ~255 °C): o volume do
    pedaço colapsa do aparente ("solto") para o denso conforme a fração fundida f_m(T); na janela de fusão o
    pedaço fica pegajoso (coesão + atrito maiores: pontes de fundido); com f_m ≥ f_merge ele coalesce na
    POÇA DE FUNDIDO (sai do DEM e entra no inventário da poça, por componente);
  * celulósicos, borracha e PVC não fundem: perdem massa pela cinética e encolhem até virar carvão (escurecem);
  * a poça: volume pela massa de cada polímero ainda não craqueado / densidade do fundido; viscosidade
    η(T, conversão) que despenca com a cisão das cadeias; nos pedaços submersos atuam empuxo (ρ_fundido V g) e
    arrasto de Stokes (relaxação exata da velocidade para a do fundido, estável com η alto);
  * o carvão que se forma no fundido (PS, PET, PVC, poliolefinas) aparece como grânulos novos na poça.

Relógio: o movimento de cada volta é o real (mesmo regime de rolamento), mas a batelada de horas é comprimida
em poucas voltas — o DEM não tenta reproduzir as ~290 voltas de 6 h; a temperatura e a conversão vêm do modelo
validado da batelada (a carga girando é quase isotérmica na seção). Uma pequena dispersão de temperatura entre
pedaços (σ ≈ 8 K: graus e formas diferentes do mesmo material) espalha a fusão de cada classe.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import torch

from . import feed as fd
from .dem import DEMConfig, DrumDEM, G
from .geometry import Drum, fill_half_angle, lifter_contacts

# rótulo no DEM, componentes da carga, diâmetro típico do pedaço [m], cor sRGB (cores aproximadas dos materiais)
MATERIALS = [
    ("filme", ["LDPE"], 0.09, (228, 228, 218)),
    ("rigido_pe", ["HDPE"], 0.08, (70, 130, 200)),
    ("rigido_pp", ["PP"], 0.07, (232, 186, 64)),
    ("isopor", ["PS"], 0.10, (246, 246, 246)),
    ("pet", ["PET"], 0.08, (125, 200, 175)),
    ("pvc", ["PVC"], 0.06, (150, 152, 160)),
    ("organico", ["CELL"], 0.07, (150, 105, 60)),
    ("borracha", ["RUBa", "RUBb", "RUBc", "CB"], 0.06, (42, 42, 42)),
    ("areia", ["INERT"], 0.03, (205, 185, 140)),
]
CHAR_RGB = (26, 22, 20)
MELT_RGB = (196, 128, 52)           # fundido de poliolefina âmbar; escurece com o craqueamento
NAMES = [m[0] for m in MATERIALS] + ["carvao"]
MELTERS = {"filme": "LDPE", "rigido_pe": "HDPE", "rigido_pp": "PP", "isopor": "PS", "pet": "PET"}


@dataclass
class PhaseConfig:
    slab: float = 0.5                # comprimento da fatia periódica [m]
    rpm: float = 3.0                 # rotação simulada (regime de rolamento; o real é 0,8 rpm)
    n_rev: float = 5.0               # voltas do DEM para a batelada inteira (relógio comprimido)
    pre_rev: float = 1.0 / 3.0       # voltas frias antes de ligar o relógio (segmento "dentro do tambor")
    contact_time: float = 6.0e-3     # duração do contato [s] (rigidez proporcional à massa)
    d_spread: float = 0.25
    phi_pack: float = 0.58
    rho_inert: float = 2300.0        # pedaços de concha/vidro/pedra [kg/m³]
    sigma_T: float = 8.0             # dispersão de temperatura entre pedaços [K]
    f_merge: float = 0.85            # fração fundida a partir da qual o pedaço entra na poça
    cohesion: float = 1.5            # força coesiva máxima / peso efetivo, para pedaços totalmente pegajosos
    flow_frac: float = 0.6           # velocidade do fundido = flow_frac × rotação de corpo rígido
    beta_pool_deg: float = 6.0       # inclinação da superfície da poça (fundido viscoso arrastado pela parede)
    char_d: float = 0.03             # diâmetro dos grânulos de carvão que nascem na poça [m]
    char_rho: float = 420.0          # massa específica aparente dos grânulos [kg/m³]
    shrink_char: dict = field(default_factory=lambda: {"organico": 0.45, "borracha": 0.55, "pvc": 0.70})
    reserve: float = 0.25            # partículas reservadas para os grânulos (fração das ativas)
    upd_dt: float = 0.05             # intervalo entre atualizações de estado [s de DEM]
    frames: int = 1200               # quadros gravados ao longo da batelada
    pre_frames: int = 120            # quadros gravados no trecho frio
    seed: int = 1
    device: str = "auto"


def melt_viscosity(T_K, conv):
    """Viscosidade do fundido de poliolefinas [Pa s] durante a pirólise.

    η₀(T) de PE/PP fundido (~10³ Pa s a 200 °C, energia de ativação de fluxo ~30 kJ/mol) e queda com a cisão
    das cadeias: Mn/Mn₀ = 1/(1 + DPn₀ · 0,068 · √α) (cisão aleatória, mesma relação do reator agitado) e
    η ∝ Mn^3,4 acima do emaranhamento; abaixo dele, o ramo de ceras (mPa s)."""
    T = np.asarray(T_K, float)
    eta0 = 1.0e3 * np.exp(30e3 / 8.314 * (1.0 / np.maximum(T, 300.0) - 1.0 / 473.15))
    dpn0 = 30.0 / 0.028
    ratio = 1.0 / (1.0 + dpn0 * 0.068 * np.sqrt(np.clip(conv, 0.0, 1.0)))
    eta = eta0 * ratio ** 3.4
    wax = 2.0e-3 * np.exp(25e3 / 8.314 * (1.0 / np.maximum(T, 300.0) - 1.0 / 473.15))
    return np.maximum(eta, wax)


class PhaseDEM(DrumDEM):
    """DEM da carga com mudança de fase dirigida pelo log da batelada (BatchDrum.log)."""

    def __init__(self, drum: Drum, charge: fd.Charge, batch_log: list, pc: PhaseConfig | None = None):
        pc = pc or PhaseConfig()
        self.pc = pc
        self.log = batch_log
        gen = np.random.default_rng(pc.seed)
        self.gen = gen
        m_all = charge.masses()
        frac_slab = pc.slab / drum.L
        st1 = fd.KineticState(m_all, 1)
        V_raw = float(st1.volume(np.array([fd.T0]))[0])
        self.loose_scale = V_raw / (charge.fill * drum.volume())
        dry_tot = sum(v for k, v in m_all.items() if k != "H2O")
        self.moist = m_all["H2O"] / max(dry_tot, 1e-9)
        # ---- pedaços por material: massa real na fatia, densidade aparente do pedaço
        d_list, rho_list, lab_list, m0_list = [], [], [], []
        self.piece_rho, self.dense_rho = {}, {}
        for li, (name, comps, dmean, _) in enumerate(MATERIALS):
            M = sum(m_all[c] for c in comps) * frac_slab
            if M <= 0:
                continue
            if name == "areia":
                rho_piece = pc.rho_inert
                rho_dense = pc.rho_inert
            else:
                c0 = fd.COMPONENTS[comps[0]]
                rho_piece = c0.rho_loose * self.loose_scale / pc.phi_pack
                rho_dense = c0.rho_dense
            self.piece_rho[name] = rho_piece
            self.dense_rho[name] = rho_dense
            V1 = math.pi / 6 * dmean ** 3 * (1 + pc.d_spread ** 2)
            n = max(int(round(M / (rho_piece * V1))), 1)
            d = dmean * gen.uniform(1 - pc.d_spread, 1 + pc.d_spread, n)
            mp = rho_piece * math.pi / 6 * d ** 3
            mp *= M / mp.sum()                         # massa exata da fatia
            d_list.append(d); rho_list.append(mp / (math.pi / 6 * d ** 3)); lab_list += [li] * n
            m0_list.append(mp)
        d = np.concatenate(d_list); rho = np.concatenate(rho_list); m0 = np.concatenate(m0_list)
        lab = np.array(lab_list)
        n_act = len(d)
        n_res = int(pc.reserve * n_act)
        d = np.concatenate([d, np.full(n_res, pc.char_d)])
        rho = np.concatenate([rho, np.full(n_res, pc.char_rho)])
        lab = np.concatenate([lab, np.full(n_res, len(MATERIALS))])
        m0 = np.concatenate([m0, np.zeros(n_res)])
        active = np.r_[np.ones(n_act, bool), np.zeros(n_res, bool)]
        x0 = self._random_fill(drum, pc.slab, d, gen)
        cfg = DEMConfig(fill=charge.fill, d_mean=float(np.median(d[:n_act])), d_spread=pc.d_spread,
                        rho_bulk=float(np.sum(m0) / (charge.fill * math.pi * drum.R ** 2 * pc.slab)),
                        phi_pack=pc.phi_pack, slab=pc.slab, contact_time=pc.contact_time, cohesion=pc.cohesion,
                        device=pc.device, seed=pc.seed)
        super().__init__(drum, cfg, init=dict(x=x0, d=d, rho=rho, label=lab, names=NAMES, active=active, grow0=0.5))
        self.n_act0 = n_act
        self.m0p = torch.as_tensor(m0, dtype=self.ft, device=self.dev)          # massa seca inicial do pedaço
        self.r0 = self.r_final.clone()
        self.dT = torch.as_tensor(gen.normal(0.0, pc.sigma_T, self.N), dtype=self.ft, device=self.dev)
        self.f_m = torch.zeros(self.N, dtype=self.ft, device=self.dev)
        self.charf = torch.zeros(self.N, dtype=self.ft, device=self.dev)      # fração da massa que é carvão
        self.Tp = torch.full((self.N,), fd.T0, dtype=self.ft, device=self.dev)
        self.merged = torch.zeros(self.N, dtype=torch.bool, device=self.dev)
        # inventário da poça: massa "inicial equivalente" de cada polímero (m0_eq·u(t) é o que resta)
        self.pool_m0 = {c: 0.0 for c in MELTERS.values()}
        self.char_spawned = 0.0
        self.pool = dict(area=0.0, eps=0.0, beta=math.radians(pc.beta_pool_deg), T=fd.T0, mu=1e3, rho=750.0,
                         conv=0.0)
        self.t_b = 0.0
        self.records, self.pre_records = [], []
        self.lt = np.array([r["t_h"] for r in batch_log]) * 3600.0
        self.m0_comp = {k: float(sum(m_all[k] for _ in [0])) for k in fd.ORDER}
        self.t_end = float(self.lt[-1])

    # ---------------------------------------------------------- montagem
    @staticmethod
    def _random_fill(drum, slab, d, gen):
        """Posições aleatórias no tambor com raios a 50 % (crescem no assentamento), longe das aletas."""
        N = len(d)
        R = drum.R
        pts = np.zeros((N, 3))
        filled = 0
        while filled < N:
            k = (N - filled) * 3
            P = np.c_[gen.uniform(0, slab, k), gen.uniform(-R, R, k), gen.uniform(-R, R, k)]
            P = P[np.hypot(P[:, 1], P[:, 2]) < R - 0.06]
            if drum.n_lifters:
                dist, _, _ = lifter_contacts(drum, torch.as_tensor(P, dtype=torch.float64), 0.0, slab)
                P = P[(dist.min(1).values > 0.05).numpy()]
            take = min(len(P), N - filled)
            pts[filled:filled + take] = P[:take]
            filled += take
        # os maiores embaixo (assentamento mais rápido e sem pedaços presos no alto)
        order = np.argsort(pts[:, 2])
        big = np.argsort(-d)
        out = np.empty_like(pts)
        out[big] = pts[order]
        return out

    # ---------------------------------------------------------- estado da batelada
    def _log_at(self, t_b):
        i = int(np.clip(np.searchsorted(self.lt, t_b), 1, len(self.lt) - 1))
        a = (t_b - self.lt[i - 1]) / max(self.lt[i] - self.lt[i - 1], 1e-9)
        r0, r1 = self.log[i - 1], self.log[i]
        return {k: (1 - a) * r0[k] + a * r1[k] for k in r0 if isinstance(r0[k], (int, float))}

    def _u(self, row, keys):
        """Fração não reagida de um grupo de componentes."""
        m0 = sum(self.log[0].get(f"m_{k}", 0.0) for k in keys)
        return sum(row.get(f"m_{k}", 0.0) for k in keys) / m0 if m0 > 0 else 1.0

    def update_state(self, t_b):
        """Atualiza massa, raio, fração fundida, pegajosidade e a poça para o instante t_b da batelada."""
        pc = self.pc
        self.t_b = t_b
        row = self._log_at(t_b)
        T_bed = row["T_carga"] + 273.15
        lab = self.label
        Tp = T_bed + self.dT
        self.Tp = Tp
        u_w = self._u(row, ["H2O"])
        m_new = torch.zeros_like(self.m0p)
        vol_ratio = torch.ones_like(self.m0p)
        stick = torch.zeros_like(self.m0p)
        f_m = torch.zeros_like(self.m0p)
        charf = torch.zeros_like(self.m0p)
        Tp_np = Tp.cpu().numpy()
        for li, (name, comps, _, _) in enumerate(MATERIALS):
            sel = (lab == li)
            if not bool(sel.any()):
                continue
            selnp = sel.cpu().numpy()
            if name in MELTERS:
                c = fd.COMPONENTS[MELTERS[name]]
                u = self._u(row, [MELTERS[name]])
                fm = torch.as_tensor(fd.melt_fraction(c, Tp_np[selnp]), dtype=self.ft, device=self.dev)
                ratio = self.piece_rho[name] / self.dense_rho[name]
                f_m[sel] = fm
                vol_ratio[sel] = u * ((1 - fm) + fm * ratio)
                m_new[sel] = self.m0p[sel] * (u + self.moist * u_w)
                stick[sel] = ((fm - 0.03) / 0.45).clamp(0.0, 1.0)
            elif name == "organico":
                u = self._u(row, ["CELL"])
                ych = 0.29
                m_new[sel] = self.m0p[sel] * (u + ych * (1 - u) + self.moist * u_w)
                vol_ratio[sel] = u + (1 - u) * pc.shrink_char["organico"]
                charf[sel] = ych * (1 - u) / max(u + ych * (1 - u), 1e-6)
            elif name == "borracha":
                u = self._u(row, ["RUBa", "RUBb", "RUBc"])
                m_new[sel] = self.m0p[sel] * (0.6 * u + 0.4 + self.moist * u_w)
                vol_ratio[sel] = u + (1 - u) * pc.shrink_char["borracha"]
                charf[sel] = 0.4 / max(0.6 * u + 0.4, 1e-6) * (1 - u) + 0.0
            elif name == "pvc":
                m0 = self.log[0].get("m_PVC", 1e-9)
                mP, mR = row.get("m_PVC", 0.0), row.get("m_PVCr", 0.0)
                consumed_r = max(0.417 * (m0 - mP) - mR, 0.0)
                frac = (mP + mR + 0.25 * consumed_r) / m0
                m_new[sel] = self.m0p[sel] * (frac + self.moist * u_w)
                done = 1 - mP / m0
                vol_ratio[sel] = 1 - done * (1 - pc.shrink_char["pvc"])
                charf[sel] = min(1.0, (mR + 0.25 * consumed_r) / max(mP + mR + 0.25 * consumed_r, 1e-9))
            elif name == "areia":
                m_new[sel] = self.m0p[sel]
        # grânulos de carvão já nascidos: massa e raio fixos
        gran = lab == len(MATERIALS)
        m_new[gran] = self.m[gran]
        charf[gran] = 1.0
        # ---- coalescência na poça: pedaços fundidos saem do DEM e entram no inventário
        newly = (f_m >= pc.f_merge) & (self.active > 0) & (~gran)
        if bool(newly.any()):
            for name, comp in MELTERS.items():
                li = NAMES.index(name)
                s = newly & (lab == li)
                if bool(s.any()):
                    u = self._u(row, [comp])
                    self.pool_m0[comp] += float(self.m0p[s].sum()) * u / max(u, 1e-9) if u > 0 else 0.0
            self.active[newly] = 0.0
            self.v[newly] = 0.0
            self.w[newly] = 0.0
            self.merged |= newly
            self._dirty = True
        # ---- atualiza massa e raio (só ativos)
        act = (self.active > 0) & (~gran)
        r_new = self.r0 * vol_ratio.clamp(min=1e-3) ** (1.0 / 3.0)
        self.r_final = torch.where(act, r_new, self.r_final)
        self.r = torch.where(act, r_new, self.r)
        V = 4.0 / 3.0 * math.pi * self.r ** 3
        m_eff = torch.where(act, m_new.clamp(min=1e-6), self.m)
        self.m = m_eff
        self.rho_p = torch.where(act, self.m / V, self.rho_p if torch.is_tensor(self.rho_p) else self.m / V)
        self.I = 0.4 * self.m * self.r ** 2
        self.stick = torch.where(act, stick, torch.zeros_like(stick))
        self.f_m, self.charf = f_m, charf
        # ---- poça: massa por polímero não craqueado, volume, viscosidade
        mass_pool, vol_pool, char_made = 0.0, 0.0, 0.0
        for comp, m0eq in self.pool_m0.items():
            if m0eq <= 0:
                continue
            u = self._u(row, [comp])
            # m0eq foi guardado como massa no momento da fusão / u(t_fusão) ≈ massa inicial equivalente
            m = m0eq * u
            mass_pool += m
            vol_pool += m / fd.COMPONENTS[comp].rho_dense
            char_made += m0eq * (1 - u) * fd.COMPONENTS[comp].yields.get("CHAR", 0.0)
        conv_po = 1.0 - sum(self.pool_m0[c] * self._u(row, [c]) for c in self.pool_m0) / max(sum(self.pool_m0.values()), 1e-9)
        area = vol_pool / pc.slab
        F = area / (math.pi * self.drum.R ** 2)
        self.pool.update(area=area, F=F, eps=fill_half_angle(F) if F > 1e-5 else 0.0, T=T_bed,
                         mu=float(melt_viscosity(T_bed, conv_po)), rho=mass_pool / max(vol_pool, 1e-12) if vol_pool > 0 else 750.0,
                         conv=conv_po, mass=mass_pool)
        # ---- grânulos de carvão nascem na poça
        m_g = pc.char_rho * math.pi / 6 * pc.char_d ** 3
        n_new = int((char_made - self.char_spawned) / m_g)
        if n_new > 0 and self.pool["eps"] > 0:
            free = torch.nonzero((self.active == 0) & gran & (~self.merged)).flatten()
            n_new = min(n_new, len(free))
            if n_new > 0:
                idx = free[:n_new]
                self._spawn(idx, m_g)
                self.char_spawned += n_new * m_g
        if getattr(self, "_dirty", False):
            self._rebuild()
            self._dirty = False

    def _spawn(self, idx, m_g):
        pc, R = self.pc, self.drum.R
        n = len(idx)
        gen = self.gen
        eps, beta = self.pool["eps"], self.pool["beta"]
        nrm = np.array([-math.sin(beta), math.cos(beta)])
        d_surf = -R * math.cos(eps)
        pts = []
        while len(pts) < n:
            y, z = gen.uniform(-R, R, 2)
            dd = y * nrm[0] + z * nrm[1]
            if math.hypot(y, z) < R - pc.char_d and d_surf - 0.25 * R * (1 - math.cos(eps)) < dd < d_surf - 0.5 * pc.char_d:
                pts.append((gen.uniform(0, pc.slab), y, z))
        P = torch.as_tensor(np.array(pts), dtype=self.ft, device=self.dev)
        self.x[idx] = P
        Om = self.omega * pc.flow_frac
        self.v[idx] = torch.stack([torch.zeros(n, device=self.dev), -Om * P[:, 2], Om * P[:, 1]], -1)
        self.w[idx] = 0.0
        self.r[idx] = self.r_final[idx] = self.r0[idx] = 0.5 * pc.char_d
        self.m[idx] = m_g
        self.I[idx] = 0.4 * m_g * (0.5 * pc.char_d) ** 2
        self.active[idx] = 1.0
        self._dirty = True

    # ---------------------------------------------------------- forças da poça
    def _post_step(self, dt):
        p = self.pool
        if p.get("area", 0.0) <= 1e-6:
            return
        R = self.drum.R
        eps, beta = p["eps"], p["beta"]
        nrm = torch.tensor([-math.sin(beta), math.cos(beta)], dtype=self.ft, device=self.dev)
        depth = -R * math.cos(eps) - (self.x[:, 1] * nrm[0] + self.x[:, 2] * nrm[1])    # >0 abaixo da superfície
        sub = ((depth / self.r.clamp(min=1e-3)) * 0.5 + 0.5).clamp(0.0, 1.0) * self.active
        if not bool((sub > 0).any()):
            return
        V = 4.0 / 3.0 * math.pi * self.r ** 3
        # empuxo
        self.v[:, 2] += (p["rho"] * V * sub * G / self.m.clamp(min=1e-9)) * dt
        # arrasto de Stokes: relaxação exata para a velocidade do fundido
        Om = self.omega * self.pc.flow_frac
        vf = torch.stack([torch.zeros_like(self.r), -Om * self.x[:, 2], Om * self.x[:, 1]], -1)
        tau = self.m / (6 * math.pi * p["mu"] * self.r.clamp(min=1e-3) * sub.clamp(min=1e-6))
        a = torch.exp(-dt / tau)[:, None]
        a = torch.where(sub[:, None] > 0, a, torch.ones_like(a))
        self.v = vf + (self.v - vf) * a
        self.w = self.w * a

    # ---------------------------------------------------------- marcha
    def frame_state(self) -> dict:
        f = self.frame()
        act = self.active > 0
        f.update(m_dem=float(self.m[act].sum()), fill_dem=self.bed_fill())
        f.update(t_b=self.t_b, f_m=(self.f_m.clamp(0, 1) * 255).byte().cpu().numpy(),
                 charf=(self.charf.clamp(0, 1) * 255).byte().cpu().numpy(), Tp=self.Tp.half().cpu().numpy(),
                 pool={k: float(v) for k, v in self.pool.items()})
        return f

    def run_batch(self, verbose=True):
        """Assenta, grava o trecho frio e percorre a batelada inteira com o relógio comprimido."""
        pc = self.pc
        self.settle(1.0)
        self.update_state(0.0)
        self.spin_up(pc.rpm)
        T_rev = 60.0 / pc.rpm
        t_pre = pc.pre_rev * T_rev
        self.run(t_pre, frame_dt=t_pre / pc.pre_frames, on_frame=lambda d: self.pre_records.append(d.frame_state()))
        self.reset_stats()
        T_run = pc.n_rev * T_rev
        n_upd = max(int(round(pc.upd_dt / self.dt)), 1)
        frame_every = T_run / pc.frames
        t0 = self.t
        next_frame = t0
        k = 0
        import time as _t
        wall0 = _t.time()
        while self.t - t0 < T_run:
            t_b = self.t_end * (self.t - t0) / T_run
            self.update_state(t_b)
            self.step(n_upd)
            if self.t >= next_frame:
                self.records.append(self.frame_state())
                next_frame += frame_every
            k += 1
            if verbose and k % max(int(T_run / pc.upd_dt / 10), 1) == 0:
                p = self.pool
                print(f"  DEM fase: batelada {t_b / 3600:4.1f} h  T {self.Tp.mean() - 273.15:5.0f} °C  pedaços ativos "
                      f"{int(self.active.sum())}  poça {p.get('mass', 0.0):6.1f} kg (η {p['mu']:.2g} Pa s)  "
                      f"grânulos {int(((self.label == len(MATERIALS)) & (self.active > 0)).sum())}  "
                      f"[{_t.time() - wall0:5.0f} s]", flush=True)
        self.update_state(self.t_end)
        self.records.append(self.frame_state())
        return self.records

    def bed_fill(self):
        """Enchimento equivalente do DEM (pedaços ativos / empacotamento + poça) para comparar com a batelada."""
        act = self.active > 0
        V = float((4.0 / 3.0 * math.pi * self.r[act] ** 3).sum()) / self.pc.phi_pack
        return (V / self.pc.slab + self.pool.get("area", 0.0)) / (math.pi * self.drum.R ** 2)

    def describe(self):
        counts = {NAMES[i]: int((self.label == i).sum()) for i in range(len(MATERIALS))}
        return (f"DEM com mudança de fase: {self.n_act0} pedaços na fatia de {self.pc.slab:.2f} m ("
                + ", ".join(f"{k} {v}" for k, v in counts.items()) + f"), {self.N - self.n_act0} reservados "
                f"para carvão; Δt = {self.dt * 1e3:.2f} ms; {self.pc.n_rev:.0f} voltas a {self.pc.rpm:.1f} rpm "
                "para a batelada inteira")
