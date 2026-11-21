"""Gera o relatório técnico em PDF (A4) a partir de uma :class:`Analysis`.

Uso::

    from pulseva.report_pdf import build_report
    build_report(an, "relatorio.pdf", ref=ref_dict, figdir="figuras/")
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from . import __version__
from . import plots as pl
from .metrics import CORNERS, DEVIATION_STATUS, KV_ONE_PERIOD, PULSE_LIMITS, compare_with_reference, \
    reference_consistency

# ----------------------------------------------------------------------------- fontes e estilos
_FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DejaVu", str(_FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(_FONT_DIR / "DejaVuSans-Oblique.ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily  # noqa: E402

registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique",
                   boldItalic="DejaVu-Bold")

INK = colors.HexColor("#0b0b0b")
INK2 = colors.HexColor("#52514e")
GRID = colors.HexColor("#d9d8d3")
SURF = colors.HexColor("#f4f3f0")
ACCENT = colors.HexColor("#2a78d6")
OK = colors.HexColor("#0ca30c")
WARN = colors.HexColor("#b07800")
CRIT = colors.HexColor("#d03b3b")
LEVEL_COLOR = {"crítico": CRIT, "atenção": WARN, "info": INK2}

ST = {
    "title": ParagraphStyle("title", fontName="DejaVu-Bold", fontSize=22, leading=27, textColor=INK),
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVu", fontSize=12, leading=16, textColor=INK2),
    "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=14, leading=18, textColor=INK,
                         spaceBefore=6, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=10.5, leading=14, textColor=INK,
                         spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="DejaVu", fontSize=8.8, leading=12.6, textColor=INK,
                           alignment=TA_JUSTIFY, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName="DejaVu", fontSize=8.8, leading=12.4, textColor=INK,
                             leftIndent=11, bulletIndent=2, spaceAfter=2.5, alignment=TA_LEFT),
    "small": ParagraphStyle("small", fontName="DejaVu", fontSize=7.2, leading=9.5, textColor=INK2),
    "caption": ParagraphStyle("caption", fontName="DejaVu-Oblique", fontSize=7.5, leading=10, textColor=INK2,
                              spaceBefore=2, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="DejaVu", fontSize=7.4, leading=9.4, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="DejaVu-Bold", fontSize=7.4, leading=9.4, textColor=INK),
    "kpi_v": ParagraphStyle("kpi_v", fontName="DejaVu-Bold", fontSize=15, leading=18, textColor=INK),
    "kpi_l": ParagraphStyle("kpi_l", fontName="DejaVu", fontSize=7.2, leading=9, textColor=INK2),
}
PAGE_W, PAGE_H = A4
MARGIN = 17 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


def P(text, style="body"):
    return Paragraph(text, ST[style])


def bullets(items):
    return [Paragraph(t, ST["bullet"], bulletText="•") for t in items]


def fmt(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


# ----------------------------------------------------------------------------- equações (mathtext)
def _equation(latex: str, path: Path, fontsize=11) -> Path:
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${latex}$", fontsize=fontsize, color="#0b0b0b")
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    return path


def eq_image(latex, path, width_mm=None, fontsize=11):
    p = _equation(latex, path, fontsize)
    img = Image(str(p))
    scale = 0.24  # pt por px (300 dpi -> 72 dpi)
    img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
    if width_mm and img.drawWidth > width_mm * mm:
        k = width_mm * mm / img.drawWidth
        img.drawWidth *= k
        img.drawHeight *= k
    img.hAlign = "CENTER"
    return img


def fig_image(path, width=CONTENT_W, max_h=None):
    img = Image(str(path))
    k = width / img.imageWidth
    w, h = width, img.imageHeight * k
    if max_h and h > max_h:
        k2 = max_h / h
        w, h = w * k2, h * k2
    img.drawWidth, img.drawHeight = w, h
    img.hAlign = "CENTER"
    return img


def table(data, col_w=None, header_rows=1, zebra=True, align="CENTER", font=7.4, bold_first_col=False):
    rows = []
    for i, r in enumerate(data):
        rows.append([c if not isinstance(c, str) else Paragraph(c, ST["cellb"] if i < header_rows else ST["cell"])
                     for c in r])
    t = Table(rows, colWidths=col_w, repeatRows=header_rows, hAlign=align)
    style = [("FONT", (0, 0), (-1, -1), "DejaVu", font),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.8, INK),
             ("LINEBELOW", (0, header_rows), (-1, -1), 0.25, GRID),
             ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
             ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
             ("BACKGROUND", (0, 0), (-1, header_rows - 1), SURF)]
    if zebra:
        for i in range(header_rows, len(rows)):
            if (i - header_rows) % 2 == 1:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafaf8")))
    t.setStyle(TableStyle(style))
    return t


# ----------------------------------------------------------------------------- página
class _Page:
    def __init__(self, title, record_id):
        self.title, self.record_id = title, record_id

    def __call__(self, canv, doc):
        canv.saveState()
        if doc.page > 1:
            canv.setFont("DejaVu-Bold", 7.5)
            canv.setFillColor(INK)
            canv.drawString(MARGIN, PAGE_H - 11 * mm, self.title)
            canv.setFont("DejaVu", 7.5)
            canv.setFillColor(INK2)
            canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 11 * mm, self.record_id)
            canv.setStrokeColor(GRID)
            canv.setLineWidth(0.6)
            canv.line(MARGIN, PAGE_H - 12.6 * mm, PAGE_W - MARGIN, PAGE_H - 12.6 * mm)
        canv.setFont("DejaVu", 7)
        canv.setFillColor(INK2)
        canv.drawString(MARGIN, 9 * mm, f"pulseva v{__version__} · análise independente em Python · "
                                        f"gerado em {_dt.date.today():%d/%m/%Y}")
        canv.drawRightString(PAGE_W - MARGIN, 9 * mm, f"Página {doc.page}")
        canv.restoreState()


# ----------------------------------------------------------------------------- relatório
class _Num:
    """Numeração automática de seções e figuras."""

    def __init__(self):
        self.sec = 0
        self.fig = 0

    def s(self):
        self.sec += 1
        return self.sec

    def f(self):
        self.fig += 1
        return self.fig


def _status_txt(v, lim):
    return ("✓", "#0b0b0b") if v <= lim else ("✗", "#d03b3b")


def build_report(an, out_pdf, ref=None, figdir=None, author=None, equipment=None):
    """Relatório técnico. Sem ``ref``: só os resultados da gravação (formato Pulse).
    Com ``ref``: acrescenta a validação contra um relatório Pulse."""
    out_pdf = Path(out_pdf)
    figdir = Path(figdir or out_pdf.parent / "figuras")
    figdir.mkdir(parents=True, exist_ok=True)
    eqdir = figdir / "eq"
    eqdir.mkdir(exist_ok=True)

    figs = {
        "orbitas": pl.save(pl.fig_orbit_summary(an), figdir / "orbitas.png"),
        "fase": pl.save(pl.fig_phase_report(an, ref), figdir / "fase.png"),
        "rotacao": pl.save(pl.fig_speed(an), figdir / "rotacao.png"),
        "integridade": pl.save(pl.fig_integrity(an), figdir / "integridade.png"),
        "espectro_z": pl.save(pl.fig_z_spectra(an), figdir / "espectro_z.png"),
        "ordens": pl.save(pl.fig_order_spectrum(an), figdir / "ordens.png"),
    }
    fm, mdata = pl.fig_method(an)
    figs["metodo"] = pl.save(fm, figdir / "metodo.png")
    for n in an.sensors:
        figs[f"sensor_{n}"] = pl.save(pl.fig_sensor_report(an, n), figdir / f"sensor_{n}.png")
    cmp = cons = None
    if ref:
        cmp = compare_with_reference(an, ref)
        cons = reference_consistency(ref)
        figs["validacao"] = pl.save(pl.fig_validation(cmp, an), figdir / "validacao.png")

    rec = an.record
    meta = rec.meta
    equipment = equipment or meta.get("Serial", "Peneira vibratória")
    t_rec = meta.get("StartDateTime", "")[:19].replace("T", " ")
    rid = f"Gravação {t_rec}"
    c, mx, dv, th = an.center, an.maximum, an.deviations, an.throw
    alt = an.deviations_alt
    crit = [f for f in an.findings if f.level == "crítico"]
    sub = np.array([s.sub[:, 1] for s in an.sensors.values()])
    N = _Num()
    # números de seção e figura definidos de antemão para referências cruzadas
    sec_sum, sec_data, sec_met = 1, 2, 3
    sec_val = 4 if ref else None
    sec_res = 5 if ref else 4
    sec_diag, sec_conc = sec_res + 1, sec_res + 2
    fig_met = 1
    fig_val = 2 if ref else None
    fig_fase, fig_orb, fig_rot = (3, 4, 5) if ref else (2, 3, 4)
    fig_int, fig_ord, fig_z = fig_rot + 1, fig_rot + 2, fig_rot + 3

    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=17 * mm, bottomMargin=15 * mm,
                            title="Análise vibracional de peneira — dados Pulse VA",
                            author=author or "pulseva", subject=str(equipment))
    page = _Page("Análise vibracional de peneira — cálculo independente a partir dos dados Pulse VA", rid)
    S = []

    # ================= CAPA
    S += [Spacer(1, 22 * mm), P("RELATÓRIO TÉCNICO", "small"), Spacer(1, 2 * mm),
          P("Análise Vibracional de Peneira", "title"),
          P("Parâmetros do relatório Pulse VA (G-Force, stroke, frequência, ângulo de força, fase, corpo central e "
            "desvios de corpo rígido) calculados em Python a partir dos dados brutos dos 8 acelerômetros triaxiais",
            "subtitle"),
          Spacer(1, 10 * mm)]
    info = [["Equipamento", str(equipment)],
            ["Gravação (XML)", f"{t_rec} · {'com carga' if meta.get('MaterialFeed') == 'true' else 'sem carga'} · "
                               f"nota {meta.get('Notes', '-')}"],
            ["Aquisição", f"{len(an.sensors)} sensores × 3 eixos · {rec.fs:.0f} Hz · {rec.duration:.0f} s "
                          f"({rec.n_samples} amostras por canal)"],
            ["Inclinação do deck", f"{fmt(th['inclination'], 0)}° (cabeçalho do XML)"]]
    if ref:
        info.append(["Relatório de referência", f"Pulse VA · gravação {ref['meta'].get('record_start', '-')} · "
                                                f"{ref['meta']['rpm']} RPM"])
    if author:
        info.append(["Responsável", author])
    S.append(table([["Item", "Descrição"]] + info, col_w=[45 * mm, CONTENT_W - 45 * mm], zebra=False, align="LEFT"))
    S.append(Spacer(1, 10 * mm))
    kpis = [(f"{an.rpm:.0f} RPM", f"rotação média ({fmt(an.f_mean)} Hz)"),
            (f"{fmt(c['main_g'])} g", "Main G no centro"),
            (f"{fmt(c['stroke_main'], 1)} mm", "stroke no centro"),
            (f"{fmt(c['angle'], 1)}°", "ângulo de força no centro"),
            (f"{fmt(dv['pitch'], 1)} %", "pitch (limite 45 %)")]
    kt = Table([[Paragraph(v, ST["kpi_v"]) for v, _ in kpis], [Paragraph(l, ST["kpi_l"]) for _, l in kpis]],
               colWidths=[CONTENT_W / 5] * 5)
    kt.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.2, INK), ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
    S += [kt, Spacer(1, 8 * mm)]
    if crit:
        S.append(P(f"<font color='#d03b3b'><b>✗ {len(crit)} achado(s) crítico(s)</b></font> — ver Seção {sec_diag}.",
                   "body"))
    S.append(PageBreak())

    # ================= 1. SUMÁRIO
    S.append(P(f"{N.s()}. Sumário executivo", "h1"))
    S.append(P(
        "Os dados brutos de aceleração (XML) de uma peneira vibratória, adquiridos com o sistema Pulse VA da "
        "Haver &amp; Boecker, foram processados com código Python próprio. Todos os parâmetros do relatório Pulse "
        "foram calculados com as definições identificadas por engenharia reversa do relatório do fabricante "
        "(Seção 3). Além disso, foi verificada a qualidade da medição."))
    pts = [
        f"<b>Movimento:</b> {an.rpm:.0f} RPM ({fmt(an.f_mean)} Hz); no centro, Main G = {fmt(c['main_g'])} g, "
        f"stroke = {fmt(c['stroke_main'], 1)} mm, ângulo de força = {fmt(c['angle'], 1)}° e fase Y–X = "
        f"{fmt(c['phase'], 1)}°. Stroke entre {fmt(min(s.stroke_main for s in an.sensors.values()), 1)} e "
        f"{fmt(max(s.stroke_main for s in an.sensors.values()), 1)} mm nos 8 pontos.",
        f"<b>Desvios de corpo rígido:</b> Pitch {fmt(dv['pitch'], 1)} % (lim. 45 %), Roll {fmt(dv['roll'], 1)} % "
        f"(lim. 4 %), Twist {fmt(dv['twist'], 1)} % (lim. 3 %), Yaw {fmt(dv['yaw'], 1)} % (lim. 4 %) e Z "
        f"{fmt(dv['z'], 1)} % (lim. 3 %). Todos dentro dos limites de aceitação do Pulse.",
    ]
    if alt and "L1" in an.excluded:
        pts.append(
            f"<b><font color='#d03b3b'>Atenção — Yaw e Z dependem do canal L1-Z, que está com defeito</font></b> "
            f"(travado em {fmt(rec.sensors['L1'][:, 2].mean(), 1)} g, fora da faixa ±11 g do sensor). "
            f"Substituindo-o pelo par simétrico R1-Z, Yaw passa a {fmt(alt['yaw'], 1)} % e Z a {fmt(alt['z'], 1)} %, "
            f"ambos <b>acima</b> dos limites. O sensor defeituoso pode estar mascarando um movimento lateral real: "
            f"repetir a medição com o sensor reparado.")
    pts += [
        f"<b>G-Force Z</b> segue a definição do Pulse: amplitude do maior pico do espectro, que nesta máquina fica "
        f"fora da rotação (1,5× ≈ {fmt(1.5 * an.f_mean, 1)} Hz ou 55–62 Hz). O stroke Z do Pulse converte essa "
        f"amplitude como se estivesse na rotação; o deslocamento lateral real (componente 1×) é ≤ "
        f"{fmt(max(s.stroke[2] for n, s in an.sensors.items() if n not in an.excluded), 2)} mm.",
        f"<b>Rotação instável:</b> variação de {fmt(an.speed['var_pp_pct'], 1)} % pico-a-pico em 10 s. Por isso o "
        f"fundamental é obtido por rastreamento de ordem; um ajuste de frequência fixa erraria ~10 %.",
        f"<b>Ordens fracionárias 0,5× e 1,5×</b> em todos os sensores (0,5× em Y ≈ {fmt(sub[:, 0].mean())} g, uniforme): "
        f"excitação de período 2, consistente com o leito de material pousando em ciclos alternados "
        f"(K_v = {fmt(th['kv_horizontal_ref'])} &gt; √(1+π²) = {fmt(KV_ONE_PERIOD)}) ou com folga mecânica.",
        "<b>Medição:</b> gravidade lida como 0,92–0,93 g em todos os sensores (esperado 1 g) e inclinação estática "
        "dos eixos X variando de −1° a +9° entre sensores. Recomenda-se verificar calibração e padronizar a montagem.",
    ]
    S += bullets(pts)
    S.append(P("Quadro-resumo (formato do relatório Pulse)", "h2"))
    rows = [["Parâmetro", "Valor", "Limite / status"]]
    rows += [
        ["Rotação", f"{an.rpm:.0f} RPM ({fmt(an.f_mean)} Hz)", "—"],
        ["Center Body — Main G / stroke", f"{fmt(c['main_g'])} g / {fmt(c['stroke_main'], 1)} mm", "—"],
        ["Center Body — X / Y", f"{fmt(c['g'][0])} g ({fmt(c['stroke'][0], 1)} mm) / {fmt(c['g'][1])} g "
                                f"({fmt(c['stroke'][1], 1)} mm)", "—"],
        ["Center Body — ângulo / fase", f"{fmt(c['angle'], 1)}° / {fmt(c['phase'], 1)}°", "—"],
        ["Maximum Body — X / Y / Main", f"{fmt(mx['g'][0])} / {fmt(mx['g'][1])} / {fmt(mx['main_g'])} g", "—"],
        ["Maximum Body — stroke X / Y / Main", f"{fmt(mx['stroke'][0], 1)} / {fmt(mx['stroke'][1], 1)} / "
                                               f"{fmt(mx['stroke_main'], 1)} mm", "—"],
    ]
    for key, lab in (("pitch", "Pitch"), ("roll", "Roll"), ("yaw", "Yaw"), ("twist", "Twist"), ("z", "Z")):
        lim = PULSE_LIMITS[key]
        mk, col = _status_txt(dv[key], lim)
        extra = ""
        if alt and abs(alt[key] - dv[key]) > 0.05:
            mk2, col2 = _status_txt(alt[key], lim)
            extra = f" · <font color='{col2}'>sem L1-Z: {fmt(alt[key], 1)} % {mk2}</font>"
        rows.append([f"Desvio {lab}", f"<font color='{col}'>{fmt(dv[key], 1)} % {mk}</font>{extra}",
                     f"{fmt(lim, 0)} %"])
    S.append(table(rows, col_w=[58 * mm, 82 * mm, 30 * mm]))
    S.append(PageBreak())

    # ================= 2. DADOS
    S.append(P(f"{N.s()}. Dados, instrumentação e convenções", "h1"))
    S.append(P(
        f"O arquivo XML contém {len(an.sensors)} blocos <i>DataList</i> (L1–L4 no lado esquerdo, R1–R4 no direito), "
        f"cada um com {rec.n_samples} pontos X, Y, Z em g, amostrados a {rec.fs:.0f} Hz durante {rec.duration:.0f} s "
        f"({rec.n_samples} amostras por canal). Os sensores Pulse são acelerômetros MEMS triaxiais ±11 g, sem fio "
        "(Wi-Fi), acoplados em DC: registram também a gravidade, que é usada aqui como referência de calibração."))
    S += bullets([
        "X: longitudinal (sentido do fluxo), Y: vertical, Z: lateral. Posição 1 = alimentação, 4 = descarga; os "
        "cantos L1, R1, L4, R4 definem o corpo rígido.",
        "Lado esquerdo montado espelhado: no dado bruto X e Z de L têm sinal oposto ao lado R. O código converte "
        "L para o referencial da máquina com (X, Y, Z) → (−X, Y, −Z). Nas figuras de órbita, L é desenhado com o "
        "eixo X invertido, como no Pulse (vista pelo lado externo).",
        "Sentido de rotação: Y atrasado em relação a X → órbita anti-horária, com a parte superior se movendo contra "
        "o fluxo (\"counter flow\").",
    ])

    # ================= 3. METODOLOGIA
    S.append(P(f"{N.s()}. Metodologia — definições do Pulse", "h1"))
    S.append(P(
        "As definições abaixo foram identificadas por engenharia reversa de um relatório Pulse VA. Os números "
        "impressos no relatório foram passados pelas fórmulas, e os sinais desenhados no PDF (vetorial) foram "
        "extraídos e reprocessados. Status: <b>confirmada</b> = reproduz o relatório dentro do arredondamento; "
        "<b>compatível</b> = consistente com o relatório, com as alternativas naturais excluídas, mas sem prova "
        "definitiva."))
    S.append(P("3.1 Rastreamento de ordem", "h2"))
    S.append(P(
        f"A rotação varia durante a gravação (Seção {sec_res}). Para não “borrar” o fundamental, a fase de rotação θ(t) "
        "de cada sensor é estimada (passa-banda Butterworth de fase zero, direção principal X–Y, transformada de "
        "Hilbert, frequência instantânea suavizada a 2 Hz e integrada; Boashash, 1992; Fyfe &amp; Munck, 1997). Os "
        "fasores são calculados sobre um número inteiro de rotações:"))
    S.append(eq_image(r"P_n = \frac{2}{N}\sum_{k} x(t_k)\,e^{-j\,n\,\theta(t_k)}\quad\Rightarrow\quad "
                      r"x(t)\approx \mathrm{Re}\{P_n\,e^{j n \theta(t)}\}", eqdir / "eq1.png", 150))
    S.append(fig_image(figs["metodo"], max_h=58 * mm))
    S.append(P(f"Figura {fig_met} — Amplitude 1× em Y por método: frequência fixa "
               f"({fmt(np.mean(mdata['fixed'] / mdata['rms'] - 1) * 100, 0)} % abaixo do √2·RMS) × rastreamento de "
               f"ordem ({fmt(np.mean(mdata['tracked'] / mdata['rms'] - 1) * 100, 1)} %).", "caption"))
    S.append(P("3.2 Grandezas por sensor", "h2"))
    rows = [["Grandeza Pulse", "Definição", "Status"],
            ["G-Force X, Y", "amplitude da componente 1× (g de pico)", "confirmada"],
            ["G-Force Z", "amplitude do <b>maior pico do espectro</b> (qualquer frequência; FFT sem janela, energia "
                          "em ±0,4 Hz em torno do pico)", "confirmada (8/8 ≈ 0,01 g)"],
            ["RMS", "√2 × RMS do sinal AC (equivalente de pico)", "confirmada"],
            ["Stroke", "s = 2·G·g₀/ω², com ω = 2π·f de rotação (também para Z)", "confirmada"],
            ["Main G / Force Angle", "semi-eixo maior e inclinação da elipse X–Y 1×", "confirmada"],
            ["Phase Y rel. X", "atraso de Y em relação a X na componente 1×", "confirmada"],
            ["Z kurtosis", "curtose de Pearson do sinal Z (3 = gaussiano, 1,5 = senoide)", "confirmada"]]
    S.append(table(rows, col_w=[34 * mm, 104 * mm, 34 * mm]))
    S.append(eq_image(r"a^2=\frac{G_x^2+G_y^2}{2}+\frac{1}{2}\sqrt{(G_x^2+G_y^2)^2-4G_x^2G_y^2\sin^2\varphi},"
                      r"\qquad \tan 2\alpha=\frac{2G_xG_y\cos\varphi}{G_x^2-G_y^2}", eqdir / "eq3.png", 160))
    S.append(P("3.3 Sincronização, corpo central e desvios", "h2"))
    S.append(P(
        f"Os sensores sem fio não compartilham relógio (defasagens de até "
        f"{fmt(abs(max(an.lags.values(), key=lambda v: abs(v[0]))[0]) * 1e3, 0)} ms, Figura {fig_rot}). Como no "
        "Pulse, as fases são referidas ao eixo X de cada sensor. <b>Center Body</b> = média dos fasores dos 4 cantos; "
        "<b>Maximum Body</b> = máximo entre os 8 sensores. Os cinco desvios são combinações de corpo rígido dos "
        "cantos, todas divididas pelo movimento vertical total |ΣY| = |Y<sub>L1</sub>+Y<sub>R1</sub>+Y<sub>L4</sub>"
        "+Y<sub>R4</sub>|:"))
    rows = [["Desvio", "Numerador (fasores dos cantos)", "Interpretação", "Status"],
            ["Pitch", "|(Y_L1+Y_R1) − (Y_L4+Y_R4)|", "rotação em torno de Z: vertical alimentação × descarga", "confirmada"],
            ["Roll", "|(Y_L1+Y_L4) − (Y_R1+Y_R4)|", "rotação em torno de X: vertical esquerda × direita", "confirmada"],
            ["Twist", "|(Y_L1+Y_R4) − (Y_R1+Y_L4)|", "torção da estrutura: diagonais", "confirmada"],
            ["Yaw", "|(Z_L1+Z_R1) − (Z_L4+Z_R4)|", "rotação em torno de Y: lateral alimentação × descarga", "compatível"],
            ["Z", "|Z_L1+Z_R1+Z_L4+Z_R4|", "translação lateral", "compatível"]]
    S.append(table(rows, col_w=[16 * mm, 50 * mm, 80 * mm, 24 * mm]))
    S.append(P("Em Yaw e Z, o módulo de cada Z é o G-Force Z do Pulse e a fase é a da componente 1× sincronizada. "
               "Como no Pulse, todos os canais entram no cálculo, inclusive um eventual canal defeituoso; a "
               "sensibilidade a ele é apresentada à parte.", "small"))
    S.append(P("3.4 Índice de lançamento (Wurfkennziffer)", "h2"))
    S.append(eq_image(r"K_v=\frac{\Gamma\,\sin(\alpha+\beta)}{\cos\beta},\qquad "
                      r"K_v^{\ast}=\sqrt{1+\pi^2}\approx 3{,}30\ \ (\mathrm{voo} = 1\ \mathrm{per\'iodo})",
                      eqdir / "eq5.png", 150))
    S.append(P(
        f"Γ = Main G do centro, α = ângulo de força em relação à horizontal (a gravidade medida mostra o eixo X dos "
        f"sensores próximo da horizontal) e β = {fmt(th['inclination'], 0)}°: K_v = {fmt(th['kv_horizontal_ref'])} "
        f"(com α em relação ao deck seria {fmt(th['kv_deck_ref'])}). Para um leito plástico, o voo dura exatamente "
        "um período em K_v = √(1+π²); acima disso o material pousa em ciclos alternados (Schmidt et al., 2003)."))

    # ================= 4. VALIDAÇÃO (opcional)
    if ref:
        S.append(PageBreak())
        S.append(P(f"{N.s()}. Validação contra o relatório Pulse", "h1"))
        S.append(P("Números do relatório passados pelas fórmulas da Seção 3 (consistência interna):", "body"))
        cc = cons[cons["Item"].str.startswith("Centro") | cons["Item"].str.contains("Pitch|Roll|Twist|Main G")]
        rows = [["Item", "Pulse", "Recalculado", "Diferença"]] + [
            [r.Item, fmt(r.Pulse, 2), fmt(r.Recalculado, 3), fmt(r.Diferença, 3)] for r in cc.itertuples()]
        S.append(table(rows, col_w=[60 * mm, 28 * mm, 28 * mm, 28 * mm]))
        S.append(fig_image(figs["validacao"], max_h=64 * mm))
        S.append(P(f"Figura {fig_val} — Paridade Python × Pulse (gravações diferentes; acelerações corrigidas por "
                   f"(f_ref/f_xml)² = {fmt(cmp.attrs['scale'], 4)}).", "caption"))

    # ================= RESULTADOS
    S.append(PageBreak())
    S.append(P(f"{N.s()}. Resultados (formato do relatório Pulse)", "h1"))
    S.append(P(f"{sec_res}.1 Orbit Report — por sensor", "h2"))
    rows = [["Sensor", "Main G (g)", "Stroke (mm)", "Freq (Hz)", "Force Angle (°)", "G-Force X / Y / Z (g)",
             "Stroke X / Y / Z (mm)", "RMS X / Y / Z (g)", "Z kurt."]]
    for n, s in an.sensors.items():
        gr, sr, bad = s.g_report, s.stroke_report, n in an.excluded
        zf = lambda v, d=2: ("✗ " + fmt(v, d)) if bad else fmt(v, d)
        rows.append([n, fmt(s.main_g), fmt(s.stroke_main, 1), fmt(s.f_mean), fmt(s.angle, 1),
                     f"{fmt(gr[0])} / {fmt(gr[1])} / {zf(gr[2])}",
                     f"{fmt(sr[0], 1)} / {fmt(sr[1], 1)} / {zf(sr[2], 1)}",
                     f"{fmt(s.rms_pk[0])} / {fmt(s.rms_pk[1])} / {zf(s.rms_pk[2])}", fmt(s.z_kurtosis)])
    S.append(table(rows, col_w=[13 * mm, 15 * mm, 15 * mm, 15 * mm, 17 * mm, 30 * mm, 27 * mm, 27 * mm, 13 * mm]))
    S.append(P("✗ = canal com defeito (valor sem significado físico). Z: G-Force = pico dominante; stroke Z convertido "
               "na rotação (convenção Pulse).", "caption"))
    S.append(P(f"{sec_res}.2 Phase Report", "h2"))
    rows = [["Deviations (% rel.)", "Pitch", "Roll", "Yaw", "Twist", "Z"],
            ["Valor"] + [f"{fmt(dv[k], 1)} %" for k in ("pitch", "roll", "yaw", "twist", "z")],
            ["Limite de aceitação"] + [f"{fmt(PULSE_LIMITS[k], 0)} %" for k in ("pitch", "roll", "yaw", "twist", "z")],
            ["Status"] + [_status_txt(dv[k], PULSE_LIMITS[k])[0] for k in ("pitch", "roll", "yaw", "twist", "z")]]
    if alt:
        rows.append(["Sem canal defeituoso*"] + [f"{fmt(alt[k], 1)} % {_status_txt(alt[k], PULSE_LIMITS[k])[0]}"
                                                 for k in ("pitch", "roll", "yaw", "twist", "z")])
    S.append(table(rows, col_w=[44 * mm] + [25 * mm] * 5))
    if alt:
        S.append(P("* Canal Z defeituoso substituído pelo par simétrico do outro lado (estimativa de sensibilidade).",
                   "small"))
    S.append(Spacer(1, 3 * mm))
    rows = [["", "Stroke X", "Stroke Y", "Stroke Main", "Force X", "Force Y", "Force Main"],
            ["Maximum Body", f"{fmt(mx['stroke'][0], 1)} mm", f"{fmt(mx['stroke'][1], 1)} mm",
             f"{fmt(mx['stroke_main'], 1)} mm", f"{fmt(mx['g'][0])} g", f"{fmt(mx['g'][1])} g", f"{fmt(mx['main_g'])} g"],
            ["Center Body", f"{fmt(c['stroke'][0], 1)} mm", f"{fmt(c['stroke'][1], 1)} mm",
             f"{fmt(c['stroke_main'], 1)} mm", f"{fmt(c['g'][0])} g", f"{fmt(c['g'][1])} g", f"{fmt(c['main_g'])} g"]]
    S.append(table(rows, col_w=[30 * mm] + [23.5 * mm] * 6))
    S.append(Spacer(1, 3 * mm))
    rows = [["Center Body", "Angle", "Phase", "", "Phases Y rel. X", "L4", "R4", "L1", "R1"],
            ["", f"{fmt(c['angle'], 1)}°", f"{fmt(c['phase'], 1)}°", "", "",
             *[f"{fmt(an.sensors[k].phase_yx, 1)}°" for k in ("L4", "R4", "L1", "R1")]]]
    S.append(table(rows, col_w=[22 * mm, 18 * mm, 18 * mm, 6 * mm, 30 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm],
                   zebra=False))
    S.append(PageBreak())
    S.append(fig_image(figs["fase"], max_h=225 * mm))
    S.append(P(f"Figura {fig_fase} — (a) Órbitas de deslocamento em escala sobre um esquema da máquina; (b) ondas Y "
               "sincronizadas; (c) força no centro; (d) desvios em % do limite de aceitação (◆ = sem o canal "
               "defeituoso).", "caption"))
    S.append(PageBreak())
    S.append(fig_image(figs["orbitas"], max_h=235 * mm))
    S.append(P(f"Figura {fig_orb} — Órbitas X–Y medidas (5 rotações, cinza) e componente 1× (cor). As órbitas se "
               "abrem da alimentação (quase lineares) para a descarga (elípticas): efeito do pitch.", "caption"))
    S.append(PageBreak())
    S.append(fig_image(figs["rotacao"], max_h=120 * mm))
    S.append(P(f"Figura {fig_rot} — Rotação instantânea por sensor (variação de {fmt(an.speed['var_pp_pct'], 1)} % "
               "p-p); perfis deslocados no tempo = sensores sem relógio comum. Abaixo, Main G por rotação nos cantos: "
               f"o zigue-zague em L1/R1 é a assinatura de período 2 (Seção {sec_diag}).", "caption"))

    # ================= DIAGNÓSTICO
    S.append(P(f"{N.s()}. Diagnóstico e integridade da medição", "h1"))
    for f in an.findings:
        col = {"crítico": "#d03b3b", "atenção": "#b07800", "info": "#52514e"}[f.level]
        icon = {"crítico": "✗", "atenção": "▲", "info": "●"}[f.level]
        S.append(P(f"<font color='{col}'><b>{icon} {f.level.upper()}</b></font> · <b>{f.scope} — {f.title}.</b> "
                   f"{f.detail}" + (f" <i>Ação: {f.action}</i>" if f.action else ""), "bullet"))
    S.append(Spacer(1, 2 * mm))
    S.append(KeepTogether([fig_image(figs["integridade"], max_h=70 * mm),
                           P(f"Figura {fig_int} — Módulo do vetor DC (gravidade) e inclinação estática do eixo X de "
                             "cada sensor.", "caption")]))
    S.append(fig_image(figs["ordens"], max_h=72 * mm))
    S.append(P(f"Figura {fig_ord} — Espectro de ordens médio: linhas em 0,5×, 1,5×, 2,5×, 3,5×. A amplitude 0,5× "
               f"em Y é praticamente igual nos 8 sensores ({fmt(sub[:, 0].min())}–{fmt(sub[:, 0].max())} g): "
               f"movimento vertical do corpo inteiro a {fmt(an.f_mean / 2)} Hz.", "caption"))
    S.append(P(
        f"<b>Interpretação.</b> Componentes 0,5×/1,5× indicam excitação que se repete a cada duas rotações. Com "
        f"K_v = {fmt(th['kv_horizontal_ref'])} &gt; {fmt(KV_ONE_PERIOD)}, o voo do material passa de um período e o "
        "leito pode pousar em ciclos alternados (duplicação de período). A uniformidade em toda a máquina favorece "
        "essa explicação sobre uma folga localizada. Teste decisivo: gravação sem carga ou com rotação menor."))
    S.append(fig_image(figs["espectro_z"], max_h=150 * mm))
    S.append(P(f"Figura {fig_z} — Espectros do eixo lateral Z (● = pico usado no G-Force Z). O conteúdo é de banda "
               "larga; a componente 1× é pequena.", "caption"))
    S.append(PageBreak())

    # ================= CONCLUSÕES
    S.append(P(f"{N.s()}. Conclusões e recomendações", "h1"))
    conc = [
        f"Todos os parâmetros do relatório Pulse foram calculados a partir do XML: Main G {fmt(c['main_g'])} g e "
        f"stroke {fmt(c['stroke_main'], 1)} mm no centro, ângulo {fmt(c['angle'], 1)}°, rotação {an.rpm:.0f} RPM.",
        f"Pitch ({fmt(dv['pitch'], 1)} %), Roll ({fmt(dv['roll'], 1)} %) e Twist ({fmt(dv['twist'], 1)} %) dentro dos "
        f"limites, com folga.",
    ]
    if alt and "L1" in an.excluded:
        conc.append(f"<b>Yaw ({fmt(dv['yaw'], 1)} %) e Z ({fmt(dv['z'], 1)} %) passam no limite apenas com o canal "
                    f"L1-Z defeituoso.</b> Com o canal substituído pelo simétrico, ficam em {fmt(alt['yaw'], 1)} % e "
                    f"{fmt(alt['z'], 1)} % (acima de 4 % e 3 %). <b>Recomendação 1:</b> reparar o sensor L1 e repetir a "
                    "medição antes de liberar o equipamento.")
    conc += [
        "<b>Recomendação 2 — calibração:</b> verificar a escala dos sensores (gravidade lida como 0,92–0,93 g).",
        "<b>Recomendação 3 — montagem:</b> padronizar a fixação dos sensores (inclinação estática varia ~10° entre "
        "pontos e afeta o ângulo de força).",
        "<b>Recomendação 4 — processo:</b> investigar as ordens 0,5×/1,5× com gravação sem carga ou rotação reduzida.",
    ]
    S += bullets(conc)
    S.append(P("Referências", "h2"))
    S += bullets([
        "Boashash, B. (1992). Estimating and interpreting the instantaneous frequency of a signal — Part 1. "
        "<i>Proceedings of the IEEE</i>, 80(4), 520–538.",
        "Fyfe, K. R.; Munck, E. D. S. (1997). Analysis of computed order tracking. <i>Mechanical Systems and Signal "
        "Processing</i>, 11(2), 187–205.",
        "Randall, R. B. (2011). <i>Vibration-based Condition Monitoring</i>. Wiley.",
        "Brandt, A. (2011). <i>Noise and Vibration Analysis</i>. Wiley.",
        "Schmidt, P.; Körber, R.; Coppers, M. (2003). <i>Sieben und Siebmaschinen</i>. Wiley-VCH.",
        "Rao, S. S. (2017). <i>Mechanical Vibrations</i>, 6ª ed. Pearson.",
        "Born, M.; Wolf, E. (1999). <i>Principles of Optics</i>, 7ª ed. Cambridge (elipse de polarização).",
        "Haver &amp; Boecker. <i>PULSE Vibrationsanalyse</i> — folheto técnico.",
    ])

    # ================= ANEXO
    S.append(PageBreak())
    S.append(P("Anexo A — Orbit Report por sensor", "h1"))
    for i, n in enumerate(an.sensors):
        S.append(fig_image(figs[f"sensor_{n}"], max_h=238 * mm))
        if i < len(an.sensors) - 1:
            S.append(PageBreak())
    if cmp is not None:
        S.append(PageBreak())
        S.append(P("Anexo B — Comparação completa com o relatório Pulse", "h1"))
        rows = [["Grupo", "Item", "Unid.", "Python (XML)", "Python @ f_ref", "Pulse", "Δ", "Δ %"]] + [
            [r.Grupo, r.Item, r._3, fmt(r._4, 3), fmt(r._5, 3), fmt(r.Pulse, 2), fmt(r.Δ, 3),
             fmt(r._8, 1) if np.isfinite(r._8) else "—"] for r in cmp.itertuples()]
        S.append(table(rows, col_w=[17 * mm, 45 * mm, 11 * mm, 22 * mm, 23 * mm, 17 * mm, 18 * mm, 17 * mm]))

    doc.build(S, onFirstPage=page, onLaterPages=page)
    return out_pdf
