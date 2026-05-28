"""
Modelo Algébrico - Tanque Agitado com Micronizador
Clarificação de Xarope - Projeto 2

Responde:
  - Velocidade de ascensão das microbolhas
  - Tempo de residência no tanque (altura / v_ascensão)
  - Número de Weber e regime de coalescência
  - Eficiência de incorporação estimada (modelo simplificado)
  - Quantos micronizadores e em que posição?

Referências dos modelos:
  - Ascensão de bolhas: Lei de Stokes (d < 100 µm, Re_b << 1)
  - Coalescência/breakup: S-Gamma (Lo & Rao) — implementado no Star-CCM+
  - Eficiência de flotação: modelo de Sutherland (colisão bolha-partícula)

Uso:
    python modelo_tanque_micronizador.py

Ajuste PARAMETROS_PROJETO com os dados reais quando chegarem.
"""

import math

# =============================================================================
# PARÂMETROS DO PROJETO — AJUSTAR CONFORME DADOS DO MARCOS ITO
# =============================================================================
PARAMETROS_PROJETO = {
    # --- Fluido contínuo (caldo) ---
    "rho_caldo":      1050.0,  # [kg/m³]  CONFIRMAR
    "mu_caldo":       0.001,   # [Pa·s]   1 cP

    # --- Fase dispersa (microbolhas de ar) ---
    "rho_ar":         1.2,     # [kg/m³]
    "mu_ar":          1.8e-5,  # [Pa·s]
    "d_bolha_m":      30e-6,   # [m]      diâmetro inicial das bolhas (30 µm)
    "d_bolha_max":    80e-6,   # [m]      limite máximo aceito (80 µm = boa flotação)
    "sigma":          0.07,    # [N/m]    tensão superficial caldo/ar

    # --- Geometria do tanque (PLACEHOLDER — aguardando dados) ---
    "H_tanque":       3.0,     # [m]      altura útil do tanque  CONFIRMAR
    "D_tanque":       2.0,     # [m]      diâmetro do tanque     CONFIRMAR
    "H_injecao":      0.1,     # [m]      altura de injeção do micronizador (fundo)

    # --- Micronizador ---
    "Q_ar_total":     0.005,   # [m³/s]   vazão de ar total injetada  CONFIRMAR
    "N_micronizadores": 4,     # [-]      número de micronizadores    CONFIRMAR
    "d_orificio":     0.001,   # [m]      diâmetro do orifício (1 mm) CONFIRMAR

    # --- Fração de vazio ---
    "alpha_ar":       0.05,    # [-]      fração volumétrica de ar (5%)  CONFIRMAR

    # --- Critério de eficiência ---
    "efic_alvo":      0.80,    # [-]      80% das bolhas incorporadas ativamente

    # --- Gravidade ---
    "g":              9.81,    # [m/s²]
}

# =============================================================================
# CORRELAÇÕES FÍSICAS — MICROBOLHAS
# =============================================================================

def velocidade_stokes(d, rho_L, rho_G, mu_L, g=9.81):
    """
    Velocidade terminal de ascensão pela Lei de Stokes [m/s].
    Válida para Re_bolha << 1 (d < ~100 µm em água).

    v_b = d² (ρ_L - ρ_G) g / (18 µ_L)
    """
    return (d**2 * (rho_L - rho_G) * g) / (18.0 * mu_L)

def reynolds_bolha(d, v_b, rho_L, mu_L):
    """Número de Reynolds da bolha."""
    return rho_L * v_b * d / mu_L

def weber_bolha(d, v_rel, rho_L, sigma):
    """
    Número de Weber da bolha.
    We >> 1 → bolha se deforma/quebra
    We << 1 → tensão superficial mantém bolha esférica e estável
    """
    return rho_L * v_rel**2 * d / sigma

def weber_critico_coalescencia():
    """
    We crítico para coalescência de bolhas em turbulência.
    Abaixo deste valor, a tensão superficial impede deformação e
    facilita a coalescência.
    Referência: Luo & Svendsen (1996) ≈ 0.5–2.0
    """
    return 1.0

def tempo_residencia(H_tanque, H_injecao, v_ascensao):
    """Tempo médio que a bolha leva para atravessar o tanque [s]."""
    return (H_tanque - H_injecao) / v_ascensao

