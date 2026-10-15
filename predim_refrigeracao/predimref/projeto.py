"""Orquestração do pré-dimensionamento completo (entradas do cliente -> parâmetros para o Amesim)."""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Optional

from .avisos import Avisos, ErroProjeto
from .capilar import ParametrosCapilar, SelecaoCapilar, dimensionar_capilar
from .carga_fluido import ParametrosCargaFluido, estimar_carga
from .ciclo import (BalancoSistema, Ciclo, ParametrosCiclo, balanco, escala_dT_para_cop, exergia,
                    resolver_ciclo)
from .compressor import ParametrosCompressor, ResultadoCompressor, dimensionar_compressor
from .constantes import C_para_K
from .gabinete import (Capacidade, CargaTermica, Gabinete, Garrafa, Uso, calcular_carga,
                       resolver_capacidade)
from .propriedades import Fluido, ar_seco
from .trocador import (ParametrosTrocador, ResultadoTrocador, condensador_padrao,
                       dimensionar_condensador, dimensionar_evaporador, evaporador_padrao)


@dataclass
class EntradasProjeto:
    """As quatro entradas do cliente (+ umidade e fluido).

    COP: capacidade frigorífica do evaporador / potência elétrica do compressor [W/W],
         na condição de projeto. ``None`` usa ``ParametrosCiclo.eta_global_sem_cop``.
    volume_interno_L ou n_garrafas: capacidade do refrigerador (garrafas de 600 mL por padrão).
    eficacia_condensador / eficacia_evaporador: ε do lado do ar referida à saturação,
         ε = (T_ar,saída − T_ar,entrada)/(T_sat − T_ar,entrada). Define a vazão de ar e, com ela, a
         geometria (fileiras, velocidade de face, comprimento). ``None`` usa a velocidade de face fixa
         de ``ParametrosTrocador`` e a eficácia vira resultado.
    """
    COP: Optional[float]
    T_ambiente_C: float
    T_alvo_C: float
    volume_interno_L: Optional[float] = None
    n_garrafas: Optional[int] = None
    UR_ambiente: float = 0.60
    fluido: str = "R290"
    eficacia_condensador: Optional[float] = 0.65
    eficacia_evaporador: Optional[float] = 0.65


@dataclass
class ParametrosProjeto:
    garrafa: Garrafa = field(default_factory=Garrafa)
    gabinete: Gabinete = field(default_factory=Gabinete)
    uso: Uso = field(default_factory=Uso)
    ciclo: ParametrosCiclo = field(default_factory=ParametrosCiclo)
    compressor: ParametrosCompressor = field(default_factory=ParametrosCompressor)
    condensador: ParametrosTrocador = field(default_factory=condensador_padrao)
    evaporador: ParametrosTrocador = field(default_factory=evaporador_padrao)
    capilar: ParametrosCapilar = field(default_factory=ParametrosCapilar)
    carga_fluido: ParametrosCargaFluido = field(default_factory=ParametrosCargaFluido)
    potencia_ventilador_cond_W: Optional[float] = None  # None -> estimada pela ΔP do ar e η do ventilador
    analise_sensibilidade: bool = True
    max_iter: int = 10


@dataclass
class ResultadoProjeto:
    entradas: EntradasProjeto
    parametros: ParametrosProjeto
    capacidade: Capacidade
    carga: CargaTermica
    ciclo: Ciclo
    balanco: BalancoSistema
    compressor: ResultadoCompressor
    condensador: ResultadoTrocador
    evaporador: ResultadoTrocador
    capilar: SelecaoCapilar
    carga_refrigerante: dict
    exergia: dict
    energia: dict
    sensibilidade: dict
    avisos: Avisos
    iteracoes: int

    def resumo(self) -> str:
        from .relatorio import resumo_texto
        return resumo_texto(self)

    def para_dict(self) -> dict:
        from .relatorio import para_dict
        return para_dict(self)

    def exportar_json(self, caminho: str) -> str:
        from .relatorio import exportar_json
        return exportar_json(self, caminho)


