"""Dimensionamento de condensador e evaporador tubo-aleta (aletas planas, tubos escalonados).

Método: zonas por fase (dessuperaquecimento / bifásico / sub-resfriamento no condensador;
bifásico / superaquecimento no evaporador), cada zona discretizada em segmentos ao longo do
circuito de refrigerante. Em cada segmento:

* propriedades locais do refrigerante (P e h locais, CoolProp);
* coeficiente interno local: Shah (2022) na condensação, Gungor-Winterton (1987) ou
  Liu-Winterton (1991) na ebulição (com secagem de parede acima de x_di), Gnielinski no
  monofásico;
* lado do ar: Wang et al. (2000) + eficiência de aleta de Schmidt; no evaporador, fator de
  umidade ξ = Q_total/Q_sens (analogia de Lewis) quando há remoção de umidade;
* UA por metro de tubo com resistências em série (ar, incrustação, parede, refrigerante);
* ε-NTU de escoamento cruzado (refrigerante misturado, ar não misturado); no bifásico
  C_r = 0 e ε = 1 − exp(−NTU);
* o ar que atravessa cada trecho entra na temperatura de entrada da serpentina, com vazão
  proporcional ao comprimento (distribuição paralela de ar, hipótese padrão dos modelos de
  fronteira móvel): Ċ_ar por metro = ρ V_face P_t c_p / N_fileiras. Assim o NTU global é
  consistente com o UA e a vazão de ar totais da serpentina;
* queda de pressão: atrito (Müller-Steinhagen & Heck no bifásico; Churchill no monofásico)
  + aceleração com fração de vazio de Rouhani-Axelsson; a pressão é atualizada ao longo do
  circuito e a temperatura de saturação acompanha.

O comprimento requerido é a soma dos segmentos; depois aplica-se a margem de área e o
arranjo é arredondado para tubos inteiros (fileiras × tubos por fileira × comprimento do passe).
Curvas de retorno (U) não entram na perda de carga (pequenas aos fluxos mássicos destes sistemas).

Modo de eficácia (``ParametrosTrocador.eficacia``)
--------------------------------------------------
A eficácia é a do lado do ar, referida à temperatura de saturação do refrigerante (definição usual de
condensadores e evaporadores, em que o refrigerante bifásico tem C → ∞ e C_min = Ċ_ar):

    ε = (T_ar,saída − T_ar,entrada) / (T_sat − T_ar,entrada) = Q_sens / [Ċ_ar (T_sat − T_ar,entrada)]

com T_sat = T_cond (entrada do condensador) ou T_evap (saída do evaporador) e Q_sens = Q/ξ.
Dados Q (do ciclo), ε e as temperaturas, a vazão de ar fica determinada (Ċ_ar = Q_sens/(ε ΔT)).
Na distribuição paralela de ar, ε depende só da velocidade de face V e do número de fileiras N
(e do coeficiente interno), e decresce monotonamente com V: para cada N resolve-se V tal que
ε(V, N) = ε_alvo; com ``fileiras_automaticas`` escolhe-se o N (≤ ``fileiras_max``) cuja V fica mais
perto da ``velocidade_face`` preferida. O comprimento de tubo sai da marcha segmentada nessa (V, N).
Também se reporta a eficácia "estrita" Q/Q_max com o Q_max termodinâmico (calores específicos
variáveis): Q_max = min[ṁ |h_ref,entrada − h(P, T_ar,entrada)|, ξ Ċ_ar |T_ref,entrada − T_ar,entrada|],
útil se o componente do Amesim usar essa definição.
"""
from __future__ import annotations

import copy
import dataclasses
import math
from dataclasses import dataclass, field
from typing import Optional

from scipy.optimize import brentq

from .avisos import ErroProjeto
from .correlacoes import bifasico as bf
from .correlacoes.lado_ar import (DesempenhoAr, GeometriaAletada, desempenho_lado_ar,
                                  queda_pressao_ar)
from .correlacoes.monofasico import gradiente_pressao_monofasico, h_interno_monofasico
from .propriedades import Fluido, ar_seco


