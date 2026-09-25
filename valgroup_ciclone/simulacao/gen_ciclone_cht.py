"""
gen_ciclone_cht.py — FLUIDO + SÓLIDO do ciclone Stairmand para o estudo CHT/FEA — Valgroup.

Gera as DUAS geometrias do mesmo modelo paramétrico, com a superfície interna do sólido
EXATAMENTE coincidente com a externa do fluido (o sólido é construído cortando o fluido de
um envelope externo). Isso é o que permite o STAR detectar o contato sozinho na importação
via "Create Part Contacts from Coincident Entities".

Contexto: continuação do projeto Valgroup — o Simas faz o FEA (Simcenter 3D, ASME VIII Div. 1)
e precisa dos campos de pressão e temperatura. A espessura de 4,75 mm é o valor preliminar
calculado pela Valgroup (e-mail Thays, 24/09/2026) que o FEA vai validar.

Saídas:
    ciclone_Dc<DC>_t<T>_fluido.step     — domínio de fluido (CFD + lagrangeano)
    ciclone_Dc<DC>_t<T>_solido.step     — casca de aço 304L (condução + convecção externa)
    ciclone_Dc<DC>_t<T>_ASSEMBLY.step   — os dois corpos juntos  <<< IMPORTAR ESTE

Convenção de eixos (igual ao gen_ciclone_stairmand.py):
    z = 0 no TETO do ciclone · z cresce para CIMA · o cone desce para z negativo.

Uso:
    python3 gen_ciclone_cht.py [Dc_mm] [t_mm]        (default: 307  4.75)
"""
import cadquery as cq
from cadquery import exporters
import os, sys, math

OUT = os.path.dirname(os.path.abspath(__file__))

# ── parâmetros ────────────────────────────────────────────────────────────
DC = float(sys.argv[1]) if len(sys.argv) > 1 else 307.0    # Ø do corpo (mm)
T  = float(sys.argv[2]) if len(sys.argv) > 2 else 4.75     # espessura de parede (mm)

# proporções Stairmand (alta eficiência) — idênticas ao modelo do estudo anterior
A  = 0.50  * DC            # altura da entrada
B_ = 0.20  * DC            # largura da entrada (radial)
DE = 0.50  * DC            # Ø saída de gás (vortex finder)
S  = 0.50  * DC            # mergulho do vortex finder abaixo do teto
H_ = 1.50  * DC            # altura da parte cilíndrica
HT = 4.00  * DC            # altura total (cilindro + cone)
BD = 0.375 * DC            # Ø saída de pó

# extensões para o CFD (espaço para as BCs — não fazem parte da norma)
L_IN   = 1.5 * DC
L_OUT  = 1.0 * DC
L_DUST = 0.5 * DC

H_CONE = HT - H_

# Offset radial da casca cônica.
#
# Rigorosamente, numa chapa calandrada a espessura é medida NORMAL à superfície, e o
# acréscimo no raio seria t/cos(alpha) = 4,787 mm (alpha = 7,13°).
#
# MAS isso deixa um degrau de 0,037 mm nas junções cilindro/cone (z=-h) e cone/tubo de pó
# (z=-HT), porque ali o offset volta a ser t. Esse degrau vira duas faces-lâmina de 37 e
# 14 mm² — veneno para o remesher numa malha de 3-4 mm.
#
# Como este sólido existe para CONDUZIR CALOR (o aço responde por 0,3% da resistência
# térmica total), 0,7% de espessura não muda nada no resultado, e geometria limpa vale
# muito mais. Offset uniforme = T em todo o casco.
#
# Para o modelo ESTRUTURAL a escolha seria a oposta — mas esse é o modelo do FEA, não este.
ALPHA        = math.atan((DC/2 - BD/2) / H_CONE)   # semiângulo do cone (só informativo)
OFFSET_NORMAL = False                               # True -> t/cos(alpha), gera as lâminas
T_CONE = (T / math.cos(ALPHA)) if OFFSET_NORMAL else T

# ── FLUIDO ────────────────────────────────────────────────────────────────
def build_fluido():
    # corpo cilíndrico: z de -H_ a 0
    corpo = cq.Solid.makeCylinder(DC/2, H_, pnt=cq.Vector(0, 0, -H_), dir=cq.Vector(0, 0, 1))
    # cone: base menor (BD/2) em -HT, base maior (DC/2) em -H_
    cone  = cq.Solid.makeCone(BD/2, DC/2, H_CONE, pnt=cq.Vector(0, 0, -HT), dir=cq.Vector(0, 0, 1))
    f = corpo.fuse(cone)

    # tubo da saída de pó (abaixo do ápice)
    f = f.fuse(cq.Solid.makeCylinder(BD/2, L_DUST,
               pnt=cq.Vector(0, 0, -HT - L_DUST), dir=cq.Vector(0, 0, 1)))

    # tubo de saída de gás: de z=-S até z=+L_OUT
    f = f.fuse(cq.Solid.makeCylinder(DE/2, S + L_OUT,
               pnt=cq.Vector(0, 0, -S), dir=cq.Vector(0, 0, 1)))

    # parede do vortex finder: anel DE/2 -> DE/2+T, de z=-S ao teto — SUBTRAI do fluido
    # (T unificado com a espessura do casco; o modelo anterior usava 4 mm fixos aqui)
    ext = cq.Solid.makeCylinder(DE/2 + T, S, pnt=cq.Vector(0, 0, -S), dir=cq.Vector(0, 0, 1))
    itn = cq.Solid.makeCylinder(DE/2,     S, pnt=cq.Vector(0, 0, -S), dir=cq.Vector(0, 0, 1))
    f = f.cut(ext.cut(itn))

    # entrada tangencial retangular b(radial) x a(vertical), face externa tangente ao corpo
    ent = (cq.Workplane("XY")
           .transformed(offset=(DC/2 - B_/2, L_IN/2, -A/2))
           .box(B_, L_IN, A).val())
    return f.fuse(ent).clean()

