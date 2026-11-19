"""
insere_cinetica.py — acrescenta à apresentação (versão editada pelo grupo) os slides de
aprofundamento cinético e o estudo de caso CO2/NaOH, sem alterar os slides existentes.

Uso:  python insere_cinetica.py entrada.pptx saida.pptx cinetica_entradas/eq - cinetica_entradas/dados2.json
      (entrada = versão do grupo, 26 slides; saída = 35 slides. Equações em PNG e dados dos gráficos em cinetica_entradas/.)
"""
import copy
import json
import re
import sys
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ENT, SAI, EQ, AST, DADOS = map(Path, sys.argv[1:6])
D = json.loads(DADOS.read_text(encoding="utf-8"))
p = Presentation(ENT)
LAY = next(l for l in p.slide_layouts if l.name == "CONTEUDO")
COR = {k: RGBColor.from_string(v) for k, v in dict(
    navy="0B1F33", dk2="1B3A57", card="E8F4F7", aqua="1A9BAE", coral="E8833A", aqua3="8FD6E1",
    cinza="5B6B7B", verde="2E8B57", verm="C0392B", branco="FFFFFF", grade="D9E3E8", aqua2="5FB8C6").items()}
HEAD, BODY = "Cambria", "Calibri"

# número de página copiado de um slide existente (campo que se atualiza sozinho)
NUM = next(copy.deepcopy(sh._element) for sh in p.slides[10].shapes if "Slide Number" in sh.name)
TIT = next(copy.deepcopy(sh._element) for sh in p.slides[10].shapes if sh.name == "Text 0")
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def novo(titulo, notas):
    s = p.slides.add_slide(LAY)
    tree = s.shapes._spTree
    for ph in list(s.placeholders):          # título idx 100: copia o do slide 11 (mesma formatação)
        tree.remove(ph._element)
    for k, base in enumerate((TIT, NUM)):
        el = copy.deepcopy(base)
        ids = [int(x) for x in tree.xpath(".//p:cNvPr/@id")] or [1]
        el.find(f".//{NS_P}cNvPr").set("id", str(max(ids) + 1))
        if k == 0:
            ts = el.findall(f".//{NS_A}t")
            ts[0].text = titulo
            for t in ts[1:]:
                t.text = ""
        tree.insert(2, el) if k == 0 else tree.append(el)
    ns = s.notes_slide                      # o mestre de notas do arquivo não tem placeholders:
    if ns.notes_placeholder is None:        # copia o corpo de notas do slide 11
        corpo = next(sh for sh in p.slides[10].notes_slide.placeholders if sh.placeholder_format.idx == 1)
        ns.shapes._spTree.append(copy.deepcopy(corpo._element))
    ns.notes_text_frame.text = notas
    return s


def runs(par, texto, size, cor, bold=False, italic=False, font=BODY):
    """Escreve texto num parágrafo; trechos X_Y viram subscritos e X^Y sobrescritos."""
    texto = texto.replace("\\_", "\x00")              # "\_" = sublinhado literal
    partes = re.split(r"(_\{[^}]*\}|_[A-Za-z0-9]+|\^\{[^}]*\})", texto)
    for parte in partes:
        if not parte:
            continue
        parte = parte.replace("\x00", "_")
        base = 0
        if parte.startswith("_"):
            parte, base = parte[1:].strip("{}"), -25000
        elif parte.startswith("^"):
            parte, base = parte[1:].strip("{}"), 30000
        r = par.add_run()
        r.text = parte
        f = r.font
        f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, font
        f.color.rgb = cor
        if base:
            r._r.get_or_add_rPr().set("baseline", str(base))


