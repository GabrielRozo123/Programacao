#!/usr/bin/env python3
"""
Dominio fluido da coluna de bolhas de Ferrario et al. (2025).

Coluna cilindrica de 0,24 m de diametro interno, distribuidor aranha no fundo,
degassing boundary no topo, operada em BATELADA.

ALTURA DO DOMINIO -- o ponto delicado
-------------------------------------
O experimento mede o holdup pela elevacao do nivel:

    eps = (h - h0)/h        h0 = 3,00 m em repouso

Com degassing boundary o dominio e FIXO e totalmente ocupado pela mistura
aerada. Para que a media volumetrica do CFD seja comparavel ao eps medido, a
altura do dominio tem de ser a altura AERADA:

    h = h0 / (1 - eps)

que depende da propria condicao. Por isso o script gera um STEP POR CONDICAO,
com a altura correta -- exatamente como fizemos com os angulos da valvula.

DISTRIBUIDOR
------------
O distribuidor aranha real tem 6 bracos com furos de 2 mm. Numa malha de
10 mm esses furos, e mesmo a pegada dos bracos (~12 mm de largura), ficam
abaixo da resolucao. Modelar a pegada seria fidelidade falsa.

O que importa fisicamente e (a) a velocidade superficial e (b) o diametro de
bolha na formacao -- e o segundo vem da lei de Tate a partir do furo de 2 mm,
nao da geometria do braco. Logo: FUNDO INTEIRO como velocity inlet, com a
fracao volumetrica e a velocidade ajustadas para reproduzir tanto a vazao
quanto a velocidade real no orificio.

Requisitos: cadquery >= 2.8
"""

import math
import os

import cadquery as cq

from memorial import (D_C, D_HOLE, H_0, N_ARMS, RHO_L, U_INF, UG_EXP,
                      bolha_de_formacao, holdup_wallis)

STEP_UNIT = "M"

N_FUROS_POR_BRACO = 10          # presumido -- ver README
FURO_TOTAL = N_ARMS * N_FUROS_POR_BRACO

# condicoes a gerar: baixa, media e alta, cobrindo a faixa experimental
CONDICOES = [UG_EXP[0], UG_EXP[2], UG_EXP[-1]]

OUTDIR = os.path.dirname(os.path.abspath(__file__))


def verificar_unidade(path):
    """Confere que o STEP gravado declara metros, e nao milimetros."""
    with open(path, "r", errors="ignore") as fh:
        texto = fh.read()
    if "SI_UNIT(.MILLI.,.METRE.)" in texto:
        raise RuntimeError(f"{path}: gravado em MILIMETROS")
    if "SI_UNIT($,.METRE.)" not in texto:
        raise RuntimeError(f"{path}: unidade de comprimento nao reconhecida")


def altura_aerada(ug, u_inf):
    """Altura do dominio = altura do liquido aerado."""
    return H_0 / (1.0 - holdup_wallis(ug, u_inf))


def make_dominio(altura):
    """Cilindro do fundo (z = 0, distribuidor) ao topo (degassing)."""
    return cq.Solid.makeCylinder(
        D_C / 2.0, altura, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))


PATM = 101325.0
G = 9.81


def condicao_de_entrada(ug):
    """Fracao volumetrica e velocidade do gas no contorno de entrada.

    Reproduz simultaneamente a vazao volumetrica e a velocidade real no
    orificio, como o tutorial do tanque de aeracao faz com o prato perfurado
    (fracao = area aberta, velocidade = velocidade no furo).

    CORRECAO DE EXPANSAO -- o artigo referencia Ug a MEIA COLUNA ("the
    operative pressure was assumed equivalent to the pressure of half a
    column"). A entrada esta no FUNDO, onde a pressao e maior e o mesmo
    numero de moles ocupa MENOS volume:

        Q_fundo = Q_meio * p_meio / p_fundo        (~0,888)

    Ignorar isso injeta ~11% de gas a mais e infla o holdup -- quase tres
    vezes a incerteza experimental de 4,1%.
    """
    a_coluna = math.pi / 4 * D_C ** 2
    a_furos = FURO_TOTAL * math.pi / 4 * D_HOLE ** 2
    eps = holdup_wallis(ug, U_INF["ar"])
    h = altura_aerada(ug, U_INF["ar"])
    p_meio = PATM + RHO_L * G * h / 2.0 * (1.0 - eps)
    p_fundo = PATM + RHO_L * G * h * (1.0 - eps)
    q = ug * a_coluna * p_meio / p_fundo
    alpha = a_furos / a_coluna
    v_gas = q / a_furos
    return alpha, v_gas, q, a_furos