@dataclass
class ParametrosTrocador:
    geometria: GeometriaAletada
    velocidade_face: float = 2.0           # m/s, na entrada
    n_circuitos: int = 1
    comprimento_passe_m: float = 0.40      # comprimento aletado de cada tubo (largura da face)
    margem_area: float = 0.10
    n_segmentos: int = 20                  # por zona
    R_incrustacao_ar: float = 0.0          # m²K/W, sobre a área externa (pó, geada)
    R_incrustacao_ref: float = 0.0         # m²K/W, sobre a área interna (óleo)
    correlacao_bifasico: str = "shah_2022"  # condensação: shah_2022|shah_2013|shah_2009|shah_1979|chato_1962
    #                                          ebulição: gungor_winterton_1987|liu_winterton_1991
    x_secagem: float = 0.90
    eficiencia_ventilador: float = 0.20    # elétrica total de ventiladores axiais pequenos
    # modo de eficácia: ε alvo referido à saturação; None -> velocidade_face fixa (geometria livre)
    eficacia: Optional[float] = None
    fileiras_automaticas: bool = True      # com ε: escolhe N ≤ fileiras_max com V mais perto de velocidade_face
    fileiras_max: int = 6                  # limite da base de dados de Wang et al. (2000)
    velocidade_min: float = 0.3            # m/s (Re_Dc ≈ 300–400, limite inferior de Wang)
    velocidade_max: float = 4.0            # m/s


def condensador_padrao() -> ParametrosTrocador:
    """Condensador de ar forçado típico de visi-cooler (tubo 3/8", 3 fileiras, ~10 FPI)."""
    return ParametrosTrocador(
        geometria=GeometriaAletada(Do=9.52e-3, esp_parede=0.35e-3, esp_aleta=0.12e-3, passo_aleta=2.5e-3,
                                   Pt=25.4e-3, Pl=22.0e-3, n_fileiras=3),
        velocidade_face=2.0, comprimento_passe_m=0.30, correlacao_bifasico="shah_2022")


def evaporador_padrao() -> ParametrosTrocador:
    """Evaporador de ar forçado para média temperatura com degelo natural (6 FPI, 4 fileiras)."""
    return ParametrosTrocador(
        geometria=GeometriaAletada(Do=9.52e-3, esp_parede=0.35e-3, esp_aleta=0.15e-3, passo_aleta=4.23e-3,
                                   Pt=25.4e-3, Pl=22.0e-3, n_fileiras=4),
        velocidade_face=1.5, comprimento_passe_m=0.35, correlacao_bifasico="gungor_winterton_1987")


@dataclass
class Segmento:
    zona: str
    L: float              # comprimento de tubo do segmento (por circuito) [m]
    Q: float              # calor do segmento (por circuito) [W]
    P_in: float
    P_out: float
    h_in: float
    h_out: float
    T_in: float
    T_out: float
    x_in: float
    x_out: float
    h_int: float          # coeficiente interno [W/m²K]
    UA_m: float           # UA por metro [W/mK]
    eps: float
    T_ar_out: float       # temperatura de bulbo seco do ar que deixa o trecho
    alpha: float          # fração de vazio média (0 no líquido, 1 no vapor)
    rho_media: float      # massa específica média in situ [kg/m³]
    dP_atrito: float
    dP_acel: float
    regime: str = ""


@dataclass
class ResultadoTrocador:
    tipo: str
    fluido: str
    m: float
    Q: float
    segmentos: list
    zonas: dict
    L_requerido: float        # total (todos os circuitos), sem margem
    L_adotado: float
    n_circuitos: int
    n_fileiras: int
    tubos_por_fileira: int
    n_tubos: int
    comprimento_passe: float
    altura_face: float
    area_face: float
    area_externa: float
    area_interna: float
    volume_interno: float
    n_aletas: int
    vazao_ar_m3h: float
    T_ar_in: float
    T_ar_out: float
    dP_ar: float
    potencia_ventilador_aero: float
    potencia_ventilador_est: float
    P_in: float
    P_out: float
    dT_sat_queda: float
    G_ref: float
    ar: DesempenhoAr
    fator_umidade: float
    geometria: GeometriaAletada
    UA_adotado: float = 0.0
    avisos: list = field(default_factory=list)
    velocidade_face: float = 0.0     # m/s (entrada; resolvida no modo de eficácia)
    T_sat_ref: float = 0.0           # temperatura de saturação de referência da eficácia [K]
    eficacia: float = 0.0            # obtida, referida à saturação (ver docstring do módulo)
    eficacia_alvo: Optional[float] = None
    eficacia_Qmax: float = 0.0       # Q / Q_max termodinâmico (ver _consolidar)
    C_ar: float = 0.0                # capacidade térmica sensível do ar na serpentina requerida [W/K]
    UA_requerido: float = 0.0        # Σ UA' L dos segmentos (sem margem) [W/K]
    NTU: float = 0.0                 # UA_requerido / (ξ C_ar)
    fileiras_escolhidas_automaticamente: bool = False
    vazao_ar_requerida_m3h: float = 0.0  # Ċ_ar/(ρ c_p) da serpentina requerida (a adotada é maior)

    @property
    def dP_ref(self) -> float:
        return self.P_in - self.P_out


