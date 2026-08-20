#!/usr/bin/env python3
"""
Ponto de operacao e varredura de contrapressao para o caso de cavitacao.

Valvula borboleta Bray 2-Cx DN 100 estrangulada em 30 graus, agua a 20 C.
Pressao a montante fixa, contrapressao varrida. Produz a curva de referencia
da IEC 60534-2-1 para sobrepor ao CFD -- e o grafico do post.

A curva tem duas partes:

    nao estrangulada   Q = Kv * sqrt(dP)
    estrangulada       Q = Kv * F_L * sqrt(p1 - Ff*pv)      (Q para de subir)

com transicao em  dP = F_L^2 * (p1 - Ff*pv).

ESTRUTURA DO ESTUDO -- previsao e depois verificacao:

  1. A rodada monofasica em p2 = 4,0 bar mediu Kv e F_L. Dai sai a PREVISAO
     de onde a vazao para de subir.
  2. A varredura multifasica TESTA essa previsao: o ponto onde Q achata na
     curva simulada tem que bater com o joelho previsto.

Sao dois caminhos independentes para o mesmo numero. Se fecharem, o resultado
se sustenta sozinho.
"""

import math

# --- agua a 20 C -------------------------------------------------------------
RHO = 998.2           # [kg/m3]
P_VAP = 2339.0        # [Pa]
P_CRIT = 22.064e6     # [Pa] pressao critica da agua

# --- valvula -----------------------------------------------------------------
ANGULO = 30
D_BORE = 0.100        # [m]
KV_CATALOGO = 54.0    # [m3/h] catalogo Bray 2-Cx DN 100, 30 graus

# --- MEDIDO no CFD -----------------------------------------------------------
# Pontos ja executados. VOF + Schnerr-Sauer, implicit unsteady, ~0,8 s de tempo
# fisico por ponto (uma travessia do dominio e L/V = 0,815 s).
#
#   p2 [Pa]    p1 [Pa]    mdot [kg/s]   p_min [Pa]
MEDIDO = [
    (400151.0, 498131.0, 14.51478, 302144.0),
    (350180.0, 497217.0, 17.81159, 202047.0),
    (300290.0, 496294.0, 20.57648, 102870.0),
    (280296.0, 495921.0, 21.58146,  63242.0),
    (260328.0, 495548.0, 22.54474,  23454.0),
]

# A rodada monofasica permanente em p2 = 4,0 bar deu mdot = 14,446 kg/s e
# p_min = 321 491 Pa -- a multifasica reproduz a vazao em 0,5% e o dP em 0,12%,
# o que verifica a montagem. O p_min difere 6% porque e um extremo de uma unica
# celula, que passeia com a turbulencia mesmo depois das medias travarem.

KV_CFD = 52.97        # [m3/h]  media dos dois pontos; -1,9% contra o catalogo
FL_CFD = 0.706        # [-]     F_L^2 = dP/(p1 - p_min); os dois pontos dao
                      #         0,707 e 0,706 -- concordancia de 0,1%

# queda de pressao de estagnacao ate a sonda p1, ajustada aos dois pontos:
#     p1_estatica = P1_BAR*1e5 - K_P1 * mdot^2
K_P1 = 8.87           # [Pa/(kg/s)^2]

# --- ponto de operacao -------------------------------------------------------
P1_BAR = 5.0          # [bar abs] montante (Stagnation Inlet)


def ff():
    """Fator de razao de pressao critica do liquido (IEC 60534-2-1)."""
    return 0.96 - 0.28 * math.sqrt(P_VAP / P_CRIT)


def dp_choke(p1_bar, fl):
    return fl ** 2 * (p1_bar - ff() * P_VAP / 1e5)


def vazao(p1_bar, p2_bar, kv, fl):
    """Vazao pela IEC 60534-2-1. Retorna (Q, estrangulada)."""
    dp = p1_bar - p2_bar
    dpc = dp_choke(p1_bar, fl)
    if dp <= dpc:
        return kv * math.sqrt(dp), False
    return kv * fl * math.sqrt(p1_bar - ff() * P_VAP / 1e5), True


def sigma(p1_bar, p2_bar):
    return (p1_bar * 1e5 - P_VAP) / ((p1_bar - p2_bar) * 1e5)


