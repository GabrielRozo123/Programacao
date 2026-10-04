"""Renderização HD da chama (pós-processamento dos quadros gravados da LES).

O campo da LES tem Δ ≈ 0,5 m; em 1080p isso dá ~20 px por célula. Para um vídeo nítido, cada quadro é
composto em PyTorch (GPU quando houver):

* cor física: emissão espectral da fuligem (ε ∝ λ^-1,39) à temperatura média da linha de visada,
  integrada nas funções de cor CIE 1931 → sRGB linear;
* brilho: luminosidade integrada da LES (câmera sintética) × fração visível da emissão;
* realce de detalhe abaixo da malha (opcional): ruído fractal advectado com o vento que deforma e modula
  a chama só na escala da célula — efeito visual, não altera nenhum resultado da simulação;
* tone mapping fílmico (ACES), bloom em três escalas, céu noturno e chaminé iluminada pela chama;
* textos com PIL e codificação H.264 de alta qualidade pelo ffmpeg (sem passar pelo matplotlib).
"""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

RES = {"1080p": (1920, 1080), "1440p": (2560, 1440), "4k": (3840, 2160)}


# ----------------------------------------------------------------------------- cor
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


def soot_color_lut(T0: float = 700.0, T1: float = 3000.0, n: int = 232, alpha: float = 1.39):
    """Tabela T → (cor sRGB linear normalizada, peso de brilho visível relativo a 1800 K).

    Emissão espectral da fuligem ∝ λ^-α B_λ(T) (Hottel–Broughton); o peso é a luminância visível por
    unidade de potência total emitida (∝ T^(4+α)), que deixa o núcleo quente mais branco e brilhante."""
    lam = np.linspace(380e-9, 780e-9, 401)
    cmf = _cie_cmf(lam * 1e9)
    T = np.linspace(T0, T1, n)
    c2 = 1.4388e-2
    rgb = np.zeros((n, 3))
    Y = np.zeros(n)
    for i, t in enumerate(T):
        spec = lam ** (-5.0 - alpha) / np.expm1(c2 / (lam * t))
        xyz = (spec[:, None] * cmf).sum(0)
        rgb[i] = np.clip(XYZ_TO_SRGB @ xyz, 0.0, None)
        Y[i] = xyz[1] / t ** (4.0 + alpha)
    rgb /= rgb.max(1, keepdims=True)
    w = Y / np.interp(1800.0, T, Y)
    return T, rgb, w


def aces(x: torch.Tensor) -> torch.Tensor:
    """Tone mapping fílmico ACES (aproximação de Narkowicz)."""
    return ((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)).clamp(0.0, 1.0)


def to_srgb(x: torch.Tensor) -> torch.Tensor:
    return torch.where(x <= 0.0031308, 12.92 * x, 1.055 * x.clamp(min=0.0) ** (1 / 2.4) - 0.055)


# --------------------------------------------------------------------- utilidades
def _gauss_kernel(sigma: float, dev, dtype):
    r = max(1, int(3 * sigma))
    x = torch.arange(-r, r + 1, device=dev, dtype=dtype)
    k = torch.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def blur(img: torch.Tensor, sigma: float) -> torch.Tensor:
    """Desfoque gaussiano separável de (C, H, W); sigmas grandes via pirâmide (mais rápido)."""
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


def fractal_noise(n: int, lam_min: float, lam_max: float, beta: float, gen: torch.Generator, dev) -> torch.Tensor:
    """Ruído periódico n×n com espectro ∝ k^-β entre os comprimentos de onda lam_min e lam_max (em px)."""
    w = torch.randn(n, n, generator=gen)
    k = torch.fft.fftfreq(n)
    kk = torch.sqrt(k[:, None] ** 2 + k[None, :] ** 2)
    band = (kk >= 1.0 / lam_max) & (kk <= 1.0 / lam_min)
    amp = torch.where(band, kk.clamp(min=1e-6) ** (-beta / 2), torch.zeros_like(kk))
    f = torch.fft.ifft2(torch.fft.fft2(w) * amp).real
    return ((f - f.mean()) / f.std()).to(dev)


def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    import matplotlib
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def _mono(size: int, bold: bool = False):
    from PIL import ImageFont
    import matplotlib
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    try:
        return ImageFont.truetype(str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / name), size)
    except OSError:
        return _font(size, bold)