# ============================================================================ utilidades
class _Ctx:
    def __init__(self, fl: Fluido, m: float, p: ParametrosTrocador, T_ar_in: float, T_ar_m: float,
                 xi: float = 1.0):
        self.fl, self.p, self.geo = fl, p, p.geometria
        g = self.geo
        self.m_c = m / p.n_circuitos
        self.A_cs = math.pi * g.Di ** 2 / 4.0
        self.G = self.m_c / self.A_cs
        self.Ao, self.Ai = g.area_externa_por_m, g.area_interna_por_m
        self.Rw = g.resistencia_parede_por_m()
        a_in, a_m = ar_seco(T_ar_in), ar_seco(T_ar_m)
        self.rho_ar_in = a_in.rho
        self.cp_ar = a_m.cp
        self.ar = desempenho_lado_ar(p.velocidade_face, a_in.rho, a_m.cp, a_m.mu, a_m.Pr, g, xi)
        self.xi = xi
        self.Ca_seco = a_in.rho * p.velocidade_face * g.Pt * a_m.cp / g.n_fileiras  # W/(K·m)
        self.Ca = xi * self.Ca_seco
        self.T_ar_in = T_ar_in
        self.M_kmol = fl.M * 1000.0
        self.hidrocarboneto = fl.hidrocarboneto

    def UA_m(self, h_i: float) -> float:
        R = (1.0 / (self.xi * self.ar.h * self.ar.eta_superficie * self.Ao)
             + self.p.R_incrustacao_ar / self.Ao + self.Rw
             + 1.0 / (h_i * self.Ai) + self.p.R_incrustacao_ref / self.Ai)
        return 1.0 / R


def _eps_cruzado(NTU: float, C_ref: float, C_ar: float) -> float:
    """ε de escoamento cruzado, refrigerante misturado e ar não misturado (Incropera Tab. 11.3)."""
    Cmin, Cmax = min(C_ref, C_ar), max(C_ref, C_ar)
    Cr = Cmin / Cmax
    if Cr < 1e-9:
        return 1.0 - math.exp(-NTU)
    if C_ref <= C_ar:   # C_min misturado (refrigerante), C_max não misturado
        return 1.0 - math.exp(-(1.0 - math.exp(-Cr * NTU)) / Cr)
    return (1.0 - math.exp(-Cr * (1.0 - math.exp(-NTU)))) / Cr   # C_max misturado


def _L_monofasico(Q: float, C_ref: float, UA_m: float, Ca_m: float, dT_in: float) -> float:
    """Comprimento que transfere Q num trecho monofásico (raiz de ε C_min ΔT_in = Q)."""
    if dT_in <= 0 or Q >= 0.999999 * C_ref * dT_in:
        raise ErroProjeto("trecho monofásico impossível: a variação de temperatura pedida ao refrigerante "
                          "excede a diferença para o ar (reduza sub-resfriamento/superaquecimento ou "
                          "aumente a diferença de temperatura do trocador).")

    def f(L):
        Ca = Ca_m * L
        Cmin = min(Ca, C_ref)
        return _eps_cruzado(UA_m * L / Cmin, C_ref, Ca) * Cmin * dT_in - Q

    lo, hi = 1e-9, max(Q / (Ca_m * dT_in), 1e-6) * 2.0
    while f(hi) < 0:
        hi *= 2.0
        if hi > 1e5:
            raise ErroProjeto("não convergiu o comprimento do trecho monofásico")
    return brentq(f, lo, hi, xtol=1e-9, rtol=1e-10)


