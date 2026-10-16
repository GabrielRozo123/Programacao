"""Gráficos do pré-dimensionamento (matplotlib). Importação preguiçosa: o núcleo de cálculo não
depende de matplotlib, o que facilita rodar a rotina dentro do ambiente Python do Amesim."""
from __future__ import annotations

import numpy as np

# paleta categórica de referência (ordem fixa) e tokens de texto/superfície
AZUL, LARANJA, VERDE_AGUA, AMARELO = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
TEXTO, TEXTO_2, GRADE, SUPERFICIE, DOMO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#a3a29c"


def _estilo():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "axes.edgecolor": GRADE,
        "axes.labelcolor": TEXTO_2, "axes.titlecolor": TEXTO, "axes.titlesize": 11, "axes.labelsize": 9,
        "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
        "legend.frameon": False, "legend.fontsize": 8, "font.size": 9,
    })
    return plt


def _domo(fl, n=120, Tmin=None):
    Tmin = max(fl.Ttriplo + 5, 200.0) if Tmin is None else Tmin
    Ts = np.linspace(Tmin, fl.Tc - 0.5, n)
    Ps = [fl.Psat(T) for T in Ts]
    sats = [fl.sat(P) for P in Ps]
    return Ts, np.array(Ps), sats


def _caminho_ciclo(res, fl):
    """Pontos do ciclo com as trajetórias intermediárias (condensação, evaporação) para P-h/T-s."""
    e = res.ciclo.estados
    pts = [e["1s"], e["2"]]
    for s in res.condensador.segmentos:
        pts.append(fl.estado_PH(s.P_out, s.h_out))
    pts += [e["3"], e["3i"], e["4"]]
    for s in res.evaporador.segmentos:
        pts.append(fl.estado_PH(s.P_out, s.h_out))
    pts += [e["1"], e["1s"]]
    return pts


def diagrama_ph(res, ax=None):
    from .propriedades import Fluido
    plt = _estilo()
    fl = Fluido(res.ciclo.fluido)
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.5))
    _, Ps, sats = _domo(fl, Tmin=res.ciclo.T_evap - 30.0)
    ax.plot([s.hl / 1e3 for s in sats], Ps / 1e5, color=DOMO, lw=1.2)
    ax.plot([s.hv / 1e3 for s in sats], Ps / 1e5, color=DOMO, lw=1.2, label="saturação")
    pts = _caminho_ciclo(res, fl)
    ax.plot([p.h / 1e3 for p in pts], [p.P / 1e5 for p in pts], color=AZUL, label=f"ciclo {fl.nome}")
    e = res.ciclo.estados
    for k in ("1", "2", "3", "4"):
        ax.plot(e[k].h / 1e3, e[k].P / 1e5, "o", ms=8, color=AZUL, mec=SUPERFICIE, mew=2)
        ax.annotate(k, (e[k].h / 1e3, e[k].P / 1e5), textcoords="offset points", xytext=(6, 6),
                    color=TEXTO, fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("entalpia h [kJ/kg]")
    ax.set_ylabel("pressão P [bar]")
    ax.set_title("Diagrama P-h")
    ax.legend(loc="lower right")
    return ax


def diagrama_ts(res, ax=None):
    from .propriedades import Fluido
    plt = _estilo()
    fl = Fluido(res.ciclo.fluido)
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.5))
    Ts, _, sats = _domo(fl, Tmin=res.ciclo.T_evap - 30.0)
    ax.plot([s.sl / 1e3 for s in sats], Ts - 273.15, color=DOMO, lw=1.2)
    ax.plot([s.sv / 1e3 for s in sats], Ts - 273.15, color=DOMO, lw=1.2, label="saturação")
    pts = _caminho_ciclo(res, fl)
    ax.plot([p.s / 1e3 for p in pts], [p.T - 273.15 for p in pts], color=AZUL, label=f"ciclo {fl.nome}")
    e = res.ciclo.estados
    for k in ("1", "2", "3", "4"):
        ax.plot(e[k].s / 1e3, e[k].T - 273.15, "o", ms=8, color=AZUL, mec=SUPERFICIE, mew=2)
        ax.annotate(k, (e[k].s / 1e3, e[k].T - 273.15), textcoords="offset points", xytext=(6, 6), color=TEXTO)
    ax.set_xlabel("entropia s [kJ/kg·K]")
    ax.set_ylabel("temperatura [°C]")
    ax.set_title("Diagrama T-s")
    ax.legend(loc="upper left")
    return ax


