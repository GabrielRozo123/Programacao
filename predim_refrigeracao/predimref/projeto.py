"""Orquestração do pré-dimensionamento completo (entradas do cliente -> parâmetros para o Amesim)."""
from __future__ import annotations

import copy
import dataclasses
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
from .operacao import (ModeloSistema, ParametrosOperacao, ResultadoPulldown, simular_pulldown,
                       temperatura_inicial_produto)
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
    potencia_max_compressor_W: limite de potência elétrica do compressor (requisito de ensaio). O critério
         (regime ou pico de pull-down) e o modo (limitar ou só verificar) estão em ``RestricaoPotencia``.
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
    potencia_max_compressor_W: Optional[float] = None


@dataclass
class RestricaoPotencia:
    """Como aplicar ``EntradasProjeto.potencia_max_compressor_W``.

    criterio: "regime"        -> potência no ponto de projeto (gabinete na T_alvo, compressor ligado);
              "pico_pulldown" -> maior potência estimada no pull-down de portas fechadas, incluindo a
                                 partida com o gabinete encharcado (``operacao.simular_pulldown``).
    modo:     "limitar"   -> se o limite for violado, reduz a capacidade de projeto (compressor menor) até
                             atender e avisa o que muda (fração de tempo ligado, tempo de pull-down);
              "verificar" -> mantém o projeto pelos requisitos de carga e só avisa.
    Com COP fixo, potência e capacidade andam juntas (W = Q/COP): reduzir a potência sem perder capacidade
    exige COP maior (trocadores maiores, ΔT menores, compressor mais eficiente)."""
    criterio: str = "regime"
    modo: str = "limitar"
    tolerancia: float = 0.01      # banda aceita abaixo do limite quando a busca é iterativa (pico, ou COP livre)
    max_iter: int = 8


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
    restricao_potencia: RestricaoPotencia = field(default_factory=RestricaoPotencia)
    operacao: ParametrosOperacao = field(default_factory=ParametrosOperacao)
    simular_pulldown: bool = True
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
    pulldown: Optional[ResultadoPulldown] = None
    potencia: dict = field(default_factory=dict)

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


@dataclass
class _Nucleo:
    carga: CargaTermica
    ciclo: Ciclo
    bal: BalancoSistema
    cond: ResultadoTrocador
    evap: ResultadoTrocador
    comp: ResultadoCompressor
    av_carga: Avisos
    av_ciclo: Avisos
    it: int
    conv: bool
    umid: dict
    umid_conv: bool
    Q_requisitos: float          # capacidade de projeto pelos requisitos de carga (antes do teto de potência)
    dicas: tuple


def _aplicar_teto(carga: CargaTermica, Q_teto: Optional[float]) -> None:
    """Limita a capacidade de projeto (restrição de potência). A fração latente fica a mesma: com um
    compressor menor ele passa mais tempo ligado e a água removida por hora ligada cai na mesma proporção
    da capacidade, então, quando o regime governa, o balanço de umidade continua fechado com o mesmo ξ.
    Quando o pull-down governa, a serpentina continua dimensionada seca (ξ = 1, porta fechada), que é a
    condição mais exigente para a troca de calor."""
    if Q_teto is None or carga.Q_projeto <= Q_teto:
        return
    carga.Q_latente_projeto *= Q_teto / carga.Q_projeto
    carga.Q_projeto = Q_teto
    carga.caso_governante = f"limitado pela potência máxima do compressor (requisitos: {carga.caso_governante})"


