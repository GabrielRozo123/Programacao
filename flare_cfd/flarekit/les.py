"""LES 3D de baixo Mach para um flare elevado em vento cruzado (PyTorch; GPU se houver).

Formulação (seções 4.1–4.6 do documento), no espírito do FDS:
  * baixo Mach, densidade variável: ρ = ρ(Z̃, s) da tabela β-PDF (química rápida + equilíbrio);
  * restrição de divergência  ∇·u = S_m/ρ − (1/ρ²)(dρ/dZ)[∇·(ρD_t∇Z) + S_m(1−Z)];
  * momento em forma advectiva (upwind de 3ª ordem), H = p̃/ρ, termo baroclínico defasado
    (H∇ρ/ρ), empuxo, Smagorinsky;
  * Poisson de coeficiente constante ∇²H = (∇·u* − D)/Δt, resolvido de forma direta pela
    diagonalização dos operadores 1D (autoproblema generalizado B v = λ M v em malha esticada);
  * fração de mistura com advecção TVD (Superbee), variância de submalha Z''² = C_Z Δ² |∇Z̃|²;
  * fonte de combustível volumétrica no tip com o fluxo de quantidade de movimento do jato real;
  * vento com perfil log e tensão de parede no solo; RK2 (SSP) com projeção em cada estágio.

Malha deslocada (MAC) e não uniforme por produto tensorial: fina (Δ_f) numa caixa em volta do
tip e da chama, crescendo geometricamente até Δ_max fora dela.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
import scipy.linalg
import torch

from .props import G, BetaPDFTable

KAPPA = 0.41


# ----------------------------------------------------------------- utilidades
def _sl(a, axis, start, stop=None):
    idx = [slice(None)] * a.ndim
    idx[axis] = slice(start, stop)
    return a[tuple(idx)]


def _pad(a, axis, n=1):
    lo, hi = _sl(a, axis, 0, 1), _sl(a, axis, -1, None)
    return torch.cat([lo] * n + [a] + [hi] * n, dim=axis)


def _avg(a, axis):
    return 0.5 * (_sl(a, axis, 1, None) + _sl(a, axis, 0, -1))


def _to_faces(c, axis):
    """Centro → faces ao longo de axis (faces de borda recebem o valor da célula de borda)."""
    return _avg(_pad(c, axis), axis)


def _diff(a, axis):
    return _sl(a, axis, 1, None) - _sl(a, axis, 0, -1)


def _bshape(arr, axis, ndim=3):
    shape = [1] * ndim
    shape[axis] = -1
    return arr.reshape(shape)


def stretched_faces(lo, hi, f_lo, f_hi, d_fine, ratio=1.1, d_max=2.5):
    """Faces com Δ = d_fine em [f_lo, f_hi] e crescimento geométrico (ratio) até d_max fora."""
    nf = int(round((f_hi - f_lo) / d_fine))
    fine = f_lo + d_fine * np.arange(nf + 1)

    def grow(start, end, sign):
        out, x, d = [], start, d_fine
        while sign * (end - x) > 1e-9:
            d = min(d * ratio, d_max)
            x = x + sign * d
            out.append(x)
        if out:
            out[-1] = end
            if len(out) > 1 and abs(out[-1] - out[-2]) < 0.5 * d:
                out.pop(-2)
        return out

    up = grow(fine[-1], hi, +1)
    down = grow(fine[0], lo, -1)
    return np.concatenate([np.array(down[::-1]), fine, np.array(up)])


@dataclass
class LESConfig:
    # domínio e malha
    x_range: tuple = (-40.0, 130.0)
    y_range: tuple = (-40.0, 40.0)
    z_top: float = 100.0
    d_fine: float = 0.35
    fine_x: tuple = (-4.0, 30.0)
    fine_y: tuple = (-6.0, 6.0)
    fine_z: tuple = (-2.0, 24.0)       # relativo à altura do tip
    ratio: float = 1.1
    d_max: float = 2.5
    # cenário
    H: float = 30.0            # altura do tip [m]
    u_ref: float = 8.9         # vento na altura do tip [m/s]
    z0: float = 0.03           # rugosidade aerodinâmica [m]
    mdot: float = 12.6         # vazão de combustível [kg/s]
    u_jet: float = 128.7       # velocidade real no tip (fluxo de quantidade de movimento)
    src_cells: int = 2         # lado da fonte, em células finas
    X_rad: float = 0.25        # fração radiante usada para escalar a emissão
    T_inf: float = 298.15
    RH: float = 0.5
    # modelos e numérica
    sgs: str = "smagorinsky"   # "smagorinsky" ou "wale"
    Cs: float = 0.10           # valor usual em escoamentos cisalhantes livres
    Cw: float = 0.5
    Sc_t: float = 0.7
    C_Z: float = 0.15
    cfl: float = 0.5
    dt_max: float = 0.05
    upwind: float = 0.0        # fração de upwind de 1ª ordem (0 = upwind de 3ª ordem puro)
    limiter: str = "superbee"  # limitador TVD de Z (Superbee, como no FDS); "mc" ou "vanleer"
    inflow_noise: float = 0.08
    jet_noise: float = 0.0     # impulsos aleatórios na fonte (desligado por padrão)
    baroclinic: bool = True
    # radiação no solo
    receiver_dx: float = 3.0
    receiver_z: float = 1.5
    receiver_box: tuple | None = None   # (x0, x1, y_meia) extra coberto por receptores, além do domínio
    emitter_bin: float = 1.5   # agrupa emissores em blocos deste tamanho [m]
    device: str = "auto"
    seed: int = 0

    @staticmethod
    def for_flame(name: str, box: dict, **kw) -> "LESConfig":
        """Preset com a caixa de malha fina e o domínio ajustados à chama prevista (semiempirical.flame_box)."""
        x0, x1 = box["x"]
        yh = box["y_half"]
        z0, z1 = box["z"]
        H = kw.get("H", 30.0)
        dom = dict(fine_x=(x0, x1), fine_y=(-yh, yh), fine_z=(z0, z1),
                   x_range=(min(-40.0, x0 - 30.0), max(130.0, x1 + 90.0)),
                   y_range=(-max(40.0, yh + 30.0), max(40.0, yh + 30.0)),
                   z_top=max(100.0, H + z1 + 40.0))
        if name == "teste":
            dom.update(x_range=(min(-24.0, x0 - 15.0), max(60.0, x1 + 30.0)), y_range=(-21.0, 21.0),
                       z_top=max(75.0, H + z1 + 15.0))
        elif name == "cpu":   # domínio menor que o da GPU (mesma lógica, folgas reduzidas)
            dom.update(x_range=(min(-30.0, x0 - 15.0), max(100.0, x1 + 60.0)),
                       y_range=(-max(32.0, yh + 20.0), max(32.0, yh + 20.0)), z_top=max(90.0, H + z1 + 30.0))
        dom.update(kw)
        return LESConfig.preset(name, **dom)

    @staticmethod
    def preset(name: str, **kw) -> "LESConfig":
        presets = {
            # GPU (Colab T4): Δ = 0,5 m perto da chama (~0,8 M células). Validado: L e inclinação
            # sob vento de 8,9 m/s a +2% e +10% de Chamberlain (1987)
            "gpu": dict(d_fine=0.5, d_max=3.0),
            # GPU, malha fina: Δ = 0,35 m (~1,8 M células)
            "gpu_fino": dict(d_fine=0.35),
            # GPU grande (A100/L4): Δ = 0,25 m (~4 M células)
            "gpu_ultra": dict(d_fine=0.25, ratio=1.08),
            # CPU: Δ = 0,7 m num domínio menor
            "cpu": dict(d_fine=0.7, d_max=3.5, x_range=(-30.0, 100.0), y_range=(-32.0, 32.0), z_top=90.0,
                        receiver_dx=4.0, emitter_bin=2.0),
            # teste rápido (malha grossa: só para verificar o fluxo do notebook)
            "teste": dict(d_fine=1.5, d_max=3.0, x_range=(-24.0, 60.0), y_range=(-21.0, 21.0),
                          z_top=75.0, receiver_dx=6.0, emitter_bin=3.0),
        }
        cfg = presets[name].copy()
        if kw.get("u_ref", 1.0) <= 0.0 and name != "teste" and "fine_x" not in kw:
            # sem vento: chama vertical e mais longa → caixa fina centrada e mais alta
            cfg.update(x_range=(-50.0, 50.0), y_range=(-50.0, 50.0), z_top=110.0,
                       fine_x=(-7.0, 7.0), fine_y=(-7.0, 7.0), fine_z=(-2.0, 56.0))
        cfg.update(kw)
        return LESConfig(**cfg)


class FlareLES:
    def __init__(self, cfg: LESConfig, table: BetaPDFTable, Q: float):
        self.cfg = cfg
        self.Q = Q   # potência do flare (ṁ·PCI) [W], normaliza a radiação
        dev = cfg.device
        if dev == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.dev = torch.device(dev)
        self.ft = torch.float32
        torch.manual_seed(cfg.seed)
        t = lambda a: torch.as_tensor(np.asarray(a, dtype=np.float64), dtype=self.ft, device=self.dev)  # noqa: E731
        self._t = t
        df = cfg.d_fine

        # ---- malha (x = 0, y = 0 e z = H são faces)
        snap = lambda a: round(a / df) * df  # noqa: E731
        H = snap(cfg.H)
        self.xf = stretched_faces(cfg.x_range[0], cfg.x_range[1], snap(cfg.fine_x[0]), snap(cfg.fine_x[1]),
                                  df, cfg.ratio, cfg.d_max)
        self.yf = stretched_faces(cfg.y_range[0], cfg.y_range[1], snap(cfg.fine_y[0]), snap(cfg.fine_y[1]),
                                  df, cfg.ratio, cfg.d_max)
        self.zf = stretched_faces(0.0, cfg.z_top, H + snap(cfg.fine_z[0]), H + snap(cfg.fine_z[1]),
                                  df, cfg.ratio, cfg.d_max)
        self.nx, self.ny, self.nz = len(self.xf) - 1, len(self.yf) - 1, len(self.zf) - 1
        self.n_cells = self.nx * self.ny * self.nz
        self.xc, self.yc, self.zc = [0.5 * (f[1:] + f[:-1]) for f in (self.xf, self.yf, self.zf)]
        self.wind = cfg.u_ref > 0.0
        # espaçamentos: largura das células (n), distância centro-centro nas faces (n+1)
        # e largura do volume de controle das faces (n+1)
        self.dc, self.df_, self.dcf = [], [], []
        for f, c in ((self.xf, self.xc), (self.yf, self.yc), (self.zf, self.zc)):
            dc = np.diff(f)
            self.dc.append(dc)
            self.df_.append(np.concatenate([[dc[0]], np.diff(c), [dc[-1]]]))
            self.dcf.append(np.concatenate([[dc[0]], 0.5 * (dc[1:] + dc[:-1]), [dc[-1]]]))
        self.Dc = [_bshape(t(a), ax) for ax, a in enumerate(self.dc)]
        self.Df = [_bshape(t(a), ax) for ax, a in enumerate(self.df_)]
        self.Dcf = [_bshape(t(a), ax) for ax, a in enumerate(self.dcf)]
        vol = np.einsum("i,j,k->ijk", *self.dc)
        self.vol = t(vol)
        self.delta = self.vol ** (1.0 / 3.0)
        self.inv_d2 = 1 / self.Dc[0] ** 2 + 1 / self.Dc[1] ** 2 + 1 / self.Dc[2] ** 2

        # ---- tabela termoquímica
        self.tab = table
        self.tab_rho = t(table.rho); self.tab_drho = t(table.drho_dZ); self.tab_T = t(table.T)
        self.tab_e = t(table.emission)
        self.nZt, self.ns = table.rho.shape
        self.s_max = float(table.s[-1])
        self.rho_inf = float(table.rho_inf)
        self.Z_st = float(table.Z_st)

        # ---- campos
        nx, ny, nz = self.nx, self.ny, self.nz
        z = lambda *s: torch.zeros(*s, dtype=self.ft, device=self.dev)  # noqa: E731
        self.u, self.v, self.w = z(nx + 1, ny, nz), z(nx, ny + 1, nz), z(nx, ny, nz + 1)
        self.Z, self.Hp = z(nx, ny, nz), z(nx, ny, nz)

        # ---- vento (perfil log ajustado para u_ref na altura do tip)
        self.u_star = KAPPA * cfg.u_ref / math.log((H + cfg.z0) / cfg.z0) if self.wind else 0.0
        U_prof = self.u_star / KAPPA * np.log((self.zc + cfg.z0) / cfg.z0)
        self.U_in = t(U_prof).view(1, 1, nz).expand(1, ny, nz).clone()
        if self.wind:
            self.u[:] = self.U_in
        self.Cd_wall = (KAPPA / math.log((0.5 * self.dc[2][0]) / cfg.z0)) ** 2
        self.noise = z(1, ny, nz)

        # ---- fonte de combustível (bloco src×src×1 logo acima do tip)
        i0 = int(np.argmin(np.abs(self.xf))); j0 = int(np.argmin(np.abs(self.yf)))
        n2 = cfg.src_cells // 2
        self.kH = int(np.argmin(np.abs(self.zf - H)))
        self.isrc = slice(i0 - n2, i0 - n2 + cfg.src_cells)
        self.jsrc = slice(j0 - n2, j0 - n2 + cfg.src_cells)
        Sm = z(nx, ny, nz)
        V_src = float(vol[self.isrc, self.jsrc, self.kH].sum())
        Sm[self.isrc, self.jsrc, self.kH] = cfg.mdot / V_src
        self.Sm = Sm
        self.Sm_u, self.Sm_v, self.Sm_w = _to_faces(Sm, 0), _to_faces(Sm, 1), _to_faces(Sm, 2)
        self.src_u, self.src_v = self.Sm_u.gt(0).to(self.ft), self.Sm_v.gt(0).to(self.ft)
        self.tip = np.array([0.0, 0.0, self.zf[self.kH]])
        self.src_area = float(self.dc[0][self.isrc].sum() * self.dc[1][self.jsrc].sum())

        # ---- Poisson (diagonalização 1D, autoproblema generalizado)
        bx = ("N" if self.wind else "D", "D")
        self.bc = (bx, ("D", "D"), ("N", "D"))
        self._poisson_setup()

        # ---- receptores no solo
        # (os receptores são só pontos de avaliação: podem ir além do domínio do escoamento para cobrir
        # toda a zona de 1,58 kW/m²)
        rx0, rx1, ry0, ry1 = self.xf[0], self.xf[-1], self.yf[0], self.yf[-1]
        if cfg.receiver_box is not None:
            bx0, bx1, byh = cfg.receiver_box
            rx0, rx1, ry0, ry1 = min(rx0, bx0), max(rx1, bx1), min(ry0, -byh), max(ry1, byh)
        rx = np.arange(rx0 + cfg.receiver_dx / 2, rx1, cfg.receiver_dx)
        ry = np.arange(ry0 + cfg.receiver_dx / 2, ry1, cfg.receiver_dx)
        self.rec_x, self.rec_y = rx, ry
        RX, RY = np.meshgrid(rx, ry, indexing="ij")
        self.receivers = t(np.stack([RX, RY, np.full_like(RX, cfg.receiver_z)], -1).reshape(-1, 3))

        # ---- coordenadas das células
        Xc, Yc, Zc = np.meshgrid(self.xc, self.yc, self.zc, indexing="ij")
        self.cell_xyz = t(np.stack([Xc, Yc, Zc], -1)).reshape(-1, 3)
        self.dist_tip = torch.linalg.norm(self.cell_xyz - t(self.tip), dim=-1).reshape(nx, ny, nz)
        self.j_mid = int(np.argmin(np.abs(self.yc)))

        # ---- estado do tempo e médias
        self.time = 0.0; self.step_n = 0; self.dt = cfg.dt_max; self.wall = 0.0
        self._numax = 0.0; self._last_cfl = 0.0
        self.history = {k: [] for k in ("t", "L", "tilt", "qmax", "Tmax", "dt", "cfl")}
        self.avg_n = 0.0
        self.avg_T, self.avg_I = z(nx, ny, nz), z(nx, ny, nz)
        self.avg_q = z(len(rx) * len(ry))
        self.q_inst = torch.zeros_like(self.avg_q)
        self._update_props(self.Z)

    # ---------------------------------------------------------------- Poisson
    def _lap1d(self, axis):
        dc, dfa = self.dc[axis], self.df_[axis]
        lo, hi = self.bc[axis]
        n = len(dc)
        # A = M⁻¹B com M = diag(Δc) e B simétrica: B[i,i±1] = 1/Δf
        B = np.zeros((n, n))
        off = 1.0 / dfa[1:-1]
        idx = np.arange(n - 1)
        B[idx, idx + 1] = off
        B[idx + 1, idx] = off
        diag = np.zeros(n)
        diag[:-1] -= off
        diag[1:] -= off
        if lo == "D":
            diag[0] -= 2.0 / dc[0]
        if hi == "D":
            diag[-1] -= 2.0 / dc[-1]
        B[np.arange(n), np.arange(n)] = diag
        lam, V = scipy.linalg.eigh(B, np.diag(dc))      # Vᵀ M V = I  →  V⁻¹ = Vᵀ M
        return self._t(lam), self._t(V), self._t(V.T * dc[None, :])

    def _poisson_setup(self):
        (lx, Vx, Wx), (ly, Vy, Wy), (lz, Vz, Wz) = (self._lap1d(0), self._lap1d(1), self._lap1d(2))
        self.V = (Vx, Vy, Vz)
        self.Vi = (Wx, Wy, Wz)
        self.lam = lx.view(-1, 1, 1) + ly.view(1, -1, 1) + lz.view(1, 1, -1)

    def poisson(self, rhs):
        Wx, Wy, Wz = self.Vi
        Vx, Vy, Vz = self.V
        r = torch.einsum("ai,ijk->ajk", Wx, rhs)
        r = torch.einsum("bj,ajk->abk", Wy, r)
        r = torch.einsum("ck,abk->abc", Wz, r)
        r = r / self.lam
        r = torch.einsum("ia,abc->ibc", Vx, r)
        r = torch.einsum("jb,ibc->ijc", Vy, r)
        return torch.einsum("kc,ijc->ijk", Vz, r)

    def _grad_face(self, Hc, axis):
        lo, hi = self.bc[axis]
        g_lo = _sl(Hc, axis, 0, 1) * (1.0 if lo == "N" else -1.0)
        g_hi = _sl(Hc, axis, -1, None) * (1.0 if hi == "N" else -1.0)
        return _diff(torch.cat([g_lo, Hc, g_hi], dim=axis), axis) / self.Df[axis]

    def divergence(self, u, v, w):
        return _diff(u, 0) / self.Dc[0] + _diff(v, 1) / self.Dc[1] + _diff(w, 2) / self.Dc[2]

    def project(self, u, v, w, D, coef):
        rhs = (self.divergence(u, v, w) - D) / coef
        Hc = self.poisson(rhs)
        return (u - coef * self._grad_face(Hc, 0), v - coef * self._grad_face(Hc, 1),
                w - coef * self._grad_face(Hc, 2), Hc)

    # ------------------------------------------------------------ propriedades
    def _lookup(self, tab, Z, s):
        fz = Z.clamp(0, 1) * (self.nZt - 1)
        fs = (s / self.s_max).clamp(0, 1) * (self.ns - 1)
        iz = fz.floor().clamp(max=self.nZt - 2).long()
        js = fs.floor().clamp(max=self.ns - 2).long()
        wz = fz - iz
        ws = fs - js
        f = tab.reshape(-1)
        b = iz * self.ns + js
        return ((1 - wz) * (1 - ws) * f[b] + wz * (1 - ws) * f[b + self.ns]
                + (1 - wz) * ws * f[b + 1] + wz * ws * f[b + self.ns + 1])

    def _cgrad(self, q, axis):
        """Derivada centrada de um campo de centro, ao longo de axis."""
        qp = _pad(q, axis)
        dist = _sl(self.Df[axis], axis, 0, -1) + _sl(self.Df[axis], axis, 1, None)
        return (_sl(qp, axis, 2, None) - _sl(qp, axis, 0, -2)) / dist

    def _svar(self, Z):
        g2 = self._cgrad(Z, 0) ** 2 + self._cgrad(Z, 1) ** 2 + self._cgrad(Z, 2) ** 2
        var = self.cfg.C_Z * self.delta ** 2 * g2
        return (var / (Z * (1 - Z) + 1e-8)).clamp(0, self.s_max)

    def _update_props(self, Z):
        s = self._svar(Z)
        self.s = s
        self.rho = self._lookup(self.tab_rho, Z, s)
        self.drho = self._lookup(self.tab_drho, Z, s)

    # --------------------------------------------------------- turbulência
    def _nu_t(self, u, v, w):
        """Viscosidade de submalha: Smagorinsky ou WALE (Nicoud & Ducros 1999)."""
        uc, vc, wc = _avg(u, 0), _avg(v, 1), _avg(w, 2)
        g = [[None] * 3 for _ in range(3)]
        for i, (q, qc) in enumerate(((u, uc), (v, vc), (w, wc))):
            for j in range(3):
                g[i][j] = _diff(q, j) / self.Dc[j] if j == i else self._cgrad(qc, j)
        SS = 0.0
        for i in range(3):
            for j in range(i, 3):
                Sij = 0.5 * (g[i][j] + g[j][i])
                SS = SS + (1.0 if i == j else 2.0) * Sij * Sij
        if self.cfg.sgs == "wale":
            g2 = [[sum(g[i][k] * g[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
            tr = (g2[0][0] + g2[1][1] + g2[2][2]) / 3.0
            SdSd = 0.0
            for i in range(3):
                for j in range(i, 3):
                    Sd = 0.5 * (g2[i][j] + g2[j][i]) - (tr if i == j else 0.0)
                    SdSd = SdSd + (1.0 if i == j else 2.0) * Sd * Sd
            num = SdSd ** 1.5
            den = SS ** 2.5 + SdSd ** 1.25 + 1e-12
            return (self.cfg.Cw * self.delta) ** 2 * num / den
        return (self.cfg.Cs * self.delta) ** 2 * torch.sqrt(2.0 * SS)

    # ------------------------------------------------------------- momento
    def _spacings(self, comp, axis):
        """Espaçamento local h (advecção), distâncias h−/h+ e largura de controle (difusão)
        para a componente de velocidade comp ao longo de axis."""
        if comp == axis:   # variável nas faces ao longo de axis: vizinhas separadas por Δc
            dc = self.Dc[axis]
            hm = torch.cat([_sl(dc, axis, 0, 1), dc], dim=axis)
            hp = torch.cat([dc, _sl(dc, axis, -1, None)], dim=axis)
            return 0.5 * (hm + hp), hm, hp, self.Dcf[axis]
        dfa = self.Df[axis]
        return self.Dc[axis], _sl(dfa, axis, 0, -1), _sl(dfa, axis, 1, None), self.Dc[axis]

    def _adv_visc(self, comp, q, adv, mu_q, rho_q):
        """Upwind de 3ª ordem (= central de 4ª ordem + dissipação |a|h³/12 ∂⁴q) e ∇·(μ∇q)/ρ."""
        beta = self.cfg.upwind
        A = 0.0
        Vs = 0.0
        for axis, a in enumerate(adv):
            h, hm, hp, hc = self._spacings(comp, axis)
            qp = _pad(q, axis, 2)
            n = q.shape[axis]
            qm2, qm1 = _sl(qp, axis, 0, n), _sl(qp, axis, 1, n + 1)
            qp1, qp2 = _sl(qp, axis, 3, n + 3), _sl(qp, axis, 4, n + 4)
            dpos = (2 * qp1 + 3 * q - 6 * qm1 + qm2) / (6 * h)
            dneg = (-qp2 + 6 * qp1 - 3 * q - 2 * qm1) / (6 * h)
            d3 = torch.where(a >= 0, dpos, dneg)
            if beta > 0:
                d1 = torch.where(a >= 0, (q - qm1) / hm, (qp1 - q) / hp)
                d3 = (1 - beta) * d3 + beta * d1
            A = A + a * d3
            mp = _pad(mu_q, axis)
            mu_p = 0.5 * (mu_q + _sl(mp, axis, 2, None))
            mu_m = 0.5 * (mu_q + _sl(mp, axis, 0, -2))
            Vs = Vs + (mu_p * (qp1 - q) / hp - mu_m * (q - qm1) / hm) / hc
        return A - Vs / rho_q

    def _momentum_rhs(self, u, v, w, rho, Hc):
        cfg = self.cfg
        mu = rho * (self._nu_t(u, v, w) + 1.5e-5)
        uc, vc, wc = _avg(u, 0), _avg(v, 1), _avg(w, 2)
        ru, rv, rw = _to_faces(rho, 0), _to_faces(rho, 1), _to_faces(rho, 2)
        Fu = self._adv_visc(0, u, (u, _to_faces(vc, 0), _to_faces(wc, 0)), _to_faces(mu, 0), ru)
        Fv = self._adv_visc(1, v, (_to_faces(uc, 1), v, _to_faces(wc, 1)), _to_faces(mu, 1), rv)
        Fw = self._adv_visc(2, w, (_to_faces(uc, 2), _to_faces(vc, 2), w), _to_faces(mu, 2), rw)
        Fw = Fw + G * (rw - self.rho_inf) / rw                     # empuxo
        if cfg.baroclinic:                                          # −p̃∇(1/ρ) = H∇ρ/ρ
            Fu = Fu + _to_faces(Hc, 0) * _diff(_pad(rho, 0), 0) / self.Df[0] / ru
            Fv = Fv + _to_faces(Hc, 1) * _diff(_pad(rho, 1), 1) / self.Df[1] / rv
            Fw = Fw + _to_faces(Hc, 2) * _diff(_pad(rho, 2), 2) / self.Df[2] / rw
        # fonte de combustível: ρ Du/Dt += S_m (u_inj − u), com u_inj = (0, 0, u_jet)
        Fu = Fu + self.Sm_u * u / ru
        Fv = Fv + self.Sm_v * v / rv
        Fw = Fw - self.Sm_w * (cfg.u_jet - w) / rw
        if self.wind:                                               # tensão de parede (lei log)
            h0 = float(self.dc[2][0])
            u0, v0 = _sl(u, 2, 0, 1), _sl(v, 2, 0, 1)
            spd_u = torch.sqrt(u0 ** 2 + _to_faces(_sl(vc, 2, 0, 1), 0) ** 2) + 1e-6
            spd_v = torch.sqrt(_to_faces(_sl(uc, 2, 0, 1), 1) ** 2 + v0 ** 2) + 1e-6
            Fu = torch.cat([_sl(Fu, 2, 0, 1) + self.Cd_wall * spd_u * u0 / h0, _sl(Fu, 2, 1, None)], 2)
            Fv = torch.cat([_sl(Fv, 2, 0, 1) + self.Cd_wall * spd_v * v0 / h0, _sl(Fv, 2, 1, None)], 2)
        return Fu, Fv, Fw, mu

    # -------------------------------------------------- fração de mistura
    def _tvd_face(self, Z, a, axis):
        n = Z.shape[axis]
        Zp = _pad(Z, axis, 2)
        ZLL, ZL = _sl(Zp, axis, 0, n + 1), _sl(Zp, axis, 1, n + 2)
        ZR, ZRR = _sl(Zp, axis, 2, n + 3), _sl(Zp, axis, 3, n + 4)

        lim = self.cfg.limiter

        def vl(num, den):
            den = torch.where(den.abs() < 1e-12, torch.full_like(den, 1e-12), den)
            r = num / den
            if lim == "superbee":
                return torch.maximum(torch.clamp(2 * r, max=1.0), torch.clamp(r, max=2.0)).clamp(min=0.0)
            if lim == "mc":
                return torch.minimum(torch.minimum(2 * r, 0.5 * (1 + r)), torch.full_like(r, 2.0)).clamp(min=0.0)
            return (r + r.abs()) / (1 + r.abs())
        Zpos = ZL + 0.5 * vl(ZL - ZLL, ZR - ZL) * (ZR - ZL)
        Zneg = ZR + 0.5 * vl(ZR - ZRR, ZL - ZR) * (ZL - ZR)
        Zf = torch.where(a >= 0, Zpos, Zneg)
        lo, hi = _sl(Zf, axis, 0, 1), _sl(Zf, axis, -1, None)      # bordas: entra ar (Z = 0)
        lo = torch.where(_sl(a, axis, 0, 1) > 0, torch.zeros_like(lo), lo)
        hi = torch.where(_sl(a, axis, -1, None) < 0, torch.zeros_like(hi), hi)
        return torch.cat([lo, _sl(Zf, axis, 1, -1), hi], dim=axis)

    def _z_adv(self, Z, u, v, w):
        """−∇·(uZ) + Z∇·u com faces TVD."""
        adv = 0.0
        for axis, a in enumerate((u, v, w)):
            adv = adv + _diff(a * self._tvd_face(Z, a, axis), axis) / self.Dc[axis]
        return -adv + Z * self.divergence(u, v, w)

    def _z_diff_src(self, Z, mu):
        """∇·(ρD_t∇Z) + S_m(1 − Z)  [kg/(m3 s)]."""
        rhoD = mu / self.cfg.Sc_t
        dif = 0.0
        for axis in range(3):
            flux = _to_faces(rhoD, axis) * _diff(_pad(Z, axis), axis) / self.Df[axis]
            dif = dif + _diff(flux, axis) / self.Dc[axis]
        return dif + self.Sm * (1.0 - Z)

    def _divergence_target(self, rho, drho, DZ_rho):
        return self.Sm / rho - drho * DZ_rho / (rho * rho)

    # --------------------------------------------------------------- passo
    def _apply_bc(self, u, v, w):
        if self.wind:
            u = torch.cat([self.U_in * (1.0 + self.noise), u[1:]], 0)
        w = torch.cat([torch.zeros_like(w[:, :, :1]), w[:, :, 1:]], 2)
        return u, v, w

    def _compute_dt(self):
        uc, vc, wc = _avg(self.u, 0).abs(), _avg(self.v, 1).abs(), _avg(self.w, 2).abs()
        rate = (uc / self.Dc[0] + vc / self.Dc[1] + wc / self.Dc[2]).max().item()
        dt = self.cfg.cfl / max(rate, 1e-6)
        if self._numax > 0:
            dt = min(dt, 0.45 / self._numax)
        dt = min(dt, self.cfg.dt_max)
        return dt, rate * dt

    def step(self):
        t0 = time.perf_counter()
        dt, cfl = self._compute_dt()
        self.dt = dt
        cfg = self.cfg
        if self.wind and cfg.inflow_noise > 0:
            # ruído de entrada: AR(1) no tempo, suavizado na vertical
            eps = torch.randn_like(self.noise)
            eps = torch.nn.functional.avg_pool1d(eps.reshape(-1, 1, self.nz), 5, 1, 2).reshape(self.noise.shape)
            a = math.exp(-dt / 2.0)
            self.noise = a * self.noise + math.sqrt(1 - a * a) * cfg.inflow_noise * eps * 2.2
        if cfg.jet_noise > 0:
            # semente de turbulência do jato: impulsos horizontais aleatórios nas faces da fonte
            amp = cfg.jet_noise * cfg.u_jet ** 0.5 * 3.0 * math.sqrt(dt)
            self.u = self.u + self.src_u * torch.randn_like(self.u) * amp
            self.v = self.v + self.src_v * torch.randn_like(self.v) * amp
        u0, v0, w0, Z0, rho0, H0 = self.u, self.v, self.w, self.Z, self.rho, self.Hp
        # ---- estágio 1 (preditor)
        Fu, Fv, Fw, mu = self._momentum_rhs(u0, v0, w0, rho0, H0)
        RZ = self._z_adv(Z0, u0, v0, w0) + self._z_diff_src(Z0, mu) / rho0
        Z1 = (Z0 + dt * RZ).clamp(0, 1)
        self._update_props(Z1)
        rho1, drho1 = self.rho, self.drho
        D1 = self._divergence_target(rho1, drho1, self._z_diff_src(Z1, mu * (rho1 / rho0)))
        u1, v1, w1 = self._apply_bc(u0 - dt * Fu, v0 - dt * Fv, w0 - dt * Fw)
        u1, v1, w1, H1 = self.project(u1, v1, w1, D1, dt)
        # ---- estágio 2 (corretor)
        Fu, Fv, Fw, mu1 = self._momentum_rhs(u1, v1, w1, rho1, H1)
        RZ = self._z_adv(Z1, u1, v1, w1) + self._z_diff_src(Z1, mu1) / rho1
        Z2 = (0.5 * (Z0 + Z1 + dt * RZ)).clamp(0, 1)
        self._update_props(Z2)
        rho2, drho2 = self.rho, self.drho
        D2 = self._divergence_target(rho2, drho2, self._z_diff_src(Z2, mu1 * (rho2 / rho1)))
        u2, v2, w2 = self._apply_bc(0.5 * (u0 + u1 - dt * Fu), 0.5 * (v0 + v1 - dt * Fv),
                                    0.5 * (w0 + w1 - dt * Fw))
        u2, v2, w2, H2 = self.project(u2, v2, w2, D2, 0.5 * dt)
        self.u, self.v, self.w, self.Z, self.Hp = u2, v2, w2, Z2, H2
        self._numax = ((mu1 / rho1) / cfg.Sc_t * 2.0 * self.inv_d2).max().item()
        if not math.isfinite(self._numax) or not torch.isfinite(self.w).all():
            raise FloatingPointError(f"a simulação divergiu em t = {self.time:.2f} s")
        self.time += dt
        self.step_n += 1
        if self.dev.type == "cuda":
            torch.cuda.synchronize()
        self.wall += time.perf_counter() - t0
        self._last_cfl = cfl
        return dt

    # ---------------------------------------------------------- diagnósticos
    def fields(self):
        """T̃, emissão luminosa (não normalizada) e máscara da chama (Z̃ ≥ Z_st)."""
        T = self._lookup(self.tab_T, self.Z, self.s)
        e = self._lookup(self.tab_e, self.Z, self.s)
        return T, e, self.Z >= self.Z_st

    def ground_flux(self, e):
        """Fluxo incidente no solo (pior orientação, seção 3.8): soma volumétrica dos emissores
        com transmissividade de Wayne, potência total escalada para X_rad·Q (como no FDS)."""
        cfg = self.cfg
        P = (e * self.vol).reshape(-1)
        keep = P > 1e-4 * P.max().clamp(min=1e-30)
        P, xyz = P[keep], self.cell_xyz[keep]
        if len(P) == 0:
            return torch.zeros(len(self.receivers), dtype=self.ft, device=self.dev)
        # agrupa emissores em blocos (centroide ponderado pela potência)
        key = torch.floor(xyz / cfg.emitter_bin).long()
        key = key - key.min(0).values
        dims = key.max(0).values + 1
        lin = (key[:, 0] * dims[1] + key[:, 1]) * dims[2] + key[:, 2]
        uniq, inv = torch.unique(lin, return_inverse=True)
        Pb = torch.zeros(len(uniq), dtype=self.ft, device=self.dev).index_add_(0, inv, P)
        Xb = torch.zeros(len(uniq), 3, dtype=self.ft, device=self.dev).index_add_(0, inv, P[:, None] * xyz)
        Xb = Xb / Pb[:, None]
        scale = cfg.X_rad * self.Q / Pb.sum()
        psat = math.exp(20.386 - 5132.0 / cfg.T_inf)
        V = torch.zeros_like(self.receivers)
        for i0 in range(0, len(Pb), 2048):
            dv = Xb[None, i0:i0 + 2048] - self.receivers[:, None]
            r = torch.linalg.norm(dv, dim=-1).clamp(min=0.5)
            lw = torch.log10(cfg.RH * r * psat * 2.88651e2 / cfg.T_inf)
            lc = torch.log10(r * 273.0 / cfg.T_inf)
            tau = (1.006 - 0.01171 * lw - 0.02368 * lw ** 2 - 0.03188 * lc + 0.001164 * lc ** 2).clamp(0, 1)
            wgt = Pb[None, i0:i0 + 2048] * tau / (4 * math.pi * r ** 3)
            V += (wgt[..., None] * dv).sum(1)
        return torch.linalg.norm(V, dim=1) * scale

    def _centroid_tilt(self, mask):
        if not mask.any():
            return float("nan")
        c = self.cell_xyz[mask.reshape(-1)].mean(0).cpu().numpy() - self.tip
        return math.degrees(math.atan2(math.hypot(c[0], c[1]), max(c[2], 1e-6)))

    def diagnostics(self, averaging: bool):
        T, e, mask = self.fields()
        q = self.ground_flux(e)
        self.q_inst = q
        L = torch.where(mask, self.dist_tip, torch.zeros_like(self.dist_tip)).max().item()
        h = self.history
        h["t"].append(self.time); h["L"].append(L); h["tilt"].append(self._centroid_tilt(mask))
        h["qmax"].append(q.max().item()); h["Tmax"].append(T.max().item()); h["dt"].append(self.dt)
        h["cfl"].append(self._last_cfl)
        if averaging:
            self.avg_n += 1.0
            self.avg_T += T
            self.avg_I += mask.to(self.ft)
            self.avg_q += q
        return T, e, mask, q

    def mean_flame_length(self, threshold: float = 0.5):
        if self.avg_n == 0:
            return float("nan")
        I = self.avg_I / self.avg_n
        return torch.where(I >= threshold, self.dist_tip, torch.zeros_like(self.dist_tip)).max().item()

    def mean_tilt(self, threshold: float = 0.5):
        if self.avg_n == 0:
            return float("nan")
        return self._centroid_tilt(self.avg_I / self.avg_n >= threshold)

    def q_grid(self, q):
        return q.reshape(len(self.rec_x), len(self.rec_y)).cpu().numpy()

    def slice_y0(self, f):
        return f[:, self.j_mid, :].float().cpu().numpy()

    def mass_balance(self):
        """Massa no domínio e vazão volumétrica líquida pelas fronteiras."""
        m = (self.rho * self.vol).sum().item()
        A_x = torch.outer(self._t(self.dc[1]), self._t(self.dc[2]))
        A_y = torch.outer(self._t(self.dc[0]), self._t(self.dc[2]))
        A_z = torch.outer(self._t(self.dc[0]), self._t(self.dc[1]))
        out = ((self.u[-1] - self.u[0]) * A_x).sum() + ((self.v[:, -1] - self.v[:, 0]) * A_y).sum() \
            + (self.w[:, :, -1] * A_z).sum()
        return m, out.item()

    def summary(self) -> str:
        dmin = min(float(d.min()) for d in self.dc)
        dmax = max(float(d.max()) for d in self.dc)
        return (f"{self.nx}×{self.ny}×{self.nz} = {self.n_cells / 1e6:.2f} M células · Δ {dmin:.2f}–{dmax:.2f} m · "
                f"fonte {self.src_area:.2f} m² · {self.dev.type.upper()}")
