"""Exportação dos resultados para Excel (uma aba por tipo de resultado)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .metrics import DEVIATION_STATUS, PULSE_LIMITS, compare_with_reference, reference_consistency


def to_excel(an, path, ref=None):
    path = Path(path)
    meta = an.record.meta
    resumo = pd.DataFrame([
        ("Arquivo", an.record.path.name), ("Início", meta.get("StartDateTime")),
        ("Taxa amostral (Hz)", an.record.fs), ("Amostras por canal", an.record.n_samples),
        ("Rotação média (RPM)", round(an.rpm, 2)), ("Frequência média (Hz)", round(an.f_mean, 4)),
        ("Variação de rotação p-p (%)", round(an.speed["var_pp_pct"], 2)),
        ("Centro — Main G (g)", round(an.center["main_g"], 3)),
        ("Centro — curso (mm)", round(an.center["stroke_main"], 2)),
        ("Centro — ângulo (°)", round(an.center["angle"], 2)), ("Centro — fase Y-X (°)", round(an.center["phase"], 2)),
        ("Máximo — Main G (g)", round(an.maximum["main_g"], 3)),
        ("Máximo — curso (mm)", round(an.maximum["stroke_main"], 2)),
        ("K_v (ângulo vs horizontal)", round(an.throw["kv_horizontal_ref"], 3)),
        ("K_v (ângulo vs deck)", round(an.throw["kv_deck_ref"], 3)),
    ], columns=["Parâmetro", "Valor"])
    desv = pd.DataFrame([{"Desvio": k, "Valor (%)": round(v, 2), "Limite Pulse (%)": PULSE_LIMITS[k],
                          "Status": "OK" if v <= PULSE_LIMITS[k] else "ACIMA", "Fórmula": DEVIATION_STATUS[k]}
                         for k, v in an.deviations.items()])
    achados = pd.DataFrame([{"Nível": f.level, "Escopo": f.scope, "Achado": f.title, "Detalhe": f.detail,
                             "Ação": f.action} for f in an.findings])
    rot = pd.DataFrame({"t (s)": an.speed["profile_t"], "f (Hz)": an.speed["profile_f"],
                        "RPM": 60 * an.speed["profile_f"]})
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        resumo.to_excel(xw, sheet_name="Resumo", index=False)
        an.table().round(4).to_excel(xw, sheet_name="Sensores")
        desv.to_excel(xw, sheet_name="Desvios", index=False)
        achados.to_excel(xw, sheet_name="Diagnóstico", index=False)
        rot.iloc[::4].round(4).to_excel(xw, sheet_name="Rotação", index=False)
        if ref:
            compare_with_reference(an, ref).round(4).to_excel(xw, sheet_name="Comparação Pulse", index=False)
            reference_consistency(ref).round(4).to_excel(xw, sheet_name="Consistência fórmulas", index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)
    return path
