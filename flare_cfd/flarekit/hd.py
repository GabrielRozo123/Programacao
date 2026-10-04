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
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .dashboard import br

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
_GLUE = re.compile(r"^(\([A-Z]{2}\)|m|m/s|s|kg/s|MW|kW/m²|MJ/kg|g/mol|°C|K|%)[.,;:)]?$")


def _words(text):
    """Palavras para quebra de linha, sem separar '(SP)' do nome nem a unidade do número."""
    out = []
    for w in text.split():
        if out and _GLUE.match(w):
            out[-1] += "\u00a0" + w
        else:
            out.append(w)
    return out


def _wrap(draw, text, font, width):
    words, lines, cur = _words(text), [], ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if draw.textlength(nxt, font=font) <= width:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def _wrap_balanced(draw, text, font, width):
    """Como _wrap, mas com linhas de comprimento parecido (evita uma palavra sozinha na última linha)."""
    lines = _wrap(draw, text, font, width)
    if len(lines) < 2:
        return lines
    lo, hi = 0.3 * width, float(width)
    for _ in range(18):                      # menor largura que mantém o mesmo número de linhas
        mid = 0.5 * (lo + hi)
        if len(_wrap(draw, text, font, mid)) <= len(lines):
            hi = mid
        else:
            lo = mid
    return _wrap(draw, text, font, hi)


def _caption_alpha(captions, t, fade=0.45):
    """Legenda ativa no instante t (s) e sua opacidade (entrada e saída suaves)."""
    for t0, t1, text in captions:
        if t0 <= t < t1:
            return text, float(np.clip(min(t - t0, t1 - t) / fade, 0, 1))
    return None, 0.0


def even_captions(texts, duration, lead=0.3):
    """Distribui as legendas igualmente na duração do segmento: [(t0, t1, texto)]."""
    texts = [t for t in texts if t]
    if not texts:
        return []
    d = (duration - lead) / len(texts)
    return [(lead + k * d, lead + (k + 1) * d, t) for k, t in enumerate(texts)]


def draw_lower_third(im, text, alpha, s, accent=(255, 176, 64), y_bottom=None, max_w=None):
    """Legenda em caixa escura translúcida no terço inferior (PIL RGBA)."""
    from PIL import Image, ImageDraw
    if not text or alpha <= 0:
        return im
    W, H = im.size
    font = _font(int(34 * s))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    max_w = max_w or int(W * 0.62)
    lines = _wrap(d, br(text), font, max_w)
    lh = int(font.size * 1.28)
    pad = int(22 * s)
    box_h = lh * len(lines) + 2 * pad
    box_w = max(d.textlength(ln, font=font) for ln in lines) + 2 * pad + int(10 * s)
    y1 = y_bottom if y_bottom is not None else H - int(150 * s)
    y0 = y1 - box_h
    x0 = int(60 * s)
    d.rounded_rectangle([x0, y0, x0 + box_w, y1], radius=int(10 * s), fill=(6, 9, 15, int(185 * alpha)))
    d.rectangle([x0, y0, x0 + int(6 * s), y1], fill=accent + (int(255 * alpha),))
    for k, ln in enumerate(lines):
        d.text((x0 + pad + int(10 * s), y0 + pad + k * lh), ln, font=font, fill=(240, 244, 250, int(255 * alpha)))
    im.alpha_composite(layer)
    return im


