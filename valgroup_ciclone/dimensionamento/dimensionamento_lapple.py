"""
Dimensionamento preliminar do ciclone Lapple — Valgroup.
Método: Peçanha, Cap. 3 (ver ../literatura/pecanha_ciclone_lapple.md).
Entradas com ⚠️ são ESTIMATIVAS a confirmar; ρ_gás foi enviado pelo cliente.
"""
import numpy as np

# ── ENTRADAS ──────────────────────────────────────────────────────────────
RHO_GAS = 3.946      # kg/m³  ✅ cliente (400°C, 1,2 bar) — "não 100% confiante"
MU_GAS  = 2.5e-5     # Pa·s   ⚠️ ESTIMATIVA (gás de pirólise ~400°C); confirmar c/ composição
RHO_S   = 1500.0     # kg/m³  ⚠️ ESTIMATIVA densidade da PARTÍCULA (bulk=776,75; minerais ↑); confirmar
MDOT_GAS = 720.0     # kg/h   (800 total − 80 char); gás que carreia o char
N_E     = 5          # espiras efetivas (padrão Lapple)
V_I_ALVO = 15.2      # m/s    velocidade de entrada recomendada (~50 ft/s, Perry)
DP_MAX  = 40e2       # Pa     (40 mbar) restrição do projeto
ETA_BLOWER = 0.7

# Granulometria (amostra EXTRAÍDA 3072-1/2025.0). ⚠️ char CARREADO é mais fino.
# (faixa_μm_min, faixa_μm_max, %massa) — bin representado pela média geométrica
BINS = [
    (12500, 20000, 2.78),
    ( 4750, 12500, 3.77),
    ( 1000,  4750, 9.51),
    (  425,  1000, 12.10),
    (  150,   425, 25.79),
    (   75,   150, 36.91),
    (   20,    75, 9.41),   # "fundo <75": faixa 20–75 assumida (⚠️)
]

# ── CÁLCULOS ──────────────────────────────────────────────────────────────
Q = (MDOT_GAS/3600.0)/RHO_GAS          # m³/s
# Dimensiona D_c para v_i alvo:  v_i = Q/(B_c·H_c) = Q/((D_c/4)(D_c/2)) = 8Q/D_c²
D_c = np.sqrt(8*Q/V_I_ALVO)
B_c = D_c/4; H_c = D_c/2
v_i = Q/(B_c*H_c)
# Diâmetro de corte (eq. 3.92):  D'/D_c = 0.0946·√(μ·D_c/(Q·(ρ_s−ρ)))
d_corte = 0.0946*np.sqrt(MU_GAS*D_c/(Q*(RHO_S-RHO_GAS)))*D_c   # m
# Queda de pressão (ξ=8): ΔP = 4·ρ·v_i²
dP = 4*RHO_GAS*v_i**2
pot = dP*Q/ETA_BLOWER

def eta_i(dp_m):                        # eq. 3.90 Lapple
    return 1.0/(1.0 + (d_corte/dp_m)**2)

print("="*60)
print("DIMENSIONAMENTO PRELIMINAR — CICLONE LAPPLE (Valgroup)")
print("="*60)
print(f"Q (gás)          = {Q*3600:.1f} m³/h  ({Q:.4f} m³/s)")
print(f"D_c (corpo)      = {D_c*1000:.1f} mm")
print(f"  B_c={B_c*1000:.1f}  H_c={H_c*1000:.1f}  D_e={D_c/2*1000:.1f}  H_total≈{4*D_c*1000:.0f} mm")
print(f"v_i (entrada)    = {v_i:.1f} m/s   (faixa 6–21; alvo {V_I_ALVO}) {'OK' if 6<=v_i<=21 else 'FORA'}")
print(f"d* (corte)       = {d_corte*1e6:.2f} µm")
print(f"ΔP               = {dP:.0f} Pa = {dP/100:.1f} mbar   (limite {DP_MAX/100:.0f}) {'OK' if dP<=DP_MAX else 'EXCEDE'}")
print(f"Pot. soprador    = {pot:.0f} W")
print()
print("Eficiência por faixa (Lapple = LIMITE SUPERIOR):")
eta_g=0.0; m_tot=sum(m for *_,m in BINS)
for lo,hi,m in BINS:
    dgm=np.sqrt(lo*hi)*1e-6
    e=eta_i(dgm)
    eta_g += e*m
    print(f"  {lo:>6}–{hi:<6} µm  (dgm {dgm*1e6:6.0f})  massa {m:5.2f}%  η_i={e*100:6.2f}%")
eta_g/=m_tot
print(f"\nη GLOBAL (amostra extraída, normalizada) = {eta_g*100:.2f}%")
print()
print("SENSIBILIDADE (d* muda pouco):")
for mu in (2.0e-5, 2.5e-5, 3.0e-5):
    for rs in (1200, 1500, 2000):
        dc=0.0946*np.sqrt(mu*D_c/(Q*(rs-RHO_GAS)))*D_c*1e6
        print(f"  μ={mu:.1e}  ρ_s={rs:4d} -> d*={dc:.2f} µm")
