#!/usr/bin/env python3
"""
Dominio fluido de valvula borboleta revestida em PTFE - Bray 2-Cx, DN 100.

Base dimensional: manual tecnico de vendas Bray 2-Cx (PT_TSM_2Cx_20251030_01),
corpo wafer PN 10, DN 100:

    face a face (B)        52 mm    -- confere com EN 558 Serie 20
    diametro da haste (G)  16 mm
    corda do disco (K)     88 mm

O diametro de passagem NAO e publicado (o revestimento em PTFE o reduz em
relacao ao nominal). Adotado 100 mm e a ser CALIBRADO pelo Kv de 90 graus
publicado no catalogo (909 m3/h para DN 100). Ver README.

O modelo e o DOMINIO FLUIDO: tubo a montante, passagem do corpo, disco no
angulo, haste, tubo a jusante. Corpo tratado como furo cilindrico reto, que e
o que o revestimento produz na pratica.

Saidas: um STEP por angulo de abertura, em METROS.

Requisitos: cadquery >= 2.8
"""

import math
import os

import cadquery as cq

# Unidade do STEP. O exportador do cadquery grava em MILIMETROS por padrao;
# como a geometria e construida em metros, sem declarar a unidade o importador
# leria o tubo de 1,5 m como 1,5 mm.
STEP_UNIT = "M"

# ----------------------------------------------------------------------------
# PARAMETROS  (todos em metros)
# ----------------------------------------------------------------------------

D_BORE = 0.100        # diametro de passagem  <- calibrar pelo Kv de 90 graus
FACE_TO_FACE = 0.052  # B, corpo wafer, EN 558 Serie 20
D_STEM = 0.016        # G, diametro da haste
D_DISC = 0.098        # diametro do disco (folga radial de 1 mm no furo)
T_DISC = 0.020        # espessura do disco no cubo (lente biconvexa)

L_UP = 5.0            # comprimento a montante, em diametros
L_DOWN = 10.0         # comprimento a jusante, em diametros

# Angulos de abertura a gerar [graus]. 90 = totalmente aberta.
# Abaixo de 30 graus a folga entre disco e sede domina o Kv e o modelo
# simplificado deixa de ser confiavel -- ver README.
ANGULOS = [90, 80, 70, 60, 50, 40, 30]

# --- agua a 20 C, para o memorial -------------------------------------------
RHO = 998.2           # [kg/m3]
P_VAP = 2339.0        # [Pa] pressao de vapor
Q_SERVICO = 70.7      # [m3/h] vazao de referencia (~2,5 m/s em DN 100)

# --- Kv publicado no catalogo, DN 100 ---------------------------------------
KV_CATALOGO = {90: 909, 80: 702, 70: 435, 60: 247,
               50: 153, 40: 94, 30: 54, 20: 23, 10: 3}

OUTDIR = os.path.dirname(os.path.abspath(__file__))


def verificar_unidade(path):
    """Confere que o STEP gravado declara metros, e nao milimetros."""
    with open(path, "r", errors="ignore") as fh:
        texto = fh.read()
    if "SI_UNIT(.MILLI.,.METRE.)" in texto:
        raise RuntimeError(f"{path}: gravado em MILIMETROS")
    if "SI_UNIT($,.METRE.)" not in texto:
        raise RuntimeError(f"{path}: unidade de comprimento nao reconhecida")


# ----------------------------------------------------------------------------
# GEOMETRIA
# ----------------------------------------------------------------------------

def make_lente(diametro, espessura):
    """Disco biconvexo (lente), eixo em z, centrado na origem.

    Perfil de lente e o formato real de disco de borboleta -- um cilindro reto
    superestimaria o bloqueio e a perda de carga.
    """
    r = diametro / 2.0
    t = espessura / 2.0
    r_esf = (r ** 2 + t ** 2) / (2.0 * t)
    desloc = r_esf - t
    sup = cq.Solid.makeSphere(r_esf, cq.Vector(0, 0, -desloc), angleDegrees1=-90,
                              angleDegrees2=90, angleDegrees3=360)
    inf = cq.Solid.makeSphere(r_esf, cq.Vector(0, 0, desloc), angleDegrees1=-90,
                              angleDegrees2=90, angleDegrees3=360)
    return sup.intersect(inf).clean()


def make_dominio(angulo_graus):
    """Dominio fluido para um angulo de abertura.

    90 graus = disco paralelo ao escoamento (aberta).
     0 graus = disco perpendicular ao escoamento (fechada).
    """
    x0 = -L_UP * D_BORE
    x1 = L_DOWN * D_BORE

    tubo = cq.Solid.makeCylinder(
        D_BORE / 2.0, x1 - x0, cq.Vector(x0, 0, 0), cq.Vector(1, 0, 0))

    # disco construido aberto (normal em z) e girado em torno do eixo da haste
    disco = make_lente(D_DISC, T_DISC)
    disco = disco.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0),
                         90.0 - angulo_graus)

    # haste atravessando a passagem, eixo em y
    haste = cq.Solid.makeCylinder(
        D_STEM / 2.0, D_BORE * 1.5, cq.Vector(0, -D_BORE * 0.75, 0),
        cq.Vector(0, 1, 0))

    return tubo.cut(disco).cut(haste).clean()


# ----------------------------------------------------------------------------
# MEMORIAL
# ----------------------------------------------------------------------------

def fracao_area_livre(angulo_graus):
    """Fracao de area livre projetada no plano normal ao escoamento.

    O disco, girado do angulo de abertura, projeta uma elipse de semieixos
    (D_disc/2) e (D_disc/2)*cos(theta). Aproximacao de disco fino: despreza a
    contribuicao da espessura, que so pesa perto da abertura total.
    """
    th = math.radians(angulo_graus)
    return 1.0 - (D_DISC / D_BORE) ** 2 * math.cos(th)