class Overlay:
    """Textos e elementos gráficos desenhados com PIL sobre o quadro HD."""

    def __init__(self, size, view, title: str, subtitle: str, caption: str, wind: bool = True,
                 kicker: str = "", captions=None, accent=(255, 176, 64)):
        from PIL import Image, ImageDraw
        self.W, self.H = size
        self.s = self.H / 1080.0
        self.view = view
        self.captions = captions or []
        self.accent = accent
        self.static = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(self.static)
        s = self.s
        y = int(36 * s)
        if kicker:
            d.text((int(60 * s), y), br(kicker).upper(), font=_font(int(24 * s), True), fill=accent + (255,))
            y += int(38 * s)
        d.text((int(58 * s), y), br(title), font=_font(int(44 * s), True), fill=(236, 240, 246, 255))
        d.text((int(60 * s), y + int(62 * s)), br(subtitle), font=_font(int(24 * s)), fill=(150, 160, 175, 255))
        if wind:
            y = int(240 * s) if kicker else int(200 * s)
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
        d.text((self.W - int(60 * s), self.H - int(48 * s)), br(caption), font=_font(int(18 * s)),
               fill=(140, 148, 160, 255), anchor="rm")
        self.f_clock = _mono(int(40 * s), True)
        self.f_read = _font(int(24 * s))

    def compose(self, rgb: np.ndarray, t: float, L: float, tv: float | None = None) -> np.ndarray:
        """t: tempo simulado [s]; L: comprimento instantâneo da chama [m]; tv: tempo no vídeo [s] (legendas)."""
        from PIL import Image, ImageDraw
        im = Image.fromarray(rgb).convert("RGBA")
        im.alpha_composite(self.static)
        d = ImageDraw.Draw(im)
        s = self.s
        d.text((self.W - int(60 * s), int(36 * s)), br(f"t = {t:4.1f} s"), font=self.f_clock,
               fill=self.accent + (255,), anchor="ra")
        d.text((self.W - int(60 * s), int(92 * s)), "tempo simulado", font=self.f_read,
               fill=(150, 160, 175, 255), anchor="ra")
        d.text((self.W - int(60 * s), int(130 * s)), br(f"comprimento da chama: {L:.1f} m"), font=self.f_read,
               fill=(236, 240, 246, 255), anchor="ra")
        if tv is not None and self.captions:
            text, a = _caption_alpha(self.captions, tv)
            draw_lower_third(im, text, a, s, self.accent)
        return np.asarray(im.convert("RGB"))


