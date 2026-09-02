"""Gera os SVGs das laminas de grafico. Coordenadas calculadas, nao posicionadas a mao."""
import json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "casos-python", "02-splitter-c3"))
import simulate as tw

AZUL, COBRE = "#5798CE", "#D37642"     # validados: banda de luminosidade, croma, CVD, contraste
TINTA, FRACO, RETICULA = "#E4E9ED", "#8A96A1", "#2B343D"
W = 912                                 # 1080 - 2 x 84 de margem

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def texto(x, y, s, cor=FRACO, tam=19, fam="mono", anc="middle", peso=400, extra=""):
    f = {"mono": "'JetBrains Mono', monospace",
         "disp": "'Archivo', system-ui, sans-serif"}[fam]
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" fill="{cor}" '
            f'font-family="{f}" font-size="{tam}" font-weight="{peso}"{extra}>{esc(s)}</text>')


# ============================================ 1) a parede: pureza e lucro x refluxo
def curva():
    pts = []
    R = 11.0
    while R <= 24.0001:
        r = tw.simulate({"N_estagios": 240, "pos_alimentacao": 0.664, "razao_refluxo": R,
                         "corte_pct": 99.90, "pressao": 19.0, "z_propeno": 0.75,
                         "F_alimentacao": 1000})
        if r["convergiu"] == 1.0:
            pts.append((R, r["pureza_topo"], r["lucro"]))
        R += 0.125
    return pts


