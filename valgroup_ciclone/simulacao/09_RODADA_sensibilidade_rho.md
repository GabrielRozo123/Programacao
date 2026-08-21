# 09 — RODADA de sensibilidade a ρ do gás (±5 %)

> Folha de execução. Campo base: **Rodada 8** (k-ω steady, `Outlet`, parede convectiva).
> Método de η: **§8 do `07_EXECUCAO`** — `η = 1 − |mdot_gas| / mdot_inj`.
> Previsão analítica em `relatorio/NOTA_sensibilidade_rho_gas.md`.

---

## 0. O que esta rodada testa

**Não é** re-medir a curva η×d. É **validar a lei de escala** que permite reaproveitá-la:

```
Re independe de ρ  →  campo adimensional idêntico  →  η(d) só desliza em d
d* ∝ √ρ            →   ±5 % em ρ  ⇒  ±2,5 % no corte
```

Se a rodada confirmar, a tabela analítica de η global fica validada e não é preciso
rodar mais nada. Se não confirmar, existe um efeito de ρ fora de Stokes — e aí é
achado, não erro.

**Escopo:** 4 campos novos + 4 rastreamentos. A base já está rodada.

| | 100 % | 50 % |
|---|---|---|
| −5 % | rodar | rodar |
| base | ✅ já temos | ✅ já temos |
| +5 % | rodar | rodar |

---

## 1. O caso é GÁS IDEAL — não existe nó `Density`

Confirmado na árvore: `Gas → Gás_Pirólise → Material Properties` tem
`Dynamic Viscosity`, **`Molecular Weight`**, `Specific Heat`,
`Thermal Conductivity` e `Turbulent Prandtl Number`. Sem `Density`, porque ela
vem da equação de estado.

```
ρ = P·M / (R·T)        →    a P e T fixos,   ρ ∝ M
```

**A massa molar é o único lever.** `M = 184 kg/kmol` (verificado).

> **Verificação cruzada do caso base:** invertendo, `P = ρRT/M` =
> 3,946 × 8314,5 × 673,15 / 184 = **120 029 Pa = 1,200 bar**. Bate com a pressão
> de projeto — pressão, temperatura e massa molar estão consistentes entre si.

**Não mexa na temperatura** para variar ρ: µ iria junto (~T^0,7), o Reynolds
mudaria e a rodada deixaria de isolar a variável. Alterando `M`, só ρ muda.

**Não mexa em `Specific Heat` nem `Thermal Conductivity`.** Numa mudança real de
composição elas se moveriam também — mas o pedido é sensibilidade a **ρ**, e
isolar é o correto. Registrar essa fronteira ao apresentar.

---

## 2. ⭐ TABELA ÚNICA DE AJUSTE

Só **uma célula** muda por cenário. Todo o resto é consequência ou permanece.

| | **−5 %** | **base** | **+5 %** |
|---|---|---|---|
| ⬅️ **`Molecular Weight`** (kg/kmol) | **174,8** | 184,0 | **193,2** |
| ρ resultante (kg/m³) | 3,7487 | 3,9460 | 4,1433 |
| ⬅️ **`Inlet → Mass Flow Rate`** · 100 % | **0,505556 kg/s** | **0,505556 kg/s** | **0,505556 kg/s** |
| ⬅️ **`Inlet → Mass Flow Rate`** · 50 % | **0,252778 kg/s** | **0,252778 kg/s** | **0,252778 kg/s** |
| ⬅️ `Turbulence Intensity` 100 % / 50 % | 0,0417 / 0,0455 | 0,0417 / 0,0455 | 0,0417 / 0,0455 |
| ⬅️ `Dynamic Viscosity` (Pa·s) | 9,5e-5 | 9,5e-5 | 9,5e-5 |
| ⬅️ `mdot_inj` 100 % / 50 % (kg/s) | 2,7778e-3 / 1,389e-3 | idem | idem |

