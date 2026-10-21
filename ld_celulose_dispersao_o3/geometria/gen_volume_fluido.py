"""
gen_volume_fluido.py — gera o VOLUME DE AR pronto para malhar no STAR: domínio poligonal MENOS os obstáculos, num
único STL (em METROS) com cada superfície nomeada.

Por quê: o domínio (R 600 m) não entra pelo 3D-CAD (limite de 1 km do Parasolid) e, importado separado da geometria,
obriga a fazer Subtract + Surface Wrapper no STAR — e o wrapper, com superfície de 0,25 m, fecha frestas menores
que isso (colou um tanque na laje das prensas). Aqui a subtração é feita no OpenCascade, com as primitivas exatas:
o resultado já é fechado, manifold e sem interseções → no STAR basta Import Surface Mesh → Surface Remesher +
Trimmed Cell + Prism Layer. Wrapper só como plano B.

Superfícies (cada uma vira um "part surface" no STAR, pelo nome do bloco `solid` do STL):
  S01..S16  laterais do domínio (S01 centrado em 0° = +y, sentido horário, 22,5° cada)
  Solo, Topo
  <nome do objeto>        paredes de cada obstáculo (nome da tabela)
  Saida_<tag>             face de saída de cada objeto `descarga_*` (a maior face exposta da placa)

Uso:
  python3 gen_volume_fluido.py ../_privado/objetos_real.csv --out ../_privado/volume_ar_LD.stl
  (domínio: --centro X Y --raio 600 --altura 350 --setores 16; refinos: --refinos 80:70,300:120)
Gera também refino_r<R>_h<H>.stl (cilindros fechados, para Volumetric Controls) na mesma pasta.
Verifica: nº de volumes de ar (bolsões fechados), arestas livres/não-manifold do STL e volume com sinal.
Requer: pip install cadquery
"""
import argparse, math, os, re
from collections import Counter, defaultdict
import cadquery as cq
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location
from gen_geometria_cfd import ler, solido

ap = argparse.ArgumentParser()
ap.add_argument("tabela")
ap.add_argument("--out", default="volume_ar.stl")
ap.add_argument("--centro", nargs=2, type=float, default=[15.5, 15.7])
ap.add_argument("--raio", type=float, default=600.0)
ap.add_argument("--altura", type=float, default=350.0)
ap.add_argument("--setores", type=int, default=16)
ap.add_argument("--refinos", default="80:70,300:120", help="raio:altura de cada cilindro de refino")
ap.add_argument("--deflexao", type=float, default=0.01, help="desvio máx. da faceta [m] nas superfícies curvas")
ap.add_argument("--angulo", type=float, default=5.0, help="ângulo máx. entre facetas [graus] nas superfícies curvas")
a = ap.parse_args()
cx, cy = a.centro
n = a.setores; dth = 2 * math.pi / n


def ponto(ang, r):  # ângulo de rosa dos ventos (0 = +y, horário) → (x, y)
    return (cx + r * math.sin(ang), cy + r * math.cos(ang))


# 1. domínio poligonal (mesma convenção do gen_dominio_cilindrico.py) e obstáculos
dominio = cq.Workplane("XY").polyline([ponto(-dth / 2 + k * dth, a.raio) for k in range(n)]).close().extrude(a.altura).val()
objs = ler(a.tabela)
solidos = {o["nome"].strip(): solido(o) for o in objs}
nomes = list(solidos)
lista = list(solidos.values())
obstaculos = lista[0].fuse(*lista[1:])
ar = dominio.cut(obstaculos)
volumes = sorted(ar.Solids(), key=lambda s: -s.Volume())
if len(volumes) > 1:
    print(f"⚠️ {len(volumes) - 1} bolsão(ões) de ar fechado(s) descartado(s):",
          ", ".join(f"{v.Volume():.2f} m³" for v in volumes[1:]))
ar = volumes[0]

# 2. malha de superfície (uma só para o sólido inteiro → arestas compartilhadas idênticas → STL estanque)
BRepMesh_IncrementalMesh(ar.wrapped, a.deflexao, False, math.radians(a.angulo), True)


def triangulos(face):
    loc = TopLoc_Location()
    tri = BRep_Tool.Triangulation_s(face.wrapped, loc)
    trsf = loc.Transformation()
    nos = [tri.Node(i).Transformed(trsf) for i in range(1, tri.NbNodes() + 1)]
    nos = [(p.X(), p.Y(), p.Z()) for p in nos]
    inv = face.wrapped.Orientation() == TopAbs_REVERSED
    out = []
    for i in range(1, tri.NbTriangles() + 1):
        i1, i2, i3 = tri.Triangle(i).Get()
        t = (nos[i1 - 1], nos[i3 - 1], nos[i2 - 1]) if inv else (nos[i1 - 1], nos[i2 - 1], nos[i3 - 1])
        out.append(t)
    return out