def perfil_trocador(r):
    """Dois painéis: temperaturas (refrigerante e ar de saída do trecho) e coeficiente interno."""
    plt = _estilo()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7, 5.5), sharex=True)
    L = np.cumsum([s.L for s in r.segmentos])
    a1.plot(L, [s.T_out - 273.15 for s in r.segmentos], color=AZUL, label="refrigerante")
    a1.plot(L, [s.T_ar_out - 273.15 for s in r.segmentos], color=LARANJA, label="ar na saída do trecho")
    a1.axhline(r.T_ar_in - 273.15, color=TEXTO_2, lw=0.8)
    a1.annotate("ar na entrada", (L[-1], r.T_ar_in - 273.15), textcoords="offset points", xytext=(-4, 4),
                ha="right", color=TEXTO_2, fontsize=8)
    a1.set_ylabel("temperatura [°C]")
    a1.set_title(f"{r.tipo.capitalize()}: perfil ao longo do circuito")
    a1.legend(loc="best")
    a2.plot(L, [s.h_int for s in r.segmentos], color=AZUL)
    a2.set_ylabel("h interno [W/m²K]")
    a2.set_xlabel("comprimento de tubo por circuito [m]")
    z0 = 0.0
    for z, v in r.zonas.items():
        z1 = z0 + v["L"] / r.n_circuitos
        a2.axvline(z1, color=GRADE, lw=1.0)
        a2.annotate(z, ((z0 + z1) / 2, a2.get_ylim()[1]), ha="center", va="top", color=TEXTO_2, fontsize=8)
        z0 = z1
    fig.tight_layout()
    return fig


def perfil_capilar(res):
    plt = _estilo()
    c = res.capilar.escolhido
    pf = c.perfil
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
    a1.plot(pf["L"], np.array(pf["P"]) / 1e5, color=AZUL)
    a1.axhline(res.ciclo.estados["4"].P / 1e5, color=TEXTO_2, lw=0.8)
    a1.annotate("P entrada do evaporador", (pf["L"][-1], res.ciclo.estados["4"].P / 1e5),
                textcoords="offset points", xytext=(-4, 4), ha="right", color=TEXTO_2, fontsize=8)
    a1.set_ylabel("pressão [bar]")
    a1.set_title(f"Capilar Ø{c.D * 1e3:.3f} mm × {c.L:.2f} m ({'blocado' if c.blocado else 'não blocado'})")
    a2.plot(pf["L"], pf["x"], color=AZUL)
    a2.set_ylabel("título x")
    a2.set_xlabel("posição [m]")
    fig.tight_layout()
    return fig


def barras(dados: dict, titulo: str, unidade: str):
    """Barras horizontais de uma única série (cor única), ordenadas, com rótulo de valor."""
    plt = _estilo()
    itens = sorted(dados.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(itens) + 1.2))
    y = np.arange(len(itens))
    vals = [v for _, v in itens]
    ax.barh(y, vals, height=0.6, color=AZUL)
    ax.set_yticks(y, [k for k, _ in itens])
    for yi, v in zip(y, vals):
        ax.annotate(f"{v:.1f}", (v, yi), textcoords="offset points", xytext=(4, 0), va="center",
                    color=TEXTO, fontsize=8)
    ax.set_xlabel(unidade)
    ax.set_title(titulo)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def mapa_cop(fluido: str, T_alvo_C: float, T_amb_C: np.ndarray, p_ciclo=None, etas=(0.70, 0.55),
             cop_pedido=None):
    """COP alcançável em função da temperatura ambiente, com as diferenças de temperatura de
    projeto dos trocadores: ciclo ideal (compressão isentrópica) e compressores com η_global dado."""
    from .ciclo import ParametrosCiclo, resolver_ciclo
    from .propriedades import Fluido
    plt = _estilo()
    fl = Fluido(fluido)
    pc = p_ciclo or ParametrosCiclo()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ideal, por_eta = [], {e: [] for e in etas}
    for Ta in T_amb_C:
        Te = T_alvo_C + 273.15 + pc.dT_retorno_evap - pc.dT_evap
        Tc = Ta + 273.15 + pc.dT_recirculacao_cond + pc.dT_cond
        c = resolver_ciclo(fl, Te, Tc, pc, None)
        ideal.append(c.COP_ciclo_ideal)
        for e in etas:
            por_eta[e].append(e * c.COP_ciclo_ideal)
    ax.plot(T_amb_C, ideal, color=AZUL, label="ciclo ideal (compressão isentrópica)")
    for cor, e in zip((LARANJA, VERDE_AGUA), etas):
        ax.plot(T_amb_C, por_eta[e], color=cor, label=f"compressor com η_global = {e:.2f}")
    if cop_pedido is not None:
        ax.axhline(cop_pedido, color=TEXTO_2, lw=0.8)
        ax.annotate(f"COP pedido = {cop_pedido:.2f}", (T_amb_C[0], cop_pedido), textcoords="offset points",
                    xytext=(2, 4), color=TEXTO_2, fontsize=8)
    ax.set_xlabel("temperatura ambiente [°C]")
    ax.set_ylabel("COP [W/W]")
    ax.set_title(f"COP alcançável — {fluido}, T_alvo {T_alvo_C:.1f} °C, ΔT_evap {pc.dT_evap:g} K, "
                 f"ΔT_cond {pc.dT_cond:g} K", fontsize=10)
    ax.legend(loc="upper right")
    fig.tight_layout()
    return fig


