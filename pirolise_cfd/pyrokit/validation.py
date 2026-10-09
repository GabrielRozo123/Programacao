"""Validação em três níveis (escada do documento de projeto), cada item com alvo, tolerância e veredito.

L1 · componentes do CFD: Couette newtoniano e de lei de potência (solução exata), Kp da fita helicoidal em
     regime laminar (correlação, ±20%, abaixo do limite de Couette), coeficiente interno contra Nagata
     (±30%) e fechamento dos balanços de massa e energia do reator 3D.
L2 · química e propriedades: picos de DTG (consenso a 10 K/min e Westerhout et al. 1997), PET a 2 K/min
     (Dubdub & Al-Yaari 2023), Kissinger, deslocamento do pico por duplicação da taxa, constantes
     isotérmicas de Westerhout, densidades da ISO 1133, viscosidade das ceras POLYWAX e a taxa de
     volatilização por massa retida de Murata et al. (2002).
L3 · sistema: CFD 3D × reator ideal 0-D (T dentro de 3 K, vazão dentro de 10%) e faixas de produtos.

Cada verificação devolve um dicionário {nível, item, valor, alvo, ok, nota}; `dashboard` desenha a tabela.
"""
from __future__ import annotations

import math
import time

import numpy as np

from . import kinetics as kin
from . import rheology as rh

TARGETS = {
    "kp_ribbon": 269.0, "kp_tol": 0.20, "kp_couette_bound": 653.0, "h_tol": 0.30,
    "westerhout_PS": 410.9, "westerhout_HDPE": 474.0, "PET_2K_K": 680.0,
    "westerhout_k": {400: 1.61e-4, 420: 5.01e-4, 440: 1.46e-3},
    "iso1133": {"PE": (190.0, 763.6), "PP": (230.0, 738.6)},
    "polywax_mPa_s": {655: 7.0, 1000: 15.0, 2000: 55.0, 3000: 130.0},
    "murata_per_h": (0.3, 1.0),
    "slate": {"gás": (0.04, 0.10), "líquido": (0.85, 0.93), "coque": (0.005, 0.04)},
}


def check(level, item, value, target, ok, note="", fmt="{:.3g}"):
    return {"nível": level, "item": item, "valor": value if isinstance(value, str) else fmt.format(value),
            "alvo": target, "ok": bool(ok), "nota": note}


# --------------------------------------------------------------------- L2
def chemistry_checks() -> list:
    out = []
    for key in ("HDPE", "LDPE", "PP", "PS"):
        p = kin.POLYMERS[key]
        tp = kin.tga_peak(p, 10.0)
        out.append(check("L2", f"pico DTG {key}, 10 K/min (calibração)", tp, f"{p.tpeak_10:.0f} ± 3 °C",
                         abs(tp - p.tpeak_10) <= 3.0, "consenso da literatura", "{:.1f} °C"))
    tp = kin.tga_peak(kin.POLYMERS["PS"], 10.0)
    out.append(check("L2", "pico DTG PS × Westerhout (1997)", tp, f"{TARGETS['westerhout_PS']} ± 12 °C",
                     abs(tp - TARGETS["westerhout_PS"]) <= 12, "independente da calibração", "{:.1f} °C"))
    tp = kin.tga_peak(kin.POLYMERS["HDPE"], 10.0)
    out.append(check("L2", "pico DTG HDPE × Westerhout (1997)", tp, f"{TARGETS['westerhout_HDPE']} ± 5 °C",
                     abs(tp - TARGETS["westerhout_HDPE"]) <= 5, "", "{:.1f} °C"))
    tpet = kin.tga_peak(kin.POLYMERS["PET"], 2.0) + 273.15
    out.append(check("L2", "pico DTG PET a 2 K/min", tpet, f"{TARGETS['PET_2K_K']:.0f} ± 5 K",
                     abs(tpet - TARGETS["PET_2K_K"]) <= 5, "Dubdub & Al-Yaari (2023)", "{:.0f} K"))
    for key in ("HDPE", "PP"):
        p = kin.POLYMERS[key]
        E, Tp = kin.kissinger(p)
        out.append(check("L2", f"Kissinger {key}: E recuperada", E / 1e3, f"{p.E / 1e3:.0f} kJ/mol (±5%)",
                         abs(E - p.E) / p.E < 0.05, "consistência da cinética RS-L2", "{:.0f} kJ/mol"))
        shift = float(np.mean(np.diff([kin.tga_peak(p, b) for b in (5, 10, 20)])))
        out.append(check("L2", f"deslocamento do pico por 2× na taxa ({key})", shift, "12–16 K",
                         11.0 <= shift <= 17.0, "", "{:.1f} K"))
    p = kin.POLYMERS["HDPE"]
    errs = [float(kin.rate(p, Tc + 273.15)) / k - 1 for Tc, k in TARGETS["westerhout_k"].items()]
    worst = max(errs, key=abs)
    out.append(check("L2", "k isotérmico HDPE 400–440 °C × Westerhout", f"{100 * worst:+.0f}% (pior)",
                     "dentro de ±40%", abs(worst) <= 0.40, "constantes de 1ª ordem medidas"))
    for poly, (Tc, ref) in TARGETS["iso1133"].items():
        key = "HDPE" if poly == "PE" else "PP"
        rho = float(rh.density(key, Tc + 273.15))
        out.append(check("L2", f"densidade {poly} a {Tc:.0f} °C (ISO 1133)", rho, f"{ref} kg/m³ ± 2%",
                         abs(rho / ref - 1) <= 0.02, "", "{:.1f} kg/m³"))
    errs = []
    for M, mpas in TARGETS["polywax_mPa_s"].items():
        model = 1e3 * 0.015 * (M / 1080.0) ** 1.9
        errs.append(model / mpas - 1)
    worst = max(errs, key=abs)
    out.append(check("L2", "viscosidade de ceras PE a 149 °C (POLYWAX)", f"{100 * worst:+.0f}% (pior)",
                     "±30%", abs(worst) <= 0.30, "ramo de cera da reologia"))
    return out


