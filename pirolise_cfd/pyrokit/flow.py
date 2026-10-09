"""Escoamento do fundido no tanque agitado (PyTorch; GPU se houver).

Formulação:
  * Navier–Stokes incompressível no referencial que gira com o agitador (Ω = ω ẑ): o agitador fica
    parado e a parede do vaso gira com velocidade −Ω × r. Num vaso sem chicanas, com paredes de
    revolução, o problema é estacionário nesse referencial; Coriolis −2Ω × u explícito, centrífuga
    absorvida na pressão modificada (densidade constante);
  * viscosidade variável μ(γ̇, …) de fluido newtoniano generalizado, na forma ∇·(μ∇u) + (∇u)ᵀ·∇μ,
    mais a viscosidade turbulenta do modelo RANS quando houver;
  * malha MAC uniforme; advecção upwind de 3ª ordem; RK2 (SSP) com projeção em cada estágio;
  * fronteiras imersas por forçamento direto (fração sólida suavizada em 1 célula) para o vaso e o
    agitador, aplicado antes e depois de cada projeção; o torque no agitador vem do impulso total do
    forçamento (que inclui a pressão) e a potência é P = ω·T;
  * Poisson direto pela diagonalização dos operadores 1D (Neumann em todas as faces).

Fundo em z = 0 (parede que gira, ou deslizamento no caso de verificação) e topo em z = H_L com
deslizamento (superfície livre plana).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
import scipy.linalg
import torch

from .geometry import Tank
from .ops import avg, cgrad, diff, extend_into_solid, pad, sl, to_faces


@dataclass
class FlowConfig:
    n_diam: int = 64             # células ao longo do diâmetro do vaso
    rho: float = 750.0           # massa específica do fundido [kg/m³]
    cfl: float = 0.45
    dt_max: float = 0.02
    bottom: str = "wall"         # "wall" (parede que gira) ou "slip" (verificação)
    upwind: float = 0.0          # mistura com upwind de 1ª ordem (0 = 3ª ordem pura)
    mu_max: float = 1e9          # teto de viscosidade [Pa s] (estabilidade do passo explícito)
    spin0: float = 0.0           # partida: núcleo girando a spin0·Ω no referencial fixo (0 = repouso)
    vessel_ibm: str = "diffuse"  # "diffuse" (sem deslizamento, laminar) ou "wallfn" (lei de parede, RANS)
    advection: str = "conservative"  # "conservative" (fluxos, conserva momento) ou "advective" (u·∇u)
    device: str = "auto"
    dtype: str = "float32"


class TankFlow:
    def __init__(self, tank: Tank, cfg: FlowConfig, mu_fn=None):
        """mu_fn(gamma_dot) → μ [Pa s] nos centros (tensor); None = newtoniano com μ = 1 Pa s."""
        self.tank, self.cfg = tank, cfg
        dev = cfg.device
        if dev == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.dev = torch.device(dev)
        self.ft = getattr(torch, cfg.dtype)
        t = lambda a: torch.as_tensor(np.asarray(a, dtype=np.float64), dtype=self.ft, device=self.dev)  # noqa: E731
        self._t = t
        self.mu_fn = mu_fn if mu_fn is not None else (lambda g: torch.ones_like(g))
        self.rho = cfg.rho
        self.omega = tank.omega

        # ---- malha uniforme no plano, espaçamento próprio em z (H_L/nz)
        h = tank.T / cfg.n_diam
        n_xy = cfg.n_diam + 4                                   # duas células de parede de cada lado
        half = 0.5 * n_xy * h
        self.h = h
        self.nx = self.ny = n_xy
        self.nz = max(4, int(round(tank.H_L / h)))
        self.hz = tank.H_L / self.nz
        self.H = (h, h, self.hz)
        self.xf = -half + h * np.arange(n_xy + 1)
        self.yf = self.xf.copy()
        self.zf = self.hz * np.arange(self.nz + 1)
        self.xc, self.yc, self.zc = [0.5 * (f[1:] + f[:-1]) for f in (self.xf, self.yf, self.zf)]
        self.vol = h * h * self.hz
        self.inv_d2 = 2.0 / h ** 2 + 1.0 / self.hz ** 2

        # ---- geometria nos centros e nas faces
        def grid(xs, ys, zs):
            X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
            return np.stack([X, Y, Z], -1)

        self.P_c = grid(self.xc, self.yc, self.zc)
        P_u, P_v, P_w = grid(self.xf, self.yc, self.zc), grid(self.xc, self.yf, self.zc), grid(self.xc, self.yc, self.zf)
        frac = lambda s: np.clip(0.5 + s / h, 0.0, 1.0)  # noqa: E731   fração sólida (SDF > 0 no sólido)
        self.chi_v = [t(frac(tank.vessel_sdf(P))) for P in (P_u, P_v, P_w)]      # parede do vaso
        self.chi_i = [t(frac(tank.impeller_sdf(P))) for P in (P_u, P_v, P_w)]    # agitador
        w = self.omega
        self.uwall = [t(w * P_u[..., 1]), t(-w * P_v[..., 0]), torch.zeros_like(self.chi_v[2])]  # −Ω×r
        self.vtarget = list(self.uwall)
        self.vghost = None             # faces do vaso profundo (sem troca de momento por advecção)
        self.wallfn = cfg.vessel_ibm == "wallfn"
        if self.wallfn:
            # Lei de parede no vaso (RANS). Numa malha cartesiana a parede cilíndrica vira uma escada; no
            # referencial do agitador ela gira, e qualquer forçamento sem deslizamento (suavizado ou nítido)
            # faz os degraus empurrarem o fluido como dentes de engrenagem, com um torque que não diminui
            # com o refinamento (verificado em 32, 48 e 64 células). Aqui:
            #  * além de Δ/2 dentro da parede, a região fantasma gira como corpo rígido com a velocidade
            #    angular média (por altura) do anel de fluido junto à parede: a escada entre os dois fica
            #    "invisível", porque os dois lados andam juntos (sem velocidade radial: impermeável);
            #  * a tensão τ_w = ρu_τ² (lei de Spalding) entra como força distribuída nesse anel (δ = 1/Δ
            #    numa faixa de uma célula), com a área verdadeira do cilindro.
            s_f = [tank.vessel_sdf(P) for P in (P_u, P_v, P_w)]
            self.chi_v = [torch.zeros_like(c) for c in self.chi_v]
            self.ghost_face = [t((sf > 0.5 * h).astype(float)) > 0.5 for sf in s_f]
            s_c = tank.vessel_sdf(self.P_c)
            self.ring = t(((s_c > -h) & (s_c <= 0.0)).astype(float))      # anel de fluido junto à parede
            # δ da interface [1/m]: faixa de uma célula do lado do fluido, para que a força caia em faces
            # que não são reimpostas (as faces além de Δ/2 da parede são fantasmas)
            band = (s_c > -h) & (s_c <= 0.0)
            per_layer = band[..., 0].sum() * h * h                     # volume da faixa por unidade de altura
            self.delta_w = t(np.where(band, 2 * math.pi * tank.R / max(per_layer, 1e-30), 0.0))  # ∫δ = área real
            self.beyond_wall = t((s_c > 0.5 * h).astype(float))              # além da parede: μ ≈ 0
            Xc, Yc = self.P_c[..., 0], self.P_c[..., 1]
            rc = np.hypot(Xc, Yc) + 1e-12
            self.n_c = (t(Xc / rc), t(Yc / rc))
            self.uwall_c = (t(w * Yc), t(-w * Xc))
            self.tau_w = None
        self.chi_i = [ci * (1 - cv) for ci, cv in zip(self.chi_i, self.chi_v)]
        # casca da parede do vaso (onde há fluido por perto): só ela entra no torque da parede
        self.shell = [t((tank.vessel_sdf(P) < 1.5 * h).astype(float)) for P in (P_u, P_v)]
        self.xu, self.yu = t(P_u[..., 0]), t(P_u[..., 1])
        self.xv, self.yv = t(P_v[..., 0]), t(P_v[..., 1])
        self.fluid = t(1.0 - np.maximum(frac(tank.vessel_sdf(self.P_c)), frac(tank.impeller_sdf(self.P_c))))
        self.wall_dist = t(tank.wall_distance(self.P_c))
        self.r_c = t(np.hypot(self.P_c[..., 0], self.P_c[..., 1]))
        # velocidade da parede do fundo nas faces u e v da primeira camada
        self.ubot = self.uwall[0][:, :, :1]
        self.vbot = self.uwall[1][:, :, :1]

        # ---- campos (velocidade relativa ao agitador); partida: líquido em repouso no referencial fixo
        self.u = self.uwall[0].clone() * (1 - self.chi_i[0]) * (1 - cfg.spin0)
        self.v = self.uwall[1].clone() * (1 - self.chi_i[1]) * (1 - cfg.spin0)
        self.w = torch.zeros_like(self.chi_v[2])
        self.P = torch.zeros(self.nx, self.ny, self.nz, dtype=self.ft, device=self.dev)   # p/ρ
        self.mu = torch.full_like(self.P, float(self.mu_fn(torch.zeros(1, dtype=self.ft, device=self.dev))[0]))
        self.mu_t = torch.zeros_like(self.P)
        self.gamma = torch.zeros_like(self.P)
        self.body = None            # forças de corpo extras (ex.: empuxo), lista de 3 tensores nas faces
        self.turb = None            # modelo RANS (turbulence.SST), opcional
        self.mu_bottom = None       # viscosidade da face-fantasma do fundo (função de parede)

        self._poisson_setup()
        self.time, self.step_n, self.dt, self.wall = 0.0, 0, cfg.dt_max, 0.0
        self.torque_imp = 0.0
        self.torque_wall = 0.0
        self.history = {k: [] for k in ("t", "torque", "torque_wall", "dt", "ke")}

    # -------------------------------------------------------------- Poisson
    def _lap1d(self, n, h):
        B = np.zeros((n, n))
        i = np.arange(n - 1)
        B[i, i + 1] = B[i + 1, i] = 1.0 / h ** 2
        d = np.full(n, -2.0 / h ** 2)
        d[0] += 1.0 / h ** 2
        d[-1] += 1.0 / h ** 2                     # Neumann nas duas pontas
        B[np.arange(n), np.arange(n)] = d
        lam, V = scipy.linalg.eigh(B)
        return self._t(lam), self._t(V)

    def _poisson_setup(self):
        (lx, Vx), (ly, Vy), (lz, Vz) = (self._lap1d(self.nx, self.h), self._lap1d(self.ny, self.h),
                                        self._lap1d(self.nz, self.hz))
        self.V = (Vx, Vy, Vz)
        lam = lx.view(-1, 1, 1) + ly.view(1, -1, 1) + lz.view(1, 1, -1)
        k0 = tuple(int(torch.argmin(l.abs())) for l in (lx, ly, lz))   # modo constante (autovalor nulo)
        lam[k0] = 1.0                              # pressão definida a menos de uma constante
        self.lam = lam
        self.zero_mode = torch.ones_like(lam)
        self.zero_mode[k0] = 0.0

    def poisson(self, rhs):
        Vx, Vy, Vz = self.V
        r = torch.einsum("ia,ijk->ajk", Vx, rhs)
        r = torch.einsum("jb,ajk->abk", Vy, r)
        r = torch.einsum("kc,abk->abc", Vz, r)
        r = r / self.lam * self.zero_mode
        r = torch.einsum("ia,abc->ibc", Vx, r)
        r = torch.einsum("jb,ibc->ijc", Vy, r)
        return torch.einsum("kc,ijc->ijk", Vz, r)

    def divergence(self, u, v, w):
        return diff(u, 0) / self.h + diff(v, 1) / self.h + diff(w, 2) / self.hz

    def grad_face(self, Pc, axis):
        """Gradiente nas faces internas; nas faces de borda (Neumann) é zero."""
        g = diff(Pc, axis) / self.H[axis]
        z = torch.zeros_like(sl(Pc, axis, 0, 1))
        return torch.cat([z, g, z], dim=axis)

    def project(self, u, v, w, coef):
        phi = self.poisson(self.divergence(u, v, w) / coef)
        return (u - coef * self.grad_face(phi, 0), v - coef * self.grad_face(phi, 1),
                w - coef * self.grad_face(phi, 2), phi)

    # ---------------------------------------------------------- contornos
    def _pad_comp(self, q, comp, axis, n=2):
        """Células-fantasma de uma componente de velocidade ao longo de axis.

        Em x e y o domínio termina dentro da parede (sólido): replica. Em z: fundo com parede que gira
        (fantasma = 2·u_parede − u) ou deslizamento; topo com deslizamento (espelho); w é nulo nas faces
        de fundo e topo (espelho antissimétrico)."""
        if axis != 2:
            return pad(q, axis, n)
        if comp == 2:
            lo = [-sl(q, 2, k, k + 1) for k in range(n, 0, -1)]
            hi = [-sl(q, 2, -1 - k, -k) for k in range(1, n + 1)]
            return torch.cat(lo + [q] + hi, dim=2)
        if self.cfg.bottom == "wall":
            ub = self.ubot if comp == 0 else self.vbot
            lo = [2 * ub - sl(q, 2, k - 1, k) for k in range(n, 0, -1)]
        else:
            lo = [sl(q, 2, k - 1, k) for k in range(n, 0, -1)]
        hi = [sl(q, 2, q.shape[2] - k, q.shape[2] - k + 1) for k in range(1, n + 1)]
        return torch.cat(lo + [q] + hi, dim=2)

    # ---------------------------------------------------------- viscosidade
    def strain(self, u, v, w):
        """Gradiente de velocidade nos centros g[i][j] = ∂u_i/∂x_j e taxa de cisalhamento γ̇ = √(2 S:S)."""
        uc, vc, wc = avg(u, 0), avg(v, 1), avg(w, 2)
        g = [[None] * 3 for _ in range(3)]
        for i, (q, qc) in enumerate(((u, uc), (v, vc), (w, wc))):
            for j in range(3):
                g[i][j] = diff(q, j) / self.H[j] if j == i else cgrad(qc, j, self.H[j])
        SS = 0.0
        for i in range(3):
            for j in range(i, 3):
                Sij = 0.5 * (g[i][j] + g[j][i])
                SS = SS + (1.0 if i == j else 2.0) * Sij * Sij
        return g, torch.sqrt(2.0 * SS + 1e-30)

    def update_viscosity(self, relax: float = 1.0):
        g, gam = self.strain(self.u, self.v, self.w)
        self.gamma = gam
        mu = extend_into_solid(self.mu_fn(gam).clamp(max=self.cfg.mu_max), self.fluid > 0.5)
        self.mu = mu if relax >= 1.0 else relax * mu + (1 - relax) * self.mu
        return g

    # -------------------------------------------------------------- momento
    def _advect_conservative(self, comp, q, vel):
        """∇·(u q) em forma de fluxo nos volumes de controle da componente comp, com interpolação upwind de
        3ª ordem nas faces. Pelas faces impermeáveis (velocidade normal nula) não passa momento: num vaso
        fechado o momento só é trocado com as paredes pela tensão e pela pressão."""
        beta = self.cfg.upwind
        out = 0.0
        for a in range(3):
            qp = self._pad_comp(q, comp, a, 2)
            nf = q.shape[a] + 1
            l2, l1, r1, r2 = (sl(qp, a, k, k + nf) for k in range(4))
            U = 0.5 * (l1 + r1) if a == comp else to_faces(vel[a], comp)
            qf = torch.where(U >= 0, (-l2 + 5 * l1 + 2 * r1) / 6.0, (2 * l1 + 5 * r1 - r2) / 6.0)
            if beta > 0:
                qf = (1 - beta) * qf + beta * torch.where(U >= 0, l1, r1)
            F = U * qf
            if self.vghost is not None and comp < 2:
                # vaso profundo (reimposto a cada estágio): nenhum fluxo de momento entra ou sai dele
                gp = pad(self.vghost[comp].to(q.dtype), a)
                F = F * (1 - torch.maximum(sl(gp, a, 0, nf), sl(gp, a, 1, nf + 1)))
            out = out + (sl(F, a, 1, None) - sl(F, a, 0, -1)) / self.H[a]
        return out

    def _adv_visc(self, comp, q, adv, mu_q, mu_bot=None, qv=None, vel=None):
        """Upwind de 3ª ordem e ∇·(μ∇q)/ρ para a componente comp (nas suas faces); mu_bot: viscosidade
        da face-fantasma do fundo (função de parede), no lugar da réplica da primeira camada; qv: campo
        usado no termo viscoso (com a velocidade da parede nas faces sólidas, na parede nítida)."""
        beta = self.cfg.upwind
        A, Vs = 0.0, 0.0
        qv = q if qv is None else qv
        for axis, a in enumerate(adv):
            h = self.H[axis]
            qp = self._pad_comp(q, comp, axis, 2)
            qvp = qp if qv is q else self._pad_comp(qv, comp, axis, 1)
            n = q.shape[axis]
            qm2, qm1 = sl(qp, axis, 0, n), sl(qp, axis, 1, n + 1)
            qp1, qp2 = sl(qp, axis, 3, n + 3), sl(qp, axis, 4, n + 4)
            dpos = (2 * qp1 + 3 * q - 6 * qm1 + qm2) / (6 * h)
            dneg = (-qp2 + 6 * qp1 - 3 * q - 2 * qm1) / (6 * h)
            d3 = torch.where(a >= 0, dpos, dneg)
            if beta > 0:
                d1 = torch.where(a >= 0, (q - qm1) / h, (qp1 - q) / h)
                d3 = (1 - beta) * d3 + beta * d1
            if vel is None:
                A = A + a * d3
            mp = pad(mu_q, axis)
            if axis == 2 and mu_bot is not None:
                mp = torch.cat([mu_bot, sl(mp, 2, 1, None)], dim=2)
            mu_p = 0.5 * (mu_q + sl(mp, axis, 2, None))
            mu_m = 0.5 * (mu_q + sl(mp, axis, 0, -2))
            if qv is q:
                Vs = Vs + (mu_p * (qp1 - q) - mu_m * (q - qm1)) / (h * h)
            else:
                k0 = 1 if qvp is not qp else 2
                vm1, vp1 = sl(qvp, axis, k0 - 1, n + k0 - 1), sl(qvp, axis, k0 + 1, n + k0 + 1)
                Vs = Vs + (mu_p * (vp1 - qv) - mu_m * (qv - vm1)) / (h * h)
        if vel is not None:
            A = self._advect_conservative(comp, q, vel)
        return A - Vs / self.rho

    def momentum_rhs(self, u, v, w, g=None):
        """F tal que ∂u/∂t = −F − ∇P (sem a pressão)."""
        mu = self.mu + self.mu_t
        mb = self.mu_bottom
        if self.wallfn:                       # além da parede: sem atrito (a tensão é a da lei de parede)
            mu = torch.where(self.beyond_wall > 0, 1e-3 * self.mu, mu)
            if mb is not None:
                mb = torch.where(self.beyond_wall[:, :, :1] > 0, 1e-3 * mb, mb)
        uc, vc, wc = avg(u, 0), avg(v, 1), avg(w, 2)
        vel = (u, v, w) if self.cfg.advection == "conservative" else None
        Fu = self._adv_visc(0, u, (u, to_faces(vc, 0), to_faces(wc, 0)), to_faces(mu, 0),
                            None if mb is None else to_faces(mb, 0), vel=vel)
        Fv = self._adv_visc(1, v, (to_faces(uc, 1), v, to_faces(wc, 1)), to_faces(mu, 1),
                            None if mb is None else to_faces(mb, 1), vel=vel)
        Fw = self._adv_visc(2, w, (to_faces(uc, 2), to_faces(vc, 2), w), to_faces(mu, 2), vel=vel)
        # termo transposto (∇u)ᵀ·∇μ: importante onde a viscosidade varia muito (reologia, turbulência)
        if g is not None:
            dmu = [cgrad(mu, j, self.H[j]) for j in range(3)]
            Tt = [sum(dmu[j] * g[j][i] for j in range(3)) for i in range(3)]
            Fu = Fu - to_faces(Tt[0], 0) / self.rho
            Fv = Fv - to_faces(Tt[1], 1) / self.rho
            Fw = Fw - to_faces(Tt[2], 2) / self.rho
        # Coriolis: −2Ω×u = (2ωv, −2ωu, 0)
        om = self.omega
        Fu = Fu - 2 * om * to_faces(vc, 0)
        Fv = Fv + 2 * om * to_faces(uc, 1)
        if self.body is not None:
            Fu, Fv, Fw = Fu - self.body[0], Fv - self.body[1], Fw - self.body[2]
        if self.wallfn and self.tau_w is not None:
            fx, fy, fz = self.tau_faces
            Fu, Fv, Fw = Fu - fx, Fv - fy, Fw - fz
        return Fu, Fv, Fw

    def wall_shear(self):
        """Lei de parede no vaso: u_τ de Spalding com a velocidade tangencial relativa à parede na faixa
        da interface (y = Δ) e a aceleração −u_τ² δ t̂ [m/s²] nos centros (congelada durante o passo)."""
        from .turbulence import spalding_utau
        uc, vc, wc = avg(self.u, 0), avg(self.v, 1), avg(self.w, 2)
        nx, ny = self.n_c
        ux, uy = uc - self.uwall_c[0], vc - self.uwall_c[1]
        un = ux * nx + uy * ny
        tx, ty, tz = ux - un * nx, uy - un * ny, wc
        Ut = torch.sqrt(tx * tx + ty * ty + tz * tz).clamp(min=1e-9)
        nu = (self.mu / self.rho).clamp(min=1e-9)
        ut = spalding_utau(Ut, torch.full_like(Ut, self.h), nu)
        a = -(ut ** 2) * self.delta_w / Ut
        self.u_tau_w = torch.where(self.delta_w > 0, ut, torch.zeros_like(ut))
        self.tau_w = (a * tx, a * ty, a * tz)
        # nas faces (as fantasmas são reimpostas, então a força ali se perderia): renormaliza o torque de
        # cada camada para o da tensão modelada, para que a força aplicada seja a da área verdadeira
        X, Y = self.n_c[0] * self.r_c, self.n_c[1] * self.r_c
        keep = [(~g).to(self.ft) for g in self.ghost_face]
        fx, fy, fz = (to_faces(c, k) * keep[k] for k, c in enumerate(self.tau_w))
        t_cell = (X * self.tau_w[1] - Y * self.tau_w[0]).sum((0, 1))
        t_face = (self.xv * fy).sum((0, 1)) - (self.yu * fx).sum((0, 1))
        sc = torch.where(t_face.abs() > 1e-30, t_cell / t_face, torch.ones_like(t_cell)).clamp(0.5, 2.0).view(1, 1, -1)
        self.tau_faces = (fx * sc, fy * sc, fz)
        return self.tau_w

    def _slip_ghost(self, u, v, w):
        """Região além da parede: gira como corpo rígido com a velocidade angular média (por altura) do
        primeiro anel de fluido, sem componente radial nem axial. Um campo de rotação rígida tem divergência
        nula, e a troca de momento por advecção com o líquido junto à parede fica neutra em média."""
        uc, vc = avg(u, 0), avg(v, 1)
        X, Y = self.n_c[0] * self.r_c, self.n_c[1] * self.r_c
        om = (X * vc - Y * uc) / self.r_c.clamp(min=1e-9) ** 2
        wz = (om * self.ring).sum((0, 1)) / self.ring.sum((0, 1)).clamp(min=1.0)       # [nz]
        wz = wz.view(1, 1, -1)
        u = torch.where(self.ghost_face[0], -wz * self.yu, u)
        v = torch.where(self.ghost_face[1], wz * self.xv, v)
        w = torch.where(self.ghost_face[2], torch.zeros_like(w), w)
        return u, v, w

    def _force(self, q, comp):
        """Forçamento direto: impõe a velocidade do sólido; devolve (q, impulso do agitador, da parede)."""
        ci, cv = self.chi_i[comp], self.chi_v[comp]
        di = ci * (0.0 - q)
        dv = cv * (self.vtarget[comp] - q)
        return q + di + dv, di, dv

    def _apply_bc(self, w):
        w = torch.cat([torch.zeros_like(w[:, :, :1]), w[:, :, 1:-1], torch.zeros_like(w[:, :, :1])], 2)
        return w

    def compute_dt(self):
        uc, vc, wc = avg(self.u, 0).abs(), avg(self.v, 1).abs(), avg(self.w, 2).abs()
        rate = (uc / self.h + vc / self.h + wc / self.hz).max().item()
        dt = self.cfg.cfl / max(rate, 1e-9)
        nu_max = (self.mu + self.mu_t).max().item() / self.rho
        if nu_max > 0:
            dt = min(dt, 0.45 / (2.0 * nu_max * self.inv_d2))
        dt = min(dt, 0.45 / max(self.omega, 1e-9), self.cfg.dt_max)
        return dt

    def _torques(self, du, dv, dt, chi_sel):
        """Torque (em z) aplicado ao fluido pelo impulso (du, dv) nas faces [N m]."""
        return self.rho * self.vol * float(((self.xv * dv).sum() - (self.yu * du).sum()).item()) / dt

    def step(self, update_mu: bool = True):
        """Passo RK2 (SSP). Pressão não incremental; forçamento antes e depois de cada projeção (o
        impulso total no sólido inclui a pressão e dá o torque)."""
        t0 = time.perf_counter()
        g = self.update_viscosity() if update_mu else self.strain(self.u, self.v, self.w)[0]
        if self.turb is not None:
            if not update_mu:
                self.gamma = self.strain(self.u, self.v, self.w)[1]
            self.turb.update(self.dt, g, self.gamma)
        dt = self.compute_dt()
        self.dt = dt
        if self.wallfn:
            self.wall_shear()
        u0, v0, w0 = self.u, self.v, self.w

        def stage(uu, vv, ww, coef):
            if self.wallfn:
                uu, vv, ww = self._slip_ghost(uu, vv, ww)
            uu, ai_u, av_u = self._force(uu, 0)
            vv, ai_v, av_v = self._force(vv, 1)
            ww, _, _ = self._force(ww, 2)
            ww = self._apply_bc(ww)
            uu, vv, ww, phi = self.project(uu, vv, ww, coef)
            if self.wallfn:
                uu, vv, ww = self._slip_ghost(uu, vv, ww)
            uu, bi_u, bv_u = self._force(uu, 0)              # reforço: o sólido fica exatamente na sua velocidade
            vv, bi_v, bv_v = self._force(vv, 1)
            ww, _, _ = self._force(ww, 2)
            ww = self._apply_bc(ww)
            return uu, vv, ww, phi, (ai_u + bi_u, ai_v + bi_v, av_u + bv_u, av_v + bv_v)

        # ---- estágio 1
        Fu, Fv, Fw = self.momentum_rhs(u0, v0, w0, g)
        u1, v1, w1, _, I1 = stage(u0 - dt * Fu, v0 - dt * Fv, w0 - dt * Fw, dt)
        # ---- estágio 2
        g1 = self.strain(u1, v1, w1)[0]
        Fu, Fv, Fw = self.momentum_rhs(u1, v1, w1, g1)
        u2, v2, w2, phi2, I2 = stage(0.5 * (u0 + u1 - dt * Fu), 0.5 * (v0 + v1 - dt * Fv),
                                     0.5 * (w0 + w1 - dt * Fw), 0.5 * dt)
        self.u, self.v, self.w = u2, v2, w2
        self.P = phi2
        # ---- torques: impulso efetivo no passo (o estágio 1 entra com peso 1/2)
        Iu_i, Iv_i, Iu_v, Iv_v = [0.5 * a + b for a, b in zip(I1, I2)]
        self.torque_imp = self._torques(Iu_i, Iv_i, dt, "i")
        if self.wallfn:
            # lei de parede: o torque da parede é o da tensão modelada (a remoção da componente normal
            # é radial e não exerce torque)
            ax, ay, _ = self.tau_w
            X, Y = self._t(self.P_c[..., 0]), self._t(self.P_c[..., 1])
            self.torque_wall = self.rho * self.vol * float((X * ay - Y * ax).sum())
            if self.cfg.bottom == "wall":
                self.torque_wall += self.bottom_torque()
        else:
            self.torque_wall = self._torques(Iu_v * self.shell[0], Iv_v * self.shell[1], dt, "v")
            if self.cfg.bottom == "wall":
                self.torque_wall += self.bottom_torque()
        if not torch.isfinite(self.u).all():
            raise FloatingPointError(f"o escoamento divergiu em t = {self.time:.3f} s")
        self.time += dt
        self.step_n += 1
        if self.dev.type == "cuda":
            torch.cuda.synchronize()
        self.wall += time.perf_counter() - t0
        return dt

    def angular_momentum(self):
        """Momento angular do fluido em torno do eixo, no referencial do laboratório [kg m²/s]."""
        ul, vl, _ = self.lab_velocity_centers()
        X, Y = self._t(self.P_c[..., 0]), self._t(self.P_c[..., 1])
        return self.rho * float(((X * vl - Y * ul) * self.fluid).sum()) * self.vol

    def bottom_torque(self):
        """Torque da parede do fundo sobre o fluido (tensão viscosa na primeira camada)."""
        mu_c = (self.mu + self.mu_t)[:, :, :1]
        if self.mu_bottom is not None:                       # mesma média da face usada no momento
            mu_c = 0.5 * (mu_c + self.mu_bottom)
        if self.wallfn:
            mu_c = mu_c * (self.fluid[:, :, :1] > 0.5)
        mu_u = to_faces(mu_c, 0)
        mu_v = to_faces(mu_c, 1)
        tu = mu_u * (self.ubot - self.u[:, :, :1]) / (0.5 * self.hz) * (1 - self.chi_v[0][:, :, :1])
        tv = mu_v * (self.vbot - self.v[:, :, :1]) / (0.5 * self.hz) * (1 - self.chi_v[1][:, :, :1])
        A = self.h * self.h
        return float(((self.xv[:, :, :1] * tv).sum() - (self.yu[:, :, :1] * tu).sum()).item()) * A

    # ------------------------------------------------------------ diagnósticos
    def record(self):
        ke = 0.5 * float(((avg(self.u, 0) ** 2 + avg(self.v, 1) ** 2 + avg(self.w, 2) ** 2) * self.fluid).sum()) * self.vol
        for k, val in (("t", self.time), ("torque", self.torque_imp), ("torque_wall", self.torque_wall),
                       ("dt", self.dt), ("ke", ke)):
            self.history[k].append(val)

    def power(self, n_avg: int = 200):
        """Potência média do agitador nas últimas n_avg medições [W] (P = ω T)."""
        T = np.asarray(self.history["torque"][-n_avg:])
        return self.omega * float(T.mean()) if len(T) else 0.0

    def lab_velocity_centers(self):
        """Velocidade no referencial do laboratório nos centros: u_lab = u_rel + Ω × r."""
        uc, vc, wc = avg(self.u, 0), avg(self.v, 1), avg(self.w, 2)
        X, Y = self._t(self.P_c[..., 0]), self._t(self.P_c[..., 1])
        om = self.omega
        return uc - om * Y, vc + om * X, wc

    def summary(self) -> str:
        n = self.nx * self.ny * self.nz
        return (f"malha {self.nx}×{self.ny}×{self.nz} = {n / 1e6:.2f} M células, Δ = {1e3 * self.h:.1f} mm, "
                f"{self.dev.type.upper()}")
