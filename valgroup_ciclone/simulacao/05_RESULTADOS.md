# RESULTADOS — CFD do Ciclone Valgroup

> Registro acumulativo das rodadas. Geometria: **Stairmand Dc=290 mm** ·
> Malha: **486.990 células** (Face Validity 100% em 1,0 · Volume Change mín 1,1e-2)
> Condição: gás **1820 kg/h** (= 1900 − 80 de particulado) a 400°C / 1,2 bar · ρ=3,946 · µ=9,5e-5

---

## RODADA 1 — 100% da vazão, só gás, K-Omega SST steady ✅

| | valor |
|---|---|
| v_i (entrada) | 15,23 m/s |
| Convergência | ~6.400 iterações, ΔP plano |
| **ΔP (CFD)** | **2.823,9 Pa = 28,24 mbar** |
| ΔP (analítico Stairmand ξ=6,4) | 2.928,9 Pa = 29,29 mbar |
| **Erro CFD × analítico** | **3,6 %** ✅ |
| Limite do cliente | 40 mbar → **folga de 29%** ✅ |

**Checagem cruzada — o fator de perda:**
`ξ_CFD = ΔP/(½ρv_i²) =` **6,17** vs **6,40** tabelado para Stairmand HE
→ a geometria se comporta como um Stairmand de verdade.

**Campo de Total Pressure:** padrão clássico e correto — alta pressão no **anel externo**,
**núcleo de baixa pressão** no eixo e no vortex finder (mín. −251 Pa), gradiente radial forte.

> **Valida de uma vez:** geometria · malha · BCs · modelo físico · **e o dimensionamento analítico**.

---

## RODADA 2 — 50% da vazão ✅

| | valor |
|---|---|
| v_i | 7,62 m/s |
| **ΔP (CFD)** | **642,8 Pa = 6,43 mbar** |
| ΔP (analítico) | 733,2 Pa = 7,33 mbar |
| **Erro** | **12,3 %** ✅ |

**Escalonamento:** ΔP(100%)/ΔP(50%) = **4,39** (teórico v² = 4,00).
**ξ extraído:** 6,17 (100%) → **5,61** (50%) — cai suavemente com o Reynolds, **fisicamente esperado**.

> ✅ **DOIS pontos validados.** O modelo deixou de ser "acertou num ponto" e virou **curva**.

### Resumo da validação
| Carga | v_i | ΔP CFD | ΔP analítico | erro | ξ |
|---|---|---|---|---|---|
| **100%** | 15,23 m/s | **2.823,9 Pa** | 2.928,9 | **3,6%** | 6,17 |
| **50%** | 7,62 m/s | **642,8 Pa** | 733,2 | **12,3%** | 5,61 |

Ambos **muito abaixo** do limite de 40 mbar. A 50% sobra folga enorme (84%).

---

## RODADA 3 — 100% da vazão **COM ENERGIA** (gás ideal + CHT) ✅

**Contexto:** primeira tentativa com `Ideal Gas` deu **ΔP = 381 Pa** (contra 2.823,9 do constant-density).
**Causa:** `Molecular Weight` ficou no default do ar (**28,96**) → ρ = 0,621 em vez de 3,946
(**6,35× baixo**). Diagnóstico previu 444 Pa; observado 381 → confirmado.
**Correção:** `Molecular Weight = 184,0 kg/kmol` (o gás de pirólise, não ar).

| | valor |
|---|---|
| **ΔP (CFD, gás ideal, M=184)** | **2.893,98 Pa = 28,94 mbar** (it. 9.526) |
| ΔP (constant density) | 2.823,9 Pa |
| ΔP (analítico Stairmand ξ=6,4) | 2.928,9 Pa |
| **Erro × analítico** | **−1,2 %** ✅ *(melhor que os 3,6 % do constant-density)* |
| **ξ extraído** | **6,32** (tabelado: 6,40) |
| Limite do cliente | 40 mbar → **folga de 28 %** ✅ |

> A energia **subiu** o ΔP em 2,5 % (o gás resfria junto à parede → densifica localmente).
> Confirma a previsão de que a térmica **não invalida** a validação hidrodinâmica.

