#!/usr/bin/env python3
"""
Validador local de Python Cases do AI4Tech Suite.

Roda o caso na sua maquina ANTES de subir para a plataforma. Serve para tres
coisas que economizam quota de simulacao na nuvem:

  1. Garantir que simulate() existe, aceita um dict e devolve um dict de floats.
  2. Rodar um DOE (Latin Hypercube) local e medir taxa de falha e tempo por run.
  3. Detectar saidas constantes ou nao-finitas — que quebram surrogate e
     otimizacao mais adiante, ja com a quota gasta.

Uso:
    python3 ferramentas/validar_caso.py casos-python/01-cstr-nao-isotermico/simulate.py
    python3 ferramentas/validar_caso.py <caso.py> --n 200 --csv saida.csv
    python3 ferramentas/validar_caso.py <caso.py> --tabela

Sem dependencias externas: roda em qualquer Python 3.8+.
"""

import argparse
import importlib.util
import math
import os
import random
import sys
import time


# --------------------------------------------------------------------------
# Carregamento do caso
# --------------------------------------------------------------------------
def carregar_caso(caminho):
    """Importa um arquivo .py isolado como modulo e devolve o objeto modulo."""
    caminho = os.path.abspath(caminho)
    if not os.path.isfile(caminho):
        sys.exit("ERRO: arquivo nao encontrado: {}".format(caminho))

    spec = importlib.util.spec_from_file_location("caso_ai4tech", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    if not hasattr(modulo, "simulate"):
        sys.exit("ERRO: o arquivo nao define a funcao simulate(inputs: dict) -> dict")
    if not hasattr(modulo, "VARIAVEIS"):
        sys.exit("ERRO: o arquivo nao define o dicionario VARIAVEIS "
                 "(entradas/saidas) usado para gerar o DOE")
    return modulo


# --------------------------------------------------------------------------
# Amostragem: Latin Hypercube em Python puro
# --------------------------------------------------------------------------
def amostrar_lhs(n, entradas, semente=42):
    """
    Latin Hypercube: cada variavel tem sua faixa dividida em n estratos e cada
    estrato e visitado exatamente uma vez. Cobre o espaco muito melhor que
    amostragem aleatoria pura com o mesmo numero de simulacoes.

    Variaveis 'Fixed' ficam no valor padrao; 'Discrete' sao arredondadas ao
    passo declarado.
    """
    rng = random.Random(semente)
    variaveis = [v for v in entradas if v.get("tipo", "Continuous") != "Fixed"]

    colunas = {}
    for v in variaveis:
        estratos = [(i + rng.random()) / n for i in range(n)]
        rng.shuffle(estratos)
        colunas[v["nome"]] = estratos

    amostras = []
    for i in range(n):
        ponto = {}
        for v in entradas:
            if v.get("tipo", "Continuous") == "Fixed":
                ponto[v["nome"]] = v["padrao"]
                continue
            lo, hi = v["min"], v["max"]
            valor = lo + colunas[v["nome"]][i] * (hi - lo)
            if v.get("tipo") == "Discrete" and v.get("passo"):
                passo = v["passo"]
                valor = lo + round((valor - lo) / passo) * passo
                valor = min(max(valor, lo), hi)
            ponto[v["nome"]] = valor
        amostras.append(ponto)
    return amostras


# --------------------------------------------------------------------------
# Estatistica minima (previa do que o modulo Analysis vai mostrar)
# --------------------------------------------------------------------------
def pearson(x, y):
    n = len(x)
    if n < 2:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0.0 or syy <= 0.0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def postos(v):
    """Postos com media em caso de empate (necessario para Spearman correto)."""
    ordenado = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(ordenado):
        j = i
        while j + 1 < len(ordenado) and v[ordenado[j + 1]] == v[ordenado[i]]:
            j += 1
        media = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[ordenado[k]] = media
        i = j + 1
    return r


def spearman(x, y):
    return pearson(postos(x), postos(y))


# --------------------------------------------------------------------------
# Relatorios
# --------------------------------------------------------------------------
def imprimir_tabela(modulo):
    """Imprime as tabelas prontas para colar no wizard de variaveis da suite."""
    var = modulo.VARIAVEIS
    print("\n### Variaveis de entrada\n")
    print("| Name | Cell | Unit | Type | Default | Min | Max |")
    print("|---|---|---|---|---|---|---|")
    for v in var["entradas"]:
        tipo = v.get("tipo", "Continuous")
        if tipo == "Fixed":
            faixa = ("—", "—")
        else:
            faixa = ("{:g}".format(v["min"]), "{:g}".format(v["max"]))
        print("| {} | `{}` | {} | {} | {:g} | {} | {} |".format(
            v["nome"], v["nome"], v["unidade"], tipo, v["padrao"], faixa[0], faixa[1]))

    print("\n### Variaveis de saida\n")
    print("| Name | Cell | Unit |")
    print("|---|---|---|")
    for v in var["saidas"]:
        print("| {} | `{}` | {} |".format(v["nome"], v["nome"], v["unidade"]))
    print("\nA coluna Cell e a chave do dicionario — deve bater exatamente com o codigo.\n")


def executar(modulo, n, semente):
    """Roda o DOE local e devolve (linhas, nomes_entrada, nomes_saida, falhas, tempo)."""
    entradas = modulo.VARIAVEIS["entradas"]
    nomes_entrada = [v["nome"] for v in entradas]
    nomes_saida = [v["nome"] for v in modulo.VARIAVEIS["saidas"]]

    amostras = amostrar_lhs(n, entradas, semente)
    linhas, falhas = [], []
    inicio = time.time()

    for i, ponto in enumerate(amostras):
        try:
            saida = modulo.simulate(dict(ponto))
        except Exception as exc:            # noqa: BLE001 — queremos capturar tudo
            falhas.append((i, "excecao: {}".format(exc)))
            continue

        if not isinstance(saida, dict):
            falhas.append((i, "simulate() nao devolveu dict"))
            continue

        ausentes = [k for k in nomes_saida if k not in saida]
        if ausentes:
            falhas.append((i, "saidas ausentes: {}".format(", ".join(ausentes))))
            continue

        valores = {}
        problema = None
        for k in nomes_saida:
            try:
                valor = float(saida[k])
            except (TypeError, ValueError):
                problema = "saida '{}' nao e numerica".format(k)
                break
            if not math.isfinite(valor):
                problema = "saida '{}' nao finita ({})".format(k, saida[k])
                break
            valores[k] = valor

        if problema:
            falhas.append((i, problema))
            continue

        linhas.append((ponto, valores))

    return linhas, nomes_entrada, nomes_saida, falhas, time.time() - inicio


def relatorio(linhas, nomes_entrada, nomes_saida, falhas, duracao, n):
    print("\n" + "=" * 72)
    print("RESULTADO DA VALIDACAO")
    print("=" * 72)
    print("Simulacoes solicitadas : {}".format(n))
    print("Bem-sucedidas          : {}".format(len(linhas)))
    print("Falhas                 : {}".format(len(falhas)))
    print("Tempo total            : {:.2f} s  ({:.1f} ms por run)".format(
        duracao, 1000.0 * duracao / max(n, 1)))

    if falhas:
        print("\nPrimeiras falhas:")
        for indice, motivo in falhas[:5]:
            print("  run {:>4}: {}".format(indice, motivo))

    if not linhas:
        print("\nNenhum run valido — corrija o caso antes de subir para a plataforma.")
        return 1

    print("\nFaixa das saidas no DOE local:")
    print("  {:<18} {:>14} {:>14} {:>14}".format("saida", "min", "media", "max"))
    constantes = []
    for k in nomes_saida:
        col = [v[k] for _, v in linhas]
        lo, hi = min(col), max(col)
        print("  {:<18} {:>14.5g} {:>14.5g} {:>14.5g}".format(
            k, lo, sum(col) / len(col), hi))
        if hi - lo < 1e-12:
            constantes.append(k)

    if constantes:
        print("\n  AVISO: saidas constantes neste DOE -> {}".format(", ".join(constantes)))
        print("  Uma saida constante nao pode ser aprendida por surrogate nem")
        print("  otimizada. Amplie as faixas de entrada ou remova a saida.")

    print("\nPrevia de dependencia (o modulo Analysis fara isso com muito mais metodos):")
    print("  {:<12} {:<18} {:>10} {:>10}".format("entrada", "saida", "Pearson", "Spearman"))
    for ent in nomes_entrada:
        x = [p[ent] for p, _ in linhas]
        for sai in nomes_saida:
            y = [v[sai] for _, v in linhas]
            r = pearson(x, y)
            rho = spearman(x, y)
            if math.isfinite(r) and abs(r) >= 0.3:
                print("  {:<12} {:<18} {:>10.3f} {:>10.3f}".format(ent, sai, r, rho))
    print("\nDica: pares com Spearman alto e Pearson baixo indicam relacao monotona")
    print("nao-linear — e onde HSIC e o xi de Chatterjee, no modulo Analysis, brilham.\n")
    return 0


def gravar_csv(caminho, linhas, nomes_entrada, nomes_saida):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(",".join(nomes_entrada + nomes_saida) + "\n")
        for entrada, saida in linhas:
            campos = ["{:.10g}".format(entrada[k]) for k in nomes_entrada]
            campos += ["{:.10g}".format(saida[k]) for k in nomes_saida]
            arquivo.write(",".join(campos) + "\n")
    print("CSV gravado em: {}".format(caminho))


def main():
    parser = argparse.ArgumentParser(
        description="Valida um Python Case do AI4Tech Suite localmente.")
    parser.add_argument("caso", help="caminho do arquivo .py com simulate()")
    parser.add_argument("--n", type=int, default=100, help="pontos do DOE local (padrao 100)")
    parser.add_argument("--semente", type=int, default=42, help="semente do LHS (padrao 42)")
    parser.add_argument("--csv", help="grava os resultados neste arquivo CSV")
    parser.add_argument("--tabela", action="store_true",
                        help="apenas imprime a tabela de variaveis para o wizard")
    args = parser.parse_args()

    modulo = carregar_caso(args.caso)
    print("Caso carregado: {}".format(modulo.VARIAVEIS.get("descricao", args.caso)))

    if args.tabela:
        imprimir_tabela(modulo)
        return 0

    print("Executando run unico com os valores padrao...")
    nominal = modulo.simulate({})
    for chave, valor in nominal.items():
        print("  {:<18} = {:>14.5g}".format(chave, float(valor)))

    print("\nExecutando DOE local (LHS, {} pontos)...".format(args.n))
    linhas, ents, sais, falhas, duracao = executar(modulo, args.n, args.semente)
    codigo = relatorio(linhas, ents, sais, falhas, duracao, args.n)

    if args.csv and linhas:
        gravar_csv(args.csv, linhas, ents, sais)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
