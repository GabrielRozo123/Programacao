"""
Propriedades físicas e cinéticas — transesterificação de triolein/MeOH
Catalisador heterogêneo ZnAl2O4 | Reator monolítico 2D (STAR-CCM+)
Gabriel Rozo | FEQ/UNICAMP | Mestrado 2025–2027

Referência cinética principal:
  Allain et al. (2015), Chemical Engineering Journal 281, 654–664.
  DOI: 10.1016/j.cej.2015.07.075
  Modelo "Clássico" (melhor ajuste, LS=0.022, Tabelas 6, 7 e 12)
  Três reações reversíveis em série:
    r1: TG  + MeOH <-> DG   + FAME
    r2: DG  + MeOH <-> MG   + FAME
    r3: MG  + MeOH <-> GL   + FAME

Referências complementares:
  Wilke & Chang (1955): difusividade em solventes
  Perry's Chemical Engineers' Handbook (8th ed.)
"""

import math

# ============================================================
# 0. CONSTANTES GLOBAIS
# ============================================================
R_GAS = 8.314          # J/(mol·K)

# ============================================================
# 1. CONDICOES OPERACIONAIS
# ============================================================
T_op_C    = 120.0          # temperatura de operacao do projeto [°C]
T_op_K    = T_op_C + 273.15  # 393.15 K
T_ref_C   = 185.0          # temperatura de referencia do artigo (experimentos) [°C]
T_ref_K   = T_ref_C + 273.15  # 458.15 K
P_bar     = 8.0            # pressao de operacao [bar]

print("=" * 70)
print("  PROPRIEDADES FISICAS E CINETICAS — Allain et al. (2015)")
print("  Transesterificacao triolein/MeOH | ZnAl2O4 | Canal monolitico 2D")
print("=" * 70)
print(f"\n  T_operacao  = {T_op_C:.0f} degC ({T_op_K:.2f} K)")
print(f"  T_referencia artigo = {T_ref_C:.0f} degC ({T_ref_K:.2f} K)")
print(f"  P_operacao  = {P_bar} bar")

# ============================================================
# 2. PARAMETROS CINETICOS — MODELO CLASSICO (Tabelas 6 e 7)
# ============================================================
# Unidades dos fatores pre-exponenciais: m6/(mol·s·kgcata)
# Unidades das taxas r: mol/(kgcata·s)
# Reacoes: segunda ordem, reversiveis
#
#   r_i = k_i0 * exp(-Ea_i / RT) * (C_A * C_B - (1/K_i) * C_C * C_D)

# --- Fatores pre-exponenciais [m6/(mol·kgcata·s)] ---
k1_0 = 1.26e-2    # Tabela 6
k2_0 = 8.88e-6    # Tabela 6
k3_0 = 1.28e-7    # Tabela 6

# --- Energias de ativacao [J/mol] (convertidas de kJ/mol) ---
Ea1  = 64.6e3     # 64.6 kJ/mol → Tabela 6
Ea2  = 31.8e3     # 31.8 kJ/mol → Tabela 6
Ea3  = 17.0e3     # 17.0 kJ/mol → Tabela 6

# --- Constantes de equilibrio (adimensionais) --- Tabela 7
K1_eq = 51.2
K2_eq = 53.1
K3_eq = 12.2

print("\n" + "-" * 70)
print("  CINETICA — Modelo Classico (Allain 2015, Tabela 6 e 7)")
print("-" * 70)
print(f"  k1_0 = {k1_0:.2e}  m6/(mol·kgcata·s)  |  Ea1 = {Ea1/1e3:.1f} kJ/mol")
print(f"  k2_0 = {k2_0:.2e}  m6/(mol·kgcata·s)  |  Ea2 = {Ea2/1e3:.1f} kJ/mol")
print(f"  k3_0 = {k3_0:.2e}  m6/(mol·kgcata·s)  |  Ea3 = {Ea3/1e3:.1f} kJ/mol")
print(f"  K1_eq = {K1_eq}  |  K2_eq = {K2_eq}  |  K3_eq = {K3_eq}  (adimensionais)")

