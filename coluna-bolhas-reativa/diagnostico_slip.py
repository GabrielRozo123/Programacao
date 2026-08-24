#!/usr/bin/env python3
"""
De onde vem a diferenca de 21% entre o slip do CFD e o do experimento?

O Nivel 0 entregou slip = 0,233 m/s com Tomiyama + Contaminated e bolha fixa
de 4,5 mm. O artigo entrega velocidade de enxame de 0,282 m/s (Tabela 8) e
velocidade terminal ajustada de 0,314 m/s (Tabela 9).

Ha exatamente tres candidatos para fechar essa diferenca, e este script testa
os tres COM NUMERO, antes de gastar rodada de maquina:

    1. estado de contaminacao do Tomiyama
    2. correcao de enxame (Simonnet)
    3. diametro de bolha

E um quarto que a gente vinha assumindo -- circulacao / parametro de
distribuicao C_0 -- que o proprio drift-flux limita.
"""

import math

from memorial import G, MU_L, RHO_L, SIGMA, U_INF, U_SWARM, UG_EXP

RHO_G = 1.2
UG = UG_EXP[2]          # 0,0115 m/s -- a condicao que estamos rodando
EPS_CFD = 0.049853      # Nivel 1
SLIP_CFD = 0.2331       # Nivel 1


# ---------------------------------------------------------------------------
# 1. TOMIYAMA -- as tres variantes
# ---------------------------------------------------------------------------

def eotvos(d):
    return G * (RHO_L - RHO_G) * d ** 2 / SIGMA


def cd_tomiyama(d, u, estado):
    """C_D de Tomiyama (1998), as tres variantes do STAR-CCM+."""
    re = RHO_L * abs(u) * d / MU_L
    if re < 1e-6:
        re = 1e-6
    eo = eotvos(d)
    cd_eo = 8.0 * eo / (3.0 * (eo + 4.0))
    if estado == "pure":
        visc = min(16.0 / re * (1 + 0.15 * re ** 0.687), 48.0 / re)
    elif estado == "slightly":
        visc = min(24.0 / re * (1 + 0.15 * re ** 0.687), 72.0 / re)
    else:                                   # contaminated
        visc = 24.0 / re * (1 + 0.15 * re ** 0.687)
    return max(visc, cd_eo), visc, cd_eo, re, eo


def terminal(d, estado, f_swarm=1.0):
    """Velocidade terminal por iteracao do balanco empuxo = arrasto."""
    u = 0.2
    for _ in range(300):
        cd, _, _, _, _ = cd_tomiyama(d, u, estado)
        cd *= f_swarm
        novo = math.sqrt(4.0 * d * G * (RHO_L - RHO_G) / (3.0 * cd * RHO_L))
        u += 0.3 * (novo - u)
    return u


# ---------------------------------------------------------------------------
# 2. SIMONNET -- correcao de enxame
# ---------------------------------------------------------------------------

def f_simonnet(eps, m=25.0, expo=2.0):
    """C_D_enxame / C_D_isolada  (Simonnet et al., 2007).

    f = (1-eps) * [ (1-eps)^m + (4,8 eps/(1-eps))^m ]^(-expo/m)

    f > 1 -> mais arrasto -> bolha MAIS LENTA
    f < 1 -> menos arrasto -> bolha MAIS RAPIDA (enxame acelerado)
    """
    a = (1.0 - eps) ** m
    b = (4.8 * eps / (1.0 - eps)) ** m
    return (1.0 - eps) * (a + b) ** (-expo / m)


