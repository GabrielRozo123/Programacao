"""Chamas da fornalha com base física: emissão da fuligem e quimiluminescência integradas na linha de visada.

Pós-processamento dos quadros 3D gravados da LES (furnace_les.FurnaceLES), no espírito do render HD do flare:

* fuligem: f_v da relação de estado (tabela β-PDF; pico 1 ppm em φ ≈ 2) × fv_scale. Queimadores de GLP
  com ar forçado (bico de mistura) são pouco fuliginosos: f_v de pico ~0,1–0,3 ppm (chamas de propano
  difusivas chegam a ~1 ppm; a mistura parcial do ar forçado reduz) → fv_scale = 0,2 por padrão;
* absorção da fuligem κ_s = C f_v T, C = 1862 m⁻¹K⁻¹ (média de Planck; a mesma da LES) e, por célula da
  linha de visada, dτ = κ_s Δs; emissão visível ∝ L_vis(T)·(1 − e^(−dτ)), composta da frente para trás
  com a transmitância acumulada. L_vis(T) e a cor saem do espectro λ^(−1,39)·B_λ(T) integrado nas funções
  de cor CIE 1931 (a mesma tabela do flare): ~1400 K laranja-avermelhado, ~1800 K amarelo, ~2200 K branco;
* quimiluminescência azul (CH*, C₂*) proporcional à liberação de calor da química rápida
  q = ρχ/2 · LHV/(1 − Z_st) · P(Z_st), fina e sem absorção, cor sRGB linear ≈ (0,22; 0,42; 1,0), só onde q
  passa de 10 % do pico (sem véu azul do gás morno). Sem medida de referência para a razão azul/fuligem, o
  ganho é visual: ~1 MW/m² de calor por área projetada vale ~0,3 % da luminância de um corpo negro a 1800 K
  (parâmetro `blue`);
* resolução abaixo da célula: T, f_v e q interpolados (trilinear) numa grade ~3 cm antes da emissão — como a
  luminância cresce ~T^20, as bordas da chama ficam finas em vez de quadradas;
* superfícies (vista lateral): casco de aço e refratário com a incandescência do próprio T (ponto de
  Draper ≈ 798 K, vermelho escuro quase invisível; ~1100 K cereja/laranja) e iluminados de forma difusa
  pela luz da chama (soma das células emissoras, ∝ cos θ/r², sem sombra);
* detalhe abaixo da malha (opcional): ruído fractal advectado com a velocidade projetada (advecção de
  textura em duas fases), que deforma e modula a chama só na escala da célula — efeito visual;
* exposição automática pelo percentil 99,9 da luminância (mediana móvel de ±20 quadros, independente da
  ordem de renderização), compressão HDR (radiância^0,5), bloom em duas escalas, ACES e sRGB.

Custo (CPU, 2 núcleos, malha de 5 cm 108×40×45): projeção ~0,2 s por quadro (uma vez, no início); depois
~0,2–0,4 s por quadro de 1080p (amostragem por pixel e bloom). Na GPU, ~10× mais rápido.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn.functional as F

C_SOOT = 1862.0                  # κ_s = C f_v T [1/(m K)] (média de Planck; a mesma da LES)
BLUE_RGB = (0.22, 0.42, 1.0)     # CH* 431 nm + C₂* 516 nm (bandas de Swan), sRGB linear
T_DRAPER = 798.0                 # K: início do brilho visível no escuro


# ============================================================ gravação dos quadros
def _pool(a: torch.Tensor, stride: int) -> torch.Tensor:
    if stride <= 1:
        return a
    nx, ny, nz = (n // stride * stride for n in a.shape)
    return F.avg_pool3d(a[None, None, :nx, :ny, :nz].float(), stride)[0, 0]


def flame_meta(les, stride: int = 1, fv_scale: float = 0.2) -> dict:
    """Metadados estáticos dos quadros: coordenadas dos centros, h, geometria do tambor e da caixa."""
    c = les.cfg

    def coords(v):
        n = len(v) // stride * stride
        return np.asarray(v[:n], float).reshape(-1, stride).mean(1)
    fluid = (_pool(les.fluid, stride) > 0.5).cpu().numpy().astype(np.uint8)
    return dict(xc=coords(les.xc), yc=coords(les.yc), zc=coords(les.zc), h=float(les.h) * stride, stride=stride,
                R_out=float(c.R_out), L_drum=float(c.L_drum), half_width=float(c.half_width), z_bot=float(c.z_bot),
                z_top=float(c.z_top), Lx=float(les.xf[-1]), burners_x=tuple(c.burners_x), burner_z=float(c.burner_z),
                Q_fire=float(c.Q_fire), T_shell=float(c.T_shell), T_refr=float(c.T_refr), Z_st=float(les.Z_st),
                fv_scale=float(fv_scale), fluid=fluid)


def record_flame_frame(les, fv_scale: float = 0.2, stride: int = 1, fluid=None) -> dict:
    """Quadro 3D do estado atual da LES, em float16: T [K], f_v [ppm], q [MW/m³], u, v, w [m/s].

    `fluid` (uint8) é a máscara fluida estática; passe sempre o mesmo objeto (o pickle guarda uma vez só)."""
    f = les.flame_fields(fv_scale)
    cv = lambda a, s=1.0: (_pool(a, stride) * s).cpu().numpy().astype(np.float16)  # noqa: E731
    if fluid is None:
        fluid = (_pool(les.fluid, stride) > 0.5).cpu().numpy().astype(np.uint8)
    return dict(t=float(les.time), T=cv(f["T"]), fv=cv(f["fv"], 1e6), q=cv(f["q"], 1e-6), u=cv(f["u"]),
                v=cv(f["v"]), w=cv(f["w"]), fluid=fluid)


class FlameRecorder:
    """on_frame da LES: grava quadros a partir de t_start. Uso:
    rec = FlameRecorder(les, t_start=10.0); les.run(12.0, frame_dt=0.05, on_frame=rec)."""

    def __init__(self, les, t_start: float = 0.0, fv_scale: float = 0.2, stride: int = 1):
        self.t_start, self.fv_scale, self.stride = t_start, fv_scale, stride
        self.meta = flame_meta(les, stride, fv_scale)
        self.frames: list[dict] = []

    def __call__(self, les):
        if les.time >= self.t_start:
            self.frames.append(record_flame_frame(les, self.fv_scale, self.stride, self.meta["fluid"]))

    def data(self) -> dict:
        return dict(frames=self.frames, meta=self.meta)


# ============================================================ cor (CIE 1931 + Planck), portado do flare
def _cie_cmf(lam_nm: np.ndarray) -> np.ndarray:
    """Funções de cor CIE 1931 2° (ajuste analítico de Wyman, Sloan & Shirley, 2013)."""
    def g(x, mu, s1, s2):
        s = np.where(x < mu, s1, s2)
        return np.exp(-0.5 * ((x - mu) / s) ** 2)
    x = 1.056 * g(lam_nm, 599.8, 37.9, 31.0) + 0.362 * g(lam_nm, 442.0, 16.0, 26.7) \
        - 0.065 * g(lam_nm, 501.1, 20.4, 26.2)
    y = 0.821 * g(lam_nm, 568.8, 46.9, 40.5) + 0.286 * g(lam_nm, 530.9, 16.3, 31.1)
    z = 1.217 * g(lam_nm, 437.0, 11.8, 36.0) + 0.681 * g(lam_nm, 459.0, 26.0, 13.8)
    return np.stack([x, y, z], -1)


XYZ_TO_SRGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])


def radiance_lut(T0: float = 300.0, T1: float = 3000.0, n: int = 541, alpha: float = 1.39):
    """Tabela T → (cromaticidade sRGB linear, luminância visível Y) da fuligem (ε_λ ∝ λ^−α, normalizada em
    550 nm) e de um corpo negro (superfícies). Y em unidades arbitrárias comuns (as duas comparáveis)."""
    lam = np.linspace(380e-9, 780e-9, 401)
    cmf = _cie_cmf(lam * 1e9)
    T = np.linspace(T0, T1, n)
    c2 = 1.4388e-2
    out = {}
    for key, a in (("soot", alpha), ("bb", 0.0)):
        rgb = np.zeros((n, 3)); Y = np.zeros(n)
        for i, t in enumerate(T):
            spec = (lam / 550e-9) ** (-a) * lam ** -5.0 / np.expm1(np.minimum(c2 / (lam * t), 700.0))
            xyz = (spec[:, None] * cmf).sum(0)
            rgb[i] = np.clip(XYZ_TO_SRGB @ xyz, 0.0, None)
            Y[i] = xyz[1]
        rgb = rgb / np.maximum(rgb.max(1, keepdims=True), 1e-30)
        out[key] = (rgb, Y)
    ref = np.interp(1800.0, T, out["soot"][1])
    return T, out["soot"][0], out["soot"][1] / ref, out["bb"][0], out["bb"][1] / ref


_LUT = None


def _lut():
    global _LUT
    if _LUT is None:
        _LUT = radiance_lut()
    return _LUT


def incandescence_rgb(T_K):
    """Cor (sRGB linear) × luminância relativa de uma superfície negra a T (refratário, casco). Abaixo do ponto
    de Draper (~798 K) é praticamente invisível; ~1100 K cereja/laranja."""
    T, _, _, rgb, Y = _lut()
    Tq = np.clip(np.asarray(T_K, float), T[0], T[-1])
    c = np.stack([np.interp(Tq, T, rgb[:, i]) for i in range(3)], -1)
    return c * np.interp(Tq, T, Y)[..., None]


def aces(x: torch.Tensor) -> torch.Tensor:
    """Tone mapping fílmico ACES (aproximação de Narkowicz)."""
    return ((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)).clamp(0.0, 1.0)


def to_srgb(x: torch.Tensor) -> torch.Tensor:
    return torch.where(x <= 0.0031308, 12.92 * x, 1.055 * x.clamp(min=0.0) ** (1 / 2.4) - 0.055)


def _gauss_kernel(sigma: float, dev, dtype):
    r = max(1, int(3 * sigma))
    x = torch.arange(-r, r + 1, device=dev, dtype=dtype)
    k = torch.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def blur(img: torch.Tensor, sigma: float) -> torch.Tensor:
    """Desfoque gaussiano separável de (C, H, W); sigmas grandes via pirâmide."""
    if sigma < 0.5:
        return img
    x = img[None]
    down = 1
    while sigma / down > 12 and min(x.shape[-2:]) > 64:
        x = F.avg_pool2d(x, 2)
        down *= 2
    k = _gauss_kernel(sigma / down, img.device, img.dtype)
    C = x.shape[1]
    pad = len(k) // 2
    x = F.conv2d(F.pad(x, (pad, pad, 0, 0), mode="replicate"), k.view(1, 1, 1, -1).expand(C, 1, 1, -1), groups=C)
    x = F.conv2d(F.pad(x, (0, 0, pad, pad), mode="replicate"), k.view(1, 1, -1, 1).expand(C, 1, -1, 1), groups=C)
    if down > 1:
        x = F.interpolate(x, size=img.shape[-2:], mode="bilinear", align_corners=False)
    return x[0]


def fractal_noise(n: int, lam_min: float, lam_max: float, beta: float, gen: torch.Generator) -> torch.Tensor:
    """Ruído periódico n×n com espectro ∝ k^-β entre os comprimentos de onda lam_min e lam_max (em px)."""
    w = torch.randn(n, n, generator=gen)
    k = torch.fft.fftfreq(n)
    kk = torch.sqrt(k[:, None] ** 2 + k[None, :] ** 2)
    band = (kk >= 1.0 / lam_max) & (kk <= 1.0 / lam_min)
    amp = torch.where(band, kk.clamp(min=1e-6) ** (-beta / 2), torch.zeros_like(kk))
    f = torch.fft.ifft2(torch.fft.fft2(w) * amp).real
    return (f - f.mean()) / f.std()


# ============================================================ projeção ao longo da linha de visada
def _lut_torch(dev):
    """(T0, ΔT, L_fuligem [n, 3], L_corpo_negro [n, 3]) como tensores: radiância visível relativa já com a cor."""
    T, c_s, Y_s, c_b, Y_b = _lut()
    ls = torch.as_tensor(c_s * Y_s[:, None], dtype=torch.float32, device=dev)
    lb = torch.as_tensor(c_b * Y_b[:, None], dtype=torch.float32, device=dev)
    return float(T[0]), float(T[1] - T[0]), ls, lb


def _lookup(table, T, T0, dT):
    n = table.shape[0]
    x = ((T - T0) / dT).clamp(0.0, n - 1.001)
    i0 = x.floor().long()
    f = (x - i0)[..., None]
    return table[i0] * (1.0 - f) + table[i0 + 1] * f


def project(frame: dict, meta: dict, view: str = "corte", blue: float = 0.003, T_shell: float | None = None,
            T_refr: float | None = None, up: int = 3, device: str = "cpu"):
    """Integra emissão e absorção ao longo da visada. Devolve (rgb linear das chamas [A, Z, 3], opacidade [A, Z],
    rgb linear das superfícies vistas [A, Z, 3] — zero na vista 'corte') com
    A = y (vista 'corte', visada +x) ou x (vista 'lateral', visada +y a partir da parede dos queimadores), numa
    grade `up` vezes mais fina que a da LES nos dois eixos da imagem (centros em a0 − h/2 + (j + ½)·h/up).

    Resolução abaixo da célula: T, f_v e q são interpolados (trilinear) antes de calcular a emissão; como a
    luminância visível cresce ~T^20 perto de 1500 K, isso afina as bordas da chama em vez de borrar a emissão
    célula a célula.

    Vista lateral: o raio para no casco do tambor (opaco), que entra com a sua incandescência e iluminado pela
    luz das chamas (difusa, ρ/π·L·Ω ~ 1 % da radiância da chama, mais a luz local borrada); a face de baixo,
    voltada para os queimadores, recebe mais luz (sombreamento de cilindro). Se o raio atravessa tudo, aparece
    o refratário do fundo (incandescência de T_refr, também iluminado)."""
    dev = torch.device(device)
    T0, dT, L_s, _ = _lut_torch(dev)
    h = float(meta["h"])
    fl0 = frame.get("fluid", meta["fluid"])
    f = torch.stack([torch.as_tensor(np.asarray(a, np.float32), device=dev)
                     for a in (frame["T"], frame["fv"], frame["q"], fl0)])
    ax = 0 if view == "corte" else 1
    img_axes = (1, 2) if view == "corte" else (0, 2)
    size = list(f.shape[1:])
    for a in img_axes:
        size[a] *= up
    f = F.interpolate(f[None], size=size, mode="trilinear", align_corners=False)[0]
    T, fv, q, fl = f[0], f[1].clamp(min=0.0) * 1e-6, f[2].clamp(min=0.0), f[3].clamp(0.0, 1.0)

    def centres(c, n):
        c = np.asarray(c, float)
        a0 = c[0] - h / 2
        return torch.as_tensor(a0 + (np.arange(n) + 0.5) * (h * len(c) / n), dtype=torch.float32, device=dev)
    xs, ys, zs = (centres(meta[k], size[i]) for i, k in enumerate(("xc", "yc", "zc")))

    dtau = C_SOOT * fv * T * h * fl
    emis = (1.0 - torch.exp(-dtau))[..., None] * _lookup(L_s, T, T0, dT)
    # quimiluminescência só onde a liberação de calor passa de 10 % do pico (sem véu azul do gás morno), com o pico
    # limitado ao percentil 99,5 (a borda do jato na boca do queimador tem |∇Z|² de uma célula só)
    qs = q.flatten()[::max(1, q.numel() // 200000)]
    q_hi = float(torch.quantile(qs, 0.995)) + 1e-30
    qe = (q.clamp(max=q_hi) - 0.10 * q_hi).clamp(min=0.0) * fl
    if view == "lateral":
        X, Y, Z = torch.meshgrid(xs, ys, zs, indexing="ij")
        drum = (torch.hypot(Y, Z) < meta["R_out"]) & (X < meta["L_drum"])
        blocked = torch.cumsum(drum.int(), dim=1) > 0                   # da parede dos queimadores para dentro
        prev = torch.cat([torch.zeros_like(blocked[:, :1]), blocked[:, :-1]], 1)
        first = blocked & ~prev
        dtau = torch.where(blocked, torch.zeros_like(dtau), dtau)
        emis = torch.where(blocked[..., None], torch.zeros_like(emis), emis)
    cum = torch.cumsum(dtau, dim=ax)
    trans_before = torch.exp(-(cum - dtau))
    rgb = (emis * trans_before[..., None]).sum(dim=ax)
    trans = torch.exp(-cum.select(ax, -1))
    if blue > 0:
        if view == "lateral":
            qe = torch.where(blocked, torch.zeros_like(qe), qe)
        bl = blur((blue * h * (qe * trans_before).sum(dim=ax))[None], 0.6 * up)[0]   # posição da folha: ± ½ célula
        rgb = rgb + bl[..., None] * torch.tensor(BLUE_RGB, device=dev)
    surf_rgb = torch.zeros_like(rgb)
    if view == "lateral":
        T_sh = meta["T_shell"] if T_shell is None else T_shell
        T_rf = meta["T_refr"] if T_refr is None else T_refr
        hit = first.any(dim=1)
        t_hit = (trans_before * first).sum(dim=1)
        lum = rgb.sum(-1)
        peak = float(torch.quantile(lum.flatten()[::max(1, lum.numel() // 200000)], 0.995)) + 1e-30
        sig = 0.35 / (h / up)                                           # luz local: ~35 cm de alcance
        glow = blur(rgb.permute(2, 0, 1), sig).permute(1, 2, 0).sum(-1, keepdim=True)
        nz = (zs / meta["R_out"]).clamp(-1, 1)[None, :, None]           # normal do casco no ponto visto (z/R)
        shade = 0.35 + 0.65 * (-nz).clamp(min=0.0)
        steel = torch.tensor([0.50, 0.52, 0.56], device=dev)
        brick = torch.tensor([0.60, 0.33, 0.22], device=dev)
        inc_sh = torch.as_tensor(incandescence_rgb(T_sh), dtype=torch.float32, device=dev)
        inc_rf = torch.as_tensor(incandescence_rgb(T_rf), dtype=torch.float32, device=dev)
        surf = inc_sh + (0.01 * peak + 0.25 * glow) * shade * steel
        back = inc_rf + (0.006 * peak + 0.10 * glow) * brick
        surf_rgb = torch.where(hit[..., None], t_hit[..., None] * surf, trans[..., None] * back)
        trans = torch.where(hit, torch.zeros_like(trans), trans)
    return (rgb.cpu().numpy().astype(np.float32), (1.0 - trans).cpu().numpy().astype(np.float32),
            surf_rgb.cpu().numpy().astype(np.float32))


class FlameRenderer:
    """Quadros das chamas a partir dos quadros 3D gravados (FlameRecorder.data())."""

    def __init__(self, data: dict, view: str = "corte", exposure: float = 1.0, bloom: float = 0.5,
                 detail: float = 0.15, blue: float = 0.003, seed: int = 3, device: str = "cpu", gamma: float = 0.5,
                 up: int | None = None):
        self.frames, self.meta = data["frames"], data["meta"]
        self.gamma = gamma
        self.view, self.exposure, self.bloom, self.detail, self.blue = view, exposure, bloom, detail, blue
        self.dev = torch.device(device)
        m = self.meta
        # grade da imagem ~3 cm: 0,10 m → ×3; 0,05 m → ×2; 0,035 m → ×1
        self.up = up if up is not None else max(1, int(round(m["h"] / 0.033)))
        self.proj = [project(f, m, view, blue, up=self.up, device=device) for f in self.frames]
        lum = np.array([float(np.percentile(p[0].sum(-1), 99.9)) for p in self.proj])   # pelas chamas
        k = 20
        self.norm = np.array([np.median(lum[max(0, i - k):i + k + 1]) for i in range(len(lum))])
        gen = torch.Generator().manual_seed(seed)
        self.noise = [fractal_noise(256, 3.0, 40.0, 3.0, gen) for _ in range(2)]
        self.hp = m["h"] / self.up
        self.ax0 = np.asarray(m["yc"] if view == "corte" else m["xc"])
        self.ax1 = np.asarray(m["zc"])

    def _sample(self, img: np.ndarray, A, B):
        """Amostra bilinear (sem sobressinal nas bordas) de img [n0, n1, C] nas coordenadas físicas (A, B) dos pixels."""
        t = torch.as_tensor(img, dtype=torch.float32, device=self.dev).permute(2, 0, 1)
        t = blur(t, 0.8)
        n0, n1 = img.shape[:2]
        h = self.meta["h"]
        a0, b0 = self.ax0[0] - h / 2, self.ax1[0] - h / 2
        gx = 2 * ((torch.as_tensor(np.array(B), dtype=torch.float32) - b0) / (n1 * self.hp)) - 1
        gy = 2 * ((torch.as_tensor(np.array(A), dtype=torch.float32) - a0) / (n0 * self.hp)) - 1
        grid = torch.stack([gx, gy], -1)[None].to(self.dev)
        out = F.grid_sample(t[None], grid, mode="bilinear", padding_mode="zeros", align_corners=False)[0]
        return out.clamp(min=0.0)

    def _detail(self, A, B, i):
        """Modulação abaixo da malha (efeito visual): ruído fractal com comprimentos de onda de ~3 a 33 cm,
        em duas fases que sobem com o empuxo (~1,5 m/s) e se alternam sem emenda."""
        texel = 120.0                                       # texels por metro
        t = i / 30.0
        P = 0.8
        ph = (t % P) / P
        A_t = torch.as_tensor(np.array(A), dtype=torch.float32)
        B_t = torch.as_tensor(np.array(B), dtype=torch.float32)
        tot = 0.0
        for k, off in enumerate((0.0, 0.5)):
            s = (ph + off) % 1.0
            wgt = 1 - abs(2 * s - 1)
            u = torch.remainder(A_t * texel, 256.0)
            v = torch.remainder((B_t - 1.2 * s * P) * texel + 97.0 * k, 256.0)
            nz = F.pad(self.noise[k][None, None], (0, 1, 0, 1), mode="circular")
            grid = torch.stack([(v + 0.5) / 257 * 2 - 1, (u + 0.5) / 257 * 2 - 1], -1)[None]
            tot = tot + wgt * F.grid_sample(nz, grid, mode="bilinear", align_corners=False)[0, 0]
        return (1.0 + self.detail * tot).clamp(min=0.0).to(self.dev)

    def render_on_grid(self, i: int, A, B, gain: float = 1.0):
        """(rgb [H, W, 3] em 0–1 com tone mapping, opacidade [H, W]) nas coordenadas físicas A (y ou x), B (z)."""
        i = i % len(self.proj)
        rgb, op, surf = self.proj[i]
        img = np.concatenate([rgb, op[..., None], surf], -1)
        s = self._sample(img, A, B)
        lin, alpha = s[:3], s[3].clamp(0, 1)
        if self.detail > 0:
            lin = lin * self._detail(A, B, i)[None]        # o detalhe só deforma a chama, não as superfícies
        lin = lin + s[4:]
        # compressão da faixa dinâmica (câmera HDR): radiância^γ antes do tone mapping, para a chama não virar
        # só o pico mais quente (a luminância visível cresce ~T^20 perto de 1500 K)
        lin = (lin * (gain / max(self.norm[i], 1e-30))).clamp(min=0.0) ** self.gamma * (self.exposure * 1.6)
        if self.bloom > 0:
            bright = (lin - 0.6).clamp(min=0.0)
            lin = lin + self.bloom * (0.6 * blur(bright, 6.0) + 0.4 * blur(bright, 22.0))
        out = to_srgb(aces(lin)).permute(1, 2, 0).cpu().numpy()
        a = np.clip(np.asarray(alpha.cpu().numpy()) * 8.0 + out.max(-1), 0, 1)
        return out, a

    def render_image(self, i: int, extent: tuple, size: tuple, gain: float = 1.0):
        """Imagem isolada (W×H) cobrindo extent = (a0, a1, b0, b1) em metros (a horizontal, b vertical)."""
        W, H = size
        a0, a1, b0, b1 = extent
        A = np.ascontiguousarray(np.broadcast_to(np.linspace(a0, a1, W)[None, :], (H, W)))
        B = np.ascontiguousarray(np.broadcast_to(np.linspace(b1, b0, H)[:, None], (H, W)))
        return self.render_on_grid(i, A, B, gain)
