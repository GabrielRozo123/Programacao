"""Vídeo em HD (1080p): cartões de título, texto e números-chave, figuras com legenda e montagem final.

Mesma linguagem visual do estudo do flare: fundo escuro, textos com PIL (vírgula decimal), entrada suave e
codificação H.264 pelo ffmpeg, quadro a quadro, sem passar pelo matplotlib.
"""
from __future__ import annotations

import math
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

_DEC = re.compile(r"(?<=\d)\.(?=\d)")


def br(text: str) -> str:
    """Vírgula decimal (norma brasileira) em todo número de um texto: '6.8 m/s' → '6,8 m/s'."""
    return _DEC.sub(",", text) if isinstance(text, str) else text


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



_GLUE = re.compile(r"^(\([A-Z]{2}\)|m|m/s|s|kg/h|kg/s|kW|MW|t/a|W/m²K|Pa\u00a0s|mPa\u00a0s|rpm|°C|K|%|h)[.,;:)]?$")


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



def _gradient(W: int, H: int) -> np.ndarray:
    bg = np.zeros((H, W, 3), np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    for c, (a, b) in enumerate(zip((8, 11, 20), (14, 20, 34))):
        bg[..., c] = a + (b - a) * yy
    return bg


def _bright_cx(im: np.ndarray) -> float:
    """Posição horizontal (fração da largura) do centro luminoso da imagem."""
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
    """Fundo escuro em gradiente; com `backdrop` (quadro HD do reator, sem textos), a imagem é deslocada
    para a fração `place` da largura e entra esmaecida, sem competir com o texto à esquerda."""
    W, H = size
    bg = _gradient(W, H)
    if backdrop is not None:
        from PIL import Image
        im = np.asarray(Image.fromarray(np.asarray(backdrop, np.uint8)).resize((W, H), Image.LANCZOS), np.float32)
        bg = _compose(bg, im, place, strength, ramp_from, _bright_cx(im))
    return np.clip(bg, 0, 255)


def _probe(src: str):
    """(largura, altura, duração [s]) de um vídeo, lidos da saída do ffmpeg."""
    txt = subprocess.run([shutil.which("ffmpeg"), "-i", src], capture_output=True, text=True).stderr
    m = re.search(r", (\d{2,5})x(\d{2,5})", txt)
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", txt)
    dur = 3600 * int(d.group(1)) + 60 * int(d.group(2)) + float(d.group(3)) if d else 0.0
    return int(m.group(1)), int(m.group(2)), dur


class Backdrop:
    """Fundo dos cartões. Aceita None, um quadro RGB (fundo fixo) ou um vídeo limpo (sem textos) do
    reator girando: aí a imagem se move atrás dos textos, em câmera lenta (`speed`) e em
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
        self.cx = _bright_cx(np.mean([f.astype(np.float32) for f in fr[::max(1, len(fr) // 8)]], axis=0))
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
    backdrop: None, quadro RGB (ex.: um quadro HD do reator) ou Backdrop (reator em movimento), mostrado
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

    kpis = [{"value": 169, "fmt": "{:.0f}", "unit": "kg/h", "label": "plástico processado",
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

def render_still(src_png: str, path: str, seconds: float = 5.0, fps: int = 30):
    """Segmento de vídeo a partir de uma imagem fixa (1920×1080)."""
    ff = shutil.which("ffmpeg")
    subprocess.run([ff, "-y", "-loop", "1", "-framerate", str(fps), "-t", f"{seconds}", "-i", src_png,
                    "-vf", "scale=1920:1080,setsar=1,format=yuv420p", "-c:v", "libx264", "-crf", "16",
                    "-preset", "medium", path], check=True, capture_output=True)
    return path


def assemble(segments: list[str], out: str, fps: int = 30, size: tuple = (1920, 1080), crf: int = 16) -> str:
    """Concatena os segmentos em um MP4 final na resolução `size` (os de outra resolução são reescalados
    com Lanczos, preservando o aspecto)."""
    ff = shutil.which("ffmpeg")
    if ff is None:
        raise RuntimeError("ffmpeg não encontrado")
    segs = [p for p in segments if p and Path(p).exists()]
    cmd = [ff, "-y"]
    for p in segs:
        cmd += ["-i", p]
    W, H = size
    chains = "".join(f"[{i}:v]scale={W}:{H}:flags=lanczos:force_original_aspect_ratio=decrease,"
                     f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p[v{i}];"
                     for i in range(len(segs)))
    cmd += ["-filter_complex", chains + "".join(f"[v{i}]" for i in range(len(segs)))
            + f"concat=n={len(segs)}:v=1:a=0[v]", "-map", "[v]", "-c:v", "libx264", "-crf", str(crf),
            "-preset", "slow", "-tune", "film", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