def diametro_critico_stokes(v_b, rho_L, rho_G, mu_L, g=9.81):
    """Diâmetro de bolha que teria velocidade de ascensão v_b [m]."""
    return math.sqrt(18.0 * mu_L * v_b / ((rho_L - rho_G) * g))

def eficiencia_colisao_sutherland(d_bolha, d_particula, v_ascensao):
    """
    Eficiência de colisão bolha-partícula (modelo de Sutherland simplificado).
    E_c ≈ (3/2) × (d_p / d_b)²

    Para flotação eficiente: d_partícula ≈ d_bolha → E_c → máximo
    """
    return 1.5 * (d_particula / d_bolha)**2

def vazao_ar_por_micronizador(Q_total, N_mic):
    return Q_total / N_mic

def velocidade_orificio(Q_mic, d_orificio):
    """Velocidade de saída no orifício do micronizador [m/s]."""
    A = math.pi * d_orificio**2 / 4.0
    return Q_mic / A

def diametro_bolha_orificio(d_orificio, v_orificio, rho_L, sigma, g=9.81):
    """
    Estimativa do diâmetro de bolha gerado no orifício (correlação empírica).

    d_bolha ≈ 0.76 × d_orifício × (We_orifício)^(-0.5)
    para We > 1 (regime de jato)

    We_or = rho_L × v_or² × d_or / sigma

    Ref: Leibson et al. (1956), adaptado.
    """
    We_or = rho_L * v_orificio**2 * d_orificio / sigma
    if We_or < 1.0:
        # regime de gotejamento: bolha ≈ tamanho do orifício
        d_b = d_orificio * 1.5
    else:
        # regime de jato / turbulento: bolhas menores
        d_b = 0.76 * d_orificio * We_or**(-0.5)
    return max(d_b, 10e-6)   # mínimo 10 µm

# =============================================================================
# EFICIÊNCIA DE INCORPORAÇÃO
# =============================================================================

def eficiencia_incorporacao(alpha, t_res, d_bolha, params):
    """
    Estimativa da Eficiência de Incorporação de Microbolhas.

    Modelo simplificado:
      E_inc = (1 - taxa_coalescência) × (cobertura_volumétrica)

    Taxa de coalescência: função do We e da fração de vazio (α)
      - We << 1: tensão superficial estabiliza bolhas → coalescência lenta
      - α alto (> 15%): muitas colisões → coalescência rápida

    Cobertura volumétrica: fração do tanque com bolhas ativas
    """
    rho_L = params["rho_caldo"]
    sigma = params["sigma"]
    v_b   = velocidade_stokes(d_bolha, rho_L, params["rho_ar"], params["mu_caldo"])

    # Velocidade relativa entre bolhas (estimativa: 10% da velocidade de ascensão)
    v_rel = 0.1 * v_b
    We    = weber_bolha(d_bolha, v_rel, rho_L, sigma)
    We_cr = weber_critico_coalescencia()

    # Taxa de coalescência relativa
    if We < We_cr:
        # bolhas estáveis, pouca coalescência
        taxa_coal = alpha * 0.3    # 30% máx por α
    else:
        # bolhas instáveis, coalescência intensa
        taxa_coal = alpha * 0.7

    taxa_coal = min(taxa_coal, 0.95)

    # Cobertura: bolhas menores → mais superfície → melhor incorporação
    d_ref = 80e-6  # referência (80 µm = aceitável)
    cob   = min(1.0, (d_ref / d_bolha) ** 0.5)

    efic = (1.0 - taxa_coal) * cob
    return efic, We, taxa_coal

# =============================================================================
# ANÁLISE DE POSIÇÃO E NÚMERO DE MICRONIZADORES
# =============================================================================

