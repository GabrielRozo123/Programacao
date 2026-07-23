"""
gen_no_nativo.py — DOMÍNIO DE FLUIDO do nó de aeração, EXTRAÍDO DO STEP NATIVO do cadista (Brendo).

Fonte: 00__CONJUNTO_EJETOR.stp (nativo, sólido analítico limpo — 490 sólidos).
Medições diretas (lança X=0), confirmam TODA a nossa análise:
  - Header 8" ao longo de X · lanças 2½" ao longo de Y · PORTAS DE AR 1½" ao longo de Z (laterais). ✅
  - Ar entra pela VÁLVULA 1½" lateral (Brendo apontou a seta) — "a única entrada que tem é essa".
  - Furos Ø7 do bico = RADIAIS (X/Z), 16 no total = 4 por bico → FIXAÇÃO. ✅
  - BICO nativo = **7 × Ø9 (r4,5) hexagonal em PCD Ø27** (1 central + 6 a r13,5) — medido exato.
    (O desenho de peça CSA01-300-001 trazia 4×Ø15; o MODELO nativo do conjunto usa 7×Ø9 — confirmar
     com o Ito qual é o de produção; aqui uso o nativo.)

Topologia da lança (medida, Y do header ao fundo):
  8" header → 4" (r51,15) → válvula borboleta → AR 1½" (Y≈542) → redução 27,9° → BICO 7×Ø9 (Y≈174–224)
  → válvula → 4" → redução 22° → lança 2½" (r31,4) × 3 m → redução → header 8" inferior.

Este script constrói o NÓ (zona da física da bolha): 4" + ar 1½" + redução + bico 7×Ø9 + descarga.
Cotas todas do nativo. Flow ao longo de +Z aqui; ar ao longo de X.
"""
import cadquery as cq
import math, os
OUT = os.path.dirname(os.path.abspath(__file__))

R_4  = 51.15    # 4" ID (medido)
R_AR = 19.05    # 1½" bore da válvula de ar (medido)
R_SEAT = 26.0   # assento do bico (Ø52) — recebe o bico Ø50
R_HOLE = 4.5    # Ø9 furos de xarope (medido)
PCD_R = 13.5    # 6 furos a r13,5 (PCD Ø27) + 1 central (medido)
R_DISCH = 60.0  # descarga Ø120

L_IN   = 80.0
Z_AR   = 40.0
L_RED  = 50.0   # redução 4"->assento (~27° como no nativo)
L_SEAT = 5.0
L_PLUG = 45.0   # espessura do bico (furos passam)
L_DISCH= 120.0

def cyl(r,z0,z1): return cq.Solid.makeCylinder(r,z1-z0,pnt=cq.Vector(0,0,z0),dir=cq.Vector(0,0,1))
def cone(r0,r1,z0,z1): return cq.Solid.makeCone(r0,r1,z1-z0,pnt=cq.Vector(0,0,z0),dir=cq.Vector(0,0,1))

def hole_positions():
    pos=[(0.0,0.0)]
    for k in range(6):
        a=math.radians(60*k); pos.append((PCD_R*math.cos(a),PCD_R*math.sin(a)))
    return pos

def no_nativo():
    z=0.0; parts=[]
    parts.append(cyl(R_4,z,z+L_IN)); z+=L_IN                    # 4" motriz
    # porta de ar 1½" radial (ao longo de X) em z=Z_AR
    ar=cq.Solid.makeCylinder(R_AR,70.0,pnt=cq.Vector(R_4+70,0,Z_AR),dir=cq.Vector(-1,0,0))
    parts.append(cone(R_4,R_SEAT,z,z+L_RED)); z+=L_RED          # redução 4"->assento
    parts.append(cyl(R_SEAT,z,z+L_SEAT)); z+=L_SEAT            # assento (alimenta furos)
    z_bico=z
    for (x,y) in hole_positions():                             # BICO 7×Ø9
        parts.append(cq.Solid.makeCylinder(R_HOLE,L_PLUG,pnt=cq.Vector(x,y,z_bico),dir=cq.Vector(0,0,1)))
    z+=L_PLUG
    parts.append(cyl(R_DISCH,z,z+L_DISCH)); z+=L_DISCH          # descarga
    fl=parts[0]
    for p in parts[1:]: fl=fl.fuse(p)
    fl=fl.fuse(ar).clean()
    return fl, dict(z_ar=Z_AR, z_red=L_IN, z_bico=z_bico, z_total=z)

print("== NÓ DE AERAÇÃO (do STEP nativo) — 4\" + ar 1½\" + reducao + BICO 7×Ø9 + descarga ==")
fl,m=no_nativo()
bb=fl.BoundingBox()
print(f"  valid={fl.isValid()} vol={fl.Volume()/1e3:.1f} cm3 altura={bb.zlen:.0f} Ø_max={max(bb.xlen,bb.ylen):.0f}")
print("  marcos:",{k:round(v,1) for k,v in m.items()})
p=os.path.join(OUT,"dominio_fluido_no_NATIVO_7furos.step")
cq.exporters.export(fl,p); print("STEP:",os.path.basename(p),f"({os.path.getsize(p)} bytes)")
