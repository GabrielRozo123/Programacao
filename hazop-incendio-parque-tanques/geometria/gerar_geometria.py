#!/usr/bin/env python3
"""
Geracao da geometria CAD do caso de incendio em parque de tanques de solvente.

Base de projeto derivada das informacoes publicas do incendio industrial de
04/08/2026 em Itaquaquecetuba (SP): planta de solventes e resinas poliester,
com 24 tanques de solvente de aproximadamente 31 m3 cada.

O layout aqui e REPRESENTATIVO, nao uma reconstituicao: o arranjo real da
planta nao e publico. O que vem do caso real e a base de projeto (tipo de
produto, volume unitario dos tanques, natureza do parque).

Saidas:
    parque_tanques_completo.step  - solidos nomeados separadamente
    parque_tanques_cfd.step       - 2 partes (Fire + Air), pronto para o
                                    fluxo "Assign Parts to Regions" do
                                    tutorial Fire and Smoke Wizard

Requisitos: cadquery >= 2.8
"""

import math
import os

import cadquery as cq

# ----------------------------------------------------------------------------
# 1. PARAMETROS
# ----------------------------------------------------------------------------

# --- Tanque (base: ~31 m3, conforme inventario noticiado) --------------------
TANK_D = 3.0          # [m] diametro do costado
TANK_H = 4.4          # [m] altura do costado
ROOF_RISE = 0.25      # [m] flecha do teto conico

# --- Bacias de contencao (dique) ---------------------------------------------
BUND_LX = 12.0        # [m] comprimento interno
BUND_LY = 10.0        # [m] largura interna
BUND_H = 1.0          # [m] altura da mureta
BUND_T = 0.3          # [m] espessura da mureta

# --- Poca / regiao de fogo ----------------------------------------------------
POOL_D = 5.0          # [m] diametro equivalente da poca (derramamento parcial)
FIRE_H = 5.0          # [m] altura da regiao de fonte volumetrica de calor
                      #     (~zona de chama continua; a chama visivel e maior,
                      #      ver relatorio de Heskestad abaixo)

# --- Dominio computacional ----------------------------------------------------
DOM_X = (-30.0, 30.0)   # [m] vento sopra em +x (do tanque-fonte para o alvo)
DOM_Y = (-20.0, 20.0)
DOM_Z = (0.0, 30.0)

# --- Posicoes (planta) --------------------------------------------------------
BUND_A_X0 = -13.0     # bacia A (incendio): interno x de -13 a -1
BUND_A_Y0 = -5.0
BUND_B_X0 = 2.0       # bacia B (alvo):     interno x de  2 a 14
BUND_B_Y0 = -5.0

TANK_SOURCE_POS = (-10.0, 0.0)   # T-01, tanque de origem do vazamento
POOL_POS = (-4.5, 0.0)           # poca, deslocada do tanque (vazamento lateral)
TANK_TARGET_POS = (5.0, 0.0)     # T-02, tanque-alvo (exposto)

# --- Propriedades do combustivel (tolueno, literatura aberta) -----------------
MDOT_INF = 0.06       # [kg/m2.s] taxa de queima assintotica
K_BETA = 2.5          # [1/m]     coeficiente de Burgess-Zabetakis
DHC = 40.6            # [MJ/kg]   calor de combustao

# --- Ambiente -----------------------------------------------------------------
RHO_INF = 1.2         # [kg/m3]
CP_INF = 1.005        # [kJ/kg.K]
T_INF = 293.0         # [K]
G = 9.81              # [m/s2]

OUTDIR = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------
# 2. PRIMITIVAS
# ----------------------------------------------------------------------------

def make_tank(x, y, diameter=TANK_D, height=TANK_H, rise=ROOF_RISE):
    """Tanque vertical cilindrico com teto conico, base em z=0."""
    r = diameter / 2.0
    shell = cq.Solid.makeCylinder(r, height, cq.Vector(x, y, 0))
    roof = cq.Solid.makeCone(r, 0.0, rise, cq.Vector(x, y, height))
    return shell.fuse(roof).clean()


def make_bund(x0, y0, lx=BUND_LX, ly=BUND_LY, h=BUND_H, t=BUND_T):
    """Mureta de bacia de contencao (anel retangular)."""
    outer = cq.Solid.makeBox(lx + 2 * t, ly + 2 * t, h, cq.Vector(x0 - t, y0 - t, 0))
    inner = cq.Solid.makeBox(lx, ly, h, cq.Vector(x0, y0, 0))
    return outer.cut(inner).clean()


def make_fire(x, y, diameter=POOL_D, height=FIRE_H):
    """Regiao de fonte volumetrica de calor sobre a poca."""
    return cq.Solid.makeCylinder(diameter / 2.0, height, cq.Vector(x, y, 0))


def make_domain():
    """Caixa do dominio computacional."""
    return cq.Solid.makeBox(
        DOM_X[1] - DOM_X[0],
        DOM_Y[1] - DOM_Y[0],
        DOM_Z[1] - DOM_Z[0],
        cq.Vector(DOM_X[0], DOM_Y[0], DOM_Z[0]),
    )


# ----------------------------------------------------------------------------
# 3. MEMORIAL DE CALCULO
# ----------------------------------------------------------------------------

