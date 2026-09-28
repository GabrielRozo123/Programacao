"""
regua_pluma_gaussiana.py — a régua analítica do estudo de dispersão de O₃ (LD Celulose).

Mesma lógica que usamos no ciclone Valgroup (Lapple) e no tanque chiller da GreyLogix:
montar o modelo analítico ANTES de rodar CFD, para (a) saber a ordem de grandeza esperada,
(b) dimensionar a matriz de cenários e (c) ter com o que comparar o resultado do CFD.

Modelo: pluma gaussiana contínua com reflexão no solo, coeficientes de Briggs.

    C(x,0,0) = Q / (pi · u · sy · sz) · exp(-H² / (2·sz²))

O que a régua NÃO faz — e é por isso que o CFD existe:
  · recirculação na esteira dos prédios
  · efeito canyon entre estruturas
  · aprisionamento em pátios fechados
  · plume rise / downwash na descarga dos exaustores
É exatamente nesses lugares que os sensores têm que ir.

Uso:  python3 regua_pluma_gaussiana.py
"""
import numpy as np

# ── conversão ppm ↔ g/m³ para O₃ a 25 °C, 1 atm ──────────────────────────
R, T, P, M_O3 = 8.314, 298.15, 101325.0, 48.0
RHO_O3 = P * M_O3 / (R * T)              # 1962 g/m³ = densidade do O₃ puro
ppm2gm3 = lambda ppm: ppm * 1e-6 * RHO_O3

LIMIARES = {"0,01 ppm (afeta)": 0.01, "0,2 ppm (isola área)": 0.2,
            "0,5 ppm (isola tudo)": 0.5, "3 ppm (off-gás)": 3.0}

# ── coeficientes de Briggs ───────────────────────────────────────────────
# Rural = campo aberto. Urbano = rugosidade de planta industrial — é o caso daqui.
def sigmas(x, classe, terreno="urbano"):
    x = np.maximum(x, 1.0)
    if terreno == "rural":
        tab = {"A": (0.22, -0.5, 0.0001, 0.20,  0.0, 0.0),
               "B": (0.16, -0.5, 0.0001, 0.12,  0.0, 0.0),
               "C": (0.11, -0.5, 0.0001, 0.08, -0.5, 0.0002),
               "D": (0.08, -0.5, 0.0001, 0.06, -0.5, 0.0015),
               "E": (0.06, -0.5, 0.0001, 0.03, -1.0, 0.0003),
               "F": (0.04, -0.5, 0.0001, 0.016, -1.0, 0.0003)}
    else:  # urbano / industrial
        tab = {"A": (0.32, -0.5, 0.0004, 0.24,  0.5, 0.001),
               "B": (0.32, -0.5, 0.0004, 0.24,  0.5, 0.001),
               "C": (0.22, -0.5, 0.0004, 0.20,  0.0, 0.0),
               "D": (0.16, -0.5, 0.0004, 0.14, -0.5, 0.0003),
               "E": (0.11, -0.5, 0.0004, 0.08, -0.5, 0.0015),
               "F": (0.11, -0.5, 0.0004, 0.08, -0.5, 0.0015)}
    ay, py, by, az, pz, bz = tab[classe]
    sy = ay * x * (1 + by * x) ** py
    sz = az * x * ((1 + bz * x) ** pz if bz else 1.0)
    return sy, sz


def C_solo(x, Q, u, classe, H=0.0, terreno="urbano"):
    """Concentração no solo, na linha de centro. Q em g/s, u em m/s, x e H em m."""
    sy, sz = sigmas(x, classe, terreno)
    return Q / (np.pi * u * sy * sz) * np.exp(-(H ** 2) / (2 * sz ** 2))


# A pluma gaussiana diverge quando x -> 0 (fonte pontual). Abaixo de ~10 m ela não
# vale de qualquer forma: é campo próximo, dominado pelo momento do jato e pelo prédio.
# É precisamente o regime que só o CFD resolve.
X_MIN = 10.0


def dist_ate(limiar_ppm, Q, u, classe, H=0.0, terreno="urbano"):
    """Maior distância em que a concentração ainda excede o limiar."""
    x = np.logspace(np.log10(X_MIN), 4, 20000)
    c = C_solo(x, Q, u, classe, H, terreno)
    m = c >= ppm2gm3(limiar_ppm)
    return x[m].max() if m.any() else 0.0


