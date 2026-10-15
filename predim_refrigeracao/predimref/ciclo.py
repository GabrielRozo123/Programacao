"""Ciclo de compressão de vapor subcrítico com superaquecimento, sub-resfriamento,
trocador interno (linha de sucção / capilar) opcional, e verificação termodinâmica do COP.

Pontos (numeração usada em todo o pacote)
  1   saída do evaporador (P_evap, T_evap + SA)
  1s  sucção do compressor (após o trocador interno, se houver)
  2s  descarga isentrópica;  2 descarga real (P_cond)
  3   saída do condensador (P_cond − ΔP_cond, T_sat − SR)
  3i  entrada do capilar (após o trocador interno)
  4   entrada do evaporador (P_evap + ΔP_evap, h4 = h3i: capilar adiabático)

Definições de rendimento do compressor
  η_global = ṁ (h2s − h1s) / W_el           (isentrópico global, referido à potência elétrica)
  η_is     = (h2s − h1s) / (h2 − h1s)       (isentrópico interno, define a temperatura de descarga)
  η_em     = η_global / η_is                (eletromecânico: motor × mecânico)
  Calor perdido pela carcaça: Q_carc = W_el − ṁ (h2 − h1s) ≥ 0.

Com o COP informado, η_global = COP / COP_ciclo_ideal, onde COP_ciclo_ideal é o COP do mesmo
ciclo com compressão isentrópica. COP > COP_ciclo_ideal (ou > Carnot) é impossível.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from scipy.optimize import brentq

from .avisos import Avisos, ErroProjeto
from .propriedades import Fluido


@dataclass
class ParametrosCiclo:
    dT_evap: float = 10.0            # T_ar entrada evaporador − T_evap [K]
    dT_cond: float = 13.0            # T_cond − T_ar entrada condensador [K]
    dT_recirculacao_cond: float = 0.0  # aquecimento do ar no compartimento antes do condensador [K]
    dT_retorno_evap: float = 0.0     # ar de retorno ao evaporador − T alvo [K]
    superaquecimento: float = 5.0    # na saída do evaporador [K]
    subresfriamento: float = 3.0     # na saída do condensador [K]
    eficacia_ihx: float = 0.0        # trocador capilar/linha de sucção (0 = sem)
    eta_eletromecanica: float = 0.72  # motor × mecânico, compressor hermético pequeno
    eta_global_sem_cop: float = 0.55  # usado só quando o COP não é informado
    T_descarga_max_C: float = 130.0
    eta_global_faixa: tuple = (0.35, 0.70)  # faixa realista para herméticos alternativos pequenos


@dataclass
class Ciclo:
    fluido: str
    T_evap: float
    T_cond: float
    estados: dict
    COP: float
    COP_ciclo_ideal: float      # compressão isentrópica, mesmas temperaturas
    COP_carnot_ciclo: float     # entre T_evap e T_cond
    eta_global: float
    eta_is: float
    eta_em: float
    q_evap: float               # J/kg
    w_s: float                  # h2s − h1s
    q_ihx: float
    razao_pressao: float
    extras: dict = field(default_factory=dict)

    @property
    def w_ref(self) -> float:
        """Trabalho específico entregue ao refrigerante (h2 − h1s)."""
        return self.estados["2"].h - self.estados["1s"].h


def resolver_ciclo(fl: Fluido, T_evap: float, T_cond: float, p: ParametrosCiclo,
                   cop: Optional[float], dP_cond: float = 0.0, dP_evap: float = 0.0,
                   avisos: Optional[Avisos] = None) -> Ciclo:
    av = avisos if avisos is not None else Avisos()
    if T_cond >= fl.Tc - 5.0:
        raise ErroProjeto(f"T_cond = {T_cond - 273.15:.1f} °C muito próxima da crítica do {fl.nome} "
                          f"({fl.Tc - 273.15:.1f} °C): ciclo subcrítico inválido.")
    if T_evap <= fl.Ttriplo + 5:
        raise ErroProjeto("T_evap abaixo da faixa válida do fluido.")
    P_evap, P_cond = fl.Psat(T_evap), fl.Psat(T_cond)
    if p.superaquecimento > 0:
        e1 = fl.estado_PT(P_evap, T_evap + p.superaquecimento)
    else:
        e1 = fl.estado_PQ(P_evap, 1.0)
    P3 = P_cond - dP_cond
    T3sat = fl.Tsat(P3)
    e3 = fl.estado_PT(P3, T3sat - p.subresfriamento) if p.subresfriamento > 0 else fl.estado_PQ(P3, 0.0)
    # trocador interno: a corrente de vapor (menor capacidade térmica) é a de referência
    q_ihx = 0.0
    if p.eficacia_ihx > 0:
        h_v_max = fl.estado_PT(P_evap, e3.T).h
        q_ihx = p.eficacia_ihx * (h_v_max - e1.h)
    e1s = fl.estado_PH(P_evap, e1.h + q_ihx)
    e3i = fl.estado_PH(P3, e3.h - q_ihx)
    e4 = fl.estado_PH(P_evap + dP_evap, e3i.h)
    e2s = fl.estado_PS(P_cond, e1s.s)
    w_s = e2s.h - e1s.h
    q_evap = e1.h - e4.h
    cop_ideal = q_evap / w_s
    cop_carnot = T_evap / (T_cond - T_evap)
    if cop is not None:
        if cop >= cop_carnot:
            raise ErroProjeto(f"COP {cop:.2f} ≥ COP de Carnot {cop_carnot:.2f} entre T_evap = "
                              f"{T_evap - 273.15:.1f} °C e T_cond = {T_cond - 273.15:.1f} °C: viola a 2ª lei.")
        if cop >= cop_ideal:
            raise ErroProjeto(f"COP {cop:.2f} ≥ COP do ciclo com compressão isentrópica ({cop_ideal:.2f}): "
                              "impossível com essas temperaturas. Reduza as diferenças de temperatura "
                              "dos trocadores (trocadores maiores) ou reveja o COP.")
        eta_g = cop / cop_ideal
    else:
        eta_g = p.eta_global_sem_cop
        cop = eta_g * cop_ideal
    eta_is = eta_g / p.eta_eletromecanica
    eta_em = p.eta_eletromecanica
    if eta_is > 1.0:
        eta_is, eta_em = 1.0, eta_g
        av.critico("compressor", f"η_global = {eta_g:.2f} exige η_eletromecânica = η_global (η_is = 1): "
                   "o COP pedido só é atingível com compressor sem perdas internas.")
    lo, hi = p.eta_global_faixa
    if eta_g > hi:
        av.atencao("compressor", f"COP pedido implica η_global = {eta_g:.2f} (> {hi:.2f}, acima dos melhores "
                   "herméticos alternativos de pequena capacidade). Verificar com catálogo ou rever o COP.")
    elif eta_g < lo:
        av.atencao("compressor", f"COP pedido implica η_global = {eta_g:.2f} (< {lo:.2f}): COP baixo para estas "
                   "temperaturas; há margem para pedir um COP maior.")
    e2 = fl.estado_PH(P_cond, e1s.h + w_s / eta_is)
    if e2.T - 273.15 > p.T_descarga_max_C:
        av.atencao("compressor", f"temperatura de descarga {e2.T - 273.15:.0f} °C > {p.T_descarga_max_C:.0f} °C "
                   "(risco de degradação do óleo).")
    if P_evap < 101325.0:
        av.atencao("ciclo", f"P_evap = {P_evap / 1e5:.3f} bar abs < 1 atm: risco de entrada de ar/umidade "
                   "em vazamentos.")
    estados = {"1": e1, "1s": e1s, "2s": e2s, "2": e2, "3": e3, "3i": e3i, "4": e4}
    if e4.x <= 0:
        raise ErroProjeto("Estado 4 sem vapor: verifique sub-resfriamento/IHX.")
    return Ciclo(fl.nome, T_evap, T_cond, estados, cop, cop_ideal, cop_carnot, eta_g, eta_is, eta_em,
                 q_evap, w_s, q_ihx, P_cond / P_evap)


@dataclass
class BalancoSistema:
    m: float
    Q_evap: float
    W_el: float
    Q_cond: float
    Q_carcaca: float
    Q_ihx: float
    erro_balanco: float  # (Q_evap + W_el − Q_cond − Q_carc)/W_el


def balanco(ciclo: Ciclo, Q_evap: float, avisos: Optional[Avisos] = None) -> BalancoSistema:
    e = ciclo.estados
    m = Q_evap / ciclo.q_evap
    W_el = Q_evap / ciclo.COP
    Q_cond = m * (e["2"].h - e["3"].h)
    Q_carc = W_el - m * (e["2"].h - e["1s"].h)
    if Q_carc < -1e-9 and avisos is not None:
        avisos.critico("balanço", "calor de carcaça negativo: η_is incoerente com η_global.")
    err = (Q_evap + W_el - Q_cond - Q_carc) / W_el
    return BalancoSistema(m, Q_evap, W_el, Q_cond, Q_carc, m * ciclo.q_ihx, err)


def exergia(ciclo: Ciclo, b: BalancoSistema, T0: float, T_frio: float) -> dict:
    """Destruição de exergia por componente [W], estado morto T0 = ambiente.

    O efeito útil é a exergia do calor retirado do espaço refrigerado à T_frio:
    Ex_Q = Q_evap (T0/T_frio − 1). Fechamento: W_el = Ex_Q + Σ Ex_destruída.
    O evaporador inclui a irreversibilidade da diferença de temperatura ar-refrigerante,
    e o condensador a do calor rejeitado ao ambiente."""
    e, m = ciclo.estados, b.m
    d = {
        "compressor": T0 * (m * (e["2"].s - e["1s"].s) + b.Q_carcaca / T0),
        "condensador": T0 * (m * (e["3"].s - e["2"].s) + b.Q_cond / T0),
        "trocador interno": T0 * m * ((e["1s"].s - e["1"].s) + (e["3i"].s - e["3"].s)),
        "capilar": T0 * m * (e["4"].s - e["3i"].s),
        "evaporador": T0 * (m * (e["1"].s - e["4"].s) - b.Q_evap / T_frio),
    }
    ex_q = b.Q_evap * (T0 / T_frio - 1.0)
    d = {k: (0.0 if abs(v) < 1e-6 else v) for k, v in d.items()}
    fech = (b.W_el - ex_q - sum(d.values())) / b.W_el
    return {"destruicao_W": d, "Ex_util_W": ex_q, "eta_II": ex_q / b.W_el, "erro_fechamento": fech}


def escala_dT_para_cop(fl: Fluido, cop_alvo: float, T_ar_evap: float, T_ar_cond: float,
                       p: ParametrosCiclo, eta_global: float) -> Optional[float]:
    """Fator s que multiplica (dT_evap, dT_cond) para que um compressor de η_global dado atinja
    o COP alvo. s < 1 => trocadores maiores. Retorna None se inatingível mesmo com s = 0,02.
    O limite superior de s respeita T_cond < T_c − 5 K (validade do ciclo subcrítico)."""
    q = ParametrosCiclo(**{**p.__dict__, "eta_global_sem_cop": eta_global})

    def resid(s):
        c = resolver_ciclo(fl, T_ar_evap - s * p.dT_evap, T_ar_cond + s * p.dT_cond, q, None)
        return c.COP - cop_alvo

    s_min = 0.02
    s_max = min(3.0, (fl.Tc - 5.1 - T_ar_cond) / p.dT_cond, (T_ar_evap - fl.Ttriplo - 5.1) / p.dT_evap)
    try:
        a = resid(s_min)
    except ErroProjeto:
        return None
    if a < 0.0 or s_max <= s_min:
        return None
    try:
        b = resid(s_max)
    except ErroProjeto:
        return None
    if b >= 0.0:
        return s_max
    return brentq(resid, s_min, s_max, xtol=1e-4)
