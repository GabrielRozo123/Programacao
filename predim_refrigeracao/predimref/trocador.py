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
  circuito e a temperatura de saturação acompanha. A diferença de temperatura refrigerante-ar
  é verificada com sinal em cada trecho: se a queda de pressão levar a saturação para o "lado
  errado" do ar (pinch), o ponto é rejeitado em vez de produzir calor no sentido contrário.

Duas serpentinas são reportadas:
* **de projeto (sem margem)** — o comprimento requerido; com a vazão de ar requerida ela entrega
  exatamente a capacidade e as temperaturas do ciclo (é a que reproduz ``alvo_validacao``);
* **construtiva (com margem)** — comprimento × (1 + margem_area), com o mesmo nº de fileiras,
  tubos por fileira inteiros e o comprimento do passe ajustado (padrão) ou com tubos inteiros
  num passe fixo. Na mesma velocidade de face ela tem a mesma ε, porém mais vazão de ar e mais
  UA: num modelo de sistema ela condensa abaixo de T_cond e evapora acima de T_evap (é a folga).
Curvas de retorno (U) não entram na perda de carga (pequenas aos fluxos mássicos destes sistemas).

Modo de eficácia (``ParametrosTrocador.eficacia``)
--------------------------------------------------
A eficácia é a do lado do ar, referida à temperatura de saturação do refrigerante (definição usual de
condensadores e evaporadores, em que o refrigerante bifásico tem C → ∞ e C_min = Ċ_ar):

    ε = (T_ar,saída − T_ar,entrada) / (T_sat − T_ar,entrada) = Q_sens / [Ċ_ar (T_sat − T_ar,entrada)]

com T_sat = T_cond (entrada do condensador) ou T_evap (saída do evaporador) e Q_sens = Q/ξ.
Dados Q (do ciclo), ε e as temperaturas, a vazão de ar fica determinada (Ċ_ar = Q_sens/(ε ΔT)).
Na distribuição paralela de ar, ε independe do comprimento: depende da velocidade de face V, do nº
de fileiras N, do coeficiente interno e, no condensador, também da temperatura de descarga (o ar
que passa pelo dessuperaquecimento sai acima de T_sat; por isso no condensador ε não segue
1 − e^(−NTU) e, a velocidades muito baixas, pode até passar de 1). Na zona bifásica vale
ε_zona ≤ 1 − e^(−NTU_zona) (desigualdade de Jensen) e os valores por zona são exportados.
Com perda de carga relevante ε(V) pode deixar de ser monotônica; por isso, para cada N, a busca de V
percorre uma grade logarítmica de velocidade_max para velocidade_min, refina por Brent a primeira
troca de sinal encontrada e adota essa raiz, a de maior V (menos tubo e menos perda de carga). Com ``fileiras_automaticas`` escolhe-se
o N (≤ ``fileiras_max``) cuja V fica mais perto da ``velocidade_face`` preferida.
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

import numpy as np
from scipy.optimize import brentq

from .avisos import ErroProjeto
from .correlacoes import bifasico as bf
from .correlacoes.lado_ar import (DesempenhoAr, GeometriaAletada, desempenho_lado_ar,
                                  queda_pressao_ar)
from .correlacoes.monofasico import gradiente_pressao_monofasico, h_interno_monofasico
from .propriedades import Fluido, ar_seco

class ErroPerdaCarga(ErroProjeto):
    """Inviabilidade causada pela perda de carga do refrigerante (pinch ou queda excessiva):
    resolvida com mais circuitos ou tubo de maior diâmetro."""


FOLGA_PINCH_K = 0.2          # diferença mínima refrigerante-ar aceita num trecho [K]
FRACAO_DP_MAX = 0.5          # queda de pressão máxima admitida, fração da pressão de entrada
N_GRADE_VELOCIDADE = 10      # pontos da grade logarítmica de V no modo de eficácia


@dataclass
class ParametrosTrocador:
    geometria: GeometriaAletada
    velocidade_face: float = 2.0           # m/s, na entrada (preferida, no modo de eficácia)
    n_circuitos: int = 1
    comprimento_passe_m: float = 0.40      # comprimento aletado de cada tubo (largura da face)
    ajustar_comprimento_passe: bool = True  # serpentina construtiva com L = L_req (1 + margem) exato
    margem_area: float = 0.10
    n_segmentos: int = 40                  # por zona bifásica (≤ 0,15 % de diferença para 240)
    n_segmentos_monofasico: int = 8        # por zona monofásica (perfis suaves: converge com poucos)
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
    circuitos_automaticos: bool = True     # se a perda de carga impedir o projeto, tenta n_circuitos + 1
    circuitos_max: int = 4


def condensador_padrao() -> ParametrosTrocador:
    """Condensador de ar forçado típico de visi-cooler (tubo 3/8", aleta 2,5 mm ≈ 10 FPI)."""
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
    UA_m: float           # UA por metro [W/mK] (no evaporador, base úmida: ξ no filme de ar e na aleta)
    eps: float
    T_ar_out: float       # temperatura de bulbo seco do ar que deixa o trecho
    alpha: float          # fração de vazio média (0 no líquido, 1 no vapor)
    rho_media: float      # massa específica média in situ [kg/m³]
    dP_atrito: float
    dP_acel: float
    regime: str = ""
    UA_m_seco: float = 0.0  # UA por metro com ξ = 1 (superfície seca)


