"""
gen_aerador_16lancas.py — DOMÍNIO FLUIDO do aerador com o novo arranjo de lanças (Fase 3 · Ito)

Decisão do cliente (06/08/2026): aerador APENAS COM LANÇAS, sem ejetor, com liberdade de
número, diâmetro e cota de descarga. Arranjo dimensionado em `algebra_lancas.py`.

⚠️ TOPOLOGIA — igual à do STEP original de 3 lanças (medida, não suposta):
   cada lança é UM CILINDRO SUBTRAÍDO do fluido, com exatamente 2 faces:
       · a lateral cilíndrica          -> parede da lança   (`aerador.lancas`)
       · o disco plano na ponta        -> stagnation inlet  (`aerador.injetores`)
   NÃO é um tubo. Não há parede interna/externa, não há face de topo, nada
   sobressai da superfície livre. O escoamento dentro da lança não é resolvido
   pelo CFD — entra pelo disco da ponta com a pressão total imposta.

⚠️ FUNDO CÔNICO (medido no STEP do cliente):
       z = −4368,6  →  r = 1016 mm   (fim da parte cilíndrica)
       z = −5246,5  →  r =  580 mm
       z = −5892,0  →  r =  260 mm   (fundo)
   ⇒ DESCARGA ESCALONADA: cada anel para na cota mais funda que o cone permite.
   O script VERIFICA ponto a ponto, ao longo de toda a lança, em vez de assumir.

Base: o aerador do STEP do cliente, com as 3 lanças originais TAPADAS (o arranjo
novo substitui o antigo). Saída: `aerador_16lancas_fluido.step` — só o AERADOR.
Convenção: mm, mesmo sistema do STEP do cliente.
"""
import cadquery as cq
import math, os

from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(OUT, "..", "geometria", "sugar_dominio_fluido_completo.step")

AER_X, AER_Y, AER_R = 200.0, -440.0, 1016.0
AER_ZTOP, AER_ZFUNDO = 1220.0, -5892.0

D_LANCA = 62.7                             # Ø interno 2½" Sch40 — é a área de escoamento
Z_TOPO = 1220.0                            # rente à superfície livre, sem tocos salientes
FOLGA_PAREDE = 50.0                        # mm entre a lança e a parede do cone

# perfil do cone, ajustado às medidas: r(z) = R0 + K·(z − z_fundo)
CONE_R0, CONE_K = 259.5, 0.4966
Z_INICIO_CONE = -4368.6

ANEIS = [(5, 375.0, 0.0), (11, 770.0, math.pi/11)]


def raio_tanque(z):
    """Raio interno do aerador na cota z."""
    if z >= Z_INICIO_CONE:
        return AER_R
    return CONE_R0 + CONE_K*(z - AER_ZFUNDO)


def z_minimo(r_lanca):
    """Cota mais FUNDA em que uma lança em `r_lanca` ainda cabe, com folga."""
    preciso = r_lanca + D_LANCA/2 + FOLGA_PAREDE
    if preciso >= AER_R:
        return None                      # não cabe nem na parte cilíndrica
    if preciso <= CONE_R0:
        return AER_ZFUNDO                # cabe até o fundo do cone
    return (preciso - CONE_R0)/CONE_K + AER_ZFUNDO


def verifica(r_lanca, z_desc, passo=25.0):
    """Confere a lança inteira contra o perfil do tanque. Devolve a folga mínima."""
    z, pior = z_desc, 1e9
    while z <= AER_ZTOP:
        pior = min(pior, raio_tanque(z) - (r_lanca + D_LANCA/2))
        z += passo
    return pior


