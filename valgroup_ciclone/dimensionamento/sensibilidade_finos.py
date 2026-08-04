"""
sensibilidade_finos.py — quanto a EFICIÊNCIA GLOBAL depende da fração de finos NÃO MEDIDA.

Motivação (áudio Valgroup, 04/08/2026)
--------------------------------------
O cliente confirmou que a amostra analisada é o **char COLETADO** (o que ficou para trás),
e que o **carreado NÃO é amostrável** — só se recupera em manutenção, contaminado de parafina.

Mas o achado mais grave é outro: as faixas do dado deles (150-425 / 75-150 / 20-75 µm) são
**peneiras ASTM padrão** (40 / 100 / 200 / 635 mesh). É análise por PENEIRAMENTO, que **não
resolve abaixo de ~20 µm**.

E é justamente abaixo de 10 µm que mora toda a perda do ciclone (d* = 7,6 µm).
⇒ A incerteza do nosso número principal está inteira numa faixa que o dado não mede.

Este script quantifica essa incerteza em vez de escondê-la.
"""
import numpy as np

D_STAR = 7.6          # µm — corte Lapple a 100% de carga, ρ_p = 1500
ETA_GROSSO = None     # calculado abaixo a partir da PSD peneirada

PSD_PENEIRADA = [(150, 425, 0.358), (75, 150, 0.512), (20, 75, 0.131)]

eta = lambda d: 1.0 / (1.0 + (D_STAR / d) ** 2)


def eta_da_parte_grossa():
    return sum(f * eta(np.sqrt(lo * hi)) for lo, hi, f in PSD_PENEIRADA)


if __name__ == "__main__":
    ETA_GROSSO = eta_da_parte_grossa()
    print("=" * 78)
    print("  SENSIBILIDADE DA EFICIÊNCIA GLOBAL À FRAÇÃO DE FINOS NÃO MEDIDA")
    print("=" * 78)
    print(f"\n  d* (Lapple, 100% carga) = {D_STAR} µm")
    print("\n  η(d) na faixa que importa:")
    for d in (250, 100, 39, 20, 10, 6, 3):
        print(f"      {d:5.0f} µm → {eta(d)*100:5.1f} %")

    print(f"\n  η da parte PENEIRADA (>20 µm), como está hoje = {ETA_GROSSO*100:.1f} %")
    print("  ⚠️  Esse é o número que sai HOJE — e ele assume MASSA ZERO abaixo de 20 µm.\n")

    finos = [0.0, 0.02, 0.05, 0.10, 0.20]
    dfs   = [3.0, 6.0, 10.0]
    print("  η_global [%] em função da fração mássica < 20 µm e do seu tamanho médio:\n")
    print("     frac<20µm │  d_finos=3µm   d_finos=6µm   d_finos=10µm")
    print("     ──────────┼──────────────────────────────────────────")
    for phi in finos:
        linha = f"       {phi*100:5.1f} %  │"
        for df in dfs:
            g = (1 - phi) * ETA_GROSSO + phi * eta(df)
            linha += f"   {g*100:8.1f}    "
        print(linha)

    print("\n" + "=" * 78)
    g_min = min((1-0.20)*ETA_GROSSO + 0.20*eta(3.0), (1-0.20)*ETA_GROSSO + 0.20*eta(10.0))
    print(f"  FAIXA: de {ETA_GROSSO*100:.1f} % (finos = 0) a {g_min*100:.1f} % (20 % de finos a 3 µm)")
    print(f"  ⇒ amplitude de {(ETA_GROSSO-g_min)*100:.0f} pontos percentuais, TODA ela")
    print("    dentro do que o peneiramento não mede.")
    print("=" * 78)
    print("""
  CONCLUSÃO PARA O CLIENTE
  ------------------------
  Não é questão de refinar o ajuste da distribuição. Os três modelos de DT
  ajustados pelo cliente e escolhidos por R² são todos ajustados aos MESMOS
  pontos de peneira — e R² sobre curva acumulada é quase cego à cauda fina,
  porque a curva é monótona e suave ali. Os três vão dar R² > 0,98 e divergir
  exatamente onde a resposta mora.

  O que resolve: DIFRAÇÃO A LASER (ou equivalente) na amostra que eles JÁ têm.
  Não precisa coletar material novo nem enfrentar a parafina — é reanalisar o
  char coletado num equipamento que enxergue abaixo de 20 µm.
""")