def _segmento_monofasico(ctx: _Ctx, zona: str, P_in: float, h_in: float, h_out: float) -> Segmento:
    fl, g = ctx.fl, ctx.geo
    e_in = fl.estado_PH(P_in, h_in)
    dP = 0.0
    for _ in range(3):
        e_out = fl.estado_PH(P_in - dP, h_out)
        e_m = fl.estado_PH(P_in - 0.5 * dP, 0.5 * (h_in + h_out))
        Q = ctx.m_c * abs(h_in - h_out)
        dT_r = abs(e_in.T - e_out.T)
        C_ref = Q / dT_r if dT_r > 1e-9 else 1e12
        h_i = h_interno_monofasico(ctx.G, g.Di, e_m.mu, e_m.k, e_m.Pr)
        UA = ctx.UA_m(h_i)
        L = _L_monofasico(Q, C_ref, UA, ctx.Ca, abs(e_in.T - ctx.T_ar_in))
        dP_f = gradiente_pressao_monofasico(ctx.G, g.Di, e_m.rho, e_m.mu, g.rugosidade_int) * L
        dP_a = ctx.G ** 2 * (1.0 / e_out.rho - 1.0 / e_in.rho)
        dP = dP_f + dP_a
    Cmin = min(ctx.Ca * L, C_ref)
    eps = Q / (Cmin * abs(e_in.T - ctx.T_ar_in))
    sinal = 1.0 if e_in.T > ctx.T_ar_in else -1.0
    T_ar_out = ctx.T_ar_in + sinal * Q / (ctx.Ca * L)
    alpha = 1.0 if e_in.x >= 1.0 else 0.0
    return Segmento(zona, L, Q, P_in, P_in - dP, h_in, h_out, e_in.T, e_out.T, e_in.x, e_out.x, h_i, UA, eps,
                    T_ar_out, alpha, e_m.rho, dP_f, dP_a, "laminar" if ctx.G * g.Di / e_m.mu < 2300 else "turbulento")


def _h_bifasico(ctx: _Ctx, x_m: float, sat, q: float, condensando: bool) -> tuple[float, str]:
    p, D = ctx.p, ctx.geo.Di
    c = p.correlacao_bifasico
    if condensando:
        if c == "shah_2022":
            return bf.condensacao_shah_2022(ctx.G, x_m, D, sat, ctx.hidrocarboneto)
        if c == "shah_2013":
            return bf.condensacao_shah_2013(ctx.G, x_m, D, sat)
        if c == "shah_2009":
            return bf.condensacao_shah_2009(ctx.G, x_m, D, sat)
        if c == "shah_1979":
            return bf.condensacao_shah_1979(ctx.G, x_m, D, sat)
        if c == "chato_1962":
            h0 = bf.condensacao_shah_2013(ctx.G, x_m, D, sat)[0]
            h = h0
            for _ in range(30):   # ΔT_parede = q/h (forma implícita de Nusselt)
                h_novo, reg = bf.condensacao_chato_1962(D, sat, q / h)
                if abs(h_novo - h) < 1e-4 * h:
                    break
                h = h_novo
            return h_novo, reg
        raise ValueError(f"correlação de condensação desconhecida: {c}")
    h = bf.ebulicao_com_secagem(ctx.G, x_m, D, q, sat, ctx.M_kmol, c, p.x_secagem)
    return h, ("secagem" if x_m > p.x_secagem else "ebulição")


