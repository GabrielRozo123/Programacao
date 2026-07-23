"""
gen_lanca_dominio.py — DOMÍNIO DE FLUIDO da LANÇA INTEIRA do ejetor (1 de 4).

Monta o volume interno de fluido de uma lança completa, do bocal motriz no topo,
passando pelo VENTURI (redução 4"->2½") + PORTA DE AR (1½"), descendo os 3 m da
lança 2½", até o BICO (4×Ø15) e a descarga no xarope.

Fontes (desenho CSA01-300-000 Rev01 + peça CSA01-300-001):
  - Cadeia vertical (CORTE A-A): 4" ~180 · válvula borboleta ~212 · redução+ar ~351 · lança 3000
  - Ar: VÁLVULA ESFERA 1½" (item 18) + CONECTOR 1½" (item 5), ~50 mm abaixo da redução
  - Tubos: 8"→4"(ID102,3)→red.4"×2½"→2½"(ID62,7)→2"Sch160(ID49,25 no suporte do bico)
  - Bico: 4×Ø15, PCD Ø24, plug 45 mm (as-built, reto). Ver bico_v3_notas.md

Convenção: z=0 no bocal MOTRIZ (topo); z cresce p/ JUSANTE (descarga no fim).
Aproximações (spools retos não mudam a física) sinalizadas com ~. Cotas finas de
redução/porta de ar = premissa de fitting padrão (Ito crava se quiser).
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))

# --- diâmetros internos (mm) ---
ID_8  = 202.7   # 8" Sch40 (header) - representado só como plenum de entrada
ID_4  = 102.3   # 4" Sch40
ID_25 = 62.7    # 2½" Sch40 (lança)
ID_2  = 49.25   # 2" Sch160 (suporte do bico)
ID_AR = 40.9    # 1½" Sch40 (ar)

# --- comprimentos verticais (mm) ---
L_MOT   = 180.0   # trecho 4" (motriz, do header)
L_VALV  = 212.0   # spool da válvula borboleta (4")
L_RED1  = 90.0    # redução concêntrica 4"->2½" (o VENTURI) ~
Z_AR    = 50.0    # porta de ar ~50 abaixo do fim da redução
L_LANCA = 3000.0  # lança 2½"
L_RED2  = 50.0    # redução 2½"->2" junto ao bico ~
L_FEED2 = 25.0    # trecho 2" (suporte do bico) ~
# bico
D_HEAD, H_TOT = 50.0, 45.0
PCD, D_FURO = 24.0, 15.0
# descarga
D_DISCH, L_DISCH = 120.0, 120.0


def cyl(r, z0, z1):
    return cq.Solid.makeCylinder(r, z1 - z0, pnt=cq.Vector(0, 0, z0), dir=cq.Vector(0, 0, 1))

def cone(r0, r1, z0, z1):
    return cq.Solid.makeCone(r0, r1, z1 - z0, pnt=cq.Vector(0, 0, z0), dir=cq.Vector(0, 0, 1))


def lanca_dominio():
    z = 0.0
    parts = []
    # 1) motriz 4"
    parts.append(cyl(ID_4/2, z, z+L_MOT)); z += L_MOT
    # 2) spool válvula 4"
    parts.append(cyl(ID_4/2, z, z+L_VALV)); z += L_VALV
    # 3) VENTURI: redução 4"->2½"
    z_ven0 = z
    parts.append(cone(ID_4/2, ID_25/2, z, z+L_RED1)); z += L_RED1
    z_throat = z  # fim do venturi (garganta 2½")
    # 4) porta de AR 1½" radial, ~Z_AR abaixo do venturi
    z_ar = z_throat + Z_AR
    ar = cq.Solid.makeCylinder(ID_AR/2, 60.0,
                               pnt=cq.Vector(ID_25/2 + 60, 0, z_ar),
                               dir=cq.Vector(-1, 0, 0))
    # 5) lança 2½" (3 m) — inclui o trecho do Z_AR
    parts.append(cyl(ID_25/2, z, z+L_LANCA)); z += L_LANCA
    # 6) redução 2½"->2" no bico
    parts.append(cone(ID_25/2, ID_2/2, z, z+L_RED2)); z += L_RED2
    # 7) trecho 2" (suporte do bico) — alimenta os furos
    parts.append(cyl(ID_2/2, z, z+L_FEED2)); z += L_FEED2
    z_bico_top = z
    # 8) BICO: só os 4 furos Ø15 atravessam o plug de 45 mm
    for k in range(4):
        a = math.radians(90*k)
        x, y = (PCD/2)*math.cos(a), (PCD/2)*math.sin(a)
        parts.append(cq.Solid.makeCylinder(D_FURO/2, H_TOT,
                     pnt=cq.Vector(x, y, z_bico_top), dir=cq.Vector(0, 0, 1)))
    z += H_TOT
    z_disch = z
    # 9) descarga
    parts.append(cyl(D_DISCH/2, z, z+L_DISCH)); z += L_DISCH

    fluid = parts[0]
    for p in parts[1:]:
        fluid = fluid.fuse(p)
    fluid = fluid.fuse(ar)          # porta de ar
    fluid = fluid.clean()
    return fluid, dict(z_ven0=z_ven0, z_throat=z_throat, z_ar=z_ar,
                       z_bico_top=z_bico_top, z_disch=z_disch, z_total=z)


print("== DOMÍNIO DE FLUIDO — LANÇA INTEIRA ==")
fl, marks = lanca_dominio()
ok = fl.isValid(); bb = fl.BoundingBox()
print(f"  valid={ok}  vol={fl.Volume()/1e3:.1f} cm3  altura={bb.zlen:.0f} mm  "
      f"Ø_max={max(bb.xlen,bb.ylen):.0f} mm")
print("  marcos (z, mm):", {k: round(v,1) for k,v in marks.items()})
p = os.path.join(OUT, "dominio_fluido_lanca_completa.step")
cq.exporters.export(fl, p)
print("STEP:", p, f"({os.path.getsize(p)} bytes)")
