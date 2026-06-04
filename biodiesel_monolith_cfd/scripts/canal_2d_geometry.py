"""
Canal 2D representativo do monólito de biodiesel — Fase 1 (hidrodinâmica a frio)
Geometria: retângulo L × Dh = 50 mm × 1,1 mm
Exporta: canal_2d.step  (importar no STAR-CCM+ como 2D geometry)

Referência geométrica: Bath 2015/2017 PhD Thesis (Dh=1,1 mm, 400 CPSI)
"""

# ── Parâmetros ─────────────────────────────────────────────────────────────────
Dh_m  = 1.1e-3    # m — diâmetro hidráulico (canal quadrado)
L_m   = 50.0e-3   # m — comprimento do canal

# build123d trabalha em mm por padrão
Dh_mm = Dh_m  * 1e3   # 1,1 mm
L_mm  = L_m   * 1e3   # 50 mm

# ── Geometria ──────────────────────────────────────────────────────────────────
try:
    from build123d import BuildSketch, Rectangle, export_step, Plane

    with BuildSketch(Plane.XY) as sketch:
        Rectangle(L_mm, Dh_mm)

    output_file = "canal_2d.step"
    export_step(sketch.sketch, output_file)
    print(f"✓ STEP exportado: {output_file}")
    print(f"  Canal: {L_mm:.0f} mm (x) × {Dh_mm:.1f} mm (y)")

except ImportError:
    print("build123d não instalado — exibindo apenas os parâmetros geométricos.\n")
    print(f"  Comprimento L  = {L_mm:.1f} mm")
    print(f"  Altura     Dh  = {Dh_mm:.1f} mm")
    print(f"  Razão L/Dh     = {L_mm/Dh_mm:.0f}")
    print("\nInstalar build123d: pip install build123d")

# ── Informações para criar a geometria manualmente no STAR-CCM+ ───────────────
print("\n" + "=" * 60)
print("STAR-CCM+ — Criar geometria 2D manualmente:")
print("=" * 60)
print(f"  Geometry → 3D-CAD → New Part → Sketch → Rectangle")
print(f"    Width  (x): {L_mm:.1f} mm  (direção axial do escoamento)")
print(f"    Height (y): {Dh_mm:.1f} mm  (direção transversal)")
print(f"    Origin: (0, 0)")
print()
print("  Renomear superfícies após importação:")
print("    y = 0    → Bottom_Wall (parede inerte ou Symmetry)")
print(f"    y = {Dh_mm:.1f} → Top_Wall    (parede catalítica com washcoat)")
print("    x = 0    → Inlet")
print(f"    x = {L_mm:.0f}  → Outlet")
print()

# ── Verificação analítica Poiseuille (para validação da Fase 1) ────────────────
import math

# Propriedades da mistura a 120°C
rho    = 870.0    # kg/m³
mu     = 6.0e-3   # Pa·s (viscosidade dinâmica)
u_in   = 1.0e-3   # m/s  (velocidade de entrada)

Re = rho * u_in * Dh_m / mu
u_max = 1.5 * u_in   # perfil de Poiseuille: u_max = 3/2 * u_media

# ΔP Hagen-Poiseuille para canal plano 2D: ΔP = 12μLu/Dh²
dP = 12 * mu * L_m * u_in / (Dh_m ** 2)

# Comprimento de entrada hidrodinâmica
L_hid = 0.05 * Re * Dh_m

print("=" * 60)
print("Verificação analítica — Fase 1 (Poiseuille):")
print("=" * 60)
print(f"  Re    = {Re:.3f}  (Regime de Stokes, completamente laminar)")
print(f"  u_max = {u_max*1e3:.2f} mm/s  (linha central, deve ser 1,5 × u_entrada)")
print(f"  ΔP    = {dP:.2f} Pa  (Hagen-Poiseuille — deve ser ~3 Pa para L=50mm)")
print(f"  L_hid = {L_hid*1e6:.1f} µm  (perfil desenvolvido a < 0,1 mm da entrada)")
print()
print("  → Comparar u_max_CFD com u_max_analítico = {:.4f} m/s".format(u_max))
print("  → Comparar ΔP_CFD com ΔP_analítico = {:.2f} Pa".format(dP))
print("  → Desvio aceitável: < 1% (malha independente)")
