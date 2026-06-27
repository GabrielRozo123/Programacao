#!/usr/bin/env python3
"""
Tanque criogênico LN2 — Caso de validação Seo & Jeong (2010)
============================================================
Geometria do domínio fluido para estudo CFD de auto-pressurização / BOG
(Boil-Off Gas) em tanque de nitrogênio líquido. Caso de validação barato
para o estudo de segurança BOG/rollover (ver revisao_bog_rollover.md).

Referência geométrica (Seo & Jeong, 2010, Cryogenics):
  - Cilindro vertical de aço inox 304
  - Diâmetro interno = 201 mm
  - Altura interna   = 213 mm
  - Volume interno   ≈ 6.75 L

Estratégia de malha (ver notas_tutorial_vof_boiling.md):
  - O caso CFD será rodado em 2D-AXISSIMÉTRICO (mais barato que 3D).
  - Este script gera o SÓLIDO 3D completo (revolve) como referência/CAD;
    o domínio 2D axissimétrico (meio-perfil) também é exportado para
    importação direta como geometria 2D no Star-CCM+.

Workflow CFD pretendido (adaptado do tutorial VOF: Boiling):
  - VOF, Implicit Unsteady, Gravity, Segregated Multiphase Temperature
  - Fases: N2 líquido + N2 gasoso (banco Standard)
  - Phase interaction: Schrage Boiling/Condensation — NÃO Rohsenow, NÃO Evap/Cond
    (Rohsenow = wall boiling; Evap/Cond = multicomponente; Schrage = interfacial
     cinético single-component, correto p/ N2 puro em auto-pressurização)
  - Paredes fechadas com heat flux (heat leak); validar P(t) vs Seo & Jeong
"""

import cadquery as cq
from cadquery import exporters
import math
import os

# ================================================================
# PARÂMETROS GEOMÉTRICOS (mm)
# ================================================================
D_INNER   = 201.0          # diâmetro interno [mm]
R_INNER   = D_INNER / 2.0
H_INNER   = 213.0          # altura interna [mm]

# Nível de líquido inicial (fração de enchimento).
# Seo & Jeong testam vários; fill < 35% dá subida acentuada de pressão.
FILL_FRAC = 0.80           # 80% líquido / 20% ullage (ajustável no caso CFD)
H_LIQUID  = FILL_FRAC * H_INNER

OUTPUT_DIR = "/home/user/Programacao/processos_seguranca/bog_rollover"

# ================================================================
# VERIFICAÇÃO DE VOLUME
# ================================================================
V_internal = math.pi * R_INNER**2 * H_INNER / 1e6   # litros (mm3 -> L)
print(f"  Diâmetro interno : {D_INNER:.0f} mm")
print(f"  Altura interna   : {H_INNER:.0f} mm")
print(f"  Volume interno   : {V_internal:.2f} L  (ref. Seo & Jeong: 6.75 L)")
print(f"  Nível de líquido : {H_LIQUID:.0f} mm  ({FILL_FRAC*100:.0f}% fill)")

# ================================================================
# SÓLIDO 3D (referência CAD) — cilindro vertical
# ================================================================
print("\nConstruindo domínio fluido 3D (referência)...")
tank_3d = (
    cq.Workplane("XY")
    .circle(R_INNER)
    .extrude(H_INNER)
)
ok3d = tank_3d.val().isValid()
vol3d = tank_3d.val().Volume() / 1e6
print(f"  OCCT validity 3D : {'VALID' if ok3d else 'INVALID'}")
print(f"  Volume OCCT 3D   : {vol3d:.2f} L")
assert ok3d
assert abs(vol3d - V_internal) / V_internal < 0.01

path_3d = os.path.join(OUTPUT_DIR, "ln2_tank_3d.step")
exporters.export(tank_3d, path_3d)
print(f"  Exportado: ln2_tank_3d.step ({os.path.getsize(path_3d)/1024:.1f} KB)")

# ================================================================
# PERFIL 2D-AXISSIMÉTRICO (meio-perfil no plano X-Y, eixo em X=0)
# ================================================================
# Star-CCM+ 2D axissimétrico: malha no plano X-Y, eixo de rotação = eixo Y.
# Retângulo: x de 0 (eixo) a R_INNER; y de 0 (fundo) a H_INNER (topo).
print("\nConstruindo perfil 2D-axissimétrico...")
profile_2d = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .lineTo(R_INNER, 0)        # fundo
    .lineTo(R_INNER, H_INNER)  # parede lateral
    .lineTo(0, H_INNER)        # topo
    .close()                   # eixo de simetria (x=0)
)
path_2d = os.path.join(OUTPUT_DIR, "ln2_tank_profile_2d.step")
exporters.export(profile_2d, path_2d)
print(f"  Exportado: ln2_tank_profile_2d.step ({os.path.getsize(path_2d)/1024:.1f} KB)")

# ================================================================
# VALORES DE REFERÊNCIA PARA O SETUP CFD
# ================================================================
# Propriedades aproximadas LN2 saturado a 1 atm (~77.4 K):
RHO_LIQ = 807.0     # kg/m3
RHO_VAP = 4.6       # kg/m3
T_SAT   = 77.4      # K @ 1 atm
H_LV    = 199.0e3   # J/kg (calor latente de vaporização)

print(f"""
================================================================
 REFERÊNCIA PARA SETUP CFD (LN2 @ ~77.4 K, 1 atm)
================================================================
  Geometria        : cilindro 201 mm (D) x 213 mm (H), {V_internal:.2f} L
  Fill inicial     : {FILL_FRAC*100:.0f}%  ->  nível de líquido y = {H_LIQUID:.0f} mm
  rho_liquido      : {RHO_LIQ:.1f} kg/m3
  rho_vapor        : {RHO_VAP:.1f} kg/m3
  T_saturacao      : {T_SAT:.1f} K
  Calor latente    : {H_LV/1e3:.0f} kJ/kg

  PROXIMOS PASSOS NO STAR-CCM+:
   1. Importar ln2_tank_profile_2d.step -> Convert to 2D (axissimétrico)
   2. Physics: VOF, Implicit Unsteady, Gravity, Seg. Multiphase Temperature
   3. Fases: N2 (Liquid) + N2 (Gas) do banco Standard
   4. Phase Interaction: Schrage Boiling/Condensation  [NAO Rohsenow/Evap-Cond]
   5. Initial: VF estratificada (liquido ate y={H_LIQUID:.0f} mm, vapor acima)
   6. BCs: paredes fechadas com HEAT FLUX (heat leak Seo & Jeong)
   7. Monitor: Pressao do ullage P(t) + T(z)  ->  validar vs Seo & Jeong
================================================================
""")
