"""
gen_refino_3lancas_furadas.py — CILINDROS DE REFINO para o aerador de 3 lanças perfuradas

Dois níveis por lança, porque a razão entre a malha base (50 mm) e o furo (0,25 mm)
é de 200× — o trimmer precisa de degraus, senão a transição estoura em células.

  REFINO_FURO   Ø120 × 75 mm   → 2,0 mm    envolve a banda perfurada (2 anéis)
  REFINO_PLUMA  Ø300 × 1000 mm → 12,5 mm   near-field da pluma acima da descarga

⚠️ O refino FINO (0,25 mm) NÃO sai daqui. Ele vem de SURFACE SIZE customizado no
   contorno `lanca.furos`. São 144 furos: controle volumétrico por furo é inviável
   de montar e desnecessário — o trimmer refina sozinho a partir da superfície.

Sólidos gerados: 3 lanças × 2 níveis = 6 cilindros, num único STEP.
Convenção: mm, mesmo sistema do STEP do cliente.
"""
import cadquery as cq
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))
AER_X, AER_Y = 200.0, -440.0
R_LANCA, Z_DESCARGA = 305.0, -5246.5
ANGULOS = [-90.0, 29.9, 150.1]

# (nome, diâmetro, z inicial, z final, tamanho alvo de célula)
# UM cilindro por lança. O segundo nível (pluma Ø300×1000) foi descartado:
# Re do jato = rho_x·v·d/mu = 1350·98,2·0,001/6,5 = 20 — o jato é VISCOSO e morre
# em poucos diâmetros. Não há near-field distante para resolver neste xarope.
NIVEIS = [
    ("REFINO_LANCA", 150.0, Z_DESCARGA - 18.5, Z_DESCARGA + 131.5, 2.0),
]


def cil(d, z0, z1, x, y):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


if __name__ == "__main__":
    print("=" * 76)
    print("  CILINDROS DE REFINO — 3 lanças perfuradas")
    print("=" * 76)

    pos = [(AER_X + R_LANCA * math.cos(math.radians(a)),
            AER_Y + R_LANCA * math.sin(math.radians(a))) for a in ANGULOS]

    solidos, total = [], 0.0
    print(f"\n  {'nível':<14}{'Ø':>7}{'z inicial':>12}{'z final':>11}{'célula':>9}"
          f"{'volume':>12}{'células/lança':>15}")
    print("  " + "-" * 78)
    for nome, d, z0, z1, h in NIVEIS:
        V = math.pi / 4 * d**2 * (z1 - z0)
        n = V / h**3
        total += 3 * n
        print(f"  {nome:<14}{d:>7.0f}{z0:>12.1f}{z1:>11.1f}{h:>8.2f} {V/1e3:>10.1f} cm³"
              f"{n:>14.2e}")
        for x, y in pos:
            solidos.append(cil(d, z0, z1, x, y))

    print("  " + "-" * 78)
    print(f"  subtotal dos controles volumétricos (3 lanças): {total:.2e} células")

    # ── estimativa do resto da malha ──────────────────────────────────────
    V_TANQUE = 20.27e9                       # mm³
    base = 50.0
    n_base = V_TANQUE / base**3
    V_INT = 3 * math.pi / 4 * 62.68**2 * (1220 + 5246.5)
    n_int = V_INT / 12.0**3
    n_furos = 144 * 5e3                      # gerado pelo surface size, ~5e3 por furo
    print(f"\n  resto da malha:")
    print(f"    base {base:.0f} mm no tanque de {V_TANQUE/1e9:.2f} m³ : {n_base:.2e}")
    print(f"    interior das 3 lanças a 12 mm         : {n_int:.2e}")
    print(f"    entorno dos 144 furos (surface size)  : {n_furos:.2e}")
    soma = total + n_base + n_int + n_furos
    print(f"\n  TOTAL estimado ≈ {soma:.2e} células  (+ transições ≈ {soma*1.5:.2e})")

    comp = cq.Compound.makeCompound(solidos)
    out = os.path.join(OUT, "refino_3lancas_furadas.step")
    cq.exporters.export(cq.Workplane(obj=comp), out)
    print(f"\n  → {os.path.basename(out)}   ({len(solidos)} cilindros)")

    print("\n  COORDENADAS para montar direto no STAR (Part > Cylinder):")
    print(f"  {'lança':<8}{'nível':<14}{'Start X':>10}{'Start Y':>10}{'Start Z':>11}"
          f"{'End X':>10}{'End Y':>10}{'End Z':>11}{'Radius':>9}")
    print("  " + "-" * 83)
    for i, (x, y) in enumerate(pos, 1):
        for nome, d, z0, z1, h in NIVEIS:
            print(f"  {i:<8}{nome:<14}{x:>10.1f}{y:>10.1f}{z0:>11.1f}"
                  f"{x:>10.1f}{y:>10.1f}{z1:>11.1f}{d/2:>9.1f}")
    print("\n  ⚠️ End X = Start X e End Y = Start Y — senão o cilindro sai inclinado.")
