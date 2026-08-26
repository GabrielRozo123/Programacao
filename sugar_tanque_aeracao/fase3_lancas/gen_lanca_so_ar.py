"""
gen_lanca_so_ar.py — DOMÍNIO DE AR PURO de UMA lança perfurada (Fase 3 · Ito)

Responde a pergunta que a rodada EMP não conseguiu: **como o ar se distribui
entre os 48 furos**. Essa é uma questão hidráulica de gás, decidida dentro da
lança — o xarope entra apenas como contrapressão, que é conhecida.

Domínio = interior do tubo + os 48 túneis de furo. SEM xarope, SEM EMP, SEM
bolha. Monofásico compressível, steady.

Por que UMA lança basta: as três são idênticas e estão na mesma cota, então a
contrapressão hidrostática é a mesma. A distribuição entre lanças é trivial;
a distribuição entre FUROS é a pergunta.

CONTORNOS (nomear no STAR pela geometria):
  · disco Ø62,68 em z = 1,220     -> Mass Flow Inlet (7,029e-3 kg/s) ou Stagnation
  · cilindro interno R 31,34      -> Wall
  · disco no fundo (tampa)        -> Wall
  · 48 cilindros R 0,5            -> Wall
  · 48 discos em R = 36,5         -> PRESSURE OUTLET, pressão por field function:
                                        13243.5 * (1.220 - $$Position[2])
    (é a hidrostática do xarope na cota de cada furo: 85 246 Pa no anel
     inferior contra 85 048 no superior — a diferença de 198,7 Pa é exatamente
     o que o critério de uniformidade disputa)

⚠️ Reference Density = densidade do AR (não 1350), porque aqui não há xarope.

Saída: lanca_so_ar_dominio.step
Convenção: mm, mesmo sistema do STEP do cliente.
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))

OD, ID = 73.0, 62.68
PAREDE = (OD - ID) / 2
D_FURO, N_ANEL = 1.0, 24
T_TAMPA = 6.0
DEFASAGEM = math.pi / N_ANEL

Z_DESCARGA, Z_TOPO = -5246.5, 1220.0
Z_TAMPA = Z_DESCARGA + T_TAMPA            # -5240,5 — topo da tampa cega
Z_ANEL1, Z_ANEL2 = Z_DESCARGA + 30.0, Z_DESCARGA + 45.0

X, Y = 200.0, -745.0                       # lança 1; as outras são idênticas


def build():
    print("=" * 74)
    print("  DOMÍNIO DE AR PURO — uma lança perfurada")
    print("=" * 74)

    interior = cq.Solid.makeCylinder(ID / 2, Z_TOPO - Z_TAMPA,
                                     cq.Vector(X, Y, Z_TAMPA), cq.Vector(0, 0, 1))
    v_int = interior.Volume()

    tuneis = []
    for z, fase in ((Z_ANEL1, 0.0), (Z_ANEL2, DEFASAGEM)):
        for k in range(N_ANEL):
            a = fase + 2 * math.pi * k / N_ANEL
            d = cq.Vector(math.cos(a), math.sin(a), 0)
            # começa um pouco dentro da parede interna para garantir a fusão
            p0 = cq.Vector(X + (ID / 2 - 0.5) * math.cos(a),
                           Y + (ID / 2 - 0.5) * math.sin(a), z)
            tuneis.append(cq.Solid.makeCylinder(D_FURO / 2, PAREDE + 0.5, p0, d))

    dom = interior
    for t in tuneis:
        dom = dom.fuse(t)
    dom = dom.clean()

    v = dom.Volume()
    v_tun = 2 * N_ANEL * math.pi / 4 * D_FURO**2 * PAREDE
    print(f"\n  interior do tubo  = {v_int/1e3:9.2f} cm³")
    print(f"  48 túneis         = {v_tun/1e3:9.4f} cm³")
    print(f"  volume do domínio = {v/1e3:9.2f} cm³")
    print(f"  faces             = {len(dom.Faces())}"
          f"   (esperado 4 + 48 laterais + 48 discos de saída = 100)")

    print(f"\n  CONTRAPRESSÃO nos furos (hidrostática do xarope):")
    for z, lab in ((Z_ANEL1, "anel inferior"), (Z_ANEL2, "anel superior")):
        p = 1350 * 9.81 * (Z_TOPO - z) / 1000
        print(f"    {lab}: z = {z:.1f} mm -> {p:8.0f} Pa")
    dp = 1350 * 9.81 * (Z_ANEL2 - Z_ANEL1) / 1000
    print(f"    diferença = {dp:.1f} Pa   <- o que o critério de uniformidade disputa")

    print(f"\n  MALHA sugerida — o tubo e longo e o escoamento nele e lento (1,2 m/s):")
    v_banda = math.pi/4*ID**2*100
    print(f"    base 10 mm no tubo inteiro          : {v/1000:9.0f} celulas")
    print(f"    1 mm nos ultimos 100 mm (banda)     : {v_banda/1:9.0f} celulas")
    print(f"    surface size 0,15 mm nos 48 furos   : {48*5e3:9.0f} celulas")
    print(f"    TOTAL                               : {v/1000 + v_banda + 48*5e3:9.0f} celulas")

    out = os.path.join(OUT, "lanca_so_ar_dominio.step")
    cq.exporters.export(dom, out)
    print(f"\n  → {os.path.basename(out)}")
    return dom


if __name__ == "__main__":
    build()
