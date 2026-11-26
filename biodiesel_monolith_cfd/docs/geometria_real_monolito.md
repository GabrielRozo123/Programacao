# Geometria real do monólito — consequências para o modelo

**Origem:** medidas da peça de suporte do catalisador, repassadas pelo
Prof. Raphael Suppino em 26/11/2026.

```
altura da peça (comprimento do canal)   29,15 mm
abertura de célula                       0,55 mm
arranjo                                  canais quadrados, 2 × 2 na peça fotografada
uso previsto                             várias peças empilhadas, recheando o leito
```

---

## O que muda em relação ao que foi simulado

| | Simulado (Fases 1–3) | Peça real |
|---|---|---|
| Seção do canal | plano, $H$ = 1,1 mm | quadrado, lado 0,55 mm |
| Paredes catalíticas | 1 (a outra inerte) | 4 |
| Comprimento | 50 mm | 29,15 mm |
| $D_h$ | 2,20 mm | 0,55 mm |

A altura de 1,1 mm adotada veio da geometria de 400 cpsi de
Asli (2011). A peça do laboratório tem **metade** dessa abertura, e canais
quadrados em vez de plano.

---

## Consequências estimadas

Extrapolações a partir do modelo verificado, pela solução de Lévêque e pelo
balanço de área. **São estimativas de ordem de grandeza**, não substituem
simular a geometria real.

```
                              simulado        real
Re                            0,182           0,045
Pe = Re·Sc                    3,1e4           7,9e3
L_entrada,massa               3457 mm          216 mm
L_e/L                         69              7,4
δ_c(L)                        179 µm          119 µm
k_m ~ D/δ_c                   3,90e-7 m/s     5,88e-7 m/s
área de parede / volume       909 1/m         7273 1/m
```

**Número de Damköhler:** 0,76 → **≈ 0,51**

O canal menor engrossa menos a camada-limite, o coeficiente de transferência
de massa sobe 1,5×, e a resistência ao transporte perde peso relativo. **O
regime continua misto**, e a conclusão central da Fase 3 se mantém.

**Conversão por passe:** 1,40 % → **≈ 7,7 %**

O ganho vem de dois fatores: área de parede por volume 8× maior (quatro
paredes e canal menor), parcialmente compensada pelo comprimento menor, o que
dá fator 4,7; e menor limitação por transporte, fator 1,17.

---

## O empilhamento favorece o sistema, e isso é quantificável

Com $L_e/L$ = 7,4 o canal opera na região de entrada, onde o coeficiente de
transferência de massa decai como $x^{-1/3}$. Empilhar peças curtas com mistura
entre elas **reinicia a camada-limite a cada peça**, mantendo $k_m$ alto.

Comparado a um canal contínuo de mesmo comprimento total, fatiar em $N$ peças
eleva o $k_m$ médio por um fator $N^{1/3}$:

```
N = 10 peças   →  2,2×
N = 30 peças   →  3,1×
```

Supondo reinício completo a cada peça:

```
 5 peças  =  146 mm de leito  →  X ≈ 33 %
10 peças  =  292 mm           →  X ≈ 55 %
20 peças  =  583 mm           →  X ≈ 80 %
30 peças  =  875 mm           →  X ≈ 91 %
```

Perda de carga estimada para 30 peças: ≈ 364 Pa. Desprezível.

**A condição para que isso valha é que haja mistura entre as peças.** Se elas
forem empilhadas com os canais alinhados e sem folga, o escoamento enxerga um
canal contínuo, a camada-limite não reinicia, e o ganho de $N^{1/3}$ desaparece.
Um pequeno espaçamento, ou rotação de 45° entre peças sucessivas, basta.

---

## O que o modelo precisa

A física, as Field Functions e o protocolo de verificação transferem sem
alteração. Muda a geometria e a malha:

```
□ Domínio novo: duto quadrado de 0,55 mm, comprimento 29,15 mm
□ Por simetria, simular um quarto: 0,275 × 0,275 mm, com dois planos de simetria
□ Deixa de ser pseudo-2D — passa a ser 3D de verdade, mas pequeno
□ Camadas prismáticas nas duas paredes catalíticas do quarto de duto
□ Reverificar: estequiometria, independência de malha, balanço global
```

---

## Perguntas em aberto com o laboratório

```
□ Quantos canais por peça? (a foto mostra 2 × 2)
□ Espessura de parede do substrato
□ Material da peça
□ Como as peças serão empilhadas: canais alinhados, ou com folga/rotação?
□ Diâmetro interno do tubo do reator
□ Vazão ou velocidade superficial prevista
```

As três últimas são as que mais afetam o resultado.

---

*Novembro/2026 | Gabriel Rozo — FEQ/UNICAMP*