def dimensionar(entradas: EntradasProjeto, parametros: Optional[ParametrosProjeto] = None) -> ResultadoProjeto:
    """Pré-dimensiona o sistema completo. Lança ``ErroProjeto`` para entradas impossíveis (e também,
    com a causa original encadeada, para falhas numéricas não previstas)."""
    try:
        return _dimensionar(entradas, parametros)
    except ErroProjeto:
        raise
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as err:
        raise ErroProjeto(f"falha numérica não prevista ({type(err).__name__}: {err}); revise as entradas "
                          "(e reporte o caso se elas forem razoáveis)") from err


def _acoplar(fl, entradas, p, carga, T_evap, T_cond, T_ar_evap, T_ar_cond, dicas):
    """Ciclo <-> trocadores: as quedas de pressão realimentam o ciclo até convergir."""
    pc = p.ciclo
    dPc = dPe = 0.0
    dica_c, dica_e = dicas
    it, conv = 0, False
    for it in range(1, p.max_iter + 1):
        av_ciclo = Avisos()
        try:
            ciclo = resolver_ciclo(fl, T_evap, T_cond, pc, entradas.COP, dPc, dPe, av_ciclo)
        except ErroProjeto as err:
            raise ErroProjeto(str(err) + _sugestao_cop(fl, entradas, T_ar_evap, T_ar_cond, pc)) from None
        bal = balanco(ciclo, carga.Q_projeto, av_ciclo)
        e = ciclo.estados
        cond = dimensionar_condensador(fl, bal.m, e["2"].P, e["2"].h, pc.subresfriamento, T_ar_cond, p.condensador,
                                       dica_c)
        evap = dimensionar_evaporador(fl, bal.m, e["3i"].h, e["1"].P, pc.superaquecimento, T_ar_evap,
                                      p.evaporador, carga.fator_umidade, dica_e)
        # o nº de circuitos escolhido (automático por perda de carga) passa a valer nas iterações seguintes
        p.condensador.n_circuitos, p.evaporador.n_circuitos = cond.n_circuitos, evap.n_circuitos
        dica_c = (cond.n_fileiras, cond.velocidade_face)
        dica_e = (evap.n_fileiras, evap.velocidade_face)
        conv = abs(cond.dP_ref - dPc) < 20.0 and abs(evap.dP_ref - dPe) < 20.0
        dPc, dPe = cond.dP_ref, evap.dP_ref
        if conv:
            break
    return ciclo, bal, cond, evap, av_ciclo, it, conv, (dica_c, dica_e)


def umidade_equilibrio(entradas: EntradasProjeto, p: ParametrosProjeto, carga: CargaTermica, bal: BalancoSistema,
                       evap: ResultadoTrocador) -> dict:
    """Umidade interna de regime: a água que entra por infiltração é removida pela serpentina.

    Serpentina úmida pelo modelo de superfície efetiva com Lewis = 1 (Braun, Klein & Mitchell 1989,
    ASHRAE Trans. 95(2); ASHRAE Handbook—Fundamentals, cap. "Psychrometrics"/"Air-cooling coils"):
        T_s,ef = T_e − (T_e − T_s)/(1 − e^(−NTU_o)),  NTU_o = h_o η_o A_o / (ṁ_ar c_p)
        ṁ_água,serp = ṁ_ar (1 − e^(−NTU_o)) (W_i − W_sat(T_s,ef))
    Em média diária, com o compressor ligado a fração f = Q_regime/Q_evap:
        A (W_e − W_i) = f ṁ_ar (1 − e^(−NTU_o)) (W_i − W_s)  →  W_i = (A W_e + B W_s)/(A + B)
    com A = aberturas/dia × m_ar,abertura / 86400 [kg_as/s] e B = f ṁ_ar (1 − e^(−NTU_o))."""
    import CoolProp.CoolProp as CP
    from .propriedades import ar_umido
    T_int = C_para_K(entradas.T_alvo_C)
    W_e = ar_umido(C_para_K(entradas.T_ambiente_C), entradas.UR_ambiente)["W"]
    cp = ar_seco(evap.T_ar_in).cp
    m_ar = evap.C_ar / cp
    NTU_o = evap.ar.h * evap.ar.eta_superficie * evap.projeto.area_externa / (m_ar * cp)
    eps_o = 1.0 - math.exp(-NTU_o)
    T_s = evap.T_ar_in - (evap.T_ar_in - evap.T_ar_out) / eps_o
    W_s = CP.HAPropsSI("W", "T", T_s, "P", 101325.0, "R", 1.0)
    f_on = min(carga.Q_regime / bal.Q_evap, 1.0)
    A = p.uso.aberturas_por_dia * carga.infiltracao.get("m_ar_abertura", 0.0) / 86400.0
    B = f_on * m_ar * eps_o
    W_i = (A * W_e + B * W_s) / (A + B) if A + B > 0 else W_s
    UR = min(CP.HAPropsSI("R", "T", T_int, "P", 101325.0, "W", W_i), 1.0)
    return {"W_interno": W_i, "UR_interna": UR, "T_superficie_efetiva_K": T_s, "W_superficie": W_s,
            "NTU_ar": NTU_o, "fracao_ligado": f_on}


