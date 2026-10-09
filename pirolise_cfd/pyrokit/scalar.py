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

import math

import torch

from .ops import pad, sl


def sl_pad(face_coef, axis):
    """Soma, em cada célula, dos coeficientes das suas faces internas ao longo de axis."""
    z = torch.zeros_like(sl(face_coef, axis, 0, 1))
    return torch.cat([face_coef, z], dim=axis) + torch.cat([z, face_coef], dim=axis)


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
        self.both = []
        for axis, vel in enumerate((u, v, w)):
            both = sl(self.fluid, axis, 1, None) * sl(self.fluid, axis, 0, -1)
            q = sl(vel, axis, 1, -1) * both * self.A[axis]
            self.Q.append(q)
            self.both.append(both)
        # Cortar as faces junto ao sólido deixa um resíduo de divergência nas células de interface (a
        # fronteira imersa é difusa); uma projeção só no fluido torna o campo de vazões conservativo, para
        # que o balanço global de massa e energia feche.
        self.div_before = float(self._div_flux(self.Q).abs().sum())
        self.Q = self._make_conservative(self.Q)
        self.divQ = self._div_flux([q for q in self.Q])     # ∑ vazões que saem (≈ 0 após a projeção)

    # ------------------------------------------------------------ operadores
    def _lap_fluid(self, psi):
        """−∑ (A/Δ)(ψ_viz − ψ) nas faces fluido–fluido (Laplaciano de Neumann no fluido, SPD a menos de
        constantes por região conexa)."""
        F = [self.both[a] * self.A[a] / self.H[a] * (sl(psi, a, 1, None) - sl(psi, a, 0, -1)) for a in range(3)]
        return -self._div_flux(F)

    def _make_conservative(self, Q, tol: float = 1e-6, maxit: int = 5000):
        div = self._div_flux(Q) * self.fluid
        if float(div.abs().sum()) == 0.0:
            return Q
        dg = sum(sl_pad(self.both[a] * self.A[a] / self.H[a], a) for a in range(3)) * self.fluid
        Minv = torch.where(dg > 0, 1.0 / dg.clamp(min=1e-30), torch.zeros_like(dg))
        # CG para L ψ = div, L = −∇·(A∇) (SPD semidefinida; o lado direito é compatível em cada região
        # conexa); então ∇·(Q + A∇ψ) = div − Lψ = 0
        psi = torch.zeros_like(div)
        r = div.clone()
        z = Minv * r
        p = z.clone()
        rz = float((r * z).sum())
        r0 = float(torch.linalg.vector_norm(r)) + 1e-300
        best, best_psi = 1.0, psi
        for _ in range(maxit):
            Ap = self._lap_fluid(p)
            pAp = float((p * Ap).sum())
            if pAp <= 0:
                break
            al = rz / pAp
            psi = psi + al * p
            r = r - al * Ap
            rn = float(torch.linalg.vector_norm(r)) / r0
            if rn < best:
                best, best_psi = rn, psi
            if rn < tol or rn > 1e3 * best:          # convergiu, ou o arredondamento tomou conta
                break
            z = Minv * r
            rz_new = float((r * z).sum())
            p = z + (rz_new / rz) * p
            rz = rz_new
        psi = best_psi
        return [Q[a] + self.both[a] * self.A[a] / self.H[a] * (sl(psi, a, 1, None) - sl(psi, a, 0, -1))
                for a in range(3)]

    def _div_flux(self, F):
        """Soma dos fluxos que saem de cada célula, a partir dos fluxos nas faces internas."""
        out = 0.0
        for axis, Fa in enumerate(F):
            z = torch.zeros_like(sl(self.fluid, axis, 0, 1))
            Ff = torch.cat([z, Fa, z], dim=axis)
            out = out + sl(Ff, axis, 1, None) - sl(Ff, axis, 0, -1)
        return out

    def setup(self, Gamma, Sp, Sc, dirichlet_mask=None, dirichlet_value=None, bottom_value=None, wall_cond=None):
        """Γ nas células [unid·m²/s ou W/(m K)/(ρc)], S_p ≥ 0 e S_c por volume; dirichlet_mask: células
        sólidas com valor imposto (o resto do sólido é isolado); bottom_value: valor imposto no fundo
        (z = 0), se a parede do fundo também troca; wall_cond: condutância de parede por área nas células
        de fluido [m/s] (função de parede), no lugar de Γ/(Δ/2) nas faces com a parede."""
        f = self.f
        fl = self.fluid
        dm = torch.zeros_like(fl) if dirichlet_mask is None else dirichlet_mask.to(fl.dtype) * (1 - fl)
        self.dm = dm
        self.dv = torch.zeros_like(fl) if dirichlet_value is None else dirichlet_value * torch.ones_like(fl)
        # condutâncias difusivas nas faces internas: fluido–fluido e fluido–sólido com valor imposto
        self.Dc, self.Dw = [], []
        for axis in range(3):
            g_lo, g_hi = sl(Gamma, axis, 0, -1), sl(Gamma, axis, 1, None)
            gf = 2 * g_lo * g_hi / (g_lo + g_hi).clamp(min=1e-30)       # média harmônica
            a_lo, a_hi = sl(fl, axis, 0, -1), sl(fl, axis, 1, None)
            d_lo, d_hi = sl(dm, axis, 0, -1), sl(dm, axis, 1, None)
            ff = a_lo * a_hi
            fs = a_lo * d_hi + d_lo * a_hi                                # face entre fluido e parede
            if wall_cond is None:
                c_fs = 2 * torch.where(a_lo > 0, g_lo, g_hi) / self.H[axis]     # meia célula: Γ/(Δ/2)
            else:
                c_fs = torch.where(a_lo > 0, sl(wall_cond, axis, 0, -1), sl(wall_cond, axis, 1, None))
            self.Dc.append(ff * gf * self.A[axis] / self.H[axis] + fs * c_fs * self.A[axis])
            self.Dw.append((fs * c_fs * self.A[axis], a_lo))
        # fundo: troca com a parede em z = 0 (meia célula)
        self.bottom = None
        if bottom_value is not None:
            cb = 2 * sl(Gamma, 2, 0, 1) / self.H[2] if wall_cond is None else sl(wall_cond, 2, 0, 1)
            gb = cb * sl(fl, 2, 0, 1) * self.A[2]
            self.bottom = (gb, bottom_value)
        self.Sp, self.Sc = Sp * self.V, Sc * self.V
        self.extra = 0.0                    # diagonal extra (passo pseudo-transiente)
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
        r = (self.Sp + self.extra) * phi
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
    def rhs_norm(self):
        """Norma do lado direito efetivo nas células de fluido (fontes + valores impostos nas paredes,
        como se as linhas de Dirichlet fossem eliminadas): escala para os resíduos relativos."""
        b = self.rhs()
        xD = torch.where(self.fluid > 0, torch.zeros_like(b), b)
        return float(torch.linalg.vector_norm((b - self.apply(xD)) * self.fluid)) + 1e-30

    def solve(self, x0=None, tol: float = 1e-8, maxit: int = 4000, rel_r0: bool = False):
        """BiCGSTAB precondicionado por Jacobi. Devolve (φ, resíduo relativo, iterações). As células fora
        do fluido (linhas identidade) começam no valor exato e não mudam; o resíduo é relativo ao lado
        direito efetivo do fluido ou, com rel_r0, ao resíduo inicial (partida a quente)."""
        b = self.rhs()
        x = torch.zeros_like(b) if x0 is None else x0.clone()
        x = torch.where(self.fluid > 0, x, b)
        Minv = 1.0 / self.diag
        r = b - self.apply(x)
        r0 = r.clone()
        bn = (float(torch.linalg.vector_norm(r)) if rel_r0 else self.rhs_norm()) + 1e-30
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
            r0v = float((r0 * vv).sum())
            if r0v == 0.0 or not math.isfinite(r0v):           # quebra do BiCGSTAB
                break
            alpha = rho_new / r0v
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

    def wall_flux(self, phi):
        """Fluxo que entra no fluido pelas paredes com valor imposto (lateral e fundo), por célula de
        fluido [unid·m³/s]; para a temperatura, × ρc_p dá o calor em W."""
        out = torch.zeros_like(phi)
        for axis in range(3):
            Dw, a_lo = self.Dw[axis]
            lo, hi = sl(phi, axis, 0, -1), sl(phi, axis, 1, None)
            q = Dw * (hi - lo)                                    # do lado hi para o lo
            z = torch.zeros_like(sl(phi, axis, 0, 1))
            out = out + torch.cat([q * a_lo, z], dim=axis) - torch.cat([z, q * (1 - a_lo)], dim=axis)
        if self.bottom is not None:
            gb, vb = self.bottom
            out = out + torch.cat([gb * (vb - sl(phi, 2, 0, 1)), torch.zeros_like(sl(phi, 2, 1, None))], dim=2)
        return out * self.fluid

    def wall_loss(self):
        """A·1_fluido por célula: o que um deslocamento uniforme do fluido (paredes fixas) perde para as
        paredes e os sumidouros."""
        return self.apply(self.fluid) * self.fluid

    def solve_ptc(self, x0, tol: float = 5e-4, dtau0: float = 1.0, growth: float = 2.0, dtau_max: float = 300.0,
                  steps: int = 30, inner_tol: float = 1e-2, inner_maxit: int = 300, verbose: bool = False):
        """Continuação pseudo-transiente (Euler implícito em τ, passo crescendo até dtau_max) com BiCGSTAB
        em cada passo e correção do modo médio global: num vaso fechado com recirculação, o nível médio do
        escalar só relaxa na escala do tempo de residência (horas); um deslocamento uniforme ótimo resolve
        esse modo de uma vez, e o passo τ limitado mantém cada sistema linear bem condicionado. Um passo
        que piora o resíduo é rejeitado e refeito com dτ/4."""
        fl = self.fluid
        bn = self.rhs_norm()
        # trabalha com o desvio em relação à média inicial no fluido (x = c + y): os termos de advecção,
        # grandes, passam a agir sobre números pequenos, o que baixa o piso de arredondamento em float32
        c = float((x0 * fl).sum() / fl.sum().clamp(min=1.0))
        Sc_orig = self.Sc
        self.Sc = Sc_orig - self.apply(c * fl) * fl
        b0 = self.rhs()
        x = torch.where(fl > 0, x0 - c, b0)
        base_diag = self.diag.clone()
        loss = self.wall_loss()
        den = float(loss.sum())

        def residual(z):
            return float(torch.linalg.vector_norm((b0 - self.apply(z)) * fl)) / bn

        def mean_fix(z):
            if den > 0 and bool(torch.isfinite(z).all()):
                z = z + float(((b0 - self.apply(z)) * fl).sum()) / den * fl
            return z

        x = mean_fix(x)                                   # a partida já satisfaz o balanço global
        res = residual(x)
        dtau = dtau0
        n = 0
        for n in range(steps):
            self.extra = self.V / dtau * fl
            self.diag = torch.where(fl > 0, base_diag + self.extra, base_diag)
            Sc0 = self.Sc
            self.Sc = Sc0 + self.extra * x
            xn, _, _ = self.solve(x, tol=inner_tol, maxit=inner_maxit, rel_r0=True)
            self.Sc = Sc0
            self.extra = 0.0
            self.diag = base_diag
            xn = mean_fix(xn)                             # correção global (0-D) do nível médio
            rn = residual(xn) if bool(torch.isfinite(xn).all()) else float("inf")
            if verbose:
                print(f"    ptc {n}: dτ = {dtau:.3g} s, resíduo {rn:.2e}")
            if not rn < 2.0 * res:                         # passo ruim: rejeita e reduz dτ
                dtau = max(dtau / 4.0, 1e-3)
                continue
            x, res = xn, rn
            if res < tol:
                break
            dtau = min(dtau * growth, dtau_max)
        self.Sc = Sc_orig
        return torch.where(fl > 0, x + c, x), res, n + 1
