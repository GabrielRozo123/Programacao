"""
gen_acoplado_aerador_ejetor.py — DOMÍNIO FLUIDO ACOPLADO: aerador + reator + EJETOR

O cliente enviou o ejetor (`00__CONJUNTO_EJETOR.stp`) SEPARADO do conjunto aerador+reator.
Este script MONTA os dois num único domínio fluido de CFD.

═══════════════════════════════════════════════════════════════════════════
COTAS MEDIDAS (não estimadas) — fonte de cada uma:
═══════════════════════════════════════════════════════════════════════════
DO CONJUNTO AERADOR+REATOR  (`sugar_dominio_fluido_completo.step`, 4 sólidos, 169,7 m³):
    sólido 1 : reator          V = 139,86 m³ · Ø5080 · centro (196, −6278)
    sólido 2 : passagem        V =   4,35 m³ · Ø1100
    sólido 3 : AERADOR         V =  20,18 m³ · Ø2032 · eixo (200, −440) · z −5892 a +1220
    sólido 4 : canal do topo   V =   5,31 m³ · 1524 × 2692 × 1295

DO CONJUNTO EJETOR  (`00__CONJUNTO_EJETOR.stp`, 490 sólidos de hardware):
    lanças  : 4 × Ø73,0 OD × 3000 mm  ·  x = 0 / 350 / 700 / 1050  (passo 350, vão 1050)
    header  : 2 × Ø219,1 (8") × 1400 mm  ·  x de −175 a +1225
    Ø73,0 OD  ⇒  tubo 2½"  ⇒  ID 62,7 (Sch40)

═══════════════════════════════════════════════════════════════════════════
⚠️ AS DUAS PREMISSAS DE MONTAGEM (o CAD do conjunto NÃO veio — declarar no relatório)
═══════════════════════════════════════════════════════════════════════════
 (1) POSIÇÃO RADIAL: a fileira de 4 lanças é centrada no eixo do aerador e alinhada com X.
     → vão de 1050 mm num tanque de Ø2032 (raio 1016) ⇒ lanças em r = 175 e 525 mm. CABE.
 (2) PROFUNDIDADE: a descarga fica a Z_DESCARGA (parâmetro abaixo).
     ⇒ PEDIR AO ITO: penetração real das lanças / cota da descarga.

Convenção: mm, mesmo sistema do `sugar_dominio_fluido_completo.step`.
"""
import cadquery as cq
import os

OUT = os.path.dirname(os.path.abspath(__file__))
TANQUE = os.path.join(OUT, "sugar_dominio_fluido_completo.step")

# ── Aerador (medido) ──────────────────────────────────────────────────────
AER_X, AER_Y = 200.0, -440.0      # eixo
AER_ZTOP     = 1220.0             # topo do fluido

# ── Ejetor (medido no STEP nativo) ────────────────────────────────────────
N_LANCAS   = 4
PASSO      = 350.0                # espaçamento entre lanças
LANCA_OD   = 73.0                 # 2½"
LANCA_ID   = 62.7                 # 2½" Sch40
HEADER_OD  = 219.1                # 8"
HEADER_ID  = 202.7                # 8" Sch40
HEADER_L   = 1400.0

# ── LANÇAS ANTIGAS (3) — a serem REMOVIDAS (furos tapados) ────────────────
#    medidas em `injetor_1/2/3.step`: OD 84,8 · ID 70,8 · L 7112 mm
OLD_OD   = 84.8
OLD_ZTOP = 1865.5
OLD_ZBOT = -5246.5                # ⭐ a cota de descarga que o Marcus mandou MANTER
OLD_POS  = [(464.0, -288.0), (-64.0, -288.0), (200.0, -745.0)]   # r=305 mm, 120°

# ── MONTAGEM DO EJETOR NOVO (decisão do Marcus, 11:10) ────────────────────
#    "mantém a mesma altura de descarga da anterior · mantém a proporção do CAD"
#    → mesma boca (z=-5246,5) e mesmo topo (z=+1865,5) das antigas;
#      muda só a lança: 4 × Ø73 (ID 62,7) em fileira de passo 350, no lugar de 3 × Ø84,8 a 120°
Z_DESCARGA = OLD_ZBOT
Z_HEADER   = OLD_ZTOP

