"""Geometria do reator: vaso cilíndrico encamisado e agitador tipo âncora, por funções de distância.

Convenção do Tank: a função de distância com sinal (SDF) é positiva dentro do sólido e negativa no
líquido (as formas do agitador usam a convenção usual, negativa dentro, e o Tank troca o sinal).
O agitador é descrito no referencial que gira com ele (onde está parado); o vaso, no mesmo referencial,
é uma parede que gira em sentido contrário. Fundo plano em z = 0 (face da malha) e superfície livre plana
em z = H_L (sem vórtice central: hipótese usual para fundidos viscosos e vasos sem chicanas).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


def _box_sdf(p, center, half):
    """SDF de uma caixa alinhada aos eixos (p: [..., 3])."""
    q = np.abs(p - np.asarray(center)) - np.asarray(half)
    outside = np.linalg.norm(np.maximum(q, 0.0), axis=-1)
    inside = np.minimum(q.max(axis=-1), 0.0)
    return outside + inside


@dataclass
class Anchor:
    """Agitador âncora: dois braços verticais junto à parede, barra inferior e eixo central.

    D: diâmetro externo [m]; w: largura radial dos braços [m]; t: espessura (tangencial) [m];
    h_arm: altura dos braços a partir do fundo da barra [m]; c_b: folga no fundo [m];
    r_shaft: raio do eixo [m]."""
    D: float
    w: float
    t: float
    h_arm: float
    c_b: float
    r_shaft: float

    def sdf(self, p):
        Ra = 0.5 * self.D
        z0 = self.c_b
        zc = z0 + 0.5 * self.h_arm
        arms = [_box_sdf(p, (s * (Ra - 0.5 * self.w), 0.0, zc), (0.5 * self.w, 0.5 * self.t, 0.5 * self.h_arm))
                for s in (-1.0, 1.0)]
        bar = _box_sdf(p, (0.0, 0.0, z0 + 0.5 * self.w), (Ra, 0.5 * self.t, 0.5 * self.w))
        shaft = np.hypot(p[..., 0], p[..., 1]) - self.r_shaft
        shaft = np.maximum(shaft, z0 - p[..., 2])           # o eixo começa na barra inferior
        return np.minimum.reduce([arms[0], arms[1], bar, shaft])


@dataclass
class Shaft:
    """Só o eixo central (caso de verificação de Couette circular)."""
    r_shaft: float

    def sdf(self, p):
        return np.hypot(p[..., 0], p[..., 1]) - self.r_shaft


@dataclass
class Tank:
    """Vaso cilíndrico de diâmetro T [m] com líquido até H_L [m] e um agitador (Anchor ou Shaft)."""
    T: float
    H_L: float
    impeller: object = None
    rpm: float = 30.0
    meta: dict = field(default_factory=dict)

    @property
    def R(self):
        return 0.5 * self.T

    @property
    def omega(self):
        return 2.0 * math.pi * self.rpm / 60.0

    def vessel_sdf(self, p):
        """Positiva fora do raio interno (parede e camisa)."""
        return np.hypot(p[..., 0], p[..., 1]) - self.R

    def impeller_sdf(self, p):
        """Positiva dentro do agitador (as formas usam a convenção usual, negativa dentro)."""
        if self.impeller is None:
            return np.full(p.shape[:-1], -1e3)         # sem agitador: tudo fora do sólido
        return -self.impeller.sdf(p)

    def wall_distance(self, p):
        """Distância à parede mais próxima (lateral, fundo, agitador); a superfície livre não é parede."""
        d_side = -self.vessel_sdf(p)
        d_bot = p[..., 2]
        d_imp = np.abs(self.impeller_sdf(p))
        return np.maximum(np.minimum.reduce([d_side, d_bot, d_imp]), 0.0)

    @property
    def impeller_diameter(self):
        imp = self.impeller
        return getattr(imp, "D", 2 * getattr(imp, "r_shaft", 0.0))

    def describe(self) -> str:
        imp = self.impeller
        s = (f"vaso T = {self.T:.2f} m, líquido até {self.H_L:.2f} m "
             f"({math.pi * self.R ** 2 * self.H_L:.2f} m³); {self.rpm:.0f} rpm")
        if isinstance(imp, Anchor):
            s += (f"; âncora D = {imp.D:.2f} m (D/T = {imp.D / self.T:.2f}, folga na parede "
                  f"{1e3 * (self.R - 0.5 * imp.D):.0f} mm)")
        return s


def standard_anchor_tank(T: float = 1.6, H_over_T: float = 1.0, D_over_T: float = 0.92, rpm: float = 30.0,
                         w_over_D: float = 0.10, t: float | None = None) -> Tank:
    """Vaso padrão com âncora (proporções típicas de reatores de fundido: D/T ≈ 0,9–0,95, w/D ≈ 0,1)."""
    H_L = H_over_T * T
    D = D_over_T * T
    w = w_over_D * D
    c_b = 0.5 * (T - D)                     # folga no fundo igual à folga na parede
    anc = Anchor(D=D, w=w, t=t if t is not None else 0.04 * T, h_arm=0.85 * H_L - c_b, c_b=c_b,
                 r_shaft=0.035 * T)
    return Tank(T=T, H_L=H_L, impeller=anc, rpm=rpm)
