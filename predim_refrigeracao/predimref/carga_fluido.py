"""Estimativa da carga de refrigerante e comparação com limites de hidrocarbonetos.

Massa = Σ ρ_in-situ · V por trecho. Nos trechos bifásicos dos trocadores a massa específica
in situ usa a fração de vazio de Rouhani-Axelsson (deslizamento entre fases), mais realista
que o modelo homogêneo, que subestima a massa de líquido. No capilar usa-se o perfil HEM.
Inclui linhas, filtro secador, gás na carcaça do compressor e refrigerante dissolvido no óleo
(hidrocarbonetos são muito solúveis em óleo mineral/POE — premissa a calibrar).

Referências de limite de carga (apenas indicativas; consultar a edição vigente da
IEC 60335-2-89 e a regulamentação local, p. ex. NOM no México e NTC na Colômbia):
150 g (IEC 60335-2-89:2010); 8×LFL e 13×LFL (≈ 304 g e 494 g para R290) nas edições
recentes, conforme o tipo de aparelho e requisitos adicionais.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .propriedades import LFL_KG_M3, Fluido


@dataclass
class ParametrosCargaFluido:
    linha_liquido_L_m: float = 0.3
    linha_liquido_Di_m: float = 3.3e-3
    filtro_secador_cm3: float = 10.0       # volume livre ocupado por líquido
    linha_succao_L_m: float = 1.5
    linha_succao_Di_m: float = 6.0e-3
    linha_descarga_L_m: float = 0.8
    linha_descarga_Di_m: float = 4.75e-3
    volume_livre_carcaca_L: float = 1.0
    T_gas_carcaca_C: float = 50.0
    massa_oleo_kg: float = 0.20
    solubilidade_oleo: float = 0.08        # kg de refrigerante / kg de óleo


def _massa_trocador(res) -> float:
    A = math.pi * res.geometria.Di ** 2 / 4.0
    fator = res.L_adotado / res.L_requerido   # o arranjo adotado tem mais tubo que o requerido
    return sum(s.rho_media * A * s.L for s in res.segmentos) * res.n_circuitos * fator


def _massa_capilar(cap) -> float:
    pf = cap.perfil
    if not pf or len(pf["L"]) < 2:
        return 0.0
    A = math.pi * cap.D ** 2 / 4.0
    m = 0.0
    for i in range(1, len(pf["L"])):
        dL = pf["L"][i] - pf["L"][i - 1]
        m += A * dL * 2.0 / (pf["v"][i] + pf["v"][i - 1])
    return m


def estimar_carga(fl: Fluido, ciclo, cond, evap, cap, p: ParametrosCargaFluido) -> dict:
    e = ciclo.estados
    vol = lambda L, Di: math.pi * Di ** 2 / 4.0 * L  # noqa: E731
    gas_carcaca = fl.estado_PT(e["1s"].P, p.T_gas_carcaca_C + 273.15).rho * p.volume_livre_carcaca_L * 1e-3
    partes = {
        "condensador": _massa_trocador(cond),
        "evaporador": _massa_trocador(evap),
        "linha de líquido + filtro": e["3"].rho * (vol(p.linha_liquido_L_m, p.linha_liquido_Di_m)
                                                   + p.filtro_secador_cm3 * 1e-6),
        "capilar": _massa_capilar(cap),
        "linha de sucção": e["1s"].rho * vol(p.linha_succao_L_m, p.linha_succao_Di_m),
        "linha de descarga": e["2"].rho * vol(p.linha_descarga_L_m, p.linha_descarga_Di_m),
        "gás na carcaça": gas_carcaca,
        "dissolvido no óleo": p.massa_oleo_kg * p.solubilidade_oleo,
    }
    total = sum(partes.values())
    limites = {}
    lfl = LFL_KG_M3.get(fl.nome)
    if fl.hidrocarboneto and lfl is not None:   # A3: limites de carga de aparelhos autocontidos
        limites = {"IEC 60335-2-89:2010 (150 g)": 0.150,
                   f"8×LFL ({8 * lfl * 1e3:.0f} g)": 8 * lfl,
                   f"13×LFL ({13 * lfl * 1e3:.0f} g)": 13 * lfl}
    return {"partes_kg": partes, "total_kg": total, "limites_kg": limites,
            "inflamavel": lfl is not None, "A3": fl.hidrocarboneto}
