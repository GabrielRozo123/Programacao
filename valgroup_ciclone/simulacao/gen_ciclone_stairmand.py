"""
gen_ciclone_stairmand.py — DOMÍNIO DE FLUIDO do ciclone STAIRMAND (alta eficiência) — Valgroup.

Dimensionado para: gás 1820 kg/h (1900 − 80 de particulado) a 400°C / 1,2 bar
→ Q = 461,2 m³/h · v_i = 15,2 m/s  →  **Dc = 290 mm**  (ver ../dimensionamento/00_plano_cfd_e_dimensionamento.md)

TUDO PARAMÉTRICO EM FUNÇÃO DE Dc (proporções Stairmand HE):
    a  (altura entrada)      = 0,50 · Dc
    b  (largura entrada)     = 0,20 · Dc
    De (saída de gás)        = 0,50 · Dc
    S  (mergulho do vortex)  = 0,50 · Dc
    h  (altura cilíndrica)   = 1,50 · Dc
    H  (altura total)        = 4,00 · Dc
    B  (saída de pó)         = 0,375 · Dc

Convenção: z=0 no TETO do ciclone, z cresce para CIMA (a saída de gás sobe; o cone desce para z negativo).
Entrada tangencial retangular (face externa tangente ao corpo).
"""
import cadquery as cq
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# ── O ÚNICO PARÂMETRO ─────────────────────────────────────────────────────
DC = 290.0                 # mm — diâmetro do corpo (mude só aqui)

# ── proporções Stairmand (alta eficiência) ────────────────────────────────
A  = 0.50  * DC            # altura da entrada
B_ = 0.20  * DC            # largura da entrada
DE = 0.50  * DC            # Ø saída de gás (vortex finder)
S  = 0.50  * DC            # mergulho do vortex finder abaixo do teto
H_ = 1.50  * DC            # altura da parte cilíndrica
HT = 4.00  * DC            # altura total (cilindro + cone)
BD = 0.375 * DC            # Ø saída de pó

# extensões para o CFD (não fazem parte da norma — dão espaço p/ as BCs)
L_IN   = 1.5 * DC          # duto de entrada a montante
L_OUT  = 1.0 * DC          # tubo de saída acima do teto
L_DUST = 0.5 * DC          # tubo da saída de pó
T_VF   = 4.0               # espessura da parede do vortex finder (mm)

H_CONE = HT - H_           # altura do cone

def build():
    # 1) corpo: cilindro (z 0 → −h) + cone (z −h → −H)
    corpo = cq.Solid.makeCylinder(DC/2, H_, pnt=cq.Vector(0,0,-H_), dir=cq.Vector(0,0,1))
    cone  = cq.Solid.makeCone(DC/2, BD/2, H_CONE, pnt=cq.Vector(0,0,-HT), dir=cq.Vector(0,0,1))
    # makeCone cria r1 na base -> inverter: base em -HT com raio BD/2, topo em -h com DC/2
    cone  = cq.Solid.makeCone(BD/2, DC/2, H_CONE, pnt=cq.Vector(0,0,-HT), dir=cq.Vector(0,0,1))
    fluido = corpo.fuse(cone)

    # 2) tubo da saída de pó (abaixo do ápice)
    dust = cq.Solid.makeCylinder(BD/2, L_DUST, pnt=cq.Vector(0,0,-HT-L_DUST), dir=cq.Vector(0,0,1))
    fluido = fluido.fuse(dust)

    # 3) tubo de saída de gás: de z=−S até z=+L_OUT (Ø interno De)
    saida = cq.Solid.makeCylinder(DE/2, S+L_OUT, pnt=cq.Vector(0,0,-S), dir=cq.Vector(0,0,1))
    fluido = fluido.fuse(saida)

    # 4) parede do vortex finder (anel De → De+2t, de z=−S até o teto) — SUBTRAI
    ext = cq.Solid.makeCylinder(DE/2+T_VF, S, pnt=cq.Vector(0,0,-S), dir=cq.Vector(0,0,1))
    int_= cq.Solid.makeCylinder(DE/2,      S, pnt=cq.Vector(0,0,-S), dir=cq.Vector(0,0,1))
    fluido = fluido.cut(ext.cut(int_))

    # 5) entrada tangencial retangular b(radial) × a(vertical), face externa tangente ao corpo
    #    ocupa x de (Dc/2 − b) a Dc/2 ; y de 0 a L_in ; z de −a a 0
    ent = (cq.Workplane("XY")
           .transformed(offset=(DC/2 - B_/2, L_IN/2, -A/2))
           .box(B_, L_IN, A).val())
    fluido = fluido.fuse(ent).clean()
    return fluido

fl = build()
bb = fl.BoundingBox()
print("="*66)
print(f" CICLONE STAIRMAND — domínio de fluido   (Dc = {DC:.0f} mm)")
print("="*66)
print(f"  a (entrada, alt) = {A:7.1f}     De (saída gás)  = {DE:7.1f}")
print(f"  b (entrada, lar) = {B_:7.1f}     S  (vortex)     = {S:7.1f}")
print(f"  h (cilindro)     = {H_:7.1f}     H  (total)      = {HT:7.1f}")
print(f"  cone             = {H_CONE:7.1f}     B  (saída pó)   = {BD:7.1f}")
print(f"\n  válido = {fl.isValid()} | volume = {fl.Volume()/1e6:.2f} L")
print(f"  bbox: X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] Z[{bb.zmin:.0f},{bb.zmax:.0f}] mm")
print(f"  altura total do modelo = {bb.zlen:.0f} mm ({bb.zlen/1000:.2f} m)")
p = os.path.join(OUT, f"ciclone_stairmand_Dc{DC:.0f}_fluido.step")
cq.exporters.export(fl, p)
print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)} bytes)")
