"""Saídas: resumo legível, dicionário/JSON para o acoplamento com o Simcenter Amesim e tabelas."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass

from .constantes import W_PARA_BTUH
from .propriedades import ar_umido


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


def _serp_dict(sp, r) -> dict:
    return {"descricao": sp.descricao, "comprimento_total_tubo_m": sp.comprimento_tubo,
            "comprimento_por_circuito_m": sp.comprimento_tubo / r.n_circuitos,
            "comprimento_passe_m": sp.comprimento_passe, "tubos_por_fileira": sp.tubos_por_fileira,
            "n_tubos": sp.n_tubos, "face_altura_m": sp.altura_face, "face_largura_m": sp.comprimento_passe,
            "face_area_m2": sp.area_face, "area_externa_m2": sp.area_externa, "area_interna_m2": sp.area_interna,
            "volume_interno_L": sp.volume_interno * 1e3, "n_aletas": sp.n_aletas,
            "vazao_ar_m3_h": sp.vazao_ar_m3h, "UA_W_K": sp.UA, "UA_seco_W_K": sp.UA_seco}


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
            "n_fileiras": r.n_fileiras, "n_circuitos": r.n_circuitos,
            "arranjo": "escalonado", "tipo_aleta": "plana contínua", "material_tubo": "cobre",
            "material_aleta": "alumínio", "k_aleta_W_mK": g.k_aleta, "rugosidade_interna_um": g.rugosidade_int * 1e6,
        },
        "serpentina_projeto": _serp_dict(r.projeto, r),
        "serpentina_construtiva": _serp_dict(r.construtiva, r),
        "zonas": {z: {"comprimento_m": v["L"], "calor_W": v["Q"], "UA_W_K": v["UA"], "UA_seco_W_K": v["UA_seco"],
                      "eficacia_saturacao": v["eficacia"], "NTU": v["NTU"]} for z, v in r.zonas.items()},
        "ar": {"velocidade_face_m_s": r.velocidade_face, "vazao_requerida_m3_h": r.vazao_ar_requerida_m3h,
               "vazao_serpentina_construtiva_m3_h": r.vazao_ar_m3h, "T_entrada_C": _c(r.T_ar_in),
               "T_saida_ponto_projeto_C": _c(r.T_ar_out), "queda_pressao_Pa": r.dP_ar,
               "h_W_m2K": r.ar.h, "eficiencia_superficie": r.ar.eta_superficie, "Re_Dc": r.ar.Re_Dc,
               "j": r.ar.j, "f": r.ar.f, "fator_umidade": r.fator_umidade,
               "potencia_ventilador_aerodinamica_W": r.potencia_ventilador_aero,
               "nota": "T_saida e vazao_requerida valem para a serpentina de projeto; a construtiva, na mesma "
                       "velocidade de face, passa a vazão indicada e tem a mesma eficácia, com mais capacidade."},
        "refrigerante": {"fluxo_massico_kg_m2s": r.G_ref, "P_entrada_bar": r.P_in / 1e5,
                         "P_saida_bar": r.P_out / 1e5, "queda_pressao_kPa": r.dP_ref / 1e3,
                         "queda_T_saturacao_K": r.dT_sat_queda},
        "eficacia": {"alvo": r.eficacia_alvo, "obtida": r.eficacia, "estrita_Q_Qmax": r.eficacia_Qmax,
                     "NTU": r.NTU, "C_ar_sensivel_W_K": r.C_ar, "T_sat_referencia_C": _c(r.T_sat_ref),
                     "definicao": "ε = (T_ar,saída − T_ar,entrada)/(T_sat − T_ar,entrada), bulbo seco; "
                                  "NTU = UA/(ξ·Ċ_ar,sensível)",
                     "fileiras_automaticas": r.fileiras_escolhidas_automaticamente},
    }


def _pulldown_dict(pd) -> dict | None:
    """Resumo e curva do pull-down estimado (°C, h)."""
    if pd is None:
        return None
    pk = pd.pico
    cv = pd.curva()
    return {
        "premissas": {"porta": "fechada", "T_ambiente_C": _c(pd.T_ambiente), "T_produto_inicial_C": _c(pd.T_produto_inicial),
                      "T_alvo_C": _c(pd.T_alvo), "capacidade_termica_produto_kJ_K": pd.C_produto_J_K / 1e3,
                      "hA_ar_produto_W_K": pd.hA_produto_W_K, "UA_gabinete_W_K": pd.UA_gabinete_W_K,
                      "cargas_internas_W": pd.Q_internas_W, "fator_umidade": pd.fator_umidade,
                      "modelo": "casamento compressor–trocadores quase estático (geometria de projeto, ε, η_global e "
                                "superaquecimento constantes); produto concentrado trocando calor com o ar por hA"},
        "concluido": pd.concluido, "tempo_h": pd.tempo_h,
        "T_produto_equilibrio_C": None if pd.T_produto_equilibrio is None else _c(pd.T_produto_equilibrio),
        "potencia_pico_W": pd.W_pico, "pico_na_partida": pd.pico_na_partida, "t_pico_h": pd.t_pico_s / 3600.0,
        "potencia_pico_trajetoria_W": pd.W_pico_trajetoria, "potencia_inicial_W": pd.W_inicial,
        "potencia_final_W": pd.W_final, "energia_compressor_kWh": pd.E_compressor_kWh,
        "T_descarga_max_C": _c(pd.T_descarga_max),
        "ponto_pico": {"T_ar_evaporador_C": _c(pk.T_ar_evap), "T_evap_C": _c(pk.T_evap), "T_cond_C": _c(pk.T_cond),
                       "razao_pressao": pk.razao_pressao, "Q_evap_W": pk.Q_evap, "vazao_massica_kg_h": pk.m * 3600.0,
                       "COP": pk.COP},
        "curva": {"t_h": [t / 3600.0 for t in cv["t_s"]],
                  **{k.replace("_K", "_C"): [_c(T) for T in v] for k, v in cv.items() if k.endswith("_K")},
                  "Q_evap_W": cv["Q_evap_W"], "W_el_W": cv["W_el_W"]},
        "nota": "pico = máximo de W(T_ar) entre o ar no fim do pull-down e o produto inicial: inclui a partida com o "
                "gabinete encharcado (limite superior dos primeiros minutos) e não depende de hA; o tempo depende de hA, "
                "a calibrar com ensaio de pull-down.",
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
                     "eficacia_evaporador": ent.eficacia_evaporador,
                     "potencia_max_compressor_W": ent.potencia_max_compressor_W},
        "gabinete": {"largura_int_m": res.capacidade.largura_m, "profundidade_int_m": res.capacidade.profundidade_m,
                     "altura_int_m": res.capacidade.altura_m, "volume_ar_livre_L": res.capacidade.volume_ar_livre_L,
                     "massa_produto_kg": res.capacidade.massa_produto_kg,
                     "UA_gabinete_W_K": car.transmissao["UA_total"]},
        "carga_termica_W": {**car.componentes, "regime": car.Q_regime,
                            "requerida_regime": car.Q_requerida_regime, "pull_down": car.Q_pulldown,
                            "caso_governante": car.caso_governante, "projeto": car.Q_projeto,
                            "latente_projeto": car.Q_latente_projeto, "fator_umidade": car.fator_umidade,
                            "agua_removida_kg_dia": car.infiltracao.get("agua_kg_dia", 0.0),
                            "umidade_interna": car.infiltracao.get("umidade")},
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
                       "T_descarga_C": _c(comp.T_descarga), "ponto_catalogo": comp.catalogo,
                       "potencia_pico_pulldown_W": None if res.pulldown is None else res.pulldown.W_pico},
        "potencia_compressor": res.potencia,
        "pulldown": _pulldown_dict(res.pulldown),
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
                               "total_serpentinas_projeto_g": res.carga_refrigerante["total_projeto_kg"] * 1e3,
                               "classe_seguranca": res.carga_refrigerante["classe"],
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


def _ar_entrada(res, tipo: str) -> dict:
    """Estado do ar na entrada do trocador (para submodelos de ar úmido)."""
    import CoolProp.CoolProp as CP
    ent, pc = res.entradas, res.parametros.ciclo
    if tipo == "condensador":
        W = ar_umido(ent.T_ambiente_C + 273.15, ent.UR_ambiente)["W"]
        T = ent.T_ambiente_C + 273.15 + pc.dT_recirculacao_cond
    else:
        T = ent.T_alvo_C + 273.15 + pc.dT_retorno_evap
        W = ar_umido(T, res.parametros.uso.UR_interna)["W"]
    UR = CP.HAPropsSI("R", "T", T, "P", 101325.0, "W", W)
    return {"T_K": T, "umidade_relativa": UR, "umidade_absoluta_kg_kg": W, "P_Pa": 101325.0}


def _bloco_amesim(res) -> dict:
    """Parâmetros em SI, agrupados por componente, prontos para mapear nos submodelos.
    O mapeamento para os nomes de parâmetro de cada submodelo do Amesim fica com a equipe de
    integração; aqui os nomes são descritivos e as unidades explícitas.

    Cada trocador traz duas serpentinas com a mesma seção (fileiras, tubos por fileira, aletas):
    ``projeto_sem_margem`` reproduz ``alvo_validacao`` com a vazão de ar requerida; a
    ``construtiva_com_margem`` é a que se fabrica (mais área e, na mesma velocidade de face, mais
    vazão): num modelo de sistema ela leva a T_cond menor e T_evap maior que o alvo — é a folga."""
    c, cap = res.ciclo, res.capilar.escolhido
    pcf = res.parametros.carga_fluido

    def serp(sp, Vdot_m3h):
        return {"comprimento_passe_m": sp.comprimento_passe, "comprimento_total_tubo_m": sp.comprimento_tubo,
                "area_face_m2": sp.area_face, "area_externa_m2": sp.area_externa, "area_interna_m2": sp.area_interna,
                "volume_interno_m3": sp.volume_interno, "vazao_ar_m3_s": Vdot_m3h / 3600.0,
                "UA_W_K": sp.UA, "UA_seco_W_K": sp.UA_seco}

    def hx(r):
        g = r.geometria
        return {"geometria": {"Do_m": g.Do, "Di_m": g.Di, "esp_parede_m": g.esp_parede, "esp_aleta_m": g.esp_aleta,
                              "passo_aleta_m": g.passo_aleta, "Pt_m": g.Pt, "Pl_m": g.Pl,
                              "n_fileiras": r.n_fileiras, "tubos_por_fileira": r.tubos_por_fileira,
                              "n_circuitos": r.n_circuitos, "arranjo": "escalonado", "tipo_aleta": "plana contínua",
                              "k_aleta_W_mK": g.k_aleta, "k_tubo_W_mK": g.k_tubo, "rugosidade_m": g.rugosidade_int},
                "projeto_sem_margem": serp(r.projeto, r.projeto.vazao_ar_m3h),
                "construtiva_com_margem": serp(r.construtiva, r.construtiva.vazao_ar_m3h),
                "margem_area": res.parametros.condensador.margem_area if r.tipo == "condensador"
                else res.parametros.evaporador.margem_area,
                "velocidade_face_m_s": r.velocidade_face, "ar_entrada": _ar_entrada(res, r.tipo),
                "eficacia_saturacao": r.eficacia, "eficacia_Q_Qmax": r.eficacia_Qmax, "NTU": r.NTU,
                "fator_umidade": r.fator_umidade,
                "notas": "eficacia_saturacao é de bulbo seco (sensível); UA_W_K inclui ξ (analogia de Lewis no "
                         "filme de ar e na aleta) e UA_seco_W_K usa ξ = 1 — use o seco se o submodelo calcular a "
                         "condensação de umidade por conta própria; NTU = UA/(ξ·Ċ_ar,sensível)."}

    partes = res.carga_refrigerante["partes_kg"]
    fora = partes.get("gás na carcaça", 0.0) + partes.get("dissolvido no óleo", 0.0)
    circuito = res.carga_refrigerante["total_kg"] - fora
    circuito_proj = res.carga_refrigerante["total_projeto_kg"] - fora
    umid = res.carga.infiltracao.get("umidade") or {}
    return {
        "fluido": c.fluido,
        "compressor": {"deslocamento_m3": res.compressor.deslocamento_cm3 * 1e-6,
                       "rotacao_rpm": res.compressor.rotacao_rpm, "eta_volumetrica": res.compressor.eta_v,
                       "eta_isentropica": c.eta_is, "eta_eletromecanica": c.eta_em,
                       "eta_global": c.eta_global, "potencia_eletrica_W": res.balanco.W_el,
                       "volume_livre_carcaca_m3": pcf.volume_livre_carcaca_L * 1e-3,
                       "massa_oleo_kg": pcf.massa_oleo_kg, "solubilidade_oleo_kg_kg": pcf.solubilidade_oleo},
        "condensador": hx(res.condensador),
        "evaporador": hx(res.evaporador),
        "capilar": {"diametro_interno_m": cap.D, "comprimento_m": cap.L,
                    "rugosidade_m": res.parametros.capilar.rugosidade_m},
        "linhas": {"liquido": {"comprimento_m": pcf.linha_liquido_L_m, "Di_m": pcf.linha_liquido_Di_m},
                   "filtro_secador_volume_m3": pcf.filtro_secador_cm3 * 1e-6,
                   "succao": {"comprimento_m": pcf.linha_succao_L_m, "Di_m": pcf.linha_succao_Di_m},
                   "descarga": {"comprimento_m": pcf.linha_descarga_L_m, "Di_m": pcf.linha_descarga_Di_m}},
        "condicoes_iniciais": {"P_alta_Pa": c.estados["2"].P, "P_baixa_Pa": c.estados["1"].P,
                               "carga_refrigerante_total_kg": res.carga_refrigerante["total_kg"],
                               "carga_circuito_kg": circuito,
                               "carga_refrigerante_total_projeto_kg": res.carga_refrigerante["total_projeto_kg"],
                               "carga_circuito_projeto_kg": circuito_proj,
                               "carga_gas_carcaca_kg": partes.get("gás na carcaça", 0.0),
                               "carga_dissolvida_oleo_kg": partes.get("dissolvido no óleo", 0.0),
                               "superaquecimento_K": res.parametros.ciclo.superaquecimento,
                               "subresfriamento_K": res.parametros.ciclo.subresfriamento,
                               "nota": "carga do circuito = trocadores + capilar + linhas + filtro; '_projeto' usa as "
                                       "serpentinas sem margem (para conferir alvo_validacao num modelo de carga fixa), "
                                       "a outra as construtivas; somar carcaça e óleo se o modelo não os representar."},
        "ar_interno": {"T_K": res.entradas.T_alvo_C + 273.15, "umidade_relativa": res.parametros.uso.UR_interna,
                       "umidade_absoluta_kg_kg": umid.get("W_interno"),
                       "modo": res.parametros.uso.umidade_interna,
                       "T_superficie_efetiva_evaporador_K": umid.get("T_superficie_efetiva_K"),
                       "nota": "no modo 'equilibrio' a umidade interna fecha o balanço água da infiltração = água "
                               "removida pela serpentina (superfície efetiva, Lewis = 1); ξ do evaporador e "
                               "ar_entrada são coerentes com ela. No caso governante de pull-down (portas fechadas) "
                               "o evaporador é dimensionado seco (ξ = 1)."},
        "restricoes": {"potencia_max_compressor_W": res.entradas.potencia_max_compressor_W,
                       "criterio": (res.potencia or {}).get("criterio"),
                       "atendida": (res.potencia or {}).get("atende"),
                       "nota": "criterio 'regime' = potência no ponto de projeto; 'pico_pulldown' = maior potência no "
                               "pull-down de portas fechadas, incluindo a partida."},
        "pulldown_estimado": None if res.pulldown is None else {
            "T_ambiente_K": res.pulldown.T_ambiente, "T_produto_inicial_K": res.pulldown.T_produto_inicial,
            "T_alvo_K": res.pulldown.T_alvo, "capacidade_termica_produto_J_K": res.pulldown.C_produto_J_K,
            "hA_ar_produto_W_K": res.pulldown.hA_produto_W_K, "cargas_internas_W": res.pulldown.Q_internas_W,
            "tempo_ate_T_alvo_s": res.pulldown.tempo_s if res.pulldown.concluido else None,
            "potencia_pico_W": res.pulldown.W_pico, "potencia_inicial_W": res.pulldown.W_inicial,
            "potencia_final_W": res.pulldown.W_final, "energia_compressor_J": res.pulldown.E_compressor_J,
            "nota": "estimativa quase estática para comparar com o ensaio de pull-down no Amesim (não é alvo exato): "
                    "massa do gabinete desprezada, superaquecimento fixo e hA ar–produto premissa."},
        "alvo_validacao": {"Q_evap_W": res.balanco.Q_evap, "W_el_W": res.balanco.W_el,
                           "vazao_massica_kg_s": res.balanco.m, "T_evap_K": c.T_evap, "T_cond_K": c.T_cond,
                           "nota": "reproduzido com as serpentinas 'projeto_sem_margem', a vazão de ar requerida e "
                                   "a carga 'carga_*_projeto_kg'; com as 'construtiva_com_margem', T_cond fica menor "
                                   "e T_evap maior (folga)."},
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
    um = car.infiltracao.get("umidade")
    if um:
        w(f"  umidade interna ({res.parametros.uso.umidade_interna}): UR {res.parametros.uso.UR_interna:.0%} a "
          f"{ent.T_alvo_C:.1f} °C (W = {um['W_interno'] * 1e3:.2f} g/kg); superfície efetiva do evaporador "
          f"{_c(um['T_superficie_efetiva_K']):.1f} °C; água removida {car.infiltracao.get('agua_kg_dia', 0.0) * 1e3:.0f} g/dia")
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
    pot = res.potencia or {}
    if pot.get("limite_W"):
        estado = ("ATIVO: capacidade de projeto " f"{pot['Q_requisitos_W']:.0f} → {pot['Q_projeto_W']:.0f} W"
                  if pot["limitado"] else "inativo")
        atende = {True: "atende", False: "NÃO ATENDE", None: "não verificado"}[pot["atende"]]
        pico = "" if pot.get("W_pico_pulldown_W") is None else f", pico no pull-down {pot['W_pico_pulldown_W']:.0f} W"
        w(f"  limite de potência {pot['limite_W']:.0f} W ({pot['criterio']}, {pot['modo']}): {atende}, {estado} | "
          f"regime {pot['W_regime_W']:.1f} W{pico}")
    pd = res.pulldown
    if pd is not None:
        w("")
        w(f"PULL-DOWN ESTIMADO (porta fechada; produto {_c(pd.T_produto_inicial):.1f} → {_c(pd.T_alvo):.1f} °C; ambiente "
          f"{_c(pd.T_ambiente):.1f} °C; C {pd.C_produto_J_K / 1e3:.0f} kJ/K; hA ar–produto {pd.hA_produto_W_K:.0f} W/K)")
        fim = (f"{pd.tempo_h:.1f} h até {_c(pd.T_alvo):.1f} °C" if pd.concluido else
               f"NÃO atinge {_c(pd.T_alvo):.1f} °C (equilíbrio ≈ {_c(pd.T_produto_equilibrio):.1f} °C)")
        quando = "na partida" if pd.pico_na_partida else f"em t ≈ {pd.t_pico_s / 3600.0:.1f} h"
        w(f"  {fim} | compressor {pd.W_inicial:.0f} W (início) → {pd.W_final:.0f} W (fim); pico {pd.W_pico:.0f} W {quando} "
          f"({pd.W_pico / res.balanco.W_el:.2f}× o de regime; T_evap {_c(pd.pico.T_evap):.1f} °C, T_cond "
          f"{_c(pd.pico.T_cond):.1f} °C) | {pd.E_compressor_kWh:.2f} kWh | T_descarga máx {_c(pd.T_descarga_max):.0f} °C")
    for r in (res.condensador, res.evaporador):
        g = r.geometria
        w("")
        w(r.tipo.upper())
        w(f"  {r.Q:.1f} W | tubo Ø{g.Do * 1e3:.2f} × {g.esp_parede * 1e3:.2f} mm (Di {g.Di * 1e3:.2f} mm), "
          f"aleta {g.esp_aleta * 1e3:.2f} mm @ {g.passo_aleta * 1e3:.2f} mm ({25.4e-3 / g.passo_aleta:.1f} FPI)")
        zonas = ", ".join(f"{z} {v['L']:.2f} m" for z, v in r.zonas.items())
        pj, ct = r.projeto, r.construtiva
        w(f"  serpentina de projeto (sem margem): {pj.comprimento_tubo:.2f} m de tubo ({zonas})")
        w(f"  serpentina construtiva (+{(ct.comprimento_tubo / pj.comprimento_tubo - 1):.0%}): {r.n_fileiras} fileiras × "
          f"{ct.tubos_por_fileira} tubos × {ct.comprimento_passe:.3f} m = {ct.comprimento_tubo:.2f} m, "
          f"{r.n_circuitos} circuito(s)")
        w(f"  face {ct.comprimento_passe * 1e3:.0f} × {ct.altura_face * 1e3:.0f} mm | A_ext {ct.area_externa:.3f} m² | "
          f"A_int {ct.area_interna:.4f} m² | V_int {ct.volume_interno * 1e6:.0f} cm³")
        alvo = "" if r.eficacia_alvo is None else f" (alvo {r.eficacia_alvo:.2f})"
        auto = ", fileiras escolhidas automaticamente" if r.fileiras_escolhidas_automaticamente else ""
        seco = f", seco {pj.UA_seco:.1f}" if r.fator_umidade > 1.0 else ""
        w(f"  eficácia ε = {r.eficacia:.3f}{alvo}, ε estrita Q/Q_max = {r.eficacia_Qmax:.3f}, NTU = {r.NTU:.3f}, "
          f"UA projeto {pj.UA:.1f} W/K{seco} (construtiva {ct.UA:.1f}){auto}")
        w(f"  ar no ponto de projeto: {pj.vazao_ar_m3h:.0f} m³/h, {_c(r.T_ar_in):.1f} → {_c(r.T_ar_out):.1f} °C | "
          f"face a {r.velocidade_face:.2f} m/s (construtiva passa {ct.vazao_ar_m3h:.0f} m³/h), ΔP {r.dP_ar:.1f} Pa, "
          f"h_ar {r.ar.h:.1f} W/m²K, η_sup {r.ar.eta_superficie:.3f}")
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
    w(f"CARGA DE REFRIGERANTE ≈ {cr['total_kg'] * 1e3:.0f} g ({cr['classe']}; com as serpentinas de projeto "
      f"{cr['total_projeto_kg'] * 1e3:.0f} g)  (" +
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
            if nome in res.sensibilidade and "erro" in res.sensibilidade[nome]:
                w(f"  {nome}: correlação alternativa sem solução ({res.sensibilidade[nome]['erro'][:120]})")
            elif nome in res.sensibilidade:
                d = res.sensibilidade[nome]
                w(f"  {nome}: {d['correlacao_base']} {d['L_base']:.2f} m @ {d['V_base']:.2f} m/s vs "
                  f"{d['correlacao_alt']} {d['L_alt']:.2f} m @ {d['V_alt']:.2f} m/s ({d['variacao']:+.1%} no comprimento)")
        if "capilar_viscosidade" in res.sensibilidade and "erro" not in res.sensibilidade["capilar_viscosidade"]:
            w("  capilar (viscosidade): " + ", ".join(f"{k} {v:.2f} m" for k, v in res.sensibilidade["capilar_viscosidade"].items()))
    if len(res.avisos):
        w("")
        w("AVISOS")
        for a in sorted(res.avisos, key=lambda a: {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}[a.nivel]):
            w(f"  {a}")
    return "\n".join(L)
