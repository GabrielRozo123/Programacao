"""
gen_bico_v3.py  —  BICO do EJETOR (projeto Ito / Sugar) a partir do desenho NATIVO cotado.

Fonte (desenhos Sugar&Azucar, "BOM P/ FABRICAÇÃO"):
  - CSA01-300-001  "EJETOR / BICO - Ø15mm"  Rev 00  (22/07/2023)  -> 4 furos Ø15, PCD Ø24
  - CSA01-300-000  "EJETOR / CONJUNTO"      Rev 01  (13/03/2023)  -> 7 furos Ø9,  PCD Ø27 (hex)
  Corpo IDÊNTICO nos dois; muda só o padrão de furos. O desenho de PEÇA (‑001, mais novo)
  é o que GOVERNA -> padrão 4×Ø15 é o default. 7×Ø9 fica como variante para comparar.

Corpo do bico (CORTE A-A / D-D, ESC 1:1), material INOX A-316, barra Ø50×45:
  - Cabeça  Ø50 x 27 mm   (topo)
  - Encaixe Ø43 x 18 mm   (base, "spigot" que entra no tubo 2" Sch160 do suporte)
  - Total 45 mm ; chanfro base Ch.1,5x45° ; quebra topo ~Ch.1x45°
  - Furos de vazão passantes (topo->base)
  - 4 furos Ø7 radiais a 90° PARA FIXAÇÃO (parafuso cab. chata, item 19) — só no sólido

Convenção do modelo (z-up, mm):
  z=0    face da BASE (Ø43)  ......... lado do TUBO de alimentação (entrada)
  z=0..18   encaixe Ø43
  z=18..45  cabeça Ø50 ................ face de topo = DESCARGA no xarope (saída)
  Furos de vazão de z=0 a z=45.

Entregáveis:
  bico_4furos_Ø15_CSA01-300-001.step   (sólido — atual/governante)
  bico_7furos_Ø9_CSA01-300-000.step    (sólido — variante do conjunto)
  dominio_fluido_bico_4furos.step      (volume de FLUIDO p/ CFD: plenum 2" + furos + descarga)
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- corpo (comum) ----------
D_HEAD = 50.0      # Ø cabeça
H_HEAD = 27.0      # altura cabeça
D_SPIG = 43.0      # Ø encaixe
H_SPIG = 18.0      # altura encaixe
H_TOT  = H_HEAD + H_SPIG   # 45
CH_BASE = 1.5      # chanfro base Ch.1,5x45
CH_TOP  = 1.0      # quebra topo Ch.1x45 (Det E)

# ---------- furos de fixação ----------
D_FIX  = 7.0
Z_FIX  = H_TOT - 12.5   # 32,5 do topo -> 12,5 (Det: cota 12,5 / "4")

# ---------- padrões de furo de vazão ----------
PAT_4 = dict(n=4, d=15.0, pcd=24.0, ang0=0.0)              # CSA01-300-001 (atual)
PAT_7 = dict(n=7, d=9.0,  pcd=27.0, ang0=0.0, center=True) # CSA01-300-000 (hex 6+1)


def corpo():
    """Sólido do corpo (cabeça Ø50 + encaixe Ø43) com chanfros, sem furos."""
    b = (
        cq.Workplane("XY")
        .circle(D_SPIG / 2).extrude(H_SPIG)              # encaixe z 0..18
        .faces(">Z").workplane().circle(D_HEAD / 2).extrude(H_HEAD)  # cabeça z 18..45
    )
    # chanfro na aresta externa da base (z=0) e quebra no topo (z=45)
    b = b.edges("|Z").edges("<Z").chamfer(CH_BASE) if False else b
    # chanfros por seleção de arestas circulares externas
    b = b.faces("<Z").edges(cq.selectors.RadiusNthSelector(0)).chamfer(CH_BASE)
    b = b.faces(">Z").edges(cq.selectors.RadiusNthSelector(0)).chamfer(CH_TOP)
    return b


def furos_vazao_positions(pat):
    pos = []
    n, pcd = pat["n"], pat["pcd"]
    r = pcd / 2.0
    if pat.get("center"):
        pos.append((0.0, 0.0))
        n_ring = n - 1
    else:
        n_ring = n
    for i in range(n_ring):
        a = math.radians(pat["ang0"] + i * 360.0 / n_ring)
        pos.append((r * math.cos(a), r * math.sin(a)))
    return pos


def bico_solido(pat, fix=True):
    b = corpo()
    # furos de vazão passantes
    for (x, y) in furos_vazao_positions(pat):
        b = (
            b.faces(">Z").workplane(origin=(0, 0, 0))
            .pushPoints([(x, y)]).hole(pat["d"])   # através de todo o sólido
        )
    if fix:
        # 4 furos Ø7 radiais a 90°, defasados 45° dos furos de vazão do padrão de 4
        off = 45.0 if pat["n"] == 4 else 30.0
        for k in range(4):
            a = math.radians(off + 90.0 * k)
            # furo radial: cilindro ao longo do raio, centrado em z=Z_FIX
            cyl = (
                cq.Workplane("XY")
                .transformed(offset=(0, 0, Z_FIX), rotate=(90, 0, math.degrees(a)))
            )
            # constrói cilindro radial manualmente
            dir_x, dir_y = math.cos(a), math.sin(a)
            start = (dir_x * (D_HEAD/2 + 1), dir_y * (D_HEAD/2 + 1), Z_FIX)
            hole = cq.Solid.makeCylinder(
                D_FIX/2, D_HEAD/2 + 2,
                pnt=cq.Vector(*start),
                dir=cq.Vector(-dir_x, -dir_y, 0),
            )
            b = b.cut(hole)
    return b


def bico_conico_proposta(pat=PAT_4, d_saida=7.0, ang_meia=22.0):
    """PROPOSTA (Trilho 1): furos convergentes Ø(entrada)->Ø(saida) na descarga.
    Corpo idêntico; cada furo é Ø15 reto e converge a Ø7 na saída (topo) num
    cone de meia-abertura 22° (o próprio 22° do desenho -> cone de ~10 mm)."""
    b = corpo()
    r_in = pat["d"] / 2.0
    r_out = d_saida / 2.0
    L_cone = (r_in - r_out) / math.tan(math.radians(ang_meia))   # ~10 mm p/ 22°
    z_cone0 = H_TOT - L_cone
    for (x, y) in furos_vazao_positions(pat):
        # bore reto Ø15 de z=0 até z=z_cone0
        bore = cq.Solid.makeCylinder(r_in, z_cone0, pnt=cq.Vector(x, y, 0), dir=cq.Vector(0, 0, 1))
        # cone convergente Ø15->Ø7 de z_cone0 até H_TOT
        cone = cq.Solid.makeCone(r_in, r_out, L_cone, pnt=cq.Vector(x, y, z_cone0), dir=cq.Vector(0, 0, 1))
        b = b.cut(bore).cut(cone)
    # furos de fixação (iguais)
    off = 45.0
    for k in range(4):
        a = math.radians(off + 90.0 * k)
        dir_x, dir_y = math.cos(a), math.sin(a)
        hole = cq.Solid.makeCylinder(D_FIX/2, D_HEAD/2 + 2,
                                     pnt=cq.Vector(dir_x*(D_HEAD/2+1), dir_y*(D_HEAD/2+1), Z_FIX),
                                     dir=cq.Vector(-dir_x, -dir_y, 0))
        b = b.cut(hole)
    return b


def dominio_fluido_conico(pat=PAT_4, d_saida=7.0, ang_meia=22.0):
    ID_PIPE, L_PLENUM, D_DISCH, L_DISCH = 49.25, 40.0, 120.0, 120.0
    r_in, r_out = pat["d"]/2.0, d_saida/2.0
    L_cone = (r_in - r_out)/math.tan(math.radians(ang_meia)); z_cone0 = H_TOT - L_cone
    fl = cq.Workplane("XY").workplane(offset=-L_PLENUM).circle(ID_PIPE/2).extrude(L_PLENUM)
    for (x, y) in furos_vazao_positions(pat):
        bore = cq.Solid.makeCylinder(r_in, z_cone0, pnt=cq.Vector(x, y, 0), dir=cq.Vector(0,0,1))
        cone = cq.Solid.makeCone(r_in, r_out, L_cone, pnt=cq.Vector(x, y, z_cone0), dir=cq.Vector(0,0,1))
        fl = fl.union(cq.Workplane(obj=bore)).union(cq.Workplane(obj=cone))
    fl = fl.union(cq.Workplane("XY").workplane(offset=H_TOT).circle(D_DISCH/2).extrude(L_DISCH))
    return fl


def dominio_fluido(pat):
    """Volume de FLUIDO p/ CFD (padrão 4×Ø15): plenum 2"Sch160 + furos + descarga."""
    ID_PIPE = 49.25     # 2" Sch160 (OD 60,33 / par. 5,54)
    L_PLENUM = 40.0     # tubo de alimentação a montante da base
    D_DISCH = 120.0     # cilindro de descarga (xarope)
    L_DISCH = 120.0
    # plenum abaixo da base (z de -L_PLENUM a 0)
    fl = cq.Workplane("XY").workplane(offset=-L_PLENUM).circle(ID_PIPE/2).extrude(L_PLENUM)
    # furos de vazão (z 0..45)
    for (x, y) in furos_vazao_positions(pat):
        fl = fl.union(
            cq.Workplane("XY").pushPoints([(x, y)]).circle(pat["d"]/2).extrude(H_TOT)
        )
    # descarga (z 45..165)
    fl = fl.union(
        cq.Workplane("XY").workplane(offset=H_TOT).circle(D_DISCH/2).extrude(L_DISCH)
    )
    return fl


