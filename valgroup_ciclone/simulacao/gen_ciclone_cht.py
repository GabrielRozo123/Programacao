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
    ciclone_<tag>_fluido.step     — domínio de fluido (CFD + lagrangeano)
    ciclone_<tag>_solido.step     — casca de aço 304L (condução + convecção externa)
    ciclone_<tag>_ASSEMBLY.step   — os dois corpos juntos  <<< IMPORTAR ESTE

Convenção de eixos (igual ao gen_ciclone_stairmand.py):
    z = 0 no TETO do ciclone · z cresce para CIMA · o cone desce para z negativo.
    O duto de entrada corre ao longo de +y; y = 0 é o plano que contém o eixo do ciclone,
    onde a parede EXTERNA do duto tangencia o corpo.

Entrada com transição redondo-retangular (pedido Valgroup, 13/10/2026):
    a montante do duto retangular entra uma transição para um tubo redondo. Topologia:

        ciclone ── duto retangular (y = 0 → L_ret) ── transição (L_trans) ── tubo redondo (L_tubo)

    O tubo redondo a montante é EXTENSÃO DE CFD (afasta a condição de contorno da transição);
    não é peça do FEA. Sem --d-tubo o modelo é o original: duto retangular de 1,5·Dc, sem
    transição.

Uso:
    python3 gen_ciclone_cht.py [Dc_mm] [t_mm]                       (default: 307  4.75)
    python3 gen_ciclone_cht.py 307 4.75 --l-ret 250 --d-tubo 102.3 --l-trans 200
