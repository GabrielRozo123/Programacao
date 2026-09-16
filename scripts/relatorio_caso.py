#!/usr/bin/env python3
"""Gera o relatorio de dimensionamento e o cartao de setup do STAR-CCM+.

Uso:
    python3 scripts/relatorio_caso.py                          # caso padrao
    python3 scripts/relatorio_caso.py propeno_refrigeracao
    python3 scripts/relatorio_caso.py --todos
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vaso_separador.casos import CASOS, CRITERIOS_POR_CASO
from vaso_separador.dimensionamento import dimensionar_vaso_vertical
from vaso_separador.relatorio import relatorio
from vaso_separador.starccm import gerar_cartao

PADRAO = "propeno_refrigeracao"


def roda(chave: str, com_cartao: bool = True) -> None:
    dim = dimensionar_vaso_vertical(CASOS[chave], CRITERIOS_POR_CASO[chave])
    print(relatorio(dim))
    if com_cartao:
        print()
        print(gerar_cartao(dim).texto())


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args and args[0] == "--todos":
        for chave in CASOS:
            roda(chave, com_cartao=False)
            print("\n")
        return 0
    chave = args[0] if args else PADRAO
    if chave not in CASOS:
        print(f"caso desconhecido: {chave}\ndisponiveis: {', '.join(CASOS)}", file=sys.stderr)
        return 2
    roda(chave)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
