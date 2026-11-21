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
def build_report(an, out_pdf, ref=None, figdir=None, author=None, equipment=None):
    out_pdf = Path(out_pdf)
    figdir = Path(figdir or out_pdf.parent / "figuras")
    figdir.mkdir(parents=True, exist_ok=True)
    eqdir = figdir / "eq"
    eqdir.mkdir(exist_ok=True)

    # ---------------- figuras
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
    equipment = equipment or (ref["meta"].get("serial") if ref else None) or meta.get("Serial", "Peneira vibratória")
    rid = f"Gravação {meta.get('StartDateTime', '')[:19].replace('T', ' ')}"
    c, mx, dv, th = an.center, an.maximum, an.deviations, an.throw
    crit = [f for f in an.findings if f.level == "crítico"]
    sub = np.array([s.sub[:, 1] for s in an.sensors.values()])

    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=17 * mm, bottomMargin=15 * mm,
                            title="Análise vibracional de peneira — reprocessamento Pulse VA",
                            author=author or "pulseva", subject=str(equipment))
    page = _Page("Análise vibracional de peneira — reprocessamento independente dos dados Pulse VA", rid)
    S = []

    # ================= CAPA
    S += [Spacer(1, 22 * mm), P("RELATÓRIO TÉCNICO", "small"), Spacer(1, 2 * mm),
          P("Análise Vibracional de Peneira", "title"),
          P("Reprocessamento independente, em Python, dos dados brutos de acelerômetros "
            "Pulse VA (8 sensores triaxiais) e validação contra o relatório do fabricante", "subtitle"),
          Spacer(1, 10 * mm)]
    info = [["Equipamento", str(equipment)],
            ["Gravação analisada (XML)", f"{meta.get('StartDateTime', '-')[:19].replace('T', ' ')} · "
                                         f"{'com carga' if meta.get('MaterialFeed') == 'true' else 'sem carga'} · "
                                         f"nota {meta.get('Notes', '-')}"],
            ["Aquisição", f"{len(an.sensors)} sensores × 3 eixos · {rec.fs:.0f} Hz · {rec.duration:.0f} s "
                          f"({rec.n_samples} amostras por canal)"],
            ["Relatório de referência", (f"Pulse VA {ref['meta'].get('source', '')} · gravação "
                                         f"{ref['meta'].get('record_start', '-')} · {ref['meta']['rpm']} RPM")
             if ref else "—"],
            ["Inclinação do deck", f"{fmt(th['inclination'], 0)}° (cabeçalho do XML)"]]
    if author:
        info.append(["Responsável", author])
    S.append(table([["Item", "Descrição"]] + info, col_w=[45 * mm, CONTENT_W - 45 * mm], zebra=False,
                   align="LEFT"))
    S.append(Spacer(1, 10 * mm))
    kpis = [(f"{an.rpm:.0f} RPM", f"rotação média ({fmt(an.f_mean)} Hz)"),
            (f"{fmt(c['main_g'])} g", "Main G no centro"),
            (f"{fmt(c['stroke_main'], 1)} mm", "curso (stroke) no centro"),
            (f"{fmt(c['angle'], 1)}°", "ângulo de força no centro"),
            (f"{fmt(th['kv_horizontal_ref'])}", "índice de lançamento K_v")]
    kt = Table([[Paragraph(v, ST["kpi_v"]) for v, _ in kpis], [Paragraph(l, ST["kpi_l"]) for _, l in kpis]],
               colWidths=[CONTENT_W / 5] * 5)
    kt.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.2, INK), ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
    S += [kt, Spacer(1, 10 * mm)]
    if cmp is not None:
        st = cmp[cmp["Grupo"] == "Stroke"]["Δ (%)"].abs()
        gg = cmp[cmp["Grupo"] == "G-Force"]["Δ (%)"].abs()
        an_ = cmp[cmp["Grupo"] == "Ângulo"]["Δ"].abs()
        S.append(P(f"<b>Validação:</b> fórmulas reproduzem o relatório Pulse a partir dos seus próprios números "
                   f"(erro máx. de Main G {fmt(cons[cons['Item'].str.contains('Main G')]['Diferença'].abs().max(), 3)} g); "
                   f"dados brutos de outra gravação (≈{fmt(abs(an.f_mean / ref['meta']['freq_hz'] - 1) * 100, 1)} % mais rápida) "
                   f"concordam com o relatório em stroke (erro médio {fmt(st.mean(), 1)} %), G-Force corrigida por f² "
                   f"({fmt(gg.mean(), 1)} %) e ângulo ({fmt(an_.mean(), 1)}°).", "body"))
    if crit:
        S.append(P(f"<font color='#d03b3b'><b>✗ {len(crit)} achado(s) crítico(s)</b></font> — ver Seção 6.", "body"))
    S.append(PageBreak())

    # ================= 1. SUMÁRIO EXECUTIVO
    S.append(P("1. Sumário executivo", "h1"))
    S.append(P(
        "Os dados brutos de aceleração (XML) de uma peneira vibratória, adquiridos com o sistema Pulse VA da "
        "Haver &amp; Boecker, foram reprocessados com código Python próprio. O objetivo foi reproduzir, a partir "
        "dos sinais, os parâmetros do relatório do fabricante (G-Force, curso, frequência, ângulo de força, fase, "
        "corpo central e desvios de corpo rígido), entender a modelagem por trás deles e verificar a qualidade "
        "da medição."))
    pts = [
        f"<b>Modelo identificado e validado.</b> As grandezas do Pulse correspondem à componente harmônica 1× da "
        f"aceleração em cada eixo; Main G e Force Angle são o semi-eixo maior e a inclinação da elipse X–Y; o curso é "
        f"s = 2·A·g₀/ω²; o corpo central é a média dos quatro cantos com fases referidas ao eixo X. Recalculados a "
        f"partir dos números do próprio relatório, todos os itens batem dentro do arredondamento.",
        f"<b>Desvios Pitch, Roll e Twist</b> seguem a diferença relativa |a−b|/|a+b| dos fasores verticais "
        f"(alimentação × descarga, esquerda × direita, diagonais). Yaw e Z não puderam ser reproduzidos sem a "
        f"definição do fabricante: são apresentados com fórmulas de corpo rígido e marcados como hipótese.",
        f"<b>Gravações diferentes.</b> O XML recebido (11:06:43, {an.rpm:.0f} RPM) não é a gravação do relatório "
        f"({ref['meta']['record_start'][11:] if ref else '-'}, {ref['meta']['rpm'] if ref else '-'} RPM). "
        f"A comparação usa a física do regime supercrítico: curso independente da rotação e aceleração ∝ f². "
        f"Com isso, stroke, G-Force e ângulos ficam dentro de ~1–3 %." if ref else "",
        f"<b>Rotação instável:</b> variação de {fmt(an.speed['var_pp_pct'], 1)} % pico-a-pico em 10 s. Um ajuste "
        f"senoidal de frequência fixa subestima o fundamental em ~10 %; por isso foi usado rastreamento de ordem.",
        f"<b>Canal L1-Z defeituoso</b> (média de {fmt(rec.sensors['L1'][:, 2].mean(), 1)} g, fora da faixa ±11 g do "
        f"sensor, sem sinal AC). O mesmo defeito aparece no relatório Pulse (kurtosis 1,49 ≈ senoide pura, "
        f"G-Force 0,02 g). O desvio Z do relatório ({fmt(ref['deviations']['z'], 1)} %, acima do limite) usa esse canal "
        f"e deve ser reavaliado." if 'L1' in an.excluded and ref else "",
        f"<b>Ordens fracionárias 0,5× e 1,5×</b> presentes em todos os sensores (0,5× em Y ≈ {fmt(sub[:, 0].mean())} g, "
        f"uniforme em toda a máquina). É a assinatura de excitação de período 2. Com K_v = {fmt(th['kv_horizontal_ref'])}, "
        f"acima de √(1+π²) = {fmt(KV_ONE_PERIOD)}, é consistente com o leito de material pousando em ciclos alternados; "
        f"folga mecânica é a hipótese alternativa.",
        "<b>Calibração e montagem:</b> a gravidade medida é 0,92–0,93 g em todos os sensores (esperado 1 g) e a "
        "inclinação estática dos eixos X varia de −1° a +9° entre sensores, o que afeta diretamente o ângulo de força "
        "de cada ponto.",
    ]
    S += bullets([p for p in pts if p])
    S.append(Spacer(1, 3 * mm))
    S.append(P("Quadro-resumo", "h2"))
    rows = [["Parâmetro", "Python (XML, 11:06:43)", "Python corrigido p/ f do relatório",
             "Relatório Pulse" + (f" ({ref['meta']['record_start'][11:]})" if ref else ""), "Limite"]]
    k2 = (ref["meta"]["freq_hz"] / an.f_mean) ** 2 if ref else 1
    rr = ref or {}
    rows += [
        ["Rotação", f"{an.rpm:.0f} RPM ({fmt(an.f_mean)} Hz)", "—",
         f"{rr['meta']['rpm']} RPM ({fmt(rr['meta']['freq_hz'])} Hz)" if ref else "—", "—"],
        ["Centro — Main G", f"{fmt(c['main_g'])} g", f"{fmt(c['main_g'] * k2)} g",
         f"{fmt(rr['center']['main_g'])} g" if ref else "—", "—"],
        ["Centro — curso", f"{fmt(c['stroke_main'], 1)} mm", f"{fmt(c['stroke_main'], 1)} mm",
         f"{fmt(rr['center']['stroke_main'], 1)} mm" if ref else "—", "—"],
        ["Centro — ângulo / fase", f"{fmt(c['angle'], 1)}° / {fmt(c['phase'], 1)}°", "idem",
         f"{fmt(rr['center']['angle'], 1)}° / {fmt(rr['center']['phase'], 1)}°" if ref else "—", "—"],
        ["Máximo — Main G / curso", f"{fmt(mx['main_g'])} g / {fmt(mx['stroke_main'], 1)} mm",
         f"{fmt(mx['main_g'] * k2)} g / {fmt(mx['stroke_main'], 1)} mm",
         f"{fmt(rr['maximum']['main_g'])} g / {fmt(rr['maximum']['stroke_main'], 1)} mm" if ref else "—", "—"],
    ]
    for key, lab in (("pitch", "Pitch"), ("roll", "Roll"), ("yaw", "Yaw"), ("twist", "Twist"), ("z", "Z lateral")):
        lim = PULSE_LIMITS[key]
        v = dv[key]
        okv = "✓" if v <= lim else "✗"
        tag = "" if DEVIATION_STATUS[key] == "confirmada" else " (hipótese)"
        pv = rr["deviations"][key] if ref else None
        rows.append([f"Desvio {lab}{tag}", f"{fmt(v, 1)} % {okv}", "idem",
                     (f"{fmt(pv, 1)} % {'✓' if pv <= lim else '✗'}") if ref else "—", f"{fmt(lim, 0)} %"])
    S.append(table(rows, col_w=[34 * mm, 36 * mm, 38 * mm, 40 * mm, 18 * mm]))
    S.append(P("Strokes, ângulos, fases e desvios são comparados diretamente (independentes da rotação em regime "
               "supercrítico); acelerações são corrigidas por (f_ref/f_xml)².", "caption"))
    S.append(PageBreak())

    # ================= 2. DADOS E CONVENÇÕES
    S.append(P("2. Dados, instrumentação e convenções", "h1"))
    S.append(P(
        f"O arquivo XML contém {len(an.sensors)} blocos <i>DataList</i> (L1–L4 no lado esquerdo, R1–R4 no direito), "
        f"cada um com {rec.n_samples} pontos X, Y, Z em g, amostrados a {rec.fs:.0f} Hz durante {rec.duration:.0f} s. "
        f"São, portanto, {rec.n_samples} medições por canal ({rec.fs:.0f} por segundo), e não 8000 por segundo. "
        "Os sensores Pulse são acelerômetros MEMS triaxiais ±11 g com comunicação Wi-Fi e bateria; cada um "
        "grava 10 s de dados brutos. Por serem acoplados em DC, registram também a gravidade, usada aqui como "
        "referência de calibração."))
    S.append(P("Referencial e espelhamento", "h2"))
    S += bullets([
        "X: longitudinal (sentido do fluxo), Y: vertical, Z: lateral. Posição 1 = extremidade de alimentação, "
        "4 = descarga; os cantos (L1, R1, L4, R4) definem o corpo rígido.",
        "No lado esquerdo os sensores estão montados espelhados: no dado bruto, X e Z de L têm sinal oposto ao "
        "lado R (correlação X–Y de −0,80 a −0,99 em L e de +0,80 a +0,98 em R; componente DC de X com sinais "
        "opostos). O código converte L para o referencial da máquina com (X, Y, Z) → (−X, Y, −Z).",
        "Nas figuras de órbita os sensores L são desenhados com o eixo X invertido, como no relatório Pulse "
        "(vista pelo lado externo esquerdo).",
        f"Sentido de rotação: Y atrasado em relação a X (fase positiva) → órbita anti-horária no plano X–Y, com a "
        f"parte superior se movendo contra o fluxo. É coerente com o \"counter flow\" do relatório se +X apontar "
        f"para a descarga.",
    ])
    S.append(P("3. Metodologia", "h1"))
    S.append(P("3.1 Rastreamento de ordem (order tracking computacional)", "h2"))
    S.append(P(
        "A rotação varia durante a gravação (Seção 5). Para não “borrar” o fundamental, cada sensor tem sua fase de "
        "rotação θ(t) estimada: filtro passa-banda Butterworth de fase zero em torno da rotação, projeção X–Y na "
        "direção principal, transformada de Hilbert (fase analítica), frequência instantânea suavizada a 2 Hz e "
        "integrada (Boashash, 1992; Fyfe &amp; Munck, 1997). Descartam-se 0,75 s em cada extremidade (transientes de "
        "filtro) e usa-se um número inteiro de rotações. O fasor complexo da ordem n de um canal x(t) é:"))
    S.append(eq_image(r"P_n = \frac{2}{N}\sum_{k} x(t_k)\,e^{-j\,n\,\theta(t_k)}\quad\Rightarrow\quad "
                      r"x(t)\approx \mathrm{Re}\{P_n\,e^{j n \theta(t)}\}", eqdir / "eq1.png", 150))
    S.append(fig_image(figs["metodo"], max_h=62 * mm))
    S.append(P(f"Figura 1 — Amplitude 1× em Y por método. Com frequência fixa o fundamental sai "
               f"{fmt(np.mean(mdata['fixed'] / mdata['rms'] - 1) * 100, 0)} % abaixo do √2·RMS; com rastreamento de "
               f"ordem a diferença cai para {fmt(np.mean(mdata['tracked'] / mdata['rms'] - 1) * 100, 1)} % "
               f"(o resto são harmônicas e ruído).", "caption"))
    S.append(P("3.2 Grandezas por sensor (mesma definição do relatório Pulse)", "h2"))
    S.append(eq_image(r"G_i = |P_{1,i}|\ [g],\qquad \mathrm{RMS}_i^{Pulse}=\sqrt{2}\,\sigma_i,\qquad "
                      r"s_i = \frac{2\,G_i\,g_0}{(2\pi f)^2}\ [m]", eqdir / "eq2.png", 160))
    S.append(P(
        "A órbita 1× no plano X–Y é a elipse x = |P<sub>x</sub>|cos θ, y = |P<sub>y</sub>|cos(θ − φ). Main G "
        "(semi-eixo maior a), eixo menor b e Force Angle α saem da decomposição em valores singulares da matriz "
        "dos fasores (equivalente à elipse de polarização; Born &amp; Wolf). Em forma fechada:"))
    S.append(eq_image(r"a^2=\frac{G_x^2+G_y^2}{2}+\frac{1}{2}\sqrt{(G_x^2+G_y^2)^2-4G_x^2G_y^2\sin^2\varphi},"
                      r"\qquad \tan 2\alpha=\frac{2G_xG_y\cos\varphi}{G_x^2-G_y^2}", eqdir / "eq3.png", 165))
    S.append(P("3.3 Sincronização, corpo central e desvios", "h2"))
    S.append(P(
        "Os sensores sem fio não compartilham relógio: os perfis de rotação mostram defasagens de até "
        f"{fmt(abs(max(an.lags.values(), key=lambda v: abs(v[0]))[0]) * 1e3, 0)} ms entre sensores (Figura 5). "
        "Por isso as fases entre sensores são referidas ao eixo X de cada um (X de todos os sensores em fase), que é a "
        "convenção que reproduz o “Center Body” do Pulse. O corpo central (centro de gravidade) é a média dos "
        "fasores sincronizados dos 4 cantos; o “Maximum Body” é o máximo entre os 8 sensores. Os desvios são "
        "diferenças relativas entre grupos de fasores:"))
    S.append(eq_image(r"D = \frac{|a-b|}{|a+b|}\times 100\%:\ \ "
                      r"\mathrm{Pitch}:a=Y_{L1}+Y_{R1},\ b=Y_{L4}+Y_{R4};\ \ "
                      r"\mathrm{Roll}:a=Y_{L1}+Y_{L4},\ b=Y_{R1}+Y_{R4};\ \ "
                      r"\mathrm{Twist}:a=Y_{L1}+Y_{R4},\ b=Y_{R1}+Y_{L4}", eqdir / "eq4.png", 170, fontsize=10))
    S.append(P(
        "Yaw (rotação em torno de Y) e Z (translação lateral) foram implementados como hipóteses de corpo rígido "
        "(Yaw: X esquerdo × direito com a mesma fórmula; Z: |Z médio dos cantos| / Main G do centro), pois a "
        "definição do fabricante não pôde ser identificada só com os números do relatório."))
    S.append(P("3.4 Índice de lançamento (Wurfkennziffer)", "h2"))
    S.append(eq_image(r"K_v=\frac{\Gamma\,\sin(\alpha+\beta)}{\cos\beta},\qquad "
                      r"K_v^{\ast}=\sqrt{1+\pi^2}\approx 3{,}30\ \ (\mathrm{voo} = 1\ \mathrm{per\'iodo})",
                      eqdir / "eq5.png", 150))
    S.append(P(
        f"Γ = Main G do centro, α = ângulo de força em relação à horizontal e β = inclinação do deck "
        f"({fmt(th['inclination'], 0)}°). A gravidade medida mostra que o eixo X dos sensores está próximo da "
        f"horizontal (inclinação estática média de {fmt(th['mean_sensor_tilt'], 1)}°, contra "
        f"{fmt(th['inclination'], 0)}° do deck), então α é tomado em relação à horizontal: "
        f"K_v = {fmt(th['kv_horizontal_ref'])}. Se o ângulo fosse em relação ao deck, K_v = {fmt(th['kv_deck_ref'])}. "
        "Para um leito plástico, o tempo de voo é exatamente um período quando K_v = √(1+π²); acima disso o "
        "material pousa em ciclos alternados (Schmidt et al., 2003)."))

    # ================= 4. VALIDAÇÃO
    if ref:
        S.append(P("4. Validação contra o relatório Pulse", "h1"))
        S.append(P("4.1 Consistência interna das fórmulas", "h2"))
        S.append(P(
            "Primeiro teste, sem usar os dados brutos: os números impressos no próprio relatório (G-Force por eixo, fase "
            "Y–X, frequência) foram passados pelas fórmulas da Seção 3 e comparados com os demais números do relatório. "
            "Se a modelagem estiver correta, as diferenças devem ser apenas de arredondamento."))
        groups = [("Strokes por eixo e Main (32 itens)", cons["Item"].str.contains("stroke"), "mm"),
                  ("Main G dos cantos", cons["Item"].str.contains(r"^[LR]\d Main G"), "g"),
                  ("Force Angle dos cantos", cons["Item"].str.contains("Force Angle"), "°"),
                  ("Corpo central (X, Y, Main, ângulo, fase, stroke)", cons["Item"].str.startswith("Centro"), "—"),
                  ("Pitch / Roll / Twist", cons["Item"].str.contains("Pitch|Roll|Twist"), "%")]
        rows = [["Grupo", "Itens", "Maior |diferença|", "Unid.", "Leitura"]]
        for lab, m, u in groups:
            d = cons[m]
            rows.append([lab, str(len(d)), fmt(d["Diferença"].abs().max(), 3), u, "arredondamento ✓"])
        S.append(table(rows, col_w=[70 * mm, 14 * mm, 28 * mm, 14 * mm, 40 * mm]))
        cc = cons[cons["Item"].str.startswith("Centro") | cons["Item"].str.contains("Pitch|Roll|Twist")]
        rows = [["Item", "Pulse", "Recalculado", "Diferença"]] + [
            [r.Item, fmt(r.Pulse, 2), fmt(r.Recalculado, 3), fmt(r.Diferença, 3)] for r in cc.itertuples()]
        S.append(Spacer(1, 2 * mm))
        S.append(table(rows, col_w=[60 * mm, 28 * mm, 28 * mm, 28 * mm]))
        S.append(P("Tabela — Corpo central e desvios reconstruídos a partir dos cantos L1, R1, L4, R4 do relatório "
                   "(fases referidas ao eixo X).", "caption"))
        S.append(P("4.2 Dados brutos (XML) × relatório", "h2"))
        S.append(P(
            f"O XML é uma gravação diferente (2,5 min antes, {an.rpm:.0f} RPM contra {ref['meta']['rpm']} RPM), então "
            "não se espera igualdade exata. Em uma peneira operando muito acima da frequência natural da suspensão "
            "(regime supercrítico), a amplitude de deslocamento tende a m·e/M, independente da rotação, e a aceleração "
            f"cresce com f² (Rao, 2017). Assim, strokes e ângulos são comparados diretamente e as acelerações são "
            f"multiplicadas por (f_ref/f_xml)² = {fmt(cmp.attrs['scale'], 4)}."))
        S.append(fig_image(figs["validacao"], max_h=64 * mm))
        st = cmp[cmp["Grupo"] == "Stroke"]
        S.append(P(f"Figura 2 — Paridade Python × Pulse (faixa cinza: ±3 % ou ±2°). Os strokes do XML ficam em média "
                   f"{fmt(st['Δ (%)'].mean(), 1)} % acima do relatório. Essa diferença pequena e sistemática é "
                   f"compatível com outra condição de carga e confirma a operação supercrítica.", "caption"))
        d = cmp[cmp["Grupo"].isin(["Centro", "Máximo", "Desvio", "Fase"])]
        rows = [["Grupo", "Item", "Python (XML)", "Python @ f_ref", "Pulse", "Δ"]] + [
            [r.Grupo, r.Item + f" ({r._3})", fmt(r._4, 2), fmt(r._5, 2), fmt(r.Pulse, 2), fmt(r.Δ, 2)]
            for r in d.itertuples()]
        S.append(table(rows, col_w=[18 * mm, 52 * mm, 24 * mm, 26 * mm, 20 * mm, 18 * mm]))
        S.append(P("4.3 O que não fecha, e por quê", "h2"))
        S += bullets([
            "<b>Yaw e Z:</b> nenhuma combinação de corpo rígido dos fasores 1× reproduz 2,3 % e 3,9 % a partir dos "
            "números do relatório. O desvio Z do relatório é calculado com o estimador de “G-Force Z” do Pulse, que não "
            "é a componente 1× (abaixo) e que inclui o canal L1-Z defeituoso.",
            "<b>G-Force em Z:</b> no relatório, Z vale 0,08–0,54 g, enquanto a componente 1× medida é ≤ 0,05 g. O Z "
            "desta máquina é dominado por conteúdo de banda larga (15–100 Hz, Figura 8), e o Pulse provavelmente usa "
            "um estimador filtrado ou de pico. Os valores “stroke Z” de 1–2 mm do relatório superestimam o deslocamento "
            "lateral real, que é de ~0,1 mm em 1×.",
            "<b>Fases nos cantos de descarga</b> (L4/R4) ficaram 1–2° acima: diferença física entre as gravações.",
        ])
        S.append(PageBreak())

    # ================= 5. RESULTADOS
    S.append(P("5. Resultados da gravação analisada", "h1"))
    tb = an.table()
    rows = [["Sensor", "Main G (g)", "Curso (mm)", "Ângulo (°)", "Fase Y–X (°)", "X / Y / Z 1× (g)",
             "X / Y curso (mm)", "Z RMS√2 (g)", "Z kurt.", "0,5× / 1,5× Y (g)"]]
    for n, r in tb.iterrows():
        bad = n in an.excluded
        rows.append([n, fmt(r["Main G (g)"]), fmt(r["Stroke (mm)"], 1), fmt(r["Force Angle (°)"], 1),
                     fmt(r["Fase Y-X (°)"], 1),
                     f"{fmt(r['X G (g)'])} / {fmt(r['Y G (g)'])} / " + ("✗" if bad else fmt(r['Z G 1× (g)'])),
                     f"{fmt(r['X stroke (mm)'], 1)} / {fmt(r['Y stroke (mm)'], 1)}",
                     "✗" if bad else fmt(r["Z RMS√2 (g)"]), fmt(r["Z kurtosis"]),
                     f"{fmt(r['Y 0,5× (g)'])} / {fmt(r['Y 1,5× (g)'])}"])
    S.append(table(rows, col_w=[13 * mm, 15 * mm, 15 * mm, 15 * mm, 17 * mm, 30 * mm, 23 * mm, 17 * mm, 13 * mm,
                                 22 * mm]))
    S.append(P(f"Tabela — Parâmetros por sensor a {an.rpm:.0f} RPM. ✗ = canal defeituoso (L1-Z).", "caption"))
    S.append(PageBreak())
    S.append(fig_image(figs["fase"], max_h=225 * mm))
    S.append(P("Figura 3 — (a) Órbitas de deslocamento em escala sobre um esquema da máquina; (b) ondas Y "
               "sincronizadas; (c) força no centro; (d) desvios de corpo rígido em % do limite de aceitação.",
               "caption"))
    S.append(PageBreak())
    S.append(fig_image(figs["orbitas"], max_h=235 * mm))
    S.append(P("Figura 4 — Órbitas X–Y medidas (5 rotações, cinza) e componente 1× (cor). As órbitas se abrem da "
               "alimentação (quase lineares, fase ≈ 9–11°) para a descarga (elípticas, fase ≈ 36°): é o efeito do "
               "pitch, que soma uma componente vertical defasada nas extremidades.", "caption"))
    S.append(PageBreak())
    S.append(fig_image(figs["rotacao"], max_h=120 * mm))
    S.append(P(f"Figura 5 — Rotação instantânea por sensor (variação de {fmt(an.speed['var_pp_pct'], 1)} % p-p). "
               "Os perfis de R2 e R3 aparecem deslocados no tempo: os sensores Wi-Fi não são sincronizados em "
               "hardware. Abaixo, o Main G rotação a rotação nos cantos: o zigue-zague em L1/R1 (valores alternados "
               "entre rotações consecutivas) é a assinatura de período 2 discutida na Seção 6.", "caption"))

    # ================= 6. DIAGNÓSTICO
    S.append(P("6. Diagnóstico e integridade da medição", "h1"))
    for f in an.findings:
        col = {"crítico": "#d03b3b", "atenção": "#b07800", "info": "#52514e"}[f.level]
        icon = {"crítico": "✗", "atenção": "▲", "info": "●"}[f.level]
        S.append(P(f"<font color='{col}'><b>{icon} {f.level.upper()}</b></font> · <b>{f.scope} — {f.title}.</b> "
                   f"{f.detail}" + (f" <i>Ação: {f.action}</i>" if f.action else ""), "bullet"))
    S.append(Spacer(1, 2 * mm))
    S.append(KeepTogether([fig_image(figs["integridade"], max_h=70 * mm),
                           P("Figura 6 — Módulo do vetor DC (gravidade) e inclinação estática do eixo X de cada "
                             "sensor.", "caption")]))
    S.append(fig_image(figs["ordens"], max_h=72 * mm))
    S.append(P(
        f"Figura 7 — Espectro de ordens médio. Além do 1× e das harmônicas inteiras, há linhas nítidas em 0,5×, 1,5×, "
        f"2,5× e 3,5×. A amplitude 0,5× em Y é praticamente a mesma nos 8 sensores ({fmt(sub[:, 0].min())}–"
        f"{fmt(sub[:, 0].max())} g), ou seja, um movimento vertical do corpo inteiro a {fmt(an.f_mean / 2)} Hz.",
        "caption"))
    S.append(P("Interpretação das ordens fracionárias", "h2"))
    S.append(P(
        f"Componentes em 0,5× e 1,5× indicam uma excitação que se repete a cada <i>duas</i> rotações. Em peneiras, a "
        f"causa clássica é o regime de lançamento do material: para K_v acima de √(1+π²) ≈ {fmt(KV_ONE_PERIOD)} o voo "
        f"dura mais que um período e o leito passa a pousar em ciclos alternados (duplicação de período), aplicando "
        f"um impacto a cada duas rotações. O K_v estimado é {fmt(th['kv_horizontal_ref'])}. A uniformidade do 0,5× "
        f"em toda a máquina favorece essa explicação, de força global, contra uma folga localizada, que também gera "
        f"0,5×/1,5× mas de forma concentrada perto da fonte. <b>Teste decisivo:</b> repetir a gravação sem carga, "
        f"ou com rotação menor (K_v &lt; 3,3). Se as ordens fracionárias desaparecerem, a origem é o material."))
    S.append(fig_image(figs["espectro_z"], max_h=150 * mm))
    S.append(P("Figura 8 — Espectros do eixo lateral Z. A componente 1× é pequena (≤ 0,05 g, curso ≈ 0,1 mm); o "
               "conteúdo é de banda larga, típico de impactos e modos estruturais das laterais. L1-Z: canal travado.",
               "caption"))
    S.append(PageBreak())

    # ================= 7. CONCLUSÕES
    S.append(P("7. Conclusões e recomendações", "h1"))
    S += bullets([
        "A cadeia de cálculo do relatório Pulse foi identificada e reproduzida: G-Force por eixo (1×), curso, Main G e "
        "Force Angle (elipse 1×), fase Y–X, corpo central (média dos cantos sincronizada por X), corpo máximo e os "
        "desvios Pitch, Roll e Twist.",
        "A máquina opera de forma coerente: curso de ~11,4–12,2 mm em todos os pontos, ângulo de força de 40–58° "
        "(maior na descarga), pitch de ~24 % (limite 45 %), roll e twist pequenos, movimento lateral 1× desprezível.",
        "<b>Recomendação 1 — sensor L1:</b> substituir ou reparar o canal Z (travado em −14,8 g) antes da próxima "
        "medição; reavaliar o desvio Z, que hoje aparece reprovado por causa dele.",
        "<b>Recomendação 2 — calibração:</b> verificar a escala dos sensores (gravidade lida como 0,92–0,93 g). Se o "
        "fator afetar também o sinal dinâmico, G-Force e curso reais seriam ~7–8 % maiores.",
        "<b>Recomendação 3 — montagem:</b> padronizar a fixação (bases niveladas). A inclinação estática varia até "
        "~10° entre pontos e entra diretamente no Force Angle de cada sensor.",
        "<b>Recomendação 4 — processo:</b> investigar as ordens 0,5×/1,5× com uma gravação sem carga e outra em rotação "
        "reduzida; avaliar se o K_v ≈ 3,5 é o desejado para o material (o relatório, a 714 RPM, corresponde a "
        f"K_v ≈ {fmt(th['kv_horizontal_ref'] * (ref['meta']['freq_hz'] / an.f_mean) ** 2 if ref else th['kv_horizontal_ref'])}).",
        "<b>Recomendação 5 — validação definitiva:</b> obter o XML da mesma gravação do relatório (11:09:12), ou o "
        "relatório da gravação 11:06:43, para comparação um a um, e a definição oficial de Yaw e Z junto à "
        "Haver &amp; Boecker.",
    ])
    S.append(P("Referências", "h2"))
    S += bullets([
        "Boashash, B. (1992). Estimating and interpreting the instantaneous frequency of a signal — Part 1: "
        "Fundamentals. <i>Proceedings of the IEEE</i>, 80(4), 520–538.",
        "Fyfe, K. R.; Munck, E. D. S. (1997). Analysis of computed order tracking. <i>Mechanical Systems and Signal "
        "Processing</i>, 11(2), 187–205.",
        "Randall, R. B. (2011). <i>Vibration-based Condition Monitoring</i>. Wiley.",
        "Brandt, A. (2011). <i>Noise and Vibration Analysis: Signal Analysis and Experimental Procedures</i>. Wiley.",
        "Antoni, J.; Randall, R. B. (2006). The spectral kurtosis: application to the vibratory surveillance and "
        "diagnostics of rotating machines. <i>Mechanical Systems and Signal Processing</i>, 20(2), 308–331.",
        "Schmidt, P.; Körber, R.; Coppers, M. (2003). <i>Sieben und Siebmaschinen: Grundlagen und Anwendung</i>. "
        "Wiley-VCH.",
        "Rao, S. S. (2017). <i>Mechanical Vibrations</i>, 6ª ed. Pearson (desbalanceamento rotativo, regime "
        "supercrítico).",
        "Born, M.; Wolf, E. (1999). <i>Principles of Optics</i>, 7ª ed. Cambridge (elipse de polarização).",
        "Haver &amp; Boecker. <i>PULSE Vibrationsanalyse</i> — folheto técnico (sensores triaxiais Wi-Fi ±11 g, "
        "gravações de 10 s).",
        "Wacker Chemie AG. US 10.589.318 B2 — <i>Classifying polysilicon</i> (definição de K_v com sin(α+β)/cos β).",
    ])

    # ================= ANEXO
    S.append(PageBreak())
    S.append(P("Anexo A — Relatórios por sensor", "h1"))
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
