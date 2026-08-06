"""
convolucao_CFD.py — EFICIÊNCIA GLOBAL a partir da curva η(d) MEDIDA no CFD.

Substitui o stand-in de Lapple do `convolucao_eficiencia.py`.

PSD: análise por PENEIRAMENTO da Valgroup (planilha do ciclone, aba 1).
     ⚠️ A peneira mais fina é 61 µm. O "fundo de peneira" — 9,14 % da massa —
        NÃO tem distribuição interna medida. É a maior incerteza do projeto.

Uso: python3 convolucao_CFD.py
"""
import numpy as np
from curva_eta_x_d import eta_cfd, eta_lapple, D_STAR_LAPPLE

# ── PSD peneirada (planilha Valgroup, aba "Distribuição de Tamanhos") ─────
#    (d# médio em µm, fração mássica)
PENEIRADA = [(8625.0, 0.0278), (2875.0, 0.0377), (712.5, 0.0951),
             (287.5, 0.1210), (112.5, 0.2579), (68.0, 0.3691)]
FUNDO = 0.0914          # < 61 µm — distribuição interna NÃO MEDIDA

M_PART_KGH = 80.0       # particulado total


def eta_global(d_fundo_um, eta_fn):
    """η global com o fundo de peneira concentrado em d_fundo_um."""
    acc = sum(f*eta_fn(d) for d, f in PENEIRADA)
    return acc + FUNDO*float(np.asarray(eta_fn(d_fundo_um)))


def eta_l(d_um):
    return eta_lapple(np.asarray(d_um)*1e-6, D_STAR_LAPPLE)


if __name__ == "__main__":
    print("="*74)
    print("  EFICIÊNCIA GLOBAL — curva CFD × PSD peneirada da Valgroup")
    print("="*74)

    grosso = sum(f*eta_cfd(d) for d, f in PENEIRADA)
    print(f"\n  Fração PENEIRADA (≥ 61 µm): {sum(f for _,f in PENEIRADA)*100:.2f} % da massa")
    print(f"  η nessa fração (CFD)      : {grosso/sum(f for _,f in PENEIRADA)*100:.2f} %")
    print("  ⇒ TODAS as faixas medidas caem na região onde η = 100 %.\n")
    print(f"  Fundo de peneira (< 61 µm): {FUNDO*100:.2f} % da massa — DISTRIBUIÇÃO NÃO MEDIDA")

    print("\n" + "-"*74)
    print("  SENSIBILIDADE — η global conforme onde esteja o fundo de peneira")
    print("-"*74)
    print(f"\n  {'d do fundo':>12} {'η(d) CFD':>11} {'η GLOBAL CFD':>14} {'η GLOBAL Lapple':>17}")
    print("  " + "-"*58)
    for d in (61, 40, 30, 20, 15, 10, 7, 5, 3, 2, 1):
        gc = eta_global(d, lambda x: eta_cfd(x))
        gl = eta_global(d, eta_l)
        print(f"  {d:>10} µm {eta_cfd(d)*100:>10.1f} % {gc*100:>13.2f} % {gl*100:>16.2f} %")

    bc = [eta_global(d, lambda x: eta_cfd(x)) for d in (61, 1)]
    bl = [eta_global(d, eta_l) for d in (61, 1)]
    print("\n" + "="*74)
    print(f"  BANDA com a curva CFD    : {bc[1]*100:.1f} a {bc[0]*100:.1f} %   →  {(bc[0]-bc[1])*100:.1f} pontos")
    print(f"  BANDA com Lapple         : {bl[1]*100:.1f} a {bl[0]*100:.1f} %   →  {(bl[0]-bl[1])*100:.1f} pontos")
    print("="*74)
    print(f"""
  LEITURA
  -------
  A curva CFD ESTREITA a incerteza de {(bl[0]-bl[1])*100:.0f} para {(bc[0]-bc[1])*100:.0f} pontos, porque ela tem
  um PATAMAR de ~22 % abaixo de 3 µm (deposição turbulenta) enquanto Lapple
  tende a zero. Mesmo no cenário mais pessimista — todo o fundo de peneira
  em 1 µm — o ciclone entrega {bc[1]*100:.0f} %.

  Emissão correspondente, com {M_PART_KGH:.0f} kg/h de particulado:
     melhor caso : {M_PART_KGH*(1-bc[0]):.2f} kg/h de char arrastado
     pior  caso : {M_PART_KGH*(1-bc[1]):.2f} kg/h

  ⇒ O pedido de DIFRAÇÃO A LASER no fundo de peneira (< 61 µm) é o único
    item capaz de fechar esse intervalo. Ver dados_cliente/PEDIDO_valgroup.md §5.
""")