def _dimensionar(entradas: EntradasProjeto, parametros: Optional[ParametrosProjeto]) -> ResultadoProjeto:
    p = copy.deepcopy(parametros) if parametros is not None else ParametrosProjeto()
    av = Avisos()
    fl = Fluido(entradas.fluido)
    if entradas.COP is not None and entradas.COP <= 0:
        raise ErroProjeto("COP deve ser positivo.")

    # 1) capacidade --------------------------------------------------------------------------
    cap = resolver_capacidade(entradas.volume_interno_L, entradas.n_garrafas, p.garrafa, p.gabinete, av)

    # 2) temperaturas de projeto -------------------------------------------------------------
    pc = p.ciclo
    T_ar_evap = C_para_K(entradas.T_alvo_C) + pc.dT_retorno_evap
    T_ar_cond = C_para_K(entradas.T_ambiente_C) + pc.dT_recirculacao_cond
    T_evap, T_cond = T_ar_evap - pc.dT_evap, T_ar_cond + pc.dT_cond
    if pc.superaquecimento >= pc.dT_evap:
        raise ErroProjeto("superaquecimento ≥ ΔT do evaporador: o ar não consegue superaquecer o vapor.")
    if pc.subresfriamento >= pc.dT_cond:
        raise ErroProjeto("sub-resfriamento ≥ ΔT do condensador: o ar não consegue sub-resfriar o líquido.")
    p.condensador.eficacia = entradas.eficacia_condensador
    p.evaporador.eficacia = entradas.eficacia_evaporador

    # 3) carga térmica <-> ciclo <-> trocadores, fechando o balanço de umidade do gabinete -----------
    equilibrio = p.uso.umidade_interna == "equilibrio"
    nc0 = {"condensador": p.condensador.n_circuitos, "evaporador": p.evaporador.n_circuitos}
    dicas = (None, None)
    umid = None
    for it_u in range(1, 5 if equilibrio else 2):
        av_carga = Avisos()
        carga = calcular_carga(cap, p.gabinete, p.uso, p.garrafa, entradas.T_ambiente_C, entradas.UR_ambiente,
                               entradas.T_alvo_C, av_carga)
        ciclo, bal, cond, evap, av_ciclo, it, conv, dicas = _acoplar(fl, entradas, p, carga, T_evap, T_cond,
                                                                     T_ar_evap, T_ar_cond, dicas)
        umid = umidade_equilibrio(entradas, p, carga, bal, evap)
        if not equilibrio:
            break
        UR_ant = p.uso.UR_interna
        p.uso.UR_interna = umid["UR_interna"]
        if abs(umid["UR_interna"] - UR_ant) < 0.003:
            break
    else:
        av.atencao("umidade", "o balanço de umidade do gabinete não convergiu em 4 passos")
    av.itens.extend(av_carga.itens)
    carga.infiltracao["umidade"] = umid
    for r in (cond, evap):
        r.avisos = [a for a in r.avisos if not a.startswith("n_circuitos aumentado")]
        if r.n_circuitos != nc0[r.tipo]:
            r.avisos.append(f"n_circuitos aumentado de {nc0[r.tipo]} para {r.n_circuitos}: com {nc0[r.tipo]} a perda de "
                            f"carga do refrigerante impedia o projeto do {r.tipo} (pinch ou ε inatingível)")
    if not equilibrio and abs(umid["UR_interna"] - p.uso.UR_interna) > 0.05:
        av.atencao("umidade", f"UR interna fixa de {p.uso.UR_interna:.0%} incompatível com a serpentina: o equilíbrio "
                   f"entre infiltração e remoção daria {umid['UR_interna']:.0%} (o ξ do evaporador e a umidade "
                   "exportada ao Amesim ficam incoerentes).")
    if not conv:
        av.atencao("iteração", "acoplamento ciclo-trocadores não convergiu dentro de max_iter")
    av.itens.extend(av_ciclo.itens)
    if entradas.COP is not None and ciclo.eta_global > pc.eta_global_faixa[1]:
        av.info("compressor", _sugestao_cop(fl, entradas, T_ar_evap, T_ar_cond, pc).strip())
    if 0.85 < ciclo.eta_is < 1.0:
        av.atencao("compressor", f"η_is implícita = {ciclo.eta_is:.2f} (> 0,85): reveja η_eletromecânica "
                   f"({pc.eta_eletromecanica:.2f}) ou o COP; a temperatura de descarga fica subestimada.")

    # 4) compressor ------------------------------------------------------------------------
    e = ciclo.estados
    comp = dimensionar_compressor(fl, bal.m, e["1s"], e["2"].P, bal.W_el, e["2"].T, ciclo.eta_global, p.compressor)

    # 5) capilar (entrada após o IHX, saída na pressão de entrada do evaporador) ----------------
    cap_sel = dimensionar_capilar(fl, bal.m, e["3i"].P, e["3i"].h, e["4"].P, p.capilar)
    av.extend("capilar", cap_sel.avisos, "INFO")
    if pc.eficacia_ihx > 0:
        av.info("capilar", "com trocador interno o capilar real é não adiabático (soldado à sucção); o "
                "comprimento adiabático calculado é uma estimativa a ser ajustada em protótipo.")

    # 6) carga de refrigerante, exergia, energia -------------------------------------------------
    carga_ref = estimar_carga(fl, ciclo, cond, evap, cap_sel.escolhido, p.carga_fluido)
    if carga_ref["limites_kg"]:
        lim = carga_ref["limites_kg"]
        if carga_ref["total_kg"] > min(lim.values()):
            av.atencao("carga de fluido", f"carga estimada {carga_ref['total_kg'] * 1e3:.0f} g de {fl.nome} "
                       f"(classe {carga_ref['classe']}) acima de {min(lim.values()) * 1e3:.0f} g; verificar a norma "
                       "aplicável ao produto (IEC 60335-2-89 vigente e regulamentação local).")
    T0, Tf = C_para_K(entradas.T_ambiente_C), C_para_K(entradas.T_alvo_C)
    ex = exergia(ciclo, bal, T0, Tf)
    if p.potencia_ventilador_cond_W is None:
        p.potencia_ventilador_cond_W = max(cond.potencia_ventilador_est, 3.0)
        av.info("condensador", f"potência do ventilador estimada em {p.potencia_ventilador_cond_W:.1f} W "
                f"({cond.vazao_ar_m3h:.0f} m³/h, {cond.dP_ar:.0f} Pa, η = {p.condensador.eficiencia_ventilador:.2f}).")
        p_cond_informada = False
    else:
        p_cond_informada = True
    energia = _energia_diaria(carga, bal, p, cond, evap)

    # 7) verificações finais ------------------------------------------------------------------
    for r in (cond, evap):
        av.extend(r.tipo, r.avisos)
        if r.tipo == "condensador" and not p_cond_informada:
            continue
        P_vent = p.potencia_ventilador_cond_W if r.tipo == "condensador" else p.uso.potencia_ventilador_evap_W
        if r.potencia_ventilador_est > P_vent:
            av.atencao(r.tipo, f"potência estimada do ventilador ({r.potencia_ventilador_est:.1f} W para "
                       f"{r.vazao_ar_m3h:.0f} m³/h a {r.dP_ar:.0f} Pa) maior que a informada ({P_vent:.1f} W).")
    if evap.T_ar_out - 273.15 < -1.5:
        av.info("evaporador", f"ar insuflado a {evap.T_ar_out - 273.15:.1f} °C com o compressor ligado (comum em "
                "visi-coolers); verificar na distribuição de ar o risco de congelar bebidas junto à descarga "
                "(ponto de congelamento ≈ −1 a −2 °C).")
    for r in (cond, evap):
        if r.eficacia_alvo is not None and r.fileiras_escolhidas_automaticamente:
            av.info(r.tipo, f"ε = {r.eficacia_alvo:.2f} atendida com {r.n_fileiras} fileira(s) a "
                    f"{r.velocidade_face:.2f} m/s (escolha automática; ver alternativas_fileiras).")
    v_suc = bal.m / (e["1"].rho * evap.geometria.Di ** 2 * math.pi / 4.0 * evap.n_circuitos)
    if v_suc < 3.8:
        av.info("evaporador", f"velocidade do vapor na saída do evaporador {v_suc:.1f} m/s (< 3,8 m/s, regra "
                "prática ASHRAE para arraste de óleo em linhas horizontais); com HC + óleo miscível em "
                "sistemas pequenos isso costuma ser aceitável, mas avalie no protótipo.")

    sens = (_sensibilidade(fl, bal, ciclo, carga, p, T_ar_cond, T_ar_evap, cond, evap, cap_sel.escolhido.D)
            if p.analise_sensibilidade else {})
    return ResultadoProjeto(entradas, p, cap, carga, ciclo, bal, comp, cond, evap, cap_sel, carga_ref, ex,
                            energia, sens, av, it)


