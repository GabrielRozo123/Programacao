# Dois slides — resultado do ejetor (apresentação Ito)

> Base: rodada multifásica com ar imposto na vazão-alvo de 40 m³/h · v_bico estabilizada em
> 18,24 m/s · SMD medido no threshold de fração volumétrica de ar > 0,01.

---

# SLIDE 1

## Título
**A bolha gerada não atinge a faixa de flotação**

## Subtítulo
Ar injetado na vazão-alvo de 40 m³/h · xarope 130 m³/h · µ = 6,5 Pa·s

## Corpo

| | |
|---|---|
| Bolha **antes** do bico | 1,00 mm |
| Bolha **depois** do bico | **1,00 mm** |
| Variação ao atravessar | **0,02 %** |
| | |
| **Diâmetro de Sauter gerado** | **1,00 mm** |
| Meta para flotação | 0,20 mm |
| **Razão** | **5×** |

- A bolha atravessa o bico de 7 furos Ø9 mm **sem se alterar**
- Taxa de deformação no bico: **16.200 s⁻¹**
- Não há quebra

> 🖼️ **Figura:** histograma de tamanho de bolha, ponderado por volume de ar,
> com linha de referência em 200 µm

---

# SLIDE 2

## Título
**Cisalhamento não é a alavanca neste xarope**

## Subtítulo
Por que aumentar velocidade, pressão ou vazão não muda o resultado

## Corpo

**O cisalhamento aplicado é altíssimo:**

| | |
|---|---|
| Taxa de deformação no bico | **16.200 s⁻¹** |
| Número de capilaridade | **Ca ≈ 900** |

Para a maioria dos pares de fluidos, um Ca dessa ordem quebraria a gota com folga.
**Aqui não quebra** — e a razão está na natureza do par ar/xarope:

```
λ = µ_ar / µ_xarope = 1,85×10⁻⁵ / 6,5 = 2,8×10⁻⁶  ≈  0
```

**Curva de Grace:** quando a razão de viscosidade tende a zero, o número de capilaridade
crítico **diverge em cisalhamento simples**.

> **Não existe cisalhamento suficiente.** O regime dentro do bico é cisalhamento simples, e
> nesse regime uma bolha de ar em líquido viscoso não se quebra, qualquer que seja a
> intensidade aplicada.

**O que quebraria:**

| mecanismo | presente no ejetor? |
|---|---|
| Cisalhamento simples | ✅ sim — e não quebra |
| **Escoamento extensional / atomização por jato** | ❌ **não** |

Atingir a faixa de flotação (< 200–300 µm) exige **atomização**: jato de ar em alta velocidade
rompendo o líquido — não líquido cisalhando o ar.

## Fecho
> Aumentar a vazão de xarope, a pressão da bomba ou a velocidade no bico **não altera este
> resultado**, porque nenhum deles muda o regime de escoamento nem a razão de viscosidade.

---

# Notas para quem apresenta (não vai no slide)

- **A ordem importa.** O slide 1 dá o número; o slide 2 explica por que ele não se move com
  ajuste de operação. Sem o slide 2, a reação natural é *"e se aumentarmos a pressão?"*.
- **O Ca ≈ 900 é o dado que convence.** Mostra que não se trata de cisalhamento insuficiente —
  o cisalhamento é enorme e mesmo assim não quebra. Desloca a conversa de "intensidade" para
  "mecanismo".
- **É a resposta à pergunta que o próprio cliente fez** na reunião de 21/07: *"quais condições
  favorecem o cisalhamento?"*. Resposta: **nenhuma**, neste par de fluidos. A alavanca não é
  cisalhamento.
- **O SMD de 1,00 mm é o diâmetro de injeção.** O resultado não é o valor absoluto — é o fato
  de ele **não se alterar** ao atravessar o bico.
