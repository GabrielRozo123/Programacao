#!/usr/bin/env python3
"""
Memorial de calculo -- coluna de bolhas de grande diametro, hidrodinamica e
quimissorcao de CO2 em NaOH.

FASE 1 -- hidrodinamica, ancorada em:
    Ferrario, Varallo, Besagni & Mereu (2025)
    "Influence of the gas phase on a large-scale bubble column fluid dynamics:
     Gas holdup, flow regime transitions, and bubble size distributions"
    Chemical Engineering Science 302, 120792.  ACESSO ABERTO (CC BY).

    Coluna d_c = 0,24 m, H_c = 5,3 m, H_0 = 3,0 m (AR = 12,5), batelada,
    agua de torneira, ar OU CO2, T = 295,15 K, distribuidor aranha de 6 bracos
    com furos de 2 mm.

FASE 2 -- absorcao com reacao, ancorada em:
    Darmana, Henket, Deen & Kuipers (2007)
    "Detailed modelling of hydrodynamics, mass transfer and chemical reactions
     in a bubble column using a discrete bubble model: chemisorption of CO2
     into NaOH solution"
    Chemical Engineering Science 62, 2556-2575.

    Todo o fechamento fisico-quimico vem do Apendice A daquele artigo.

O ponto pedagogico do estudo esta no numero de Hatta: ele decide se o projeto
do reator e governado por VOLUME ou por AREA INTERFACIAL, e ele muda de regime
dentro da faixa de concentracao usada no proprio experimento.
"""

import math

# ============================================================================
# FASE 1 -- COLUNA DE FERRARIO et al. (2025)
# ============================================================================

D_C = 0.24            # [m] diametro interno
H_C = 5.3             # [m] altura da coluna
H_0 = 3.0             # [m] altura inicial de liquido acima do distribuidor
D_HOLE = 0.002        # [m] diametro dos furos do distribuidor aranha
N_ARMS = 6            # bracos do distribuidor
T_EXP = 295.15        # [K]

# velocidades superficiais em que as BSD foram medidas [m/s]
UG_EXP = [0.0037, 0.0076, 0.0115, 0.0154, 0.0193, 0.0223]

# ajuste de Wallis (Richardson-Zaki, n = 2), Tabela 9 do artigo
U_INF = {"ar": 0.314, "CO2": 0.292}          # [m/s] velocidade terminal
# velocidade de enxame no regime homogeneo, Tabela 8
U_SWARM = {"ar": 0.282, "CO2": 0.257}        # [m/s]
# transicao de regime, Tabela 7 (metodo do enxame)
TRANSICAO = {"ar": (0.028, 0.098), "CO2": (0.028, 0.110)}   # (Ug, eps)

D_CRIT_LIFT = 0.0052  # [m] diametro critico de inversao de sinal da forca de
                      #     sustentacao (Ziegenhein & Lucas, 2019)

# propriedades, agua a 295 K
RHO_L = 998.0         # [kg/m3]
MU_L = 9.6e-4         # [Pa.s]
SIGMA = 0.0724        # [N/m]
G = 9.81


def holdup_wallis(ug, u_inf):
    """Holdup de gas no regime homogeneo, a partir do ajuste de Wallis.

    J_drift = u_inf * eps * (1 - eps)^2   e, em batelada, J_drift = Ug(1-eps).
    Logo   Ug = u_inf * eps * (1 - eps).  Raiz fisica (a menor).
    """
    disc = 1.0 - 4.0 * ug / u_inf
    if disc < 0:
        return float("nan")
    return (1.0 - math.sqrt(disc)) / 2.0


def diametro_adimensional():
    """Criterio de coluna de grande diametro (Kataoka & Ishii, 1987)."""
    return D_C / math.sqrt(SIGMA / (G * (RHO_L - 1.2)))


