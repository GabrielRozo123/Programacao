"""
gen_acoplado_aerador_ejetor.py — DOMÍNIO FLUIDO ACOPLADO: aerador + reator + EJETOR COMPLETO

O cliente enviou o ejetor (`00__CONJUNTO_EJETOR.stp`, CAD do Brendo) SEPARADO do conjunto
aerador+reator. Este script monta os dois num único domínio fluido de CFD, com o perfil
interno do ejetor MEDIDO sólido a sólido no CAD nativo.

═══════════════════════════════════════════════════════════════════════════
1) COTAS DO TANQUE  (`sugar_dominio_fluido_completo.step`, 4 sólidos)
═══════════════════════════════════════════════════════════════════════════
    reator 139,86 m³ Ø5080 · passagem 4,35 m³ · canal do topo 5,31 m³
    AERADOR 20,18 m³ · Ø2032 · eixo (200, −440) · z de −5892 a +1220

═══════════════════════════════════════════════════════════════════════════
2) PERFIL INTERNO DO EJETOR  — MEDIDO no CAD nativo (coordenada Y do CAD)
═══════════════════════════════════════════════════════════════════════════
    Y = 858   header 8"          (OD 219,1 · ID 202,7)
    Y = 764   início do ramal 4" (OD 114,3 · ID 102,3)
    Y = 542   ⭐ PORTA DE AR 1½"  (ID 38,1) — LATERAL
    Y = 224,3 fim do 4"
    Y = 199   ⭐ CONTRAÇÃO 4"→2"  (ID 102,3 → 52,5) = assento do BICO
    Y = 174,3 fim do 2"          → BICO: 7 furos Ø9 em PCD Ø27
    Y = 0     topo da lança 2½"  (OD 73,0 · ID 62,7)
    Y = −3000 fim da lança no CAD

    ⚠️ ACHADO: a porta de ar está **318 mm A MONTANTE** da contração — ou seja, no trecho de
    4", onde a pressão é MÁXIMA. Num eductor correto ela fica NA GARGANTA (pressão mínima).
    Razão de contração 4"→2" = 3,80:1 (82,2 → 21,6 cm²).
    ⇒ É a explicação geométrica da sucção 1000× fraca medida no CFD do ejetor isolado.

═══════════════════════════════════════════════════════════════════════════
3) MONTAGEM  (decisão do Marcus, chat 11:10)
═══════════════════════════════════════════════════════════════════════════
    "manter a mesma altura de descarga da anterior · manter a proporção do CAD"
    → boca em z = −5246,5 (a mesma das 3 lanças antigas, que foram REMOVIDAS)
    → cabeça do ejetor (header→ar→contração→bico) com as cotas EXATAS do CAD
    → só a LANÇA é alongada (é tubo de entrega) para alcançar a boca

    ⚠️ ÚNICA PREMISSA restante: POSIÇÃO RADIAL — fileira de 4 lanças centrada no eixo do
       aerador e alinhada com X (o CAD do conjunto não define orientação).
       Raios resultantes: 175 e 525 mm, contra 1016 de raio do tanque. Cabe.

Convenção: mm, mesmo sistema do `sugar_dominio_fluido_completo.step`.
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))
TANQUE = os.path.join(OUT, "sugar_dominio_fluido_completo.step")

# ── Tanque ────────────────────────────────────────────────────────────────
AER_X, AER_Y = 200.0, -440.0
AER_ZTOP     = 1220.0

# ── Lanças antigas (a remover) ────────────────────────────────────────────
OLD_OD, OLD_ZTOP, OLD_ZBOT = 84.8, 1865.5, -5246.5
OLD_POS = [(464.0, -288.0), (-64.0, -288.0), (200.0, -745.0)]

# ── Ejetor: diâmetros INTERNOS (o que o CFD precisa) ──────────────────────
HEADER_ID = 202.7    # 8"  Sch40
RAMAL_ID  = 102.3    # 4"  Sch40
AR_ID     =  38.1    # 1½"
GARG_ID   =  52.5    # 2"  Sch40  (assento do bico)
LANCA_ID  =  62.7    # 2½" Sch40
LANCA_OD  =  73.0
N_FUROS, D_FURO, PCD = 7, 9.0, 27.0     # bico

N_LANCAS, PASSO = 4, 350.0

# ── Mapeamento Y(CAD) → z(modelo): bico (Y=199) na cota do topo antigo ────
Z_BICO = OLD_ZTOP                       # 1865,5
zc = lambda Y: Z_BICO + (Y - 199.0)

Z_HEADER   = zc(858.0)     # 2524,5
Z_RAMAL_T  = zc(764.0)     # 2430,5
Z_AR       = zc(542.0)     # 2208,5
Z_CONTR_T  = zc(224.3)     # 1890,8   topo da contração
Z_CONTR_B  = zc(199.0)     # 1865,5   fim da contração = assento
Z_BICO_B   = zc(174.3)     # 1840,8   saída do bico
Z_DESCARGA = OLD_ZBOT      # −5246,5

AR_STUB, XAROPE_STUB = 250.0, 300.0


def xs_lancas():
    vao = (N_LANCAS - 1) * PASSO
    return [AER_X - vao/2 + i*PASSO for i in range(N_LANCAS)]


def cil(d, h, x, y, z, dr=(0, 0, 1)):
    return cq.Solid.makeCylinder(d/2, h, cq.Vector(x, y, z), cq.Vector(*dr))


def cabeca_ejetor(x):
    """Um ramal completo: 4" → porta de ar → contração → bico (7 furos) → lança."""
    p = cil(RAMAL_ID, Z_RAMAL_T - Z_CONTR_T, x, AER_Y, Z_CONTR_T)          # ramal 4"
    p = p.fuse(cil(AR_ID, AR_STUB, x, AER_Y, Z_AR, (0, 1, 0)))              # ⭐ porta de ar
    p = p.fuse(cq.Solid.makeCone(RAMAL_ID/2, GARG_ID/2, Z_CONTR_T - Z_CONTR_B,
                                 cq.Vector(x, AER_Y, Z_CONTR_B), cq.Vector(0, 0, 1)))  # contração
    # BICO: 7 furos Ø9 (1 central + 6 no PCD Ø27)
    for k in range(N_FUROS):
        if k == 0:
            fx, fy = x, AER_Y
        else:
            a = 2*math.pi*(k-1)/(N_FUROS-1)
            fx, fy = x + PCD/2*math.cos(a), AER_Y + PCD/2*math.sin(a)
        p = p.fuse(cil(D_FURO, Z_CONTR_B - Z_BICO_B, fx, fy, Z_BICO_B))
    p = p.fuse(cil(LANCA_ID, Z_BICO_B - Z_DESCARGA, x, AER_Y, Z_DESCARGA))  # lança
    return p