def _segmento_bifasico(ctx: _Ctx, zona: str, P_in: float, x_in: float, x_out: float,
                       condensando: bool) -> Segmento:
    fl, g = ctx.fl, ctx.geo
    sat_in = fl.sat(P_in)
    h_in = sat_in.hl + x_in * sat_in.hlv
    dP, q = 0.0, 5000.0
    for _ in range(4):
        P_out = P_in - dP
        sat_m, sat_out = fl.sat(P_in - 0.5 * dP), fl.sat(P_out)
        x_m = 0.5 * (x_in + x_out)
        h_out = sat_out.hl + x_out * sat_out.hlv
        Q = ctx.m_c * abs(h_in - h_out)
        dT = abs(sat_m.T - ctx.T_ar_in)
        for _k in range(30):   # ponto fixo no fluxo de calor (correlações dependentes de q)
            h_i, regime = _h_bifasico(ctx, x_m, sat_m, q, condensando)
            UA = ctx.UA_m(h_i)
            eps = 1.0 - math.exp(-UA / ctx.Ca)
            L = Q / (eps * ctx.Ca * dT)
            q_novo = Q / (ctx.Ai * L)
            conv = abs(q_novo - q) < 1e-4 * q
            q = q_novo
            if conv:
                break
        dP_f = bf.gradiente_atrito_msh(ctx.G, x_m, g.Di, sat_m) * L
        a_in = bf.fracao_vazio_rouhani_axelsson(x_in, ctx.G, sat_in)
        a_out = bf.fracao_vazio_rouhani_axelsson(x_out, ctx.G, sat_out)
        dP_a = ctx.G ** 2 * (bf.fluxo_momento_especifico(x_out, a_out, sat_out)
                             - bf.fluxo_momento_especifico(x_in, a_in, sat_in))
        dP = dP_f + dP_a
    alpha = 0.5 * (a_in + a_out)
    rho_m = 0.5 * (a_in * sat_in.rhov + (1 - a_in) * sat_in.rhol + a_out * sat_out.rhov + (1 - a_out) * sat_out.rhol)
    sinal = 1.0 if sat_m.T > ctx.T_ar_in else -1.0
    T_ar_out = ctx.T_ar_in + sinal * Q / (ctx.Ca * L)
    return Segmento(zona, L, Q, P_in, P_in - dP, h_in, h_out, sat_in.T, sat_out.T, x_in, x_out, h_i, UA, eps,
                    T_ar_out, alpha, rho_m, dP_f, dP_a, regime)


def _consolidar(tipo: str, fl: Fluido, m: float, segs: list, ctx: _Ctx, p: ParametrosTrocador,
                T_ar_in: float, T_sat_ref: float) -> ResultadoTrocador:
    g = p.geometria
    Nc = p.n_circuitos
    zonas: dict = {}
    for s in segs:
        z = zonas.setdefault(s.zona, {"L": 0.0, "Q": 0.0})
        z["L"] += s.L * Nc
        z["Q"] += s.Q * Nc
    L_req = sum(s.L for s in segs) * Nc
    Q = sum(s.Q for s in segs) * Nc
    L_proj = L_req * (1.0 + p.margem_area)
    n_tubos = math.ceil(L_proj / p.comprimento_passe_m - 1e-9)
    tpf = math.ceil(n_tubos / g.n_fileiras)
    while (tpf * g.n_fileiras) % Nc:
        tpf += 1
    n_tubos = tpf * g.n_fileiras
    L_adot = n_tubos * p.comprimento_passe_m
    altura = tpf * g.Pt
    A_face = altura * p.comprimento_passe_m
    Vdot = p.velocidade_face * A_face
    # temperatura média de mistura do ar na saída (ponderada pela capacidade de cada trecho)
    T_out = sum(s.T_ar_out * s.L for s in segs) / sum(s.L for s in segs)
    rho_out = ar_seco(T_out).rho
    dP_ar = queda_pressao_ar(ctx.ar.G_max, ctx.ar.f, g, ctx.rho_ar_in, rho_out)
    P_in, P_out = segs[0].P_in, segs[-1].P_out
    dTsat = abs(fl.Tsat(P_in) - fl.Tsat(P_out))
    av = list(g.verificar_faixa_wang())
    if not 100 <= ctx.ar.Re_Dc <= 20000:
        av.append(f"Re_Dc do ar = {ctx.ar.Re_Dc:.0f} fora da faixa usual da correlação de Wang")
    if dTsat > 1.5:
        av.append(f"queda de pressão do refrigerante equivale a {dTsat:.2f} K de saturação: considere mais circuitos")
    UA_req = sum(s.UA_m * s.L for s in segs) * Nc
    UA_adot = UA_req / L_req * L_adot
    C_ar = ctx.Ca_seco * L_req                       # sensível, serpentina requerida
    eps = abs(T_out - T_ar_in) / abs(T_sat_ref - T_ar_in)
    # eficácia "estrita" com o Q_max termodinâmico (calores específicos variáveis, Shah & Sekulic 2003):
    # refrigerante levado à temperatura de entrada do ar, ou ar levado à temperatura de entrada do refrigerante
    T_ref_in = segs[0].T_in
    h_ref_lim = fl.estado_PT(P_out, T_ar_in).h
    Qmax_ref = m * abs(segs[0].h_in - h_ref_lim)
    Qmax_ar = ctx.xi * C_ar * abs(T_ref_in - T_ar_in)
    eps_Qmax = Q / min(Qmax_ref, Qmax_ar)
    return ResultadoTrocador(
        tipo, fl.nome, m, Q, segs, zonas, L_req, L_adot, Nc, g.n_fileiras, tpf, n_tubos, p.comprimento_passe_m,
        altura, A_face, g.area_externa_por_m * L_adot, g.area_interna_por_m * L_adot,
        math.pi * g.Di ** 2 / 4.0 * L_adot, int(p.comprimento_passe_m / g.passo_aleta), Vdot * 3600.0,
        T_ar_in, T_out, dP_ar, Vdot * dP_ar, Vdot * dP_ar / p.eficiencia_ventilador, P_in, P_out, dTsat,
        ctx.G, ctx.ar, ctx.xi, g, UA_adot, av, p.velocidade_face, T_sat_ref, eps, p.eficacia, eps_Qmax, C_ar,
        UA_req, UA_req / (ctx.xi * C_ar), False, C_ar / (ctx.rho_ar_in * ctx.cp_ar) * 3600.0)


