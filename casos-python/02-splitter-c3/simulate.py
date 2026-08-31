"""
Splitter propeno/propano (C3 splitter) — Python Case para o AI4Tech Suite.

Coluna de destilacao binaria em MODO RATING: dados o numero de estagios, a
posicao da alimentacao, a razao de refluxo, o corte e a pressao, calcula as
purezas, as cargas termicas, o dimensionamento e a economia anual.

Modo rating (e nao modo projeto) porque e assim que a coluna rigorosa do DWSIM
se comporta: voce fixa os estagios e as especificacoes de operacao, e a coluna
devolve as composicoes. Isso permite comparar ponto a ponto este modelo com o
DWSIM e medir o erro do atalho.

Por que este caso vale a pena
-----------------------------
O splitter C3 e a separacao onde o surrogate tem o maior retorno possivel. Com
volatilidade relativa em torno de 1,12, a coluna precisa de 150 a 250 estagios
e refluxo de 12 a 20 — a versao rigorosa e lenta, e um NSGA-III quer dezenas de
milhares de avaliacoes. O surrogate deixa de ser enfeite e passa a ser o que
viabiliza a otimizacao.

Alem disso o problema economico e real e tem um degrau: propeno grau polimero
(fracao molar >= 0,995) vale muito mais que grau quimico, que por sua vez vale
muito mais que GLP. O otimo tende a encostar na especificacao por cima, que e
exatamente o dilema de projeto de uma unidade de verdade.

Hipoteses do modelo
-------------------
  * Sistema binario propeno/propano, volatilidade relativa constante ao longo
    da coluna, corrigida pela pressao.
  * Fluxo molar constante (CMO) e alimentacao liquido saturado (q = 1).
  * Condensador total, refervedor parcial (conta como um estagio).
  * Perda de carga ao longo da coluna desprezada.

Nenhuma dessas hipoteses vale exatamente. E esse justamente e o ponto: o DWSIM
fornece a resposta rigorosa e este modelo fornece a resposta instantanea. A
diferenca entre os dois e o objeto de estudo, nao um defeito.

Unidades: kmol/h, bar, K, m, kW, USD.
"""

import math

# --------------------------------------------------------------------------
# Propriedades dos componentes
# --------------------------------------------------------------------------
MM_PROPENO = 42.08   # kg/kmol
MM_PROPANO = 44.10   # kg/kmol
TC_PROPENO = 364.9   # K, temperatura critica

# Antoine na forma log10(Psat[bar]) = A - B/(T[K] + C).
#
# B e C vem de ajuste a pontos de saturacao de literatura a 0, 25 e 50 C. O
# intercepto A foi depois REANCORADO no DWSIM 10.2.3.0 com Peng-Robinson: as
# medicoes quase puras a 18 bar, extrapoladas ao componente puro, dao 43,631 C
# para o propeno e 52,093 C para o propano, contra 44,153 C e 52,382 C das
# constantes originais. Os dois Antoine corriam quentes — 0,52 C e 0,29 C.
#
# A ancoragem e de um ponto so (18 bar) e preserva a forma da curva. Na faixa
# estreita de 14 a 22 bar isso e adequado; fora dela, remedir.
ANTOINE_PROPENO = (4.182428, 901.4496, -8.8200)
ANTOINE_PROPANO = (4.283326, 985.8223, 0.3200)

# Calor latente de referencia do propeno, para escalonamento de Watson.
#
# ANCORADO EM MEDICAO. O valor de literatura (343,0 kJ/kg a 298,15 K) produzia
# cargas termicas 3,2 % acima do DWSIM em cinco rodadas de coluna. O lambda
# implicito nas cargas do DWSIM foi identico em rodadas com refluxo 15 e 17,8
# — 12 351,8 e 12 352,9 kJ/kmol, diferenca de 0,009 % — o que confirma um
# unico parametro errado, e nao erro estrutural do modelo.
#
# A ancoragem e de uma temperatura so (topo a 18 bar, 43,6 C), porque todas as
# rodadas foram nessa pressao. O expoente de Watson, que governa a dependencia
# com a temperatura, continua sem verificacao.
LAMBDA_REF = 332.4181   # kJ/kg a 298,15 K
T_LAMBDA_REF = 298.15
EXPOENTE_WATSON = 0.38

