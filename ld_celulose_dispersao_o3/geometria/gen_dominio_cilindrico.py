"""
gen_dominio_cilindrico.py — domínio CILÍNDRICO para o CFD atmosférico, com a lateral dividida em SETORES.

A lateral é um POLÍGONO de n lados (um lado plano por setor) → no STAR, "Split by Angle" separa os setores; para cada cenário
de vento, marcar os setores de barlavento como Velocity Inlet e os de sotavento como Pressure Outlet, SEM remalhar.
Também gera corpos de REFINO (cilindros) para controles volumétricos de malha.

Uso: python3 gen_dominio_cilindrico.py --centro X Y --raio 600 --altura 350 --setores 16 --out dominio.step
     (coordenadas locais, em metros; o STEP sai em mm, como o da geometria)
⚠️ LIMITE DO PARASOLID: o 3D-CAD do STAR (Parasolid) só aceita geometria dentro de uma caixa de 1 km (±500 m da
origem). Domínio maior que isso NÃO importa pelo 3D-CAD ("No bodies imported"). Para R = 600 m: exportar o domínio
em STL (metros) e importar como superfície (parts-based) — ver --stl.
Setores: 16 de 22,5°, centrados em 0° (eixo +y), 22,5°, 45°… (convenção de rosa dos ventos no sistema local).
"""
import argparse, math
import cadquery as cq
ap = argparse.ArgumentParser()
ap.add_argument("--centro", nargs=2, type=float, default=[15.5, 15.7])
ap.add_argument("--raio", type=float, default=600.0)
ap.add_argument("--altura", type=float, default=350.0)
ap.add_argument("--setores", type=int, default=16)
ap.add_argument("--refinos", default="80:70,300:120", help="raio:altura de cada cilindro de refino")
ap.add_argument("--out", default="dominio.step")
ap.add_argument("--stl", help="também grava o domínio em STL, em METROS (para importar como superfície no STAR)")
a = ap.parse_args()
cx, cy = a.centro
n = a.setores; dth = 2 * math.pi / n

def ponto(ang, r):  # ângulo de rosa dos ventos (0 = +y, horário) → (x, y)
    return (cx + r * math.sin(ang), cy + r * math.cos(ang))

# lateral POLIGONAL (n lados planos, um por setor): o STAR separa os setores sozinho com "Split by Angle"
# (as arestas entre setores têm 360/n graus de quebra). Raio = distância centro → vértice.
vertices = [ponto(-dth / 2 + k * dth, a.raio) for k in range(n)]
dominio = cq.Workplane("XY").polyline(vertices).close().extrude(a.altura).val()
lat = [f for f in dominio.Faces() if abs(f.normalAt().z) < 0.5]
print(f"domínio: raio {a.raio} m, altura {a.altura} m, {len(lat)} faces laterais (setores), {len(dominio.Faces())} faces no total")

asm = cq.Assembly()
asm.add(dominio.scale(1000), name="dominio")
for txt in a.refinos.split(","):
    r, h = (float(v) for v in txt.split(":"))
    ref = cq.Workplane("XY").center(cx, cy).circle(r).extrude(h).val()
    asm.add(ref.scale(1000), name=f"refino_r{int(r)}_h{int(h)}")
asm.export(a.out)
if a.stl:
    cq.exporters.export(dominio, a.stl, tolerance=0.01, angularTolerance=0.1)
    print("STL (m):", a.stl)
print("setores (direção central, de onde vem o vento, no sistema local):",
      ", ".join(f"S{k+1:02d}={k*360/n:.1f}°" for k in range(n)))
print("->", a.out)
