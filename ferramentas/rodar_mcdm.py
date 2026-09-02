"""
Decisao multicriterio sobre a frente de Pareto do splitter C3.

Roda duas vezes:
  A) frente nos objetivos que o NSGA-II usou  — recuperacao (max), Q (min)
  B) frente nos objetivos economicos          — lucro (max), pureza no pior caso (max)

e mostra que a diferenca entre as duas respostas nao esta no metodo de decisao.
"""

import csv
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from mcdm_pareto import (Z_PIOR, avaliar, lhs, nao_dominados,
                         normaliza_beneficio, pesos_entropia, postos, spearman,
                         topsis, viavel, vikor)

FAIXAS = [("N", 180.0, 320.0), ("pos", 0.55, 0.75), ("R", 13.0, 22.0),
          ("corte", 99.50, 99.95), ("P", 16.5, 21.0)]
N_AMOSTRAS = 6000
CACHE = os.path.join(AQUI, "..", "dados", "mcdm-viaveis.csv")

CAMPOS = ["N", "pos", "R", "corte", "P", "lucro", "pureza_nom", "pureza_pior",
          "Q", "cascos", "recuperacao", "altura", "aprox", "precisa_refrig"]


def gerar_cache():
    print("amostrando %d projetos (cache ausente)..." % N_AMOSTRAS)
    linhas = []
    for p in lhs(N_AMOSTRAS, FAIXAS):
        p["N"] = round(p["N"] / 10.0) * 10.0
        r = avaliar(p)
        if not viavel(r):
            continue
        pior = avaliar(p, z=Z_PIOR)["pureza_topo"]
        linhas.append({
            "N": p["N"], "pos": p["pos"], "R": p["R"], "corte": p["corte"],
            "P": p["P"], "lucro": r["lucro"], "pureza_nom": r["pureza_topo"],
            "pureza_pior": pior, "Q": r["Q_refervedor"], "cascos": r["n_cascos"],
            "recuperacao": r["recuperacao"], "altura": r["altura_total"],
            "aprox": r["aprox_condensador"], "precisa_refrig": r["precisa_refrig"]})
    with open(CACHE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, CAMPOS)
        w.writeheader()
        for l in linhas:
            w.writerow({k: "%.6f" % l[k] for k in CAMPOS})
    return linhas


def carregar_cache():
    with open(CACHE, encoding="utf-8") as f:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]


pontos = carregar_cache() if os.path.exists(CACHE) else gerar_cache()
print("projetos viaveis: %d" % len(pontos))

NOMES = ["lucro", "pureza z=0,60", "Q refervedor", "cascos"]
SENTIDOS = [1, 1, -1, -1]
CHAVES = ["lucro", "pureza_pior", "Q", "cascos"]

CENARIOS = {
    "entropia":  None,                    # calculado por frente
    "iguais":    [0.25, 0.25, 0.25, 0.25],
    "economico": [0.55, 0.15, 0.20, 0.10],
    "robustez":  [0.25, 0.45, 0.15, 0.15],
}


def topsis_minmax(matriz, sentidos, pesos):
    """TOPSIS com normalizacao min-max no lugar da vetorial."""
    b = normaliza_beneficio(matriz, sentidos)     # tudo ja em [0,1], maior=melhor
    return topsis(b, [1] * len(sentidos), pesos)


def rotulo(s):
    return "N=%3d R=%5.2f P=%5.2f | L=%6.2f pior=%7.4f Q=%5.1f c=%d" % (
        s["N"], s["R"], s["P"], s["lucro"], s["pureza_pior"], s["Q"], s["cascos"])


def analisar(titulo, frente):
    print("\n" + "=" * 96)
    print("%s  —  %d solucoes na frente" % (titulo, len(frente)))
    print("=" * 96)
    matriz = [[s[k] for k in CHAVES] for s in frente]
    w_ent = pesos_entropia(matriz, SENTIDOS)
    print("pesos por entropia: " + "  ".join(
        "%s=%.3f" % (n, w) for n, w in zip(NOMES, w_ent)))

    print("\n%-10s | %-11s | %-46s | %-46s" %
          ("cenario", "metodo", "escolha", "concordancia"))
    print("-" * 96)
    for nome_c, w in CENARIOS.items():
        w = w_ent if w is None else w
        tv = topsis(matriz, SENTIDOS, w)              # normalizacao vetorial
        tm = topsis_minmax(matriz, SENTIDOS, w)       # normalizacao min-max
        q, S, R = vikor(matriz, SENTIDOS, w)
        iv = max(range(len(tv)), key=lambda i: tv[i])
        im = max(range(len(tm)), key=lambda i: tm[i])
        iq = min(range(len(q)), key=lambda i: q[i])
        rho_v = spearman(postos(tv, True), postos(q, False))
        rho_m = spearman(postos(tm, True), postos(q, False))
        print("%-10s | %-11s | %-46s | rho vs VIKOR = %+.3f"
              % (nome_c, "TOPSIS vet", rotulo(frente[iv]), rho_v))
        print("%-10s | %-11s | %-46s | rho vs VIKOR = %+.3f"
              % ("", "TOPSIS mm", rotulo(frente[im]), rho_m))
        print("%-10s | %-11s | %-46s |" % ("", "VIKOR", rotulo(frente[iq])))
        print("-" * 96)
    return matriz, w_ent


# ------------------------------------------------------------------- frente A
frenteA = nao_dominados(pontos, chaves_max=["recuperacao"], chaves_min=["Q"])
frenteA.sort(key=lambda d: d["Q"])
analisar("A) objetivos do NSGA-II — recuperacao (max), Q (min)", frenteA)

# ------------------------------------------------------------------- frente B
frenteB = nao_dominados(pontos, chaves_max=["lucro", "pureza_pior"], chaves_min=[])
frenteB.sort(key=lambda d: -d["lucro"])
analisar("B) objetivos economicos — lucro (max), pureza no pior caso (max)", frenteB)

# ------------------------------------------------- o projeto que escolhemos
melhor_lucro = max(pontos, key=lambda s: s["lucro"])
print("\nmaior lucro entre TODOS os %d viaveis: %s" % (len(pontos), rotulo(melhor_lucro)))
naA = any(abs(s["lucro"] - melhor_lucro["lucro"]) < 1e-9 for s in frenteA)
naB = any(abs(s["lucro"] - melhor_lucro["lucro"]) < 1e-9 for s in frenteB)
print("  esta na frente A (recuperacao x Q)? %s" % ("SIM" if naA else "NAO"))
print("  esta na frente B (lucro x robustez)? %s" % ("SIM" if naB else "NAO"))

for nome, fr in (("A", frenteA), ("B", frenteB)):
    print("  melhor lucro DENTRO da frente %s: %.3f MUSD" % (nome, max(s["lucro"] for s in fr)))

with open(os.path.join(AQUI, "..", "dados", "mcdm-frente-economica.csv"),
          "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, CAMPOS)
    w.writeheader()
    for s in frenteB:
        w.writerow({k: "%.6f" % s[k] for k in CAMPOS})
print("\nfrente B salva em dados/mcdm-frente-economica.csv")