class FFmpegPipe:
    """Escreve quadros RGB (H, W, 3) uint8 direto no ffmpeg (H.264, CRF baixo, yuv420p)."""

    def __init__(self, path: str, size: tuple, fps: int = 30, crf: int = 14):
        ff = shutil.which("ffmpeg")
        if ff is None:
            raise RuntimeError("ffmpeg não encontrado")
        W, H = size
        self.p = subprocess.Popen(
            [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
             "-tune", "film", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path],
            stdin=subprocess.PIPE)
        self.path = path

    def write(self, frame: np.ndarray):
        self.p.stdin.write(np.ascontiguousarray(frame, dtype=np.uint8).tobytes())

    def close(self):
        self.p.stdin.close()
        if self.p.wait() != 0:
            raise RuntimeError(f"ffmpeg falhou ao gravar {self.path}")
        return self.path


# ------------------------------------------------------------------- render HD
def hd_view(rec, aspect: float = 16 / 9, pad: float = 4.0, top_room: float = 0.18):
    """Janela da câmera: envelope médio da LES (I ≥ 0,2) com folga e um pedaço da chaminé."""
    s = rec.static
    tip = s["tip"]
    xs, zs = [0.0], [float(tip[2])]
    Ip = rec.final.get("I_proj")
    if Ip is not None and (np.asarray(Ip) >= 0.2).any():
        ii, kk = np.nonzero(np.asarray(Ip) >= 0.2)
        xs += [s["xc"][ii].min(), s["xc"][ii].max()]
        zs += [s["zc"][kk].min(), s["zc"][kk].max()]
    else:   # sem médias: usa o maior quadro
        lum = np.asarray(rec.frames[-1]["lum"], float)
        m = lum > 0.05 * lum.max()
        ii, kk = np.nonzero(m)
        xs += [s["xc"][ii].min(), s["xc"][ii].max()]
        zs += [s["zc"][kk].min(), s["zc"][kk].max()]
    x0, x1 = min(xs) - pad, max(xs) + pad
    z0, z1 = min(zs) - pad, max(zs) + pad
    z1 += top_room * (z1 - z0)
    z0 = max(z0, float(tip[2]) - 0.45 * (z1 - z0))
    cx, cz, w, h = 0.5 * (x0 + x1), 0.5 * (z0 + z1), x1 - x0, z1 - z0
    if w / h < aspect:
        w = h * aspect
    else:
        h = w / aspect
    return (cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2)


