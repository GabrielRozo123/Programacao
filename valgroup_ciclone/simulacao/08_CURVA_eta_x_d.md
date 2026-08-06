# 08 — CURVA η × d · Dc = 307 mm · 100 % de vazão

> Campo base: **Rodada 8** (k-ω steady · `Outlet` · parede convectiva · ΔP = 1.955,6 Pa).
> Método: **η = 1 − |mdot_gas| / mdot_inj** (ver `07_EXECUCAO` §8).
> Fase Lagrangeana: **ρ_p = 1500 kg/m³** · classes monodispersas · 5.082 parcels.

---

## 1. Resultados medidos

| d (µm) | sub-steps | ativas no fim | **η c/ dispersão** | **η s/ dispersão** | Lapple (d\*=8,28) |
|---|---|---|---|---|---|
| **1** | 150.000 | 34 (0,67 %) ✅ | **22,70 %** | — | 1,4 % |
| **2** | 150.000 | 28 (0,55 %) ✅ | **22,31 %** | — | 5,5 % |
| **2** | 150.000 | 968 (19,1 %) ⚠️ | — | *19,9 %* | 5,5 % |
| ~~2~~ | ~~50.000~~ ⚠️ | ~~1.325 (26,1 %)~~ | ~~62,0 %~~ | — | *descartada, §2* |
| **5** | 150.000 | 19 (0,37 %) ✅ | **31,34 %** | — | 26,7 % |
| **50** | 20.000 | 5.077 (travadas) ✅ | **100,00 %** | — | 97,3 % |

*(nas classes grossas a fração ativa não cai — travam na parede — mas o η já está determinado
porque `mdot_gas` zera cedo; ver `07_EXECUCAO` §9.4)*

---

## 2. ✅ RESOLVIDO — a inconsistência do 2 µm era sub-step

A sequência com dispersão dava **22,7 / 62,0 / 31,3 %** para 1 / 2 / 5 µm — impossível, porque
eficiência de grade é monotônica.

**Causa:** o 2 µm era o único a 50.000 sub-steps, com **26,1 % das parcelas sem resolver**, todas
contadas como retidas.

**Refeito a 150.000: η = 22,31 %** (28 parcelas ativas = 0,55 %).
*(previsão registrada antes: "entre 22,7 e 31,3 %, provavelmente 26–28" — o medido ficou logo
abaixo da faixa)*

### E os dois pontos finos são o MESMO número
```
1 µm: 22,70 %      SE = √[η(1−η)/N] = √(0,2231·0,7769/5082) = 0,58 ponto
2 µm: 22,31 %      diferença = 0,39 ponto = 0,67 σ
```
**Estatisticamente indistinguíveis.** Não é dispersão de resultado — é um **PATAMAR**.

Abaixo de ~2 µm a captura deixa de depender da inércia e passa a ser governada por **deposição
turbulenta na parede**; a partícula vira quase um traçador e o tamanho para de importar. Regime
real e reconhecido em ciclones.

---

## 2b. ⚠️ CORREÇÃO DO §10 DO `07_EXECUCAO` — o efeito da dispersão é MUITO menor

O §10 registrou **fator 3,1** para a dispersão turbulenta, comparando 62,0 % (com) × 19,9 % (sem).
**Comparação inválida:** o 62,0 % vinha da rodada de 50.000 sub-steps, não convergida.

Comparação correta, **ambas a 150.000**:

| 2 µm | η | não resolvidas |
|---|---|---|
| **com** dispersão | **22,31 %** | 0,55 % ✅ |
| **sem** dispersão | *19,9 %* | 19,1 % ⚠️ órbitas permanentes |

⇒ **2,4 pontos de diferença, não 42.**

**Isso melhora o entregável:** a banda da ponta fina encolhe de ~5,7 pontos em η_global para
cerca de **1,2 ponto**. O número confiável é o **com dispersão** — o caso sem dispersão tem
ambiguidade insolúvel por construção (19,1 % em órbita determinística permanente).

---

## 3. A assinatura da dispersão isotrópica

| d (µm) | CFD | Lapple | **razão** |
|---|---|---|---|
| 1 | 22,7 % | 1,4 % | **16,2** |
| 5 | 31,3 % | 26,7 % | **1,17** |
| 50 | 100,0 % | 97,3 % | **1,03** |

A razão **cai monotonicamente com o tamanho**: quanto mais leve a partícula, mais ela obedece ao
chute turbulento radial que o modelo isotrópico exagera. É o mesmo mecanismo que o teste
com/sem dispersão isolou (§10 do `07_EXECUCAO`): 2 µm vai de **62,0 % para 19,9 %** ao desligar
o modelo.

**Formato da curva:** a ponta fina fica **achatada** (22,7 % → ~27 % → 31,3 % entre 1 e 5 µm) —
característico do regime dominado por transporte turbulento, onde a captura deixa de depender da
inércia. O fenômeno é real; aqui está **exagerado pela isotropia** do k-ω.

---

## 4. O que falta

| classe | c/ dispersão | s/ dispersão |
|---|---|---|
| 1 µm | ✅ 22,70 % | ⏳ |
| **2 µm** | ✅ **22,31 %** | ✅ 19,9 % *(com ressalva)* |
| 5 µm | ✅ 31,34 % | ⏳ |
| 10 µm | ⏳ 150.000 | — |
| 20 µm | ⏳ 150.000 | — |
| 50 µm | ✅ 100,00 % | — |
| 75 µm | ⏳ 20.000 | — |
| 150 µm | ⏳ 20.000 | — |