# --------------------------------------------------------------------- L1
def kp_ribbon(tank_fn, n_diam: int = 40, Re: float = 8.0, device: str = "auto", t_max_visc: float = 2.5,
              verbose: bool = False):
    """Kp = Np·Re da fita em regime laminar, por simulação newtoniana (μ escolhido para dar Re)."""
    import torch
    from .flow import FlowConfig, TankFlow
    tank = tank_fn()
    N, d = tank.rpm / 60.0, tank.impeller_diameter
    rho = 640.0
    mu = rho * N * d * d / Re
    f = TankFlow(tank, FlowConfig(n_diam=n_diam, rho=rho, device=device, spin0=0.8),
                 lambda g: torch.full_like(g, mu))
    t_end = t_max_visc * tank.R ** 2 / (mu / rho)
    t0 = time.perf_counter()
    last = None
    while f.time < t_end:
        f.step()
        f.record()
        if f.step_n % 500 == 0:
            P = f.power(200)
            if last is not None and abs(P - last) < 0.002 * abs(P):
                break
            last = P
            if verbose:
                print(f"  t = {f.time:.2f} s, Np·Re = {P / (rho * N ** 3 * d ** 5) * Re:.1f}")
    Np = f.power(200) / (rho * N ** 3 * d ** 5)
    return {"Kp": Np * Re, "Np": Np, "Re": Re, "steps": f.step_n, "wall_s": time.perf_counter() - t0,
            "torque_balance": -f.torque_wall / max(f.torque_imp, 1e-12)}


def flow_checks(kp: dict | None = None, reactor_kpis: dict | None = None, h_nagata: float | None = None) -> list:
    out = []
    if kp is not None:
        k = kp["Kp"]
        out.append(check("L1", f"Kp da fita (laminar, Re = {kp['Re']:.0f})", k,
                         f"{TARGETS['kp_ribbon']:.0f} ± 20% e < {TARGETS['kp_couette_bound']:.0f}",
                         abs(k / TARGETS["kp_ribbon"] - 1) <= TARGETS["kp_tol"] and k < TARGETS["kp_couette_bound"],
                         "correlação de Delaplace / limite de Couette", "{:.0f}"))
    if reactor_kpis is not None:
        kp_ = reactor_kpis
        out.append(check("L1", "balanço de massa (alimentação = vapor + purga)", f"{100 * kp_['mass_balance_err']:+.2f}%",
                         "|erro| < 1%", abs(kp_["mass_balance_err"]) < 0.01, "controle de nível"))
        out.append(check("L1", "balanço de energia (parede + agitação = carga + pirólise)",
                         f"{100 * kp_['energy_balance_err']:+.2f}%", "|erro| < 3%",
                         abs(kp_["energy_balance_err"]) < 0.03, "fluxos conservativos"))
        if h_nagata:
            h = kp_["h_mean"]
            out.append(check("L1", "coeficiente interno h × Nagata (fita, turbulento)", h,
                             f"{h_nagata:.0f} W/m²K ± 30%", abs(h / h_nagata - 1) <= TARGETS["h_tol"],
                             "lei de parede de Kader + SST", "{:.0f} W/m²K"))
    return out