class HDFlameRenderer:
    """Compõe quadros HD da chama a partir dos quadros gravados (Recorder)."""

    def __init__(self, rec, size=(1920, 1080), view=None, detail: float = 0.35, exposure: float = 1.0,
                 bloom: float = 0.6, wind_speed: float | None = None, device: str = "auto", seed: int = 3):
        # detail: 0 = só a LES; ~0,35 = realce discreto; > 0,6 fica artificial
        self.rec = rec
        s = rec.static
        self.W, self.H = size
        self.dev = torch.device("cuda" if (device == "auto" and torch.cuda.is_available()) else
                                ("cpu" if device == "auto" else device))
        self.view = view or hd_view(rec, aspect=self.W / self.H)
        x0, x1, z0, z1 = self.view
        self.ppm = self.W / (x1 - x0)                     # pixels por metro
        self.detail, self.exposure, self.bloom = detail, exposure, bloom
        self.U = float(s["u_ref"]) if wind_speed is None else wind_speed
        t = lambda a: torch.as_tensor(np.asarray(a, np.float32), device=self.dev)  # noqa: E731
        # posições físicas dos pixels (centros), z para cima
        xs = x0 + (np.arange(self.W) + 0.5) / self.ppm
        zs = z1 - (np.arange(self.H) + 0.5) / self.ppm
        self.X = t(np.broadcast_to(xs[None, :], (self.H, self.W)))
        self.Zc = t(np.broadcast_to(zs[:, None], (self.H, self.W)))
        # mapeamento físico → índice da malha esticada da LES (para grid_sample)
        self.xc, self.zc = np.asarray(s["xc"], float), np.asarray(s["zc"], float)
        self._xi = (t(self.xc), t(np.arange(len(self.xc))))
        self._zi = (t(self.zc), t(np.arange(len(self.zc))))
        # cor da fuligem
        T, rgb, w = soot_color_lut()
        self.lut_T0, self.lut_dT = float(T[0]), float(T[1] - T[0])
        self.lut_rgb, self.lut_w = t(rgb), t(w)
        # ruído fractal periódico (detalhe abaixo da malha), em metros
        gen = torch.Generator().manual_seed(seed)
        self.tile_m = 12.0
        n = 512
        dcell = float(np.median(np.diff(self.xc)[np.abs(self.xc[:-1]) < 20])) if len(self.xc) > 2 else 0.5
        self.dcell = dcell
        px_per_m = n / self.tile_m
        # deformação: estruturas de 1–6 células (línguas de chama); brilho: 0,6–3 células
        warp = (1.0 * dcell * px_per_m, 6.0 * dcell * px_per_m)
        fine = (0.6 * dcell * px_per_m, 3.0 * dcell * px_per_m)
        self.noise = [fractal_noise(n, *warp, 3.0, gen, self.dev) for _ in range(4)] + \
                     [fractal_noise(n, *fine, 3.0, gen, self.dev) for _ in range(2)]
        self.tl_fallback = None
        self.norm_hist: list[float] = []
        self.background = self._background()

    # ---------------------------------------------------------------- partes
    def _interp_index(self, v: torch.Tensor, pair) -> torch.Tensor:
        xp, ip = pair
        j = torch.searchsorted(xp, v.clamp(xp[0], xp[-1]).contiguous()).clamp(1, len(xp) - 1)
        x0, x1 = xp[j - 1], xp[j]
        return ip[j - 1] + (v - x0) / (x1 - x0)

    def _sample(self, field: np.ndarray, X: torch.Tensor, Z: torch.Tensor, smooth: float = 0.7) -> torch.Tensor:
        """Amostra um campo (nx, nz) da malha da LES nos pontos físicos (X, Z) (bicúbico, pré-filtrado)."""
        f = torch.as_tensor(np.asarray(field, np.float32), device=self.dev)
        if smooth:
            f = blur(f[None], smooth)[0]
        ix = self._interp_index(X, self._xi)
        iz = self._interp_index(Z, self._zi)
        nx, nz = f.shape
        gx = 2 * (iz + 0.5) / nz - 1        # grid_sample: x ↔ última dimensão (z da LES)
        gy = 2 * (ix + 0.5) / nx - 1
        grid = torch.stack([gx, gy], -1)[None]
        out = F.grid_sample(f[None, None], grid, mode="bicubic", padding_mode="border", align_corners=False)[0, 0]
        inside = (X >= self.xc[0]) & (X <= self.xc[-1]) & (Z >= self.zc[0]) & (Z <= self.zc[-1])
        return torch.where(inside, out, torch.zeros_like(out))

    def _noise(self, k: int, X: torch.Tensor, Z: torch.Tensor, t: float) -> torch.Tensor:
        """Ruído advectado com o escoamento (vento em x, empuxo em z) e que evolui no tempo."""
        u, w = max(self.U, 1.0), 0.35 * max(self.U, 3.0)
        ph = 2 * math.pi * t / 1.2
        out = 0.0
        for j, c in ((2 * k, math.cos(ph)), (2 * k + 1, math.sin(ph))):
            gx = 2 * (((X - u * t) / self.tile_m) % 1.0) - 1
            gy = 2 * (((Z - w * t) / self.tile_m) % 1.0) - 1
            out = out + c * F.grid_sample(self.noise[j][None, None], torch.stack([gx, gy], -1)[None],
                                          mode="bilinear", padding_mode="reflection", align_corners=False)[0, 0]
        return out

    def _background(self) -> torch.Tensor:
        H, W = self.H, self.W
        y = torch.linspace(0, 1, H, device=self.dev)[:, None, None]
        top = torch.tensor([0.004, 0.006, 0.014], device=self.dev)
        bot = torch.tensor([0.012, 0.016, 0.030], device=self.dev)
        return (top * (1 - y) + bot * y).expand(H, W, 3).permute(2, 0, 1).contiguous()

    def _stack_mask(self) -> torch.Tensor:
        tip = self.rec.static["tip"]
        half = max(0.45, 0.012 * (self.view[1] - self.view[0]))
        return ((self.X.abs() <= half) & (self.Zc <= float(tip[2]))).float()

    # ---------------------------------------------------------------- quadro
    def frame(self, f) -> torch.Tensor:
        """Imagem linear (3, H, W) do quadro f (antes do tone mapping)."""
        t = float(f["t"])
        X, Z = self.X, self.Zc
        a = self.detail
        lum = np.asarray(f["lum"], np.float32)
        if a > 0:   # deformação suave (1–6 células), concentrada nas bordas da chama, não no núcleo
            s0 = (self._sample(lum, X, Z, smooth=2.0) / max(float(lum.max()), 1e-12)).clamp(0, 1) ** 0.5
            d = 1.2 * a * self.dcell * (0.25 + 3.0 * s0 * (1 - s0))
            X = X + d * self._noise(0, X, Z, t)
            Z = Z + d * self._noise(1, X, Z, t)
        L = self._sample(np.log(np.maximum(lum, 1e-6 * max(lum.max(), 1e-12))), X, Z)
        I = torch.exp(L) * (L > math.log(1e-5 * max(lum.max(), 1e-12)))
        tl = f.get("tl")
        if tl is not None:
            T = self._sample(np.asarray(tl, np.float32), X, Z, smooth=1.0)
        else:      # quadros antigos sem temperatura: estima pela intensidade (núcleo mais quente)
            T = 1350.0 + 650.0 * (I / I.max().clamp(min=1e-12)) ** 0.5
        if a > 0:   # modulação de brilho só nas bordas da chama
            s = (I / I.max().clamp(min=1e-12)) ** 0.5
            I = I * torch.exp(0.45 * a * self._noise(2, X, Z, t) * (4 * s * (1 - s) + 0.15))
        idx = ((T.clamp(self.lut_T0, self.lut_T0 + self.lut_dT * (len(self.lut_w) - 1)) - self.lut_T0)
               / self.lut_dT)
        i0 = idx.floor().long().clamp(0, len(self.lut_w) - 2)
        fr = (idx - i0)[..., None]
        rgb = self.lut_rgb[i0] * (1 - fr) + self.lut_rgb[i0 + 1] * fr
        wv = self.lut_w[i0] * (1 - fr[..., 0]) + self.lut_w[i0 + 1] * fr[..., 0]
        I = I * wv.clamp(0.25, 4.0)
        # exposição automática estável (mediana dos últimos quadros do percentil 99,7)
        q = torch.quantile(I.flatten()[:: max(1, I.numel() // 400000)], 0.997).item()
        self.norm_hist.append(q)
        ref = max(float(np.median(self.norm_hist[-40:])), 1e-12)
        E = (2.2 * self.exposure / ref) * I
        flame = (E[..., None] * rgb).permute(2, 0, 1)
        img = self.background.clone()
        # chaminé iluminada pela chama (silhueta + reflexo quente)
        sm = self._stack_mask()
        tipz = float(self.rec.static["tip"][2])
        lit = 0.02 * float(E.max().clamp(max=6.0)) / (1.0 + ((tipz - self.Zc) / 6.0) ** 2)
        base = torch.tensor([0.030, 0.033, 0.040], device=self.dev)[:, None, None]
        warm = torch.tensor([1.0, 0.68, 0.42], device=self.dev)[:, None, None]
        img = img * (1 - sm) + (base + warm * lit[None]) * sm
        img = img + flame
        if self.bloom > 0:
            bright = (flame - 0.6).clamp(min=0.0)
            b = 0.0
            for sig, wgt in ((0.004, 0.55), (0.015, 0.3), (0.05, 0.15)):
                b = b + wgt * blur(bright, sig * self.H)
            img = img + self.bloom * b
        return img

    def to_uint8(self, img: torch.Tensor) -> np.ndarray:
        out = to_srgb(aces(img)).clamp(0, 1)
        return (out.permute(1, 2, 0) * 255.0 + 0.5).to(torch.uint8).cpu().numpy()


# -------------------------------------------------------------- sobreposições
class Overlay:
    """Textos e elementos gráficos desenhados com PIL sobre o quadro HD."""

    def __init__(self, size, view, title: str, subtitle: str, caption: str, wind: bool = True):
        from PIL import Image, ImageDraw
        self.W, self.H = size
        self.s = self.H / 1080.0
        self.view = view
        self.static = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(self.static)
        s = self.s
        d.text((int(58 * s), int(36 * s)), title, font=_font(int(44 * s), True), fill=(236, 240, 246, 255))
        d.text((int(60 * s), int(98 * s)), subtitle, font=_font(int(24 * s)), fill=(150, 160, 175, 255))
        if wind:
            y = int(200 * s)
            d.line([(int(60 * s), y), (int(185 * s), y)], fill=(120, 200, 255, 255), width=max(2, int(3 * s)))
            d.polygon([(int(200 * s), y), (int(182 * s), y - int(9 * s)), (int(182 * s), y + int(9 * s))],
                      fill=(120, 200, 255, 255))
            d.text((int(60 * s), y + int(16 * s)), "vento", font=_font(int(22 * s)), fill=(120, 200, 255, 255))
        # barra de escala de 10 m
        x0, x1, z0, z1 = view
        ppm = self.W / (x1 - x0)
        L = 10 * ppm
        xr = self.W - int(60 * s)
        yb = self.H - int(110 * s)
        d.line([(int(xr - L), yb), (xr, yb)], fill=(235, 238, 242, 255), width=max(2, int(4 * s)))
        d.text((int(xr - L / 2), yb - int(36 * s)), "10 m", font=_font(int(22 * s)), fill=(235, 238, 242, 255),
               anchor="mm")
        d.text((self.W - int(60 * s), self.H - int(48 * s)), caption, font=_font(int(18 * s)),
               fill=(140, 148, 160, 255), anchor="rm")
        self.f_clock = _mono(int(46 * s), True)
        self.f_read = _mono(int(26 * s))

    def compose(self, rgb: np.ndarray, t: float, L: float) -> np.ndarray:
        from PIL import Image, ImageDraw
        im = Image.fromarray(rgb).convert("RGBA")
        im.alpha_composite(self.static)
        d = ImageDraw.Draw(im)
        s = self.s
        d.text((self.W - int(60 * s), int(36 * s)), f"t = {t:5.1f} s", font=self.f_clock,
               fill=(255, 176, 64, 255), anchor="ra")
        d.text((self.W - int(60 * s), int(104 * s)), f"L = {L:4.1f} m", font=self.f_read,
               fill=(236, 240, 246, 255), anchor="ra")
        return np.asarray(im.convert("RGB"))


def render_flame_hd(rec, path: str, title: str, subtitle: str, resolution: str = "1080p", fps: int = 30,
                    every: int = 1, detail: float = 0.35, exposure: float = 1.0, bloom: float = 0.6,
                    caption: str | None = None, t_range: tuple | None = None, device: str = "auto",
                    log_every: int = 100) -> str:
    """Segmento HD da chama: resolução '1080p', '1440p' ou '4k'; detail = realce visual abaixo da malha
    (0 desliga); every = usa 1 a cada `every` quadros gravados (acelera o vídeo)."""
    size = RES.get(resolution, resolution if isinstance(resolution, tuple) else RES["1080p"])
    r = HDFlameRenderer(rec, size=size, detail=detail, exposure=exposure, bloom=bloom, device=device)
    if caption is None:
        caption = ("LES 3D · emissão da fuligem integrada na linha de visada (câmera sintética)"
                   + (" · realce visual de detalhes abaixo da malha" if detail > 0 else ""))
    ov = Overlay(size, r.view, title, subtitle, caption, wind=float(rec.static["u_ref"]) > 0)
    frames = rec.frames[::every]
    if t_range is not None:
        frames = [f for f in frames if t_range[0] <= f["t"] <= t_range[1]]
    pipe = FFmpegPipe(path, size, fps)
    with torch.no_grad():
        for n, f in enumerate(frames):
            pipe.write(ov.compose(r.to_uint8(r.frame(f)), float(f["t"]), float(f["L"])))
            if log_every and (n + 1) % log_every == 0:
                print(f"  HD: {n + 1}/{len(frames)} quadros", flush=True)
    return pipe.close()


def flame_hd_png(rec, path: str, i: int = -1, resolution: str = "1080p", **kw) -> str:
    """Um quadro HD isolado (PNG), para conferência ou capa do post."""
    from PIL import Image
    size = RES.get(resolution, RES["1080p"])
    r = HDFlameRenderer(rec, size=size, **kw)
    with torch.no_grad():
        for f in rec.frames[max(0, (i % len(rec.frames)) - 40): (i % len(rec.frames)) + 1]:
            img = r.frame(f)   # aquece a exposição automática
    Image.fromarray(r.to_uint8(img)).save(path)
    return path


# ------------------------------------------------------------- cartões de texto
def _card_background(size, backdrop=None, place: float = 0.78, strength: float = 0.5,
                     ramp_from: float = 0.42) -> np.ndarray:
    """Fundo escuro em gradiente; com `backdrop` (quadro HD da chama, sem textos), a chama é deslocada
    para a fração `place` da largura e entra esmaecida, sem competir com o texto à esquerda."""
    W, H = size
    bg = np.zeros((H, W, 3), np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    for c, (a, b) in enumerate(zip((8, 11, 20), (14, 20, 34))):
        bg[..., c] = a + (b - a) * yy
    if backdrop is not None:
        from PIL import Image
        im = np.asarray(Image.fromarray(np.asarray(backdrop, np.uint8)).resize((W, H), Image.LANCZOS), np.float32)
        lum = im.mean(2)
        wgt = np.clip(lum - np.percentile(lum, 50), 0, None)
        cx = float((wgt.sum(0) * np.arange(W)).sum() / max(wgt.sum(), 1e-6))
        sh = int(place * W - cx)
        out = np.zeros_like(im)
        if sh >= 0:
            out[:, sh:] = im[:, :W - sh]
        else:
            out[:, :W + sh] = im[:, -sh:]
        ramp = np.clip((np.linspace(0, 1, W) - ramp_from) / 0.35, 0, 1)[None, :, None] ** 1.5
        bg = np.maximum(bg, strength * ramp * out)
    return np.clip(bg, 0, 255)


def render_title_card(path: str, title: str, subtitle: str, credit: str = "", note: str = "",
                      size=(1920, 1080), fps: int = 30, seconds: float = 3.5, backdrop=None,
                      accent=(255, 176, 64)) -> str:
    """Abertura em HD (PIL): título, subtítulo, crédito e nota, com entrada suave."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    base = Image.fromarray(_card_background(size, backdrop, place=0.5, strength=0.38,
                                            ramp_from=-1.0).astype(np.uint8)).convert("RGBA")
    probe = ImageDraw.Draw(base)

    def fit(text, bold, size0, maxw):
        sz = size0
        while sz > 12 and probe.textlength(text, font=_font(int(sz * s), bold)) > maxw:
            sz -= 2
        return _font(int(sz * s), bold)
    items = [(title, fit(title, True, 78, 0.9 * W), (240, 244, 250), 0.50, 0.0),
             (subtitle, fit(subtitle, False, 36, 0.9 * W), accent, 0.60, 0.35)]
    if credit:
        items.append((credit, fit(credit, False, 28, 0.9 * W), (170, 178, 190), 0.69, 0.7))
    if note:
        items.append((note, fit(note, False, 22, 0.9 * W), (130, 138, 150), 0.93, 1.0))
    pipe = FFmpegPipe(path, size, fps, crf=16)
    n = int(seconds * fps)
    for i in range(n):
        t = i / fps
        im = base.copy()
        d = ImageDraw.Draw(im)
        for text, font, col, yf, delay in items:
            a = float(np.clip((t - delay) / 0.6, 0, 1) * np.clip((seconds - t) / 0.4, 0, 1))
            ease = 1 - (1 - a) ** 3
            d.text((W / 2, yf * H + (1 - ease) * 20 * s), text, font=font, fill=tuple(col) + (int(255 * a),),
                   anchor="mm")
        pipe.write(np.asarray(im.convert("RGB")))
    return pipe.close()


def render_text_cards(path: str, cards: list[dict], size=(1920, 1080), fps: int = 30,
                      seconds: float | list = 7.0, fade: float = 0.6, accent=(255, 176, 64),
                      backdrop=None) -> str:
    """Cartões de texto (kicker, título, tópicos, nota opcional) com entrada suave, em HD.

    cards = [{"kicker": "O DESAFIO", "headline": "...", "bullets": ["...", "..."], "footnote": "..."}]
    backdrop: imagem RGB opcional (ex.: um quadro HD da chama) mostrada esmaecida à direita."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    pipe = FFmpegPipe(path, size, fps, crf=16)
    f_k, f_h, f_b, f_n = _font(int(30 * s), True), _font(int(62 * s), True), _font(int(38 * s)), _font(int(24 * s))
    secs = seconds if isinstance(seconds, (list, tuple)) else [seconds] * len(cards)
    bg = _card_background(size, backdrop)

    def wrap(d, text, font, width):
        words, lines, cur = text.split(), [], ""
        for w in words:
            nxt = (cur + " " + w).strip()
            if d.textlength(nxt, font=font) <= width:
                cur = nxt
            else:
                lines.append(cur)
                cur = w
        return lines + ([cur] if cur else [])

    for card, sec in zip(cards, secs):
        n = int(sec * fps)
        base = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
        layers = []   # (y_alvo, imagem RGBA, atraso em s)
        x0, wmax = int(150 * s), int(W - 300 * s)
        y = int(230 * s)
        probe = ImageDraw.Draw(base)

        def layer(lines, font, color, gap, delay, bullet=False):
            nonlocal y
            h = int(font.size * 1.25)
            im = Image.new("RGBA", (W, h * len(lines) + int(gap)), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            for k, ln in enumerate(lines):
                xo = x0 + (int(48 * s) if bullet else 0)
                if bullet and k == 0:
                    d.ellipse([x0 + int(6 * s), int(h * 0.42 - 8 * s), x0 + int(22 * s), int(h * 0.42 + 8 * s)],
                              fill=accent + (255,))
                d.text((xo, k * h), ln, font=font, fill=color)
            layers.append((y, im, delay))
            y += im.height

        layer([card.get("kicker", "").upper()], f_k, accent + (255,), 18 * s, 0.0)
        layer(wrap(probe, card["headline"], f_h, wmax), f_h, (238, 242, 248, 255), 46 * s, 0.25)
        for j, bl in enumerate(card.get("bullets", [])):
            layer(wrap(probe, bl, f_b, wmax - int(48 * s)), f_b, (200, 208, 220, 255), 22 * s, 0.7 + 0.45 * j,
                  bullet=True)
        foot = card.get("footnote")
        y_top = int(230 * s)
        shift = int((H - (y - y_top)) / 2 - y_top - 20 * s)      # centraliza o bloco na vertical
        layers = [(yl + shift, L, dl) for (yl, L, dl) in layers]
        bar = (y_top + shift, y + shift)
        icard = cards.index(card)
        for i in range(n):
            t = i / fps
            im = base.copy()
            dr = ImageDraw.Draw(im)
            dr.rectangle([x0 - int(40 * s), bar[0], x0 - int(32 * s), bar[1]], fill=accent + (255,))
            if len(cards) > 1:   # indicador de progresso (bolinhas)
                for j in range(len(cards)):
                    cx = W - int((60 + 28 * (len(cards) - 1 - j)) * s)
                    r = int((7 if j == icard else 5) * s)
                    col = accent + (255,) if j == icard else (90, 98, 112, 255)
                    dr.ellipse([cx - r, H - int(60 * s) - r, cx + r, H - int(60 * s) + r], fill=col)
            for (yl, L, delay) in layers:
                a = float(np.clip((t - delay) / fade, 0, 1))
                a *= float(np.clip((sec - t) / fade, 0, 1))
                if a <= 0:
                    continue
                ease = 1 - (1 - a) ** 3
                Lc = L.copy()
                Lc.putalpha(Image.eval(L.getchannel("A"), lambda v, a=a: int(v * a)))
                im.alpha_composite(Lc, (0, int(yl + (1 - ease) * 24 * s)))
            if foot:
                a = float(np.clip((t - 1.2) / fade, 0, 1) * np.clip((sec - t) / fade, 0, 1))
                dr.text((x0, H - int(90 * s)), foot, font=f_n, fill=(140, 148, 160, int(255 * a)))
            pipe.write(np.asarray(im.convert("RGB")))
    return pipe.close()
