"""
Fase 2 — Curva de partida do reator monolítico
Evolução das espécies na saída ao longo do tempo físico.

Entrada esperada: CSV exportado dos monitores do STAR-CCM+
  (Monitors → selecionar todos → botão direito → Export...)
  Deve conter uma coluna de tempo físico e uma coluna por espécie.

Uso:
    python plot_fase2_partida.py  [caminho_do_csv]

Estilo: CEJ (Chemical Engineering Journal)
Gabriel Rozo | FEQ/UNICAMP | 2025-2027
"""

import sys
import re
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Condições nominais da simulação ───────────────────────────────────────
Y_TG_IN   = 0.8218       # fração mássica de TG na entrada (razão molar 6:1)
Y_MEOH_IN = 0.1782
L         = 50e-3        # m
U_MEAN    = 1.0e-3       # m/s
U_MAX     = 1.5 * U_MEAN # canal plano

T_CENTRO  = L / U_MAX    # 33,3 s — chegada do fluido da linha central
T_MEDIO   = L / U_MEAN   # 50,0 s — tempo de residência médio

# Valores previstos analiticamente (ver FASE2_resultados_CFD.md)
X_TG_PREV    = 0.0171    # %
Y_FAME_PREV  = 4.71e-5

# ── Leitura do CSV ────────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
CSV = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_DIR.parent / "results" / "fase2_monitores.csv"

if not CSV.exists():
    print(f"CSV nao encontrado: {CSV}")
    print()
    print("Exporte do STAR-CCM+:")
    print("  Monitors -> selecionar os monitores -> botao direito -> Export...")
    print(f"  Salvar como: {CSV}")
    sys.exit(1)

dados = np.genfromtxt(CSV, delimiter=",", names=True, deletechars="", replace_space="_")
colunas = list(dados.dtype.names)

def achar(*padroes):
    """Localiza a coluna cujo nome casa com qualquer um dos padroes."""
    for p in padroes:
        for c in colunas:
            if re.search(p, c, re.IGNORECASE):
                return c
    return None

col_t = achar(r"physical.*time", r"\btime\b", r"tempo")
if col_t is None:
    print(f"Coluna de tempo nao encontrada. Colunas: {colunas}")
    sys.exit(1)

t = dados[col_t]

ESPECIES = {
    "TG":   dict(padroes=[r"YTG", r"\bTG\b"],     cor="#1a6faf", papel="reagente"),
    "MeOH": dict(padroes=[r"YMeOH", r"MeOH"],     cor="#2ca02c", papel="reagente"),
    "DG":   dict(padroes=[r"YDG", r"\bDG\b"],     cor="#ff7f0e", papel="produto"),
    "MG":   dict(padroes=[r"YMG", r"\bMG\b"],     cor="#9467bd", papel="produto"),
    "FAME": dict(padroes=[r"YFAME", r"FAME"],     cor="#d62728", papel="produto"),
    "GL":   dict(padroes=[r"YGL", r"\bGL\b"],     cor="#8c564b", papel="produto"),
}

serie = {}
for nome, info in ESPECIES.items():
    c = achar(*info["padroes"])
    if c is not None and c != col_t:
        serie[nome] = dados[c]

print(f"Coluna de tempo : {col_t}")
print(f"Especies lidas  : {', '.join(serie) if serie else '(nenhuma)'}")
print(f"Tempo final     : {t[-1]:.1f} s")
print()

# ── Estilo CEJ ────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "lines.linewidth": 1.4,
    "legend.fontsize": 7.5, "legend.framealpha": 0.9, "legend.edgecolor": "0.7",
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.0))
fig.subplots_adjust(wspace=0.32)

def marcar_tempos(ax):
    """Linhas verticais nos tempos caracteristicos de transito."""
    y0, y1 = ax.get_ylim()
    for tc, rot in ((T_CENTRO, "linha central"), (T_MEDIO, r"$\tau_{res}$")):
        if t[-1] >= tc:
            ax.axvline(tc, color="0.6", lw=0.7, ls=":", zorder=1)
            ax.text(tc, y0 + 0.04 * (y1 - y0), f" {rot}", fontsize=6,
                    color="0.45", va="bottom", ha="left", rotation=90)
    ax.set_ylim(y0, y1)

# ── Painel (a): conversao de TG ───────────────────────────────────────────
if "TG" in serie:
    X_TG = (Y_TG_IN - serie["TG"]) / Y_TG_IN * 100.0
    ax1.plot(t, X_TG, color=ESPECIES["TG"]["cor"], label=r"$X_{\mathrm{TG}}$")
    ax1.axhline(X_TG_PREV, color="0.5", lw=0.8, ls="--",
                label=f"previsto = {X_TG_PREV:.4f} %")
    ax1.set_ylabel(r"$X_{\mathrm{TG}}$" + " (%)")
    ax1.legend(loc="lower right", handlelength=1.8)
    marcar_tempos(ax1)

ax1.set_xlabel(r"$t$ (s)")
ax1.set_xlim(0, t[-1])
ax1.set_title("(a) Conversão de triglicerídeo", fontsize=8, pad=4)

# ── Painel (b): formacao de produtos ──────────────────────────────────────
produtos = [n for n in ("FAME", "DG", "MG", "GL") if n in serie]
for nome in produtos:
    ax2.plot(t, serie[nome] * 1e6, color=ESPECIES[nome]["cor"], label=nome)

if "FAME" in serie:
    ax2.axhline(Y_FAME_PREV * 1e6, color="0.5", lw=0.8, ls="--",
                label="FAME previsto")

ax2.set_xlabel(r"$t$ (s)")
ax2.set_ylabel(r"$Y_i \times 10^{6}$ (-)")
ax2.set_xlim(0, t[-1])
if produtos:
    ax2.legend(loc="upper left", handlelength=1.8, ncol=2)
    marcar_tempos(ax2)
ax2.set_title("(b) Formação de produtos", fontsize=8, pad=4)

# ── Salvar ────────────────────────────────────────────────────────────────
out_dir = SCRIPT_DIR.parent / "results"
out_dir.mkdir(exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(out_dir / f"fig4_fase2_partida.{ext}", dpi=300, bbox_inches="tight")

print(f"Figura salva: {out_dir}/fig4_fase2_partida.pdf")
if "TG" in serie:
    X_final = (Y_TG_IN - serie['TG'][-1]) / Y_TG_IN * 100.0
    print(f"  X_TG em t={t[-1]:.1f} s : {X_final:.5f} %   (previsto {X_TG_PREV:.4f} %)")
if "FAME" in serie:
    print(f"  Y_FAME em t={t[-1]:.1f} s : {serie['FAME'][-1]:.3e}   (previsto {Y_FAME_PREV:.3e})")