def _nucleo(fl, entradas: EntradasProjeto, p: ParametrosProjeto, cap: Capacidade, temps: tuple, dicas: tuple,
            Q_teto: Optional[float]) -> _Nucleo:
    """Carga térmica <-> ciclo <-> trocadores, fechando o balanço de umidade do gabinete, e compressor."""
    T_evap, T_cond, T_ar_evap, T_ar_cond = temps
    equilibrio = p.uso.umidade_interna == "equilibrio"
    umid, umid_conv = None, True
    for _ in range(1, 5 if equilibrio else 2):
        av_carga = Avisos()
        carga = calcular_carga(cap, p.gabinete, p.uso, p.garrafa, entradas.T_ambiente_C, entradas.UR_ambiente,
                               entradas.T_alvo_C, av_carga)
        Q_req = carga.Q_projeto
        _aplicar_teto(carga, Q_teto)
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
        umid_conv = False
    carga.infiltracao["umidade"] = umid
    e = ciclo.estados
    comp = dimensionar_compressor(fl, bal.m, e["1s"], e["2"].P, bal.W_el, e["2"].T, ciclo.eta_global, p.compressor)
    return _Nucleo(carga, ciclo, bal, cond, evap, comp, av_carga, av_ciclo, it, conv, umid, umid_conv, Q_req, dicas)


def _pulldown(nuc: _Nucleo, p: ParametrosProjeto, cap: Capacidade,
              entradas: EntradasProjeto) -> tuple[ResultadoPulldown, Optional[str]]:
    """Pull-down estimado do projeto. Se o produto de reposição já entra frio (≤ T_alvo + 0,5 K), simula o
    ensaio usual: gabinete e produto encharcados à temperatura ambiente."""
    po, nota = p.operacao, None
    T_p0 = temperatura_inicial_produto(p.uso, po, entradas.T_ambiente_C)
    if T_p0 <= entradas.T_alvo_C + 0.5:
        T_amb = entradas.T_ambiente_C if po.T_ambiente_C is None else po.T_ambiente_C
        po = dataclasses.replace(po, T_produto_inicial_C=T_amb)
        nota = (f"o produto de reposição entra a {T_p0:.1f} °C (≤ T_alvo + 0,5 K): o pull-down foi simulado como "
                f"ensaio com o gabinete e o produto encharcados à ambiente ({T_amb:.1f} °C).")
    modelo = ModeloSistema.do_projeto(nuc.ciclo, nuc.comp, nuc.cond, nuc.evap, p.ciclo, p.compressor)
    return simular_pulldown(modelo, cap, p.gabinete, p.uso, p.garrafa, p.ciclo, entradas.T_ambiente_C,
                            entradas.T_alvo_C, po), nota


def _potencia_criterio(rp: RestricaoPotencia, nuc: _Nucleo, pd: Optional[ResultadoPulldown],
                       pd_erro: Optional[str]) -> float:
    if rp.criterio == "regime":
        return nuc.bal.W_el
    if pd is None:
        raise ErroProjeto(f"limite de potência no pico de pull-down: a simulação de pull-down falhou ({pd_erro}).")
    return max(pd.W_pico, nuc.bal.W_el)


def _proximo_teto(hist: list, W_alvo: float) -> float:
    """Secante em (Q_projeto, W_critério); W cresce com Q (compressor maior)."""
    Q1, W1 = hist[-1]
    if len(hist) >= 2:
        Q0, W0 = hist[-2]
        if Q1 != Q0 and (W1 - W0) / (Q1 - Q0) > 0.0:
            return Q1 + (W_alvo - W1) * (Q1 - Q0) / (W1 - W0)
    return Q1 * W_alvo / W1


def _cop_necessario(nuc: _Nucleo, W_c: float, W_max: float, Q: float) -> float:
    """COP para entregar a capacidade Q com o critério de potência em W_max (W_critério ∝ Q/COP)."""
    return nuc.ciclo.COP * (W_c / W_max) * (Q / nuc.carga.Q_projeto)


def _nome_criterio(rp: RestricaoPotencia) -> str:
    return "potência de regime" if rp.criterio == "regime" else "pico de potência no pull-down"