L_LANCA = Z_HEADER - Z_DESCARGA   # = 7112 mm


def posicoes_lancas():
    """x de cada lança, fileira centrada no eixo do aerador."""
    vao = (N_LANCAS - 1) * PASSO
    return [AER_X - vao/2 + i*PASSO for i in range(N_LANCAS)]


def build():
    tanque = cq.importers.importStep(TANQUE)
    solidos = tanque.solids().vals()
    print(f"  tanque importado: {len(solidos)} sólidos, "
          f"{sum(s.Volume() for s in solidos)/1e9:.2f} m³")

    xs = posicoes_lancas()

    # 0) TAPAR os furos das 3 lanças ANTIGAS (elas estavam subtraídas do fluido)
    tapa = None
    for (x, y) in OLD_POS:
        t = cq.Solid.makeCylinder(OLD_OD/2, OLD_ZTOP - OLD_ZBOT,
                                  cq.Vector(x, y, OLD_ZBOT), cq.Vector(0,0,1))
        tapa = t if tapa is None else tapa.fuse(t)

    # 1) o TUBO das lanças DESLOCA líquido → subtrair o OD do fluido do tanque
    tubos_od = None
    for x in xs:
        t = cq.Solid.makeCylinder(LANCA_OD/2, L_LANCA,
                                  cq.Vector(x, AER_Y, Z_DESCARGA), cq.Vector(0,0,1))
        tubos_od = t if tubos_od is None else tubos_od.fuse(t)

    novos = []
    for s in solidos:
        b = s.BoundingBox()
        # só o aerador é atravessado pelas lanças
        if 15e9 < s.Volume() < 26e9:
            novos.append(s.fuse(tapa).cut(tubos_od))   # tapa as antigas, abre as novas
        else:
            novos.append(s)

    # 2) o INTERIOR das lanças é domínio fluido (o xarope desce por dentro)
    interior = None
    for x in xs:
        t = cq.Solid.makeCylinder(LANCA_ID/2, L_LANCA,
                                  cq.Vector(x, AER_Y, Z_DESCARGA), cq.Vector(0,0,1))
        interior = t if interior is None else interior.fuse(t)

    # 3) header 8" horizontal alimentando as 4 lanças
    hx0 = min(xs) - 175.0
    header = cq.Solid.makeCylinder(HEADER_ID/2, HEADER_L,
                                   cq.Vector(hx0, AER_Y, Z_HEADER), cq.Vector(1,0,0))

    ejetor = interior.fuse(header)

    todos = novos + [ejetor]
    comp = todos[0]
    for s in todos[1:]:
        comp = comp.fuse(s)
    return comp.clean(), xs


if __name__ == "__main__":
    fl, xs = build()
    bb = fl.BoundingBox()
    print("="*72)
    print("  DOMÍNIO ACOPLADO — aerador + reator + ejetor")
    print("="*72)
    print(f"  lanças em x = {['%.0f' % x for x in xs]}  (y = {AER_Y:.0f})")
    print(f"  raio de cada lança ao eixo: "
          f"{[round(abs(x-AER_X)) for x in xs]} mm   (raio do aerador = 1016)")
    print(f"  comprimento da lança  = {L_LANCA:.0f} mm")
    print(f"  descarga em z         = {Z_DESCARGA:.0f} mm   (MESMA das 3 antigas ✅)")
    print(f"  topo/header em z      = {Z_HEADER:.0f} mm")
    print(f"  submergência          = {AER_ZTOP - Z_DESCARGA:.0f} mm de líquido acima da descarga")
    print(f"  3 lanças antigas      : REMOVIDAS (furos tapados)")
    print(f"\n  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m³")
    print(f"  bbox X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] Z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    p = os.path.join(OUT, "ACOPLADO_aerador_reator_ejetor_fluido.step")
    cq.exporters.export(fl, p)
    print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e6:.2f} MB)")
