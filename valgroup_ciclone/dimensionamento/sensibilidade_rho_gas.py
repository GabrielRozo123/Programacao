"""
sensibilidade_rho_gas.py — IMPACTO DE ±5 % NA MASSA ESPECÍFICA DO GÁS
                            SOBRE A EFICIÊNCIA DE COLETA (pedido do Marcus)

A pergunta do cliente é sobre ρ do gás, mas a variável de processo que está
travada é a VAZÃO MÁSSICA (1 820 kg/h de gás). Isso decide tudo:

    v_i = mdot / (rho · A)        →   v_i  ∝  1/rho
    Re  = mdot · D / (A · mu)     →   Re   INDEPENDENTE de rho
    dP  = xi · ½ · rho · v_i²     →   dP   ∝  1/rho
    St  = rho_p · d² · v_i / (18 · mu · Dc)   →   St ∝ 1/rho

Como Re não muda, o campo ADIMENSIONAL é o mesmo: mesmo vórtice, mesmo número
efetivo de voltas. Só a ESCALA de velocidade muda. Logo a curva de eficiência
não muda de FORMA — ela apenas desliza em d, pela equivalência de Stokes:

    eta_novo(d) = eta_ref( d · sqrt(v_novo/v_ref) ) = eta_ref( d / sqrt(rho_novo/rho_ref) )
    d*_novo = d*_ref · sqrt(rho_novo/rho_ref)        →   d* ∝ sqrt(rho)

    (gás mais DENSO → v_i menor → St menor → corte mais grosso → eta menor)

NÃO é preciso rodar CFD novo. A curva medida é reaproveitada com esse mapa.

Uso: python3 sensibilidade_rho_gas.py
"""
import numpy as np
from curva_eta_x_d import eta_cfd, d_star_cfd
from convolucao_CFD import PENEIRADA, FUNDO, M_PART_KGH

# ── Base ──────────────────────────────────────────────────────────────────
RHO_BASE = 3.946            # kg/m³ @ 400 °C, 1,2 bar
MDOT_GAS = 1820.0           # kg/h — FIXO. É a âncora de toda a análise.
DC, A_IN = 0.307, 0.5*0.307 * 0.2*0.307     # Stairmand: a=0,5Dc · b=0,2Dc
MU = 9.5e-5

DP_MEDIDO = {"100": 1955.6, "50": 468.0}    # Pa, das rodadas CFD na base
V_BASE    = {"100": 13.594, "50": 6.797}    # m/s

CENARIOS = [("-5 %", 0.95), ("base", 1.00), ("+5 %", 1.05)]


def eta_desloc(d_um, carga, f_rho):
    """Curva de eficiência com rho = f_rho · rho_base, a vazão MÁSSICA fixa."""
    return eta_cfd(np.asarray(d_um, dtype=float) / np.sqrt(f_rho), carga)


def eta_global(eta_fn, d_fundo_um):
    """Convolução com a PSD peneirada; fundo (<61 µm) concentrado em d_fundo."""
    return sum(f*float(eta_fn(d)) for d, f in PENEIRADA) + FUNDO*float(eta_fn(d_fundo_um))


