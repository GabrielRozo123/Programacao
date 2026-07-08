# 03 — Dados de processo e condições de contorno

> Fonte: e-mail original do cliente (dados fornecidos por GreyLogix). A confirmar que seguem
> válidos para o novo cenário (pergunta 5 em `05_...`).

## Fluido — solução hidroalcoólica
- **Composição:** 70% água / 30% etanol (m/m).
- **Propriedades a 0 °C** (fornecidas pelo cliente):

| Propriedade | Valor |
|---|---|
| Densidade | 932,65 kg/m³ |
| Viscosidade dinâmica | 0,00179626 Pa·s |
| Condutividade térmica | 0,275767 W/(m·K) |
| Capacidade térmica (cp) | 3,652 kJ/(kg·K) |

- **Densidade em função de T (usada no CFD as-built):**
  **ρ = 1082,88 − 0,55·T** [kg/m³, T em K] → dá 932,66 a 0 °C (bate com o fornecido).
  É essa dependência de ρ com T que **governa a estratificação** (empuxo). A −5 °C: ρ ≈ 935,4;
  a +5 °C: ρ ≈ 929,9 → **o frio afunda**.
- O cliente autoriza usar **pacote termodinâmico próprio** para as propriedades, como alternativa
  aos valores acima.

## Circuito do chiller
| Corrente | Pressão | Temperatura | Vazão |
|---|---|---|---|
| **Saída** da solução ao chiller | tanque atmosférico (0 barg) | 5 °C | 12 m³/h |
| **Entrada** da solução vinda do chiller | 1,5 barg (recalque; sem perda de carga até o tanque) | −5 °C | 12 m³/h |

## Condições iniciais e de parede
- **Temperatura inicial** (todo o tanque): **+5 °C** uniforme.
- **Material/parede:** Inox 304 com **isolamento de 100 mm** → tratado como **parede adiabática**
  no CFD (ganho térmico estimado < 2% da capacidade do chiller com 100 mm de isolamento).

## Capacidade térmica efetiva do chiller
- a **0 °C**: 35.984 kcal/h
- a **−5 °C**: 30.583 kcal/h

## Lógica de controle
- O chiller **deveria desligar** assim que o tanque medir **−5 °C**.
  (No as-built adotou-se T de entrada fixa em −5 °C, chiller com capacidade não limitada —
  resultado conservador; o resfriamento real pode ser ligeiramente mais lento.)

## Recirculação (novo — só no cenário 2)
- **Bomba de 12 m³/h** acoplada ao tanque (loop de mistura, separado do chiller).
- **[PENDENTE]** alturas de captação e retorno, DN dos bocais, e se os 12 m³/h **somam** aos
  12 m³/h do chiller (duas bombas) ou é a mesma vazão. Ver pergunta 4 em `05_...`.