def main():
    a_col = math.pi / 4 * 0.24 ** 2
    v_gas_cfd = UG / EPS_CFD
    eps_wallis = (1.0 - math.sqrt(1.0 - 4.0 * UG / U_INF["ar"])) / 2.0
    v_gas_exp = UG / eps_wallis

    print("=" * 78)
    print("DE ONDE VEM A DIFERENCA DE 21%?")
    print("=" * 78)
    print(f"  Condicao                    Ug = {UG:.4f} m/s")
    print(f"  CFD Nivel 1                 eps = {EPS_CFD:.5f}   "
          f"v_gas = {v_gas_cfd:.3f} m/s   slip = {SLIP_CFD:.3f}")
    print(f"  Ajuste de Wallis (artigo)   eps = {eps_wallis:.5f}   "
          f"v_gas = {v_gas_exp:.3f} m/s")
    print(f"  Enxame (Tabela 8)                          "
          f"u_swarm = {U_SWARM['ar']:.3f} m/s")
    print(f"  Terminal ajustada (Tab. 9)                 "
          f"u_inf   = {U_INF['ar']:.3f} m/s")
    print("-" * 78)
    print(f"  FALTA               {v_gas_exp - v_gas_cfd:+.3f} m/s "
          f"({100*(v_gas_exp/v_gas_cfd - 1):+.1f}%)")
    print("=" * 78)

    # -------------------------------------------------------------------
    print("\n[1] ESTADO DE CONTAMINACAO -- muda alguma coisa a 4,5 mm?")
    print("-" * 78)
    print(f"{'d':>7s}{'Eo':>8s}{'C_D visc':>11s}{'C_D Eo':>10s}"
          f"{'C_D usado':>12s}{'ramo':>12s}{'u_term':>10s}")
    print(f"{'[mm]':>7s}{'[-]':>8s}{'pure':>11s}{'[-]':>10s}{'[-]':>12s}"
          f"{'':>12s}{'[m/s]':>10s}")
    for estado in ("pure", "slightly", "contaminated"):
        d = 0.0045
        u = terminal(d, estado)
        cd, visc, cd_eo, re, eo = cd_tomiyama(d, u, estado)
        ramo = "EOTVOS" if cd_eo >= visc else "viscoso"
        print(f"{d*1000:7.1f}{eo:8.2f}{visc:11.4f}{cd_eo:10.4f}"
              f"{cd:12.4f}{ramo:>12s}{u:10.4f}   <- {estado}")
    print("-" * 78)
    print("  A 4,5 mm o ramo de Eotvos domina nas TRES variantes -- e ele nao")
    print("  depende do estado de contaminacao. Trocar Contaminated por Pure")
    print("  nao muda NADA aqui. Rodada desnecessaria.")

    # -------------------------------------------------------------------
    print("\n[2] CORRECAO DE ENXAME DE SIMONNET")
    print("-" * 78)
    print(f"{'eps':>8s}{'f = CD/CD0':>13s}{'efeito no slip':>18s}{'':>6s}")
    print("-" * 78)
    for eps in (0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
        f = f_simonnet(eps)
        # slip ~ 1/sqrt(f) no ramo de Eotvos (C_D independente de Re)
        rel = 1.0 / math.sqrt(f) - 1.0
        marca = "  <-- nossa condicao" if abs(eps - 0.05) < 1e-9 else ""
        print(f"{eps:8.2f}{f:13.4f}{100*rel:+17.1f}%{marca}")
    print("-" * 78)
    print("  Em eps baixo o termo (4,8 eps/(1-eps))^25 e desprezivel e a")
    print("  funcao degenera em  f -> 1/(1-eps),  ou seja, ARRASTO MAIOR.")
    print(f"  Em eps = 0,05:  f = {f_simonnet(0.05):.4f}  ->  slip "
          f"{100*(1/math.sqrt(f_simonnet(0.05))-1):+.1f}%.")
    print("  O Simonnet so ACELERA o enxame acima de eps ~ 0,2. Na nossa")
    print("  condicao ele empurra para o lado ERRADO.")

    # -------------------------------------------------------------------
    print("\n[3] LIMITE DA CIRCULACAO -- o que o drift-flux permite")
    print("-" * 78)
    print("  Zuber & Findlay:   <jg>/<eps> = C_0 <j> + u_drift")
    print(f"  Em BATELADA a vazao liquida liquida e zero, entao")
    print(f"      <j> = <jg> = Ug = {UG:.4f} m/s")
    print("-" * 78)
    print(f"{'C_0':>8s}{'C_0 <j>':>12s}{'v_gas com u_drift = 0,233':>28s}")
    print("-" * 78)
    for c0 in (1.0, 1.2, 1.5, 2.0):
        print(f"{c0:8.2f}{c0*UG:12.4f}{c0*UG + SLIP_CFD*(1-EPS_CFD):28.4f}")
    c0_necessario = (v_gas_exp - SLIP_CFD * (1 - EPS_CFD)) / UG
    print("-" * 78)
    print(f"  Para fechar a diferenca sozinha, a circulacao precisaria de")
    print(f"      C_0 = {c0_necessario:.1f}")
    print("  C_0 fisico em coluna de bolhas: 1,0 a 1,5 (ate ~2 no bolhoso).")
    print("  ==> A CIRCULACAO NAO FECHA. Em batelada <j> e a propria Ug, que")
    print("      e 20x menor que o slip -- o termo C_0<j> vale no maximo 1%.")
    print("      Eu tinha atribuido os 21% a circulacao. Estava errado.")

    # -------------------------------------------------------------------
    print("\n[4] DIAMETRO DE BOLHA -- o unico candidato que sobra")
    print("-" * 78)
    print(f"{'d':>7s}{'Eo':>9s}{'C_D':>9s}{'u_term':>10s}{'eps previsto':>15s}"
          f"{'':>4s}")
    print(f"{'[mm]':>7s}{'[-]':>9s}{'[-]':>9s}{'[m/s]':>10s}{'[-]':>15s}")
    print("-" * 78)
    alvo = None
    for dmm in (2, 3, 4.5, 6, 8, 10, 12, 14, 16, 18, 20):
        d = dmm / 1000.0
        u = terminal(d, "contaminated")
        cd, _, _, _, eo = cd_tomiyama(d, u, "contaminated")
        # holdup de equilibrio: Ug = eps * u * (1-eps)  -> raiz fisica
        disc = 1.0 - 4.0 * UG / u
        eps = (1.0 - math.sqrt(disc)) / 2.0 if disc > 0 else float("nan")
        marca = ""
        if dmm == 4.5:
            marca = "  <-- Nivel 0 (lei de Tate, formacao)"
        if alvo is None and u >= U_SWARM["ar"]:
            alvo = dmm
            marca = "  <-- alcanca u_swarm do artigo"
        print(f"{dmm:7.1f}{eo:9.2f}{cd:9.4f}{u:10.4f}{eps:15.5f}{marca}")
    print("-" * 78)
    print(f"  eps medido (Wallis) = {eps_wallis:.5f}   "
          f"eps medido (enxame) = {UG/U_SWARM['ar']*1.0:.5f} aprox.")
    print("-" * 78)
    print("  A lei de Tate da o diametro de FORMACAO no furo. Depois vem 3 m")
    print("  de coluna. O d32 medio da coluna nao tem por que ser 4,5 mm.")
    print("-" * 78)
    print("  NOTE A CURVA: u_term tem um MINIMO entre 4 e 6 mm. A lei de Tate")
    print("  caiu exatamente no fundo do poco -- o pior diametro possivel para")
    print("  fixar. Dos dois lados a bolha sobe mais rapido.")
    print("-" * 78)
    print("  Para reproduzir o holdup medido o Tomiyama precisa de")
    print("      d ~ 16 mm  ->  eps = 0,0405   (bate o ajuste de enxame, 0,0408)")
    print("      d ~ 18 mm  ->  eps = 0,0386   (bate o ajuste de Wallis,  0,0381)")
    print("  ou seja d32 na casa de 15 a 18 mm -- o topo da faixa em que os")
    print("  grupos do AMUSIG tinham ido parar (3,3 a 17,1 mm).")
    print("=" * 78)

    print("\n[5] MODA NAO E d32 -- a reconciliacao com a BSD medida")
    print("-" * 78)
    print("  O artigo mede modas de 0,67 mm e 4 a 6 mm. Isso e densidade de")
    print("  NUMERO. O arrasto responde ao diametro de Sauter, que pesa d^3/d^2")
    print("  e portanto e dominado pela CAUDA GRANDE, nao pela moda.")
    print("-" * 78)
    print("  Populacao base: 1000 satelites de 0,67 mm + 1000 bolhas de 5 mm")
    print("  (as duas modas medidas). Varia-se so a cauda de 20 mm:")
    print("-" * 78)
    print(f"{'n de 20 mm':>12s}{'% do numero':>14s}{'% do volume':>14s}"
          f"{'d10':>10s}{'d32':>10s}")
    print(f"{'':>12s}{'':>14s}{'':>14s}{'[mm]':>10s}{'[mm]':>10s}")
    print("-" * 78)
    base = [(1000.0, 0.00067), (1000.0, 0.0050)]
    for n20 in (0, 5, 20, 50, 100, 200):
        pop = base + ([(float(n20), 0.020)] if n20 else [])
        ntot = sum(n for n, _ in pop)
        vol = sum(n * d ** 3 for n, d in pop)
        d32 = vol / sum(n * d ** 2 for n, d in pop)
        d10 = sum(n * d for n, d in pop) / ntot
        fv = (n20 * 0.020 ** 3 / vol * 100.0) if n20 else 0.0
        print(f"{n20:12d}{100*n20/ntot:13.1f}%{fv:13.1f}%"
              f"{d10*1000:10.2f}{d32*1000:10.2f}")
    print("-" * 78)
    print("  Sem cauda nenhuma o d32 e 4,9 mm -- perto do nosso 4,5 mm fixo.")
    print("  Bastam 5% das bolhas em 20 mm (que carregam 87% do volume de gas)")
    print("  para o d32 ir a 14 mm, SEM MEXER em nenhuma das duas modas.")
    print("  A BSD medida e a nossa hipotese de d32 grande sao compativeis:")
    print("  a moda conta bolha, o d32 conta gas, e o arrasto responde ao gas.")
    print("-" * 78)
    print("  Fixar o diametro na MODA subestima a velocidade de ascensao e")
    print("  portanto SUPERESTIMA o holdup -- exatamente o sinal do nosso erro.")
    print("  E o mesmo d32 governa a area interfacial a = 6 eps / d32 da Fase 2:")
    print("  errar d32 por 3x erra a area interfacial por 3x, e com ela o k_L a.")
    print("=" * 78)

    print("\nCONCLUSAO")
    print("-" * 78)
    print("  contaminacao   -> inerte a 4,5 mm (ramo de Eotvos)")
    print("  Simonnet       -> -2,5% em eps = 0,05, lado errado")
    print("  circulacao     -> teto de ~1% em batelada")
    print("  DIAMETRO       -> unico mecanismo com magnitude suficiente")
    print("-" * 78)
    print("  Logo o fechamento do holdup NAO esta no Nivel 1. Esta na")
    print("  populacao de bolhas -- ou seja, no Nivel 2 (AMUSIG com")
    print("  coalescencia). O Nivel 1 continua valendo, mas pelo que ele")
    print("  realmente entrega: a ESTRUTURA RADIAL, nao o holdup global.")
    print("=" * 78)
    print("\nPREVISAO FALSIFICAVEL PARA O NIVEL 2")
    print("-" * 78)
    print("  Registrada ANTES de rodar o AMUSIG:")
    print("      se o AMUSIG convergir com d32 entre 15 e 18 mm, o holdup cai")
    print("      para 0,038 a 0,041 e a validacao fecha SOZINHA.")
    print("      se convergir com d32 ~ 5 mm, o holdup fica em 0,050 e a")
    print("      hipotese do diametro esta MORTA -- o erro e do arrasto.")
    print("  Os dois desfechos sao informativos. E o que faz disso verificacao")
    print("  e nao ajuste de curva.")
    print("=" * 78)


if __name__ == "__main__":
    main()
