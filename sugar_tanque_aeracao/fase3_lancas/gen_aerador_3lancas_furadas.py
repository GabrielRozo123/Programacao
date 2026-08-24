"""
gen_aerador_3lancas_furadas.py — DOMÍNIO FLUIDO do aerador com 3 LANÇAS PERFURADAS
                                  (Fase 3 · Ito — pedido do Marcus, 3 lanças)

Substitui as 3 lanças originais do cliente (Ø84,8 em r = 305, 120° entre si) por
3 lanças perfuradas no ponto de projeto do RELATORIO §8.4:

    tubo 2½" Sch40 (OD 73,0 · ID 62,68 · parede 5,16)
    48 furos Ø1,0 mm — 2 anéis de 24, defasados de meio passo, passo axial 15 mm
    TAMPA CEGA na ponta

⚠️ TOPOLOGIA — diferente da convenção das rodadas anteriores, e de propósito:

   Antes: a lança era um CILINDRO CHEIO subtraído do fluido, com o ar entrando por
          um disco na ponta. O interior não era resolvido.

   Agora: subtrai-se apenas a PAREDE do tubo (anel) mais a tampa. O interior da
          lança FICA NO DOMÍNIO FLUIDO, conectado ao tanque pelos 48 furos.
          O ar entra pelo disco no topo (z = 1220) e tem de se distribuir sozinho
          entre os 48 furos.

   Isso é o que permite VERIFICAR o critério de uniformidade do relatório
   (ΔP_furo ≥ 4 × ΔP_hidrostático, razão calculada = 5,0). Com o interior fora do
   domínio, a distribuição entre furos seria imposta, não medida.

MALHA — por que 3 lanças cabem:
   O furo aqui é uma ABERTURA, não uma interface a resolver (o SMD é prescrito no
   modelo EMP). Bastam ~4 células no diâmetro, ou seja 0,25 mm, contra os 0,125 mm
   que um VOF exigiria. São ~1e4 células por furo → 1,5e6 para os 144 furos.
   Use SURFACE SIZE customizado no contorno `lanca.furos`; não monte 144 controles
   volumétricos.

Saída: aerador_3lancas_furadas_fluido.step — só o AERADOR.
Convenção: mm, mesmo sistema do STEP do cliente.
"""
import cadquery as cq
import math, os

from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(OUT, "..", "geometria", "sugar_dominio_fluido_completo.step")

AER_X, AER_Y, AER_R = 200.0, -440.0, 1016.0
AER_ZTOP, AER_ZFUNDO = 1220.0, -5892.0
CONE_R0, CONE_K = 259.5, 0.4966
Z_INICIO_CONE = -4368.6

# ── Lança recomendada (RELATORIO §8.4) ────────────────────────────────────
OD, ID = 73.0, 62.68
PAREDE = (OD - ID) / 2
D_FURO, N_ANEL = 1.0, 24
Z_ANEL1, Z_ANEL2 = 30.0, 45.0               # acima da base da tampa
T_TAMPA = 6.0
DEFASAGEM = math.pi / N_ANEL

# ── Posições ORIGINAIS do cliente (detectadas no STEP, não supostas) ──────
R_LANCA, Z_DESCARGA, Z_TOPO = 305.0, -5246.5, 1220.0
ANGULOS = [-90.0, 29.9, 150.1]              # graus, do centro do aerador


def raio_tanque(z):
    return AER_R if z >= Z_INICIO_CONE else CONE_R0 + CONE_K * (z - AER_ZFUNDO)


def cil(d, z0, z1, x, y):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def aerador_liso():
    """Aerador do cliente com as 3 lanças ORIGINAIS tapadas (detectadas)."""
    aer = next(s for s in cq.importers.importStep(BASE).solids().vals()
               if 15e9 < s.Volume() < 26e9)
    v0 = aer.Volume()
    achadas = []
    for f in aer.Faces():
        surf = GeomAdaptor_Surface(BRep_Tool.Surface_s(f.wrapped))
        if surf.GetType() != GeomAbs_Cylinder:
            continue
        c = surf.Cylinder()
        if c.Radius() > 200.0:
            continue
        bb, ax = f.BoundingBox(), c.Axis().Location()
        achadas.append((c.Radius(), ax.X(), ax.Y(), bb.zmin, bb.zmax))
    for R, x, y, zmin, zmax in achadas:
        print(f"    tapando lança original: Ø{2*R:.1f} em ({x:.0f},{y:.0f})")
        aer = aer.fuse(cil(2 * R, zmin, zmax, x, y))
    aer = aer.clean()
    print(f"    volume {v0/1e9:.4f} → {aer.Volume()/1e9:.4f} m³")
    return aer