def analisar_micronizador(N_mic, posicoes_radiais_m, params):
    """
    Analisa configuração de micronizadores no tanque.

    posicoes_radiais_m: lista de raios [m] onde cada micronizador é instalado
    """
    Q_mic = vazao_ar_por_micronizador(params["Q_ar_total"], N_mic)
    v_or  = velocidade_orificio(Q_mic, params["d_orificio"])
    d_bol = diametro_bolha_orificio(
        params["d_orificio"], v_or,
        params["rho_caldo"], params["sigma"]
    )
    v_asc = velocidade_stokes(
        d_bol, params["rho_caldo"], params["rho_ar"], params["mu_caldo"]
    )
    Re_b  = reynolds_bolha(d_bol, v_asc, params["rho_caldo"], params["mu_caldo"])
    t_res = tempo_residencia(
        params["H_tanque"], params["H_injecao"], v_asc
    )
    efic, We, taxa_coal = eficiencia_incorporacao(
        params["alpha_ar"], t_res, d_bol, params
    )

    # Área coberta por micronizador (aproximação circular)
    R_tanque = params["D_tanque"] / 2.0
    A_tanque = math.pi * R_tanque**2
    A_por_mic = A_tanque / N_mic  # área ideal por micronizador

    return {
        "N_mic":       N_mic,
        "Q_mic_m3s":   Q_mic,
        "Q_mic_lmin":  Q_mic * 1000 * 60,
        "v_orificio":  v_or,
        "d_bolha_um":  d_bol * 1e6,
        "d_bolha_ok":  d_bol <= params["d_bolha_max"],
        "Re_bolha":    Re_b,
        "valido_stokes": Re_b < 1.0,
        "v_ascensao":  v_asc * 1000,  # mm/s
        "t_res_s":     t_res,
        "We_bolha":    We,
        "taxa_coal":   taxa_coal,
        "efic_inc":    efic,
        "efic_ok":     efic >= params["efic_alvo"],
        "A_por_mic":   A_por_mic,
    }

# =============================================================================
# RELATÓRIO
# =============================================================================

