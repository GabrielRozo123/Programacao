"""
gen_refino_lancas.py — os 16 cilindros de refino dos injetores (Fase 3 · Ito)

Alternativa ao macro Java: um STEP com 16 sólidos separados e NOMEADOS, para
importar com "Create a Part for Each Body" e usar direto como volumetric control.
Independente de versão do STAR.

Convenção: mm, mesmo sistema do `aerador_16lancas_fluido.step`.
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))

AER_X, AER_Y = 200.0, -440.0
R_REFINO = 100.0            # ~3,2x o raio da lanca (31,35)
ABAIXO, ACIMA = 350.0, 150.0
ANEIS = [(5, 375.0, 0.0, -5450.0), (11, 770.0, math.pi/11, -4660.0)]

asm = cq.Assembly()
i, vol = 0, 0.0
for n, r, fase, zd in ANEIS:
    for k in range(n):
        i += 1
        a = fase + 2*math.pi*k/n
        x, y = AER_X + r*math.cos(a), AER_Y + r*math.sin(a)
        z0, z1 = zd - ABAIXO, zd + ACIMA
        s = cq.Solid.makeCylinder(R_REFINO, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))
        asm.add(cq.Workplane(obj=s), name=f"refino_lanca_{i:02d}")
        vol += s.Volume()
        print(f"  refino_lanca_{i:02d}  centro ({x:8.2f},{y:8.2f})  z {z0:8.1f}..{z1:8.1f}")

p = os.path.join(OUT, "refino_lancas_16.step")
asm.save(p, exportType="STEP")
print(f"\n  {i} solidos · volume {vol/1e9:.4f} m3 ({vol/1e9/19.991*100:.2f}% do dominio)")
print(f"  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e3:.0f} kB)")