As linhas com ⬅️ são o que se digita. **A vazão mássica é idêntica nos três** — é
exatamente esse o ponto do estudo.

### Por que a entrada tem de ser MÁSSICA

Com gás ideal, a densidade **na face de entrada** não é exatamente o valor de
referência: depende da pressão e da temperatura locais ali. Prescrever velocidade
vira chute. Com `Mass Flow Rate` o STAR calcula a velocidade a partir da densidade
local e a armadilha desaparece sozinha.

E a armadilha é séria: trocar ρ **deixando** a velocidade em 13,59 m/s não varia a
densidade a vazão fixa — varia a **vazão mássica** em ∓5 %, que é outro estudo (e
nele a eficiência não muda nada, enquanto o ΔP inverte o sinal).

`Turbulent Length Scale` e `Turbulent Viscosity Ratio` são geométricos —
inalterados. A `Turbulence Intensity` também não muda, porque `I = 0,16·Re^(−1/8)`
e **Re não muda**.

---

## 3. TABELA DE CONFERÊNCIA — o que tem de sair

Monte estes reports **antes** de rodar. O primeiro é o mais importante: é a prova
de que o ∓5 % realmente entrou, e não depende de acreditar na conta da massa molar.

| report | −5 % | base | +5 % |
|---|---|---|---|
| ⭐ `Volume Average` de **Density** | **3,749** | 3,946 | **4,143** |
| `Surface Average` de **Velocity Magnitude** na `Inlet` · 100 % | **14,31 m/s** | 13,59 m/s | **12,95 m/s** |
| idem · 50 % | 7,155 m/s | 6,797 m/s | 6,473 m/s |
| vazão volumétrica implícita · 100 % | 485,5 m³/h | 461,2 m³/h | 439,3 m³/h |
| **ΔP · 100 %** | **2 058 Pa** | 1 956 Pa | **1 862 Pa** |
| **ΔP · 50 %** | **493 Pa** | 468 Pa | **446 Pa** |
| **Reynolds** | **173 343** | **173 343** | **173 343** |

O **Re idêntico** é o que fecha o argumento: mesmo campo adimensional, só a escala
de velocidade mudou. É por isso que a curva η×d pode ser deslizada em vez de
remedida.

**Mach:** 0,070 / 0,068 / 0,067. Incompressível na prática — a troca de `M` não
traz efeito parasita de compressibilidade.

---

## 4. Escoamento — o que rodar

Rode **steady até convergir**, exatamente como a Rodada 8.

**Deixe a energia ligada.** Com gás ideal ela é genuinamente acoplada (a
temperatura entra na densidade), então precisa estar lá — e ela já está no caso
base. A regra da campanha continua: mudar uma variável por vez.

**Tolerância de aceite:** ±3 % nos ΔP da tabela do §3. Se cair dentro, a lei
`ΔP ∝ 1/ρ` está confirmada e o `ξ` é o mesmo nos três — evidência direta de que o
campo adimensional não mudou. **Esse é o primeiro resultado da rodada, antes de
qualquer partícula.**

---

## 5. Lagrangeano — sim, uma classe só, e é a de 10 µm

Não refaça as 8 classes. O efeito de ρ só existe no **joelho** da curva:

| classe | espalhamento −5 % → +5 % a 100 % | a 50 % |
|---|---|---|
| 5 µm | 1,77 pt | 0,57 pt |
| 7 µm | 3,45 pt | 1,75 pt |
| **10 µm** | **3,07 pt** | **3,13 pt** ← única boa nas duas |
| 15 µm | 1,32 pt | 3,07 pt |
| 20 µm | 0,19 pt | 1,31 pt |

**Rode 10 µm.** Se quiser uma segunda para reforçar, 7 µm a 100 % e 15 µm a 50 %.

### Previsões — anote antes de rodar

