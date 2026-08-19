#!/usr/bin/env python3
"""
Ponto de operacao e curva de referencia para o caso de cavitacao.

Valvula borboleta Bray 2-Cx DN 100 estrangulada em 30 graus, agua a 20 C.
Pressao a montante fixa, contrapressao varrida. Produz a curva analitica da
IEC 60534-2-1 para sobrepor ao CFD -- e a validacao que o post precisa.

A curva tem duas partes:

    nao estrangulada   Q = Kv * sqrt(dP)
    estrangulada       Q = Kv * F_L * sqrt(p1 - Ff*pv)      (Q para de subir)

A transicao acontece em  dP = F_L^2 * (p1 - Ff*pv).

F_L e o unico parametro desconhecido -- o catalogo nao publica. E ele que o
CFD entrega, e e ele que define a partir de que contrapressao a valvula deixa
de controlar a vazao.
"""

import math

# --- agua a 20 C -------------------------------------------------------------
RHO = 998.2           # [kg/m3]
P_VAP = 2339.0        # [Pa]
P_CRIT = 22.064e6     # [Pa] pressao critica da agua

# --- valvula -----------------------------------------------------------------
ANGULO = 30
KV = 54.0             # [m3/h] catalogo Bray 2-Cx DN 100, 30 graus
D_BORE = 0.100        # [m]

# --- ponto de operacao -------------------------------------------------------
P1_BAR = 5.0          # [bar abs] pressao a montante (recalque tipico de bomba)
P2_SWEEP = [4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0]   # [bar abs]

# F_L candidatos -- o CFD escolhe qual
FL_CANDIDATOS = [0.50, 0.60, 0.70]


def ff():
    """Fator de razao de pressao critica do liquido (IEC 60534-2-1)."""
    return 0.96 - 0.28 * math.sqrt(P_VAP / P_CRIT)


def vazao(p1_bar, p2_bar, fl):
    """Vazao pela IEC 60534-2-1, com estrangulamento. Retorna (Q, estrangulada)."""
    dp = p1_bar - p2_bar
    dp_choke = fl ** 2 * (p1_bar - ff() * P_VAP / 1e5)
    if dp <= dp_choke:
        return KV * math.sqrt(dp), False
    return KV * fl * math.sqrt(p1_bar - ff() * P_VAP / 1e5), True


def sigma(p1_bar, p2_bar):
    """Indice de cavitacao."""
    return (p1_bar * 1e5 - P_VAP) / ((p1_bar - p2_bar) * 1e5)


def main():
    a = math.pi / 4 * D_BORE ** 2

    print("=" * 78)
    print(f"PONTO DE OPERACAO -- BORBOLETA DN 100 a {ANGULO} GRAUS")
    print("=" * 78)
    print(f"  Kv de catalogo             {KV:8.0f} m3/h")
    print(f"  Pressao a montante         {P1_BAR:8.1f} bar abs")
    print(f"  Pressao de vapor (20 C)    {P_VAP/1e5:8.4f} bar abs")
    print(f"  Ff                         {ff():8.4f}")
    print("=" * 78)

    print(f"\n{'p2':>7s}{'dP':>8s}{'sigma':>8s}", end="")
    for fl in FL_CANDIDATOS:
        print(f"{'Q (F_L=' + f'{fl:.2f}' + ')':>18s}", end="")
    print()
    print(f"{'[bar]':>7s}{'[bar]':>8s}{'[-]':>8s}", end="")
    for _ in FL_CANDIDATOS:
        print(f"{'[m3/h]':>18s}", end="")
    print()
    print("-" * 78)

    for p2 in P2_SWEEP:
        dp = P1_BAR - p2
        print(f"{p2:7.1f}{dp:8.1f}{sigma(P1_BAR, p2):8.2f}", end="")
        for fl in FL_CANDIDATOS:
            q, choke = vazao(P1_BAR, p2, fl)
            marca = " *" if choke else "  "
            print(f"{q:16.1f}{marca}", end="")
        print()
    print("-" * 78)
    print("  * = escoamento estrangulado -- baixar mais a contrapressao NAO")
    print("      aumenta a vazao. So aumenta a erosao.")

    print("\n" + "=" * 78)
    print("ONDE ESTA A TRANSICAO")
    print("=" * 78)
    print(f"{'F_L':>6s}{'dP de choke':>14s}{'p2 de choke':>14s}"
          f"{'Q maxima':>12s}{'velocidade':>14s}")
    print(f"{'[-]':>6s}{'[bar]':>14s}{'[bar abs]':>14s}"
          f"{'[m3/h]':>12s}{'no tubo [m/s]':>14s}")
    print("-" * 78)
    for fl in FL_CANDIDATOS:
        dp_c = fl ** 2 * (P1_BAR - ff() * P_VAP / 1e5)
        p2_c = P1_BAR - dp_c
        q_max = KV * fl * math.sqrt(P1_BAR - ff() * P_VAP / 1e5)
        v = q_max / 3600.0 / a
        print(f"{fl:6.2f}{dp_c:14.2f}{p2_c:14.2f}{q_max:12.1f}{v:14.2f}")
    print("-" * 78)
    print("  A faixa de F_L de 0,50 a 0,70 move a vazao maxima em ~40%.")
    print("  E dessa incerteza que o projetista precisa se livrar -- e o")
    print("  catalogo nao ajuda, porque publica Kv e nao publica F_L.")
    print("=" * 78)

    print("\nRODADAS DE CFD SUGERIDAS")
    print("-" * 78)
    print("  Stagnation Inlet fixo em {:.1f} bar abs, Pressure Outlet varrido."
          .format(P1_BAR))
    print("  Uma rodada por linha da tabela acima -- 8 pontos, permanente.")
    print("  A vazao resultante e o eixo y do grafico; o ponto onde ela para")
    print("  de subir da o F_L, que e o entregavel.")
    print("-" * 78)


if __name__ == "__main__":
    main()
