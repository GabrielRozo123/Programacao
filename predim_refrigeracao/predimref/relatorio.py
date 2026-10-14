"""Saídas: resumo legível, dicionário/JSON para o acoplamento com o Simcenter Amesim e tabelas."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass

from .constantes import W_PARA_BTUH


def _c(T: float) -> float:
    return T - 273.15


def tabela_estados(res) -> list[dict]:
    nomes = {"1": "saída do evaporador", "1s": "sucção do compressor", "2s": "descarga isentrópica",
             "2": "descarga real", "3": "saída do condensador", "3i": "entrada do capilar",
             "4": "entrada do evaporador"}
    linhas = []
    for k, e in res.ciclo.estados.items():
        linhas.append({"ponto": k, "descricao": nomes[k], "P_bar": e.P / 1e5, "T_C": _c(e.T),
                       "h_kJ_kg": e.h / 1e3, "s_kJ_kgK": e.s / 1e3, "rho_kg_m3": e.rho,
                       "titulo": e.x if 0.0 <= e.x <= 1.0 else None})
    return linhas


def perfil_trocador(r) -> list[dict]:
    """Perfil ao longo do circuito (posição acumulada por circuito)."""
    out, L = [], 0.0
    for s in r.segmentos:
        L += s.L
        out.append({"zona": s.zona, "L_acum_m": L, "P_bar": s.P_out / 1e5, "T_ref_C": _c(s.T_out),
                    "x": s.x_out, "h_int": s.h_int, "UA_m": s.UA_m, "T_ar_saida_C": _c(s.T_ar_out),
                    "alpha": s.alpha, "regime": s.regime})
    return out


def _trocador_dict(r) -> dict:
    g = r.geometria
    return {
        "tipo": r.tipo,
        "capacidade_W": r.Q,
        "geometria": {
            "tubo_diametro_externo_mm": g.Do * 1e3, "tubo_diametro_interno_mm": g.Di * 1e3,
            "tubo_espessura_mm": g.esp_parede * 1e3, "aleta_espessura_mm": g.esp_aleta * 1e3,
            "passo_aleta_mm": g.passo_aleta * 1e3, "aletas_por_polegada": 25.4e-3 / g.passo_aleta,
            "passo_transversal_mm": g.Pt * 1e3, "passo_longitudinal_mm": g.Pl * 1e3,
            "n_fileiras": r.n_fileiras, "tubos_por_fileira": r.tubos_por_fileira, "n_tubos": r.n_tubos,
            "n_circuitos": r.n_circuitos, "comprimento_passe_m": r.comprimento_passe,
            "arranjo": "escalonado", "material_tubo": "cobre", "material_aleta": "alumínio",
            "k_aleta_W_mK": g.k_aleta, "rugosidade_interna_um": g.rugosidade_int * 1e6,
        },
        "comprimento_tubo_requerido_m": r.L_requerido,
        "comprimento_tubo_adotado_m": r.L_adotado,
        "comprimento_por_circuito_m": r.L_adotado / r.n_circuitos,
        "zonas": {z: {"comprimento_m": v["L"], "calor_W": v["Q"]} for z, v in r.zonas.items()},
        "area_externa_m2": r.area_externa, "area_interna_m2": r.area_interna,
        "volume_interno_L": r.volume_interno * 1e3,
        "face": {"altura_m": r.altura_face, "largura_m": r.comprimento_passe, "area_m2": r.area_face},
        "n_aletas": r.n_aletas,
        "ar": {"velocidade_face_m_s": r.velocidade_face, "vazao_m3_h": r.vazao_ar_m3h,
               "vazao_requerida_m3_h": r.vazao_ar_requerida_m3h,
               "T_entrada_C": _c(r.T_ar_in), "T_saida_C": _c(r.T_ar_out), "queda_pressao_Pa": r.dP_ar,
               "h_W_m2K": r.ar.h, "eficiencia_superficie": r.ar.eta_superficie, "Re_Dc": r.ar.Re_Dc,
               "j": r.ar.j, "f": r.ar.f, "fator_umidade": r.fator_umidade,
               "potencia_ventilador_aerodinamica_W": r.potencia_ventilador_aero},
        "refrigerante": {"fluxo_massico_kg_m2s": r.G_ref, "P_entrada_bar": r.P_in / 1e5,
                         "P_saida_bar": r.P_out / 1e5, "queda_pressao_kPa": r.dP_ref / 1e3,
                         "queda_T_saturacao_K": r.dT_sat_queda},
        "UA_adotado_W_K": r.UA_adotado,
        "UA_requerido_W_K": r.UA_requerido,
        "eficacia": {"alvo": r.eficacia_alvo, "obtida": r.eficacia, "estrita_Q_Qmax": r.eficacia_Qmax,
                     "NTU": r.NTU, "C_ar_W_K": r.C_ar, "T_sat_referencia_C": _c(r.T_sat_ref),
                     "definicao": "ε = (T_ar,saída − T_ar,entrada)/(T_sat − T_ar,entrada)",
                     "fileiras_automaticas": r.fileiras_escolhidas_automaticamente},
    }


def para_dict(res) -> dict:
    """Dicionário JSON-serializável. O bloco 'amesim' reúne os parâmetros de entrada típicos de
    um modelo de sistema (compressor volumétrico, trocadores tubo-aleta, capilar)."""
    c, b, comp = res.ciclo, res.balanco, res.compressor
    cap = res.capilar.escolhido
    car = res.carga
    ent = res.entradas
    d = {
        "entradas": {"COP": ent.COP, "T_ambiente_C": ent.T_ambiente_C, "T_alvo_C": ent.T_alvo_C,
                     "UR_ambiente": ent.UR_ambiente, "volume_interno_L": res.capacidade.volume_interno_L,
                     "n_garrafas": res.capacidade.n_garrafas, "fluido": ent.fluido,
                     "eficacia_condensador": ent.eficacia_condensador,
                     "eficacia_evaporador": ent.eficacia_evaporador},
        "gabinete": {"largura_int_m": res.capacidade.largura_m, "profundidade_int_m": res.capacidade.profundidade_m,
                     "altura_int_m": res.capacidade.altura_m, "volume_ar_livre_L": res.capacidade.volume_ar_livre_L,
                     "massa_produto_kg": res.capacidade.massa_produto_kg,
                     "UA_gabinete_W_K": car.transmissao["UA_total"]},
        "carga_termica_W": {**car.componentes, "regime": car.Q_regime,
                            "requerida_regime": car.Q_requerida_regime, "pull_down": car.Q_pulldown,
                            "caso_governante": car.caso_governante, "projeto": car.Q_projeto,
                            "latente_projeto": car.Q_latente_projeto, "fator_umidade": car.fator_umidade,
                            "agua_removida_kg_dia": car.infiltracao.get("agua_kg_dia", 0.0)},
        "ciclo": {"T_evap_C": _c(c.T_evap), "T_cond_C": _c(c.T_cond), "P_evap_bar": c.estados["1"].P / 1e5,
                  "P_cond_bar": c.estados["2"].P / 1e5, "razao_pressao": c.razao_pressao,
                  "COP": c.COP, "COP_ciclo_ideal": c.COP_ciclo_ideal, "COP_carnot_ciclo": c.COP_carnot_ciclo,
                  "eta_global": c.eta_global, "eta_isentropica": c.eta_is, "eta_eletromecanica": c.eta_em,
                  "estados": tabela_estados(res)},
        "balanco_W": {"vazao_massica_kg_h": b.m * 3600, "Q_evaporador": b.Q_evap, "W_eletrica_compressor": b.W_el,
                      "Q_condensador": b.Q_cond, "Q_carcaca": b.Q_carcaca, "Q_trocador_interno": b.Q_ihx,
                      "erro_relativo": b.erro_balanco},
        "compressor": {"potencia_eletrica_W": b.W_el, "capacidade_W": b.Q_evap,
                       "capacidade_Btuh": b.Q_evap * W_PARA_BTUH, "deslocamento_cm3": comp.deslocamento_cm3,
                       "rotacao_rpm": comp.rotacao_rpm, "eficiencia_volumetrica": comp.eta_v,
                       "vazao_volumetrica_succao_m3_h": comp.vazao_volumetrica_succao * 3600,
                       "T_descarga_C": _c(comp.T_descarga), "ponto_catalogo": comp.catalogo},
        "condensador": _trocador_dict(res.condensador),
        "evaporador": _trocador_dict(res.evaporador),
        "capilar": {"diametro_interno_mm": cap.D * 1e3, "diametro_interno_pol": cap.D / 25.4e-3,
                    "comprimento_m": cap.L, "comprimento_liquido_m": cap.L_liquido,
                    "rugosidade_um": res.parametros.capilar.rugosidade_m * 1e6, "blocado": cap.blocado,
                    "P_entrada_bar": res.ciclo.estados["3i"].P / 1e5, "P_saida_bar": cap.P_saida / 1e5,
                    "titulo_saida": cap.x_saida, "modelo": f"HEM, viscosidade {res.parametros.capilar.modelo_viscosidade}",
                    "sensibilidade_tolerancia_D": res.capilar.sensibilidade,
                    "alternativas": [{"D_mm": a.D * 1e3, "L_m": a.L, "blocado": a.blocado}
                                     for a in res.capilar.candidatos]},
        "carga_refrigerante": {"total_g": res.carga_refrigerante["total_kg"] * 1e3,
                               "partes_g": {k: v * 1e3 for k, v in res.carga_refrigerante["partes_kg"].items()},
                               "limites_g": {k: v * 1e3 for k, v in res.carga_refrigerante["limites_kg"].items()}},
        "exergia_W": {**res.exergia["destruicao_W"], "util": res.exergia["Ex_util_W"],
                      "eficiencia_2a_lei": res.exergia["eta_II"]},
        "energia": res.energia,
        "sensibilidade_modelos": res.sensibilidade,
        "avisos": [str(a) for a in res.avisos],
    }
    d["amesim"] = _bloco_amesim(res)
    return _limpar(d)


def _bloco_amesim(res) -> dict:
    """Parâmetros em SI, agrupados por componente, prontos para mapear nos submodelos.
    O mapeamento para os nomes de parâmetro de cada submodelo do Amesim fica com a equipe de
    integração; aqui os nomes são descritivos e as unidades explícitas."""
    c, cap = res.ciclo, res.capilar.escolhido

    def hx(r):
        g = r.geometria
        return {"Do_m": g.Do, "Di_m": g.Di, "esp_parede_m": g.esp_parede, "esp_aleta_m": g.esp_aleta,
                "passo_aleta_m": g.passo_aleta, "Pt_m": g.Pt, "Pl_m": g.Pl, "n_fileiras": r.n_fileiras,
                "tubos_por_fileira": r.tubos_por_fileira, "n_circuitos": r.n_circuitos,
                "comprimento_passe_m": r.comprimento_passe, "comprimento_total_tubo_m": r.L_adotado,
                "area_externa_m2": r.area_externa, "area_interna_m2": r.area_interna,
                "volume_interno_m3": r.volume_interno, "vazao_ar_m3_s": r.vazao_ar_m3h / 3600,
                "vazao_ar_requerida_m3_s": r.vazao_ar_requerida_m3h / 3600,
                "T_ar_entrada_K": r.T_ar_in, "velocidade_face_m_s": r.velocidade_face,
                "k_aleta_W_mK": g.k_aleta, "k_tubo_W_mK": g.k_tubo, "rugosidade_m": g.rugosidade_int,
                "eficacia_saturacao": r.eficacia, "eficacia_Q_Qmax": r.eficacia_Qmax, "NTU": r.NTU,
                "UA_W_K": r.UA_adotado}

    return {
        "fluido": c.fluido,
        "compressor": {"deslocamento_m3": res.compressor.deslocamento_cm3 * 1e-6,
                       "rotacao_rpm": res.compressor.rotacao_rpm, "eta_volumetrica": res.compressor.eta_v,
                       "eta_isentropica": c.eta_is, "eta_eletromecanica": c.eta_em,
                       "eta_global": c.eta_global, "potencia_eletrica_W": res.balanco.W_el},
        "condensador": hx(res.condensador),
        "evaporador": hx(res.evaporador),
        "capilar": {"diametro_interno_m": cap.D, "comprimento_m": cap.L,
                    "rugosidade_m": res.parametros.capilar.rugosidade_m},
        "condicoes_iniciais": {"P_alta_Pa": c.estados["2"].P, "P_baixa_Pa": c.estados["1"].P,
                               "carga_refrigerante_kg": res.carga_refrigerante["total_kg"],
                               "superaquecimento_K": res.parametros.ciclo.superaquecimento,
                               "subresfriamento_K": res.parametros.ciclo.subresfriamento},
        "alvo_validacao": {"Q_evap_W": res.balanco.Q_evap, "W_el_W": res.balanco.W_el,
                           "vazao_massica_kg_s": res.balanco.m, "T_evap_K": c.T_evap, "T_cond_K": c.T_cond},
    }


def _limpar(o):
    if is_dataclass(o):
        o = asdict(o)
    if isinstance(o, dict):
        return {str(k): _limpar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpar(v) for v in o]
    if isinstance(o, float):
        return None if not math.isfinite(o) else o
    if hasattr(o, "item"):
        return o.item()
    return o


def exportar_json(res, caminho: str) -> str:
    with open(caminho, "w", encoding="utf-8") as fh:
        json.dump(para_dict(res), fh, ensure_ascii=False, indent=2)
    return caminho


def resumo_texto(res) -> str:
    c, b, comp, car = res.ciclo, res.balanco, res.compressor, res.carga
    cap = res.capilar.escolhido
    ent = res.entradas
    L = []
    w = L.append
    w("=" * 78)
    w("PRÉ-DIMENSIONAMENTO DO CICLO DE REFRIGERAÇÃO")
    w("=" * 78)
    cop_txt = "não informado" if ent.COP is None else f"{ent.COP:.2f}"
    def _e(v):
        return "livre" if v is None else f"{v:.2f}"
    w(f"Entradas: COP {cop_txt} | T_amb {ent.T_ambiente_C:.1f} °C, UR {ent.UR_ambiente:.0%} | "
      f"T_alvo {ent.T_alvo_C:.1f} °C | {ent.fluido} | ε cond {_e(ent.eficacia_condensador)}, "
      f"ε evap {_e(ent.eficacia_evaporador)}")
    k = res.capacidade
    w(f"Gabinete: {k.volume_interno_L:.0f} L internos ({k.largura_m * 1e3:.0f} × {k.profundidade_m * 1e3:.0f} × "
      f"{k.altura_m * 1e3:.0f} mm), {k.n_garrafas} garrafas, {k.massa_produto_kg:.1f} kg de produto")
    w("")
    w("CARGA TÉRMICA [W]")
    for nome, v in car.componentes.items():
        w(f"  {nome:34s} {v:8.1f}")
    w(f"  regime / fator de utilização       {car.Q_requerida_regime:8.1f}")
    w(f"  pull-down (100 % ligado)           {car.Q_pulldown:8.1f}")
    w(f"  >> projeto ({car.caso_governante}, +{res.parametros.uso.margem_seguranca:.0%}): {car.Q_projeto:.1f} W "
      f"({car.Q_projeto * W_PARA_BTUH:.0f} Btu/h), ξ = {car.fator_umidade:.3f}")
    w("")
    w("CICLO")
    w(f"  T_evap {_c(c.T_evap):6.1f} °C ({c.estados['1'].P / 1e5:.3f} bar) | T_cond {_c(c.T_cond):5.1f} °C "
      f"({c.estados['2'].P / 1e5:.2f} bar) | razão de pressão {c.razao_pressao:.2f}")
    w(f"  COP {c.COP:.3f} | ciclo ideal {c.COP_ciclo_ideal:.3f} | Carnot {c.COP_carnot_ciclo:.3f} | "
      f"η_global {c.eta_global:.3f}, η_is {c.eta_is:.3f}, η_em {c.eta_em:.3f}")
    w(f"  {'pt':3s} {'P [bar]':>8s} {'T [°C]':>8s} {'h [kJ/kg]':>10s} {'s [kJ/kgK]':>11s} {'x':>6s}")
    for row in tabela_estados(res):
        x = "" if row["titulo"] is None else f"{row['titulo']:.3f}"
        w(f"  {row['ponto']:3s} {row['P_bar']:8.3f} {row['T_C']:8.2f} {row['h_kJ_kg']:10.2f} "
          f"{row['s_kJ_kgK']:11.4f} {x:>6s}")
    w(f"  Balanço: ṁ = {b.m * 3600:.3f} kg/h | Q_evap {b.Q_evap:.1f} + W_el {b.W_el:.1f} = Q_cond {b.Q_cond:.1f} "
      f"+ Q_carcaça {b.Q_carcaca:.1f} W (erro {b.erro_balanco:.1e})")
    w("")
    w("COMPRESSOR")
    w(f"  potência elétrica {b.W_el:.1f} W | deslocamento {comp.deslocamento_cm3:.2f} cm³ @ {comp.rotacao_rpm:.0f} rpm "
      f"| η_v {comp.eta_v:.3f} | T_descarga {_c(comp.T_descarga):.1f} °C")
    cat = comp.catalogo
    w(f"  no ponto {cat['condicao']} ({cat['T_evap_C']:.1f}/{cat['T_cond_C']:.1f} °C): ≈ {cat['Q_W']:.0f} W "
      f"({cat['Q_Btuh']:.0f} Btu/h), {cat['W_el_W']:.0f} W elétricos, COP {cat['COP']:.2f}")
    for r in (res.condensador, res.evaporador):
        g = r.geometria
        w("")
        w(r.tipo.upper())
        w(f"  {r.Q:.1f} W | tubo Ø{g.Do * 1e3:.2f} × {g.esp_parede * 1e3:.2f} mm (Di {g.Di * 1e3:.2f} mm), "
          f"aleta {g.esp_aleta * 1e3:.2f} mm @ {g.passo_aleta * 1e3:.2f} mm ({25.4e-3 / g.passo_aleta:.1f} FPI)")
        zonas = ", ".join(f"{z} {v['L']:.2f} m" for z, v in r.zonas.items())
        w(f"  comprimento requerido {r.L_requerido:.2f} m ({zonas})")
        w(f"  adotado: {r.n_fileiras} fileiras × {r.tubos_por_fileira} tubos × {r.comprimento_passe:.3f} m = "
          f"{r.L_adotado:.2f} m, {r.n_circuitos} circuito(s)")
        w(f"  face {r.comprimento_passe * 1e3:.0f} × {r.altura_face * 1e3:.0f} mm | A_ext {r.area_externa:.3f} m² | "
          f"A_int {r.area_interna:.4f} m² | V_int {r.volume_interno * 1e6:.0f} cm³")
        alvo = "" if r.eficacia_alvo is None else f" (alvo {r.eficacia_alvo:.2f})"
        auto = ", fileiras escolhidas automaticamente" if r.fileiras_escolhidas_automaticamente else ""
        w(f"  eficácia ε = {r.eficacia:.3f}{alvo}, ε estrita Q/Q_max = {r.eficacia_Qmax:.3f}, NTU = {r.NTU:.3f}, "
          f"UA = {r.UA_requerido:.1f} W/K (adotado {r.UA_adotado:.1f}){auto}")
        w(f"  ar: {r.vazao_ar_requerida_m3h:.0f} m³/h requeridos ({r.vazao_ar_m3h:.0f} m³/h na face adotada) a "
          f"{r.velocidade_face:.2f} m/s, {_c(r.T_ar_in):.1f} → "
          f"{_c(r.T_ar_out):.1f} °C, ΔP {r.dP_ar:.1f} Pa, h_ar {r.ar.h:.1f} W/m²K, η_sup {r.ar.eta_superficie:.3f}")
        w(f"  refrigerante: G {r.G_ref:.1f} kg/m²s, ΔP {r.dP_ref / 1e3:.2f} kPa ({r.dT_sat_queda:.2f} K de saturação)")
    w("")
    w("CAPILAR")
    w(f"  D_int {cap.D * 1e3:.3f} mm ({cap.D / 25.4e-3:.3f}\") × L {cap.L:.2f} m (líquido {cap.L_liquido:.2f} m) | "
      f"{'blocado' if cap.blocado else 'não blocado'}, P_saída {cap.P_saida / 1e5:.3f} bar, x_saída {cap.x_saida:.3f}")
    s = res.capilar.sensibilidade
    w(f"  tolerância ±{res.parametros.capilar.tolerancia_diametro_mm * 1e3:.1f} µm no diâmetro: vazão "
      f"{s['vazao_rel_D_menos_tol']:+.1%} / {s['vazao_rel_D_mais_tol']:+.1%}")
    alts = ", ".join(f"{a.D * 1e3:.3f} mm→{a.L:.2f} m" for a in res.capilar.candidatos if 0.3 <= a.L <= 8)
    w(f"  alternativas: {alts}")
    w("")
    cr = res.carga_refrigerante
    w(f"CARGA DE REFRIGERANTE ≈ {cr['total_kg'] * 1e3:.0f} g  (" +
      ", ".join(f"{k} {v * 1e3:.0f} g" for k, v in cr["partes_kg"].items()) + ")")
    ex = res.exergia
    w(f"EXERGIA: η_II = {ex['eta_II']:.3f}; destruição [W]: " +
      ", ".join(f"{k} {v:.1f}" for k, v in ex["destruicao_W"].items()))
    en = res.energia
    w(f"ENERGIA: compressor ligado {en['fracao_ligado']:.0%} do tempo em regime; ≈ {en['total_kWh_dia']:.2f} kWh/dia; "
      f"COP do sistema (com ventiladores) {en['COP_sistema']:.2f}")
    if res.sensibilidade:
        w("")
        w("INCERTEZA DE MODELO (correlações alternativas)")
        for nome in ("evaporador", "condensador"):
            if nome in res.sensibilidade:
                d = res.sensibilidade[nome]
                w(f"  {nome}: {d['correlacao_base']} {d['L_base']:.2f} m @ {d['V_base']:.2f} m/s vs "
                  f"{d['correlacao_alt']} {d['L_alt']:.2f} m @ {d['V_alt']:.2f} m/s ({d['variacao']:+.1%} no comprimento)")
        if "capilar_viscosidade" in res.sensibilidade:
            w("  capilar (viscosidade): " + ", ".join(f"{k} {v:.2f} m" for k, v in res.sensibilidade["capilar_viscosidade"].items()))
    if len(res.avisos):
        w("")
        w("AVISOS")
        for a in sorted(res.avisos, key=lambda a: {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}[a.nivel]):
            w(f"  {a}")
    return "\n".join(L)
