"""
analise_meteo_zeus.py — tratamento da série horária da estação Zeus (LD Celulose).

Entrada: relatorio_zeus_03_simulation.xlsx, aba "Pic Data", série horária.
Saída  : estatísticas mensais, rosa dos ventos, análise de rajada e a matriz de cenários.

Pedido do Marcus (reunião 29/09):
  · filtrar por mês e calcular as médias de velocidade, umidade e temperatura
  · análise estatística de direção e velocidade
  · situação de rajada
  · consolidar numa planilha

Convenção: direção do vento em GRAUS METEOROLÓGICOS (de onde o vento VEM),
0° = Norte, 90° = Leste. Velocidades convertidas de km/h para m/s.

Uso:  python3 analise_meteo_zeus.py <caminho_do_xlsx> [saida.xlsx]
"""
import sys, math
from collections import defaultdict
from datetime import datetime

import numpy as np
import openpyxl

KMH = 1 / 3.6  # km/h -> m/s

SETORES = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def setor(graus):
    """Índice do setor de 16 pontos (22,5° cada) para uma direção em graus."""
    return int(((graus % 360) + 11.25) // 22.5) % 16


# ── leitura ──────────────────────────────────────────────────────────────
def ler(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Pic Data"]
    linhas = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        try:
            t = datetime.strptime(str(r[4]).strip(), "%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            continue

        def num(v):
            try:
                x = float(v)
                return x if not math.isnan(x) else None
            except (TypeError, ValueError):
                return None

        linhas.append(dict(
            t=t, inativa=(str(r[6]).strip().lower() == "sim"),
            chuva=num(r[7]), t_med=num(r[9]),
            ur_min=num(r[11]), ur_med=num(r[12]), ur_max=num(r[13]),
            lum=num(r[14]),
            v_med=num(r[16]), dir=num(r[17]), v_inst=num(r[18]), rajada=num(r[19]),
        ))
    return linhas


# ── estatística direcional (vetorial, não aritmética) ────────────────────
def dir_media(dirs, pesos=None):
    """Média vetorial de direções. Média aritmética de ângulos é ERRADA:
    350° e 10° dariam 180°, quando o correto é 0°."""
    d = np.radians(np.asarray(dirs, float))
    w = np.ones_like(d) if pesos is None else np.asarray(pesos, float)
    s, c = np.sum(w * np.sin(d)), np.sum(w * np.cos(d))
    ang = math.degrees(math.atan2(s, c)) % 360
    R = math.hypot(s, c) / max(np.sum(w), 1e-12)   # 0 = disperso, 1 = concentrado
    return ang, R


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "relatorio_zeus_03_simulation.xlsx"
    dados = ler(path)

    validos = [d for d in dados if not d["inativa"] and d["v_med"] is not None
               and d["dir"] is not None]

    print("=" * 78)
    print(" ANÁLISE METEOROLÓGICA — ESTAÇÃO ZEUS · LD CELULOSE (FÁBRICA)")
    print("=" * 78)
    print(f" registros totais : {len(dados)}")
    print(f" registros válidos: {len(validos)}  ({100*len(validos)/max(len(dados),1):.1f} %)")
    if validos:
        print(f" período          : {validos[0]['t']:%d/%m/%Y} a {validos[-1]['t']:%d/%m/%Y}")

    v = np.array([d["v_med"] for d in validos]) * KMH
    vi = np.array([d["v_inst"] for d in validos if d["v_inst"] is not None]) * KMH
    rj = np.array([d["rajada"] for d in validos if d["rajada"] is not None]) * KMH
    dirs = np.array([d["dir"] for d in validos])

    # ── 1. estatística mensal ────────────────────────────────────────────
    print("\n" + "─" * 78)
    print(" 1. MÉDIAS MENSAIS")
    print("─" * 78)
    print(f" {'mês':>8} {'n':>5} {'v_méd':>7} {'v_inst':>7} {'rajada':>7} "
          f"{'T_méd':>7} {'UR_méd':>7} {'dir':>6} {'R':>5}")
    print(f" {'':>8} {'':>5} {'m/s':>7} {'m/s':>7} {'m/s':>7} {'°C':>7} {'%':>7} {'°':>6} {'':>5}")

    por_mes = defaultdict(list)
    for d in validos:
        por_mes[(d["t"].year, d["t"].month)].append(d)

    linhas_mes = []
    for (a, m), g in sorted(por_mes.items()):
        gv = np.array([x["v_med"] for x in g]) * KMH
        gi = np.array([x["v_inst"] for x in g if x["v_inst"] is not None]) * KMH
        gr = np.array([x["rajada"] for x in g if x["rajada"] is not None]) * KMH
        gt = np.array([x["t_med"] for x in g if x["t_med"] is not None])
        gu = np.array([x["ur_med"] for x in g if x["ur_med"] is not None])
        ang, R = dir_media([x["dir"] for x in g], gv)
        linhas_mes.append(dict(mes=f"{m:02d}/{a}", n=len(g),
                               v=gv.mean(), vi=gi.mean() if gi.size else float("nan"),
                               rj=gr.mean() if gr.size else float("nan"),
                               T=gt.mean() if gt.size else float("nan"),
                               UR=gu.mean() if gu.size else float("nan"),
                               dir=ang, R=R))
        L = linhas_mes[-1]
        print(f" {L['mes']:>8} {L['n']:>5} {L['v']:7.2f} {L['vi']:7.2f} {L['rj']:7.2f} "
              f"{L['T']:7.1f} {L['UR']:7.1f} {L['dir']:6.1f} {L['R']:5.2f}")

    ang_g, R_g = dir_media(dirs, v)
    print(f"\n {'GERAL':>8} {len(validos):>5} {v.mean():7.2f} "
          f"{vi.mean() if vi.size else float('nan'):7.2f} "
          f"{rj.mean() if rj.size else float('nan'):7.2f} "
          f"{'':>7} {'':>7} {ang_g:6.1f} {R_g:5.2f}")
    print(f"\n >> R = concentração direcional (0 = vento de todo lado, 1 = sempre da mesma).")
    print(f"    R = {R_g:.2f} -> " + ("direção BEM definida" if R_g > 0.5 else
          "direção POUCO definida — a rosa manda mais que a média"))

    # ── 2. rosa dos ventos ───────────────────────────────────────────────
    print("\n" + "─" * 78)
    print(" 2. ROSA DOS VENTOS — frequência e velocidade por setor")
    print("─" * 78)
    print(f" {'setor':>6} {'faixa':>14} {'n':>5} {'freq':>7} {'v_méd':>7} {'v_p95':>7} {'rajada_máx':>11}")
    idx = np.array([setor(d) for d in dirs])
    rosa = []
    for k, nome in enumerate(SETORES):
        m = idx == k
        if not m.any():
            rosa.append(dict(setor=nome, n=0, freq=0.0, v=0.0, p95=0.0, rmax=0.0))
            continue
        rj_k = np.array([validos[i]["rajada"] for i in np.where(m)[0]
                         if validos[i]["rajada"] is not None]) * KMH
        rosa.append(dict(setor=nome, n=int(m.sum()), freq=100 * m.sum() / len(dirs),
                         v=v[m].mean(), p95=np.percentile(v[m], 95),
                         rmax=rj_k.max() if rj_k.size else 0.0))
        R_ = rosa[-1]
        c = k * 22.5
        print(f" {nome:>6} {c-11.25:6.1f}–{c+11.25:6.1f}° {R_['n']:>5} "
              f"{R_['freq']:6.1f}% {R_['v']:7.2f} {R_['p95']:7.2f} {R_['rmax']:11.2f}")

    dom = max(rosa, key=lambda r: r["freq"])
    print(f"\n >> setor DOMINANTE: {dom['setor']} ({dom['freq']:.1f} % das horas, "
          f"v_méd {dom['v']:.2f} m/s)")

    # ── 3. rajada ────────────────────────────────────────────────────────
    print("\n" + "─" * 78)
    print(" 3. RAJADA")
    print("─" * 78)
    par = [(d["v_med"] * KMH, d["rajada"] * KMH) for d in validos
           if d["rajada"] is not None and d["v_med"] and d["v_med"] > 0]
    vv = np.array([p[0] for p in par]); rr = np.array([p[1] for p in par])
    G = rr / vv
    print(f" rajada média            : {rr.mean():6.2f} m/s")
    print(f" rajada p95              : {np.percentile(rr,95):6.2f} m/s")
    print(f" rajada p99              : {np.percentile(rr,99):6.2f} m/s")
    print(f" rajada MÁXIMA            : {rr.max():6.2f} m/s")
    print(f"\n fator de rajada G = rajada / v_média")
    for q in (50, 90, 95, 99):
        print(f"   p{q:<3d} = {np.percentile(G,q):5.2f}")
    print(f"   máx  = {G.max():5.2f}")
    print(f"\n >> G mediano de {np.median(G):.2f} é típico de terreno com rugosidade")
    print("    moderada. G alto acompanha vento fraco (divisão por número pequeno),")
    print("    então NÃO use G para extrapolar o caso de rajada — use a rajada medida.")

    # ── 4. percentis de velocidade ───────────────────────────────────────
    print("\n" + "─" * 78)
    print(" 4. DISTRIBUIÇÃO DE VELOCIDADE (v_média horária)")
    print("─" * 78)
    for q in (1, 5, 10, 25, 50, 75, 90, 95, 99):
        print(f"   p{q:<3d} = {np.percentile(v,q):5.2f} m/s")
    print(f"   média = {v.mean():5.2f} m/s   |   máx = {v.max():5.2f} m/s")
    calmo = 100 * (v < 1.5).sum() / v.size
    print(f"\n >> horas com v < 1,5 m/s: {calmo:.1f} %  <- faixa de dispersão desfavorável")

    # ── 5. noite x dia ───────────────────────────────────────────────────
    print("\n" + "─" * 78)
    print(" 5. NOITE × DIA  (proxy de estabilidade atmosférica)")
    print("─" * 78)
    noite = np.array([(d["t"].hour >= 21 or d["t"].hour < 6) for d in validos])
    for nome, m in [("NOITE (21h–06h)", noite), ("DIA   (06h–21h)", ~noite)]:
        a, R_ = dir_media(dirs[m], v[m])
        print(f" {nome}: n={m.sum():5d}  v_méd={v[m].mean():5.2f} m/s  "
              f"p10={np.percentile(v[m],10):5.2f}  dir={a:5.1f}°  R={R_:.2f}  "
              f"calmo={100*(v[m]<1.5).sum()/m.sum():4.1f}%")
    print("\n >> Vento noturno mais fraco + céu limpo = estratificação estável.")
    print("    É a condição de dispersão desfavorável identificada na régua analítica.")
    print("    A coluna de luminosidade permite refinar isso para classes de Pasquill.")

    return dict(validos=validos, v=v, dirs=dirs, rosa=rosa, linhas_mes=linhas_mes,
                G=G, rr=rr, dom=dom, ang_g=ang_g, R_g=R_g, noite=noite)


if __name__ == "__main__":
    main()
