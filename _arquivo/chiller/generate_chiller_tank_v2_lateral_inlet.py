#!/usr/bin/env python3
"""
GreyBeer Chiller Tank – Fluid Domain Geometry for Star-CCM+  [v2 — lateral inlet]
============================================================
Tanque de solução hidroalcóolica (70%m/m água + 30%m/m etanol)
resfriado por chiller externo. Estudo de estratificação térmica transiente.

Geometria (domínio fluido only — paredes excluídas):
  - Cilindro vertical com fundo cônico e topo plano
  - Dois bocais: inlet (do chiller, -5°C) na PAREDE LATERAL, z=2200mm, jato horizontal
                 outlet (para o chiller) no ápice do cone de fundo

Coord system: eixo Z vertical, origem no ápice do cone (ponto mais baixo do fluido)

Dimensões (as-built, extraídas do STEP GreyBeer_20400100TK):
  Scale factor STEP/DWG: ×10 — valores abaixo são reais em mm

ALTERAÇÃO v2: inlet movido do teto (z=5500mm) para parede lateral (z=2200mm = sensor_alto)
  Face inlet no Star-CCM+: face circular plana em X = R_SHELL + L_INLET = 2305mm do eixo
  BC inlet  → Mass Flow Inlet: ṁ = 3.109 kg/s, T = 268.15 K (-5°C)
  BC outlet → Pressure Outlet: 0 Pa gauge
"""

import cadquery as cq
from cadquery import exporters
import math, os

# ================================================================
# PARÂMETROS GEOMÉTRICOS (mm — escala real)
# ================================================================
D_SHELL      = 4210.0    # diâmetro interno do casco [mm] (medido DWG viewer: 42.088/10)
R_SHELL      = D_SHELL / 2

H_CONE       = 780.0     # altura do cone de fundo [mm]
H_CYLINDER   = 4720.0    # altura da seção cilíndrica [mm]
H_TOTAL      = H_CONE + H_CYLINDER   # altura total do domínio fluido

# Ângulo semi-vertical do cone
CONE_HALF_ANGLE = math.degrees(math.atan(R_SHELL / H_CONE))
print(f"  Ângulo semi-vertical do cone: {CONE_HALF_ANGLE:.1f}°")

# Bocal de SAÍDA — ápice do cone (fundo), drenagem → chiller suction
D_OUTLET     = 150.0     # DN150 estimado
L_OUTLET     = 200.0     # comprimento do stub [mm]

# Bocal de ENTRADA — PAREDE LATERAL, z=sensor_alto (cliente confirmou posição)
D_INLET      = 150.0     # DN150
L_INLET      = 200.0     # comprimento do stub [mm]
Z_INLET_H    = 2200.0    # altura do bocal a partir do ápice do cone [mm] (sensor_alto)

OUTPUT_DIR   = "/home/user/Programacao/_arquivo/chiller"

# ================================================================
# VOLUME TOTAL (verificação)
# ================================================================
V_cyl  = math.pi * R_SHELL**2 * H_CYLINDER
V_cone = math.pi * R_SHELL**2 * H_CONE / 3
V_tot  = (V_cyl + V_cone) / 1e9   # litros (mm³ → L: ÷1e6; → m³: ÷1e9)
print(f"  Volume cilindro : {V_cyl/1e6:.0f} L")
print(f"  Volume cone     : {V_cone/1e6:.0f} L")
print(f"  Volume total    : {V_tot*1000:.0f} L = {V_tot:.2f} m³")

# ================================================================
# BUILD GEOMETRY
# ================================================================
print("\nConstruindo domínio fluido...")

