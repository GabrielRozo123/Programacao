"""Operações de malha deslocada (MAC) compartilhadas pelos solvers."""
from __future__ import annotations

import torch


def sl(a, axis, start, stop=None):
    idx = [slice(None)] * a.ndim
    idx[axis] = slice(start, stop)
    return a[tuple(idx)]


def pad(a, axis, n=1):
    """Replica as células de borda (gradiente nulo)."""
    lo, hi = sl(a, axis, 0, 1), sl(a, axis, -1, None)
    return torch.cat([lo] * n + [a] + [hi] * n, dim=axis)


def avg(a, axis):
    return 0.5 * (sl(a, axis, 1, None) + sl(a, axis, 0, -1))


def diff(a, axis):
    return sl(a, axis, 1, None) - sl(a, axis, 0, -1)


def to_faces(c, axis):
    """Centro → faces ao longo de axis (faces de borda recebem o valor da célula de borda)."""
    return avg(pad(c, axis), axis)


def cgrad(q, axis, h):
    """Gradiente central de um campo nos centros (unilateral nas bordas)."""
    qp = pad(q, axis)
    return (sl(qp, axis, 2, None) - sl(qp, axis, 0, -2)) / (2 * h)


def extend_into_solid(q, fluid_mask, passes: int = 3):
    """Estende para dentro do sólido (máscara False) os valores do fluido vizinho, por médias sucessivas.

    Usado para a viscosidade: no sólido a taxa de cisalhamento é nula e um modelo pseudoplástico daria
    viscosidades enormes, que contaminariam a tensão nas faces da interface."""
    known = fluid_mask.to(q.dtype)
    val = q * known
    pool = lambda a: torch.nn.functional.avg_pool3d(a[None, None], 3, 1, 1, count_include_pad=False)[0, 0]  # noqa: E731
    for _ in range(passes):
        s, c = pool(val * known), pool(known)
        newly = (known == 0) & (c > 0)
        val = torch.where(newly, s / c.clamp(min=1e-12), val)
        known = torch.maximum(known, newly.to(q.dtype))
    return torch.where(known > 0, val, q)
