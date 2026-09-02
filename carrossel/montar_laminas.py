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

def topo(sobre, n, total=12):
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

# ============================================================== 01 · capa · o penhasco
lamina("Main.dc.html", "O que a simulação de processo entrega", 1, gap=22, miolo=(
    h1("Um décimo de ponto percentual separa dois mercados.", 56)
    + '    <div>' + svg("parede") + '</div>\n'
    + p("Splitter de propeno. Acima de 99,5 % o produto vale US$ 1 150/t; abaixo, US$ 950/t. "
        "A pureza sobe suave com o refluxo — " + forte("o dinheiro salta de 14 para 65 milhões")
        + " ao cruzar a linha.", 27)))

# ==================================================== 02 · o que estava em jogo
lamina("L02.dc.html", "O que estava em jogo", 2, miolo=(
    h1("O projeto que parecia razoável não fazia especificação.")
    + p("Uma coluna de 200 estágios com refluxo 15 entrega 98,5 % de pureza. É uma coluna "
        "que funciona, converge e parece correta. Só que vende grau químico.")
    + celas([("Projeto inicial", "15,25", "MUSD/ano &middot; grau químico", CINZA),
             ("Projeto final validado", "63,08", "MUSD/ano &middot; grau polímero", CB)])
    + cita("Mesma alimentação, mesma planta, " + forte("21 % mais energia") + " — e "
           + forte("quatro vezes o lucro") + ". A diferença entre um projeto e outro "
           "raramente é marginal.")))

# ============================================ 03 · o que a simulação rigorosa entrega
lamina("L03.dc.html", "Capacidade 1 · simulação rigorosa", 3, miolo=(
    h1("A simulação não é um desenho. É o número que você assina.")
    + p("Um simulador rigoroso resolve o equilíbrio líquido-vapor estágio a estágio, com "
        "equação de estado validada, e fecha os balanços de massa e energia. O que sai não é "
        "estimativa: é o ponto de operação que vai para a planta.")
    + cartoes([("Entrega", "Perfil de temperatura, composição e carga térmica em cada estágio."),
               ("Entrega", "Dimensionamento: diâmetro, altura, área de troca, consumo de utilidades."),
               ("Entrega", "O caso base contra o qual todo modelo aproximado é conferido.")])
    + cita("Neste estudo o projeto final foi montado no DWSIM e mediu "
           + forte("99,768 % de pureza") + " contra 99,720 % previstos. É esse número que "
           "sustenta a decisão de investimento — não o do modelo aproximado.")))

# =========================================== 04 · onde o resultado realmente se decide
lamina("L04.dc.html", "Capacidade 2 · análise de sensibilidade", 4, gap=26, miolo=(
    h1("Seis variáveis. Duas decidem três quartos do resultado.", 58)
    + ('    <div style="display: flex; gap: 32px; align-items: center; font-size: 23px; '
       'color: #95A2AD">\n'
       '      <div style="display: flex; align-items: center; gap: 11px"><div style="width: 17px; '
       'height: 17px; border-radius: 3px; background: #5798CE"></div>você decide</div>\n'
       '      <div style="display: flex; align-items: center; gap: 11px"><div style="width: 17px; '
       'height: 17px; border-radius: 3px; background: #D37642"></div>você recebe</div>\n'
       '    </div>\n')
    + '    <div>' + svg("sobol") + '</div>\n'
    + p("Quanto cada variável explica da variação do lucro. Serve para decidir onde gastar "
        "atenção de engenharia — e o que é ruído. " + forte("A maior influência isolada é a "
        "composição da alimentação") + ", que chega pela tubulação e ninguém escolhe.", 27)))

# =================================================== 05 · a variável que ninguém revisita
lamina("L05.dc.html", "O achado que pagou o estudo", 5, miolo=(
    h1("O dinheiro estava na variável que ninguém revisita.")
    + p("Revamp de coluna quase sempre discute refluxo e número de estágios. A pressão de "
        "operação é decisão de projeto original e costuma ficar congelada por décadas.")
    + celas([("Ganho da otimização", "+1,5", "MUSD/ano", CB),
             ("Origem do ganho", "pressão", "de 18,0 para 16,6 bar", AZ)])
    + p("Menos pressão, mais volatilidade relativa — e menos refluxo para a mesma pureza.")
    + cita("A otimização multiobjetivo não é mais um relatório. É a única etapa que testa "
           + forte("combinações que ninguém pensaria em testar") + ".")))

# ===================================================== 06 · o que o ML entrega e o que nao
lamina("L06.dc.html", "Capacidade 3 · aprendizado de máquina", 6, miolo=(
    h1("O que o modelo aprendido entrega — e o que ele não entrega.")
    + cartoes([("Entrega", "Milhares de cenários avaliados onde caberiam dezenas. O espaço de projeto inteiro, não três casos."),
               ("Entrega", "Quais variáveis movem o resultado, medido nos dados e não por intuição."),
               ("Entrega", "Uma equação legível quando existe: a regressão simbólica reencontrou o balanço de energia da coluna sozinha.")])
    + p("O que ele " + forte("não") + " entrega é precisão no ponto ótimo. Um modelo aprendido "
        "erra mais justamente onde o otimizador quer chegar — porque o otimizador procura onde "
        "o modelo é otimista.")
    + cita("Por isso a etapa seguinte não é opcional.")))