### 🌡️ Temperatura de parede — a pergunta do Lucas, respondida

| | valor |
|---|---|
| **T_parede (CFD)** | **654,142 K = 381,0 °C** (it. 8.882) |
| Estimativa analítica prévia (sem isolamento) | ~356 °C |
| **Ponto de orvalho dos pesados (C12–C15)** | ~250 °C |
| **MARGEM** | **+131 °C** ✅ |

> ✅ **Sem condensação.** E a estimativa analítica (356 °C) errou por só 25 °C para menos —
> ou seja, era **conservadora**, como deveria ser.

### Resumo das três rodadas
| Rodada | Modelo | v_i | **ΔP CFD** | analítico | erro | ξ |
|---|---|---|---|---|---|---|
| 1 · 100 % | K-ω SST, ρ const | 15,23 m/s | 2.823,9 Pa | 2.928,9 | 3,6 % | 6,17 |
| 2 · 50 % | K-ω SST, ρ const | 7,62 m/s | 642,8 Pa | 733,2 | 12,3 % | 5,61 |
| **3 · 100 %** | **K-ω SST + energia (ideal, M=184)** | 15,23 m/s | **2.893,98 Pa** | 2.928,9 | **1,2 %** | **6,32** |

> 🏁 **ETAPA A (hidrodinâmica + térmica) ENCERRADA E VALIDADA.**
> A base está pronta para receber as partículas.

### 📌 Armadilha registrada (nº 5)
**`Ideal Gas` sem ajustar `Molecular Weight`** → o STAR usa o default do ar (28,96) e a densidade sai
errada por um fator, silenciosamente. **Sempre setar M junto com o modelo de gás ideal.**
Aqui: **M = 184 kg/kmol**.

---

## 🌡️ E a TEMPERATURA? (pergunta do Gabriel — resposta com número)

**Sim, vamos fazer CHT — mas depois, e por bons motivos.**

### 1. A temperatura NÃO invalida o que já rodamos
| Cenário | Perda de calor | Queda de T do gás |
|---|---|---|
| **Sem** isolamento (U≈10 W/m²K) | 5,20 kW | **5,1 °C** |
| **Com** lã mineral (U≈3) | 1,56 kW | 1,5 °C |

O gás cai **poucos graus** (a residência é só **0,48 s**) → a densidade muda **<1%** →
**o ΔP praticamente não muda.** ✅ **A validação de 3,6% continua valendo.**

### 2. O CHT responde outra pergunta — a do Lucas
Não é sobre ΔP, é sobre **condensação**: *"a parede fica acima do ponto de orvalho (~250°C)?"*

Estimativa preliminar (h_int≈75 W/m²K pelo swirl forte):
| Cenário | T_parede estimada |
|---|---|
| Sem isolamento | **~356 °C** ✅ |
| Com isolamento | ~390 °C ✅ |

→ **Margem confortável** mesmo sem isolamento. **Mas** o CFD com CHT é que crava os
**pontos frios locais** (ápice do cone, flanges, saída de pó) — que a conta global não vê.

### 3. Por que CHT depois e não agora
| Motivo | |
|---|---|
| **Precisa da espessura de parede** | ainda a calcular (corrosão HCl + erosão do char mineral) |
| **Precisa decidir isolamento** | decisão de projeto ainda aberta |
| **É outro entregável** | eficiência de coleta (Lagrangeano) é o principal |
| **Sequência correta** | hidrodinâmica ✅ → partículas → térmica |

---

## 📋 Sequência do estudo
- [x] **1.** Gás steady 100% → **ΔP validado (3,6%)** ✅
- [x] **2.** Gás steady 50% → **2º ponto validado (12,3%)** ✅
- [x] **3.** **Energia/CHT 100%** → **ΔP 1,2% · T_parede 381 °C** ✅
- [x] **4.** **Energia/CHT 50%** → **ΔP −1,0% da previsão · T_parede 367 °C** ✅ *(caso governante do orvalho)*
- [ ] **5.** Lagrangeano 100% e 50% → **curva de eficiência η × d** ⭐ *(entregável principal)* ← **AGORA**
- [ ] **6.** Transiente (URANS + Curvature Correction) → PVC e seu efeito nos finos
- [ ] **7.** RSM → confirmar/refinar o campo de swirl
- [ ] **8.** Espessura de parede (corrosão HCl + erosão) + decisão de isolamento
- [ ] **9.** Erosão → mapa de desgaste (char com 21% de minerais)

