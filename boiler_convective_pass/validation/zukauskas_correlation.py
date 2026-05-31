"""
Žukauskas correlation for heat transfer in tube banks (crossflow).

Reference:
    Žukauskas, A. (1972). Heat transfer from tubes in crossflow.
    Advances in Heat Transfer, Vol. 8, pp. 93-160. Academic Press.

Also in:
    Incropera, F.P. et al. (2006). Fundamentals of Heat and Mass Transfer,
    6th ed., Wiley. Section 7.4 (Table 7.2).

Valid for:
    - 0.7 ≤ Pr ≤ 500
    - 10 ≤ Re_D,max ≤ 2×10^6
    - N_L ≥ 20 rows (correction factor F applied for fewer rows)
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class FlueGas:
    """Approximate flue gas properties at mean temperature (biomass combustion)."""
    T_mean: float        # K — mean film temperature
    rho: float = None    # kg/m³
    mu: float = None     # Pa·s
    k: float = None      # W/(m·K)
    Pr: float = None     # —
    cp: float = None     # J/(kg·K)

    def __post_init__(self):
        T = self.T_mean
        # Simplified correlations for flue gas (CO2+H2O+N2 mixture, dry)
        # Valid roughly 500–1200 K
        if self.rho is None:
            self.rho = 101325 / (287.0 * T)   # ideal gas, dry air approx
        if self.mu is None:
            self.mu = 1.458e-6 * T**1.5 / (T + 110.4)   # Sutherland
        if self.k is None:
            self.k = 2.495e-3 * T**0.8646 / 1000         # approx fit
        if self.cp is None:
            self.cp = 1050.0                               # J/(kg·K) typical
        if self.Pr is None:
            self.Pr = self.mu * self.cp / self.k


def zukauskas_Nu(Re_max: float, Pr: float, Pr_w: float,
                 arrangement: str = "staggered", N_L: int = 20) -> float:
    """
    Compute average Nusselt number for a tube bank per Žukauskas correlation.

    Args:
        Re_max: Reynolds number based on maximum velocity (at minimum free area)
        Pr:     Prandtl number at mean fluid temperature
        Pr_w:   Prandtl number at tube wall temperature
        arrangement: "staggered" or "inline"
        N_L:    number of tube rows in flow direction

    Returns:
        Nu_D: average Nusselt number
    """
    # Table 7.2 — Incropera 6th ed.
    if arrangement == "staggered":
        if Re_max < 500:
            C, m = 0.350, 0.600
        elif Re_max < 2e5:
            C, m = 0.400, 0.600
        else:
            C, m = 0.022, 0.840
    else:  # inline
        if Re_max < 100:
            C, m = 0.800, 0.400
        elif Re_max < 1000:
            C, m = 0.273, 0.635
        elif Re_max < 2e5:
            C, m = 0.210, 0.700
        else:
            C, m = 0.037, 0.800

    Nu = C * Re_max**m * Pr**0.36 * (Pr / Pr_w)**0.25

    # Row correction factor (Table 7.3 — Incropera)
    F = _row_correction(N_L, arrangement)
    return F * Nu


def _row_correction(N_L: int, arrangement: str) -> float:
    """Correction factor for N_L < 20 rows (Incropera Table 7.3)."""
    # Approximate fit — exact values from table
    if N_L >= 20:
        return 1.0
    table_stag = {1: 0.68, 2: 0.75, 3: 0.83, 4: 0.89, 5: 0.92,
                  7: 0.95, 10: 0.97, 13: 0.98, 16: 0.99}
    table_inl  = {1: 0.64, 2: 0.76, 3: 0.84, 4: 0.89, 5: 0.92,
                  7: 0.95, 10: 0.97, 13: 0.98, 16: 0.99}
    table = table_stag if arrangement == "staggered" else table_inl
    keys = sorted(table.keys())
    for i in range(len(keys) - 1):
        if keys[i] <= N_L < keys[i + 1]:
            # linear interpolation
            t = (N_L - keys[i]) / (keys[i + 1] - keys[i])
            return table[keys[i]] + t * (table[keys[i + 1]] - table[keys[i]])
    return table.get(N_L, 1.0)


def pressure_drop(rho: float, V_max: float, N_L: int,
                  arrangement: str, ST_D: float, SL_D: float,
                  Re_max: float) -> float:
    """
    Pressure drop across a tube bank (Žukauskas/Jakob method).

    Returns: Δp [Pa]
    """
    # Euler number (friction factor) — simplified fit
    # For staggered arrangement, use Jakob (1938) empirical expression
    if arrangement == "staggered":
        f = 0.264 * Re_max**(-0.145) if Re_max > 1000 else 1.0 / Re_max**0.5
    else:
        f = 0.27 * Re_max**(-0.14) if Re_max > 1000 else 1.2 / Re_max**0.4

    delta_p = N_L * f * rho * V_max**2 / 2
    return delta_p


def run_parametric_study():
    """Compare staggered vs. inline over a velocity range."""
    D = 0.0381          # tube OD [m]
    ST_D = 2.0          # transverse pitch ratio
    SL_D = 1.75         # longitudinal pitch ratio
    ST = ST_D * D
    N_L = 8             # number of tube rows
    T_gas = 700         # K — mean flue gas temperature
    T_wall = 500        # K — tube wall temperature (approx saturation + metal)

    gas = FlueGas(T_mean=T_gas)
    gas_w = FlueGas(T_mean=T_wall)

    velocities = np.linspace(4, 18, 50)   # approach velocity [m/s]
    V_max = velocities * ST / (ST - D)    # velocity at minimum free area

    results = {}
    for arr in ("staggered", "inline"):
        Nu_list, h_list, dp_list = [], [], []
        for V, V_m in zip(velocities, V_max):
            Re = gas.rho * V_m * D / gas.mu
            Nu = zukauskas_Nu(Re, gas.Pr, gas_w.Pr, arr, N_L)
            h = Nu * gas.k / D
            dp = pressure_drop(gas.rho, V_m, N_L, arr, ST_D, SL_D, Re)
            Nu_list.append(Nu)
            h_list.append(h)
            dp_list.append(dp)
        results[arr] = {"Nu": Nu_list, "h": h_list, "dp": dp_list}

    # --- Plot ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        f"Žukauskas Correlation — Tube Bank (D={D*1000:.1f} mm, "
        f"ST/D={ST_D}, SL/D={SL_D}, {N_L} rows, T_gas={T_gas} K)",
        fontsize=11
    )

    for arr, color in zip(("staggered", "inline"), ("tab:blue", "tab:orange")):
        axes[0].plot(velocities, results[arr]["Nu"], color=color, label=arr)
        axes[1].plot(velocities, results[arr]["h"],  color=color, label=arr)
        axes[2].plot(velocities, results[arr]["dp"] / 1000, color=color, label=arr)

    # Mark velocity window
    for ax in axes:
        ax.axvspan(6, 12, alpha=0.1, color="green", label="optimal window")
        ax.axvline(6,  ls="--", color="gray", lw=0.8)
        ax.axvline(12, ls="--", color="gray", lw=0.8)
        ax.set_xlabel("Approach velocity [m/s]")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.4)

    axes[0].set_ylabel("Nu_D  [—]")
    axes[1].set_ylabel("h  [W/(m²·K)]")
    axes[2].set_ylabel("Δp  [kPa]")

    axes[0].set_title("Nusselt number")
    axes[1].set_title("Heat transfer coeff.")
    axes[2].set_title("Pressure drop")

    plt.tight_layout()
    plt.savefig("../results/zukauskas_parametric.png", dpi=150, bbox_inches="tight")
    print("Saved: results/zukauskas_parametric.png")
    plt.show()

    # Print summary table
    print(f"\n{'V [m/s]':>10} {'Nu (stag)':>12} {'h (stag)':>12} "
          f"{'Nu (inl)':>12} {'h (inl)':>12} {'Δp_stag [Pa]':>14}")
    print("-" * 78)
    for i, V in enumerate(velocities[::5]):
        idx = i * 5
        print(f"{V:>10.1f} "
              f"{results['staggered']['Nu'][idx]:>12.1f} "
              f"{results['staggered']['h'][idx]:>12.1f} "
              f"{results['inline']['Nu'][idx]:>12.1f} "
              f"{results['inline']['h'][idx]:>12.1f} "
              f"{results['staggered']['dp'][idx]:>14.1f}")


if __name__ == "__main__":
    run_parametric_study()