def caixa(s, x, y, w, h, linhas, size=16, cor=None, bold=False, italic=False, font=BODY, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, espaco=6, nome=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(linhas, str):
        linhas = [linhas]
    for i, ln in enumerate(linhas):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        par.space_after = Pt(espaco)
        segs = ln if isinstance(ln, list) else [(ln, {})]
        for txt, o in segs:
            runs(par, txt, o.get("size", size), o.get("cor", cor or COR["navy"]), o.get("bold", bold),
                 o.get("italic", italic), o.get("font", font))
    if nome:
        tb.name = nome
    return tb


def cartao(s, x, y, w, h, cor=None, nome="cartao"):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = 0.06
    sh.fill.solid()
    sh.fill.fore_color.rgb = cor or COR["card"]
    sh.line.fill.background()
    sh.shadow.inherit = False
    sh.name = nome
    return sh


def eq(s, nome, x, y, hmax, wmax=None, centro=False):
    arq = EQ / f"{nome}.png"
    w0, h0 = Image.open(arq).size
    h = hmax
    w = h * w0 / h0
    if wmax and w > wmax:
        w, h = wmax, wmax * h0 / w0
    if centro:
        x, y = x + ((wmax or w) - w) / 2, y + (hmax - h) / 2
    pic = s.shapes.add_picture(str(arq), Inches(x), Inches(y), Inches(w), Inches(h))
    pic.name = "eq_" + nome
    return w, h


def grafico(s, tipo, x, y, w, h, cats, series, cores, titulo=None, xt=None, yt=None, ymin=None, ymax=None,
            legenda=True, fmt=None, tracos=None, skip=None, nome="grafico"):
    if skip:                                   # rótulo do eixo x só a cada `skip` pontos
        cats = [c if k % skip == 0 else "\u200b" * (k + 1) for k, c in enumerate(cats)]
    cd = CategoryChartData()
    cd.categories = cats
    for n, v in series:
        cd.add_series(n, v)
    gf = s.shapes.add_chart(tipo, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = nome
    ch = gf.chart
    ch.font.size, ch.font.name = Pt(11), BODY
    ch.font.color.rgb = COR["cinza"]
    if titulo:
        ch.has_title = True
        tf = ch.chart_title.text_frame
        tf.text = titulo
        f = tf.paragraphs[0].runs[0].font
        f.size, f.bold, f.name = Pt(13), True, BODY
        f.color.rgb = COR["navy"]
    else:
        ch.has_title = False
    ch.has_legend = legenda
    if legenda:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(11)
    va, ca = ch.value_axis, ch.category_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = COR["grade"]
    va.format.line.fill.background()
    if ymin is not None:
        va.minimum_scale = ymin
    if ymax is not None:
        va.maximum_scale = ymax
    if fmt:
        va.tick_labels.number_format, va.tick_labels.number_format_is_linked = fmt, False
    for ax, t in ((ca, xt), (va, yt)):
        if t:
            ax.has_title = True
            ax.axis_title.text_frame.text = t
            f = ax.axis_title.text_frame.paragraphs[0].runs[0].font
            f.size, f.bold, f.name = Pt(12), False, BODY
            f.color.rgb = COR["cinza"]
    for i, (ser, cor) in enumerate(zip(ch.plots[0].series, cores)):
        if tipo in (XL_CHART_TYPE.LINE, XL_CHART_TYPE.LINE_MARKERS):
            ser.format.line.color.rgb = cor
            ser.format.line.width = Pt(2.5)
            ser.smooth = False
            if tracos and tracos[i]:
                ser.format.line.dash_style = tracos[i]
            if tipo == XL_CHART_TYPE.LINE_MARKERS:
                ser.marker.style = XL_MARKER_STYLE.CIRCLE
                ser.marker.size = 6
                ser.marker.format.fill.solid()
                ser.marker.format.fill.fore_color.rgb = cor
                ser.marker.format.line.color.rgb = cor
        else:
            ser.format.fill.solid()
            ser.format.fill.fore_color.rgb = cor
    return ch


virg = lambda v: str(v).replace(".", ",")

# =====================================================================================
# T1 — o que é cada termo
s = novo("Desvendando a equação: o que é cada termo",
         "Cada termo da equação tem um significado físico e uma origem diferente. Três vêm da hidrodinâmica "
         "(a, εL e, em parte, kL), um da termodinâmica (C*), um da cinética de laboratório (k1) e um do acoplamento "
         "entre difusão e reação (E). É por isso que a coluna de bolhas é um problema de cinética E de escoamento.")
w, h = eq(s, "eq_K", 0, 1.35, 0.8)  # do conjunto anterior
sh = s.shapes[-1]
sh.left = Inches((13.333 - w) / 2)
linhas = [("−r_A", "taxa de consumo de A por volume de reator (mol/m³·s)", "é o que se quer calcular"),
          ("C*", "concentração de A na interface, em equilíbrio com o gás: C* = p_A/H (Henry)", "termodinâmica"),
          ("k_L", "coeficiente de transferência de massa do filme líquido (m/s)", "teoria da penetração (Higbie) ou correlações"),
          ("a", "área de bolhas por volume de reator: a = 6ε_G/d_{32} (m²/m³)", "hidrodinâmica: correlação ou CFD"),
          ("E", "fator de aumento: quantas vezes a reação no filme acelera a absorção (E ≥ 1)", "número de Hatta e E_i (próximo slide)"),
          ("k_1 = k_2·C_B", "constante de pseudo-1ª ordem, com o reagente líquido B em excesso (1/s)", "cinética de laboratório"),
          ("ε_L = 1 − ε_G", "fração do volume do reator ocupada por líquido", "hidrodinâmica")]
tab = s.shapes.add_table(len(linhas) + 1, 3, Inches(0.6), Inches(2.35), Inches(12.1), Inches(4.4)).table
tab.columns[0].width, tab.columns[1].width, tab.columns[2].width = Inches(2.0), Inches(6.6), Inches(3.5)
for j, t in enumerate(["Termo", "O que é", "De onde vem"]):
    c = tab.cell(0, j)
    c.fill.solid(); c.fill.fore_color.rgb = COR["dk2"]
    c.text_frame.paragraphs[0].text = ""
    runs(c.text_frame.paragraphs[0], t, 15, COR["branco"], bold=True)
for i, (a, b, c_) in enumerate(linhas, start=1):
    for j, (t, kw) in enumerate([(a, dict(bold=True, italic=True, cor=COR["aqua"], size=16)),
                                 (b, dict(cor=COR["navy"], size=15)), (c_, dict(cor=COR["dk2"], size=14))]):
        cel = tab.cell(i, j)
        cel.fill.solid(); cel.fill.fore_color.rgb = COR["card"] if i % 2 else COR["branco"]
        cel.vertical_anchor = MSO_ANCHOR.MIDDLE
        cel.text_frame.paragraphs[0].text = ""
        runs(cel.text_frame.paragraphs[0], t, kw["size"], kw["cor"], bold=kw.get("bold", False), italic=kw.get("italic", False))
T1 = s

# =====================================================================================
# T2 — fator de aumento E
s = novo("O fator de aumento E: o que a reação faz dentro do filme",
         "Sem reação, o perfil de A no filme líquido é uma reta e o fluxo vale kL·C*. Com reação, A é consumido "
         "antes de atravessar o filme: o perfil se curva e fica mais inclinado junto à interface. Como o fluxo é "
         "proporcional a essa inclinação, a absorção é acelerada E vezes. Para Ha = 3, E = 3; para Ha = 10, E = 10. "
         "O limite é o regime instantâneo: quando falta B no filme, E não passa de Ei.")
cats = [virg(x) for x in D["xi"]]
ser = [(f"Ha = {virg(k)}  (E = {virg(D['Es'][k])})", v) for k, v in D["perf"].items()]
grafico(s, XL_CHART_TYPE.LINE, 0.6, 1.5, 6.9, 5.2, cats, ser, [COR["cinza"], COR["aqua3"], COR["aqua"], COR["coral"]],
        titulo="Perfil de A no filme líquido (B em excesso)", xt="posição no filme, x/δ (0 = interface)",
        yt="CA / C*", ymin=0, ymax=1, fmt="0.0", nome="graf_perfil")
cartao(s, 7.85, 1.5, 4.85, 5.2, nome="card_E")
eq(s, "E_def", 8.15, 1.7, 0.75)
caixa(s, 8.15, 2.55, 4.3, 0.9, "Razão entre o fluxo com reação e o fluxo puramente físico.", size=15, cor=COR["dk2"])
eq(s, "E_pfo", 8.15, 3.35, 0.75)
caixa(s, 8.15, 4.15, 4.3, 0.7, "pseudo-1ª ordem (B em excesso): cresce com Ha.", size=15, cor=COR["dk2"])
eq(s, "Ei", 8.15, 4.85, 0.75)
caixa(s, 8.15, 5.65, 4.3, 0.95, "teto do regime instantâneo: limitado pela difusão de B até o plano de reação.", size=15, cor=COR["dk2"])
T2 = s

# =====================================================================================
# R1 — taxa de consumo em cada regime
s = novo("Taxa de consumo −rA em cada regime",
         "Três regimes, três parâmetros hidrodinâmicos 'donos' da taxa. No regime lento, a taxa cresce com kLa "
         "até saturar no limite cinético k1·εL·C*: a partir daí, melhorar a hidrodinâmica não adianta. No regime "
         "rápido, a taxa é proporcional à área interfacial a e independe de kL. No instantâneo, é proporcional a kLa "
         "e à concentração do reagente líquido. Curvas por unidade de C*, ar–água, εL = 0,91.")
blocos = [("Lento", COR["verde"], "r_lento", "−r_A / C* × k_{L}a", D["kla"], D["lento"], "k1 = {}", "k_{L}a (1/s)"),
          ("Rápido", COR["coral"], "r_rap", "−r_A / C* × a", D["a"], D["rap"], "k1 = {}", "a (m²/m³)"),
          ("Instantâneo", COR["verm"], "r_ins", "−r_A / C* × k_{L}a", D["kla"], D["ins"], "C_B/C* = {}", "k_{L}a (1/s)")]
for i, (nome, cor, eqn, tit, xs, series, leg, xt) in enumerate(blocos):
    x = 0.6 + i * 4.1
    caixa(s, x, 1.42, 3.85, 0.45, nome, size=22, cor=cor, bold=True, font=HEAD)
    eq(s, eqn, x, 1.9, 0.62, wmax=3.85, centro=True)
    grafico(s, XL_CHART_TYPE.LINE, x - 0.1, 2.6, 4.0, 3.95, [virg(v) for v in xs],
            [(leg.format(virg(k)).replace("_", ""), v) for k, v in series.items()],
            [COR["aqua3"], COR["aqua"], COR["dk2"]], xt=re.sub(r"[_{}]", "", xt), yt="−rA / C* (1/s)" if i == 0 else None,
            ymin=0, fmt="0.00", skip=2 if i != 1 else None, nome=f"graf_{nome}")
caixa(s, 0.6, 6.62, 12.1, 0.3, "Lento (k1 em 1/s): satura no limite cinético k_1·ε_L·C*.  Rápido: só a área a importa.  Instantâneo: k_{L}a e a concentração de B.",
      size=13, cor=COR["dk2"], italic=True)
R1 = s

# =====================================================================================
# R2 — equações de projeto por regime
s = novo("Equações de projeto em cada regime",
         "Juntando a taxa de cada regime com o modelo de escoamento, saem as equações de projeto. A altura do reator "
         "vem do balanço do gás em escoamento pistonado. O tempo de batelada vem do balanço do reagente líquido B. "
         "Note como o parâmetro hidrodinâmico muda de linha para linha: εL, kLa, a e kLa novamente. As expressões de "
         "tempo saem integrando dC_B/dt = −b·(−rA)/εL com C* constante.")
cols = [("Regime", 0.6, 2.75), ("Taxa −r_A", 3.45, 2.6), ("Altura do reator (gás pistonado)", 6.15, 3.2), ("Tempo de batelada para consumir B", 9.45, 3.25)]
for t, x, w in cols:
    hdr = cartao(s, x, 1.45, w, 0.5, cor=COR["dk2"], nome="hdr")
    caixa(s, x, 1.45, w, 0.5, t, size=14, cor=COR["branco"], bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
regs = [("Lento, controle cinético", "k_1ε_L ≪ k_{L}a", COR["verde"], "cin"),
        ("Lento, controle por TM", "k_1ε_L ≫ k_{L}a; Ha < 0,3", COR["verde"], "tm"),
        ("Rápido", "3 < Ha ≪ E_i", COR["coral"], "rap"),
        ("Instantâneo", "Ha ≫ E_i", COR["verm"], "ins")]
for i, (nome, crit, cor, k) in enumerate(regs):
    y = 2.05 + i * 1.12
    cartao(s, 0.6, y, 12.1, 1.02, cor=COR["card"] if i % 2 == 0 else COR["branco"], nome="linha")
    caixa(s, 0.75, y + 0.12, 2.6, 0.45, nome, size=16, cor=cor, bold=True, font=HEAD)
    caixa(s, 0.75, y + 0.55, 2.6, 0.4, crit, size=13, cor=COR["cinza"])
    eq(s, f"r_{k}", 3.45, y + 0.15, 0.55, wmax=2.6, centro=True)
    eq(s, f"H_{k}", 6.15, y + 0.08, 0.86, wmax=3.2, centro=True)
    eq(s, f"t_{k}", 9.45, y + 0.08, 0.86, wmax=3.25, centro=True)
caixa(s, 0.6, 6.55, 12.1, 0.4, "Altura: A diluído no gás, B em excesso. Tempo: C* constante (gás puro ou em excesso), líquido bem misturado; β = b·D_A·C*/D_B.",
      size=12, cor=COR["dk2"], italic=True)
R2 = s

# =====================================================================================
# CS1 — o caso
s = novo("Estudo de caso: CO₂ em NaOH numa coluna de bolhas",
         "O sistema CO2/NaOH é o caso-referência da literatura recente para colunas de bolhas reativas: o experimento "
         "de Darmana et al. (2007) é usado para validar modelos de fator de aumento (Krauß & Rzehak, 2017), simulações "
         "Euler–Euler reativas (Krauß & Rzehak, 2018; Liu et al., 2021) e modelos de projeto (Michelson et al., 2023). "
         "Aplicamos a mesma química à nossa coluna, com a hidrodinâmica da correlação e do CFD validado.")
cartao(s, 0.6, 1.5, 5.95, 3.75, nome="card_quim")
caixa(s, 0.9, 1.7, 5.4, 0.5, "A química", size=22, cor=COR["aqua"], bold=True, font=HEAD)
caixa(s, 0.9, 2.3, 5.4, 2.9, [
    [("CO_2 + OH^{−} → HCO_3^{−}", dict(bold=True)), ("   rápida, k_2 ≈ 8×10³ L/(mol·s)", dict(cor=COR["cinza"], size=14))],
    [("HCO_3^{−} + OH^{−} ⇌ CO_3^{2−} + H_{2}O", dict(bold=True)), ("   instantânea", dict(cor=COR["cinza"], size=14))],
    [("CO_2 + H_{2}O ⇌ HCO_3^{−} + H^{+}", dict(bold=True)), ("   lenta, ≈ 0,03 1/s", dict(cor=COR["cinza"], size=14))],
    "O pH cai em degraus à medida que o OH⁻ é consumido: é a grandeza medida nos experimentos de referência."],
    size=16, espaco=10)
cartao(s, 6.75, 1.5, 5.95, 3.75, nome="card_lit")
caixa(s, 7.05, 1.7, 5.4, 0.5, "Por que este caso?", size=22, cor=COR["aqua"], bold=True, font=HEAD)
caixa(s, 7.05, 2.3, 5.4, 2.9, [
    [("Benchmark experimental: ", dict(bold=True)), ("Darmana et al. (2007), CO₂ puro em NaOH a pH 12,5.", {})],
    [("Fator de aumento: ", dict(bold=True)), ("Krauß & Rzehak (2017).", {})],
    [("CFD reativo: ", dict(bold=True)), ("Krauß & Rzehak (2018); Liu et al. (2021).", {})],
    [("Modelo de projeto: ", dict(bold=True)), ("Michelson et al. (2023).", {})]], size=16, espaco=10)
cartao(s, 0.6, 5.45, 12.1, 1.25, cor=COR["navy"], nome="card_caso")
caixa(s, 0.9, 5.55, 11.5, 1.05, [
    [("Nosso caso: ", dict(bold=True, cor=COR["aqua3"])),
     ("CO₂ puro (1 atm) em NaOH 0,0316 mol/L (pH 12,5) · coluna D = 0,15 m, H_0 = 0,9 m · U_G = 2 cm/s · "
      "hidrodinâmica da correlação clássica × do CFD validado.", dict(cor=COR["branco"]))]],
    size=17, anchor=MSO_ANCHOR.MIDDLE)
CS1 = s

# =====================================================================================
# CS2 — o modelo programado
s = novo("O modelo que programamos",
         "Quatro blocos acoplados, resolvidos no tempo com um integrador implícito (as reações são rápidas e o "
         "sistema é rígido). A hidrodinâmica entra só pelo primeiro bloco: trocar correlação por CFD muda a e kL, "
         "e o resto do modelo propaga o efeito até o pH e o tempo de batelada.")
blocos = [("1", "Hidrodinâmica", "ε_G e d_b → a = 6ε_G/d_b e k_L (Higbie)", "correlação clássica × CFD validado", COR["aqua"]),
          ("2", "Fator de aumento", "Ha = √(k_2[OH⁻]D)/k_L,  E_i,  E (van Krevelen–Hoftijzer)", "recalculado a cada instante", COR["aqua"]),
          ("3", "Gás pistonado", "as bolhas de CO₂ puro encolhem: F(H) = F_0 e^{−λH}", "eficiência de absorção = 1 − e^{−λH}", COR["aqua"]),
          ("4", "Líquido bem misturado", "balanços de CO₂ dissolvido e carbono iônico; pH pelo balanço de cargas", "retromistura intensa do líquido (Pe ≪ 1)", COR["coral"])]
for i, (n, t, d1, d2, cor) in enumerate(blocos):
    y = 1.5 + i * 1.3
    cartao(s, 0.6, y, 12.1, 1.15, nome="bloco" + n)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.85), Inches(y + 0.2), Inches(0.75), Inches(0.75))
    c.fill.solid(); c.fill.fore_color.rgb = cor; c.line.fill.background(); c.shadow.inherit = False
    caixa(s, 0.85, y + 0.2, 0.75, 0.75, n, size=22, cor=COR["branco"], bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    caixa(s, 1.9, y + 0.12, 3.2, 0.9, t, size=19, cor=COR["navy"], bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    caixa(s, 5.1, y + 0.12, 7.4, 0.9, [d1, [(d2, dict(cor=COR["cinza"], size=14, italic=True))]], size=16, anchor=MSO_ANCHOR.MIDDLE, espaco=2)
caixa(s, 0.6, 6.7, 12.1, 0.3, "Python (NumPy/SciPy, integrador BDF) · caso\\_co2\\_naoh.py · cinética: Pohorecki & Moniuk (1988)",
      size=12, cor=COR["cinza"], italic=True)
CS2 = s

# =====================================================================================
# CS3 — resultado pH
C = D["caso"]
cor_, cfd = C["Correlação (Akita & Yoshida)"], C["CFD validado"]
s = novo("Resultado: a hidrodinâmica muda o tempo de batelada",
         f"Mesma química, mesma vazão, só a hidrodinâmica muda. Com a área interfacial do CFD (a = {cfd['a']} m⁻¹ "
         f"contra {cor_['a']} m⁻¹ da correlação), o NaOH é convertido em bicarbonato mais cedo: pH 8,3 em "
         f"{virg(cfd['t83'])} s contra {virg(cor_['t83'])} s. Os dois patamares da curva são a química: primeiro OH⁻ vira carbonato, "
         "depois carbonato vira bicarbonato; a queda brusca marca o fim do carbonato: todo o carbono iônico já é bicarbonato.")
grafico(s, XL_CHART_TYPE.LINE, 0.6, 1.5, 7.6, 5.2, [str(int(t)) for t in cfd["t"]],
        [("Correlação clássica", cor_["pH"]), ("CFD validado", cfd["pH"])], [COR["cinza"], COR["aqua"]],
        titulo="pH do líquido × tempo (CO₂ puro em NaOH, U_G = 2 cm/s)".replace("_", ""), xt="tempo (s)", yt="pH",
        ymin=6, ymax=13, fmt="0", skip=4, nome="graf_ph")
red = round(100 * (1 - cfd["t83"] / cor_["t83"]))
caixa(s, 8.7, 1.6, 4.0, 1.1, f"−{red} %", size=60, cor=COR["aqua"], bold=True, font=HEAD)
caixa(s, 8.7, 2.75, 4.0, 0.7, f"no tempo até pH 8,3: {virg(cor_['t83'])} s → {virg(cfd['t83'])} s", size=17, cor=COR["dk2"])
cartao(s, 8.7, 3.65, 4.0, 1.05, nome="card_eta")
caixa(s, 8.95, 3.75, 3.6, 1.1, [[("Absorção inicial do CO₂", dict(bold=True))],
                                 f"{round(100*cor_['eta0'])} % (correlação) → {round(100*cfd['eta0'])} % (CFD)"], size=16, espaco=4)
caixa(s, 8.7, 5.15, 4.0, 1.5, "Patamares: OH⁻ → CO₃²⁻ (pH ≈ 12 → 10) e CO₃²⁻ → HCO₃⁻ (pH ≈ 10 → 8). Queda brusca: acabou o carbonato, resta só bicarbonato.",
      size=14, cor=COR["dk2"], italic=True)
CS3 = s

# =====================================================================================
# CS4 — regime ao longo do tempo
s = novo("O regime muda durante a batelada",
         f"Este é o resultado mais 'cinético' do estudo. No início, Ha ≈ {virg(cfd['Ha0'])} e Ei ≈ {virg(cfd['Ei0'])}: regime "
         f"intermediário, com E ≈ {virg(cfd['E0'])} limitado pelo pouco OH⁻ diante do CO₂ puro. Em ~{int(cfd['tHa03'])} s, Ha cai abaixo "
         "de 0,3 e E vai a 1: a reação passa para o seio do líquido e a taxa é kL·a·C*. Depois que o bicarbonato se forma, "
         "sobra absorção física. Ou seja, o parâmetro hidrodinâmico que importa muda com o tempo.")
grafico(s, XL_CHART_TYPE.LINE, 0.6, 1.5, 7.6, 5.2, [str(int(t)) for t in cfd["t"]],
        [("Número de Hatta, Ha", cfd["Ha"]), ("Fator de aumento, E", cfd["E"])], [COR["coral"], COR["aqua"]],
        titulo="Ha e E ao longo da batelada (hidrodinâmica do CFD)", xt="tempo (s)", yt="Ha, E", ymin=0, ymax=2.5,
        fmt="0.0", skip=4, nome="graf_regime")
fases = [(f"0–{int(cfd['tHa03'])} s · Intermediário", f"Ha ≈ 2 → 0,3; E ≈ 1,6 → 1, limitado por E_i ≈ 2,3. Importam a e E_i.", COR["coral"]),
         (f"{int(cfd['tHa03'])}–{int(cfd['t83'])} s · Lento, controle por TM", "E = 1; o OH⁻ ainda reage no seio. Taxa = k_L·a·C*: importa k_{L}a.", COR["verde"]),
         (f"> {int(cfd['t83'])} s · Absorção física", "bicarbonato formado, pH < 8; o CO₂ dissolvido se acumula.", COR["cinza"])]
for i, (t, d_, cor) in enumerate(fases):
    y = 1.5 + i * 1.72
    cartao(s, 8.55, y, 4.15, 1.55, nome="fase" + str(i))
    caixa(s, 8.8, y + 0.12, 3.75, 0.45, t, size=16, cor=cor, bold=True, font=HEAD)
    caixa(s, 8.8, y + 0.6, 3.75, 0.9, d_, size=14, cor=COR["dk2"])
CS4 = s

# =====================================================================================
# referências do estudo de caso
s = novo("Referências: cinética e estudo de caso", "Referências adicionais dos slides de cinética e do estudo de caso CO2/NaOH.")
refs = ["Darmana, D.; Henket, R. L. B.; Deen, N. G.; Kuipers, J. A. M. (2007). Chem. Eng. Sci., 62(9), 2556–2575.",
        "Higbie, R. (1935). Trans. AIChE, 31, 365–389.",
        "Krauß, M.; Rzehak, R. (2017). Reactive absorption of CO₂ in NaOH: detailed study of enhancement factor models. Chem. Eng. Sci., 166, 193–209.",
        "Krauß, M.; Rzehak, R. (2018). Reactive absorption of CO₂ in NaOH: an Euler–Euler simulation study. Chem. Eng. Sci., 181, 199–214.",
        "Liu, J.; Zhou, P.; Liu, L.; Chen, S.; Song, Y.; Yan, H. (2021). CFD modeling of reactive absorption of CO₂ in aqueous NaOH in a rectangular bubble column. Chem. Eng. Sci., 230, 116218.",
        "Michelson, J. et al. (2023). Modeling of a bubble column for CO₂ removal by absorption with NaOH. Chem. Eng. Commun., 211(4), 571–581.",
        "van Krevelen, D. W.; Hoftijzer, P. J. (1948). Rec. Trav. Chim. Pays-Bas, 67, 563–586."]
caixa(s, 0.6, 1.6, 12.1, 5.1, refs, size=15, espaco=10)
REF2 = s

# =====================================================================================
# roteiro (slide 3): tempos
for sh in p.slides[2].shapes:
    if sh.has_text_frame:
        for par in sh.text_frame.paragraphs:
            for r in par.runs:
                r.text = (r.text.replace("0–12 min", "0–10 min").replace("12–30 min", "10–30 min")
                          .replace("30–50 min", "30–52 min").replace("50–60 min", "52–60 min")
                          .replace("O que simulamos, o que comparamos e o que aprendemos",
                                   "Simulação, validação e estudo de caso CO₂/NaOH"))

# =====================================================================================
# reordenação: 1..11, T1, T2, 12, R1, R2, 13..22, CS1..CS4, 23..26 (refs), REF2 antes do "Obrigado"
lst = p.slides._sldIdLst
ids = list(lst)
orig, novos = ids[:26], ids[26:]
T1i, T2i, R1i, R2i, C1, C2, C3, C4, RF = novos
ordem = orig[:11] + [T1i, T2i] + [orig[11]] + [R1i, R2i] + orig[12:22] + [C1, C2, C3, C4] + orig[22:25] + [RF] + [orig[25]]
for el in ids:
    lst.remove(el)
for el in ordem:
    lst.append(el)
# referência cruzada que mudou de número ("Da cinética à conversão": 14 → 18)
for sl in p.slides:
    for sh in sl.shapes:
        if sh.has_text_frame:
            for par in sh.text_frame.paragraphs:
                for r in par.runs:
                    if "slide 14" in r.text:
                        r.text = r.text.replace("slide 14", "slide 18")
p.save(SAI)

# tipo de mídia: o arquivo original declarava "image/jpg" (não padrão); padroniza para image/jpeg
import shutil, tempfile, zipfile
tmp = Path(tempfile.mkstemp(suffix=".pptx")[1])
with zipfile.ZipFile(SAI) as zi, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        dado = zi.read(it.filename)
        if it.filename == "[Content_Types].xml":
            x = re.sub(r'<Override PartName="/ppt/media/[^"]+\.jpg" ContentType="image/jpg"/>', "", dado.decode("utf-8"))
            if 'Extension="jpg"' not in x:
                x = x.replace("<Default ", '<Default Extension="jpg" ContentType="image/jpeg"/><Default ', 1)
            dado = x.encode("utf-8")
        zo.writestr(it, dado)
shutil.move(tmp, SAI)
print("ok", len(p.slides))