Z_VAPOR = 0.80       # fator de compressibilidade medio na faixa de operacao
R_GAS = 8.314        # kJ/(kmol.K)

# --------------------------------------------------------------------------
# Volatilidade relativa — superficie ajustada a medicoes no DWSIM 10.2.3.0
# com Peng-Robinson (flash PVF, fracao de vapor 0,5).
#
# Dependencia com a COMPOSICAO, a 18 bar (seis medicoes cobrindo toda a faixa
# util da coluna, do fundo ao topo):
#     x = 0,00919 -> alfa = 1,177690
#     x = 0,04618 -> alfa = 1,174670
#     x = 0,48435 -> alfa = 1,133423
#     x = 0,74063 -> alfa = 1,105152
#     x = 0,94817 -> alfa = 1,080285
#     x = 0,98964 -> alfa = 1,075116
#   ln(alfa) quadratico em x, rms = 1,2e-5. Um termo cubico reduz o rms para
#   3,7e-6, mas o ganho e menor que a propria resolucao dos dados: nao vale o
#   parametro extra com seis pontos.
#
# Dependencia com a PRESSAO, a x = 0,74 (tres medicoes, 14/18/22 bar):
#   linear, inclinacao -0,003363 por bar, residuos ~2,5e-4.
#
# A superficie NAO extrapola dentro da coluna: as medicoes vao de x = 0,009 a
# x = 0,990, e o destilado opera em torno de x = 0,99. O ajuste anterior, feito
# so com os quatro primeiros pontos, previa 1,080221 e 1,075035 nos dois
# ultimos — erro de 0,01 % contra o medido.
# --------------------------------------------------------------------------
ALFA_C0 = 0.164200
ALFA_C1 = -0.068679
ALFA_C2 = -0.024311
ALFA_POR_BAR = -0.003363
ALFA_P_REFERENCIA = 18.0

# --------------------------------------------------------------------------
# Geometria e hidraulica
# --------------------------------------------------------------------------
EFICIENCIA_PRATO = 0.85     # eficiencia de Murphree tipica para hidrocarbonetos proximos
ESPACAMENTO_PRATO = 0.60    # m
ALTURA_EXTRA = 4.0          # m, fundo mais topo
K_SOUDERS_BROWN = 0.09      # m/s
FRACAO_INUNDACAO = 0.80     # projeto a 80 % da velocidade de inundacao
ALTURA_MAX_CASCO = 60.0     # m; acima disso a coluna e dividida em cascos em serie

# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
T_AGUA_ENTRADA = 303.15     # K (30 C)
T_AGUA_SAIDA = 313.15       # K (40 C)
T_MIN_AGUA = 313.15         # K; condensador abaixo disso exige refrigeracao
T_VAPOR_BAIXA = 403.15      # K (130 C), vapor de baixa pressao
LAMBDA_VAPOR_AGUA = 2160.0  # kJ/kg
U_CONDENSADOR = 500.0       # W/(m2.K)
U_REFERVEDOR = 800.0        # W/(m2.K)

CUSTO_VAPOR = 20.0          # USD/t
CUSTO_AGUA = 0.35           # USD/GJ
FATOR_REFRIGERACAO = 10.0   # refrigeracao custa cerca de 10x a agua de resfriamento
HORAS_ANO = 8000.0

