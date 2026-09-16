"""Souders-Brown: velocidade superficial maxima do gas e o que ela esconde.

    v_max = K * sqrt( (rho_L - rho_G) / rho_G )

A expressao sai do balanco peso-empuxo-arrasto de UMA gota, rearranjado:

    v_t = sqrt( 4 g d (rho_L - rho_G) / (3 Cd rho_G) )
        = [ sqrt( 4 g d / (3 Cd) ) ] * sqrt( (rho_L - rho_G) / rho_G )
          \______________________/
                     K

Ou seja, K = sqrt(4 g d / (3 Cd)). O fator empirico empacota, de uma vez so, um
diametro de gota assumido e um coeficiente de arrasto. Tres hipoteses ficam
escondidas ali:

    1. escoamento pistonado, velocidade uniforme na secao transversal;
    2. uma unica gota representativa, sem distribuicao de tamanhos;
    3. nenhuma influencia do bocal de entrada sobre o campo de velocidade.

As tres quebram na pratica, e e exatamente isso que o CFD vai mostrar.

A funcao `diametro_de_gota_implicito` desfaz a conta: dado um K, devolve o
diametro de gota que aquele K corresponde nas condicoes reais do vaso.

AVISO SOBRE OS VALORES DE K
---------------------------
Todo fator K abaixo carrega o campo `fonte` e o campo `confirmar`. Os valores
sao os de uso corrente na industria, mas variam entre GPSA, API, NORSOK e a
pratica interna de cada projetista/licenciador. Antes de assinar qualquer
dimensionamento, abra a edicao da norma que voce vai citar e confirme o numero.
O codigo imprime esse aviso no relatorio de proposito.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .arraste import diametro_para_velocidade_terminal, velocidade_terminal

FT_S = 0.3048          # 1 ft/s em m/s
PSI = 6894.757         # 1 psi em Pa
BAR = 1.0e5            # 1 bar em Pa
ATM_BARA = 1.01325     # pressao atmosferica em bara


# ---------------------------------------------------------------------------
# Correcao de K com a pressao
# ---------------------------------------------------------------------------


def correcao_gpsa_pressao(K_base_ft_s: float, P_bara: float, K_min_ft_s: float = 0.12) -> float:
    """Correcao de K com a pressao, regra pratica do GPSA.

    K = K_base                                      para P <= 100 psig
    K = K_base - 0.01 * (P_psig - 100)/100          para P >  100 psig

    com piso em `K_min_ft_s`. Fisicamente: subindo a pressao o gas fica mais
    denso, o arrasto sobre a gota cresce e o mesmo diametro passa a ser
    arrastado a velocidade menor.

    CONFIRMAR na tabela da edicao do GPSA Engineering Data Book que voce citar.
    Algumas edicoes trazem a tabela ponto a ponto em vez da regra linear.
    """
    P_psig = (P_bara - ATM_BARA) * BAR / PSI
    if P_psig <= 100.0:
        return K_base_ft_s
    K = K_base_ft_s - 0.01 * (P_psig - 100.0) / 100.0
    return max(K, K_min_ft_s)


def sem_correcao(K_base_ft_s: float, P_bara: float) -> float:
    return K_base_ft_s


# ---------------------------------------------------------------------------
# Registro de fatores K
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FatorK:
    chave: str
    descricao: str
    K_ft_s: float
    fonte: str
    corrige_pressao: bool = True
    confirmar: str = "Confirmar o valor na edicao da norma efetivamente citada."
    observacao: str = ""

    @property
    def K_m_s(self) -> float:
        return self.K_ft_s * FT_S

    def K_efetivo_ft_s(self, P_bara: float) -> float:
        if self.corrige_pressao:
            return correcao_gpsa_pressao(self.K_ft_s, P_bara)
        return self.K_ft_s

    def K_efetivo(self, P_bara: float) -> float:
        """K corrigido pela pressao, em m/s."""
        return self.K_efetivo_ft_s(P_bara) * FT_S


FATORES_K: dict[str, FatorK] = {
    "gpsa_vertical_com_demister": FatorK(
        chave="gpsa_vertical_com_demister",
        descricao="Vaso vertical com eliminador de nevoa de tela de malha (wire mesh)",
        K_ft_s=0.35,
        fonte="GPSA Engineering Data Book, Sec. 7 (Separators) - valor de referencia a "
              "P <= 100 psig, com reducao de 0,01 ft/s a cada 100 psi acima disso.",
        observacao="0,35 ft/s = 0,1067 m/s. E o numero que quase todo mundo cita de cabeca. "
                   "Nao e um limite de sedimentacao: e o limite de reencharque/inundacao da "
                   "propria tela. Por isso e tao maior que o K sem demister.",
    ),
    "gpsa_vertical_sem_demister": FatorK(
        chave="gpsa_vertical_sem_demister",
        descricao="Vaso vertical sem eliminador de nevoa (separacao so por gravidade)",
        K_ft_s=0.175,
        fonte="GPSA Sec. 7 - pratica corrente de tomar cerca de metade do K com demister; "
              "a faixa citada na literatura vai de 0,15 a 0,20 ft/s.",
        observacao="Aqui o K SIM tem significado de sedimentacao. Use "
                   "diametro_de_gota_implicito() para ver que gota ele remove de fato.",
    ),
    "gpsa_horizontal_com_demister": FatorK(
        chave="gpsa_horizontal_com_demister",
        descricao="Vaso horizontal com eliminador de nevoa",
        K_ft_s=0.4375,  # 1,25 x 0,35
        fonte="GPSA Sec. 7 - pratica de majorar o K vertical por ~1,25 em vaso horizontal, "
              "por conta do caminho de sedimentacao mais curto. Varias fontes corrigem por L/D.",
        observacao="So faz sentido comparar com o vertical depois de fixar L/D.",
    ),
    "succao_de_compressor": FatorK(
        chave="succao_de_compressor",
        descricao="Vaso de succao de compressor (K rebaixado por severidade de consequencia)",
        K_ft_s=0.25,
        fonte="Pratica de projeto para servico de succao de compressor; API 617 exige gas "
              "isento de liquido na succao mas nao prescreve K. Faixa usual citada: 0,20 a 0,27 ft/s.",
        observacao="O rebaixamento nao e fisica, e gestao de risco: arraste aqui significa "
                   "golpe de liquido no compressor. Este e o vaso do post.",
    ),
    "servico_com_espuma": FatorK(
        chave="servico_com_espuma",
        descricao="Servico com tendencia a espuma (aminas, glicol, crus espumantes)",
        K_ft_s=0.21,  # ~0,6 x 0,35
        fonte="Pratica de rebaixar o K em 30-40% em servico espumante. Fator exato varia "
              "muito entre projetistas - confirmar com a filosofia do licenciador.",
        observacao="Se houver espuma, nenhum CFD monofasico-lagrangiano representa o "
                   "fenomeno. Sai do escopo do metodo proposto.",
    ),
}


# ---------------------------------------------------------------------------
# Souders-Brown direto e inverso
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResultadoSoudersBrown:
    K_ft_s: float
    K_m_s: float
    v_max: float           # velocidade superficial maxima do gas [m/s]
    rho_g: float
    rho_l: float
    P_bara: float
    fator: FatorK | None = None
    avisos: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        nome = self.fator.descricao if self.fator else "K informado diretamente"
        linhas = [nome]
        if self.fator is not None:
            linhas.append(f"  K nominal  : {self.fator.K_ft_s:.4f} ft/s")
        linhas.append(
            f"  K efetivo  : {self.K_ft_s:.4f} ft/s = {self.K_m_s:.5f} m/s "
            f"(a {self.P_bara:.2f} bara)"
        )
        linhas.append(f"  v_max      : {self.v_max:.4f} m/s")
        return "\n".join(linhas)


def velocidade_maxima(K_m_s: float, rho_g: float, rho_l: float) -> float:
    """v_max = K sqrt((rho_L - rho_G)/rho_G), com K ja em m/s."""
    if rho_l <= rho_g:
        raise ValueError("rho_l deve ser maior que rho_g")
    return K_m_s * math.sqrt((rho_l - rho_g) / rho_g)


def souders_brown(
    chave_ou_K: str | float,
    rho_g: float,
    rho_l: float,
    P_bara: float,
    fator_de_projeto: float = 1.0,
) -> ResultadoSoudersBrown:
    """Velocidade superficial maxima do gas.

    `chave_ou_K` aceita uma chave do registro FATORES_K (com correcao de pressao
    automatica) ou um K numerico em ft/s, se voce ja tem o valor da norma do
    cliente em maos.

    `fator_de_projeto` e a margem adicional que o projetista aplica (ex.: 0,8
    para operar 20% abaixo do limite). Multiplica o K.
    """
    avisos: list[str] = []
    if isinstance(chave_ou_K, str):
        fator = FATORES_K[chave_ou_K]
        K_ft_s = fator.K_efetivo_ft_s(P_bara)
        if fator.corrige_pressao and K_ft_s < fator.K_ft_s:
            avisos.append(
                f"K corrigido de {fator.K_ft_s:.3f} para {K_ft_s:.3f} ft/s pela pressao "
                f"({(P_bara - ATM_BARA) * BAR / PSI:.0f} psig, regra GPSA)."
            )
        avisos.append(f"Fonte do K: {fator.fonte}")
        avisos.append(f"CONFIRMAR: {fator.confirmar}")
    else:
        fator = None
        K_ft_s = float(chave_ou_K)
        avisos.append("K informado diretamente pelo usuario; nenhuma correcao de pressao aplicada.")

    K_ft_s *= fator_de_projeto
    if fator_de_projeto != 1.0:
        avisos.append(f"Fator de projeto {fator_de_projeto:.2f} aplicado sobre o K.")

    K_m_s = K_ft_s * FT_S
    return ResultadoSoudersBrown(
        K_ft_s=K_ft_s,
        K_m_s=K_m_s,
        v_max=velocidade_maxima(K_m_s, rho_g, rho_l),
        rho_g=rho_g,
        rho_l=rho_l,
        P_bara=P_bara,
        fator=fator,
        avisos=avisos,
    )


def diametro_de_gota_implicito(
    v_max: float,
    rho_g: float,
    rho_l: float,
    mu_g: float,
    lei: str = "schiller-naumann",
) -> float:
    """O diametro de gota escondido dentro do K, nas condicoes REAIS do vaso.

    Resolve v_t(d) = v_max. E a gota que, em escoamento pistonado ideal, fica
    exatamente estacionaria: tudo acima dela desce, tudo abaixo vai embora com
    o gas.

    Este numero e o resultado mais util do modulo, porque desmonta o mito de
    que "0,35 ft/s remove nevoa". Nao remove: quem remove e a tela. O K de
    0,35 ft/s costuma corresponder a gotas de ordem de MILIMETRO em servico de
    baixa pressao. Retorna em metros.
    """
    return diametro_para_velocidade_terminal(v_max, rho_g, rho_l, mu_g, lei=lei)


def K_para_remover_gota(
    d_alvo: float,
    rho_g: float,
    rho_l: float,
    mu_g: float,
    lei: str = "schiller-naumann",
) -> tuple[float, float]:
    """Caminho inverso: fixo o diametro de gota a remover e obtenho K e v_max.

    E assim que se dimensiona vaso de nocaute de flare pela API 521, que
    prescreve remocao de gotas numa faixa (tipicamente 300 a 600 um - CONFIRMAR
    na edicao vigente) em vez de prescrever um K.

    Retorna (K em ft/s, v_max em m/s).
    """
    v_max = velocidade_terminal(d_alvo, rho_g, rho_l, mu_g, lei=lei).v_t
    K_m_s = v_max / math.sqrt((rho_l - rho_g) / rho_g)
    return K_m_s / FT_S, v_max
