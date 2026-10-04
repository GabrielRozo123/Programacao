"""Renderização HD (pós-processamento): cor da fuligem, quadro sintético e codificação."""
import shutil

import numpy as np
import pytest

from flarekit import hd


def _fake_rec(n=3):
    class R:
        pass
    xc = np.linspace(-10, 40, 101)
    zc = np.linspace(20, 70, 101)
    X, Z = np.meshgrid(xc, zc, indexing="ij")
    rec = R()
    rec.static = dict(xc=xc, zc=zc, tip=np.array([0.0, 0.0, 30.0]), u_ref=8.0, summary="CPU")
    rec.frames = []
    for k in range(n):
        lum = 100.0 * np.exp(-(((X - 8 - k) / 6) ** 2 + ((Z - 40) / 4) ** 2))
        rec.frames.append(dict(t=0.1 * k, L=20.0, lum=lum.astype(np.float16),
                               tl=(1300 + 600 * lum / lum.max()).astype(np.float16)))
    rec.final = {}
    return rec


def test_soot_color_shifts_with_temperature():
    T, rgb, w = hd.soot_color_lut()
    c1000, c2500 = rgb[np.searchsorted(T, 1000)], rgb[np.searchsorted(T, 2500)]
    assert c1000[0] >= c1000[1] >= c1000[2]                 # fuligem fria: vermelha
    assert c2500[1] / c2500[0] > c1000[1] / c1000[0]         # mais quente: mais amarela/branca
    assert np.all(np.diff(w) > 0)                            # brilho visível cresce com T


def test_hd_frame_lights_the_flame_only():
    rec = _fake_rec()
    r = hd.HDFlameRenderer(rec, size=(320, 180), detail=0.35, device="cpu")
    img = r.to_uint8(r.frame(rec.frames[-1]))
    assert img.shape == (180, 320, 3)
    x0, x1, z0, z1 = r.view
    j = int((10 - x0) / (x1 - x0) * 320)                      # pixel perto do centro da chama
    i = int((z1 - 40) / (z1 - z0) * 180)
    assert img[i, j].sum() > 3 * img[5, 5].sum()             # chama muito mais clara que o céu


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg ausente")
def test_hd_segment_and_cards(tmp_path):
    rec = _fake_rec()
    out = hd.render_flame_hd(rec, str(tmp_path / "f.mp4"), "t", "s", resolution=(320, 180), fps=10,
                             device="cpu", log_every=0)
    assert (tmp_path / "f.mp4").stat().st_size > 0 and out.endswith("f.mp4")
    hd.render_text_cards(str(tmp_path / "c.mp4"), [{"kicker": "k", "headline": "título", "bullets": ["a", "b"]}],
                         size=(320, 180), fps=10, seconds=1.0)
    hd.render_title_card(str(tmp_path / "t.mp4"), "título", "sub", size=(320, 180), fps=10, seconds=1.0)
    assert (tmp_path / "c.mp4").stat().st_size > 0 and (tmp_path / "t.mp4").stat().st_size > 0


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg ausente")
def test_animated_backdrop_cards_and_cover(tmp_path):
    rec = _fake_rec(12)
    clean = str(tmp_path / "fundo.mp4")
    hd.render_flame_hd(rec, str(tmp_path / "f.mp4"), "t", "s", resolution=(320, 180), fps=10, device="cpu",
                       log_every=0, clean_path=clean)
    bd = hd.Backdrop(clean, (320, 180), width=160)
    assert bd.animated and len(bd.frames) >= 8          # só a parte desenvolvida da chama (75% final)
    a, b = bd.next(), bd.next()
    assert a.shape == (180, 320, 3) and a.dtype == np.uint8
    for _ in range(3 * len(bd.frames)):                  # o laço não estoura índices
        bd.next()
    still = hd.Backdrop(np.full((90, 160, 3), 200, np.uint8), (320, 180))
    assert not still.animated and np.array_equal(still.next(), still.next())
    hd.render_title_card(str(tmp_path / "t.mp4"), "título", "sub", size=(320, 180), fps=10, seconds=1.0,
                         backdrop=bd, contact="linkedin.com/in/exemplo")
    hd.render_text_cards(str(tmp_path / "c.mp4"), [{"kicker": "k", "headline": "título", "bullets": ["a"]}],
                         size=(320, 180), fps=10, seconds=1.0, backdrop=bd)
    hd.render_kpi_card(str(tmp_path / "k.mp4"), "números", [{"value": 1.5, "unit": "kW/m²", "label": "x"}],
                       size=(320, 180), fps=10, seconds=1.0, backdrop=bd)
    hd.caption_segment(str(tmp_path / "t.mp4"), str(tmp_path / "s.mp4"), ["legenda"], "1. capítulo",
                       size=(320, 180), fps=10, handle="linkedin.com/in/exemplo")
    cover = hd.still_of(str(tmp_path / "t.mp4"), str(tmp_path / "capa.png"), 0.5)
    assert (tmp_path / "capa.png").stat().st_size > 0 and cover.endswith("capa.png")


def test_wrap_keeps_units_and_states_together():
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = hd._wrap(d, "vento de Paulínia (SP) a 5,2 m/s e 567 MW", hd._font(20), 90)
    assert not any(ln.startswith(("(SP)", "m/s", "MW")) for ln in lines)
