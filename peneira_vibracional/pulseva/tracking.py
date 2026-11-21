"""Rastreamento de ordem (order tracking) e estimadores espectrais.

Por que não basta uma FFT ou um ajuste senoidal de frequência fixa?
-------------------------------------------------------------------
A rotação do excitador varia ~±1 % ao longo dos 10 s de gravação (carga de
material, escorregamento do motor de indução). Para 122 ciclos, uma deriva de
0,1 Hz acumula dezenas de graus de fase, e um ajuste com frequência fixa
"borra" o fasor: a amplitude do fundamental sai subestimada (até -15 % nesta
gravação). A solução clássica é o **rastreamento de ordem computacional**
(Fyfe & Munck, 1997): estima-se a fase instantânea de rotação θ(t) e todas as
grandezas passam a ser calculadas no domínio angular, onde a componente 1×
fica estacionária.

Implementação (demodulação síncrona)
------------------------------------
1. Filtro passa-banda Butterworth (fase zero) em torno da rotação.
2. Projeção X–Y na direção principal (maior energia) → sinal de referência.
3. Transformada de Hilbert → fase analítica → frequência instantânea
   (Boashash, 1992), suavizada por passa-baixa de 2 Hz e integrada → θ(t).
4. Fasor complexo da ordem n de um canal x(t), sobre um número inteiro de
   rotações::

       P_n = 2 · mean[ x(t) · exp(-j n θ(t)) ]   ⇒   x(t) ≈ Re{ P_n · exp(j n θ(t)) }

   |P_n| é a amplitude (g) e arg(P_n) a fase da ordem n.

Como cada sensor é sem fio (sem relógio comum confiável), θ(t) é estimado
por sensor; a fase absoluta entre sensores é tratada na etapa de
sincronização (ver ``metrics.synchronize``).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt


@dataclass
class RotationTrack:
    """Fase de rotação estimada para um sensor."""

    theta: np.ndarray      # fase de rotação (rad), N amostras
    f_inst: np.ndarray     # frequência instantânea suavizada (Hz), N amostras
    fs: float
    i0: int                # início da janela de análise (amostra)
    i1: int                # fim (exclusivo) — número inteiro de rotações
    n_rev: int

    @property
    def window(self) -> slice:
        return slice(self.i0, self.i1)

    @property
    def f_mean(self) -> float:
        """Frequência média = rotações completas / tempo (Hz)."""
        return self.n_rev / ((self.i1 - self.i0) / self.fs)


def dominant_frequency(x: np.ndarray, fs: float, fmin: float = 3.0, fmax: float = 60.0,
                       pad: int = 8) -> float:
    """Frequência do maior pico espectral (soma dos eixos), com interpolação parabólica."""
    x = np.atleast_2d(x.T).T
    x = x - x.mean(axis=0)
    n = x.shape[0]
    w = np.hanning(n)
    spec = np.abs(np.fft.rfft(x * w[:, None], pad * n, axis=0)).sum(axis=1)
    f = np.fft.rfftfreq(pad * n, 1 / fs)
    band = np.where((f >= fmin) & (f <= fmax))[0]
    k = band[np.argmax(spec[band])]
    a, b, c = np.log(spec[k - 1:k + 2] + 1e-30)
    delta = 0.5 * (a - c) / (a - 2 * b + c)
    return float(f[k] + delta * (f[1] - f[0]))


def track_rotation(xy: np.ndarray, fs: float, f_guess: float | None = None,
                   rel_band: float = 0.35, smooth_hz: float = 2.0,
                   edge_s: float = 0.75) -> RotationTrack:
    """Estima θ(t) a partir dos eixos X e Y de um sensor (array N×2, em g)."""
    xy = np.asarray(xy, float)
    xy = xy - xy.mean(axis=0)
    if f_guess is None:
        f_guess = dominant_frequency(xy, fs)
    sos = butter(4, [f_guess * (1 - rel_band), f_guess * (1 + rel_band)],
                 btype="band", fs=fs, output="sos")
    bp = sosfiltfilt(sos, xy, axis=0)
    # direção principal do movimento no plano X-Y
    _, vec = np.linalg.eigh(np.cov(bp.T))
    ref = bp @ vec[:, -1]
    phase = np.unwrap(np.angle(hilbert(ref)))
    f_raw = np.gradient(phase) * fs / (2 * np.pi)
    f_s = sosfiltfilt(butter(2, smooth_hz, fs=fs, output="sos"), f_raw)
    # integração trapezoidal da frequência suavizada
    inc = np.concatenate([[0.0], np.cumsum(0.5 * (f_s[1:] + f_s[:-1]))]) * 2 * np.pi / fs
    theta = inc + np.mean(phase - inc)
    # janela de análise: descarta bordas (transientes de Hilbert e do filtro de
    # suavização, ~0,6 s em cada extremo) e usa um número inteiro de rotações
    e = int(round(edge_s * fs))
    i0 = e
    rev = (theta - theta[i0]) / (2 * np.pi)
    n_rev = int(np.floor(rev[len(theta) - e - 1]))
    i1 = int(np.searchsorted(rev, n_rev))
    return RotationTrack(theta=theta, f_inst=f_s, fs=fs, i0=i0, i1=i1, n_rev=n_rev)


def order_phasors(x: np.ndarray, track: RotationTrack, orders=(1, 2, 3, 4, 5)) -> np.ndarray:
    """Fasores complexos P_n (array n_ordens × n_canais) na janela de análise."""
    x = np.atleast_2d(np.asarray(x, float).T).T
    sl = track.window
    xs = x[sl] - x[sl].mean(axis=0)
    th = track.theta[sl]
    return np.array([2 * np.mean(xs * np.exp(-1j * n * th)[:, None], axis=0) for n in orders])


def fractional_order_phasors(x: np.ndarray, track: RotationTrack, orders=(0.5, 1.5)) -> np.ndarray:
    """Fasores de ordens fracionárias (ex.: 0,5× e 1,5×) sobre um número PAR de rotações,
    para que cada ordem complete ciclos inteiros na janela."""
    x = np.atleast_2d(np.asarray(x, float).T).T
    th = track.theta
    n_even = track.n_rev - (track.n_rev % 2)
    i1 = int(np.searchsorted(th, th[track.i0] + 2 * np.pi * n_even))
    sl = slice(track.i0, i1)
    xs = x[sl] - x[sl].mean(axis=0)
    t = th[sl] - th[track.i0]
    return np.array([2 * np.mean(xs * np.exp(-1j * n * t)[:, None], axis=0) for n in orders])


def per_revolution_phasors(x: np.ndarray, track: RotationTrack) -> np.ndarray:
    """Fasor 1× calculado rotação a rotação (array n_rev × n_canais)."""
    x = np.atleast_2d(np.asarray(x, float).T).T
    sl = track.window
    xs = x[sl] - x[sl].mean(axis=0)
    th = track.theta[sl]
    rev = np.floor((th - th[0]) / (2 * np.pi)).astype(int)
    e = np.exp(-1j * th)[:, None]
    out = np.empty((track.n_rev, x.shape[1]), complex)
    for k in range(track.n_rev):
        m = rev == k
        out[k] = 2 * np.mean(xs[m] * e[m], axis=0)
    return out


def angle_resample(x: np.ndarray, track: RotationTrack, n_per_rev: int = 64) -> np.ndarray:
    """Reamostra no domínio angular: array (n_rev, n_per_rev, n_canais)."""
    x = np.atleast_2d(np.asarray(x, float).T).T
    th0 = track.theta[track.i0]
    grid = th0 + np.arange(track.n_rev * n_per_rev) * 2 * np.pi / n_per_rev
    cols = [np.interp(grid, track.theta, x[:, c]) for c in range(x.shape[1])]
    return np.stack(cols, axis=-1).reshape(track.n_rev, n_per_rev, x.shape[1])


def time_synchronous_average(x: np.ndarray, track: RotationTrack, n_per_rev: int = 64) -> np.ndarray:
    """Média síncrona (TSA): forma de onda média de uma rotação (n_per_rev × n_canais)."""
    return angle_resample(x, track, n_per_rev).mean(axis=0)


def amplitude_spectrum(x: np.ndarray, fs: float):
    """Espectro de amplitude (janela Hann, corrigido em amplitude) — g de pico."""
    x = np.atleast_2d(np.asarray(x, float).T).T
    x = x - x.mean(axis=0)
    n = x.shape[0]
    w = np.hanning(n)
    amp = np.abs(np.fft.rfft(x * w[:, None], axis=0)) * 2 / w.sum()
    return np.fft.rfftfreq(n, 1 / fs), amp


def dominant_peak_amplitude(x: np.ndarray, fs: float, fmin: float = 1.0, fmax: float | None = None,
                            half_band_hz: float = 0.4):
    """Estimador "G-Force" do Pulse VA: amplitude do maior pico do espectro (qualquer frequência).

    Identificado por engenharia reversa do relatório Pulse (FFT sem janela; energia em ±2 bins de
    0,195 Hz em torno do pico → ±0,4 Hz). Implementado como a amplitude equivalente da energia
    espectral numa banda de ±``half_band_hz`` em torno do pico dominante, o que torna o resultado
    independente do comprimento da FFT. Para uma senoide pura devolve a sua amplitude.

    Retorna (amplitude em g por canal, frequência do pico em Hz por canal).
    """
    x = np.atleast_2d(np.asarray(x, float).T).T
    x = x - x.mean(axis=0)
    n = x.shape[0]
    a = 2 * np.abs(np.fft.rfft(x, axis=0)) / n          # espectro de amplitude, janela retangular
    f = np.fft.rfftfreq(n, 1 / fs)
    fmax = fmax or fs / 2
    band = np.flatnonzero((f >= fmin) & (f <= fmax))
    amps, freqs = [], []
    for c in range(x.shape[1]):
        k = band[np.argmax(a[band, c])]
        m = np.abs(f - f[k]) <= half_band_hz
        amps.append(np.sqrt(np.sum(a[m, c] ** 2)))
        freqs.append(f[k])
    return np.array(amps), np.array(freqs)


def order_spectrum(x: np.ndarray, track: RotationTrack, n_per_rev: int = 64):
    """Espectro de ordens (eixo em múltiplos da rotação) via reamostragem angular."""
    a = angle_resample(x, track, n_per_rev)
    flat = a.reshape(-1, a.shape[-1])
    flat = flat - flat.mean(axis=0)
    n = flat.shape[0]
    w = np.hanning(n)
    amp = np.abs(np.fft.rfft(flat * w[:, None], axis=0)) * 2 / w.sum()
    orders = np.fft.rfftfreq(n, 1 / n_per_rev)
    return orders, amp


def bandpass(x: np.ndarray, fs: float, lo: float, hi: float, order: int = 4) -> np.ndarray:
    sos = butter(order, [lo, hi], btype="band", fs=fs, output="sos")
    return sosfiltfilt(sos, x, axis=0)


def estimate_lag(a: np.ndarray, b: np.ndarray, fs: float, max_lag_s: float = 1.0) -> tuple[float, float]:
    """Atraso de ``a`` em relação a ``b`` (s) por correlação cruzada normalizada."""
    a = a - a.mean()
    b = b - b.mean()
    n = len(a)
    m = int(max_lag_s * fs)
    lags = np.arange(-m, m + 1)
    c = np.array([np.dot(a[max(0, k):n + min(0, k)], b[max(0, -k):n - max(0, k)]) for k in lags])
    c /= np.sqrt(np.dot(a, a) * np.dot(b, b))
    k = int(np.argmax(c))
    return lags[k] / fs, float(c[k])