def area(t):
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = t
    u, v = (x2 - x1, y2 - y1, z2 - z1), (x3 - x1, y3 - y1, z3 - z1)
    c = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return 0.5 * math.sqrt(sum(k * k for k in c)), c


def mais_proximo(p):
    vx = BRepBuilderAPI_MakeVertex(gp_Pnt(*p)).Vertex()
    d = [(BRepExtrema_DistShapeShape(vx, s.wrapped).Value(), nm) for nm, s in solidos.items()]
    return min(d)


# 3. nomear cada face: domínio pelo plano/normal, obstáculos pelo sólido de origem mais próximo
grupos = defaultdict(list)
faces_descarga = defaultdict(list)
r_insc = a.raio * math.cos(dth / 2)
for f in ar.Faces():
    tris = triangulos(f)
    if not tris:
        continue
    t = max(tris, key=lambda t: area(t)[0])
    p = tuple(sum(c) / 3 for c in zip(*t))
    _, nrm = area(t)
    if abs(p[2]) < 1e-6:
        nome = "Solo"
    elif abs(p[2] - a.altura) < 1e-6:
        nome = "Topo"
    elif math.hypot(p[0] - cx, p[1] - cy) > 0.99 * r_insc:
        ang = math.degrees(math.atan2(nrm[0], nrm[1])) % 360  # normal para fora do ar = para fora do domínio
        nome = f"S{int(round(ang / (360 / n))) % n + 1:02d}"
    else:
        dist, nome = mais_proximo(p)
        if dist > 1e-3:
            print(f"⚠️ face a {dist:.3f} m do objeto mais próximo ({nome})")
        if nome.startswith("descarga_"):
            faces_descarga[nome].append((sum(area(t)[0] for t in tris), tris))
            continue
    grupos[nome] += tris

# descarga: a maior face exposta da placa é a saída; as bordas (2 cm) entram na parede do exaustor
for nome, fs in faces_descarga.items():
    fs.sort(key=lambda x: -x[0])
    tag = re.search(r"\d{4}-\d{2}-(\d+)", nome)
    tag = tag.group(1) if tag else nome
    grupos[f"Saida_{tag}"] += fs[0][1]
    exaustor = next((m for m in nomes if m.startswith("exaustor_") and m.endswith(tag)), nome)
    for _, tris in fs[1:]:
        grupos[exaustor] += tris
    print(f"Saida_{tag}: {fs[0][0]:.3f} m²")


# 4. gravar STL ASCII (um bloco `solid` por superfície) e verificar
def gravar_stl(caminho, grupos):
    with open(caminho, "w") as fh:
        for nome in sorted(grupos):
            fh.write(f"solid {nome}\n")
            for t in grupos[nome]:
                _, c = area(t)
                m = math.sqrt(sum(k * k for k in c)) or 1.0
                fh.write(f" facet normal {c[0]/m:.6e} {c[1]/m:.6e} {c[2]/m:.6e}\n  outer loop\n")
                for v in t:
                    fh.write(f"   vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                fh.write("  endloop\n endfacet\n")
            fh.write(f"endsolid {nome}\n")


def verificar(grupos):
    arestas = Counter()
    vol = 0.0
    chave = lambda v: tuple(round(c, 5) for c in v)
    for tris in grupos.values():
        for t in tris:
            k = [chave(v) for v in t]
            for i in range(3):
                arestas[tuple(sorted((k[i], k[(i + 1) % 3])))] += 1
            (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = t
            vol += (x1 * (y2 * z3 - y3 * z2) - x2 * (y1 * z3 - y3 * z1) + x3 * (y1 * z2 - y2 * z1)) / 6
    livres = sum(1 for c in arestas.values() if c == 1)
    nao_manifold = sum(1 for c in arestas.values() if c > 2)
    return livres, nao_manifold, vol


gravar_stl(a.out, grupos)
livres, nm, vol = verificar(grupos)
ntri = sum(len(t) for t in grupos.values())
print(f"{a.out}: {len(grupos)} superfícies, {ntri} triângulos")
print(f"  arestas livres {livres}, não-manifold {nm}, volume com sinal {vol:,.0f} m³ (sólido: {ar.Volume():,.0f} m³)")
print("  superfícies:", ", ".join(f"{k}({len(v)})" for k, v in sorted(grupos.items())))

pasta = os.path.dirname(os.path.abspath(a.out))
for txt in a.refinos.split(","):
    r, h = (float(v) for v in txt.split(":"))
    ref = cq.Workplane("XY").center(cx, cy).circle(r).extrude(h).val()
    arq = os.path.join(pasta, f"refino_r{int(r)}_h{int(h)}.stl")
    cq.exporters.export(ref, arq, tolerance=0.05, angularTolerance=0.1)
    print("refino (m):", arq)