@dataclass
class Serpentina:
    """Uma realização geométrica da serpentina (de projeto ou construtiva)."""
    descricao: str
    comprimento_tubo: float      # total, todos os circuitos [m]
    comprimento_passe: float     # comprimento aletado de cada tubo [m]
    tubos_por_fileira: int
    n_tubos: int
    altura_face: float
    area_face: float
    area_externa: float
    area_interna: float
    volume_interno: float
    n_aletas: int
    vazao_ar_m3h: float          # na velocidade de face de projeto
    UA: float                    # base úmida no evaporador (ver Segmento.UA_m)
    UA_seco: float


@dataclass
class ResultadoTrocador:
    tipo: str
    fluido: str
    m: float
    Q: float
    segmentos: list
    zonas: dict
    projeto: Serpentina          # sem margem: reproduz o ponto de projeto do ciclo
    construtiva: Serpentina      # com margem e tubos inteiros
    n_circuitos: int
    n_fileiras: int
    T_ar_in: float
    T_ar_out: float              # serpentina de projeto, vazão requerida
    dP_ar: float                 # depende só de V e N (igual nas duas serpentinas)
    potencia_ventilador_aero: float   # serpentina construtiva
    potencia_ventilador_est: float    # serpentina construtiva
    P_in: float
    P_out: float
    dT_sat_queda: float
    G_ref: float
    ar: DesempenhoAr
    fator_umidade: float
    geometria: GeometriaAletada
    velocidade_face: float
    T_sat_ref: float             # temperatura de saturação de referência da eficácia [K]
    eficacia: float              # obtida, referida à saturação (ver docstring do módulo)
    eficacia_alvo: Optional[float]
    eficacia_Qmax: float         # Q / Q_max termodinâmico
    C_ar: float                  # capacidade térmica sensível do ar na serpentina de projeto [W/K]
    NTU: float                   # UA_projeto / (ξ C_ar)
    avisos: list = field(default_factory=list)
    fileiras_escolhidas_automaticamente: bool = False
    ar_seco: Optional[DesempenhoAr] = None   # lado do ar com ξ = 1 (coeficiente sensível)

    # ----------------------------------------------------- atalhos (serpentina construtiva)
    @property
    def dP_ref(self) -> float:
        return self.P_in - self.P_out

    @property
    def L_requerido(self) -> float:
        return self.projeto.comprimento_tubo

    @property
    def L_adotado(self) -> float:
        return self.construtiva.comprimento_tubo

    @property
    def UA_requerido(self) -> float:
        return self.projeto.UA

    @property
    def UA_adotado(self) -> float:
        return self.construtiva.UA

    @property
    def vazao_ar_requerida_m3h(self) -> float:
        return self.projeto.vazao_ar_m3h

    @property
    def vazao_ar_m3h(self) -> float:
        return self.construtiva.vazao_ar_m3h

    @property
    def tubos_por_fileira(self) -> int:
        return self.construtiva.tubos_por_fileira

    @property
    def n_tubos(self) -> int:
        return self.construtiva.n_tubos

    @property
    def comprimento_passe(self) -> float:
        return self.construtiva.comprimento_passe

    @property
    def altura_face(self) -> float:
        return self.construtiva.altura_face

    @property
    def area_face(self) -> float:
        return self.construtiva.area_face

    @property
    def area_externa(self) -> float:
        return self.construtiva.area_externa

    @property
    def area_interna(self) -> float:
        return self.construtiva.area_interna

    @property
    def volume_interno(self) -> float:
        return self.construtiva.volume_interno

    @property
    def n_aletas(self) -> int:
        return self.construtiva.n_aletas


