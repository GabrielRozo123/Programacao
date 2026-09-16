"""Cartao de configuracao do Simcenter STAR-CCM+ derivado do dimensionamento.

A ideia e que nenhum numero do setup seja digitado de cabeca. Tudo que entra no
solver sai do dimensionamento: condicao de contorno, turbulencia na entrada,
altura da primeira celula, faixa de diametro do injetor, criterio de convergencia
e o caso de verificacao.

DECISAO DE METODO QUE VALE A PENA LER ANTES DE RODAR
----------------------------------------------------
Nao injete uma Rosin-Rammler e leia um numero unico de eficiencia. A distribuicao
de tamanho de gota na entrada e a MAIOR incerteza do estudo, e se ela entrar como
insumo, ela sai como resultado - voce perde a capacidade de defender a conclusao.

Faca o contrario: injete classes monodispersas em varredura logaritmica
(10, 20, 50, 100, 200, 300, 500 um), extraia a curva de eficiencia por tamanho
eta(d), e so DEPOIS convolua com a distribuicao que quiser:

    eficiencia_global = integral eta(d) * f(d) dd

Assim eta(d) e um resultado de fisica, robusto, que sobrevive a troca de hipotese
de distribuicao. A Rosin-Rammler vira pos-processamento de planilha, nao insumo
de CFD. E o revisor do cliente consegue refazer a conta com a distribuicao dele
sem voce rodar nada de novo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .arraste import G, tabela_de_velocidades_terminais
from .dimensionamento import Dimensionamento

# Varredura de classes monodispersas recomendada [um].
CLASSES_DE_GOTA_UM = (10.0, 20.0, 35.0, 50.0, 75.0, 100.0, 150.0, 200.0, 300.0, 500.0)


@dataclass
class CartaoSetup:
    dimensionamento: Dimensionamento
    linhas: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    notas: list[str] = field(default_factory=list)

    def texto(self) -> str:
        larg = 78
        out = ["=" * larg, "CARTAO DE CONFIGURACAO - Simcenter STAR-CCM+".center(larg), "=" * larg, ""]
        for secao, itens in self.linhas.items():
            out.append(secao)
            out.append("-" * larg)
            for rotulo, valor in itens:
                out.append(f"  {rotulo:<44} {valor}")
            out.append("")
        if self.notas:
            out.append("NOTAS DE CONFIGURACAO")
            out.append("-" * larg)
            for i, n in enumerate(self.notas, 1):
                out.append(f"  {i}. {n}")
            out.append("")
        return "\n".join(out)


def _turbulencia_na_entrada(v: float, di: float, rho: float, mu: float) -> tuple[float, float, float]:
    """Intensidade e escala de comprimento na entrada, para tubo desenvolvido.

    I = 0.16 Re^(-1/8), l = 0.07 D. Correlacoes classicas de escoamento interno.
    """
    Re = rho * v * di / mu
    I = 0.16 * Re ** (-1.0 / 8.0)
    l = 0.07 * di
    return Re, I, l


def _altura_primeira_celula(y_plus: float, v: float, L: float, rho: float, mu: float) -> float:
    """Altura da PRIMEIRA CELULA para um y+ alvo (placa plana, Cf = 0.058 Re^-0.2).

    Estimativa a priori. y+ e avaliado no centroide da celula, entao a espessura
    da celula e o dobro da distancia ao centroide. Confira o y+ real no
    pos-processamento e reajuste - a estimativa erra facil por um fator 2.
    """
    Re_L = rho * v * L / mu
    Cf = 0.058 * Re_L ** (-0.2)
    tau_w = 0.5 * Cf * rho * v**2
    u_tau = math.sqrt(tau_w / rho)
    y_centroide = y_plus * mu / (rho * u_tau)
    return 2.0 * y_centroide


def gerar_cartao(dim: Dimensionamento) -> CartaoSetup:
    c, crit = dim.corrente, dim.criterios
    rho_g, mu_g = c.rho_g, c.mu_g
    be = dim.bocal_entrada

    Re_bocal, I_bocal, l_bocal = _turbulencia_na_entrada(be.velocidade, be.di, rho_g, mu_g)
    y1_1 = _altura_primeira_celula(1.0, dim.v_gas, dim.alturas.total, rho_g, mu_g)
    y1_30 = _altura_primeira_celula(30.0, dim.v_gas, dim.alturas.total, rho_g, mu_g)

    base = be.di / 20.0          # ~20 celulas no diametro do bocal
    refino_jato = be.di / 40.0   # regiao do jato

    cartao = CartaoSetup(dimensionamento=dim)

    cartao.linhas["1. GEOMETRIA (cotas a partir da tangente inferior)"] = [
        ("Diametro interno do costado", f"{dim.D:.3f} m"),
        ("Altura tangente-tangente", f"{dim.alturas.total:.3f} m  (L/D = {dim.LD:.2f})"),
        ("Cota do HLL (piso do dominio fluido)", f"{dim.alturas.nivel_HLL:.3f} m"),
        ("Cota do eixo do bocal de entrada", f"{dim.alturas.cota_bocal_entrada:.3f} m"),
        ("Cota da base do demister", f"{dim.alturas.cota_base_demister:.3f} m"
            if crit.com_demister else "sem demister"),
        ("Bocal de entrada", f"{be.nps}, DI {be.di * 1000:.1f} mm"),
        ("Bocal de saida de gas", f"{dim.bocal_saida_gas.nps}, DI {dim.bocal_saida_gas.di * 1000:.1f} mm"),
        ("Trecho reto a montante do bocal", f">= {5 * be.di:.2f} m (5 diametros)"),
    ]

    cartao.linhas["2. FISICA (fase continua)"] = [
        ("Modelos", "Steady | Gas | Segregated Flow | Constant Density"),
        ("", "Turbulent | RANS | K-Omega Turbulence | SST (Menter) K-Omega"),
        ("", "All y+ Wall Treatment | Gravity"),
        ("Massa especifica do gas", f"{rho_g:.4f} kg/m3"),
        ("Viscosidade dinamica do gas", f"{mu_g:.3e} Pa.s"),
        ("Gravidade", f"[0, 0, -{G:.5f}] m/s2  (eixo do vaso em +Z)"),
        ("Pressao de referencia", f"{c.P_bara * 1e5:.0f} Pa"),
    ]

    cartao.linhas["3. CONDICOES DE CONTORNO"] = [
        ("Entrada - tipo", "Mass Flow Inlet"),
        ("Entrada - vazao massica de gas", f"{c.W_gas / 3600.0:.4f} kg/s"),
        ("Entrada - velocidade resultante", f"{be.velocidade:.2f} m/s"),
        ("Entrada - Reynolds do bocal", f"{Re_bocal:.3e}"),
        ("Entrada - intensidade turbulenta", f"{I_bocal * 100:.2f} %"),
        ("Entrada - escala de comprimento", f"{l_bocal * 1000:.1f} mm"),
        ("Saida de gas - tipo", "Pressure Outlet"),
        ("Saida de gas - pressao manometrica", "0 Pa (relativa a referencia)"),
        ("Superficie de liquido (HLL) - tipo", "Wall, no-slip"),
        ("Costado e tampos - tipo", "Wall, no-slip"),
    ]

    cartao.linhas["4. MALHA"] = [
        ("Modelos", "Polyhedral Mesher | Prism Layer Mesher | Surface Remesher"),
        ("Tamanho base", f"{base * 1000:.1f} mm  (~20 celulas no DI do bocal)"),
        ("Refino - bocal e regiao do jato", f"{refino_jato * 1000:.1f} mm"),
        ("Refino - volume do jato", f"cilindro de ~{3 * be.di:.2f} m a jusante do bocal"),
        ("Camadas de prisma", "12 a 15, razao de crescimento 1,3"),
        ("Altura da 1a celula para y+ ~ 1", f"{y1_1 * 1e6:.0f} um"),
        ("Altura da 1a celula para y+ ~ 30", f"{y1_30 * 1000:.2f} mm"),
        ("Contagem alvo", "3 a 8 milhoes de celulas (varie e mostre a independencia)"),
    ]

    cartao.linhas["5. FASE LAGRANGIANA (gotas)"] = [
        ("Modelo", "Lagrangian Multiphase | Material Particles | Liquid"),
        ("Acoplamento", "One-Way Coupling"),
        ("Massa especifica da gota", f"{c.rho_l:.1f} kg/m3"),
        ("Tensao interfacial", f"{c.sigma * 1000:.1f} mN/m"),
        ("Forcas", "Drag Force + Gravity  (as DUAS - ver nota)"),
        ("Lei de arrasto", "Schiller-Naumann (Spherical)"),
        ("Dispersao turbulenta", "Turbulent Dispersion LIGADA (ver nota)"),
        ("Injetor - tipo", "Part Injector na face do bocal de entrada"),
        ("Injetor - vazao massica de liquido", f"{c.W_liq / 3600.0:.4f} kg/s"),
        ("Injetor - velocidade", f"{be.velocidade:.2f} m/s (equilibrio com o gas)"),
        ("Distribuicao de tamanho", "MONODISPERSA, uma classe por rodada (ver cabecalho)"),
        ("Classes a varrer", ", ".join(f"{d:g}" for d in CLASSES_DE_GOTA_UM) + " um"),
        ("Parcelas por classe", "20.000 (verificar convergencia estatistica)"),
        ("Saida de gas - condicao", "Escape  (conta como ARRASTE)"),
        ("Superficie de liquido - condicao", "Trap   (conta como SEPARADO)"),
        ("Costado e tampos - condicao", "Trap   (conta como SEPARADO, filme drena)"),
    ]

    cartao.linhas["6. LIMITES FISICOS DO PROPRIO CASO"] = [
        ("v_max de Souders-Brown", f"{dim.sb.v_max:.4f} m/s"),
        ("Velocidade superficial real", f"{dim.v_gas:.4f} m/s  ({dim.uso_do_limite * 100:.0f}% do limite)"),
        ("Gota implicita no K (a v_max)", f"{dim.d_implicito * 1e6:.0f} um"),
        ("Gota implicita na velocidade real", f"{dim.d_implicito_operacao * 1e6:.0f} um"),
        ("Maior gota estavel no bocal (We_c=12)", f"{dim.d_max_estavel_bocal * 1e6:.0f} um"),
        ("Razao de atomizacao", f"{dim.razao_de_atomizacao:.1f}x"),
    ]

    tabela = tabela_de_velocidades_terminais(CLASSES_DE_GOTA_UM, rho_g, c.rho_l, mu_g)
    cartao.linhas["7. CASO DE VERIFICACAO - gota em gas parado"] = [
        (f"d = {t.d_um:.0f} um", f"v_t = {t.v_t:.5f} m/s   (Re = {t.Re:.2f}, Cd = {t.Cd:.3f})")
        for t in tabela
    ]

    cartao.notas = [
        "RODE O CASO DE VERIFICACAO PRIMEIRO. Caixa fechada, gas parado, uma classe "
        "de gota, gravidade ligada, sem escoamento. A velocidade assintotica tem que "
        "bater com a tabela da secao 7 dentro de 1%. Se nao bater, pare: e configuracao, "
        "nao fisica.",

        "O erro mais comum nesse teste e ligar Gravity no continuum e esquecer de "
        "incluir a forca Gravity na fase lagrangiana. A gota flutua, o caso 'converge', "
        "e o resultado nao significa nada.",

        "A tabela da secao 7 usa Schiller-Naumann. Se voce marcar outra lei de arrasto "
        "no solver, regere a tabela com a mesma lei (arraste.tabela_de_velocidades_"
        "terminais(..., lei=...)) antes de comparar. Comparar contra a lei errada "
        "produz uma discrepancia de 10-20% que parece bug e nao e.",

        "DISPERSAO TURBULENTA e o item que mais muda o resultado. Sem ela as gotas "
        "seguem a linha de corrente media e a eficiencia sai otimista. Rode as duas "
        "e mostre a diferenca: isso sozinho ja e meio post.",

        "Com dispersao turbulenta ligada o resultado e ESTOCASTICO. Rode duas vezes "
        "com sementes diferentes, ou parta as parcelas em duas metades e compare a "
        "eficiencia. Se as duas metades diferem mais que ~1 ponto percentual, "
        "aumente a contagem de parcelas antes de reportar qualquer numero.",

        "RANS estacionario pode nao convergir para o jato de entrada num vaso grande - "
        "o jato tende a bater e oscilar. Se os residuos estagnarem e os monitores "
        "ficarem oscilando com amplitude estavel, isso e fisica, nao numerica: a "
        "solucao estacionaria nao existe. Use o campo estacionario como condicao "
        "inicial e passe para URANS.",

        "Resolva o campo de gas ate convergir ANTES de ligar a fase lagrangiana. Com "
        "acoplamento de uma via as gotas nao alteram o gas, entao o tracking pode ser "
        "feito em pos-processamento sobre o campo congelado. Isso torna a varredura de "
        "10 classes barata: um campo de gas, dez rodadas de tracking.",

        "O demister NAO deve ser modelado como geometria resolvida. Se precisar "
        "represente-o como meio poroso com resistencia inercial calibrada pela perda de "
        "carga do fabricante, ou simplesmente termine o dominio na base da tela e "
        "reporte a distribuicao de velocidade e de gota que CHEGA nela. A segunda opcao "
        "e mais honesta e e o que interessa: a tela do fabricante tem limite de carga "
        "local, e a media nao diz se ele foi violado.",
    ]
    return cartao
