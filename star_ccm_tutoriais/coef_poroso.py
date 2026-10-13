"""
coef_poroso.py — coeficientes de resistência porosa no formato do STAR-CCM+.

O STAR modela a perda de carga num meio poroso por unidade de comprimento como

    Δp / L = P_i·|v|·v + P_v·v          (v = velocidade SUPERFICIAL, a do tubo vazio)

    P_i = Porous Inertial Resistance  [kg/m⁴]
    P_v = Porous Viscous Resistance   [kg/m³·s]

Dois jeitos de obter P_i e P_v:

1) A partir de pontos medidos ou de catálogo (Δp a várias velocidades, espessura L):
       python3 coef_poroso.py dados --L 0.15 --pontos 1.0:120 2.0:400 3.0:850
   Ajuste por mínimos quadrados de Δp/L = P_i·v² + P_v·v (sem termo constante).
   Com um único ponto, informar qual termo domina: --so-inercial ou --so-viscoso.

2) A partir da equação de Ergun (leito de partículas):
       python3 coef_poroso.py ergun --d 0.003 --eps 0.4 --rho 1.2 --mu 1.8e-5
       P_v = 150·μ·(1−ε)² / (ε³·d²)        P_i = 1,75·ρ·(1−ε) / (ε³·d)

Saída: P_i e P_v, Δp previsto em algumas velocidades e a velocidade em que os dois termos se igualam.
"""
import argparse
import sys


def ajuste(pontos, L, so=None):
    """Mínimos quadrados de y = a·v² + b·v, y = Δp/L, passando pela origem."""
    vs = [v for v, _ in pontos]
    ys = [dp / L for _, dp in pontos]
    if so == "inercial":
        a = sum(y * v * v for v, y in zip(vs, ys)) / sum(v ** 4 for v in vs)
        return a, 0.0
    if so == "viscoso":
        b = sum(y * v for v, y in zip(vs, ys)) / sum(v * v for v in vs)
        return 0.0, b
    if len(pontos) < 2:
        sys.exit("Com 1 ponto, use --so-inercial ou --so-viscoso.")
    s4 = sum(v ** 4 for v in vs); s3 = sum(v ** 3 for v in vs); s2 = sum(v * v for v in vs)
    t2 = sum(y * v * v for v, y in zip(vs, ys)); t1 = sum(y * v for v, y in zip(vs, ys))
    det = s4 * s2 - s3 * s3
    a = (t2 * s2 - t1 * s3) / det
    b = (s4 * t1 - s3 * t2) / det
    return a, b


def relatorio(Pi, Pv, L, pontos=None):
    print(f"\n  Porous Inertial Resistance  P_i = {Pi:12.4g} kg/m^4")
    print(f"  Porous Viscous Resistance   P_v = {Pv:12.4g} kg/m^3-s")
    if Pi > 0 and Pv > 0:
        print(f"  Termos iguais em v = P_v/P_i = {Pv/Pi:.3g} m/s "
              f"(abaixo: domina o viscoso; acima: o inercial)")
    if Pi < 0 or Pv < 0:
        print("  ⚠️ coeficiente negativo: os pontos não seguem a forma quadrática — "
              "rever os dados ou ajustar só um termo.")
    if L:
        vs = [v for v, _ in pontos] if pontos else [0.5, 1, 2, 5]
        print(f"\n  {'v [m/s]':>8} {'Δp previsto [Pa]':>17}" + (f" {'Δp dado [Pa]':>13}" if pontos else ""))
        for k, v in enumerate(vs):
            dp = (Pi * v * v + Pv * v) * L
            extra = f" {pontos[k][1]:13.1f}" if pontos else ""
            print(f"  {v:8.3g} {dp:17.1f}{extra}")
    print()


ap = argparse.ArgumentParser(description="Coeficientes porosos P_i, P_v para o STAR-CCM+")
sub = ap.add_subparsers(dest="modo", required=True)
d = sub.add_parser("dados", help="ajuste a pontos (v, Δp)")
d.add_argument("--L", type=float, required=True, help="espessura do meio poroso [m]")
d.add_argument("--pontos", nargs="+", required=True, help="pares v:Δp (m/s:Pa), velocidade superficial")
g = d.add_mutually_exclusive_group()
g.add_argument("--so-inercial", action="store_true")
g.add_argument("--so-viscoso", action="store_true")
e = sub.add_parser("ergun", help="leito de partículas (Ergun)")
e.add_argument("--d", type=float, required=True, help="diâmetro da partícula [m]")
e.add_argument("--eps", type=float, required=True, help="porosidade [-]")
e.add_argument("--rho", type=float, required=True, help="densidade do fluido [kg/m³]")
e.add_argument("--mu", type=float, required=True, help="viscosidade do fluido [Pa·s]")
e.add_argument("--L", type=float, help="espessura, para mostrar Δp [m]")
args = ap.parse_args()

if args.modo == "dados":
    pts = [tuple(float(x) for x in p.split(":")) for p in args.pontos]
    so = "inercial" if args.so_inercial else "viscoso" if args.so_viscoso else None
    Pi, Pv = ajuste(pts, args.L, so)
    relatorio(Pi, Pv, args.L, pts)
else:
    eps, dp_ = args.eps, args.d
    Pv = 150 * args.mu * (1 - eps) ** 2 / (eps ** 3 * dp_ ** 2)
    Pi = 1.75 * args.rho * (1 - eps) / (eps ** 3 * dp_)
    relatorio(Pi, Pv, args.L)
