"""
projeto_generico.py
===================
Equações de projeto GENÉRICAS para uma coluna de bolhas com reação gás–líquido

    ν_A A(g→l) + ν_B B(l)  ⇌  ν_C C(l) + ν_D D(l)
    base: 1 mol de A absorvido  →  A + b B ⇌ c C + d D,   b = ν_B/ν_A, c = ν_C/ν_A, d = ν_D/ν_A
    (ν em vez de a, b, c, d para não confundir com a área interfacial a)

Lei de velocidade (por volume de LÍQUIDO):  r = k C_A^m C_B^n − k' C_C^p C_D^q    (irreversível: k' = 0)

Balanços (−r_A = taxa de consumo de A por volume de REATOR):
  líquido em batelada:   ε_L dC_B/dt = −b (−r_A)   ⇒  t = (ε_L C_B0 / b) ∫₀^{X_B} dX_B / (−r_A)
  gás pistonado (A diluído, U_G ≈ cte):   U_G dC_AG/dz = −(−r_A)  ⇒  H = U_G C_AG0 ∫₀^{X_A} dX_A / (−r_A)
  líquido contínuo (CSTR):  V_R = Q_L C_B0 X_B / [b (−r_A)_saída]

−r_A por regime (irreversível, ordem m em A e n em B):
  lento, cinético    ε_L k C*^m C_B^n
  lento, TM          k_L a C*                                  (a ordem some)
  rápido             a √[2/(m+1) · k D_A C*^(m+1) C_B^n]        (Hikita & Asai, 1964)
  instantâneo        k_L a (C* + D_B C_B/(b D_A))               (a cinética some)

Este script (i) confere as formas fechadas contra a integral numérica (scipy.quad) para
vários (m, n), (ii) resolve um caso reversível só pela integral e (iii) gera os dados dos
gráficos da apresentação.

Uso:  python projeto_generico.py   →  resultados/projeto_generico.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad


# ----------------------------------------------------------------------------- taxas
def rA_batelada(regime, X, P):
    """−r_A (mol A/m³ reator·s) no líquido em batelada: C* constante, C_B = C_B0 (1 − X_B)."""
    CB = P["CB0"] * (1 - X)
    m, n, Cs = P["m"], P["n"], P["Cs"]
    if regime == "cinetico":
        return P["epsL"] * P["k"] * Cs**m * CB**n
    if regime == "tm":
        return P["kLa"] * Cs
    if regime == "rapido":
        return P["a"] * np.sqrt(2 / (m + 1) * P["k"] * P["DA"] * Cs**(m + 1) * CB**n)
    if regime == "instantaneo":
        return P["kLa"] * (Cs + P["DB"] * CB / (P["b"] * P["DA"]))
    raise ValueError(regime)


def rA_gas(regime, X, P):
    """−r_A ao longo do gás pistonado: C_B constante (B em excesso), C* = C_AG0 (1 − X_A)/He."""
    Cs = P["CAG0"] * (1 - X) / P["He"]
    m, n, CB = P["m"], P["n"], P["CB"]
    if regime == "cinetico":
        return P["epsL"] * P["k"] * Cs**m * CB**n
    if regime == "tm":
        return P["kLa"] * Cs
    if regime == "rapido":
        return P["a"] * np.sqrt(2 / (m + 1) * P["k"] * P["DA"] * Cs**(m + 1) * CB**n)
    if regime == "instantaneo":
        return P["kLa"] * (Cs + P["DB"] * CB / (P["b"] * P["DA"]))
    raise ValueError(regime)


# ----------------------------------------------------------------------------- integrais
def t_integral(regime, XB, P):
    return P["epsL"] * P["CB0"] / P["b"] * quad(lambda x: 1 / rA_batelada(regime, x, P), 0, XB, limit=200)[0]


def H_integral(regime, XA, P):
    return P["UG"] * P["CAG0"] * quad(lambda x: 1 / rA_gas(regime, x, P), 0, XA, limit=200)[0]


# ----------------------------------------------------------------------------- formas fechadas
def _pot(X, e):
    """∫ função auxiliar: [(1−X)^(1−e) − 1]/(e − 1), com o limite ln[1/(1−X)] em e = 1."""
    return np.log(1 / (1 - X)) if abs(e - 1) < 1e-12 else ((1 - X)**(1 - e) - 1) / (e - 1)


def t_fechada(regime, XB, P):
    m, n, b, CB0, Cs, eL = P["m"], P["n"], P["b"], P["CB0"], P["Cs"], P["epsL"]
    if regime == "cinetico":
        return _pot(XB, n) / (b * P["k"] * Cs**m * CB0**(n - 1))
    if regime == "tm":
        return eL * CB0 * XB / (b * P["kLa"] * Cs)
    if regime == "rapido":
        Phi = b * P["a"] / eL * np.sqrt(2 / (m + 1) * P["k"] * P["DA"] * Cs**(m + 1))
        return CB0**(1 - n / 2) * _pot(XB, n / 2) / Phi
    if regime == "instantaneo":
        beta = b * P["DA"] * Cs / P["DB"]
        return eL * P["DA"] / (P["kLa"] * P["DB"]) * np.log((CB0 + beta) / (CB0 * (1 - XB) + beta))
    raise ValueError(regime)


def H_fechada(regime, XA, P):
    m, n, He, UG, C0, CB = P["m"], P["n"], P["He"], P["UG"], P["CAG0"], P["CB"]
    if regime == "cinetico":
        return UG * He**m * C0**(1 - m) * _pot(XA, m) / (P["epsL"] * P["k"] * CB**n)
    if regime == "tm":
        return He * UG / P["kLa"] * np.log(1 / (1 - XA))
    if regime == "rapido":
        p = (m + 1) / 2
        Psi = P["a"] * np.sqrt(2 / (m + 1) * P["k"] * P["DA"] * CB**n)
        return UG * He**p * C0**(1 - p) * _pot(XA, p) / Psi
    if regime == "instantaneo":
        gam = He * P["DB"] * CB / (P["b"] * P["DA"])
        return He * UG / P["kLa"] * np.log((C0 + gam) / (C0 * (1 - XA) + gam))
    raise ValueError(regime)


REGIMES = ["cinetico", "tm", "rapido", "instantaneo"]


def confere():
    rng = np.random.default_rng(7)
    pior = 0.0
    for m in (0.5, 1, 1.5, 2):
        for n in (0, 0.5, 1, 2, 3):
            P = dict(m=m, n=n, b=rng.uniform(0.5, 3), CB0=rng.uniform(10, 500), CB=rng.uniform(10, 500),
                     Cs=rng.uniform(0.5, 40), CAG0=rng.uniform(1, 40), He=rng.uniform(0.8, 50),
                     epsL=rng.uniform(0.8, 0.95), k=10**rng.uniform(-3, 1), kLa=rng.uniform(0.01, 0.1),
                     a=rng.uniform(50, 300), DA=1.9e-9, DB=rng.uniform(1e-9, 5e-9), UG=0.02)
            for reg in REGIMES:
                for X in (0.3, 0.9):
                    e1 = abs(t_fechada(reg, X, P) / t_integral(reg, X, P) - 1)
                    e2 = abs(H_fechada(reg, X, P) / H_integral(reg, X, P) - 1)
                    pior = max(pior, e1, e2)
    print(f"formas fechadas × integral numérica: maior desvio relativo = {pior:.1e}  (m = 0,5–2; n = 0–3; 4 regimes)")
    assert pior < 1e-6


def caso_reversivel():
    """A + B ⇌ C no regime cinético: r = k C* C_B − k' C_C;  κ = K_c C* = k C*/k'.
    Só a integral: τ(X) = ∫ dX / [(1 − X) − X/κ],  τ = b k C* t."""
    taus = np.round(np.arange(0, 4.01, 0.25), 2)
    out = {}
    for nome, kap in (("Irreversível", np.inf), ("Reversível, κ = 4 (X_e = 0,80)", 4.0), ("Reversível, κ = 1 (X_e = 0,50)", 1.0)):
        Xe = 1.0 if np.isinf(kap) else kap / (1 + kap)
        f = lambda x: 1 / ((1 - x) - (0 if np.isinf(kap) else x / kap))
        Xs = []
        for tau in taus:   # inverte τ(X) por bisseção sobre a integral
            lo, hi = 0.0, Xe * (1 - 1e-12)
            for _ in range(60):
                mid = (lo + hi) / 2
                (lo, hi) = (mid, hi) if quad(f, 0, mid)[0] < tau else (lo, mid)
            Xs.append(round((lo + hi) / 2, 4))
        out[nome] = Xs
    return [float(t) for t in taus], out


def formas_por_regime():
    """Mesma reação (m = 1, n = 2) em quatro regimes; tempo normalizado pelo tempo de meia conversão."""
    taus = np.round(np.arange(0, 3.01, 0.25), 2)
    bp = 0.2   # β/C_B0 no instantâneo
    kh = np.log((1 + bp) / (0.5 + bp))
    curvas = {
        "Lento cinético (ordem 2 em B)": [t / (1 + t) for t in taus],
        "Rápido (ordem aparente n/2 = 1)": [1 - np.exp(-np.log(2) * t) for t in taus],
        "Lento TM (ordem 0 em B)": [min(0.5 * t, 1.0) for t in taus],
        "Instantâneo (β/C_B0 = 0,2)": [min((1 + bp) * (1 - np.exp(-kh * t)), 1.0) for t in taus],
    }
    return [float(t) for t in taus], {k: [round(float(v), 4) for v in vs] for k, vs in curvas.items()}


def main():
    confere()
    tr, rev = caso_reversivel()
    tf, formas = formas_por_regime()
    for k, v in rev.items():
        print(f"  {k}: X_B(τ = 1, 2, 4) = {v[4]:.3f}, {v[8]:.3f}, {v[16]:.3f}")
    out = Path(__file__).parent / "resultados"
    out.mkdir(exist_ok=True)
    (out / "projeto_generico.json").write_text(json.dumps(dict(tau_rev=tr, rev=rev, tau_formas=tf, formas=formas),
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"salvo em {out / 'projeto_generico.json'}")


if __name__ == "__main__":
    main()
