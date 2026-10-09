"""Turbulência RANS (k-ω SST de Menter, 2003) e funções de parede para fronteiras imersas.

Por que RANS no fundido: depois de craqueado, o conteúdo do reator é uma cera com viscosidade de
~1–10 mPa s a 400–440 °C, e o Reynolds do agitador fica em 10⁴–10⁶ (turbulento); só a pluma de
alimentação, ainda com o polímero longo, é viscosa. O SST se laminariza sozinho onde ν_t ≪ ν.

Paredes (vaso, fundo e agitador) ficam em células de uma malha cartesiana, com distância e normal dadas
pelas funções de distância analíticas. Na primeira célula de fluido:
  * lei de Spalding (válida para todo y⁺) → u_τ a partir da velocidade tangencial relativa à parede;
  * a tensão de parede entra por uma viscosidade efetiva nas faces entre a célula e o sólido
    (μ_w = ρ u_τ² Δ / |u_t|), que substitui o gradiente não resolvido;
  * ω = √(ω_vis² + ω_log²) (tratamento automático de parede) e produção de k pela lei log;
  * calor: função de parede de Kader (1981), T⁺(y⁺, Pr), h = ρ c_p u_τ / T⁺.
"""
from __future__ import annotations

import math

import numpy as np
import torch

from .ops import avg, cgrad, diff, extend_into_solid, pad, sl, to_faces

KAPPA, B_LOG = 0.41, 5.2
BETA_STAR, A1 = 0.09, 0.31
SIG_K1, SIG_K2, SIG_W1, SIG_W2 = 0.85, 1.0, 0.5, 0.856
BETA1, BETA2 = 0.075, 0.0828
ALPHA1, ALPHA2 = 5.0 / 9.0, 0.44


# --------------------------------------------------------------- leis de parede
def spalding_utau(U, y, nu, iters: int = 12):
    """u_τ pela lei de Spalding: y⁺ = u⁺ + e^{−κB}[e^{κu⁺} − 1 − κu⁺ − (κu⁺)²/2 − (κu⁺)³/6]."""
    U = U.clamp(min=1e-9)
    ut = torch.sqrt(nu * U / y).clamp(min=1e-9)                 # chute viscoso
    ut = torch.maximum(ut, KAPPA * U / torch.log(1 + 9.0 * (y * U / nu).clamp(min=1.0)))
    ekb = math.exp(-KAPPA * B_LOG)
    for _ in range(iters):
        up = U / ut
        ku = (KAPPA * up).clamp(max=60.0)
        f_up = up + ekb * (torch.exp(ku) - 1 - ku - ku ** 2 / 2 - ku ** 3 / 6)
        f = y * ut / nu - f_up
        dfu = 1 + ekb * KAPPA * (torch.exp(ku) - 1 - ku - ku ** 2 / 2)        # d(f_up)/du⁺
        df = y / nu + dfu * U / ut ** 2
        ut = (ut - f / df).clamp(min=1e-9)
    return ut


def kader_Tplus(yplus, Pr):
    """Temperatura adimensional de Kader (1981), válida da subcamada viscosa à região log."""
    beta = (3.85 * Pr ** (1.0 / 3.0) - 1.3) ** 2 + 2.12 * math.log(Pr) if not torch.is_tensor(Pr) else \
        (3.85 * Pr ** (1.0 / 3.0) - 1.3) ** 2 + 2.12 * torch.log(Pr)
    G = 0.01 * (Pr * yplus) ** 4 / (1 + 5 * Pr ** 3 * yplus)
    return Pr * yplus * torch.exp(-G) + (2.12 * torch.log(1 + yplus) + beta) * torch.exp(-1.0 / G.clamp(min=1e-12))