# ============================================================================ condensador
def _condensador_fixo(fl: Fluido, m: float, P_in: float, h_in: float, subresfriamento: float,
                      T_ar_in: float, p: ParametrosTrocador) -> ResultadoTrocador:
    """Marcha do condensador para geometria e velocidade de face fixas."""
    n = p.n_segmentos
    T_ar_m = T_ar_in + 5.0
    for _ in range(3):   # propriedades do ar na temperatura média
        ctx = _Ctx(fl, m, p, T_ar_in, T_ar_m)
        segs: list = []
        P, h = P_in, h_in
        sat = fl.sat(P)
        if h > sat.hv:   # dessuperaquecimento
            for k in range(1, n + 1):
                h_t = h_in + (sat.hv - h_in) * k / n
                s = _segmento_monofasico(ctx, "dessuperaquecimento", P, h, h_t)
                segs.append(s)
                P, h = s.P_out, s.h_out
        sat = fl.sat(P)
        x0 = min((h - sat.hl) / sat.hlv, 1.0)
        for k in range(n):   # condensação
            x_a = x0 * (1.0 - k / n)
            x_b = x0 * (1.0 - (k + 1) / n)
            s = _segmento_bifasico(ctx, "condensação", P, x_a, x_b, True)
            segs.append(s)
            P = s.P_out
        h = fl.sat(P).hl
        if subresfriamento > 0:
            T_sat = fl.Tsat(P)
            h_fim = fl.estado_PT(P, T_sat - subresfriamento).h
            for k in range(1, n + 1):
                h_t = h + (h_fim - h) * k / n if k < n else h_fim
                h_a = segs[-1].h_out if segs[-1].zona == "sub-resfriamento" else h
                s = _segmento_monofasico(ctx, "sub-resfriamento", P, h_a, h_t)
                segs.append(s)
                P = s.P_out
        T_out_mix = sum(s.T_ar_out * s.L for s in segs) / sum(s.L for s in segs)
        T_novo = 0.5 * (T_ar_in + T_out_mix)
        if abs(T_novo - T_ar_m) < 0.05:
            break
        T_ar_m = T_novo
    return _consolidar("condensador", fl, m, segs, ctx, p, T_ar_in, fl.Tsat(P_in))