def relatorio():
    print("=" * 78)
    print("DOMINIO -- COLUNA DE BOLHAS DE FERRARIO et al. (2025)")
    print("=" * 78)
    print(f"  Diametro interno           {D_C*1000:8.0f} mm")
    print(f"  Liquido em repouso         {H_0:8.2f} m")
    print(f"  Distribuidor               aranha, {N_ARMS} bracos, "
          f"furos de {D_HOLE*1000:.0f} mm")
    print(f"  Furos presumidos           {FURO_TOTAL:8d}  "
          f"({N_ARMS} x {N_FUROS_POR_BRACO})")
    print(f"  Diametro de bolha (Tate)   {bolha_de_formacao(D_HOLE)*1000:8.2f} mm")
    print("=" * 78)

    print(f"\n{'Ug':>9s}{'eps':>9s}{'ALTURA':>10s}{'volume':>10s}"
          f"{'alpha in':>10s}{'v_gas in':>11s}{'Q':>10s}")
    print(f"{'[m/s]':>9s}{'[-]':>9s}{'[m]':>10s}{'[L]':>10s}"
          f"{'[-]':>10s}{'[m/s]':>11s}{'[L/s]':>10s}")
    print("-" * 78)
    for ug in CONDICOES:
        eps = holdup_wallis(ug, U_INF["ar"])
        h = altura_aerada(ug, U_INF["ar"])
        vol = math.pi / 4 * D_C ** 2 * h * 1000.0
        alpha, v_gas, q, _ = condicao_de_entrada(ug)
        print(f"{ug:9.4f}{eps:9.4f}{h:10.3f}{vol:10.1f}"
              f"{alpha:10.5f}{v_gas:11.2f}{q*1000:10.3f}")
    print("-" * 78)
    print("  A altura muda de condicao para condicao porque o dominio TEM de")
    print("  ser o liquido aerado -- so assim a media volumetrica do CFD e")
    print("  comparavel ao eps = (h-h0)/h que o experimento mede.")
    print("=" * 78)

    print("\nCONTORNOS  (3 faces por STEP)")
    print("-" * 78)
    print(f"{'nome':22s}{'localizacao':22s}{'tipo':34s}")
    print("-" * 78)
    for nome, loc, tipo in (
            ("Sparger_Inlet", "z = 0", "Velocity Inlet"),
            ("Degassing_Outlet", "z = altura", "Wall + Phase Permeable (gas)"),
            ("Column_Wall", "lateral", "Wall, sem escorregamento")):
        print(f"{nome:22s}{loc:22s}{tipo:34s}")
    print("-" * 78)
    print("  ATENCAO no Degassing_Outlet: a velocidade tangencial fica em ZERO.")
    print("  O tutorial do tanque de aeracao impoe 5 m/s ali para induzir")
    print("  circulacao -- copiar isso destruiria a validacao em batelada.")
    print("=" * 78)

    # malha
    print("\nMALHA ESTIMADA")
    print("-" * 78)
    for dx in (0.015, 0.010, 0.008):
        ncols = D_C / dx
        h = altura_aerada(CONDICOES[1], U_INF["ar"])
        vol = math.pi / 4 * D_C ** 2 * h
        n = vol / dx ** 3
        print(f"  dx = {dx*1000:4.0f} mm   {ncols:4.0f} celulas no diametro   "
              f"{n:12,.0f} celulas")
    print("-" * 78)
    print("  10 mm da 24 celulas no diametro, que e a pratica usual para")
    print("  holdup global convergido em EMP de coluna de bolhas.")
    print("=" * 78)


def main():
    relatorio()
    print("\nGERANDO STEP\n" + "-" * 78)
    for ug in CONDICOES:
        h = altura_aerada(ug, U_INF["ar"])
        dom = make_dominio(h)
        nome = f"coluna_D240_Ug{ug*10000:04.0f}.step"
        path = os.path.join(OUTDIR, nome)
        assy = cq.Assembly(name=f"Coluna_Ug_{ug}")
        assy.add(dom, name="Liquido", color=cq.Color("steelblue"))
        assy.export(path, unit=STEP_UNIT)
        verificar_unidade(path)
        print(f"  {nome:34s} {len(dom.Faces()):2d} faces   "
              f"h = {h:.3f} m   {dom.Volume()*1000:7.1f} L")
    print("-" * 78)
    print("  Nome do arquivo traz Ug em unidades de 1e-4 m/s.")


if __name__ == "__main__":
    main()