def _sugestao_cop(fl, entradas, T_ar_evap, T_ar_cond, pc: ParametrosCiclo) -> str:
    if entradas.COP is None:
        return ""
    eta_ref = 0.55
    s = escala_dT_para_cop(fl, entradas.COP, T_ar_evap, T_ar_cond, pc, eta_ref)
    if s is None:
        return (f" Mesmo com trocadores muito grandes, um compressor com η_global = {eta_ref:.2f} não chega a "
                f"COP {entradas.COP:.2f} nestas temperaturas.")
    return (f" Para COP {entradas.COP:.2f} com um compressor típico (η_global = {eta_ref:.2f}) seriam "
            f"necessários ΔT_evap ≈ {s * pc.dT_evap:.1f} K e ΔT_cond ≈ {s * pc.dT_cond:.1f} K "
            f"(hoje {pc.dT_evap:.1f} K e {pc.dT_cond:.1f} K).")


def _energia_diaria(carga: CargaTermica, bal: BalancoSistema, p: ParametrosProjeto, cond, evap) -> dict:
    """Consumo diário estimado no regime de uso (compressor cicla na capacidade de projeto)."""
    fr = min(carga.Q_regime / bal.Q_evap, 1.0)
    u = p.uso
    kwh = {"compressor": bal.W_el * fr * 24e-3,
           "ventilador do condensador": p.potencia_ventilador_cond_W * fr * 24e-3,
           "ventilador do evaporador": u.potencia_ventilador_evap_W * 24e-3,
           "iluminação": u.potencia_iluminacao_W * 24e-3,
           "anti-embaçante": u.potencia_antiembacante_W * 24e-3}
    cop_sist = bal.Q_evap / (bal.W_el + p.potencia_ventilador_cond_W + u.potencia_ventilador_evap_W)
    return {"fracao_ligado": fr, "kWh_dia": kwh, "total_kWh_dia": sum(kwh.values()),
            "COP_sistema": cop_sist}