"""
import cadquery as cq
from cadquery import exporters
import argparse, os, math

# ── parâmetros ────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser(description="Ciclone Stairmand — fluido + sólido para CHT/FEA")
ap.add_argument("dc", nargs="?", type=float, default=307.0, help="Ø do corpo (mm)")
ap.add_argument("t",  nargs="?", type=float, default=4.75,  help="espessura de parede (mm)")
ap.add_argument("--l-ret",   type=float, help="duto retangular, de y=0 até o início da transição (mm). Default 1,5·Dc")
ap.add_argument("--d-tubo",  type=float, help="Ø INTERNO do tubo redondo a montante (mm). Ativa a transição")
ap.add_argument("--l-trans", type=float, help="comprimento da transição redondo-retangular (mm)")
ap.add_argument("--l-tubo",  type=float, help="trecho reto de tubo redondo — extensão de CFD (mm). Default 5·D")
ap.add_argument("--dx-tubo", type=float, default=0.0, help="desvio radial do eixo do tubo em relação ao centro do retângulo (mm)")
ap.add_argument("--dz-tubo", type=float, default=0.0, help="desvio vertical do eixo do tubo em relação ao centro do retângulo (mm)")
ap.add_argument("--t-tubo",  type=float, help="espessura do tubo redondo (mm). Default = t")
ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)), help="pasta de saída")
args = ap.parse_args()

DC, T, OUT = args.dc, args.t, args.out

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

# entrada: duto retangular + (opcional) transição + tubo redondo
TRANS   = args.d_tubo is not None
L_RET   = args.l_ret if args.l_ret is not None else L_IN
XC, ZC  = DC/2 - B_/2, -A/2                  # centro da seção retangular
if TRANS:
    if args.l_trans is None:
        ap.error("--d-tubo exige --l-trans")
    R_TUBO  = args.d_tubo / 2
    L_TRANS = args.l_trans
    L_TUBO  = args.l_tubo if args.l_tubo is not None else 5 * args.d_tubo
    T_TUBO  = args.t_tubo if args.t_tubo is not None else T
    DX, DZ  = args.dx_tubo, args.dz_tubo

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


# ── transição redondo-retangular ──────────────────────────────────────────
# Loft REGRADO entre o retângulo e um círculo partido em 4 arcos, com os vértices do círculo
# nos mesmos ângulos dos cantos do retângulo. Assim cada lado reto casa com um arco e o loft
# não torce — é a mesma lógica da peça de caldeiraria (lado reto -> quarto de cone).
#
# Pela mesma razão da casca cônica, o envelope é um offset RADIAL (t na seção), não normal à
# superfície: nas junções retângulo/transição e transição/tubo as seções casam exatamente e
# não sobra degrau. Na transição a espessura normal fica t·cos(semiângulo) — ~3 % a menos
# para 15°, irrelevante para condução.
def _cantos(w, h):
    """Ângulos dos 4 cantos do retângulo w×h vistos do centro, em ordem crescente."""
    a0 = math.atan2(h/2, w/2)
    return [-a0, a0, math.pi - a0, math.pi + a0]


def _secao_ret(y, w, h):
    angs = _cantos(w, h)
    pts = [cq.Vector(XC + math.copysign(w/2, math.cos(a)), y, ZC + math.copysign(h/2, math.sin(a)))
           for a in angs]
    return cq.Wire.makePolygon(pts, close=True), angs


def _secao_circ(y, r, angs, dx, dz):
    cx, cz = XC + dx, ZC + dz
    p = lambda a: cq.Vector(cx + r*math.cos(a), y, cz + r*math.sin(a))
    angs4 = angs + [angs[0] + 2*math.pi]
    arcos = [cq.Edge.makeThreePointArc(p(a), p((a + b)/2), p(b)) for a, b in zip(angs4, angs4[1:])]
    return cq.Wire.assembleEdges(arcos)


def transicao(w, h, r, y0, comp, dx, dz):
    """Sólido da transição: retângulo w×h em y0  ->  círculo de raio r em y0 + comp."""
    w_ret, angs = _secao_ret(y0, w, h)
    w_cir = _secao_circ(y0 + comp, r, angs, dx, dz)
    return cq.Solid.makeLoft([w_ret, w_cir], ruled=True)


def tubo(r, y0, comp, dx, dz):
    return cq.Solid.makeCylinder(r, comp, pnt=cq.Vector(XC + dx, y0, ZC + dz), dir=cq.Vector(0, 1, 0))


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
           .transformed(offset=(XC, L_RET/2, ZC))
           .box(B_, L_RET, A).val())
    f = f.fuse(ent)

    if TRANS:
        f = f.fuse(transicao(B_, A, R_TUBO, L_RET, L_TRANS, DX, DZ))
        f = f.fuse(tubo(R_TUBO, L_RET + L_TRANS, L_TUBO, DX, DZ))
    return f.clean()

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
           .transformed(offset=(XC, L_RET/2, ZC))
           .box(B_ + 2*T, L_RET, A + 2*T).val())
    e = e.fuse(ent)

    if TRANS:
        e = e.fuse(transicao(B_ + 2*T, A + 2*T, R_TUBO + T_TUBO, L_RET, L_TRANS, DX, DZ))
        e = e.fuse(tubo(R_TUBO + T_TUBO, L_RET + L_TRANS, L_TUBO, DX, DZ))
    return e.clean()

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

# onde a parede interna do duto (x = Dc/2 - b) deixa de cortar o casco: abaixo disto o duto
# ainda está "dentro" do corpo, e a transição não pode começar
y_casco = math.sqrt((DC/2 + T)**2 - (DC/2 - B_ - T)**2)
print(f"\n  ENTRADA: duto retangular de y = 0 a {L_RET:.1f} mm "
      f"(a parede interna do duto sai do casco em y ≈ {y_casco:.1f} mm)")
if TRANS:
    A_ret, A_tubo = A*B_, math.pi*R_TUBO**2
    # semiângulos por lado, no sentido do escoamento (tubo -> retângulo); + = expande
    lados = {"topo":  (A/2 - DZ) - R_TUBO, "fundo": (A/2 + DZ) - R_TUBO,
             "externo": (B_/2 - DX) - R_TUBO, "interno": (B_/2 + DX) - R_TUBO}
    ang = {k: math.degrees(math.atan(v / L_TRANS)) for k, v in lados.items()}
    print(f"  transição: Ø{2*R_TUBO:.1f} -> {B_:.1f} × {A:.1f} mm em {L_TRANS:.1f} mm "
          f"· tubo reto de CFD {L_TUBO:.1f} mm (t = {T_TUBO:.2f})")
    print(f"  área retângulo / área tubo = {A_ret/A_tubo:.3f}  "
          f"({'EXPANDE' if A_ret > A_tubo else 'CONTRAI'} em área no sentido do escoamento)")
    print("  semiângulos por lado (+ expande, − contrai):  " +
          " · ".join(f"{k} {v:+.1f}°" for k, v in ang.items()))
    if max(ang.values()) > 7.5:
        print(f"  >> ATENÇÃO: lado expandindo a {max(ang.values()):.1f}° (> ~7,5°) — "
              "risco de descolamento na transição")
    if L_RET < y_casco:
        print(f"  >> ATENÇÃO: L_ret = {L_RET:.1f} < {y_casco:.1f} mm — a transição começa dentro do casco")
    corpo_env = cq.Solid.makeCylinder(DC/2 + T, H_ + T, pnt=cq.Vector(0, 0, -H_), dir=cq.Vector(0, 0, 1))
    choque = transicao(B_ + 2*T, A + 2*T, R_TUBO + T_TUBO, L_RET, L_TRANS, DX, DZ).intersect(corpo_env)
    v_choque = choque.Volume() if choque.Solids() else 0.0
    print(f"  interferência transição × casco: {v_choque:.1f} mm³"
          + ("  >> COLIDE — aumentar L_ret" if v_choque > 1.0 else "  (livre)"))

print()
print(f"  FLUIDO  válido={fluido.isValid()}  volume = {fluido.Volume()/1e6:8.2f} L")
print(f"          bbox X[{bbf.xmin:.0f},{bbf.xmax:.0f}] Y[{bbf.ymin:.0f},{bbf.ymax:.0f}] Z[{bbf.zmin:.0f},{bbf.zmax:.0f}]")
print(f"  SÓLIDO  válido={solido.isValid()}  volume = {solido.Volume()/1e6:8.2f} L")
print(f"          bbox X[{bbs.xmin:.0f},{bbs.xmax:.0f}] Y[{bbs.ymin:.0f},{bbs.ymax:.0f}] Z[{bbs.zmin:.0f},{bbs.zmax:.0f}]")
print(f"          massa de aço (7900 kg/m3) = {solido.Volume()/1e9*7900:.1f} kg")
print(f"          área total de faces = {area_int/1e6:.3f} m2")

# faces-lâmina: o que derrubou o remesher na primeira versão (37 e 14 mm²)
laminas = sorted(f.Area() for f in solido.Faces() if f.Area() < 50.0)
print(f"          faces < 50 mm²: {len(laminas)}" + (f"  {[round(a, 2) for a in laminas]}" if laminas else ""))

# verificação: volume do sólido ~ área de parede x espessura
print()
print("  >> conferir: 'válido' True nos dois, e a massa de aço plausível para o porte.")

# ── exportação ────────────────────────────────────────────────────────────
tag = f"Dc{DC:.0f}_t{T:.2f}".replace(".", "p")
if TRANS:
    tag += f"_Lr{L_RET:.0f}_D{2*R_TUBO:.0f}_Lt{L_TRANS:.0f}"
os.makedirs(OUT, exist_ok=True)
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
