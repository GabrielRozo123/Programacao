"""Carga de resíduo pós-consumo misto (lixo marinho) e cinética de pirólise por pseudocomponentes.

Cada pseudocomponente da carga reage por uma lei cinética da literatura aberta e se divide em grupos de
produtos ("lumps"):

  G_HC  gás não condensável de hidrocarbonetos (CH4, C2–C4, H2)        PCI ~46 MJ/kg
  G_OX  gás oxigenado (CO, CO2, um pouco de CH4 e H2)                  PCI ~8 MJ/kg
  O     óleo leve (C5–C20)          W  cera (C21+)          A  aromáticos (estireno, benzeno)
  OX    oxigenados e sublimados do PET (ácido benzoico/tereftálico)
  TAR   alcatrão primário da celulose (reage no espaço livre: vira gás ou coque)
  H2O   água (umidade livre e água de pirólise)      HCl  cloreto de hidrogênio do PVC
  CHAR  carvão (fica no leito)                       ASH  cinzas, areia e sal (inerte)

Leis cinéticas (k = A exp(−E/RT)):
  rs2    cisão aleatória L = 2: dx/dt = k(1 − x), α = x² (poliolefinas e PS; Aboulkas 2010, A ajustado
         aos picos de DTG de consenso a 10 K/min, como no reator agitado)
  first  primeira ordem: dα/dt = k(1 − α) (PET, frações da borracha)
  p2     nucleação P2 com semente: s = √α, ds/dt = k (PVC, etapa I de desidrocloração)
  f3     terceira ordem: dα/dt = k(1 − α)³ (PVC, etapa II, resíduo poliênico)
  sc     Shafizadeh–Chin: três reações paralelas de 1ª ordem para gás, alcatrão e carvão (celulósicos)
Umidade: platô de ebulição a 100 °C (o calor que chega acima disso evapora a água).

Rendimentos por kg de componente reagido para um tambor em batelada a ~500 °C (síntese da pesquisa,
docs/brief_tambor_batelada.md): composições e números com a fonte ao lado. [H] = hipótese de projeto.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

R_GAS = 8.314462618
T0 = 298.15

LUMPS = ["G_HC", "G_OX", "O", "W", "A", "OX", "TAR", "H2O", "HCl"]       # saem do leito como vapor
SOLIDS = ["CHAR", "ASH"]
CONDENSABLE = ["O", "W", "A", "OX", "TAR"]
LHV = {"G_HC": 46.3e6, "G_OX": 8.0e6}          # caso A da pesquisa (46,3 MJ/kg) e mistura CO/CO2 [H]
AFR = {"G_HC": 15.43, "G_OX": 2.2}             # ar estequiométrico [kg/kg]


@dataclass(frozen=True)
class Component:
    key: str
    name: str
    law: str                       # rs2 | first | p2 | f3 | sc | water | inert
    A: float = 0.0                 # [1/s]
    E: float = 0.0                 # [J/mol]
    yields: dict = field(default_factory=dict)   # kg de produto por kg reagido (lumps, CHAR, ou componente)
    dH: float = 0.0                # calor de reação + vaporização dos produtos [J/kg reagido] (> 0 endotérmico)
    cp: float = 1800.0             # calor específico do sólido [J/(kg K)]
    cp_l: float = 0.0              # calor específico do fundido (0 = igual ao sólido)
    Tm: float = 0.0                # fusão [K] (0 = não funde)
    hm: float = 0.0                # calor latente de fusão [J/kg]
    rho_loose: float = 100.0       # massa específica aparente como carregado (peso relativo) [kg/m³]
    rho_dense: float = 900.0       # massa específica aparente depois de fundir/compactar [kg/m³]
    k_dense: float = 0.2           # condutividade do material denso [W/(m K)]
    sc: tuple = ()                 # Shafizadeh–Chin: ((A, E) gás, (A, E) alcatrão, (A, E) carvão)
    seed: float = 0.0              # semente da lei p2 (α inicial)
    color: tuple = (0.6, 0.6, 0.6)
    group: str = ""                # rótulo para gráficos
    source: str = ""

    def k(self, T):
        return self.A * np.exp(-self.E / (R_GAS * np.asarray(T, float)))


def _sc_rates(c: Component, T):
    return [a * np.exp(-e / (R_GAS * np.asarray(T, float))) for a, e in c.sc]


# ----------------------------------------------------------------- componentes
PO_SRC = "E: Aboulkas 2010; A ajustado ao pico de DTG de consenso a 10 K/min; rendimentos: pesquisa R2 [H]"
COMPONENTS = {
    "H2O": Component("H2O", "umidade", "water", yields={"H2O": 1.0}, dH=2.257e6, cp=4180.0,
                     rho_loose=1e9, rho_dense=1e9, k_dense=0.6, color=(0.35, 0.55, 0.85), group="água",
                     source="h_fg a 100 °C"),
    "LDPE": Component("LDPE", "PEBD (filmes, sacolas)", "rs2", 1.92e13, 215e3,
                      {"G_HC": 0.10, "O": 0.55, "W": 0.34, "CHAR": 0.01}, 0.92e6, 1900.0, 2600.0,
                      383.15, 130e3, 45.0, 740.0, 0.22, color=(0.92, 0.92, 0.88), group="poliolefinas",
                      source=PO_SRC),
    "HDPE": Component("HDPE", "PEAD (frascos, tampas)", "rs2", 5.2e14, 238e3,
                      {"G_HC": 0.10, "O": 0.55, "W": 0.34, "CHAR": 0.01}, 0.92e6, 1900.0, 2600.0,
                      403.15, 200e3, 70.0, 740.0, 0.25, color=(0.30, 0.55, 0.85), group="poliolefinas",
                      source=PO_SRC),
    "PP": Component("PP", "PP (tampas, redes, embalagens)", "rs2", 6.98e10, 179e3,
                    {"G_HC": 0.12, "O": 0.60, "W": 0.26, "CHAR": 0.02}, 1.0e6, 1900.0, 2600.0,
                    438.15, 90e3, 90.0, 730.0, 0.20, color=(0.95, 0.80, 0.25), group="poliolefinas",
                    source=PO_SRC + "; ΔH ~1,0 MJ/kg (faixa 0,6–1,3)"),
    "PS": Component("PS", "PS/EPS (isopor, copos)", "rs2", 4.1e11, 180e3,
                    {"A": 0.65, "O": 0.25, "G_HC": 0.05, "CHAR": 0.05}, 0.8e6, 1500.0, 2000.0,
                    373.15, 0.0, 25.0, 950.0, 0.15, color=(0.97, 0.97, 0.97), group="PS",
                    source="E meio da faixa 150–204 kJ/mol; estireno ~0,65 [S/H]"),
    "PET": Component("PET", "PET (garrafas, poliéster)", "first", 2.59e13, 210e3,
                     {"CHAR": 0.15, "OX": 0.40, "G_OX": 0.43, "H2O": 0.02}, 0.4e6, 1300.0, 1900.0,
                     528.15, 50e3, 40.0, 1150.0, 0.20, color=(0.55, 0.85, 0.75), group="PET",
                     source="Dubdub & Al-Yaari 2023; rendimentos [H] (PET forma sublimados que sujam o condensador)"),
    "PVC": Component("PVC", "PVC (tubos, cabos) – etapa I", "p2", 3.0e4, 75e3,
                     {"HCl": 0.583, "PVCr": 0.417}, 0.4e6, 1000.0, 1500.0, 0.0, 0.0, 300.0, 1300.0, 0.17,
                     seed=1e-4, color=(0.85, 0.45, 0.35), group="PVC",
                     source="desidrocloração P2 (75 kJ/mol); HCl 0,583 kg/kg; ΔH [H, não verificado]"),
    "PVCr": Component("PVCr", "resíduo poliênico do PVC – etapa II", "f3", 8.07e7, 140e3,
                      {"A": 0.55, "G_HC": 0.15, "CHAR": 0.25, "O": 0.05}, 0.4e6, 1200.0, 0.0, 0.0, 0.0,
                      400.0, 1200.0, 0.17, color=(0.45, 0.25, 0.20), group="PVC",
                      source="F3 (140 kJ/mol); produtos [H] limitados pelo carbono fixo 5–6 % do PVC"),
    "CELL": Component("CELL", "celulósicos (papel, madeira, coco, algas)", "sc",
                      yields={}, dH=0.3e6, cp=1500.0, rho_loose=150.0, rho_dense=450.0, k_dense=0.12,
                      sc=((1.44e4, 88.6e3), (4.12e6, 112.7e3), (7.38e5, 106.5e3)),
                      color=(0.70, 0.52, 0.30), group="celulósicos",
                      source="Shafizadeh–Chin (carvalho), via Navarrete 2024; ΔH [H] (faixa −0,3 a +0,5 MJ/kg)"),
    "RUBa": Component("RUBa", "borracha – fração leve", "first", 3.8e2 / 60, 33.1e3,
                      {"O": 0.667, "A": 0.083, "G_HC": 0.25}, 0.5e6, 1900.0, 0.0, 0.0, 0.0, 400.0, 1100.0, 0.20,
                      color=(0.15, 0.15, 0.15), group="borracha", source="Cherbański 2017 (3 componentes)"),
    "RUBb": Component("RUBb", "borracha – óleos e aditivos", "first", 3.1e9 / 60, 124.1e3,
                      {"O": 0.667, "A": 0.083, "G_HC": 0.25}, 0.5e6, 1900.0, 0.0, 0.0, 0.0, 400.0, 1100.0, 0.20,
                      color=(0.15, 0.15, 0.15), group="borracha", source="Cherbański 2017"),
    "RUBc": Component("RUBc", "borracha – elastômero", "first", 1.6e11 / 60, 161.6e3,
                      {"O": 0.667, "A": 0.083, "G_HC": 0.25}, 0.5e6, 1900.0, 0.0, 0.0, 0.0, 400.0, 1100.0, 0.20,
                      color=(0.15, 0.15, 0.15), group="borracha", source="Cherbański 2017"),
    "CB": Component("CB", "negro de fumo da borracha", "inert", cp=1100.0, rho_loose=400.0, rho_dense=500.0,
                    k_dense=0.15, color=(0.08, 0.08, 0.08), group="borracha", source="carvão da borracha 38–40 %"),
    "INERT": Component("INERT", "areia, conchas e sal", "inert", cp=850.0, rho_loose=1300.0, rho_dense=1500.0,
                       k_dense=0.35, color=(0.80, 0.72, 0.55), group="inertes",
                       source="agregado fino 10,6 % (rejeitos do Rio, Cruz 2024)"),
    "CHAR": Component("CHAR", "carvão formado", "inert", cp=1100.0, rho_loose=300.0, rho_dense=350.0,
                      k_dense=0.12, color=(0.10, 0.09, 0.08), group="carvão", source="—"),
}
# celulósicos: o "alcatrão" primário sai como TAR; o "gás" como G_OX + água [H, calibrado para dar, a 500 °C,
# carvão ~0,29, orgânico ~0,25, água ~0,22, gás ~0,24 kg/kg (pesquisa R2, faixas de Navarrete e Fulgencio)]
SC_PRODUCTS = ({"G_OX": 0.75, "H2O": 0.25}, {"TAR": 0.62, "H2O": 0.38}, {"CHAR": 1.0})

ORDER = list(COMPONENTS)
IDX = {k: i for i, k in enumerate(ORDER)}
REACTIVE = [k for k in ORDER if COMPONENTS[k].law not in ("inert", "water")]


@dataclass
class Charge:
    """Carga do tambor: massa úmida, umidade e composição seca (frações mássicas, normalizadas)."""
    name: str = "lixo marinho misto (caso base)"
    mass: float = 600.0             # kg úmidos por batelada
    moisture: float = 0.15          # fração mássica de água livre (base úmida)
    dry: dict = field(default_factory=lambda: {
        "LDPE": 25, "HDPE": 15, "PP": 20, "PS": 12, "PET": 6, "PVC": 2, "RUB": 3, "CELL": 8, "INERT": 9})
    fill: float = 0.62              # fração do tambor ocupada pela carga solta (≤ 2/3)
    source: str = ("composição seca de projeto [H] (pesquisa R2: PE 40, PP 20, PS 12, PET 6, PVC 2, borracha 3, "
                   "celulósicos 8, inertes 9 %); 0,5–0,8 t por batelada, enchimento ≤ 2/3")

    def masses(self) -> dict:
        d = {k: float(v) for k, v in self.dry.items()}
        tot = sum(d.values())
        dry_mass = self.mass * (1 - self.moisture)
        m = {k: 0.0 for k in ORDER}
        m["H2O"] = self.mass * self.moisture
        for k, v in d.items():
            mk = dry_mass * v / tot
            if k == "RUB":       # Cherbański: 60 % voláteis em 3 frações (z = 0,053/0,294/0,653), 40 % negro de fumo
                for kk, z in (("RUBa", 0.053), ("RUBb", 0.294), ("RUBc", 0.653)):
                    m[kk] += 0.60 * mk * z
                m["CB"] += 0.40 * mk
            else:
                m[k] += mk
        return m

    def describe(self) -> str:
        d = self.dry
        tot = sum(d.values())
        return (f"{self.mass:.0f} kg úmidos ({100 * self.moisture:.0f} % de água); seco: "
                + ", ".join(f"{k} {100 * v / tot:.0f}%" for k, v in d.items()))


CHARGES = {
    "base": Charge(),
    "plastico_triado": Charge("plástico triado (poliolefinas)", 600.0, 0.05,
                              {"LDPE": 45, "HDPE": 20, "PP": 30, "PS": 3, "INERT": 2}),
    "rejeito_rio": Charge("rejeito de cooperativa do Rio (Cruz 2024)", 600.0, 0.15,
                          {"LDPE": 9, "HDPE": 2, "PP": 12, "PS": 30, "PET": 13, "PVC": 4, "CELL": 14, "RUB": 2,
                           "INERT": 14}),
}


# ---------------------------------------------------------------- propriedades
def melt_fraction(c: Component, T):
    """Fração fundida (rampa suave de ±8 K em torno de Tm)."""
    if c.Tm <= 0:
        return np.zeros_like(np.asarray(T, float))
    return np.clip((np.asarray(T, float) - (c.Tm - 8.0)) / 16.0, 0.0, 1.0)


def apparent_cp(c: Component, T):
    """c_p aparente: sensível (sólido → fundido) + calor latente espalhado na rampa de fusão."""
    T = np.asarray(T, float)
    if c.Tm <= 0:
        return np.full_like(T, c.cp)
    f = melt_fraction(c, T)
    cpl = c.cp_l or c.cp
    lat = np.where((T > c.Tm - 8.0) & (T < c.Tm + 8.0), c.hm / 16.0, 0.0)
    return (1 - f) * c.cp + f * cpl + lat


def sensible_enthalpy(c: Component, T):
    """h(T) − h(T0) por integração analítica da c_p aparente [J/kg]."""
    T = np.asarray(T, float)
    if c.Tm <= 0:
        return c.cp * (T - T0)
    cpl = c.cp_l or c.cp
    a, b = c.Tm - 8.0, c.Tm + 8.0
    Ts = np.minimum(T, a)
    h = c.cp * (Ts - T0)
    Tm_ = np.clip(T, a, b)
    # na rampa: c_p varia linearmente de cp a cpl, mais o latente uniforme
    x = (Tm_ - a)
    h = h + c.cp * x + 0.5 * (cpl - c.cp) * x ** 2 / 16.0 + c.hm * x / 16.0
    h = h + cpl * np.maximum(T - b, 0.0)
    return h


# ------------------------------------------------------------------- cinética
class KineticState:
    """Estado químico de N volumes de leito (fatias ou camadas): massas iniciais e progresso por componente.

    m0[c]: massa de referência (inicial, ou acumulada para os intermediários PVCr e CHAR);
    p[c]:  variável de progresso da lei (x para rs2, √α para p2, α para first/f3/sc).
    A massa que resta é m = m0 (1 − α(p)); intermediários recebem massa por "m0 += Δ" com α reescalado.
    """

    def __init__(self, masses: dict, n: int = 1):
        self.n = n
        self.m0 = {k: np.full(n, float(masses.get(k, 0.0))) for k in ORDER}
        self.p = {k: np.zeros(n) for k in ORDER}
        for k in ORDER:
            if COMPONENTS[k].law == "p2":
                self.p[k][:] = math.sqrt(COMPONENTS[k].seed)

    def alpha(self, k):
        c, p = COMPONENTS[k], self.p[k]
        if c.law == "rs2":
            return p ** 2
        if c.law == "p2":
            return np.minimum(p ** 2, 1.0)
        if c.law in ("first", "f3", "sc", "water"):
            return p
        return np.zeros_like(p)

    def mass(self, k):
        return self.m0[k] * (1.0 - self.alpha(k))

    def masses(self) -> dict:
        return {k: self.mass(k) for k in ORDER}

    def total(self):
        return sum(self.mass(k) for k in ORDER)

    def add(self, k, dm):
        """Acrescenta massa a um componente intermediário/inerte mantendo a massa já convertida."""
        m_now = self.mass(k)
        new = m_now + dm
        if COMPONENTS[k].law == "inert":
            self.m0[k] = new
            return
        # reescala para α' com m0' = m0 + dm: m0' (1 − α') = new
        m0n = self.m0[k] + dm
        a = np.where(m0n > 0, 1.0 - new / np.maximum(m0n, 1e-30), 0.0)
        self.m0[k] = m0n
        c = COMPONENTS[k]
        if c.law == "f3" or c.law == "first":
            self.p[k] = np.clip(a, 0.0, 1.0)
        elif c.law == "rs2":
            self.p[k] = np.sqrt(np.clip(a, 0.0, 1.0))

    def react(self, T, dt):
        """Avança as reações por dt na temperatura T (array n) com integração exata por lei.

        Devolve (produtos {lump: kg}, calor de reação [J], taxas por componente {k: kg/s})."""
        T = np.asarray(T, float)
        prod = {k: np.zeros(self.n) for k in LUMPS}
        heat = np.zeros(self.n)
        rates = {}
        new_mass = {}
        for k in REACTIVE:
            c = COMPONENTS[k]
            m_before = self.mass(k)
            if not np.any(self.m0[k] > 0):
                continue
            p = self.p[k]
            if c.law == "rs2":
                self.p[k] = 1.0 - (1.0 - p) * np.exp(-c.k(T) * dt)
            elif c.law == "first":
                self.p[k] = 1.0 - (1.0 - p) * np.exp(-c.k(T) * dt)
            elif c.law == "p2":
                self.p[k] = np.minimum(p + c.k(T) * dt, 1.0)
            elif c.law == "f3":
                q = np.maximum(1.0 - p, 1e-12)
                self.p[k] = 1.0 - 1.0 / np.sqrt(q ** -2 + 2 * c.k(T) * dt)
            elif c.law == "sc":
                ks = _sc_rates(c, T)
                kt = ks[0] + ks[1] + ks[2]
                self.p[k] = 1.0 - (1.0 - p) * np.exp(-kt * dt)
            dm = np.maximum(m_before - self.mass(k), 0.0)
            rates[k] = dm / dt
            heat += dm * c.dH
            if c.law == "sc":
                for kk, frac in zip(ks, SC_PRODUCTS):
                    w = kk / np.maximum(kt, 1e-300)
                    for lump, y in frac.items():
                        new_mass[lump] = new_mass.get(lump, 0.0) + dm * w * y
            else:
                for lump, y in c.yields.items():
                    new_mass[lump] = new_mass.get(lump, 0.0) + dm * y
        for lump, dm in new_mass.items():
            if lump in prod:
                prod[lump] += dm
            else:   # intermediário ou sólido que fica no leito
                self.add(lump, dm)
        return prod, heat, rates

    # ----------------------------------------------------- propriedades do leito
    def heat_capacity(self, T):
        """Σ m c_p,aparente [J/K]."""
        return sum(self.mass(k) * apparent_cp(COMPONENTS[k], T) for k in ORDER)

    def enthalpy(self, T):
        return sum(self.mass(k) * sensible_enthalpy(COMPONENTS[k], T) for k in ORDER)

    def melt_state(self, T):
        """Fração em volume denso do leito que está fundida (0 = pedaços soltos, 1 = poça de fundido)."""
        vm, vt = 0.0, 0.0
        for k in ORDER:
            c = COMPONENTS[k]
            if k == "H2O":
                continue
            v = self.mass(k) / c.rho_dense
            vt = vt + v
            if c.Tm > 0 or c.key == "PS":
                vm = vm + v * melt_fraction(c, T)
        return np.where(vt > 0, vm / np.maximum(vt, 1e-30), 0.0)

    def volume(self, T, loose_scale: float = 1.0):
        """Volume aparente do leito [m³]: pedaços soltos até fundirem; depois poça densa.

        Componentes que não fundem ficam soltos enquanto o leito não tiver fundido (melt_state)."""
        ms = self.melt_state(T)
        V = 0.0
        for k in ORDER:
            c = COMPONENTS[k]
            if k == "H2O":
                continue
            m = self.mass(k)
            if c.Tm > 0 or k == "PS":
                f = melt_fraction(c, T) if c.Tm > 0 else np.clip((np.asarray(T, float) - 383.15) / 30.0, 0, 1)
                V = V + m * ((1 - f) / (c.rho_loose * loose_scale) + f / c.rho_dense)
            else:
                V = V + m * ((1 - ms) / (c.rho_loose * loose_scale) + ms / c.rho_dense)
        return V

    def conductivity(self, T, d_piece: float = 0.08, eps: float = 0.85):
        """Condutividade efetiva do leito [W/(m K)]: média em volume do material denso, ponderada pela
        compacidade, mais o termo de radiação nos poros entre os pedaços (Zehner–Schlünder simplificado)."""
        T = np.asarray(T, float)
        Vd, kd = 0.0, 0.0
        for k in ORDER:
            if k == "H2O":
                continue
            c = COMPONENTS[k]
            v = self.mass(k) / c.rho_dense
            Vd = Vd + v
            kd = kd + v * c.k_dense
        kd = np.where(Vd > 0, kd / np.maximum(Vd, 1e-30), 0.2)
        V = np.maximum(self.volume(T), 1e-30)
        solid = np.clip(Vd / V, 0.0, 1.0)              # fração de material denso no volume aparente
        k_gas = 0.026 + 5.0e-5 * (T - 300.0)
        k_rad = 4 * 5.670374e-8 * eps / (2 - eps) * d_piece * T ** 3 * (1 - solid)
        # mistura série/paralelo: k_s^φ k_g^(1−φ) (média geométrica) + radiação nos vazios
        return kd ** solid * k_gas ** (1 - solid) + k_rad


# ------------------------------------------------------------------- TGA
def tga(key_or_masses, beta_K_min: float, T_start: float = 300.0, T_end: float = 1000.0, dT: float = 0.25):
    """TGA a taxa constante para um componente (chave) ou uma mistura {chave: massa}.

    Devolve T [K], massa relativa restante (sólidos inclusive) e −dm/dT [1/K]."""
    masses = {key_or_masses: 1.0} if isinstance(key_or_masses, str) else dict(key_or_masses)
    st = KineticState(masses, 1)
    m_init = st.total()[0]
    beta = beta_K_min / 60.0
    Ts = np.arange(T_start, T_end + dT, dT)
    mr = np.empty_like(Ts)
    dt = dT / beta
    for i, T in enumerate(Ts):
        if "H2O" in masses and T > 373.15:       # TGA: a umidade sai ao passar de 100 °C (taxa rápida)
            st.p["H2O"] = np.minimum(st.p["H2O"] + 0.2 * dT, 1.0)
        st.react(np.array([T]), dt)
        mr[i] = st.total()[0] / m_init
    return Ts, mr, -np.gradient(mr, Ts)


def dtg_peak(key: str, beta_K_min: float) -> float:
    """Temperatura do pico de DTG [°C] (com refino parabólico)."""
    T, _, d = tga(key, beta_K_min)
    i = int(np.argmax(d))
    if 0 < i < len(T) - 1:
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
        return float(T[i] + off * (T[1] - T[0]) - 273.15)
    return float(T[i] - 273.15)


def t_k1e3(key: str) -> float:
    """Temperatura em que k = 10⁻³ s⁻¹ [°C] (verificação da pesquisa)."""
    c = COMPONENTS[key]
    if c.law == "sc":
        A, E = c.sc[1]
    else:
        A, E = c.A, c.E
    return E / (R_GAS * math.log(A / 1e-3)) - 273.15


def ultimate_yields(charge: Charge, T: float = 773.15, hours: float = 10.0) -> dict:
    """Rendimentos finais em isoterma longa (sem craqueamento secundário): {lump/sólido: fração da carga}."""
    st = KineticState(charge.masses(), 1)
    tot0 = st.total()[0]
    out = {k: 0.0 for k in LUMPS}
    out["H2O"] += charge.mass * charge.moisture
    st.p["H2O"][:] = 1.0
    t, dt = 0.0, 5.0
    while t < hours * 3600:
        prod, _, _ = st.react(np.array([T]), dt)
        for k, v in prod.items():
            out[k] += float(v[0])
        t += dt
    out["CHAR"] = float(st.mass("CHAR")[0] + st.mass("CB")[0])
    out["ASH"] = float(st.mass("INERT")[0])
    out["resto"] = float(st.total()[0]) - out["CHAR"] - out["ASH"]
    return {k: v / tot0 for k, v in out.items()}
