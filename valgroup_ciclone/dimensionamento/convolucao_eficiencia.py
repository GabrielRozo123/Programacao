"""
convolucao_eficiencia.py — converte a CURVA η(d) do CFD em EFICIÊNCIA GLOBAL para uma PSD qualquer.

Por que este script existe
--------------------------
A curva de eficiência de grade η(d) é uma **propriedade do ciclone** (geometria + escoamento),
NÃO do que entra nele. Uma vez medida no CFD, ela serve para qualquer alimentação:

    η_global = Σ f_i · η(d_i)

Ou seja: quando a Valgroup enviar a PSD amostrada NA CORRENTE GASOSA (a que ainda falta), não é
preciso rodar CFD nenhum de novo — troca-se a PSD aqui e a resposta sai em segundos.

É por isso que injetamos CLASSES MONODISPERSAS no STAR em vez de uma distribuição Rosin-Rammler:
a distribuição devolveria UM número global (para uma PSD incerta), a curva devolve a FÍSICA.

Uso: python3 convolucao_eficiencia.py
"""
import numpy as np

# ──────────────────────────────────────────────────────────────────────────
# 1. A CURVA η(d)  — substituir pelos valores do CFD assim que rodarem
# ──────────────────────────────────────────────────────────────────────────
# Enquanto o Lagrangeano não roda, usamos Lapple como stand-in: η = 1/(1+(d*/d)²)
D_STAR = {"100%": 7.6, "50%": 10.8}      # µm — diâmetro de corte (ρ_p = 1500 kg/m³)

def eta_lapple(d_um, d_star_um):
    return 1.0 / (1.0 + (d_star_um / d_um) ** 2)

# Quando o CFD terminar, troque por interpolação nos pontos medidos:
# ETA_CFD = {"100%": {1:0.0x, 2:..., 5:..., 10:..., 20:..., 50:..., 75:..., 150:...}}
# def eta_cfd(d, carga): return np.interp(np.log(d), np.log(ds), etas)

# ──────────────────────────────────────────────────────────────────────────
# 2. A PSD DA ALIMENTAÇÃO
# ──────────────────────────────────────────────────────────────────────────
# ⚠️ ESTIMADA. A amostra que o cliente mandou é do char EXTRAÍDO (fundo): 28% dela é >1 mm,
#    que fisicamente NÃO pode ser arrastada a 1,03 m/s (v_terminal 1,3–13,4 m/s).
#    Esta é a amostra reponderada aplicando o corte de arraste (~346 µm).
#    ➜ PENDÊNCIA COM A VALGROUP: PSD amostrada NA CORRENTE GASOSA.
PSD_ESTIMADA = [  # (d_min µm, d_max µm, fração mássica)
    (150, 425, 0.358),
    ( 75, 150, 0.512),
    ( 20,  75, 0.131),
]

M_TOTAL_KGH = 80.0   # particulado total


def rosin_rammler_fit(psd):
    """Ajusta R(d)=exp(-(d/d')^n) (fração ACIMA de d) a uma PSD em faixas."""
    acum, pts = 0.0, []
    for lo, hi, f in psd:                      # psd vem da faixa mais grossa p/ a mais fina
        acum += f
        pts.append((lo, acum))                 # acima de `lo` está tudo o que já somou
    (x1, r1), (x2, r2) = pts[0], pts[1]
    y1, y2 = np.log(-np.log(r1)), np.log(-np.log(r2))
    n = (y1 - y2) / (np.log(x1) - np.log(x2))
    dref = np.exp(np.log(x1) - y1 / n)
    return dref, n


def convolui(psd, eta_fn, d_star):
    tot = 0.0
    linhas = []
    for lo, hi, f in psd:
        dm = np.sqrt(lo * hi)                  # média geométrica (faixa log-espaçada)
        e = eta_fn(dm, d_star)
        tot += f * e
        linhas.append((lo, hi, f, dm, e))
    return tot, linhas


if __name__ == "__main__":
    dref, n = rosin_rammler_fit(PSD_ESTIMADA)
    print("=" * 74)
    print(" PSD estimada do char ARRASTADO — ajuste Rosin-Rammler")
    print("=" * 74)
    print(f"  R(d) = exp(-(d/{dref:.1f})^{n:.2f})      [d em µm, R = fração ACIMA de d]")
    print(f"  → se algum dia quiser injetar a distribuição no STAR em vez das classes:")
    print(f"      Reference Size (d') = {dref*1e-6:.3e} m    Exponent (n) = {n:.2f}\n")
    for d in (10, 20, 50, 75, 150, 250, 425):
        print(f"      acima de {d:>3} µm : {np.exp(-(d/dref)**n)*100:5.1f} %")

    print("\n" + "=" * 74)
    print(" CONVOLUÇÃO η_global = Σ f_i·η(d_i)   [η de Lapple — trocar pelo CFD]")
    print("=" * 74)
    for carga, ds in D_STAR.items():
        tot, linhas = convolui(PSD_ESTIMADA, eta_lapple, ds)
        print(f"\n  --- {carga} da vazão · d* = {ds} µm ---")
        for lo, hi, f, dm, e in linhas:
            print(f"    {lo:>3}–{hi:<3} µm | f = {f*100:4.1f}% | d_méd = {dm:5.1f} µm | η = {e*100:6.2f}%")
        print(f"    {'':>3} {'':<3}    | {'':>10} | {'ETA GLOBAL':>14} = {tot*100:6.2f}%")
        print(f"    emissão = {(1-tot)*100:.2f}% = {M_TOTAL_KGH*(1-tot):.2f} kg/h")

    print("\n" + "=" * 74)
    print(" ⚠️  LEITURA CRÍTICA")
    print("=" * 74)
    print("  Toda a PSD estimada está ACIMA de 20 µm — muito acima do corte (7,6 µm).")
    print("  Por isso η_global sai ~99%: a resposta é dominada por partículas que o ciclone")
    print("  captura com folga. TODA a ação da curva η(d) está ABAIXO de 20 µm,")
    print("  exatamente onde NÃO temos dado amostrado.")
    print("  ➜ A curva η(d) do CFD é robusta a isso; a η_global NÃO é.")
    print("  ➜ Entregar a CURVA como resultado, e a η_global como cenário declarado.")