def bolha_de_formacao(d0):
    """Diametro de bolha no desprendimento do furo -- lei de Tate.

    Balanco entre empuxo e tensao superficial no orificio, valido no regime
    de borbulhamento (We baixo), que e o caso aqui:

        d_b = ( 6 d0 sigma / (g (rho_l - rho_g)) )^(1/3)
    """
    return (6.0 * d0 * SIGMA / (G * (RHO_L - 1.2))) ** (1.0 / 3.0)


def weber_orificio(q_gas, n_furos, d0, rho_g=1.2):
    """Weber no orificio -- separa borbulhamento de jateamento."""
    a = n_furos * math.pi / 4 * d0 ** 2
    u = q_gas / a
    return rho_g * u ** 2 * d0 / SIGMA, u


def dissipacao(ug):
    """Taxa de dissipacao turbulenta media na coluna [m2/s3].

    Em coluna de bolhas em batelada, toda a potencia entra pelo empuxo do
    gas: P/m = g * U_g. E a estimativa padrao (Kawase & Moo-Young).
    """
    return G * ug


def d_critico_martinez_bazan(eps, beta=8.2):
    """Diametro critico de quebra turbulenta (Martinez-Bazan et al., 1999).

    Abaixo dele a tensao turbulenta nao vence a tensao superficial e a bolha
    NAO quebra:
        d_c = (12 sigma / (beta rho_l))^(3/5) * eps^(-2/5)
    """
    return (12.0 * SIGMA / (beta * RHO_L)) ** 0.6 * eps ** (-0.4)


def satelite_de_pinchoff(d_b):
    """Bolha satelite tipica no destacamento -- ordem de d_b/7."""
    return d_b / 7.0