# ── ENVELOPE EXTERNO (fluido + casca) ─────────────────────────────────────
def build_envelope():
    # corpo cilíndrico + espessura do teto (z de -H_ a +T)
    corpo = cq.Solid.makeCylinder(DC/2 + T, H_ + T,
            pnt=cq.Vector(0, 0, -H_), dir=cq.Vector(0, 0, 1))
    # cone externo: offset normal -> t/cos(alpha) no raio
    cone  = cq.Solid.makeCone(BD/2 + T_CONE, DC/2 + T_CONE, H_CONE,
            pnt=cq.Vector(0, 0, -HT), dir=cq.Vector(0, 0, 1))
    e = corpo.fuse(cone)

    # tubo da saída de pó
    e = e.fuse(cq.Solid.makeCylinder(BD/2 + T, L_DUST,
               pnt=cq.Vector(0, 0, -HT - L_DUST), dir=cq.Vector(0, 0, 1)))

    # tubo de saída de gás acima do teto (a parte abaixo do teto já vem do corpo)
    e = e.fuse(cq.Solid.makeCylinder(DE/2 + T, S + L_OUT,
               pnt=cq.Vector(0, 0, -S), dir=cq.Vector(0, 0, 1)))

    # duto de entrada: engrossa só na seção transversal (x e z), mantém o comprimento em y
    ent = (cq.Workplane("XY")
           .transformed(offset=(DC/2 - B_/2, L_IN/2, -A/2))
           .box(B_ + 2*T, L_IN, A + 2*T).val())
    return e.fuse(ent).clean()

# ── construção ────────────────────────────────────────────────────────────
fluido = build_fluido()
solido = build_envelope().cut(fluido).clean()

# ── relatório ─────────────────────────────────────────────────────────────
bbf, bbs = fluido.BoundingBox(), solido.BoundingBox()
area_int = sum(f.Area() for f in solido.Faces())   # referência grosseira

print("=" * 70)
print(f" CICLONE STAIRMAND — CHT (fluido + sólido)   Dc = {DC:.0f} mm · t = {T:.2f} mm")
print("=" * 70)
print(f"  a (entrada, alt) = {A:7.1f}     De (saída gás)  = {DE:7.1f}")
print(f"  b (entrada, lar) = {B_:7.1f}     S  (vortex)     = {S:7.1f}")
print(f"  h (cilindro)     = {H_:7.1f}     H  (total)      = {HT:7.1f}")
print(f"  cone             = {H_CONE:7.1f}     B  (saída pó)   = {BD:7.1f}")
print(f"  semiângulo do cone = {math.degrees(ALPHA):.2f}°  ->  offset radial da casca = {T_CONE:.3f} mm")
print()
print(f"  FLUIDO  válido={fluido.isValid()}  volume = {fluido.Volume()/1e6:8.2f} L")
print(f"          bbox X[{bbf.xmin:.0f},{bbf.xmax:.0f}] Y[{bbf.ymin:.0f},{bbf.ymax:.0f}] Z[{bbf.zmin:.0f},{bbf.zmax:.0f}]")
print(f"  SÓLIDO  válido={solido.isValid()}  volume = {solido.Volume()/1e6:8.2f} L")
print(f"          bbox X[{bbs.xmin:.0f},{bbs.xmax:.0f}] Y[{bbs.ymin:.0f},{bbs.ymax:.0f}] Z[{bbs.zmin:.0f},{bbs.zmax:.0f}]")
print(f"          massa de aço (7900 kg/m3) = {solido.Volume()/1e9*7900:.1f} kg")
print(f"          área total de faces = {area_int/1e6:.3f} m2")

# verificação: volume do sólido ~ área de parede x espessura
print()
print("  >> conferir: 'válido' True nos dois, e a massa de aço plausível para o porte.")

# ── exportação ────────────────────────────────────────────────────────────
tag = f"Dc{DC:.0f}_t{T:.2f}".replace(".", "p")
pf = os.path.join(OUT, f"ciclone_{tag}_fluido.step")
ps = os.path.join(OUT, f"ciclone_{tag}_solido.step")
pa = os.path.join(OUT, f"ciclone_{tag}_ASSEMBLY.step")

exporters.export(fluido, pf)
exporters.export(solido, ps)

# assembly com os dois corpos — é ESTE que vai para o STAR
asm = cq.Assembly()
asm.add(fluido, name="FLUIDO")
asm.add(solido, name="SOLIDO_304L")
asm.save(pa)

print()
for p in (pf, ps, pa):
    print(f"  STEP -> {os.path.basename(p):42s} ({os.path.getsize(p):>9,} bytes)")
print()
print("  >>> IMPORTAR NO STAR:  " + os.path.basename(pa))
print("      Surface Import -> marcar 'Create Part Contacts from Coincident Entities'")
print("      Depois: multi-selecionar as DUAS partes -> Assign Parts to Regions")
print("              -> 'Create a Region For Each Part'")
print("              -> 'Create Contact-mode Interfaces from Contacts'   (exigido pelo FE Solid Energy)")
