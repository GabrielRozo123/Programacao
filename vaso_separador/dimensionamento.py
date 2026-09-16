"""Dimensionamento de vaso de nocaute (KO drum) vertical gas-liquido.

Metodo classico: Souders-Brown para o diametro, alturas por regra de folga e
tempo de retencao, bocais por criterio de momento rho*v^2.

O modulo devolve, junto com as dimensoes, TRES numeros que o metodo classico
normalmente nao mostra e que sao o assunto do estudo de CFD:

  1. o diametro de gota implicito no K adotado, nas condicoes reais do vaso;
  2. o maior diametro de gota que sobrevive ao cisalhamento do bocal de entrada
     (limite de Weber);
  3. a razao entre os dois.

Quando (2) fica bem abaixo de (1), o vaso esta dimensionado para separar gotas
que o proprio bocal de entrada nao produz - ele produz gotas bem menores. O vaso
atende a norma e mesmo assim arrasta. Essa e a falha que o CFD expoe e que o
dimensionamento pela media nao ve.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .arraste import diametro_maximo_estavel, numero_de_weber, velocidade_terminal
from .propriedades import (
    CRITERIOS_RHO_V2,
    RHO_V2_SAIDA_GAS,
    V_MAX_SAIDA_LIQUIDO,
    Bocal,
    massa_especifica_gas,
    rho_v2_em_pa,
    seleciona_bocal,
    vazao_volumetrica,
)
from .souders_brown import (
    ResultadoSoudersBrown,
    diametro_de_gota_implicito,
    souders_brown,
)

# Folgas geometricas, em metros. Todas sao pratica de projeto consolidada
# (GPSA Sec. 7 e equivalentes). CONFIRMAR contra o padrao do cliente - cada
# licenciador tem o seu, e alguns sao bem mais folgados.
FOLGA_FUNDO_A_LLL = 0.3048        # 12 in: aloja quebra-vortice e bocal de saida
FOLGA_HLL_A_BOCAL_BASE = 0.3048   # 12 in + metade do bocal de entrada
FOLGA_BOCAL_A_DEMISTER_MIN = 0.3048   # minimo GPSA: 12 in + metade do bocal
FOLGA_BOCAL_A_DEMISTER_BOA = 0.9144   # 36 in: pratica para o jato se distribuir
FOLGA_DEMISTER_A_SAIDA = 0.3048   # 12 in acima da tela, ou 1 diametro de saida
ESPESSURA_DEMISTER = 0.15         # 6 in de tela de malha

LD_MIN, LD_MAX = 2.0, 5.0         # faixa usual de esbeltez para vaso vertical


@dataclass
class Corrente:
    """Condicoes de processo na entrada do vaso."""

    nome: str
    P_bara: float
    T_C: float
    MM: float              # massa molar do gas [kg/kmol]
    Z: float               # fator de compressibilidade [-]
    rho_l: float           # massa especifica do liquido [kg/m3]
    mu_g: float            # viscosidade do gas [Pa.s]
    sigma: float           # tensao interfacial [N/m]
    W_gas: float           # vazao massica de gas [kg/h]
    W_liq: float           # vazao massica de liquido [kg/h]
    servico: str = ""
    rotulo: str = ""          # rotulo curto para grafico
    fonte_dados: str = ""

    @property
    def rho_g(self) -> float:
        return massa_especifica_gas(self.P_bara, self.T_C, self.MM, self.Z)

    @property
    def Q_gas(self) -> float:
        return vazao_volumetrica(self.W_gas, self.rho_g)

    @property
    def Q_liq(self) -> float:
        return vazao_volumetrica(self.W_liq, self.rho_l)

    @property
    def rho_mistura(self) -> float:
        """Massa especifica homogenea da mistura bifasica no bocal de entrada."""
        return (self.W_gas + self.W_liq) / 3600.0 / (self.Q_gas + self.Q_liq)

    @property
    def fracao_massica_liquido(self) -> float:
        return self.W_liq / (self.W_gas + self.W_liq)


@dataclass
class Criterios:
    """Escolhas de projeto. Tudo que e opiniavel fica reunido aqui."""

    fator_K: str = "succao_de_compressor"
    fator_de_projeto: float = 1.0
    com_demister: bool = True
    dispositivo_de_entrada: str = "sem_dispositivo"
    tempo_holdup_min: float = 5.0     # LLL -> NLL, tempo de reacao do operador
    tempo_surge_min: float = 2.0      # NLL -> HLL, pulmao
    espessura_demister: float = ESPESSURA_DEMISTER
    incremento_diametro: float = 0.05  # arredondamento do costado, 50 mm
    we_critico: float = 12.0
    forcar_LD_minimo: float | None = LD_MIN
    """Se o L/D calculado ficar abaixo deste valor, a altura faltante e somada ao
    espaco de desengajamento (bocal de entrada -> base do demister). E onde o
    projetista acrescenta altura na pratica, e e o lugar fisicamente certo: mais
    altura ali e mais tempo de residencia para a gota sedimentar antes da tela.
    Passe None para deixar o vaso atarracado e so receber o aviso."""


@dataclass
class Alturas:
    fundo_a_LLL: float
    holdup_LLL_a_NLL: float
    surge_NLL_a_HLL: float
    HLL_a_bocal: float
    bocal_a_demister: float
    demister: float
    demister_a_saida: float

    @property
    def total(self) -> float:
        return (
            self.fundo_a_LLL
            + self.holdup_LLL_a_NLL
            + self.surge_NLL_a_HLL
            + self.HLL_a_bocal
            + self.bocal_a_demister
            + self.demister
            + self.demister_a_saida
        )

    @property
    def nivel_HLL(self) -> float:
        """Cota do HLL medida a partir da tangente inferior [m]."""
        return self.fundo_a_LLL + self.holdup_LLL_a_NLL + self.surge_NLL_a_HLL

    @property
    def cota_bocal_entrada(self) -> float:
        return self.nivel_HLL + self.HLL_a_bocal

    @property
    def cota_base_demister(self) -> float:
        return self.cota_bocal_entrada + self.bocal_a_demister

    def como_lista(self) -> list[tuple[str, float]]:
        return [
            ("Tangente inferior -> LLL", self.fundo_a_LLL),
            ("LLL -> NLL (retencao)", self.holdup_LLL_a_NLL),
            ("NLL -> HLL (pulmao)", self.surge_NLL_a_HLL),
            ("HLL -> eixo do bocal de entrada", self.HLL_a_bocal),
            ("Bocal de entrada -> base do demister", self.bocal_a_demister),
            ("Demister (espessura da tela)", self.demister),
            ("Topo do demister -> saida de gas", self.demister_a_saida),
        ]


@dataclass
class Dimensionamento:
    corrente: Corrente
    criterios: Criterios
    sb: ResultadoSoudersBrown

    D: float                    # diametro interno adotado [m]
    D_minimo: float             # diametro minimo teorico [m]
    area: float                 # area da secao transversal [m2]
    v_gas: float                # velocidade superficial real do gas [m/s]
    uso_do_limite: float        # v_gas / v_max [-]

    alturas: Alturas
    LD: float

    bocal_entrada: Bocal
    bocal_saida_gas: Bocal
    bocal_saida_liquido: Bocal

    d_implicito: float          # gota implicita no K, a v_max [m]
    d_implicito_operacao: float # gota implicita a velocidade real [m]
    d_max_estavel_bocal: float  # limite de Weber no bocal de entrada [m]
    we_no_bocal_do_d_implicito: float

    volume_holdup: float        # LLL -> NLL [m3]
    volume_surge: float         # NLL -> HLL [m3]
    altura_extra_por_LD: float = 0.0  # acrescimo de desengajamento para atender L/D

    avisos: list[str] = field(default_factory=list)

    @property
    def razao_de_atomizacao(self) -> float:
        """d_implicito / d_max_estavel. Acima de 1 o bocal produz gota que o
        vaso, pela sua propria base de dimensionamento, nao separa."""
        return self.d_implicito / self.d_max_estavel_bocal


def dimensionar_vaso_vertical(corrente: Corrente, criterios: Criterios | None = None) -> Dimensionamento:
    """Dimensiona o vaso vertical completo e levanta os avisos de projeto."""
    crit = criterios or Criterios()
    rho_g, rho_l, mu_g = corrente.rho_g, corrente.rho_l, corrente.mu_g
    Q_gas, Q_liq = corrente.Q_gas, corrente.Q_liq
    avisos: list[str] = []

    # --- 1. Diametro por Souders-Brown ------------------------------------
    sb = souders_brown(crit.fator_K, rho_g, rho_l, corrente.P_bara, crit.fator_de_projeto)
    area_min = Q_gas / sb.v_max
    D_min = math.sqrt(4.0 * area_min / math.pi)
    D = math.ceil(D_min / crit.incremento_diametro) * crit.incremento_diametro
    area = math.pi * D**2 / 4.0
    v_gas = Q_gas / area

    # --- 2. Bocais ---------------------------------------------------------
    lim_lb, nota_disp = CRITERIOS_RHO_V2[crit.dispositivo_de_entrada]
    bocal_entrada = seleciona_bocal(
        Q_gas + Q_liq, corrente.rho_mistura, rho_v2_em_pa(lim_lb)
    )
    bocal_saida_gas = seleciona_bocal(Q_gas, rho_g, rho_v2_em_pa(RHO_V2_SAIDA_GAS))
    # Saida de liquido: criterio de velocidade, convertido para rho*v^2 equivalente.
    bocal_saida_liquido = seleciona_bocal(
        Q_liq, rho_l, rho_l * V_MAX_SAIDA_LIQUIDO**2, di_minimo_extra=0.0508
    )

    # --- 3. Alturas --------------------------------------------------------
    V_holdup = Q_liq * crit.tempo_holdup_min * 60.0
    V_surge = Q_liq * crit.tempo_surge_min * 60.0
    espessura = crit.espessura_demister if crit.com_demister else 0.0

    alturas = Alturas(
        fundo_a_LLL=FOLGA_FUNDO_A_LLL,
        holdup_LLL_a_NLL=V_holdup / area,
        surge_NLL_a_HLL=V_surge / area,
        HLL_a_bocal=FOLGA_HLL_A_BOCAL_BASE + bocal_entrada.di / 2.0,
        bocal_a_demister=max(
            FOLGA_BOCAL_A_DEMISTER_BOA,
            FOLGA_BOCAL_A_DEMISTER_MIN + bocal_entrada.di / 2.0,
        ),
        demister=espessura,
        demister_a_saida=max(FOLGA_DEMISTER_A_SAIDA, bocal_saida_gas.di),
    )
    LD = alturas.total / D

    extra_LD = 0.0
    if crit.forcar_LD_minimo is not None and LD < crit.forcar_LD_minimo:
        extra_LD = crit.forcar_LD_minimo * D - alturas.total
        alturas.bocal_a_demister += extra_LD
        LD = alturas.total / D
        avisos.append(
            f"Altura de desengajamento acrescida de {extra_LD:.3f} m para atender "
            f"L/D >= {crit.forcar_LD_minimo:.1f} (de {(alturas.total - extra_LD) / D:.2f} "
            f"para {LD:.2f}). O acrescimo vai entre o bocal de entrada e o demister, "
            f"que e onde ele tambem melhora a separacao."
        )

    # --- 4. O que o K esconde ---------------------------------------------
    d_impl = diametro_de_gota_implicito(sb.v_max, rho_g, rho_l, mu_g)
    d_impl_op = diametro_de_gota_implicito(v_gas, rho_g, rho_l, mu_g)
    d_max_est = diametro_maximo_estavel(
        bocal_entrada.velocidade, rho_g, corrente.sigma, crit.we_critico
    )
    we_d_impl = numero_de_weber(d_impl, bocal_entrada.velocidade, rho_g, corrente.sigma)

    # --- 5. Avisos ---------------------------------------------------------
    avisos.extend(sb.avisos)
    avisos.append(f"Dispositivo de entrada: {nota_disp}")

    if not (LD_MIN <= LD <= LD_MAX):
        avisos.append(
            f"ATENCAO: L/D = {LD:.2f} fora da faixa usual {LD_MIN:.0f}-{LD_MAX:.0f}. "
            + (
                "Vaso muito esbelto: reveja tempos de retencao ou considere vaso horizontal."
                if LD > LD_MAX
                else "Vaso muito atarracado: o jato de entrada nao tera altura para se distribuir."
            )
        )
    if crit.com_demister and d_impl > 300e-6:
        avisos.append(
            f"O K adotado corresponde a gotas de {d_impl * 1e6:.0f} um por sedimentacao pura. "
            f"Tudo abaixo disso depende inteiramente do demister - nao da gravidade."
        )
    if d_max_est < d_impl:
        avisos.append(
            f"CRITICO PARA O ESTUDO: o bocal de entrada a {bocal_entrada.velocidade:.1f} m/s "
            f"quebra gotas acima de {d_max_est * 1e6:.0f} um (We_c = {crit.we_critico:.0f}), "
            f"mas o dimensionamento so garante separacao gravitacional acima de "
            f"{d_impl * 1e6:.0f} um. Razao de atomizacao = {d_impl / d_max_est:.1f}x. "
            f"O vaso esta dimensionado para separar uma gota que a sua propria entrada "
            f"nao produz."
        )
    razao_bocal = bocal_entrada.di / D
    if razao_bocal > 0.40:
        avisos.append(
            f"ATENCAO: bocal de entrada {bocal_entrada.nps} equivale a {razao_bocal * 100:.0f}% do "
            f"diametro do costado. Acima de ~40% o jato ocupa boa parte da secao e nao existe "
            f"regiao de desengajamento de verdade - o vaso vira um trecho de tubulacao alargado. "
            f"Considere dispositivo de entrada mais permissivo (que reduz o bocal), entrada "
            f"multipla, ou vaso horizontal."
        )
    if dim_v_saida := bocal_saida_gas.velocidade:
        if dim_v_saida > 30.0:
            avisos.append(
                f"Saida de gas a {dim_v_saida:.0f} m/s. O criterio de rho.v2 esta atendido, "
                f"mas velocidade acima de ~30 m/s costuma esbarrar em limite de ruido e de "
                f"vibracao induzida por escoamento. Confirmar contra a especificacao de "
                f"tubulacao antes de fechar a bitola."
            )
    if not crit.com_demister:
        avisos.append(
            "Sem demister a separacao e 100% gravitacional: a curva de eficiencia por "
            "tamanho de gota do CFD e o unico criterio de aceitacao que faz sentido."
        )

    return Dimensionamento(
        corrente=corrente,
        criterios=crit,
        sb=sb,
        D=D,
        D_minimo=D_min,
        area=area,
        v_gas=v_gas,
        uso_do_limite=v_gas / sb.v_max,
        alturas=alturas,
        LD=LD,
        bocal_entrada=bocal_entrada,
        bocal_saida_gas=bocal_saida_gas,
        bocal_saida_liquido=bocal_saida_liquido,
        d_implicito=d_impl,
        d_implicito_operacao=d_impl_op,
        d_max_estavel_bocal=d_max_est,
        we_no_bocal_do_d_implicito=we_d_impl,
        volume_holdup=V_holdup,
        volume_surge=V_surge,
        altura_extra_por_LD=extra_LD,
        avisos=avisos,
    )


def eficiencia_ideal(d: float, v_gas: float, rho_g: float, rho_l: float, mu_g: float) -> float:
    """Eficiencia de separacao no modelo pistonado ideal: degrau em v_t = v_gas.

    E o que o metodo classico preve. O CFD vai borrar esse degrau em duas
    direcoes: para baixo porque existe regiao da secao onde a velocidade local
    passa da media, e para cima porque a dispersao turbulenta joga gota contra
    a parede. O grafico dos dois juntos e o resultado do estudo.
    """
    return 1.0 if velocidade_terminal(d, rho_g, rho_l, mu_g).v_t >= v_gas else 0.0
