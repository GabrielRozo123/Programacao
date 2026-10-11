"""Carga do tambor por elementos discretos (DEM) na GPU.

Esferas macias (mola-amortecedor linear na normal; mola tangencial com histórico e limite de Coulomb,
Cundall & Strack 1979; resistência ao rolamento de torque constante, modelo A de Ai et al. 2011) num tambor
que gira com aletas. As paredes (casco, tampas e aletas) entram como superfícies analíticas que giram com o
tambor; a velocidade da parede no ponto de contato é Ω x̂ × p.

O objetivo não é seguir 6–8 h de batelada (impossível em DEM), e sim:
  * mostrar o movimento real da carga (leito rolante, cortinas das aletas) para o vídeo;
  * medir as grandezas que o modelo térmico da batelada precisa: ângulo dinâmico, arco de parede coberto,
    tempo de contato com a parede (modelo de penetração), fração em queda livre nas cortinas, espessura
    da camada ativa, taxa de mistura (índice de Lacey) e torque/potência de acionamento.

Rigidez reduzida: k_n é escolhido para uma sobreposição de ~1,5 % do diâmetro no fundo do leito, prática
usual para leitos grandes (Lommen et al. 2014); o regime transversal depende de Fr, do atrito e do
enchimento, não de k_n, enquanto a sobreposição for pequena.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np
import torch

from .geometry import Drum, bed_depth, lifter_contacts

G = 9.81


@dataclass
class DEMConfig:
    fill: float = 0.30           # fração do volume interno ocupada pela carga (volume aparente)
    d_mean: float = 0.09         # diâmetro médio dos pedaços [m]
    d_spread: float = 0.30       # diâmetros uniformes em d_mean·(1 ± d_spread)
    rho_bulk: float = 300.0      # massa específica aparente do leito [kg/m³]
    phi_pack: float = 0.58       # fração de sólidos do empacotamento aleatório de esferas
    e_n: float = 0.30            # coeficiente de restituição (pedaços de plástico e madeira: baixo)
    mu: float = 0.55             # atrito de deslizamento partícula–partícula
    mu_wall: float = 0.45        # atrito partícula–aço
    mu_r: float = 0.20           # resistência ao rolamento (adimensional, braço = μ_r·r)
    overlap: float = 0.010       # sobreposição alvo no fundo do leito / d (define k_n)
    kt_kn: float = 2.0 / 7.0     # razão das rigidezes tangencial/normal
    cohesion: float = 0.0        # força coesiva máxima / peso médio da partícula (fundido pegajoso)
    slab: float | None = None    # comprimento de uma fatia periódica em x [m]; None = tambor inteiro
    skin: float = 0.30           # pele da lista de vizinhos (fração de d_max)
    k_nb: int = 20               # vizinhos guardados por partícula
    dt_frac: float = 1.0 / 18.0  # Δt = t_contato·dt_frac
    check_every: int = 10        # passos entre verificações de reconstrução da lista
    device: str = "auto"
    seed: int = 0
    compile: bool = False        # torch.compile do passo (GPU); cai para o modo normal se falhar
    contact_time: float | None = None   # se dado: rigidez por par k = m_eff (π/t_c)²/(1 − β²) — duração do
    #                                     contato fixa, independente do tamanho (pedaços que encolhem/fundem)


@dataclass
class DEMStats:
    t: float = 0.0
    revs: float = 0.0
    beta_deg: float = float("nan")         # ângulo dinâmico do leito
    covered_frac: float = float("nan")     # fração do perímetro do casco coberta pela carga
    wall_contact_s: float = float("nan")   # duração média de um contato partícula–casco
    passive_contact_s: float = float("nan")  # tempo de passagem do leito sobre a parede: 2ε/Ω
    airborne_frac: float = float("nan")    # fração em queda livre (cortinas)
    active_layer_m: float = float("nan")   # espessura da camada ativa
    lacey: float = float("nan")            # índice de mistura (0 segregado, 1 aleatório)
    torque_Nm: float = float("nan")        # torque de acionamento médio
    power_W: float = float("nan")
    max_overlap: float = float("nan")      # maior sobreposição / d

    def as_dict(self):
        return dict(self.__dict__)


class DrumDEM:
    def __init__(self, drum: Drum, cfg: DEMConfig, labels_frac: dict | None = None, init: dict | None = None):
        self.drum, self.cfg = drum, cfg
        dev = cfg.device
        if dev == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.dev = torch.device(dev)
        self.ft = torch.float32
        gen = np.random.default_rng(cfg.seed)
        self.periodic = cfg.slab is not None
        self.Lx = cfg.slab if self.periodic else drum.L

        # ---- partículas: tamanhos, massas e posições iniciais numa rede acima do leito final
        t = lambda a: torch.as_tensor(np.asarray(a), dtype=self.ft, device=self.dev)  # noqa: E731
        d_lo, d_hi = cfg.d_mean * (1 - cfg.d_spread), cfg.d_mean * (1 + cfg.d_spread)
        Vmean = math.pi / 6 * (d_hi ** 4 - d_lo ** 4) / (4 * (d_hi - d_lo)) if d_hi > d_lo else math.pi / 6 * cfg.d_mean ** 3
        A = math.pi * drum.R ** 2
        if init is not None:          # partículas dadas (DEM com mudança de fase): posições, diâmetros, densidades
            pts, d = np.asarray(init["x"], float), np.asarray(init["d"], float)
            N = len(pts)
            d_hi = float(d.max())
            self.rho_p = t(init["rho"])
            grow0 = init.get("grow0", 0.5)
            active = np.asarray(init.get("active", np.ones(N, bool)))
        else:
            N = int(round(cfg.phi_pack * cfg.fill * A * self.Lx / Vmean))
            pts = self._lattice(N, gen)
            N = len(pts)
            d = gen.uniform(d_lo, d_hi, N)
            self.rho_p = cfg.rho_bulk / cfg.phi_pack
            grow0 = min(1.0, cfg.d_mean / d_hi)
            active = np.ones(N, bool)
        self.d_max = d_hi
        self.N = N
        self.x = t(pts)
        self.v = torch.zeros_like(self.x)
        self.w = torch.zeros_like(self.x)
        self.r_final = t(0.5 * d)
        self.grow0 = grow0
        self.r = self.r_final * self.grow0
        self.active = t(active.astype(np.float32))
        self.stick = torch.zeros(N, dtype=self.ft, device=self.dev)   # pegajosidade (0–1) de cada partícula
        self._set_mass()
        # rótulos de material (cores) e de mistura (lado inicial)
        if init is not None:
            self.label_names = list(init["names"])
            self.label = torch.as_tensor(np.asarray(init["label"]), device=self.dev, dtype=torch.long)
        elif labels_frac:
            keys = list(labels_frac)
            p = np.array([labels_frac[k] for k in keys], float); p /= p.sum()
            self.label_names = keys
            self.label = torch.as_tensor(gen.choice(len(keys), N, p=p), device=self.dev)
        else:
            self.label_names = ["carga"]
            self.label = torch.zeros(N, dtype=torch.long, device=self.dev)

        # ---- contato: rigidez para a sobreposição alvo no fundo do leito (ou duração de contato fixa)
        lne = math.log(max(cfg.e_n, 1e-4))
        self.beta_n = -lne / math.sqrt(math.pi ** 2 + lne ** 2)
        self.tc_mode = cfg.contact_time is not None
        if self.tc_mode:
            t_c = cfg.contact_time
            self.w2 = (math.pi / t_c) ** 2 / (1 - self.beta_n ** 2)
            self.kn = self.kt = None
            self.f_coh = 0.0
        else:
            H = bed_depth(cfg.fill, drum.R)
            self.kn = cfg.rho_bulk * G * H * cfg.d_mean / cfg.overlap
            self.kt = cfg.kt_kn * self.kn
            m_mean = float(np.mean(np.asarray(self.rho_p.cpu() if torch.is_tensor(self.rho_p) else self.rho_p))) * Vmean
            t_c = math.pi * math.sqrt(0.5 * d_lo ** 3 / cfg.d_mean ** 3 * m_mean / self.kn)
            self.f_coh = cfg.cohesion * m_mean * G
        self.t_contact = t_c
        self.dt = cfg.dt_frac * t_c
        self.t, self.theta = 0.0, 0.0
        self.omega = 0.0          # começa parado (assentamento)
        self.damping = 0.0        # amortecimento global (só no assentamento)
        self.steps = 0
        # ---- listas de vizinhos e históricos tangenciais
        self.cell = self.d_max * (1 + cfg.skin)
        self.lo = t([0.0, -drum.R - self.cell, -drum.R - self.cell])
        hi = np.array([self.Lx, drum.R + self.cell, drum.R + self.cell])
        self.dims = np.maximum(np.ceil((hi - self.lo.cpu().numpy()) / self.cell).astype(int), 1)
        csize = np.full(3, self.cell)
        if self.periodic:   # células inteiras ao longo da fatia periódica (sem célula parcial na emenda)
            self.dims[0] = int(self.Lx // self.cell)
            if self.dims[0] < 3:
                raise ValueError("fatia periódica curta demais para a lista de vizinhos (mín. 3 células)")
            csize[0] = self.Lx / self.dims[0]
        self.csize = t(csize)
        self.nwall = 1 + (0 if self.periodic else 2) + drum.n_lifters * len(drum.lifter_boxes())
        self.xi = torch.zeros(N, cfg.k_nb, 3, device=self.dev)
        self.xi_w = torch.zeros(N, self.nwall, 3, device=self.dev)
        self._rebuild()
        # ---- estatísticas
        self.reset_stats()
        self._step_fn = self._step
        if cfg.compile and self.dev.type == "cuda":
            try:
                self._step_fn = torch.compile(self._step, dynamic=False)
            except Exception:   # noqa: BLE001
                self._step_fn = self._step

    # ------------------------------------------------------------ montagem
    def _set_mass(self):
        V = 4.0 / 3.0 * math.pi * self.r ** 3
        self.m = self.rho_p * V
        self.I = 0.4 * self.m * self.r ** 2

    def _lattice(self, N, gen):
        """Rede cúbica dentro do tambor, longe das aletas, preenchida de baixo para cima."""
        dr, a = self.drum, self.cfg.d_mean * 1.03     # rede no diâmetro médio: os raios crescem no assentamento
        nx = max(int(self.Lx / a), 1)
        xs = (np.arange(nx) + 0.5) * self.Lx / nx
        ys = np.arange(-dr.R + a, dr.R - a / 2, a)
        X, Y, Z = np.meshgrid(xs, ys, ys, indexing="ij")
        P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
        P = P[np.hypot(P[:, 1], P[:, 2]) < dr.R - 0.55 * a]
        if dr.n_lifters:
            dist, _, _ = lifter_contacts(dr, torch.as_tensor(P, dtype=torch.float64), 0.0,
                                         self.Lx if self.periodic else None)
            P = P[(dist.min(1).values > 0.6 * a).numpy()]
        P = P[np.argsort(P[:, 2] + 1e-3 * gen.random(len(P)), kind="stable")][:N]
        P += gen.uniform(-0.03, 0.03, P.shape) * a
        return P

    # ------------------------------------------------------------ vizinhança
    def _wrap(self, dx):
        if self.periodic:
            dx = dx.clone()
            dx[..., 0] -= self.Lx * torch.round(dx[..., 0] / self.Lx)
        return dx

    def _rebuild(self):
        x, c, dims = self.x, self.cell, self.dims
        idx = ((x - self.lo) / self.csize).floor().long()
        for a in range(3):
            idx[:, a] = idx[:, a].clamp(0, int(dims[a]) - 1)
        cid = (idx[:, 0] * int(dims[1]) + idx[:, 1]) * int(dims[2]) + idx[:, 2]
        order = torch.argsort(cid)
        cs = cid[order]
        start = torch.searchsorted(cs, cs)
        rank = torch.arange(self.N, device=self.dev) - start
        Kc = int(rank.max().item()) + 1
        ncell = int(np.prod(dims))
        table = torch.full((ncell, Kc), -1, dtype=torch.long, device=self.dev)
        table[cs, rank] = order
        off = torch.stack(torch.meshgrid(*[torch.arange(-1, 2, device=self.dev)] * 3, indexing="ij"), -1).reshape(-1, 3)
        nid = idx[:, None, :] + off[None]
        ok = torch.ones(nid.shape[:2], dtype=torch.bool, device=self.dev)
        if self.periodic:
            nid[..., 0] = torch.remainder(nid[..., 0], int(dims[0]))
        for a in range(3):
            ok &= (nid[..., a] >= 0) & (nid[..., a] < int(dims[a]))
        ncid = (nid[..., 0].clamp(0, int(dims[0]) - 1) * int(dims[1]) + nid[..., 1].clamp(0, int(dims[1]) - 1)) \
            * int(dims[2]) + nid[..., 2].clamp(0, int(dims[2]) - 1)
        cand = table[ncid]                                   # [N, 27, Kc]
        cand = torch.where(ok[..., None], cand, torch.full_like(cand, -1)).reshape(self.N, -1)
        j = cand.clamp(min=0)
        dx = self._wrap(x[j] - x[:, None])
        dist = dx.norm(dim=-1)
        ar = torch.arange(self.N, device=self.dev)[:, None]
        valid = (cand >= 0) & (cand != ar) & (dist < self.r[:, None] + self.r[j] + self.cfg.skin * self.d_max)
        valid &= (self.active[:, None] > 0) & (self.active[j] > 0)
        key = torch.where(valid, dist, torch.full_like(dist, float("inf")))
        K = self.cfg.k_nb
        nmax = int(valid.sum(1).max().item())
        if nmax > K:      # cresce a lista (e o histórico) em vez de perder contatos
            grow = nmax + 4 - K
            K = self.cfg.k_nb = nmax + 4
            if hasattr(self, "nb"):
                self.nb = torch.cat([self.nb, torch.full((self.N, grow), -1, dtype=self.nb.dtype, device=self.dev)], 1)
            self.xi = torch.cat([self.xi, torch.zeros(self.N, grow, 3, device=self.dev)], 1)
        val, pos = torch.topk(key, K, dim=1, largest=False)
        nb = torch.gather(cand, 1, pos)
        nb = torch.where(torch.isfinite(val), nb, torch.full_like(nb, -1))
        # transfere o histórico tangencial dos pares que continuam na lista
        if hasattr(self, "nb"):
            same = nb[:, :, None] == self.nb[:, None, :]
            same &= nb[:, :, None] >= 0
            has = same.any(-1)
            src = same.float().argmax(-1)
            xi = torch.gather(self.xi, 1, src[..., None].expand(-1, -1, 3))
            self.xi = torch.where(has[..., None], xi, torch.zeros_like(xi))
        self.nb = nb
        self.x_ref = x.clone()

    # ------------------------------------------------------------ contato
    def _law(self, delta, n, u, m_eff, xi, kn, kt, mu, rad, dt, f_coh):
        """Força na partícula i (normal + tangencial), torque tangencial e novo histórico.

        delta: sobreposição; n: normal unitária de i para o outro corpo; u: velocidade do ponto de contato
        de i relativa ao outro corpo; rad: braço (raio de i até o ponto de contato)."""
        touch = delta > 0
        un = (u * n).sum(-1)
        gn = 2 * self.beta_n * torch.sqrt(m_eff * kn)
        fn = kn * delta + gn * un
        fn = torch.where(touch, torch.maximum(fn, -f_coh * torch.ones_like(fn)), torch.zeros_like(fn))
        ut = u - un[..., None] * n
        xi = xi - (xi * n).sum(-1, keepdim=True) * n + ut * dt
        gt = 2 * self.beta_n * torch.sqrt(m_eff * kt)
        ktv = kt[..., None] if torch.is_tensor(kt) else kt
        ft = -ktv * xi - gt[..., None] * ut
        fmax = mu * (fn + f_coh).clamp(min=0)
        ftn = ft.norm(dim=-1).clamp(min=1e-12)
        slip = ftn > fmax
        ft = torch.where(slip[..., None], ft * (fmax / ftn)[..., None], ft)
        xi = torch.where(slip[..., None], -ft / ktv, xi)
        xi = torch.where(touch[..., None], xi, torch.zeros_like(xi))
        ft = torch.where(touch[..., None], ft, torch.zeros_like(ft))
        F = -fn[..., None] * n + ft
        Mt = torch.cross(rad[..., None] * n, ft, dim=-1)
        return F, Mt, fn, xi

    def _walls(self, x, theta):
        """Corpos de parede: casco, tampas (se não periódico) e caixas das aletas → (dist, n, p_c)."""
        dr = self.drum
        rho = torch.hypot(x[:, 1], x[:, 2]).clamp(min=1e-9)
        ey, ez = x[:, 1] / rho, x[:, 2] / rho
        zero = torch.zeros_like(rho)
        dists = [dr.R - rho]
        ns = [torch.stack([zero, ey, ez], -1)]
        ps = [torch.stack([x[:, 0], dr.R * ey, dr.R * ez], -1)]
        if not self.periodic:
            dists += [x[:, 0], dr.L - x[:, 0]]
            ns += [torch.stack([-torch.ones_like(rho), zero, zero], -1), torch.stack([torch.ones_like(rho), zero, zero], -1)]
            ps += [torch.stack([zero, x[:, 1], x[:, 2]], -1), torch.stack([zero + dr.L, x[:, 1], x[:, 2]], -1)]
        dist = torch.stack(dists, 1)
        n = torch.stack(ns, 1)
        p = torch.stack(ps, 1)
        if dr.n_lifters:
            dl, nl, pl = lifter_contacts(dr, x, theta, self.Lx if self.periodic else None)
            dist, n, p = torch.cat([dist, dl], 1), torch.cat([n, nl], 1), torch.cat([p, pl], 1)
        return dist, n, p

    def _step(self, x, v, w, xi, xi_w, nb, theta, omega, damping, dt):
        r, m, I = self.r, self.m, self.I
        valid = nb >= 0
        j = nb.clamp(min=0)
        dx = x[j] - x[:, None]
        if self.periodic:
            dx = torch.cat([dx[..., :1] - self.Lx * torch.round(dx[..., :1] / self.Lx), dx[..., 1:]], -1)
        dist = dx.norm(dim=-1).clamp(min=1e-9)
        n = dx / dist[..., None]
        delta = torch.where(valid, r[:, None] + r[j] - dist, torch.full_like(dist, -1.0))
        ai = (r[:, None] - 0.5 * delta.clamp(min=0))
        aj = (r[j] - 0.5 * delta.clamp(min=0))
        u = (v[:, None] + torch.cross(w[:, None].expand_as(n), ai[..., None] * n, dim=-1)) \
            - (v[j] + torch.cross(w[j], -aj[..., None] * n, dim=-1))
        m_eff = m[:, None] * m[j] / (m[:, None] + m[j])
        if self.tc_mode:
            kn_p = m_eff * self.w2
            kt_p = self.cfg.kt_kn * kn_p
            fc_p = self.cfg.cohesion * G * m_eff * torch.minimum(self.stick[:, None], self.stick[j])
        else:
            kn_p, kt_p, fc_p = self.kn, self.kt, self.f_coh
        Fp, Mp, fnp, xi = self._law(delta, n, u, m_eff, xi, kn_p, kt_p, self.cfg.mu, ai, dt, fc_p)
        r_eff = r[:, None] * r[j] / (r[:, None] + r[j])
        wrel = w[:, None] - w[j]
        # paredes
        dw_, nw, pw = self._walls(x, theta)
        delw = torch.where(self.active[:, None] > 0, r[:, None] - dw_, torch.full_like(dw_, -1.0))
        aw = r[:, None] - 0.5 * delw.clamp(min=0)
        vwall = torch.stack([torch.zeros_like(pw[..., 0]), -omega * pw[..., 2], omega * pw[..., 1]], -1)
        uw = v[:, None] + torch.cross(w[:, None].expand_as(nw), aw[..., None] * nw, dim=-1) - vwall
        mw_ = m[:, None].expand_as(delw)
        if self.tc_mode:
            kn_w = mw_ * self.w2
            kt_w = self.cfg.kt_kn * kn_w
            fc_w = 0.5 * self.cfg.cohesion * G * mw_ * self.stick[:, None]
        else:
            kn_w, kt_w, fc_w = self.kn, self.kt, self.f_coh
        Fw, Mw, fnw, xi_w = self._law(delw, nw, uw, mw_, xi_w, kn_w, kt_w, self.cfg.mu_wall, aw, dt, fc_w)
        # resistência ao rolamento (torque constante, regularizado perto de ω_rel = 0)
        mr = self.cfg.mu_r

        def roll(wr, fn, re):
            mag = mr * re * fn.clamp(min=0)
            wn = wr.norm(dim=-1)
            w_c = (mag * dt / I[:, None]).clamp(min=1e-6)
            return -mag[..., None] * wr / torch.maximum(wn, w_c)[..., None]
        w_wall = torch.stack([w[:, 0] - omega, w[:, 1], w[:, 2]], -1)
        Mr = roll(wrel, fnp, r_eff).sum(1) + roll(w_wall[:, None].expand_as(nw), fnw, r[:, None].expand_as(fnw)).sum(1)
        F = Fp.sum(1) + Fw.sum(1)
        F = F + torch.stack([torch.zeros_like(m), torch.zeros_like(m), -m * G * self.active], -1)
        M = Mp.sum(1) + Mw.sum(1) + Mr
        F = F - damping * m[:, None] * v
        M = M - damping * I[:, None] * w
        v = v + F / m[:, None] * dt
        w = w + M / I[:, None] * dt
        x = x + v * dt
        if self.periodic:
            x = torch.cat([torch.remainder(x[:, :1], self.Lx), x[:, 1:]], -1)
        # torque das partículas sobre o tambor (em torno de x): parede recebe −Fw
        tq = (pw[..., 1] * Fw[..., 2] - pw[..., 2] * Fw[..., 1]).sum()   # torque que o motor precisa dar
        ncont = (delta > 0).sum(1) + (delw > 0).sum(1)
        ovl = torch.maximum(delta.max(), delw.max())
        near_shell = delw[:, 0] > -0.1 * 2 * r     # junto ao casco (folga < 0,1 d): contato térmico
        return x, v, w, xi, xi_w, tq, ncont, near_shell, ovl

    # ------------------------------------------------------------ marcha
    def reset_stats(self):
        self._acc = dict(n=0, torque=0.0, air=0.0, covered=0.0, ovl=0.0, ep_sum=0.0, ep_n=0)
        self._contact_t0 = torch.full((self.N,), -1.0, device=self.dev)
        self._free = torch.zeros(self.N, device=self.dev)

    def step(self, nsteps: int = 1):
        dt = self.dt
        for _ in range(nsteps):
            sc = lambda a: torch.tensor(a, dtype=self.ft, device=self.dev)  # noqa: E731
            (self.x, self.v, self.w, self.xi, self.xi_w, tq, ncont, shell, ovl) = self._step_fn(
                self.x, self.v, self.w, self.xi, self.xi_w, self.nb, sc(self.theta), sc(self.omega),
                sc(self.damping), dt)
            self.t += dt
            self.theta += self.omega * dt
            self.steps += 1
            self._post_step(dt)
            # estatísticas (sem sincronizar com a CPU)
            a = self._acc
            a["n"] += 1
            a["torque"] = a["torque"] + tq
            self._free = torch.where(ncont == 0, self._free + dt, torch.zeros_like(self._free))
            a["air"] = a["air"] + ((self._free > 4 * self.t_contact).float() * self.active).sum() / self.active.sum().clamp(min=1)
            a["ovl"] = torch.maximum(torch.as_tensor(a["ovl"], device=self.dev), ovl)
            started = shell & (self._contact_t0 < 0)
            ended = (~shell) & (self._contact_t0 >= 0)
            dur = (self.t - self._contact_t0)
            a["ep_sum"] = a["ep_sum"] + torch.where(ended, dur, torch.zeros_like(dur)).sum()
            a["ep_n"] = a["ep_n"] + ended.sum()
            self._contact_t0 = torch.where(started, torch.full_like(dur, self.t),
                                           torch.where(ended, torch.full_like(dur, -1.0), self._contact_t0))
            if self.steps % self.cfg.check_every == 0:
                disp = self._wrap(self.x - self.x_ref).norm(dim=-1).max()
                if float(disp) > 0.5 * self.cfg.skin * self.d_max:
                    self._rebuild()

    def _post_step(self, dt):
        """Gancho para forças externas aplicadas após a integração (poça de fundido no DEM com mudança de fase)."""
        return None

    def settle(self, seconds: float = 2.0, damping: float = 4.0):
        """Assentamento com o tambor parado e amortecimento global; os raios crescem até o valor final
        nos primeiros 60 % (a rede inicial usa o diâmetro médio, sem sobreposição)."""
        om, self.omega, self.damping = self.omega, 0.0, damping
        for i in range(10):
            f = self.grow0 + (1 - self.grow0) * min(1.0, (i + 1) / 6)
            self.r = self.r_final * f
            self._set_mass()
            self.run(seconds / 10)
        self.omega, self.damping = om, 0.0
        self.v.zero_(); self.w.zero_()
        self.reset_stats()

    def spin_up(self, rpm: float | None = None):
        self.omega = self.drum.omega if rpm is None else 2 * math.pi * rpm / 60

    def run(self, seconds: float, frame_dt: float | None = None, on_frame=None, verbose: bool = False):
        n = max(int(round(seconds / self.dt)), 1)
        every = max(int(round(frame_dt / self.dt)), 1) if frame_dt else n + 1
        t0, done = time.time(), 0
        while done < n:
            k = min(every - (self.steps % every) if frame_dt else n - done, n - done)
            self.step(k)
            done += k
            if frame_dt and self.steps % every == 0 and on_frame is not None:
                on_frame(self)
            if verbose and (done == n or done % max(n // 10, 1) < k):
                print(f"  DEM t = {self.t:7.2f} s  ({done}/{n} passos, {time.time() - t0:5.1f} s de relógio)", flush=True)

    # ------------------------------------------------------------ diagnóstico
    def frame(self) -> dict:
        """Estado leve para renderização (float16 na CPU)."""
        return dict(t=self.t, theta=self.theta, x=self.x.half().cpu().numpy(),
                    speed=self.v.norm(dim=-1).half().cpu().numpy(), r=self.r.half().cpu().numpy(),
                    active=self.active.cpu().numpy() > 0)

    def surface_angle(self):
        """Ângulo dinâmico: reta ajustada ao topo do leito no miolo da corda (partículas fora das aletas)."""
        x = self.x.cpu().numpy().astype(float)
        dr = self.drum
        rho = np.hypot(x[:, 1], x[:, 2])
        inner = rho < dr.R - dr.lifter_h - self.d_max if dr.n_lifters else rho < dr.R
        y, z = x[inner, 1], x[inner, 2]
        edges = np.linspace(-dr.R, dr.R, 41)
        k = np.digitize(y, edges)
        yc, zt = [], []
        for b in range(1, len(edges)):
            zz = z[k == b]
            if len(zz) >= 5:
                yc.append(0.5 * (edges[b - 1] + edges[b])); zt.append(np.sort(zz)[-3:].mean())
        yc, zt = np.array(yc), np.array(zt)
        if len(yc) < 6:
            return float("nan"), None
        lo, hi = np.quantile(yc, [0.25, 0.75])
        sel = (yc >= lo) & (yc <= hi)
        b, a = np.polyfit(yc[sel], zt[sel], 1)
        return float(np.degrees(np.arctan(b))), (a, b)

    def active_layer(self, line):
        """Espessura da camada ativa: profundidade, abaixo da superfície, onde a velocidade ao longo da
        encosta troca de sinal (desce na camada ativa, sobe com a parede no leito passivo)."""
        if line is None:
            return float("nan")
        a, b = line
        x = self.x.cpu().numpy().astype(float)
        v = self.v.cpu().numpy().astype(float)
        t = np.array([1.0, b]) / math.hypot(1.0, b)        # direção da encosta (sobe para +y se b > 0)
        nrm = np.array([-t[1], t[0]])                        # normal para cima
        yz = x[:, 1:]
        depth = (np.array([0.0, a]) - yz) @ nrm              # >0 abaixo da superfície
        s = yz @ t
        mid = np.abs(s) < 0.25 * self.drum.R
        vs = v[:, 1:] @ t
        bins = np.arange(0, 0.8 * self.drum.R, 0.5 * self.cfg.d_mean)
        prof = []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = mid & (depth >= lo) & (depth < hi)
            prof.append(np.mean(vs[m]) if m.sum() > 3 else np.nan)
        prof = np.array(prof)
        down = -np.sign(b) if b != 0 else -1.0                # a carga desce na direção −sinal(b)
        flow = prof * down
        for i in range(1, len(flow)):
            if np.isfinite(flow[i]) and np.isfinite(flow[i - 1]) and flow[i - 1] > 0 >= flow[i]:
                return float(bins[i - 1] + (bins[i] - bins[i - 1]) * flow[i - 1] / (flow[i - 1] - flow[i]))
        return float("nan")

    def lacey(self, labels: np.ndarray, ncell: int = 12) -> float:
        """Índice de Lacey na seção transversal (amostras numa grade y–z)."""
        x = self.x.cpu().numpy()
        p = labels.mean()
        R = self.drum.R
        iy = np.clip(((x[:, 1] + R) / (2 * R) * ncell).astype(int), 0, ncell - 1)
        iz = np.clip(((x[:, 2] + R) / (2 * R) * ncell).astype(int), 0, ncell - 1)
        key = iy * ncell + iz
        cnt = np.bincount(key, minlength=ncell * ncell)
        s1 = np.bincount(key, weights=labels, minlength=ncell * ncell)
        ok = cnt >= 8
        if ok.sum() < 3 or p in (0.0, 1.0):
            return float("nan")
        frac = s1[ok] / cnt[ok]
        S2 = np.average((frac - p) ** 2, weights=cnt[ok])
        S0 = p * (1 - p)
        Sr = S0 / cnt[ok].mean()
        return float(np.clip((S0 - S2) / (S0 - Sr), 0.0, 1.0))

    def stats(self) -> DEMStats:
        a = self._acc
        n = max(a["n"], 1)
        st = DEMStats(t=self.t, revs=self.theta / (2 * math.pi))
        beta, line = self.surface_angle()
        st.beta_deg = beta
        st.active_layer_m = self.active_layer(line)
        st.torque_Nm = float(a["torque"]) / n if a["n"] else float("nan")
        st.power_W = st.torque_Nm * self.omega
        st.airborne_frac = float(a["air"]) / n if a["n"] else float("nan")
        st.max_overlap = float(a["ovl"]) / self.cfg.d_mean
        st.wall_contact_s = float(a["ep_sum"]) / max(int(a["ep_n"]), 1) if int(a["ep_n"]) else float("nan")
        # arco coberto: setores de 10° com ao menos uma partícula encostada no casco (folga < 2 cm)
        x = self.x.cpu().numpy()
        r = self.r.cpu().numpy()
        rho = np.hypot(x[:, 1], x[:, 2])
        near = (rho > self.drum.R - r - 0.02) & (self.active.cpu().numpy() > 0)
        if near.any():
            phi = np.arctan2(x[near, 2], x[near, 1])
            h, _ = np.histogram(phi, bins=36, range=(-math.pi, math.pi))
            st.covered_frac = float((h >= 1).mean())
            if self.omega > 0:
                st.passive_contact_s = st.covered_frac * 2 * math.pi / self.omega
        return st

    def kinetic_energy(self) -> float:
        return float(0.5 * (self.m * (self.v ** 2).sum(-1)).sum() + 0.5 * (self.I * (self.w ** 2).sum(-1)).sum())

    def describe(self) -> str:
        d = self.drum
        return (f"DEM: {self.N} pedaços de {self.cfg.d_mean * 1000:.0f} mm (±{self.cfg.d_spread * 100:.0f} %), "
                f"tambor {d.D:.2f} m × {self.Lx:.2f} m{' (fatia periódica)' if self.periodic else ''}, "
                f"{d.n_lifters} aletas, enchimento {self.cfg.fill * 100:.0f} %, k_n = {self.kn:.3g} N/m, "
                f"Δt = {self.dt * 1e3:.3f} ms, Fr = {d.froude():.2e}")
