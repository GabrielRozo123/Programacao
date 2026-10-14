"""Capacidade do gabinete (litros <-> garrafas) e carga térmica de refrigeração.

Componentes da carga
--------------------
1. Transmissão pelas paredes isoladas: resistências em série (convecção interna,
   condução na espuma, convecção externa) com fatores de forma de condução para arestas
   (S = 0,54 L) e cantos (S = 0,15 δ) — Incropera et al., Fundamentals of Heat and Mass
   Transfer, Tab. 4.1 — mais um fator de pontes térmicas (parafusos, passagens de tubos, dreno).
2. Porta de vidro (U global com moldura) e gaxeta (transmitância linear ψ no perímetro).
3. Infiltração por abertura de porta: vazão de Gosney & Olama (1975), a mesma da ASHRAE
   Handbook—Refrigeration (cap. "Refrigeration Load"):
       I = 0,221 A (gH)^0,5 (1 − ρ_e/ρ_i)^0,5 F_m ,  F_m = [2/(1 + (ρ_i/ρ_e)^(1/3))]^1,5
   com fator de fluxo da porta D_f (0,8 para ΔT > 11 K; 1,1 abaixo). Em gabinetes pequenos
   o fluxo estabelecido de Gosney-Olama trocaria várias vezes o volume interno numa abertura
   de 8 s, o que é impossível; a troca por abertura é limitada ao volume de ar livre
   (volume interno menos o volume das garrafas) vezes um número máximo de renovações.
4. Produto: pull-down da carga completa e reposição diária; cp da bebida por
   Choi & Okos (1986), recomendado na ASHRAE Handbook—Refrigeration (cap. "Thermal
   Properties of Foods").
5. Cargas internas: iluminação, ventilador do evaporador, resistência anti-embaçante.

A carga de projeto é o maior entre (a) regime diário dividido pelo fator de utilização
máximo do compressor e (b) pull-down com o compressor ligado 100 % do tempo, mais a margem.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .avisos import Avisos, ErroProjeto
from .constantes import G, SEGUNDOS_DIA, C_para_K
from .propriedades import ar_umido, calor_latente_agua


# ============================================================================ produto
@dataclass
class Garrafa:
    """Garrafa PET de bebida (padrão: 600 mL de refrigerante de cola com açúcar).

    Dimensões padrão de uma garrafa genérica de 600 mL (≈ 65 mm × 239 mm). Para precisão,
    meça a garrafa usada pelo cliente: o volume do envelope entra direto na conversão
    litros <-> garrafas."""
    volume_nominal_L: float = 0.600
    diametro_m: float = 0.065
    altura_m: float = 0.239
    densidade_bebida: float = 1040.0      # kg/m³ (refrigerante com ~10,6 °Brix)
    acucar_g_por_L: float = 106.0          # 0 para versões sem açúcar
    massa_embalagem_kg: float = 0.025      # PET + tampa
    cp_embalagem: float = 1100.0           # PET [J/kgK]
    fator_volume_deslocado: float = 1.10   # volume externo / volume nominal (PET + espaço livre)

    @property
    def volume_envelope_m3(self) -> float:
        """Prisma de base quadrada ocupado por garrafa em arranjo retangular (D² H)."""
        return self.diametro_m ** 2 * self.altura_m

    @property
    def volume_deslocado_m3(self) -> float:
        return self.volume_nominal_L * 1e-3 * self.fator_volume_deslocado

    @property
    def massa_bebida_kg(self) -> float:
        return self.volume_nominal_L * 1e-3 * self.densidade_bebida

    @property
    def fracao_carboidrato(self) -> float:
        return self.acucar_g_por_L / self.densidade_bebida

    def cp_bebida(self, T_C: float) -> float:
        """cp [J/kgK] por Choi & Okos (1986): soma ponderada de água e carboidrato."""
        xc = self.fracao_carboidrato
        cp_w = 4.1762 - 9.0864e-5 * T_C + 5.4731e-6 * T_C ** 2
        cp_c = 1.5488 + 1.9625e-3 * T_C - 5.9399e-6 * T_C ** 2
        return 1000.0 * ((1.0 - xc) * cp_w + xc * cp_c)

    def energia_resfriamento(self, T1_C: float, T2_C: float) -> float:
        """Energia [J] para resfriar uma garrafa cheia de T1 a T2 (cp integrado por Simpson)."""
        Tm = 0.5 * (T1_C + T2_C)
        cp_m = (self.cp_bebida(T1_C) + 4.0 * self.cp_bebida(Tm) + self.cp_bebida(T2_C)) / 6.0
        return (self.massa_bebida_kg * cp_m + self.massa_embalagem_kg * self.cp_embalagem) * (T1_C - T2_C)


# ============================================================================ gabinete
@dataclass
class Gabinete:
    """Construção do gabinete vertical de porta de vidro (visi-cooler)."""
    dimensoes_internas_m: Optional[tuple] = None  # (largura, profundidade, altura) — opcional
    razao_altura_largura: float = 2.4
    razao_profundidade_largura: float = 0.85
    fator_ocupacao: float = 0.55        # Σ envelope das garrafas / volume interno (carga cheia)
    fator_ocupacao_max: float = 0.70    # limite físico (prateleiras, dutos, folgas)
    esp_lateral_m: float = 0.050
    esp_fundo_m: float = 0.050
    esp_topo_m: float = 0.050
    esp_base_m: float = 0.060
    k_isolamento: float = 0.022          # PU expandido com ciclopentano [W/mK]
    h_interno: float = 10.0              # convecção forçada interna [W/m²K]
    h_externo: float = 7.7               # convecção natural + radiação (ISO 6946: Rs = 0,13)
    U_porta: float = 2.0                 # porta de vidro duplo low-e com moldura [W/m²K]
    psi_gaxeta: float = 0.10             # transmitância linear da região da gaxeta [W/mK]
    fator_pontes_termicas: float = 1.10  # multiplicador sobre as paredes isoladas
    dT_compartimento_maquina: float = 5.0  # base sobre o compartimento do compressor [K]


@dataclass
class Uso:
    """Perfil de uso e premissas de carga."""
    UR_interna: float = 0.75
    aberturas_por_dia: float = 100.0
    tempo_abertura_s: float = 8.0
    fator_fluxo_porta: Optional[float] = None   # D_f; None -> 0,8 (ΔT > 11 K) ou 1,1
    renovacoes_max_por_abertura: float = 1.0
    T_produto_entrada_C: Optional[float] = None  # None -> temperatura ambiente
    tempo_pulldown_h: float = 24.0
    fracao_reposicao_diaria: float = 0.5         # fração das garrafas trocada por dia
    massa_adicional_kg: float = 0.0              # prateleiras etc. no pull-down
    cp_adicional: float = 500.0                  # aço [J/kgK]
    potencia_iluminacao_W: float = 10.0
    potencia_ventilador_evap_W: float = 8.0
    potencia_antiembacante_W: float = 0.0
    fracao_antiembacante_interna: float = 0.5
    fator_utilizacao_max: float = 0.70           # fração do tempo ligado em regime
    margem_seguranca: float = 0.10


@dataclass
class Capacidade:
    volume_interno_L: float
    n_garrafas: int
    largura_m: float
    profundidade_m: float
    altura_m: float
    volume_ar_livre_L: float
    massa_produto_kg: float
    origem: str


def resolver_capacidade(volume_L: Optional[float], n_garrafas: Optional[int], garrafa: Garrafa,
                        gab: Gabinete, avisos: Avisos) -> Capacidade:
    """Converte volume interno <-> número de garrafas e define as dimensões internas.

    Atenção à conversão ingênua 'litros / 0,6 L': ela dá o volume de LÍQUIDO, não o volume
    de gabinete necessário. Cada garrafa ocupa o envelope D²H e só uma fração do volume
    interno (``fator_ocupacao``) é aproveitável (prateleiras, folgas de ar, evaporador)."""
    Venv = garrafa.volume_envelope_m3
    if gab.dimensoes_internas_m is not None:
        W, D, H = gab.dimensoes_internas_m
        V_dims = W * D * H
        if volume_L is not None and abs(V_dims * 1e3 - volume_L) / volume_L > 0.05:
            avisos.atencao("capacidade", f"dimensões internas dão {V_dims * 1e3:.0f} L, diferente dos "
                           f"{volume_L:.0f} L informados; usando as dimensões.")
        volume_L = V_dims * 1e3
    if volume_L is None and n_garrafas is None:
        raise ErroProjeto("Informe o volume interno [L] ou o número de garrafas.")

    if volume_L is not None and n_garrafas is None:
        V = volume_L * 1e-3
        n = int(math.floor(gab.fator_ocupacao * V / Venv))
        origem = "volume informado; garrafas estimadas pelo fator de ocupação"
    elif volume_L is None:
        n = int(n_garrafas)
        V = n * Venv / gab.fator_ocupacao
        origem = "garrafas informadas; volume estimado pelo fator de ocupação"
    else:
        V, n = volume_L * 1e-3, int(n_garrafas)
        origem = "volume e garrafas informados"
        ocup = n * Venv / V
        if ocup > gab.fator_ocupacao_max:
            n_max = int(gab.fator_ocupacao_max * V / Venv)
            avisos.critico("capacidade", f"{n} garrafas não cabem em {volume_L:.0f} L (ocupação "
                           f"{ocup:.0%} > {gab.fator_ocupacao_max:.0%}). Máximo físico ≈ {n_max} garrafas; "
                           f"para {n} garrafas são necessários ≈ {n * Venv / gab.fator_ocupacao * 1e3:.0f} L.")
    vol_liquido_L = n * garrafa.volume_nominal_L
    if abs(vol_liquido_L - V * 1e3) / (V * 1e3) < 0.05:
        avisos.atencao("capacidade", f"{n} garrafas × {garrafa.volume_nominal_L * 1e3:.0f} mL = "
                       f"{vol_liquido_L:.0f} L de líquido ≈ volume interno: parece uma conversão por volume de "
                       "líquido. O gabinete precisa de mais volume que o líquido que guarda.")

    if gab.dimensoes_internas_m is not None:
        W, D, H = gab.dimensoes_internas_m
    else:
        W = (V / (gab.razao_altura_largura * gab.razao_profundidade_largura)) ** (1.0 / 3.0)
        D, H = gab.razao_profundidade_largura * W, gab.razao_altura_largura * W
    V_livre = V - n * garrafa.volume_deslocado_m3
    if V_livre <= 0.1 * V:
        avisos.atencao("capacidade", "volume de ar livre < 10 % do interno: circulação de ar comprometida.")
        V_livre = max(V_livre, 0.1 * V)
    massa = n * (garrafa.massa_bebida_kg + garrafa.massa_embalagem_kg)
    return Capacidade(V * 1e3, n, W, D, H, V_livre * 1e3, massa, origem)


# ============================================================================ transmissão
@dataclass
class Face:
    nome: str
    area_int: float
    area_ext: float
    espessura: float
    fator_forma: float
    UA: float
    dT: float
    Q: float


def transmissao(cap: Capacidade, gab: Gabinete, T_amb: float, T_int: float) -> dict:
    """Carga de transmissão [W] pelas cinco faces isoladas, porta de vidro e gaxeta."""
    W, D, H = cap.largura_m, cap.profundidade_m, cap.altura_m
    dT = T_amb - T_int
    faces = {
        "topo": (W, D, gab.esp_topo_m, 0.0),
        "base": (W, D, gab.esp_base_m, gab.dT_compartimento_maquina),
        "lateral_esq": (D, H, gab.esp_lateral_m, 0.0),
        "lateral_dir": (D, H, gab.esp_lateral_m, 0.0),
        "fundo": (W, H, gab.esp_fundo_m, 0.0),
    }
    arestas = [("fundo", "topo", W), ("fundo", "base", W), ("fundo", "lateral_esq", H),
               ("fundo", "lateral_dir", H), ("topo", "lateral_esq", D), ("topo", "lateral_dir", D),
               ("base", "lateral_esq", D), ("base", "lateral_dir", D)]
    cantos = [("fundo", "topo", "lateral_esq"), ("fundo", "topo", "lateral_dir"),
              ("fundo", "base", "lateral_esq"), ("fundo", "base", "lateral_dir")]
    S = {n: a * b / esp for n, (a, b, esp, _) in faces.items()}
    for f1, f2, L in arestas:            # S_aresta = 0,54 L, dividido entre as duas faces
        S[f1] += 0.27 * L
        S[f2] += 0.27 * L
    for trio in cantos:                  # S_canto = 0,15 δ, dividido entre as três faces
        esp_m = sum(faces[n][2] for n in trio) / 3.0
        for n in trio:
            S[n] += 0.05 * esp_m
    lista = []
    for nome, (a, b, esp, dT_extra) in faces.items():
        Ai, Ae = a * b, (a + 2 * esp) * (b + 2 * esp)
        R = 1.0 / (gab.h_interno * Ai) + 1.0 / (gab.k_isolamento * S[nome]) + 1.0 / (gab.h_externo * Ae)
        UA = gab.fator_pontes_termicas / R
        lista.append(Face(nome, Ai, Ae, esp, S[nome], UA, dT + dT_extra, UA * (dT + dT_extra)))
    A_porta = W * H
    Q_paredes = sum(f.Q for f in lista)
    Q_porta = gab.U_porta * A_porta * dT
    perimetro = 2.0 * (W + H)
    Q_gaxeta = gab.psi_gaxeta * perimetro * dT
    return {"faces": lista, "Q_paredes": Q_paredes, "Q_porta": Q_porta, "Q_gaxeta": Q_gaxeta,
            "A_porta": A_porta, "perimetro_porta": perimetro,
            "UA_total": sum(f.UA for f in lista) + gab.U_porta * A_porta + gab.psi_gaxeta * perimetro,
            "Q_total": Q_paredes + Q_porta + Q_gaxeta}


# ============================================================================ infiltração
def infiltracao(cap: Capacidade, uso: Uso, T_amb: float, UR_amb: float, T_int: float,
                avisos: Avisos) -> dict:
    """Carga média de infiltração [W] por abertura de porta (sensível + latente)."""
    ext, inn = ar_umido(T_amb, UR_amb), ar_umido(T_int, uso.UR_interna)
    rho_e, rho_i = ext["rho_mist"], inn["rho_mist"]
    zero = {"Q_media": 0.0, "Q_sensivel": 0.0, "Q_latente": 0.0, "agua_kg_dia": 0.0,
            "m_ar_abertura": 0.0, "limitado_por_volume": False, "V_gosney_olama_m3": 0.0}
    if rho_i <= rho_e or uso.aberturas_por_dia <= 0:
        return zero
    A, H = cap.largura_m * cap.altura_m, cap.altura_m
    Fm = (2.0 / (1.0 + (rho_i / rho_e) ** (1.0 / 3.0))) ** 1.5
    I = 0.221 * A * math.sqrt(G * H) * math.sqrt(1.0 - rho_e / rho_i) * Fm   # m³/s de ar frio
    dT = T_amb - T_int
    Df = uso.fator_fluxo_porta if uso.fator_fluxo_porta is not None else (0.8 if dT > 11.0 else 1.1)
    V_GO = I * Df * uso.tempo_abertura_s
    m_GO = V_GO / inn["v"]                                    # kg de ar seco (ASHRAE usa ρ do ar frio)
    m_lim = uso.renovacoes_max_por_abertura * cap.volume_ar_livre_L * 1e-3 / ext["v"]
    m_ab = min(m_GO, m_lim)
    limitado = m_lim < m_GO
    if limitado:
        avisos.info("infiltração", f"Gosney-Olama trocaria {m_GO / m_lim:.1f}× o ar livre por abertura; "
                    f"troca limitada a {uso.renovacoes_max_por_abertura:g} renovação(ões) do volume livre.")
    q_ab = m_ab * (ext["h"] - inn["h"])
    dW = max(ext["W"] - inn["W"], 0.0)
    q_lat_ab = m_ab * dW * calor_latente_agua(T_int)
    n = uso.aberturas_por_dia
    return {"Q_media": n * q_ab / SEGUNDOS_DIA, "Q_latente": n * q_lat_ab / SEGUNDOS_DIA,
            "Q_sensivel": n * (q_ab - q_lat_ab) / SEGUNDOS_DIA, "agua_kg_dia": n * m_ab * dW,
            "m_ar_abertura": m_ab, "limitado_por_volume": limitado, "V_gosney_olama_m3": V_GO,
            "vazao_gosney_olama_m3s": I, "Df": Df, "Tdp_interno_K": inn["Tdp"]}


# ============================================================================ total
@dataclass
class CargaTermica:
    capacidade: Capacidade
    transmissao: dict
    infiltracao: dict
    Q_paredes: float
    Q_porta: float
    Q_gaxeta: float
    Q_infiltracao: float
    Q_internas: float
    Q_reposicao: float
    Q_pulldown_produto: float
    Q_regime: float              # média diária com o uso definido [W]
    Q_requerida_regime: float    # Q_regime / fator de utilização
    Q_pulldown: float            # pull-down com compressor 100 % ligado
    caso_governante: str
    Q_projeto: float             # capacidade frigorífica de projeto do evaporador [W]
    Q_latente_projeto: float
    fator_umidade: float         # ξ = Q_total / Q_sensível no evaporador
    componentes: dict = field(default_factory=dict)

    def tabela(self) -> list[tuple[str, float]]:
        return list(self.componentes.items())


def calcular_carga(cap: Capacidade, gab: Gabinete, uso: Uso, garrafa: Garrafa, T_amb_C: float,
                   UR_amb: float, T_alvo_C: float, avisos: Avisos) -> CargaTermica:
    T_amb, T_int = C_para_K(T_amb_C), C_para_K(T_alvo_C)
    if T_int >= T_amb:
        raise ErroProjeto("A temperatura alvo deve ser menor que a ambiente.")
    tr = transmissao(cap, gab, T_amb, T_int)
    inf = infiltracao(cap, uso, T_amb, UR_amb, T_int, avisos)
    Q_int = (uso.potencia_iluminacao_W + uso.potencia_ventilador_evap_W
             + uso.fracao_antiembacante_interna * uso.potencia_antiembacante_W)
    T_prod = T_amb_C if uso.T_produto_entrada_C is None else uso.T_produto_entrada_C
    E_garrafa = garrafa.energia_resfriamento(T_prod, T_alvo_C)
    E_cheia = cap.n_garrafas * E_garrafa + uso.massa_adicional_kg * uso.cp_adicional * (T_prod - T_alvo_C)
    Q_rep = uso.fracao_reposicao_diaria * cap.n_garrafas * E_garrafa / SEGUNDOS_DIA
    Q_pd_prod = E_cheia / (uso.tempo_pulldown_h * 3600.0)

    Q_regime = tr["Q_total"] + inf["Q_media"] + Q_int + Q_rep
    Q_req_reg = Q_regime / uso.fator_utilizacao_max
    Q_pd = tr["Q_total"] + Q_int + Q_pd_prod      # porta fechada no pull-down
    if Q_req_reg >= Q_pd:
        caso, Q_base, Q_lat = "regime (uso diário / fator de utilização)", Q_req_reg, inf["Q_latente"] / uso.fator_utilizacao_max
    else:
        caso, Q_base, Q_lat = "pull-down da carga completa", Q_pd, 0.0
    Q_proj = Q_base * (1.0 + uso.margem_seguranca)
    Q_lat_proj = Q_lat * (1.0 + uso.margem_seguranca)
    xi = Q_proj / max(Q_proj - Q_lat_proj, 1e-9)
    comp = {"paredes isoladas": tr["Q_paredes"], "porta de vidro": tr["Q_porta"], "gaxeta": tr["Q_gaxeta"],
            "infiltração (média)": inf["Q_media"], "cargas internas": Q_int,
            "reposição diária de produto": Q_rep, "pull-down do produto": Q_pd_prod}
    if uso.fator_utilizacao_max > 0.85:
        avisos.atencao("carga", "fator de utilização > 85 % deixa pouca folga para degelo e controle.")
    return CargaTermica(cap, tr, inf, tr["Q_paredes"], tr["Q_porta"], tr["Q_gaxeta"], inf["Q_media"], Q_int,
                        Q_rep, Q_pd_prod, Q_regime, Q_req_reg, Q_pd, caso, Q_proj, Q_lat_proj, xi, comp)


__all__ = ["Garrafa", "Gabinete", "Uso", "Capacidade", "CargaTermica", "resolver_capacidade",
           "transmissao", "infiltracao", "calcular_carga"]
