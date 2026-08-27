"""Figuras para relatório e defesa.

Usa o backend ``Agg``: gera arquivos sem precisar de display, que é o
necessário em servidor e em execução automatizada.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .data import Dataset  # noqa: E402
from .discrimination import Ranking  # noqa: E402
from .estimation import FitResult  # noqa: E402
from .reactor import simulate_batch, simulate_monolith  # noqa: E402
from .species import FLUID_SPECIES, SPECIES_LABEL  # noqa: E402

#: Cores estáveis por espécie, para que todas as figuras se leiam juntas.
SPECIES_COLOR = {
    "TG": "#1b3a6b",
    "DG": "#2f7dc4",
    "MG": "#67b0e8",
    "M": "#9aa5b1",
    "E": "#c2452d",
    "G": "#e0a030",
}


def _predict(fit: FitResult, exp, mode: str = "ideal") -> np.ndarray:
    values = fit.values_at(exp.T_K)
    pvec = np.array([values[n] for n in fit.network.param_names])
    t = np.linspace(0.0, float(exp.t[-1]), 200)
    if exp.reactor == "monolith":
        return t, simulate_monolith(fit.network, pvec, exp.C0, t, exp.operation, mode)
    return t, simulate_batch(fit.network, pvec, exp.C0, t, exp.catalyst_g_L)


def plot_profiles(
    fit: FitResult,
    dataset: Dataset,
    path: str | Path,
    mode: str = "ideal",
    max_panels: int = 9,
) -> Path:
    """Perfis medidos (pontos) contra o modelo ajustado (linhas)."""
    exps = list(dataset)[:max_panels]
    ncol = min(3, len(exps))
    nrow = int(np.ceil(len(exps) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 3.2 * nrow), squeeze=False)

    for ax, exp in zip(axes.ravel(), exps):
        try:
            t, prof = _predict(fit, exp, mode)
        except Exception:  # noqa: BLE001 - modelo inviável nesta corrida
            t, prof = exp.t, np.full((len(exp.t), len(FLUID_SPECIES)), np.nan)
        for i, sp in enumerate(FLUID_SPECIES):
            if sp == "M" or not np.isfinite(exp.Y[:, i]).any():
                continue
            c = SPECIES_COLOR[sp]
            ax.plot(t, prof[:, i], "-", color=c, lw=1.6, label=sp)
            ax.plot(exp.t, exp.Y[:, i], "o", color=c, ms=4, mfc="white", mew=1.2)
        ax.set_title(f"{exp.label}  ({exp.T_K - 273.15:.0f} °C)", fontsize=9)
        ax.set_xlabel("tempo espacial [min]" if exp.reactor == "monolith" else "tempo [min]")
        ax.set_ylabel("C [mol/L]")
        ax.grid(alpha=0.25)
    for ax in axes.ravel()[len(exps):]:
        ax.set_visible(False)
    axes[0, 0].legend(fontsize=7, ncol=2, frameon=False)
    fig.suptitle(f"Perfis: {fit.model_id}", fontsize=11)
    fig.tight_layout()
    return _save(fig, path)


def plot_parity(fit: FitResult, dataset: Dataset, path: str | Path, mode: str = "ideal") -> Path:
    """Previsto contra observado, por espécie."""
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    lim = 0.0
    for exp in dataset:
        values = fit.values_at(exp.T_K)
        pvec = np.array([values[n] for n in fit.network.param_names])
        try:
            if exp.reactor == "monolith":
                prof = simulate_monolith(
                    fit.network, pvec, exp.C0, exp.t, exp.operation, mode
                )
            else:
                prof = simulate_batch(
                    fit.network, pvec, exp.C0, exp.t, exp.catalyst_g_L
                )
        except Exception:  # noqa: BLE001
            continue
        for i, sp in enumerate(FLUID_SPECIES):
            m = np.isfinite(exp.Y[:, i])
            if not m.any() or sp == "M":
                continue
            ax.plot(
                exp.Y[m, i], prof[m, i], "o", color=SPECIES_COLOR[sp], ms=4,
                mfc="white", mew=1.1,
                label=sp if sp not in ax.get_legend_handles_labels()[1] else None,
            )
            lim = max(lim, float(np.nanmax(exp.Y[m, i])), float(np.nanmax(prof[m, i])))
    lim *= 1.05
    ax.plot([0, lim], [0, lim], "k-", lw=1)
    ax.plot([0, lim], [0, lim * 1.1], "k--", lw=0.6, alpha=0.5)
    ax.plot([0, lim], [0, lim * 0.9], "k--", lw=0.6, alpha=0.5)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("observado [mol/L]")
    ax.set_ylabel("previsto [mol/L]")
    ax.set_title(f"Paridade — {fit.model_id}\n(tracejado: ±10 %)", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, path)


def plot_ranking(ranking: Ranking, path: str | Path, top: int = 12) -> Path:
    """Pesos de Akaike dos modelos admissíveis."""
    rows = ranking.admissible[:top]
    fig, ax = plt.subplots(figsize=(8.0, 0.42 * max(len(rows), 3) + 1.6))
    if not rows:
        ax.text(0.5, 0.5, "nenhum modelo admissível", ha="center", va="center")
        ax.axis("off")
        return _save(fig, path)
    names = [s.model_id for s in rows][::-1]
    weights = [s.weight for s in rows][::-1]
    colors = ["#1b3a6b" if w == max(weights) else "#7f9dc0" for w in weights]
    ax.barh(range(len(rows)), weights, color=colors)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("peso de Akaike (probabilidade relativa)")
    ax.set_title("Ranqueamento dos mecanismos admissíveis", fontsize=11)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    return _save(fig, path)


def plot_residuals(fit: FitResult, path: str | Path) -> Path:
    """Resíduos contra ordem e histograma — procura de padrão."""
    r = np.asarray(fit.residuals, dtype=float)
    r = r[np.isfinite(r)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 3.4))
    a1.plot(r, "o", ms=3, color="#1b3a6b", mfc="white")
    a1.axhline(0, color="k", lw=1)
    a1.set_xlabel("ordem da observação")
    a1.set_ylabel("resíduo ponderado")
    a1.set_title("Resíduos", fontsize=10)
    a1.grid(alpha=0.25)
    a2.hist(r, bins=max(10, len(r) // 15), color="#7f9dc0", edgecolor="white")
    a2.set_xlabel("resíduo ponderado")
    a2.set_title("Distribuição", fontsize=10)
    a2.grid(alpha=0.25)
    fig.suptitle(fit.model_id, fontsize=10)
    fig.tight_layout()
    return _save(fig, path)


def plot_arrhenius(fit: FitResult, path: str | Path, temperatures=None) -> Path:
    """Gráfico de Arrhenius/van 't Hoff dos parâmetros ajustados."""
    Ts = np.asarray(temperatures if temperatures is not None else np.linspace(313, 363, 30))
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    plotted = False
    for name in fit.network.param_names:
        spec = fit.parameterization.get(name)
        if not spec.fit_energy:
            continue
        vals = [fit.values_at(float(T))[name] for T in Ts]
        ax.plot(1000.0 / Ts, np.log(vals), lw=1.8, label=name)
        plotted = True
    if not plotted:
        ax.text(0.5, 0.5, "ajuste isotérmico:\nsem dependência com T",
                ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return _save(fig, path)
    ax.set_xlabel("1000/T [K⁻¹]")
    ax.set_ylabel("ln(parâmetro)")
    ax.set_title(f"Arrhenius / van 't Hoff — {fit.model_id}", fontsize=10)
    ax.legend(fontsize=8, frameon=False, ncol=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return _save(fig, path)


def _save(fig, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def write_all_figures(
    result, outdir: str | Path, mode: str = "ideal"
) -> list[Path]:
    """Gera o conjunto completo de figuras de uma varredura."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = [plot_ranking(result.final, outdir / "ranking.png")]
    best = result.best
    if best is not None:
        paths += [
            plot_profiles(best.fit, result.dataset, outdir / "perfis.png", mode),
            plot_parity(best.fit, result.dataset, outdir / "paridade.png", mode),
            plot_residuals(best.fit, outdir / "residuos.png"),
            plot_arrhenius(best.fit, outdir / "arrhenius.png"),
        ]
    return paths