def _mensagem_potencia_inviavel(fl, entradas, p, car: CargaTermica, Q_req: float, Q_cap: float, cop: float,
                                W_max: float, rp: RestricaoPotencia, T_ar_evap, T_ar_cond) -> str:
    """Q_cap: capacidade que o limite permite com o COP atual (W_critério ∝ Q/COP, então o COP necessário para a
    capacidade Q é cop·Q/Q_cap)."""
    u = p.uso
    cop_min = cop * car.Q_regime * (1.0 + u.margem_seguranca) / Q_cap
    cop_req = cop * Q_req / Q_cap
    txt = (f"limite de {W_max:.0f} W ({_nome_criterio(rp)}) inviável com COP {cop:.2f}: o maior compressor que o "
           f"respeita entrega ≈ {Q_cap:.0f} W no ponto de projeto, abaixo da carga média de regime ({car.Q_regime:.0f} W) — o "
           f"gabinete não manteria {entradas.T_alvo_C:.1f} °C nem com o compressor 100 % ligado. Com W ≤ {W_max:.0f} W "
           f"seriam necessários COP ≥ {cop_min:.2f} para o regime com a margem de {u.margem_seguranca:.0%} e "
           f"COP ≈ {cop_req:.2f} para todos os requisitos (fator de utilização {u.fator_utilizacao_max:.0%}, "
           f"pull-down em {u.tempo_pulldown_h:g} h).")
    return txt + _sugestao_cop(fl, dataclasses.replace(entradas, COP=cop_req), T_ar_evap, T_ar_cond, p.ciclo)


