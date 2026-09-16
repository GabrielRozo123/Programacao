#!/usr/bin/env python3
"""Gera todas as figuras do estudo em figuras/, nos temas claro e escuro."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from vaso_separador import graficos
from vaso_separador.casos import CASOS, CRITERIOS_POR_CASO
from vaso_separador.dimensionamento import dimensionar_vaso_vertical

CASO_PRINCIPAL = "propeno_refrigeracao"


def main() -> int:
    destino = RAIZ / "figuras"
    destino.mkdir(exist_ok=True)

    dims = {k: dimensionar_vaso_vertical(CASOS[k], CRITERIOS_POR_CASO[k]) for k in CASOS}
    principal = dims[CASO_PRINCIPAL]

    for tema in ("claro", "escuro"):
        sufixo = "" if tema == "claro" else "_escuro"
        gerados = [
            graficos.figura_velocidade_terminal(
                principal, destino / f"01_velocidade_terminal{sufixo}.png", tema),
            graficos.figura_efeito_da_pressao(
                principal, destino / f"02_efeito_da_pressao{sufixo}.png", tema),
            graficos.figura_eficiencia(
                principal, destino / f"03_eficiencia{sufixo}.png", tema),
            graficos.figura_comparativo(
                list(dims.values()), destino / f"04_comparativo{sufixo}.png", tema),
        ]
        for g in gerados:
            print(f"  {g.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