# ============================================================================ evaporador
def _evaporador_fixo(fl: Fluido, m: float, h_in: float, P_out_alvo: float, superaquecimento: float,
                     T_ar_in: float, p: ParametrosTrocador, fator_umidade: float = 1.0) -> ResultadoTrocador:
    """Marcha do evaporador para geometria e velocidade de face fixas. A pressão de entrada
    (= saída do capilar) é obtida iterando a queda de pressão."""
    n = p.n_segmentos
    T_sat_out = fl.Tsat(P_out_alvo)
    h_fim = fl.estado_PT(P_out_alvo, T_sat_out + superaquecimento).h if superaquecimento > 0 else fl.sat(P_out_alvo).hv
    dP_tot = 0.0
    T_ar_m = T_ar_in - 2.0
    for _ in range(12):
        ctx = _Ctx(fl, m, p, T_ar_in, T_ar_m, fator_umidade)
        P = P_out_alvo + dP_tot
        sat = fl.sat(P)
        x_in = (h_in - sat.hl) / sat.hlv
        if not 0.0 < x_in < 1.0:
            raise ErroProjeto(f"título na entrada do evaporador fora de (0,1): {x_in:.3f}")
        segs: list = []
        for k in range(n):
            x_a = x_in + (1.0 - x_in) * k / n
            x_b = x_in + (1.0 - x_in) * (k + 1) / n
            s = _segmento_bifasico(ctx, "evaporação", P, x_a, x_b, False)
            segs.append(s)
            P = s.P_out
        if superaquecimento > 0:
            h = fl.sat(P).hv
            for k in range(1, n + 1):
                h_t = h + (h_fim - h) * k / n
                h_a = segs[-1].h_out if segs[-1].zona == "superaquecimento" else h
                s = _segmento_monofasico(ctx, "superaquecimento", P, h_a, h_t)
                segs.append(s)
                P = s.P_out
        erro = P - P_out_alvo
        T_out_mix = sum(s.T_ar_out * s.L for s in segs) / sum(s.L for s in segs)
        T_ar_m = 0.5 * (T_ar_in + T_out_mix)
        dP_tot = segs[0].P_in - segs[-1].P_out
        if abs(erro) < 1.0:
            break
    return _consolidar("evaporador", fl, m, segs, ctx, p, T_ar_in, T_sat_out)


# ============================================================================ modo de eficácia
def _com(p: ParametrosTrocador, N: int, V: float) -> ParametrosTrocador:
    pp = copy.copy(p)
    pp.geometria = dataclasses.replace(p.geometria, n_fileiras=int(N))
    pp.velocidade_face = float(V)
    return pp


class _Solucionador:
    """Resolve a velocidade de face (e, se pedido, o nº de fileiras) para uma eficácia alvo."""

    def __init__(self, rodar, p: ParametrosTrocador, tipo: str):
        if not 0.0 < p.eficacia < 1.0:
            raise ErroProjeto(f"eficácia do {tipo} deve estar entre 0 e 1 (recebido {p.eficacia}).")
        self.rodar, self.p, self.tipo, self.alvo = rodar, p, tipo, p.eficacia
        self._cache: dict = {}

    def resultado(self, N: int, V: float) -> ResultadoTrocador:
        k = (int(N), round(V, 7))
        if k not in self._cache:
            self._cache[k] = self.rodar(_com(self.p, N, V))
        return self._cache[k]

    def eps(self, N: int, V: float) -> float:
        return self.resultado(N, V).eficacia

    def velocidade(self, N: int, V_dica: Optional[float] = None) -> Optional[float]:
        """V tal que ε(V, N) = ε_alvo, ou None se o alvo é inatingível com N fileiras na faixa de V."""
        p = self.p
        f = (lambda V: self.eps(N, V) - self.alvo)
        lo, hi = p.velocidade_min, p.velocidade_max
        if V_dica is not None:   # intervalo estreito em torno da solução anterior (iterações do ciclo)
            a, b = max(lo, 0.85 * V_dica), min(hi, 1.15 * V_dica)
            if a < b and f(a) >= 0.0 >= f(b):
                return brentq(f, a, b, xtol=1e-4, rtol=1e-6)
        if f(lo) < 0.0 or f(hi) > 0.0:
            return None
        return brentq(f, lo, hi, xtol=1e-4, rtol=1e-6)

    def resolver(self, dica: Optional[tuple] = None) -> ResultadoTrocador:
        p = self.p
        if not p.fileiras_automaticas:
            N = p.geometria.n_fileiras
            V = self.velocidade(N, dica[1] if dica and dica[0] == N else None)
            if V is None:
                raise ErroProjeto(self._mensagem_inviavel([N]))
            return self._final(N, V, False)
        if dica is not None and 1 <= dica[0] <= p.fileiras_max:
            V = self.velocidade(dica[0], dica[1])
            if V is not None:
                return self._final(dica[0], V, True)
        Vp = min(max(p.velocidade_face, p.velocidade_min), p.velocidade_max)
        Ns = list(range(1, p.fileiras_max + 1))
        N_alto = next((N for N in Ns if self.eps(N, Vp) >= self.alvo), None)   # ε cresce com N
        cand = [Ns[-1]] if N_alto is None else [N_alto] + ([N_alto - 1] if N_alto > 1 else [])
        sols = [(N, V) for N in cand if (V := self.velocidade(N)) is not None]
        if not sols:
            raise ErroProjeto(self._mensagem_inviavel(Ns))
        N, V = min(sols, key=lambda s: abs(math.log(s[1] / Vp)))
        return self._final(N, V, True)

    def _final(self, N: int, V: float, auto: bool) -> ResultadoTrocador:
        r = self.rodar(_com(self.p, N, V))
        r.fileiras_escolhidas_automaticamente = auto
        if abs(r.eficacia - self.alvo) > 2e-3:
            r.avisos.append(f"eficácia obtida {r.eficacia:.3f} difere do alvo {self.alvo:.3f}")
        return r

    def _mensagem_inviavel(self, Ns: list) -> str:
        p = self.p
        N = max(Ns)
        e_max = self.eps(N, p.velocidade_min)
        return (f"eficácia {self.alvo:.2f} inatingível no {self.tipo} com até {N} fileira(s): o máximo é "
                f"{e_max:.2f} a {p.velocidade_min} m/s. Reduza a eficácia, aumente fileiras_max, diminua o passo "
                "de aleta ou use mais área por fileira (o lado do refrigerante limita o NTU a fluxos mássicos baixos).")