---

## RODADA 4 — 50 % da vazão **COM ENERGIA** ✅ **PREVISÕES CONFIRMADAS**

Convergida: ΔP plano desde ~it. 2.500 (leitura em 4.248) · T_parede plana desde ~it. 1.000 (leitura em 4.337).

| | **previsto (registrado antes)** | **OBTIDO** | |
|---|---|---|---|
| **ΔP** | 655–670 Pa | **652,58 Pa = 6,53 mbar** | ✅ **−1,0 % do centro da faixa** |
| **T_parede** | 355–370 °C | **640,238 K = 367,1 °C** | ✅ **dentro da faixa** |

### O que isso fecha
| | valor |
|---|---|
| ξ extraído (v_i = 7,62) | **5,70** *(100 % com energia: 6,32 — razão 0,90)* |
| Efeito da energia no ΔP | **+1,5 %** *(a 100 % foi +2,5 % — cai com o Re, coerente)* |
| Erro × analítico (733,2 Pa) | **−11,0 %** *(era −12,3 % sem energia)* |
| Limite do cliente (40 mbar) | **folga de 84 %** ✅ |
| **Queda da T_parede vs 100 %** | **−13,9 °C** (381,0 → 367,1) |
| **MARGEM sobre o orvalho (250 °C)** | **+117 °C** ✅ |

> 🏁 **A pergunta do Lucas está ENCERRADA nos dois extremos do turndown.**
> Parede a **381 °C @ 100 %** e **367 °C @ 50 %** → **não condensa em nenhuma condição de operação**,
> **mesmo sem isolamento**. O isolamento passa a ser decisão de **eficiência energética**, não de
> integridade do equipamento. Este é um resultado entregável ao cliente.

> 📉 **A queda foi menor que o teto que eu estimei (−13,9 °C contra os −15 a −25 previstos)** —
> ou seja, o sistema é **menos sensível ao turndown** do que a estimativa conservadora sugeria.
> Mecanismo: a residência dobra, mas h_int cai (∝Re^0,8), e os dois efeitos **se cancelam em parte**.

### ⚠️ Ponto a confirmar
O relato veio como *"7,42 m/s"*, mas a especificação é **7,62 m/s**. Evidência de que a caixa tinha
**7,62**: a razão ξ_50/ξ_100 dá **0,901**, praticamente idêntica aos **0,909** medidos entre as
rodadas 1 e 2 (constant density). Com 7,42 a razão daria 0,951 — uma queda de ξ **mais fraca** com um
Reynolds **menor**, o que contraria a tendência já estabelecida. **Conferir o campo antes de publicar
o número.** (Se for 7,42 mesmo, é 48,7 % da nominal e o ΔP a 50 % real sobe ~5 %, para ~687 Pa —
nada muda qualitativamente.)

### 📊 Resumo consolidado — as 4 rodadas
| # | Carga | Modelo | v_i | **ΔP CFD** | analítico | erro | ξ | T_parede |
|---|---|---|---|---|---|---|---|---|
| 1 | 100 % | ρ const | 15,23 | 2.823,9 Pa | 2.928,9 | 3,6 % | 6,17 | — |
| 2 | 50 % | ρ const | 7,62 | 642,8 Pa | 733,2 | 12,3 % | 5,61 | — |
| 3 | 100 % | **+ energia** | 15,23 | **2.893,98 Pa** | 2.928,9 | **1,2 %** | 6,32 | **381,0 °C** |
| 4 | 50 % | **+ energia** | 7,62 | **652,58 Pa** | 733,2 | **11,0 %** | 5,70 | **367,1 °C** |

> **ETAPA A ENCERRADA.** Quatro pontos, duas cargas, com e sem energia, todos coerentes entre si e
> com o analítico. A base hidrodinâmica e térmica está validada — **pronta para as partículas**.

---

## RODADA 5 — 100 % **com a BC do fundo VERIFICADA** ✅ (a Etapa A está de pé)

