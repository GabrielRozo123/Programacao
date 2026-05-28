"""
Modelo Algébrico - Misturador Estático 18''
Clarificação de Xarope - Projeto 1

Responde:
  - Quantos elementos são necessários para CoV < alvo?
  - Qual a perda de carga para cada configuração?
  - Qual o diâmetro ótimo (menor ΔP com mistura adequada)?
  - Qual o ângulo ótimo das aletas?

Uso:
    python modelo_misturador_estatico.py

Ajuste os parâmetros em PARAMETROS_PROJETO antes de rodar.
"""

import math
import itertools

# =============================================================================
# PARÂMETROS DO PROJETO — AJUSTAR CONFORME DADOS DO MARCOS ITO
# =============================================================================
PARAMETROS_PROJETO = {
    # --- Fluidos ---
    "rho_caldo":     1050.0,   # [kg/m³]  CONFIRMAR (ver reunião)
    "mu_caldo":      0.001,    # [Pa·s]   1 cP
    "rho_polimero":  1050.0 * 1.35,  # [kg/m³]  35% maior
    "mu_polimero":   0.040,    # [Pa·s]   40 cP
    "fracao_polimero": 0.05,   # [-]      fração volumétrica do polímero

    # --- Geometria base ---
    "D_base":        0.4445,   # [m]      18'' Schedule 40
    "H_disponivel":  3.5,      # [m]      altura disponível na instalação — CONFIRMAR

    # --- Vazão ---
    "Q":             0.10,     # [m³/s]   CONFIRMAR (ex: 360 m³/h = 0.1 m³/s)

    # --- Critério de mistura ---
    "CoV_alvo":      0.05,     # [-]      5% = mistura excelente
    "CoV_inicial":   1.0,      # [-]      sem mistura = 1.0

    # --- Comprimentos fixos (entrada + saída) ---
    "L_entrada":     0.50,     # [m]      trecho reto antes das aletas
    "L_saida":       0.40,     # [m]      trecho reto após as aletas

    # --- Tensão superficial (para número de Weber) ---
    "sigma":         0.07,     # [N/m]    caldo aquoso ~70 mN/m
}

# =============================================================================
# CORRELAÇÕES FÍSICAS
# =============================================================================

def reynolds(rho, V, D, mu):
    """Número de Reynolds."""
    return rho * V * D / mu

def fator_atrito(Re):
    """Fator de Darcy-Weisbach. Blasius (turbulento) ou Hagen-Poiseuille (laminar)."""
    if Re < 2300:
        return 64.0 / Re                    # laminar
    elif Re < 4000:
        # interpolação transição
        f_lam = 64.0 / Re
        f_turb = 0.316 / (Re ** 0.25)
        t = (Re - 2300) / 1700.0
        return f_lam * (1 - t) + f_turb * t
    else:
        return 0.316 / (Re ** 0.25)         # Blasius (turbulento, Re < 100.000)
        # Para Re > 100.000 usar: return 0.184 / Re**0.2   (Filonenko)

def velocidade(Q, D):
    """Velocidade média na seção circular."""
    return Q / (math.pi * D**2 / 4.0)

def fator_Z(angulo_graus):
    """
    Multiplicador de perda de carga do misturador (Z) em função do ângulo das aletas.

    Correlação empírica para misturadores helicoidais tipo Kenics/SMX:
      Z = Z_ref × (θ / θ_ref)^n

    Referência típica: θ_ref = 90°, Z_ref = 5 (turbulento)
    Expoente n ≈ 1.5 (empírico para misturadores helicoidais)

    Interpretação:
      θ pequeno → aleta quase paralela ao fluxo → menos resistência, mas
                  caminhos preferenciais (by-pass) → precisa mais elementos
      θ grande  → aleta transversal → muito resistência → mistura rápida
                  mas ΔP alto
    """
    Z_ref = 5.0   # turbulento, ângulo 90°
    n     = 1.5
    theta_ref = 90.0
    return Z_ref * (angulo_graus / theta_ref) ** n

