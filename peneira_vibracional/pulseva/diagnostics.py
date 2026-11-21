"""Verificações de integridade dos sensores e achados de diagnóstico.

Os sensores Pulse são acelerômetros MEMS triaxiais ±11 g, acoplados em DC.
Isso permite usar a gravidade (1 g) como referência de calibração estática:
em repouso relativo, a média de cada sensor deve ter módulo ≈ 1 g e nenhum
eixo pode ter média acima de 1 g em módulo.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SENSOR_RANGE_G = 11.0  # faixa nominal do sensor (folheto Pulse VA)

LEVELS = ("crítico", "atenção", "info")


@dataclass
class Finding:
    level: str          # crítico | atenção | info
    scope: str          # sensor/eixo ou "geral"
    title: str
    detail: str
    action: str = ""

    def __str__(self) -> str:
        s = f"[{self.level.upper()}] {self.scope}: {self.title} — {self.detail}"
        return s + (f"\n    → {self.action}" if self.action else "")


def run_health_checks(record, sensors: dict) -> tuple[list[Finding], dict]:
    """Retorna (lista de achados, {sensor: Z válido?})."""
    out: list[Finding] = []
    z_valid = {n: True for n in sensors}
    names = list(sensors)

    ac_rms = {n: record.sensors[n].std(axis=0) for n in names}
    med_ac = np.median(np.array(list(ac_rms.values())), axis=0)

    defective_axes = {}
    for n in names:
        raw = record.sensors[n]
        dc = raw.mean(axis=0)
        for i, ax in enumerate("XYZ"):
            bad_dc = abs(dc[i]) > 1.5
            low_ac = ac_rms[n][i] < 0.25 * med_ac[i]
            if bad_dc or (low_ac and i == 2 and ac_rms[n][i] < 0.03):
                defective_axes.setdefault(n, []).append(ax)
                if ax == "Z":
                    z_valid[n] = False
                why = []
                if bad_dc:
                    why.append(f"média de {dc[i]:+.2f} g (impossível para gravidade; faixa do sensor ±{SENSOR_RANGE_G:.0f} g)")
                if low_ac:
                    why.append(f"sinal AC de {ac_rms[n][i] * np.sqrt(2):.3f} g (√2·RMS) contra mediana de "
                               f"{med_ac[i] * np.sqrt(2):.3f} g nos demais sensores")
                out.append(Finding(
                    "crítico", f"{n}-{ax}", "Canal com defeito",
                    "; ".join(why) + ". O canal está saturado/travado e não representa o movimento. "
                    "Foi excluído das médias que o utilizam (corpo central Z e desvio Z).",
                    "Substituir/recalibrar o sensor ou verificar conector; repetir a medição."))
        clip = np.abs(raw) >= SENSOR_RANGE_G * 0.99
        for i, ax in enumerate("XYZ"):
            if ax in defective_axes.get(n, []):
                clip[:, i] = False
        if clip.any():
            axs = "".join(ax for i, ax in enumerate("XYZ") if clip[:, i].any())
            out.append(Finding("atenção", n, "Possível saturação",
                               f"{int(clip.sum())} amostras ≥ 99 % da faixa nos eixos {axs}."))

    # gravidade medida pelos sensores saudáveis
    mags = []
    for n in names:
        dc = record.sensors[n].mean(axis=0).copy()
        bad = defective_axes.get(n, [])
        if bad:
            continue
        mags.append(np.linalg.norm(dc))
    if mags:
        gm = float(np.mean(mags))
        if abs(gm - 1.0) > 0.05:
            out.append(Finding(
                "atenção", "geral", "Referência estática (gravidade) fora de 1 g",
                f"Módulo médio do vetor DC = {gm:.3f} g (faixa {min(mags):.3f}–{max(mags):.3f} g) "
                f"nos sensores sem defeito; esperado 1,000 g. O desvio é sistemático (~{(1 - gm) * 100:.0f} %), "
                "o que indica erro de sensibilidade/offset em DC ou escala de firmware. Se o mesmo fator "
                "afetar o sinal AC, G-Force e stroke estariam subestimados na mesma proporção.",
                "Verificar a calibração estática (ensaio de inversão ±1 g em cada eixo) e a escala do firmware."))

    # inclinação estática (montagem)
    tilts = {n: s.tilt_deg for n, s in sensors.items() if n not in defective_axes or "Y" not in defective_axes[n]}
    if tilts:
        tmin, tmax = min(tilts.values()), max(tilts.values())
        if tmax - tmin > 4.0:
            worst = max(tilts, key=lambda k: abs(tilts[k]))
            out.append(Finding(
                "atenção", "geral", "Montagem dos sensores não uniforme",
                f"A gravidade indica inclinação estática do eixo X entre {tmin:+.1f}° e {tmax:+.1f}° "
                f"(maior: {worst}, {tilts[worst]:+.1f}°). Num corpo rígido todos deveriam ser iguais; "
                "a diferença entra diretamente no Force Angle de cada sensor.",
                "Padronizar a montagem (base usinada/nivelada) ou corrigir o ângulo pela gravidade medida."))

    # kurtosis Z
    for n, s in sensors.items():
        if not z_valid[n]:
            continue
        if s.z_kurtosis > 4.0:
            out.append(Finding("atenção", f"{n}-Z", "Impactos no eixo lateral",
                               f"Kurtosis Z = {s.z_kurtosis:.2f} (> 4): sinal impulsivo — impactos, folgas ou "
                               "batidas de material contra a lateral.",
                               "Inspecionar fixações, revestimentos e folgas próximas ao sensor."))

    # sincronismo dos sensores sem fio
    return out, z_valid


def speed_findings(speed: dict, lags: dict) -> list[Finding]:
    out = []
    out.append(Finding(
        "info" if speed["var_pp_pct"] < 1.0 else "atenção", "geral", "Estabilidade da rotação",
        f"Rotação média {speed['rpm']:.1f} RPM ({speed['f_mean']:.3f} Hz); variação pico-a-pico "
        f"{speed['var_pp_pct']:.2f} % ({speed['f_min']:.3f}–{speed['f_max']:.3f} Hz) durante a gravação. "
        "Variações dessa ordem são típicas de alimentação irregular de material (escorregamento do motor) "
        "e justificam o rastreamento de ordem.",
        "Se a variação for recorrente, verificar regularidade da alimentação e o acionamento (correias/inversor)."))
    worst = max(lags.items(), key=lambda kv: abs(kv[1][0]))
    if abs(worst[1][0]) > 0.005:
        out.append(Finding(
            "info", "geral", "Sensores sem relógio comum",
            f"Os perfis de rotação dos sensores aparecem deslocados no tempo (até {worst[1][0] * 1e3:+.0f} ms em "
            f"{worst[0]}). Coerente com sensores Wi-Fi sem sincronismo de hardware: por isso a fase entre "
            "sensores é alinhada pelo eixo X (mesma convenção do Pulse)."))
    return out
