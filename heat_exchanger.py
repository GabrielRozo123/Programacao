#!/usr/bin/env python3
"""Simulador industrial de trocador de calor casco e tubo.

Recursos principais:
- Propriedades de fluidos via banco de dados com interpolação em temperatura.
- Balanço térmico, LMTD e ε-NTU.
- Coeficientes convectivos por correlações consagradas:
  * Lado tubo: Gnielinski (turbulento), Sieder-Tate (laminar em desenvolvimento)
  * Lado casco: Bell-Delaware (j-factor ideal + fatores de correção)
- Cálculo detalhado de Uo (base área externa) com parede do tubo e incrustação.
- Queda de pressão:
  * Lado tubo: Darcy-Weisbach com fator de atrito de Churchill.
  * Lado casco: Bell-Delaware (ideal + correções de bypass/leakage).
- Otimização multi-cenário e geração de gráficos estilo dashboard.

Observação: apesar de usar correlações industriais, ainda é ferramenta de anteprojeto.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class FluidProps:
    rho: float
    cp: float
    mu: float
    k: float

    @property
    def pr(self) -> float:
        return self.cp * self.mu / self.k


@dataclass
class StreamSpec:
    fluid: str
    m_dot: float
    t_in: float
    t_out_target: float | None


@dataclass
class Geometry:
    do: float
    di: float
    pitch: float
    length: float
    n_tubes: int
    n_passes_tube: int
    baffle_cut: float
    baffle_spacing: float
    tube_layout: str = "triangular"


@dataclass
class Fouling:
    tube: float
    shell: float


@dataclass
class Result:
    q_kw: float
    t_hot_out: float
    t_cold_out: float
    lmtd: float
    f_corr: float
    uo_clean: float
    uo_fouled: float
    area_required: float
    area_available: float
    re_tube: float
    re_shell: float
    h_tube: float
    h_shell: float
    dp_tube_kpa: float
    dp_shell_kpa: float
    shell_diameter: float
    effectiveness: float
    score: float
    notes: str


def load_fluid_db(path: Path) -> Dict[str, Dict[str, List[float]]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def interp_property(t: float, t_grid: List[float], values: List[float]) -> float:
    if t <= t_grid[0]:
        return values[0]
    if t >= t_grid[-1]:
        return values[-1]

    for i in range(len(t_grid) - 1):
        if t_grid[i] <= t <= t_grid[i + 1]:
            t0, t1 = t_grid[i], t_grid[i + 1]
            v0, v1 = values[i], values[i + 1]
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return values[-1]


def fluid_props(db: Dict[str, Dict[str, List[float]]], fluid: str, t_bulk: float) -> FluidProps:
    rec = db[fluid]
    t_grid = rec["T_C"]
    return FluidProps(
        rho=interp_property(t_bulk, t_grid, rec["rho"]),
        cp=interp_property(t_bulk, t_grid, rec["cp"]),
        mu=interp_property(t_bulk, t_grid, rec["mu"]),
        k=interp_property(t_bulk, t_grid, rec["k"]),
    )


def heat_duty(hot: StreamSpec, cold: StreamSpec, hot_cp: float, cold_cp: float) -> Tuple[float, float, float]:
    if hot.t_out_target is None and cold.t_out_target is None:
        raise ValueError("Informe ao menos uma temperatura de saída alvo.")
    if hot.t_out_target is not None:
        q = hot.m_dot * hot_cp * (hot.t_in - hot.t_out_target)
        t_hot_out = hot.t_out_target
        t_cold_out = cold.t_in + q / (cold.m_dot * cold_cp)
    else:
        q = cold.m_dot * cold_cp * (cold.t_out_target - cold.t_in)
        t_cold_out = cold.t_out_target
        t_hot_out = hot.t_in - q / (hot.m_dot * hot_cp)
    return q, t_hot_out, t_cold_out


def lmtd(th_in: float, th_out: float, tc_in: float, tc_out: float) -> float:
    dt1 = th_in - tc_out
    dt2 = th_out - tc_in
    if dt1 <= 0 or dt2 <= 0:
        raise ValueError("Pinch térmico inválido para LMTD.")
    if abs(dt1 - dt2) < 1e-9:
        return dt1
    return (dt1 - dt2) / math.log(dt1 / dt2)


def f_correction_1_2(th_in: float, th_out: float, tc_in: float, tc_out: float) -> float:
    r = (th_in - th_out) / (tc_out - tc_in)
    p = (tc_out - tc_in) / (th_in - tc_in)
    if abs(r - 1.0) < 1e-9:
        val = math.sqrt(2) * (1 - p) / (2 - p)
        return max(0.5, min(1.0, val))
    s = math.sqrt(r * r + 1)
    num = s / (r - 1) * math.log((1 - p) / (1 - p * r))
    den = math.log((2 - p * (r + 1 - s)) / (2 - p * (r + 1 + s)))
    return max(0.3, min(1.0, num / den))


def shell_diameter_estimate(geom: Geometry) -> float:
    # TEMA-like estimate for triangular pitch bundle
    k1 = 0.175
    n1 = 2.285
    d_b = geom.do * (geom.n_tubes / k1) ** (1 / n1)
    return 1.05 * d_b


def churchill_friction(re: float, e_d: float = 0.0) -> float:
    a = (2.457 * math.log((7 / re) ** 0.9 + 0.27 * e_d)) ** 16
    b = (37530 / re) ** 16
    return 8 * ((8 / re) ** 12 + 1 / (a + b) ** 1.5) ** (1 / 12)


def tube_h_gnielinski(props: FluidProps, geom: Geometry, m_dot: float, mu_w: float) -> Tuple[float, float, float, float]:
    a_flow = geom.n_tubes / geom.n_passes_tube * math.pi * geom.di**2 / 4
    v = m_dot / (props.rho * a_flow)
    re = props.rho * v * geom.di / props.mu

    if re < 2300:
        graetz = re * props.pr * geom.di / geom.length
        nu = 1.86 * graetz ** (1 / 3) * (props.mu / mu_w) ** 0.14
    else:
        f = (0.79 * math.log(re) - 1.64) ** -2
        nu = (f / 8) * (re - 1000) * props.pr / (1 + 12.7 * math.sqrt(f / 8) * (props.pr ** (2 / 3) - 1))
    h = nu * props.k / geom.di
    f_d = churchill_friction(re)
    return h, re, v, f_d


def bell_delaware_shell_h(
    hot_props: FluidProps,
    geom: Geometry,
    m_dot_shell: float,
    th_in: float,
    th_out: float,
    shell_d: float,
) -> Tuple[float, float, float, Dict[str, float]]:
    # Geometria auxiliar
    pt = geom.pitch
    do = geom.do
    b = geom.baffle_spacing
    c = pt - do

    # Área de escoamento transversal principal
    sm = shell_d * b * c / pt
    g_s = m_dot_shell / max(sm, 1e-12)
    v = g_s / hot_props.rho

    # Diâmetro equivalente triangular (Bell)
    de = 1.10 * (pt**2 - 0.917 * do**2) / do
    re = g_s * de / hot_props.mu

    # Colburn j ideal para banco de tubos (Kern/Bell range)
    if re < 100:
        j = 0.9 * re ** -0.5
    elif re < 1000:
        j = 0.52 * re ** -0.38
    elif re < 2e5:
        j = 0.27 * re ** -0.2
    else:
        j = 0.023 * re ** -0.14

    h_ideal = j * g_s * hot_props.cp / (hot_props.pr ** (2 / 3))

    # Fatores de correção Bell-Delaware (aproximações industriais)
    f_w = geom.baffle_cut
    jc = 0.55 + 0.72 * (1 - 2 * f_w)  # janela/banco

    # leakage
    s_sb = 0.01 * shell_d * b
    s_tb = geom.n_tubes * math.pi * do * 0.0004
    rl = (s_sb + s_tb) / max(sm, 1e-9)
    rs = s_sb / max((s_sb + s_tb), 1e-9)
    jl = 0.44 * (1 - rs) + (1 - 0.44 * (1 - rs)) * math.exp(-2.2 * rl)

    # bypass
    s_b = 0.015 * shell_d * b
    r_b = s_b / max(sm, 1e-9)
    c_j = 1.35 if re >= 100 else 1.25
    jb = math.exp(-c_j * r_b * (1 - (2 * f_w) ** (1 / 3)))

    # adverse temperature gradient / laminar correction
    jr = 1.0 if re >= 100 else (re / 100) ** 0.18

    # unequal baffle spacing
    js = 1.0

    h = h_ideal * jc * jl * jb * jr * js
    factors = {"j": j, "jc": jc, "jl": jl, "jb": jb, "jr": jr, "js": js, "h_ideal": h_ideal}
    return h, re, v, factors


def overall_uo(hi: float, ho: float, geom: Geometry, foul: Fouling, k_wall: float = 16.0) -> Tuple[float, float]:
    do, di = geom.do, geom.di
    r_wall = do * math.log(do / di) / (2 * k_wall)
    inv_clean = do / (di * hi) + r_wall + 1 / ho
    inv_foul = inv_clean + do / di * foul.tube + foul.shell
    return 1 / inv_clean, 1 / inv_foul


def dp_tube(props: FluidProps, geom: Geometry, v: float, f: float) -> float:
    l_eq = geom.length * geom.n_passes_tube
    dp_fric = f * l_eq / geom.di * 0.5 * props.rho * v * v
    k_return = 1.5 * (geom.n_passes_tube - 1)
    k_nozzle = 1.0
    return dp_fric + (k_return + k_nozzle) * 0.5 * props.rho * v * v


def dp_shell_bell(props: FluidProps, geom: Geometry, shell_d: float, v: float, re: float, factors: Dict[str, float]) -> float:
    nb = max(int(geom.length / geom.baffle_spacing) - 1, 1)
    # fator de atrito ideal em feixe tubular
    if re < 100:
        f_id = 5.0 / re ** 0.3
    else:
        f_id = 1.4 / re ** 0.18

    dp_ideal_per_cross = 4 * f_id * 0.5 * props.rho * v * v
    dp_c = dp_ideal_per_cross * nb

    # correções Bell para ΔP
    rb = max(0.0, 0.02)
    rl = max(0.0, 0.05)
    z_b = math.exp(-3.7 * rb)
    z_l = math.exp(-1.33 * rl)
    z_s = 1.0
    dp = dp_c * z_b * z_l * z_s + 2 * 0.5 * props.rho * v * v
    return dp


def eps_ntu_counterflow(c_hot: float, c_cold: float, ua: float) -> float:
    c_min = min(c_hot, c_cold)
    c_max = max(c_hot, c_cold)
    cr = c_min / c_max
    ntu = ua / c_min
    if abs(cr - 1) < 1e-12:
        return ntu / (1 + ntu)
    e = math.exp(-ntu * (1 - cr))
    return (1 - e) / (1 - cr * e)


def simulate(
    db: Dict[str, Dict[str, List[float]]],
    hot: StreamSpec,
    cold: StreamSpec,
    geom: Geometry,
    foul: Fouling,
) -> Result:
    t_hot_bulk = (hot.t_in + (hot.t_out_target if hot.t_out_target else hot.t_in - 20)) / 2
    t_cold_bulk = (cold.t_in + (cold.t_out_target if cold.t_out_target else cold.t_in + 20)) / 2

    hot_props = fluid_props(db, hot.fluid, t_hot_bulk)
    cold_props = fluid_props(db, cold.fluid, t_cold_bulk)

    q, t_hot_out, t_cold_out = heat_duty(hot, cold, hot_props.cp, cold_props.cp)
    lm = lmtd(hot.t_in, t_hot_out, cold.t_in, t_cold_out)
    fc = f_correction_1_2(hot.t_in, t_hot_out, cold.t_in, t_cold_out)

    shell_d = shell_diameter_estimate(geom)

    # viscosidade na parede por interpolação na temperatura média de parede aproximada
    tw = (t_hot_bulk + t_cold_bulk) / 2
    mu_w_tube = fluid_props(db, cold.fluid, tw).mu

    h_t, re_t, v_t, f_t = tube_h_gnielinski(cold_props, geom, cold.m_dot, mu_w_tube)
    h_s, re_s, v_s, factors = bell_delaware_shell_h(hot_props, geom, hot.m_dot, hot.t_in, t_hot_out, shell_d)

    u_clean, u_foul = overall_uo(h_t, h_s, geom, foul)
    a_req = q / (u_foul * lm * fc)
    a_av = math.pi * geom.do * geom.length * geom.n_tubes

    dp_t = dp_tube(cold_props, geom, v_t, f_t)
    dp_s = dp_shell_bell(hot_props, geom, shell_d, v_s, re_s, factors)

    c_hot = hot.m_dot * hot_props.cp
    c_cold = cold.m_dot * cold_props.cp
    eff = eps_ntu_counterflow(c_hot, c_cold, u_foul * a_av)

    ratio = a_av / a_req
    penalty = (dp_t + dp_s) / 100000
    score = max(0.0, 100 * (1 - abs(ratio - 1)) - 10 * penalty)

    notes = "Projeto válido"
    if fc < 0.75:
        notes = "F de correção baixo; revisar arranjo térmico"
    if dp_t > 120000 or dp_s > 90000:
        notes += " | Queda de pressão alta"

    return Result(
        q_kw=q / 1000,
        t_hot_out=t_hot_out,
        t_cold_out=t_cold_out,
        lmtd=lm,
        f_corr=fc,
        uo_clean=u_clean,
        uo_fouled=u_foul,
        area_required=a_req,
        area_available=a_av,
        re_tube=re_t,
        re_shell=re_s,
        h_tube=h_t,
        h_shell=h_s,
        dp_tube_kpa=dp_t / 1000,
        dp_shell_kpa=dp_s / 1000,
        shell_diameter=shell_d,
        effectiveness=eff,
        score=score,
        notes=notes,
    )


def optimize(db, hot, cold, foul) -> List[Tuple[Geometry, Result]]:
    candidates: List[Tuple[Geometry, Result]] = []
    for di in [0.0157, 0.01905]:
        do = di + 0.00277
        for n_pass in [1, 2, 4]:
            for l in [3.66, 4.88, 6.10]:
                for nt in [120, 180, 260, 340]:
                    geom = Geometry(
                        do=do,
                        di=di,
                        pitch=1.25 * do,
                        length=l,
                        n_tubes=nt,
                        n_passes_tube=n_pass,
                        baffle_cut=0.25,
                        baffle_spacing=max(0.2, l / 6),
                    )
                    try:
                        r = simulate(db, hot, cold, geom, foul)
                    except Exception:
                        continue
                    if r.area_available >= r.area_required * 0.95:
                        candidates.append((geom, r))
    candidates.sort(key=lambda x: x[1].score, reverse=True)
    return candidates[:8]


def make_dashboard(results: List[Tuple[Geometry, Result]], output: Path) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None

    names = [f"Alt {i+1}" for i in range(len(results))]
    scores = [r.score for _, r in results]
    u_vals = [r.uo_fouled for _, r in results]
    dpt = [r.dp_tube_kpa for _, r in results]
    dps = [r.dp_shell_kpa for _, r in results]
    area_ratio = [r.area_available / r.area_required for _, r in results]

    fig, axs = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("Dashboard de Alternativas - Trocador Casco e Tubo", fontsize=14, fontweight="bold")

    axs[0, 0].bar(names, scores, color="#005f73")
    axs[0, 0].set_title("Score técnico")
    axs[0, 0].grid(axis="y", alpha=0.25)

    axs[0, 1].plot(names, u_vals, marker="o", color="#0a9396")
    axs[0, 1].set_title("Uo sujo [W/m².K]")
    axs[0, 1].grid(alpha=0.25)

    axs[1, 0].bar(names, dpt, label="ΔP tubo", color="#94d2bd")
    axs[1, 0].bar(names, dps, bottom=dpt, label="ΔP casco", color="#ee9b00")
    axs[1, 0].set_title("Perda de carga [kPa]")
    axs[1, 0].legend()

    axs[1, 1].plot(names, area_ratio, marker="s", color="#bb3e03")
    axs[1, 1].axhline(1.0, color="k", linestyle="--", linewidth=1)
    axs[1, 1].set_title("Razão área disponível/requerida")
    axs[1, 1].grid(alpha=0.25)

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=170)
    return output


def print_result(idx: int, g: Geometry, r: Result) -> None:
    print(f"\n=== Alternativa {idx} ===")
    print(f"Q = {r.q_kw:.2f} kW | Tq,out = {r.t_hot_out:.2f} °C | Tf,out = {r.t_cold_out:.2f} °C")
    print(f"LMTD = {r.lmtd:.2f} K | F = {r.f_corr:.3f} | ε-NTU = {r.effectiveness:.3f}")
    print(f"h_tubo = {r.h_tube:.1f} | h_casco = {r.h_shell:.1f} W/m².K")
    print(f"Uo limpo/sujo = {r.uo_clean:.1f}/{r.uo_fouled:.1f} W/m².K")
    print(f"Areq/Adisp = {r.area_required:.2f}/{r.area_available:.2f} m²")
    print(f"Re_t/Re_s = {r.re_tube:.0f}/{r.re_shell:.0f}")
    print(f"ΔP_t/ΔP_s = {r.dp_tube_kpa:.2f}/{r.dp_shell_kpa:.2f} kPa")
    print(f"Ds = {r.shell_diameter:.3f} m | score = {r.score:.2f}")
    print(
        f"Geom: do={g.do:.4f} m, di={g.di:.4f} m, L={g.length:.2f} m, Nt={g.n_tubes}, "
        f"passes={g.n_passes_tube}, baffle_cut={g.baffle_cut:.2f}"
    )
    print(f"Obs: {r.notes}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Projeto industrial de trocador casco e tubo")
    parser.add_argument("--db", default="fluids_db.json", help="Caminho do banco de dados de fluidos")
    parser.add_argument("--plot", action="store_true", help="Gera dashboard PNG")
    args = parser.parse_args()

    db = load_fluid_db(Path(args.db))

    hot = StreamSpec(fluid="thermal_oil", m_dot=7.2, t_in=185.0, t_out_target=115.0)
    cold = StreamSpec(fluid="water", m_dot=10.0, t_in=28.0, t_out_target=None)
    foul = Fouling(tube=0.00018, shell=0.00030)

    best = optimize(db, hot, cold, foul)
    if not best:
        raise RuntimeError("Nenhuma alternativa viável encontrada.")

    print("Top alternativas com correlações industriais (Bell-Delaware + Gnielinski):")
    for i, (g, r) in enumerate(best, start=1):
        print_result(i, g, r)

    if args.plot:
        img = make_dashboard(best, Path("artifacts/heat_exchanger_dashboard.png"))
        if img:
            print(f"\nDashboard salvo em: {img}")
        else:
            print("\nMatplotlib não disponível; dashboard não foi gerado.")


if __name__ == "__main__":
    main()
