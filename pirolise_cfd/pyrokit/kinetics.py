"""Cinética de pirólise dos polímeros (literatura aberta) e validação por termogravimetria (TGA).

Modelo primário: cisão aleatória com comprimento mínimo não volátil L = 2 (Simha–Wall; forma de
Sánchez-Jiménez et al.), resolvido pela fração de ligações rompidas x:

    dx/dt = k(T)(1 − x),     α = x²  (fração volatilizada),     k = A exp(−E/RT)

Taxa específica de volatilização da massa que resta: 2 k x / (1 + x). Energias de ativação de Aboulkas
et al. (2010, isoconversional): HDPE 238, LDPE 215, PP 179 kJ/mol; PS 180 kJ/mol (meio da faixa da
literatura); fatores pré-exponenciais calibrados para os picos de DTG de consenso a 10 K/min (HDPE 475,
LDPE 465, PP 455, PS 420 °C). PET usa primeira ordem com 15% de resíduo (Dubdub e Al-Yaari, 2023).

Cada cisão física mapeia na cisão aparente por x_fís = 0,068 x (L = 20 unidades C2), o que dá a massa
molar média do fundido: Mn = m0 / (1/DPn0 + x_fís). Seletividade dos voláteis num tanque agitado a
425–450 °C: gás 0,07, óleo 0,70, cera 0,23 (polietileno/polipropileno); estireno 0,65 para PS.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

R_GAS = 8.314462618


@dataclass(frozen=True)
class Polymer:
    key: str
    name: str
    E: float               # energia de ativação aparente [J/mol]
    A: float               # fator pré-exponencial [1/s]
    model: str             # "rs2" (cisão aleatória, L = 2) ou "first" (primeira ordem)
    char: float            # fração da massa reagida que vira resíduo sólido
    tpeak_10: float        # pico de DTG de consenso a 10 K/min [°C] (alvo de validação)
    dH: float              # entalpia de pirólise + vaporização dos produtos [J/kg] (endotérmica)
    split: tuple           # seletividade dos voláteis (gás, óleo, cera) em massa
    m0: float = 0.028      # massa da unidade de cisão [kg/mol] (C2 para poliolefinas)
    Mn0: float = 30.0      # massa molar numérica da resina [kg/mol]
    sources: str = ""


POLYMERS = {
    "HDPE": Polymer("HDPE", "polietileno de alta densidade", 238e3, 5.2e14, "rs2", 0.0, 475.0, 1.0e6,
                    (0.07, 0.70, 0.23), 0.028, 30.0,
                    "E: Aboulkas et al. 2010; ΔH: Stoliarov & Walters (DSC, 920 ± 120 J/g); seletividade: tanque agitado"),
    "LDPE": Polymer("LDPE", "polietileno de baixa densidade", 215e3, 1.92e13, "rs2", 0.0, 465.0, 1.0e6,
                    (0.07, 0.70, 0.23), 0.028, 30.0, "E: Aboulkas et al. 2010"),
    "PP": Polymer("PP", "polipropileno", 179e3, 6.98e10, "rs2", 0.0, 455.0, 1.0e6,
                  (0.08, 0.80, 0.12), 0.042, 60.0, "E: Aboulkas et al. 2010; ΔH: Stoliarov & Walters (faixa 630–1310 J/g)"),
    "PS": Polymer("PS", "poliestireno", 180e3, 4.1e11, "rs2", 0.0, 420.0, 0.8e6,
                  (0.02, 0.98, 0.0), 0.104, 100.0, "E: meio da faixa 150–204 kJ/mol; produtos: estireno 0,65"),
    "PET": Polymer("PET", "poli(tereftalato de etileno)", 210e3, 2.59e13, "first", 0.15, 435.0, 0.4e6,
                   (0.47, 0.53, 0.0), 0.192, 20.0, "Dubdub & Al-Yaari 2023 (pico 680 K a 2 K/min)"),
}


def rate(p: Polymer, T):
    """k(T) [1/s] (T em K, escalar ou array)."""
    return p.A * np.exp(-p.E / (R_GAS * np.asarray(T, dtype=float)))


def volatilisation_specific(p: Polymer, x, T):
    """Taxa de volatilização por massa de fundido restante [1/s] para o estado x."""
    k = rate(p, T)
    if p.model == "rs2":
        return 2.0 * k * x / (1.0 + x)
    return k * (1.0 - p.char) * np.ones_like(np.asarray(x, dtype=float))


def Mn_of_x(p: Polymer, x):
    """Massa molar numérica do fundido [kg/mol] pela cisão aleatória (x_fís = 0,068 x)."""
    dpn0 = p.Mn0 / p.m0
    return p.m0 / (1.0 / dpn0 + 0.068 * np.asarray(x, dtype=float))


# ------------------------------------------------------------------------- TGA
def tga(p: Polymer, beta_K_min: float, T0: float = 400.0, T1: float = 950.0, n: int = 6000):
    """Termogravimetria a taxa constante: devolve T [K], α (fração volatilizada) e dα/dT [1/K]."""
    T = np.linspace(T0, T1, n)
    beta = beta_K_min / 60.0
    dT = T[1] - T[0]
    if p.model == "rs2":
        # dx/dT = (k/β)(1 − x)  →  integral exata por passo: ln(1−x) = −∫k dT/β
        k = rate(p, T)
        I = np.concatenate([[0.0], np.cumsum(0.5 * (k[1:] + k[:-1]) * dT)]) / beta
        x = 1.0 - np.exp(-I)
        alpha = x ** 2
    else:
        k = rate(p, T)
        I = np.concatenate([[0.0], np.cumsum(0.5 * (k[1:] + k[:-1]) * dT)]) / beta
        alpha = (1.0 - np.exp(-I)) * (1.0 - p.char)
    dadT = np.gradient(alpha, T)
    return T, alpha, dadT


def tga_peak(p: Polymer, beta_K_min: float) -> float:
    """Temperatura do pico de DTG [°C]."""
    T, _, d = tga(p, beta_K_min)
    i = int(np.argmax(d))
    # refino parabólico do máximo
    if 0 < i < len(T) - 1:
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
        return float(T[i] + off * (T[1] - T[0]) - 273.15)
    return float(T[i] - 273.15)


def kissinger(p: Polymer, betas=(2, 5, 10, 20, 50)):
    """E recuperada pelo método de Kissinger [J/mol]: inclinação de ln(β/Tp²) × 1/Tp (ICTAC)."""
    Tp = np.array([tga_peak(p, b) + 273.15 for b in betas])
    y = np.log(np.asarray(betas) / Tp ** 2)
    slope = np.polyfit(1.0 / Tp, y, 1)[0]
    return -slope * R_GAS, Tp - 273.15


def half_life(p: Polymer, T_C: float) -> float:
    """Tempo para volatilizar 50% em isoterma [min] (limite cinético)."""
    k = float(rate(p, T_C + 273.15))
    if p.model == "rs2":
        x = math.sqrt(0.5)
        return -math.log(1 - x) / k / 60.0
    return -math.log(1 - 0.5 / (1 - p.char)) / k / 60.0


# ------------------------------------------------------------------- misturas
@dataclass
class Feed:
    """Carga do reator: frações mássicas por polímero (as poliolefinas dominam as cargas reais)."""
    name: str
    fractions: dict = field(default_factory=dict)
    source: str = ""

    def normalised(self):
        s = sum(self.fractions.values())
        return {k: v / s for k, v in self.fractions.items()}

    def polymers(self):
        return [(POLYMERS[k], w) for k, w in self.normalised().items()]

    def describe(self):
        return ", ".join(f"{k} {100 * w:.0f}%" for k, w in self.normalised().items())


FEEDS = {
    "HDPE": Feed("HDPE puro", {"HDPE": 1.0}),
    "PP": Feed("PP puro", {"PP": 1.0}),
    "poliolefinas": Feed("mistura de poliolefinas", {"LDPE": 0.40, "HDPE": 0.35, "PP": 0.25},
                         "mistura típica de resíduos pós-consumo sem PVC/PET"),
    "pos-consumo": Feed("plástico pós-consumo selecionado", {"HDPE": 0.30, "LDPE": 0.35, "PP": 0.25, "PS": 0.10},
                        "composição de demonstração da literatura; PVC e PET excluídos (cloro, oxigenados)"),
}


def tga_blend(feed: Feed, beta_K_min: float):
    """TGA de uma mistura, por aditividade das curvas α_i(T)."""
    T = None
    alpha = 0.0
    for p, w in feed.polymers():
        T, a, _ = tga(p, beta_K_min)
        alpha = alpha + w * a
    return T, alpha, np.gradient(alpha, T)
