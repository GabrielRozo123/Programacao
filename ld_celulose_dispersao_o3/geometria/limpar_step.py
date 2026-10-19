"""
limpar_step.py — limpeza automática de um STEP de montagem da planta, por regras de NOME + COTA.

Lê o STEP com nomes (XCAF/OpenCascade), classifica cada peça (folha da montagem) pelas regras
abaixo (critérios de ../05_limpeza_CAD_criterios.md §4), translada para uma origem local e grava:
  - <saida>_limpo.step     peças que FICAM, com nome, em metros, origem local
  - <saida>_inventario.csv todas as peças: categoria, decisão, caixa envolvente (coord. locais)
  - <saida>_vista.png      vista de cima e isométrica (fica = cor; sai = cinza claro)

Uso:
  python3 -I limpar_step.py MODELO.stp SAIDA --origem X Y Z
    (X, Y, Z em metros, no sistema da planta; ex.: canto do prédio de O3 e cota do piso)

As regras são uma lista editável (REGRAS): a primeira que casar com o nome decide.
"""
import argparse, csv, re
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.IFSelect import IFSelect_RetDone

# (padrão no nome, categoria, decisão)  decisão: fica | sai | conferir
REGRAS = [
    (r"^FITTING", "estrutura", "sai"),
    (r"^(GWALL|STWALL)", "parede", "fica"),
    (r"PILE|BLOCK_P\d|OZ_B_BASE|P\.R-|FUND|_BASE\b|BASES_ELEV", "fundação / bases", "sai"),
    (r"WALL-HOLE|_INS-|SEALING_ENTRY", "furos / insertos / vedação", "sai"),
    (r"FLOOR.*974,900|FLOOR.*TRANSFORMERS", "laje / plataforma", "fica"),
    (r"FLOOR", "piso interno", "sai"),
    (r"SUBSTRUCTURE|SBFRAMEWORK|SCTN|BEANS|COLUMNS|FRMWORK", "estrutura", "sai"),
    (r"OPENNING|OPENING", "abertura", "conferir"),
    (r"^TUB-AP", "eletroduto fino (descida junto às paredes)", "sai"),
    (r"^TUB|PIPE|DUTO|DUCT", "tubulação / duto", "conferir"),
    (r"FAN|EXAUST|VENT", "exaustor / ventilação", "fica"),
]

def classificar(nome):
    for pad, cat, dec in REGRAS:
        if re.search(pad, nome, re.I):
            return cat, dec
    return "sem regra", "conferir"

def ler(arq):
    doc = TDocStd_Document(TCollection_ExtendedString("doc"))
    r = STEPCAFControl_Reader(); r.SetNameMode(True)
    assert r.ReadFile(arq) == IFSelect_RetDone, "falha ao ler STEP"
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    def nome(lab):
        a = TDataStd_Name()
        return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"
    out = []
    def visita(lab, loc, nm):
        if st.IsReference_s(lab):
            ref = TDF_Label(); st.GetReferredShape_s(lab, ref)
            visita(ref, loc.Multiplied(st.GetLocation_s(lab)), nome(lab)); return
        if st.IsAssembly_s(lab):
            f = TDF_LabelSequence(); st.GetComponents_s(lab, f, False)
            for i in range(1, f.Length() + 1): visita(f.Value(i), loc, nm)
            return
        out.append((nm or nome(lab), cq.Shape.cast(st.GetShape_s(lab).Moved(loc))))
    top = TDF_LabelSequence(); st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1): visita(top.Value(i), TopLoc_Location(), None)
    return out

ap = argparse.ArgumentParser()
ap.add_argument("step"); ap.add_argument("saida")
ap.add_argument("--origem", nargs=3, type=float, required=True, metavar=("X", "Y", "Z"))
ap.add_argument("--sem-imagem", action="store_true")
a = ap.parse_args()

