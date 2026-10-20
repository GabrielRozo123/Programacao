"""
pipeline_limpeza_exemplo.py — o caminho completo, do CAD da planta à geometria limpa do CFD, num script só.

É a versão didática do que fizemos na LD Celulose (ver ../06_metodologia_geometria_CFD.md):

  ETAPA 1  juntar as partes do RAR e extrair o STEP            (o arquivo veio dividido em partes de 5 MB)
  ETAPA 2  ler o STEP COM OS NOMES das peças                   (OpenCascade / XCAF — biblioteca de CAD aberta)
  ETAPA 3  inventário: nome + caixa envolvente de cada peça     (vira uma planilha CSV)
  ETAPA 4  classificar por NOME + TAMANHO + DISTÂNCIA à fonte   (regras = critérios da literatura, 05_limpeza)
  ETAPA 5  agrupar por TAG de equipamento e reconstruir como    (caixas e cilindros, nas posições originais)
           primitivas → STEP limpo para o STAR-CCM+

Uso:
  python3 -I pipeline_limpeza_exemplo.py ARQUIVO.part001.rar  --origem X Y Z --saida pasta/
  python3 -I pipeline_limpeza_exemplo.py ARQUIVO.stp          --origem X Y Z --saida pasta/
    X Y Z = ponto de referência em coordenadas da planta [m] (ex.: canto do prédio de O₃ e cota do piso)

Requer: pip install cadquery   ·   unrar (só para a etapa 1)
"""
import argparse, csv, math, os, re, subprocess, time
from collections import defaultdict
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.IFSelect import IFSelect_RetDone

ap = argparse.ArgumentParser()
ap.add_argument("entrada", help=".part001.rar (multivolume) ou .stp")
ap.add_argument("--origem", nargs=3, type=float, required=True)
ap.add_argument("--saida", default="saida_limpeza")
ap.add_argument("--raio-z0", type=float, default=65.0, help="zona de detalhe em torno da fonte [m]")
ap.add_argument("--raio-z1", type=float, default=300.0, help="zona de interesse [m]")
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
OX, OY, OZ = a.origem

# ── ETAPA 1 ── juntar as partes do RAR (o unrar acha .part002, .part003… sozinho) ─────────────────
step = a.entrada
if step.lower().endswith(".rar"):
    subprocess.run(["unrar", "e", "-o+", "-inul", step, a.saida + os.sep], check=True)
    step = max((os.path.join(a.saida, f) for f in os.listdir(a.saida) if f.lower().endswith((".stp", ".step"))),
               key=os.path.getsize)
print(f"[1] STEP: {step} ({os.path.getsize(step)/1e6:.0f} MB)")

# ── ETAPA 2 ── ler COM NOMES (o leitor simples do STEP perde os nomes; o XCAF mantém a árvore) ───
t0 = time.time()
doc = TDocStd_Document(TCollection_ExtendedString("doc"))
leitor = STEPCAFControl_Reader(); leitor.SetNameMode(True)
assert leitor.ReadFile(step) == IFSelect_RetDone, "falha ao ler o STEP"
leitor.Transfer(doc)
arvore = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
print(f"[2] lido com nomes em {time.time()-t0:.0f} s")

def nome(lab):
    n = TDataStd_Name()
    return n.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"

# ── ETAPA 3 ── inventário: percorre a árvore, aplica as transformações e mede cada peça ────────────
pecas = []   # (caminho, nome, [xmin, ymin, zmin, xmax, ymax, zmax] em metros e coordenadas LOCAIS)
def visita(lab, loc, caminho):
    if arvore.IsReference_s(lab):                       # ocorrência → segue para a peça, somando a posição
        ref = TDF_Label(); arvore.GetReferredShape_s(lab, ref)
        visita(ref, loc.Multiplied(arvore.GetLocation_s(lab)), caminho + [nome(lab)]); return
    if arvore.IsAssembly_s(lab):                         # subconjunto → visita os filhos
        filhos = TDF_LabelSequence(); arvore.GetComponents_s(lab, filhos, False)
        for i in range(1, filhos.Length() + 1): visita(filhos.Value(i), loc, caminho)
        return
    caixa = Bnd_Box(); BRepBndLib.Add_s(arvore.GetShape_s(lab).Moved(loc), caixa, False)
    if caixa.IsVoid(): return
    x0, y0, z0, x1, y1, z1 = (v / 1000 for v in caixa.Get())          # mm → m
    if z0 < 100: return                                               # peça sem posição (na origem do arquivo)
    pecas.append((" / ".join(caminho[-3:]), caminho[-1] if caminho else nome(lab),
                  [x0 - OX, y0 - OY, z0 - OZ, x1 - OX, y1 - OY, z1 - OZ]))
