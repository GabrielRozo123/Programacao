"""Transporte estacionário de escalares (temperatura, estado do polímero) sobre o escoamento convergido.

As escalas de tempo são muito diferentes: o escoamento no tanque se estabelece em segundos, enquanto a
pirólise e o tempo de residência do fundido são de dezenas de minutos. Por isso a temperatura e a
composição são resolvidas diretamente no regime permanente, no referencial do agitador (onde o
escoamento é estacionário):

    ∇·(u φ) − φ ∇·u − ∇·(Γ ∇φ) + S_p φ = S_c

com advecção upwind (monótona), difusão com Γ variável (molecular + turbulenta), células sólidas com
valor imposto (parede aquecida) ou isoladas (agitador), e solução por BiCGSTAB sem matriz explícita,
precondicionado por Jacobi (GPU).
"""
from __future__ import annotations

import torch

from .ops import pad, sl


class SteadyScalar:
    def __init__(self, flow, u=None, v=None, w=None):
        """flow: TankFlow (malha, máscaras); (u, v, w): velocidades nas faces (padrão: as atuais)."""
        self.f = flow
        h, hz = flow.h, flow.hz
        self.H = (h, h, hz)
        self.A = (h * hz, h * hz, h * h)          # áreas das faces normais a x, y, z
        self.V = flow.vol
        fl = (flow.fluid > 0.5)
        self.fluid = fl.to(flow.ft)
        u = flow.u if u is None else u
        v = flow.v if v is None else v
        w = flow.w if w is None else w
        # vazões volumétricas nas faces internas entre duas células de fluido (zero junto ao sólido)
        self.Q = []
        for axis, vel in enumerate((u, v, w)):
            both = sl(self.fluid, axis, 1, None) * sl(self.fluid, axis, 0, -1)
            q = sl(vel, axis, 1, -1) * both * self.A[axis]
            self.Q.append(q)
        self.divQ = self._div_flux([q for q in self.Q])     # ∑ vazões que saem (∇·u·V discreto)

    # ------------------------------------------------------------ operadores
    def _div_flux(self, F):
        """Soma dos fluxos que saem de cada célula, a partir dos fluxos nas faces internas."""
        out = 0.0
        for axis, Fa in enumerate(F):
            z = torch.zeros_like(sl(self.fluid, axis, 0, 1))
            Ff = torch.cat([z, Fa, z], dim=axis)
            out = out + sl(Ff, axis, 1, None) - sl(Ff, axis, 0, -1)
        return out

    def setup(self, Gamma, Sp, Sc, dirichlet_mask=None, dirichlet_value=None, bottom_value=None):
        """Γ nas células [unid·m²/s ou W/(m K)/(ρc)], S_p ≥ 0 e S_c por volume; dirichlet_mask: células
        sólidas com valor imposto (o resto do sólido é isolado); bottom_value: valor imposto no fundo
        (z = 0), se a parede do fundo também troca."""
        f = self.f
        fl = self.fluid
        dm = torch.zeros_like(fl) if dirichlet_mask is None else dirichlet_mask.to(fl.dtype) * (1 - fl)
        self.dm = dm
        self.dv = torch.zeros_like(fl) if dirichlet_value is None else dirichlet_value * torch.ones_like(fl)
        # condutâncias difusivas nas faces internas: fluido–fluido e fluido–sólido com valor imposto
        self.Dc = []
        for axis in range(3):
            g_lo, g_hi = sl(Gamma, axis, 0, -1), sl(Gamma, axis, 1, None)
            gf = 2 * g_lo * g_hi / (g_lo + g_hi).clamp(min=1e-30)       # média harmônica
            a_lo, a_hi = sl(fl, axis, 0, -1), sl(fl, axis, 1, None)
            d_lo, d_hi = sl(dm, axis, 0, -1), sl(dm, axis, 1, None)
            ff = a_lo * a_hi
            fs = a_lo * d_hi + d_lo * a_hi                                # face entre fluido e parede
            g_fs = torch.where(a_lo > 0, g_lo, g_hi)
            # meia célula até a parede: condutância Γ/(h/2)
            self.Dc.append((ff * gf + fs * 2 * g_fs) * self.A[axis] / self.H[axis])
        # fundo: troca com a parede em z = 0 (meia célula)
        self.bottom = None
        if bottom_value is not None:
            gb = sl(Gamma, 2, 0, 1) * sl(fl, 2, 0, 1) * 2 * self.A[2] / self.H[2]
            self.bottom = (gb, bottom_value)
        self.Sp, self.Sc = Sp * self.V, Sc * self.V
        # diagonal (para o precondicionador)
        diag = self._diag()
        self.diag = torch.where(fl > 0, diag, torch.ones_like(diag))
        return self

    def _diag(self):
        d = self.Sp * self.fluid
        for axis in range(3):
            Q, D = self.Q[axis], self.Dc[axis]
            # célula "lo" de cada face: saída para +; célula "hi": saída para −
            z = torch.zeros_like(sl(self.fluid, axis, 0, 1))
            out_lo = torch.cat([Q.clamp(min=0) + D, z], dim=axis)
            out_hi = torch.cat([z, (-Q).clamp(min=0) + D], dim=axis)
            d = d + out_lo + out_hi
        d = d - (self.divQ * self.fluid)
        if self.bottom is not None:
            gb = self.bottom[0]
            d = d + torch.cat([gb, torch.zeros_like(sl(d, 2, 1, None))], dim=2)
        return d

    def apply(self, phi):
        """A φ (só nas células de fluido; nas demais, identidade)."""
        fl = self.fluid
        r = self.Sp * phi
        F = []
        for axis in range(3):
            lo, hi = sl(phi, axis, 0, -1), sl(phi, axis, 1, None)
            Q, D = self.Q[axis], self.Dc[axis]
            up = torch.where(Q >= 0, lo, hi)
            F.append(Q * up - D * (hi - lo))
        r = r + self._div_flux(F) - phi * self.divQ
        if self.bottom is not None:
            gb = self.bottom[0]
            r = r + torch.cat([gb * sl(phi, 2, 0, 1), torch.zeros_like(sl(phi, 2, 1, None))], dim=2)
        return torch.where(fl > 0, r, phi)

    def rhs(self):
        """Termo independente: fontes e parede do fundo; nas células sólidas com valor imposto, o valor
        (as paredes entram pelo acoplamento com essas células, que são incógnitas com linha identidade)."""
        fl, dm = self.fluid, self.dm
        b = self.Sc.clone()
        if self.bottom is not None:
            gb, Tb = self.bottom
            b = b + torch.cat([gb * Tb, torch.zeros_like(sl(b, 2, 1, None))], dim=2)
        return torch.where(fl > 0, b, self.dv * dm)

    # --------------------------------------------------------------- solver
    def solve(self, x0=None, tol: float = 1e-8, maxit: int = 4000):
        """BiCGSTAB precondicionado por Jacobi. Devolve (φ, resíduo relativo, iterações)."""
        b = self.rhs()
        x = torch.zeros_like(b) if x0 is None else x0.clone()
        Minv = 1.0 / self.diag
        r = b - self.apply(x)
        r0 = r.clone()
        bn = float(torch.linalg.vector_norm(b)) + 1e-30
        rho = alpha = omega = 1.0
        vv = torch.zeros_like(b)
        p = torch.zeros_like(b)
        res = float(torch.linalg.vector_norm(r)) / bn
        it = 0
        for it in range(1, maxit + 1):
            rho_new = float((r0 * r).sum())
            if abs(rho_new) < 1e-300:
                break
            beta = (rho_new / rho) * (alpha / omega)
            p = r + beta * (p - omega * vv)
            ph = Minv * p
            vv = self.apply(ph)
            alpha = rho_new / float((r0 * vv).sum())
            s = r - alpha * vv
            sh = Minv * s
            t = self.apply(sh)
            tt = float((t * t).sum())
            omega = float((t * s).sum()) / tt if tt > 0 else 0.0
            x = x + alpha * ph + omega * sh
            r = s - omega * t
            rho = rho_new
            res = float(torch.linalg.vector_norm(r)) / bn
            if res < tol or omega == 0.0:
                break
        return x, res, it