def main():
    a = math.pi / 4 * D_BORE ** 2
    dpc = dp_choke(P1_BAR, FL_CFD)
    p2c = P1_BAR - dpc
    q_max = KV_CFD * FL_CFD * math.sqrt(P1_BAR - ff() * P_VAP / 1e5)

    print("=" * 76)
    print(f"VARREDURA DE CONTRAPRESSAO -- BORBOLETA DN 100 a {ANGULO} GRAUS")
    print("=" * 76)
    print(f"  Kv de catalogo             {KV_CATALOGO:8.1f} m3/h")
    print(f"  Kv medido no CFD           {KV_CFD:8.2f} m3/h   "
          f"({100*(KV_CFD/KV_CATALOGO-1):+.1f}%)")
    print(f"  F_L medido no CFD          {FL_CFD:8.3f}        nao publicado")
    print(f"  Pressao a montante         {P1_BAR:8.1f} bar abs")
    print(f"  Pressao de vapor (20 C)    {P_VAP/1e5:8.4f} bar abs")
    print("=" * 76)
    print("\nPREVISAO A TESTAR")
    print("-" * 76)
    print(f"  dP de estrangulamento      {dpc:8.2f} bar")
    print(f"  p2 do joelho               {p2c:8.2f} bar abs")
    print(f"  vazao maxima               {q_max:8.1f} m3/h   "
          f"({q_max/3600/a:.2f} m/s no tubo)")
    print("-" * 76)
    print("  Abaixo dessa contrapressao, baixar mais NAO aumenta a vazao.")
    print("  So aumenta a erosao. E o que a varredura tem que reproduzir.")

    # --- conferencia dos pontos ja medidos ---------------------------------
    print("\n" + "=" * 76)
    print("PONTOS MEDIDOS")
    print("=" * 76)
    print(f"{'p2':>9s}{'dP':>10s}{'mdot':>10s}{'Q':>9s}{'Kv':>8s}"
          f"{'p_min':>10s}{'F_L':>8s}{'sigma':>8s}")
    print(f"{'[bar]':>9s}{'[bar]':>10s}{'[kg/s]':>10s}{'[m3/h]':>9s}"
          f"{'[m3/h]':>8s}{'[Pa]':>10s}{'[-]':>8s}{'[-]':>8s}")
    print("-" * 76)
    for p2, p1, mdot, pmin in MEDIDO:
        dp = p1 - p2
        q = mdot / RHO * 3600.0
        kv = q / math.sqrt(dp / 1e5)
        fl = math.sqrt(dp / (p1 - pmin))
        s = (p1 - P_VAP) / dp
        print(f"{p2/1e5:9.2f}{dp/1e5:10.3f}{mdot:10.3f}{q:9.2f}{kv:8.2f}"
              f"{pmin:10.0f}{fl:8.3f}{s:8.2f}")
    print("-" * 76)
    print("  Kv e F_L constantes entre os pontos: a valvula se comporta como a")
    print("  IEC 60534 preve no regime nao cavitante. E o que autoriza")
    print("  extrapolar para o joelho.")

    # --- previsao dos pontos restantes -------------------------------------
    pontos = [2.5, 2.4, 2.2, 1.8, 1.4]

    print("\n" + "=" * 76)
    print("PONTOS A RODAR -- PREVISAO A TESTAR")
    print("=" * 76)
    print(f"{'p2':>8s}{'p1':>10s}{'dP':>9s}{'sigma':>8s}{'Q':>9s}"
          f"{'mdot':>10s}{'p_min':>11s}{'regime':>15s}")
    print(f"{'[bar]':>8s}{'[Pa]':>10s}{'[bar]':>9s}{'[-]':>8s}{'[m3/h]':>9s}"
          f"{'[kg/s]':>10s}{'[Pa]':>11s}")
    print("-" * 76)
    for p2 in pontos:
        # p1 estatica depende da vazao; itera
        mdot = 20.0
        for _ in range(40):
            p1 = P1_BAR * 1e5 - K_P1 * mdot ** 2
            q, choke = vazao(p1 / 1e5, p2, KV_CFD, FL_CFD)
            mdot = q / 3600.0 * RHO
        dp = p1 - p2 * 1e5
        pmin = p1 - dp / FL_CFD ** 2
        s = (p1 - P_VAP) / dp
        if choke:
            reg, pmin_txt = "ESTRANGULADO", "~2339"
        else:
            reg = "cavitacao" if pmin < 5e4 else "sem cavitacao"
            pmin_txt = f"{pmin:.0f}"
        marca = "  <-- joelho" if abs(p2 - p2c) < 0.11 else ""
        print(f"{p2:8.2f}{p1:10.0f}{dp/1e5:9.3f}{s:8.2f}{q:9.2f}"
              f"{mdot:10.3f}{pmin_txt:>11s}{reg:>15s}{marca}")
    print("-" * 76)
    print("  Toda a acao esta entre 2,8 e 2,2 bar. Abaixo de 2,0 nada mais")
    print("  muda -- dois pontos ali bastam para provar o plato.")
    print("  O vapor deve aparecer ANTES do p_min medio cruzar 2339 Pa: o RANS")
    print("  entrega a media, e a incipiencia nasce das flutuacoes.")
    print("=" * 76)

    print("\nO QUE REGISTRAR EM CADA PONTO")
    print("-" * 76)
    for item in ("mdot no Outlet                    [kg/s]",
                 "p1  Surface Average, 2D montante  [Pa]",
                 "p2  Surface Average, 6D jusante   [Pa]",
                 "p_min  Volume Minimum             [Pa]",
                 "volume de vapor  Volume Integral da fracao de vapor  [m3]",
                 "fracao de vapor maxima            [-]"):
        print(f"    {item}")
    print("-" * 76)


if __name__ == "__main__":
    main()
