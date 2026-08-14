"""
algebra_lancas.py — DIMENSIONAMENTO do arranjo de lanças do aerador (Fase 3 · Ito)

Decisão do cliente (06/08/2026): retomar o aerador APENAS COM LANÇAS (sem ejetor),
com liberdade para alterar NÚMERO, DIÂMETRO, ALTURA DE DESCARGA e FUROS.

O que este script resolve
-------------------------
Para cada arranjo (N lanças · Ø da lança · cota de descarga · furos), calcula:
  1. hidráulica  — velocidade, Reynolds, perda de carga (Poiseuille laminar)
  2. geometria   — se as N lanças cabem no aerador Ø2032
  3. aeração     — vazão de ar por ponto de descarga, submergência, tempo de contato
  4. bolha       — diâmetro de formação por Tate (limite estático)

⚠️ SOBRE O TAMANHO DE BOLHA
O diâmetro de formação num orifício é o ÚNICO item aqui que não é hidráulica pura.
Usa-se a lei de Tate (limite estático de destacamento por empuxo × tensão superficial):
    d_b = (6·σ·d_furo / ρ·g)^(1/3)
Ela é o LIMITE INFERIOR: no regime viscoso (Davidson-Schuler) a bolha cresce com µ e com
a vazão de gás por furo. Portanto os valores de d_b abaixo são OTIMISTAS e assim declarados.
"""
import numpy as np

# ── Fluido e processo ─────────────────────────────────────────────────────
RHO, MU, SIGMA = 1350.0, 6.5, 0.058        # xarope: kg/m³, Pa·s, N/m
Q_XAR = 130.0/3600                          # m³/s  (130 m³/h — bomba Colombo)
Q_AR  = 40.0/3600                           # m³/s  (alvo do Ito)
G = 9.81

# ── Geometria do aerador (medida no STEP) ─────────────────────────────────
D_AER, R_AER = 2.032, 1.016                # m
Z_SUPERFICIE = 1.2200                       # m — superfície livre
Z_FUNDO      = -5.8920                      # m — fundo do aerador
Z_TOPO_LANCA = 1.8408                       # m — cota de entrada nas lanças (mantida)

# ── Tubos comerciais Sch40 (ID, OD em m) ──────────────────────────────────
TUBOS = {'1½"': (0.0409, 0.0483), '2"': (0.0525, 0.0603),
         '2½"': (0.0627, 0.0730), '3"': (0.0779, 0.0889), '4"': (0.1023, 0.1143)}

FOLGA = 0.030          # m — folga mínima entre lanças (montagem/solda)
DP_BOMBA_MAX = 6.0e5   # Pa — teto razoável de descarga de bomba de processo (6 bar)


def tate(d_furo):
    """Diâmetro de bolha no destacamento — limite estático (otimista)."""
    return (6*SIGMA*d_furo/(RHO*G))**(1/3)


def cabem(n, od, r_circ):
    """N lanças de diâmetro externo `od` cabem num círculo de raio r_circ?"""
    if n == 1:
        return True
    passo_ang = 2*np.pi/n
    corda = 2*r_circ*np.sin(passo_ang/2)          # distância entre centros
    return corda >= od + FOLGA and r_circ + od/2 <= R_AER - FOLGA


def sampson_dp(q_furo, d_furo):
    """Perda por orifício fino em escoamento reptante (Sampson): ΔP = 3µQ/a³."""
    return 3*MU*q_furo/(d_furo/2)**3


def n_furos_para(dp_alvo, d_furo, q_total):
    """Quantos furos de `d_furo` são precisos para passar q_total com ΔP ≤ dp_alvo."""
    return 3*MU*q_total/((d_furo/2)**3 * dp_alvo)


def arranjo(n, tubo, z_desc, d_furo=1.0e-3, n_furos=12):
    di, od = TUBOS[tubo]
    a_int = np.pi/4*di**2
    q_l   = Q_XAR/n
    v     = q_l/a_int
    re    = RHO*v*di/MU
    comp  = Z_TOPO_LANCA - z_desc                 # comprimento da lança
    dp_l  = 32*MU*comp*v/di**2                    # Poiseuille
    # furos: a vazão de xarope sai pelos furos
    a_f   = np.pi/4*d_furo**2
    v_f   = q_l/(n_furos*a_f)
    dp_f  = sampson_dp(q_l/n_furos, d_furo)       # orifício fino, escoamento reptante
    subm  = Z_SUPERFICIE - z_desc
    # raio do círculo de lanças: o maior que cabe
    r_c   = R_AER - od/2 - FOLGA
    return dict(n=n, tubo=tubo, di=di, od=od, v=v, re=re, comp=comp,
                dp_l=dp_l, dp_f=dp_f, dp=dp_l+dp_f+RHO*G*subm - RHO*G*comp,
                v_furo=v_f, subm=subm, r_c=r_c, cabe=cabem(n, od, r_c),
                q_ar_ponto=Q_AR/(n*n_furos)*3.6e6,      # cm³/s por furo
                d_bolha=tate(d_furo)*1e3)               # mm


