"""Varredura completa sobre dados sintéticos de mecanismo conhecido.

Serve para (a) validar que o pipeline funciona e (b) dimensionar o
esforço experimental: mexa no ruído e no planejamento e veja a partir de
que ponto a varredura deixa de recuperar o mecanismo verdadeiro.

    python examples/02_varredura_sintetica.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from biokin.report import write_all_figures
from biokin.screening import ScreeningConfig, run_screening
from biokin.synthetic import TRUE_MODEL_ID, Condition, generate_dataset

# Constantes de equilíbrio conhecidas por via termodinâmica.
# Longe do equilíbrio elas não são identificáveis a partir de dados
# cinéticos — fixá-las é a decisão correta.
KEQ = {"Keq_1": 3.0, "Keq_2": 2.0, "Keq_3": 5.0}

tempos = np.array([0, 5, 10, 20, 30, 45, 60, 90, 120.0])

# Grade térmica mais corridas com produto na alimentação. As dopadas são
# o que quebra a colinearidade entre glicerol e éster.
condicoes = [
    Condition(f"B-T{T - 273.15:.0f}-R{r:.0f}", T, r, times_min=tempos)
    for T in (323.15, 333.15, 343.15)
    for r in (6.0, 9.0, 12.0)
]
condicoes += [
    Condition(f"B-T{T - 273.15:.0f}-dopG{g:g}", T, 9.0, C_G0=g, times_min=tempos)
    for T in (323.15, 333.15, 343.15)
    for g in (0.2, 0.45)
]
condicoes += [
    Condition(f"B-T{T - 273.15:.0f}-dopE{e:g}", T, 9.0, C_E0=e, times_min=tempos)
    for T in (323.15, 333.15, 343.15)
    for e in (0.6, 1.5)
]

dados = generate_dataset(conditions=condicoes, relative_noise=0.03, seed=11)
print(dados.summary())
print()

resultado = run_screening(
    dados,
    ScreeningConfig(fixed=KEQ, n_refine=5, n_starts_differential=8),
)

print()
print(resultado.report())

print()
print("=" * 78)
melhor = resultado.best
print(f"mecanismo verdadeiro : {TRUE_MODEL_ID}")
print(f"melhor candidato     : {melhor.model_id if melhor else '—'}")

caminhos = write_all_figures(resultado, "figuras")
print(f"\nfiguras em figuras/: {', '.join(p.name for p in caminhos)}")
