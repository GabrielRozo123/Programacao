"""
Matriz de Decisão — Separação Gás-Sólido (Valgroup Ciclone)
Metodologia: score ∈ {+1=positivo, 0=neutro, -1=negativo} × peso → soma ponderada
Atualizar os dados abaixo conforme literatura e dados do cliente chegarem.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
import numpy as np

# ── Paleta ───────────────────────────────────────────────────────────────────
COR_POS  = "#92D050"   # verde
COR_NEU  = "#FFFF99"   # amarelo claro
COR_NEG  = "#FF6B6B"   # vermelho
COR_HDR  = "#2E5FA3"   # azul cabeçalho
COR_SOMA = "#D9D9D9"   # cinza soma
COR_PESO = "#BDD7EE"   # azul claro peso

SCORE_COR = {1: COR_POS, 0: COR_NEU, -1: COR_NEG}

# ── Tecnologias (colunas) ─────────────────────────────────────────────────────
TECHS = [
    "Ciclone",
    "Quench\nTower",
    "Filtro\nCerâmico",
    "ESP",
    "Scrubber\nÚmido",
    "Settler\nGravit.",
]

# ── Critérios (linhas) ────────────────────────────────────────────────────────
# Cada critério: nome, peso, lista de (texto_célula, score) por tecnologia
# Ordem de tecnologias: Ciclone | Quench | F.Cerâmico | ESP | Scrubber | Settler
CRITERIOS = [
    {
        "nome": "Temperatura\nde operação",
        "peso": 2,
        "celulas": [
            # Ciclone | Quench | F.Cerâmico | ESP | Scrubber | Settler
            ("Até >1000°C\npadrão pirólise\n✓✓",   1),
            ("Entrada até\n500°C → saída\n<250°C",  0),
            ("350–500°C\npirólise ✓\naté 850°C",   1),
            ("⚠ degrada\n>400°C; menor\nefic. + ↑E",-1),
            ("Entrada até\n400°C → saída\n<250°C", -1),
            ("Qualquer\n(passivo)\n✓✓",             1),
        ],
    },
    {
        "nome": "Faixa de\npartículas",
        "peso": 2,
        "celulas": [
            ("5–200 μm\n✗ <10μm\nescapam",          0),
            ("Qualquer\n(dissolve\nou dilui)",        1),
            ("≥ 0.3 μm\n✓✓ finos",                  1),
            ("0.01–10 μm\n✓✓ esp.\nfinos",           1),
            ("≥ 1 μm\n✓ finos",                      1),
            ("> 200–500 μm\n✗✗ ineficaz\npara finos",-1),
        ],
    },
    {
        "nome": "Eficiência\nde coleta",
        "peso": 2,
        "celulas": [
            ("70–95%\n(d* depend.)\n✗ finos",        0),
            ("> 99%\n(dissolve\nchar)",                1),
            ("> 99%\n(0.3μm poro)\n✓✓",              1),
            ("96–99%\n(wire-cyl.\n>500°C)",           1),
            ("90–99%\n≥1μm\n✓",                       1),
            ("50–80%\napenas\ngrossos ✗",            -1),
        ],
    },
    {
        "nome": "Queda de\npressão",
        "peso": 2,
        "celulas": [
            ("5–25 mbar\n✓ < 40 mbar\nLapple",       1),
            ("10–50 mbar\n⚠ no limite\ndo projeto",   0),
            ("10–30 mbar\n✓ (sobe com\nacúmulo)",     1),
            ("0.5–2 mbar\n✓✓ mínimo",                1),
            ("5–30 mbar\n✓",                          1),
            ("< 5 mbar\n✓✓",                          1),
        ],
    },
    {
        "nome": "Char pegajoso\na 450°C",
        "peso": 2,
        "celulas": [
            ("⚠ Risco no\nhopper cônico\n(mitigável)",  0),
            ("✓✓ Char\ndissolve no\nfluido quench",      1),
            ("✗✗ Regeneração\n6–9h! Inviável\ncontínuo",-1),
            ("⚠ Alta resist.\nchar → back-\ncorona",    -1),
            ("✓✓ Lavagem\ncontinua\nremove char",        1),
            ("⚠ Acúmulo\nno fundo\n(limpeza periód.)",   0),
        ],
    },
    {
        "nome": "Adequação\ndownstream\n(condensador\ncasco-tubo)",
        "peso": 2,
        "celulas": [
            ("✓✓ Gás seco\na ~450°C\nperfito",           1),
            ("✗✗ Gás frio\númido <250°C\nmodifica T",   -1),
            ("✓✓ Gás seco\na T alta\ncompatível",        1),
            ("✓✓ Gás seco\ncompatível",                   1),
            ("✗✗ Gás úmido\nfrio <250°C\nincompatível", -1),
            ("✓✓ Gás seco",                               1),
        ],
    },
    {
        "nome": "Custo de\ninvestimento",
        "peso": 1,
        "celulas": [
            ("Baixo\nsem partes\nmóveis ✓✓",  1),
            ("Médio\nbomba +\nrecirculação",   0),
            ("Alto\n600 velas\n3m cada ✗",    -1),
            ("Alto\neletrodos\nalta T ✗",     -1),
            ("Médio\n+ tratamento\nefluente",   0),
            ("Muito\nbaixo ✓✓",                1),
        ],
    },
    {
        "nome": "Manutenção",
        "peso": 1,
        "celulas": [
            ("Baixa\nsem partes\nmóveis ✓✓",    1),
            ("Média\nbomba +\nnebulizador",      0),
            ("Alta\n6–9h regen.\npor ciclo ✗", -1),
            ("Média\nlimpeza\neletrodos",         0),
            ("Média\ntratamento\nlíquido",        0),
            ("Baixa\n✓✓",                        1),
        ],
    },
    {
        "nome": "Maturidade\ntecnológica",
        "peso": 1,
        "celulas": [
            ("Alta\npadrão\nindústria ✓✓",  1),
            ("Alta\npiloto e\nlab ✓",        1),
            ("Alta em\ngasific.\n⚠ pirólise",0),
            ("⚠ Parcial\n>400°C ainda\nem pesquisa",0),
            ("Alta\n✓✓",                    1),
            ("Alta\n(trivial)\n✓✓",         1),
        ],
    },
]

# ── Cálculo das somas ponderadas ──────────────────────────────────────────────
n_tech = len(TECHS)
n_crit = len(CRITERIOS)

somas = [0] * n_tech
for c in CRITERIOS:
    for t, (_, sc) in enumerate(c["celulas"]):
        somas[t] += sc * c["peso"]

# ── Construção da figura ──────────────────────────────────────────────────────
COL_NOME_W  = 1.8   # largura coluna "critério"
COL_PESO_W  = 0.5   # largura coluna "peso"
COL_TECH_W  = 1.5   # largura colunas de tecnologia
ROW_H       = 0.85  # altura de cada linha de critério
ROW_H_HDR   = 0.55  # altura cabeçalho
ROW_H_SOMA  = 0.55  # altura linha de soma

total_w = COL_NOME_W + COL_PESO_W + n_tech * COL_TECH_W + 0.4
total_h = ROW_H_HDR + n_crit * ROW_H + ROW_H_SOMA + 0.4

fig, ax = plt.subplots(figsize=(total_w, total_h))
ax.set_xlim(0, total_w)
ax.set_ylim(0, total_h)
ax.axis("off")

def col_x(col_idx):
    """Retorna x do lado esquerdo da coluna (0=nome, 1=peso, 2..=techs)."""
    if col_idx == 0:
        return 0.2
    if col_idx == 1:
        return 0.2 + COL_NOME_W
    return 0.2 + COL_NOME_W + COL_PESO_W + (col_idx - 2) * COL_TECH_W

def draw_cell(ax, x, y, w, h, text, facecolor, textcolor="black", fontsize=7.5,
              bold=False, ha="center", va="center"):
    rect = plt.Rectangle((x, y), w, h, facecolor=facecolor,
                          edgecolor="white", linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text, ha=ha, va=va,
            fontsize=fontsize, color=textcolor,
            fontweight="bold" if bold else "normal",
            wrap=True, multialignment="center")

y_top = total_h - 0.2

# ── Cabeçalho ────────────────────────────────────────────────────────────────
draw_cell(ax, col_x(0), y_top - ROW_H_HDR, COL_NOME_W, ROW_H_HDR,
          "Critério", COR_HDR, textcolor="white", bold=True)
draw_cell(ax, col_x(1), y_top - ROW_H_HDR, COL_PESO_W, ROW_H_HDR,
          "Peso", COR_HDR, textcolor="white", bold=True)
for t, tech in enumerate(TECHS):
    draw_cell(ax, col_x(t + 2), y_top - ROW_H_HDR, COL_TECH_W, ROW_H_HDR,
              tech, COR_HDR, textcolor="white", bold=True, fontsize=8)

# ── Linhas de critério ────────────────────────────────────────────────────────
for r, crit in enumerate(CRITERIOS):
    y = y_top - ROW_H_HDR - (r + 1) * ROW_H
    # fundo alternado para nome
    bg_nome = "#F2F2F2" if r % 2 == 0 else "#FFFFFF"
    draw_cell(ax, col_x(0), y, COL_NOME_W, ROW_H,
              crit["nome"], bg_nome, fontsize=7.5, ha="center")
    draw_cell(ax, col_x(1), y, COL_PESO_W, ROW_H,
              str(crit["peso"]), COR_PESO, bold=True, fontsize=9)
    for t, (txt, sc) in enumerate(crit["celulas"]):
        draw_cell(ax, col_x(t + 2), y, COL_TECH_W, ROW_H,
                  txt, SCORE_COR[sc], fontsize=7)

# ── Linha de soma ─────────────────────────────────────────────────────────────
y_soma = y_top - ROW_H_HDR - n_crit * ROW_H - ROW_H_SOMA
draw_cell(ax, col_x(0), y_soma, COL_NOME_W, ROW_H_SOMA,
          "SOMA PONDERADA", COR_HDR, textcolor="white", bold=True)
draw_cell(ax, col_x(1), y_soma, COL_PESO_W, ROW_H_SOMA,
          "—", COR_HDR, textcolor="white", bold=True)
soma_max = sum(c["peso"] for c in CRITERIOS)
for t, s in enumerate(somas):
    # cor da soma: verde se positivo, amarelo se 0, vermelho se negativo
    cor_s = COR_POS if s > 0 else (COR_NEU if s == 0 else COR_NEG)
    draw_cell(ax, col_x(t + 2), y_soma, COL_TECH_W, ROW_H_SOMA,
              f"{s:+d}\n(máx {soma_max})", cor_s, bold=True, fontsize=9)

# ── Legenda ───────────────────────────────────────────────────────────────────
leg_x = 0.2
leg_y = y_soma - 0.45
patches = [
    mpatches.Patch(color=COR_POS,  label="Positivo  (+1 × peso)"),
    mpatches.Patch(color=COR_NEU,  label="Neutro     (0 × peso)"),
    mpatches.Patch(color=COR_NEG,  label="Negativo  (−1 × peso)"),
]
ax.legend(handles=patches, loc="lower left",
          bbox_to_anchor=(leg_x / total_w, 0.0),
          fontsize=8, framealpha=0.9, title="Legenda", title_fontsize=8)

# ── Título ────────────────────────────────────────────────────────────────────
fig.text(0.5, 0.98,
         "Matriz de Decisão — Separação Gás-Sólido (Valgroup Ciclone)\n"
         "Gás de pirólise: 400–450°C, 1.2 bar, ~80 kg/h char  |  ΔP máx. 40 mbar",
         ha="center", va="top", fontsize=10, fontweight="bold")

plt.tight_layout(rect=[0, 0.04, 1, 0.96])
plt.savefig("matriz_decisao_valgroup.png", dpi=180, bbox_inches="tight")
print("Salvo: matriz_decisao_valgroup.png")
print("\nSomas ponderadas:")
for t, s in zip(TECHS, somas):
    bar = "█" * abs(s) if s > 0 else "░" * abs(s)
    print(f"  {t.replace(chr(10),' '):20s}  {s:+3d}  {bar}")
