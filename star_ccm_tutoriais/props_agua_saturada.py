"""
props_agua_saturada.py — propriedades de água/vapor saturados prontas para o STAR-CCM+ (Eulerian, ebulição).

No tutorial "Eulerian: Conjugate Heat Transfer Wall Boiling" as duas fases são definidas com
propriedades CONSTANTES na saturação, e o calor latente entra por um truque:

    Heat of Formation (líquido) = h_l(sat)      Heat of Formation (vapor) = h_v(sat)
    Standard State Temperature  = Tsat          (as duas fases)
    -> o STAR obtém h_fg = h_v - h_l da diferença dos "calores de formação"

Os valores do tutorial (71,7 bar) são as entalpias IAPWS de saturação — este script reproduz
1 276 100 / 2 770 300 J/kg com erro < 0,02 %. Use-o para gerar a tabela em qualquer pressão.

Uso:   python3 props_agua_saturada.py 30 40          (pressões em bar absolutos)
Requer: pip install CoolProp
"""
import sys
from CoolProp.CoolProp import PropsSI

pressoes = [float(a) for a in sys.argv[1:]] or [71.7]

for pbar in pressoes:
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
