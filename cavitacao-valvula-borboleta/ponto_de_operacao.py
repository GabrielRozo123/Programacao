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

# --- MEDIDO no CFD, rodada 0 (monofasica, permanente) ------------------------
#     p1 = 498 199 Pa   p2 = 400 335 Pa   mdot = 14,446 kg/s   p_min = 321 491 Pa
KV_CFD = 52.67        # [m3/h]  desvio de -2,5% contra o catalogo
FL_CFD = 0.744        # [-]     F_L^2 = dP/(p1 - p_min)

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

    # pontos concentrados no joelho
    pontos = [4.5, 4.0, 3.5, 3.0, 2.6, 2.4, 2.25, 2.1, 1.9, 1.6, 1.2]

    print("\n" + "=" * 76)
    print("PONTOS DA VARREDURA")
    print("=" * 76)
    print(f"{'#':>3s}{'p2':>8s}{'dP':>8s}{'sigma':>8s}{'Q prevista':>13s}"
          f"{'mdot':>11s}{'regime':>16s}")
    print(f"{'':>3s}{'[bar]':>8s}{'[bar]':>8s}{'[-]':>8s}{'[m3/h]':>13s}"
          f"{'[kg/s]':>11s}")
    print("-" * 76)
    for i, p2 in enumerate(pontos):
        q, choke = vazao(P1_BAR, p2, KV_CFD, FL_CFD)
        mdot = q / 3600.0 * RHO
        s = sigma(P1_BAR, p2)
        if choke:
            reg = "ESTRANGULADO"
        elif s < 2.0:
            reg = "cavitacao forte"
        elif s < 3.5:
            reg = "cavitacao"
        else:
            reg = "sem cavitacao"
        marca = "  <-- joelho" if abs(p2 - p2c) < 0.15 else ""
        print(f"{i:3d}{p2:8.2f}{P1_BAR-p2:8.2f}{s:8.2f}{q:13.1f}"
              f"{mdot:11.3f}{reg:>16s}{marca}")
    print("-" * 76)
    print("  Rodada 0 (p2 = 4,0) ja executada em monofasico: 14,446 kg/s.")
    print("  A rodada 1 repete p2 = 4,0 COM o modelo de cavitacao ligado e")
    print("  tem que devolver o mesmo numero -- e a verificacao do setup.")
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