def _avisos_potencia(av: Avisos, entradas, p, nuc: _Nucleo, pd, pd_erro, pd_nota, W_max, rp, fl, T_ar_evap,
                     T_ar_cond) -> dict:
    """Avisos e resumo da restrição de potência e do pull-down estimado."""
    car, bal, u = nuc.carga, nuc.bal, p.uso
    limitado = car.Q_projeto < nuc.Q_requisitos * (1.0 - 1e-9)
    m = u.margem_seguranca
    if pd_erro:
        av.atencao("pull-down", f"simulação de pull-down não concluída: {pd_erro}")
    if pd_nota:
        av.info("pull-down", pd_nota)
    if pd is not None:
        quando = "na partida, com o gabinete ainda encharcado" if pd.pico_na_partida else \
            f"em t ≈ {pd.t_pico_s / 3600.0:.1f} h"
        fim = (f"{pd.tempo_h:.1f} h" if pd.concluido else
               f"não chega a {pd.T_alvo - 273.15:.1f} °C (equilíbrio ≈ {pd.T_produto_equilibrio - 273.15:.1f} °C)")
        av.info("pull-down", f"estimativa quase estática (porta fechada, compressor 100 % ligado, produto de "
                f"{pd.T_produto_inicial - 273.15:.1f} a {pd.T_alvo - 273.15:.1f} °C, ambiente {pd.T_ambiente - 273.15:.1f} °C, "
                f"hA ar–produto {pd.hA_produto_W_K:.0f} W/K): {fim}; potência do compressor de {pd.W_inicial:.0f} W "
                f"(início) a {pd.W_final:.0f} W (fim), pico {pd.W_pico:.0f} W {quando} = "
                f"{pd.W_pico / bal.W_el:.2f}× a de regime; no fim o ar interno chega a {pd.T_ar_min - 273.15:.1f} °C e o "
                f"insuflado a {pd.T_insuflado_min - 273.15:.1f} °C. Calibrar hA com um ensaio de pull-down.")
        if not pd.concluido:
            av.critico("pull-down", f"com a porta fechada o produto não chega a {entradas.T_alvo_C:.1f} °C: equilíbrio "
                       f"em ≈ {pd.T_produto_equilibrio - 273.15:.1f} °C (capacidade seca menor que a carga do gabinete).")
        elif pd.tempo_h > u.tempo_pulldown_h:
            causa = ("a capacidade foi reduzida pelo limite de potência" if limitado else
                     f"a troca ar–produto (hA = {pd.hA_produto_W_K:.0f} W/K) limita; a carga de pull-down do "
                     "dimensionamento supõe o produto à temperatura do ar")
            av.atencao("pull-down", f"tempo estimado {pd.tempo_h:.1f} h > requisito de {u.tempo_pulldown_h:g} h: {causa}.")
        if pd.T_descarga_max - 273.15 > p.ciclo.T_descarga_max_C:
            av.atencao("pull-down", f"temperatura de descarga chega a {pd.T_descarga_max - 273.15:.0f} °C no pull-down "
                       f"(> {p.ciclo.T_descarga_max_C:.0f} °C).")
    resumo_pd = {} if pd is None else {
        "W_pico_pulldown_W": pd.W_pico, "razao_pico_regime": pd.W_pico / bal.W_el,
        "pulldown_concluido": pd.concluido, "tempo_pulldown_h": pd.tempo_h if pd.concluido else None,
        "requisito_pulldown_atendido": pd.concluido and pd.tempo_h <= u.tempo_pulldown_h}
    if W_max is None:
        return {} if pd is None else {"limite_W": None, "W_regime_W": bal.W_el, **resumo_pd}
    nome = _nome_criterio(rp)
    W_c = bal.W_el if rp.criterio == "regime" else (None if pd is None else max(pd.W_pico, bal.W_el))
    atende = None if W_c is None else W_c <= W_max * (1.0 + 1e-6)
    f_on = car.Q_regime / car.Q_projeto
    if W_c is None:
        av.atencao("potência", f"limite de {W_max:.0f} W no pico de pull-down não verificado (simulação falhou).")
    elif not atende:
        cop_req = _cop_necessario(nuc, W_c, W_max, nuc.Q_requisitos)
        Q_lim = car.Q_projeto * W_max / W_c
        if rp.modo != "verificar":
            alternativa = "."
        elif Q_lim > car.Q_regime * (1.0 + 1e-6):
            alternativa = (f" ou aceitar um compressor menor (RestricaoPotencia.modo = 'limitar'): ≈ {Q_lim:.0f} W de "
                           f"capacidade, ligado ≈ {car.Q_regime / Q_lim:.0%} do tempo em regime.")
        else:
            cop_min = _cop_necessario(nuc, W_c, W_max, car.Q_regime * (1.0 + m))
            alternativa = (f"; um compressor menor não resolve: o limite deixaria ≈ {Q_lim:.0f} W, abaixo da carga média "
                           f"de regime ({car.Q_regime:.0f} W), e só o regime com a margem já exigiria COP ≥ {cop_min:.2f}.")
        av.critico("potência", f"{nome} {W_c:.0f} W acima do limite de {W_max:.0f} W. Para atender todos os requisitos "
                   f"de carga com esse limite seria preciso COP ≈ {cop_req:.2f} (hoje {nuc.ciclo.COP:.2f})" + alternativa
                   + _sugestao_cop(fl, dataclasses.replace(entradas, COP=cop_req), T_ar_evap, T_ar_cond, p.ciclo))
    elif limitado:
        msg = (f"limite de {W_max:.0f} W ({nome}) ativo: capacidade de projeto reduzida de {nuc.Q_requisitos:.0f} para "
               f"{car.Q_projeto:.0f} W (compressor de {nuc.comp.deslocamento_cm3:.2f} cm³); em regime o compressor fica "
               f"ligado ≈ {f_on:.0%} do tempo (premissa: ≤ {u.fator_utilizacao_max:.0%})")
        if car.Q_pulldown * (1.0 + m) > car.Q_projeto * (1.0 + 1e-9):
            msg += f"; o requisito de pull-down em {u.tempo_pulldown_h:g} h deixa de ser garantido pela carga de projeto"
            disp = car.Q_projeto / (1.0 + m) - (car.Q_pulldown - car.Q_pulldown_produto)
            if pd is None and disp > 0.0:
                msg += (f" (≈ {car.Q_pulldown_produto * u.tempo_pulldown_h / disp:.1f} h pela conta do dimensionamento, com "
                        "o produto à temperatura do ar)")
        if pd is not None:
            msg += (f"; pull-down estimado em {pd.tempo_h:.1f} h (requisito {u.tempo_pulldown_h:g} h)" if pd.concluido else
                    f"; no pull-down o produto não chega a {entradas.T_alvo_C:.1f} °C")
        if f_on > 1.0 / (1.0 + m):
            av.critico("potência", msg + f" — sem a margem de segurança de {m:.0%}: reveja o COP ou o limite de potência.")
        else:
            av.atencao("potência", msg + ".")
    else:
        av.info("potência", f"{nome} {W_c:.0f} W dentro do limite de {W_max:.0f} W.")
    if rp.criterio == "regime" and pd is not None and pd.W_pico > W_max * (1.0 + 1e-6):
        av.atencao("potência", f"o pico estimado no pull-down ({pd.W_pico:.0f} W"
                   f"{', na partida' if pd.pico_na_partida else ''}) passa do limite de {W_max:.0f} W, que foi aplicado "
                   "à potência de regime; se o requisito vale para o ensaio inteiro, use "
                   "RestricaoPotencia(criterio='pico_pulldown').")
    return {"limite_W": W_max, "criterio": rp.criterio, "modo": rp.modo, "W_criterio_W": W_c, "atende": atende,
            "limitado": limitado, "W_regime_W": bal.W_el, "W_pico_pulldown_W": None, "razao_pico_regime": None,
            **resumo_pd, "Q_requisitos_W": nuc.Q_requisitos, "Q_projeto_W": car.Q_projeto,
            "fracao_ligado_regime": f_on}


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

    # 3) carga térmica <-> ciclo <-> trocadores <-> compressor, com a restrição de potência --------------
    W_max = entradas.potencia_max_compressor_W
    rp = p.restricao_potencia
    if W_max is not None:
        if not (W_max > 0.0 and math.isfinite(W_max)):
            raise ErroProjeto("potencia_max_compressor_W deve ser um número positivo.")
        if rp.criterio not in ("regime", "pico_pulldown"):
            raise ErroProjeto("RestricaoPotencia.criterio deve ser 'regime' ou 'pico_pulldown'.")
        if rp.modo not in ("limitar", "verificar"):
            raise ErroProjeto("RestricaoPotencia.modo deve ser 'limitar' ou 'verificar'.")
        if not 0.0 < rp.tolerancia < 0.5 or rp.max_iter < 1:
            raise ErroProjeto("RestricaoPotencia: use 0 < tolerancia < 0,5 e max_iter ≥ 1.")
    limitar = W_max is not None and rp.modo == "limitar"
    no_pico = W_max is not None and rp.criterio == "pico_pulldown"
    temps = (T_evap, T_cond, T_ar_evap, T_ar_cond)
    nc0 = {"condensador": p.condensador.n_circuitos, "evaporador": p.evaporador.n_circuitos}
    UR0 = p.uso.UR_interna
    Q_teto = None
    if limitar and not no_pico and entradas.COP is not None:
        # com COP informado W = Q/COP é exato: no critério de regime o teto de capacidade sai direto
        Q_teto = W_max * entradas.COP
        car0 = calcular_carga(cap, p.gabinete, p.uso, p.garrafa, entradas.T_ambiente_C, entradas.UR_ambiente,
                              entradas.T_alvo_C, Avisos())
        if Q_teto < car0.Q_regime:
            raise ErroProjeto(_mensagem_potencia_inviavel(fl, entradas, p, car0, car0.Q_projeto, Q_teto, entradas.COP,
                                                          W_max, rp, T_ar_evap, T_ar_cond))
    W_alvo = None if W_max is None else W_max * (1.0 - (0.5 * rp.tolerancia if no_pico else 1e-6))
    hist: list = []
    convergiu_pot = True
    for _ in range(rp.max_iter if limitar else 1):
        # cada passada parte do mesmo estado: o projeto final depende só da capacidade final
        p.condensador.n_circuitos, p.evaporador.n_circuitos = nc0["condensador"], nc0["evaporador"]
        p.uso.UR_interna = UR0
        try:
            nuc = _nucleo(fl, entradas, p, cap, temps, (None, None), Q_teto)
        except ErroProjeto as err:
            if Q_teto is None:
                raise
            raise ErroProjeto(f"com a capacidade de projeto limitada a {Q_teto:.0f} W pelo limite de {W_max:.0f} W "
                              f"({_nome_criterio(rp)}): {err}") from err
        pd, pd_erro, pd_nota = None, None, None
        if p.simular_pulldown or no_pico:
            try:
                pd, pd_nota = _pulldown(nuc, p, cap, entradas)
            except ErroProjeto as err:   # análise secundária (simular_pulldown já converte falhas numéricas)
                pd_erro = str(err)
        if not limitar:
            break
        W_c = _potencia_criterio(rp, nuc, pd, pd_erro)
        limitado = nuc.carga.Q_projeto < nuc.Q_requisitos * (1.0 - 1e-9)
        if limitado and nuc.carga.Q_projeto < nuc.carga.Q_regime:
            raise ErroProjeto(_mensagem_potencia_inviavel(fl, entradas, p, nuc.carga, nuc.Q_requisitos,
                                                          nuc.carga.Q_projeto * W_max / W_c, nuc.ciclo.COP, W_max, rp,
                                                          T_ar_evap, T_ar_cond))
        if W_c <= W_max * (1.0 + 1e-9) and (not limitado or W_c >= min(W_max * (1.0 - rp.tolerancia),
                                                                         W_alvo * (1.0 - 1e-6))):
            break
        hist.append((nuc.carga.Q_projeto, W_c))
        Q_no_limite = min(_proximo_teto(hist, W_max), nuc.Q_requisitos)
        if Q_no_limite < nuc.carga.Q_regime:
            raise ErroProjeto(_mensagem_potencia_inviavel(fl, entradas, p, nuc.carga, nuc.Q_requisitos, Q_no_limite,
                                                          nuc.ciclo.COP, W_max, rp, T_ar_evap, T_ar_cond))
        Q_teto = max(min(_proximo_teto(hist, W_alvo), nuc.Q_requisitos), nuc.carga.Q_regime * (1.0 + 1e-6))
    else:
        convergiu_pot = False
    carga, ciclo, bal, cond, evap, comp = nuc.carga, nuc.ciclo, nuc.bal, nuc.cond, nuc.evap, nuc.comp
    it, conv, umid = nuc.it, nuc.conv, nuc.umid
    equilibrio = p.uso.umidade_interna == "equilibrio"
    if not nuc.umid_conv:
        av.atencao("umidade", "o balanço de umidade do gabinete não convergiu em 4 passos")
    if not convergiu_pot:
        av.atencao("potência", f"a busca da capacidade que respeita {W_max:.0f} W não convergiu em {rp.max_iter} passos.")
    av.itens.extend(nuc.av_carga.itens)
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
    av.itens.extend(nuc.av_ciclo.itens)
    if entradas.COP is not None and ciclo.eta_global > pc.eta_global_faixa[1]:
        av.info("compressor", _sugestao_cop(fl, entradas, T_ar_evap, T_ar_cond, pc).strip())
    if 0.85 < ciclo.eta_is < 1.0:
        av.atencao("compressor", f"η_is implícita = {ciclo.eta_is:.2f} (> 0,85): reveja η_eletromecânica "
                   f"({pc.eta_eletromecanica:.2f}) ou o COP; a temperatura de descarga fica subestimada.")

    # 4) compressor (dimensionado em _nucleo) ---------------------------------------------------------
    e = ciclo.estados

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

    pot = _avisos_potencia(av, entradas, p, nuc, pd, pd_erro, pd_nota, W_max, rp, fl, T_ar_evap, T_ar_cond)

    sens = (_sensibilidade(fl, bal, ciclo, carga, p, T_ar_cond, T_ar_evap, cond, evap, cap_sel.escolhido.D)
            if p.analise_sensibilidade else {})
    return ResultadoProjeto(entradas, p, cap, carga, ciclo, bal, comp, cond, evap, cap_sel, carga_ref, ex,
                            energia, sens, av, it, pd, pot)


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