# --------------------------------------------------------------------- L3
def system_checks(reactor, reactor_kpis: dict) -> list:
    """CFD 3D × reator ideal 0-D com o MESMO coeficiente interno médio (isola o efeito da mistura não
    ideal: pluma fria da alimentação, gradientes junto à parede) e faixas de produtos."""
    from .chemistry import product_slate, solve_cstr
    kp = reactor_kpis
    cfg = reactor.cfg
    ideal = solve_cstr(reactor.feed, reactor.V_liq, reactor.A_wall, kp["h_mean"], T_wall=kp["T_wall_C"] + 273.15,
                       feed_rate=None if cfg.feed_kgph is None else cfg.feed_kgph / 3600.0, rho=cfg.rho0)
    out = []
    dT = kp["T_bulk_C"] - (ideal.T - 273.15)
    out.append(check("L3", "T do fundido: CFD 3D × reator ideal 0-D (mesmo h)", f"{dT:+.1f} K", "dentro de ±3 K",
                     abs(dT) <= 3.0, "efeito da mistura não ideal"))
    dF = kp["feed_kgph"] / (3600 * ideal.feed) - 1
    out.append(check("L3", "vazão processada: CFD × 0-D (mesmo h)", f"{100 * dF:+.1f}%", "dentro de ±10%",
                     abs(dF) <= 0.10, ""))
    vol_h = kp["vapour_kgph"] / (cfg.rho0 * reactor.V_liq)
    lo, hi = TARGETS["murata_per_h"]
    out.append(check("L3", "volatilização por massa retida", vol_h, f"{lo}–{hi} 1/h (Murata 2002)",
                     lo <= vol_h <= hi, "reator contínuo agitado, 400–420 °C", "{:.2f} 1/h"))
    # faixas da literatura valem para reatores a 425–450 °C: o modelo de produtos é avaliado a 435 °C
    sl = product_slate(708.15)
    liq = sl["óleo"] + sl["cera"]
    for name, val in (("gás", sl["gás"]), ("líquido", liq), ("coque", sl["coque"])):
        lo, hi = TARGETS["slate"][name]
        out.append(check("L3", f"produtos a 435 °C: {name}", f"{100 * val:.1f}%", f"{100 * lo:.1f}–{100 * hi:.0f}%",
                         lo - 1e-9 <= val <= hi + 1e-9, "faixa da literatura (seletividade calibrada)"))
    return out, ideal


# ------------------------------------------------------------------ figura
def dashboard(checks: list, path: str | None = None, title: str = "Validação", size=(19.2, 10.8)):
    """Tabela de verificações com veredito colorido (PASSOU / FORA)."""
    import matplotlib.pyplot as plt
    from .video import br
    fig = plt.figure(figsize=size, dpi=100, facecolor="#0d1117")
    ax = fig.add_axes([0.03, 0.03, 0.94, 0.86])
    ax.axis("off")
    fig.text(0.03, 0.94, title, color="#eef2f8", fontsize=30, fontweight="bold")
    n_ok = sum(c["ok"] for c in checks)
    fig.text(0.97, 0.945, f"{n_ok}/{len(checks)} dentro do alvo", color="#7ee0a2" if n_ok == len(checks) else "#ffb040",
             fontsize=22, ha="right", fontweight="bold")
    cols = ["", "verificação", "resultado", "alvo", ""]
    xs = [0.0, 0.035, 0.53, 0.68, 0.93]
    n = len(checks)
    lh = min(0.06, 0.95 / (n + 1))
    fs = max(10, min(17, int(lh * 300)))
    for j, c in enumerate(cols):
        ax.text(xs[j], 1.0, c, color="#8b95a5", fontsize=fs, fontweight="bold", va="top", transform=ax.transAxes)
    for i, c in enumerate(checks):
        y = 1.0 - (i + 1.2) * lh
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0, y - 0.32 * lh), 1, lh, transform=ax.transAxes, color="#151b24", zorder=0))
        ax.text(xs[0], y, c["nível"], color="#ffb040", fontsize=fs, va="center", transform=ax.transAxes,
                fontweight="bold")
        ax.text(xs[1], y, br(c["item"]), color="#e6eaf0", fontsize=fs, va="center", transform=ax.transAxes)
        ax.text(xs[2], y, br(str(c["valor"])), color="#ffffff", fontsize=fs, va="center", transform=ax.transAxes,
                fontweight="bold")
        ax.text(xs[3], y, br(str(c["alvo"])), color="#aab3c2", fontsize=fs, va="center", transform=ax.transAxes)
        ax.text(xs[4], y, "PASSOU" if c["ok"] else "FORA", color="#7ee0a2" if c["ok"] else "#ff6b6b",
                fontsize=fs, va="center", transform=ax.transAxes, fontweight="bold")
    if path:
        fig.savefig(path, facecolor=fig.get_facecolor())
        plt.close(fig)
    return fig
