"""Os gradientes de transporte comprometem os seus dados?

Rode isto **antes** de qualquer análise cinética. Se os critérios
reprovarem, a cinética observada está deformada de modo sistemático — a
ordem aparente e a energia de ativação caem para cerca da metade — e uma
discriminação de mecanismos sobre esses dados encontra um vencedor com
ótima estatística e mecanismo errado.

    python examples/04_transporte.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from biokin.transport import (
    FluidProperties,
    MonolithGeometry,
    diagnose,
    effective_diffusivity,
    wilke_chang_diffusivity,
)

# --------------------------------------------------------------------
# A sua geometria e as suas condições
# --------------------------------------------------------------------
T = 333.15            # temperatura de operação [K]
VISCOSIDADE = 6.0e-4  # viscosidade do meio [Pa·s]
C_TG = 0.9            # concentração de triglicerídeo no seio [mol/L]
R_OBS = 2.0e-3        # velocidade observada [mol/(g_cat·min)]

fluido = FluidProperties(
    density_kg_m3=820.0,
    viscosity_Pa_s=VISCOSIDADE,
    diffusivity_m2_s=wilke_chang_diffusivity(T, VISCOSIDADE),
)
print(f"difusividade estimada (Wilke-Chang): {fluido.diffusivity_m2_s:.3e} m²/s")
print()

# --------------------------------------------------------------------
# Varredura: espessura de washcoat contra velocidade superficial
# --------------------------------------------------------------------
espessuras_um = (10.0, 20.0, 30.0, 50.0, 100.0)
velocidades = (0.002, 0.005, 0.010, 0.020)

print(f"Weisz-Prater (limite 0,15) para r_obs = {R_OBS:g} mol/(g·min)")
print(f"{'washcoat':>10s} | " + " ".join(f"u={u * 1e3:>5.0f} mm/s" for u in velocidades))
print("-" * 62)
for esp in espessuras_um:
    geom = MonolithGeometry(washcoat_thickness_m=esp * 1e-6, length_m=0.20)
    linha = []
    for u in velocidades:
        d = diagnose(lambda c: R_OBS * c / C_TG, C_TG, geom, fluido, u)
        marca = " " if d.internal_ok else "!"
        linha.append(f"{d.weisz_prater:>10.3f}{marca}")
    print(f"{esp:>7.0f} µm | " + " ".join(linha))

print()
print("O critério interno depende quase só da espessura do washcoat:")
print("a velocidade superficial afeta o filme externo, não a difusão")
print("dentro do poro. Reduzir a espessura é o que resolve.")
print()

# --------------------------------------------------------------------
# Detalhe de uma condição
# --------------------------------------------------------------------
geom = MonolithGeometry(washcoat_thickness_m=3.0e-5, length_m=0.20)
d = diagnose(lambda c: R_OBS * c / C_TG, C_TG, geom, fluido, 0.005)
print(f"Condição de referência (washcoat 30 µm, u = 5 mm/s):")
print(d.report())
print()
print(f"  D_eff no washcoat  {effective_diffusivity(geom, fluido):.3e} m²/s")
print(f"  catalisador        {geom.catalyst_density_g_L:.1f} g/L de reator")
print(f"  área específica    {geom.specific_surface_m2_m3:.0f} m²/m³")
