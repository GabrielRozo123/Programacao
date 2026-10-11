"""Escada de validação do tambor em batelada (cada item: valor do modelo × faixa da literatura).

N1 componentes  — cinética (picos de DTG a 10 K/min; T para k = 10⁻³ s⁻¹), radiação (WSGG), DEM (regime,
                  ângulo dinâmico, arco coberto), balanços de massa e energia, conservação de massa da LES.
N2 processo     — coeficiente parede-carga (Suzuki 2008: 22–55 W/m²K), ganho das aletas (7–26 %),
                  ganho da rotação acima de ~1 rpm pequeno, duração da batelada (IVIG: 6–8 h),
                  combustível auxiliar por tonelada (Beston: 2,1–2,9 GJ/t), eficiência da fornalha (45–70 %),
                  queima autossuficiente depois da partida, rendimentos (Faussone 2022; Fulgencio-Medrano 2022).
N3 sistema      — tambor parado × girando: mancha quente acima do limite do aço, batelada muito mais longa.
"""
from __future__ import annotations

from . import feed as fd

OK, WARN = "dentro", "fora"


def _row(group, name, model, target, lo, hi, unit="", source=""):
    ok = (model >= lo) and (model <= hi)
    return dict(grupo=group, item=name, modelo=model, alvo=target, ok=ok, unidade=unit, fonte=source)


def chemistry_checks() -> list:
    rows = []
    for k, tgt in (("HDPE", 475), ("LDPE", 465), ("PP", 455), ("PS", 420)):
        p = fd.dtg_peak(k, 10)
        rows.append(_row("N1 cinética", f"pico de DTG do {k} a 10 K/min", p, f"{tgt} ± 10 °C", tgt - 10, tgt + 10,
                         "°C", "picos de consenso (Aboulkas 2010; Westerhout 1997)"))
    for k, tgt, tol in (("PVC", 251, 15), ("PET", 395, 15), ("PP", 402, 10), ("LDPE", 417, 10), ("HDPE", 429, 10),
                        ("PS", 370, 10)):
        v = fd.t_k1e3(k)
        rows.append(_row("N1 cinética", f"T com k = 10⁻³ s⁻¹ ({k})", v, f"{tgt} ± {tol} °C", tgt - tol, tgt + tol,
                         "°C", "pesquisa R2 (conjuntos cinéticos da literatura)"))
    y = fd.ultimate_yields(fd.CHARGES["plastico_triado"])
    oil = sum(y[k] for k in fd.CONDENSABLE) * 100
    rows.append(_row("N1 cinética", "óleo + cera, plástico triado (poliolefinas)", oil, "70–90 %", 70, 90, "%",
                     "Fulgencio-Medrano 2022 (filme triado 70,6 %); Beston PEAD > 85 %"))
    return rows


def furnace_checks() -> list:
    from .furnace import wsgg_emissivity
    rows = []
    e = float(wsgg_emissivity(1200.0, 0.2 * 0.35))
    rows.append(_row("N1 radiação", "emissividade do gás de combustão no corredor (WSGG)", e, "0,10–0,18", 0.10, 0.18,
                     "", "Smith, Shen & Friedman 1982; pesquisa R4"))
    return rows