# --- Perfil meridional completo (revolve) -----------------------
# Coordenadas no plano XZ (X=raio, Z=altura), revolve em torno de Z
# Ápice do cone em (0,0), sobe pelo cone, percorre o casco, fecha pelo topo
tank_fluid = (
    cq.Workplane("XZ")
    .moveTo(0, 0)                            # ápice do cone
    .lineTo(R_SHELL, H_CONE)                 # borda da base do cone
    .lineTo(R_SHELL, H_CONE + H_CYLINDER)    # topo do casco
    .lineTo(0,       H_CONE + H_CYLINDER)    # centro do topo
    .close()                                 # retorna ao ápice
    .revolve(360, (0, 0, 0), (0, 1, 0))      # gira em torno do eixo local Y = global Z
)
vol_check = tank_fluid.val().Volume()
print(f"  Volume OCCT: {vol_check/1e6:.0f} L  (esperado: {(V_cyl+V_cone)/1e6:.0f} L)")
assert abs(vol_check - V_cyl - V_cone) / (V_cyl + V_cone) < 0.01, "Volume check failed!"

# --- Bocal de SAÍDA (outlet) — ápice do cone, direção -Z --------
outlet_stub = (cq.Workplane("XY")
               .circle(D_OUTLET / 2)
               .extrude(L_OUTLET, both=True))
tank_fluid = tank_fluid.union(outlet_stub)

# --- Bocal de ENTRADA (inlet) — PAREDE LATERAL, jato horizontal em +X
# Workplane YZ com normal em X; offset=R_SHELL posiciona no raio interno do casco.
# center(0, Z_INLET_H): Y=0 (sem offset circunferencial), Z=sensor_alto.
# both=True: stub cresce para fora (x > R_SHELL) e penetra na parede (x < R_SHELL);
#   a face externa em x = R_SHELL + L_INLET = 2305mm → Mass Flow Inlet no Star-CCM+.
inlet_stub = (cq.Workplane("YZ")
              .workplane(offset=R_SHELL)
              .center(0, Z_INLET_H)
              .circle(D_INLET / 2)
              .extrude(L_INLET, both=True))
tank_fluid = tank_fluid.union(inlet_stub)

# --- OCCT validity check ----------------------------------------
ok = tank_fluid.val().isValid()
print(f"  OCCT validity: {'VALID ✓' if ok else '!!! INVALID !!!'}")
assert ok

# --- Face count -------------------------------------------------
faces = tank_fluid.faces().vals()
print(f"  Total faces: {len(faces)}")

# ================================================================
# EXPORT
# ================================================================
path = os.path.join(OUTPUT_DIR, "chiller_tank_fluid_v2.step")
exporters.export(tank_fluid, path)
sz = os.path.getsize(path) / 1024
print(f"\n  Exportado: chiller_tank_fluid_v2.step  ({sz:.1f} KB)")

# ================================================================
# REFERENCE CALCULATIONS
# ================================================================
Q_VOL    = 12.0 / 3600       # m³/s (12 m³/h)
A_INLET  = math.pi * (D_INLET/2000)**2
V_INLET  = Q_VOL / A_INLET
TURNOVER = V_tot / 12.0             # horas (V_m3 / Q_m3/h)

print(f"""
================================================================
 REFERENCE VALUES
================================================================
  Diâmetro interno       : {D_SHELL:.0f} mm = {D_SHELL/1000:.2f} m
  Altura cilindro        : {H_CYLINDER:.0f} mm = {H_CYLINDER/1000:.2f} m
  Altura cone            : {H_CONE:.0f} mm = {H_CONE/1000:.2f} m
  Volume total           : {V_tot*1000:.1f} L = {V_tot:.3f} m³
  Turnover time          : {TURNOVER:.1f} h (V/Q)

  Bocal inlet DN{D_INLET:.0f} (PAREDE LATERAL, z={Z_INLET_H:.0f} mm = sensor_alto):
    Velocidade de entrada : {V_INLET:.3f} m/s  @ 12 m³/h (jato horizontal +X)
    Face BC em Star-CCM+ : x = {R_SHELL + L_INLET:.0f} mm do eixo do tanque

  Propriedades fluido (0°C):
    ρ  = 932.65 kg/m³
    μ  = 0.001796 Pa·s
    k  = 0.2758 W/m·K
    cp = 3652 J/kg·K
    Re = {932.65 * V_INLET * (D_INLET/1000) / 0.001796:.0f}  (no bocal de entrada)
================================================================
""")