Rodada após corrigir `outlet_dust → Type = Wall` (estava como `Outlet` — ver
`06_GUIA...md` Parte 17). Convergida: platô desde ~it. 4.000, leitura em **9.751**.

| | valor |
|---|---|
| **ΔP** | **2.787,38 Pa = 27,87 mbar** |
| **ξ extraído** | **6,09** (tabelado Stairmand HE: 6,40) |
| vs analítico (2.928,9 Pa) | **−4,8 %** ✅ |
| vs rodada 3 (2.893,98 Pa) | **−3,7 %** |
| Folga vs limite do cliente (40 mbar) | **30 %** ✅ |

### ✅ Isso PROVA que a Etapa A não foi contaminada
Se a rodada 3 tivesse sido feita com `outlet_dust = Outlet`, o ΔP não mudaria 3,7 % — **mudaria de
figura**. O ápice fica na zona de pressão negativa do vórtice, e um outlet a 0 Pa ali injetaria
**37 a 52 % de vazão parasita** (168 a 238 m³/h contra os 461 nominais). Uma perturbação dessa
ordem move o ΔP em dezenas de por cento, não em 3,7.

> **Conclusão:** a rodada 3 (ΔP 2.893,98 · T_parede 381 °C) foi feita com `Wall`. O `Outlet` entrou
> depois, durante a montagem do Lagrangeano, e só contaminou a rodada de partículas.
> **Etapa A validada permanece válida.**

### 📊 O ganho inesperado: agora temos a INCERTEZA NUMÉRICA medida
Três rodadas convergidas do **mesmo caso a 100 %** deram:

| Rodada | ΔP | ξ |
|---|---|---|
| 1 · ρ constante | 2.823,9 Pa | 6,17 |
| 3 · energia | 2.893,98 Pa | 6,32 |
| **5 · energia, BC verificada** | **2.787,38 Pa** | **6,09** |

**Espalhamento pico a pico: 3,8 %.** Isso normalmente é difícil de obter — é a
**reprodutibilidade numérica do setup** (escoamento com swirl forte em RANS steady tem múltiplos
estados quase-estacionários; reconvergir de um campo perturbado assenta num atrator ligeiramente
diferente).

> **Como usar isso no relatório:** declarar **ΔP = 28,0 ± 1,1 mbar (±4 %)** em vez de um número seco.
> Todos os três valores ficam dentro de **5 % do analítico** e **30 % abaixo do limite do cliente**.
> Incerteza declarada é mais forte que precisão aparente.

### Número de referência
Adotar a **rodada 5 (2.787,38 Pa)** como valor de projeto: é a única com **todas as BCs
verificadas uma a uma** após o diagnóstico.

⏳ **Pendente:** confirmar a **T_parede** desta rodada (esperado ~381 °C, como na rodada 3 —
a térmica não depende da BC do fundo enquanto ela é parede adiabática/convectiva).

---

## RODADA 7 — **Dc = 307 mm** · k-ω steady + `Outlet` ✅ **CONVERGIU PERFEITAMENTE**

Geometria nova (`ciclone_stairmand_Dc307_fluido.step`, 73,30 L) · v_i = **13,59 m/s** ·
`Outlet_gas` = **`Outlet` (flow-split)** · `outlet_dust` = `Wall`.

| | valor |
|---|---|
| **ΔP** | **2.487,3 Pa = 24,87 mbar** |
| **Desvio-padrão** | **0,0 Pa ao longo de 20.000 iterações** |
| **v_max** | **30,29 m/s** (sd 0,00) → **v_max/v_i = 2,23** ✅ |
| **ξ** | **6,83** (tabelado 6,40) |
| vs analítico (2.333 Pa) | **+6,6 %** |
| **Folga vs 40 mbar** | **38 %** ✅ |

Convergência em ~8.000 iterações e **desvio-padrão exatamente zero** depois disso.