def cov_reducao_por_elemento(angulo_graus, Re):
    """
    Fator de redução do CoV por elemento (r): CoV_N = CoV_0 × r^N

    Em regime turbulento, cada elemento reduz o CoV em (1-r)×100%.

    Correlação semi-empírica:
      - θ maior → melhor mistura por elemento → r menor
      - Re maior → melhor mistura por elemento → r menor
      - Base: Kenics 90° turbulento → r ≈ 0.30 (reduz 70% por elemento)
    """
    r_ref = 0.30          # Kenics 90°, turbulento
    # efeito do ângulo: ângulo menor → r mais próximo de 1 (pior mistura)
    fator_angulo = (90.0 / angulo_graus) ** 0.4
    # efeito do Re: maior Re → melhor mistura → reduz r levemente
    fator_Re = (10000.0 / max(Re, 10000.0)) ** 0.1
    r = r_ref * fator_angulo * fator_Re
    return min(r, 0.95)   # limitado: cada elemento sempre faz alguma coisa

def n_elementos_necessarios(CoV_alvo, CoV_inicial, r):
    """Número mínimo de elementos para atingir CoV_alvo."""
    if r >= 1.0:
        return float('inf')
    return math.ceil(math.log(CoV_alvo / CoV_inicial) / math.log(r))

def perda_carga_misturador(Q, D, angulo, N, params):
    """
    Perda de carga total do misturador [Pa].

    ΔP_total = ΔP_misturador + ΔP_trechos_retos

    ΔP_misturador = Z × f × (N × L_elem / D) × (ρV²/2)
    L_elem ≈ D (cada elemento tem comprimento ≈ diâmetro, padrão Kenics)
    """
    rho = params["rho_caldo"]
    mu  = params["mu_caldo"]
    V   = velocidade(Q, D)
    Re  = reynolds(rho, V, D, mu)
    f   = fator_atrito(Re)
    Z   = fator_Z(angulo)
    L_elem = D  # comprimento de cada elemento ≈ D

    # Seção com aletas
    dP_mist = Z * f * (N * L_elem / D) * (rho * V**2 / 2.0)

    # Trechos retos (entrada + saída)
    L_reto = params["L_entrada"] + params["L_saida"]
    dP_reto = f * (L_reto / D) * (rho * V**2 / 2.0)

    return dP_mist + dP_reto, Re, V, f, Z

def comprimento_total(N, D, params):
    """Comprimento total da instalação [m]."""
    return params["L_entrada"] + N * D + params["L_saida"]

def weber(rho, V, d_bolha, sigma):
    """Número de Weber da bolha/gota."""
    return rho * V**2 * d_bolha / sigma

# =============================================================================
# ANÁLISE PRINCIPAL
# =============================================================================

def analisar_configuracao(D, angulo, params, verbose=True):
    """Analisa uma configuração (D, ângulo) e retorna métricas."""
    Q        = params["Q"]
    H_max    = params["H_disponivel"]
    CoV_alv  = params["CoV_alvo"]
    CoV_ini  = params["CoV_inicial"]

    V   = velocidade(Q, D)
    rho = params["rho_caldo"]
    mu  = params["mu_caldo"]
    Re  = reynolds(rho, V, D, mu)
    r   = cov_reducao_por_elemento(angulo, Re)
    N_min = n_elementos_necessarios(CoV_alv, CoV_ini, r)

    # Quantos elementos cabem na altura disponível?
    N_max = int((H_max - params["L_entrada"] - params["L_saida"]) / D)
    N_max = max(N_max, 0)

    if N_min == float('inf') or N_min > N_max:
        viavel = False
        N_usar = N_max
    else:
        viavel = True
        N_usar = int(N_min)

    if N_usar < 1:
        return None  # não cabe nenhum elemento

    dP, Re, V, f, Z = perda_carga_misturador(Q, D, angulo, N_usar, params)
    L_tot = comprimento_total(N_usar, D, params)
    CoV_final = CoV_ini * (r ** N_usar)

    return {
        "D_m":       D,
        "angulo":    angulo,
        "V_ms":      V,
        "Re":        Re,
        "regime":    "Turbulento" if Re > 4000 else ("Transição" if Re > 2300 else "Laminar"),
        "f":         f,
        "Z":         Z,
        "r":         r,
        "N_min_mix": N_min,
        "N_max_alt": N_max,
        "N_usado":   N_usar,
        "dP_Pa":     dP,
        "dP_bar":    dP / 1e5,
        "dP_mca":    dP / (rho * 9.81),  # metros de coluna d'água
        "L_total_m": L_tot,
        "CoV_final": CoV_final,
        "viavel":    viavel,
    }