def fase1():
    print("=" * 76)
    print("FASE 1 -- HIDRODINAMICA   (Ferrario et al., Chem. Eng. Sci. 302, 2025)")
    print("=" * 76)
    print(f"  Diametro interno            {D_C:8.3f} m")
    print(f"  Altura da coluna            {H_C:8.2f} m")
    print(f"  Liquido acima do sparger    {H_0:8.2f} m     AR = {H_0/D_C:.1f}")
    print(f"  Volume de liquido           {math.pi/4*D_C**2*H_0*1000:8.1f} L")
    print(f"  Distribuidor                aranha, {N_ARMS} bracos, furos de "
          f"{D_HOLE*1000:.0f} mm")
    print("-" * 76)
    dh = diametro_adimensional()
    print(f"  D*_H = {dh:.1f}   (criterio > 52)   "
          f"{'grande diametro -- SEM regime de slug' if dh > 52 else 'REVISAR'}")
    print(f"  Artigo reporta D*_H = 88,13")
    print("=" * 76)

    print(f"\n{'Ug':>9s}{'eps ar':>10s}{'eps CO2':>10s}{'u_swarm':>11s}"
          f"{'Q_gas':>10s}{'regime':>16s}")
    print(f"{'[m/s]':>9s}{'[-]':>10s}{'[-]':>10s}{'ar [m/s]':>11s}"
          f"{'[NL/min]':>10s}")
    print("-" * 76)
    a = math.pi / 4 * D_C ** 2
    for ug in UG_EXP:
        e_ar = holdup_wallis(ug, U_INF["ar"])
        e_co2 = holdup_wallis(ug, U_INF["CO2"])
        q = ug * a * 60000.0                     # L/min
        reg = "homogeneo" if ug < TRANSICAO["ar"][0] else "heterogeneo"
        print(f"{ug:9.4f}{e_ar:10.4f}{e_co2:10.4f}{ug/e_ar:11.3f}"
              f"{q:10.1f}{reg:>16s}")
    print("-" * 76)
    ugt, epst = TRANSICAO["ar"]
    print(f"  TRANSICAO medida:  Ug = {ugt} m/s,  eps = {epst} (ar) / "
          f"{TRANSICAO['CO2'][1]} (CO2)")
    print("  Toda a faixa das BSD esta ABAIXO da transicao -> regime")
    print("  poli-disperso homogeneo. Isso simplifica muito o CFD: nao e")
    print("  preciso resolver estruturas induzidas por coalescencia.")
    print("=" * 76)

    print("\nO QUE UM MODELO DE UMA UNICA BOLHA NAO CONSEGUE REPRODUZIR")
    print("-" * 76)
    print(f"  A BSD medida e BIMODAL abaixo de Ug = 0,0154 m/s:")
    print(f"     pico 1   d_eq = 0,67 mm")
    print(f"     pico 2   d_eq = 4 a 6 mm")
    print(f"  E o sinal da forca de sustentacao inverte em d = "
          f"{D_CRIT_LIFT*1000:.1f} mm:")
    print("     bolha pequena -> sustentacao POSITIVA -> migra para a PAREDE")
    print("     bolha grande  -> sustentacao NEGATIVA -> migra para o CENTRO")
    print("-" * 76)
    db = bolha_de_formacao(D_HOLE)
    print("-" * 76)
    print(f"  LEI DE TATE no furo de {D_HOLE*1000:.0f} mm:  d_b = {db*1000:.2f} mm")
    print(f"     -> cai dentro do segundo pico medido (4 a 6 mm).")
    print("     O distribuidor explica a populacao GRANDE. A populacao de")
    print("     0,67 mm nao vem do furo -- vem de quebra a jusante.")
    a = math.pi / 4 * D_C ** 2
    print(f"\n{'Ug':>9s}{'Q real':>11s}{'u_furo':>10s}{'We':>9s}{'regime':>16s}")
    print(f"{'[m/s]':>9s}{'[L/s]':>11s}{'[m/s]':>10s}{'[-]':>9s}")
    for ug in (UG_EXP[0], UG_EXP[-1]):
        q = ug * a                                  # [m3/s] na coluna
        we, u = weber_orificio(q, 60, D_HOLE)       # 60 furos presumidos
        reg = "borbulhamento" if we < 2 else "jateamento"
        print(f"{ug:9.4f}{q*1000:11.3f}{u:10.2f}{we:9.3f}{reg:>16s}")
    print("  (60 furos presumidos: 6 bracos x 10 furos, a confirmar na Fig. 3)")
    print("  We << 2 nos dois extremos -> borbulhamento puro, e a lei de Tate")
    print("  vale. O tamanho da bolha na entrada NAO depende da vazao.")
    print("-" * 76)
    print("\n" + "=" * 76)
    print("A QUEBRA TURBULENTA ESTA DESLIGADA NESTA COLUNA")
    print("=" * 76)
    print(f"{'Ug':>9s}{'eps':>11s}{'d_critico':>12s}{'d_medido':>12s}{'quebra?':>14s}")
    print(f"{'[m/s]':>9s}{'[m2/s3]':>11s}{'[mm]':>12s}{'[mm]':>12s}")
    print("-" * 76)
    for ug in (UG_EXP[0], UG_EXP[2], UG_EXP[-1]):
        eps = dissipacao(ug)
        dc = d_critico_martinez_bazan(eps)
        quebra = "SIM" if dc < 0.006 else "nao -- inerte"
        print(f"{ug:9.4f}{eps:11.4f}{dc*1000:12.2f}{'4 a 6':>12s}{quebra:>14s}")
    print("-" * 76)
    print("  O diametro critico de Martinez-Bazan fica ACIMA das bolhas")
    print("  medidas em toda a faixa. A turbulencia desta coluna e fraca")
    print("  demais para quebrar bolha de 4 a 6 mm.")
    print("-" * 76)
    print("  CONSEQUENCIA PARA O SETUP:")
    print("     o kernel de quebra do AMUSIG sera praticamente INERTE aqui.")
    print("     A distribuicao bimodal NAO nasce de quebra a jusante -- tem")
    print("     de ser INJETADA no distribuidor.")
    print(f"\n     bolha primaria (Tate)          {bolha_de_formacao(D_HOLE)*1000:5.2f} mm")
    print(f"     satelite de pinch-off (~d/7)   "
          f"{satelite_de_pinchoff(bolha_de_formacao(D_HOLE))*1000:5.2f} mm")
    print(f"     pico pequeno MEDIDO             0.67 mm")
    print("\n  O satelite de destacamento explica o pico de 0,67 mm. Isso")
    print("  fecha a origem das DUAS populacoes no proprio orificio.")
    print("=" * 76)
    print("\n  As duas populacoes vao para lados opostos da coluna. Um EMP de")
    print("  diametro unico coloca todo o gas no mesmo lugar e erra o campo")
    print("  de holdup por construcao -- por isso o caso exige pelo menos")
    print("  dois grupos de tamanho (AMUSIG multi-velocidade ou S-Gamma).")
    print("=" * 76)