# ============================================================================ utilidades
class _Ctx:
    def __init__(self, fl: Fluido, m: float, p: ParametrosTrocador, T_ar_in: float, T_ar_m: float,
                 xi: float, sentido: float):
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
        self.ar_seco = (self.ar if xi == 1.0 else
                        desempenho_lado_ar(p.velocidade_face, a_in.rho, a_m.cp, a_m.mu, a_m.Pr, g, 1.0))
        self.xi = xi
        self.Ca_seco = a_in.rho * p.velocidade_face * g.Pt * a_m.cp / g.n_fileiras  # W/(K·m)
        self.Ca = xi * self.Ca_seco
        self.T_ar_in = T_ar_in
        self.sentido = sentido          # +1: refrigerante mais quente que o ar (condensador); −1: evaporador
        self.M_kmol = fl.M * 1000.0
        self.hidrocarboneto = fl.hidrocarboneto

    def _UA(self, h_i: float, h_ar_eq: float, eta_o: float) -> float:
        R = (1.0 / (h_ar_eq * eta_o * self.Ao) + self.p.R_incrustacao_ar / self.Ao + self.Rw
             + 1.0 / (h_i * self.Ai) + self.p.R_incrustacao_ref / self.Ai)
        return 1.0 / R

    def UA_m(self, h_i: float) -> float:
        """UA por metro na base úmida (ξ no filme de ar e na eficiência de aleta)."""
        return self._UA(h_i, self.xi * self.ar.h, self.ar.eta_superficie)

    def UA_m_seco(self, h_i: float) -> float:
        return self._UA(h_i, self.ar_seco.h, self.ar_seco.eta_superficie)

    def dT_motriz(self, T_ref: float, zona: str) -> float:
        """Diferença refrigerante-ar no sentido esperado; rejeita pinch (inclusive o causado pela
        queda de pressão, que leva a saturação para o lado errado do ar)."""
        dT = self.sentido * (T_ref - self.T_ar_in)
        if dT <= FOLGA_PINCH_K:
            raise ErroPerdaCarga(f"pinch no {zona}: diferença refrigerante-ar de {dT:.2f} K "
                              "(perda de carga alta demais? aumente n_circuitos ou o diâmetro do tubo)")
        return dT


def _checar_pressao(P_entrada: float, P: float, zona: str) -> None:
    if not (P > (1.0 - FRACAO_DP_MAX) * P_entrada) or not math.isfinite(P):
        raise ErroPerdaCarga(f"queda de pressão excessiva no {zona} (> {FRACAO_DP_MAX:.0%} da pressão de entrada): "
                          "aumente n_circuitos ou o diâmetro do tubo")


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
    e_in = fl.estado_PH(P_in, h_in, transporte=False)
    dT_in = ctx.dT_motriz(e_in.T, zona)
    dP = 0.0
    for it in range(4):
        _checar_pressao(P_in, P_in - dP, zona)
        e_out = fl.estado_PH(P_in - dP, h_out, transporte=False)
        e_m = fl.estado_PH(P_in - 0.5 * dP, 0.5 * (h_in + h_out))
        if e_m.mu is None:
            raise ErroPerdaCarga(f"estado médio bifásico num trecho de {zona} (queda de pressão excessiva)")
        Q = ctx.m_c * abs(h_in - h_out)
        dT_r = abs(e_in.T - e_out.T)
        C_ref = Q / dT_r if dT_r > 1e-9 else 1e12
        h_i = h_interno_monofasico(ctx.G, g.Di, e_m.mu, e_m.k, e_m.Pr)
        UA = ctx.UA_m(h_i)
        L = _L_monofasico(Q, C_ref, UA, ctx.Ca, dT_in)
        dP_f = gradiente_pressao_monofasico(ctx.G, g.Di, e_m.rho, e_m.mu, g.rugosidade_int) * L
        dP_a = ctx.G ** 2 * (1.0 / e_out.rho - 1.0 / e_in.rho)
        dP_novo = dP_f + dP_a
        conv = abs(dP_novo - dP) <= 1e-6 * P_in + 1e-3 * abs(dP_novo)
        dP = dP_novo
        if conv and it > 0:
            break
    _checar_pressao(P_in, P_in - dP, zona)
    Cmin = min(ctx.Ca * L, C_ref)
    eps = Q / (Cmin * dT_in)
    T_ar_out = ctx.T_ar_in + ctx.sentido * Q / (ctx.Ca * L)
    alpha = 1.0 if e_in.x >= 1.0 else 0.0
    return Segmento(zona, L, Q, P_in, P_in - dP, h_in, h_out, e_in.T, e_out.T, e_in.x, e_out.x, h_i, UA, eps,
                    T_ar_out, alpha, e_m.rho, dP_f, dP_a,
                    "laminar" if ctx.G * g.Di / e_m.mu < 2300 else "turbulento", ctx.UA_m_seco(h_i))


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
    ctx.dT_motriz(sat_in.T, zona)
    h_in = sat_in.hl + x_in * sat_in.hlv
    dP, q = 0.0, 5000.0
    for _ in range(6):
        _checar_pressao(P_in, P_in - dP, zona)
        P_out = P_in - dP
        sat_m, sat_out = fl.sat(P_in - 0.5 * dP), fl.sat(P_out)
        x_m = 0.5 * (x_in + x_out)
        h_out = sat_out.hl + x_out * sat_out.hlv
        Q = ctx.m_c * abs(h_in - h_out)
        dT = ctx.dT_motriz(sat_m.T, zona)
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
        dP_novo = dP_f + dP_a
        conv = abs(dP_novo - dP) <= 1e-6 * P_in + 1e-3 * abs(dP_novo)
        dP = dP_novo
        if conv:
            break
    _checar_pressao(P_in, P_in - dP, zona)
    ctx.dT_motriz(fl.sat(P_in - dP).T, zona)   # a saturação na saída do trecho também precisa de folga
    alpha = 0.5 * (a_in + a_out)
    rho_m = 0.5 * (a_in * sat_in.rhov + (1 - a_in) * sat_in.rhol + a_out * sat_out.rhov + (1 - a_out) * sat_out.rhol)
    T_ar_out = ctx.T_ar_in + ctx.sentido * Q / (ctx.Ca * L)
    return Segmento(zona, L, Q, P_in, P_in - dP, h_in, h_out, sat_in.T, sat_out.T, x_in, x_out, h_i, UA, eps,
                    T_ar_out, alpha, rho_m, dP_f, dP_a, regime, ctx.UA_m_seco(h_i))


