"""
fit_PSD_distribuicoes.py — a PSD do char da Valgroup cabe numa função do STAR-CCM+?

Contexto: o Marcus pediu para ajustar a granulometria medida da Valgroup a uma das funções
de distribuição de tamanho nativas do STAR-CCM+ (Rosin-Rammler ou Log-normal), em vez de
usar a tabela de CDF.

Resposta curta: NÃO CABE. Este script é a justificativa quantitativa dessa conclusão.

O motivo é a forma da distribuição medida — um modo estreitíssimo em ~70 µm (cara de corte
de peneira) somado a uma cauda que se estende até 12,5 mm. Nenhuma função de dois parâmetros
reproduz as duas coisas ao mesmo tempo, e o erro cai justamente na massa grossa, que é a que
importa para erosão (energia de impacto ~ d³).

Uso:  python3 fit_PSD_distribuicoes.py
Dados: char_PSD_CDF.csv (mesma tabela usada no injetor do STAR)
"""
import os
import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf

HERE = os.path.dirname(os.path.abspath(__file__))

# ── dados medidos (CDF acumulada passante, em massa) ──────────────────────
# O ponto de 40 µm é SUPOSIÇÃO nossa: é o piso adotado para a fração de fundo de peneira
# que o laudo não caracterizou. Os demais são medidos.
cdf = np.array([0.0000, 0.0914, 0.4605, 0.7184, 0.8394, 0.9345, 0.9722, 1.0000])
d   = np.array([4.0e-5, 6.1e-5, 7.5e-5, 1.5e-4, 4.25e-4, 1.0e-3, 4.75e-3, 1.25e-2])

# pontos internos — 0 e 1 são assíntotas e não restringem o ajuste
m = (cdf > 0) & (cdf < 1)
dm, cm = d[m], cdf[m]


def rosin_rammler(dd, d_ref, n):
    """F(d) = 1 - exp(-(d/d_ref)^n)"""
    return 1 - np.exp(-(dd / d_ref) ** n)


def log_normal(dd, d_g, sigma_g):
    """F(d) = Phi( ln(d/d_g) / ln(sigma_g) )"""
    return 0.5 * (1 + erf(np.log(dd / d_g) / (np.sqrt(2) * np.log(sigma_g))))


print("=" * 74)
print(" PSD DO CHAR — VALGROUP · ajuste às funções nativas do STAR-CCM+")
print("=" * 74)

print("\n1. DISTRIBUIÇÃO DE MASSA MEDIDA")
for i in range(1, len(d)):
    print(f"   {d[i-1]*1e6:8.1f} – {d[i]*1e6:8.1f} µm : {(cdf[i]-cdf[i-1])*100:6.2f} %")
print(f"\n   >> 36,9 % da massa num intervalo de apenas 23 % em diâmetro (61–75 µm),")
print(f"      e uma cauda que vai até 12,5 mm. Faixa total: 312×.")

print("\n2. AJUSTES")
fits = {}
for nome, f, p0, rot in [
    ("Rosin-Rammler", rosin_rammler, [1e-4, 0.8], ("d_ref", "n")),
    ("Log-normal",    log_normal,    [1e-4, 3.0], ("d_g", "sigma_g")),
]:
    p, _ = curve_fit(f, dm, cm, p0=p0, maxfev=400000)
    res = f(dm, *p) - cm
    fits[nome] = (f, p)
    print(f"   {nome:15s} {rot[0]} = {p[0]*1e6:7.2f} µm · {rot[1]} = {p[1]:.4f}"
          f"   RMS = {np.sqrt((res**2).mean()):.4f}   máx|err| = {np.abs(res).max():.4f}")

print("\n3. ONDE O AJUSTE ERRA — a massa grossa, que é a que erode")
print(f"   {'fração acima de':>18}   {'medido':>8}   {'R-R':>8}   {'log-normal':>11}")
for lim in [4.25e-4, 1.0e-3, 4.75e-3]:
    med = 1 - np.interp(lim, d, cdf)
    vals = [1 - f(lim, *p) for f, p in fits.values()]
    print(f"   {lim*1e6:14.0f} µm   {med*100:7.2f}%   {vals[0]*100:7.2f}%   {vals[1]*100:10.2f}%")
print("\n   >> Mesmo o MELHOR ajuste (log-normal) joga fora 6× da massa acima de 425 µm")
print("      e 65× da acima de 1 mm. O Rosin-Rammler é pior: zera a cauda inteira.")
print("      A energia de impacto escala com d³ — perder a cauda é perder o fenômeno.")

print("\n4. CONCLUSÃO")
print("   Usar `Table (particle size CDF)` com char_PSD_CDF.csv no injetor.")
print("   É o recurso NATIVO do STAR para este caso e reproduz a medida sem erro.")
print("   O ajuste analítico fica registrado como tentado e descartado, com os")
print("   números acima como justificativa para o cliente.")
print()
