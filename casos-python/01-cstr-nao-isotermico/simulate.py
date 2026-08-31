"""
CSTR nao-isotermico com camisa de resfriamento — Python Case para o AI4Tech Suite.

Reacao: A -> B, irreversivel, primeira ordem, exotermica.
Estado estacionario resolvido por varredura + bisseccao (sem dependencias externas).

Por que este caso e interessante para o AI4Tech Suite
-----------------------------------------------------
O balanco de energia deste reator admite ATE TRES estados estacionarios para a
mesma combinacao de entradas (o classico problema de ignicao/extincao). Isso faz
com que o mapa entrada->saida seja NAO-LINEAR e, em algumas regioes, DESCONTINUO.
Consequencias praticas nos modulos da suite:

  * Analysis      -> Pearson tende a zero em regioes onde HSIC/Chatterjee acusam
                     dependencia forte. Otimo para mostrar que correlacao linear
                     engana.
  * Surrogate     -> MLP, XGBoost e GPR se comportam de formas bem diferentes
                     diante do degrau de ignicao. Comparacao rica.
  * Williams Plot -> pontos na fronteira de ignicao aparecem como alta alavancagem.
  * Optimization  -> conflito real entre conversao, custo de resfriamento e
                     margem de seguranca termica.
  * Operability   -> o Achievable Output Set (AOS) fica NAO-CONVEXO, que e
                     exatamente o cenario em que o indice de operabilidade de
                     Georgakis diz algo relevante.

Convencao de estado estacionario
--------------------------------
Quando existe multiplicidade, a funcao devolve como ponto de operacao o ramo
ALCANCAVEL A PARTIR DE PARTIDA FRIA (menor raiz estavel), que e o comportamento
fisico de um reator que sobe de temperatura ambiente. O ramo ignitado e a
contagem de estados sao devolvidos como saidas auxiliares, para que o degrau
possa ser estudado explicitamente.

Parametros do modelo: conjunto classico de Seborg, Edgar, Mellichamp & Doyle,
"Process Dynamics and Control" (CSTR nao-isotermico).
Unidades: minuto, litro, mol, joule, kelvin.
"""

import math

# --------------------------------------------------------------------------
# Constantes fisico-quimicas do sistema (nao variam no DOE)
# --------------------------------------------------------------------------
RHO = 1000.0          # densidade da mistura, g/L
CP = 0.239            # calor especifico, J/(g.K)
DELTA_HR = -5.0e4     # calor de reacao, J/mol (negativo = exotermica)
EA_SOBRE_R = 8750.0   # energia de ativacao / R, K
K0 = 7.2e10           # fator pre-exponencial, 1/min

T_LIMITE_SEGURANCA = 400.0   # K — acima disso consideramos runaway termico
T_MIN_BUSCA = 250.0          # K — limite inferior da varredura de raizes
T_MAX_BUSCA = 800.0          # K — limite superior da varredura de raizes
N_PONTOS_VARREDURA = 1500    # resolucao da varredura (detecta raizes proximas)