def report(name, wp):
    s = wp.val() if hasattr(wp, "val") else wp
    solid = s
    ok = solid.isValid()
    bb = solid.BoundingBox()
    vol = solid.Volume()
    print(f"  {name:42s} valid={ok}  vol={vol/1000:8.2f} cm3  "
          f"bbox=({bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}) mm")
    return ok


print("== BICO EJETOR v3 (desenho nativo) ==")
b4 = bico_solido(PAT_4, fix=True)
b7 = bico_solido(PAT_7, fix=True)
fd = dominio_fluido(PAT_4)

bc = bico_conico_proposta(PAT_4)
fdc = dominio_fluido_conico(PAT_4)

report("bico 4xØ15 RETO (CSA01-300-001, ATUAL)", b4)
report("bico 7xØ9  RETO (CSA01-300-000, variante)", b7)
report("bico 4x conico Ø15->Ø7 (PROPOSTA T1)", bc)
report("dominio fluido 4xØ15 RETO (CFD)", fd)
report("dominio fluido conico Ø15->Ø7 (CFD)", fdc)

exports = {
    "bico_4furos_D15_CSA01-300-001.step": b4,
    "bico_7furos_D9_CSA01-300-000.step": b7,
    "bico_4furos_conico_D15-D7_PROPOSTA.step": bc,
    "dominio_fluido_bico_4furos.step": fd,
    "dominio_fluido_conico_D15-D7.step": fdc,
}
print("STEP exportados:")
for name, obj in exports.items():
    p = os.path.join(OUT, name)
    cq.exporters.export(obj, p)
    print("  ", name, f"({os.path.getsize(p)} bytes)")