def batch_checks(rot: dict, est: dict | None = None, sweep: dict | None = None, log=None) -> list:
    """rot/est: resumos (BatchDrum.summary()) + extras h_mean, Tmax; sweep: {'sem_aletas':…, 'rpm2':…}."""
    rows = []
    rows.append(_row("N1 balanços", "fecho de massa da batelada", abs(rot["fecho_massa"]) * 100, "< 1 %", 0, 1, "%"))
    rows.append(_row("N1 balanços", "fecho de energia do casco", abs(rot["fecho_casco"]) * 100, "< 1 %", 0, 1, "%"))
    rows.append(_row("N2 processo", "duração da batelada (1 t, parede a 500 °C)", rot["duracao_h"], "6–8 h", 5.5, 8.5,
                     "h", "IVIG/UFRJ (vídeo: 6 a 8 h a partir da carga)"))
    if "h_mean" in rot:
        rows.append(_row("N2 processo", "coeficiente parede → carga médio", rot["h_mean"], "22–55 W/m²K", 22, 55,
                         "W/m²K", "Suzuki et al. 2008 (resíduo em forno rotativo com aletas)"))
    rows.append(_row("N2 processo", "combustível auxiliar por tonelada de carga", rot["aux_GJ_por_t"], "2,1–2,9 GJ/t (± 25 %)",
                     1.6, 3.6, "GJ/t", "Beston (GLP 50–55 kg/t; diesel 55–65 kg/t)"))
    rows.append(_row("N2 processo", "eficiência da fornalha", rot["eficiencia_fornalha"] * 100, "45–70 %", 45, 72, "%",
                     "pesquisa R4 (balanço da fornalha; Hamm 2009)"))
    if log:
        import numpy as np
        t = np.array([r["t_h"] for r in log]); qn = np.array([r["Q_ncg_kW"] for r in log])
        qf = np.array([r["Q_fire_kW"] for r in log])
        on = np.nonzero(qn > 0.5 * qf)[0]
        if len(on):
            sel = slice(on[0], None)
            trap = getattr(np, "trapezoid", None) or np.trapz
            frac = 100 * trap(qn[sel], t[sel]) / max(trap(qf[sel], t[sel]), 1e-9)
            rows.append(_row("N2 processo", "gás próprio cobre a queima depois da troca", frac, "≈ 100 %", 95, 100.1, "%",
                             "Beston; Ma & Zhong 2018: autossuficiente após a partida"))
    oil = rot["oleo"] * 100
    rows.append(_row("N2 rendimentos", "óleo (base úmida, lixo marinho misto)", oil, "45–70 %", 45, 70, "%",
                     "Faussone 2022 (45 %, 400 °C); Fulgencio 2022 (61 %); IVIG ~70 %"))
    rows.append(_row("N2 rendimentos", "carvão + cinzas", (rot["carvao"] + rot["cinzas"]) * 100, "10–26 %", 10, 26, "%",
                     "Faussone 2022 (26 %); Fulgencio 2022 (16,6–24,7 %)"))
    if sweep and "sem_aletas" in sweep:
        gain = 100 * (sweep["sem_aletas"]["duracao_h"] - rot["duracao_h"]) / sweep["sem_aletas"]["duracao_h"]
        rows.append(_row("N2 processo", "redução do tempo com 6 aletas", gain, "7–26 %", 5, 26, "%",
                         "Suzuki et al. 2008 (42 → 31–35 min)"))
    if sweep and "rpm2" in sweep:
        g2 = 100 * (rot["duracao_h"] - sweep["rpm2"]["duracao_h"]) / rot["duracao_h"]
        rows.append(_row("N2 processo", "ganho de 0,8 → 2 rpm", g2, "pequeno (< 15 %)", 0, 15, "%",
                         "pesquisa R3 (ganho modesto acima de ~1–2 rpm)"))
    if est is not None:
        rows.append(_row("N3 sistema", "tambor parado: batelada mais longa", est["duracao_h"] / rot["duracao_h"],
                         "> 1,5×", 1.5, 100, "×", "KINTEK; penetração × condução pura (brief §2)"))
        rows.append(_row("N3 sistema", "tambor parado: mancha quente do casco", est["Tmax"], "> limite do aço (475 °C)",
                         475, 2000, "°C", "Q345R ≤ 475 °C de serviço; caso P4O (brief)"))
    return rows


