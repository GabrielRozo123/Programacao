"""
Canal 2D representativo do monólito de biodiesel — Fase 1 (hidrodinâmica a frio)

Geometria: retângulo L × Dh = 50 mm × 1,1 mm
  x → direção axial (escoamento)   [0, L]
  y → direção transversal          [0, Dh]

Superfícies/arestas:
  y = 0    → Bottom_Wall  (parede inerte ou Symmetry)
  y = Dh   → Top_Wall     (parede catalítica — washcoat ZnAl₂O₄)
  x = 0    → Inlet        (Velocity Inlet)
  x = L    → Outlet       (Pressure Outlet)

Exporta: geometry/canal_2d.step  (importar no STAR-CCM+ como 2D geometry)
"""

from pathlib import Path

# ── Parâmetros ─────────────────────────────────────────────────────────────────
Dh_m = 1.1e-3    # m — diâmetro hidráulico (canal quadrado, 400 CPSI)
L_m  = 50.0e-3   # m — comprimento do canal

Dh_mm = Dh_m * 1e3    # 1.1 mm
L_mm  = L_m  * 1e3    # 50.0 mm

# Saída relativa ao diretório do projeto (rodar de qualquer lugar)
SCRIPT_DIR  = Path(__file__).resolve().parent
OUTPUT_STEP = SCRIPT_DIR.parent / "geometry" / "canal_2d.step"
OUTPUT_STEP.parent.mkdir(parents=True, exist_ok=True)

# ── Geometria (build123d) ──────────────────────────────────────────────────────
try:
    from build123d import BuildSketch, Rectangle, export_step, Plane

    with BuildSketch(Plane.XY) as sketch:
        Rectangle(L_mm, Dh_mm)

    export_step(sketch.sketch, str(OUTPUT_STEP))
    print(f"STEP exportado: {OUTPUT_STEP}")

except ImportError:
    print("build123d não instalado — exibindo apenas parâmetros geométricos.")
    print("Instalar: pip install build123d")

# ── Resumo da geometria ────────────────────────────────────────────────────────
print()
print("=" * 60)
print("Geometria do canal 2D")
print("=" * 60)
print(f"  Comprimento L   = {L_mm:.1f} mm   (x: 0 → {L_mm:.0f} mm)")
print(f"  Altura Dh       = {Dh_mm:.2f} mm   (y: 0 → {Dh_mm:.1f} mm)")
print(f"  Razão L/Dh      = {L_mm/Dh_mm:.0f}  (canal longo → perfil desenvolvido rápido)")
print()
print("  Fronteiras (renomear no STAR-CCM+ após importação):")
print(f"    Inlet      → aresta x=0       (Velocity Inlet)")
print(f"    Outlet     → aresta x={L_mm:.0f}    (Pressure Outlet)")
print(f"    Bottom_Wall → aresta y=0      (No-Slip ou Symmetry)")
print(f"    Top_Wall   → aresta y={Dh_mm:.1f}  (No-Slip + Surface Reaction — Fase 2)")
print()

# ── Verificação analítica Poiseuille ──────────────────────────────────────────
rho   = 870.0    # kg/m³
mu    = 6.0e-3   # Pa·s
u_in  = 1.0e-3   # m/s   (velocidade de entrada Fase 1)

Re    = rho * u_in * Dh_m / mu
u_max = 1.5 * u_in
dP    = 12.0 * mu * L_m * u_in / Dh_m**2
L_hid = 0.05 * Re * Dh_m

print("=" * 60)
print("Verificação analítica — Fase 1 (Poiseuille, canal plano 2D)")
print("=" * 60)
print(f"  u_entrada = {u_in*1e3:.1f} mm/s")
print(f"  Re        = {Re:.4f}  → Stokes (laminar, sem turbulência)")
print(f"  u_max     = {u_max*1e3:.3f} mm/s  (linha central = 3/2 × u_média)")
print(f"  ΔP        = {dP:.3f} Pa   (Hagen-Poiseuille: 12μLu/Dh²)")
print(f"  L_hid     = {L_hid*1e6:.1f} µm   (perfil desenvolvido praticamente na entrada)")
print()
print("  Critério de validação do CFD (Fase 1):")
print(f"    u_max_CFD deve ser ≈ {u_max*1e3:.3f} mm/s  (desvio < 1%)")
print(f"    ΔP_CFD   deve ser ≈ {dP:.3f} Pa    (desvio < 1%)")
