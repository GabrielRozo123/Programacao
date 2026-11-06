"""
projeto_coluna_bolhas.py
========================
Equações de projeto (correlações empíricas + modelo de reator) para uma
coluna de bolhas ar–água. Serve de referência "de engenharia" para comparar
com a simulação CFD (Euler–Euler) no Simcenter STAR-CCM+.

Uso:
    python projeto_coluna_bolhas.py            # caso padrão (D = 0,15 m)
    python projeto_coluna_bolhas.py --D 0.20 --H0 1.0 --Ug 0.01 0.02 0.04

Saídas (pasta ./resultados):
    tabela_correlacoes.csv   → εG, d32, a, kLa, D_L vs. U_G
    fig_holdup_correlacoes.png
    resumo_projeto.txt       → exemplo de projeto do reator (cinética + TM)

Apenas numpy + matplotlib (sem scipy).

Autor: Gabriel Rozo | Seminário de Cinética — Reator de Coluna de Bolhas
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

G = 9.81  # m/s²


# ---------------------------------------------------------------------------
# Propriedades físicas
# ---------------------------------------------------------------------------
@dataclass
class Propriedades:
    """Ar–água a 25 °C e 1 atm (valores de tabela)."""
    rho_L: float = 997.0      # kg/m³
    mu_L: float = 8.9e-4      # Pa·s
    sigma: float = 0.072      # N/m
    rho_G: float = 1.18       # kg/m³
    mu_G: float = 1.8e-5      # Pa·s
    D_A: float = 2.1e-9       # m²/s  difusividade do O2 em água
    He: float = 31.5          # Henry adimensional C_G/C_L* do O2 (25 °C)
    eletrolito: bool = False  # Akita-Yoshida: C = 0,25 p/ eletrólitos

    @property
    def nu_L(self) -> float:
        return self.mu_L / self.rho_L


# ---------------------------------------------------------------------------
# Hidrodinâmica: retenção gasosa (gas holdup)
# ---------------------------------------------------------------------------
def holdup_akita_yoshida(Ug, D, p: Propriedades):
    """Akita & Yoshida (1973), Ind. Eng. Chem. Process Des. Dev. 12, 76.

        εG / (1 − εG)^4 = C · Bo^(1/8) · Ga^(1/12) · Fr
        Bo = g D² ρL/σ,  Ga = g D³/νL²,  Fr = UG/√(gD)
        C = 0,20 (líquidos puros / não eletrólitos), 0,25 (eletrólitos)

    Os autores recomendam usar D = 0,6 m para colunas maiores que isso.
    Resolvido por bisseção (lado esquerdo é monotônico em εG).
    """
    D_eff = min(D, 0.6)
    C = 0.25 if p.eletrolito else 0.20
    Bo = G * D_eff**2 * p.rho_L / p.sigma
    Ga = G * D_eff**3 / p.nu_L**2
    rhs = C * Bo**(1 / 8) * Ga**(1 / 12) * np.asarray(Ug) / np.sqrt(G * D_eff)

    lo = np.zeros_like(rhs, dtype=float)
    hi = np.full_like(rhs, 0.95, dtype=float)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f = mid / (1 - mid)**4 - rhs
        lo = np.where(f < 0, mid, lo)
        hi = np.where(f >= 0, mid, hi)
    return 0.5 * (lo + hi)


def holdup_hikita(Ug, p: Propriedades):
    """Hikita et al. (1980), Chem. Eng. J. 20, 59 (não eletrólitos, f = 1).

        εG = 0,672 (UG μL/σ)^0,578 (μL⁴ g/(ρL σ³))^−0,131
                   (ρG/ρL)^0,062 (μG/μL)^0,107
    """
    Ug = np.asarray(Ug)
    return (0.672 * (Ug * p.mu_L / p.sigma)**0.578
            * (p.mu_L**4 * G / (p.rho_L * p.sigma**3))**-0.131
            * (p.rho_G / p.rho_L)**0.062
            * (p.mu_G / p.mu_L)**0.107)


def holdup_reilly(Ug, p: Propriedades):
    """Reilly et al. (1986), Can. J. Chem. Eng. 64, 705 (SI).

        εG = 296 UG^0,44 ρL^−0,98 σ^−0,16 ρG^0,19 + 0,009
    """
    Ug = np.asarray(Ug)
    return 296 * Ug**0.44 * p.rho_L**-0.98 * p.sigma**-0.16 * p.rho_G**0.19 + 0.009


def holdup_besagni_inzoli(Ug, p: Propriedades):
    """Besagni & Inzoli (2016), CES 146:259, Eq. (31) — ajuste aos dados da
    coluna de 0,24 m com aspersor "spider" (furos 1–3,5 mm), modo batelada:

        εG / (1 − εG)^4,9 = 329,31 · Ca^0,997,     Ca = U_G μL / σ
    """
    rhs = 329.31 * (np.asarray(Ug, dtype=float) * p.mu_L / p.sigma)**0.997
    lo = np.zeros_like(rhs)
    hi = np.full_like(rhs, 0.95)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f = mid / (1 - mid)**4.9 - rhs
        lo = np.where(f < 0, mid, lo)
        hi = np.where(f >= 0, mid, hi)
    return 0.5 * (lo + hi)


def holdup_deslizamento(Ug, U_inf=0.23, n=2.0):
    """Modelo de deslizamento (drift-flux homogêneo, Wallis / Richardson–Zaki)
    com líquido em batelada (UL = 0):

        UG / εG = U∞ (1 − εG)^(n−1)

    Só vale no regime HOMOGÊNEO; U∞ ≈ velocidade terminal da bolha isolada.
    """
    Ug = np.asarray(Ug, dtype=float)
    lo = np.zeros_like(Ug)
    hi = np.full_like(Ug, 0.95)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f = mid * U_inf * (1 - mid)**(n - 1) - Ug
        lo = np.where(f < 0, mid, lo)
        hi = np.where(f >= 0, mid, hi)
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Bolhas, área interfacial e transferência de massa
# ---------------------------------------------------------------------------
def d32_akita_yoshida(Ug, D, p: Propriedades):
    """Akita & Yoshida (1974), Ind. Eng. Chem. Process Des. Dev. 13, 84.

        d32 / D = 26 Bo^−0,50 Ga^−0,12 (UG/√(gD))^−0,12
    """
    Bo = G * D**2 * p.rho_L / p.sigma
    Ga = G * D**3 / p.nu_L**2
    Fr = np.asarray(Ug) / np.sqrt(G * D)
    return D * 26 * Bo**-0.5 * Ga**-0.12 * Fr**-0.12


def u_terminal_mendelson(d, p: Propriedades):
    """Mendelson (1967): bolhas deformáveis em água limpa (d ≳ 2 mm).
        U∞ = √(2σ/(ρL d) + g d/2)
    """
    return np.sqrt(2 * p.sigma / (p.rho_L * d) + G * d / 2)


def kla_akita_yoshida(eps, D, p: Propriedades):
    """Akita & Yoshida (1973):
        kLa D²/DA = 0,6 Sc^0,5 Bo^0,62 Ga^0,31 εG^1,1     [kLa em 1/s]
    """
    Sc = p.nu_L / p.D_A
    Bo = G * D**2 * p.rho_L / p.sigma
    Ga = G * D**3 / p.nu_L**2
    return 0.6 * Sc**0.5 * Bo**0.62 * Ga**0.31 * np.asarray(eps)**1.1 * p.D_A / D**2


def kla_shah(Ug):
    """Shah et al. (1982), AIChE J. 28, 353 — ar–água: kLa = 0,467 UG^0,82 (SI)."""
    return 0.467 * np.asarray(Ug)**0.82


def kl_higbie(d, u_slip, p: Propriedades):
    """Teoria da penetração (Higbie): kL = 2 √(DA u_slip / (π d))."""
    return 2 * np.sqrt(p.D_A * u_slip / (np.pi * d))


# ---------------------------------------------------------------------------
# Mistura axial (retromistura) da fase líquida
# ---------------------------------------------------------------------------
def DL_deckwer(Ug, D):
    """Deckwer et al. (1974): D_L = 2,7 D^1,4 UG^0,3  (unidades cgs!)."""
    D_cm, U_cms = D * 100, np.asarray(Ug) * 100
    return 2.7 * D_cm**1.4 * U_cms**0.3 * 1e-4  # cm²/s → m²/s


def DL_baird_rice(Ug, D):
    """Baird & Rice (1975): D_L = 0,35 D^(4/3) (g UG)^(1/3)  (SI)."""
    return 0.35 * D**(4 / 3) * (G * np.asarray(Ug))**(1 / 3)


def vl_centro_riquarts(Ug, D, p: Propriedades):
    """Riquarts (1981): velocidade axial média do líquido no eixo da coluna
        V_L(0) = 0,21 √(gD) (UG³/(g νL))^(1/8)
    Perfil típico: sobe no centro, desce junto à parede; inversão em r/R ≈ 0,7.
    """
    return 0.21 * np.sqrt(G * D) * (np.asarray(Ug)**3 / (G * p.nu_L))**(1 / 8)


# ---------------------------------------------------------------------------
# Equações de projeto do REATOR
# ---------------------------------------------------------------------------
def conversao_adm_1a_ordem(Da, Pe):
    """Modelo de dispersão axial, reação de 1ª ordem, CC de Danckwerts
    (solução de Wehner–Wilhelm):

        X = 1 − 4 a e^(Pe/2) / [(1+a)² e^(aPe/2) − (1−a)² e^(−aPe/2)]
        a = √(1 + 4 Da/Pe),  Da = k τ,  Pe = uL H / D_L

    Limites: Pe → 0 ⇒ CSTR (X = Da/(1+Da));  Pe → ∞ ⇒ PFR (X = 1 − e^−Da).
    """
    a = np.sqrt(1 + 4 * Da / Pe)
    num = 4 * a * np.exp(Pe / 2)
    den = (1 + a)**2 * np.exp(a * Pe / 2) - (1 - a)**2 * np.exp(-a * Pe / 2)
    return 1 - num / den


def reator_gas_pistonado_liquido_misturado(Ug, H, eps, kla, k1, p: Propriedades):
    """Absorção com reação lenta (Ha < 0,3) em coluna semibatelada:
    gás em escoamento pistonado, líquido perfeitamente misturado.

    Balanço no gás (por volume de dispersão):
        UG dC_G/dz = −kLa (C_G/He − C_L)
    Balanço no líquido (estado pseudo-estacionário, consumo k1 C_L):
        kLa · <C_G/He − C_L>_H = k1 εL C_L

    Solução analítica (St = kLa H / (He UG)):
        Φ   = kLa (1 − e^−St)/St
        C_L / (C_G0/He) = Φ / (Φ + k1 εL)
        X_gás = (1 − He C_L/C_G0)(1 − e^−St)
    Retorna (X_gás, C_L/C*_entrada, St).
    """
    St = kla * H / (p.He * Ug)
    Phi = kla * (1 - np.exp(-St)) / St
    cl_rel = Phi / (Phi + k1 * (1 - eps))
    X = (1 - cl_rel) * (1 - np.exp(-St))
    return X, cl_rel, St


def hatta(k1, kL, p: Propriedades):
    """Número de Hatta (reação de pseudo-1ª ordem): Ha = √(k1 DA)/kL."""
    return np.sqrt(k1 * p.D_A) / kL


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--D", type=float, default=0.15, help="diâmetro da coluna [m]")
    ap.add_argument("--H0", type=float, default=0.90, help="altura de líquido estático [m]")
    ap.add_argument("--Ug", type=float, nargs="+", default=[0.01, 0.02, 0.04],
                    help="velocidades superficiais simuladas no CFD [m/s]")
    ap.add_argument("--k1", type=float, default=0.01,
                    help="constante de 1ª ordem do consumo de A no líquido [1/s]")
    ap.add_argument("--uL", type=float, default=0.005,
                    help="vel. superficial do líquido p/ exemplo contínuo [m/s]")
    ap.add_argument("--out", type=Path, default=Path("resultados"))
    args = ap.parse_args()

    p = Propriedades()
    D, H0 = args.D, args.H0
    args.out.mkdir(parents=True, exist_ok=True)

    # ---- Tabela das correlações ---------------------------------------
    Ug_tab = np.array(sorted(set([0.005, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08] + args.Ug)))
    eAY = holdup_akita_yoshida(Ug_tab, D, p)
    eHk = holdup_hikita(Ug_tab, p)
    eRe = holdup_reilly(Ug_tab, p)
    d32 = d32_akita_yoshida(Ug_tab, D, p)
    a = 6 * eAY / d32
    klaAY = kla_akita_yoshida(eAY, D, p)
    klaSh = kla_shah(Ug_tab)
    DLd = DL_deckwer(Ug_tab, D)
    DLb = DL_baird_rice(Ug_tab, D)

    with open(args.out / "tabela_correlacoes.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ug_m_s", "eps_AkitaYoshida", "eps_Hikita", "eps_Reilly",
                    "d32_AY_mm", "a_m2_m3", "kLa_AY_1_s", "kLa_Shah_1_s",
                    "DL_Deckwer_m2_s", "DL_BairdRice_m2_s"])
        for row in zip(Ug_tab, eAY, eHk, eRe, d32 * 1e3, a, klaAY, klaSh, DLd, DLb):
            w.writerow([f"{v:.5g}" for v in row])

    # ---- Resumo / exemplo de projeto -----------------------------------
    linhas = []
    P = linhas.append
    P(f"COLUNA DE BOLHAS AR–ÁGUA  |  D = {D:.3f} m,  H0 = {H0:.2f} m,  H0/D = {H0/D:.1f}")
    P("Critérios de Wilkinson et al. (1992) p/ εG independente da escala:")
    P(f"  D > 0,15 m ........ {'OK' if D >= 0.15 else 'NÃO'}  (D = {D} m)")
    P(f"  H/D > 5 ........... {'OK' if H0 / D > 5 else 'NÃO'}  (H/D = {H0/D:.1f})")
    P("  furos do aspersor > 1–2 mm (definido no CFD pelo diâmetro de bolha)")
    P("")
    hdr = (f"{'Ug[m/s]':>8} {'εG AY':>7} {'εG Hik':>7} {'εG Rei':>7} {'d32[mm]':>8} "
           f"{'a[1/m]':>7} {'kLa AY':>7} {'kLa Shah':>8} {'D_L[m²/s]':>10}")
    P(hdr)
    P("-" * len(hdr))
    for i, u in enumerate(Ug_tab):
        P(f"{u:8.3f} {eAY[i]:7.3f} {eHk[i]:7.3f} {eRe[i]:7.3f} {d32[i]*1e3:8.2f} "
          f"{a[i]:7.1f} {klaAY[i]:7.4f} {klaSh[i]:8.4f} {DLd[i]:10.4f}")
    P("")

    db = 5e-3
    Uinf = u_terminal_mendelson(db, p)
    kL = kl_higbie(db, Uinf, p)
    Eo = G * (p.rho_L - p.rho_G) * db**2 / p.sigma
    Reb = p.rho_L * Uinf * db / p.mu_L
    P(f"Bolha de referência p/ o CFD: d = {db*1e3:.1f} mm  →  U∞ (Mendelson) = {Uinf:.3f} m/s,"
      f"  Eo = {Eo:.2f},  Re_b = {Reb:.0f}")
    P(f"  kL (Higbie) = {kL:.2e} m/s")
    Ha = hatta(args.k1, kL, p)
    regime = "LENTO (reação no seio do líquido)" if Ha < 0.3 else (
        "INTERMEDIÁRIO" if Ha < 3 else "RÁPIDO (reação no filme)")
    P(f"  Hatta (k1 = {args.k1:g} 1/s) = {Ha:.3g}  →  regime {regime}")
    P("")

    P("Circulação do líquido (alvo p/ o CFD, Riquarts 1981): V_L(eixo) = "
      + ", ".join(f"{float(vl_centro_riquarts(u, D, p)):.2f} m/s @ {u*100:g} cm/s" for u in args.Ug))
    P("")

    P("EXEMPLO DE PROJETO 1 — absorção de O2 com consumo de 1ª ordem no líquido")
    P("  (gás pistonado + líquido misturado, semibatelada; ver docstring)")
    P(f"{'Ug':>6} {'St':>6} {'X_O2 gás':>9} {'C_L/C*':>7} {'r/C*_entrada [1/s]':>19}")
    for u in args.Ug:
        e = float(holdup_akita_yoshida(u, D, p))
        kla = float(kla_akita_yoshida(e, D, p))
        X, cl, St = reator_gas_pistonado_liquido_misturado(u, H0 / (1 - e), e, kla, args.k1, p)
        P(f"{u:6.3f} {St:6.3f} {X:9.3%} {cl:7.3f} {args.k1*(1-e)*cl:19.2e}")
    P("")

    P("EXEMPLO DE PROJETO 2 — fase líquida contínua, reação de 1ª ordem k1,")
    P(f"  efeito da retromistura (modelo de dispersão axial), uL = {args.uL} m/s")
    P(f"{'Ug':>6} {'D_L':>8} {'Pe':>6} {'Da':>6} {'X_PFR':>7} {'X_ADM':>7} {'X_CSTR':>7}")
    for u in args.Ug:
        e = float(holdup_akita_yoshida(u, D, p))
        H = H0 / (1 - e)
        DL = float(DL_deckwer(u, D))
        Pe = args.uL * H / DL
        tau = (1 - e) * H / args.uL
        Da = args.k1 * tau
        P(f"{u:6.3f} {DL:8.4f} {Pe:6.3f} {Da:6.2f} {1-np.exp(-Da):7.3f} "
          f"{conversao_adm_1a_ordem(Da, Pe):7.3f} {Da/(1+Da):7.3f}")
    P("  → Pe < 1: a fase líquida se comporta quase como CSTR. A circulação de")
    P("    líquido (que o CFD resolve) é o que define D_L e, portanto, X.")

    texto = "\n".join(linhas)
    (args.out / "resumo_projeto.txt").write_text(texto, encoding="utf-8")
    print(texto)

    # ---- Figura ---------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib não instalado — figura não gerada)")
        return

    U = np.linspace(0.002, 0.10, 200)
    fig, ax = plt.subplots(figsize=(6, 4.2), dpi=150)
    ax.plot(U * 100, holdup_akita_yoshida(U, D, p), label="Akita & Yoshida (1973)")
    ax.plot(U * 100, holdup_hikita(U, p), "--", label="Hikita et al. (1980)")
    ax.plot(U * 100, holdup_reilly(U, p), "-.", label="Reilly et al. (1986)")
    Uh = U[U <= 0.04]
    ax.plot(Uh * 100, holdup_deslizamento(Uh, U_inf=Uinf), ":", color="k",
            label=f"Deslizamento homogêneo (U∞={Uinf:.2f} m/s)")
    ax.axvspan(0, 4, color="tab:green", alpha=0.07)
    ax.text(0.4, 0.27, "homogêneo", color="tab:green", fontsize=8)
    ax.axvspan(4, 10, color="tab:orange", alpha=0.07)
    ax.text(5.5, 0.27, "transição / heterogêneo", color="tab:orange", fontsize=8)
    ax.set_xlabel(r"$U_G$ [cm/s]")
    ax.set_ylabel(r"$\varepsilon_G$ [–]")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 0.30)
    ax.set_title(f"Retenção gasosa — ar/água, D = {D:.2f} m")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(args.out / "fig_holdup_correlacoes.png")
    print(f"\nFigura salva em {args.out / 'fig_holdup_correlacoes.png'}")


if __name__ == "__main__":
    main()
