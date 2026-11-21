"""Métricas de engenharia da peneira vibratória (modelo do relatório Pulse VA).

Convenções
----------
* Referencial da máquina: X longitudinal (sentido do fluxo), Y vertical,
  Z lateral. Os sensores do lado esquerdo (L) são montados espelhados em
  relação aos do lado direito (R): no dado bruto X e Z de L têm sinal oposto
  (comprovado pela correlação X–Y e pela gravidade medida). Por isso
  ``SIDE_SIGN['L'] = (-1, +1, -1)`` leva tudo ao mesmo referencial.
* "G-Force" de um eixo = amplitude (pico) da componente 1× da aceleração, em g.
* "RMS" (coluna do Pulse) = √2·RMS do sinal AC completo (equivalente de pico).
* Stroke (curso) = deslocamento pico-a-pico do movimento harmônico::

      s = 2·A·g0/ω²,  ω = 2πf          (A em g, g0 = 9,80665 m/s²)

* Órbita X–Y da componente 1×: elipse descrita por x = |Px|cos(θ),
  y = |Py|cos(θ − φ). "Main G" = semi-eixo maior; "Force Angle" = inclinação
  do eixo maior em relação a X; "Phase" = atraso φ de Y em relação a X.
  Calculados pela SVD da matriz [[Re Px, Im Px], [Re Py, Im Py]] (elipse de
  polarização; Born & Wolf).
* Sincronização entre sensores: como os sensores são sem fio, o Pulse
  alinha todos os fasores pela fase do eixo X (verificado: o "Center Body" do
  relatório só é reproduzido com essa hipótese).
* Corpo central ("Center Body", centro de gravidade) = média dos fasores
  sincronizados dos 4 sensores de canto (L1, R1, L4, R4).
* Desvios (% relativos), com a = soma de fasores de um grupo e b do outro::

      desvio = |a − b| / |a + b| · 100

  Pitch: Y alimentação (L1+R1) × descarga (L4+R4)     — confirmado
  Roll : Y esquerdo (L1+L4) × direito (R1+R4)          — confirmado
  Twist: Y diagonais (L1+R4) × (R1+L4)                 — confirmado
  Yaw  : X esquerdo × direito (hipótese de corpo rígido — não confirmada)
  Z    : |Z médio| / Main G do centro (hipótese — não confirmada)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.stats import kurtosis

from .io import Record
from .tracking import (RotationTrack, estimate_lag, fractional_order_phasors, order_phasors,
                       per_revolution_phasors, track_rotation)

G0 = 9.80665  # m/s²
SIDE_SIGN = {"L": np.array([-1.0, 1.0, -1.0]), "R": np.array([1.0, 1.0, 1.0])}
CORNERS = ("L1", "R1", "L4", "R4")
#: Níveis de aceitação impressos no relatório Pulse (Phase Report).
PULSE_LIMITS = {"pitch": 45.0, "roll": 4.0, "yaw": 4.0, "twist": 3.0, "z": 3.0}
DEVIATION_STATUS = {"pitch": "confirmada", "roll": "confirmada", "twist": "confirmada",
                    "yaw": "hipótese", "z": "hipótese"}
ORDERS = (1, 2, 3, 4, 5)


# --------------------------------------------------------------------------- #
# Relações básicas
# --------------------------------------------------------------------------- #
def stroke_mm(acc_g, f_hz):
    """Curso pico-a-pico (mm) de um movimento harmônico de amplitude ``acc_g`` (g)."""
    w = 2 * np.pi * np.asarray(f_hz, float)
    return 2 * np.asarray(acc_g, float) * G0 / w**2 * 1e3


def accel_from_stroke(stroke, f_hz):
    w = 2 * np.pi * np.asarray(f_hz, float)
    return np.asarray(stroke, float) / 1e3 / 2 * w**2 / G0


def ellipse_from_phasors(px: complex, py: complex) -> dict:
    """Elipse da órbita X–Y a partir dos fasores 1× (convenção x = Re{P e^{jθ}})."""
    m = np.array([[px.real, px.imag], [py.real, py.imag]])
    u, s, _ = np.linalg.svd(m)
    angle = np.degrees(np.arctan2(u[1, 0], u[0, 0])) % 180.0
    phase = np.degrees(np.angle(px) - np.angle(py))          # atraso de Y em relação a X
    phase = (phase + 180.0) % 360.0 - 180.0
    return {"main": float(s[0]), "minor": float(s[1]), "angle": float(angle), "phase": float(phase)}


def ellipse_from_amplitudes(ax: float, ay: float, phase_deg: float) -> dict:
    """Mesma elipse a partir de amplitudes e defasagem (usado para checar o relatório)."""
    return ellipse_from_phasors(complex(ax, 0.0), ay * np.exp(-1j * np.radians(phase_deg)))


def relative_difference(a: complex, b: complex) -> float:
    """|a − b| / |a + b| em %."""
    return float(abs(a - b) / abs(a + b) * 100.0)


#: K_v para o qual o tempo de voo de um leito plástico é exatamente 1 período: √(1+π²)
KV_ONE_PERIOD = float(np.sqrt(1 + np.pi**2))


def throw_index(main_g: float, angle_h_deg: float, incl_deg: float) -> float:
    """Índice de lançamento (Wurfkennziffer) K_v = Γ·sin(α+β)/cos β.

    Γ = aceleração de pico na direção de lançamento (g), α = ângulo de
    lançamento em relação à horizontal, β = inclinação do deck (lançamento
    no sentido descendente do deck). K_v > 1 → o material decola do deck.
    """
    a, b = np.radians(angle_h_deg), np.radians(incl_deg)
    return float(main_g * np.sin(a + b) / np.cos(b))


# --------------------------------------------------------------------------- #
# Resultado por sensor
# --------------------------------------------------------------------------- #
@dataclass
class SensorResult:
    name: str
    side: str
    position: int
    track: RotationTrack = field(repr=False)
    P: np.ndarray = field(repr=False)          # (n_ordens, 3) fasores no referencial da máquina
    Psync: np.ndarray = field(repr=False)      # (3,) 1× sincronizado (fase de X = 0)
    per_rev: np.ndarray = field(repr=False)    # (n_rev, 3) fasores 1× por rotação
    g: np.ndarray                              # amplitude 1× por eixo (g)
    rms_pk: np.ndarray                         # √2·RMS por eixo (g)
    stroke: np.ndarray                         # curso por eixo (mm)
    main_g: float
    minor_g: float
    angle: float
    phase_yx: float
    stroke_main: float
    thd: np.ndarray                            # distorção harmônica (ordens 2–5 / 1×)
    z_kurtosis: float
    dc: np.ndarray                             # média bruta (g) — gravidade + offset
    tilt_deg: float                            # inclinação estática do eixo X (referencial da máquina)
    main_g_rev_std: float                      # desvio-padrão ciclo a ciclo do Main G
    sub: np.ndarray = field(default=None, repr=False)  # (2, 3) amplitudes 0,5× e 1,5× (g)

    @property
    def f_mean(self) -> float:
        return self.track.f_mean

    @property
    def rotation_sense(self) -> str:
        return "anti-horário" if self.phase_yx > 0 else "horário"


def analyze_sensor(name: str, acc: np.ndarray, fs: float, f_guess: float | None = None) -> SensorResult:
    side, pos = name[0].upper(), int(name[1:]) if name[1:].isdigit() else 0
    sign = SIDE_SIGN.get(side, SIDE_SIGN["R"])
    raw = np.asarray(acc, float)
    dc = raw.mean(axis=0)
    a = (raw - dc) * sign                                   # AC, referencial da máquina
    tr = track_rotation(a[:, :2], fs, f_guess=f_guess)
    P = order_phasors(a, tr, ORDERS)
    p1 = P[0]
    psync = p1 * np.exp(-1j * np.angle(p1[0]))
    g = np.abs(p1)
    el = ellipse_from_phasors(psync[0], psync[1])
    per = per_revolution_phasors(a, tr)
    main_rev = np.array([ellipse_from_phasors(r[0], r[1])["main"] for r in per])
    thd = np.sqrt((np.abs(P[1:]) ** 2).sum(axis=0)) / np.maximum(g, 1e-12)
    dcm = dc * sign
    return SensorResult(
        name=name, side=side, position=pos, track=tr, P=P, Psync=psync, per_rev=per,
        g=g, rms_pk=np.sqrt(2) * a.std(axis=0), stroke=stroke_mm(g, tr.f_mean),
        main_g=el["main"], minor_g=el["minor"], angle=el["angle"], phase_yx=el["phase"],
        stroke_main=float(stroke_mm(el["main"], tr.f_mean)), thd=thd,
        z_kurtosis=float(kurtosis(a[:, 2], fisher=False)), dc=dc,
        tilt_deg=float(np.degrees(np.arctan2(dcm[0], -dcm[1]))),
        main_g_rev_std=float(main_rev.std(ddof=1)),
        sub=np.abs(fractional_order_phasors(a, tr, (0.5, 1.5))),
    )


# --------------------------------------------------------------------------- #
# Análise completa
# --------------------------------------------------------------------------- #
@dataclass
class Analysis:
    record: Record = field(repr=False)
    sensors: dict
    f_mean: float
    center: dict
    maximum: dict
    deviations: dict
    throw: dict
    speed: dict
    lags: dict
    findings: list
    excluded: dict

    @property
    def rpm(self) -> float:
        return 60.0 * self.f_mean

    def table(self):
        """Tabela por sensor no formato do relatório Pulse (pandas.DataFrame)."""
        import pandas as pd
        rows = []
        for s in self.sensors.values():
            rows.append({
                "Sensor": s.name, "Main G (g)": s.main_g, "Stroke (mm)": s.stroke_main,
                "Freq (Hz)": s.f_mean, "Force Angle (°)": s.angle, "Fase Y-X (°)": s.phase_yx,
                "X G (g)": s.g[0], "Y G (g)": s.g[1], "Z G 1× (g)": s.g[2],
                "X stroke (mm)": s.stroke[0], "Y stroke (mm)": s.stroke[1], "Z stroke (mm)": s.stroke[2],
                "X RMS√2 (g)": s.rms_pk[0], "Y RMS√2 (g)": s.rms_pk[1], "Z RMS√2 (g)": s.rms_pk[2],
                "Z kurtosis": s.z_kurtosis, "THD Y (%)": 100 * s.thd[1],
                "σ ciclo Main G (g)": s.main_g_rev_std,
                "Y 0,5× (g)": s.sub[0, 1], "Y 1,5× (g)": s.sub[1, 1],
            })
        return pd.DataFrame(rows).set_index("Sensor")


def _center_body(sensors: dict, f: float, z_valid: dict) -> dict:
    ps = np.array([sensors[c].Psync for c in CORNERS])
    c = ps.mean(axis=0)
    zs = [sensors[k].Psync[2] for k in CORNERS if z_valid.get(k, True)]
    cz = np.mean(zs) if zs else 0j
    el = ellipse_from_phasors(c[0], c[1])
    g = np.array([abs(c[0]), abs(c[1]), abs(cz)])
    return {"phasors": np.array([c[0], c[1], cz]), "g": g, "stroke": stroke_mm(g, f),
            "main_g": el["main"], "minor_g": el["minor"], "angle": el["angle"],
            "phase": el["phase"], "stroke_main": float(stroke_mm(el["main"], f))}


def _maximum_body(sensors: dict, f: float) -> dict:
    gx = max(sensors.values(), key=lambda s: s.g[0])
    gy = max(sensors.values(), key=lambda s: s.g[1])
    gm = max(sensors.values(), key=lambda s: s.main_g)
    g = np.array([gx.g[0], gy.g[1]])
    return {"g": g, "stroke": stroke_mm(g, f), "main_g": gm.main_g,
            "stroke_main": float(stroke_mm(gm.main_g, f)),
            "where": {"X": gx.name, "Y": gy.name, "Main": gm.name}}


def _deviations(sensors: dict, center: dict, z_valid: dict) -> dict:
    X = {k: sensors[k].Psync[0] for k in CORNERS}
    Y = {k: sensors[k].Psync[1] for k in CORNERS}
    zs = [sensors[k].Psync[2] for k in CORNERS if z_valid.get(k, True)]
    dev = {
        "pitch": relative_difference(Y["L1"] + Y["R1"], Y["L4"] + Y["R4"]),
        "roll": relative_difference(Y["L1"] + Y["L4"], Y["R1"] + Y["R4"]),
        "twist": relative_difference(Y["L1"] + Y["R4"], Y["R1"] + Y["L4"]),
        "yaw": relative_difference(X["L1"] + X["L4"], X["R1"] + X["R4"]),
        "z": float(abs(np.mean(zs)) / center["main_g"] * 100.0) if zs else float("nan"),
    }
    return dev


def analyze(record: Record, inclination_deg: float | None = None) -> Analysis:
    """Executa toda a cadeia de cálculo sobre uma gravação Pulse."""
    from .diagnostics import run_health_checks

    fs = record.fs
    names = record.names
    # frequência inicial comum (todos os sensores), depois rastreamento por sensor
    from .tracking import dominant_frequency
    f_guess = float(np.median([dominant_frequency(record.sensors[n][:, :2], fs) for n in names]))
    sensors = {n: analyze_sensor(n, record.sensors[n], fs, f_guess) for n in names}
    f_mean = float(np.mean([s.f_mean for s in sensors.values()]))

    findings, z_valid = run_health_checks(record, sensors)
    excluded = {k: "eixo Z" for k, ok in z_valid.items() if not ok}

    center = _center_body(sensors, f_mean, z_valid)
    maximum = _maximum_body(sensors, f_mean)
    devs = _deviations(sensors, center, z_valid)

    # rotação: perfil comum (média dos sensores) e estatística
    fi = np.array([s.track.f_inst for s in sensors.values()])
    e = sensors[names[0]].track.i0
    prof = fi[:, e:-e].mean(axis=0)
    speed = {"f_mean": f_mean, "rpm": 60 * f_mean, "f_min": float(prof.min()),
             "f_max": float(prof.max()), "f_std": float(prof.std()),
             "var_pp_pct": float((prof.max() - prof.min()) / f_mean * 100),
             "profile_t": np.arange(e, e + prof.size) / fs, "profile_f": prof}

    # atraso aparente entre sensores (perfis de rotação) — indicativo de sincronismo
    ref = names[-1]
    lags = {n: estimate_lag(sensors[n].track.f_inst[e:-e], sensors[ref].track.f_inst[e:-e], fs,
                            max_lag_s=0.5) for n in names}

    from .diagnostics import speed_findings
    findings += speed_findings(speed, lags)

    incl = inclination_deg if inclination_deg is not None else (record.inclination_deg or 0.0)
    throw = {
        "inclination": incl,
        "kv_horizontal_ref": throw_index(center["main_g"], center["angle"], incl),
        "kv_deck_ref": float(center["main_g"] * np.sin(np.radians(center["angle"])) / np.cos(np.radians(incl))),
        "angle_to_deck_if_horizontal_ref": center["angle"] + incl,
        "mean_sensor_tilt": float(np.mean([sensors[k].tilt_deg for k in CORNERS if z_valid.get(k, True)])),
    }
    return Analysis(record=record, sensors=sensors, f_mean=f_mean, center=center,
                    maximum=maximum, deviations=devs, throw=throw, speed=speed,
                    lags=lags, findings=findings, excluded=excluded)


# --------------------------------------------------------------------------- #
# Comparação com o relatório Pulse
# --------------------------------------------------------------------------- #
def reference_consistency(ref: dict):
    """Recalcula Main G, ângulo, strokes e corpo central a partir dos números do
    próprio relatório Pulse — valida as fórmulas sem usar os dados brutos."""
    import pandas as pd
    f = ref["meta"]["freq_hz"]
    rows = []
    for name, d in ref["sensors"].items():
        gx, gy, gz = d["g"]
        for ax, gv, sv in zip("XYZ", d["g"], d["stroke"]):
            rows.append({"Item": f"{name} stroke {ax} (mm)", "Pulse": sv,
                         "Recalculado": float(stroke_mm(gv, f))})
        rows.append({"Item": f"{name} stroke Main (mm)", "Pulse": d["stroke_main"],
                     "Recalculado": float(stroke_mm(d["main_g"], f))})
        if name in ref.get("phase_yx", {}):
            el = ellipse_from_amplitudes(gx, gy, ref["phase_yx"][name])
            rows.append({"Item": f"{name} Main G (g)", "Pulse": d["main_g"], "Recalculado": el["main"]})
            rows.append({"Item": f"{name} Force Angle (°)", "Pulse": d["angle"], "Recalculado": el["angle"]})
    # corpo central = média dos 4 cantos com fases relativas a X
    ph = ref["phase_yx"]
    xs = np.array([ref["sensors"][c]["g"][0] for c in CORNERS], complex)
    ys = np.array([ref["sensors"][c]["g"][1] * np.exp(-1j * np.radians(ph[c])) for c in CORNERS])
    cx, cy = xs.mean(), ys.mean()
    el = ellipse_from_phasors(cx, cy)
    c = ref["center"]
    rows += [
        {"Item": "Centro X (g)", "Pulse": c["g"][0], "Recalculado": abs(cx)},
        {"Item": "Centro Y (g)", "Pulse": c["g"][1], "Recalculado": abs(cy)},
        {"Item": "Centro Main G (g)", "Pulse": c["main_g"], "Recalculado": el["main"]},
        {"Item": "Centro ângulo (°)", "Pulse": c["angle"], "Recalculado": el["angle"]},
        {"Item": "Centro fase (°)", "Pulse": c["phase"], "Recalculado": el["phase"]},
        {"Item": "Centro stroke Main (mm)", "Pulse": c["stroke_main"],
         "Recalculado": float(stroke_mm(el["main"], f))},
    ]
    Y = dict(zip(CORNERS, ys))
    d = ref["deviations"]
    rows += [
        {"Item": "Pitch (%)", "Pulse": d["pitch"], "Recalculado": relative_difference(Y["L1"] + Y["R1"], Y["L4"] + Y["R4"])},
        {"Item": "Roll (%)", "Pulse": d["roll"], "Recalculado": relative_difference(Y["L1"] + Y["L4"], Y["R1"] + Y["R4"])},
        {"Item": "Twist (%)", "Pulse": d["twist"], "Recalculado": relative_difference(Y["L1"] + Y["R4"], Y["R1"] + Y["L4"])},
    ]
    df = pd.DataFrame(rows)
    df["Diferença"] = df["Recalculado"] - df["Pulse"]
    return df


def compare_with_reference(an: Analysis, ref: dict):
    """Compara a análise do XML com um relatório Pulse de outra gravação.

    Em regime supercrítico (rotação >> frequência natural da suspensão) o
    curso independe da rotação e a aceleração escala com f². Assim:
    strokes, ângulos, fases e desvios são comparados diretamente, e as
    acelerações são corrigidas por (f_ref/f_xml)².
    """
    import pandas as pd
    f_ref = ref["meta"]["freq_hz"]
    k = (f_ref / an.f_mean) ** 2
    rows = []

    def add(grp, item, ours, pulse, scaled=None, unit=""):
        cmp = ours if scaled is None else scaled
        rows.append({"Grupo": grp, "Item": item, "Unid.": unit, "Python (XML)": ours,
                     "Python @ f_ref": cmp, "Pulse": pulse, "Δ": cmp - pulse,
                     "Δ (%)": (cmp - pulse) / pulse * 100 if pulse else np.nan})

    for name, d in ref["sensors"].items():
        s = an.sensors.get(name)
        if s is None:
            continue
        add("Stroke", f"{name} Main", s.stroke_main, d["stroke_main"], unit="mm")
        add("Stroke", f"{name} X", s.stroke[0], d["stroke"][0], unit="mm")
        add("Stroke", f"{name} Y", s.stroke[1], d["stroke"][1], unit="mm")
        add("G-Force", f"{name} Main", s.main_g, d["main_g"], s.main_g * k, unit="g")
        add("G-Force", f"{name} X", s.g[0], d["g"][0], s.g[0] * k, unit="g")
        add("G-Force", f"{name} Y", s.g[1], d["g"][1], s.g[1] * k, unit="g")
        add("Ângulo", f"{name} Force Angle", s.angle, d["angle"], unit="°")
        if name in ref.get("phase_yx", {}):
            add("Fase", f"{name} Y-X", s.phase_yx, ref["phase_yx"][name], unit="°")
    c, rc = an.center, ref["center"]
    add("Centro", "Stroke Main", c["stroke_main"], rc["stroke_main"], unit="mm")
    add("Centro", "Stroke X", c["stroke"][0], rc["stroke"][0], unit="mm")
    add("Centro", "Stroke Y", c["stroke"][1], rc["stroke"][1], unit="mm")
    add("Centro", "Main G", c["main_g"], rc["main_g"], c["main_g"] * k, unit="g")
    add("Centro", "Force Angle", c["angle"], rc["angle"], unit="°")
    add("Centro", "Fase Y-X", c["phase"], rc["phase"], unit="°")
    m, rm = an.maximum, ref["maximum"]
    add("Máximo", "Stroke Main", m["stroke_main"], rm["stroke_main"], unit="mm")
    add("Máximo", "Main G", m["main_g"], rm["main_g"], m["main_g"] * k, unit="g")
    for key in ("pitch", "roll", "twist", "yaw", "z"):
        add("Desvio", f"{key.capitalize()} ({DEVIATION_STATUS[key]})", an.deviations[key],
            ref["deviations"][key], unit="%")
    df = pd.DataFrame(rows)
    df.attrs["f_ref"] = f_ref
    df.attrs["f_xml"] = an.f_mean
    df.attrs["scale"] = k
    return df