def parede():
    pts = curva()
    R_CORTE = 16.8723
    x0, x1 = 78, W - 8
    RMIN, RMAX = 11.0, 24.0
    fx = lambda R: x0 + (R - RMIN) / (RMAX - RMIN) * (x1 - x0)

    # painel de cima: pureza
    ay0, ay1 = 26, 210
    PMIN, PMAX = 95.4, 100.05
    fy1 = lambda p: ay1 - (p - PMIN) / (PMAX - PMIN) * (ay1 - ay0)
    # painel de baixo: lucro
    by0, by1 = 274, 456
    LMIN, LMAX = 0.0, 70.0
    fy2 = lambda v: by1 - (v - LMIN) / (LMAX - LMIN) * (by1 - by0)

    o = [f'<svg viewBox="0 0 {W} 532" role="img" aria-label="Pureza de topo e lucro anual '
         f'em funcao da razao de refluxo, com o degrau de grau polimero em 99,5 por cento">']

    # ---- painel 1
    o.append(texto(x0, ay0 - 8, "PUREZA DE TOPO  (%)", FRACO, 17, "disp", "start", 700,
                   ' letter-spacing="0.11em"'))
    for p in (96, 97, 98, 99, 100):
        y = fy1(p)
        o.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{RETICULA}" stroke-width="1"/>')
        o.append(texto(x0 - 12, y + 6, str(p), FRACO, 18, "mono", "end"))
    # a linha do grau polimero
    yg = fy1(99.5)
    o.append(f'<line x1="{x0}" y1="{yg:.1f}" x2="{x1}" y2="{yg:.1f}" stroke="{COBRE}" '
             f'stroke-width="2" stroke-dasharray="7 5"/>')
    o.append(texto(x0 + 10, yg - 11, "grau polímero · 99,5", COBRE, 18, "mono", "start"))
    d = " ".join(("M" if i == 0 else "L") + f"{fx(R):.1f},{fy1(p):.1f}"
                 for i, (R, p, _) in enumerate(pts))
    o.append(f'<path d="{d}" fill="none" stroke="{AZUL}" stroke-width="3" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')

    # ---- guia vertical unindo os dois paineis
    xc = fx(R_CORTE)
    o.append(f'<line x1="{xc:.1f}" y1="{ay0}" x2="{xc:.1f}" y2="{by1}" stroke="{COBRE}" '
             f'stroke-width="1.5" stroke-dasharray="4 6" opacity="0.8"/>')

    # ---- painel 2
    o.append(texto(x0, by0 - 8, "LUCRO ANUAL  (MUSD)", FRACO, 17, "disp", "start", 700,
                   ' letter-spacing="0.11em"'))
    for v in (0, 20, 40, 60):
        y = fy2(v)
        o.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{RETICULA}" stroke-width="1"/>')
        o.append(texto(x0 - 12, y + 6, str(v), FRACO, 18, "mono", "end"))
    baixo = [(R, l) for R, p, l in pts if p < 99.5]
    alto = [(R, l) for R, p, l in pts if p >= 99.5]
    for seg, cor in ((baixo, FRACO), (alto, COBRE)):
        d = " ".join(("M" if i == 0 else "L") + f"{fx(R):.1f},{fy2(l):.1f}"
                     for i, (R, l) in enumerate(seg))
        o.append(f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="3" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
    # o salto
    o.append(f'<line x1="{fx(baixo[-1][0]):.1f}" y1="{fy2(baixo[-1][1]):.1f}" '
             f'x2="{fx(alto[0][0]):.1f}" y2="{fy2(alto[0][1]):.1f}" stroke="{COBRE}" '
             f'stroke-width="3" stroke-dasharray="5 4"/>')
    for R, l in (baixo[-1], alto[0]):
        o.append(f'<circle cx="{fx(R):.1f}" cy="{fy2(l):.1f}" r="6" fill="{COBRE}" '
                 f'stroke="#10151A" stroke-width="2"/>')
    o.append(texto(xc + 16, fy2(38), "+50,5 MUSD/ano", COBRE, 22, "mono", "start", 600))
    o.append(texto(xc + 16, fy2(38) + 26, "ao cruzar 99,5 %", FRACO, 18, "mono", "start"))

    # ---- eixo x
    for R in (12, 14, 16, 18, 20, 22, 24):
        o.append(texto(fx(R), by1 + 30, str(R), FRACO, 18, "mono"))
    o.append(texto((x0 + x1) / 2, by1 + 60, "RAZÃO DE REFLUXO", FRACO, 17, "disp", "middle", 700,
                   ' letter-spacing="0.11em"'))
    o.append("</svg>")
    return "\n".join(o)


# ==================================== 2) paridade: previsto pelo surrogate x real
def paridade():
    pts = json.load(open(os.path.join(AQUI, "..", "dados", "pareto-paridade.json")))
    x0, x1, y0, y1 = 82, W - 10, 16, 366
    XMIN, XMAX = 99.60, 100.30
    YMIN, YMAX = 99.42, 100.00
    fx = lambda v: x0 + (v - XMIN) / (XMAX - XMIN) * (x1 - x0)
    fy = lambda v: y1 - (v - YMIN) / (YMAX - YMIN) * (y1 - y0)

    o = [f'<svg viewBox="0 0 {W} 436" role="img" aria-label="Pureza prevista pelo surrogate '
         f'contra pureza real, nas cem solucoes da frente de Pareto">']
    for v in (99.5, 99.6, 99.7, 99.8, 99.9, 100.0):
        y = fy(v)
        if y0 <= y <= y1:
            o.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{RETICULA}" stroke-width="1"/>')
            o.append(texto(x0 - 12, y + 6, ("%.1f" % v).replace(".", ","), FRACO, 18, "mono", "end"))

    # a parede fisica: fracao molar nao passa de 100 %
    xw = fx(100.0)
    o.append(f'<rect x="{xw:.1f}" y="{y0}" width="{x1-xw:.1f}" height="{y1-y0}" fill="{COBRE}" opacity="0.07"/>')
    o.append(f'<line x1="{xw:.1f}" y1="{y0}" x2="{xw:.1f}" y2="{y1}" stroke="{COBRE}" stroke-width="2"/>')
    o.append(texto(xw + 10, y0 + 20, "impossível: previsão > 100 %", COBRE, 18, "mono", "start"))

    # a especificacao real
    ys = fy(99.7)
    o.append(f'<line x1="{x0}" y1="{ys:.1f}" x2="{x1}" y2="{ys:.1f}" stroke="{TINTA}" '
             f'stroke-width="2" stroke-dasharray="7 5"/>')
    o.append(texto(xw - 12, ys - 11, "especificação · 99,7", TINTA, 18, "mono", "end"))

    # identidade: onde os pontos cairiam se o surrogate acertasse
    a, b = max(XMIN, YMIN), min(XMAX, YMAX)
    o.append(f'<line x1="{fx(a):.1f}" y1="{fy(a):.1f}" x2="{fx(b):.1f}" y2="{fy(b):.1f}" '
             f'stroke="{FRACO}" stroke-width="1.5" stroke-dasharray="3 5"/>')
    o.append(texto(fx(a) + 14, fy(a) - 10, "previsão = realidade", FRACO, 17, "mono", "start"))

    for prev, real, ok in pts:
        cx, cy = fx(prev), fy(real)
        cor = AZUL if ok else COBRE
        o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{cor}" fill-opacity="0.78" '
                 f'stroke="#10151A" stroke-width="2"/>')

    for v in (99.6, 99.8, 100.0, 100.2):
        o.append(texto(fx(v), y1 + 32, ("%.1f" % v).replace(".", ","), FRACO, 18, "mono"))
    o.append(texto((x0 + x1) / 2, y1 + 62, "PUREZA PREVISTA PELO SURROGATE  (%)", FRACO, 17,
                   "disp", "middle", 700, ' letter-spacing="0.11em"'))
    o.append(texto(20, (y0 + y1) / 2, "PUREZA REAL  (%)", FRACO, 17, "disp", "middle", 700,
                   f' letter-spacing="0.11em" transform="rotate(-90 20 {(y0+y1)/2:.0f})"'))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    open(os.path.join(AQUI, "_svg_parede.svg"), "w", encoding="utf-8").write(parede())
    open(os.path.join(AQUI, "_svg_paridade.svg"), "w", encoding="utf-8").write(paridade())
    print("svgs gerados")
