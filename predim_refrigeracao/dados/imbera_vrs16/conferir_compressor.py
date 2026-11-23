"""Confere o mapa do compressor VEMT404U transcrito do datasheet Embraco (compressor_VEMT404U.csv).

Duas checagens por ponto:
1. COP publicado = capacidade / potência (dentro do arredondamento);
2. capacidade = ṁ (h_retorno − h_líquido) do R290 pelo CoolProp, com a condição do catálogo
   (gás de retorno a 4,4 °C, sub-resfriamento 0 K), dentro do arredondamento de Q e ṁ.

Uso: python dados/imbera_vrs16/conferir_compressor.py
"""
import csv
import os

import CoolProp.CoolProp as CP

ARQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compressor_VEMT404U.csv")
T_RETORNO_C = 4.4


def delta_h(t_evap_C: float, t_cond_C: float) -> float:
    P_e = CP.PropsSI("P", "T", t_evap_C + 273.15, "Q", 1, "Propane")
    h_ret = CP.PropsSI("H", "T", T_RETORNO_C + 273.15, "P", P_e, "Propane")
    h_liq = CP.PropsSI("H", "T", t_cond_C + 273.15, "Q", 0, "Propane")
    return h_ret - h_liq


def main() -> int:
    linhas = list(csv.DictReader(open(ARQ, encoding="utf-8")))
    falhas = 0
    for r in linhas:
        Q, cop, W = float(r["capacidade_W"]), float(r["cop_W_W"]), float(r["potencia_W"])
        m = float(r["vazao_kg_h"]) / 3600.0
        dm = 0.05 if r["vazao_kg_h"].count(".") and len(r["vazao_kg_h"].split(".")[1]) == 1 else 0.005
        x = Q / (m * delta_h(float(r["t_evap_C"]), float(r["t_cond_C"])))
        tol_m = 0.5 / Q + dm / float(r["vazao_kg_h"]) + 0.004
        tol_cop = 0.5 / W * Q / W + 0.5 / Q * Q / W + 0.006
        if abs(x - 1.0) > tol_m or abs(Q / W - cop) > tol_cop:
            falhas += 1
            print("FORA:", r)
    print(f"{len(linhas)} pontos conferidos, {falhas} fora da tolerância")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