def imprimir_relatorio(params):
    print("=" * 70)
    print("  MODELO ALGÉBRICO — TANQUE COM MICRONIZADOR")
    print("  Clarificação de Xarope — Projeto 2")
    print("=" * 70)
    print(f"\n  Fluido:         rho={params['rho_caldo']} kg/m³, mu={params['mu_caldo']*1000:.1f} cP")
    print(f"  Tanque:         H={params['H_tanque']} m, D={params['D_tanque']} m")
    print(f"  Ar total:       Q={params['Q_ar_total']*1000*60:.1f} L/min")
    print(f"  Alvo efic.:     {params['efic_alvo']*100:.0f}%")

    # --- Física das microbolhas ---
    print("\n" + "-" * 70)
    print("  FÍSICA DAS MICROBOLHAS — Lei de Stokes")
    print("-" * 70)
    for d_um in [10, 20, 30, 50, 80, 100, 200]:
        d = d_um * 1e-6
        v = velocidade_stokes(d, params["rho_caldo"], params["rho_ar"], params["mu_caldo"])
        Re = reynolds_bolha(d, v, params["rho_caldo"], params["mu_caldo"])
        We = weber_bolha(d, v*0.1, params["rho_caldo"], params["sigma"])
        t  = tempo_residencia(params["H_tanque"], params["H_injecao"], v)
        valido = "✓" if Re < 1.0 else "aprox."
        print(f"  d={d_um:>4} µm | v={v*1000:>7.3f} mm/s | Re={Re:>7.4f} {valido:>7} "
              f"| We={We:>7.4f} | t_res={t:>6.1f} s  ({t/60:.1f} min)")

    print(f"\n  Stokes válido (Re_b < 1) para d < ~100 µm — adequado para esse processo.")
    print(f"  We << 1 → tensão superficial estabiliza as bolhas → S-Gamma: regime viscoso")

    # --- Efeito do número de micronizadores ---
    print("\n" + "-" * 70)
    print("  EFEITO DO NÚMERO DE MICRONIZADORES")
    print("-" * 70)
    print(f"  {'N_mic':>6} {'Q/mic [L/min]':>14} {'d_bol [µm]':>11} {'v_asc [mm/s]':>13} "
          f"{'t_res [s]':>10} {'Efic. Inc.':>11} {'OK':>4}")
    print("  " + "-" * 68)
    for N in [1, 2, 3, 4, 5, 6, 8, 10, 12]:
        R = analisar_micronizador(N, [], params)
        print(f"  {R['N_mic']:>6} {R['Q_mic_lmin']:>14.3f} {R['d_bolha_um']:>11.1f} "
              f"{R['v_ascensao']:>13.3f} {R['t_res_s']:>10.1f} "
              f"{R['efic_inc']*100:>10.1f}% {'✓' if R['efic_ok'] else '✗':>4}")

    # --- Configuração recomendada ---
    print("\n" + "-" * 70)
    print("  CONFIGURAÇÃO RECOMENDADA")
    print("-" * 70)
    N_ot = params["N_micronizadores"]
    R = analisar_micronizador(N_ot, [], params)
    print(f"  Número de micronizadores: {R['N_mic']}")
    print(f"  Vazão por micronizador:   {R['Q_mic_lmin']:.3f} L/min")
    print(f"  Diâmetro de bolha gerado: {R['d_bolha_um']:.1f} µm "
          f"({'≤ 80µm ✓' if R['d_bolha_ok'] else '> 80µm ✗ — reduzir Q ou aumentar N'})")
    print(f"  Validade de Stokes:       {'Re_b={:.4f} ✓'.format(R['Re_bolha']) if R['valido_stokes'] else 'Re_b={:.2f} — usar correlação de Schiller-Naumann'.format(R['Re_bolha'])}")
    print(f"  Velocidade de ascensão:   {R['v_ascensao']:.3f} mm/s")
    print(f"  Tempo de residência:      {R['t_res_s']:.1f} s  ({R['t_res_s']/60:.2f} min)")
    print(f"  Número de Weber:          {R['We_bolha']:.5f}  (< 1 = estável ✓)")
    print(f"  Taxa de coalescência est.:{R['taxa_coal']*100:.1f}%")
    print(f"  Eficiência de incorporação:{R['efic_inc']*100:.1f}% "
          f"({'≥ alvo ✓' if R['efic_ok'] else '< alvo ✗'})")

    # --- Posicionamento ---
    print("\n" + "-" * 70)
    print("  POSICIONAMENTO DOS MICRONIZADORES NO TANQUE")
    print("-" * 70)
    R_t = params["D_tanque"] / 2.0
    N   = params["N_micronizadores"]
    print(f"  Raio do tanque: {R_t:.2f} m")
    print(f"  Disposição radial sugerida (raios equidistantes):")
    for i in range(1, N + 1):
        r_mic = R_t * (i / (N + 1))
        ang   = 360.0 * (i - 1) / N
        print(f"    Mic {i}: r = {r_mic:.3f} m, θ = {ang:.0f}°  "
              f"(raio = {r_mic/R_t*100:.0f}% do raio total)")
    print(f"\n  Nota: disposição em anel a r ≈ {0.6*R_t:.2f} m (60% do raio) é típica")
    print(f"  para maximizar cobertura e minimizar zonas mortas.")

    # --- Conexão com Star-CCM+ ---
    print("\n" + "-" * 70)
    print("  MODELO STAR-CCM+ RECOMENDADO")
    print("-" * 70)
    print("  Fase contínua:   Eulerian (caldo)")
    print("  Fase dispersa:   Eulerian (bolhas de ar) — tamanho inicial calculado acima")
    print("  Distribuição:    S-Gamma PSD")
    print("    ├─ Entrainment: geração de bolhas no micronizador")
    print("    ├─ Coalescence: regime viscoso (We << 1, Stokes)")
    print("    └─ Breakup:     desativado inicialmente (We << 1 → bolhas estáveis)")
    print("  Turbulência:     k-ε Realizable (melhor para tanques com ascensão livre)")
    print("  Gravidade:       ativada (flotação contra-corrente)")
    print("  Pós-proc.:       campo α (fração de vazio), campo d_m (diâm. médio),")
    print("                   eficiência de incorporação por integração volumétrica")

    print("\n" + "=" * 70)
    print("  PARÂMETROS A CONFIRMAR COM MARCOS ITO:")
    print("  • Geometria real do tanque (H, D)")
    print("  • Vazão de ar total e por micronizador")
    print("  • Diâmetro e geometria real do orifício do micronizador")
    print("  • Número e posição atual dos micronizadores")
    print("  • Fração de vazio desejada no tanque")
    print("  • Critério quantitativo de eficiência de incorporação")
    print("=" * 70)


if __name__ == "__main__":
    imprimir_relatorio(PARAMETROS_PROJETO)
