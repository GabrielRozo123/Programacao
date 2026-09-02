# -*- coding: utf-8 -*-
"""Desenha a coluna que este estudo projetou: tres cascos, 240 estagios,
alimentacao no 159, condensador no topo do primeiro casco e refervedor no fundo
do terceiro. Nao e ilustracao generica — e a anatomia deste projeto."""

TINTA, FRACO, COBRE, RETICULA = "#E4E9ED", "#8A96A1", "#D9814F", "#3A454F"
MONO = "'JetBrains Mono', monospace"


def _rot(x, y, t, cor=FRACO, tam=13, anc="middle", peso=400):
    return ('<text x="%.1f" y="%.1f" text-anchor="%s" fill="%s" font-family="%s" '
            'font-size="%d" font-weight="%d">%s</text>' % (x, y, anc, cor, MONO, tam, peso, t))


def _trocador(x, y, larg):
    """Casco de trocador com os tubos insinuados."""
    o = ['<rect x="%d" y="%d" width="%d" height="30" rx="4" fill="none" stroke="%s" '
         'stroke-width="2"/>' % (x, y, larg, COBRE)]
    for k in range(4):
        xk = x + 9 + k * 13
        o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5"/>'
                 % (xk, y + 6, xk, y + 24, COBRE))
    return o


def coluna():
    W, H = 350, 826
    larg, vao = 58, 52
    esq = [56, 56 + larg + vao, 56 + 2 * (larg + vao)]
    topo, base = 172, 640
    cx = [x + larg / 2 for x in esq]

    o = ['<svg viewBox="0 0 %d %d" role="img" aria-label="A coluna deste projeto: tres '
         'cascos em serie, condensador no topo do primeiro, refervedor no fundo do '
         'terceiro e alimentacao no estagio 159 de 240">' % (W, H),
         '<defs><marker id="pt" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
         'markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="%s"/></marker>'
         '<marker id="ptq" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
         'markerHeight="6" orient="auto"><path d="M0,1 L9,5 L0,9 z" fill="%s"/></marker>'
         '</defs>' % (FRACO, COBRE)]

    # ---------------------------------------------------------------- os cascos
    for i, x in enumerate(esq):
        o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="none" '
                 'stroke="%s" stroke-width="2"/>' % (x, topo, larg, base - topo, TINTA))
        y = topo + 26
        while y < base - 14:
            o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" '
                     'stroke-width="1"/>' % (x + 7, y, x + larg - 7, y, RETICULA))
            y += 27
        o.append(_rot(cx[i], base + 24, "casco %d" % (i + 1), FRACO, 13))

    # ------------------------------------------------- condensador e produto de topo
    o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="2"/>'
             % (cx[0], topo, cx[0], 122, TINTA))
    o += _trocador(esq[0] - 4, 92, larg + 8)
    o.append(_rot(cx[0] + 16, 84, "condensador", COBRE, 13))

    o.append('<path d="M%d,107 L24,107 L24,54" fill="none" stroke="%s" stroke-width="2" '
             'marker-end="url(#ptq)"/>' % (esq[0] - 4, COBRE))
    o.append(_rot(38, 40, "PROPENO", COBRE, 15, "start", 600))
    o.append(_rot(38, 60, "99,77 %", COBRE, 15, "start", 600))

    # refluxo de volta ao topo
    o.append('<path d="M%.1f,122 L%.1f,148 L%.1f,148 L%.1f,%d" fill="none" stroke="%s" '
             'stroke-width="1.6" marker-end="url(#pt)"/>'
             % (cx[0] - 13, cx[0] - 13, cx[0] + 17, cx[0] + 17, topo - 2, FRACO))
    o.append(_rot(cx[0] + 30, 143, "refluxo 18,7", FRACO, 12, "start"))

    # ---------------------------------------- alimentacao no fundo do segundo casco
    ya = base - 62
    o.append('<line x1="%.1f" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="2" '
             'marker-end="url(#pt)"/>' % (esq[1] - 36, ya, esq[1] - 2, ya, TINTA))
    o.append(_rot(esq[1] - 19, ya - 11, "159", TINTA, 13))

    # ------------------------------------------------- refervedor e produto de fundo
    o.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="2"/>'
             % (cx[2], base, cx[2], 712, TINTA))
    o += _trocador(esq[2] - 4, 712, larg + 8)
    o.append(_rot(esq[2] - 14, 731, "refervedor", COBRE, 13, "end"))

    o.append('<line x1="%.1f" y1="742" x2="%.1f" y2="780" stroke="%s" stroke-width="2" '
             'marker-end="url(#ptq)"/>' % (cx[2], cx[2], COBRE))
    o.append(_rot(W - 8, 806, "PROPANO  98,87 %", COBRE, 15, "end", 600))

    # ------------------------------------ ligacao entre cascos: liquido desce, vapor sobe
    for i in (0, 1):
        xa, xb = esq[i] + larg, esq[i + 1]
        meio = (xa + xb) / 2
        o.append('<path d="M%.1f,%d L%.1f,%d L%.1f,%d L%.1f,%d" fill="none" stroke="%s" '
                 'stroke-width="1.6" marker-end="url(#pt)"/>'
                 % (xa, base - 20, meio + 9, base - 20, meio + 9, topo + 18,
                    xb - 2, topo + 18, FRACO))
        o.append('<path d="M%.1f,%d L%.1f,%d L%.1f,%d L%.1f,%d" fill="none" stroke="%s" '
                 'stroke-width="1.6" stroke-dasharray="4 4" marker-end="url(#pt)"/>'
                 % (xb, topo + 46, meio - 9, topo + 46, meio - 9, base - 44,
                    xa + 2, base - 44, FRACO))

    o.append(_rot(W / 2 - 48, base + 54, "alimentação no estágio 159", FRACO, 12))
    o.append(_rot(W / 2 - 48, base + 72, "líquido desce · vapor sobe", FRACO, 12))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_svg_coluna.svg"),
         "w", encoding="utf-8").write(coluna())
    print("coluna desenhada")
