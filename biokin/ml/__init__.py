"""Camada de aprendizado de máquina do pacote.

Três ferramentas, cada uma respondendo a uma pergunta distinta:

:mod:`biokin.ml.mlp`
    Rede neural densa em numpy puro. Serve de *teto de desempenho*: é o
    melhor ajuste alcançável por uma função flexível sem qualquer estrutura
    mecanística. Se o melhor modelo LHHW empata com ela, a forma
    mecanística está capturando tudo o que há nos dados; se perde por muito,
    falta estrutura ao mecanismo — ou sobra ruído aos dados.

:mod:`biokin.ml.surrogate`
    Extração de velocidades de reação a partir de perfis de concentração,
    por suavização e inversão da matriz estequiométrica. Converte dados
    integrais em dados diferenciais sem comprometer-se com nenhum modelo.

:mod:`biokin.ml.sparse`
    Regressão racional esparsa. Descobre a *forma* de numerador e
    denominador diretamente dos dados, sem enumerar mecanismos — e aponta
    quais termos de inibição têm suporte empírico.
"""

from .mlp import MLP, StandardScaler
from .sparse import RationalModel, fit_rational_sparse, rational_library
from .surrogate import RateTable, estimate_rate_table, smooth_profile

__all__ = [
    "MLP",
    "StandardScaler",
    "RationalModel",
    "fit_rational_sparse",
    "rational_library",
    "RateTable",
    "estimate_rate_table",
    "smooth_profile",
]
