"""Figuras do estudo.

Paleta e regras de marca validadas para daltonismo; tema claro e tema escuro
sao dois conjuntos de passos escolhidos para cada fundo, nao uma inversao
automatica. Sem eixo duplo em nenhuma figura: quando ha duas grandezas de escala
diferente, sao dois paineis empilhados com o mesmo eixo x.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .arraste import velocidade_terminal, velocidade_terminal_stokes
from .dimensionamento import Dimensionamento
from .souders_brown import FATORES_K, FT_S, diametro_de_gota_implicito, souders_brown

TEMAS = {
    "claro": {
        "superficie": "#fcfcfb",
        "texto": "#0b0b0b",
        "secundario": "#52514e",
        "grade": "#e6e5e1",
        "faixa": "#f0efec",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],
    },
    "escuro": {
        "superficie": "#1a1a19",
        "texto": "#ffffff",
        "secundario": "#c3c2b7",
        "grade": "#33332f",
        "faixa": "#26262300",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500"],
    },
}


def _n(valor: float, casas: int = 1) -> str:
    """Numero com virgula decimal, como se escreve em portugues."""
    return f"{valor:.{casas}f}".replace(".", ",")


def _aplica(tema: dict) -> None:
    plt.rcParams.update({
        "figure.facecolor": tema["superficie"],
        "axes.facecolor": tema["superficie"],
        "savefig.facecolor": tema["superficie"],
        "text.color": tema["texto"],
        "axes.labelcolor": tema["secundario"],
        "axes.edgecolor": tema["grade"],
        "xtick.color": tema["secundario"],
        "ytick.color": tema["secundario"],
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.color": tema["grade"],
        "grid.linewidth": 0.8,
        "grid.linestyle": "-",
        "axes.axisbelow": True,
        "legend.frameon": False,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
    })


def _limpa(ax, tema: dict) -> None:
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(tema["grade"])
        ax.spines[lado].set_linewidth(0.8)


def _titulo(ax, titulo: str, subtitulo: str, tema: dict) -> None:
    ax.set_title(titulo, color=tema["texto"], loc="left", pad=30)
    ax.text(0.0, 1.018, subtitulo, transform=ax.transAxes, fontsize=9,
            color=tema["secundario"], va="bottom", ha="left")


# ---------------------------------------------------------------------------
# Figura 1 - velocidade terminal, v_max e os dois limites escondidos
# ---------------------------------------------------------------------------


def figura_velocidade_terminal(dim: Dimensionamento, saida: Path, tema_nome: str = "claro") -> Path:
    tema = TEMAS[tema_nome]
    _aplica(tema)
    c = dim.corrente
    d = np.logspace(math.log10(5e-6), math.log10(3e-3), 320)
    vt = np.array([velocidade_terminal(x, c.rho_g, c.rho_l, c.mu_g).v_t for x in d])
    vst = np.array([velocidade_terminal_stokes(x, c.rho_g, c.rho_l, c.mu_g) for x in d])

    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=170)

    # Faixa de gota que o bocal de entrada destroi por Weber.
    ax.axvspan(dim.d_max_estavel_bocal * 1e6, d[-1] * 1e6,
               color=tema["grade"], alpha=0.55, lw=0, zorder=0)

    ax.plot(d * 1e6, vt, color=tema["series"][0], label="Velocidade terminal (Schiller-Naumann)")
    ax.plot(d * 1e6, vst, color=tema["series"][1], label="Assíntota de Stokes")

    # Limite de projeto: linha fina em tinta de texto, nunca cor de série.
    ax.axhline(dim.sb.v_max, color=tema["secundario"], lw=1.2, zorder=3)
    ax.axvline(dim.d_implicito * 1e6, color=tema["secundario"], lw=1.2, zorder=3)
    ax.plot([dim.d_implicito * 1e6], [dim.sb.v_max], "o", ms=7,
            color=tema["series"][0], mec=tema["superficie"], mew=2, zorder=5)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(d[0] * 1e6, d[-1] * 1e6)
    ax.set_ylim(8e-4, 30.0)   # a assíntota de Stokes sai pelo topo, e é esse o ponto
    ax.set_xlabel("Diâmetro da gota  [µm]")
    ax.set_ylabel("Velocidade  [m/s]")
    _limpa(ax, tema)
    _titulo(ax,
            "O diâmetro de gota escondido dentro do fator K",
            f"{c.nome} · K = {_n(dim.sb.K_ft_s, 3)} ft/s · {_n(c.P_bara, 2)} bara · {c.T_C:.0f} °C",
            tema)

    ax.annotate(f"$v_{{max}}$ de Souders-Brown = {_n(dim.sb.v_max, 2)} m/s",
                xy=(d[0] * 1e6 * 1.3, dim.sb.v_max), xytext=(0, 6),
                textcoords="offset points", color=tema["secundario"], fontsize=9)
    ax.annotate(f"gota implícita no K\n{dim.d_implicito * 1e6:.0f} µm",
                xy=(dim.d_implicito * 1e6, dim.sb.v_max), xytext=(10, -34),
                textcoords="offset points", color=tema["texto"], fontsize=9, fontweight="bold")
    ax.annotate(f"o bocal de entrada, a {dim.bocal_entrada.velocidade:.0f} m/s, não deixa\n"
                f"sobreviver gota acima de {dim.d_max_estavel_bocal * 1e6:.0f} µm  (We > 12)",
                xy=(dim.d_max_estavel_bocal * 1e6 * 1.25, 18.0),
                color=tema["secundario"], fontsize=9, va="top")

    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.02),
              labelcolor=tema["secundario"])
    fig.tight_layout()
    fig.savefig(saida, bbox_inches="tight")
    plt.close(fig)
    return saida


# ---------------------------------------------------------------------------
# Figura 2 - o mesmo K significa fisica diferente em cada pressao
# ---------------------------------------------------------------------------


def figura_efeito_da_pressao(dim: Dimensionamento, saida: Path, tema_nome: str = "claro") -> Path:
    tema = TEMAS[tema_nome]
    _aplica(tema)
    c = dim.corrente
    P = np.linspace(1.2, 45.0, 180)
    chaves = ["gpsa_vertical_com_demister", "succao_de_compressor", "gpsa_vertical_sem_demister"]
    rotulos = ["GPSA vertical c/ demister", "Sucção de compressor", "GPSA vertical s/ demister"]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.0, 7.4), dpi=170, sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1.15], "hspace": 0.16})

    for i, (ch, rot) in enumerate(zip(chaves, rotulos)):
        K = np.array([FATORES_K[ch].K_efetivo_ft_s(p) for p in P])
        a1.plot(P, K, color=tema["series"][i], label=rot)
        d = []
        for p in P:
            rho_g = c.rho_g * (p / c.P_bara)  # gas ideal na mesma T, so para a tendencia
            v = souders_brown(ch, rho_g, c.rho_l, p).v_max
            d.append(diametro_de_gota_implicito(v, rho_g, c.rho_l, c.mu_g) * 1e6)
        a2.plot(P, d, color=tema["series"][i], label=rot)
        a2.annotate(rot, xy=(P[-1], d[-1]), xytext=(6, 0), textcoords="offset points",
                    color=tema["series"][i], fontsize=8.5, va="center")

    a1.set_ylabel("K efetivo  [ft/s]")
    a1.yaxis.set_major_formatter(lambda v, _: _n(v, 2))
    a1.set_ylim(0.098, 0.372)   # folga embaixo para a legenda horizontal
    _limpa(a1, tema)
    _titulo(a1, "O mesmo K não significa a mesma física",
            f"Correção GPSA de K com a pressão, e a gota que cada K realmente remove · "
            f"gás com MM = {c.MM:.0f} kg/kmol a {c.T_C:.0f} °C", tema)
    a1.legend(loc="lower left", labelcolor=tema["secundario"], ncols=3,
              columnspacing=1.6, handlelength=1.6)

    a2.axhline(300, color=tema["secundario"], lw=1.2)
    a2.annotate("300 µm — alvo da API 521", xy=(P[0], 300), xytext=(2, 6),
                textcoords="offset points", color=tema["secundario"], fontsize=8.5)
    a2.set_yscale("log")
    a2.set_xlabel("Pressão de operação  [bara]")
    a2.set_ylabel("Gota implícita no K  [µm]")
    a2.set_xlim(P[0], P[-1] * 1.14)
    _limpa(a2, tema)

    fig.savefig(saida, bbox_inches="tight")
    plt.close(fig)
    return saida


# ---------------------------------------------------------------------------
# Figura 3 - a curva de eficiencia que o metodo classico preve
# ---------------------------------------------------------------------------


def _rosin_rammler_acumulada(d_um: np.ndarray, d_ref_um: float, n: float) -> np.ndarray:
    """F(d) = 1 - exp(-(d/d_ref)^n): fracao VOLUMETRICA acumulada abaixo de d."""
    return 1.0 - np.exp(-((d_um / d_ref_um) ** n))


def figura_eficiencia(
    dim: Dimensionamento,
    saida: Path,
    tema_nome: str = "claro",
    cfd: tuple[np.ndarray, np.ndarray] | None = None,
) -> Path:
    """Painel de cima: eficiencia por tamanho. Painel de baixo: onde esta a massa.

    `cfd` aceita (diametros_um, eficiencia_0a1) para sobrepor o resultado do
    STAR-CCM+ quando ele existir. Ate la a figura mostra so a previsao classica -
    que e, propositalmente, um degrau.
    """
    tema = TEMAS[tema_nome]
    _aplica(tema)
    d = np.logspace(math.log10(5), math.log10(1000), 400)
    c = dim.corrente

    vt = np.array([velocidade_terminal(x * 1e-6, c.rho_g, c.rho_l, c.mu_g).v_t for x in d])
    eta_ideal = (vt >= dim.v_gas).astype(float)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.0, 7.6), dpi=170, sharex=True,
                                 gridspec_kw={"height_ratios": [1.1, 1], "hspace": 0.16})

    a1.plot(d, eta_ideal * 100, color=tema["series"][0],
            label="Previsão clássica (escoamento pistonado)")
    if cfd is not None:
        a1.plot(cfd[0], np.asarray(cfd[1]) * 100, color=tema["series"][1],
                label="CFD — lagrangiano com dispersão turbulenta")
    a1.axvline(dim.d_max_estavel_bocal * 1e6, color=tema["secundario"], lw=1.2)
    a1.annotate(f"limite de Weber do bocal\n{dim.d_max_estavel_bocal * 1e6:.0f} µm",
                xy=(dim.d_max_estavel_bocal * 1e6, 6), xytext=(-8, 0),
                textcoords="offset points", color=tema["secundario"], fontsize=9,
                ha="right", va="bottom")
    a1.annotate(f"degrau em {dim.d_implicito * 1e6:.0f} µm\n(a gota implícita no K)",
                xy=(dim.d_implicito * 1e6, 70), xytext=(12, 0), textcoords="offset points",
                color=tema["texto"], fontsize=9, fontweight="bold", va="center")
    a1.set_ylim(-5, 112)
    a1.set_ylabel("Eficiência de separação  [%]")
    _limpa(a1, tema)
    _titulo(a1, "O método clássico prevê um degrau. A realidade não tem degrau.",
            f"{c.nome} · v superficial = {_n(dim.v_gas, 2)} m/s · vaso Ø{_n(dim.D, 2)} m", tema)
    a1.legend(loc="upper left", labelcolor=tema["secundario"])

    fracoes = []
    for i, (d_ref, n) in enumerate([(40.0, 2.0), (80.0, 2.2), (150.0, 2.4)]):
        F = _rosin_rammler_acumulada(d, d_ref, n)
        a2.plot(d, F * 100, color=tema["series"][i], label=f"d_ref = {d_ref:.0f} µm, n = {_n(n, 1)}")
        fracoes.append(float(_rosin_rammler_acumulada(
            np.array([dim.d_implicito * 1e6]), d_ref, n)[0]) * 100)

    a2.axvline(dim.d_implicito * 1e6, color=tema["secundario"], lw=1.2)
    a2.annotate(
        f"abaixo de {dim.d_implicito * 1e6:.0f} µm está "
        + " / ".join(f"{_n(f, 1)}%" for f in fracoes)
        + "\nda massa de líquido — a conclusão não depende\nda distribuição que se assuma",
        xy=(dim.d_implicito * 1e6, 46), xytext=(-12, 0), textcoords="offset points",
        color=tema["texto"], fontsize=9, ha="right", va="center")
    a2.set_xscale("log")
    a2.set_xlim(d[0], d[-1])
    a2.set_ylim(0, 112)
    a2.set_xlabel("Diâmetro da gota  [µm]")
    a2.set_ylabel("Fração volumétrica\nacumulada de líquido  [%]")
    _limpa(a2, tema)
    a2.legend(loc="upper left", labelcolor=tema["secundario"],
              title="Rosin-Rammler assumida na entrada", title_fontproperties={"size": 9},
              alignment="left")

    fig.savefig(saida, bbox_inches="tight")
    plt.close(fig)
    return saida


# ---------------------------------------------------------------------------
# Figura 4 - comparativo entre servicos
# ---------------------------------------------------------------------------


def figura_comparativo(dims: list[Dimensionamento], saida: Path, tema_nome: str = "claro") -> Path:
    tema = TEMAS[tema_nome]
    _aplica(tema)
    dims = sorted(dims, key=lambda d: d.razao_de_atomizacao, reverse=True)
    nomes = [d.corrente.rotulo or d.corrente.servico.split(",")[0] for d in dims]
    impl = [d.d_implicito * 1e6 for d in dims]
    weber = [d.d_max_estavel_bocal * 1e6 for d in dims]

    y = np.arange(len(dims))
    h = 0.33
    fig, ax = plt.subplots(figsize=(9.6, 1.35 * len(dims) + 2.6), dpi=170)

    ax.barh(y - h / 2 - 0.022, impl, height=h, color=tema["series"][0],
            label="Gota que o dimensionamento promete separar")
    ax.barh(y + h / 2 + 0.022, weber, height=h, color=tema["series"][1],
            label="Maior gota que sobrevive ao bocal de entrada")

    for i, (a, b) in enumerate(zip(impl, weber)):
        ax.annotate(f"{a:.0f} µm", xy=(a, i - h / 2 - 0.012), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9, color=tema["secundario"])
        ax.annotate(f"{b:.0f} µm   ({_n(a / b, 1)}× menor)", xy=(b, i + h / 2 + 0.012),
                    xytext=(6, 0), textcoords="offset points", va="center",
                    fontsize=9, color=tema["secundario"])

    ax.set_yticks(y, nomes, fontsize=9)
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    ax.set_xlabel("Diâmetro da gota  [µm]")
    ax.set_xlim(0, max(impl) * 1.42)
    ax.xaxis.grid(True); ax.yaxis.grid(False)
    _limpa(ax, tema)
    _titulo(ax, "Todo vaso promete separar uma gota que sua própria entrada destrói",
            "Quatro serviços dimensionados pelo método clássico, com os critérios de "
            "ρv² usuais no bocal de entrada", tema)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncols=2,
              labelcolor=tema["secundario"])

    fig.savefig(saida, bbox_inches="tight")
    plt.close(fig)
    return saida