def cil(d, z0, z1, x, y):
    return cq.Solid.makeCylinder(d/2, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def aerador_liso():
    """Aerador do cliente com as 3 lanças ORIGINAIS tapadas (detectadas, não chutadas)."""
    aer = next(s for s in cq.importers.importStep(BASE).solids().vals()
               if 15e9 < s.Volume() < 26e9)
    v0 = aer.Volume()

    achadas = []
    for f in aer.Faces():
        surf = GeomAdaptor_Surface(BRep_Tool.Surface_s(f.wrapped))
        if surf.GetType() != GeomAbs_Cylinder:
            continue
        c = surf.Cylinder()
        R = c.Radius()
        if R > 200.0:                                  # é o casco do tanque
            continue
        bb, ax = f.BoundingBox(), c.Axis().Location()
        achadas.append((R, ax.X(), ax.Y(), bb.zmin, bb.zmax))

    for R, x, y, zmin, zmax in achadas:
        print(f"    tapando lança original: Ø{2*R:.1f} em ({x:.0f},{y:.0f}) "
              f"z {zmin:.1f}..{zmax:.1f}")
        aer = aer.fuse(cil(2*R, zmin, zmax, x, y))
    aer = aer.clean()
    print(f"    volume {v0/1e9:.4f} -> {aer.Volume()/1e9:.4f} m³ "
          f"(+{(aer.Volume()-v0)/1e9:.4f} m³ recuperados)")
    return aer


def build():
    print("\n  Recuperando o aerador liso a partir do STEP do cliente:")
    aer = aerador_liso()

    print("\n  Novo arranjo:")
    lancas, vazio = [], None
    for n, r, fase in ANEIS:
        zmin = z_minimo(r)
        z_desc = math.ceil((zmin + 40.0)/10)*10          # 40 mm de margem extra, arredondado
        folga = verifica(r, z_desc)
        print(f"    anel r={r:5.0f}: {n:2d} lanças · z mín geométrico {zmin:8.1f} → "
              f"descarga {z_desc:8.1f} · folga mínima à parede {folga:5.1f} mm")
        assert folga > 0, f"lança em r={r} ainda atravessa a parede"
        for k in range(n):
            a = fase + 2*math.pi*k/n
            x, y = AER_X + r*math.cos(a), AER_Y + r*math.sin(a)
            lancas.append((x, y, r, z_desc))
            t = cil(D_LANCA, z_desc, Z_TOPO, x, y)
            vazio = t if vazio is None else vazio.fuse(t)

    return aer.cut(vazio).clean(), lancas


if __name__ == "__main__":
    print("="*78)
    print("  AERADOR + 16 LANÇAS — domínio fluido (Fase 3) · topologia do original")
    print("="*78)
    print("\n  Perfil do aerador (medido no STEP do cliente):")
    for z in (1220, -4000, -4369, -4650, -5000, -5246, -5892):
        print(f"     z = {z:7.0f}  →  r = {raio_tanque(z):6.1f} mm")

    fl, lancas = build()
    bb = fl.BoundingBox()

    print(f"\n  Lanças: {len(lancas)} × Ø{D_LANCA:.1f} (interno de 2½\" Sch40)")
    print(f"  Topo das lanças: z = {Z_TOPO:.0f} — rente à superfície livre")

    print("\n  Comprimento, submergência e ΔP por anel:")
    for n, r, _ in ANEIS:
        zd = next(l[3] for l in lancas if l[2] == r)
        comp, subm = Z_TOPO - zd, AER_ZTOP - zd
        v = (130.0/3600/len(lancas))/(math.pi/4*(D_LANCA/1000)**2)
        dp = 32*6.5*(comp/1000)*v/(D_LANCA/1000)**2
        print(f"    {n:2d} lanças em r={r:5.0f}: comp {comp:6.0f} mm · submergência {subm:6.0f} mm"
              f" · v {v:4.2f} m/s · ΔP {dp/1e5:4.2f} bar")

    a_inj = math.pi/4*D_LANCA**2
    print("\n  Inventário de faces esperado no STAR-CCM+:")
    print(f"    aerador.injetores : {len(lancas):2d} discos de {a_inj:9.1f} mm² (Ø{D_LANCA})")
    print(f"    aerador.lancas    : {len(lancas):2d} cilindros Ø{D_LANCA}")
    print(f"    aerador.topo      :  1 face em z={Z_TOPO:.0f} de "
          f"{math.pi*AER_R**2 - len(lancas)*a_inj:.1f} mm²")
    print(f"    aerador.parede    :  3 faces (casco Ø{2*AER_R:.0f}, cone, fundo)")

    print(f"\n  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m³ | "
          f"faces = {len(fl.Faces())}")
    print(f"  bbox X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] "
          f"Z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    p = os.path.join(OUT, "aerador_16lancas_fluido.step")
    cq.exporters.export(fl, p)
    print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e6:.2f} MB)")