# ============================================================
# 3. ARRHENIUS — EXTRAPOLACAO PARA 120 degC
# ============================================================

def k_arrhenius(k0, Ea, T_K):
    """Constante cinetica via Arrhenius. k0 em m6/(mol·kgcata·s)."""
    return k0 * math.exp(-Ea / (R_GAS * T_K))

# Constantes a 120 degC (extrapolacao — T < faixa do artigo 140-220 degC)
k1_120 = k_arrhenius(k1_0, Ea1, T_op_K)
k2_120 = k_arrhenius(k2_0, Ea2, T_op_K)
k3_120 = k_arrhenius(k3_0, Ea3, T_op_K)

# Constantes a 185 degC (valor de referencia do artigo — validacao cruzada)
k1_185 = k_arrhenius(k1_0, Ea1, T_ref_K)
k2_185 = k_arrhenius(k2_0, Ea2, T_ref_K)
k3_185 = k_arrhenius(k3_0, Ea3, T_ref_K)

# Valores reportados na Tabela 8 do artigo (para validar a extrapolacao)
k1_185_paper = 5.6e-10
k2_185_paper = 2.1e-9
k3_185_paper = 1.5e-9

print("\n" + "-" * 70)
print("  EXTRAPOLACAO ARRHENIUS — k(T) [m6/(mol·kgcata·s)]")
print("-" * 70)
print(f"  {'T (degC)':<10} {'k1':>14} {'k2':>14} {'k3':>14}")
print(f"  {'-'*10} {'-'*14} {'-'*14} {'-'*14}")
for T_C, T_K in [(160, 433.15), (185, 458.15), (200, 473.15)]:
    k1v = k_arrhenius(k1_0, Ea1, T_K)
    k2v = k_arrhenius(k2_0, Ea2, T_K)
    k3v = k_arrhenius(k3_0, Ea3, T_K)
    print(f"  {T_C:<10} {k1v:>14.2e} {k2v:>14.2e} {k3v:>14.2e}  (calculado)")
print(f"  {'185 (paper)':<10} {k1_185_paper:>14.2e} {k2_185_paper:>14.2e} {k3_185_paper:>14.2e}  (Tabela 8)")
print()
print(f"  EXTRAPOLACAO para T_op = {T_op_C:.0f} degC ({T_op_K:.2f} K):")
print(f"    k1(120 degC) = {k1_120:.3e}  m6/(mol·kgcata·s)")
print(f"    k2(120 degC) = {k2_120:.3e}  m6/(mol·kgcata·s)")
print(f"    k3(120 degC) = {k3_120:.3e}  m6/(mol·kgcata·s)")
print()
print(f"  Razao k1(185)/k1(120) = {k1_185/k1_120:.1f}x  (cinética ~{k1_185/k1_120:.0f}x mais rápida a 185 degC)")
print(f"  Razao k2(185)/k2(120) = {k2_185/k2_120:.1f}x")
print(f"  Razao k3(185)/k3(120) = {k3_185/k3_120:.1f}x")
print()
print("  ATENCAO: T=120 degC e EXTRAPOLACAO alem da faixa do artigo (140-220 degC).")
print("           Usar com cautela. Validar com dados experimentais se disponíveis.")

# ============================================================
# 4. PROPRIEDADES DO CATALISADOR (Tabela 1, Allain 2015)
# ============================================================
rho_cat    = 1188.0    # kg/m3 — densidade do catalisador
epsilon_cat = 0.512    # porosidade
tau_cat    = 2.5       # tortuosidade
S_BET      = 160.0     # m2/g — area superficial especifica
d_meso_min = 9e-9      # m — tamanho minimo de mesoporo
d_meso_max = 100e-9    # m — tamanho maximo de mesoporo

print("\n" + "-" * 70)
print("  PROPRIEDADES DO CATALISADOR ZnAl2O4 (Allain 2015, Tabela 1)")
print("-" * 70)
print(f"  Densidade:            {rho_cat:.0f} kg/m3")
print(f"  Porosidade:           {epsilon_cat}")
print(f"  Tortuosidade:         {tau_cat}")
print(f"  Area BET:             {S_BET:.0f} m2/g  ({S_BET*rho_cat:.2e} m2/m3)")
print(f"  Mesoporos:            {d_meso_min*1e9:.0f}-{d_meso_max*1e9:.0f} nm")

