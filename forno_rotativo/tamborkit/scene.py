"""Cena em corte transversal do tambor dentro da fornalha (estilo dos infográficos de forno rotativo).

Camadas, de trás para a frente: fundo; caixa da fornalha (aço + refratário aquecido); gás de combustão e
chamas (fatia da LES no plano de um queimador, cor de corpo negro); casco do tambor colorido pela
temperatura (setores no referencial do tambor, girando); aletas; carga (partículas do DEM projetadas ao
longo do eixo, com oclusão por z-buffer e sombreamento de esfera; ou a poça de fundido); vapores.
Tudo em NumPy + PIL; sem matplotlib no quadro principal.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .video import _font, br

# ------------------------------------------------------------------ cores
_TSTOPS = [(20, (40, 70, 160)), (100, (40, 150, 190)), (200, (80, 190, 150)), (300, (230, 210, 80)),
           (400, (245, 150, 40)), (480, (225, 70, 30)), (560, (170, 20, 30)), (650, (255, 235, 220))]


def thermal_rgb(T_C):
    """Mapa de cor de temperatura da carga e do casco (azul frio → amarelo → vermelho → branco)."""
    T = np.asarray(T_C, float)
    xs = np.array([s[0] for s in _TSTOPS], float)
    cs = np.array([s[1] for s in _TSTOPS], float)
    return np.stack([np.interp(T, xs, cs[:, i]) for i in range(3)], -1)


def flame_rgba(T_K):
    """Cor e opacidade de chama/gás quente (aprox. corpo negro, intensidade ~ T⁴)."""
    T = np.asarray(T_K, float)
    stops = np.array([900, 1100, 1300, 1500, 1700, 2000], float)
    cols = np.array([(120, 20, 5), (200, 50, 10), (245, 110, 20), (255, 170, 50), (255, 215, 120),
                     (255, 245, 210)], float)
    rgb = np.stack([np.interp(T, stops, cols[:, i]) for i in range(3)], -1)
    a = np.clip((T - 850.0) / 550.0, 0, 1) ** 1.1
    return rgb, a


def colorbar(width, height, Tmin=20, Tmax=600, label="temperatura da carga e do casco (°C)", s=1.0):
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bar_h = int(14 * s)
    xs = np.linspace(Tmin, Tmax, width - 2)
    rgb = thermal_rgb(xs).astype(np.uint8)
    bar = np.repeat(rgb[None], bar_h, 0)
    im.paste(Image.fromarray(bar), (1, int(26 * s)))
    f = _font(int(15 * s))
    d.text((0, 0), label, font=f, fill=(225, 225, 225, 255))
    for T in range(int(Tmin // 100 * 100 + 100), int(Tmax) + 1, 100):
        x = int(1 + (T - Tmin) / (Tmax - Tmin) * (width - 3))
        d.text((x - 12 * s, int(26 * s) + bar_h + 2), f"{T}", font=_font(int(13 * s)), fill=(200, 200, 200, 255))
    return im


# ------------------------------------------------------------- esferas
def splat_spheres(H, W, cx, cy, r, depth, rgb, light=(-0.45, -0.6, 0.66)):
    """Desenha esferas (centros em pixels, raio em pixels) com z-buffer e sombreamento difuso + brilho.

    depth: menor = mais perto da câmera. Devolve (imagem RGB float [H, W, 3], alfa [H, W])."""
    n = len(cx)
    out = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    if n == 0:
        return out, alpha
    zbuf = np.full(H * W, np.inf, np.float32)
    owner = np.full(H * W, -1, np.int64)
    Rm = int(np.ceil(r.max())) + 1
    oy, ox = np.mgrid[-Rm:Rm + 1, -Rm:Rm + 1]
    ox = ox.ravel().astype(np.float32); oy = oy.ravel().astype(np.float32)
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    # processa em blocos para limitar memória
    nn = np.zeros((H * W, 3), np.float32)
    for b0 in range(0, n, 2048):
        sl = slice(b0, min(n, b0 + 2048))
        px = np.floor(cx[sl, None]) + ox[None]
        py = np.floor(cy[sl, None]) + oy[None]
        dx = (px + 0.5 - cx[sl, None]) / r[sl, None]
        dy = (py + 0.5 - cy[sl, None]) / r[sl, None]
        q = dx * dx + dy * dy
        ok = (q < 1.0) & (px >= 0) & (px < W) & (py >= 0) & (py < H)
        dz = np.sqrt(np.clip(1 - q, 0, 1))
        d = depth[sl, None] - dz * r[sl, None] * 1e-3
        ids = (py * W + px).astype(np.int64)
        ids_ok, d_ok = ids[ok], d[ok]
        pid = np.broadcast_to(np.arange(sl.start, sl.stop)[:, None], ok.shape)[ok]
        # ordena por profundidade decrescente e escreve: o mais perto fica por último (vence)
        order = np.argsort(-d_ok, kind="stable")
        ids_o, d_o, pid_o = ids_ok[order], d_ok[order], pid[order]
        closer = d_o < zbuf[ids_o]
        ids_c, d_c, pid_c = ids_o[closer], d_o[closer], pid_o[closer]
        zbuf[ids_c] = d_c
        owner[ids_c] = pid_c
        nx_ = dx[ok][order][closer]; ny_ = dy[ok][order][closer]; nz_ = dz[ok][order][closer]
        nn[ids_c] = np.stack([nx_, ny_, nz_], -1)
    hit = owner >= 0
    nrm = nn[hit]
    lam = np.clip(nrm @ L, 0, 1)
    Hv = L + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
    spec = np.clip(nrm @ Hv, 0, 1) ** 24
    col = rgb[owner[hit]].astype(np.float32)
    shade = 0.32 + 0.78 * lam
    pix = col * shade[:, None] + 90.0 * spec[:, None]
    out.reshape(-1, 3)[hit] = np.clip(pix, 0, 255)
    alpha.reshape(-1)[hit] = 1.0
    return out, alpha


# ------------------------------------------------------------- a cena
class CrossSection:
    """Corte do conjunto tambor + fornalha no plano (y, z), em pixels."""

    def __init__(self, drum, furnace_box, size=(1080, 1080), center=None, scale=None):
        self.drum = drum
        self.box = furnace_box            # dict(half_width, z_bot, z_top, wall)
        self.W, self.H = size
        hw, zb, zt = furnace_box["half_width"], furnace_box["z_bot"], furnace_box["z_top"]
        wall = furnace_box.get("wall", 0.18)
        span = max(2 * (hw + wall), (zt - zb) + 2 * wall) * 1.06
        self.s = scale or min(self.W, self.H) / span
        cz = 0.5 * (zt + zb)
        self.c = center or (self.W / 2, self.H / 2 + cz * self.s)
        Y, Z = np.meshgrid(np.arange(self.W) + 0.5, np.arange(self.H) + 0.5)
        self.Yw = (Y - self.c[0]) / self.s
        self.Zw = -(Z - self.c[1]) / self.s
        self.rho = np.hypot(self.Yw, self.Zw)
        self.phi = np.arctan2(self.Zw, self.Yw)

    def px(self, y, z):
        return self.c[0] + np.asarray(y) * self.s, self.c[1] - np.asarray(z) * self.s

    # ---------------------------------------------------------- partes
    def furnace_layer(self, T_refr_C=700.0, gas=None, flame=None, flame_img=None):
        """Caixa da fornalha, refratário e gás. gas/flame: (T_K [ny, nz], yc, zc) da LES no plano do queimador."""
        hw, zb, zt = self.box["half_width"], self.box["z_bot"], self.box["z_top"]
        wall = self.box.get("wall", 0.18)
        Y, Zw = self.Yw, self.Zw
        img = np.zeros((self.H, self.W, 3), np.float32)
        # fundo
        g = np.clip(1 - (Zw - zb) / (zt - zb + 2 * wall), 0, 1)
        img[:] = (np.array([14, 17, 24]) * (0.7 + 0.3 * g[..., None]))
        inside = (np.abs(Y) < hw) & (Zw > zb) & (Zw < zt)
        lining = (np.abs(Y) < hw + wall) & (Zw > zb - wall) & (Zw < zt + wall) & ~inside
        shell = (np.abs(Y) < hw + wall + 0.035) & (Zw > zb - wall - 0.035) & (Zw < zt + wall + 0.035) & ~inside & ~lining
        # refratário: tijolo com brilho conforme a temperatura (quente por dentro, frio por fora)
        depth_in = np.minimum.reduce([hw + wall - np.abs(Y), Zw - (zb - wall), (zt + wall) - Zw]) / wall
        heat = np.clip(1 - depth_in, 0, 1)
        brick = np.array([120, 72, 50], np.float32)
        glow = thermal_rgb(np.full(1, 0.0) + T_refr_C)[0]
        # tijolos: fiadas de 6,5 cm, juntas escuras finas
        row = np.floor(Zw / 0.065)
        jx = np.abs(((Y + 0.11 * (row % 2)) / 0.22) % 1 - 0.5) > 0.47
        jz = np.abs((Zw / 0.065) % 1 - 0.5) > 0.44
        tex = np.where(jx | jz, 0.62, 0.92 + 0.08 * np.sin(row * 12.9898) ** 2)
        ref = brick * (0.55 + 0.25 * heat[..., None]) * tex[..., None]
        ref = ref * (1 - 0.35 * heat[..., None]) + glow * 0.35 * heat[..., None] * min(1.0, (T_refr_C - 250) / 600)
        img[lining] = ref[lining]
        img[shell] = np.array([150, 158, 168])
        img[inside] = np.array([28, 22, 22])
        a_gas = np.zeros((self.H, self.W), np.float32)
        if gas is not None:
            T, yc, zc = gas[:3]
            gain = gas[3] if len(gas) > 3 else 1.0
            Ts = self._sample(T, yc, zc)
            rgb, a = flame_rgba(Ts)
            a = np.where(inside & (self.rho > self.drum.R + 0.01), a * gain, 0.0)
            img = img * (1 - 0.9 * a[..., None]) + rgb * 0.9 * a[..., None]
            # brilho (bloom) da chama
            glow = Image.fromarray(np.clip(rgb * a[..., None], 0, 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(radius=max(4, int(0.035 * self.s))))
            img = img + 0.55 * np.asarray(glow, np.float32)
            a_gas = a
        if flame_img is not None:
            # chamas renderizadas com base física (flames.FlameRenderer.render_on_grid): luz somada à cena
            rgb_f, a_f = flame_img
            a_f = np.where(inside & (self.rho > self.drum.R + 0.01), a_f, 0.0)
            img = img * (1 - 0.6 * a_f[..., None]) + 255.0 * np.asarray(rgb_f, np.float32) * \
                (inside & (self.rho > self.drum.R + 0.01))[..., None]
            a_gas = a_f
        # bocais dos queimadores na parede lateral
        for zb_ in self.box.get("burners_z", (-1.0,)):
            bx, bz = self.px(-hw, zb_)
            r_ = 0.06 * self.s
            m = (np.abs(self.Yw + hw + 0.03) < 0.05) & (np.abs(self.Zw - zb_) < 0.07)
            img[m] = np.array([70, 74, 82])
        self.inside = inside
        return img, a_gas

    def _sample(self, f, yc, zc):
        """Amostra bilinear de um campo (ny, nz) na malha de pixels."""
        fy = np.interp(self.Yw, yc, np.arange(len(yc)))
        fz = np.interp(self.Zw, zc, np.arange(len(zc)))
        j0 = np.clip(np.floor(fy).astype(int), 0, len(yc) - 2); k0 = np.clip(np.floor(fz).astype(int), 0, len(zc) - 2)
        wy, wz = fy - j0, fz - k0
        return ((1 - wy) * (1 - wz) * f[j0, k0] + wy * (1 - wz) * f[j0 + 1, k0]
                + (1 - wy) * wz * f[j0, k0 + 1] + wy * wz * f[j0 + 1, k0 + 1])

    def drum_layer(self, img, Ts_C_mat, theta, wall_px=None):
        """Casco colorido pela temperatura de cada setor (referencial do tambor) e aletas girando."""
        dr = self.drum
        R = dr.R
        t = max((wall_px or 9) / self.s, 0.03)
        ring = (self.rho >= R) & (self.rho < R + t)
        nphi = Ts_C_mat.shape[-1]
        phi_mat = (self.phi - theta + math.pi) % (2 * math.pi) - math.pi
        k = np.clip(((phi_mat + math.pi) / (2 * math.pi) * nphi).astype(int), 0, nphi - 1)
        col = thermal_rgb(Ts_C_mat[k])
        steel = np.array([95, 100, 110], np.float32)
        hot = np.clip((Ts_C_mat[k] - 350) / 250, 0, 1)[..., None]
        ringcol = steel * (1 - 0.75 * hot) + col * 0.75 * hot
        img[ring] = ringcol[ring]
        img[(self.rho >= R + t) & (self.rho < R + t + 0.006)] = np.array([30, 30, 34])
        inner = self.rho < R
        img[inner] = np.array([18, 16, 18]) + 10 * np.clip(1 - self.rho[inner] / R, 0, 1)[:, None]
        self.inner = inner
        return img

    def lifters_polys(self, theta):
        dr = self.drum
        out = []
        for a in dr.lifter_angles() + theta:
            ca, sa = math.cos(a), math.sin(a)
            for (u0, u1, w0, w1) in dr.lifter_boxes():
                u1 = min(u1, dr.R)
                if w1 - w0 < 0.03:          # espessura mínima visível
                    wc = 0.5 * (w0 + w1); w0, w1 = wc - 0.015, wc + 0.015
                pts = [(u0, w0), (u1, w0), (u1, w1), (u0, w1)]
                out.append([self.px(u * ca - w * sa, u * sa + w * ca) for u, w in pts])
        return out

    def bed_particles(self, img, xyz, radii, colors, view_depth=None):
        """Partículas do DEM vistas ao longo do eixo do tambor (y→direita, z→cima; x = profundidade)."""
        cx, cy = self.px(xyz[:, 1], xyz[:, 2])
        r = np.maximum(radii * self.s, 1.2)
        depth = xyz[:, 0] if view_depth is None else view_depth
        rgb, a = splat_spheres(self.H, self.W, cx.astype(np.float32), cy.astype(np.float32), r.astype(np.float32),
                               depth.astype(np.float32), colors)
        return img * (1 - a[..., None]) + rgb * a[..., None], a

    def pool(self, img, F, beta, T_C, char=0.0):
        """Poça de fundido: segmento circular com superfície inclinada de β, cor da temperatura."""
        from .geometry import fill_half_angle
        R = self.drum.R
        eps = fill_half_angle(max(F, 1e-4))
        # superfície: reta a distância R cos ε do centro, normal apontando para cima girada de β
        nrm = np.array([-math.sin(beta), math.cos(beta)])
        d = self.Yw * nrm[0] + self.Zw * nrm[1]
        m = (d < -R * math.cos(eps)) & (self.rho < R)
        col = thermal_rgb(T_C) * (1 - 0.8 * char)
        depth = (-R * math.cos(eps) - d) / max(R * (1 - math.cos(eps)), 1e-3)
        shade = 0.75 + 0.25 * np.clip(1 - depth, 0, 1)
        gloss = np.exp(-((-R * math.cos(eps) - d) * self.s / 3.0) ** 2)
        pix = col[None, None, :] * shade[..., None] + 70 * gloss[..., None]
        img[m] = np.clip(pix[m], 0, 255)
        return img, m

    def bed_raster(self, img, F, beta, T_fn, char_fn=None):
        """Leito como mapa de temperatura: T_fn(σ) com σ = 0 na parede molhada e 1 na superfície livre."""
        from .geometry import fill_half_angle
        R = self.drum.R
        eps = fill_half_angle(max(F, 1e-4))
        nrm = np.array([-math.sin(beta), math.cos(beta)])
        d = self.Yw * nrm[0] + self.Zw * nrm[1]
        hs = -R * math.cos(eps) - d                       # distância até a superfície
        m = (hs > 0) & (self.rho < R)
        dw = R - self.rho                                 # distância até a parede
        sig = np.clip(dw / np.maximum(dw + hs, 1e-6), 0, 1)
        T = T_fn(sig[m])
        col = thermal_rgb(T)
        if char_fn is not None:
            col = col * (1 - 0.8 * char_fn(sig[m]))[:, None]
        img[m] = col
        return img, m


def draw_overlay(canvas: Image.Image, cs: CrossSection, theta, labels=True, s=1.0, lifter_col=(165, 170, 180)):
    """Aletas (polígonos) e rótulos sobre a imagem da cena."""
    d = ImageDraw.Draw(canvas, "RGBA")
    for poly in cs.lifters_polys(theta):
        d.polygon([(float(x), float(y)) for x, y in poly], fill=lifter_col + (255,), outline=(60, 60, 66, 255))
    return canvas


# ----------------------------------------------------------- carga com mudança de fase (PhaseDEM)
def phase_colors(rec, label, mode="temperatura", T_bed_C=None):
    """Cor de cada pedaço: material → (aquecimento) → fundido âmbar → carvão. mode 'material' mantém a cor do
    material (segmento da química); 'temperatura' usa o mapa de temperatura da barra de cores."""
    from .phasedem import MATERIALS, CHAR_RGB, MELT_RGB
    base = np.array([m[3] for m in MATERIALS] + [CHAR_RGB], float)[label]
    Tp = np.asarray(rec["Tp"], float) - 273.15
    fm = np.asarray(rec["f_m"], float) / 255.0
    ch = np.asarray(rec["charf"], float) / 255.0
    if mode == "temperatura":
        w = np.clip((Tp - 40.0) / 60.0, 0, 1)[:, None] * 0.85
        col = base * (1 - w) + thermal_rgb(Tp) * w
    else:
        col = base.copy()
    col = col * (1 - fm[:, None] * 0.7) + np.array(MELT_RGB, float) * fm[:, None] * 0.7
    col = col * (1 - ch[:, None] * 0.9) + np.array(CHAR_RGB, float) * ch[:, None] * 0.9
    return col


def draw_phase_bed(cs, img, rec, label, mode="temperatura"):
    """Pedaços ativos do PhaseDEM + a poça de fundido translúcida por cima dos submersos."""
    act = np.asarray(rec["active"], bool)
    x = np.asarray(rec["x"], np.float32)[act]
    r = np.asarray(rec["r"], np.float32)[act]
    col = phase_colors(rec, label, mode)[act]
    if len(x):
        img, _ = cs.bed_particles(img, x, r, col)
    p = rec["pool"]
    if p.get("area", 0.0) > 1e-5:
        from .geometry import fill_half_angle
        from .phasedem import MELT_RGB
        R = cs.drum.R
        eps = fill_half_angle(max(p["area"] / (math.pi * R ** 2), 1e-5))
        beta = p.get("beta", 0.1)
        nrm = np.array([-math.sin(beta), math.cos(beta)])
        d = cs.Yw * nrm[0] + cs.Zw * nrm[1]
        depth = -R * math.cos(eps) - d
        m = (depth > 0) & (cs.rho < R)
        conv = float(p.get("conv", 0.0))
        if mode == "temperatura":
            c = thermal_rgb(p["T"] - 273.15) * 0.75 + np.array(MELT_RGB) * 0.25
        else:
            c = np.array(MELT_RGB, float)
        c = c * (1 - 0.55 * conv) + np.array([60, 32, 14], float) * 0.55 * conv
        gloss = np.exp(-(depth * cs.s / 3.0) ** 2)
        a = 0.72
        pix = c[None, None, :] * (0.8 + 0.2 * np.clip(1 - depth / max(R * (1 - math.cos(eps)), 1e-3), 0, 1))[..., None] \
            + 80 * gloss[..., None]
        img[m] = img[m] * (1 - a) + np.clip(pix[m], 0, 255) * a
    return img