def k_loss_de_kv(kv):
    """Coeficiente de perda referido a velocidade no tubo, a partir do Kv."""
    a = math.pi / 4 * D_BORE ** 2
    return (50912.0 * a / kv) ** 2


def relatorio():
    a_tubo = math.pi / 4 * D_BORE ** 2
    v = Q_SERVICO / 3600.0 / a_tubo

    print("=" * 78)
    print("DOMINIO FLUIDO - VALVULA BORBOLETA BRAY 2-Cx  DN 100")
    print("=" * 78)
    print(f"  Diametro de passagem       {D_BORE*1000:7.1f} mm   (a calibrar)")
    print(f"  Face a face                {FACE_TO_FACE*1000:7.1f} mm   EN 558 Serie 20")
    print(f"  Diametro da haste          {D_STEM*1000:7.1f} mm")
    print(f"  Disco (diametro x esp.)    {D_DISC*1000:7.1f} x {T_DISC*1000:.1f} mm")
    print(f"  Dominio                    {L_UP:.0f}D montante + {L_DOWN:.0f}D jusante"
          f"  =  {(L_UP+L_DOWN)*D_BORE*1000:.0f} mm")
    print("-" * 78)
    print(f"  Vazao de referencia        {Q_SERVICO:7.1f} m3/h  ->  {v:.2f} m/s no tubo")
    print("=" * 78)
    print(f"\n{'ang':>5s}{'Kv cat.':>10s}{'K_perda':>10s}{'area livre':>12s}"
          f"{'dP servico':>12s}{'p1 minima':>12s}")
    print(f"{'[gr]':>5s}{'[m3/h]':>10s}{'[-]':>10s}{'[% do tubo]':>12s}"
          f"{'[bar]':>12s}{'[bar]':>12s}")
    print("-" * 78)
    kv_ref = KV_CATALOGO[90]
    a_ref = fracao_area_livre(90)
    linhas = []
    for ang in ANGULOS:
        kv = KV_CATALOGO[ang]
        k = k_loss_de_kv(kv)
        fa = fracao_area_livre(ang)
        dp = (Q_SERVICO / kv) ** 2                      # [bar]
        # pressao a montante minima para a vena contracta ficar acima de p_vap,
        # com F_L = 0,70 PRESUMIDO (tipico de borboleta; extrair do CFD)
        p1_min = (P_VAP / 1e5) + dp / (0.70 ** 2)
        print(f"{ang:5d}{kv:10d}{k:10.2f}{100*fa:12.1f}{dp:12.3f}{p1_min:12.2f}")
        linhas.append((ang, kv_ref / kv, a_ref / fa))
    print("-" * 78)
    print("  K_perda vem de  Kv = 50912*A/sqrt(K)  com A na area do tubo.")
    print("  p1 minima usa  sigma = (p1-pv)/(p1-p2)  com F_L = 0,70 PRESUMIDO.")
    print("  O F_L real sai do CFD -- e o principal entregavel, pois o")
    print("  catalogo publica Kv mas nao publica F_L.")

    print("\n" + "=" * 78)
    print("A NAO-LINEARIDADE: Kv cai mais rapido que a area")
    print("=" * 78)
    print(f"{'ang':>5s}{'queda de Kv':>14s}{'queda de area':>16s}{'razao':>10s}")
    print(f"{'[gr]':>5s}{'(rel. a 90 gr)':>14s}{'(rel. a 90 gr)':>16s}{'[-]':>10s}")
    print("-" * 78)
    for ang, qkv, qa in linhas:
        print(f"{ang:5d}{qkv:14.1f}{qa:16.1f}{qkv/qa:10.2f}")
    print("-" * 78)
    print("  A area livre cai por geometria; o Kv cai mais porque o coeficiente")
    print("  de descarga tambem despenca -- a passagem vira duas frestas em")
    print("  meia-lua, com escoamento tortuoso. E dessa diferenca que nasce a")
    print("  cavitacao: mesma vazao, muito mais perda, vena contracta profunda.")
    print("=" * 78)

    # --- estimativa de malha ---
    vol = a_tubo * (L_UP + L_DOWN) * D_BORE
    v_ref = math.pi / 4 * D_BORE ** 2 * 0.20           # zona refinada, 2D
    n_ref = v_ref / 0.0015 ** 3
    n_res = (vol - v_ref) / 0.004 ** 3
    print(f"\nMALHA ESTIMADA  (1,5 mm na zona do disco, 4 mm no tubo)")
    print(f"  zona do disco (2D)   {n_ref:10,.0f} celulas")
    print(f"  restante do tubo     {n_res:10,.0f} celulas")
    print(f"  TOTAL                {n_ref+n_res:10,.0f} celulas")
    print(f"  com simetria em y=0  {(n_ref+n_res)/2:10,.0f} celulas")
    print("=" * 78)


# ----------------------------------------------------------------------------

def main():
    relatorio()
    print("\nGERANDO STEP\n" + "-" * 78)
    for ang in ANGULOS:
        dom = make_dominio(ang)
        nome = f"valvula_borboleta_DN100_{ang:02d}graus.step"
        path = os.path.join(OUTDIR, nome)
        assy = cq.Assembly(name=f"Fluido_{ang}graus")
        assy.add(dom, name="Fluido", color=cq.Color("steelblue"))
        assy.export(path, unit=STEP_UNIT)
        verificar_unidade(path)
        print(f"  {nome:45s} {len(dom.Faces()):3d} faces"
              f"   {dom.Volume()*1e6:9.1f} cm3")
    print("-" * 78)


if __name__ == "__main__":
    main()