def _sensibilidade(fl, bal, ciclo, carga, p: ParametrosProjeto, T_ar_cond, T_ar_evap, cond, evap,
                   D_cap: float) -> dict:
    """Incerteza de modelo: mesmo problema com correlações alternativas."""
    e = ciclo.estados
    out = {}
    try:
        pe = copy.deepcopy(p.evaporador)
        pe.correlacao_bifasico = ("liu_winterton_1991" if pe.correlacao_bifasico == "gungor_winterton_1987"
                                  else "gungor_winterton_1987")
        pe.fileiras_automaticas = False
        pe.geometria.n_fileiras = evap.n_fileiras
        r = dimensionar_evaporador(fl, bal.m, e["3i"].h, e["1"].P, p.ciclo.superaquecimento, T_ar_evap, pe,
                                   carga.fator_umidade, (evap.n_fileiras, evap.velocidade_face))
        out["evaporador"] = {"correlacao_base": p.evaporador.correlacao_bifasico, "L_base": evap.L_requerido,
                             "correlacao_alt": pe.correlacao_bifasico, "L_alt": r.L_requerido,
                             "variacao": r.L_requerido / evap.L_requerido - 1.0,
                             "V_base": evap.velocidade_face, "V_alt": r.velocidade_face}
    except (ErroProjeto, ValueError, TypeError, ZeroDivisionError) as err:   # análise secundária
        out["evaporador"] = {"erro": str(err)}
    try:
        pq = copy.deepcopy(p.condensador)
        Re_GT = cond.G_ref * cond.geometria.Di / fl.sat(e["2"].P).muv
        pq.correlacao_bifasico = "chato_1962" if Re_GT < 35000 else "shah_1979"
        pq.fileiras_automaticas = False
        pq.geometria.n_fileiras = cond.n_fileiras
        r = dimensionar_condensador(fl, bal.m, e["2"].P, e["2"].h, p.ciclo.subresfriamento, T_ar_cond, pq,
                                    (cond.n_fileiras, cond.velocidade_face))
        out["condensador"] = {"correlacao_base": p.condensador.correlacao_bifasico, "L_base": cond.L_requerido,
                              "correlacao_alt": pq.correlacao_bifasico, "L_alt": r.L_requerido,
                              "variacao": r.L_requerido / cond.L_requerido - 1.0,
                              "V_base": cond.velocidade_face, "V_alt": r.velocidade_face}
    except (ErroProjeto, ValueError, TypeError, ZeroDivisionError) as err:   # análise secundária
        out["condensador"] = {"erro": str(err)}
    try:
        from .capilar import comprimento_capilar
        Ls = {}
        for mod in ("mcadams", "cicchitti", "dukler"):
            pcap = copy.deepcopy(p.capilar)
            pcap.modelo_viscosidade = mod
            Ls[mod] = comprimento_capilar(fl, bal.m, D_cap, e["3i"].P, e["3i"].h, e["4"].P, pcap).L
        out["capilar_viscosidade"] = Ls
    except (ErroProjeto, ValueError, TypeError, ZeroDivisionError) as err:   # análise secundária
        out["capilar_viscosidade"] = {"erro": str(err)}
    return out