### 🔍 Achado: a BC `Outlet` também estabilizou o STEADY
As rodadas steady no Dc=290 usavam `Pressure Outlet` — e a R6 **não convergiu** (razão 0,985).
Esta, com `Outlet`, converge a **sd = 0,0**.
> **Refina o nosso diagnóstico anterior:** atribuímos a não-convergência do steady só ao PVC.
> Com o flow-split, o k-ω steady fecha perfeitamente. **A BC era um contribuinte importante** —
> o `Pressure Outlet` com fluxo reverso desestabilizava o solver.
> *(A parte do PVC continua válida: o k-ω amortece a instabilidade, e é por isso que ele consegue
> um ponto fixo enquanto o RST não consegue.)*

### ⚠️ E é justamente por isso que este número é um PISO
sd = 0,0 significa **nenhuma oscilação** → o PVC foi suprimido → **ΔP subestimado**, como já medimos
no Dc=290 (k-ω 31,3 mbar × RST 37,0 mbar).

### 📊 A comparação que decide o diâmetro
| Cenário de modelo | **Dc = 290** | **Dc = 307** |
|---|---|---|
| k-ω (piso) | 31,3 mbar (folga 22 %) | **24,9 mbar (38 %)** |
| RST steady | 37,0 mbar (folga **7 %**) | **29,5 mbar (26 %)** |
| RST assíntota pessimista | **43,5 mbar (folga −9 %)** 🔴 | **34,7 mbar (13 %)** ✅ |

> **Dc = 307 atende em TODOS os cenários de modelo. Dc = 290 estoura no pessimista.**
> Custo: **≤ 4 pontos percentuais** de eficiência em 10 µm, e **≤ 2 pp** acima de 20 µm.

---

## ▶️ (histórico) RODADA 4 — previsões registradas ANTES de rodar

**Por que ela é necessária e não é redundante:** a 50 % o tempo de residência **DOBRA**
(0,48 → 0,96 s) e o coeficiente de troca interno **CAI** (h ∝ Re^0,8 → ×0,57). O gás fica mais
tempo trocando calor e troca com um filme mais fraco → **a parede esfria**.
**O caso de 50 % é o caso GOVERNANTE para a pergunta do orvalho**, não o de 100 %.

Setup: **só mudar `Inlet → Velocity Magnitude` de 15,23 para 7,62 m/s** e a intensidade
turbulenta (0,041 → 0,045). Tudo o mais permanece. Reiniciar do campo convergido a 100 %.

### Previsões (registradas ANTES de rodar — falseáveis)
| | previsto |
|---|---|
| **ΔP** | **655–670 Pa** (642,8 do constant-density × 1,025 da energia = **659 Pa**) |
| **T_parede** | **355–370 °C** (queda de ~15–25 °C vs os 381 °C a 100 %) |
| Queda de T do gás ao longo do ciclone | ~6 °C (era ~5 °C a 100 %) |

> ✅ Se a T_parede cair para essa faixa → **margem sobre o orvalho continua > 100 °C** e a
> resposta ao Lucas fica fechada **nos dois extremos de operação**: *não condensa em nenhum ponto
> do turndown*. Aí sim o isolamento vira decisão de eficiência energética, não de integridade.
>
> ⚠️ Se cair **abaixo de 300 °C**, o quadro muda: o isolamento deixa de ser opcional e passa a ser
> requisito de projeto. Vale a pena saber disso **antes** de gastar o Lagrangeano.


---

# RODADA 8 — Dc = 307 · k-ω steady + `Outlet` + parede CONVECTIVA · 100 % e 50 %

> `ciclone_307_100` · `Outlet_Gas` = **`Outlet`** (flow-split) · `outlet_dust` = `Wall`
> Parede: **Convection**, h_e = **10 W/m²·K**, T_amb = **298,15 K**
> ⚠️ **Substitui a Rodada 7**, que foi rodada a **15 m/s** e não a 13,59 (ver §correção abaixo).

## 1. Resultados

| | **100 %** | **50 %** |
|---|---|---|
| v_i | 13,59 m/s | 6,80 m/s |
| **ΔP** | **1.955,6 Pa** (19,56 mbar) | **469,9 Pa** (4,70 mbar) |
| **ξ** | **5,37** | **5,15** |
| **v_max** | 26,573 m/s | 12,348 m/s |
| **v_max/v_i** | **1,96** ✅ | **1,82** ✅ |
| **T_parede** | **378,5 °C** ✅ | ⚠️ **399,6 °C — inválido**, ver §3 |