pecas = ler(a.step)
mm = 1000.0  # OpenCascade lê o STEP em mm
ox, oy, oz = (v * mm for v in a.origem)
asm = cq.Assembly(name="limpo")
linhas, desenho, usados = [], [], {}
for nm, shp in pecas:
    try:
        bb = shp.BoundingBox()
    except Exception:
        continue  # peça vazia (sem geometria)
    if bb.zmin < 100 * mm:  # peça sem posicionamento (perto da origem do arquivo) → sai
        cat, dec = "sem posição", "sai"
    else:
        cat, dec = classificar(nm)
    loc = shp.translate(cq.Vector(-ox, -oy, -oz)).scale(1 / mm)
    b = loc.BoundingBox()
    linhas.append([nm, cat, dec, round(b.xmin, 2), round(b.ymin, 2), round(b.zmin, 2),
                   round(b.xmax, 2), round(b.ymax, 2), round(b.zmax, 2)])
    desenho.append((loc, dec, cat))
    if dec in ("fica", "conferir"):
        k = usados.get(nm, 0); usados[nm] = k + 1
        asm.add(loc, name=nm if k == 0 else f"{nm}__{k}")
asm.export(a.saida + "_limpo.step")
with open(a.saida + "_inventario.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["peca", "categoria", "decisao", "xmin", "ymin", "zmin", "xmax", "ymax", "zmax"])
    w.writerows(sorted(linhas, key=lambda l: (l[2], l[1], l[0])))

from collections import Counter
c = Counter((l[2], l[1]) for l in linhas)
print(f"{len(linhas)} peças")
for (d, cat), n in sorted(c.items()): print(f"  {d:9s} {cat:28s} {n:4d}")

if not a.sem_imagem:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.collections import PolyCollection
    cores = {"parede": "#4C78A8", "laje / plataforma": "#72B7B2", "tubulação / duto": "#E45756",
             "abertura": "#F58518", "exaustor / ventilação": "#B279A2", "sem regra": "#EECA3B"}
    fig = plt.figure(figsize=(16, 8))
    ax1 = fig.add_subplot(1, 2, 1); ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    for shp, dec, cat in desenho:
        if dec == "sai" and cat == "sem posição": continue
        vs, tris = shp.tessellate(0.05)
        P = [[(vs[i].x, vs[i].y, vs[i].z) for i in t] for t in tris]
        cor = "#DDDDDD" if dec == "sai" else cores.get(cat, "#999999")
        al = 0.15 if dec == "sai" else 0.9
        ax1.add_collection(PolyCollection([[(p[0], p[1]) for p in tri] for tri in P], facecolor=cor, edgecolor="none", alpha=al))
        if dec != "sai":
            ax2.add_collection3d(Poly3DCollection(P, facecolor=cor, edgecolor="none", alpha=al))
    xs = [l[3] for l in linhas if l[1] != "sem posição"] + [l[6] for l in linhas if l[1] != "sem posição"]
    ys = [l[4] for l in linhas if l[1] != "sem posição"] + [l[7] for l in linhas if l[1] != "sem posição"]
    zs = [l[5] for l in linhas if l[2] != "sai"] + [l[8] for l in linhas if l[2] != "sai"]
    ax1.set_xlim(min(xs) - 2, max(xs) + 2); ax1.set_ylim(min(ys) - 2, max(ys) + 2); ax1.set_aspect("equal")
    ax1.grid(alpha=.3); ax1.set_xlabel("x [m]"); ax1.set_ylabel("y [m]")
    ax1.set_title("Vista de cima — colorido = fica/conferir · cinza = sai")
    ax2.set_xlim(min(xs), max(xs)); ax2.set_ylim(min(ys), max(ys)); ax2.set_zlim(min(zs), max(zs))
    ax2.set_box_aspect((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    ax2.view_init(25, -60); ax2.set_title("Isométrica — só o que fica/conferir")
    from matplotlib.patches import Patch
    ax1.legend(handles=[Patch(color=v, label=k) for k, v in cores.items()], loc="upper left", fontsize=8)
    fig.tight_layout(); fig.savefig(a.saida + "_vista.png", dpi=110)
    print("imagem:", a.saida + "_vista.png")