def _serpentina(descricao: str, L_total: float, N: int, Nc: int, p: ParametrosTrocador, UA_m_medio: float,
                UA_m_seco_medio: float, ajustar: bool) -> Serpentina:
    """Arranjo de tubos inteiros para um comprimento total de tubo."""
    g = p.geometria
    if ajustar:
        tpf = max(1, math.ceil(L_total / (N * p.comprimento_passe_m) - 1e-9))
        while (tpf * N) % Nc:
            tpf += 1
        L_passe = L_total / (N * tpf)
    else:
        tpf = max(1, math.ceil(math.ceil(L_total / p.comprimento_passe_m - 1e-9) / N))
        while (tpf * N) % Nc:
            tpf += 1
        L_passe = p.comprimento_passe_m
    n_tubos = tpf * N
    L = n_tubos * L_passe
    altura = tpf * g.Pt
    A_face = altura * L_passe
    return Serpentina(descricao, L, L_passe, tpf, n_tubos, altura, A_face, g.area_externa_por_m * L,
                      g.area_interna_por_m * L, math.pi * g.Di ** 2 / 4.0 * L, int(L_passe / g.passo_aleta),
                      p.velocidade_face * A_face * 3600.0, UA_m_medio * L, UA_m_seco_medio * L)


def _consolidar(tipo: str, fl: Fluido, m: float, segs: list, ctx: _Ctx, p: ParametrosTrocador,
                T_ar_in: float, T_sat_ref: float) -> ResultadoTrocador:
    g = p.geometria
    Nc = p.n_circuitos
    N = g.n_fileiras
    zonas: dict = {}
    for s in segs:
        z = zonas.setdefault(s.zona, {"L": 0.0, "Q": 0.0, "UA": 0.0, "UA_seco": 0.0})
        z["L"] += s.L * Nc
        z["Q"] += s.Q * Nc
        z["UA"] += s.UA_m * s.L * Nc
        z["UA_seco"] += s.UA_m_seco * s.L * Nc
    for z in zonas.values():
        C_z = ctx.Ca_seco * z["L"]
        z["eficacia"] = z["Q"] / (ctx.xi * C_z * abs(T_sat_ref - T_ar_in))
        z["NTU"] = z["UA"] / (ctx.xi * C_z)
    L_req = sum(s.L for s in segs) * Nc
    Q = sum(s.Q for s in segs) * Nc
    UA_req = sum(s.UA_m * s.L for s in segs) * Nc
    UA_seco_req = sum(s.UA_m_seco * s.L for s in segs) * Nc
    UA_m, UA_m_s = UA_req / L_req, UA_seco_req / L_req
    # serpentina de projeto (sem margem): comprimento exato, passe ajustado ao arranjo da construtiva
    construtiva = _serpentina("construtiva (com margem)", L_req * (1.0 + p.margem_area), N, Nc, p, UA_m, UA_m_s,
                              p.ajustar_comprimento_passe)
    proj = Serpentina("projeto (sem margem)", L_req, L_req / (N * construtiva.tubos_por_fileira),
                      construtiva.tubos_por_fileira, construtiva.n_tubos, construtiva.altura_face,
                      construtiva.altura_face * L_req / (N * construtiva.tubos_por_fileira),
                      g.area_externa_por_m * L_req, g.area_interna_por_m * L_req,
                      math.pi * g.Di ** 2 / 4.0 * L_req,
                      int(L_req / (N * construtiva.tubos_por_fileira) / g.passo_aleta),
                      ctx.Ca_seco * L_req / (ctx.rho_ar_in * ctx.cp_ar) * 3600.0, UA_req, UA_seco_req)
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
    C_ar = ctx.Ca_seco * L_req                       # sensível, serpentina de projeto
    eps = abs(T_out - T_ar_in) / abs(T_sat_ref - T_ar_in)
    if eps > 1.0:
        av.append(f"eficácia referida à saturação = {eps:.3f} > 1: o ar sai acima de T_sat por causa do "
                  "dessuperaquecimento (velocidade de face muito baixa)")
    # eficácia "estrita" com o Q_max termodinâmico (calores específicos variáveis, Shah & Sekulic 2003):
    # refrigerante levado à temperatura de entrada do ar, ou ar levado à temperatura de entrada do refrigerante
    T_ref_in = segs[0].T_in
    h_ref_lim = fl.estado_PT(P_out, T_ar_in).h
    Qmax_ref = m * abs(segs[0].h_in - h_ref_lim)
    Qmax_ar = ctx.xi * C_ar * abs(T_ref_in - T_ar_in)
    eps_Qmax = Q / min(Qmax_ref, Qmax_ar)
    Vdot_c = construtiva.vazao_ar_m3h / 3600.0
    return ResultadoTrocador(
        tipo, fl.nome, m, Q, segs, zonas, proj, construtiva, Nc, N, T_ar_in, T_out, dP_ar, Vdot_c * dP_ar,
        Vdot_c * dP_ar / p.eficiencia_ventilador, P_in, P_out, dTsat, ctx.G, ctx.ar, ctx.xi, g,
        p.velocidade_face, T_sat_ref, eps, p.eficacia, eps_Qmax, C_ar, UA_req / (ctx.xi * C_ar), av,
        ar_seco=ctx.ar_seco)


