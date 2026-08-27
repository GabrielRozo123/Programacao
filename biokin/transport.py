"""Transporte de massa em monolitos de canais quadrados.

Por que isto entra num pacote de discriminação de mecanismos: se houver
limitação difusional, a cinética *observada* não é a intrínseca. A ordem
aparente cai para metade, a energia de ativação aparente cai pela metade,
e os termos de inibição do denominador ficam achatados. Discriminar
mecanismos sobre dados disfarçados por difusão leva ao mecanismo errado
com excelente ajuste estatístico — o modo de falha mais perigoso deste
tipo de estudo.

O módulo faz três coisas:

1. estima os coeficientes de transporte (filme externo no canal, difusão
   efetiva no washcoat);
2. calcula fatores de efetividade;
3. aplica os critérios de Weisz-Prater, Mears e Carberry, que dizem se os
   dados podem ser tratados como intrínsecos.

Unidades: comprimento em m, tempo em min, concentração em mol/L,
difusividade em m²/s (convertida internamente).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

#: Sherwood assintótico, duto quadrado, parede a concentração constante.
SH_SQUARE_DUCT = 2.98

#: Limiar clássico dos critérios de Weisz-Prater e Mears.
CRITERION_THRESHOLD = 0.15


@dataclass
class MonolithGeometry:
    """Geometria de um monolito de canais quadrados com washcoat."""

    cell_density_cpsi: float = 400.0  # células por polegada quadrada
    wall_thickness_m: float = 1.5e-4
    washcoat_thickness_m: float = 3.0e-5
    length_m: float = 0.10
    washcoat_porosity: float = 0.45
    washcoat_tortuosity: float = 3.5
    washcoat_density_kg_m3: float = 1300.0

    @property
    def cell_pitch_m(self) -> float:
        """Passo da célula (lado do canal + parede)."""
        cells_per_m2 = self.cell_density_cpsi / (0.0254**2)
        return 1.0 / math.sqrt(cells_per_m2)

    @property
    def channel_side_m(self) -> float:
        """Lado livre do canal, descontando parede e washcoat."""
        side = self.cell_pitch_m - self.wall_thickness_m - 2 * self.washcoat_thickness_m
        if side <= 0:
            raise ValueError("geometria inconsistente: canal com lado não positivo")
        return side

    @property
    def hydraulic_diameter_m(self) -> float:
        """Para canal quadrado, ``d_h`` é o próprio lado."""
        return self.channel_side_m

    @property
    def open_frontal_area(self) -> float:
        """Fração de área frontal aberta (porosidade do monolito)."""
        return (self.channel_side_m / self.cell_pitch_m) ** 2

    @property
    def specific_surface_m2_m3(self) -> float:
        """Área geométrica por volume de *reator*: ``a_v = 4 eps / d_h``."""
        return 4.0 * self.open_frontal_area / self.hydraulic_diameter_m

    @property
    def washcoat_volume_fraction(self) -> float:
        """Volume de washcoat por volume de reator."""
        a = self.channel_side_m
        outer = a + 2 * self.washcoat_thickness_m
        return (outer**2 - a**2) / self.cell_pitch_m**2

    @property
    def catalyst_density_g_L(self) -> float:
        """Massa de washcoat por litro de reator [g/L]."""
        return (
            self.washcoat_volume_fraction
            * self.washcoat_density_kg_m3
            * 1000.0  # kg->g
            / 1000.0  # m³->L
        )


@dataclass
class FluidProperties:
    """Propriedades do meio reacional (mistura óleo/metanol)."""

    density_kg_m3: float = 820.0
    viscosity_Pa_s: float = 6.0e-4
    diffusivity_m2_s: float = 7.5e-10  # triglicerídeo em metanol, ~60 °C

    def reynolds(self, velocity_m_s: float, d_h: float) -> float:
        return self.density_kg_m3 * velocity_m_s * d_h / self.viscosity_Pa_s

    def schmidt(self) -> float:
        return self.viscosity_Pa_s / (self.density_kg_m3 * self.diffusivity_m2_s)


def wilke_chang_diffusivity(
    T_K: float,
    viscosity_Pa_s: float,
    solvent_molar_mass_g_mol: float = 32.04,
    solute_molar_volume_cm3_mol: float = 1000.0,
    association_factor: float = 1.9,
) -> float:
    """Difusividade líquida por Wilke-Chang, em m²/s.

    Valores por omissão: soluto volumoso (triglicerídeo, V ~ 1000 cm³/mol)
    em metanol (fator de associação 1,9).
    """
    mu_cP = viscosity_Pa_s * 1e3
    D_cm2_s = (
        7.4e-8
        * math.sqrt(association_factor * solvent_molar_mass_g_mol)
        * T_K
        / (mu_cP * solute_molar_volume_cm3_mol**0.6)
    )
    return D_cm2_s * 1e-4


def sherwood_number(
    reynolds: float, schmidt: float, d_h: float, length: float
) -> float:
    """Sherwood médio em canal quadrado laminar (correlação de Hawthorn).

    ``Sh = Sh_inf * [1 + 0.095 * (d_h/L) * Re * Sc]^0.45``

    O termo de entrada domina em canais curtos e vazões altas, situação
    comum em monolitos de bancada.
    """
    graetz = (d_h / length) * reynolds * schmidt
    return SH_SQUARE_DUCT * (1.0 + 0.095 * graetz) ** 0.45


def mass_transfer_coefficient(
    geom: MonolithGeometry, fluid: FluidProperties, velocity_m_s: float
) -> float:
    """Coeficiente de transferência de massa no filme externo [m/s]."""
    d_h = geom.hydraulic_diameter_m
    Re = fluid.reynolds(velocity_m_s, d_h)
    Sc = fluid.schmidt()
    Sh = sherwood_number(Re, Sc, d_h, geom.length_m)
    return Sh * fluid.diffusivity_m2_s / d_h


def volumetric_mass_transfer_per_min(
    geom: MonolithGeometry, fluid: FluidProperties, velocity_m_s: float
) -> float:
    """``k_c * a_v`` em 1/min — coeficiente volumétrico de transferência."""
    kc = mass_transfer_coefficient(geom, fluid, velocity_m_s)
    return kc * geom.specific_surface_m2_m3 * 60.0


def effective_diffusivity(geom: MonolithGeometry, fluid: FluidProperties) -> float:
    """Difusividade efetiva no washcoat: ``D_eff = D * eps / tau``."""
    return (
        fluid.diffusivity_m2_s * geom.washcoat_porosity / geom.washcoat_tortuosity
    )


# ----------------------------------------------------------------------
# fator de efetividade
# ----------------------------------------------------------------------
def generalized_thiele(
    rate_of_C,
    C_surface: float,
    thickness_m: float,
    D_eff_m2_s: float,
    density_kg_m3: float,
    n_quad: int = 25,
) -> float:
    """Módulo de Thiele generalizado (Aris) para cinética arbitrária.

    ``phi = L * r(Cs) / sqrt( 2 * D_eff * int_0^Cs r(C) dC )``

    ``rate_of_C`` recebe a concentração do reagente-chave em mol/L e devolve
    a velocidade específica em mol/(g_cat·min). A forma generalizada é o que
    permite aplicar o conceito a leis LHHW, onde a "ordem" não é constante.
    """
    if C_surface <= 0:
        return 0.0
    grid = np.linspace(0.0, C_surface, n_quad)
    r_grid = np.array([max(rate_of_C(c), 0.0) for c in grid])
    r_s = r_grid[-1]
    if r_s <= 0:
        return 0.0

    # mol/(g·min) -> mol/(m³_wc·s):  * (g/m³) / 60
    to_vol = density_kg_m3 * 1e3 / 60.0
    # concentração mol/L -> mol/m³ : * 1e3
    integral = np.trapezoid(r_grid * to_vol, grid * 1e3)
    if integral <= 0:
        return 0.0
    return thickness_m * (r_s * to_vol) / math.sqrt(2.0 * D_eff_m2_s * integral)


def effectiveness_factor(phi: float) -> float:
    """Efetividade de uma placa plana: ``eta = tanh(phi)/phi``."""
    if phi < 1e-8:
        return 1.0
    if phi > 50.0:
        return 1.0 / phi
    return math.tanh(phi) / phi


# ----------------------------------------------------------------------
# critérios de diagnóstico
# ----------------------------------------------------------------------
@dataclass
class TransportDiagnostics:
    """Resultado dos critérios clássicos de exclusão de gradientes."""

    weisz_prater: float
    mears: float
    carberry: float
    effectiveness: float
    thiele: float
    k_c_a_v_per_min: float

    @property
    def internal_ok(self) -> bool:
        return self.weisz_prater < CRITERION_THRESHOLD

    @property
    def external_ok(self) -> bool:
        return self.mears < CRITERION_THRESHOLD

    @property
    def intrinsic(self) -> bool:
        """``True`` se os dados podem ser lidos como cinética intrínseca."""
        return self.internal_ok and self.external_ok

    def report(self) -> str:
        def mark(ok: bool) -> str:
            return "OK " if ok else "!! "

        return (
            f"  {mark(self.internal_ok)}Weisz-Prater = {self.weisz_prater:.3g} "
            f"(< {CRITERION_THRESHOLD} -> sem limitação interna)\n"
            f"  {mark(self.external_ok)}Mears        = {self.mears:.3g} "
            f"(< {CRITERION_THRESHOLD} -> sem limitação externa)\n"
            f"     Carberry     = {self.carberry:.3g}  "
            f"(fração da força motriz consumida no filme)\n"
            f"     efetividade  = {self.effectiveness:.3f}  (phi = {self.thiele:.3g})\n"
            f"     k_c·a_v      = {self.k_c_a_v_per_min:.4g} 1/min"
        )


def diagnose(
    rate_of_C,
    C_bulk: float,
    geom: MonolithGeometry,
    fluid: FluidProperties,
    velocity_m_s: float,
    reaction_order: float = 1.0,
) -> TransportDiagnostics:
    """Aplica os critérios de exclusão de gradientes a uma condição.

    ``rate_of_C(C)`` devolve a velocidade específica do reagente-chave em
    mol/(g_cat·min).
    """
    D_eff = effective_diffusivity(geom, fluid)
    kc = mass_transfer_coefficient(geom, fluid, velocity_m_s)
    kca = kc * geom.specific_surface_m2_m3 * 60.0  # 1/min

    r_obs = max(rate_of_C(C_bulk), 0.0)  # mol/(g·min)
    rho_wc = geom.washcoat_density_kg_m3
    r_vol = r_obs * rho_wc * 1e3 / 60.0  # mol/(m³_wc·s)
    C_m3 = C_bulk * 1e3  # mol/m³

    L = geom.washcoat_thickness_m
    weisz = r_vol * L**2 / (D_eff * C_m3) if C_m3 > 0 else 0.0

    # Mears usa a velocidade por volume de reator contra o fluxo no filme
    r_reactor = r_obs * geom.catalyst_density_g_L  # mol/(L·min)
    mears = (
        r_reactor * reaction_order / (kca * C_bulk) if C_bulk > 0 and kca > 0 else 0.0
    )
    carberry = r_reactor / (kca * C_bulk) if C_bulk > 0 and kca > 0 else 0.0

    phi = generalized_thiele(rate_of_C, C_bulk, L, D_eff, rho_wc)
    return TransportDiagnostics(
        weisz_prater=weisz,
        mears=mears,
        carberry=carberry,
        effectiveness=effectiveness_factor(phi),
        thiele=phi,
        k_c_a_v_per_min=kca,
    )