# ------------------------------------------------------- correção de rotação/curvatura
def rotation_curvature_factor(f, g, w_turb, frame_omega, cr1=1.0, cr2=2.0, cr3=1.0):
    """f_r1 de Spalart–Shur na forma de Smirnov & Menter (2009) para o SST, no referencial que gira com
    Ω = frame_omega ẑ. Suprime a produção de k em escoamentos com rotação estabilizante (o núcleo de um
    tanque sem chicanas gira quase como corpo rígido) e a aumenta onde a curvatura desestabiliza."""
    S = [[0.5 * (g[i][j] + g[j][i]) for j in range(3)] for i in range(3)]
    W = [[0.5 * (g[i][j] - g[j][i]) for j in range(3)] for i in range(3)]
    om = frame_omega
    # vorticidade absoluta: Ω_ij + ε_mji Ω_m  (Ω_m = ω δ_m3) → Ω_12 −= ω, Ω_21 += ω
    W[0][1] = W[0][1] - om
    W[1][0] = W[1][0] + om
    S2 = 2 * sum(S[i][j] ** 2 for i in range(3) for j in range(3))
    W2 = 2 * sum(W[i][j] ** 2 for i in range(3) for j in range(3))
    Sm, Wm = torch.sqrt(S2 + 1e-30), torch.sqrt(W2 + 1e-30)
    rstar = Sm / Wm
    # derivada material do tensor de deformação (escoamento estacionário no referencial girante)
    uc, vc, wc = avg(f.u, 0), avg(f.v, 1), avg(f.w, 2)
    vel = (uc, vc, wc)
    DS = [[None] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(i, 3):
            d = sum(vel[a] * cgrad(S[i][j], a, f.H[a]) for a in range(3))
            DS[i][j] = DS[j][i] = d
    # termo de rotação do referencial: (ε_imn S_jn + ε_jmn S_in) Ω_m, só com m = 3
    def rot(i, j):
        t = 0.0
        if i == 0:
            t = t - S[j][1]
        if i == 1:
            t = t + S[j][0]
        if j == 0:
            t = t - S[i][1]
        if j == 1:
            t = t + S[i][0]
        return om * t
    num = 0.0
    for i in range(3):
        for j in range(3):
            Aij = DS[i][j] + rot(i, j)
            for k in range(3):
                num = num + 2 * W[i][k] * S[j][k] * Aij
    D2 = torch.maximum(S2, 0.09 * w_turb ** 2)
    rtil = num / (Wm * D2 ** 1.5 + 1e-30)
    fr = (1 + cr1) * 2 * rstar / (1 + rstar) * (1 - cr3 * torch.atan(cr2 * rtil)) - cr1
    return fr.clamp(0.0, 1.25)


# ------------------------------------------------------------------------ SST
class SST:
    def __init__(self, flow, intensity: float = 0.05, L_frac: float = 0.07, curvature: bool = True):
        f = self.f = flow
        tank = flow.tank
        t = flow._t
        self.rho = flow.rho
        fl = flow.fluid > 0.5
        self.fl = fl
        self.flf = fl.to(flow.ft)
        P = flow.P_c
        # ---- paredes: distância, normal e velocidade da parede mais próxima
        d_side = -tank.vessel_sdf(P)
        d_bot = P[..., 2] if flow.cfg.bottom == "wall" else np.full(P.shape[:-1], 1e3)
        d_imp = -tank.impeller_sdf(P)
        D = np.stack([d_side, d_bot, np.abs(d_imp)], 0)
        which = np.argmin(D, 0)
        h = flow.h
        y = np.clip(D.min(0), 0.25 * h, None)
        self.y = t(y)
        # normais (para o fluido) por diferenças do SDF de cada parede
        nrm = np.zeros(P.shape)
        r = np.hypot(P[..., 0], P[..., 1]) + 1e-12
        n_side = np.stack([-P[..., 0] / r, -P[..., 1] / r, 0 * r], -1)
        n_bot = np.stack([0 * r, 0 * r, 1 + 0 * r], -1)
        gi = np.stack(np.gradient(d_imp, flow.xc, flow.yc, flow.zc), -1)
        n_imp = gi / (np.linalg.norm(gi, axis=-1, keepdims=True) + 1e-12)
        for k, n in enumerate((n_side, n_bot, n_imp)):
            nrm = np.where((which == k)[..., None], n, nrm)
        self.n = t(nrm)
        om = flow.omega
        uw = np.stack([om * P[..., 1], -om * P[..., 0], 0 * r], -1)
        self.uw = t(np.where((which == 2)[..., None], 0.0, uw))     # agitador parado; vaso e fundo: −Ω×r
        # células de parede: fluido com vizinho sólido (ou no fundo) e área de parede por volume
        sol = (~fl).to(flow.ft)
        nb = 0.0
        for axis in range(3):
            sp = pad(sol, axis)
            nb = nb + sl(sp, axis, 0, -2) * flow.H[axis] ** -1 + sl(sp, axis, 2, None) * flow.H[axis] ** -1
        if flow.cfg.bottom == "wall":
            bot = torch.zeros_like(sol)
            bot[:, :, 0] = 1.0 / flow.hz
            nb = nb + bot
        self.a_w = nb * self.flf                                      # [1/m] área de parede / volume
        self.wallcell = (self.a_w > 0) & fl
        self.wallzone = ((self.y < 1.5 * h) & fl) | self.wallcell
        # ---- campos k, ω
        U = om * tank.R
        k0 = 1.5 * (intensity * U) ** 2 + 1e-8
        w0 = math.sqrt(k0) / (BETA_STAR ** 0.25 * L_frac * tank.T)
        self.k = torch.full_like(flow.P, k0) * self.flf + 1e-10
        self.w = torch.full_like(flow.P, w0)
        self.nu_t = torch.zeros_like(flow.P)
        self.u_tau = torch.zeros_like(flow.P)
        self.F1 = torch.ones_like(flow.P)
        self.curvature = curvature
        self.nu_t_max_ratio = 1e5
        self.fr1 = torch.ones_like(flow.P)

    # ---------------------------------------------------------------- auxiliares
    def _faces_both_fluid(self, axis):
        return sl(self.flf, axis, 1, None) * sl(self.flf, axis, 0, -1)

    def _adv_diff(self, q, Q, Gam):
        """−∇·(u q) + q∇·u (upwind 1ª ordem, fluxos só entre células de fluido) + ∇·(Γ∇q)."""
        f = self.f
        out = 0.0
        divq = 0.0
        for axis in range(3):
            lo, hi = sl(q, axis, 0, -1), sl(q, axis, 1, None)
            m = self._faces_both_fluid(axis)
            Qa = sl(Q[axis], axis, 1, -1) * m
            g_lo, g_hi = sl(Gam, axis, 0, -1), sl(Gam, axis, 1, None)
            Gf = 0.5 * (g_lo + g_hi) * m
            F = Qa * torch.where(Qa >= 0, lo, hi) - Gf * (hi - lo) / f.H[axis]
            z = torch.zeros_like(sl(q, axis, 0, 1))
            Ff = torch.cat([z, F, z], dim=axis)
            Qf = torch.cat([z, Qa, z], dim=axis)
            out = out - (sl(Ff, axis, 1, None) - sl(Ff, axis, 0, -1)) / f.H[axis]
            divq = divq + (sl(Qf, axis, 1, None) - sl(Qf, axis, 0, -1)) / f.H[axis]
        return out + q * divq

    def wall_velocity_rel(self):
        """Velocidade tangencial relativa à parede nas células (vetor) e seu módulo."""
        f = self.f
        uc, vc, wc = avg(f.u, 0), avg(f.v, 1), avg(f.w, 2)
        U = torch.stack([uc, vc, wc], -1) - self.uw
        un = (U * self.n).sum(-1, keepdim=True)
        Ut = U - un * self.n
        return Ut, torch.linalg.vector_norm(Ut, dim=-1)

    # -------------------------------------------------------------------- passo
    def update(self, dt, g=None, gamma=None):
        f = self.f
        rho = self.rho
        nu = (f.mu / rho).clamp(min=1e-8)
        if gamma is None:
            g, gamma = f.strain(f.u, f.v, f.w)
        k, w = self.k, self.w
        y = self.y
        S2 = gamma ** 2
        # misturas F1, F2
        dk = [cgrad(k, a, f.H[a]) for a in range(3)]
        dw = [cgrad(w, a, f.H[a]) for a in range(3)]
        kw = sum(a * b for a, b in zip(dk, dw))
        CD = torch.clamp(2 * SIG_W2 * kw / w, min=1e-10)
        sk = torch.sqrt(k.clamp(min=0))
        arg1 = torch.minimum(torch.maximum(sk / (BETA_STAR * w * y), 500 * nu / (y ** 2 * w)),
                             4 * SIG_W2 * k / (CD * y ** 2))
        F1 = torch.tanh(arg1 ** 4)
        arg2 = torch.maximum(2 * sk / (BETA_STAR * w * y), 500 * nu / (y ** 2 * w))
        F2 = torch.tanh(arg2 ** 2)
        bl = lambda a, b: F1 * a + (1 - F1) * b  # noqa: E731
        nu_t = A1 * k / torch.maximum(A1 * w, gamma * F2)
        Pk = torch.minimum(nu_t * S2, 10 * BETA_STAR * k * w)
        if self.curvature:
            if g is None:
                g = f.strain(f.u, f.v, f.w)[0]
            self.fr1 = rotation_curvature_factor(f, g, w, f.omega)
            Pk = Pk * self.fr1
        # paredes: u_τ (Spalding), produção pela lei log e ω automático. Na faixa junto às paredes
        # (y < 1,5Δ) o gradiente da fronteira imersa não é físico: a produção vem da lei de parede
        Ut, Um = self.wall_velocity_rel()
        ut = spalding_utau(Um, y, nu)
        self.u_tau = torch.where(self.wallcell, ut, torch.zeros_like(ut))
        Pk = torch.where(self.wallzone, ut ** 3 / (KAPPA * y), Pk)
        Gk = nu + bl(SIG_K1, SIG_K2) * nu_t
        Gw = nu + bl(SIG_W1, SIG_W2) * nu_t
        Rk = self._adv_diff(k, (f.u, f.v, f.w), Gk) + Pk
        Rw = self._adv_diff(w, (f.u, f.v, f.w), Gw) + bl(ALPHA1, ALPHA2) * Pk / nu_t.clamp(min=1e-12) \
            + (1 - F1) * 2 * SIG_W2 * kw / w
        k_new = ((k + dt * Rk) / (1 + dt * BETA_STAR * w)).clamp(min=1e-10)
        w_new = ((w + dt * Rw) / (1 + dt * bl(BETA1, BETA2) * w)).clamp(min=1e-4)
        w_vis = 6 * nu / (BETA1 * y ** 2)
        w_log = ut / (math.sqrt(BETA_STAR) * KAPPA * y)
        w_new = torch.where(self.wallcell, torch.sqrt(w_vis ** 2 + w_log ** 2), w_new)
        self.k = torch.where(self.fl, k_new, torch.full_like(k_new, 1e-10))
        self.w = torch.where(self.fl, w_new, w_vis)
        self.F1 = F1
        nu_t = A1 * self.k / torch.maximum(A1 * self.w, gamma * F2)
        self.nu_t = torch.minimum(nu_t, self.nu_t_max_ratio * nu) * self.flf
        # ---- viscosidade para o momento: μ_t no fluido; nas células sólidas vizinhas, a viscosidade de
        # parede que reproduz τ_w = ρu_τ² na face (média aritmética das duas células)
        mu_eff = f.mu + rho * self.nu_t
        mu_w = rho * ut ** 2 * f.h / Um.clamp(min=1e-6)
        ghost = torch.where(self.wallcell, (2 * mu_w - mu_eff).clamp(min=0.0), torch.zeros_like(mu_w))
        solid_mu = extend_into_solid(ghost, self.wallcell, passes=1)
        f.mu_t = torch.where(self.fl, rho * self.nu_t, (solid_mu - f.mu).clamp(min=-0.999 * f.mu))
        if f.cfg.bottom == "wall":
            # fundo (face da malha): viscosidade da face-fantasma que dá τ_w na primeira camada
            mwb = rho * ut[:, :, :1] ** 2 * (0.5 * f.hz) / Um[:, :, :1].clamp(min=1e-6)
            f.mu_bottom = (2 * mwb - mu_eff[:, :, :1]).clamp(min=0.0)
        return self

    def wall_heat_transfer(self, cp, k_mol, Pr=None):
        """Coeficiente de troca nas células de parede pela função de Kader: h = ρ c_p u_τ / T⁺ [W/(m² K)]."""
        f = self.f
        nu = (f.mu / self.rho).clamp(min=1e-8)
        if Pr is None:
            Pr = (f.mu * cp / k_mol)
        yp = (self.y * self.u_tau / nu).clamp(min=1e-3)
        Tp = kader_Tplus(yp, torch.as_tensor(Pr, dtype=f.ft, device=f.dev) * torch.ones_like(yp))
        h_wf = self.rho * cp * self.u_tau / Tp.clamp(min=1e-6)
        h_lam = k_mol / self.y                                      # limite de condução pura
        return torch.where(self.wallcell, torch.maximum(h_wf, h_lam), torch.zeros_like(h_wf))