# ============================================================
# 5. CONVERSAO DE UNIDADES PARA STAR-CCM+ (Surface Reaction BC)
# ============================================================
# Artigo: r [mol/(kgcata·s)] — base em massa de catalisador
# STAR-CCM+ Surface Reaction: r_wall [mol/(m2_wall·s)] — base em area de parede
#
# Conversao:
#   r_wall = r_vol * rho_washcoat * delta_washcoat
#
# Onde:
#   rho_washcoat  = densidade do catalisador [kg/m3]     = 1188 kg/m3 (Tabela 1)
#   delta_washcoat = espessura do washcoat [m]            = 20e-6 m (tipico monolito)
#   => fator_conv  = rho_washcoat * delta_washcoat        [kgcata/m2_wall]

delta_washcoat = 20e-6          # m — espessura tipica de washcoat em monolito
fator_conv     = rho_cat * delta_washcoat  # kgcata/m2_wall

print("\n" + "-" * 70)
print("  CONVERSAO DE UNIDADES: mol/(kgcata·s) → mol/(m2_wall·s)")
print("-" * 70)
print(f"  rho_washcoat   = {rho_cat:.0f} kg/m3  (Tabela 1)")
print(f"  delta_washcoat = {delta_washcoat*1e6:.0f} um  (tipico monolito — assumido)")
print(f"  Fator de conversao = rho * delta = {fator_conv:.5f} kgcata/m2_wall")
print()
print(f"  r_wall [mol/(m2·s)] = r_vol [mol/(kgcata·s)] × {fator_conv:.5f}")
print()
print("  Em notacao STAR-CCM+ (Field Function):")
print("    r_wall_i = r_vol_i * 0.02376")

# ============================================================
# 6. COEFICIENTES DE DIFUSAO (Tabela 12, Allain 2015, a 185 degC)
# ============================================================
# Valores otimizados por ajuste experimental, unidades: m2/s a ~185 degC

D_TG_ref   = 0.17e-9   # m2/s — muito baixo (molecula grande, TG = C57H104O6)
D_MeOH_ref = 17.00e-9  # m2/s
D_DG_ref   = 3.88e-9   # m2/s
D_MG_ref   = 15.34e-9  # m2/s
D_GL_ref   = 9.63e-9   # m2/s
D_FAME_ref = 9.00e-9   # m2/s

# Correcao de temperatura: D ∝ T/mu (Stokes-Einstein simplificado)
# mu(MeOH) a 185 degC ≈ 0.18 cP = 0.18e-3 Pa·s (estimado, DIPPR)
# mu(MeOH) a 120 degC ≈ 0.26 cP = 0.26e-3 Pa·s (do script original)
mu_MeOH_ref = 0.18e-3   # Pa·s a 185 degC
mu_MeOH_op  = 0.26e-3   # Pa·s a 120 degC

def corr_difusao(D_ref, T_ref_K, T_op_K, mu_ref, mu_op):
    """
    Corrige difusividade com proporcionalidade D ∝ T/mu (Stokes-Einstein).
    D_op = D_ref * (T_op / T_ref) * (mu_ref / mu_op)
    """
    return D_ref * (T_op_K / T_ref_K) * (mu_ref / mu_op)

D_TG_op   = corr_difusao(D_TG_ref,   T_ref_K, T_op_K, mu_MeOH_ref, mu_MeOH_op)
D_MeOH_op = corr_difusao(D_MeOH_ref, T_ref_K, T_op_K, mu_MeOH_ref, mu_MeOH_op)
D_DG_op   = corr_difusao(D_DG_ref,   T_ref_K, T_op_K, mu_MeOH_ref, mu_MeOH_op)
D_MG_op   = corr_difusao(D_MG_ref,   T_ref_K, T_op_K, mu_MeOH_ref, mu_MeOH_op)
D_GL_op   = corr_difusao(D_GL_ref,   T_ref_K, T_op_K, mu_MeOH_ref, mu_MeOH_op)
D_FAME_op = corr_difusao(D_FAME_ref, T_ref_K, T_op_K, mu_MeOH_ref, mu_MeOH_op)