| | −5 % | base *(medido)* | +5 % |
|---|---|---|---|
| d\* · 100 % | 6,67 µm | 6,84 µm | 7,01 µm |
| d\* · 50 % | 9,65 µm | 9,90 µm | 10,14 µm |
| **η(10 µm) · 100 %** | **80,3 %** | 79,14 % | **77,2 %** |
| **η(10 µm) · 50 %** | **52,4 %** | 50,49 % | **49,3 %** |

**Sinal esperado: gás mais denso → η menor.** (ρ↑ → v_i↓ → St↓ → corte mais grosso.)
Se sair invertido, o problema está no §2 — provavelmente a velocidade ficou fixa.

### O que fica igual no Lagrangeano
| | valor | por quê |
|---|---|---|
| `mdot_inj` | **2,7778e-3** kg/s (100 %) · **1,389e-3** (50 %) | a carga de sólido é 80 kg/h, independe de ρ |
| ρ_p | 1500 kg/m³ | — |
| `Turbulent Dispersion` | **ligada** | a base foi rodada com ela |
| restituição, sub-steps, `Parcel Streams` | idênticos à base | comparação **pareada** |

> ⚠️ **Confira o injetor.** Se a velocidade das parcelas na injeção for **prescrita**
> (e não herdada do gás), ela tem de acompanhar a nova `v_i` de cada caso. Injetor
> com velocidade fixa em 13,59 enquanto o gás anda a 14,31 introduz um transiente de
> arrasto na entrada que não existe.

---

## 6. ⚠️ "Um passo só" — quase

**Sim:** em steady, o solver Lagrangeano rastreia cada parcela da injeção até a
terminação **dentro de uma única iteração**. Quem governa não é o número de
iterações, é o **`Maximum Sub-Steps`** (150 000 para as classes perto do corte).

**Antes de dar o passo:**
1. `Solvers → Segregated Flow`, `K-Omega Turbulence`, `Segregated Energy` → **`Frozen`**
2. Confirme que o `Lagrangian Multiphase` **não** está `Frozen` (armadilha nº1 do §3
   do `07_EXECUCAO`: devolve zero sem erro nenhum)
3. Apague `.trk` antigos da pasta (armadilha nº12)

**Mas não pare em uma iteração.** Com `Turbulent Dispersion` ativa, cada iteração é
uma **realização aleatória nova**. O efeito que estamos caçando vale ~3 pontos, e o
espalhamento entre realizações é da ordem de 0,4 ponto. Um único passo pode
confundir os dois.

> **Rode 5 iterações e anote `eta_010` em cada uma.** Reporte média e faixa.
> Custa 5× quase nada e transforma "77,2 contra 79,1" em resultado defensável em vez
> de coincidência.

Confira também, em cada caso, a **fração de parcelas ainda ativas** no fim
(critério do §9.4: abaixo de 1 %). Ela precisa ser comparável entre os três cenários —
se um deles travar mais que os outros, a diferença de η pode ser artefato de
truncamento e não física.

---

## 7. Ordem de execução

1. **Um caso só primeiro:** −5 % a 100 %. Confira o ΔP contra os 2 058,5 Pa.
   Se não bater em ±3 %, **pare** — o setup está errado, não a física.
2. Lagrangeano 10 µm, 5 iterações. Compare com os 80,3 % previstos.
3. Se fechou, os outros três casos em sequência.
4. Me passe as 4 medições de ΔP e as 4 de η que eu fecho a tabela e o slide.

---

## 8. O que a rodada NÃO vai mostrar — e por que está tudo bem

A eficiência **global** (a que o Marcus vai ver) não muda visivelmente, porque
90,86 % da massa está acima de 61 µm, em η = 100 % nos três cenários. A variação
máxima é **0,3 ponto**, e ela vive inteira nos 9,14 % de fundo de peneira.

Isso não torna a rodada inútil — ao contrário. Ela produz o argumento de que
**±5 % em ρ não é variável crítica**, medido e não apenas deduzido. E o
contraste com os **7 pontos** de incerteza da granulometria dos finos é o
melhor gancho que temos para o pedido de difração a laser.
