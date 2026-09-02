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
nao da geometria do braco. Logo: FUNDO INTEIRO como velocity inlet.

E a velocidade a impor NAO e a do furo. Ver entrada_de_equilibrio().

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
    """Condicao de entrada CASADA COM O ORIFICIO -- NAO USAR. Ver abaixo.

    Reproduz a velocidade real no furo (fracao = area aberta, velocidade =
    velocidade no furo), como o tutorial do tanque de aeracao faz com o prato
    perfurado.

    POR QUE NAO USAR: com furos de 2 mm a velocidade no orificio da 2,45 m/s
    em Ug = 0,0115. Numa celula de 10 mm isso e CFL ~2,5 no proprio contorno,
    e os residuos divergem cinco ordens de grandeza. Ja aconteceu.

    A velocidade no furo so faz sentido se a malha resolver o furo. Nao
    resolve, e nem deve: o que o furo determina fisicamente e o DIAMETRO DE
    BOLHA (lei de Tate), nao o campo de velocidade a jusante.

    Mantida no codigo como registro do que foi tentado.
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


V_ENTRADA = 0.29          # [m/s] proxima da velocidade terminal da bolha


def entrada_de_equilibrio(ug, v_gas=V_ENTRADA):
    """A condicao de entrada QUE SE USA.

    O contorno tem de entregar a VELOCIDADE SUPERFICIAL correta. Qualquer par
    (alpha, v) com  alpha * v = Ug  entrega a mesma vazao; a escolha define
    apenas o quanto o campo precisa se reacomodar logo acima do distribuidor.

    Escolhe-se v perto da velocidade terminal da bolha (0,233 m/s) e alpha
    perto do holdup de equilibrio. Assim o gas ja entra quase no estado em que
    vai viajar, e nao existe frente violenta no fundo.

    NAO SE APLICA CORRECAO DE EXPANSAO. O caso roda com Constant Density (a
    Ideal Gas liga a equacao de energia silenciosamente -- ja aconteceu, o
    residuo "Energy of Ar" apareceu na legenda). Num gas incompressivel a
    coluna carrega a MESMA velocidade superficial em toda altura, e o valor a
    impor e o proprio Ug de referencia do artigo, medido a meia coluna.
    """
    a_coluna = math.pi / 4 * D_C ** 2
    alpha = ug / v_gas
    return alpha, v_gas, ug * a_coluna


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

    print(f"\n{'Ug':>9s}{'eps alvo':>10s}{'ALTURA':>10s}{'volume':>10s}"
          f"{'Q':>10s}")
    print(f"{'[m/s]':>9s}{'[-]':>10s}{'[m]':>10s}{'[L]':>10s}{'[L/s]':>10s}")
    print("-" * 78)
    for ug in CONDICOES:
        eps = holdup_wallis(ug, U_INF["ar"])
        h = altura_aerada(ug, U_INF["ar"])
        vol = math.pi / 4 * D_C ** 2 * h * 1000.0
        _, _, q = entrada_de_equilibrio(ug)
        print(f"{ug:9.4f}{eps:10.4f}{h:10.3f}{vol:10.1f}{q*1000:10.3f}")
    print("-" * 78)
    print("  A altura muda de condicao para condicao porque o dominio TEM de")
    print("  ser o liquido aerado -- so assim a media volumetrica do CFD e")
    print("  comparavel ao eps = (h-h0)/h que o experimento mede.")
    print("=" * 78)

    print("\nCONDICAO DE ENTRADA  --  Sparger_Inlet, Velocity Inlet")
    print("=" * 78)
    print(f"{'Ug':>9s}{'alpha Ar':>11s}{'v do Ar':>11s}{'v da Agua':>12s}"
          f"{'CFL na celula de 10 mm':>26s}")
    print(f"{'[m/s]':>9s}{'[-]':>11s}{'[m/s]':>11s}{'[m/s]':>12s}"
          f"{'(dt = 0,01 s)':>26s}")
    print("-" * 78)
    for ug in CONDICOES:
        alpha, v, _ = entrada_de_equilibrio(ug)
        print(f"{ug:9.4f}{alpha:11.5f}{v:11.3f}{0.0:12.1f}"
              f"{v*0.01/0.010:26.2f}")
    print("-" * 78)
    print("  Regra: alpha * v = Ug. Qualquer par entrega a mesma vazao.")
    print("  Escolhe-se v ~ velocidade terminal da bolha para que o gas entre")
    print("  ja no estado em que vai viajar.")
    print("-" * 78)
    print("  NAO USAR a condicao casada com o orificio:")
    print(f"{'Ug':>9s}{'alpha':>11s}{'v no furo':>12s}{'CFL':>10s}")
    for ug in CONDICOES:
        alpha, v_gas, _, _ = condicao_de_entrada(ug)
        print(f"{ug:9.4f}{alpha:11.5f}{v_gas:12.2f}{v_gas*0.01/0.010:10.1f}")
    print("  CFL de 2,4 no proprio contorno. Os residuos divergem. Ja aconteceu.")
    print("=" * 78)

    print("\nINICIALIZACAO  --  o outro tropeco")
    print("-" * 78)
    for ug in CONDICOES:
        eps = holdup_wallis(ug, U_INF["ar"])
        print(f"  Ug = {ug:.4f}   ->   inicializar Volume Fraction of Ar em "
              f"{eps:.3f}, NAO em zero")
    print("-" * 78)
    print("  Partir de alpha = 0 cria uma frente violenta subindo a coluna.")
    print("  Partir do holdup esperado economiza a transiente inteira de")
    print("  enchimento e nao muda o estado final.")
    print("-" * 78)
    print("  E o gas fica em CONSTANT DENSITY. A Ideal Gas liga a equacao de")
    print("  energia sem avisar -- o residuo 'Energy of Ar' aparece na legenda.")
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