# ============================================================================
# FASE 2 -- QUIMISSORCAO, FECHAMENTO DE DARMANA et al. (2007), APENDICE A
# ============================================================================

R_MOL = 8.314         # [J/(mol.K)]
D_OH = 5.27e-9        # [m2/s] difusividade do OH- em agua


def k_direta(T, ionic):
    """k1,1 de CO2(aq) + OH- -> HCO3-  [m3/(kmol.s)].

    Pohorecki & Moniuk (1988), eqs. A.9 e A.10. Valida de 291 a 314 K.
    """
    log_k_inf = 11.895 - 2382.0 / T
    log_ratio = 0.221 * ionic - 0.016 * ionic ** 2
    return 10.0 ** (log_k_inf + log_ratio)


def dif_co2(T, c_oh):
    """Difusividade do CO2, eqs. A.3 e A.4."""
    dw = 2.35e-6 * math.exp(-2119.0 / T)
    return dw * (1.0 - 1.29e-4 * c_oh)


def henry(T, c_na, c_oh):
    """Coeficiente de distribuicao C_liq/C_gas, ADIMENSIONAL. Eqs. A.1 e A.2.

    Hw de Versteeg & van Swaaij (1988) vale ~0,93 para CO2 em agua a 293 K.
    O salting-out de Weisenberger & Schumpe (1996) REDUZ a solubilidade:
        log(Hw/H) = sum (h_i + h_g) c_i     ->    H = Hw / 10^soma
    """
    hw = 3.59e-7 * R_MOL * T * math.exp(2044.0 / T)
    h_g = -0.0183
    soma = (0.1171 + h_g) * c_na + (0.756 + h_g) * c_oh
    return hw / 10.0 ** soma


def c_gas(T, p):
    """Concentracao molar do CO2 na fase gasosa [kmol/m3]."""
    return p / (R_MOL * T) / 1000.0


def kl_brauer(d_b, u_b, T, c_oh):
    """Coeficiente de pelicula, correlacao de Brauer (1981), eq. A.5."""
    d = dif_co2(T, c_oh)
    nu = MU_L / RHO_L
    re = RHO_L * u_b * d_b / MU_L
    sc = nu / d
    sh = 2.0 + 0.015 * re ** 0.89 * sc ** 0.7
    return sh * d / d_b, re, sc, sh


def hatta(k11, d_co2, c_oh, kl):
    """Numero de Hatta, eq. A.8."""
    return math.sqrt(k11 * d_co2 * c_oh) / kl


def e_infinito(d_co2, c_oh, h, cg):
    """Fator de intensificacao no limite instantaneo, eq. A.7.

    H e adimensional, entao a concentracao de CO2 do lado liquido da
    interface e simplesmente H * C_gas.
    """
    c_int = h * cg                          # [kmol/m3] CO2 na interface
    return (1.0 + D_OH * c_oh / (2.0 * d_co2 * c_int)) * math.sqrt(d_co2 / D_OH)


def fator_intensificacao(ha, e_inf):
    """Westerterp et al. (1984), eq. A.6. Precisao de 10%."""
    if e_inf <= 1.0:
        return 1.0
    a = ha ** 2 / (2.0 * (e_inf - 1.0))
    b = ha ** 4 / (4.0 * (e_inf - 1.0) ** 2) + e_inf * ha ** 2 / (e_inf - 1.0) + 1.0
    return -a + math.sqrt(b)


