"""
Geometria do CICLONE LAPPLE — domínio FLUIDO para CFD (Valgroup).
Proporções: Peçanha Fig. 3.20 (ver ../literatura/pecanha_ciclone_lapple.md).
D_c do dimensionamento preliminar (../dimensionamento/dimensionamento_lapple.py).

Gera o volume interno (o que o STAR malha): corpo cilíndrico + cone + entrada
tangencial retangular + vortex finder (tubo de saída do gás).
Saídas nomeadas: entrada tangencial, saída de gás (topo do vortex finder),
saída de sólidos (base do cone).
Unidades: mm. Importar no STAR em mm.
"""
import sys
import numpy as np
import cadquery as cq

# ── Parâmetro livre (do dimensionamento) ─────────────────────────────────────
D_c = 163.3        # mm  diâmetro do corpo (v_i=15,2 m/s, ρ_gás=3,946)
if len(sys.argv) >= 2:
    D_c = float(sys.argv[1])

# ── Proporções Lapple (Fig. 3.20) ────────────────────────────────────────────
B_c = D_c / 4.0    # largura da entrada (radial)
H_c = D_c / 2.0    # altura da entrada (axial)
D_e = D_c / 2.0    # diâmetro do vortex finder (saída de gás)
S_c = D_c / 8.0    # profundidade de inserção do vortex finder
L_c = 2.0 * D_c    # comprimento do cilindro
Z_c = 2.0 * D_c    # comprimento do cone
J_c = D_c / 4.0    # diâmetro da saída de sólidos
L_inlet = 1.2 * D_c    # comprimento do duto de entrada
L_out   = 0.6 * D_c    # comprimento do tubo de saída acima do topo
T_VF    = 2.0          # espessura da parede do vortex finder

R_c = D_c / 2.0
R_e = D_e / 2.0
R_j = J_c / 2.0
Ri  = R_e - T_VF       # raio interno do vortex finder (canal de saída)

# ── Construção do FLUIDO ──────────────────────────────────────────────────────
# Topo do cilindro em z=0; cilindro desce até -L_c; cone até -(L_c+Z_c).
cyl  = cq.Solid.makeCylinder(R_c, L_c, cq.Vector(0, 0, -L_c), cq.Vector(0, 0, 1))
cone = cq.Solid.makeCone(R_j, R_c, Z_c, cq.Vector(0, 0, -L_c - Z_c), cq.Vector(0, 0, 1))
body = cyl.fuse(cone)

# Canal de saída acima do topo (fluido dentro do vortex finder, r<Ri, z:0..+L_out)
outlet_core = cq.Solid.makeCylinder(Ri, L_out, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))

# Entrada tangencial: caixa B_c(radial) × L_inlet(tangencial) × H_c(axial),
# tangente ao cilindro em x=+R_c, no topo (z de -H_c a 0).
inlet = cq.Solid.makeBox(B_c, L_inlet, H_c,
                         cq.Vector(R_c - B_c, 0.0, -H_c))   # x:[R_c-B_c,R_c], y:[0,L_inlet], z:[-H_c,0]

fluid = body.fuse(outlet_core).fuse(inlet)

# Parede do vortex finder (tubo oco) = annulus Ri..R_e, de z=-S_c até +L_out.
vf_outer = cq.Solid.makeCylinder(R_e, S_c + L_out, cq.Vector(0, 0, -S_c), cq.Vector(0, 0, 1))
vf_inner = cq.Solid.makeCylinder(Ri,  S_c + L_out + 2, cq.Vector(0, 0, -S_c - 1), cq.Vector(0, 0, 1))
vf_wall  = vf_outer.cut(vf_inner)
fluid = fluid.cut(vf_wall)

result = cq.Workplane(obj=fluid)

# ── Exporta ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cq.exporters.export(result, "ciclone_lapple_fluido.step")
    vol = fluid.Volume() / 1e9   # m³ (mm³→m³ /1e9... na verdade mm³/1e9 = dm³? cuidado)
    bb = fluid.BoundingBox()
    print(f"CICLONE LAPPLE — domínio fluido")
    print(f"  D_c={D_c:.1f}  B_c={B_c:.1f}  H_c={H_c:.1f}  D_e={D_e:.1f}  S_c={S_c:.1f} mm")
    print(f"  L_c={L_c:.1f}  Z_c={Z_c:.1f}  J_c={J_c:.1f}  H_total={L_c+Z_c:.0f} mm")
    print(f"  bbox: x[{bb.xmin:.0f},{bb.xmax:.0f}] y[{bb.ymin:.0f},{bb.ymax:.0f}] z[{bb.zmin:.0f},{bb.zmax:.0f}] mm")
    print(f"  volume interno = {fluid.Volume()/1e3:.1f} cm³   válido={fluid.isValid()}   sólidos={len(fluid.Solids())}")
    print("  -> ciclone_lapple_fluido.step")