def otimizacao(params):
    """
    Varre o espaço de (D, ângulo) e encontra a configuração ótima:
    menor ΔP que satisfaz CoV < alvo dentro da altura disponível.
    """
    diametros = [0.3556, 0.4064, 0.4445, 0.5080, 0.6096, 0.7112]  # 14'',16'',18'',20'',24'',28''
    angulos   = [30, 45, 60, 75, 90]  # graus

    resultados = []
    for D, ang in itertools.product(diametros, angulos):
        res = analisar_configuracao(D, ang, params, verbose=False)
        if res and res["viavel"]:
            resultados.append(res)

    if not resultados:
        print("Nenhuma configuração viável encontrada. Revisar H_disponivel ou Q.")
        return None

    # Ordenar por menor ΔP
    resultados.sort(key=lambda x: x["dP_Pa"])
    return resultados

# =============================================================================
# RELATÓRIO
# =============================================================================

def imprimir_relatorio(params):
    print("=" * 70)
    print("  MODELO ALGÉBRICO — MISTURADOR ESTÁTICO")
    print("  Clarificação de Xarope — Projeto 1")
    print("=" * 70)
    print(f"\n  Fluido (caldo): rho={params['rho_caldo']} kg/m³, mu={params['mu_caldo']*1000:.1f} cP")
    print(f"  Vazão:          Q={params['Q']*3600:.1f} m³/h  ({params['Q']:.4f} m³/s)")
    print(f"  Altura máx.:    H={params['H_disponivel']:.2f} m")
    print(f"  Alvo mistura:   CoV < {params['CoV_alvo']*100:.0f}%")

    # --- Análise do diâmetro 18'' (base) ---
    print("\n" + "-" * 70)
    print("  ANÁLISE BASE — D = 18'' (444,5 mm)")
    print("-" * 70)
    print(f"  {'Ângulo':>8} {'Re':>10} {'Regime':>12} {'N_mín':>7} {'N_cabe':>7} "
          f"{'N_usar':>7} {'ΔP [Pa]':>10} {'ΔP [mca]':>10} {'CoV':>8} {'Viável':>8}")
    print("  " + "-" * 68)
    for ang in [30, 45, 60, 75, 90]:
        r = analisar_configuracao(0.4445, ang, params, verbose=False)
        if r:
            print(f"  {r['angulo']:>7}° {r['Re']:>10.0f} {r['regime']:>12} "
                  f"{r['N_min_mix']:>7} {r['N_max_alt']:>7} {r['N_usado']:>7} "
                  f"{r['dP_Pa']:>10.1f} {r['dP_mca']:>10.4f} "
                  f"{r['CoV_final']:>8.4f} {'✓' if r['viavel'] else '✗':>8}")

    # --- Efeito do diâmetro (melhor ângulo de 90°) ---
    print("\n" + "-" * 70)
    print("  EFEITO DO DIÂMETRO — ângulo fixo = 90° (turbulento ideal)")
    print("-" * 70)
    nomes_D = {0.3556:"14''", 0.4064:"16''", 0.4445:"18''",
               0.5080:"20''", 0.6096:"24''", 0.7112:"28''"}
    print(f"  {'Diâm':>8} {'V [m/s]':>9} {'Re':>10} {'N_mín':>7} {'N_cabe':>7} "
          f"{'ΔP [Pa]':>10} {'ΔP [mca]':>10} {'Viável':>8}")
    print("  " + "-" * 68)
    for D, nome in nomes_D.items():
        r = analisar_configuracao(D, 90, params, verbose=False)
        if r:
            print(f"  {nome:>7} {r['V_ms']:>9.3f} {r['Re']:>10.0f} "
                  f"{r['N_min_mix']:>7} {r['N_max_alt']:>7} "
                  f"{r['dP_Pa']:>10.1f} {r['dP_mca']:>10.4f} "
                  f"{'✓' if r['viavel'] else '✗':>8}")

    # --- Otimização global ---
    print("\n" + "-" * 70)
    print("  OTIMIZAÇÃO GLOBAL — menor ΔP com CoV < alvo e H ≤ H_disponível")
    print("-" * 70)
    resultados = otimizacao(params)
    if resultados:
        print(f"  TOP 5 configurações ótimas:\n")
        print(f"  {'#':>3} {'D':>6} {'Ângulo':>8} {'N':>5} {'ΔP [Pa]':>10} "
              f"{'ΔP [mca]':>10} {'CoV':>8} {'Re':>10}")
        print("  " + "-" * 60)
        for i, r in enumerate(resultados[:5], 1):
            D_pol = r['D_m'] * 39.3701  # m → polegadas
            print(f"  {i:>3} {D_pol:>5.0f}'' {r['angulo']:>7}° {r['N_usado']:>5} "
                  f"{r['dP_Pa']:>10.1f} {r['dP_mca']:>10.4f} "
                  f"{r['CoV_final']:>8.4f} {r['Re']:>10.0f}")

        melhor = resultados[0]
        print(f"\n  → CONFIGURAÇÃO ÓTIMA:")
        D_pol = melhor['D_m'] * 39.3701
        print(f"     Diâmetro:        {D_pol:.0f}'' ({melhor['D_m']*1000:.0f} mm)")
        print(f"     Ângulo das aletas:{melhor['angulo']}°")
        print(f"     Nº de elementos: {melhor['N_usado']}")
        print(f"     Velocidade:      {melhor['V_ms']:.3f} m/s")
        print(f"     Reynolds:        {melhor['Re']:.0f} ({melhor['regime']})")
        print(f"     Perda de carga:  {melhor['dP_Pa']:.2f} Pa  "
              f"({melhor['dP_mca']:.5f} mca)  ({melhor['dP_bar']:.7f} bar)")
        print(f"     CoV final:       {melhor['CoV_final']:.4f} "
              f"({'OK' if melhor['viavel'] else 'INSUFICIENTE'})")
        print(f"     Comp. total:     {melhor['L_total_m']:.2f} m")

    # --- Nota sobre caminhos preferenciais ---
    print("\n" + "-" * 70)
    print("  NOTA: ÂNGULO vs. CAMINHO PREFERENCIAL")
    print("-" * 70)
    print("  θ pequeno (< 45°): aleta quase paralela ao fluxo")
    print("    → menor ΔP por elemento, mas fluido contorna as aletas")
    print("    → mais elementos necessários para compensar")
    print("  θ grande (> 75°): aleta transversal ao fluxo")
    print("    → maior ΔP por elemento, mistura mais intensa")
    print("    → menos elementos, mas pressão maior")
    print("  θ ≈ 60-75°: balanço ótimo para a maioria dos casos industriais")

    print("\n" + "=" * 70)
    print("  PARÂMETROS A CONFIRMAR COM MARCOS ITO:")
    print("  • Vazão (Q) real do processo")
    print("  • Altura disponível (H) na instalação")
    print("  • Densidade real do caldo")
    print("  • Ângulo das aletas nas revisões REV.2 e REV.4")
    print("=" * 70)


if __name__ == "__main__":
    imprimir_relatorio(PARAMETROS_PROJETO)
