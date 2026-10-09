"""Imagem 3D do reator em corte (ray marching de funções de distância em PyTorch; GPU quando houver).

Cena (referencial do laboratório; o agitador gira de θ):
  * vaso encamisado de aço com um quarto removido de frente para a câmera (corte em cunha);
  * dupla fita helicoidal (a mesma função de distância usada na malha), em aço polido;
  * o líquido aparece como um sólido opaco cortado pela cunha: as faces do corte e a superfície livre
    são coloridas pelo campo escolhido (temperatura, massa molar, viscosidade…), amostrado na solução
    do referencial girante — no laboratório, a solução estacionária só gira junto com a fita.

Sem malha poligonal: a geometria é traçada direto das SDFs (sphere tracing), com normais por diferenças,
oclusão ambiente barata, especular de Blinn-Phong e tone mapping. Antisserrilhado por supersampling.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn.functional as F


def _lut(name: str, n: int = 256, dev=None):
    import matplotlib
    cm = matplotlib.colormaps[name]
    return torch.tensor(cm(np.linspace(0, 1, n))[:, :3], dtype=torch.float32, device=dev)


def _rotz(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    x, y = p[..., 0], p[..., 1]
    return torch.stack([c * x - s * y, s * x + c * y, p[..., 2]], -1)


class Cutaway:
    """Renderizador do reator em corte. fields: {nome: tensor [nx, ny, nz] nos centros da malha}."""

    MAT_LIQ, MAT_IMP, MAT_SHELL, MAT_JACKET = 0, 1, 2, 3

    def __init__(self, tank, xc, yc, zc, device=None, wall: float = 0.012, jacket_gap: float = 0.03,
                 jacket: float = 0.010, cut_deg: float = 100.0):
        self.tank = tank
        self.dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.R, self.H = tank.R, tank.H_L
        self.wall, self.jg, self.jt = wall, jacket_gap, jacket
        self.H_top = self.H + 0.10 * tank.T           # o vaso continua acima do nível do líquido
        self.cut = math.radians(cut_deg)
        self.xc, self.yc, self.zc = (float(xc[0]), float(xc[-1])), (float(yc[0]), float(yc[-1])), \
            (float(zc[0]), float(zc[-1]))
        self.fields = {}

    # ------------------------------------------------------------------ campos
    def set_field(self, name, values, cmap="inferno", vmin=None, vmax=None, log=False, fluid=None):
        v = torch.as_tensor(values, dtype=torch.float32, device=self.dev)
        if fluid is not None:   # estende o campo um pouco para dentro das paredes (amostragem na borda)
            from .ops import extend_into_solid
            v = extend_into_solid(v, torch.as_tensor(fluid, device=self.dev) > 0.5, passes=3)
        if log:
            v = torch.log10(v.clamp(min=1e-30))
        lo = float(v.min()) if vmin is None else (math.log10(vmin) if log else vmin)
        hi = float(v.max()) if vmax is None else (math.log10(vmax) if log else vmax)
        self.fields[name] = dict(vol=v.permute(2, 1, 0)[None, None].contiguous(), lut=_lut(cmap, dev=self.dev),
                                 lo=lo, hi=hi, log=log, cmap=cmap)

    def _sample(self, name, p_rot):
        f = self.fields[name]
        g = torch.stack([(p_rot[..., 0] - self.xc[0]) / (self.xc[1] - self.xc[0]) * 2 - 1,
                         (p_rot[..., 1] - self.yc[0]) / (self.yc[1] - self.yc[0]) * 2 - 1,
                         (p_rot[..., 2] - self.zc[0]) / (self.zc[1] - self.zc[0]) * 2 - 1], -1)
        val = F.grid_sample(f["vol"], g.view(1, -1, 1, 1, 3), mode="bilinear", padding_mode="border",
                            align_corners=True).view(-1)
        x = ((val - f["lo"]) / max(f["hi"] - f["lo"], 1e-12)).clamp(0, 1)
        idx = (x * (f["lut"].shape[0] - 1)).long()
        return f["lut"][idx]

    # ------------------------------------------------------------------- SDFs
    def _wedge(self, p, phi_c):
        """SDF (negativa dentro) da cunha removida, centrada no azimute phi_c e com abertura self.cut."""
        a1, a2 = phi_c - 0.5 * self.cut, phi_c + 0.5 * self.cut
        n1 = (-math.sin(a1), math.cos(a1))           # normais para dentro da cunha
        n2 = (math.sin(a2), -math.cos(a2))
        d1 = p[..., 0] * n1[0] + p[..., 1] * n1[1]
        d2 = p[..., 0] * n2[0] + p[..., 1] * n2[1]
        return torch.maximum(-d1, -d2)

    def _scene(self, p, theta, phi_c):
        r = torch.hypot(p[..., 0], p[..., 1])
        z = p[..., 2]
        wedge = self._wedge(p, phi_c)
        # líquido (cilindro) sem a cunha
        liq = torch.maximum(torch.maximum(r - self.R, torch.maximum(-z, z - self.H)), -wedge)
        # agitador (no referencial dele) e eixo até o motor
        pr = _rotz(p, -theta)
        imp = self.tank.impeller.sdf(pr)
        imp = torch.maximum(imp, z - (self.H_top + 0.25 * self.tank.T))
        # vaso: parede e fundo, sem a cunha
        Ro = self.R + self.wall
        outer = torch.maximum(r - Ro, torch.maximum(-self.wall - z, z - self.H_top))
        inner = torch.maximum(r - self.R, torch.maximum(-z, z - self.H_top - 1.0))
        shell = torch.maximum(torch.maximum(outer, -inner), -wedge)
        # camisa: segunda casca, mais baixa, com folga
        Rj0, Rj1 = Ro + self.jg, Ro + self.jg + self.jt
        jac = torch.maximum(torch.maximum(r - Rj1, Rj0 - r), torch.maximum(0.06 * self.H - z, z - 0.96 * self.H))
        jac = torch.maximum(jac, -wedge)
        d = torch.stack([liq, imp, shell, jac], -1)
        dmin, mat = d.min(-1)
        return dmin, mat

    # ------------------------------------------------------------------ câmera
    def _rays(self, W, H, az, el, dist, fov, target):
        az, el = math.radians(az), math.radians(el)
        eye = torch.tensor([target[0] + dist * math.cos(el) * math.cos(az),
                            target[1] + dist * math.cos(el) * math.sin(az),
                            target[2] + dist * math.sin(el)], device=self.dev)
        tgt = torch.tensor(target, device=self.dev, dtype=torch.float32)
        fwd = F.normalize(tgt - eye, dim=0)
        right = F.normalize(torch.linalg.cross(fwd, torch.tensor([0.0, 0.0, 1.0], device=self.dev)), dim=0)
        up = torch.linalg.cross(right, fwd)
        th = math.tan(math.radians(fov) / 2)
        xs = (torch.arange(W, device=self.dev) + 0.5) / W * 2 - 1
        ys = 1 - (torch.arange(H, device=self.dev) + 0.5) / H * 2
        Y, X = torch.meshgrid(ys, xs, indexing="ij")
        d = fwd + X[..., None] * th * (W / H) * right + Y[..., None] * th * up
        return eye.expand(H, W, 3).reshape(-1, 3), F.normalize(d, dim=-1).reshape(-1, 3)

    # ---------------------------------------------------------------- desenho
    @torch.no_grad()
    def render(self, field: str, theta: float = 0.0, az: float = -60.0, el: float = 24.0, dist: float | None = None,
               size=(1920, 1080), ssaa: float = 1.5, fov: float = 32.0, background=None, max_steps: int = 140,
               exposure: float = 1.0) -> np.ndarray:
        W0, H0 = size
        W, H = int(W0 * ssaa), int(H0 * ssaa)
        T = self.tank.T
        dist = dist or 3.1 * T
        target = (0.0, 0.0, 0.47 * self.H)
        o, d = self._rays(W, H, az, el, dist, fov, target)
        phi_c = math.radians(az)                       # a cunha aponta para a câmera
        n = o.shape[0]
        t = torch.zeros(n, device=self.dev)
        hit = torch.zeros(n, dtype=torch.bool, device=self.dev)
        alive = torch.ones(n, dtype=torch.bool, device=self.dev)
        far = dist + 3 * T
        eps = 4e-4 * T
        idx = torch.arange(n, device=self.dev)
        for _ in range(max_steps):
            ia = idx[alive]
            if ia.numel() == 0:
                break
            p = o[ia] + t[ia, None] * d[ia]
            dd, _ = self._scene(p, theta, phi_c)
            close = dd < eps
            hit[ia[close]] = True
            t[ia] = t[ia] + dd.clamp(min=0.25 * eps) * 0.9
            gone = close | (t[ia] > far)
            alive[ia[gone]] = False
        img = self._background(H, W) if background is None else background
        img = img.reshape(-1, 3).clone()
        ih = idx[hit]
        if ih.numel():
            p = o[ih] + t[ih, None] * d[ih]
            _, mat = self._scene(p, theta, phi_c)
            e = 5e-4 * T
            nrm = torch.zeros_like(p)
            for k in range(3):
                dp = torch.zeros(3, device=self.dev)
                dp[k] = e
                nrm[:, k] = self._scene(p + dp, theta, phi_c)[0] - self._scene(p - dp, theta, phi_c)[0]
            nrm = F.normalize(nrm, dim=-1)
            col = self._shade(p, nrm, -d[ih], mat, field, theta, phi_c)
            img[ih] = col
        img = img.reshape(H, W, 3)
        img = 1 - torch.exp(-exposure * img * 1.6)                       # tone mapping suave
        img = img.clamp(0, 1) ** (1 / 2.2)
        if ssaa != 1.0:
            img = F.interpolate(img.permute(2, 0, 1)[None], size=(H0, W0), mode="area")[0].permute(1, 2, 0)
        return (img * 255).round().byte().cpu().numpy()

    def _background(self, H, W):
        yy = torch.linspace(0, 1, H, device=self.dev)[:, None, None]
        top = torch.tensor([0.020, 0.028, 0.045], device=self.dev)
        bot = torch.tensor([0.050, 0.062, 0.085], device=self.dev)
        bg = top + (bot - top) * yy
        return bg.expand(H, W, 3)

    def _ao(self, p, nrm, theta, phi_c):
        T = self.tank.T
        occ = torch.zeros(p.shape[0], device=self.dev)
        for k, h in enumerate((0.01, 0.025, 0.05, 0.09)):
            hh = h * T
            dd = self._scene(p + nrm * hh, theta, phi_c)[0]
            occ = occ + (hh - dd).clamp(min=0) / hh * 0.5 ** k
        return (1 - 0.55 * occ).clamp(0.25, 1.0)

    def _shade(self, p, nrm, view, mat, field, theta, phi_c):
        dev = self.dev
        L1 = F.normalize(torch.tensor([0.4, -0.6, 0.9], device=dev), dim=0)    # luz principal
        L2 = F.normalize(torch.tensor([-0.7, 0.5, 0.35], device=dev), dim=0)   # contraluz fria
        ndl1 = (nrm @ L1).clamp(min=0)[:, None]
        ndl2 = (nrm @ L2).clamp(min=0)[:, None]
        hv = F.normalize(L1 + view, dim=-1)
        spec = (nrm * hv).sum(-1).clamp(min=0)[:, None]
        ao = self._ao(p, nrm, theta, phi_c)[:, None]
        fres = (1 - (nrm * view).sum(-1).clamp(0, 1))[:, None] ** 5
        out = torch.zeros_like(p)
        # líquido: cor do campo, levemente sombreada (o corte é "pintado" pelo resultado)
        m = mat == self.MAT_LIQ
        if m.any():
            c = self._sample(field, _rotz(p[m], -theta)) if field in self.fields else \
                torch.tensor([0.9, 0.5, 0.2], device=dev).expand(int(m.sum()), 3)
            lin = c ** 2.2
            out[m] = lin * (0.55 + 0.45 * ndl1[m]) * ao[m] * 1.15 + 0.06 * spec[m] ** 40
        # agitador: aço polido
        m = mat == self.MAT_IMP
        if m.any():
            base = torch.tensor([0.56, 0.58, 0.62], device=dev)
            out[m] = (base * (0.10 + 0.70 * ndl1[m] + 0.25 * ndl2[m]) * ao[m] + 0.9 * spec[m] ** 60
                      + 0.25 * fres[m] * torch.tensor([0.6, 0.7, 0.9], device=dev))
        # vaso: aço escovado; faces internas mais claras
        m = mat == self.MAT_SHELL
        if m.any():
            r = torch.hypot(p[m, 0], p[m, 1])
            inside = (r < self.R + 0.5 * self.wall)[:, None]
            base = torch.where(inside, torch.tensor([0.36, 0.38, 0.42], device=dev),
                               torch.tensor([0.24, 0.26, 0.30], device=dev))
            out[m] = base * (0.12 + 0.75 * ndl1[m] + 0.2 * ndl2[m]) * ao[m] + 0.35 * spec[m] ** 30
        # camisa de aquecimento: cobre/laranja
        m = mat == self.MAT_JACKET
        if m.any():
            base = torch.tensor([0.62, 0.30, 0.12], device=dev)
            out[m] = base * (0.12 + 0.75 * ndl1[m] + 0.2 * ndl2[m]) * ao[m] + 0.5 * spec[m] ** 40
        return out
