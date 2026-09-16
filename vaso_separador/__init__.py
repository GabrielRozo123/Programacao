"""Dimensionamento de vaso de nocaute gas-liquido e preparacao do estudo de CFD.

Fluxo de uso:

    from vaso_separador.casos import CASOS, CRITERIOS_POR_CASO
    from vaso_separador.dimensionamento import dimensionar_vaso_vertical
    from vaso_separador.relatorio import relatorio
    from vaso_separador.starccm import gerar_cartao

    dim = dimensionar_vaso_vertical(CASOS["propeno_refrigeracao"],
                                    CRITERIOS_POR_CASO["propeno_refrigeracao"])
    print(relatorio(dim))
    print(gerar_cartao(dim).texto())

Para um caso proprio, monte a Corrente com os dados da folha de dados do cliente
e ajuste os Criterios conforme a norma adotada.
"""

from .arraste import (
    diametro_maximo_estavel,
    diametro_para_velocidade_terminal,
    numero_de_weber,
    tabela_de_velocidades_terminais,
    velocidade_terminal,
)
from .dimensionamento import Corrente, Criterios, dimensionar_vaso_vertical
from .souders_brown import (
    FATORES_K,
    K_para_remover_gota,
    diametro_de_gota_implicito,
    souders_brown,
    velocidade_maxima,
)

__all__ = [
    "Corrente",
    "Criterios",
    "dimensionar_vaso_vertical",
    "souders_brown",
    "velocidade_maxima",
    "diametro_de_gota_implicito",
    "K_para_remover_gota",
    "FATORES_K",
    "velocidade_terminal",
    "diametro_para_velocidade_terminal",
    "tabela_de_velocidades_terminais",
    "diametro_maximo_estavel",
    "numero_de_weber",
]
