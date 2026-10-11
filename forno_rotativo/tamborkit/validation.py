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
    rows.append(_row("N2 processo", "combustível auxiliar por tonelada de carga", rot["aux_GJ_por_t"], "2,1–2,9 GJ/t",
                     1.5, 3.0, "GJ/t", "Beston (GLP 50–55 kg/t; diesel 55–65 kg/t)"))
    rows.append(_row("N2 processo", "eficiência da fornalha", rot["eficiencia_fornalha"] * 100, "45–70 %", 45, 72, "%",
                     "pesquisa R4 (balanço da fornalha; Hamm 2009)"))
    rows.append(_row("N2 processo", "gás próprio cobre a queima depois da partida",
                     100 * rot["Q_gas_proprio_GJ"] / max(rot["Q_queima_GJ"] - rot["Q_aux_GJ"] + rot["Q_gas_proprio_GJ"], 1e-9),
                     "sim (≈ 100 %)", 95, 100.1, "%", "Beston / Ma & Zhong 2018: autossuficiente após a partida"))
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
    if st.get("lacey") is not None:
        rows.append(_row("N1 DEM", "índice de mistura de Lacey após 1 volta", st["lacey"], "> 0,5", 0.5, 1.0, "",
                         "mistura rápida frente à batelada (horas)"))
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
