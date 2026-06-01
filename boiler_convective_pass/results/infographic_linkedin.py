"""
Infográfico LinkedIn — Passe Convectivo de Caldeira Aquatubular
Dados reais da simulação CHT no Simcenter STAR-CCM+
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ─── Paleta ───────────────────────────────────────────────────────────────────
BG      = '#0d1117'
PANEL   = '#161b22'
BORDER  = '#30363d'
BLUE    = '#58a6ff'
RED     = '#f85149'
ORANGE  = '#e3b341'
GREEN   = '#3fb950'
TEXT    = '#e6edf3'
SUBTEXT = '#8b949e'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'text.color': TEXT,
    'axes.labelcolor': TEXT,
    'xtick.color': SUBTEXT,
    'ytick.color': SUBTEXT,
    'axes.edgecolor': BORDER,
    'figure.facecolor': BG,
    'axes.facecolor': PANEL,
    'grid.color': BORDER,
    'grid.alpha': 0.4,
    'axes.grid': True,
})

# ─── Dados da simulação ───────────────────────────────────────────────────────
q_raw = np.array([
    4.921e4, 4.909e4, 5.037e4,   # Fileira 1
    5.110e4, 4.985e4, 5.044e4,   # Fileira 2
    4.960e4, 5.867e4, 4.667e4,   # Fileira 3
    5.716e4, 6.352e4, 4.957e4,   # Fileira 4
    5.909e4, 6.389e4, 4.578e4,   # Fileira 5
    5.492e4, 4.975e4, 4.358e4,   # Fileira 6
    4.414e4, 4.003e4, 3.423e4,   # Fileira 7
    3.736e4, 3.567e4, 2.812e4,   # Fileira 8
    2.424e4, 3.196e4, 2.512e4,   # Fileira 9
    1.947e4, 2.991e4, 2.398e4,   # Fileira 10
    1.974e4, 2.626e4, 2.111e4,   # Fileira 11
    2.036e4, 2.578e4, 1.651e4,   # Fileira 12
    1.738e4, 2.541e4, 1.767e4,   # Fileira 13
    1.604e4, 2.454e4, 1.685e4,   # Fileira 14
])

q_matrix = q_raw.reshape(14, 3) / 1000   # kW/m²
row_avg  = q_matrix.mean(axis=1)
rows     = np.arange(1, 15)

Re_range = np.logspace(3.3, 5.2, 300)
Nu_Zuk   = 0.27 * Re_range**0.63 * 0.71**0.36
Re_CFD   = 7500
Nu_CFD   = 55.8

# ─── Layout ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(21, 13.5), facecolor=BG)
gs  = gridspec.GridSpec(
    3, 3, figure=fig,
    hspace=0.55, wspace=0.38,
    top=0.88, bottom=0.10,
    left=0.05, right=0.97,
    height_ratios=[1.0, 1.15, 0.28],
)

# Título principal
fig.text(0.5, 0.955, 'CFD DO PASSE CONVECTIVO — CALDEIRA AQUATUBULAR INDUSTRIAL',
         ha='center', va='center', fontsize=15, fontweight='bold', color=TEXT)
fig.text(0.5, 0.925,
         'STAR-CCM+  |  CHT  |  k-ω SST  |  20,5M células  |  Validação Žukauskas (1972)',
         ha='center', va='center', fontsize=9, color=SUBTEXT)

# ─── PAINEL 1 — Condições de Operação ─────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 8)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_facecolor(PANEL)
ax1.set_title('CONDIÇÕES DE OPERAÇÃO', color=TEXT, fontsize=10,
              fontweight='bold', pad=8, loc='center')

# Divisor vertical: texto à esquerda (x<5), tubos à direita (x>=5)
ax1.axvline(4.8, color=BORDER, lw=0.8, alpha=0.5)

# Tubos 3×4 — lado DIREITO
for row in range(4):
    for col in range(3):
        cx = 5.8 + col * 1.35
        cy = 1.5 + row * 1.6
        ax1.add_patch(Circle((cx, cy), 0.38, color=BLUE, zorder=3, alpha=0.85))
        ax1.add_patch(Circle((cx, cy), 0.22, color='#1f6feb', zorder=4))

# Setas de escoamento apontando para os tubos
for y in [1.5, 3.1, 4.7, 6.3]:
    ax1.annotate('', xy=(5.2, y), xytext=(0.4, y),
                 arrowprops=dict(arrowstyle='->', color=RED, lw=1.8))

# Rótulos — lado ESQUERDO (coordenadas de dados, sem sobreposição)
params = [
    (0.3, 7.2, 'Gás de combustão', RED, 8.5, 'bold'),
    (0.3, 6.65,'900 °C  |  8 m/s', RED, 8.5, 'normal'),
    (0.3, 5.7, 'Tubo SA-192', BLUE, 8, 'normal'),
    (0.3, 5.15, u'Ø50,8 mm  (BWG 9)', BLUE, 8, 'normal'),
    (0.3, 4.3, 'Tₛₐₜ = 195 °C', BLUE, 8, 'normal'),
    (0.3, 3.75,'P = 14 bar', BLUE, 8, 'normal'),
    (0.3, 2.9, 'ST/D = SL/D = 2,0', SUBTEXT, 7.5, 'normal'),
    (0.3, 2.35,'14 fileiras × 3 tubos', SUBTEXT, 7.5, 'normal'),
    (0.3, 1.4, 'U_max = 16 m/s', ORANGE, 8.5, 'bold'),
    (0.3, 0.85,'Re_D ≈ 7 500', ORANGE, 8.5, 'bold'),
]
for x, y, txt, col, fs, fw in params:
    ax1.text(x, y, txt, color=col, fontsize=fs, fontweight=fw, va='center')

# ─── PAINEL 2 — Mapa de Fluxo de Calor por Tubo ──────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(PANEL)
ax2.set_title('CFD — FLUXO DE CALOR POR TUBO (kW/m²)', color=TEXT,
              fontsize=10, fontweight='bold', pad=8, loc='center')

cmap_hot = LinearSegmentedColormap.from_list(
    'boiler', ['#1f4e8c', '#3498db', '#f39c12', '#e74c3c', '#8b0000'])
im = ax2.imshow(q_matrix, aspect='auto', cmap=cmap_hot, origin='upper',
                vmin=q_matrix.min(), vmax=q_matrix.max())

# Anotações de valor em cada célula
for i in range(14):
    for j in range(3):
        val = q_matrix[i, j]
        color = 'white' if val < 45 else 'black'
        ax2.text(j, i, f'{val:.0f}', ha='center', va='center',
                 fontsize=7.5, color=color, fontweight='bold')

ax2.set_xticks([0, 1, 2])
ax2.set_xticklabels(['Tubo A', 'Tubo B', 'Tubo C'], fontsize=8)
ax2.set_yticks(range(14))
ax2.set_yticklabels([f'F{i+1}' for i in range(14)], fontsize=7.5)
ax2.set_xlabel('← Direção transversal →', fontsize=8, color=SUBTEXT)
ax2.set_ylabel('Direção do escoamento →', fontsize=8, color=SUBTEXT)

cb = plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
cb.set_label('q"  (kW/m²)', color=SUBTEXT, fontsize=8)
cb.ax.yaxis.set_tick_params(color=SUBTEXT)
plt.setp(cb.ax.yaxis.get_ticklabels(), color=SUBTEXT, fontsize=7)

ax2.text(-0.01, -0.06, '← Entrada gás 900 °C', transform=ax2.transAxes,
         fontsize=7.5, color=RED, ha='left', va='top')

# ─── PAINEL 3 — Validação Žukauskas ──────────────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor(PANEL)
ax3.set_title('VALIDAÇÃO — CORRELAÇÃO DE ŽUKAUSKAS', color=TEXT,
              fontsize=10, fontweight='bold', pad=8, loc='center')

ax3.loglog(Re_range, Nu_Zuk, '-', color=ORANGE, lw=2.5,
           label='Žukauskas (1972)\nNu = 0,27·Re⁰·⁶³·Pr⁰·³⁶')
ax3.loglog(Re_CFD, Nu_CFD, 'o', color=GREEN, ms=12, zorder=5,
           label=f'CFD (STAR-CCM+)\nNu = {Nu_CFD:.1f}')

# Linha de desvio
ax3.annotate(f'Desvio: −14,8%\n(dentro da faixa\nRANS k-ω SST)',
             xy=(Re_CFD, Nu_CFD), xytext=(Re_CFD*2.5, Nu_CFD*0.55),
             color=GREEN, fontsize=8,
             arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5))

# Zona de aceitação ±20%
ax3.fill_between(Re_range, Nu_Zuk*0.80, Nu_Zuk*1.20,
                 alpha=0.12, color=GREEN, label='±20% (aceitável)')

ax3.set_xlabel('Re_D  (baseado em U_max)', fontsize=9)
ax3.set_ylabel('Nu_D', fontsize=9)
ax3.legend(fontsize=7.5, framealpha=0.2, labelcolor=TEXT,
           facecolor=PANEL, edgecolor=BORDER)
ax3.set_xlim(2e3, 2e5)
ax3.set_ylim(20, 400)

# Resultado ΔP
ax3.text(0.04, 0.12,
         f'ΔP = 244 Pa  (14 fileiras)\nEu_CFD = 0,37  ✓',
         transform=ax3.transAxes, color=BLUE, fontsize=8,
         bbox=dict(boxstyle='round', facecolor=PANEL, edgecolor=BLUE, alpha=0.8))

# ─── PAINEL 4 — Distribuição por Fileira ──────────────────────────────────────
ax4 = fig.add_subplot(gs[1, :2])
ax4.set_facecolor(PANEL)
ax4.set_title('DISTRIBUIÇÃO DE FLUXO DE CALOR POR FILEIRA — IMPLICAÇÃO DIRETA NA MANUTENÇÃO',
              color=TEXT, fontsize=10, fontweight='bold', pad=8, loc='center')

# Cores por zona de risco
bar_colors = []
for q in row_avg:
    if q > 50:
        bar_colors.append(RED)
    elif q > 35:
        bar_colors.append(ORANGE)
    else:
        bar_colors.append(BLUE)

bars = ax4.bar(rows, row_avg, color=bar_colors, alpha=0.88,
               edgecolor=BORDER, linewidth=0.8, width=0.75)

# Valor sobre cada barra
for bar, val in zip(bars, row_avg):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val:.0f}', ha='center', va='bottom', fontsize=7.5,
             color=TEXT, fontweight='bold')

# Zonas de risco
ax4.axvspan(0.5,  5.5, alpha=0.06, color=RED,    label='Zona crítica: maior erosão/fouling')
ax4.axvspan(5.5,  8.5, alpha=0.06, color=ORANGE, label='Zona de transição')
ax4.axvspan(8.5, 14.5, alpha=0.06, color=BLUE,   label='Zona estável: menor risco')

# Linha de média global
ax4.axhline(row_avg.mean(), color=SUBTEXT, ls='--', lw=1.2, alpha=0.7)
ax4.text(14.6, row_avg.mean(), f'Média\n{row_avg.mean():.0f} kW/m²',
         va='center', color=SUBTEXT, fontsize=8)

# Anotações industriais
ax4.annotate('Pico nas fil. 3–5\n(turbulência desenvolvida)\n→ máxima erosão por cinzas',
             xy=(4, row_avg[3]), xytext=(5.5, 58),
             color=RED, fontsize=7.5, ha='center',
             arrowprops=dict(arrowstyle='->', color=RED, lw=1.3))

ax4.annotate('Queda abrupta\nfil. 7→9\n→ alvo de soot blowing',
             xy=(8, row_avg[7]), xytext=(9.5, 50),
             color=ORANGE, fontsize=7.5, ha='center',
             arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1.3))

ax4.set_xlabel('Fileira (direção do escoamento →)', fontsize=9)
ax4.set_ylabel('q"  médio  (kW/m²)', fontsize=9)
ax4.set_xlim(0.3, 15.5)
ax4.set_ylim(0, 72)
ax4.set_xticks(rows)
ax4.legend(fontsize=8, loc='upper right', framealpha=0.2,
           facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT)

# ─── PAINEL 5 — Implicações Industriais ──────────────────────────────────────
ax5 = fig.add_subplot(gs[1, 2])
ax5.set_facecolor(PANEL)
ax5.axis('off')
ax5.set_title('PROBLEMAS INDUSTRIAIS\nENDEREÇADOS', color=TEXT,
              fontsize=10, fontweight='bold', pad=8, loc='center')

issues = [
    (RED,    '[ I ]  EROSÃO POR CINZAS',
             'U_max = 16 m/s nas seções\nmínimas. Fil. 3–5: pico de\nfluxo → maior impacto\nde partículas de SiO₂.'),
    (ORANGE, '[ II ]  FOULING / INCRUSTAÇÃO',
             'Gradiente de q" revela\nonde a deposição reduz\nmais a eficiência.\nGuia a frequência de limpeza.'),
    (BLUE,   '[ III ]  QUEDA DE PRESSÃO',
             'ΔP = 244 Pa (14 fileiras)\nEu = 0,37 — base para\ndimensionar ventilador\nde tiragem forçada.'),
    (GREEN,  '[ IV ]  PROJETO DE PITCH',
             'ST/D = 2 valida acesso\npara sopradores de fuligem\ne distribui erosão.\nTrade-off: Nu × ΔP.'),
]

y = 0.96
for color, title, body in issues:
    ax5.text(0.04, y, title, transform=ax5.transAxes,
             color=color, fontsize=8.5, fontweight='bold', va='top')
    y -= 0.07
    ax5.text(0.04, y, body, transform=ax5.transAxes,
             color=SUBTEXT, fontsize=7.5, va='top')
    y -= 0.18
    ax5.plot([0.04, 0.96], [y + 0.04, y + 0.04],
             color=BORDER, lw=0.8, transform=ax5.transAxes, clip_on=False)

# ─── FAIXA INFERIOR — Fluxo do processo ──────────────────────────────────────
ax6 = fig.add_subplot(gs[2, :])
ax6.axis('off')
ax6.set_facecolor(BG)

steps = [
    (BLUE,   'GEOMETRIA\nPython/build123d\n42 tubos SA-192'),
    (BLUE,   'MALHA\n20,5M células\ny⁺ < 1'),
    (ORANGE, 'FÍSICA\nCHT + k-ω SST\nIdeal Gas'),
    (ORANGE, 'CONVERGÊNCIA\nNu estável\n~800 iter.'),
    (GREEN,  'VALIDAÇÃO\nNu: −14,8%\nEu: dentro da faixa'),
    (RED,    'INSIGHT\nErosão/Fouling\nFileiras 3–5'),
    (RED,    'DECISÃO\nSoot blowing\nOtimização pitch'),
]

n = len(steps)
box_w = 1.0 / (n + (n-1)*0.15) * 0.88
gap   = box_w * 0.18
x0    = 0.01

for i, (color, label) in enumerate(steps):
    x = x0 + i * (box_w + gap)
    rect = FancyBboxPatch((x, 0.12), box_w, 0.76,
                           transform=ax6.transAxes,
                           boxstyle='round,pad=0.02',
                           facecolor=color + '22',
                           edgecolor=color, linewidth=1.5,
                           clip_on=False)
    ax6.add_patch(rect)
    ax6.text(x + box_w/2, 0.50, label,
             transform=ax6.transAxes,
             ha='center', va='center',
             fontsize=7.5, color=TEXT, fontweight='bold',
             linespacing=1.4)
    if i < n - 1:
        ax6.annotate('', xy=(x + box_w + gap, 0.50),
                     xytext=(x + box_w + 0.002, 0.50),
                     xycoords='axes fraction', textcoords='axes fraction',
                     arrowprops=dict(arrowstyle='->', color=SUBTEXT, lw=1.5))

# ─── Salvar ───────────────────────────────────────────────────────────────────
out = '/home/user/Programacao/boiler_convective_pass/results/linkedin_infographic.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=BG)
print(f'Salvo em: {out}')
plt.close()
