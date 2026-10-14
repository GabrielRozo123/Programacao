"""Lado do ar de trocadores tubo-aleta (aletas planas contínuas, tubos redondos escalonados).

Referências
-----------
* Wang, C.C., Chi, K.Y., Chang, C.J. (2000). Heat transfer and friction characteristics of
  plain fin-and-tube heat exchangers, part II: Correlation. Int. J. Heat Mass Transfer
  43:2693-2700. Base: 74 trocadores; j em ±15 % para 88,6 % e f em ±15 % para 85,1 % dos dados.
* Schmidt, T.E. (1949). Heat transfer calculations for extended surfaces. Refrig. Eng. 57:351-357
  (eficiência de aleta por raio equivalente; é a mesma usada na redução de dados de Wang et al.,
  o que mantém a correlação consistente).
* Kays, W.M., London, A.L. (1984). Compact Heat Exchangers, 3ª ed. (queda de pressão do núcleo).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class GeometriaAletada:
    """Geometria de trocador tubo-aleta. Todas as dimensões em metros."""
    Do: float = 9.52e-3            # diâmetro externo do tubo (3/8")
    esp_parede: float = 0.35e-3    # espessura da parede do tubo
    esp_aleta: float = 0.12e-3     # δf
    passo_aleta: float = 2.5e-3    # Fp (distância entre aletas, centro a centro)
    Pt: float = 25.4e-3            # passo transversal (perpendicular ao ar)
    Pl: float = 22.0e-3            # passo longitudinal (na direção do ar)
    n_fileiras: int = 3            # N, fileiras na direção do ar
    k_aleta: float = 222.0         # alumínio 1100 [W/mK]
    k_tubo: float = 390.0          # cobre [W/mK]
    rugosidade_int: float = 1.5e-6  # rugosidade interna do tubo de cobre [m]

    # ---------------------------------------------------------------- derivadas
    @property
    def Dc(self) -> float:
        """Diâmetro do colar da aleta, Dc = Do + 2δf (dimensão característica de Wang)."""
        return self.Do + 2.0 * self.esp_aleta

    @property
    def Di(self) -> float:
        return self.Do - 2.0 * self.esp_parede

    @property
    def area_aleta_por_m(self) -> float:
        """Área de aleta (duas faces) por metro de tubo [m²/m]."""
        return 2.0 * (self.Pt * self.Pl - math.pi * self.Dc ** 2 / 4.0) / self.passo_aleta

    @property
    def area_tubo_exposta_por_m(self) -> float:
        return math.pi * self.Dc * (1.0 - self.esp_aleta / self.passo_aleta)

    @property
    def area_externa_por_m(self) -> float:
        """Ao por metro de tubo [m²/m]."""
        return self.area_aleta_por_m + self.area_tubo_exposta_por_m

    @property
    def area_interna_por_m(self) -> float:
        return math.pi * self.Di

    @property
    def sigma(self) -> float:
        """Razão área mínima de escoamento / área de face (tubos escalonados com Pl usual,
        a área mínima é a transversal; ver verificação em ``area_minima_diagonal_ok``)."""
        return (self.Pt - self.Dc) * (self.passo_aleta - self.esp_aleta) / (self.Pt * self.passo_aleta)

    @property
    def area_minima_diagonal_ok(self) -> bool:
        """Verdadeiro se a passagem diagonal não é a mínima: 2·(Sd − Dc) ≥ (Pt − Dc)."""
        Sd = math.sqrt((self.Pt / 2.0) ** 2 + self.Pl ** 2)
        return 2.0 * (Sd - self.Dc) >= (self.Pt - self.Dc)

    @property
    def Dh(self) -> float:
        """Diâmetro hidráulico do lado do ar, Dh = 4 Amin L / Ao (definição de Wang et al.)."""
        amin_por_m = (self.Pt - self.Dc) * (1.0 - self.esp_aleta / self.passo_aleta)
        return 4.0 * amin_por_m * self.Pl / self.area_externa_por_m

    @property
    def fracao_aleta(self) -> float:
        return self.area_aleta_por_m / self.area_externa_por_m

    def resistencia_parede_por_m(self) -> float:
        """Resistência condutiva da parede do tubo por metro [m·K/W]."""
        return math.log(self.Do / self.Di) / (2.0 * math.pi * self.k_tubo)

    def verificar_faixa_wang(self) -> list[str]:
        """Faixa aproximada da base de dados de Wang et al. (2000)."""
        av = []
        fp_mm, dc_mm = self.passo_aleta * 1e3, self.Dc * 1e3
        if not 1.19 <= fp_mm <= 8.7:
            av.append(f"passo de aleta {fp_mm:.2f} mm fora de 1,19–8,7 mm (base de Wang 2000)")
        if not 6.35 <= dc_mm <= 12.7:
            av.append(f"diâmetro de colar {dc_mm:.2f} mm fora de 6,35–12,7 mm (base de Wang 2000)")
        if not 17.7 <= self.Pt * 1e3 <= 31.75:
            av.append(f"Pt {self.Pt * 1e3:.1f} mm fora de 17,7–31,75 mm (base de Wang 2000)")
        if not 12.4 <= self.Pl * 1e3 <= 27.5:
            av.append(f"Pl {self.Pl * 1e3:.1f} mm fora de 12,4–27,5 mm (base de Wang 2000)")
        if not 1 <= self.n_fileiras <= 6:
            av.append(f"{self.n_fileiras} fileiras fora de 1–6 (base de Wang 2000)")
        if not self.area_minima_diagonal_ok:
            av.append("a passagem diagonal é a área mínima: σ calculado é otimista")
        return av


def wang_2000_j_f(Re_Dc: float, geo: GeometriaAletada) -> tuple[float, float]:
    """Fatores j de Colburn e f de Fanning do núcleo, Wang, Chi & Chang (2000).

    N = 1:  j = 0,108 Re^−0,29 (Pt/Pl)^P1 (Fp/Dc)^−1,084 (Fp/Dh)^−0,786 (Fp/Pt)^P2
            P1 = 1,9 − 0,23 ln Re ;  P2 = −0,236 + 0,126 ln Re
    N ≥ 2:  j = 0,086 Re^P3 N^P4 (Fp/Dc)^P5 (Fp/Dh)^P6 (Fp/Pt)^−0,93
            P3 = −0,361 − 0,042 N/ln Re + 0,158 ln[N (Fp/Dc)^0,41]
            P4 = −1,224 − 0,076 (Pl/Dh)^1,42 / ln Re
            P5 = −0,083 + 0,058 N/ln Re
            P6 = −5,735 + 1,21 ln(Re/N)
    f = 0,0267 Re^F1 (Pt/Pl)^F2 (Fp/Dc)^F3
            F1 = −0,764 + 0,739 Pt/Pl + 0,177 Fp/Dc − 0,00758/N
            F2 = −15,689 + 64,021/ln Re ;  F3 = 1,696 − 15,695/ln Re
    Re = ρ V_max Dc / μ. Nota: algumas transcrições omitem o termo 0,158 ln[N(Fp/Dc)^0,41] de P3;
    sem ele j cai 4–5× de N=1 para N=6, o que contraria os próprios dados (j quase
    independente de N para Re > 2000) — ver tests/test_correlacoes.py.
    """
    Fp, Dc, Dh, Pt, Pl, N = geo.passo_aleta, geo.Dc, geo.Dh, geo.Pt, geo.Pl, geo.n_fileiras
    lnR = math.log(Re_Dc)
    if N == 1:
        P1 = 1.9 - 0.23 * lnR
        P2 = -0.236 + 0.126 * lnR
        j = 0.108 * Re_Dc ** -0.29 * (Pt / Pl) ** P1 * (Fp / Dc) ** -1.084 * (Fp / Dh) ** -0.786 * (Fp / Pt) ** P2
    else:
        P3 = -0.361 - 0.042 * N / lnR + 0.158 * math.log(N * (Fp / Dc) ** 0.41)
        P4 = -1.224 - 0.076 * (Pl / Dh) ** 1.42 / lnR
        P5 = -0.083 + 0.058 * N / lnR
        P6 = -5.735 + 1.21 * math.log(Re_Dc / N)
        j = 0.086 * Re_Dc ** P3 * N ** P4 * (Fp / Dc) ** P5 * (Fp / Dh) ** P6 * (Fp / Pt) ** -0.93
    F1 = -0.764 + 0.739 * Pt / Pl + 0.177 * Fp / Dc - 0.00758 / N
    F2 = -15.689 + 64.021 / lnR
    F3 = 1.696 - 15.695 / lnR
    f = 0.0267 * Re_Dc ** F1 * (Pt / Pl) ** F2 * (Fp / Dc) ** F3
    return j, f


def eficiencia_aleta_schmidt(h: float, geo: GeometriaAletada) -> float:
    """Eficiência de aleta plana em tubos escalonados (hexágono), Schmidt (1949):
    η = tanh(m r φ)/(m r φ), m = (2h/kδ)^0,5, φ = (Req/r − 1)[1 + 0,35 ln(Req/r)],
    Req/r = 1,27 ψ (β − 0,3)^0,5, ψ = X_M/r, β = X_L/X_M,
    X_M = Pt/2, X_L = ½[(Pt/2)² + Pl²]^0,5, r = Dc/2."""
    r = geo.Dc / 2.0
    XM = geo.Pt / 2.0
    XL = 0.5 * math.sqrt((geo.Pt / 2.0) ** 2 + geo.Pl ** 2)
    beta = XL / XM
    Req_r = 1.27 * (XM / r) * math.sqrt(max(beta - 0.3, 1e-9))
    phi = (Req_r - 1.0) * (1.0 + 0.35 * math.log(Req_r))
    m = math.sqrt(2.0 * h / (geo.k_aleta * geo.esp_aleta))
    z = m * r * phi
    return 1.0 if z < 1e-9 else math.tanh(z) / z


@dataclass
class DesempenhoAr:
    Re_Dc: float
    j: float
    f: float
    h: float          # coeficiente convectivo [W/m²K]
    eta_aleta: float
    eta_superficie: float
    G_max: float      # fluxo mássico na área mínima [kg/m²s]


def desempenho_lado_ar(V_face: float, rho: float, cp: float, mu: float, Pr: float,
                       geo: GeometriaAletada, fator_umidade: float = 1.0) -> DesempenhoAr:
    """h do lado do ar (Wang 2000) e eficiência global de superfície.

    ``fator_umidade`` ξ = Q_total/Q_sensível ≥ 1 aplica a analogia de Lewis para serpentina
    com desumidificação (Threlkeld 1970; McQuiston 1978): h_eq = ξ·h na eficiência da aleta
    e no fluxo de calor total."""
    G_max = rho * V_face / geo.sigma
    Re = G_max * geo.Dc / mu
    j, f = wang_2000_j_f(Re, geo)
    h = j * G_max * cp / Pr ** (2.0 / 3.0)
    eta_f = eficiencia_aleta_schmidt(h * fator_umidade, geo)
    eta_o = 1.0 - geo.fracao_aleta * (1.0 - eta_f)
    return DesempenhoAr(Re, j, f, h, eta_f, eta_o, G_max)


def queda_pressao_ar(G_max: float, f: float, geo: GeometriaAletada, rho_in: float,
                     rho_out: float) -> float:
    """ΔP do núcleo [Pa], Kays & London (mesma expressão da redução de dados de Wang):
    ΔP = G²/(2ρ_in) [ (1+σ²)(ρ_in/ρ_out − 1) + f (Ao/Amin)(ρ_in/ρ_m) ]"""
    rho_m = 2.0 / (1.0 / rho_in + 1.0 / rho_out)
    Ao_Amin = geo.area_externa_por_m * geo.n_fileiras / (geo.sigma * geo.Pt)
    return G_max ** 2 / (2.0 * rho_in) * (
        (1.0 + geo.sigma ** 2) * (rho_in / rho_out - 1.0) + f * Ao_Amin * rho_in / rho_m)
