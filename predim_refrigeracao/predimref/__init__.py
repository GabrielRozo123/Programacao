"""predimref — pré-dimensionamento de ciclos de refrigeração por compressão de vapor
para refrigeradores comerciais de bebidas (visi-coolers).

Fluxo do cálculo (ver ``projeto.dimensionar``):

1. capacidade do gabinete (litros <-> garrafas) e carga térmica (``gabinete``);
2. ciclo termodinâmico com propriedades de equação de estado (CoolProp / HEOS),
   consistência do COP pedido com Carnot e com o compressor real (``ciclo``);
3. compressor: vazão mássica, deslocamento volumétrico, ponto de catálogo (``compressor``);
4. condensador e evaporador aletados, dimensionados segmento a segmento com ε-NTU,
   correlações locais e queda de pressão (``trocador``);
5. tubo capilar adiabático pelo modelo homogêneo com detecção de blocagem (``capilar``);
6. carga de refrigerante, balanço de energia e de exergia, avisos de projeto.

Unidades internas: SI (Pa, K, J/kg, m, kg/s, W). A interface de alto nível aceita °C e litros.
"""

__version__ = "0.1.0"

from .avisos import ErroProjeto
from .projeto import EntradasProjeto, ParametrosProjeto, ResultadoProjeto, dimensionar

__all__ = ["ErroProjeto", "EntradasProjeto", "ParametrosProjeto", "ResultadoProjeto", "dimensionar"]