def lanca_perfurada(x, y):
    """Sólido a subtrair: PAREDE do tubo + tampa cega, já com os 48 furos abertos.

    O interior do tubo NÃO entra neste sólido — ele permanece fluido."""
    z_base = Z_DESCARGA
    externo = cil(OD, z_base, Z_TOPO, x, y)
    interno = cil(ID, z_base + T_TAMPA, Z_TOPO + 1.0, x, y)   # +1 garante corte limpo no topo
    solido = externo.cut(interno)                              # anel + tampa maciça embaixo

    brocas = []
    for dz, fase in ((Z_ANEL1, 0.0), (Z_ANEL2, DEFASAGEM)):
        z = z_base + dz
        for k in range(N_ANEL):
            a = fase + 2 * math.pi * k / N_ANEL
            brocas.append(cq.Solid.makeCylinder(
                D_FURO / 2, OD,
                cq.Vector(x, y, z),
                cq.Vector(math.cos(a), math.sin(a), 0)))
    return solido.cut(cq.Compound.makeCompound(brocas))


def build():
    print("=" * 74)
    print("  AERADOR COM 3 LANÇAS PERFURADAS — domínio fluido")
    print("=" * 74)
    aer = aerador_liso()
    v_liso = aer.Volume()

    pos = []
    for ang in ANGULOS:
        a = math.radians(ang)
        pos.append((AER_X + R_LANCA * math.cos(a), AER_Y + R_LANCA * math.sin(a)))

    print(f"\n  Verificação de folga contra o cone (ponto a ponto):")
    pior = 1e9
    for z in [Z_DESCARGA + i * 50 for i in range(int((Z_TOPO - Z_DESCARGA) / 50) + 1)]:
        pior = min(pior, raio_tanque(z) - (R_LANCA + OD / 2))
    print(f"    folga mínima = {pior:.1f} mm  {'✅' if pior > 50 else '⚠️'}")

    for i, (x, y) in enumerate(pos, 1):
        print(f"  subtraindo lança {i}/3 em ({x:8.1f},{y:8.1f}) … ", end="", flush=True)
        aer = aer.cut(lanca_perfurada(x, y))
        print("ok")
    aer = aer.clean()

    v = aer.Volume()
    v_parede = 3 * (math.pi / 4 * (OD**2 - ID**2) * (Z_TOPO - Z_DESCARGA)
                    + math.pi / 4 * ID**2 * T_TAMPA
                    - 2 * N_ANEL * math.pi / 4 * D_FURO**2 * PAREDE)
    print(f"\n  volume liso     = {v_liso/1e9:.4f} m³")
    print(f"  volume final    = {v/1e9:.4f} m³")
    print(f"  parede removida = {(v_liso-v)/1e6:.2f} L   (analítico {v_parede/1e6:.2f} L)"
          f"  desvio {((v_liso-v)/v_parede-1)*100:+.3f} %")

    a_furo = math.pi / 4 * (D_FURO / 1000) ** 2
    print(f"\n  furos: 3 × 48 = {3*2*N_ANEL} · área somada {3*2*N_ANEL*a_furo*1e6:.1f} mm²")
    print(f"  vazão de projeto 40 m³/h → {40/3600/(3*2*N_ANEL*a_furo):.1f} m/s no furo")

    print(f"\n  faces = {len(aer.Faces())}")
    print("""
  CONTORNOS a criar no STAR (por lança):
    lanca.parede_ext  cilindro Ø73,0     → Wall
    lanca.parede_int  cilindro Ø62,68    → Wall
    lanca.tampa       disco no fundo     → Wall
    lanca.furos       48 cilindros Ø1,0  → Wall  ⭐ SURFACE SIZE = 0,25 mm aqui
    lanca.inlet       disco Ø62,68 em z = 1220 → entrada de ar""")

    out = os.path.join(OUT, "aerador_3lancas_furadas_fluido.step")
    cq.exporters.export(aer, out)
    print(f"\n  → {os.path.basename(out)}")
    return aer


if __name__ == "__main__":
    build()
