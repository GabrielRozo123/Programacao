#!/usr/bin/env python3
"""
Balanco de energia da coluna -- o teste que qualquer EMP de coluna de bolhas
tem de passar antes de se acreditar na turbulencia dele.

MOTIVACAO
---------
O caso do Nivel 1b reportou

    Volume Average de Turbulent Dissipation Rate, ponderado pela fracao de
    agua, sobre a region inteira:   4,255e-4 m2/s3

O objetivo aqui e decidir se esse numero e um RESULTADO ou um SINTOMA.

O ARGUMENTO
-----------
Em batelada e em regime permanente a coluna e um sistema fechado em energia
mecanica. O gas sobe, e o unico caminho pelo qual ele entrega energia ao
liquido e o ARRASTO. Por unidade de volume de mistura:

    potencia entregue = alpha * (rho_l - rho_g) * g * u_slip

e em batelada u_slip ~ v_gas = Ug/alpha, entao alpha se cancela:

    potencia/volume = (rho_l - rho_g) * g * Ug

O liquido nao acumula energia cinetica em regime permanente e nao tem saida.
Logo TUDO isso tem de reaparecer como dissipacao. Dividindo pela massa de
liquido por unidade de volume:

    eps_diss = (rho_l - rho_g) g Ug / (rho_l (1 - alpha))   ~   g Ug

Esse resultado nao depende de modelo de turbulencia, de malha ou de
fechamento. E contabilidade. Se o CFD reporta muito menos que isso, falta
uma FONTE -- nao e a coluna que e pouco turbulenta.
"""

import math

from memorial import G, MU_L, RHO_L, SIGMA, UG_EXP, d_critico_martinez_bazan

RHO_G = 1.2
UG = UG_EXP[2]
EPS_ALPHA = 0.049795          # holdup do Nivel 1b, aos 74,4 s
SLIP = 0.2331                 # slip do Nivel 1b
D_B = 0.0045                  # diametro prescrito na Interaction Length Scale

MEDIDO = 4.255158e-04         # [m2/s3] Volume Average reportado


def dissipacao_esperada():
    """Dissipacao especifica no liquido, por balanco de energia."""
    pot_vol = EPS_ALPHA * (RHO_L - RHO_G) * G * SLIP      # [W/m3]
    massa_vol = RHO_L * (1.0 - EPS_ALPHA)                 # [kg/m3]
    return pot_vol / massa_vol, pot_vol


def nu_t_sato(c=0.6):
    """Viscosidade turbulenta induzida pelas bolhas (Sato & Sekoguchi, 1975).

        nu_t,BIT = C * alpha * d_b * |u_slip|

    E a contribuicao que NAO depende do cisalhamento do liquido -- por isso
    ela e a unica fonte relevante numa coluna em batelada, onde o liquido
    medio esta praticamente parado.
    """
    return c * EPS_ALPHA * D_B * SLIP


