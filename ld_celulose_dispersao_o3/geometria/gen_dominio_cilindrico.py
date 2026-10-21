"""
gen_dominio_cilindrico.py — domínio CILÍNDRICO para o CFD atmosférico, com a lateral dividida em SETORES.

Cada setor da lateral é uma face separada no STEP → no STAR, separar as faces (Split by Patch) e, para cada cenário
de vento, marcar os setores de barlavento como Velocity Inlet e os de sotavento como Pressure Outlet, SEM remalhar.
Também gera corpos de REFINO (cilindros) para controles volumétricos de malha.

Uso: python3 gen_dominio_cilindrico.py --centro X Y --raio 600 --altura 350 --setores 16 --out dominio.step
     (coordenadas locais, em metros; o STEP sai em mm, como o da geometria)
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
a = ap.parse_args()
cx, cy = a.centro
n = a.setores; dth = 2 * math.pi / n

def ponto(ang, r):  # ângulo de rosa dos ventos (0 = +y, horário) → (x, y)
    return (cx + r * math.sin(ang), cy + r * math.cos(ang))

# n fatias (pizza) unidas SEM limpeza → as faces laterais de cada fatia continuam separadas (um setor = uma face)
fatias = []
for k in range(n):
    a0 = -dth / 2 + k * dth
    w = (cq.Workplane("XY").moveTo(cx, cy).lineTo(*ponto(a0, a.raio))
         .threePointArc(ponto(a0 + dth / 2, a.raio), ponto(a0 + dth, a.raio)).close())
    fatias.append(w.extrude(a.altura).val())
dominio = fatias[0].fuse(*fatias[1:], glue=True)
lat = [f for f in dominio.Faces() if f.geomType() == "CYLINDER"]
print(f"domínio: raio {a.raio} m, altura {a.altura} m, {len(lat)} faces laterais (setores), {len(dominio.Faces())} faces no total")

asm = cq.Assembly()
asm.add(dominio.scale(1000), name="dominio")
for txt in a.refinos.split(","):
    r, h = (float(v) for v in txt.split(":"))
    ref = cq.Workplane("XY").center(cx, cy).circle(r).extrude(h).val()
    asm.add(ref.scale(1000), name=f"refino_r{int(r)}_h{int(h)}")
asm.export(a.out)
print("setores (direção central, de onde vem o vento, no sistema local):",
      ", ".join(f"S{k+1:02d}={k*360/n:.1f}°" for k in range(n)))
print("->", a.out)