def _rotulos_fim(ax, x, itens, sep_frac=0.06):
    """Rótulos diretos no fim das curvas, afastados verticalmente para não se sobreporem."""
    y0, y1 = ax.get_ylim()
    sep = sep_frac * (y1 - y0)
    ordem = sorted(itens, key=lambda it: it[0])
    ys = [y for y, _ in ordem]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + sep)
    for (_, nome), y in zip(ordem, ys):
        ax.annotate(nome, (x, y), textcoords="offset points", xytext=(6, 0), va="center", color=TEXTO_2, fontsize=8,
                    annotation_clip=False)


def pulldown(res):
    """Pull-down estimado (porta fechada): temperaturas e potência do compressor ao longo do tempo."""
    pd = res.pulldown
    if pd is None:
        return None
    plt = _estilo()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.3))
    th = pd.t / 3600.0
    T_alvo = pd.T_alvo - 273.15
    curvas = ((pd.T_produto, AZUL, "produto"), (pd.T_ar, LARANJA, "ar interno"),
              (pd.T_evap, VERDE_AGUA, "evaporação"))
    for y, cor, nome in curvas:
        a1.plot(th, y - 273.15, color=cor, label=nome)
    a1.hlines(T_alvo, 0.0, th[-1], color=TEXTO_2, lw=0.8, ls="--")
    a1.annotate(f"alvo {T_alvo:.1f} °C", (0.55 * th[-1], T_alvo), textcoords="offset points", xytext=(0, 4),
                ha="center", color=TEXTO_2, fontsize=8)
    a1.set_xlabel("tempo [h]")
    a1.set_ylabel("temperatura [°C]")
    fim = f"{pd.tempo_h:.1f} h até {T_alvo:.1f} °C" if pd.concluido else "não atinge o alvo"
    a1.set_title(f"Pull-down estimado (porta fechada): {fim}")
    a1.legend(loc="upper right")
    a1.set_xlim(0.0, th[-1] * 1.14)
    _rotulos_fim(a1, th[-1], [(y[-1] - 273.15, nome) for y, _, nome in curvas])

    a2.plot(th, pd.Q_evap, color=AZUL, label="capacidade frigorífica")
    a2.plot(th, pd.W_el, color=LARANJA, label="potência elétrica do compressor")
    a2.plot(pd.t_pico_s / 3600.0, pd.W_pico, "o", ms=8, color=LARANJA, mec=SUPERFICIE, mew=2, clip_on=False,
            zorder=5)
    a2.annotate(f"pico {pd.W_pico:.0f} W" + (" (partida)" if pd.pico_na_partida else ""),
                (pd.t_pico_s / 3600.0, pd.W_pico), textcoords="offset points", xytext=(8, 6), color=TEXTO, fontsize=8)
    lim = (res.potencia or {}).get("limite_W")
    a2.set_ylim(0.0, max(float(np.max(pd.Q_evap)), lim or 0.0) * 1.12)
    if lim:
        a2.hlines(lim, 0.0, th[-1], color=TEXTO_2, lw=1.0, ls="--")
        # rótulo no meio do eixo, do lado da linha em que a curva de potência não passa
        x_rot = 0.5 * th[-1]
        acima = float(np.interp(x_rot, th, pd.W_el)) < lim
        a2.annotate(f"limite {lim:.0f} W", (x_rot, lim), textcoords="offset points", xytext=(0, 4 if acima else -10),
                    ha="center", color=TEXTO_2, fontsize=8)
    a2.set_xlabel("tempo [h]")
    a2.set_ylabel("potência [W]")
    a2.set_xlim(0.0, th[-1] * 1.16)
    a2.set_title(f"Compressor no pull-down: regime de projeto {res.balanco.W_el:.0f} W, pico {pd.W_pico:.0f} W")
    a2.legend(loc="upper right")
    _rotulos_fim(a2, th[-1], [(pd.Q_evap[-1], "capacidade"), (pd.W_el[-1], "potência")])
    fig.tight_layout()
    return fig


def painel(res):
    """Gera todas as figuras principais e devolve um dicionário nome -> Figure."""
    plt = _estilo()
    figs = {}
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.5))
    diagrama_ph(res, a)
    diagrama_ts(res, b)
    fig.tight_layout()
    figs["ciclo"] = fig
    figs["carga"] = barras(res.carga.componentes, "Componentes da carga térmica", "W")
    figs["condensador"] = perfil_trocador(res.condensador)
    figs["evaporador"] = perfil_trocador(res.evaporador)
    figs["capilar"] = perfil_capilar(res)
    figs["exergia"] = barras(res.exergia["destruicao_W"], "Destruição de exergia por componente", "W")
    if getattr(res, "pulldown", None) is not None:
        figs["pulldown"] = pulldown(res)
    return figs