print("\n" + "-" * 70)
print("  COEFICIENTES DE DIFUSAO (Allain 2015, Tabela 12 + correcao T)")
print(f"  Correcao: D ∝ T/mu  |  de {T_ref_C:.0f} degC para {T_op_C:.0f} degC")
print(f"  Fator de correcao T/mu = {(T_op_K/T_ref_K)*(mu_MeOH_ref/mu_MeOH_op):.4f}")
print("-" * 70)
print(f"  {'Especie':<8} {'M (g/mol)':>12} {'D(185 degC) [m2/s]':>20} {'D(120 degC) [m2/s]':>20}")
print(f"  {'-'*8} {'-'*12} {'-'*20} {'-'*20}")
especies = [
    ("TG",   885.4, D_TG_ref,   D_TG_op),
    ("DG",   621.0, D_DG_ref,   D_DG_op),
    ("MG",   357.0, D_MG_ref,   D_MG_op),
    ("MeOH",  32.0, D_MeOH_ref, D_MeOH_op),
    ("FAME", 297.0, D_FAME_ref, D_FAME_op),
    ("GL",    92.0, D_GL_ref,   D_GL_op),
]
for nome, M, D_ref, D_op in especies:
    print(f"  {nome:<8} {M:>12.1f} {D_ref:>20.2e} {D_op:>20.2e}")

# ============================================================
# 7. NUMEROS ADIMENSIONAIS COM DADOS REAIS
# ============================================================

# Propriedades da mistura a 120 degC, 8 bar
rho_mix = 870.0         # kg/m3 (mistura oleo 6:1 MeOH — estimado)
mu_mix  = 6.0e-3        # Pa·s  (dominado pelo oleo a 120 degC)
Dh      = 1.1e-3        # m     (diametro hidraulico, 400 CPSI)
u_ref   = 1.0e-3        # m/s   (velocidade de referencia)
L_canal = 50.0e-3       # m     (comprimento do canal)

# Numero de Schmidt para cada especie (com mu_mix da mistura real)
print("\n" + "-" * 70)
print("  NUMEROS DE SCHMIDT — Sc = mu_mix / (rho_mix * D_i)")
print(f"  mu_mix = {mu_mix:.1e} Pa·s  |  rho_mix = {rho_mix} kg/m3")
print("-" * 70)
print(f"  {'Especie':<8} {'D (120 degC)':>18} {'Sc':>12}")
print(f"  {'-'*8} {'-'*18} {'-'*12}")
for nome, M, D_ref, D_op in especies:
    Sc_i = mu_mix / (rho_mix * D_op)
    print(f"  {nome:<8} {D_op:>18.2e} {Sc_i:>12.0f}")
print()
print("  OBS: Sc_TG >> 1 — gradientes radiais de concentracao de TG dominantes.")
print("       Justifica resolucao espacial fina na direcao radial (malha refinada na parede).")

# Numero de Reynolds
Re_ref = rho_mix * u_ref * Dh / mu_mix

print("\n" + "-" * 70)
print("  NUMERO DE REYNOLDS")
print("-" * 70)
for u in [1e-3, 5e-3]:
    Re = rho_mix * u * Dh / mu_mix
    regime = "laminar (Stokes)" if Re < 1 else ("laminar" if Re < 2300 else "TURBULENTO")
    print(f"  u = {u*1000:.1f} mm/s  ->  Re = {Re:.4f}  ({regime})")

# ============================================================
# 8. NUMERO DE DAMKOHLER (com cinetica real de Allain 2015)
# ============================================================
# Estimativa conservadora: condicao de entrada
# C0_TG  (mol/m3): mistura 6:1 molar MeOH:oleo, fracao massica TG ~88%
# C0_MeOH (mol/m3): fracao massica MeOH ~12%

M_TG_kg   = 0.8854    # kg/mol
M_MeOH_kg = 0.0320    # kg/mol