def render_flame_hd(rec, path: str, title: str, subtitle: str, resolution: str = "1080p", fps: int = 30,
                    every: int = 1, detail: float = 0.35, exposure: float = 1.0, bloom: float = 0.6,
                    caption: str | None = None, t_range: tuple | None = None, device: str = "auto",
                    log_every: int = 100, kicker: str = "", captions=None, clean_path: str | None = None,
                    clean_from: float = 0.25) -> str:
    """Segmento HD da chama: resolução '1080p', '1440p' ou '4k'; detail = realce visual abaixo da malha
    (0 desliga); every = usa 1 a cada `every` quadros gravados (acelera o vídeo); kicker = rótulo do
    capítulo; captions = textos de legenda, distribuídos igualmente na duração (ou [(t0, t1, texto)]);
    clean_path = grava também a chama sem textos (a partir da fração `clean_from` do tempo, já desenvolvida),
    usada como fundo animado dos cartões (Backdrop)."""
    size = RES.get(resolution, resolution if isinstance(resolution, tuple) else RES["1080p"])
    r = HDFlameRenderer(rec, size=size, detail=detail, exposure=exposure, bloom=bloom, device=device)
    if caption is None:
        caption = ("LES 3D · emissão da fuligem integrada na linha de visada (câmera sintética)"
                   + (" · realce visual de detalhes abaixo da malha" if detail > 0 else ""))
    frames = rec.frames[::every]
    if t_range is not None:
        frames = [f for f in frames if t_range[0] <= f["t"] <= t_range[1]]
    dur = len(frames) / fps
    caps = captions or []
    if caps and isinstance(caps[0], str):
        caps = even_captions(caps, dur)
    ov = Overlay(size, r.view, title, subtitle, caption, wind=float(rec.static["u_ref"]) > 0, kicker=kicker,
                 captions=caps)
    pipe = FFmpegPipe(path, size, fps)
    clean = FFmpegPipe(clean_path, size, fps, crf=20) if clean_path else None
    t_clean = float(frames[0]["t"]) + clean_from * (float(frames[-1]["t"]) - float(frames[0]["t"]))
    with torch.no_grad():
        for n, f in enumerate(frames):
            rgb = r.to_uint8(r.frame(f))
            if clean is not None and float(f["t"]) >= t_clean:
                clean.write(rgb)
            pipe.write(ov.compose(rgb, float(f["t"]), float(f["L"]), tv=n / fps))
            if log_every and (n + 1) % log_every == 0:
                print(f"  HD: {n + 1}/{len(frames)} quadros", flush=True)
    if clean is not None:
        clean.close()
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
def _gradient(W: int, H: int) -> np.ndarray:
    bg = np.zeros((H, W, 3), np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    for c, (a, b) in enumerate(zip((8, 11, 20), (14, 20, 34))):
        bg[..., c] = a + (b - a) * yy
    return bg


def _flame_cx(im: np.ndarray) -> float:
    """Posição horizontal (fração da largura) do centro luminoso da chama."""
    lum = np.asarray(im, np.float32).mean(2)
    wgt = np.clip(lum - np.percentile(lum, 50), 0, None)
    return float((wgt.sum(0) * np.arange(lum.shape[1])).sum() / max(wgt.sum(), 1e-6)) / lum.shape[1]


def _compose(bg: np.ndarray, im: np.ndarray, place: float, strength: float, ramp_from: float,
             cx: float) -> np.ndarray:
    """Chama deslocada para a fração `place` da largura, esmaecida e com rampa da esquerda para a direita."""
    W = bg.shape[1]
    im = np.asarray(im, np.float32)
    sh = int((place - cx) * W)
    out = np.zeros_like(im)
    if sh >= 0:
        out[:, sh:] = im[:, :W - sh]
    else:
        out[:, :W + sh] = im[:, -sh:]
    ramp = np.clip((np.linspace(0, 1, W) - ramp_from) / 0.35, 0, 1)[None, :, None] ** 1.5
    return np.clip(np.maximum(bg, strength * ramp * out), 0, 255)


def _card_background(size, backdrop=None, place: float = 0.78, strength: float = 0.5,
                     ramp_from: float = 0.42) -> np.ndarray:
    """Fundo escuro em gradiente; com `backdrop` (quadro HD da chama, sem textos), a chama é deslocada
    para a fração `place` da largura e entra esmaecida, sem competir com o texto à esquerda."""
    W, H = size
    bg = _gradient(W, H)
    if backdrop is not None:
        from PIL import Image
        im = np.asarray(Image.fromarray(np.asarray(backdrop, np.uint8)).resize((W, H), Image.LANCZOS), np.float32)
        bg = _compose(bg, im, place, strength, ramp_from, _flame_cx(im))
    return np.clip(bg, 0, 255)


def _probe(src: str):
    """(largura, altura, duração [s]) de um vídeo, lidos da saída do ffmpeg."""
    txt = subprocess.run([shutil.which("ffmpeg"), "-i", src], capture_output=True, text=True).stderr
    m = re.search(r", (\d{2,5})x(\d{2,5})", txt)
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", txt)
    dur = 3600 * int(d.group(1)) + 60 * int(d.group(2)) + float(d.group(3)) if d else 0.0
    return int(m.group(1)), int(m.group(2)), dur


class Backdrop:
    """Fundo dos cartões. Aceita None, um quadro RGB (fundo fixo) ou o vídeo limpo da chama gerado por
    render_flame_hd(clean_path=...): aí a chama se move atrás dos textos, em câmera lenta (`speed`) e em
    laço sem emenda (fusão de `cross` quadros). O relógio continua de um segmento para o outro. Os quadros
    ficam na memória em resolução reduzida (`width`), o bastante para um fundo esmaecido."""

    def __init__(self, src=None, size=(1920, 1080), speed: float = 0.5, width: int = 960, max_mb: float = 500.0,
                 cross: int = 24):
        from PIL import Image
        self.size, self.speed, self.k = tuple(size), speed, 0
        self.still, self.frames, self._cache = None, None, {}
        if src is None:
            return
        if not isinstance(src, (str, Path)):
            self.still = np.asarray(src, np.uint8)
            return
        src = str(src)
        if src.lower().endswith((".png", ".jpg", ".jpeg")):
            self.still = np.asarray(Image.open(src).convert("RGB"))
            return
        w0, h0, dur = _probe(src)
        bw = min(width, w0)
        bh = max(2, int(round(h0 * bw / w0 / 2)) * 2)
        nmax = max(8, int(max_mb * 1e6 / (bw * bh * 3)))
        fps = min(30.0, nmax / max(dur, 1e-3))          # clipes longos são subamostrados para caber
        p = subprocess.Popen([shutil.which("ffmpeg"), "-loglevel", "error", "-i", src, "-vf",
                              f"fps={fps:.5f},scale={bw}:{bh}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             stdout=subprocess.PIPE)
        n, fr = bw * bh * 3, []
        while len(fr) < nmax:
            buf = p.stdout.read(n)
            if len(buf) < n:
                break
            fr.append(np.frombuffer(buf, np.uint8).reshape(bh, bw, 3))
        p.stdout.close()
        p.wait()
        if not fr:
            raise ValueError(f"nenhum quadro lido de {src}")
        self.frames = fr
        self.speed = speed * fps / 30.0                  # mesma velocidade aparente com quadros mais espaçados
        self.cross = min(cross, len(fr) // 3)
        self.period = len(fr) - self.cross
        self.cx = _flame_cx(np.mean([f.astype(np.float32) for f in fr[::max(1, len(fr) // 8)]], axis=0))
        self.grad = _gradient(bw, bh)

    @property
    def animated(self) -> bool:
        return self.frames is not None

    def _seq(self, j: int) -> np.ndarray:
        """Quadro j do laço: os primeiros `cross` quadros fundem o fim do clipe ao começo."""
        F, C, Lp = self.frames, self.cross, self.period
        j %= Lp
        if j < C:
            w = j / C
            return (1 - w) * F[Lp + j].astype(np.float32) + w * F[j].astype(np.float32)
        return F[j].astype(np.float32)

    def next(self, place: float = 0.78, strength: float = 0.5, ramp_from: float = 0.42) -> np.ndarray:
        """Próximo fundo (uint8, H×W×3); cada chamada avança um quadro do vídeo final."""
        from PIL import Image
        if not self.animated:
            key = (place, strength, ramp_from)
            if key not in self._cache:
                self._cache[key] = _card_background(self.size, self.still, place, strength,
                                                    ramp_from).astype(np.uint8)
            return self._cache[key]
        pos = self.k * self.speed
        self.k += 1
        i0, w = int(pos), pos - int(pos)
        im = (1 - w) * self._seq(i0) + w * self._seq(i0 + 1)
        bg = _compose(self.grad, im, place, strength, ramp_from, self.cx)
        return np.asarray(Image.fromarray(bg.astype(np.uint8)).resize(self.size, Image.BILINEAR))


def _backdrop(backdrop, size) -> Backdrop:
    return backdrop if isinstance(backdrop, Backdrop) else Backdrop(backdrop, size)


def still_of(src: str, path: str, t: float) -> str:
    """Salva o quadro do instante t [s] de um vídeo como PNG (ex.: capa do post)."""
    subprocess.run([shutil.which("ffmpeg"), "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", src,
                    "-frames:v", "1", path], check=True)
    return path


def render_title_card(path: str, title: str, subtitle: str, credit: str = "", note: str = "",
                      size=(1920, 1080), fps: int = 30, seconds: float = 4.5, backdrop=None,
                      accent=(255, 176, 64), contact: str = "") -> str:
    """Abertura (ou encerramento) em HD: título e subtítulo em linhas equilibradas, autoria, contato
    (ex.: endereço do LinkedIn) e aviso, com entrada suave. backdrop: None, quadro RGB ou Backdrop."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    bd = _backdrop(backdrop, size)
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    title, subtitle, credit, note = br(title), br(subtitle), br(credit), br(note)
    f_t, f_s, f_c, f_n = _font(int(72 * s), True), _font(int(36 * s)), _font(int(28 * s)), _font(int(22 * s))
    t_lines = _wrap_balanced(probe, title, f_t, int(0.86 * W))
    s_lines = _wrap_balanced(probe, subtitle, f_s, int(0.80 * W))
    blocks = []      # (linhas, fonte, cor, altura de linha, atraso)
    blocks.append((t_lines, f_t, (240, 244, 250), int(f_t.size * 1.18), 0.0))
    blocks.append(([""], f_c, (0, 0, 0), int(24 * s), 0.0))
    blocks.append((s_lines, f_s, accent, int(f_s.size * 1.3), 0.4))
    if credit:
        blocks.append(([""], f_c, (0, 0, 0), int(30 * s), 0.0))
        blocks.append(([credit], f_c, (178, 186, 198), int(f_c.size * 1.3), 0.8))
    if contact:
        blocks.append(([""], f_c, (0, 0, 0), int(12 * s), 0.0))
        blocks.append(([contact], _font(int(30 * s), True), accent, int(f_c.size * 1.4), 1.0))
    total = sum(len(l) * lh for l, _, _, lh, _ in blocks)
    y0 = (H - total) / 2 - 20 * s
    pipe = FFmpegPipe(path, size, fps, crf=16)
    n = int(seconds * fps)
    for i in range(n):
        t = i / fps
        im = Image.fromarray(bd.next(place=0.5, strength=0.38, ramp_from=-1.0)).convert("RGBA")
        d = ImageDraw.Draw(im)
        y = y0
        for lines, font, col, lh, delay in blocks:
            a = float(np.clip((t - delay) / 0.6, 0, 1) * np.clip((seconds - t) / 0.4, 0, 1))
            ease = 1 - (1 - a) ** 3
            for ln in lines:
                if ln:
                    d.text((W / 2, y + lh / 2 + (1 - ease) * 18 * s), ln, font=font,
                           fill=tuple(col) + (int(255 * a),), anchor="mm")
                y += lh
        if note:
            a = float(np.clip((t - 1.1) / 0.6, 0, 1) * np.clip((seconds - t) / 0.4, 0, 1))
            for k, ln in enumerate(_wrap(d, note, f_n, int(0.86 * W))[:2]):
                d.text((W / 2, H - int((92 - 30 * k) * s)), ln, font=f_n, fill=(140, 148, 160, int(255 * a)),
                       anchor="mm")
        pipe.write(np.asarray(im.convert("RGB")))
    return pipe.close()


def render_text_cards(path: str, cards: list[dict], size=(1920, 1080), fps: int = 30,
                      seconds: float | list = 7.0, fade: float = 0.6, accent=(255, 176, 64),
                      backdrop=None) -> str:
    """Cartões de texto (kicker, título, tópicos, nota opcional) com entrada suave, em HD.

    cards = [{"kicker": "O DESAFIO", "headline": "...", "bullets": ["...", "..."], "footnote": "..."}]
    backdrop: None, quadro RGB (ex.: um quadro HD da chama) ou Backdrop (chama em movimento), mostrado
    esmaecido à direita."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    pipe = FFmpegPipe(path, size, fps, crf=16)
    f_k, f_h, f_b, f_n = _font(int(30 * s), True), _font(int(62 * s), True), _font(int(38 * s)), _font(int(24 * s))
    secs = seconds if isinstance(seconds, (list, tuple)) else [seconds] * len(cards)
    bd = _backdrop(backdrop, size)
    wrap = _wrap

    for card, sec in zip(cards, secs):
        n = int(sec * fps)
        base = Image.new("RGBA", (8, 8))
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

        layer([br(card.get("kicker", "")).upper()], f_k, accent + (255,), 18 * s, 0.0)
        layer(_wrap_balanced(probe, br(card["headline"]), f_h, wmax), f_h, (238, 242, 248, 255), 46 * s, 0.25)
        for j, bl in enumerate(card.get("bullets", [])):
            layer(wrap(probe, br(bl), f_b, wmax - int(48 * s)), f_b, (200, 208, 220, 255), 22 * s, 0.7 + 0.45 * j,
                  bullet=True)
        foot = br(card.get("footnote") or "")
        y_top = int(230 * s)
        shift = int((H - (y - y_top)) / 2 - y_top - 20 * s)      # centraliza o bloco na vertical
        layers = [(yl + shift, L, dl) for (yl, L, dl) in layers]
        bar = (y_top + shift, y + shift)
        icard = cards.index(card)
        for i in range(n):
            t = i / fps
            im = Image.fromarray(bd.next()).convert("RGBA")
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


# ------------------------------------------------------------ figuras com legenda
def _frames_of(src: str, seconds: float | None, fps: int):
    """Quadros RGB de um vídeo (decodificado pelo ffmpeg) ou de uma imagem repetida por `seconds`."""
    from PIL import Image
    if src.lower().endswith((".png", ".jpg", ".jpeg")):
        im = np.asarray(Image.open(src).convert("RGB"))
        for _ in range(int(round((seconds or 5.0) * fps))):
            yield im
        return
    ff = shutil.which("ffmpeg")
    probe = subprocess.run([ff, "-i", src], capture_output=True, text=True).stderr
    import re
    m = re.search(r", (\d{2,5})x(\d{2,5})", probe)
    w, h = int(m.group(1)), int(m.group(2))
    p = subprocess.Popen([ff, "-loglevel", "error", "-i", src, "-vf", f"fps={fps}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    p.wait()


def caption_segment(src: str, path: str, captions, chapter: str = "", size=(1920, 1080), fps: int = 30,
                    seconds: float | None = None, band: float = 0.14, accent=(255, 176, 64),
                    handle: str = "") -> str:
    """Coloca um vídeo ou imagem (figura do estudo) acima de uma faixa de legenda: rótulo do capítulo e
    textos que se alternam com transição suave. captions: lista de textos (distribuídos igualmente) ou
    [(t0, t1, texto)]; handle: assinatura discreta no canto da faixa (ex.: endereço do LinkedIn)."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    bh = int(band * H)
    frames = list(_frames_of(src, seconds, fps))
    dur = len(frames) / fps
    caps = captions or []
    if caps and isinstance(caps[0], str):
        caps = even_captions(caps, dur)
    f_k, f_c = _font(int(24 * s), True), _font(int(34 * s))
    base = Image.new("RGBA", size, (13, 17, 23, 255))
    d0 = ImageDraw.Draw(base)
    d0.rectangle([0, H - bh, W, H], fill=(9, 12, 18, 255))
    d0.rectangle([int(60 * s), H - bh + int(22 * s), int(66 * s), H - int(22 * s)], fill=accent + (255,))
    if chapter:
        d0.text((int(84 * s), H - bh + int(20 * s)), br(chapter).upper(), font=f_k, fill=accent + (255,))
    if handle:
        d0.text((W - int(60 * s), H - bh + int(22 * s)), handle, font=_font(int(22 * s)), fill=(118, 126, 140, 255),
                anchor="ra")
    pipe = FFmpegPipe(path, size, fps, crf=16)
    area_h = H - bh
    for i, fr in enumerate(frames):
        im = base.copy()
        src_im = Image.fromarray(fr)
        sc = min(W / src_im.width, area_h / src_im.height)
        fit = src_im.resize((int(src_im.width * sc), int(src_im.height * sc)), Image.LANCZOS)
        im.paste(fit, ((W - fit.width) // 2, (area_h - fit.height) // 2))
        text, a = _caption_alpha(caps, i / fps)
        if text:
            layer = Image.new("RGBA", size, (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            lines = _wrap(d, br(text), f_c, int(W - 180 * s))[:2]
            y = H - bh + int((56 if chapter else 30) * s)
            for k, ln in enumerate(lines):
                d.text((int(84 * s), y + k * int(f_c.size * 1.2)), ln, font=f_c, fill=(236, 240, 246, int(255 * a)))
            im.alpha_composite(layer)
        pipe.write(np.asarray(im.convert("RGB")))
    return pipe.close()


# --------------------------------------------------------------- números-chave
def render_kpi_card(path: str, title: str, kpis: list[dict], size=(1920, 1080), fps: int = 30,
                    seconds: float = 8.0, backdrop=None, note: str = "", kicker: str = "",
                    accent=(255, 176, 64)) -> str:
    """Cartão de números-chave com contagem animada.

    kpis = [{"value": 0.5, "fmt": "{:.1f}", "unit": "kW/m²", "label": "pico de radiação no solo",
             "color": (255, 176, 64)}, ...] — value pode ser texto (sem animação)."""
    from PIL import Image, ImageDraw
    W, H = size
    s = H / 1080.0
    bd = _backdrop(backdrop, size)
    base = Image.new("RGBA", size, (0, 0, 0, 0))      # título e caixas, compostos sobre o fundo a cada quadro
    d0 = ImageDraw.Draw(base)
    y_t = int(170 * s)
    if kicker:
        d0.text((W // 2, y_t - int(48 * s)), br(kicker).upper(), font=_font(int(28 * s), True), fill=accent + (255,),
                anchor="mm")
    d0.text((W // 2, y_t + int(10 * s)), br(title), font=_font(int(56 * s), True), fill=(240, 244, 250, 255),
            anchor="mm")
    if note:
        d0.text((W // 2, H - int(70 * s)), br(note), font=_font(int(22 * s)), fill=(140, 148, 160, 255),
                anchor="mm")
    n = len(kpis)
    cols = 2 if n == 4 else n
    rows = int(math.ceil(n / cols))
    cw, ch = int(W * 0.40), int(250 * s)
    gx = (W - cols * cw) // (cols + 1)
    y0 = int(300 * s)
    boxes = []
    for k, kp in enumerate(kpis):
        r, c = divmod(k, cols)
        x = gx + c * (cw + gx)
        y = y0 + r * (ch + int(40 * s))
        d0.rounded_rectangle([x, y, x + cw, y + ch], radius=int(18 * s), fill=(18, 24, 33, 230),
                             outline=(40, 52, 68, 255), width=max(1, int(2 * s)))
        boxes.append((x, y))
    f_v, f_u, f_l = _font(int(92 * s), True), _font(int(40 * s), True), _font(int(30 * s))
    pipe = FFmpegPipe(path, size, fps, crf=16)
    N = int(seconds * fps)
    for i in range(N):
        t = i / fps
        im = Image.fromarray(bd.next(strength=0.35)).convert("RGBA")
        im.alpha_composite(base)
        d = ImageDraw.Draw(im)
        for k, (kp, (x, y)) in enumerate(zip(kpis, boxes)):
            a = float(np.clip((t - 0.3 - 0.35 * k) / 0.5, 0, 1) * np.clip((seconds - t) / 0.4, 0, 1))
            if a <= 0:
                continue
            col = tuple(kp.get("color", accent))
            v = kp["value"]
            if isinstance(v, (int, float)):
                prog = 1 - (1 - min(1.0, max(0.0, (t - 0.3 - 0.35 * k) / 1.4))) ** 3
                vs = br(kp.get("fmt", "{:.1f}").format(v * prog))
            else:
                vs = br(str(v))
            unit = kp.get("unit", "")
            wv = d.textlength(vs, font=f_v)
            wu = d.textlength(" " + unit, font=f_u) if unit else 0
            xs = x + (cw - wv - wu) / 2
            d.text((xs, y + int(40 * s)), vs, font=f_v, fill=col + (int(255 * a),))
            if unit:
                d.text((xs + wv, y + int(84 * s)), " " + unit, font=f_u, fill=col + (int(255 * a),))
            for j, ln in enumerate(_wrap(d, br(kp.get("label", "")), f_l, cw - int(40 * s))[:2]):
                d.text((x + cw / 2, y + int(170 * s) + j * int(36 * s)), ln, font=f_l,
                       fill=(200, 208, 220, int(255 * a)), anchor="mm")
        pipe.write(np.asarray(im.convert("RGB")))
    return pipe.close()