if __name__ == "__main__":
    print("="*90)
    print("  ARRANJO DE LANÇAS — aerador Ø2032 · xarope 130 m³/h · ar 40 m³/h")
    print("="*90)

    print("\n### 1. BOLHA vs DIÂMETRO DE FURO (lei de Tate — limite otimista)\n")
    print("   furo (mm)   d_bolha (mm)   vs meta 0,20 mm")
    print("   " + "-"*46)
    for df in (3.0, 2.0, 1.0, 0.5, 0.3, 0.2, 0.1):
        db = tate(df*1e-3)*1e3
        print(f"   {df:7.1f}     {db:9.2f}       {db/0.2:6.1f}×")
    print("\n   ⚠️ d_b ∝ d_furo^(1/3): reduzir o furo 30× reduz a bolha só 3×.")

    Q_MIST = Q_XAR + Q_AR
    print("\n\n### 2. ⭐ FUROS — quantos são precisos para passar a mistura")
    print(f"       (xarope + ar = {Q_MIST*3600:.0f} m³/h · orifício fino, Sampson)\n")
    print("   furo (mm)   d_bolha (mm)    nº de furos para ΔP de:")
    print("                              1 bar      3 bar      6 bar")
    print("   " + "-"*62)
    for df in (0.5, 1.0, 2.0, 3.0, 5.0, 9.0):
        db = tate(df*1e-3)*1e3
        ns = [n_furos_para(p*1e5, df*1e-3, Q_MIST) for p in (1, 3, 6)]
        print(f"   {df:7.1f}     {db:9.2f}     {ns[0]:9.0f}  {ns[1]:9.0f}  {ns[2]:9.0f}")
    print("\n   ⇒ furo menor dá bolha menor, mas o número de furos explode com 1/d³.")

    print("\n\n### 3. ⭐ HIDRÁULICA DA LANÇA × NÚMERO DE LANÇAS")
    print("       (Ø2½\" · descarga em z = −5,2465 · SEM os furos)\n")
    print("    N    v (m/s)     Re     ΔP lança   cabem?")
    print("   " + "-"*46)
    for n in (4, 6, 8, 12, 16, 20, 24, 28, 32):
        a = arranjo(n, '2½"', -5.2465)
        ok = "OK " if a['cabe'] else "NAO"
        print(f"   {n:3d}   {a['v']:6.2f}   {a['re']:6.1f}   {a['dp_l']/1e5:7.2f} bar     {ok}")
    print("\n   ⇒ ΔP ∝ 1/N. Passar de 4 para 16 lanças reduz a perda na lança de 11,0 para 2,7 bar.")

    print("\n\n### 4. COTA DE DESCARGA (N = 16 · Ø2½\")\n")
    v_sub = RHO*G*(2e-3)**2/(18*MU)
    print("   z desc (m)   comp (m)   submerg (m)   ΔP lança   subida da bolha (2 mm)")
    print("   " + "-"*72)
    for z in (-5.2465, -4.5, -3.5, -2.5, -1.5):
        a = arranjo(16, '2½"', z)
        print(f"   {z:8.3f}   {a['comp']:7.2f}   {a['subm']:9.2f}   {a['dp_l']/1e5:7.2f} bar"
              f"       {a['subm']/v_sub/3600:8.2f} h")

    print("\n\n### 5. DIÂMETRO DO TUBO (N = 16 · z = −5,2465)\n")
    print("   tubo    ID (mm)   v (m/s)    Re     ΔP lança   cabem?")
    print("   " + "-"*56)
    for t in TUBOS:
        a = arranjo(16, t, -5.2465)
        ok = "OK " if a['cabe'] else "NAO"
        print(f"   {t:5s}   {a['di']*1e3:6.1f}   {a['v']:6.2f}   {a['re']:6.1f}   "
              f"{a['dp_l']/1e5:7.2f} bar     {ok}")

    print("\n\n### 6. GEOMETRIA — quantas lanças cabem no aerador Ø2032\n")
    print("   tubo    OD (mm)   raio do círculo (mm)   N máximo")
    print("   " + "-"*52)
    for t, (di, od) in TUBOS.items():
        r_c = R_AER - od/2 - FOLGA
        nmax = int(np.pi/np.arcsin((od+FOLGA)/(2*r_c)))
        print(f"   {t:5s}   {od*1e3:6.1f}       {r_c*1e3:8.0f}          {nmax:4d}")
