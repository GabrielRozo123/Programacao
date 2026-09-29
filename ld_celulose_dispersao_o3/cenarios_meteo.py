"""
cenarios_meteo.py — classificação de estabilidade e montagem da matriz de cenários.

Consome a série horária do Zeus (ver analise_meteo_zeus.py) e produz:
  · classificação de Pasquill-Turner hora a hora (usando a luminosidade medida)
  · a matriz de cenários para o DOE de dispersão
  · a planilha consolidada para o cliente

Método de Pasquill-Turner:
  DIA   — classe pela insolação (da coluna de luminosidade) × velocidade do vento
  NOITE — classe pela cobertura de nuvens × velocidade do vento.
          O Zeus NÃO mede nebulosidade. Adotamos o ramo de CÉU LIMPO (<= 3/8),
          que é a hipótese CONSERVADORA para dispersão: menos nuvem = mais
          resfriamento radiativo = inversão mais forte = pluma menos diluída.
          [SUPOSTO] — registrar no relatório.

Uso:  python3 cenarios_meteo.py <xlsx> [saida.xlsx]
"""
import sys
import numpy as np

from analise_meteo_zeus import ler, dir_media, setor, SETORES, KMH

# limiar de partida do anemômetro: abaixo disto a direção não tem significado
V_MIN_DIR = 0.3      # m/s

# faixas de insolação (W/m², a partir da luminosidade horária em Wh/m²)
INSOL_FORTE, INSOL_MODERADA = 700.0, 350.0


def pasquill(u, lum, noite):
    """Classe de Pasquill A(1) a F(6). u em m/s."""
    if noite:
        # ramo de céu limpo (<= 3/8 de nebulosidade) — conservador
        if u < 2.0:   return 'F'
        if u < 3.0:   return 'F'
        if u < 5.0:   return 'E'
        return 'D'
    # dia
    if lum >= INSOL_FORTE:        faixa = 'forte'
    elif lum >= INSOL_MODERADA:   faixa = 'moderada'
    else:                         faixa = 'fraca'
    if faixa == 'forte':
        return 'A' if u < 2 else 'B' if u < 5 else 'C'
    if faixa == 'moderada':
        return 'B' if u < 2 else 'B' if u < 3 else 'C' if u < 6 else 'D'
    return 'B' if u < 2 else 'C' if u < 5 else 'D'


def classificar(dados):
    out = []
    for d in dados:
        if d['v_med'] is None:
            continue
        u = d['v_med'] * KMH
        lum = d['lum'] or 0.0
        noite = (lum <= 0.0)
        out.append(dict(d, u=u, lum=lum, noite=noite, cls=pasquill(u, lum, noite),
                        rajada_ms=(d['rajada'] * KMH) if d['rajada'] else None))
    return out


def main():
    path = sys.argv[1]
    dados = classificar(ler(path))
    u = np.array([d['u'] for d in dados])
    cls = np.array([d['cls'] for d in dados])

    print("=" * 78)
    print(" CLASSIFICAÇÃO DE ESTABILIDADE (Pasquill-Turner) — LD Celulose")
    print("=" * 78)
    print(f" {'classe':>7} {'descrição':>22} {'n':>6} {'freq':>8} {'v_méd':>8} {'v_p10':>8}")
    desc = {'A': 'muito instável', 'B': 'instável', 'C': 'levemente instável',
            'D': 'neutra', 'E': 'levemente estável', 'F': 'estável'}
    freq = {}
    for k in 'ABCDEF':
        m = cls == k
        freq[k] = 100 * m.sum() / len(cls)
        if m.any():
            print(f" {k:>7} {desc[k]:>22} {m.sum():>6} {freq[k]:7.1f}% "
                  f"{u[m].mean():8.2f} {np.percentile(u[m],10):8.2f}")
        else:
            print(f" {k:>7} {desc[k]:>22} {0:>6} {0.0:7.1f}%")

    estavel = freq['E'] + freq['F']
    print(f"\n >> classes ESTÁVEIS (E+F): {estavel:.1f} % das horas")
    print(f"    classe NEUTRA (D)      : {freq['D']:.1f} %")
    print(f"    classes INSTÁVEIS (A-C): {freq['A']+freq['B']+freq['C']:.1f} %")

    # ── rosa restrita a vento com significado direcional ────────────────
    val = [d for d in dados if d['dir'] is not None and d['u'] >= V_MIN_DIR]
    dirs = np.array([d['dir'] for d in val])
    vv = np.array([d['u'] for d in val])
    idx = np.array([setor(x) for x in dirs])
    print("\n" + "─" * 78)
    print(f" ROSA DOS VENTOS — só horas com v >= {V_MIN_DIR} m/s  (n={len(val)})")
    print("─" * 78)
    rosa = []
    for k, nome in enumerate(SETORES):
        m = idx == k
        rosa.append(dict(setor=nome, n=int(m.sum()),
                         freq=100 * m.sum() / len(dirs) if len(dirs) else 0,
                         v=vv[m].mean() if m.any() else 0.0,
                         p95=np.percentile(vv[m], 95) if m.any() else 0.0))
    for r in sorted(rosa, key=lambda x: -x['freq'])[:6]:
        print(f"   {r['setor']:>4}: {r['freq']:5.1f} %   v_méd {r['v']:5.2f} m/s   "
              f"p95 {r['p95']:5.2f} m/s")
    dom = max(rosa, key=lambda r: r['freq'])
    quad = sum(r['freq'] for r in rosa if r['setor'] in ('N', 'NNE', 'NE', 'ENE', 'E'))
    print(f"\n >> dominante {dom['setor']} ({dom['freq']:.1f} %) · "
          f"quadrante N–E concentra {quad:.1f} % das horas")

    # ── velocidade representativa por classe ────────────────────────────
    print("\n" + "─" * 78)
    print(" VELOCIDADE REPRESENTATIVA POR CLASSE (para o CFD)")
    print("─" * 78)
    rep = {}
    for k in 'ABCDEF':
        m = cls == k
        if m.any():
            rep[k] = dict(med=u[m].mean(), p50=np.percentile(u[m], 50),
                          p90=np.percentile(u[m], 90))
            print(f"   {k}: média {rep[k]['med']:5.2f}  mediana {rep[k]['p50']:5.2f}  "
                  f"p90 {rep[k]['p90']:5.2f} m/s")

    # rajada
    rj = np.array([d['rajada_ms'] for d in dados if d['rajada_ms'] is not None])
    print(f"\n RAJADA: média {rj.mean():.2f} · p95 {np.percentile(rj,95):.2f} · "
          f"p99 {np.percentile(rj,99):.2f} · MÁX {rj.max():.2f} m/s")

    return dict(dados=dados, rosa=rosa, rep=rep, freq=freq, rj=rj, dom=dom, quad=quad)


if __name__ == "__main__":
    main()