# --------------------------------------------------------------------------
# Custos de capital
# ATENCAO: sao estimativas fatoradas, de ordem de grandeza, uteis para COMPARAR
# alternativas de projeto. Um estudo de viabilidade exige estimativa formal.
# --------------------------------------------------------------------------
CUSTO_CASCO = 17640.0       # USD; C = k * D^1.066 * H^0.802 (D, H em m)
CUSTO_PRATO = 300.0         # USD por prato; C = k * D^1.55
CUSTO_TROCADOR = 12000.0    # USD; C = k * A^0.60 (A em m2)
FATOR_INSTALACAO = 4.0      # fator de Lang: custo instalado / custo de equipamento
TAXA_JUROS = 0.10
VIDA_UTIL = 15.0            # anos

# --------------------------------------------------------------------------
# Precos de produto (USD/t). O degrau entre grau polimero e grau quimico e o que
# torna o problema economico interessante — e e real.
# --------------------------------------------------------------------------
PUREZA_GRAU_POLIMERO = 0.995
PUREZA_GRAU_QUIMICO = 0.920
PRECO_GRAU_POLIMERO = 1150.0
PRECO_GRAU_QUIMICO = 950.0
PRECO_GLP = 550.0
PRECO_ALIMENTACAO = 750.0


VARIAVEIS = {
    "descricao": "Splitter propeno/propano em modo rating, com economia anual",
    "entradas": [
        {"nome": "N_estagios", "unidade": "-", "tipo": "Discrete",
         "padrao": 200.0, "min": 100.0, "max": 260.0, "passo": 10.0,
         "descricao": "Estagios teoricos, refervedor incluido"},
        {"nome": "pos_alimentacao", "unidade": "-", "tipo": "Continuous",
         "padrao": 0.50, "min": 0.30, "max": 0.70,
         "descricao": "Posicao da alimentacao como fracao de N, contada do topo"},
        {"nome": "razao_refluxo", "unidade": "-", "tipo": "Continuous",
         "padrao": 15.0, "min": 8.0, "max": 24.0,
         "descricao": "Razao de refluxo L/D"},
        {"nome": "corte", "unidade": "-", "tipo": "Continuous",
         "padrao": 0.995, "min": 0.970, "max": 0.999,
         "descricao": "D/(F.z) — vazao de destilado por propeno alimentado"},
        {"nome": "pressao", "unidade": "bar", "tipo": "Continuous",
         "padrao": 18.0, "min": 14.0, "max": 22.0,
         "descricao": "Pressao de operacao da coluna"},
        {"nome": "z_propeno", "unidade": "-", "tipo": "Continuous",
         "padrao": 0.75, "min": 0.60, "max": 0.90,
         "descricao": "Fracao molar de propeno na alimentacao"},
        {"nome": "F_alimentacao", "unidade": "kmol/h", "tipo": "Fixed",
         "padrao": 1000.0,
         "descricao": "Vazao de alimentacao (base de calculo)"},
    ],
    "saidas": [
        {"nome": "pureza_topo",      "unidade": "% mol",   "descricao": "Propeno no destilado"},
        {"nome": "pureza_fundo",     "unidade": "% mol",   "descricao": "Propano no produto de fundo"},
        {"nome": "recuperacao",      "unidade": "%",       "descricao": "Propeno recuperado no destilado"},
        {"nome": "grau_produto",     "unidade": "-",       "descricao": "2 = polimero, 1 = quimico, 0 = GLP"},
        {"nome": "Q_refervedor",     "unidade": "MW",      "descricao": "Carga termica do refervedor"},
        {"nome": "Q_condensador",    "unidade": "MW",      "descricao": "Carga termica do condensador"},
        {"nome": "T_condensador",    "unidade": "C",       "descricao": "Temperatura de topo"},
        {"nome": "T_refervedor",     "unidade": "C",       "descricao": "Temperatura de fundo"},
        {"nome": "precisa_refrig",   "unidade": "-",       "descricao": "1 se o topo exige refrigeracao"},
        {"nome": "diametro",         "unidade": "m",       "descricao": "Diametro da coluna"},
        {"nome": "altura_total",     "unidade": "m",       "descricao": "Altura somada dos cascos"},
        {"nome": "n_cascos",         "unidade": "-",       "descricao": "Cascos em serie necessarios"},
        {"nome": "alfa_topo",        "unidade": "-",       "descricao": "Volatilidade relativa na composicao do topo"},
        {"nome": "alfa_fundo",       "unidade": "-",       "descricao": "Volatilidade relativa na composicao do fundo"},
        {"nome": "N_min",            "unidade": "-",       "descricao": "Estagios minimos (Fenske, media geometrica de alfa)"},
        {"nome": "R_min",            "unidade": "-",       "descricao": "Refluxo minimo (Underwood)"},
        {"nome": "R_sobre_Rmin",     "unidade": "-",       "descricao": "Folga de refluxo sobre o minimo"},
        {"nome": "CAPEX",            "unidade": "MUSD",    "descricao": "Investimento instalado"},
        {"nome": "CAPEX_anual",      "unidade": "MUSD/ano","descricao": "CAPEX anualizado"},
        {"nome": "OPEX",             "unidade": "MUSD/ano","descricao": "Utilidades"},
        {"nome": "custo_total",      "unidade": "MUSD/ano","descricao": "CAPEX anualizado + OPEX"},
        {"nome": "lucro",            "unidade": "MUSD/ano","descricao": "Receita - alimentacao - custo total"},
        {"nome": "convergiu",        "unidade": "-",       "descricao": "1 = sucesso, 0 = falha"},
    ],
}