Depois: repetir a **50 % de vazão** (v_i = 6,80 m/s · `mdot_inj` = 1,389e-3).

---

## 5. Premissas e limitações — para o entregável

1. **η = 1 − fuga.** Partícula que trava na parede é contada como retida. Fisicamente correto
   (está no strand), mas **não representa reentranhamento** ⇒ viés levemente otimista, maior no
   grosso. Medido: +2,7 pts em 50 µm sobre Lapple.
2. **Dispersão turbulenta isotrópica** (k-ω, Boussinesq) superestima o transporte radial, que na
   realidade é suprimido pelo gradiente centrífugo. **Medido em 2 µm: 22,31 % com × 19,9 % sem —
   apenas 2,4 pontos** (§2b). O efeito é pequeno; a ponta fina vai como **banda estreita**.
3. **ρ_p = 1500 kg/m³.** A planilha do cliente usa 776,75 (densidade **aparente do leito**,
   abaixo do mínimo de 1500 que a própria tabela de valores usuais dela declara). Conversão para
   qualquer outra densidade ou viscosidade: `07_EXECUCAO` §9.2 (número de Stokes).
4. **Sensibilidade à malha no bico** não quantificada — item de estudo futuro.
5. A conversão para **eficiência global** exige a PSD, cuja fração abaixo de 61 µm **não é
   medida** (peneiramento) e vale **17 pontos** de η_global —
   `dimensionamento/sensibilidade_finos.py`. **É a maior incerteza do projeto**, maior que a
   banda da dispersão (5,7 pontos).


---

# 6. CURVA A 50 % DE VAZÃO (v_i = 6,80 m/s · `mdot_inj` = 1,389e-3)

| d (µm) | **η 50 %** | η 100 % | **Δ (turndown)** |
|---|---|---|---|
| 1 | **25,44 %** | 22,70 % | **+2,74** |
| 2 | **24,52 %** | 22,31 % | +2,21 |
| 5 | **26,19 %** | 31,34 % | −5,15 |
| 7 | **33,08 %** | 51,35 % | −18,27 |
| **10** | **50,49 %** | 79,14 % | **−28,65** ← pico |
| 15 | ⏳ ~82 % | 97,70 % | |
| 20 | ⏳ ~95 % | 99,98 % | |
| 50 · 75 · 150 | ⏳ 100 % | 100,00 % | |

**d\*(50 %) = 9,90 µm** (interpolado entre 7 e 10 µm).

## 6.1 ⭐ VALIDAÇÃO — o escalonamento com a vazão bate com o analítico

| | d\* |
|---|---|
| CFD a 100 % | 6,84 µm |
| CFD a 50 % | 9,90 µm |
| **razão CFD** | **1,447** |
| **razão Lapple** (11,70/8,28) | **1,413** |
| **diferença** | **2,4 %** |

**Mais forte que a comparação absoluta.** O CFD discorda de Lapple em 17 % no **nível** de d\*,
mas concorda em 2,4 % em **como** a separação responde à vazão. Um erro de modelo raramente
preserva a derivada.

## 6.2 O turndown NÃO degrada uniformemente
A penalidade se concentra numa janela estreita — **5 a 15 µm** — e **atinge o pico em 10 µm,
com −28,7 pontos**. Fora dela é quase nula, e **abaixo de 2,6 µm ela INVERTE**: o turndown
melhora a captura.

### O cruzamento das curvas, em 2,6 µm
| faixa | mecanismo dominante | efeito de reduzir a vazão |
|---|---|---|
| **< 2,6 µm** | deposição turbulenta (depende de **tempo**) | **melhora** — a residência do gás dobra (0,48 → 0,96 s) |
| **> 2,6 µm** | inércia centrífuga (depende de **v²**) | **piora** |

⇒ Resultado com valor operacional direto: **em turndown o ciclone perde eficiência apenas numa
faixa estreita de tamanho**, e ganha na ponta fina.

## 6.3 O *fishhook* — aparece nas DUAS cargas
```
100 %:  η(1 µm) = 22,70 %  >  η(2 µm) = 22,31 %     (+0,39)
 50 %:  η(1 µm) = 25,44 %  >  η(2 µm) = 24,52 %     (+0,92)
```
**A eficiência sobe quando a partícula fica MAIS fina.** É o *fishhook*, fenômeno documentado em
ciclones, e aqui com mecanismo explícito: abaixo do regime inercial, quanto menor a partícula
mais difusiva ela é, e mais deposição turbulenta sofre. A inércia deixou de proteger; a difusão
passou a capturar.

**Significância:** 0,67 σ e 1,5 σ contra o erro estatístico de ~0,6 ponto (5.082 parcels).
Individualmente fracos, **mas no mesmo sentido nas duas cargas** — o que torna bem mais provável
feição real que ruído. Reportar com essa ressalva.

## 6.4 Nota operacional — o limite que passa a valer a 50 %
A rodada de 10 µm terminou em **134.515 sub-steps**, não em 150.000: foi o
**`Maximum Residence Time` (10 s)** que limitou, não os sub-steps. A 50 % de vazão a partícula
envelhece mais rápido em tempo físico por sub-step.

**Não alterar o limite.** As parcelas cortadas tinham 10 s — mais de **dez vezes** o tempo de
residência do gás (0,96 s). Se não escaparam em dez passagens, não escapariam. São 0,1 % do total.
