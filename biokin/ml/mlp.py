"""Rede neural densa implementada em numpy, com Adam.

Deliberadamente sem dependências externas: um pacote de pós-graduação que
exige instalar um framework de aprendizado profundo para rodar deixa de
ser reproduzível em poucos meses. A rede aqui é pequena por natureza do
problema — algumas centenas de pontos experimentais não sustentam nada
maior — e treina em segundos.

A saída passa por ``softplus`` quando se pede positividade, o que é
apropriado para velocidades de reação: garante ``r >= 0`` sem restrição
explícita e mantém o gradiente bem-comportado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class StandardScaler:
    """Padronização por média e desvio, com guarda contra colunas constantes."""

    mean: np.ndarray = field(default_factory=lambda: np.zeros(0))
    std: np.ndarray = field(default_factory=lambda: np.ones(0))

    def fit(self, X: np.ndarray) -> "StandardScaler":
        X = np.atleast_2d(np.asarray(X, dtype=float))
        self.mean = X.mean(axis=0)
        s = X.std(axis=0)
        self.std = np.where(s > 1e-12, s, 1.0)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (np.atleast_2d(np.asarray(X, dtype=float)) - self.mean) / self.std

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


def _softplus(z: np.ndarray) -> np.ndarray:
    # forma numericamente estável: log(1+e^z) = max(z,0) + log(1+e^-|z|)
    return np.maximum(z, 0.0) + np.log1p(np.exp(-np.abs(z)))


def _sigmoid(z: np.ndarray) -> np.ndarray:
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


class MLP:
    """Perceptron multicamadas para regressão escalar.

    Parameters
    ----------
    hidden:
        Tamanhos das camadas ocultas.
    positive_output:
        Aplica ``softplus`` na saída. Use para velocidades de reação.
    l2:
        Decaimento de pesos (regularização), essencial com poucos dados.
    """

    def __init__(
        self,
        hidden: tuple[int, ...] = (24, 24),
        positive_output: bool = True,
        l2: float = 1e-4,
        seed: int = 0,
    ) -> None:
        self.hidden = tuple(hidden)
        self.positive_output = positive_output
        self.l2 = float(l2)
        self.rng = np.random.default_rng(seed)
        self.W: list[np.ndarray] = []
        self.b: list[np.ndarray] = []
        self.x_scaler = StandardScaler()
        self.y_scale = 1.0
        self.history: list[float] = []

    # ------------------------------------------------------------------
    def _init_weights(self, n_in: int) -> None:
        sizes = [n_in, *self.hidden, 1]
        self.W, self.b = [], []
        for a, b in zip(sizes[:-1], sizes[1:]):
            # inicialização de Xavier, adequada a ativações tanh
            limit = np.sqrt(6.0 / (a + b))
            self.W.append(self.rng.uniform(-limit, limit, size=(a, b)))
            self.b.append(np.zeros(b))

    def _forward(self, X: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
        acts = [X]
        a = X
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = a @ W + b
            a = np.tanh(z) if i < len(self.W) - 1 else z
            acts.append(a)
        out = _softplus(a) if self.positive_output else a
        return out, acts

    # ------------------------------------------------------------------
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 3000,
        lr: float = 0.01,
        batch_size: int | None = None,
        verbose: bool = False,
    ) -> "MLP":
        X = np.atleast_2d(np.asarray(X, dtype=float))
        y = np.asarray(y, dtype=float).reshape(-1, 1)
        Xs = self.x_scaler.fit_transform(X)
        self.y_scale = float(np.max(np.abs(y))) or 1.0
        ys = y / self.y_scale

        self._init_weights(Xs.shape[1])
        mW = [np.zeros_like(w) for w in self.W]
        vW = [np.zeros_like(w) for w in self.W]
        mb = [np.zeros_like(v) for v in self.b]
        vb = [np.zeros_like(v) for v in self.b]
        beta1, beta2, eps = 0.9, 0.999, 1e-8
        n = Xs.shape[0]
        bs = batch_size or n
        step = 0
        self.history = []

        for epoch in range(epochs):
            order = self.rng.permutation(n)
            for start in range(0, n, bs):
                idx = order[start : start + bs]
                xb, yb = Xs[idx], ys[idx]
                out, acts = self._forward(xb)
                err = out - yb
                # dL/d(saída linear), incorporando a derivada do softplus
                delta = (2.0 / len(idx)) * err
                if self.positive_output:
                    delta = delta * _sigmoid(acts[-1])

                gW: list[np.ndarray] = [None] * len(self.W)  # type: ignore[list-item]
                gb: list[np.ndarray] = [None] * len(self.b)  # type: ignore[list-item]
                for i in range(len(self.W) - 1, -1, -1):
                    gW[i] = acts[i].T @ delta + self.l2 * self.W[i]
                    gb[i] = delta.sum(axis=0)
                    if i > 0:
                        delta = (delta @ self.W[i].T) * (1.0 - acts[i] ** 2)

                step += 1
                for i in range(len(self.W)):
                    mW[i] = beta1 * mW[i] + (1 - beta1) * gW[i]
                    vW[i] = beta2 * vW[i] + (1 - beta2) * gW[i] ** 2
                    mb[i] = beta1 * mb[i] + (1 - beta1) * gb[i]
                    vb[i] = beta2 * vb[i] + (1 - beta2) * gb[i] ** 2
                    mhat = mW[i] / (1 - beta1**step)
                    vhat = vW[i] / (1 - beta2**step)
                    self.W[i] -= lr * mhat / (np.sqrt(vhat) + eps)
                    mhat = mb[i] / (1 - beta1**step)
                    vhat = vb[i] / (1 - beta2**step)
                    self.b[i] -= lr * mhat / (np.sqrt(vhat) + eps)

            if epoch % 50 == 0 or epoch == epochs - 1:
                pred, _ = self._forward(Xs)
                mse = float(np.mean((pred - ys) ** 2))
                self.history.append(mse)
                if verbose and epoch % 500 == 0:
                    print(f"  época {epoch:5d}  MSE={mse:.4e}")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        out, _ = self._forward(self.x_scaler.transform(X))
        return (out * self.y_scale).ravel()

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """Coeficiente de determinação R²."""
        y = np.asarray(y, dtype=float).ravel()
        pred = self.predict(X)
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    @property
    def n_parameters(self) -> int:
        return sum(w.size for w in self.W) + sum(b.size for b in self.b)