# ── CENÁRIOS ─────────────────────────────────────────────────────────────
# [SUPOSTO] Q = 1 g/s (3,6 kg/h) — valor de referência. A VAZÃO REAL DA FONTE É A
# PENDÊNCIA Nº 1 do projeto. Como C é LINEAR em Q, basta reescalar.
Q_REF = 1.0
CASOS = [("D · vento 5 m/s   (diurno típico)", "D", 5.0),
         ("D · vento 3 m/s   (diurno fraco)",  "D", 3.0),
         ("E · vento 2 m/s   (transição)",     "E", 2.0),
         ("F · vento 1,5 m/s (noturno estável)", "F", 1.5)]

if __name__ == "__main__":
    print("=" * 78)
    print(f" RÉGUA — PLUMA GAUSSIANA · O₃ · LD Celulose")
    print(f" Q = {Q_REF} g/s ({Q_REF*3.6:.1f} kg/h) [SUPOSTO] · fonte no solo · terreno urbano/industrial")
    print("=" * 78)
    print(f"\n 1 ppm de O₃ a 25 °C = {ppm2gm3(1)*1000:.3f} mg/m³\n")

    print(" DISTÂNCIA (m) ATÉ CADA LIMIAR")
    print(f" {'cenário':36s}" + "".join(f"{k.split(' ')[0]:>12s}" for k in LIMIARES))
    for nome, cl, u in CASOS:
        linha = f" {nome:36s}"
        for _, lim in LIMIARES.items():
            d = dist_ate(lim, Q_REF, u, cl)
            linha += f"{d:>11.0f}m" if d else f"{'—':>12s}"
        print(linha)

    print("\n ⭐ O FATOR DE ESTABILIDADE — mesma fonte, condições diferentes")
    base = dist_ate(0.2, Q_REF, 5.0, "D")
    for nome, cl, u in CASOS:
        d = dist_ate(0.2, Q_REF, u, cl)
        print(f"   {nome:36s} 0,2 ppm até {d:6.0f} m   ({d/base:5.1f}× o caso típico)")

    print("\n ⚠️  SENSIBILIDADE À RUGOSIDADE — é uma PREMISSA, não um detalhe")
    print("     (0,2 ppm · distância em m · mesma fonte)")
    print(f"   {'cenário':36s}{'rural':>10s}{'urbano/ind.':>14s}{'razão':>9s}")
    for nome, cl, u in CASOS:
        dr = dist_ate(0.2, Q_REF, u, cl, terreno="rural")
        du = dist_ate(0.2, Q_REF, u, cl, terreno="urbano")
        print(f"   {nome:36s}{dr:9.0f}m{du:13.0f}m{dr/du:8.1f}×")
    print("   >> Terreno rural dá distâncias ~3× maiores. A planta tem rugosidade de")
    print("      sítio industrial, mas o entorno é agrícola. Definir na Etapa 2.")

    print("\n EFEITO DA ALTURA DA DESCARGA (classe D, 5 m/s, limiar 0,2 ppm)")
    print("   — é por isso que a ALTURA E DIREÇÃO do exaustor importam mais que a vazão")
    xg = np.logspace(np.log10(X_MIN), 4, 20000)
    for H in [5, 10, 15, 20, 30]:
        d = dist_ate(0.2, Q_REF, 5.0, "D", H=H)
        cmax = C_solo(xg, Q_REF, 5.0, "D", H=H).max() / ppm2gm3(1)
        alvo = f"{d:5.0f} m" if d else "  não atinge"
        print(f"   descarga a {H:2d} m :  0,2 ppm até {alvo}   ·  pico no solo {cmax:7.3f} ppm")

    print("\n VAZÃO DE FONTE QUE JÁ BASTA para 0,2 ppm a 100 m (fonte no solo)")
    for nome, cl, u in CASOS:
        sy, sz = sigmas(100.0, cl)
        Q = ppm2gm3(0.2) * np.pi * u * sy * sz          # [g/s]
        print(f"   {nome:36s} Q = {Q:6.3f} g/s = {Q*3.6:6.3f} kg/h")

    print("\n ⚠️  Tudo acima é ORDEM DE GRANDEZA, não previsão. Serve para dimensionar a")
    print("    matriz de cenários e para conferir se o CFD saiu num lugar razoável.")
    print("    O CFD existe para o que a gaussiana não faz: prédios.\n")
