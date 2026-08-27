"""Ponto de partida para os seus dados.

Passos:

1. Gere o arquivo modelo (abaixo) e preencha com os seus pontos.
2. Ajuste a geometria do monolito, se houver corridas em fluxo.
3. Rode. Comece pelo diagnóstico de transporte: se ele reprovar, o resto
   do relatório descreve cinética aparente, não intrínseca.

    python examples/03_dados_proprios.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pathlib import Path

from biokin.data import read_csv, write_csv
from biokin.reactor import MonolithOperation
from biokin.screening import ScreeningConfig, run_screening
from biokin.synthetic import generate_dataset
from biokin.transport import FluidProperties, MonolithGeometry

ARQUIVO = Path("meus_dados.csv")

# --------------------------------------------------------------------
# 1. Modelo de arquivo, se ainda não existir
# --------------------------------------------------------------------
if not ARQUIVO.exists():
    write_csv(generate_dataset(), ARQUIVO)
    print(f"Criado {ARQUIVO} com dados de exemplo.")
    print("Substitua pelas suas medidas e rode de novo.")
    print()
    print("Colunas: células vazias significam 'não medido' e simplesmente")
    print("não entram nos resíduos. A composição de alimentação vai nas")
    print("colunas C0_*, que você conhece mesmo sem titular o metanol.")
    raise SystemExit(0)

# --------------------------------------------------------------------
# 2. Geometria do seu monolito
# --------------------------------------------------------------------
geometria = MonolithGeometry(
    cell_density_cpsi=400.0,       # densidade de células
    wall_thickness_m=1.5e-4,       # espessura da parede do substrato
    washcoat_thickness_m=3.0e-5,   # espessura do washcoat  <- meça por MEV
    length_m=0.20,                 # comprimento do monolito
    washcoat_porosity=0.45,
    washcoat_tortuosity=3.5,
    washcoat_density_kg_m3=1300.0,
)
fluido = FluidProperties(
    density_kg_m3=820.0,
    viscosity_Pa_s=6.0e-4,
    diffusivity_m2_s=7.5e-10,      # ou use wilke_chang_diffusivity()
)

# Uma entrada por corrida em monolito, com a velocidade superficial
# correspondente. Corridas em batelada não precisam de nada aqui.
operacoes = {
    # "M-T60-u5": MonolithOperation(velocity_m_s=0.005, geometry=geometria, fluid=fluido),
}

dados = read_csv(ARQUIVO, operations=operacoes)
print(dados.summary())

# --------------------------------------------------------------------
# 3. Varredura
# --------------------------------------------------------------------
config = ScreeningConfig(
    # Fixe as constantes de equilíbrio se as conhecer. Longe do
    # equilíbrio elas não são identificáveis a partir de dados cinéticos.
    fixed={"Keq_1": 3.0, "Keq_2": 2.0, "Keq_3": 5.0},
    # 'ideal' pressupõe ausência de gradientes — confira no relatório.
    # Se os critérios reprovarem, troque para 'full'.
    mode="ideal",
    n_refine=5,
)

resultado = run_screening(dados, config)
print()
print(resultado.report())

Path("relatorio.txt").write_text(resultado.report(), encoding="utf-8")
print("\nRelatório gravado em relatorio.txt")
