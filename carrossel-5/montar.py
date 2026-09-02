# -*- coding: utf-8 -*-
"""Monta as doze laminas do carrossel. Uma fonte so, para os rodapes e numeros
nao saírem de sincronia quando a ordem muda."""
import io, os

AQUI = os.path.dirname(os.path.abspath(__file__))
svg = lambda n: io.open(os.path.join(AQUI, "_svg_%s.svg" % n), encoding="utf-8").read()

CABECA = '''<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=JetBrains+Mono:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
  <style>
    body { margin: 0; }
    a { color: #63A8D2; } a:hover { color: #8FC4E2; }
    svg { display: block; width: 100%; height: auto; }
  </style>
</helmet>
<div style="width: 1080px; height: 1080px; background: #10151A; color: #E4E9ED; font-family: 'Source Serif 4', Georgia, serif; padding: 84px; display: flex; flex-direction: column; box-sizing: border-box">
'''

DISP = "'Archivo', system-ui, sans-serif"
MONO = "'JetBrains Mono', monospace"

def topo(sobre, n, total=5):
    return ('  <div style="display: flex; justify-content: space-between; align-items: baseline">\n'
            '    <div style="font-family: %s; font-size: 21px; font-weight: 700; letter-spacing: 0.18em; '
            'text-transform: uppercase; color: #D9814F">%s</div>\n'
            '    <div style="font-family: %s; font-size: 20px; color: #6D7B87">%02d / %d</div>\n'
            '  </div>\n' % (DISP, sobre, MONO, n, total))

def pe(cta="deslize &rarr;"):
    return ('  <div style="display: flex; justify-content: space-between; align-items: baseline; '
            'border-top: 1px solid #2B343D; padding-top: 24px">\n'
            '    <div style="font-family: %s; font-size: 19px; color: #6D7B87; letter-spacing: 0.04em">'
            'DWSIM 10.2.3 &middot; AI4Tech Suite</div>\n'
            '    <div style="font-family: %s; font-size: 19px; font-weight: 700; letter-spacing: 0.14em; '
            'text-transform: uppercase; color: #D9814F">%s</div>\n  </div>\n</div>\n</x-dc>\n</body>\n</html>\n'
            % (MONO, DISP, cta))

def h1(t, tam=64):
    return ('    <div style="font-family: %s; font-size: %dpx; font-weight: 800; line-height: 1.0; '
            'letter-spacing: -0.03em; text-wrap: balance">%s</div>\n' % (DISP, tam, t))

def p(t, tam=29):
    return ('    <div style="font-size: %dpx; line-height: 1.42; color: #95A2AD">%s</div>\n' % (tam, t))

def cita(t, tam=30):
    return ('    <div style="border-left: 3px solid #D9814F; padding: 6px 0 6px 28px; font-size: %dpx; '
            'line-height: 1.38">%s</div>\n' % (tam, t))

def forte(t):
    return '<strong style="color: #E4E9ED; font-weight: 600">%s</strong>' % t

def celas(itens, cols=None):
    """itens: (rotulo, valor, unidade|None, cor)"""
    cols = cols or len(itens)
    o = ['    <div style="display: grid; grid-template-columns: repeat(%d, minmax(0, 1fr)); gap: 1px; '
         'background: #2B343D; border: 1px solid #2B343D">\n' % cols]
    for rot, val, uni, cor in itens:
        o.append('      <div style="background: #171E25; padding: 28px 24px">\n'
                 '        <div style="font-family: %s; font-size: 17px; font-weight: 700; '
                 'letter-spacing: 0.13em; text-transform: uppercase; color: #6D7B87; margin-bottom: 13px">%s</div>\n'
                 '        <div style="font-family: %s; font-size: 46px; font-weight: 600; color: %s">%s</div>\n'
                 % (DISP, rot, MONO, cor, val))
        if uni:
            o.append('        <div style="font-size: 23px; color: #6D7B87; margin-top: 8px">%s</div>\n' % uni)
        o.append('      </div>\n')
    o.append('    </div>\n')
    return "".join(o)

def cartoes(itens):
    """itens: (titulo, texto)"""
    o = ['    <div style="display: grid; grid-template-columns: repeat(%d, minmax(0, 1fr)); gap: 1px; '
         'background: #2B343D; border: 1px solid #2B343D">\n' % len(itens)]
    for tit, txt in itens:
        o.append('      <div style="background: #171E25; padding: 28px 24px">\n'
                 '        <div style="font-family: %s; font-size: 17px; font-weight: 700; '
                 'letter-spacing: 0.13em; text-transform: uppercase; color: #D9814F; margin-bottom: 14px">%s</div>\n'
                 '        <div style="font-size: 26px; line-height: 1.32; color: #E4E9ED">%s</div>\n'
                 '      </div>\n' % (DISP, tit, txt))
    o.append('    </div>\n')
    return "".join(o)

def lamina(arq, sobre, n, miolo, gap=32, cta="deslize &rarr;"):
    corpo = ('  <div style="flex-grow: 1; display: flex; flex-direction: column; '
             'justify-content: center; gap: %dpx">\n%s  </div>\n' % (gap, miolo))
    io.open(os.path.join(AQUI, arq), "w", encoding="utf-8").write(
        CABECA + topo(sobre, n) + corpo + pe(cta))

