#!/usr/bin/env python3
"""
Estimativa de tamanho de malha para o caso de incendio em parque de tanques.

Dimensiona os controles volumetricos a partir do diametro caracteristico de
fogo D* e estima a contagem de celulas de cada zona de refino.

Criterio de resolucao: D*/dx entre 4 (grosseiro) e 16 (refinado); 10 a 13 e a
faixa util para resultado quantitativo sem custo excessivo.
"""

import math

# --- do memorial (ver gerar_geometria.py) ------------------------------------
Q_KW = 47830.0        # [kW]  taxa de liberacao de calor
D_STAR = 4.51         # [m]   diametro caracteristico de fogo
L_FLAME = 12.40       # [m]   altura de chama (Heskestad)

DOM = ((-30.0, 30.0), (-20.0, 20.0), (0.0, 30.0))


def vol(box):
    return math.prod(hi - lo for lo, hi in box)


def inside(inner, outer):
    """Volume de inner que cai dentro de outer (assume alinhamento e contencao)."""
    return vol(inner)


# --- zonas de refino ---------------------------------------------------------
# Z1  chama, pluma e tanque-alvo  -- a zona que precisa resolver
# Z2  entorno dos equipamentos e pluma alta
# Z4  costado do tanque-alvo -- onde se mede o fluxo radiante
ZONAS = [
    ("Z4  costado do alvo", ((2.0, 8.0), (-3.0, 3.0), (0.0, 7.0)), 0.15),
    ("Z1  chama + pluma", ((-10.0, 10.0), (-8.0, 8.0), (0.0, 18.0)), 0.35),
    ("Z2  entorno", ((-20.0, 25.0), (-14.0, 14.0), (0.0, 26.0)), 0.90),
    ("Z3  campo distante", DOM, 2.00),
]


def main():
    print("=" * 72)
    print("DIMENSIONAMENTO DE MALHA")
    print("=" * 72)
    print(f"  HRR                {Q_KW/1000:8.1f} MW")
    print(f"  D*                 {D_STAR:8.2f} m")
    print(f"  Altura de chama    {L_FLAME:8.2f} m")
    print("-" * 72)
    print("  Resolucao alvo:")
    for r in (4, 10, 13, 16):
        print(f"     D*/dx = {r:2d}        dx = {D_STAR/r:6.3f} m")
    print("=" * 72)

    print(f"\n{'ZONA':24s} {'dx [m]':>8s} {'D*/dx':>7s} {'vol [m3]':>11s} {'celulas':>11s}")
    print("-" * 72)

    total = 0
    consumido = 0.0
    # da zona mais fina para a mais grossa; cada uma desconta o que ja foi coberto
    for nome, box, dx in ZONAS:
        v = vol(box) - consumido
        v = max(v, 0.0)
        n = v / dx ** 3
        total += n
        consumido += v
        print(f"{nome:24s} {dx:8.2f} {D_STAR/dx:7.1f} {v:11.0f} {n:11,.0f}")

    print("-" * 72)
    print(f"{'TOTAL (poliedrica)':24s} {'':8s} {'':7s} {vol(DOM):11.0f} {total:11,.0f}")
    print(f"\n  Estimativa com incerteza de +/- 30%: "
          f"{total*0.7:,.0f} a {total*1.3:,.0f} celulas")
    print("  Camadas prismaticas nos costados adicionam por fora dessa conta.")
    print("=" * 72)

    # verificacoes
    print("\nVERIFICACOES")
    dx_chama = next(dx for nome, _, dx in ZONAS if nome.startswith("Z1"))
    r = D_STAR / dx_chama
    print(f"  D*/dx na zona de chama = {r:.1f}   "
          f"{'OK (faixa util 10-16)' if 10 <= r <= 16 else 'REVISAR'}")
    z1_top = next(box for nome, box, _ in ZONAS if nome.startswith("Z1"))[2][1]
    print(f"  Topo da zona fina = {z1_top:.0f} m vs chama de {L_FLAME:.1f} m   "
          f"{'OK' if z1_top > L_FLAME else 'REVISAR: zona fina nao cobre a chama'}")


if __name__ == "__main__":
    main()
