# 02 — Dados de processo e critérios de projeto

> Fonte: `Dados - Reatores anóxicos.xlsx`, enviado por Douglas Costa (Nexus) em 21/09/2026.
> Transcrição integral; nada interpretado.

## 1. O reator

| Parâmetro | Valor |
|---|---|
| Processo | Biológico — lodos ativados com remoção de nutrientes |
| Etapa | **Anóxica** |
| Fluxo | Contínuo |
| **Vazão** | **6,6 a 42,6 m³/h** (turndown de 6,5×) |
| Quantidade de reatores | 1 unidade |
| Formato | Cilíndrico vertical, **fundo plano** |
| **Volume útil** | **48,2 m³** |
| **Diâmetro** | **3,2 m** |
| Altura útil | 6,0 m |
| Altura total | 6,5 m |
| Alimentação | 1 entrada, **DN 100** — cota **6,3 m** |
| Saída | 1 saída, **DN 100** — cota **6,0 m** |

### Geometria derivada
- Área de fundo: π × 1,6² = **8,04 m²**
- Razão altura/diâmetro: 6,0 / 3,2 = **1,88** (tanque esbelto)
- Tempo de residência: **1,13 h** (42,6 m³/h) a **7,30 h** (6,6 m³/h)

## 2. O misturador

| Parâmetro | Valor |
|---|---|
| Quantidade por reator | 1 unidade |
| Tipo | **Hiperbólico** |
| Dimensões | **a determinar** ← é o objeto do estudo (Opção A) |
| **Potência de mistura** | **típ. 1,3 a 4,5 W/m³** |
| **Velocidade junto ao fundo** | **≥ 0,3 m/s** |
| **Faixa de rotação** | típ. **10 a 60 rpm** |

### Orçamento de potência derivado
| | potência total no fluido |
|---|---|
| Piso (1,3 W/m³) | **62,7 W** |
| Teto (4,5 W/m³) | **216,9 W** |

> Esses são os watts **entregues ao líquido**, não a potência de placa do motor.
> No CFD saem do **torque no eixo × rotação**; no campo, da potência elétrica descontado
> o rendimento do conjunto motor-redutor.

## 3. O fluido (lodo ativado)

| Parâmetro | Valor |
|---|---|
| Sólidos em suspensão (SST) | **2,5 a 4,6 kg/m³** |
| Densidade do floco | **1.040 kg/m³** (típ. 1.015 a 1.060) |
| Volume de sólidos | 0,24 a 0,44% |
| Índice Volumétrico do Lodo (IVL) | 50 a 170 mL/g |
| **Diâmetro equivalente do floco (d50)** | **100 µm** (típ. 40 a 200) |

### Propriedades derivadas
- Diferença de densidade floco-água: **40 kg/m³** (4%)
- Fração volumétrica máxima: 0,44% → regime **diluído**
- IVL de 50 a 170 mL/g cobre de **lodo bem sedimentável** a **lodo com tendência a intumescimento
  (bulking)** — é uma faixa larga, e o extremo superior é a condição adversa para o critério 2.

## 4. Os quatro critérios de projeto

Transcritos do documento do cliente:

1. **Mistura completa** — "garantir uma condição eficiente de mistura, aproximando um reator de mistura completa"
2. **Sólidos em suspensão** — "garantir a manutenção dos sólidos em suspensão (com a velocidade próxima ao fundo indicada)"
3. **Sem aeração** — "evitar turbulência excessiva que possa induzir em introdução de oxigênio atmosférico na massa líquida (faixa de potência indicada)"
4. **Sem vórtice** — "evitar a formação de vórtices. A inclusão de defletores na periferia do tanque é uma alternativa, caso necessário."

### Por que o critério 3 existe
O reator é **anóxico**: a remoção de nitrogênio por desnitrificação exige ausência de oxigênio
dissolvido. Oxigênio introduzido pela superfície não é só perda de eficiência — ele **interrompe
a via metabólica** que o reator existe para sustentar. É uma restrição de processo, não de conforto.

### Como cada critério vira métrica no CFD
| Critério | Métrica | Onde sai |
|---|---|---|
| 1 — mistura completa | DTR por traçador numérico vs CSTR ideal; curto-circuito entrada→saída | Etapa 4 |
| 2 — sólidos | mapa de velocidade a [SUPOSTO] 5–10 cm do fundo; fração de área com v < 0,3 m/s; perfil vertical de SST | Etapa 2 |
| 3 — aeração | potência específica (torque × ω / V); velocidade e turbulência na superfície livre (VOF) | Etapa 2 |
| 4 — vórtice | depressão da superfície livre (VOF); necessidade de defletores | Etapa 2/3 |

> **[A CONFIRMAR]** a que altura do fundo o cliente considera "velocidade próxima ao fundo".
> Muda o resultado: 5 cm está dentro da camada limite, 20 cm já é escoamento livre.
> Pergunta 1 em `04_pendencias_e_perguntas.md`.
