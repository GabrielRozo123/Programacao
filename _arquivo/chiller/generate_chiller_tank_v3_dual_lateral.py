#!/usr/bin/env python3
"""
GreyBeer Chiller Tank – Fluid Domain Geometry for Star-CCM+  [v3 — dual lateral]
============================================================
Tanque de solução hidroalcóolica (70%m/m água + 30%m/m etanol)
resfriado por chiller externo. Estudo de estratificação térmica transiente.

Geometria (domínio fluido only — paredes excluídas):
  - Cilindro vertical com fundo cônico e topo plano
  - Dois bocais na PAREDE LATERAL, mesmo lado (+X), alinhados verticalmente:
      inlet  (do chiller, -5°C) → z = Z_INLET_H  = sensor_alto
      outlet (para o chiller)   → z = Z_OUTLET_H = sensor_baixo

Coord system: eixo Z vertical, origem no ápice do cone (ponto mais baixo do fluido).

ALTERAÇÃO v3 (vs v2):
  - Outlet movido do ápice do cone para parede lateral em z = sensor_baixo
  - Cone de fundo permanece fechado (sem stub embaixo)

BCs no Star-CCM+:
  inlet face  (x = R_SHELL + L_INLET,  z = Z_INLET_H)  → Mass Flow Inlet
  outlet face (x = R_SHELL + L_OUTLET, z = Z_OUTLET_H) → Pressure Outlet
  todo o resto                                           → Wall
"""

import cadquery as cq
from cadquery import exporters
import math, os

# ================================================================
# PARÂMETROS GEOMÉTRICOS (mm — escala real)
# ================================================================
D_SHELL      = 4210.0    # diâmetro interno do casco [mm]
R_SHELL      = D_SHELL / 2

H_CONE       = 780.0     # altura do cone de fundo [mm]
H_CYLINDER   = 4720.0    # altura da seção cilíndrica [mm]
H_TOTAL      = H_CONE + H_CYLINDER

CONE_HALF_ANGLE = math.degrees(math.atan(R_SHELL / H_CONE))
print(f"  Ângulo semi-vertical do cone: {CONE_HALF_ANGLE:.1f}°")

# ── Bocal de ENTRADA (inlet) ─────────────────────────────────────
D_INLET      = 150.0     # DN150
L_INLET      = 200.0     # comprimento do stub [mm]
Z_INLET_H    = 1641.0    # DWG viewer Z=1641 mm → stub inlet na parede lateral

# ── Bocal de SAÍDA (outlet) ──────────────────────────────────────
D_OUTLET     = 150.0     # DN150
L_OUTLET     = 200.0     # comprimento do stub [mm]
Z_OUTLET_H   = 1116.0    # DWG viewer Z=1116 mm → stub outlet na parede lateral

OUTPUT_DIR   = "/home/user/Programacao/_arquivo/chiller"

# ================================================================
# VERIFICAÇÃO DE POSIÇÕES
# ================================================================
assert H_CONE < Z_INLET_H < H_TOTAL,  f"Z_INLET_H={Z_INLET_H} fora da seção cilíndrica"
assert H_CONE < Z_OUTLET_H < H_TOTAL, f"Z_OUTLET_H={Z_OUTLET_H} fora da seção cilíndrica"
assert Z_OUTLET_H < Z_INLET_H, "outlet deve estar abaixo do inlet"

print(f"  Inlet  (sensor_alto) : z = {Z_INLET_H:.0f} mm")
print(f"  Outlet (sensor_baixo): z = {Z_OUTLET_H:.0f} mm")
print(f"  Separação vertical   : {Z_INLET_H - Z_OUTLET_H:.0f} mm")

# ================================================================
# VOLUME TOTAL
# ================================================================
V_cyl  = math.pi * R_SHELL**2 * H_CYLINDER
V_cone = math.pi * R_SHELL**2 * H_CONE / 3
V_tot  = (V_cyl + V_cone) / 1e9
print(f"  Volume cilindro : {V_cyl/1e6:.0f} L")
print(f"  Volume cone     : {V_cone/1e6:.0f} L")
print(f"  Volume total    : {V_tot*1000:.0f} L = {V_tot:.2f} m³")

