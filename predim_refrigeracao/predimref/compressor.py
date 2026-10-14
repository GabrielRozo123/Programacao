"""Compressor alternativo hermético: deslocamento volumétrico e conversão para ponto de catálogo.

Rendimento volumétrico (modelo de espaço morto com fator de perdas):
    η_v = f_v [1 + C − C (P_desc/P_suc)^(1/n)]
C fração de espaço morto, n expoente de reexpansão (≈ cp/cv do vapor na sucção) e f_v o
fator que reúne aquecimento do gás na sucção, vazamentos e perdas nas válvulas.
Referência: Stoecker & Jones, Refrigeration and Air Conditioning, cap. 11; Gosney,
Principles of Refrigeration, cap. 2. Os valores padrão são típicos; o ideal é calibrar
η_v e η_global com o catálogo do compressor candidato (Embraco, Secop, Tecumseh...).

Condições nominais de catálogo (tabela de condições de ensaio do catálogo Embraco):
    EN 12900 LBP −35/40 °C, MBP −10/45 °C, HBP +5/50 °C; gás de retorno 20 °C; sem sub-resfriamento
    ASHRAE LBP −23,3/54,4 °C; retorno 32,2 °C; líquido 32,2 °C
    ASHRAE M/HBP +7,2/54,4 °C; retorno 35 °C; líquido 46,1 °C
    CECOMAF LBP −25/55 °C; retorno 32 °C; sem sub-resfriamento
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .propriedades import Estado, Fluido

CONDICOES_NOMINAIS = {
    # nome: (T_evap °C, T_cond °C, T_retorno °C, T_liquido °C ou None = líquido saturado)
    "EN12900_LBP": (-35.0, 40.0, 20.0, None),
    "EN12900_MBP": (-10.0, 45.0, 20.0, None),
    "EN12900_HBP": (5.0, 50.0, 20.0, None),
    "ASHRAE_LBP": (-23.3, 54.4, 32.2, 32.2),
    "ASHRAE_MHBP": (7.2, 54.4, 35.0, 46.1),
    "CECOMAF_LBP": (-25.0, 55.0, 32.0, None),
}


@dataclass
class ParametrosCompressor:
    rotacao_rpm: float = 3500.0        # motor de 2 polos em 60 Hz (México, Colômbia, Brasil)
    fracao_espaco_morto: float = 0.04
    expoente_reexpansao: Optional[float] = None  # None -> cp/cv do vapor na sucção
    fator_volumetrico: float = 0.88
    condicao_catalogo: str = "EN12900_MBP"


def eficiencia_volumetrica(razao_pressao: float, p: ParametrosCompressor, n: float) -> float:
    C = p.fracao_espaco_morto
    return p.fator_volumetrico * (1.0 + C - C * razao_pressao ** (1.0 / n))


@dataclass
class ResultadoCompressor:
    m: float
    vazao_volumetrica_succao: float   # m³/s
    eta_v: float
    deslocamento_cm3: float           # por rotação
    rotacao_rpm: float
    W_el: float
    T_descarga: float
    catalogo: dict


def dimensionar_compressor(fl: Fluido, m: float, suc: Estado, P_desc: float, W_el: float,
                           T_desc: float, eta_global: float, p: ParametrosCompressor) -> ResultadoCompressor:
    n = p.expoente_reexpansao or fl.kappa(suc.P, suc.T)
    eta_v = eficiencia_volumetrica(P_desc / suc.P, p, n)
    Vdot = m / suc.rho
    desloc = Vdot / eta_v / (p.rotacao_rpm / 60.0)
    cat = ponto_catalogo(fl, desloc, p, eta_global)
    return ResultadoCompressor(m, Vdot, eta_v, desloc * 1e6, p.rotacao_rpm, W_el, T_desc, cat)


def ponto_catalogo(fl: Fluido, deslocamento_m3: float, p: ParametrosCompressor, eta_global: float) -> dict:
    """Capacidade e potência estimadas do MESMO compressor na condição de catálogo, para
    facilitar a seleção comercial. Mantém η_global e o modelo de η_v (estimativa ±15 %)."""
    Te, Tc, Tr, Tl = CONDICOES_NOMINAIS[p.condicao_catalogo]
    Te, Tc, Tr = Te + 273.15, Tc + 273.15, Tr + 273.15
    Pe, Pc = fl.Psat(Te), fl.Psat(Tc)
    suc = fl.estado_PT(Pe, Tr)
    liq = fl.estado_PQ(Pc, 0.0) if Tl is None else fl.estado_PT(Pc, Tl + 273.15)
    n = p.expoente_reexpansao or fl.kappa(Pe, Tr)
    eta_v = eficiencia_volumetrica(Pc / Pe, p, n)
    m = deslocamento_m3 * p.rotacao_rpm / 60.0 * eta_v * suc.rho
    q = suc.h - liq.h
    w_s = fl.estado_PS(Pc, suc.s).h - suc.h
    Q = m * q
    W = m * w_s / eta_global
    return {"condicao": p.condicao_catalogo, "T_evap_C": Te - 273.15, "T_cond_C": Tc - 273.15,
            "T_retorno_C": Tr - 273.15, "Q_W": Q, "Q_Btuh": Q * 3.412142, "W_el_W": W, "COP": Q / W,
            "m_kg_h": m * 3600.0, "eta_v": eta_v}
