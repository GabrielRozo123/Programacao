"""
MCDM sobre a frente de Pareto do splitter C3 — TOPSIS e VIKOR.

A pergunta: a escolha que fizemos por argumento de engenharia (tres cascos,
robustez a alimentacao pobre) e a mesma que um metodo formal de decisao
multicriterio escolhe? E, mais importante: quanto os pesos precisam mudar para
a resposta mudar?

Sem dependencias externas. So `math`.
"""

import math
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "casos-python", "02-splitter-c3"))
import simulate as tw  # noqa: E402

Z_NOMINAL = 0.75
Z_PIOR = 0.60
PUREZA_MINIMA = 99.7      # especificacao com margem, igual a otimizacao
GRAU_POLIMERO = 99.5      # o degrau de preco
APROX_MINIMA = 5.0        # K, agua de resfriamento economicamente viavel


def avaliar(x, z=Z_NOMINAL):
    return tw.simulate({
        "N_estagios": x["N"],
        "pos_alimentacao": x["pos"],
        "razao_refluxo": x["R"],
        "corte_pct": x["corte"],
        "pressao": x["P"],
        "z_propeno": z,
        "F_alimentacao": 1000.0,
    })


def viavel(r):
    return (r["convergiu"] == 1.0
            and r["pureza_topo"] >= PUREZA_MINIMA
            and r["aprox_condensador"] >= APROX_MINIMA
            and r["R_sobre_Rmin"] >= 1.1)


def lhs(n, faixas, semente=20260902):
    """Hipercubo latino, sem numpy."""
    rng = random.Random(semente)
    dim = len(faixas)
    cols = []
    for j in range(dim):
        fatias = [(i + rng.random()) / n for i in range(n)]
        rng.shuffle(fatias)
        cols.append(fatias)
    pts = []
    for i in range(n):
        p = {}
        for j, (nome, lo, hi) in enumerate(faixas):
            p[nome] = lo + cols[j][i] * (hi - lo)
        pts.append(p)
    return pts


def nao_dominados(pontos, chaves_max, chaves_min):
    """Filtro de Pareto O(n^2). n e pequeno."""
    frente = []
    for i, a in enumerate(pontos):
        dominado = False
        for j, b in enumerate(pontos):
            if i == j:
                continue
            melhor_ou_igual = (
                all(b[k] >= a[k] for k in chaves_max)
                and all(b[k] <= a[k] for k in chaves_min))
            estrito = (
                any(b[k] > a[k] for k in chaves_max)
                or any(b[k] < a[k] for k in chaves_min))
            if melhor_ou_igual and estrito:
                dominado = True
                break
        if not dominado:
            frente.append(a)
    return frente


# ---------------------------------------------------------------- normalizacao

def normaliza_beneficio(matriz, sentidos):
    """Min-max para [0,1], ja com todo criterio apontando para 'maior e melhor'."""
    n, m = len(matriz), len(matriz[0])
    out = [[0.0] * m for _ in range(n)]
    for j in range(m):
        col = [matriz[i][j] for i in range(n)]
        lo, hi = min(col), max(col)
        span = hi - lo
        for i in range(n):
            if span < 1e-12:
                out[i][j] = 1.0
            elif sentidos[j] > 0:
                out[i][j] = (matriz[i][j] - lo) / span
            else:
                out[i][j] = (hi - matriz[i][j]) / span
    return out


def pesos_entropia(matriz, sentidos):
    """Peso pela entropia de Shannon: criterio que discrimina mais, pesa mais."""
    b = normaliza_beneficio(matriz, sentidos)
    n, m = len(b), len(b[0])
    eps = 1e-12
    w = []
    k = 1.0 / math.log(n)
    for j in range(m):
        soma = sum(b[i][j] for i in range(n)) + eps
        e = 0.0
        for i in range(n):
            p = (b[i][j] + eps) / soma
            e -= p * math.log(p)
        w.append(1.0 - k * e)
    total = sum(w) or 1.0
    return [v / total for v in w]


# ---------------------------------------------------------------------- TOPSIS

def topsis(matriz, sentidos, pesos):
    n, m = len(matriz), len(matriz[0])
    norma = []
    for j in range(m):
        s = math.sqrt(sum(matriz[i][j] ** 2 for i in range(n))) or 1.0
        norma.append(s)
    v = [[pesos[j] * matriz[i][j] / norma[j] for j in range(m)] for i in range(n)]
    ideal, anti = [], []
    for j in range(m):
        col = [v[i][j] for i in range(n)]
        ideal.append(max(col) if sentidos[j] > 0 else min(col))
        anti.append(min(col) if sentidos[j] > 0 else max(col))
    escores = []
    for i in range(n):
        dp = math.sqrt(sum((v[i][j] - ideal[j]) ** 2 for j in range(m)))
        dm = math.sqrt(sum((v[i][j] - anti[j]) ** 2 for j in range(m)))
        escores.append(dm / (dp + dm) if (dp + dm) > 0 else 0.0)
    return escores


# ----------------------------------------------------------------------- VIKOR

def vikor(matriz, sentidos, pesos, v=0.5):
    n, m = len(matriz), len(matriz[0])
    melhor, pior = [], []
    for j in range(m):
        col = [matriz[i][j] for i in range(n)]
        melhor.append(max(col) if sentidos[j] > 0 else min(col))
        pior.append(min(col) if sentidos[j] > 0 else max(col))
    S, R = [], []
    for i in range(n):
        parcelas = []
        for j in range(m):
            span = melhor[j] - pior[j]
            perda = 0.0 if abs(span) < 1e-12 else (melhor[j] - matriz[i][j]) / span
            parcelas.append(pesos[j] * perda)
        S.append(sum(parcelas))
        R.append(max(parcelas))
    Se, Sp = min(S), max(S)
    Re, Rp = min(R), max(R)
    Q = []
    for i in range(n):
        a = 0.0 if abs(Sp - Se) < 1e-12 else (S[i] - Se) / (Sp - Se)
        b = 0.0 if abs(Rp - Re) < 1e-12 else (R[i] - Re) / (Rp - Re)
        Q.append(v * a + (1 - v) * b)
    return Q, S, R


def spearman(pa, pb):
    """Correlacao de Spearman entre dois vetores de POSTOS."""
    n = len(pa)
    d2 = sum((pa[i] - pb[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))


def postos(valores, maior_melhor=True):
    ordem = sorted(range(len(valores)), key=lambda i: valores[i],
                   reverse=maior_melhor)
    p = [0] * len(valores)
    for posto, i in enumerate(ordem, start=1):
        p[i] = posto
    return p