# ================================================================
# BUILD GEOMETRY
# ================================================================
print("\nConstruindo domínio fluido...")

# --- Corpo principal (revolve do perfil meridional) ---------------
tank_fluid = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(R_SHELL, H_CONE)
    .lineTo(R_SHELL, H_CONE + H_CYLINDER)
    .lineTo(0,       H_CONE + H_CYLINDER)
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)
vol_check = tank_fluid.val().Volume()
print(f"  Volume OCCT: {vol_check/1e6:.0f} L  (esperado: {(V_cyl+V_cone)/1e6:.0f} L)")
assert abs(vol_check - V_cyl - V_cone) / (V_cyl + V_cone) < 0.01, "Volume check failed!"

# --- Bocal de ENTRADA (inlet) — parede lateral, jato horizontal +X
# Face externa em x = R_SHELL + L_INLET → Mass Flow Inlet no Star-CCM+
inlet_stub = (cq.Workplane("YZ")
              .workplane(offset=R_SHELL)
              .center(0, Z_INLET_H)
              .circle(D_INLET / 2)
              .extrude(L_INLET, both=True))
tank_fluid = tank_fluid.union(inlet_stub)

# --- Bocal de SAÍDA (outlet) — parede lateral, jato horizontal +X
# Face externa em x = R_SHELL + L_OUTLET → Pressure Outlet no Star-CCM+
outlet_stub = (cq.Workplane("YZ")
               .workplane(offset=R_SHELL)
               .center(0, Z_OUTLET_H)
               .circle(D_OUTLET / 2)
               .extrude(L_OUTLET, both=True))
tank_fluid = tank_fluid.union(outlet_stub)

# --- OCCT validity check -----------------------------------------
ok = tank_fluid.val().isValid()
print(f"  OCCT validity: {'VALID ✓' if ok else '!!! INVALID !!!'}")
assert ok

faces = tank_fluid.faces().vals()
print(f"  Total faces: {len(faces)}")

# ================================================================
# EXPORT
# ================================================================
path = os.path.join(OUTPUT_DIR, "chiller_tank_fluid_v3.step")
exporters.export(tank_fluid, path)
sz = os.path.getsize(path) / 1024
print(f"\n  Exportado: chiller_tank_fluid_v3.step  ({sz:.1f} KB)")

# ================================================================
# REFERENCE CALCULATIONS
# ================================================================
Q_VOL    = 12.0 / 3600
A_NOZZLE = math.pi * (D_INLET / 2000) ** 2
V_NOZZLE = Q_VOL / A_NOZZLE
TURNOVER = V_tot / 12.0

print(f"""
================================================================
 REFERENCE VALUES
================================================================
  Diâmetro interno       : {D_SHELL:.0f} mm = {D_SHELL/1000:.2f} m
  Altura cilindro        : {H_CYLINDER:.0f} mm
  Altura cone            : {H_CONE:.0f} mm
  Volume total           : {V_tot*1000:.1f} L = {V_tot:.3f} m³
  Turnover time          : {TURNOVER:.1f} h

  Bocal INLET  DN{D_INLET:.0f}  (sensor_alto,  z={Z_INLET_H:.0f} mm):
    Face BC em x = {R_SHELL + L_INLET:.0f} mm do eixo
    Velocidade  : {V_NOZZLE:.3f} m/s  @ 12 m³/h

  Bocal OUTLET DN{D_OUTLET:.0f}  (sensor_baixo, z={Z_OUTLET_H:.0f} mm):
    Face BC em x = {R_SHELL + L_OUTLET:.0f} mm do eixo

  Re no bocal  : {932.65 * V_NOZZLE * (D_INLET/1000) / 0.001796:.0f}
================================================================
""")
