"""
gen_aerador_16lancas.py — DOMÍNIO FLUIDO do aerador com o novo arranjo de lanças (Fase 3 · Ito)

Decisão do cliente (06/08/2026): aerador APENAS COM LANÇAS, sem ejetor, com liberdade de
número, diâmetro, cota de descarga e furos. Arranjo dimensionado em `algebra_lancas.py`.

⚠️ REVISÃO — o aerador tem FUNDO CÔNICO (medido no STEP do cliente):
       z = −4.369  →  r = 1.016 mm   (fim da parte cilíndrica)
       z = −5.246  →  r =   580 mm
       z = −5.892  →  r =   260 mm   (fundo)
   O anel externo (r = 770, borda em 806) atravessaria a parede do cone.
   ⇒ DESCARGA ESCALONADA: cada anel para na cota mais funda que o cone permite.
   O script VERIFICA ponto a ponto, ao longo de toda a lança, em vez de assumir.

Saída: `aerador_16lancas_fluido.step` — só o AERADOR, sem reator.
Convenção: mm, mesmo sistema do STEP do cliente.
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))
TANQUE = os.path.join(OUT, "_tanque.step")

AER_X, AER_Y, AER_R = 200.0, -440.0, 1016.0
AER_ZTOP, AER_ZFUNDO = 1220.0, -5892.0

LANCA_ID, LANCA_OD = 62.7, 73.0           # 2½" Sch40
Z_TOPO = 1220.0                            # ⚠️ RENTE à superfície livre — sem tocos salientes
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
    preciso = r_lanca + LANCA_OD/2 + FOLGA_PAREDE
    if preciso >= AER_R:
        return None                      # não cabe nem na parte cilíndrica
    if preciso <= CONE_R0:
        return AER_ZFUNDO                # cabe até o fundo do cone
    return (preciso - CONE_R0)/CONE_K + AER_ZFUNDO


def verifica(r_lanca, z_desc, passo=25.0):
    """Confere a lança inteira contra o perfil do tanque. Devolve a folga mínima."""
    z, pior = z_desc, 1e9
    while z <= AER_ZTOP:
        pior = min(pior, raio_tanque(z) - (r_lanca + LANCA_OD/2))
        z += passo
    return pior


def cil(d, h, x, y, z):
    return cq.Solid.makeCylinder(d/2, h, cq.Vector(x, y, z), cq.Vector(0, 0, 1))


def build():
    tanque = cq.importers.importStep(TANQUE)
    aer = next(s for s in tanque.solids().vals() if 15e9 < s.Volume() < 26e9)
    print(f"  aerador isolado: V = {aer.Volume()/1e9:.2f} m³")

    lancas, od, ins = [], None, None
    for n, r, fase in ANEIS:
        zmin = z_minimo(r)
        z_desc = math.ceil((zmin + 40.0)/10)*10          # 40 mm de margem extra, arredondado
        folga = verifica(r, z_desc)
        print(f"  anel r={r:5.0f}: {n:2d} lanças · z mín geométrico {zmin:8.1f} → "
              f"descarga {z_desc:8.1f} · folga mínima à parede {folga:5.1f} mm")
        assert folga > 0, f"lança em r={r} ainda atravessa a parede"
        for k in range(n):
            a = fase + 2*math.pi*k/n
            x, y = AER_X + r*math.cos(a), AER_Y + r*math.sin(a)
            lancas.append((x, y, r, z_desc))
            h = Z_TOPO - z_desc
            t_od, t_id = cil(LANCA_OD, h, x, y, z_desc), cil(LANCA_ID, h, x, y, z_desc)
            od  = t_od if od  is None else od.fuse(t_od)
            ins = t_id if ins is None else ins.fuse(t_id)

    return aer.cut(od).fuse(ins).clean(), lancas


if __name__ == "__main__":
    print("="*78)
    print("  AERADOR + 16 LANÇAS — domínio fluido (Fase 3) · REVISADO")
    print("="*78)
    print("\n  Perfil do aerador (medido no STEP do cliente):")
    for z in (1220, -4000, -4369, -4650, -5000, -5246, -5892):
        print(f"     z = {z:7.0f}  →  r = {raio_tanque(z):6.1f} mm")
    print()
    fl, lancas = build()
    bb = fl.BoundingBox()

    print(f"\n  Lanças: {len(lancas)} × Ø{LANCA_ID:.1f} int / Ø{LANCA_OD:.1f} ext (2½\" Sch40)")
    print(f"  Topo (entrada de xarope): z = {Z_TOPO:.0f}  (rente à superfície livre)")
    print("\n  Comprimento e submergência por anel:")
    for n, r, _ in ANEIS:
        zd = next(l[3] for l in lancas if l[2] == r)
        comp, subm = Z_TOPO - zd, AER_ZTOP - zd
        v = (130.0/3600/16)/(math.pi/4*(LANCA_ID/1000)**2)
        dp = 32*6.5*(comp/1000)*v/(LANCA_ID/1000)**2
        print(f"    {n:2d} lanças em r={r:5.0f}: comp {comp:6.0f} mm · submergência {subm:6.0f} mm"
              f" · ΔP {dp/1e5:4.2f} bar")

    print(f"\n  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m³")
    print(f"  bbox X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] Z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    print(f"  ⇒ topo do domínio = {bb.zmax:.0f} (lanças) · fundo = {bb.zmin:.0f} (cone do aerador)")
    p = os.path.join(OUT, "aerador_16lancas_fluido.step")
    cq.exporters.export(fl, p)
    print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e6:.2f} MB)")
