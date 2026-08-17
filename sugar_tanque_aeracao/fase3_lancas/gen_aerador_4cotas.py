"""
gen_aerador_4cotas.py — aerador com lanças em QUATRO COTAS de descarga (Fase 3 · estudo)

Motivação (§8.6 do relatório): os 84,6 % de xarope não atingido não são falta de
cobertura lateral — com 16 lanças o espaçamento já é 450 mm. É ausência de transporte
vertical. A variável de projeto pertinente é o número de COTAS, não de lanças.

Arranjo proposto para o estudo: 24 lanças em 4 cotas de 6, em dois raios alternados,
com defasagem angular entre cotas para evitar colisão em planta.

Topologia idêntica à do STEP anterior: cada lança é um cilindro subtraído do fluido,
com a lateral (parede) e o disco da ponta (injetor). No STAR cada disco recebe
Mass Flow Inlet com a vazão de ar do grupo e o SMD prescrito — os 32 furos reais de
cada lança não são resolvidos, e não precisam ser: 32 jatos radiais têm momento
líquido nulo, restando fonte de massa e empuxo.

Saída: `aerador_4cotas_fluido.step`
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(OUT, "..", "geometria", "sugar_dominio_fluido_completo.step")

AER_X, AER_Y, AER_R = 200.0, -440.0, 1016.0
AER_ZTOP, AER_ZFUNDO = 1220.0, -5892.0
D_LANCA = 62.7
Z_TOPO = 1220.0
FOLGA_PAREDE = 50.0
CONE_R0, CONE_K = 259.5, 0.4966
Z_INICIO_CONE = -4368.6

# (n lanças, raio, defasagem angular, cota de descarga)
COTAS = [
    (6, 700.0, 0.0,             -4800.0),
    (6, 400.0, math.pi/6,       -3400.0),
    (6, 700.0, math.pi/6,       -2000.0),
    (6, 400.0, 0.0,              -600.0),
]

def raio_tanque(z):
    return AER_R if z >= Z_INICIO_CONE else CONE_R0 + CONE_K*(z - AER_ZFUNDO)

def z_minimo(r):
    preciso = r + D_LANCA/2 + FOLGA_PAREDE
    if preciso >= AER_R: return None
    if preciso <= CONE_R0: return AER_ZFUNDO
    return (preciso - CONE_R0)/CONE_K + AER_ZFUNDO

def verifica(r, z_desc, passo=25.0):
    z, pior = z_desc, 1e9
    while z <= AER_ZTOP:
        pior = min(pior, raio_tanque(z) - (r + D_LANCA/2)); z += passo
    return pior

def cil(dia, z0, z1, x, y):
    return cq.Solid.makeCylinder(dia/2, z1-z0, cq.Vector(x, y, z0), cq.Vector(0,0,1))

def aerador_liso():
    from OCP.BRep import BRep_Tool
    from OCP.GeomAdaptor import GeomAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    aer = next(s for s in cq.importers.importStep(BASE).solids().vals()
               if 15e9 < s.Volume() < 26e9)
    for f in aer.Faces():
        surf = GeomAdaptor_Surface(BRep_Tool.Surface_s(f.wrapped))
        if surf.GetType() != GeomAbs_Cylinder: continue
        c = surf.Cylinder(); R = c.Radius()
        if R > 200.0: continue
        bb, ax = f.BoundingBox(), c.Axis().Location()
        aer = aer.fuse(cil(2*R, bb.zmin, bb.zmax, ax.X(), ax.Y()))
    return aer.clean()

def build():
    aer = aerador_liso()
    lancas, vazio = [], None
    print(f"\n  {'cota':>10} {'lanças':>7} {'raio':>7} {'z mín':>10} {'folga':>8} {'submerg.':>10}")
    print("  " + "-"*58)
    for n, r, fase, z_desc in COTAS:
        zmin = z_minimo(r)
        assert zmin is not None and z_desc >= zmin, f"cota {z_desc} inviável em r={r} (mín {zmin:.0f})"
        folga = verifica(r, z_desc)
        print(f"  {z_desc:10.0f} {n:7d} {r:7.0f} {zmin:10.0f} {folga:7.1f} mm {AER_ZTOP-z_desc:9.0f} mm")
        for k in range(n):
            a = fase + 2*math.pi*k/n
            x, y = AER_X + r*math.cos(a), AER_Y + r*math.sin(a)
            lancas.append((x, y, r, z_desc, a))
            t = cil(D_LANCA, z_desc, Z_TOPO, x, y)
            vazio = t if vazio is None else vazio.fuse(t)
    # conferência de colisão em planta
    pior = 1e9
    for i in range(len(lancas)):
        for j in range(i+1, len(lancas)):
            dx = lancas[i][0]-lancas[j][0]; dy = lancas[i][1]-lancas[j][1]
            pior = min(pior, math.hypot(dx, dy) - D_LANCA)
    print(f"\n  menor folga entre lanças em planta: {pior:.0f} mm")
    assert pior > 0, "lanças colidem"
    return aer.cut(vazio).clean(), lancas

if __name__ == "__main__":
    print("="*74)
    print("  AERADOR · 24 LANÇAS EM 4 COTAS DE DESCARGA — domínio fluido")
    print("="*74)
    fl, lancas = build()
    bb = fl.BoundingBox()
    Q_ar = 40.0
    n_furos_total = 769
    print(f"\n  Distribuição de ar ({Q_ar:.0f} m³/h no total):")
    for n, r, _, z in COTAS:
        print(f"    cota z={z:6.0f}: {n} lanças · {Q_ar*n/len(lancas):5.2f} m³/h no grupo · "
              f"{Q_ar/len(lancas)*1000:5.0f} L/h por lança · {n_furos_total//len(lancas)} furos por lança")
    a_inj = math.pi/4*D_LANCA**2
    print(f"\n  Inventário de faces no STAR-CCM+:")
    print(f"    aerador.injetores : {len(lancas)} discos de {a_inj:.1f} mm² — um por cota, agrupar por grupo")
    print(f"    aerador.lancas    : {len(lancas)} cilindros Ø{D_LANCA}")
    print(f"    aerador.topo      :  1 face em z=1220")
    print(f"    aerador.parede    :  3 faces")
    print(f"\n  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m³ | faces = {len(fl.Faces())}")
    print(f"  bbox Z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    p = os.path.join(OUT, "aerador_4cotas_fluido.step")
    cq.exporters.export(fl, p)
    print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e6:.2f} MB)")
