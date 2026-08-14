"""
gen_aerador_16lancas.py — DOMÍNIO FLUIDO do aerador com o novo arranjo de lanças (Fase 3 · Ito)

Decisão do cliente (06/08/2026): aerador APENAS COM LANÇAS, sem ejetor, com liberdade de
número, diâmetro, cota de descarga e furos.

ARRANJO DIMENSIONADO em `algebra_lancas.py`:
    16 lanças · Ø2½" Sch40 (ID 62,7 · OD 73,0) · descarga em z = −5.246,5 mm
    furos de 1,0 mm concentrados na ponta

DISTRIBUIÇÃO RADIAL — dois anéis de ÁREA EQUIVALENTE (cada lança serve ~1/16 da seção):
    anel interno:  5 lanças em r = 375 mm
    anel externo: 11 lanças em r = 770 mm
    (um anel único encostaria todo o ar na parede e deixaria o centro sem aeração)

Saída: `aerador_16lancas_fluido.step` — só o AERADOR, sem reator.
Convenção: mm, mesmo sistema do `sugar_dominio_fluido_completo.step`.
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))
TANQUE = os.path.join(OUT, "_tanque.step")

# ── Aerador (sólido 2 do STEP do cliente) ─────────────────────────────────
AER_X, AER_Y = 200.0, -440.0
AER_R        = 1016.0
AER_ZTOP     = 1220.0

# ── Lanças ────────────────────────────────────────────────────────────────
LANCA_ID, LANCA_OD = 62.7, 73.0          # 2½" Sch40
Z_TOPO     = 1840.8                       # entrada (mantida do arranjo original)
Z_DESCARGA = -5246.5                      # ponta / descarga

ANEIS = [(5, 375.0, 0.0), (11, 770.0, math.pi/11)]   # (n, raio, defasagem angular)


def cil(d, h, x, y, z, dr=(0, 0, 1)):
    return cq.Solid.makeCylinder(d/2, h, cq.Vector(x, y, z), cq.Vector(*dr))


def posicoes():
    pos = []
    for n, r, fase in ANEIS:
        for k in range(n):
            a = fase + 2*math.pi*k/n
            pos.append((AER_X + r*math.cos(a), AER_Y + r*math.sin(a), r))
    return pos


def build():
    tanque = cq.importers.importStep(TANQUE)
    solidos = tanque.solids().vals()
    aer = next(s for s in solidos if 15e9 < s.Volume() < 26e9)
    print(f"  aerador isolado: V = {aer.Volume()/1e9:.2f} m³")

    pos = posicoes()
    H = Z_TOPO - Z_DESCARGA

    # 1) as lanças DESLOCAM líquido → cortar o OD do domínio do tanque
    od = None
    for (x, y, _) in pos:
        t = cil(LANCA_OD, H, x, y, Z_DESCARGA)
        od = t if od is None else od.fuse(t)
    fluido = aer.cut(od)

    # 2) o INTERIOR das lanças é domínio fluido → somar o ID
    ins = None
    for (x, y, _) in pos:
        t = cil(LANCA_ID, H, x, y, Z_DESCARGA)
        ins = t if ins is None else ins.fuse(t)
    fluido = fluido.fuse(ins)

    return fluido.clean(), pos


if __name__ == "__main__":
    fl, pos = build()
    bb = fl.BoundingBox()
    print("="*76)
    print("  AERADOR + 16 LANÇAS — domínio fluido (Fase 3)")
    print("="*76)
    print(f"\n  Lanças: {len(pos)} × Ø{LANCA_ID:.1f} int / Ø{LANCA_OD:.1f} ext (2½\" Sch40)")
    print(f"  Comprimento: {Z_TOPO - Z_DESCARGA:.0f} mm  ·  z de {Z_TOPO:.0f} a {Z_DESCARGA:.0f}")
    print(f"  Submergência: {AER_ZTOP - Z_DESCARGA:.0f} mm\n")
    print("  Distribuição radial (dois anéis de área equivalente):")
    for n, r, _ in ANEIS:
        corda = 2*r*math.sin(math.pi/n)
        print(f"    {n:2d} lanças em r = {r:5.0f} mm  ·  corda entre centros = {corda:5.0f} mm"
              f"  (OD {LANCA_OD:.0f})")
    print(f"    raio do aerador = {AER_R:.0f} mm · folga da externa à parede = "
          f"{AER_R - ANEIS[-1][1] - LANCA_OD/2:.0f} mm")
    print(f"\n  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m³")
    print(f"  bbox X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] Z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    p = os.path.join(OUT, "aerador_16lancas_fluido.step")
    cq.exporters.export(fl, p)
    print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e6:.2f} MB)")