def main():
    eps_esp, pot_vol = dissipacao_esperada()
    razao = eps_esp / MEDIDO

    print("=" * 78)
    print("BALANCO DE ENERGIA -- A DISSIPACAO REPORTADA E POSSIVEL?")
    print("=" * 78)
    print(f"  Ug                            {UG:12.4f} m/s")
    print(f"  holdup (Nivel 1b)             {EPS_ALPHA:12.5f}")
    print(f"  slip                          {SLIP:12.4f} m/s")
    print("-" * 78)
    print(f"  potencia entregue ao liquido  {pot_vol:12.1f} W/m3")
    print(f"  massa de liquido              "
          f"{RHO_L*(1-EPS_ALPHA):12.1f} kg/m3")
    print("-" * 78)
    print(f"  eps_diss ESPERADA (balanco)   {eps_esp:12.4f} m2/s3")
    print(f"  eps_diss = g*Ug (regra usual) {G*UG:12.4f} m2/s3")
    print(f"  eps_diss MEDIDA no caso       {MEDIDO:12.6f} m2/s3")
    print("-" * 78)
    print(f"  RAZAO ESPERADA / MEDIDA       {razao:12.0f} x")
    print("=" * 78)
    print("  O balanco e contabilidade, nao modelo: a potencia do empuxo entra")
    print("  no liquido pelo arrasto e nao tem para onde ir a nao ser dissipar.")
    print(f"  Um fator de {razao:.0f} nao e imprecisao de fechamento. E fonte")
    print("  faltando.")
    print("=" * 78)

    print("\nQUAL FONTE FALTA")
    print("-" * 78)
    print("  O k-epsilon so produz turbulencia a partir do CISALHAMENTO do")
    print("  campo medio de liquido. E o campo de liquido desta coluna esta")
    print("  praticamente parado -- voce mediu +/- 0,04 m/s, quase uniforme.")
    print("  Sem cisalhamento, sem producao. Dai o epsilon ~ 0.")
    print("-" * 78)
    print("  Numa coluna de bolhas em batelada QUASE TODA a turbulencia e")
    print("  induzida pelas bolhas, nao pelo cisalhamento. Essa contribuicao")
    print("  entra por um termo-fonte separado:")
    print("")
    print("     Phase Interactions > Agua-Ar > Models")
    print("         [ ] Particle Induced Turbulence Source   <-- provavelmente")
    print("                                                      DESLIGADO")
    print("-" * 78)
    nu_bit = nu_t_sato()
    nu_mol = MU_L / RHO_L
    print(f"  Sato daria   nu_t,BIT = C alpha d_b u_slip = {nu_bit:.3e} m2/s")
    print(f"  viscosidade molecular da agua              = {nu_mol:.3e} m2/s")
    print(f"  razao                                      = {nu_bit/nu_mol:.0f}")
    print("-" * 78)
    print("  CONSEQUENCIA RETROATIVA: a Dispersao Turbulenta do Nivel 1 nunca")
    print("  foi testada. Ela e proporcional a nu_t, e nu_t esta ~zero. O")
    print("  Nivel 1 deu nulo por DUAS razoes independentes -- campo sem")
    print("  gradiente E viscosidade turbulenta sem fonte.")
    print("=" * 78)

    print("\nO QUE ISSO FAZ COM O DIAMETRO ESTAVEL")
    print("-" * 78)
    print(f"{'cenario':>34s}{'eps_diss':>12s}{'d_crit':>10s}{'veredito':>18s}")
    print(f"{'':>34s}{'[m2/s3]':>12s}{'[mm]':>10s}")
    print("-" * 78)
    for nome, e in (("medido hoje (sem BIT)", MEDIDO),
                    ("com BIT, pelo balanco", eps_esp),
                    ("regra g*Ug", G * UG)):
        dc = d_critico_martinez_bazan(e)
        v = "16 mm sobrevive" if dc >= 0.016 else f"teto de {dc*1000:.0f} mm"
        print(f"{nome:>34s}{e:12.5f}{dc*1000:10.1f}{v:>18s}")
    print("-" * 78)
    print("  Se eu tivesse aceitado os 4,3e-4 como resultado, teria concluido")
    print("  que a quebra e inerte ate 92 mm e mandado rodar 16 mm sem")
    print("  ressalva. Com a fonte no lugar o teto cai para ~10 mm.")
    print("=" * 78)

    print("\nCOMO CONFIRMAR EM DOIS REPORTS")
    print("-" * 78)
    print("  1) Volume Average de Turbulent Viscosity Ratio (fase Agua)")
    print(f"        se der ~1 a 2      -> nu_t ~ molecular, BIT desligado")
    print(f"        se der ~{nu_bit/nu_mol:.0f}       -> Sato ativo e coerente")
    print("  2) Volume Average de Turbulent Kinetic Energy (fase Agua)")
    print("        k ~ 1e-6 m2/s2     -> liquido inerte, confirma o item 1")
    print("-" * 78)
    print("  Os dois levam segundos e fecham o diagnostico sem rodar nada.")
    print("=" * 78)


if __name__ == "__main__":
    main()
