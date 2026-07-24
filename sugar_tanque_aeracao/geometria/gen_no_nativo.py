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
R_DISCH = 60.0  # descarga Ø120

# --- os DOIS padrões de furo (a divergência dos desenhos) ---
BICOS = {
    # medido no STEP nativo do conjunto: 1 central + 6 a r13,5 (hex, PCD Ø27)
    "7xD9":  dict(r_hole=4.5, pcd_r=13.5, n=6, center=True,
                  desc="7xØ9 PCD Ø27 (modelo 3D nativo)"),
    # desenho de peça CSA01-300-001 Rev00 (22/07/2023, o mais NOVO): 4xØ15 PCD Ø24
    "4xD15": dict(r_hole=7.5, pcd_r=12.0, n=4, center=False,
                  desc="4xØ15 PCD Ø24 (desenho de peça, mais novo)"),
}

L_IN   = 280.0   # air->reducer ~240mm (fiel ao nativo: Y542->Y302)
Z_AR   = 40.0
L_RED  = 50.0   # redução 4"->assento (~27° como no nativo)
L_SEAT = 5.0
L_PLUG = 45.0   # espessura do bico (furos passam)
L_DISCH= 120.0

def cyl(r,z0,z1): return cq.Solid.makeCylinder(r,z1-z0,pnt=cq.Vector(0,0,z0),dir=cq.Vector(0,0,1))
def cone(r0,r1,z0,z1): return cq.Solid.makeCone(r0,r1,z1-z0,pnt=cq.Vector(0,0,z0),dir=cq.Vector(0,0,1))

def hole_positions(b):
    pos=[(0.0,0.0)] if b["center"] else []
    for k in range(b["n"]):
        a=math.radians(360.0/b["n"]*k)
        pos.append((b["pcd_r"]*math.cos(a), b["pcd_r"]*math.sin(a)))
    return pos

def no_nativo(bico="7xD9"):
    b=BICOS[bico]; R_HOLE=b["r_hole"]
    z=0.0; parts=[]
    parts.append(cyl(R_4,z,z+L_IN)); z+=L_IN                    # 4" motriz
    # porta de ar 1½" radial (ao longo de X) em z=Z_AR — PENETRA 15 mm no furo 4" p/ conectar o fluido
    ar=cq.Solid.makeCylinder(R_AR,70.0,pnt=cq.Vector(R_4+55,0,Z_AR),dir=cq.Vector(-1,0,0))
    parts.append(cone(R_4,R_SEAT,z,z+L_RED)); z+=L_RED          # redução 4"->assento
    parts.append(cyl(R_SEAT,z,z+L_SEAT)); z+=L_SEAT            # assento (alimenta furos)
    z_bico=z
    for (x,y) in hole_positions(b):                            # BICO (padrão escolhido)
        parts.append(cq.Solid.makeCylinder(R_HOLE,L_PLUG,pnt=cq.Vector(x,y,z_bico),dir=cq.Vector(0,0,1)))
    z+=L_PLUG
    parts.append(cyl(R_DISCH,z,z+L_DISCH)); z+=L_DISCH          # descarga
    fl=parts[0]
    for p in parts[1:]: fl=fl.fuse(p)
    fl=fl.fuse(ar).clean()
    return fl, dict(z_ar=Z_AR, z_red=L_IN, z_bico=z_bico, z_total=z)

print("== NÓ DE AERAÇÃO (cotas do STEP nativo) — 4\" + ar 1½\" + reducao + BICO + descarga ==")
saidas={"7xD9":"dominio_fluido_no_NATIVO_7furos.step",
        "4xD15":"dominio_fluido_no_4furosD15.step"}
for key,fname in saidas.items():
    b=BICOS[key]
    fl,m=no_nativo(key)
    bb=fl.BoundingBox()
    nh=b["n"]+(1 if b["center"] else 0)
    Ah=nh*math.pi*b["r_hole"]**2
    ND4=nh*(2*b["r_hole"])**4
    print(f"\n  [{key}] {b['desc']}")
    print(f"    valid={fl.isValid()} vol={fl.Volume()/1e3:.1f} cm3 altura={bb.zlen:.0f} mm")
    print(f"    {nh} furos | area aberta={Ah:.0f} mm2 | N.D^4={ND4:,.0f} mm^4")
    p_=os.path.join(OUT,fname)
    cq.exporters.export(fl,p_)
    print(f"    -> {fname} ({os.path.getsize(p_)} bytes)")
