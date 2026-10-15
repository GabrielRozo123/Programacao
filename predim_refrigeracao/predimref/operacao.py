"""Operação fora do ponto de projeto: casamento compressor–trocadores e pull-down quase estático.

Por que importa para a potência máxima
--------------------------------------
Num compressor alternativo de rotação fixa a potência elétrica não é constante. Com o gabinete
quente (início do pull-down) a pressão de evaporação é alta, a massa específica na sucção também, e
a potência passa por um máximo: para um compressor ideal sem espaço morto e pressão de descarga
fixa, W ∝ P_suc [(P_desc/P_suc)^((k−1)/k) − 1], que é máxima em P_desc/P_suc = k^(k/(k−1)) (≈ 2,9 para
k = 1,13). Por isso o motor é verificado no pull-down e não só no regime (Stoecker & Jones,
Refrigeration and Air Conditioning, 2ª ed., cap. 11). Um limite de potência máxima de ensaio
precisa dizer se vale para o regime ou para o pico; aqui calculam-se os dois.

Modelo do sistema (casamento de componentes; Stoecker & Jones, cap. 14)
-----------------------------------------------------------------------
Geometria fixa (a do projeto) e incógnitas T_evap e T_cond:
    compressor   ṁ = V_desl (N/60) η_v(r) ρ_1s ,   W_el = ṁ (h_2s − h_1s) / η_global
    evaporador   ṁ (h_1 − h_4) = ξ ε_e Ċ_ar,e (T_ar,e − T_evap)
    condensador  ṁ (h_2 − h_3) = ε_c Ċ_ar,c (T_cond − T_ar,c)
η_v pelo mesmo modelo de espaço morto do dimensionamento; η_global e η_eletromecânica constantes
(as do ponto de projeto); superaquecimento, sub-resfriamento e eficácia do trocador interno mantidos;
ε e Ċ_ar das serpentinas de projeto (sem margem), com as eficácias referidas a T_evap (saída do
evaporador) e T_cond (entrada do condensador), como no dimensionamento; quedas de pressão do
refrigerante fixas nas de projeto (P_evap é a de saída e h_4 = h_3i, então elas quase não mexem em Q e W).
No ponto de projeto o modelo reproduz T_evap, T_cond, ṁ, Q e W do dimensionamento (teste de consistência).

Pull-down quase estático (porta fechada)
----------------------------------------
Produto (bebida + embalagem + ``Uso.massa_adicional_kg``) concentrado num nó à T_p, que troca calor
com o ar interno à T_a por hA; o ar tem capacidade térmica desprezível frente à do produto e fica em
equilíbrio a cada instante:
    0 = hA (T_p − T_a) + UA_gab (T_amb − T_a) + Q_base + Q_int − Q_evap(T_a)
    C_p dT_p/dt = −hA (T_p − T_a)   →   t(T_p) = ∫ C_p dT_p / [hA (T_p − T_a(T_p))]
A transmissão é a do dimensionamento (afim em T_a: UA_gab e o acréscimo da base sobre o
compartimento do compressor). Q_evap(T_a), W(T_a) etc. vêm de uma grade de pontos de operação
interpolada por PCHIP (monotônica, sem oscilação); o pico de potência é refinado com o modelo completo.

Hipóteses e limites (estimativa de pré-dimensionamento, não substitui o Amesim):
* ε constante: o lado do ar domina a resistência; ε muda pouco com o coeficiente interno.
* η_global constante: em compressores reais ela varia com a razão de pressão; calibrar com o
  polinômio de catálogo (EN 12900 / AHRI 540) ou com ensaio do compressor candidato.
* superaquecimento fixo: com capilar o evaporador fica sub-alimentado no início do pull-down; o Amesim,
  com o capilar e a carga de fluido, representa isso.
* hA ar–produto é a premissa mais incerta do tempo de pull-down (convecção mista a baixa velocidade,
  garrafas encostadas): calibrar com um ensaio de pull-down do laboratório. Massa do gabinete (liner,
  prateleiras não informadas) desprezada: o tempo real tende a ser maior.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq, minimize_scalar

from .avisos import Avisos, ErroProjeto
from .ciclo import Ciclo, ParametrosCiclo, resolver_ciclo
from .compressor import ParametrosCompressor, eficiencia_volumetrica
from .constantes import C_para_K
from .gabinete import cargas_internas, transmissao
from .propriedades import Fluido


@dataclass
class ParametrosOperacao:
    """Premissas do pull-down quase estático."""
    T_ambiente_C: Optional[float] = None         # None -> a do projeto
    T_produto_inicial_C: Optional[float] = None  # None -> Uso.T_produto_entrada_C ou a ambiente
    h_produto_W_m2K: float = 5.0                 # ar–garrafa na área lateral (convecção mista, garrafas encostadas)
    hA_produto_W_K: Optional[float] = None       # sobrepõe h × área (use o valor calibrado em ensaio)
    fator_umidade: float = 1.0                   # porta fechada: serpentina praticamente seca
    n_pontos: int = 25                           # grade de temperatura do ar interno
    n_passos: int = 400                          # passos de integração em T_produto


@dataclass
class ModeloSistema:
    """Componentes congelados no projeto (geometria, compressor, ε e Ċ_ar das serpentinas de projeto)."""
    fluido: str
    deslocamento_m3: float
    rotacao_rpm: float
    p_compressor: ParametrosCompressor
    p_ciclo: ParametrosCiclo          # cópia com η_global e η_em do ponto de projeto
    eta_global: float
    eps_evap: float
    C_ar_evap: float
    eps_cond: float
    C_ar_cond: float
    dP_cond: float
    dP_evap: float
    dT_evap_proj: float               # T_ar,e − T_evap no projeto (chute inicial)
    dT_cond_proj: float               # T_cond − T_ar,c no projeto (chute inicial)
    Q_proj: float

    @classmethod
    def do_projeto(cls, ciclo: Ciclo, comp, cond, evap, p_ciclo: ParametrosCiclo,
                   p_comp: ParametrosCompressor) -> "ModeloSistema":
        pc = copy.deepcopy(p_ciclo)
        pc.eta_global_sem_cop = ciclo.eta_global
        pc.eta_eletromecanica = ciclo.eta_em
        return cls(ciclo.fluido, comp.deslocamento_cm3 * 1e-6, comp.rotacao_rpm, copy.deepcopy(p_comp), pc,
                   ciclo.eta_global, evap.eficacia, evap.C_ar, cond.eficacia, cond.C_ar, cond.dP_ref, evap.dP_ref,
                   evap.T_ar_in - ciclo.T_evap, ciclo.T_cond - cond.T_ar_in, evap.Q)


def modelo_do_projeto(res) -> ModeloSistema:
    p = res.parametros
    return ModeloSistema.do_projeto(res.ciclo, res.compressor, res.condensador, res.evaporador, p.ciclo, p.compressor)


@dataclass
class PontoOperacao:
    T_ar_evap: float
    T_ar_cond: float
    T_evap: float
    T_cond: float
    P_evap: float
    P_cond: float
    m: float
    Q_evap: float
    Q_cond: float
    W_el: float
    eta_v: float
    T_descarga: float

    @property
    def COP(self) -> float:
        return self.Q_evap / self.W_el

    @property
    def razao_pressao(self) -> float:
        return self.P_cond / self.P_evap


def _avaliar(modelo: ModeloSistema, fl: Fluido, T_e: float, T_c: float):
    c = resolver_ciclo(fl, T_e, T_c, modelo.p_ciclo, None, modelo.dP_cond, modelo.dP_evap, Avisos())
    s = c.estados["1s"]
    n = modelo.p_compressor.expoente_reexpansao or fl.kappa(s.P, s.T, s.rho)
    eta_v = eficiencia_volumetrica(c.estados["2"].P / s.P, modelo.p_compressor, n)
    m = modelo.deslocamento_m3 * modelo.rotacao_rpm / 60.0 * eta_v * s.rho
    return c, m, eta_v


def ponto_operacao(modelo: ModeloSistema, T_ar_evap: float, T_ar_cond: float, xi: float = 1.0,
                   chute: Optional[tuple] = None, fl: Optional[Fluido] = None) -> PontoOperacao:
    """Ponto de equilíbrio compressor–evaporador–condensador para as temperaturas de entrada do ar dadas.

    Newton 2D com jacobiana por diferenças finitas a partir do chute (ou do ΔT de projeto); se não
    convergir, bissecção aninhada (T_cond para cada T_evap e depois T_evap), que é robusta porque os dois
    resíduos são monotônicos."""
    fl = fl or Fluido(modelo.fluido)
    Ce = xi * modelo.eps_evap * modelo.C_ar_evap
    Cc = modelo.eps_cond * modelo.C_ar_cond
    Q_ref = max(modelo.Q_proj, 1.0)
    T_e_min = fl.Ttriplo + 5.5
    T_c_max = fl.Tc - 5.5
    SR = modelo.p_ciclo.subresfriamento

    def residuos(T_e: float, T_c: float):
        c, m, eta_v = _avaliar(modelo, fl, T_e, T_c)
        e = c.estados
        r = np.array([(m * c.q_evap - Ce * (T_ar_evap - T_e)) / Q_ref,
                      (m * (e["2"].h - e["3"].h) - Cc * (T_c - T_ar_cond)) / Q_ref])
        return r, (c, m, eta_v)

    def valido(T_e: float, T_c: float) -> bool:
        return T_e_min < T_e < T_ar_evap and T_ar_cond < T_c < T_c_max and T_c - SR > T_e + 0.5

    x = np.array(chute if chute is not None else (T_ar_evap - modelo.dT_evap_proj, T_ar_cond + modelo.dT_cond_proj),
                 dtype=float)
    sol = None
    if valido(*x):
        try:
            sol = _newton(residuos, valido, x)
        except (ErroProjeto, ValueError, ZeroDivisionError, np.linalg.LinAlgError):
            sol = None
    if sol is None:
        sol = _bisseccao(residuos, fl, T_ar_evap, T_ar_cond, T_e_min, T_c_max, SR)
    (T_e, T_c), (c, m, eta_v) = sol
    e = c.estados
    return PontoOperacao(T_ar_evap, T_ar_cond, T_e, T_c, e["1"].P, e["2"].P, m, m * c.q_evap,
                         m * (e["2"].h - e["3"].h), m * c.w_s / modelo.eta_global, eta_v, e["2"].T)


def _newton(residuos, valido, x, tol: float = 1e-9, max_iter: int = 30):
    r, aux = residuos(*x)
    for _ in range(max_iter):
        if np.max(np.abs(r)) < tol:
            return x, aux
        J = np.empty((2, 2))
        for j in range(2):
            dx = np.zeros(2)
            dx[j] = 1e-3
            J[:, j] = (residuos(*(x + dx))[0] - r) / 1e-3
        passo = np.linalg.solve(J, -r)
        lim = np.max(np.abs(passo))
        if lim > 5.0:
            passo *= 5.0 / lim
        lam = 1.0
        while lam > 1e-3:
            xn = x + lam * passo
            if valido(*xn):
                rn, auxn = residuos(*xn)
                if np.max(np.abs(rn)) < np.max(np.abs(r)):
                    x, r, aux = xn, rn, auxn
                    break
            lam *= 0.5
        else:
            return None
    return (x, aux) if np.max(np.abs(r)) < tol else None


def _bisseccao(residuos, fl, T_ar_e, T_ar_c, T_e_min, T_c_max, SR):
    def Tc_de(T_e):
        lo = max(T_ar_c + 1e-3, T_e + SR + 0.6)
        hi = min(T_c_max, T_ar_c + 150.0)
        f = lambda T_c: residuos(T_e, T_c)[0][1]  # noqa: E731
        if f(lo) <= 0.0:
            return lo
        if f(hi) > 0.0:
            raise ErroProjeto(f"ponto de operação: o condensador não rejeita o calor nem com T_cond = "
                              f"{hi - 273.15:.0f} °C (ar a {T_ar_c - 273.15:.1f} °C).")
        return brentq(f, lo, hi, xtol=1e-7)

    def g(T_e):
        return residuos(T_e, Tc_de(T_e))[0][0]

    lo, hi = max(T_e_min, T_ar_e - 80.0), T_ar_e - 1e-3
    if g(lo) > 0.0:
        raise ErroProjeto("ponto de operação: compressor grande demais para o evaporador mesmo no limite "
                          "inferior de T_evap.")
    T_e = brentq(g, lo, hi, xtol=1e-7)
    T_c = Tc_de(T_e)
    return np.array([T_e, T_c]), residuos(T_e, T_c)[1]


# =========================================================================== pull-down
@dataclass
class ResultadoPulldown:
    T_ambiente: float
    T_produto_inicial: float
    T_alvo: float
    C_produto_J_K: float
    hA_produto_W_K: float
    UA_gabinete_W_K: float
    Q_internas_W: float
    fator_umidade: float
    concluido: bool                  # o produto chega a T_alvo
    tempo_s: float                   # até T_alvo (ou até 0,5 K da temperatura de equilíbrio, se não concluir)
    T_produto_equilibrio: Optional[float]
    t: np.ndarray
    T_produto: np.ndarray
    T_ar: np.ndarray
    T_evap: np.ndarray
    T_cond: np.ndarray
    Q_evap: np.ndarray
    W_el: np.ndarray
    T_descarga: np.ndarray
    pico: PontoOperacao              # máximo de W entre o ar no fim do pull-down e T_p0 (inclui a partida)
    t_pico_s: float
    pico_na_partida: bool            # o máximo está na partida (ar ainda acima do valor quase estático)
    W_pico_trajetoria: float         # máximo na trajetória quase estática (t > 0)
    E_compressor_J: float
    grade: dict = field(default_factory=dict)

    @property
    def tempo_h(self) -> float:
        return self.tempo_s / 3600.0

    @property
    def W_pico(self) -> float:
        return self.pico.W_el

    @property
    def W_inicial(self) -> float:
        return float(self.W_el[0])

    @property
    def W_final(self) -> float:
        return float(self.W_el[-1])

    @property
    def E_compressor_kWh(self) -> float:
        return self.E_compressor_J / 3.6e6

    @property
    def T_descarga_max(self) -> float:
        return float(np.max(self.T_descarga))

    def curva(self, n: int = 61) -> dict:
        """Curva reamostrada em tempo uniforme (para exportar e comparar com o Amesim)."""
        tt = np.linspace(0.0, self.t[-1], n)
        f = lambda y: np.interp(tt, self.t, y).tolist()  # noqa: E731
        return {"t_s": tt.tolist(), "T_produto_K": f(self.T_produto), "T_ar_K": f(self.T_ar),
                "T_evap_K": f(self.T_evap), "T_cond_K": f(self.T_cond), "Q_evap_W": f(self.Q_evap),
                "W_el_W": f(self.W_el), "T_descarga_K": f(self.T_descarga)}


def simular_pulldown(modelo: ModeloSistema, cap, gab, uso, garrafa, pc: ParametrosCiclo, T_amb_proj_C: float,
                     T_alvo_C: float, po: ParametrosOperacao) -> ResultadoPulldown:
    """Pull-down de portas fechadas da carga cheia, do produto à T_inicial até T_alvo (ver docstring do módulo)."""
    fl = Fluido(modelo.fluido)
    T_amb_C = T_amb_proj_C if po.T_ambiente_C is None else po.T_ambiente_C
    if po.T_produto_inicial_C is not None:
        T_p0_C = po.T_produto_inicial_C
    else:
        T_p0_C = T_amb_C if uso.T_produto_entrada_C is None else uso.T_produto_entrada_C
    if T_p0_C <= T_alvo_C + 0.5:
        raise ErroProjeto("pull-down: o produto inicial deve estar acima de T_alvo + 0,5 K.")
    if T_amb_C <= T_alvo_C:
        raise ErroProjeto("pull-down: a temperatura ambiente deve ser maior que a alvo.")
    if po.n_pontos < 5 or po.n_passos < 20:
        raise ErroProjeto("pull-down: use n_pontos ≥ 5 e n_passos ≥ 20.")
    T_amb, T_p0, T_f = C_para_K(T_amb_C), C_para_K(T_p0_C), C_para_K(T_alvo_C)
    E = (cap.n_garrafas * garrafa.energia_resfriamento(T_p0_C, T_alvo_C)
         + uso.massa_adicional_kg * uso.cp_adicional * (T_p0_C - T_alvo_C))
    C_p = E / (T_p0_C - T_alvo_C)
    hA = po.hA_produto_W_K
    if hA is None:
        hA = po.h_produto_W_m2K * cap.n_garrafas * math.pi * garrafa.diametro_m * garrafa.altura_m
    if not (hA > 0.0 and C_p > 0.0):
        raise ErroProjeto("pull-down: hA do produto e capacidade térmica precisam ser positivos.")
    tr = transmissao(cap, gab, T_amb, T_f)
    UA, Qt_f = tr["UA_total"], tr["Q_total"]
    Q_int = cargas_internas(uso)
    T_ar_c = T_amb + pc.dT_recirculacao_cond
    dTr = pc.dT_retorno_evap
    xi = po.fator_umidade

    def carga_sem_produto(T_a):
        return Qt_f + UA * (T_f - T_a) + Q_int

    def ponto(T_a, chute=None):
        return ponto_operacao(modelo, T_a + dTr, T_ar_c, xi, chute, fl)

    # grade de T_a: do limite inferior (ar no fim do pull-down) até T_p0 -------------------------------
    p_f = ponto(T_f)
    N0 = p_f.Q_evap - carga_sem_produto(T_f)
    T_lo = T_f - max(N0, 0.0) / hA - 1.0
    Ts = np.linspace(T_lo, T_p0, po.n_pontos)
    i0 = int(np.argmin(np.abs(Ts - T_f)))
    pts: list = [None] * len(Ts)
    pts[i0] = ponto(Ts[i0], (p_f.T_evap, p_f.T_cond))
    for ordem in (range(i0 + 1, len(Ts)), range(i0 - 1, -1, -1)):
        anterior = i0
        for i in ordem:
            q = pts[anterior]
            pts[i] = ponto(Ts[i], (q.T_evap + (Ts[i] - Ts[anterior]) * 0.6, q.T_cond))
            anterior = i
    arr = {k: np.array([getattr(q, k) for q in pts]) for k in ("Q_evap", "W_el", "T_evap", "T_cond", "T_descarga")}
    it = {k: PchipInterpolator(Ts, v) for k, v in arr.items()}

    def liquido(T_a):  # calor líquido que o evaporador tira do produto com o ar à T_a
        return float(it["Q_evap"](T_a)) - carga_sem_produto(T_a)

    # fim: T_alvo, ou perto do equilíbrio se o sistema não chegar lá -------------------------------
    concluido, T_eq = True, None
    if liquido(T_f) <= 0.0:
        concluido = False
        if liquido(T_p0) <= 0.0:
            raise ErroProjeto("pull-down: a capacidade não supera a carga do gabinete nem com o produto quente.")
        T_eq = brentq(liquido, T_f, T_p0, xtol=1e-6)
        T_fim = T_eq + 0.5
        if T_fim >= T_p0:
            raise ErroProjeto("pull-down: o equilíbrio fica a menos de 0,5 K da temperatura inicial do produto.")
    else:
        T_fim = T_f
    Tp = np.linspace(T_p0, T_fim, po.n_passos + 1)
    Ta = np.empty_like(Tp)
    for k, T_p in enumerate(Tp):
        F = lambda T_a: liquido(T_a) - hA * (T_p - T_a)  # noqa: E731
        Ta[k] = brentq(F, T_lo, T_p, xtol=1e-7) if F(T_p) > 0.0 else T_p
    Q_prod = hA * (Tp - Ta)
    if np.any(Q_prod <= 0.0):
        raise ErroProjeto("pull-down: troca ar–produto nula na integração (revise hA e a capacidade).")
    dtdT = C_p / Q_prod                                  # s/K (T_p decrescente)
    t = -cumulative_trapezoid(dtdT, Tp, initial=0.0)
    W = it["W_el"](Ta)
    E_comp = -float(np.trapezoid(W * dtdT, Tp)) if hasattr(np, "trapezoid") else -float(np.trapz(W * dtdT, Tp))

    # pico de potência --------------------------------------------------------------------------
    # Na trajetória quase estática o ar já está abaixo do produto em t = 0⁺; nos primeiros minutos
    # (gabinete e produto encharcados à T_p0) o evaporador ainda vê ar mais quente. O pico reportado é o
    # máximo de W(T_a) entre o ar no fim do pull-down e T_p0: limite superior que inclui a partida e não
    # depende de hA (despreza a inércia térmica do evaporador e o transitório de pressões da partida).
    def chute(T_a):
        q = pts[int(np.argmin(np.abs(Ts - T_a)))]
        return (q.T_evap + (T_a + dTr - q.T_ar_evap) * 0.6, q.T_cond)

    TT = np.linspace(Ta[-1], T_p0, 400)
    WW = it["W_el"](TT)
    k = int(np.argmax(WW))
    if 0 < k < len(TT) - 1:
        opt = minimize_scalar(lambda T: -ponto(T, chute(T)).W_el, bounds=(TT[k - 1], TT[k + 1]), method="bounded",
                              options={"xatol": 1e-3})
        T_pico = float(opt.x)
    else:
        T_pico = float(TT[k])
    pico = ponto(T_pico, chute(T_pico))
    na_partida = T_pico > Ta[0]
    t_pico = 0.0 if na_partida else float(np.interp(-T_pico, -Ta, t))
    return ResultadoPulldown(T_amb, T_p0, T_f, C_p, hA, UA, Q_int, xi, concluido, float(t[-1]), T_eq, t, Tp, Ta,
                             it["T_evap"](Ta), it["T_cond"](Ta), it["Q_evap"](Ta), W, it["T_descarga"](Ta),
                             pico, t_pico, na_partida, float(np.max(W)), E_comp, {"T_ar": Ts, **arr})


__all__ = ["ParametrosOperacao", "ModeloSistema", "modelo_do_projeto", "PontoOperacao", "ponto_operacao",
           "ResultadoPulldown", "simular_pulldown"]