# --------------------------------------------------------------------------
# Termodinamica
# --------------------------------------------------------------------------
def volatilidade_relativa(x, pressao):
    """
    Volatilidade relativa propeno/propano no ponto (x, P), com x a fracao molar
    de propeno na fase liquida.

    Alfa NAO e constante ao longo da coluna: entre o fundo e o topo ele cai de
    ~1,178 para ~1,074, uma variacao de quase 10 %. Como N_min e proporcional
    a 1/ln(alfa) e ln(alfa) e pequeno nessa faixa, essa variacao vale mais de
    50 % de diferenca em dificuldade de separacao entre as duas pontas da
    coluna. Tratar alfa como constante era o maior erro deste modelo.
    """
    x = min(max(x, 0.0), 1.0)
    base = math.exp(ALFA_C0 + ALFA_C1 * x + ALFA_C2 * x * x)
    return base + ALFA_POR_BAR * (pressao - ALFA_P_REFERENCIA)


def temperatura_saturacao(pressao, constantes):
    """Temperatura de bolha do componente puro, em K, invertendo Antoine."""
    A, B, C = constantes
    return B / (A - math.log10(pressao)) - C


def calor_latente(temperatura):
    """Calor latente do propeno em kJ/kmol pelo escalonamento de Watson."""
    razao = (TC_PROPENO - temperatura) / (TC_PROPENO - T_LAMBDA_REF)
    razao = max(razao, 1e-6)
    return LAMBDA_REF * (razao ** EXPOENTE_WATSON) * MM_PROPENO


def densidade_liquido(temperatura):
    """Densidade do liquido em kg/m3, ajuste linear na faixa de operacao."""
    return 505.0 - 1.75 * (temperatura - 298.15)


def densidade_vapor(pressao, temperatura):
    """Densidade do vapor em kg/m3, gas real com fator de compressibilidade fixo."""
    return pressao * 100.0 * MM_PROPENO / (Z_VAPOR * R_GAS * temperatura)


# --------------------------------------------------------------------------
# Coluna: marcha estagio a estagio
# --------------------------------------------------------------------------
def _limitar(v):
    return min(max(v, 1e-15), 1.0 - 1e-15)


def _y_equilibrio(x, pressao):
    """Vapor em equilibrio com o liquido de composicao x."""
    alfa = volatilidade_relativa(x, pressao)
    return alfa * x / (1.0 + (alfa - 1.0) * x)


