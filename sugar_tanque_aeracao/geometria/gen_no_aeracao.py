"""
gen_no_aeracao.py — DOMÍNIO do NÓ DE AERAÇÃO (venturi + porta de ar 1½" + bico).

Resolvido (revisão adversarial de 5 leitores + medição em pixel do desenho, 2026-07-23):
  O ar entra NO TOPO da lança, pela VÁLVULA ESFERA 1½" (item 18) + CONECTOR 1½" (item 5),
  teada RADIALMENTE na parede da GARGANTA 2" Sch160 (item 11), logo após a REDUÇÃO 4"→2"
  (item 9). A garganta acelera o xarope (venturi) -> depressão -> aspira o ar -> o BICO
  (multifuro) cisalha em microbolha logo em seguida. É um EDUCTOR de garganta com injeção
  LATERAL na TUBULAÇÃO — não no bico.
  Os 4 furos Ø7 do bico são ASSENTOS DE PARAFUSO ("PARA FIXAÇÃO"), cegos, ~3 mm curtos dos
  furos de vazão (medição: Ø7 entra 3,9 mm, sobra 3,0 mm de metal maciço). NÃO são via de ar.
  (Supersede o modelo bico_eductor_arlateral_* — aquele estava errado.)

Nó compacto (item 11 = 0,20 m / 4 lanças ≈ 50 mm/lança: garganta = suporte do bico):
  4" -> redução 4"→2" (venturi) -> garganta 2" [porta de ar 1½" lateral] -> BICO 4×Ø15 -> descarga
Convenção: z=0 entrada 4" (motriz); z cresce p/ jusante.
⚠️ Premissas (fitting padrão; cotas finas não muda a física): reducer ~90 mm; porta 1½" ID 40,9.
   Ainda em aberto p/ o Ito: sentido do escoamento e se o bico é co-locado (leitura mais forte) ou 3 m abaixo.
"""
import cadquery as cq
import math, os
OUT = os.path.dirname(os.path.abspath(__file__))

ID_4, ID_2, ID_AR = 102.3, 49.25, 40.9
L_IN, L_RED, L_THR = 50.0, 90.0, 35.0
# bico
D_SPIG, H_SPIG, D_HEAD, H_HEAD = 43.0, 18.0, 50.0, 27.0
PCD, D_X = 24.0, 15.0
D_DISCH, L_DISCH = 120.0, 120.0

def cyl(r,z0,z1): return cq.Solid.makeCylinder(r,z1-z0,pnt=cq.Vector(0,0,z0),dir=cq.Vector(0,0,1))
def cone(r0,r1,z0,z1): return cq.Solid.makeCone(r0,r1,z1-z0,pnt=cq.Vector(0,0,z0),dir=cq.Vector(0,0,1))

def no_aeracao():
    z=0.0; parts=[]
    parts.append(cyl(ID_4/2, z, z+L_IN)); z+=L_IN                 # 4" motriz
    parts.append(cone(ID_4/2, ID_2/2, z, z+L_RED)); z+=L_RED      # venturi 4"->2"
    z_thr0=z
    parts.append(cyl(ID_2/2, z, z+L_THR)); z+=L_THR              # garganta 2"
    z_bico=z                                                      # face do bico (spigot)
    # porta de ar 1½" radial, no meio da garganta
    z_ar=z_thr0+L_THR*0.4
    ar=cq.Solid.makeCylinder(ID_AR/2, 60.0, pnt=cq.Vector(ID_2/2+60,0,z_ar), dir=cq.Vector(-1,0,0))
    # bico: 4 furos Ø15 atravessam o plug de 45 mm
    for k in range(4):
        a=math.radians(90*k); x,y=PCD/2*math.cos(a),PCD/2*math.sin(a)
        parts.append(cq.Solid.makeCylinder(D_X/2, H_SPIG+H_HEAD, pnt=cq.Vector(x,y,z_bico), dir=cq.Vector(0,0,1)))
    z+=H_SPIG+H_HEAD
    parts.append(cyl(D_DISCH/2, z, z+L_DISCH)); z+=L_DISCH        # descarga
    fl=parts[0]
    for p in parts[1:]: fl=fl.fuse(p)
    fl=fl.fuse(ar).clean()
    return fl, dict(z_venturi0=L_IN, z_throat0=z_thr0, z_ar=z_ar, z_bico=z_bico, z_total=z)

print("== NÓ DE AERAÇÃO (venturi + ar lateral na tubulação + bico) ==")
fl,m=no_aeracao()
bb=fl.BoundingBox()
print(f"  valid={fl.isValid()} vol={fl.Volume()/1e3:.1f} cm3 altura={bb.zlen:.0f} mm")
print("  marcos:", {k:round(v,1) for k,v in m.items()})
p=os.path.join(OUT,"dominio_fluido_no_aeracao.step")
cq.exporters.export(fl,p); print("STEP:",os.path.basename(p),f"({os.path.getsize(p)} bytes)")
