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

# ── OS DEZ PONTOS MEDIDOS EM CADA CARGA (COM dispersão turbulenta) ───────
D_UM   = np.array([1.0, 2.0,  5.0,  7.0,  10.0,  15.0,  20.0,  50.0,  75.0, 150.0])
ETA    = np.array([22.70, 22.31, 31.34, 51.35, 79.14, 97.70, 99.98, 100.0, 100.0, 100.0])/100
ETA_50 = np.array([25.44, 24.52, 26.19, 33.08, 50.49, 81.21, 94.96, 100.0, 100.0, 100.0])/100

# sensibilidade SEM dispersão (só onde foi medida; ⚠️ ver ressalva no doc)
D_SEM   = np.array([1.0, 2.0, 5.0])
ETA_SEM = np.array([22.51, 19.90, 37.44])/100
NRES    = np.array([22.1, 19.1, 37.2])          # % não resolvidas — 1 µm é o único conclusivo

# ── Parâmetros do caso ────────────────────────────────────────────────────
RHO_P, MU, V_I, DC = 1500.0, 9.5e-5, 13.59, 0.307
D_STAR_LAPPLE = 8.28e-6      # m

eta_lapple = lambda d_m, ds: 1/(1+(ds/d_m)**2)
stokes     = lambda d_m: RHO_P*d_m**2*V_I/(18*MU*DC)


def eta_cfd(d_um, carga="100"):
    """Interpola a curva medida em log(d). Fora da faixa: satura.
    carga = "100" ou "50". Escalar entra, escalar sai."""
    y = ETA if carga == "100" else ETA_50
    r = np.interp(np.log(np.asarray(d_um, dtype=float)), np.log(D_UM), y)
    return float(r) if np.isscalar(d_um) or np.ndim(d_um) == 0 else r


def d_star_cfd(carga="100"):
    """Diâmetro onde η = 50 %, por interpolação log-linear."""
    y = ETA if carga == "100" else ETA_50
    i = np.searchsorted(y, 0.5)
    (x1, y1), (x2, y2) = (D_UM[i-1], y[i-1]), (D_UM[i], y[i])
    return np.exp(np.log(x1) + (0.5-y1)/(y2-y1)*(np.log(x2)-np.log(x1)))


def d_cruzamento():
    """Onde as duas curvas se cruzam (Δ = 0)."""
    dd = np.logspace(np.log10(1), np.log10(20), 2000)
    diff = eta_cfd(dd, "50") - eta_cfd(dd, "100")
    i = np.where(np.diff(np.sign(diff)))[0]
    return dd[i[0]] if len(i) else np.nan


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

    print(f"\n  d*(50 %)    = {d_star_cfd('50'):.2f} µm")
    print(f"  razão d* 50/100 = {d_star_cfd('50')/d_star_cfd('100'):.3f}   (Lapple: 1,413)")
    print(f"  cruzamento das curvas = {d_cruzamento():.2f} µm")
    print("\n  d (µm)    η 100 %    η 50 %     Δ turndown")
    print("  " + "-"*46)
    for d, a, b in zip(D_UM, ETA, ETA_50):
        print(f"  {d:6.0f}   {a*100:7.2f} %  {b*100:7.2f} %   {(b-a)*100:+7.2f}")

    # ── figura ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    dd = np.logspace(np.log10(0.7), np.log10(200), 500)
    dcr = d_cruzamento()

    ax.semilogx(dd, eta_lapple(dd*1e-6, D_STAR_LAPPLE)*100, "--", lw=1.4,
                color="#aaa", label="Lapple (ρ$_p$=1500, 100 %)")
    ax.semilogx(dd, eta_cfd(dd, "100")*100, "-", lw=2.5, color="#1f6feb",
                label="CFD · 100 % de vazão (v$_i$=13,59 m/s)")
    ax.semilogx(dd, eta_cfd(dd, "50")*100, "-", lw=2.5, color="#cf222e",
                label="CFD ·  50 % de vazão (v$_i$=6,80 m/s)")
    ax.semilogx(D_UM, ETA*100, "o", ms=7, color="#1f6feb", zorder=5,
                markeredgecolor="white", markeredgewidth=1.1)
    ax.semilogx(D_UM, ETA_50*100, "s", ms=7, color="#cf222e", zorder=5,
                markeredgecolor="white", markeredgewidth=1.1)

    for ds, c, lab in ((d_star_cfd("100"), "#1f6feb", "6,84"), (d_star_cfd("50"), "#cf222e", "9,90")):
        ax.plot([ds], [50], "*", ms=13, color=c, zorder=7, markeredgecolor="white")
    ax.axhline(50, color="#ddd", lw=0.8, zorder=0)
    ax.annotate("d* = 6,84 µm", xy=(6.84, 50), xytext=(2.7, 62), fontsize=9, color="#1f6feb",
                arrowprops=dict(arrowstyle="->", color="#1f6feb", lw=0.9))
    ax.annotate("d* = 9,90 µm", xy=(9.90, 50), xytext=(16, 40), fontsize=9, color="#cf222e",
                arrowprops=dict(arrowstyle="->", color="#cf222e", lw=0.9))

    ax.axvline(dcr, color="#57606a", lw=1, ls=":")
    ax.annotate(f"cruzamento\n{dcr:.1f} µm", xy=(dcr, 26), xytext=(1.05, 68),
                fontsize=8.5, color="#57606a", ha="left",
                arrowprops=dict(arrowstyle="->", color="#57606a", lw=0.9))
    ax.text(1.02, 5.5, "← turndown MELHORA\n   (deposição turbulenta)", fontsize=8, color="#57606a")
    ax.text(11, 5.5, "turndown PIORA →\n(inércia centrífuga)", fontsize=8, color="#57606a")

    ax.set_xlabel("Diâmetro da partícula  d  (µm)")
    ax.set_ylabel("Eficiência de coleta  η  (%)")
    ax.set_title("Eficiência de grade — ciclone Stairmand HE, D$_c$ = 307 mm\n"
                 "CFD Lagrangeano · 20 classes medidas · ρ$_p$ = 1500 kg/m³",
                 fontsize=11, pad=24)
    ax.set_ylim(0, 104); ax.set_xlim(0.9, 200)
    ax.grid(True, which="both", alpha=0.2)
    ax.legend(loc="center right", fontsize=8.8, framealpha=0.95)

    sec = ax.secondary_xaxis("top", functions=(lambda d: stokes(np.asarray(d)*1e-6),
                                               lambda s: np.sqrt(np.asarray(s)*18*MU*DC/(RHO_P*V_I))*1e6))
    sec.set_xlabel("Número de Stokes (a 100 % de vazão)", fontsize=8.5)

    fig.tight_layout()
    fig.savefig("curva_eta_x_d.png", dpi=155)
    print("\n  → curva_eta_x_d.png")
