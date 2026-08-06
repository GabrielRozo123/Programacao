"""
curva_eta_x_d.py — a CURVA DE EFICIÊNCIA DE GRADE medida no CFD Lagrangeano.

Ciclone Stairmand HE · Dc = 307 mm · 100 % de vazão (v_i = 13,59 m/s)
Campo: k-ω steady + `Outlet` + parede convectiva (Rodada 8, ΔP = 1.955,6 Pa)
Fase: ρ_p = 1500 kg/m³ · µ_gás = 9,5e-5 Pa·s · classes monodispersas · 5.082 parcels
Método: η = 1 − |mdot_gas| / mdot_inj   (ver simulacao/07_EXECUCAO §8)

Gera: curva_eta_x_d.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── OS DEZ PONTOS MEDIDOS (100 % de vazão, COM dispersão turbulenta) ──────
D_UM  = np.array([1.0, 2.0,  5.0,  7.0,  10.0,  15.0,  20.0,  50.0,  75.0, 150.0])
ETA   = np.array([22.70, 22.31, 31.34, 51.35, 79.14, 97.70, 99.98, 100.0, 100.0, 100.0])/100

# sensibilidade SEM dispersão (só onde foi medida; ⚠️ ver ressalva no doc)
D_SEM   = np.array([1.0, 2.0, 5.0])
ETA_SEM = np.array([22.51, 19.90, 37.44])/100
NRES    = np.array([22.1, 19.1, 37.2])          # % não resolvidas — 1 µm é o único conclusivo

# ── Parâmetros do caso ────────────────────────────────────────────────────
RHO_P, MU, V_I, DC = 1500.0, 9.5e-5, 13.59, 0.307
D_STAR_LAPPLE = 8.28e-6      # m

eta_lapple = lambda d_m, ds: 1/(1+(ds/d_m)**2)
stokes     = lambda d_m: RHO_P*d_m**2*V_I/(18*MU*DC)


def eta_cfd(d_um):
    """Interpola a curva medida em log(d). Fora da faixa: satura.
    Devolve escalar para entrada escalar, array para array."""
    r = np.interp(np.log(np.asarray(d_um, dtype=float)), np.log(D_UM), ETA)
    return float(r) if np.isscalar(d_um) or np.ndim(d_um) == 0 else r


def d_star_cfd():
    """Diâmetro onde η = 50 %, por interpolação log-linear."""
    i = np.searchsorted(ETA, 0.5)
    (x1, y1), (x2, y2) = (D_UM[i-1], ETA[i-1]), (D_UM[i], ETA[i])
    return np.exp(np.log(x1) + (0.5-y1)/(y2-y1)*(np.log(x2)-np.log(x1)))


if __name__ == "__main__":
    ds = d_star_cfd()
    print("="*72)
    print("  CURVA η × d — Ciclone Dc = 307 mm · 100 % de vazão")
    print("="*72)
    print(f"\n  d* (CFD)    = {ds*1:.2f} µm")
    print(f"  d* (Lapple) = {D_STAR_LAPPLE*1e6:.2f} µm")
    print(f"  razão       = {ds/(D_STAR_LAPPLE*1e6):.3f}  →  corte {(1-ds/(D_STAR_LAPPLE*1e6))*100:.0f} % mais fino")
    print(f"  Ne implícito= {6*(D_STAR_LAPPLE*1e6/ds)**2:.1f} voltas  (Lapple tabela: 6)")
    print(f"\n  St no corte = {stokes(ds*1e-6):.3e}")
    print("\n  d (µm)    η CFD      η Lapple    razão      St")
    print("  " + "-"*52)
    for d, e in zip(D_UM, ETA):
        el = eta_lapple(d*1e-6, D_STAR_LAPPLE)
        print(f"  {d:6.0f}   {e*100:6.2f} %   {el*100:6.2f} %   {e/el:6.2f}   {stokes(d*1e-6):.2e}")

    # ── figura ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5.6))
    dd = np.logspace(np.log10(0.7), np.log10(200), 400)

    ax.semilogx(dd, eta_lapple(dd*1e-6, D_STAR_LAPPLE)*100, "--", lw=1.6,
                color="#888", label="Lapple (ρ$_p$=1500, d*=8,28 µm)")
    ax.semilogx(dd, eta_cfd(dd)*100, "-", lw=2.4, color="#1f6feb",
                label="CFD Lagrangeano (medido)")
    ax.semilogx(D_UM, ETA*100, "o", ms=8, color="#1f6feb", zorder=5,
                markeredgecolor="white", markeredgewidth=1.2)
    ax.semilogx(D_SEM[:1], ETA_SEM[:1]*100, "s", ms=8, color="#d29922", zorder=6,
                markeredgecolor="white", markeredgewidth=1.2,
                label="sem dispersão turbulenta (1 µm: Δ = 0,19 pt)")

    ax.axvline(ds, color="#1f6feb", lw=1, ls=":", alpha=0.8)
    ax.annotate(f"d* = {ds:.2f} µm", xy=(ds, 50), xytext=(ds*1.45, 40),
                fontsize=10, color="#1f6feb",
                arrowprops=dict(arrowstyle="->", color="#1f6feb", lw=1))
    ax.axhline(50, color="#ccc", lw=0.8, zorder=0)

    ax.axvspan(0.7, 3, alpha=0.07, color="#d29922")
    ax.text(1.15, 8, "patamar de deposição\nturbulenta (~22 %)",
            fontsize=8.5, color="#9a6b00", ha="center")

    ax.set_xlabel("Diâmetro da partícula  d  (µm)")
    ax.set_ylabel("Eficiência de coleta  η  (%)")
    ax.set_title("Curva de eficiência de grade — ciclone Stairmand HE, D$_c$ = 307 mm, 100 % de vazão",
                 fontsize=11.5, pad=26)
    ax.set_ylim(0, 104); ax.set_xlim(0.7, 200)
    ax.grid(True, which="both", alpha=0.22)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)

    sec = ax.secondary_xaxis("top", functions=(lambda d: stokes(np.asarray(d)*1e-6),
                                               lambda s: np.sqrt(np.asarray(s)*18*MU*DC/(RHO_P*V_I))*1e6))
    sec.set_xlabel("Número de Stokes  St = ρ$_p$d²v$_i$ / (18 µ D$_c$)", fontsize=9)

    fig.tight_layout()
    fig.savefig("curva_eta_x_d.png", dpi=150)
    print("\n  → curva_eta_x_d.png")
