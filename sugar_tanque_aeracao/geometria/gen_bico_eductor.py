"""
gen_bico_eductor.py — BICO como EDUCTOR: ar entra pelos furos LATERAIS Ø7 (interpretação do vídeo do Ito).

RELEITURA (após correção do Gabriel via vídeo):
  - Furos Ø15 do topo (PCD Ø24) = JATOS DE XAROPE (motriz).
  - Os 4 furos LATERAIS Ø7 a 90° (rotulados "PARA FIXAÇÃO" no desenho, mas ANGULADOS a 22°) =
    ENTRADA DE AR. A depressão dos jatos de xarope suga o ar por eles -> mistura/atomiza no próprio bico.
  - "quatro furinhos" (Ito) = os 4 laterais Ø7 (não os Ø15).

⚠️ PREMISSA a confirmar com o Ito: que os furos Ø7 laterais **penetram até os furos Ø15** (aqui, angulados
   22° e mirando o furo de xarope alinhado). O desenho os mostra na parede externa, sem cotar a profundidade;
   e como o ar chega neles (câmara em volta do bico / linha 1½") também falta. Modelo = leitura do vídeo.

Convenção (z-up): z=0 base Ø43 (entrada do xarope, do tubo 2"); z=45 topo Ø50 (descarga no tanque).
Furos de ar em z=32,5 (12,5 do topo), mirando os furos de xarope.
"""
import cadquery as cq
import math, os
OUT = os.path.dirname(os.path.abspath(__file__))

D_HEAD, H_HEAD = 50.0, 27.0
D_SPIG, H_SPIG = 43.0, 18.0
H_TOT = H_HEAD + H_SPIG
PCD, D_X = 24.0, 15.0        # jatos de xarope
D_AR = 7.0                   # ar (lateral)
Z_AR = H_TOT - 12.5          # 32,5 do topo
ANG_AR = 22.0                # inclinação dos furos de ar (do desenho)
CH_BASE, CH_TOP = 1.5, 1.0

def corpo():
    b = (cq.Workplane("XY").circle(D_SPIG/2).extrude(H_SPIG)
         .faces(">Z").workplane().circle(D_HEAD/2).extrude(H_HEAD))
    b = b.faces("<Z").edges(cq.selectors.RadiusNthSelector(0)).chamfer(CH_BASE)
    b = b.faces(">Z").edges(cq.selectors.RadiusNthSelector(0)).chamfer(CH_TOP)
    return b

def furos_xarope():
    return [(PCD/2*math.cos(math.radians(90*k)), PCD/2*math.sin(math.radians(90*k))) for k in range(4)]

def ar_axis(a_deg):
    """Eixo do furo de ar no plano radial-vertical: aponta p/ DENTRO+CIMA (rumo à saída), 22° da horizontal."""
    a = math.radians(a_deg)
    d = cq.Vector(-math.cos(a)*math.cos(math.radians(ANG_AR)),
                  -math.sin(a)*math.cos(math.radians(ANG_AR)),
                  +math.sin(math.radians(ANG_AR)))   # inward + up
    target = cq.Vector(PCD/2*math.cos(a), PCD/2*math.sin(a), Z_AR)  # centro do furo de xarope alinhado
    start = target - d.multiply(38.0)   # 38 mm p/ fora = entrada de ar
    return start, d

def bico_eductor_solido():
    b = corpo()
    for (x, y) in furos_xarope():
        b = b.cut(cq.Solid.makeCylinder(D_X/2, H_TOT, pnt=cq.Vector(x, y, 0), dir=cq.Vector(0,0,1)))
    for k in range(4):
        s, d = ar_axis(90*k)
        b = b.cut(cq.Solid.makeCylinder(D_AR/2, 40.0, pnt=s, dir=d))
    return b

def dominio_eductor():
    ID_PIPE, L_PLENUM, D_DISCH, L_DISCH = 49.25, 40.0, 120.0, 120.0
    fl = cq.Workplane("XY").workplane(offset=-L_PLENUM).circle(ID_PIPE/2).extrude(L_PLENUM).val()
    for (x, y) in furos_xarope():
        fl = fl.fuse(cq.Solid.makeCylinder(D_X/2, H_TOT, pnt=cq.Vector(x, y, 0), dir=cq.Vector(0,0,1)))
    for k in range(4):
        s, d = ar_axis(90*k)
        # comprimento até o furo de xarope (38) + stub de entrada de ar (não passar do furo)
        fl = fl.fuse(cq.Solid.makeCylinder(D_AR/2, 40.0, pnt=s, dir=d))
    fl = fl.fuse(cq.Workplane("XY").workplane(offset=H_TOT).circle(D_DISCH/2).extrude(L_DISCH).val())
    return fl.clean()

print("== BICO EDUCTOR (ar lateral) — interpretação do vídeo ==")
bs = bico_eductor_solido().val(); fd = dominio_eductor()
for nm, s in [("solido", bs), ("dominio fluido", fd)]:
    print(f"  {nm:16s} valid={s.isValid()} vol={s.Volume()/1e3:.1f} cm3")
for nm, s in [("bico_eductor_arlateral_solido.step", bs),
              ("dominio_fluido_eductor_arlateral.step", fd)]:
    p = os.path.join(OUT, nm); cq.exporters.export(s, p); print("  ->", nm, f"({os.path.getsize(p)} bytes)")