w_TG   = 0.88          # fracao massica TG na entrada (estimado 6:1 molar ~ 0.88/0.12 masssica)
w_MeOH = 1.0 - w_TG   # fracao massica MeOH

C0_TG   = rho_mix * w_TG   / M_TG_kg    # mol/m3
C0_MeOH = rho_mix * w_MeOH / M_MeOH_kg  # mol/m3

# Taxa volumetrica maxima a 120 degC (condicoes de entrada, sem produtos)
r1_vol_max = k1_120 * C0_TG * C0_MeOH   # mol/(kgcata·s)

# Taxa na parede washcoat [mol/(m2_wall·s)]
r1_wall_max = r1_vol_max * fator_conv    # mol/(m2_wall·s)

# Numero de Damkohler: Da = r_wall * Dh / (D_TG * C0_TG)
Da = r1_wall_max * Dh / (D_TG_op * C0_TG)

# Numero de Peclet de massa
Pe_mass = u_ref * L_canal / D_TG_op

print("\n" + "-" * 70)
print("  NUMERO DE DAMKOHLER — Reacao 1 (TG + MeOH -> DG + FAME)")
print(f"  T = {T_op_C:.0f} degC | k1 = {k1_120:.3e} m6/(mol·kgcata·s)")
print("-" * 70)
print(f"  C0_TG   = {C0_TG:.2f}  mol/m3  (fracao massica TG = {w_TG})")
print(f"  C0_MeOH = {C0_MeOH:.2f}  mol/m3  (fracao massica MeOH = {w_MeOH:.2f})")
print()
print(f"  r1_vol_max  = k1 * C_TG * C_MeOH = {r1_vol_max:.3e}  mol/(kgcata·s)")
print(f"  r1_wall_max = r_vol * fator_conv  = {r1_wall_max:.3e}  mol/(m2_wall·s)")
print()
print(f"  Da = r_wall * Dh / (D_TG * C0_TG)")
print(f"     = {r1_wall_max:.3e} * {Dh:.4f} / ({D_TG_op:.3e} * {C0_TG:.2f})")
print(f"     = {Da:.4f}")
print()
if Da < 0.1:
    print("  -> Regime CINETICO: taxa na parede controla. BC de Surface Reaction e adequada.")
    print("     O gradiente difusivo nao limita — a fisica e corretamente capturada no STAR-CCM+.")
elif Da < 10:
    print("  -> Regime MISTO: cinetica e difusao sao comparaveis. Considerar washcoat model.")
else:
    print("  ATENCAO: Regime DIFUSIVO — modelo de difusao no washcoat necessario.")

# ============================================================
# 9. PECLET DE MASSA E COMPRIMENTO DE ENTRADA DIFUSIVO
# ============================================================
print("\n" + "-" * 70)
print("  PECLET DE MASSA E TRANSPORTE AXIAL/RADIAL")
print("-" * 70)
print(f"  Pe_mass (axial, TG) = u * L / D_TG = {u_ref:.3e} * {L_canal:.3e} / {D_TG_op:.3e}")
print(f"                      = {Pe_mass:.0f}  -> conveccao axial domina (Pe >> 1)")
print(f"  Comprimento de mistura radial (estimado): L_dif ~ Dh² * u / D_TG")
L_dif_radial = Dh**2 * u_ref / D_TG_op
print(f"    L_dif_radial = {L_dif_radial:.3f} m  ({L_dif_radial*1000:.1f} mm) >> L_canal = {L_canal*1000:.0f} mm")
print("  -> TG NAO se homogeneiza radialmente no canal — gradiente de concentracao")
print("     radial persistente ao longo de todo o comprimento do canal.")

# ============================================================
# 10. QUEDA DE PRESSAO (Hagen-Poiseuille, canal plano 2D)
# ============================================================
dP = 12 * mu_mix * L_canal * u_ref / Dh**2