def _blindar(tipo: str, funcao, *args):
    """Converte falhas numéricas de propriedades (estados fora do domínio do CoolProp, divisão por
    zero) em ErroProjeto, para que o solucionador trate o ponto como inválido."""
    try:
        return funcao(*args)
    except ErroProjeto:
        raise
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as e:
        raise ErroProjeto(f"falha numérica na marcha do {tipo}: {e}") from None


# ============================================================================ condensador
def _condensador_fixo(fl: Fluido, m: float, P_in: float, h_in: float, subresfriamento: float,
                      T_ar_in: float, p: ParametrosTrocador) -> ResultadoTrocador:
    """Marcha do condensador para geometria e velocidade de face fixas."""
    return _blindar("condensador", _condensador_marcha, fl, m, P_in, h_in, subresfriamento, T_ar_in, p)


def _condensador_marcha(fl, m, P_in, h_in, subresfriamento, T_ar_in, p):
    n, n1 = p.n_segmentos, p.n_segmentos_monofasico
    T_ar_m = T_ar_in + 5.0
    for _ in range(3):   # propriedades do ar na temperatura média
        ctx = _Ctx(fl, m, p, T_ar_in, T_ar_m, 1.0, +1.0)
        segs: list = []
        P, h = P_in, h_in
        sat = fl.sat(P)
        if h > sat.hv:   # dessuperaquecimento
            for k in range(1, n1 + 1):
                h_t = h_in + (sat.hv - h_in) * k / n1
                s = _segmento_monofasico(ctx, "dessuperaquecimento", P, h, h_t)
                segs.append(s)
                P, h = s.P_out, s.h_out
        _checar_pressao(P_in, P, "condensador")
        sat = fl.sat(P)
        x0 = min((h - sat.hl) / sat.hlv, 1.0)
        for k in range(n):   # condensação
            x_a = x0 * (1.0 - k / n)
            x_b = 0.0 if k == n - 1 else x0 * (1.0 - (k + 1) / n)
            s = _segmento_bifasico(ctx, "condensação", P, x_a, x_b, True)
            segs.append(s)
            P = s.P_out
            _checar_pressao(P_in, P, "condensador")
        h = fl.sat(P).hl
        if subresfriamento > 0:
            T_sat = fl.Tsat(P)
            h_fim = fl.estado_PT(P, T_sat - subresfriamento).h
            for k in range(1, n1 + 1):
                h_t = h + (h_fim - h) * k / n1 if k < n1 else h_fim
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
    return _blindar("evaporador", _evaporador_marcha, fl, m, h_in, P_out_alvo, superaquecimento, T_ar_in, p,
                    fator_umidade)


def _evaporador_marcha(fl, m, h_in, P_out_alvo, superaquecimento, T_ar_in, p, fator_umidade):
    n, n1 = p.n_segmentos, p.n_segmentos_monofasico
    T_sat_out = fl.Tsat(P_out_alvo)
    h_fim = fl.estado_PT(P_out_alvo, T_sat_out + superaquecimento).h if superaquecimento > 0 else fl.sat(P_out_alvo).hv
    dP_tot = 0.0
    T_ar_m = T_ar_in - 2.0
    erro = math.inf
    for _ in range(12):
        ctx = _Ctx(fl, m, p, T_ar_in, T_ar_m, fator_umidade, -1.0)
        P = P_out_alvo + dP_tot
        if P >= fl.Pc:
            raise ErroProjeto("queda de pressão do evaporador incompatível (pressão de entrada ≥ crítica)")
        P_ent = P
        sat = fl.sat(P)
        x_in = (h_in - sat.hl) / sat.hlv
        if not 0.0 < x_in < 1.0:
            raise ErroProjeto(f"título na entrada do evaporador fora de (0,1): {x_in:.3f}")
        segs: list = []
        for k in range(n):
            x_a = x_in + (1.0 - x_in) * k / n
            x_b = 1.0 if k == n - 1 else x_in + (1.0 - x_in) * (k + 1) / n   # último ponto exato
            s = _segmento_bifasico(ctx, "evaporação", P, x_a, x_b, False)
            segs.append(s)
            P = s.P_out
            _checar_pressao(P_ent, P, "evaporador")
        if superaquecimento > 0:
            h = fl.sat(P).hv
            for k in range(1, n1 + 1):
                h_t = h + (h_fim - h) * k / n1 if k < n1 else h_fim
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
    if abs(erro) > max(100.0, 0.01 * P_out_alvo):
        raise ErroProjeto("a pressão de entrada do evaporador não convergiu (queda de pressão instável): "
                          "aumente n_circuitos")
    return _consolidar("evaporador", fl, m, segs, ctx, p, T_ar_in, T_sat_out)


