"""Derivar a equação de velocidade de um mecanismo postulado.

Este é o núcleo do pacote e o exemplo mais curto: declare as etapas
elementares, escolha a etapa determinante, receba a lei em forma fechada.

    python examples/01_derivar_uma_lei.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from biokin.lhhw import derive_all, derive_rate_law
from biokin.mechanism import Mechanism, Step

# --------------------------------------------------------------------
# Mecanismo Eley-Rideal via metóxido, com inibição por glicerol.
# A reação é escrita genericamente: A + M <-> B + E, onde (A, B) será
# depois instanciado como (TG, DG), (DG, MG) e (MG, G).
# --------------------------------------------------------------------
mecanismo = Mechanism(
    name="ER-metóxido",
    family="ER-M",
    steps=(
        Step(
            "ads_M",
            {"M": 1, "*": 1},
            {"M*": 1},
            description="metanol adsorve no sítio básico formando metóxido",
        ),
        Step(
            "sr",
            {"M*": 1, "A": 1},
            {"B": 1, "E": 1, "*": 1},
            description="metóxido ataca o glicerídeo em solução",
        ),
        Step(
            "ads_G",
            {"G": 1, "*": 1},
            {"G*": 1},
            in_cycle=False,
            can_be_rds=False,
            description="glicerol compete pelos sítios sem reagir",
        ),
    ),
    overall={"A": -1, "M": -1, "B": 1, "E": 1},
)

# validate() confere que as etapas do ciclo somam a reação global —
# todos os intermediários de superfície e sítios devem se cancelar.
mecanismo.validate()
print(mecanismo.pretty())
print()

# --------------------------------------------------------------------
# Uma lei para cada escolha admissível de etapa determinante.
# --------------------------------------------------------------------
for lei in derive_all(mecanismo):
    print(f"── etapa determinante: {lei.rds_label}")
    print(f"   {lei.pretty()}")
    print(f"   ordem do denominador: {lei.denominator_exponent}")
    print(f"   parâmetros: {', '.join(lei.param_names)}")
    print()

# --------------------------------------------------------------------
# As coberturas também ficam disponíveis — úteis para discutir qual
# espécie domina a superfície em cada condição.
# --------------------------------------------------------------------
lei = derive_rate_law(mecanismo, 1)  # RDS = reação superficial
print("Coberturas fracionárias:")
for especie, expressao in sorted(lei.coverages.items()):
    print(f"   θ({especie:>3s}) = {expressao}")
print()
print("LaTeX da lei (para colar na dissertação):")
print(f"   {lei.latex()}")