def alternativas_fileiras(res: ResultadoProjeto, tipo: str, fileiras=range(1, 9)) -> list[dict]:
    """Tabela de alternativas do condensador ou do evaporador para a eficácia pedida: para cada nº de
    fileiras, a velocidade de face que atende ε, o comprimento de tubo, a vazão de ar e a ΔP do ar.
    Acima de 6 fileiras a correlação de Wang (2000) é extrapolada."""
    from .trocador import _condensador_fixo, _evaporador_fixo, alternativas_fileiras as _alt
    fl = Fluido(res.entradas.fluido)
    p, e, m = res.parametros, res.ciclo.estados, res.balanco.m
    pc = p.ciclo
    if tipo == "condensador":
        pt = copy.deepcopy(p.condensador)
        T_ar = C_para_K(res.entradas.T_ambiente_C) + pc.dT_recirculacao_cond
        rodar = (lambda pp: _condensador_fixo(fl, m, e["2"].P, e["2"].h, pc.subresfriamento, T_ar, pp))
    elif tipo == "evaporador":
        pt = copy.deepcopy(p.evaporador)
        T_ar = C_para_K(res.entradas.T_alvo_C) + pc.dT_retorno_evap
        rodar = (lambda pp: _evaporador_fixo(fl, m, e["3i"].h, e["1"].P, pc.superaquecimento, T_ar, pp,
                                             res.carga.fator_umidade))
    else:
        raise ValueError("tipo deve ser 'condensador' ou 'evaporador'")
    if pt.eficacia is None:
        raise ValueError("as alternativas por fileiras exigem a eficácia definida")
    return _alt(rodar, pt, fileiras)