# ============================================================================ modo de eficácia
def _com(p: ParametrosTrocador, N: int, V: float) -> ParametrosTrocador:
    pp = copy.copy(p)
    pp.geometria = dataclasses.replace(p.geometria, n_fileiras=int(N))
    pp.velocidade_face = float(V)
    return pp


class _PontoInvalido(Exception):
    pass


@dataclass
class BuscaVelocidade:
    """Resultado da busca de V para um nº de fileiras."""
    N: int
    V: Optional[float]
    motivo: str                 # "ok" | "alvo acima do maximo" | "alvo abaixo do minimo" | "sem ponto valido"
    eps_max: Optional[float] = None
    V_eps_max: Optional[float] = None
    eps_min: Optional[float] = None
    V_eps_min: Optional[float] = None
    erro: str = ""
    invalidos: list = field(default_factory=list)   # velocidades rejeitadas (pinch, ΔP, falha numérica)
    dTsat_no_max: Optional[float] = None             # queda de saturação no ponto de ε máxima [K]

    @property
    def limitado_perda_carga(self) -> bool:
        """ε máxima limitada pela perda de carga: há pontos rejeitados abaixo da V de ε máxima, o máximo
        é interior (ε cai ao reduzir V) ou a queda de saturação nesse ponto é relevante."""
        if self.V_eps_max is None:
            return bool(self.invalidos)
        interior = self.V_eps_min is not None and self.eps_min is not None and any(
            V < self.V_eps_max for V in self.invalidos)
        return interior or (self.dTsat_no_max or 0.0) > 1.5 or self._max_interior

    _max_interior: bool = False