# --------------------------------------------------------------------------
# Metadados das variaveis — fonte unica da verdade.
# Usados por ferramentas/validar_caso.py para gerar a tabela do wizard e o DOE.
# --------------------------------------------------------------------------
VARIAVEIS = {
    "descricao": "CSTR nao-isotermico A->B com camisa de resfriamento",
    "entradas": [
        {"nome": "q",   "unidade": "L/min",     "tipo": "Continuous",
         "padrao": 100.0,  "min": 50.0,   "max": 150.0,
         "descricao": "Vazao volumetrica de alimentacao"},
        {"nome": "V",   "unidade": "L",         "tipo": "Continuous",
         "padrao": 100.0,  "min": 80.0,   "max": 150.0,
         "descricao": "Volume util do reator"},
        {"nome": "CAf", "unidade": "mol/L",     "tipo": "Continuous",
         "padrao": 1.0,    "min": 0.5,    "max": 2.0,
         "descricao": "Concentracao de A na alimentacao"},
        {"nome": "Tf",  "unidade": "K",         "tipo": "Continuous",
         "padrao": 350.0,  "min": 300.0,  "max": 370.0,
         "descricao": "Temperatura da alimentacao"},
        {"nome": "Tc",  "unidade": "K",         "tipo": "Continuous",
         "padrao": 300.0,  "min": 280.0,  "max": 340.0,
         "descricao": "Temperatura do fluido refrigerante na camisa"},
        {"nome": "UA",  "unidade": "J/(min.K)", "tipo": "Continuous",
         "padrao": 5.0e4,  "min": 3.0e4,  "max": 8.0e4,
         "descricao": "Coeficiente global de troca x area da camisa"},
    ],
    "saidas": [
        {"nome": "T_reator",       "unidade": "K",      "descricao": "Temperatura no ponto de operacao (partida fria)"},
        {"nome": "CA_saida",       "unidade": "mol/L",  "descricao": "Concentracao de A na saida"},
        {"nome": "conversao",      "unidade": "%",      "descricao": "Conversao de A"},
        {"nome": "produtividade",  "unidade": "mol/min","descricao": "Taxa de producao de B"},
        {"nome": "Q_resfriamento", "unidade": "kW",     "descricao": "Carga termica retirada pela camisa"},
        {"nome": "margem_termica", "unidade": "K",      "descricao": "T_LIMITE_SEGURANCA - T_reator"},
        {"nome": "n_estados",      "unidade": "-",      "descricao": "Numero de estados estacionarios encontrados"},
        {"nome": "T_ramo_quente",  "unidade": "K",      "descricao": "Temperatura do ramo ignitado (= T_reator se unico)"},
        {"nome": "X_ramo_quente",  "unidade": "%",      "descricao": "Conversao no ramo ignitado"},
        {"nome": "salto_ignicao",  "unidade": "K",      "descricao": "T_ramo_quente - T_reator (0 se nao ha multiplicidade)"},
        {"nome": "runaway",        "unidade": "-",      "descricao": "1 se algum ramo estavel ultrapassa o limite de seguranca"},
        {"nome": "convergiu",      "unidade": "-",      "descricao": "1 se a solucao foi obtida com sucesso"},
    ],
}


# --------------------------------------------------------------------------
# Modelo
# --------------------------------------------------------------------------
def _k(T):
    """Constante cinetica de Arrhenius, 1/min."""
    return K0 * math.exp(-EA_SOBRE_R / T)


def _ca_estacionario(T, CAf, tau):
    """Balanco de massa em estado estacionario: CA = CAf / (1 + k.tau)."""
    return CAf / (1.0 + _k(T) * tau)


def _residuo_energia(T, q, V, CAf, Tf, Tc, UA):
    """
    Balanco de energia em estado estacionario, em K.L/min.

    g(T) = conveccao pela alimentacao + calor gerado pela reacao - calor retirado

    As raizes de g(T) sao os estados estacionarios do reator.
    """
    tau = V / q
    ca = _ca_estacionario(T, CAf, tau)
    conveccao = q * (Tf - T)
    gerado = ((-DELTA_HR) / (RHO * CP)) * _k(T) * ca * V
    retirado = (UA / (RHO * CP)) * (T - Tc)
    return conveccao + gerado - retirado


def _bissecao(f, a, b, tol=1e-9, max_iter=200):
    """Bisseccao simples num intervalo que ja contem troca de sinal."""
    fa = f(a)
    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fm = f(m)
        if fm == 0.0 or (b - a) < tol:
            return m
        if (fa < 0.0) != (fm < 0.0):
            b = m
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