print("\n" + "-" * 70)
print("  QUEDA DE PRESSAO (Hagen-Poiseuille, canal plano 2D)")
print("-" * 70)
print(f"  dP = 12 * mu * L * u / Dh^2 = {dP:.2f} Pa  ({dP/(P_bar*1e5)*100:.5f}% de P_op)")
print("  -> Desprezivel frente a pressao de operacao de 8 bar.")

# ============================================================
# 11. RESUMO PARA O STAR-CCM+ (Fase 2)
# ============================================================
print("\n" + "=" * 70)
print("  RESUMO — PARAMETROS PARA STAR-CCM+ (Fase 2, T = 120 degC)")
print("=" * 70)
print()
print("  [Material Properties — Multi-Component Liquid]")
print(f"    Density:           {rho_mix} kg/m3")
print(f"    Dynamic Viscosity: {mu_mix:.1e} Pa·s")
print(f"    D_TG:              {D_TG_op:.2e} m2/s  (Tabela 12, corrigida para 120 degC)")
print(f"    D_DG:              {D_DG_op:.2e} m2/s")
print(f"    D_MG:              {D_MG_op:.2e} m2/s")
print(f"    D_MeOH:            {D_MeOH_op:.2e} m2/s")
print(f"    D_FAME:            {D_FAME_op:.2e} m2/s")
print(f"    D_GL:              {D_GL_op:.2e} m2/s")
print()
print("  [Cinetica — Field Functions em STAR-CCM+ (expressoes Arrhenius)]")
print("  Modelo: r_i = k_i0 * exp(-Ea_i / (R*T)) * (C_A * C_B - (1/K_i) * C_C * C_D)")
print("  Depois converter: r_wall = r_vol * 0.02376  [mol/(m2_wall·s)]")
print()
print("  Constantes a 120 degC (extrapoladas via Arrhenius):")
print(f"    k1(120 degC) = {k1_120:.3e}  m6/(mol·kgcata·s)")
print(f"    k2(120 degC) = {k2_120:.3e}  m6/(mol·kgcata·s)")
print(f"    k3(120 degC) = {k3_120:.3e}  m6/(mol·kgcata·s)")
print(f"    K1_eq = {K1_eq}  |  K2_eq = {K2_eq}  |  K3_eq = {K3_eq}")
print()
print("  [Expressoes para Field Functions no STAR-CCM+]")
print("  k1_T = 1.26e-2 * exp(-64600 / (8.314 * $$Temperature))")
print("  k2_T = 8.88e-6 * exp(-31800 / (8.314 * $$Temperature))")
print("  k3_T = 1.28e-7 * exp(-17000 / (8.314 * $$Temperature))")
print()
print("  [Numero de Damkohler]")
print(f"    Da = {Da:.4f}  (<< 1 = regime cinetico — BC de Surface Reaction e adequada)")
print()
print("  [Termodinamica da Reacao]")
print("    DeltaH_rxn ~ 0 J/mol (Allain 2015: reacoes praticamente termoneuras)")
print("    Tratamento isoterimco justificado — fonte termica da reacao desprezivel.")
print()
print("  [Fator de conversao de taxa (kgcata → m2_wall)]")
print(f"    rho_washcoat = {rho_cat:.0f} kg/m3  |  delta_washcoat = {delta_washcoat*1e6:.0f} um")
print(f"    Fator = {fator_conv:.5f}  kgcata/m2_wall")
print("    r_wall = r_vol * 0.02376")
print()
print("  [Inlet Conditions (6:1 molar MeOH:oleo)]")
print(f"    MassFraction_TG   = {w_TG:.2f}")
print(f"    MassFraction_MeOH = {w_MeOH:.2f}")
print(f"    Temperature: {T_op_K:.2f} K  ({T_op_C:.0f} degC)")
print(f"    Velocity:    1.0e-3 m/s  (Re = {Re_ref:.4f})")
print()
print("  [ATENCAO CRITICA]")
print("    T=120 degC e EXTRAPOLACAO alem da faixa experimental de Allain (140-220 degC).")
print(f"    Cinética a 120 degC e ~{k1_185/k1_120:.0f}x mais lenta que a 185 degC (reacao 1).")
print("    Mencionar esta limitacao explicitamente na dissertacao.")
print("=" * 70)