class _Solucionador:
    """Resolve a velocidade de face (e, se pedido, o nº de fileiras) para uma eficácia alvo."""

    def __init__(self, rodar, p: ParametrosTrocador, tipo: str):
        if p.eficacia is None or not 0.0 < p.eficacia < 1.0:
            raise ErroProjeto(f"eficácia do {tipo} deve estar entre 0 e 1 (recebido {p.eficacia}).")
        if not 0.0 < p.velocidade_min < p.velocidade_max:
            raise ErroProjeto("faixa de velocidade de face inválida")
        self.rodar, self.p, self.tipo, self.alvo = rodar, p, tipo, p.eficacia
        self._cache: dict = {}

    def resultado(self, N: int, V: float) -> Optional[ResultadoTrocador]:
        k = (int(N), round(float(V), 7))
        if k not in self._cache:
            try:
                self._cache[k] = self.rodar(_com(self.p, N, V))
            except ErroProjeto as e:
                self._cache[k] = e
        r = self._cache[k]
        return None if isinstance(r, ErroProjeto) else r

    def eps(self, N: int, V: float) -> Optional[float]:
        r = self.resultado(N, V)
        return None if r is None else r.eficacia

    def _f(self, N: int, V: float) -> float:
        e = self.eps(N, V)
        if e is None:
            raise _PontoInvalido()
        return e - self.alvo

    def _brent(self, N: int, a: float, b: float) -> Optional[float]:
        try:
            return brentq(lambda V: self._f(N, V), a, b, xtol=1e-4, rtol=1e-6)
        except (_PontoInvalido, ValueError):
            return None

    def velocidade(self, N: int, V_dica: Optional[float] = None) -> BuscaVelocidade:
        p = self.p
        lo, hi = p.velocidade_min, p.velocidade_max
        if V_dica is not None:   # intervalo estreito em torno da solução anterior (iterações do ciclo)
            a, b = max(lo, 0.85 * V_dica), min(hi, 1.15 * V_dica)
            fa, fb = self.eps(N, a), self.eps(N, b)
            if a < b and fa is not None and fb is not None and fa >= self.alvo >= fb:
                V = self._brent(N, a, b)
                if V is not None:
                    return BuscaVelocidade(N, V, "ok")
        # varredura de V_max para baixo: a primeira troca de sinal encontrada é a raiz de maior V
        # (ramo de operação normal: menos tubo e menos perda de carga); para no primeiro achado.
        grade = np.geomspace(lo, hi, N_GRADE_VELOCIDADE)[::-1]
        validos: list = []
        invalidos: list = []
        for V in grade:
            e = self.eps(N, float(V))
            if e is None:
                invalidos.append(float(V))
                continue
            if e == self.alvo:
                return BuscaVelocidade(N, float(V), "ok")
            if validos and (validos[-1][1] - self.alvo) * (e - self.alvo) < 0.0:
                Vr = self._brent(N, float(V), validos[-1][0])
                if Vr is not None:
                    return BuscaVelocidade(N, Vr, "ok")
            validos.append((float(V), e))
        if not validos:
            ult = self._cache.get((int(N), round(float(grade[0]), 7)))
            return BuscaVelocidade(N, None, "sem ponto valido", erro=str(ult) if ult is not None else "",
                                   invalidos=invalidos)
        V_emax, e_max = max(validos, key=lambda t: t[1])
        V_emin, e_min = min(validos, key=lambda t: t[1])
        motivo = "alvo acima do maximo" if e_max < self.alvo else "alvo abaixo do minimo"
        r_max = self.resultado(N, V_emax)
        b = BuscaVelocidade(N, None, motivo, e_max, V_emax, e_min, V_emin, invalidos=invalidos,
                            dTsat_no_max=r_max.dT_sat_queda if r_max is not None else None)
        b._max_interior = V_emax > min(V for V, _ in validos) * (1.0 + 1e-9)
        return b

    def resolver(self, dica: Optional[tuple] = None) -> ResultadoTrocador:
        p = self.p
        if not p.fileiras_automaticas:
            N = p.geometria.n_fileiras
            b = self.velocidade(N, dica[1] if dica and dica[0] == N else None)
            if b.V is None:
                self._levantar([b], fixo=True)
            return self._final(N, b.V, False)
        if dica is not None and 1 <= dica[0] <= p.fileiras_max:
            b = self.velocidade(dica[0], dica[1])
            if b.V is not None:
                return self._final(dica[0], b.V, True)
        Vp = min(max(p.velocidade_face, p.velocidade_min), p.velocidade_max)
        Ns = list(range(1, p.fileiras_max + 1))
        e_Vp = {N: self.eps(N, Vp) for N in Ns}
        N_alto = next((N for N in Ns if e_Vp[N] is not None and e_Vp[N] >= self.alvo), None)
        if N_alto is None:
            cand = [Ns[-1]] if any(e is not None for e in e_Vp.values()) else Ns[::-1]
        else:
            cand = [N_alto] + ([N_alto - 1] if N_alto > 1 else [])
        buscas = [self.velocidade(N) for N in cand]
        sols = [b for b in buscas if b.V is not None]
        if not sols and N_alto is None and Ns[-1] in cand and len(cand) == 1:
            buscas += [self.velocidade(N) for N in Ns[-2::-1]]   # máx. de fileiras inválido: tenta as demais
            sols = [b for b in buscas if b.V is not None]
        if not sols:
            self._levantar(buscas, fixo=False)
        b = min(sols, key=lambda s: (abs(math.log(s.V / Vp)), -s.V))
        return self._final(b.N, b.V, True)

    def _final(self, N: int, V: float, auto: bool) -> ResultadoTrocador:
        r = self.resultado(N, V)
        if r is None:
            raise ErroProjeto(f"ponto final do {self.tipo} inválido ({N} fileiras, {V:.3f} m/s)")
        r = copy.copy(r)
        r.avisos = list(r.avisos)
        r.fileiras_escolhidas_automaticamente = auto
        if abs(r.eficacia - self.alvo) > 2e-3:
            r.avisos.append(f"eficácia obtida {r.eficacia:.3f} difere do alvo {self.alvo:.3f}")
        return r

    def _levantar(self, buscas: list, fixo: bool) -> None:
        msg, por_dp = self._mensagem(buscas, fixo)
        raise (ErroPerdaCarga if por_dp else ErroProjeto)(msg)

    def _mensagem(self, buscas: list, fixo: bool) -> tuple:
        p = self.p
        Nc = p.n_circuitos
        acima = [b for b in buscas if b.motivo == "alvo acima do maximo"]
        abaixo = [b for b in buscas if b.motivo == "alvo abaixo do minimo"]
        if acima:
            b = max(acima, key=lambda t: t.N)
            base = (f"eficácia {self.alvo:.2f} acima do máximo atingível no {self.tipo} com {b.N} fileira(s) e "
                    f"{Nc} circuito(s): ε máx. = {b.eps_max:.3f} a {b.V_eps_max:.2f} m/s "
                    f"(faixa {p.velocidade_min}–{p.velocidade_max} m/s). ")
            if any(t.limitado_perda_carga for t in acima):
                dT = max((t.dTsat_no_max or 0.0) for t in acima)
                return base + (f"O limite vem da perda de carga do refrigerante (queda de saturação de {dT:.1f} K no "
                               "ponto de ε máxima; abaixo dessa velocidade há pinch ou queda excessiva): aumente "
                               "n_circuitos ou o diâmetro do tubo antes de reduzir a eficácia."), True
            if fixo:
                return base + ("Aumente geometria.n_fileiras (ou ative fileiras_automaticas), diminua o passo de aleta "
                               "ou reduza a eficácia."), False
            return base + ("Reduza a eficácia, aumente fileiras_max, diminua o passo de aleta ou aumente a área por "
                           "fileira (com fluxo mássico baixo o lado do refrigerante limita o NTU)."), False
        if abaixo:
            b = min(abaixo, key=lambda t: t.N)
            base = (f"eficácia {self.alvo:.2f} abaixo do mínimo atingível no {self.tipo} com {b.N} fileira(s) na "
                    f"faixa de velocidade: ε mín. = {b.eps_min:.3f} a {b.V_eps_min:.2f} m/s. ")
            if fixo:
                return base + ("Use menos fileiras (geometria.n_fileiras) ou ative fileiras_automaticas, aumente "
                               "velocidade_max ou aumente a eficácia."), False
            return base + "Aumente velocidade_max ou a eficácia.", False
        erros = "; ".join(b.erro for b in buscas if b.erro)[:300]
        return (f"nenhum ponto de operação válido no {self.tipo} para as fileiras testadas "
                f"({', '.join(str(b.N) for b in buscas)}) com {Nc} circuito(s): "
                f"{erros or 'pinch ou perda de carga excessiva'}. Aumente n_circuitos ou o diâmetro do tubo."), True