def regime_hatta(ha):
    if ha < 0.3:
        return "LENTA -- reage no seio; VOLUME manda"
    if ha < 3.0:
        return "intermediaria -- filme e seio"
    return "RAPIDA -- reage no filme; AREA manda"


def fase2():
    T = 293.15
    d_b = 0.004        # [m] bolha representativa
    u_b = 0.23         # [m/s] velocidade de ascensao
    p_co2 = 101325.0   # [Pa] CO2 puro, como no experimento E2
    cg = c_gas(T, p_co2)

    print("\n" + "=" * 76)
    print("FASE 2 -- QUIMISSORCAO DE CO2 EM NaOH")
    print("      (fechamento do Apendice A de Darmana et al., CES 62, 2007)")
    print("=" * 76)
    print("  CO2(aq) + OH-  <->  HCO3-        k1,1 / k1,2   <- ETAPA LENTA")
    print("  HCO3-   + OH-  <->  CO3(2-)      k2,1 / k2,2   <- transferencia")
    print("                                                    de proton, ~1e10")
    print("-" * 76)
    print(f"  T = {T:.2f} K   bolha de {d_b*1000:.0f} mm a {u_b:.2f} m/s   "
          f"CO2 puro a 1 atm")
    print(f"  C_CO2 no gas = {cg:.5f} kmol/m3")
    print("=" * 76)

    print(f"\n{'[NaOH]':>9s}{'pH':>7s}{'k1,1':>11s}{'D_CO2':>11s}{'k_L':>11s}"
          f"{'Ha':>8s}{'E_inf':>9s}{'E':>8s}{'H':>8s}")
    print(f"{'[kmol/m3]':>9s}{'':>7s}{'[m3/kmol.s]':>11s}{'[m2/s]':>11s}"
          f"{'[m/s]':>11s}{'[-]':>8s}{'[-]':>9s}{'[-]':>8s}")
    print("-" * 76)

    linhas = []
    for c_oh in (0.0316, 0.1, 0.3, 0.5, 1.0):
        ionic = c_oh                     # NaOH puro: I = [Na+] = [OH-]
        k11 = k_direta(T, ionic)
        d = dif_co2(T, c_oh)
        kl, re, sc, sh = kl_brauer(d_b, u_b, T, c_oh)
        h = henry(T, c_oh, c_oh)
        ha = hatta(k11, d, c_oh, kl)
        einf = e_infinito(d, c_oh, h, cg)
        e = fator_intensificacao(ha, einf)
        ph = 14.0 + math.log10(c_oh)
        print(f"{c_oh:9.4f}{ph:7.2f}{k11:11.0f}{d:11.3e}{kl:11.3e}"
              f"{ha:8.2f}{einf:9.1f}{e:8.2f}{h:8.3f}")
        linhas.append((c_oh, ph, ha, e, regime_hatta(ha)))
    print("-" * 76)
    kl, re, sc, sh = kl_brauer(d_b, u_b, T, 0.3)
    print(f"  Brauer:  Re = {re:.0f}   Sc = {sc:.0f}   Sh = {sh:.0f}   "
          f"k_L = {kl:.3e} m/s")

    print("\n" + "=" * 76)
    print("O ACHADO DE PROJETO -- O REGIME MUDA DENTRO DA PROPRIA FAIXA")
    print("=" * 76)
    for c_oh, ph, ha, e, reg in linhas:
        print(f"  [NaOH] = {c_oh:5.3f}  (pH {ph:5.2f})   Ha = {ha:6.2f}   "
              f"E = {e:6.2f}   {reg}")
    print("-" * 76)
    print("  O experimento E2 de Darmana parte de pH 12,5 e o pH CAI durante")
    print("  a corrida -- ou seja, o reator ATRAVESSA regimes de Hatta ao")
    print("  longo do tempo. No inicio a area interfacial manda; no fim, o")
    print("  volume. Nenhum modelo de reator ideal captura essa troca.")
    print("=" * 76)


if __name__ == "__main__":
    fase1()
    fase2()
