"""Validação do modelo de capilar (HEM) contra os dados experimentais de Li, Lin & Chen (1990).

Li, R.Y., Lin, S., Chen, Z.H. (1990). Numerical modeling of thermodynamic non-equilibrium flow of
refrigerant through capillary tubes. ASHRAE Trans. 96(1):542-549; e Metastable flow of R12 through
capillary tubes, Int. J. Refrig. 13(3):181-186. Tubo de 1,5 m, D = 0,66 mm, e/D = 0,003, R12.
Condições dos casos conforme reproduzidas por Wongwises et al. (2002), ScienceAsia 28:71-76, Tab. 1.

Uso:  python validacao/validacao_capilar_li1990.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from predimref.capilar import ParametrosCapilar, comprimento_capilar, vazao_capilar  # noqa: E402
from predimref.propriedades import Fluido  # noqa: E402

CASOS = [  # (T_in °C, P_in Pa, vazão medida kg/s)
    (31.40, 9.67e5, 1.13e-3),
    (23.40, 7.17e5, 0.844e-3),
]


def main():
    fl = Fluido("R12")
    print(f"{'caso':5s} {'viscosidade':10s} {'ṁ exp [g/s]':>12s} {'ṁ HEM [g/s]':>12s} {'erro':>7s} "
          f"{'L(ṁ exp) [m]':>13s} {'blocado':>8s}")
    for i, (Ti, Pi, m_exp) in enumerate(CASOS, 1):
        h = fl.estado_PT(Pi, Ti + 273.15).h
        for visc in ("mcadams", "cicchitti", "dukler"):
            p = ParametrosCapilar(rugosidade_m=0.003 * 0.66e-3, modelo_viscosidade=visc)
            m = vazao_capilar(fl, 0.66e-3, 1.5, Pi, h, 1.5e5, p)
            r = comprimento_capilar(fl, m_exp, 0.66e-3, Pi, h, 1.5e5, p)
            print(f"{i:<5d} {visc:10s} {m_exp * 1e3:12.3f} {m * 1e3:12.3f} {m / m_exp - 1:+7.1%} "
                  f"{r.L:13.3f} {str(r.blocado):>8s}")
    print("\nO HEM despreza o atraso de vaporização (líquido metaestável), por isso tende a subestimar")
    print("levemente a vazão para um comprimento dado (ou o comprimento para uma vazão dada).")


if __name__ == "__main__":
    main()
