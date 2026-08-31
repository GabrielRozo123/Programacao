#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitor minimo de .xlsx em Python puro, para trazer resultados do AI4Tech Suite
de volta ao repositorio sem depender de openpyxl ou pandas.

Um .xlsx e um zip de XML. Este modulo le a primeira planilha, resolve strings
compartilhadas e inline, e devolve uma lista de linhas.

Uso:
    python3 ferramentas/ler_xlsx.py resultados.xlsx            # resumo
    python3 ferramentas/ler_xlsx.py resultados.xlsx --csv s.csv
"""

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _coluna_para_indice(referencia):
    """'BC12' -> 54 (indice 0-based da coluna)."""
    letras = re.match(r"([A-Z]+)", referencia or "A").group(1)
    n = 0
    for c in letras:
        n = n * 26 + (ord(c) - ord("A") + 1)
    return n - 1


def _texto(elemento):
    """Concatena todo o texto de um no, inclusive <t> aninhados em <is>/<si>."""
    return "".join(t.text or "" for t in elemento.iter(NS + "t"))


def ler(caminho, indice_planilha=0):
    """Devolve (nome_da_planilha, linhas) — linhas e lista de listas de str."""
    with zipfile.ZipFile(caminho) as z:
        nomes = z.namelist()

        compartilhadas = []
        if "xl/sharedStrings.xml" in nomes:
            raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
            compartilhadas = [_texto(si) for si in raiz.findall(NS + "si")]

        planilhas = sorted(n for n in nomes
                           if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        if not planilhas:
            raise ValueError("nenhuma planilha encontrada em %s" % caminho)
        alvo = planilhas[indice_planilha]

        try:
            wb = ET.fromstring(z.read("xl/workbook.xml"))
            rotulos = [s.get("name") for s in wb.iter(NS + "sheet")]
            nome = rotulos[indice_planilha]
        except Exception:
            nome = alvo

        raiz = ET.fromstring(z.read(alvo))

    linhas = []
    for linha in raiz.iter(NS + "row"):
        celulas = {}
        for c in linha.findall(NS + "c"):
            tipo = c.get("t")
            if tipo == "s":                                   # string compartilhada
                v = c.find(NS + "v")
                valor = compartilhadas[int(v.text)] if v is not None else ""
            elif tipo == "inlineStr":                          # string inline
                elem = c.find(NS + "is")
                valor = _texto(elem) if elem is not None else ""
            else:                                              # numero, bool, data
                v = c.find(NS + "v")
                valor = v.text if v is not None else ""
            celulas[_coluna_para_indice(c.get("r"))] = valor
        if celulas:
            largura = max(celulas) + 1
            linhas.append([celulas.get(i, "") for i in range(largura)])
    return nome, linhas


def main():
    parser = argparse.ArgumentParser(description="Le um .xlsx sem dependencias externas.")
    parser.add_argument("arquivo")
    parser.add_argument("--csv", help="grava o conteudo neste arquivo CSV")
    parser.add_argument("--linhas", type=int, default=5, help="linhas de amostra a exibir")
    args = parser.parse_args()

    nome, linhas = ler(args.arquivo)
    print("Planilha : %s" % nome)
    print("Linhas   : %d  (1 cabecalho + %d dados)" % (len(linhas), max(len(linhas)-1, 0)))
    if not linhas:
        return 1
    print("Colunas  : %d" % len(linhas[0]))
    print("\nCabecalho:")
    for i, nome_col in enumerate(linhas[0]):
        print("  %2d  %s" % (i, nome_col))
    print("\nPrimeiras %d linhas de dados:" % args.linhas)
    for linha in linhas[1:1+args.linhas]:
        print("  " + " | ".join(linha[:8]) + (" | ..." if len(linha) > 8 else ""))

    if args.csv:
        with open(args.csv, "w", encoding="utf-8") as f:
            for linha in linhas:
                f.write(",".join('"%s"' % c if "," in c else c for c in linha) + "\n")
        print("\nCSV gravado em: %s" % args.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