def relatorio():
    """Calcula e imprime as grandezas que dimensionam o caso."""
    tank_v = math.pi / 4 * TANK_D ** 2 * TANK_H
    bund_v = BUND_LX * BUND_LY * BUND_H

    pool_a = math.pi / 4 * POOL_D ** 2
    mdot_pp = MDOT_INF * (1 - math.exp(-K_BETA * POOL_D))
    mdot = mdot_pp * pool_a
    q_mw = mdot * DHC
    q_kw = q_mw * 1000.0

    # Diametro caracteristico de fogo
    d_star = (q_kw / (RHO_INF * CP_INF * T_INF * math.sqrt(G))) ** 0.4

    # Altura de chama (Heskestad)
    l_flame = 0.235 * q_kw ** 0.4 - 1.02 * POOL_D

    # Fluxo radiante no alvo pelo modelo de fonte pontual
    # Fonte na meia-altura da chama, sobre o centro da poca.
    src = (POOL_POS[0], POOL_POS[1], 0.5 * l_flame)
    tgt = (TANK_TARGET_POS[0] - TANK_D / 2.0, TANK_TARGET_POS[1], TANK_H / 2.0)
    r = math.dist(src, tgt)

    print("=" * 74)
    print("MEMORIAL DE CALCULO - caso de incendio em parque de tanques")
    print("=" * 74)
    print(f"  Volume do tanque              {tank_v:8.1f} m3   (base: ~31 m3)")
    print(f"  Capacidade da bacia           {bund_v:8.1f} m3   "
          f"({'OK' if bund_v >= tank_v else 'INSUFICIENTE'}: >= maior tanque)")
    print("-" * 74)
    print(f"  Area da poca                  {pool_a:8.2f} m2")
    print(f"  Taxa de queima  m''           {mdot_pp:8.4f} kg/m2.s")
    print(f"  Vazao massica de combustivel  {mdot:8.3f} kg/s")
    print(f"  HRR                           {q_mw:8.1f} MW")
    print("-" * 74)
    print(f"  D* (diametro caracteristico)  {d_star:8.2f} m")
    print(f"     dx para D*/dx = 10         {d_star / 10:8.3f} m")
    print(f"     dx para D*/dx = 16         {d_star / 16:8.3f} m")
    print(f"  Altura de chama (Heskestad)   {l_flame:8.2f} m")
    print(f"  Altura do dominio             {DOM_Z[1]:8.1f} m   "
          f"({'OK' if DOM_Z[1] > 2 * l_flame else 'REVISAR'}: > 2x chama)")
    print("-" * 74)
    print(f"  Distancia fonte->alvo         {r:8.2f} m")
    print("  Fluxo radiante no alvo (modelo de fonte pontual):")
    for chi in (0.15, 0.25, 0.35):
        q_rad = chi * q_kw / (4 * math.pi * r ** 2)
        print(f"     chi_r = {chi:.2f}                {q_rad:8.1f} kW/m2")
    print("  Referencia: 37,5 / 12,5 / 5 kW/m2  |  limiar de escalonamento ~15")
    print("=" * 74)

    return {"q_mw": q_mw, "d_star": d_star, "l_flame": l_flame}


# ----------------------------------------------------------------------------
# 4. MONTAGEM E EXPORTACAO
# ----------------------------------------------------------------------------

def main():
    relatorio()

    tank_source = make_tank(*TANK_SOURCE_POS)
    tank_target = make_tank(*TANK_TARGET_POS)
    bund_a = make_bund(BUND_A_X0, BUND_A_Y0)
    bund_b = make_bund(BUND_B_X0, BUND_B_Y0)
    fire = make_fire(*POOL_POS)
    domain = make_domain()

    # --- (a) modelo completo, solidos nomeados separadamente -----------------
    assy = cq.Assembly(name="ParqueTanques")
    assy.add(tank_source, name="Tank_T01_Source", color=cq.Color("gray"))
    assy.add(tank_target, name="Tank_T02_Target", color=cq.Color("steelblue"))
    assy.add(bund_a, name="Bund_A_Fire", color=cq.Color("lightgray"))
    assy.add(bund_b, name="Bund_B_Target", color=cq.Color("lightgray"))
    assy.add(fire, name="Fire", color=cq.Color("orange"))
    assy.add(domain, name="Domain", color=cq.Color("lightblue"))

    path_full = os.path.join(OUTDIR, "parque_tanques_completo.step")
    assy.export(path_full)
    print(f"\n[ok] {path_full}")

    # --- (b) modelo CFD: Fire + Air (dominio menos solidos e menos Fire) -----
    # Reproduz a arquitetura de duas partes do tutorial Steckler Room.
    air = domain.cut(tank_source).cut(tank_target)
    air = air.cut(bund_a).cut(bund_b).cut(fire).clean()

    assy_cfd = cq.Assembly(name="ParqueTanques_CFD")
    assy_cfd.add(fire, name="Fire", color=cq.Color("orange"))
    assy_cfd.add(air, name="Air", color=cq.Color("lightblue"))

    path_cfd = os.path.join(OUTDIR, "parque_tanques_cfd.step")
    assy_cfd.export(path_cfd)
    print(f"[ok] {path_cfd}")

    print(f"\n  Volume Fire   {fire.Volume():10.2f} m3")
    print(f"  Volume Air    {air.Volume():10.2f} m3")


if __name__ == "__main__":
    main()
