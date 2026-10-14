"""Constantes físicas e conversões de unidade."""

G = 9.80665            # aceleração da gravidade padrão [m/s²]
P_ATM = 101325.0       # pressão atmosférica padrão [Pa]
T0_K = 273.15          # 0 °C em kelvin
W_PARA_BTUH = 3.412142  # 1 W = 3,412142 Btu/h
SEGUNDOS_DIA = 86400.0


def C_para_K(t_c: float) -> float:
    return t_c + T0_K


def K_para_C(t_k: float) -> float:
    return t_k - T0_K


def bar(p_pa: float) -> float:
    return p_pa / 1e5