Previsões registradas ANTES de rodar: ΔP 100 % em 1.960–1.990 (medido **1.955,6**) ·
ΔP 50 % em 440–490 (medido **469,9**, centro da faixa) · T_parede 100 % ~381 °C
(medido **378,5**). **As três confirmadas.**

`v_max/v_i` de 1,96 e 1,82 estão dentro da faixa física de 1,5–2,5 — o k-ω não está inflando
nem suprimindo o vórtice.

## 2. ⚠️ CORREÇÃO DE REGISTRO — a Rodada 7

A R7 está registrada como **2.487,3 Pa a 13,59 m/s · ξ = 6,83**. Está errado nos dois campos:
ela foi rodada a **15 m/s**, e o ξ saiu de dividir aquele ΔP pelo v² de 13,59.

```
ξ real da R7 = 2487,3 / (½·3,946·15²)    = 5,60
ξ da R8      = 1955,6 / (½·3,946·13,59²) = 5,37     ← 4 % de diferença: as duas concordam
```

⇒ **A R8 é o ponto de projeto. A R7 fica como histórico (110,4 % da vazão nominal).**

### Consequência: a margem é bem maior que a registrada
| cenário | ΔP | folga vs 40 mbar |
|---|---|---|
| k-ω (medido) | **19,56 mbar** | **51 %** |
| RST steady (×1,182) | 23,1 mbar | 42 % |
| RST pessimista (×1,390) | 27,2 mbar | **32 %** |

*(Estava registrado 13 % no cenário pessimista, calculado sobre o ΔP de 110 % de vazão.)*

## 3. ⚠️ A T_parede de 50 % é inválida — BC não aplicada

**399,6 °C a 50 % contra 378,5 °C a 100 %.** A parede está mais quente na vazão MENOR, o que é
fisicamente impossível: a 50 % o tempo de residência dobra e h_i cai (∝ Re^0,8, fator 0,574) —
o gás troca calor por mais tempo através de um filme mais fraco, **e a parede esfria**.
No Dc = 290 medimos exatamente isso: 381 → 367 °C.

E o valor denuncia a causa: **399,6 °C ≈ os 400 °C de entrada** (0,4 K de diferença).
⇒ **parede adiabática**, devolvendo a temperatura do gás. A BC convectiva não foi aplicada
naquele arquivo.

> **Terceira ocorrência do mesmo padrão nesta campanha** (antes: `P_porta_ar` devolvendo os
> 98.067 Pa do ejetor; `T_parede` devolvendo os 400 °C na primeira tentativa deste caso).
> ⇒ **Rotina:** antes de acreditar num report, perguntar *"este valor é calculado ou prescrito
> neste lugar?"*

**ΔP e v_max de 50 % continuam válidos** — a sensibilidade térmica da pressão é de ~0,3 %
(o 100 % foi de 1.961,4 adiabático para 1.955,6 convectivo).

## 4. Modelo de duas resistências — calibrado e previsão

```
T_parede = (h_i·T_gás + h_e·T_amb)/(h_i + h_e)
h_i(100 %) = 10·(651,671 − 298,15)/(673,15 − 651,671) = 164,6 W/m²·K
h_i( 50 %) = 164,6 × 0,574 = 94,5 W/m²·K
```

**Previsão para a T_parede a 50 %, ao corrigir a BC: 364 °C.**

Se confirmar, o modelo está calibrado em duas geometrias e a projeção para parede nua vira
número confiável:

| | h_e = 10 (atual) | **h_e = 31,6 (nua: rad. 22,3 + conv. nat. 9,3)** |
|---|---|---|
| 100 % | 378,5 °C | 340 °C |
| **50 %** | 364 °C *(prev.)* | **306 °C** |

⚠️ **O critério contra o qual comparar está em revisão.** O orvalho de 230–250 °C veio de uma
composição C7–C15, e o cliente informou que a corrente real vai de C1 a C40 — a cromatografia
que usamos era de uma amostra de **óleo**, já sem a fração pesada. Ver
`dados_cliente/dados_recebidos_15jul.md` §5.