# ================================================ 07 · por que otimizacao volta ao rigoroso
lamina("L07.dc.html", "Por que validar não é zelo", 7, gap=22, miolo=(
    h1("Quase metade das soluções ótimas não funcionava.", 54)
    + ('    <div style="display: flex; gap: 34px; align-items: center; font-size: 24px; '
       'color: #95A2AD">\n'
       '      <div style="display: flex; align-items: center; gap: 11px"><div style="width: 17px; '
       'height: 17px; border-radius: 50%; background: #5798CE"></div>atende a especificação &middot; 55</div>\n'
       '      <div style="display: flex; align-items: center; gap: 11px"><div style="width: 17px; '
       'height: 17px; border-radius: 50%; background: #D37642"></div>não atende &middot; 45</div>\n'
       '    </div>\n')
    + '    <div>' + svg("paridade") + '</div>\n'
    + p("Cem projetos ótimos propostos pelo modelo aprendido, todos reavaliados na simulação "
        "rigorosa. " + forte("45 violavam a pureza mínima") + ", e 54 chegaram a prever pureza "
        "acima de 100 %. Sem a etapa de validação, quase metade do que se aprova não entrega.", 26)))

# ============================================== 08 · o risco da alimentacao pobre
lamina("L08.dc.html", "O risco que ninguém pergunta na aprovação", 8, miolo=(
    h1("E quando a alimentação piorar, a coluna ainda faz o grau?")
    + p("A mesma coluna foi testada em toda a faixa de composição que a planta pode receber. "
        "41 % dos projetos que apareciam como grau polímero " + forte("só eram grau polímero "
        "porque a alimentação daquele caso era rica") + ".")
    + celas([("Projeto de maior lucro", "99,50", "% na alimentação pobre &middot; perde o grau", CB),
             ("Projeto escolhido", "99,56", "% na alimentação pobre &middot; mantém", AZ)])
    + cita("O projeto mais lucrativo é o único dos cinco que cai do grau quando a alimentação "
           "empobrece. Trocar por ele custaria " + forte("0,10 MUSD/ano") + " a menos de lucro "
           "nominal e evitaria um risco de " + forte("50 MUSD/ano") + ".")))

# ================================================ 09 · a decisao de capital
lamina("L09.dc.html", "A decisão que o modelo não sabe tomar", 9, miolo=(
    h1("O otimizador apontava para uma coluna que ninguém constrói.")
    + p("Acima de 60 metros a coluna precisa ser dividida em cascos. O modelo de custo paga o "
        "casco — mas não paga a fundação, a interligação de grande diâmetro, o bombeamento de "
        "cinquenta metros nem a área de terreno.")
    + celas([("O quarto casco rende", "0,23", "MUSD/ano", AZ),
             ("Só se paga se custar", "&lt; 1,72", "MUSD de capital", AZ),
             ("Custa de fato", "3 a 8", "MUSD", CB)])
    + cita("O modelo otimiza exatamente aquilo que você custeia. " + forte("O que fica fora da "
           "planilha, ele distribui de graça") + " — e aponta para a resposta errada com toda "
           "a confiança do mundo.")))

# ============================================================== 10 · o ciclo
lamina("L10.dc.html", "Como as três coisas se encaixam", 10, gap=30, miolo=(
    h1("Nenhuma das três resolve sozinha.")
    + '    <div>' + svg("ciclo") + '</div>\n'
    + p("A simulação rigorosa é exata e lenta demais para varrer milhares de cenários. O modelo "
        "rápido varre, mas só vale calibrado contra ela. O aprendizado de máquina explica e a "
        "otimização propõe — e nenhuma das duas tem autoridade para aprovar nada.", 27)
    + cita("O que torna isso um método de engenharia, e não um exercício de dados, é o "
           + forte("fechamento do ciclo") + ": a proposta volta para o rigoroso antes de virar "
           "projeto.", 28)))

# ========================================================== 11 · o resultado
espec = ('    <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; '
         'background: #2B343D; border: 1px solid #2B343D">\n')
for k, v in [("Pureza medida no rigoroso", "99,768 %"), ("Margem sobre o grau", "0,268 ponto"),
             ("Na alimentação mais pobre", "99,56 %"), ("Cascos", "3"),
             ("Carga do condensador", "49,9 MW"), ("Lucro anual", "63,08 MUSD")]:
    espec += ('      <div style="background: #171E25; padding: 20px 24px; display: flex; '
              'justify-content: space-between; align-items: baseline; gap: 16px">\n'
              '        <div style="font-size: 25px; color: #95A2AD">%s</div>\n'
              '        <div style="font-family: %s; font-size: 25px; font-weight: 600; color: #E4E9ED; '
              'text-align: right">%s</div>\n      </div>\n' % (k, MONO, v))
espec += '    </div>\n'

lamina("L11.dc.html", "O resultado", 11, miolo=(
    h1("O projeto que saiu do ciclo.")
    + espec
    + p("Nenhum número desta tabela é previsão de modelo aproximado. Todos foram medidos na "
        "simulação rigorosa ou calculados a partir de medições dela.")
    + cita("Quatro vezes o lucro do projeto inicial, com margem sobre a especificação em "
           "toda a faixa de alimentação que a planta pode receber.")))

# ========================================================== 12 · fecho
lamina("L12.dc.html", "O que isso significa na prática", 12, cta="", miolo=(
    h1("Três perguntas que essa combinação passa a responder.")
    + cartoes([("Quanto vale", "Qual é a diferença em milhões entre o projeto aceitável e o projeto certo."),
               ("Onde olhar", "Quais variáveis realmente movem o resultado — e quais você não controla."),
               ("Qual o risco", "O que acontece com a especificação quando a alimentação piorar.")])
    + p("Simulação de processo responde a primeira com autoridade. Aprendizado de máquina e "
        "otimização tornam a segunda e a terceira viáveis em dias, e não em meses de engenharia.")
    + cita("Estudo completo — incluindo as previsões que erraram — versionado em repositório "
           "público. Comenta aí que eu mando o link.")))

print("doze laminas montadas")