AZ, CB, CINZA = "#5798CE", "#D9814F", "#6D7B87"

# ============================================================ 01 · capa · o problema
capa = (
 '  <div style="flex-grow: 1; display: flex; gap: 44px; align-items: center">\n'
 '    <div style="flex-grow: 1; display: flex; flex-direction: column; gap: 26px">\n'
 + h1("Um décimo de ponto percentual separa dois mercados.", 54)
 + p("Propeno e propano fervem quase à mesma temperatura. São "
     "<strong style=\"color:#E4E9ED;font-weight:600\">240 estágios teóricos</strong> "
     "e refluxo 18,7 para separá-los.", 27)
 + celas([("Acima de 99,5 %", "1.150", "US$/t &middot; grau polímero", CB),
          ("Abaixo", "950", "US$/t &middot; grau químico", CINZA)])
 + cita("Um décimo de ponto tira o produto de um mercado e joga no outro: "
        + forte("15 ou 63 milhões por ano") + ".", 27)
 + '    </div>\n'
 '    <div style="width: 306px; flex-shrink: 0">' + svg("coluna") + '</div>\n'
 '  </div>\n')
io.open(os.path.join(AQUI, "Main.dc.html"), "w", encoding="utf-8").write(
    CABECA + topo("O problema", 1) + capa + pe())

# ==================================================== 02 · como fizemos
lamina("L02.dc.html", "Como fizemos", 2, gap=28, miolo=(
    h1("Nenhuma das ferramentas resolve isso sozinha.", 58)
    + '    <div>' + svg("ciclo") + '</div>\n'
    + p("O DWSIM dá a termodinâmica de verdade e é lento demais para varrer o espaço de "
        "projeto. Calibramos contra ele um modelo rápido, deixamos o aprendizado de máquina "
        "dizer o que move o resultado e a otimização propor candidatos.", 27)
    + cita("Das cem soluções que a otimização propôs, " + forte("45 violavam a "
           "especificação") + " quando reavaliadas no simulador rigoroso. É por isso que a "
           "seta de retorno existe.", 28)))

# =============================================== 03 · grafico 1 · onde esta o dinheiro
lamina("L03.dc.html", "O que a simulação revelou", 3, gap=24, miolo=(
    h1("A pureza sobe suave. O dinheiro não.", 58)
    + '    <div>' + svg("parede") + '</div>\n'
    + p("A mesma coluna, varrendo a razão de refluxo. A pureza de topo cresce de forma "
        "contínua — mas ao cruzar 99,5 % o produto muda de grau e o lucro "
        + forte("salta de 14 para 65 milhões") + ". Projetar perto dessa linha sem medir é "
        "apostar a margem do ano.", 27)))

# ================================================ 04 · grafico 2 · onde agir
lamina("L04.dc.html", "Onde o resultado se decide", 4, gap=24, miolo=(
    h1("Seis variáveis. Duas decidem três quartos do resultado.", 56)
    + ('    <div style="display: flex; gap: 32px; align-items: center; font-size: 23px; '
       'color: #95A2AD">\n'
       '      <div style="display: flex; align-items: center; gap: 11px"><div style="width: 17px; '
       'height: 17px; border-radius: 3px; background: #5798CE"></div>você decide</div>\n'
       '      <div style="display: flex; align-items: center; gap: 11px"><div style="width: 17px; '
       'height: 17px; border-radius: 3px; background: #D37642"></div>você recebe</div>\n'
       '    </div>\n')
    + '    <div>' + svg("sobol") + '</div>\n'
    + p("Quanto cada variável explica da variação do lucro. Diz onde gastar atenção de "
        "engenharia e o que é ruído — e revela que " + forte("a maior influência isolada é a "
        "composição da alimentação") + ", que chega pela tubulação e ninguém escolhe.", 27)))

# ============================================================ 05 · conclusao
espec = ('    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; '
         'background: #2B343D; border: 1px solid #2B343D">\n')
for k, v in [("Pureza medida no rigoroso", "99,768 %"), ("Margem sobre o grau", "0,268 ponto"),
             ("Na alimentação mais pobre", "99,56 %"), ("Altura &middot; cascos", "173 m &middot; 3"),
             ("Carga do condensador", "49,9 MW"), ("Lucro anual", "63,08 MUSD")]:
    espec += ('      <div style="background: #171E25; padding: 20px 24px; display: flex; '
              'justify-content: space-between; align-items: baseline; gap: 16px">\n'
              '        <div style="font-size: 25px; color: #95A2AD">%s</div>\n'
              '        <div style="font-family: %s; font-size: 25px; font-weight: 600; '
              'color: #E4E9ED; text-align: right">%s</div>\n      </div>\n' % (k, MONO, v))
espec += '    </div>\n'

lamina("L05.dc.html", "A conclusão", 5, cta="", miolo=(
    h1("O projeto que saiu do ciclo rende quatro vezes o inicial.")
    + espec
    + p("O ponto de partida — 200 estágios, refluxo 15 — entregava 98,5 % e vendia grau "
        "químico: 15,25 MUSD/ano. Todos os números acima foram medidos no simulador "
        "rigoroso, não previstos por modelo aproximado.")
    + cita("Simulação de processo diz quanto vale. Aprendizado de máquina e otimização "
           "dizem onde olhar e qual o risco — em dias, e não em meses de engenharia.")))

print("cinco laminas montadas")
