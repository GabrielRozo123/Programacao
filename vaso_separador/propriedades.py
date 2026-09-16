"""Propriedades de gas e bocais padronizados.

Nada sofisticado aqui de proposito: a massa especifica do gas vem de PV = ZnRT
com Z informado. Se o caso exigir mais rigor (proximidade do ponto critico,
mistura com forte nao-idealidade), puxe rho_g direto da simulacao de processo
(Aspen/PRO-II/HYSYS) ou da folha de dados da corrente e passe o valor pronto.
O objetivo do modulo e nao precisar chutar nada.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

R = 8314.462  # constante universal dos gases [J/(kmol.K)]


def massa_especifica_gas(P_bara: float, T_C: float, MM: float, Z: float = 1.0) -> float:
    """rho_G = P * MM / (Z R T), com P em bara, T em degC, MM em kg/kmol."""
    T_K = T_C + 273.15
    if T_K <= 0:
        raise ValueError("temperatura absoluta deve ser positiva")
    return (P_bara * 1e5) * MM / (Z * R * T_K)


def vazao_volumetrica(W_kg_h: float, rho: float) -> float:
    """Vazao volumetrica [m3/s] a partir da vazao massica [kg/h]."""
    return (W_kg_h / 3600.0) / rho


# ---------------------------------------------------------------------------
# Bocais
# ---------------------------------------------------------------------------
# Diametro interno de tubo de parede STD (ASME B36.10M). A parede real depende
# da classe de tubulacao do projeto - CONFIRMAR contra a especificacao antes de
# usar em documento de engenharia. Aqui serve para arredondar o bocal calculado
# para uma bitola comercial em vez de deixar um numero quebrado.

DI_BOCAIS_STD_MM: dict[str, float] = {
    '2"': 52.48,
    '3"': 77.92,
    '4"': 102.26,
    '6"': 154.08,
    '8"': 202.74,
    '10"': 254.46,
    '12"': 304.84,
    '14"': 336.55,
    '16"': 387.35,
    '18"': 438.15,
    '20"': 488.95,
    '24"': 590.95,
    '30"': 742.95,
    '36"': 895.35,
    '42"': 1047.75,
    '48"': 1200.15,
    '54"': 1352.55,
    '60"': 1504.95,
}


@dataclass(frozen=True)
class Bocal:
    nps: str
    di: float            # diametro interno [m]
    area: float          # area de escoamento [m2]
    velocidade: float    # velocidade real na bitola escolhida [m/s]
    rho_v2: float        # rho*v^2 real [Pa]
    rho_v2_limite: float # criterio adotado [Pa]
    di_minimo: float     # diametro minimo teorico antes do arredondamento [m]

    @property
    def folga(self) -> float:
        """Quanto de margem sobrou contra o criterio (1,0 = no limite)."""
        return self.rho_v2 / self.rho_v2_limite

    def __str__(self) -> str:
        return (
            f"{self.nps} (DI {self.di * 1000:.1f} mm) | v = {self.velocidade:.2f} m/s | "
            f"rho.v2 = {self.rho_v2:.0f} Pa de {self.rho_v2_limite:.0f} Pa "
            f"({self.folga * 100:.0f}% do criterio)"
        )


def seleciona_bocal(
    Q: float, rho: float, rho_v2_limite: float, di_minimo_extra: float = 0.0
) -> Bocal:
    """Menor bitola comercial que atende ao criterio de momento rho*v^2.

    O criterio de momento e o que governa bocal de entrada de separador: nao e
    perda de carga, e a energia com que o jato bifasico bate no vaso. Acima do
    limite o jato atomiza o liquido em gotas finas demais para o vaso separar,
    e nenhum aumento de diametro do costado resolve.
    """
    # rho v^2 = rho (Q/A)^2 <= limite  ->  A >= Q sqrt(rho/limite)
    area_min = Q * math.sqrt(rho / rho_v2_limite)
    di_min = max(math.sqrt(4.0 * area_min / math.pi), di_minimo_extra)

    for nps, di_mm in DI_BOCAIS_STD_MM.items():
        di = di_mm / 1000.0
        if di >= di_min:
            area = math.pi * di**2 / 4.0
            v = Q / area
            return Bocal(nps, di, area, v, rho * v**2, rho_v2_limite, di_min)

    raise ValueError(
        f"bocal requerido (DI >= {di_min * 1000:.0f} mm) acima da maior bitola "
        f"tabelada ({list(DI_BOCAIS_STD_MM)[-1]}). Reveja o criterio ou parta para "
        f"entrada multipla / dispositivo de entrada mais permissivo."
    )


# Criterios de rho*v^2 no bocal de entrada, por tipo de dispositivo de entrada.
# Valores em lb/(ft.s2), como a literatura cita; a conversao para Pa e 1,4882.
# Fonte: pratica consolidada de projeto de separadores (Bothamley, "Gas/Liquid
# Separators - Quantifying Separation Performance", Oil & Gas Facilities; Shell
# DEP 31.22.05.11-Gen; NORSOK P-002). As faixas variam entre as fontes.
# CONFIRMAR contra a norma/DEP que o cliente adotar.
LB_FT_S2 = 1.4881639  # 1 lb/(ft.s2) em Pa

CRITERIOS_RHO_V2: dict[str, tuple[float, str]] = {
    "sem_dispositivo": (1500.0, "Bocal nu, sem dispositivo de entrada. Faixa citada: 1000-1500."),
    "chapa_defletora": (3000.0, "Chapa defletora simples. Faixa citada: 3000-6000."),
    "meia_cana_aberta": (6000.0, "Meia-cana aberta / half-open pipe. Faixa citada: 5000-6000."),
    "palhetas": (8000.0, "Dispositivo de palhetas (vane inlet device). Faixa citada: 6000-10000."),
    "ciclonico": (10000.0, "Entrada ciclonica. Faixa citada: 10000-15000."),
}

# Bocal de saida de gas. Valor de pratica; CONFIRMAR.
RHO_V2_SAIDA_GAS = 3750.0  # lb/(ft.s2)

# Bocal de saida de liquido: governado por velocidade, nao por momento.
# 1 m/s e o teto usual; quebra-vortice e obrigatorio.
V_MAX_SAIDA_LIQUIDO = 1.0  # m/s


def rho_v2_em_pa(valor_lb_ft_s2: float) -> float:
    return valor_lb_ft_s2 * LB_FT_S2