def _encontrar_estados(q, V, CAf, Tf, Tc, UA):
    """
    Varre a faixa de temperatura procurando trocas de sinal em g(T) e refina
    cada uma por bisseccao. Devolve lista de (T, estavel) ordenada por T.

    Estabilidade: um estado estacionario e estavel quando dg/dT < 0, ou seja,
    quando a curva de retirada de calor cruza a de geracao "por cima"
    (criterio classico de van Heerden).
    """
    def g(T):
        return _residuo_energia(T, q, V, CAf, Tf, Tc, UA)

    passo = (T_MAX_BUSCA - T_MIN_BUSCA) / N_PONTOS_VARREDURA
    estados = []
    T_ant = T_MIN_BUSCA
    g_ant = g(T_ant)

    for i in range(1, N_PONTOS_VARREDURA + 1):
        T_atual = T_MIN_BUSCA + i * passo
        g_atual = g(T_atual)
        if g_ant == 0.0:
            raiz = T_ant
        elif (g_ant < 0.0) != (g_atual < 0.0):
            raiz = _bissecao(g, T_ant, T_atual)
        else:
            T_ant, g_ant = T_atual, g_atual
            continue

        # derivada numerica central para classificar a estabilidade
        h = 1e-4
        derivada = (g(raiz + h) - g(raiz - h)) / (2.0 * h)
        estados.append((raiz, derivada < 0.0))
        T_ant, g_ant = T_atual, g_atual

    return estados


# --------------------------------------------------------------------------
# Interface exigida pelo AI4Tech Suite (Python Case)
# --------------------------------------------------------------------------
def simulate(inputs):
    """
    Assinatura exigida pela plataforma: simulate(inputs: dict) -> dict.

    Entradas ausentes assumem o valor padrao declarado em VARIAVEIS, de modo que
    variaveis marcadas como Fixed no wizard continuam funcionando.

    Nunca levanta excecao: em caso de entrada invalida devolve convergiu = 0 com
    valores finitos, para nao abortar um lote inteiro de DOE.
    """
    padroes = {v["nome"]: v["padrao"] for v in VARIAVEIS["entradas"]}
    val = {nome: float(inputs.get(nome, padrao)) for nome, padrao in padroes.items()}

    q, V, CAf = val["q"], val["V"], val["CAf"]
    Tf, Tc, UA = val["Tf"], val["Tc"], val["UA"]

    falha = {saida["nome"]: 0.0 for saida in VARIAVEIS["saidas"]}

    if q <= 0.0 or V <= 0.0 or CAf < 0.0 or UA < 0.0 or Tf <= 0.0 or Tc <= 0.0:
        return falha

    estados = _encontrar_estados(q, V, CAf, Tf, Tc, UA)
    if not estados:
        return falha

    estaveis = [T for T, ok in estados if ok]
    # partida fria: o reator sobe de temperatura e para no primeiro ramo estavel
    T_op = min(estaveis) if estaveis else min(T for T, _ in estados)
    T_quente = max(estaveis) if estaveis else max(T for T, _ in estados)

    tau = V / q
    ca = _ca_estacionario(T_op, CAf, tau)
    ca_quente = _ca_estacionario(T_quente, CAf, tau)

    conversao = 100.0 * (CAf - ca) / CAf if CAf > 0.0 else 0.0
    conversao_quente = 100.0 * (CAf - ca_quente) / CAf if CAf > 0.0 else 0.0

    # UA.(T-Tc) esta em J/min; /60000 converte para kW
    q_resfriamento = UA * (T_op - Tc) / 60000.0
    runaway = 1.0 if T_quente > T_LIMITE_SEGURANCA else 0.0

    return {
        "T_reator": T_op,
        "CA_saida": ca,
        "conversao": conversao,
        "produtividade": q * (CAf - ca),
        "Q_resfriamento": q_resfriamento,
        "margem_termica": T_LIMITE_SEGURANCA - T_op,
        "n_estados": float(len(estados)),
        "T_ramo_quente": T_quente,
        "X_ramo_quente": conversao_quente,
        "salto_ignicao": T_quente - T_op,
        "runaway": runaway,
        "convergiu": 1.0,
    }


if __name__ == "__main__":
    resultado = simulate({})
    print("Ponto nominal (q=100, V=100, CAf=1.0, Tf=350, Tc=300, UA=5e4):")
    for chave, valor in resultado.items():
        print("  {:<16} = {:>12.4f}".format(chave, valor))