def dimensionar_condensador(fl: Fluido, m: float, P_in: float, h_in: float, subresfriamento: float,
                            T_ar_in: float, p: ParametrosTrocador, dica: Optional[tuple] = None) -> ResultadoTrocador:
    """Comprimento de tubo para levar o vapor de descarga (P_in, h_in) a líquido sub-resfriado.
    Com ``p.eficacia`` definido, resolve velocidade de face e fileiras para essa eficácia
    (``dica`` = (N, V) de uma solução anterior acelera as iterações do ciclo)."""
    def rodar(pp):
        return _condensador_fixo(fl, m, P_in, h_in, subresfriamento, T_ar_in, pp)
    if p.eficacia is None:
        return rodar(p)
    return _Solucionador(rodar, p, "condensador").resolver(dica)


def dimensionar_evaporador(fl: Fluido, m: float, h_in: float, P_out_alvo: float, superaquecimento: float,
                           T_ar_in: float, p: ParametrosTrocador, fator_umidade: float = 1.0,
                           dica: Optional[tuple] = None) -> ResultadoTrocador:
    """Comprimento de tubo do evaporador: entrada (h_in, pressão a determinar), saída na pressão
    de sucção ``P_out_alvo`` com o superaquecimento pedido. Com ``p.eficacia`` definido, resolve
    velocidade de face e fileiras para essa eficácia."""
    def rodar(pp):
        return _evaporador_fixo(fl, m, h_in, P_out_alvo, superaquecimento, T_ar_in, pp, fator_umidade)
    if p.eficacia is None:
        return rodar(p)
    return _Solucionador(rodar, p, "evaporador").resolver(dica)


def alternativas_fileiras(rodar_fixo, p: ParametrosTrocador, fileiras=range(1, 7)) -> list[dict]:
    """Para a eficácia alvo de ``p``, a solução (V, comprimento, vazão de ar, ΔP do ar) de cada nº de
    fileiras — o compromisso área × ventilador que o projetista escolhe."""
    sol = _Solucionador(rodar_fixo, p, "trocador")
    linhas = []
    for N in fileiras:
        V = sol.velocidade(N)
        if V is None:
            linhas.append({"fileiras": N, "viavel": False, "eficacia_max": sol.eps(N, p.velocidade_min)})
            continue
        r = sol.rodar(_com(p, N, V))
        linhas.append({"fileiras": N, "viavel": True, "velocidade_face_m_s": V, "L_requerido_m": r.L_requerido,
                       "L_adotado_m": r.L_adotado, "tubos_por_fileira": r.tubos_por_fileira,
                       "altura_face_m": r.altura_face, "area_externa_m2": r.area_externa,
                       "vazao_ar_requerida_m3_h": r.vazao_ar_requerida_m3h, "vazao_ar_face_adotada_m3_h": r.vazao_ar_m3h,
                       "dP_ar_Pa": r.dP_ar,
                       "potencia_ventilador_W": r.potencia_ventilador_est, "Re_Dc": r.ar.Re_Dc})
    return linhas