def build():
    tanque = cq.importers.importStep(TANQUE)
    solidos = tanque.solids().vals()
    print(f"  tanque: {len(solidos)} sólidos, {sum(s.Volume() for s in solidos)/1e9:.2f} m³")
    xs = xs_lancas()

    # tapar as 3 lanças antigas
    tapa = None
    for (x, y) in OLD_POS:
        t = cil(OLD_OD, OLD_ZTOP - OLD_ZBOT, x, y, OLD_ZBOT)
        tapa = t if tapa is None else tapa.fuse(t)

    # as novas lanças deslocam líquido (OD)
    od = None
    for x in xs:
        t = cil(LANCA_OD, Z_BICO_B - Z_DESCARGA, x, AER_Y, Z_DESCARGA)
        od = t if od is None else od.fuse(t)

    novos = [s.fuse(tapa).cut(od) if 15e9 < s.Volume() < 26e9 else s for s in solidos]

    # ejetor: 4 cabeças + header 8" + stub de entrada do xarope
    ej = None
    for x in xs:
        c = cabeca_ejetor(x)
        ej = c if ej is None else ej.fuse(c)
    hx0 = min(xs) - 175.0
    hL  = (max(xs) - min(xs)) + 350.0
    ej = ej.fuse(cil(HEADER_ID, hL, hx0, AER_Y, Z_HEADER, (1, 0, 0)))
    ej = ej.fuse(cil(HEADER_ID, XAROPE_STUB, hx0 - XAROPE_STUB, AER_Y, Z_HEADER, (1, 0, 0)))
    print(f"  ejetor construído: V = {ej.Volume()/1e6:.2f} L")

    comp = novos[0]
    for s in novos[1:] + [ej]:
        comp = comp.fuse(s)
    return comp.clean(), xs


if __name__ == "__main__":
    fl, xs = build()
    bb = fl.BoundingBox()
    print("="*74)
    print("  DOMÍNIO ACOPLADO COMPLETO — aerador + reator + ejetor")
    print("="*74)
    print(f"  4 lanças em x = {['%.0f' % x for x in xs]} · y = {AER_Y:.0f}")
    print(f"  raios ao eixo do aerador: {[round(abs(x-AER_X)) for x in xs]} mm  (raio = 1016)")
    print()
    print("  CAMINHO DO FLUIDO (de cima para baixo):")
    print(f"    entrada do XAROPE  Ø{HEADER_ID:.1f}  z = {Z_HEADER:.0f}   ⭐ BC de velocidade")
    print(f"    header 8\"                       z = {Z_HEADER:.0f}")
    print(f"    ramal 4\"           Ø{RAMAL_ID:.1f}  z = {Z_RAMAL_T:.0f} → {Z_CONTR_T:.0f}")
    print(f"    PORTA DE AR 1½\"    Ø{AR_ID:.1f}   z = {Z_AR:.0f}   ⭐ BC de ar (1 kgf/cm²)")
    print(f"    CONTRAÇÃO 4\"→2\"                 z = {Z_CONTR_T:.0f} → {Z_CONTR_B:.0f}  (3,80:1)")
    print(f"    BICO {N_FUROS}×Ø{D_FURO:.0f} PCD Ø{PCD:.0f}          z = {Z_CONTR_B:.0f} → {Z_BICO_B:.0f}")
    print(f"    lança 2½\"          Ø{LANCA_ID:.1f}   z = {Z_BICO_B:.0f} → {Z_DESCARGA:.0f}")
    print(f"    DESCARGA no aerador             z = {Z_DESCARGA:.0f}   ({AER_ZTOP-Z_DESCARGA:.0f} mm submersa)")
    print()
    print(f"  válido = {fl.isValid()} | volume = {fl.Volume()/1e9:.3f} m³")
    print(f"  bbox X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] Z[{bb.zmin:.0f},{bb.zmax:.0f}]")
    p = os.path.join(OUT, "ACOPLADO_aerador_reator_ejetor_fluido.step")
    cq.exporters.export(fl, p)
    print(f"\n  STEP -> {os.path.basename(p)} ({os.path.getsize(p)/1e6:.2f} MB)")
