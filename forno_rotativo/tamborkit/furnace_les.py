"""LES 3D da fornalha: chamas dos queimadores sob o tambor, gases subindo pelos corredores e saindo no topo.

Baixo Mach com densidade variável, no espírito do FDS e do flare (mesma família de métodos):
  * malha MAC uniforme; momento em forma advectiva (upwind de 3ª ordem), empuxo, termo baroclínico,
    Smagorinsky; RK2 com projeção; Poisson direto por diagonalização (paredes com Neumann, saída com
    Dirichlet no fim do plenum de exaustão);
  * química rápida: fração de mistura Z̃ (TVD Superbee) + β-PDF do equilíbrio (combustion.py);
  * perda de calor: defeito de entalpia h_d transportado, T = T_ad(Z̃, s) − h_d/c_p, com fonte
        S_h = 4 κ σ (T⁴ − T_viz⁴)  (radiação; κ do gás pelo WSGG e da fuligem)  +  h (T − T_parede) A/V;
    a restrição de divergência inclui −S_h/(ρ c_p T) (o gás que esfria contrai);
  * tambor como fronteira imersa que gira devagar (Ω R ~0,06 m/s), a uma temperatura de casco dada.

Saídas: campos médios (T, Z, velocidade), fluxo de calor no casco por fatia × ângulo (relações de Hottel
locais com o gás vizinho ao casco — as mesmas do modelo zonal, agora com a distribuição resolvida pela
LES), distribuição axial do calor liberado e balanço de energia.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
import scipy.linalg
import torch

from .combustion import FUEL_X, beta_table, state_relation, stoich
from .furnace import wsgg_emissivity

G = 9.81
SIGMA = 5.670374419e-8
CP = 1300.0


def _sl(a, axis, start, stop=None):
    idx = [slice(None)] * a.ndim
    idx[axis] = slice(start, stop)
    return a[tuple(idx)]


def _pad(a, axis, n=1):
    lo, hi = _sl(a, axis, 0, 1), _sl(a, axis, -1, None)
    return torch.cat([lo] * n + [a] + [hi] * n, dim=axis)


def _avg(a, axis):
    return 0.5 * (_sl(a, axis, 1, None) + _sl(a, axis, 0, -1))


def _diff(a, axis):
    return _sl(a, axis, 1, None) - _sl(a, axis, 0, -1)


def _to_faces(c, axis):
    return _avg(_pad(c, axis), axis)


@dataclass
class FurnaceLESConfig:
    delta: float = 0.05          # tamanho da célula [m]
    L_drum: float = 4.9
    R_out: float = 0.712
    half_width: float = 1.0      # meia largura interna da caixa [m]
    z_bot: float = -1.30         # piso da câmara de combustão
    z_top: float = 0.95          # teto da fornalha
    plenum: float = 0.45         # comprimento do plenum de exaustão atrás do tambor [m]
    burners_x: tuple = (1.2, 3.7)
    burner_z: float = -1.0
    air_patch: float = 0.20      # lado da boca de ar do queimador [m]
    Q_fire: float = 400e3        # potência total [W]
    lam: float = 1.3
    fuel: str = "GLP"
    T_shell: float = 773.15      # casco do tambor [K]
    T_refr: float = 1050.0       # refratário (para a radiação de vizinhança) [K]
    eps_s: float = 0.85
    eps_r: float = 0.85
    rpm: float = 0.8
    Lm: float = 0.5              # comprimento médio de feixe para κ do gás [m]
    h_wall: float = 8.0
    Cs: float = 0.12
    Sc_t: float = 0.7
    C_Z: float = 0.15
    cfl: float = 0.45
    dt_max: float = 0.02
    device: str = "auto"
    seed: int = 0

    @staticmethod
    def preset(name: str, **kw) -> "FurnaceLESConfig":
        d = {"teste": dict(delta=0.10), "gpu": dict(delta=0.05), "gpu_fino": dict(delta=0.035)}[name]
        d.update(kw)
        return FurnaceLESConfig(**d)


class FurnaceLES:
    def __init__(self, cfg: FurnaceLESConfig, table: dict | None = None):
        self.cfg = c = cfg
        dev = c.device
        if dev == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.dev = torch.device(dev)
        self.ft = torch.float32
        torch.manual_seed(c.seed)
        t = lambda a: torch.as_tensor(np.array(a, np.float64), dtype=self.ft, device=self.dev)  # noqa: E731
        self._t = t
        h = c.delta
        self.h = h
        Lx = c.L_drum + c.plenum
        self.nx = int(round(Lx / h)); self.ny = int(round(2 * c.half_width / h))
        self.nz = int(round((c.z_top - c.z_bot) / h))
        self.xf = np.linspace(0, self.nx * h, self.nx + 1)
        self.yf = np.linspace(-c.half_width, -c.half_width + self.ny * h, self.ny + 1)
        self.zf = np.linspace(c.z_bot, c.z_bot + self.nz * h, self.nz + 1)
        self.xc, self.yc, self.zc = [0.5 * (f[1:] + f[:-1]) for f in (self.xf, self.yf, self.zf)]
        X, Y, Z = np.meshgrid(self.xc, self.yc, self.zc, indexing="ij")
        self.n_cells = X.size
        # ---- sólidos: tambor + parede traseira/piso do plenum (o gás só sai pelo topo, atrás do tambor)
        drum = (np.hypot(Y, Z) < c.R_out) & (X < c.L_drum)
        rear = (X >= c.L_drum) & (Z < c.R_out)
        solid = drum | rear
        self.drum_np, self.solid_np = drum, solid
        self.fluid = t(~solid)
        self.drum = t(drum)
        # faces fluidas (as duas células vizinhas fluidas) e velocidade do sólido nas faces
        self.mf = []
        for ax in range(3):
            f = _pad(self.fluid, ax)
            self.mf.append(_sl(f, ax, 0, -1) * _sl(f, ax, 1, None))
        Om = 2 * math.pi * c.rpm / 60
        yv = t(np.broadcast_to(self.yf[None, :, None], (self.nx, self.ny + 1, self.nz)))
        zw = t(np.broadcast_to(self.zf[None, None, :], (self.nx, self.ny, self.nz + 1)))
        zc_v = t(np.broadcast_to(self.zc[None, None, :], (self.nx, self.ny + 1, self.nz)))
        yc_w = t(np.broadcast_to(self.yc[None, :, None], (self.nx, self.ny, self.nz + 1)))
        dfv = _to_faces(self.drum, 1); dfw = _to_faces(self.drum, 2)
        self.v_solid = -Om * zc_v * (dfv > 0)
        self.w_solid = Om * yc_w * (dfw > 0)
        del yv, zw
        # ---- vizinhança de parede (convecção) e anel junto ao casco (fluxo no tambor)
        sol = 1 - self.fluid
        nsol = 0.0
        for ax in range(3):
            sp = torch.cat([torch.ones_like(_sl(sol, ax, 0, 1)), sol, torch.ones_like(_sl(sol, ax, 0, 1))], ax)
            nsol = nsol + _sl(sp, ax, 0, -2) + _sl(sp, ax, 2, None)
        self.wall_area_per_vol = nsol * self.fluid / h
        rho_c = np.hypot(Y, Z)
        self.near_drum = t((rho_c >= c.R_out) & (rho_c < c.R_out + 0.18) & (X < c.L_drum))
        self.phi_c = np.degrees(np.arctan2(Z, Y))
        # ---- termoquímica
        if table is None:
            table = beta_table(state_relation(FUEL_X[c.fuel]))
        self.tab = table
        self.tab_rho, self.tab_drho, self.tab_T = t(table["rho"]), t(table["drho"]), t(table["T"])
        self.tab_pwc, self.tab_fv = t(table["pwc"]), t(table["fv"])
        self.tab_dT = t(np.gradient(table["T"], table["Zt"], axis=0))
        self.nZt, self.ns = table["rho"].shape
        self.s_max = float(table["s"][-1])
        self.rho_air = table["rho_air"]
        self.Z_st = table["Z_st"]
        st = stoich(FUEL_X[c.fuel])
        from .furnace import FUELS
        LHV = FUELS["GLP"]["LHV"] if c.fuel == "GLP" else FUELS["G_HC"]["LHV"]
        self.LHV = LHV
        self.m_fuel = c.Q_fire / LHV
        self.m_air = self.m_fuel * c.lam * st["AFR"]
        # ---- queimadores: fontes volumétricas de massa junto à parede y = y_min (como no flare): o ar
        # entra num bloco quadrado de lado air_patch e o combustível na célula central, com a quantidade de
        # movimento dos jatos (velocidade real de saída, sentido +y)
        nb = len(c.burners_x)
        Sa = np.zeros((self.nx, self.ny, self.nz)); Sf = np.zeros_like(Sa)
        npa = max(int(round(c.air_patch / h)), 2)
        rho_f = table["rho"][-1, 0]
        self.u_air = 8.0                          # m/s na boca de ar [H]
        self.u_fuel = 25.0                        # m/s no bico de gás [H]
        self.burner_cells = []
        for xb in c.burners_x:
            i0 = int(np.argmin(np.abs(self.xc - xb))); k0 = int(np.argmin(np.abs(self.zc - c.burner_z)))
            ii = slice(i0 - npa // 2, i0 - npa // 2 + npa); kk = slice(k0 - npa // 2, k0 - npa // 2 + npa)
            Sa[ii, 0, kk] = 1.0
            Sf[i0, 0, k0] = 1.0
            self.burner_cells.append((i0, k0))
        Sa = Sa / Sa.sum() * self.m_air / h ** 3
        Sf = Sf / Sf.sum() * self.m_fuel / h ** 3
        self.Sa, self.Sf = t(Sa), t(Sf)
        self.Sm = self.Sa + self.Sf
        # quantidade de movimento dos jatos (faces v do lado de dentro das células-fonte)
        Smv = _to_faces(self.Sm, 1)
        self.Sm_v = Smv
        self.ujet_v = torch.where(_to_faces(self.Sf, 1) > 0.5 * _to_faces(self.Sm, 1), torch.full_like(Smv, self.u_fuel),
                                  torch.full_like(Smv, self.u_air))
        # ---- Poisson: x (N parede frontal, D saída), y (N, N), z (N, N)
        self.bc = (("N", "D"), ("N", "N"), ("N", "N"))
        lams, Vs, Ws = [], [], []
        for ax, n in enumerate((self.nx, self.ny, self.nz)):
            lam, V, W = self._lap1d(n, *self.bc[ax])
            lams.append(lam); Vs.append(V); Ws.append(W)
        self.V, self.Vi = Vs, Ws
        self.lam = lams[0].view(-1, 1, 1) + lams[1].view(1, -1, 1) + lams[2].view(1, 1, -1)
        self.lam = torch.where(self.lam.abs() < 1e-9, torch.full_like(self.lam, -1e-9), self.lam)
        # ---- campos
        z = lambda *s: torch.zeros(*s, dtype=self.ft, device=self.dev)  # noqa: E731
        self.u, self.v, self.w = z(self.nx + 1, self.ny, self.nz), z(self.nx, self.ny + 1, self.nz), z(self.nx, self.ny, self.nz + 1)
        self.Z, self.hd, self.Hp = z(self.nx, self.ny, self.nz), z(self.nx, self.ny, self.nz), z(self.nx, self.ny, self.nz)
        # refratário quase adiabático: rerradia para o tambor o que recebe, então o "sumidouro" efetivo da
        # radiação do gás é o casco (a perda pela fibra cerâmica é pequena e fica no modelo zonal)
        self.T_surr = c.T_shell
        # partida a quente: a caixa cheia de ar a T_surr (encurta o transitório; o ar que entra está frio)
        self.hd = self.hd - CP * (self.T_surr - 300.0) * self.fluid
        self.time, self.steps, self.wall, self.dt = 0.0, 0, 0.0, c.dt_max
        self._numax = 0.0
        self.avg = None
        self.history = {k: [] for k in ("t", "Tmax", "Q_loss", "Q_out", "dt")}
        self._props()

    # ------------------------------------------------------------ Poisson
    def _lap1d(self, n, lo, hi):
        h = self.h
        B = np.zeros((n, n))
        idx = np.arange(n - 1)
        B[idx, idx + 1] = B[idx + 1, idx] = 1.0 / h
        diag = np.zeros(n); diag[:-1] -= 1.0 / h; diag[1:] -= 1.0 / h
        if lo == "D":
            diag[0] -= 2.0 / h
        if hi == "D":
            diag[-1] -= 2.0 / h
        B[np.arange(n), np.arange(n)] = diag
        lam, V = scipy.linalg.eigh(B, np.diag(np.full(n, h)))
        return self._t(lam), self._t(V), self._t(V.T * h)

    def poisson(self, rhs):
        (Wx, Wy, Wz), (Vx, Vy, Vz) = self.Vi, self.V
        r = torch.einsum("ai,ijk->ajk", Wx, rhs)
        r = torch.einsum("bj,ajk->abk", Wy, r)
        r = torch.einsum("ck,abk->abc", Wz, r) / self.lam
        r = torch.einsum("ia,abc->ibc", Vx, r)
        r = torch.einsum("jb,ibc->ijc", Vy, r)
        return torch.einsum("kc,ijc->ijk", Vz, r)

    def _grad_face(self, Hc, axis):
        lo, hi = self.bc[axis]
        g_lo = _sl(Hc, axis, 0, 1) * (1.0 if lo == "N" else -1.0)
        g_hi = _sl(Hc, axis, -1, None) * (1.0 if hi == "N" else -1.0)
        return _diff(torch.cat([g_lo, Hc, g_hi], dim=axis), axis) / self.h

    def divergence(self, u, v, w):
        return (_diff(u, 0) + _diff(v, 1) + _diff(w, 2)) / self.h

    def _bc(self, u, v, w):
        """Paredes da caixa (normal nula), bocas dos queimadores e sólidos imersos."""
        u = u * self.mf[0]
        v = v * self.mf[1] + self.v_solid * (1 - self.mf[1])
        w = w * self.mf[2] + self.w_solid * (1 - self.mf[2])
        v = torch.cat([torch.zeros_like(v[:, :1]), v[:, 1:-1], torch.zeros_like(v[:, :1])], 1)
        w = torch.cat([torch.zeros_like(w[:, :, :1]), w[:, :, 1:-1], torch.zeros_like(w[:, :, :1])], 2)
        u = torch.cat([torch.zeros_like(u[:1]), u[1:]], 0)
        return u, v, w

    def _Aop(self, H):
        """Laplaciano só no fluido (faces de sólido sem fluxo); identidade nas células sólidas."""
        out = 0.0
        for ax in range(3):
            out = out + _diff(self.mf[ax] * self._grad_face(H, ax), ax) / self.h
        return out * self.fluid - (1 - self.fluid) * H

    def _solve_pressure(self, b, x0, tol=2e-3, maxit=60):
        """PCG para −A x = −b com o Poisson direto da caixa inteira como pré-condicionador."""
        x = x0.clone()
        r = -b + self._Aop(x)
        bn = float(b.norm()) + 1e-30
        z = -self.poisson(r)
        p = z.clone()
        rz = (r * z).sum()
        it = 0
        for it in range(maxit):
            if float(r.norm()) < tol * bn:
                break
            Kp = -self._Aop(p)
            alpha = rz / (p * Kp).sum()
            x = x + alpha * p
            r = r - alpha * Kp
            z = -self.poisson(r)
            rz_new = (r * z).sum()
            p = z + (rz_new / rz) * p
            rz = rz_new
        self.cg_iters = it
        return x

    def _rho_face(self, rho, axis):
        return _to_faces(rho, axis)

    def project(self, u, v, w, rho_new, rho_old, dt_rate, coef):
        """Projeção na continuidade discreta: ∇·(ρ_f u) = S − (ρ_novo − ρ_antigo)/Δt, u = u* − c ∇p/ρ_f.

        ρ vem da equação de estado (Z̃, h_d): a massa fecha por construção, mesmo com ρ(Z) muito não linear."""
        u, v, w = self._bc(u, v, w)
        rf = [self._rho_face(rho_new, a) for a in range(3)]
        divm = (_diff(rf[0] * u, 0) + _diff(rf[1] * v, 1) + _diff(rf[2] * w, 2)) / self.h
        b = (divm - self.Sm + (rho_new - rho_old) / dt_rate) / coef * self.fluid
        p = self._solve_pressure(b, self.Hp if self.Hp.shape == b.shape else torch.zeros_like(b))
        u = u - coef * self.mf[0] * self._grad_face(p, 0) / rf[0]
        v = v - coef * self.mf[1] * self._grad_face(p, 1) / rf[1]
        w = w - coef * self.mf[2] * self._grad_face(p, 2) / rf[2]
        u, v, w = self._bc(u, v, w)
        return u, v, w, p

    # ----------------------------------------------------------- propriedades
    def _lookup(self, tab, Z, s):
        fz = Z.clamp(0, 1) * (self.nZt - 1)
        fs = (s / self.s_max).clamp(0, 1) * (self.ns - 1)
        iz = fz.floor().clamp(max=self.nZt - 2).long(); js = fs.floor().clamp(max=self.ns - 2).long()
        wz, ws = fz - iz, fs - js
        f = tab.reshape(-1); b = iz * self.ns + js
        return ((1 - wz) * (1 - ws) * f[b] + wz * (1 - ws) * f[b + self.ns]
                + (1 - wz) * ws * f[b + 1] + wz * ws * f[b + self.ns + 1])

    def _cgrad(self, q, axis):
        qp = _pad(q, axis)
        return (_sl(qp, axis, 2, None) - _sl(qp, axis, 0, -2)) / (2 * self.h)

    def _props(self):
        Z = self.Z
        g2 = sum(self._cgrad(Z, a) ** 2 for a in range(3))
        s = (self.cfg.C_Z * self.h ** 2 * g2 / (Z * (1 - Z) + 1e-8)).clamp(0, self.s_max)
        self.s = s
        Tad = self._lookup(self.tab_T, Z, s)
        rho_ad = self._lookup(self.tab_rho, Z, s)
        self.hd = torch.minimum(self.hd, CP * (Tad - 300.0)).clamp(min=-CP * 1200.0)
        self.T = Tad - self.hd / CP
        self.rho = rho_ad * Tad / self.T
        # ∂ρ/∂Z a h_d constante (ρ = ρ_ad T_ad / T, T = T_ad − h_d/c_p)
        self.drho = (self._lookup(self.tab_drho, Z, s) * Tad / self.T
                     - rho_ad * self._lookup(self.tab_dT, Z, s) * self.hd / (CP * self.T ** 2))
        pwc = self._lookup(self.tab_pwc, Z, s)
        fv = self._lookup(self.tab_fv, Z, s)
        eps = self._wsgg(self.T, pwc * self.cfg.Lm)
        kg = -torch.log((1 - eps).clamp(min=1e-6)) / self.cfg.Lm
        self.kappa = kg + 1862.0 * fv * self.T
        self.Sh = (4 * self.kappa * SIGMA * (self.T ** 4 - self.T_surr ** 4)
                   + self.cfg.h_wall * self.wall_area_per_vol * (self.T - self.cfg.T_shell)) * self.fluid

    def _wsgg(self, T, pL):
        """WSGG de Smith et al. (1982) em PyTorch (mesmos coeficientes de furnace.py)."""
        from .furnace import _WSGG_B, _WSGG_K
        Tc = T.clamp(600.0, 2400.0)
        eps = 0.0
        for i in range(3):
            b = _WSGG_B[i]
            a = b[0] + Tc * (b[1] + Tc * (b[2] + Tc * b[3]))
            eps = eps + a * (1 - torch.exp(-float(_WSGG_K[i]) * pL))
        return eps

    # --------------------------------------------------------------- termos
    def _nu_t(self, u, v, w):
        uc, vc, wc = _avg(u, 0), _avg(v, 1), _avg(w, 2)
        g = [[None] * 3 for _ in range(3)]
        for i, (q, qc) in enumerate(((u, uc), (v, vc), (w, wc))):
            for j in range(3):
                g[i][j] = _diff(q, j) / self.h if j == i else self._cgrad(qc, j)
        SS = 0.0
        for i in range(3):
            for j in range(i, 3):
                Sij = 0.5 * (g[i][j] + g[j][i])
                SS = SS + (1.0 if i == j else 2.0) * Sij * Sij
        return (self.cfg.Cs * self.h) ** 2 * torch.sqrt(2.0 * SS)

    def _adv_visc(self, q, adv, mu_q, rho_q):
        h = self.h
        A, Vs = 0.0, 0.0
        for axis, a in enumerate(adv):
            qp = _pad(q, axis, 2)
            n = q.shape[axis]
            qm2, qm1 = _sl(qp, axis, 0, n), _sl(qp, axis, 1, n + 1)
            qp1, qp2 = _sl(qp, axis, 3, n + 3), _sl(qp, axis, 4, n + 4)
            dpos = (2 * qp1 + 3 * q - 6 * qm1 + qm2) / (6 * h)
            dneg = (-qp2 + 6 * qp1 - 3 * q - 2 * qm1) / (6 * h)
            A = A + a * torch.where(a >= 0, dpos, dneg)
            mp = _pad(mu_q, axis)
            mu_p = 0.5 * (mu_q + _sl(mp, axis, 2, None)); mu_m = 0.5 * (mu_q + _sl(mp, axis, 0, -2))
            Vs = Vs + (mu_p * (qp1 - q) - mu_m * (q - qm1)) / (h * h)
        return A - Vs / rho_q

    def _momentum_rhs(self, u, v, w, rho):
        mu = rho * (self._nu_t(u, v, w) + 3e-5)
        uc, vc, wc = _avg(u, 0), _avg(v, 1), _avg(w, 2)
        ru, rv, rw = _to_faces(rho, 0), _to_faces(rho, 1), _to_faces(rho, 2)
        Fu = self._adv_visc(u, (u, _to_faces(vc, 0), _to_faces(wc, 0)), _to_faces(mu, 0), ru)
        Fv = self._adv_visc(v, (_to_faces(uc, 1), v, _to_faces(wc, 1)), _to_faces(mu, 1), rv)
        Fw = self._adv_visc(w, (_to_faces(uc, 2), _to_faces(vc, 2), w), _to_faces(mu, 2), rw)
        Fw = Fw + G * (rw - self.rho_air) / rw
        Fv = Fv - self.Sm_v * (self.ujet_v - v) / rv              # jatos dos queimadores
        Fu = Fu + _to_faces(self.Sm, 0) * u / ru
        Fw = Fw + _to_faces(self.Sm, 2) * w / rw
        return Fu, Fv, Fw, mu

    def _tvd_flux(self, q, a, axis, q_bnd_lo=None):
        """Fluxo a·q_face (Superbee). q_bnd_lo: valor de entrada na face de borda inferior (ou zero-grad.)."""
        n = q.shape[axis]
        qp = _pad(q, axis, 2)
        qLL, qL = _sl(qp, axis, 0, n + 1), _sl(qp, axis, 1, n + 2)
        qR, qRR = _sl(qp, axis, 2, n + 3), _sl(qp, axis, 3, n + 4)

        def sb(num, den):
            den = torch.where(den.abs() < 1e-12, torch.full_like(den, 1e-12), den)
            r = num / den
            return torch.maximum(torch.clamp(2 * r, max=1.0), torch.clamp(r, max=2.0)).clamp(min=0.0)
        qpos = qL + 0.5 * sb(qL - qLL, qR - qL) * (qR - qL)
        qneg = qR + 0.5 * sb(qR - qRR, qL - qR) * (qL - qR)
        qf = torch.where(a >= 0, qpos, qneg)
        if q_bnd_lo is not None:
            qf = torch.cat([q_bnd_lo.unsqueeze(axis), _sl(qf, axis, 1, None)], axis)
        return a * qf

    def _mass_fluxes(self, u, v, w, rho):
        """Fluxos de massa ρ_face·u nas faces (ρ a montante; nas bocas, a densidade do que entra)."""
        out = []
        for axis, a in enumerate((u, v, w)):
            out.append(self._rho_face(rho, axis) * a)
        return out

    def _scalar_rhs(self, q, F, rho, mu, q_in_y):
        """Forma de massa: [−∇·(F q_f) + q ∇·F + ∇·(ρD∇q)]/ρ, F = fluxos de massa (TVD Superbee em q_f)."""
        adv, divF = 0.0, 0.0
        for axis, Fa in enumerate(F):
            Fq = self._tvd_flux(q, Fa, axis, None)
            adv = adv + _diff(Fq, axis) / self.h
            divF = divF + _diff(Fa, axis) / self.h
        rhoD = mu / self.cfg.Sc_t
        dif = 0.0
        for axis in range(3):
            fl = _to_faces(rhoD, axis) * _diff(_pad(q, axis), axis) / self.h * self.mf[axis]
            dif = dif + _diff(fl, axis) / self.h
        return (-adv + q * divF) / rho, dif / rho

    def _compute_dt(self):
        rate = ((_avg(self.u, 0).abs() + _avg(self.v, 1).abs() + _avg(self.w, 2).abs()) / self.h).max().item()
        dt = self.cfg.cfl / max(rate, 1e-6)
        if self._numax > 0:
            dt = min(dt, 0.4 / self._numax)
        return min(dt, self.cfg.dt_max)

    def step(self):
        t0 = time.perf_counter()
        dt = self._compute_dt()
        self.dt = dt
        u0, v0, w0, Z0, h0, rho0 = self.u, self.v, self.w, self.Z, self.hd, self.rho

        def stage(u, v, w, Z, hd, rho):
            Fu, Fv, Fw, mu = self._momentum_rhs(u, v, w, rho)
            F = self._mass_fluxes(u, v, w, rho)
            aZ, dZ = self._scalar_rhs(Z, F, rho, mu, None)
            ah, dh = self._scalar_rhs(hd, F, rho, mu, None)
            RZ = (aZ + dZ + (self.Sf * (1 - Z) - self.Sa * Z) / rho) * self.fluid
            Rh = (ah + dh + (self.Sh - self.Sm * hd) / rho) * self.fluid
            return Fu, Fv, Fw, mu, RZ, Rh

        Fu, Fv, Fw, mu, RZ, Rh = stage(u0, v0, w0, Z0, h0, rho0)
        self.Z = (Z0 + dt * RZ).clamp(0, 1); self.hd = h0 + dt * Rh
        self._props()
        rho1 = self.rho
        u1, v1, w1, _ = self.project(u0 - dt * Fu, v0 - dt * Fv, w0 - dt * Fw, rho1, rho0, dt, dt)
        Z1, h1 = self.Z, self.hd
        Fu, Fv, Fw, mu1, RZ, Rh = stage(u1, v1, w1, Z1, h1, rho1)
        self.Z = (0.5 * (Z0 + Z1 + dt * RZ)).clamp(0, 1); self.hd = 0.5 * (h0 + h1 + dt * Rh)
        self._props()
        self.u, self.v, self.w, self.Hp = self.project(0.5 * (u0 + u1 - dt * Fu), 0.5 * (v0 + v1 - dt * Fv),
                                                       0.5 * (w0 + w1 - dt * Fw), self.rho, rho0, dt, 0.5 * dt)
        self._numax = ((mu1 / rho1) / self.cfg.Sc_t * 6.0 / self.h ** 2).max().item()
        if not torch.isfinite(self.w).all():
            raise FloatingPointError(f"a LES da fornalha divergiu em t = {self.time:.2f} s")
        self.time += dt
        self.steps += 1
        self.wall += time.perf_counter() - t0
        return dt

    # ------------------------------------------------------------ médias
    def accumulate(self):
        f = dict(T=self.T, Z=self.Z, Sh=self.Sh, u=_avg(self.u, 0), v=_avg(self.v, 1), w=_avg(self.w, 2))
        if self.avg is None:
            self.avg = {k: torch.zeros_like(v) for k, v in f.items()}
            self.avg_n = 0
        for k, v in f.items():
            self.avg[k] += v
        self.avg_n += 1

    def mean(self, k):
        return (self.avg[k] / max(self.avg_n, 1)).cpu().numpy()

    def energy_balance(self) -> dict:
        """Potência liberada, calor cedido ao tambor (∫S_h) e defeito de entalpia que sai na exaustão."""
        cfg = self.cfg
        V = self.h ** 3
        Q_loss = float((self.Sh * V).sum())
        rho_f = self.rho[-1]; u_f = self.u[-1]; fl = self.fluid[-1]
        hd_out = float((rho_f * u_f * self.hd[-1] * fl).sum() * self.h ** 2)
        m_out = float((rho_f * u_f).sum() * self.h ** 2)
        T_out = float((self.T[-1] * fl).sum() / fl.sum().clamp(min=1))
        return dict(Q_fire=cfg.Q_fire, Q_paredes=Q_loss, Q_exaustao=cfg.Q_fire - Q_loss, defeito_saida=hd_out,
                    m_out=m_out, m_in=self.m_fuel + self.m_air, T_max=float(self.T.max()), T_exaustao=T_out)

    def drum_flux_map(self, nphi: int = 36, nxb: int = 7) -> dict:
        """Fluxo no casco por fatia × ângulo, com o gás médio vizinho ao casco (Hottel local)."""
        cfg = self.cfg
        T = self.mean("T") if self.avg is not None else self.T.cpu().numpy()
        mask = self.near_drum.cpu().numpy() > 0
        phi = self.phi_c
        X = np.broadcast_to(self.xc[:, None, None], T.shape)
        xb = np.clip((X / cfg.L_drum * nxb).astype(int), 0, nxb - 1)
        pb = np.clip(((phi + 180.0) / 360.0 * nphi).astype(int), 0, nphi - 1)
        key = (xb * nphi + pb)[mask]
        T4 = np.bincount(key, weights=T[mask] ** 4, minlength=nxb * nphi)
        cnt = np.bincount(key, minlength=nxb * nphi)
        Tg = (T4 / np.maximum(cnt, 1)) ** 0.25
        Tg = np.where(cnt > 0, Tg, np.nan).reshape(nxb, nphi)
        # buracos (setores sem célula na malha grossa): média dos vizinhos em φ
        for _ in range(4):
            bad = ~np.isfinite(Tg)
            if not bad.any():
                break
            nb = np.nanmean(np.stack([np.roll(Tg, 1, 1), np.roll(Tg, -1, 1)]), 0)
            Tg[bad] = nb[bad]
        # forma local pelas relações de Hottel com o gás vizinho; total igual ao calor que a LES tirou do gás
        eg = wsgg_emissivity(Tg, 0.2 * 0.35)
        Ts = cfg.T_shell
        q = SIGMA * eg * (1 + cfg.eps_s) / 2 * (Tg ** 4 - Ts ** 4) + 5.0 * (Tg - Ts)
        A = 2 * np.pi * cfg.R_out / nphi * cfg.L_drum / nxb
        Q_les = float((self.mean("Sh") if self.avg is not None else self.Sh.cpu().numpy()).sum() * self.h ** 3)
        q = q / max(np.nansum(q) * A, 1e-9) * Q_les
        phi_c = -180 + (np.arange(nphi) + 0.5) * 360 / nphi
        return dict(q=q, Tg=Tg, phi=phi_c, x=(np.arange(nxb) + 0.5) * cfg.L_drum / nxb)

    def run(self, t_end: float, t_avg: float = 0.0, frame_dt: float | None = None, on_frame=None,
            verbose: bool = True):
        next_frame = self.time
        t_print = self.time
        while self.time < t_end:
            self.step()
            if self.time >= t_end - t_avg:
                self.accumulate()
            if frame_dt and on_frame and self.time >= next_frame:
                on_frame(self); next_frame += frame_dt
            if verbose and self.time - t_print >= max(t_end / 10, 1.0):
                t_print = self.time
                eb = self.energy_balance()
                print(f"  LES fornalha t = {self.time:6.2f} s  Δt = {self.dt * 1e3:5.2f} ms  T_máx = {eb['T_max'] - 273:5.0f} °C"
                      f"  ao tambor {eb['Q_paredes'] / 1e3:5.0f} kW  T saída {eb['T_exaustao'] - 273:4.0f} °C"
                      f"  CG {self.cg_iters:2d}  ṁ saída/entrada {eb['m_out'] / eb['m_in']:4.2f}  massa {float((self.rho * self.fluid).sum()) * self.h ** 3:6.2f} kg"
                      f"  ({self.wall:5.0f} s de relógio, {self.n_cells / 1e3:.0f} mil células)", flush=True)
