"""
gen_lanca_furada.py — geometria da LANÇA PERFURADA recomendada (Fase 3 · Ito)

Ponto de projeto do RELATORIO §8.4:
    furo Ø 1,0 mm · 48 furos por lança (2 anéis de 24) · passo axial 15 mm
    tubo 2½" Sch40 (OD 73,0 · ID 62,7 · parede 5,16) · ponta com TAMPA CEGA

Gera dois arquivos, com propósitos diferentes:

  1. lanca_furada_48furos.step   — SÓLIDO da ponta da lança, para desenho e cliente.
                                   NÃO é malhável junto com o tanque (ver §mesh abaixo).

  2. dominio_1furo_vof.step      — DOMÍNIO FLUIDO de UM furo, para VOF transiente.
                                   É a rodada que mede o diâmetro de bolha em jato.

Por que só um furo: resolver Ø1,0 mm exige célula de 0,125 mm. Uma caixa de refino
de 10×10×20 mm por furo dá 1,0e6 células; os 768 furos do aerador dariam 7,9e8, e
uma lança sozinha (48 furos) já daria 4,9e7. O domínio de um furo fica em ~7e5.
"""
import math
import cadquery as cq

# ── Tubo 2½" Sch40 ────────────────────────────────────────────────────────
OD, ID = 73.0, 62.68
PAREDE = (OD - ID) / 2                      # 5,16 mm

# ── Padrão de furação (RELATORIO §8.4) ────────────────────────────────────
D_FURO = 1.0
N_ANEL = 24                                 # por anel
Z_ANEL1, Z_ANEL2 = 30.0, 45.0               # cotas dos anéis acima da tampa
DEFASAGEM = math.pi / N_ANEL                # meio passo entre os anéis

# ── Lança (só a ponta; o tubo sobe até a superfície) ──────────────────────
L_TRECHO = 400.0
T_TAMPA = 6.0

# ── Domínio VOF de um furo ────────────────────────────────────────────────
VOF_L, VOF_W = 20.0, 20.0                   # extensão radial e transversal
VOF_ABAIXO, VOF_ACIMA = 15.0, 45.0          # espaço para a bolha formar e subir
D_PLENO, L_PLENO = 6.0, 4.0                 # câmara de ar atrás da parede


def lanca_solida():
    """Ponta da lança: tubo + tampa cega + 48 furos radiais."""
    corpo = (cq.Workplane("XY")
             .circle(OD / 2).circle(ID / 2)
             .extrude(L_TRECHO))
    tampa = cq.Workplane("XY").circle(OD / 2).extrude(T_TAMPA)
    lanca = corpo.union(tampa)

    brocas = []
    for z, fase in ((Z_ANEL1, 0.0), (Z_ANEL2, DEFASAGEM)):
        for k in range(N_ANEL):
            a = fase + 2 * math.pi * k / N_ANEL
            brocas.append(cq.Solid.makeCylinder(
                D_FURO / 2, OD,                              # da linha de centro para fora
                cq.Vector(0, 0, z),
                cq.Vector(math.cos(a), math.sin(a), 0)))
    return lanca.cut(cq.Compound.makeCompound(brocas))


def dominio_vof():
    """Fluido ao redor de UM furo: xarope + furo + pleno de ar.

    Parede em x = 0 (face externa).  O furo atravessa a espessura, de
    x = −PAREDE a x = 0, e descarrega radialmente no xarope.
    A curvatura do tubo é desprezada: sobre 1 mm de furo num Ø73, a flecha
    é de 0,003 mm.
    """
    xarope = (cq.Workplane("YZ")
              .rect(VOF_W, VOF_ABAIXO + VOF_ACIMA)
              .extrude(VOF_L)
              .translate((0, 0, (VOF_ACIMA - VOF_ABAIXO) / 2)))

    furo = (cq.Workplane("YZ").circle(D_FURO / 2)
            .extrude(-PAREDE))

    pleno = (cq.Workplane("YZ").workplane(offset=-PAREDE)
             .circle(D_PLENO / 2).extrude(-L_PLENO))

    return xarope.union(furo).union(pleno)


if __name__ == "__main__":
    print("=" * 72)
    print("  LANÇA PERFURADA — ponto de projeto do RELATORIO §8.4")
    print("=" * 72)

    a_furo = math.pi / 4 * (D_FURO / 1000) ** 2
    n_tot = 2 * N_ANEL
    print(f"\n  tubo             : 2½\" Sch40 · OD {OD} · ID {ID} · parede {PAREDE:.2f} mm")
    print(f"  furos            : {n_tot} × Ø{D_FURO} mm  ({N_ANEL} por anel, 2 anéis)")
    print(f"  passo circunfer. : {math.pi*OD/N_ANEL:.2f} mm  (ligamento {math.pi*OD/N_ANEL-D_FURO:.2f} mm)")
    print(f"  passo axial      : {Z_ANEL2-Z_ANEL1:.0f} mm")
    print(f"  área total furos : {n_tot*a_furo*1e6:.2f} mm²")
    print(f"  área da ponta Ø{ID:.1f}: {math.pi/4*ID**2:.1f} mm²"
          f"  →  {math.pi/4*ID**2/(n_tot*a_furo*1e6):.0f}× a dos furos")
    print("     ⇒ sem TAMPA CEGA o ar sai todo pela ponta e a furação não faz efeito.")

    lanca = lanca_solida()
    cq.exporters.export(lanca, "lanca_furada_48furos.step")
    print(f"\n  → lanca_furada_48furos.step   ({len(lanca.solids().vals())} sólido,"
          f" {len(lanca.faces().vals())} faces)")

    dom = dominio_vof()
    v = dom.val().Volume()
    cq.exporters.export(dom, "dominio_1furo_vof.step")
    print(f"  → dominio_1furo_vof.step      ({v:.1f} mm³,"
          f" {len(dom.faces().vals())} faces)")
    print(f"\n  Domínio VOF: xarope {VOF_L}×{VOF_W}×{VOF_ABAIXO+VOF_ACIMA} mm"
          f" · furo Ø{D_FURO}×{PAREDE:.2f} · pleno Ø{D_PLENO}×{L_PLENO}")
    print(f"  Saída do furo na origem; gravidade em −z; entrada de ar em x = "
          f"{-(PAREDE+L_PLENO):.2f}")
