#!/usr/bin/env python3
"""
Tubo reto de TARA para o caso da valvula borboleta Bray 2-Cx DN 100.

Mesmo dominio da valvula (5D montante + 10D jusante, furo de 100 mm), SEM
disco e SEM haste. Serve para medir a perda de carga do tubo entre as tomadas
de pressao (2D montante / 6D jusante, IEC 60534-2-3) na MESMA malha, e assim
separar:

    dP_valvula = dP_com_disco - dP_tara

que e a grandeza comparavel ao Kv de catalogo. O procedimento e o mesmo do
banco de ensaio, e tem o bonus de cancelar boa parte do erro de malha: o erro
de atrito e comum as duas rodadas.

Em 90 graus isso e essencial (atrito e valvula tem a mesma ordem de grandeza).
Nos angulos fechados a tara vira irrelevante -- em 30 graus o dP e 1,71 bar
contra ~375 Pa de atrito.

Requisitos: cadquery >= 2.8
"""

import math
import os

import cadquery as cq

from gerar_valvula import (D_BORE, L_UP, L_DOWN, RHO, Q_SERVICO, STEP_UNIT,
                           make_dominio, verificar_unidade)

# posicao das tomadas de pressao [em diametros a partir do disco]
TAP_UP = 2.0
TAP_DOWN = 6.0

MU = 1.002e-3         # [Pa.s] viscosidade dinamica, agua a 20 C

OUTDIR = os.path.dirname(os.path.abspath(__file__))


def make_tubo_reto():
    """Dominio fluido sem disco e sem haste -- so o tubo."""
    x0 = -L_UP * D_BORE
    x1 = L_DOWN * D_BORE
    return cq.Solid.makeCylinder(
        D_BORE / 2.0, x1 - x0, cq.Vector(x0, 0, 0), cq.Vector(1, 0, 0))


def fator_atrito(re):
    """Colebrook para tubo liso, por iteracao de ponto fixo."""
    f = 0.02
    for _ in range(50):
        f = 1.0 / (-2.0 * math.log10(2.51 / (re * math.sqrt(f)))) ** 2
    return f


def relatorio():
    a = math.pi / 4 * D_BORE ** 2
    v = Q_SERVICO / 3600.0 / a
    re = RHO * v * D_BORE / MU
    f = fator_atrito(re)
    q_din = RHO * v ** 2 / 2.0
    dpdl = f / D_BORE * q_din
    l_taps = (TAP_UP + TAP_DOWN) * D_BORE

    print("=" * 74)
    print("TARA -- TUBO RETO  DN 100")
    print("=" * 74)
    print(f"  Vazao                    {Q_SERVICO:8.1f} m3/h")
    print(f"  Velocidade               {v:8.2f} m/s")
    print(f"  Reynolds                 {re:8.0f}")
    print(f"  Fator de atrito (Darcy)  {f:8.4f}   Colebrook, tubo liso")
    print(f"  Pressao dinamica         {q_din:8.0f} Pa")
    print("-" * 74)
    print(f"  Gradiente de pressao     {dpdl:8.0f} Pa/m")
    print(f"  Trecho entre tomadas     {l_taps:8.3f} m   "
          f"({TAP_UP:.0f}D montante + {TAP_DOWN:.0f}D jusante)")
    print(f"  dP_tara ESPERADO         {dpdl*l_taps:8.0f} Pa")
    print("=" * 74)

    print("\nCOMO LER O RESULTADO DA RODADA")
    print("-" * 74)
    dp_total = 667.0                      # medido, malha de 1,0 mm
    print(f"  dP medido com disco (1,0 mm)      {dp_total:6.0f} Pa")
    print(f"  dP catalogo em Kv = 909            {(Q_SERVICO/909.0)**2*1e5:6.0f} Pa")
    print("-" * 74)
    print(f"{'dP_tara':>10s}{'dP_valvula':>14s}{'Kv resultante':>16s}"
          f"{'vs catalogo':>14s}")
    print("-" * 74)
    for dp_tara in (100.0, 150.0, 200.0, 250.0, 300.0, 375.0):
        dp_v = dp_total - dp_tara
        kv = Q_SERVICO / math.sqrt(dp_v / 1e5)
        print(f"{dp_tara:10.0f}{dp_v:14.0f}{kv:16.0f}"
              f"{100*(kv/909.0-1):13.1f}%")
    print("-" * 74)
    print("  dP_tara ~ 375 Pa  -> atrito bem resolvido; o disco e que perde de")
    print("                       menos. Mexer no DISCO (cubo, espessura,")
    print("                       degrau de sede), NAO no furo.")
    print("  dP_tara ~ 150 Pa  -> atrito subresolvido pela malha / tratamento")
    print("                       de parede. Conferir y+ e camada prismatica.")
    print("=" * 74)


def main():
    relatorio()

    print("\nGERANDO STEP\n" + "-" * 74)

    tubo = make_tubo_reto()
    path = os.path.join(OUTDIR, "tubo_reto_tara.step")
    assy = cq.Assembly(name="Tara")
    assy.add(tubo, name="Fluido", color=cq.Color("lightgray"))
    assy.export(path, unit=STEP_UNIT)
    verificar_unidade(path)

    vol_tara = tubo.Volume() * 1e6
    print(f"  tubo_reto_tara.step                     "
          f"{len(tubo.Faces()):3d} faces  {vol_tara:9.1f} cm3")

    # conferencia: a diferenca de volume e o disco + a haste
    valv = make_dominio(90)
    vol_valv = valv.Volume() * 1e6
    print(f"  valvula_borboleta_DN100_90graus.step    "
          f"{len(valv.Faces()):3d} faces  {vol_valv:9.1f} cm3")
    print("-" * 74)
    print(f"  diferenca (disco + haste)                            "
          f"{vol_tara - vol_valv:9.1f} cm3")
    print("-" * 74)
    print("\n  Faces esperadas na importacao:")
    for face in tubo.Faces():
        c = face.Center()
        print(f"    area {face.Area()*1e4:9.1f} cm2   "
              f"centro ({c.x:+.3f}, {c.y:+.3f}, {c.z:+.3f})")
    print("-" * 74)


if __name__ == "__main__":
    main()
