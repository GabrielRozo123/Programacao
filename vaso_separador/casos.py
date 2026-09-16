"""Casos de processo representativos de planta petroquimica brasileira.

IMPORTANTE - ORIGEM DOS DADOS
-----------------------------
Os numeros abaixo sao REPRESENTATIVOS, montados a partir de literatura aberta e
de ordens de grandeza tipicas de central de materias-primas e planta de
poliolefinas. NAO sao dados de nenhuma planta especifica e nao substituem folha
de dados de corrente.

Para um estudo real: peca ao cliente o balanco de massa e energia da corrente de
entrada (P, T, composicao, Z, vazao por fase) e as propriedades de transporte do
simulador de processo. A classe Corrente aceita esses valores direto, e todo o
resto do calculo e reproduzido sem nenhuma alteracao de codigo.

As propriedades de liquido e de transporte foram estimadas para as condicoes
indicadas; confira contra o simulador antes de usar em documento de engenharia.
"""

from __future__ import annotations

from .dimensionamento import Corrente, Criterios

# ---------------------------------------------------------------------------
# 1. Vaso de succao do compressor de refrigeracao de propeno
# ---------------------------------------------------------------------------
# Ciclo de refrigeracao a propeno de planta de polipropileno. E o caso mais
# ilustrativo do modo de falha: arraste aqui e golpe de liquido no compressor.
PROPENO_REFRIGERACAO = Corrente(
    nome="Vaso de sucção — compressor de refrigeração de propeno",
    P_bara=1.40,      # propeno saturado a -40 degC
    T_C=-40.0,
    MM=42.08,
    Z=0.96,
    rho_l=613.0,      # propeno liquido a -40 degC
    mu_g=6.5e-6,
    sigma=0.019,
    W_gas=54_000.0,   # ~6 MW de carga termica / ~400 kJ/kg de calor latente
    W_liq=2_700.0,    # 5% em massa de liquido arrastado do evaporador
    servico="Refrigeração a propeno, planta de poliolefinas",
    rotulo="Refrigeração a propeno\n1,4 bara",
    fonte_dados="Representativo. Propriedades do propeno saturado a -40 degC.",
)

# ---------------------------------------------------------------------------
# 2. Vaso de succao do 1o estagio do compressor de gas de craqueamento
# ---------------------------------------------------------------------------
# Central de materias-primas (craqueador). Gas leve (H2/CH4/C2/C3) saindo da
# torre de agua de resfriamento; o liquido e condensado de hidrocarboneto e agua.
GAS_DE_CARGA_1O_ESTAGIO = Corrente(
    nome="Vaso de sucção — 1º estágio do compressor de gás de craqueamento",
    P_bara=1.45,
    T_C=40.0,
    MM=26.5,
    Z=0.99,
    rho_l=640.0,      # condensado de hidrocarboneto com agua dispersa
    mu_g=1.05e-5,
    sigma=0.020,
    W_gas=140_000.0,
    W_liq=7_000.0,
    servico="Compressão de gás de craqueamento, central de matérias-primas",
    rotulo="Gás de craqueamento\n1º estágio, 1,45 bara",
    fonte_dados="Representativo de craqueador de ~500 kt/a de eteno.",
)

# ---------------------------------------------------------------------------
# 3. Vaso de succao de estagio de alta pressao
# ---------------------------------------------------------------------------
# Mesmo trem de compressao, estagio final. Existe para mostrar a correcao de K
# com a pressao mordendo de verdade.
GAS_DE_CARGA_ALTA_PRESSAO = Corrente(
    nome="Vaso de sucção — estágio de alta pressão do compressor de gás de craqueamento",
    P_bara=28.0,
    T_C=40.0,
    MM=25.0,
    Z=0.93,
    rho_l=520.0,
    mu_g=1.15e-5,
    sigma=0.010,
    W_gas=138_000.0,
    W_liq=2_000.0,
    servico="Compressão de gás de craqueamento, estágio de alta pressão",
    rotulo="Gás de craqueamento\nalta pressão, 28 bara",
    fonte_dados="Representativo. Note a correcao de K: 28 bara = ~391 psig.",
)

# ---------------------------------------------------------------------------
# 4. Vaso de nocaute de tocha (flare KO drum)
# ---------------------------------------------------------------------------
# Dimensionado pela API 521, que prescreve remocao de gotas numa faixa de
# diametro em vez de prescrever K. Sem demister (nao se coloca tela em linha de
# tocha, por risco de entupimento e bloqueio do alivio).
KO_DRUM_TOCHA = Corrente(
    nome="Vaso de nocaute de tocha (flare KO drum)",
    P_bara=1.50,
    T_C=60.0,
    MM=30.0,
    Z=0.99,
    rho_l=600.0,
    mu_g=1.10e-5,
    sigma=0.018,
    W_gas=45_000.0,   # contingencia dimensionante de uma unidade
    W_liq=4_500.0,
    servico="Sistema de alívio e tocha",
    rotulo="Nocaute de tocha\n1,5 bara, sem demister",
    fonte_dados="Representativo, KO drum de tocha de UMA unidade. "
                "Vaso de nocaute de tocha PRINCIPAL, na contingencia global da planta, "
                "quase sempre e HORIZONTAL - a vazao volumetrica de alivio torna o vertical "
                "grande demais. Vaso horizontal esta fora do escopo deste modulo.",
)

CASOS: dict[str, Corrente] = {
    "propeno_refrigeracao": PROPENO_REFRIGERACAO,
    "gas_de_carga_1o_estagio": GAS_DE_CARGA_1O_ESTAGIO,
    "gas_de_carga_alta_pressao": GAS_DE_CARGA_ALTA_PRESSAO,
    "ko_drum_tocha": KO_DRUM_TOCHA,
}

# Criterios de projeto associados a cada caso. Separados da corrente de
# proposito: as condicoes de processo vem do cliente, os criterios vem da norma
# adotada e da filosofia de projeto.
CRITERIOS_POR_CASO: dict[str, Criterios] = {
    "propeno_refrigeracao": Criterios(
        fator_K="succao_de_compressor",
        com_demister=True,
        dispositivo_de_entrada="sem_dispositivo",
        tempo_holdup_min=5.0,
        tempo_surge_min=2.0,
    ),
    "gas_de_carga_1o_estagio": Criterios(
        fator_K="succao_de_compressor",
        com_demister=True,
        dispositivo_de_entrada="chapa_defletora",
        tempo_holdup_min=5.0,
        tempo_surge_min=2.0,
    ),
    "gas_de_carga_alta_pressao": Criterios(
        fator_K="succao_de_compressor",
        com_demister=True,
        dispositivo_de_entrada="palhetas",
        tempo_holdup_min=3.0,
        tempo_surge_min=2.0,
    ),
    "ko_drum_tocha": Criterios(
        fator_K="gpsa_vertical_sem_demister",
        com_demister=False,
        dispositivo_de_entrada="sem_dispositivo",
        tempo_holdup_min=20.0,   # API 521: volume da contingencia, nao tempo de reacao
        tempo_surge_min=10.0,
    ),
}
