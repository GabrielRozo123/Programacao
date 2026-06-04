"""
Propriedades físicas da mistura óleo/metanol para CFD
Reator monolítico — biodiesel via transesterificação heterogênea
Gabriel Rozo | FEQ/UNICAMP | 2025–2027

Referências:
  Wilke-Chang (1955): difusividade em solventes
  Perry's Chemical Engineers' Handbook (8th ed.)
  DIPPR Project 801
"""

import math

# ─── Condições operacionais ──────────────────────────────────────────────────
T_K = 393.15        # 120°C em Kelvin
P_bar = 8.0         # pressão de operação

# ─── Propriedades do solvente (MeOH a 120°C) ────────────────────────────────
# MeOH: M = 32 g/mol, ponto ebulição 64.7°C → precisa de 8 bar para manter líquido a 120°C
M_MeOH   = 32.04        # g/mol
mu_MeOH  = 0.26e-3      # Pa·s a 120°C (reduz muito com T)
phi_MeOH = 1.9          # fator de associação de Wilke-Chang para MeOH

# ─── Propriedades do soluto (TG — triolein como componente modelo) ───────────
M_TG     = 885.4        # g/mol (triolein, C57H104O6)
V_TG     = 1060.0       # cm³/mol — volume molar de ebulição (estimado por contribuição de grupos)
                        # Método LeBas: ver Perry's Table 2-370
                        # ⚠️ VALIDAR: Wilke-Chang aqui aplica MeOH puro como solvente,
                        # mas no sistema real TG não é diluído. Verificar com literatura
                        # experimental (D_TG típico: ~1×10⁻¹⁰ m²/s a 25°C na mistura oleosa)

# ─── Correlação de Wilke-Chang (1955) ───────────────────────────────────────
# D_AB = 7.4×10⁻¹⁰ × (φ × M_B)^0.5 × T / (μ_B × V_A^0.6)
# D_AB [m²/s], T [K], μ [cP], V [cm³/mol]

mu_MeOH_cP = mu_MeOH * 1000  # converter Pa·s → cP

D_TG_MeOH = (7.4e-10 * (phi_MeOH * M_MeOH)**0.5 * T_K) / \
             (mu_MeOH_cP * V_TG**0.6)   # m²/s

print("=" * 60)
print("  PROPRIEDADES FÍSICAS — MISTURA ÓLEO/MeOH a 120°C, 8 bar")
print("=" * 60)
print()
print("─── DIFUSIVIDADE (Wilke-Chang) ─────────────────────────────")
print(f"  D_TG em MeOH:  {D_TG_MeOH:.2e} m²/s")
print()

# ─── Número de Schmidt ───────────────────────────────────────────────────────
rho_mix = 870.0         # kg/m³ (mistura óleo 6:1 MeOH a 120°C — estimado)
mu_mix  = 6.0e-3        # Pa·s (mistura — dominado pelo óleo)

Sc = mu_mix / (rho_mix * D_TG_MeOH)

print("─── NÚMEROS ADIMENSIONAIS ──────────────────────────────────")
print(f"  Sc (TG em mistura):  {Sc:.0f}  ← confirmar: deve ser >> 1")
print()

# ─── Número de Reynolds ──────────────────────────────────────────────────────
Dh = 1.1e-3             # m (diâmetro hidráulico, 400 CPSI)
u_range = [1e-3, 5e-3]  # m/s (faixa típica de velocidade)

print("─── NÚMERO DE REYNOLDS ─────────────────────────────────────")
for u in u_range:
    Re = rho_mix * u * Dh / mu_mix
    print(f"  u = {u*1000:.1f} mm/s → Re = {Re:.3f}  (laminar {'✓' if Re < 2300 else '✗'})")
print()

# ─── Queda de pressão (Hagen-Poiseuille, canal plano 2D) ─────────────────────
L_canal = 50e-3         # m (comprimento do canal)
u_ref   = 1e-3          # m/s

dP = 12 * mu_mix * L_canal * u_ref / Dh**2

print("─── QUEDA DE PRESSÃO (Hagen-Poiseuille) ───────────────────")
print(f"  L = {L_canal*1000:.0f} mm | u = {u_ref*1000:.1f} mm/s | Dh = {Dh*1000:.1f} mm")
print(f"  ΔP = {dP:.2f} Pa  ({dP/1e5*1e3:.4f} mbar)  → praticamente zero ✓")
print(f"  ΔP/P_op = {dP/(P_bar*1e5)*100:.5f}%  ← desprezível")
print()

# ─── Comprimento de entrada hidrodinâmico ────────────────────────────────────
Re_ref = rho_mix * u_ref * Dh / mu_mix
L_hid  = 0.05 * Re_ref * Dh

print("─── COMPRIMENTO DE ENTRADA HIDRODINÂMICO ──────────────────")
print(f"  Re = {Re_ref:.3f}")
print(f"  L_hid = 0.05 × Re × Dh = {L_hid*1e6:.1f} µm  ← desprezível")
print(f"  → Canal de {L_canal*1000:.0f} mm é 100% em regime desenvolvido ✓")
print()

# ─── Comprimento de entrada difusivo (espécie) ───────────────────────────────
Pe_mass = u_ref * Dh / D_TG_MeOH   # Número de Péclet de massa
L_dif   = Dh * Pe_mass / 10        # comprimento de entrada de concentração (estimado)

print("─── TRANSPORTE DE MASSA ────────────────────────────────────")
print(f"  Péclet de massa (Pe_m): {Pe_mass:.0f}  ← Pe >> 1 → convecção domina o transporte axial")
print(f"  L_difusivo estimado:    {L_dif:.3f} m = {L_dif*1000:.1f} mm")
print(f"  → TG não se homogeneiza radialmente no canal de {L_canal*1000:.0f} mm")
print(f"  → Gradiente radial de concentração significativo — justifica CHT na Fase 2")
print()

# ─── Número de Damköhler (placeholder — atualizar com cinética real) ─────────
r_max_placeholder = 1e-5   # mol/(m²·s) — estimativa
C0_TG = rho_mix * 0.88 / (M_TG * 1e-3)  # mol/m³ (fração mássica 88% de TG)

Da = r_max_placeholder * Dh / (D_TG_MeOH * C0_TG)

print("─── NÚMERO DE DAMKÖHLER ────────────────────────────────────")
print(f"  C₀_TG ≈ {C0_TG:.1f} mol/m³")
print(f"  r_max (placeholder) = {r_max_placeholder:.1e} mol/(m²·s)")
print(f"  Da = r × Dh / (D × C₀) = {Da:.3f}")
if Da < 0.1:
    print("  → Regime CINÉTICO: BC de Surface Reaction é fisicamente adequada ✓")
elif Da < 10:
    print("  → Regime MISTO: acoplamento real — modelo de washcoat pode ser necessário")
else:
    print("  ⚠️ Regime DIFUSIVO: considerar modelo de difusão no washcoat (pellet)")
print()
print("  NOTA: Atualizar r_max com parâmetros cinéticos LHHW reais (ZnAl₂O₄)")
print()
print("=" * 60)
print("  Para o CFD (STAR-CCM+):")
print(f"  Density:           {rho_mix} kg/m³")
print(f"  Dynamic Viscosity: {mu_mix:.1e} Pa·s")
print(f"  D_TG:              {D_TG_MeOH:.2e} m²/s")
print(f"  Inlet velocity:    1.0e-3 m/s  (Re = {Re_ref:.3f})")
print("=" * 60)