def _com_circuitos(resolver, p: ParametrosTrocador, tipo: str):
    """Tenta resolver; se a perda de carga impedir (ErroPerdaCarga) e ``circuitos_automaticos``,
    repete com mais circuitos (até ``circuitos_max``) e registra o aviso."""
    pp, nc0 = p, p.n_circuitos
    while True:
        try:
            r = resolver(pp)
        except ErroPerdaCarga:
            if not p.circuitos_automaticos or pp.n_circuitos >= p.circuitos_max:
                raise
            pp = copy.copy(pp)
            pp.n_circuitos += 1
            continue
        if pp.n_circuitos != nc0:
            r.avisos.append(f"n_circuitos aumentado de {nc0} para {pp.n_circuitos}: com {nc0} a perda de carga do "
                            f"refrigerante impedia o projeto do {tipo}")
        return r


def dimensionar_condensador(fl: Fluido, m: float, P_in: float, h_in: float, subresfriamento: float,
                            T_ar_in: float, p: ParametrosTrocador, dica: Optional[tuple] = None) -> ResultadoTrocador:
    """Comprimento de tubo para levar o vapor de descarga (P_in, h_in) a líquido sub-resfriado.
    Com ``p.eficacia`` definido, resolve velocidade de face e fileiras para essa eficácia
    (``dica`` = (N, V) de uma solução anterior acelera as iterações do ciclo)."""
    def resolver(pc):
        def rodar(pp):
            return _condensador_fixo(fl, m, P_in, h_in, subresfriamento, T_ar_in, pp)
        if pc.eficacia is None:
            return rodar(pc)
        d = dica if (dica is None or pc.n_circuitos == p.n_circuitos) else None
        return _Solucionador(rodar, pc, "condensador").resolver(d)
    return _com_circuitos(resolver, p, "condensador")


def dimensionar_evaporador(fl: Fluido, m: float, h_in: float, P_out_alvo: float, superaquecimento: float,
                           T_ar_in: float, p: ParametrosTrocador, fator_umidade: float = 1.0,
                           dica: Optional[tuple] = None) -> ResultadoTrocador:
    """Comprimento de tubo do evaporador: entrada (h_in, pressão a determinar), saída na pressão
    de sucção ``P_out_alvo`` com o superaquecimento pedido. Com ``p.eficacia`` definido, resolve
    velocidade de face e fileiras para essa eficácia."""
    def resolver(pc):
        def rodar(pp):
            return _evaporador_fixo(fl, m, h_in, P_out_alvo, superaquecimento, T_ar_in, pp, fator_umidade)
        if pc.eficacia is None:
            return rodar(pc)
        d = dica if (dica is None or pc.n_circuitos == p.n_circuitos) else None
        return _Solucionador(rodar, pc, "evaporador").resolver(d)
    return _com_circuitos(resolver, p, "evaporador")


def alternativas_fileiras(rodar_fixo, p: ParametrosTrocador, fileiras=range(1, 7)) -> list[dict]:
    """Para a eficácia alvo de ``p``, a solução (V, comprimento, vazão de ar, ΔP do ar) de cada nº de
    fileiras — o compromisso área × ventilador que o projetista escolhe."""
    sol = _Solucionador(rodar_fixo, p, "trocador")
    linhas = []
    for N in fileiras:
        b = sol.velocidade(N)
        if b.V is None:
            linhas.append({"fileiras": N, "viavel": False, "motivo": b.motivo, "eficacia_max": b.eps_max,
                           "eficacia_min": b.eps_min, "limitado_perda_carga": b.limitado_perda_carga})
            continue
        r = sol.resultado(N, b.V)
        linhas.append({"fileiras": N, "viavel": True, "motivo": "ok", "velocidade_face_m_s": b.V,
                       "L_requerido_m": r.L_requerido, "L_adotado_m": r.L_adotado,
                       "tubos_por_fileira": r.tubos_por_fileira, "comprimento_passe_m": r.comprimento_passe,
                       "altura_face_m": r.altura_face, "area_externa_m2": r.area_externa,
                       "vazao_ar_requerida_m3_h": r.vazao_ar_requerida_m3h,
                       "vazao_ar_construtiva_m3_h": r.vazao_ar_m3h, "dP_ar_Pa": r.dP_ar,
                       "potencia_ventilador_W": r.potencia_ventilador_est, "Re_Dc": r.ar.Re_Dc})
    return linhas