def _x_equilibrio(y, pressao):
    """
    Liquido em equilibrio com o vapor de composicao y.

    Com alfa dependendo de x a relacao fica implicita, entao resolvemos por
    ponto fixo. Alfa varia devagar com x, o que torna a iteracao fortemente
    contrativa: converge em poucos passos.
    """
    x = y
    for _ in range(50):
        alfa = volatilidade_relativa(x, pressao)
        novo = y / (alfa - (alfa - 1.0) * y)
        novo = min(max(novo, 0.0), 1.0)
        if abs(novo - x) < 1e-14:
            return novo
        x = novo
    return x


def _residuo_coluna(xD, N, Nf, R, D_sobre_F, zF, pressao):
    """
    Marcha a secao de retificacao do topo para baixo e a de esgotamento do fundo
    para cima, e devolve a diferenca entre as duas no estagio de alimentacao.

    Marchar dos dois extremos, em vez de atravessar a coluna inteira de uma vez,
    e o que torna o calculo estavel: cada marcha caminha na direcao do seu
    proprio pinch, que e um atrator numerico. Com alfa proximo de 1 e mais de
    200 estagios, atravessar a coluna de ponta a ponta acumula erro.
    """
    D = D_sobre_F
    B = 1.0 - D
    if B <= 1e-9:
        return None
    xB = (zF - D * xD) / B
    if xB <= 0.0 or xB >= 1.0:
        return None

    L = R * D
    V = L + D
    L_linha = L + 1.0      # alimentacao liquido saturado, base F = 1
    V_linha = V

    # Retificacao: condensador total, portanto y_1 = xD.
    y = xD
    x = _x_equilibrio(y, pressao)
    for _ in range(1, max(Nf - 1, 1)):
        y = _limitar((L / V) * x + (D / V) * xD)
        x = _x_equilibrio(y, pressao)
    y_por_cima = _limitar((L / V) * x + (D / V) * xD)

    # Esgotamento: refervedor parcial e o estagio N.
    x = xB
    y = _y_equilibrio(x, pressao)
    for _ in range(N, Nf, -1):
        x = _limitar((y + (B / V_linha) * xB) / (L_linha / V_linha))
        y = _y_equilibrio(x, pressao)

    return y_por_cima - y


def resolver_coluna(N, Nf, R, D_sobre_F, zF, pressao):
    """
    Encontra xD por bisseccao sobre o residuo de casamento no prato de
    alimentacao. Devolve (xD, xB) ou None se nao houver solucao na faixa.
    """
    def f(xd):
        return _residuo_coluna(xd, N, Nf, R, D_sobre_F, zF, pressao)

    lo, hi = zF + 1e-9, 1.0 - 1e-12
    f_lo, f_hi = f(lo), f(hi)
    if f_lo is None or f_hi is None:
        return None
    if (f_lo < 0.0) == (f_hi < 0.0):
        return None

    for _ in range(200):
        meio = 0.5 * (lo + hi)
        f_meio = f(meio)
        if f_meio is None:
            return None
        if (f_lo < 0.0) != (f_meio < 0.0):
            hi = meio
        else:
            lo, f_lo = meio, f_meio
        if hi - lo < 1e-14:
            break

    xD = 0.5 * (lo + hi)
    xB = (zF - D_sobre_F * xD) / (1.0 - D_sobre_F)
    return xD, xB


def estagios_minimos(xD, xB, pressao):
    """
    Equacao de Fenske com a media geometrica de alfa entre topo e fundo — a
    pratica usual quando alfa varia ao longo da coluna, e aqui ele varia muito.
    """
    if not (0.0 < xB < xD < 1.0):
        return 0.0
    alfa = math.sqrt(volatilidade_relativa(xD, pressao)
                     * volatilidade_relativa(xB, pressao))
    if alfa <= 1.0:
        return 0.0
    return math.log((xD / (1.0 - xD)) * ((1.0 - xB) / xB)) / math.log(alfa)


