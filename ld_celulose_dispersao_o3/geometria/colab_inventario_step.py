# ==============================================================================
# colab_inventario_step.py — rodar no Google Colab (uma célula só).
# Lê um STEP grande COM OS NOMES das peças (XCAF) e gera um inventário pequeno (CSV):
# nome, caixa envolvente em metros (coordenadas da planta), maior dimensão e nº de faces.
# O CSV tem poucos kB → é ele que vai para a análise (identificar exaustores, misturadores,
# tubulação de saída de O3) e para decidir as regras de limpeza (05_limpeza_CAD_criterios.md).
# ==============================================================================
# !pip install -q cadquery-ocp
import os, csv, zipfile, time
from google.colab import files
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCP.IFSelect import IFSelect_RetDone

ARQUIVO = "/content/#F-M-1219_copy.stp"      # ou .zip com o .stp dentro
SAIDA   = "/content/inventario_F-M-1219.csv"

if ARQUIVO.endswith(".zip") or (not os.path.exists(ARQUIVO) and os.path.exists(ARQUIVO[:-4] + ".zip")):
    z = zipfile.ZipFile(ARQUIVO if ARQUIVO.endswith(".zip") else ARQUIVO[:-4] + ".zip")
    nome = [n for n in z.namelist() if n.lower().endswith((".stp", ".step"))][0]
    z.extract(nome, "/content/"); ARQUIVO = "/content/" + nome

t0 = time.time()
doc = TDocStd_Document(TCollection_ExtendedString("doc"))
r = STEPCAFControl_Reader(); r.SetNameMode(True)
assert r.ReadFile(ARQUIVO) == IFSelect_RetDone, "falha ao ler o STEP"
r.Transfer(doc)
print(f"lido em {time.time()-t0:.0f} s")
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

def nome(lab):
    a = TDataStd_Name()
    return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"

linhas = []
def visita(lab, loc, caminho):
    if st.IsReference_s(lab):
        ref = TDF_Label(); st.GetReferredShape_s(lab, ref)
        visita(ref, loc.Multiplied(st.GetLocation_s(lab)), caminho + [nome(lab)]); return
    if st.IsAssembly_s(lab):
        f = TDF_LabelSequence(); st.GetComponents_s(lab, f, False)
        for i in range(1, f.Length() + 1): visita(f.Value(i), loc, caminho)
        return
    shp = st.GetShape_s(lab).Moved(loc)
    b = Bnd_Box(); BRepBndLib.Add_s(shp, b, False)
    if b.IsVoid(): return
    x0, y0, z0, x1, y1, z1 = (v / 1000 for v in b.Get())      # mm -> m
    nf = 0; e = TopExp_Explorer(shp, TopAbs_FACE)
    while e.More(): nf += 1; e.Next()
    ns = 0; e = TopExp_Explorer(shp, TopAbs_SOLID)
    while e.More(): ns += 1; e.Next()
    dmax = max(x1 - x0, y1 - y0, z1 - z0)
    linhas.append([" / ".join(caminho[-3:]), nome(lab), round(x0, 3), round(y0, 3), round(z0, 3),
                   round(x1, 3), round(y1, 3), round(z1, 3), round(dmax, 3), nf, ns])

top = TDF_LabelSequence(); st.GetFreeShapes(top)
for i in range(1, top.Length() + 1): visita(top.Value(i), TopLoc_Location(), [])
with open(SAIDA, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["caminho", "peca", "xmin", "ymin", "zmin", "xmax", "ymax", "zmax", "maior_dim_m", "faces", "solidos"])
    w.writerows(linhas)
print(len(linhas), "peças ->", SAIDA)
files.download(SAIDA)
