"""Geometria do tambor rotativo em batelada: casco cilíndrico horizontal, aletas internas e fornalha.

Convenções (iguais em todo o pacote):
  * eixo do tambor em x, de 0 (porta de carga, na frente) a L (fundo, saída dos vapores);
  * seção transversal no plano (y, z), z para cima, centro do tambor em y = z = 0;
  * rotação positiva em torno de +x: θ(t) = Ω t. O ponto mais baixo do casco anda para +y, então a carga
    sobe pelo lado y > 0 e rola de volta pela superfície do leito;
  * ângulos na seção: φ = atan2(z, y).

As aletas são placas radiais soldadas no casco (retas ou helicoidais), opcionalmente com uma aba na ponta
voltada para o sentido de giro (aleta em L), que forma a "concha" que levanta a carga.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch


@dataclass
class Drum:
    R: float = 1.4              # raio interno do casco [m]
    L: float = 6.6              # comprimento interno [m]
    wall: float = 0.016         # espessura do casco [m]
    rpm: float = 0.8            # rotação [1/min]
    n_lifters: int = 4          # número de aletas
    lifter_h: float = 0.18      # altura radial da aleta [m]
    lifter_t: float = 0.016     # espessura da chapa [m]
    lifter_tip: float = 0.0     # largura da aba na ponta (aleta em L) [m]; 0 = aleta reta
    lifter_pitch: float = 0.0   # passo da hélice [m]; 0 = aletas retas, paralelas ao eixo
    lifter_x: tuple = (0.15, 0.15)   # folga das aletas até a porta e até o fundo [m]

    @property
    def omega(self) -> float:
        return 2 * math.pi * self.rpm / 60.0

    @property
    def D(self) -> float:
        return 2 * self.R

    def froude(self, g: float = 9.81) -> float:
        return self.omega ** 2 * self.R / g

    def volume(self) -> float:
        return math.pi * self.R ** 2 * self.L

    def lifter_angles(self) -> np.ndarray:
        return 2 * math.pi * np.arange(self.n_lifters) / max(self.n_lifters, 1)

    def lifter_boxes(self):
        """Caixas de cada aleta no referencial da própria aleta (u radial para fora, w no sentido de giro):
        lista de (u0, u1, w0, w1). A placa entra um pouco no casco para não deixar fresta."""
        h, t = self.lifter_h, self.lifter_t
        boxes = [(self.R - h, self.R + 0.05, -0.5 * t, 0.5 * t)]
        if self.lifter_tip > 0:
            boxes.append((self.R - h, self.R - h + t, -0.5 * t, self.lifter_tip))
        return boxes


def fill_half_angle(fill: float) -> float:
    """Meio ângulo ε do segmento circular ocupado pela carga: fill = (ε − sen ε cos ε)/π."""
    lo, hi = 0.0, math.pi
    for _ in range(80):
        e = 0.5 * (lo + hi)
        if (e - math.sin(e) * math.cos(e)) / math.pi < fill:
            lo = e
        else:
            hi = e
    return 0.5 * (lo + hi)


def bed_depth(fill: float, R: float) -> float:
    return R * (1 - math.cos(fill_half_angle(fill)))


def lifter_contacts(drum: Drum, x: torch.Tensor, theta: float, L_period: float | None = None):
    """Contato das partículas (centros x [N,3]) com todas as caixas das aletas.

    Devolve (dist [N,B], n [N,B,3], p_c [N,B,3]): distância do centro à superfície, normal unitária da
    partícula para a aleta e ponto de contato na superfície, para cada uma das B caixas."""
    ang = torch.as_tensor(drum.lifter_angles(), dtype=x.dtype, device=x.device)
    y, z = x[:, 1:2], x[:, 2:3]
    phi = ang[None, :] + theta
    if drum.lifter_pitch > 0:
        phi = phi + 2 * math.pi * x[:, 0:1] / drum.lifter_pitch
    c, s = torch.cos(phi), torch.sin(phi)
    u = y * c + z * s            # coordenada radial no referencial da aleta
    w = -y * s + z * c           # coordenada no sentido de giro
    xs = x[:, 0:1].expand_as(u)
    x0, x1 = drum.lifter_x[0], drum.L - drum.lifter_x[1]
    out_d, out_n, out_p = [], [], []
    for (u0, u1, w0, w1) in drum.lifter_boxes():
        qu, qw = u.clamp(u0, u1), w.clamp(w0, w1)
        qx = xs.clamp(x0, x1) if L_period is None else xs
        du, dw, dx = qu - u, qw - w, qx - xs
        d = torch.sqrt(du * du + dw * dw + dx * dx).clamp(min=1e-9)
        # volta ao referencial do laboratório: e_u = (0, c, s), e_w = (0, −s, c)
        ny, nz = du * c - dw * s, du * s + dw * c
        n = torch.stack([dx, ny, nz], -1) / d[..., None]
        py, pz = qu * c - qw * s, qu * s + qw * c
        p = torch.stack([qx, py, pz], -1)
        out_d.append(d); out_n.append(n); out_p.append(p)
    return torch.cat(out_d, 1), torch.cat(out_n, 1), torch.cat(out_p, 1)