def refluxo_minimo(xD, zF, pressao):
    """Underwood para binario com alimentacao liquido saturado, alfa no prato de alimentacao."""
    if not (0.0 < zF < 1.0):
        return 0.0
    alfa = volatilidade_relativa(zF, pressao)
    if alfa <= 1.0:
        return 0.0
    valor = (xD / zF - alfa * (1.0 - xD) / (1.0 - zF)) / (alfa - 1.0)
    return max(valor, 0.0)


# --------------------------------------------------------------------------
# Interface da plataforma
# --------------------------------------------------------------------------
def simulate(inputs):
    """simulate(inputs: dict) -> dict, conforme exigido pelo AI4Tech Suite."""
    padroes = {v["nome"]: v["padrao"] for v in VARIAVEIS["entradas"]}
    val = {nome: float(inputs.get(nome, padrao)) for nome, padrao in padroes.items()}
    falha = {saida["nome"]: 0.0 for saida in VARIAVEIS["saidas"]}

    N = int(round(val["N_estagios"]))
    R = val["razao_refluxo"]
    P = val["pressao"]
    zF = val["z_propeno"]
    F = val["F_alimentacao"]
    Nf = int(round(val["pos_alimentacao"] * N))
    Nf = max(2, min(N - 1, Nf))

    if N < 5 or R <= 0.0 or P <= 0.1 or not (0.0 < zF < 1.0) or F <= 0.0:
        return falha

    if volatilidade_relativa(zF, P) <= 1.0:
        return falha

    D_sobre_F = val["corte"] * zF
    if not (0.0 < D_sobre_F < 1.0):
        return falha

    solucao = resolver_coluna(N, Nf, R, D_sobre_F, zF, P)
    if solucao is None:
        return falha
    xD, xB = solucao

    # ---- vazoes ----
    D = D_sobre_F * F
    B = F - D
    V = (R + 1.0) * D                     # vapor no topo, CMO
    recuperacao = D * xD / (F * zF)

    # ---- temperaturas ----
    T_topo = temperatura_saturacao(P, ANTOINE_PROPENO)
    T_fundo = temperatura_saturacao(P, ANTOINE_PROPANO)
    precisa_refrigeracao = 1.0 if T_topo < T_MIN_AGUA else 0.0

    # ---- cargas termicas (kW) ----
    lamb = calor_latente(T_topo)
    Q_cond = V * lamb / 3600.0
    Q_reb = Q_cond                         # CMO com alimentacao liquido saturado

    # ---- dimensionamento ----
    rho_L = densidade_liquido(T_topo)
    rho_V = densidade_vapor(P, T_topo)
    if rho_V <= 0.0 or rho_L <= rho_V:
        return falha
    u_inundacao = K_SOUDERS_BROWN * math.sqrt((rho_L - rho_V) / rho_V)
    vazao_vol = V * MM_PROPENO / rho_V / 3600.0        # m3/s
    area = vazao_vol / (FRACAO_INUNDACAO * u_inundacao)
    diametro = math.sqrt(4.0 * area / math.pi)

    pratos_reais = math.ceil((N - 1) / EFICIENCIA_PRATO)   # refervedor nao e prato
    altura = pratos_reais * ESPACAMENTO_PRATO + ALTURA_EXTRA
    n_cascos = max(1, math.ceil(altura / ALTURA_MAX_CASCO))
    altura_casco = altura / n_cascos

    # ---- areas de troca ----
    if precisa_refrigeracao:
        delta_t_cond = 10.0                # refrigerante a temperatura constante
    else:
        d1 = max(T_topo - T_AGUA_SAIDA, 1.0)
        d2 = max(T_topo - T_AGUA_ENTRADA, 2.0)
        delta_t_cond = (d2 - d1) / math.log(d2 / d1) if abs(d2 - d1) > 1e-6 else d1
    area_cond = Q_cond * 1000.0 / (U_CONDENSADOR * delta_t_cond)
    delta_t_reb = max(T_VAPOR_BAIXA - T_fundo, 5.0)
    area_reb = Q_reb * 1000.0 / (U_REFERVEDOR * delta_t_reb)

    # ---- CAPEX ----
    custo_cascos = n_cascos * CUSTO_CASCO * (diametro ** 1.066) * (altura_casco ** 0.802)
    custo_pratos = CUSTO_PRATO * (diametro ** 1.55) * pratos_reais
    custo_trocadores = CUSTO_TROCADOR * ((area_cond ** 0.60) + (area_reb ** 0.60))
    capex = FATOR_INSTALACAO * (custo_cascos + custo_pratos + custo_trocadores)

    fator = (1.0 + TAXA_JUROS) ** VIDA_UTIL
    recuperacao_capital = TAXA_JUROS * fator / (fator - 1.0)
    capex_anual = capex * recuperacao_capital

    # ---- OPEX ----
    vapor_t_h = Q_reb * 3600.0 / LAMBDA_VAPOR_AGUA / 1000.0
    custo_vapor_ano = vapor_t_h * CUSTO_VAPOR * HORAS_ANO
    custo_frio_ano = (Q_cond * 3600.0 / 1.0e6) * CUSTO_AGUA * HORAS_ANO
    if precisa_refrigeracao:
        custo_frio_ano *= FATOR_REFRIGERACAO
    opex = custo_vapor_ano + custo_frio_ano

    # ---- receita ----
    if xD >= PUREZA_GRAU_POLIMERO:
        preco_topo, grau = PRECO_GRAU_POLIMERO, 2.0
    elif xD >= PUREZA_GRAU_QUIMICO:
        preco_topo, grau = PRECO_GRAU_QUIMICO, 1.0
    else:
        preco_topo, grau = PRECO_GLP, 0.0

    mm_topo = xD * MM_PROPENO + (1.0 - xD) * MM_PROPANO
    mm_fundo = (1.0 - xB) * MM_PROPANO + xB * MM_PROPENO
    mm_alim = zF * MM_PROPENO + (1.0 - zF) * MM_PROPANO

    receita = (D * mm_topo * preco_topo + B * mm_fundo * PRECO_GLP) / 1000.0 * HORAS_ANO
    custo_alim = F * mm_alim * PRECO_ALIMENTACAO / 1000.0 * HORAS_ANO
    custo_total = capex_anual + opex
    lucro = receita - custo_alim - custo_total

    milhao = 1.0e6
    return {
        "pureza_topo": 100.0 * xD,
        "pureza_fundo": 100.0 * (1.0 - xB),
        "recuperacao": 100.0 * recuperacao,
        "grau_produto": grau,
        "Q_refervedor": Q_reb / 1000.0,
        "Q_condensador": Q_cond / 1000.0,
        "T_condensador": T_topo - 273.15,
        "T_refervedor": T_fundo - 273.15,
        "precisa_refrig": precisa_refrigeracao,
        "diametro": diametro,
        "altura_total": altura,
        "n_cascos": float(n_cascos),
        "alfa_topo": volatilidade_relativa(xD, P),
        "alfa_fundo": volatilidade_relativa(xB, P),
        "N_min": estagios_minimos(xD, xB, P),
        "R_min": refluxo_minimo(xD, zF, P),
        "R_sobre_Rmin": R / max(refluxo_minimo(xD, zF, P), 1e-9),
        "CAPEX": capex / milhao,
        "CAPEX_anual": capex_anual / milhao,
        "OPEX": opex / milhao,
        "custo_total": custo_total / milhao,
        "lucro": lucro / milhao,
        "convergiu": 1.0,
    }


if __name__ == "__main__":
    resultado = simulate({})
    print("Caso base: N=200, alim. no meio, R=15, corte=0.995, P=18 bar, z=0.75\n")
    for chave, valor in resultado.items():
        print("  {:<16} = {:>12.4f}".format(chave, valor))
