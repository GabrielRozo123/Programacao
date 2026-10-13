"""
props_agua_saturada.py — propriedades de água/vapor saturados prontas para o STAR-CCM+ (Eulerian, ebulição).

No tutorial "Eulerian: Conjugate Heat Transfer Wall Boiling" as duas fases são definidas com
propriedades CONSTANTES na saturação, e o calor latente entra por um truque:

    Heat of Formation (líquido) = h_l(sat)      Heat of Formation (vapor) = h_v(sat)
    Standard State Temperature  = Tsat          (as duas fases)
    -> o STAR obtém h_fg = h_v - h_l da diferença dos "calores de formação"

Os valores do tutorial (71,7 bar) são as entalpias IAPWS de saturação — este script reproduz
1 276 100 / 2 770 300 J/kg com erro < 0,02 %. Use-o para gerar a tabela em qualquer pressão.

Com --tin (líquido entrando SUB-RESFRIADO) aplica também a receita do tutorial "Eulerian: Wall
Boiling" para manter o balanço de energia com propriedades constantes:

    cp_L efetivo = (h_l,sat - h_l,in) / (Tsat - T_in)        (cp "secante")
    rho, mu, k do líquido na temperatura média (T_in + Tsat)/2
    velocidade de entrada = G / rho_L                         (G = fluxo mássico, --G)

Com o cp secante, h(T_in) = h_l,sat - cp·(Tsat - T_in) sai EXATO nas duas pontas.

Uso:   python3 props_agua_saturada.py 30 40                    (pressões em bar absolutos)
       python3 props_agua_saturada.py 45 --tin 470.63 --G 900  (T_in em K, G em kg/m²·s)
Requer: pip install CoolProp
"""
import argparse
from CoolProp.CoolProp import PropsSI

ap = argparse.ArgumentParser(description="Propriedades de saturação da água no formato do STAR-CCM+")
ap.add_argument("pressoes", nargs="*", type=float, default=[71.7], help="pressões em bar absolutos")
ap.add_argument("--tin", type=float, help="temperatura de entrada do líquido sub-resfriado [K]")
ap.add_argument("--G", type=float, help="fluxo mássico de entrada [kg/m²·s] (requer --tin)")
args = ap.parse_args()

for pbar in args.pressoes:
    p = pbar * 1e5
    L = lambda k: PropsSI(k, "P", p, "Q", 0, "Water")
    V = lambda k: PropsSI(k, "P", p, "Q", 1, "Water")
    T = L("T")
    print("=" * 66)
    print(f" ÁGUA SATURADA a {pbar:.2f} bar a  ->  Tsat = {T:.2f} K = {T-273.15:.2f} °C")
    print("=" * 66)
    print(f" {'propriedade (Material Properties)':34s} {'Liquid H2O (l)':>14s} {'Vapor H2O (g)':>14s}")
    linhas = [
        ("Density [kg/m^3]",                 L("D"),  V("D"),  "{:14.2f}"),
        ("Dynamic Viscosity [Pa-s]",         L("V"),  V("V"),  "{:14.4e}"),
        ("Heat of Formation [J/kg]",         L("H"),  V("H"),  "{:14.0f}"),
        ("Specific Heat [J/kg-K]",           L("C"),  V("C"),  "{:14.0f}"),
        ("Standard State Temperature [K]",   T,       T,       "{:14.2f}"),
        ("Thermal Conductivity [W/m-K]",     L("L"),  V("L"),  "{:14.4f}"),
    ]
    for nome, a, b, f in linhas:
        print(f" {nome:34s} {f.format(a)} {f.format(b)}")
    print(f"\n Multiphase Material > Boiling Temperature = {T:.2f} K")
    print(f" Multiphase Material > Surface Tension     = {L('I'):.5f} N/m")
    print(f" (calor latente resultante h_fg = {(V('H')-L('H'))/1e3:.1f} kJ/kg)\n")

    if args.tin is None:
        continue
    tin = args.tin
    if tin >= T:
        print(f" --tin {tin:.2f} K não é sub-resfriado a {pbar:.2f} bar (Tsat = {T:.2f} K)\n")
        continue
    h_in = PropsSI("H", "T", tin, "P", p, "Water")
    cp_sec = (L("H") - h_in) / (T - tin)
    tm = 0.5 * (tin + T)
    M = lambda k: PropsSI(k, "T", tm, "P", p, "Water")
    hfg = V("H") - L("H")
    print(f" LÍQUIDO SUB-RESFRIADO: T_in = {tin:.2f} K, sub-resfriamento {T-tin:.2f} K "
          f"(receita do tutorial Wall Boiling)")
    print(f"   Specific Heat (cp secante)       {cp_sec:14.1f} J/kg-K   (cp local: entrada "
          f"{PropsSI('C','T',tin,'P',p,'Water'):.0f}, saturação {L('C'):.0f})")
    print(f"   T média                          {tm:14.2f} K")
    print(f"   Density na T média               {M('D'):14.2f} kg/m^3  (na entrada: "
          f"{PropsSI('D','T',tin,'P',p,'Water'):.2f})")
    print(f"   Dynamic Viscosity na T média     {M('V'):14.4e} Pa-s")
    print(f"   Thermal Conductivity na T média  {M('L'):14.4f} W/m-K")
    print(f"   Título de entrada cp·(T_in-Tsat)/h_fg = {cp_sec*(tin-T)/hfg:.4f} (exato pela entalpia: "
          f"{(h_in-L('H'))/hfg:.4f})")
    if args.G:
        print(f"   Velocidade de entrada G/rho      {args.G/M('D'):14.4f} m/s  (G = {args.G:g} kg/m²·s)")
    print()