if __name__ == "__main__":
    print("="*78)
    print("  SENSIBILIDADE A ±5 % NA MASSA ESPECÍFICA DO GÁS")
    print(f"  Vazão mássica FIXA = {MDOT_GAS:.0f} kg/h  ·  rho_base = {RHO_BASE:.3f} kg/m³")
    print("="*78)

    # ── 1. o que muda no escoamento ───────────────────────────────────────
    print("\n  1. ESCOAMENTO\n")
    print(f"  {'cenário':>8} {'rho':>8} {'v_i 100 %':>11} {'v_i 50 %':>10}"
          f" {'dP 100 %':>10} {'dP 50 %':>9} {'Re':>10}")
    print("  " + "-"*70)
    for nome, f in CENARIOS:
        rho = RHO_BASE*f
        v100, v50 = V_BASE["100"]/f, V_BASE["50"]/f
        dp100, dp50 = DP_MEDIDO["100"]/f, DP_MEDIDO["50"]/f
        re = (MDOT_GAS/3600)*DC/(A_IN*MU)
        print(f"  {nome:>8} {rho:>8.3f} {v100:>9.2f} m/s {v50:>8.2f} m/s"
              f" {dp100/100:>8.2f} mbar {dp50/100:>7.2f} mbar {re:>10.0f}")
    print("\n  → Re é o MESMO nos três cenários. O campo adimensional não muda.")
    print("  → dP varia ∓5 %: o pior caso de perda de carga é o gás MAIS LEVE.")

    # ── 2. o que muda no corte ────────────────────────────────────────────
    print("\n  2. DIÂMETRO DE CORTE  (d* ∝ sqrt(rho))\n")
    print(f"  {'cenário':>8} {'d* 100 %':>11} {'d* 50 %':>11}   variação")
    print("  " + "-"*46)
    for nome, f in CENARIOS:
        d100, d50 = d_star_cfd("100")*np.sqrt(f), d_star_cfd("50")*np.sqrt(f)
        print(f"  {nome:>8} {d100:>9.2f} µm {d50:>9.2f} µm   {(np.sqrt(f)-1)*100:+6.2f} %")
    print("\n  → ±5 % em rho move o corte apenas ±2,5 % (raiz quadrada).")

    # ── 3. o que muda na eficiência de grade ──────────────────────────────
    print("\n  3. EFICIÊNCIA DE GRADE — onde o deslocamento aparece\n")
    print(f"  {'d (µm)':>8}", end="")
    for carga in ("100", "50"):
        for nome, _ in CENARIOS:
            print(f" {carga+'%/'+nome:>11}", end="")
    print()
    print("  " + "-"*76)
    for d in (2, 5, 7, 10, 15, 20, 40, 61):
        print(f"  {d:>8}", end="")
        for carga in ("100", "50"):
            for _, f in CENARIOS:
                print(f" {eta_desloc(d, carga, f)*100:>10.2f} %", end="")
        print()
    print("\n  → Acima de ~20 µm nada muda: já está em 100 %.")
    print("  → O efeito se concentra entre 5 e 15 µm, a região do joelho da curva.")

    # ── 4. EFICIÊNCIA GLOBAL — a resposta ao Marcus ───────────────────────
    print("\n" + "="*78)
    print("  4. EFICIÊNCIA GLOBAL  (convolução com a PSD peneirada da Valgroup)")
    print("="*78)
    print("""
  O fundo de peneira (9,14 % da massa, < 61 µm) não tem distribuição medida.
  Varre-se onde ele possa estar — é a única fatia da PSD sensível a rho.
""")
    for carga in ("100", "50"):
        print(f"\n  ─── {carga} % DE VAZÃO " + "─"*52)
        print(f"\n  {'fundo em':>9} {'eta -5 %':>11} {'eta base':>11} {'eta +5 %':>11}"
              f" {'amplitude':>12} {'arraste base':>15}")
        print("  " + "-"*74)
        pior = (0.0, None)
        for d_fundo in (61.0, 40.0, 30.0, 20.0, 15.0, 10.0, 7.0, 5.0, 3.0, 1.0):
            e = [eta_global(lambda d: eta_desloc(d, carga, f), d_fundo) for _, f in CENARIOS]
            amp = max(e) - min(e)
            if amp > pior[0]:
                pior = (amp, d_fundo)
            print(f"  {d_fundo:>7.0f} µm {e[0]*100:>9.2f} % {e[1]*100:>9.2f} %"
                  f" {e[2]*100:>9.2f} % {amp*100:>9.2f} pt {M_PART_KGH*(1-e[1]):>12.2f} kg/h")
        print(f"\n  pior caso de sensibilidade: fundo em {pior[1]:.0f} µm"
              f"  →  {pior[0]*100:.2f} ponto de amplitude")

    # ── 5. a armadilha ────────────────────────────────────────────────────
    print("\n" + "="*78)
    print("  5. A ARMADILHA — o sinal depende do que se mantém fixo")
    print("="*78)
    print("""
  Se a variação de rho for imposta mantendo a VAZÃO VOLUMÉTRICA (v_i fixa),
  em vez da mássica, TUDO se inverte:

     v_i constante  →  St constante  →  eta NÃO MUDA (zero impacto)
                    →  dP ∝ rho      →  pior caso passa a ser o gás MAIS DENSO
                    →  mas a vazão mássica de gás variaria ∓5 %, o que não é
                       o caso: o processo entrega 1 820 kg/h.

  Portanto: qualquer rerrodada de verificação PRECISA ser especificada em
  vazão MÁSSICA, não em m³/h. Caso contrário o resultado responde a outra
  pergunta.

  Origem física da variação também importa:
     • se rho varia por COMPOSIÇÃO (massa molar): mu praticamente não muda
       → vale exatamente o que está acima, d* ∝ sqrt(rho).
     • se rho varia por TEMPERATURA (rho ∝ 1/T a pressão fixa): mu sobe com T
       (~T^0,7), e como St ∝ 1/(mu·rho), os dois efeitos se OPÕEM.
       Para -5 % em rho via T: T sobe 5,3 %, mu sobe ~3,7 %,
       d* ∝ sqrt(rho·mu) → fator sqrt(0,95 × 1,037) = 0,992, ou seja
       -0,8 % em vez de -2,5 %. A variação térmica é AINDA MENOS sensível.
""")