raizes = TDF_LabelSequence(); arvore.GetFreeShapes(raizes)
for i in range(1, raizes.Length() + 1): visita(raizes.Value(i), TopLoc_Location(), [])
with open(os.path.join(a.saida, "inventario.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["caminho", "peca", "xmin", "ymin", "zmin", "xmax", "ymax", "zmax"])
    for c, n, b in pecas: w.writerow([c, n] + [round(v, 3) for v in b])
print(f"[3] inventário: {len(pecas)} peças → inventario.csv")

# ── ETAPA 4 ── classificar: NOME (nomenclatura de projeto) + TAMANHO (malha) + DISTÂNCIA (zona) ────
REGRAS_SAI = [  # (padrão no nome, motivo) — critérios do 05_limpeza_CAD_criterios.md §4
    (r"PILE|BLOCK_P\d|BASE|FUND|TUB-AP|P\.R-",          "fundação / abaixo do piso"),
    (r"CRANE|GUINDAST|SF100FT|TRUCK|CAMINH",             "temporário / veículo"),
    (r"FITTING|SCTN|FRMWORK|SBFRAMEWORK|BEANS|COLUMN",   "estrutura / perfil (treliça)"),
    (r"ESCADA|STAIR|HANDRAIL|GUARDA|PANEL|HANGER",       "acessório"),
    (r"^PS-|AIDGROUP|INSERT|_INS-|NOZZ|FLANGE|VALV",     "suporte / aterramento / bocal / válvula"),
]
TAG = re.compile(r"(1[0-9]{3}-\d{2}-\d{3})")            # tag de equipamento AVEVA: área-classe-número

def distancia(b):  # distância horizontal da caixa até a origem (fonte)
    return math.hypot(max(0, b[0], -b[3]), max(0, b[1], -b[4]))

grupos, saiu = defaultdict(list), defaultdict(int)
for caminho, n, b in pecas:
    texto = caminho + " " + n
    motivo = next((m for p, m in REGRAS_SAI if re.search(p, n, re.I)), None)
    tag = TAG.search(texto)
    if b[5] < 0.5:                       motivo = "abaixo do piso"
    elif tag:                            motivo = None          # peça de equipamento: decide o conjunto (etapa 5)
    if motivo: saiu[motivo] += 1; continue
    grupos[tag.group(1) if tag else "sem tag"].append(b)
print("[4] saíram:", dict(saiu))

# ── ETAPA 5 ── um objeto por TAG: caixa envolvente do conjunto → cilindro (planta ~quadrada) ou caixa ─
asm, tabela = cq.Assembly(), []
for tag, caixas in grupos.items():
    if tag == "sem tag": continue
    b = [min(c[0] for c in caixas), min(c[1] for c in caixas), max(0, min(c[2] for c in caixas)),
         max(c[3] for c in caixas), max(c[4] for c in caixas), max(c[5] for c in caixas)]
    dx, dy, h = b[3] - b[0], b[4] - b[1], b[5] - b[2]
    d = distancia(b)
    limite = 1.0 if d <= a.raio_z0 else 3.0 if d <= a.raio_z1 else 1e9   # critério de tamanho por zona (§3)
    if max(dx, dy, h) < limite: continue
    if abs(dx - dy) / max(dx, dy) < 0.25:                                   # planta ~quadrada → vaso/silo/torre
        s = cq.Workplane("XY").circle(min(dx, dy) / 2).extrude(h).translate(((b[0]+b[3])/2, (b[1]+b[4])/2, b[2]))
        forma = "cilindro"
    else:
        s = cq.Workplane("XY").box(dx, dy, h, centered=False).translate((b[0], b[1], b[2]))
        forma = "caixa"
    asm.add(s, name=tag); tabela.append([tag, forma, round(d), round(dx, 1), round(dy, 1), round(h, 1)])
asm.export(os.path.join(a.saida, "geometria_limpa.step"))
print(f"[5] {len(tabela)} objetos → geometria_limpa.step")
for t in sorted(tabela, key=lambda t: t[2]): print(f"    {t[0]:14s} {t[1]:8s} dist {t[2]:4d} m   {t[3]} × {t[4]} m, h {t[5]} m")