def dem_checks(st: dict, fill: float, drum) -> list:
    from .geometry import fill_half_angle
    rows = []
    rows.append(_row("N1 DEM", "número de Froude (regime de rolamento)", drum.froude(), "10⁻⁴–10⁻²", 1e-4, 1e-2, "",
                     "Henein et al. 1983; Mellmann 2001"))
    rows.append(_row("N1 DEM", "ângulo dinâmico do leito", st["beta_deg"], "30–50°", 30, 50, "°",
                     "resíduos/pedaços grossos (pesquisa R5)"))
    eps = fill_half_angle(fill)
    cov = st["covered_frac"]
    geo = 2 * eps / (2 * 3.14159265)
    rows.append(_row("N1 DEM", "arco do casco coberto: DEM / geometria", cov / geo, "1 ± 0,2", 0.8, 1.2, "",
                     "segmento circular (base do modelo de penetração)"))
    return rows


def summary(rows) -> str:
    n = len(rows); k = sum(r["ok"] for r in rows)
    lines = [f"{k} de {n} verificações dentro do alvo"]
    for r in rows:
        v = r["modelo"]
        vs = f"{v:.3g}" if abs(v) < 1e4 else f"{v:.2e}"
        lines.append(f"  [{'ok' if r['ok'] else '!!'}] {r['grupo']:<14} {r['item']:<52} {vs:>8} {r['unidade']:<5} alvo {r['alvo']}")
    from .video import br
    return br("\n".join(lines))


def phase_checks(fase: dict, log: list, drum, slab: float) -> list:
    """DEM com mudança de fase × modelo da batelada (massa e enchimento) e a ordem física das reações."""
    import numpy as np
    from .phasedem import melt_viscosity
    rows = []
    recs = fase["recs"]
    lt = np.array([r["t_h"] for r in log]) * 3600.0
    frac = slab / drum.L
    errs, fills = [], []
    for rec in recs[len(recs) // 10::max(len(recs) // 10, 1)]:
        m_bed = float(np.interp(rec["t_b"], lt, [r["carga_kg"] for r in log])) * frac
        m_dem = rec["m_dem"] + rec["pool"].get("mass", 0.0)
        errs.append(abs(m_dem - m_bed) / max(m_bed, 1e-9))
        F_b = float(np.interp(rec["t_b"], lt, [r["enchimento"] for r in log]))
        fills.append(rec["fill_dem"] / max(F_b, 1e-9))
    rows.append(_row("N1 mudança de fase", "massa do DEM (pedaços + poça) × batelada", 100 * float(np.max(errs)),
                     "< 5 %", 0, 5, "%", "acoplamento em uma via (o DEM segue a conversão de cada componente)"))
    rows.append(_row("N1 mudança de fase", "enchimento do DEM / enchimento da batelada (mediana)",
                     float(np.median(fills)), "1 ± 0,35", 0.65, 1.35, "",
                     "colapso solto → denso por material × volume aparente do modelo da batelada"))
    order = ["água", "PVC", "celulósicos", "PS", "PP", "PE"]
    t = np.array([r["t_h"] for r in log])
    peaks = [float(t[int(np.argmax([r[f"taxa_{g}"] for r in log]))]) for g in order]
    ok = all(b >= a for a, b in zip(peaks, peaks[1:]))
    rows.append(_row("N2 cinética", "ordem dos picos de taxa: água < PVC < celulósicos < PS < PP < PE", 1.0 if ok else 0.0,
                     "sim", 0.5, 1.5, "", "ordem dos picos de TGA (Westerhout 1997; Aboulkas 2010; pesquisa R2)"))
    eta_melt = float(melt_viscosity(473.15, 0.0))
    eta_wax = float(melt_viscosity(693.15, 0.3))
    rows.append(_row("N1 mudança de fase", "viscosidade do PE fundido a 200 °C", eta_melt, "10²–10⁴ Pa·s", 1e2, 1e4,
                     "Pa·s", "PE/PP fundidos (faixa de catálogo; reator agitado, Cross)"))
    rows.append(_row("N1 mudança de fase", "viscosidade do fundido craqueado (420 °C, 30 % convertido)", eta_wax,
                     "≤ 0,1 Pa·s (cera)", 1e-4, 0.1, "Pa·s", "ceras de PE (POLYWAX: mPa·s); Westerhout"))
    return rows
