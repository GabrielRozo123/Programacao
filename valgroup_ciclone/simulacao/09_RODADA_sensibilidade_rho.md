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

## 1. ⚠️ A decisão que define tudo — como impor o ±5 %

Abra `Continua → Physics → [gás] → Material Properties → Density` e veja o que está lá.

### Caso A — `Constant`
Edite o número direto. **É o caminho limpo.**

| cenário | valor |
|---|---|
| −5 % | **3,7487** kg/m³ |
| base | 3,946 kg/m³ |
| +5 % | **4,1433** kg/m³ |

### Caso B — `Ideal Gas`
**Não mexa na temperatura.** Mexa na **massa molar**:
`Material Properties → Molecular Weight` × 0,95 e × 1,05.

Motivo: `ρ = PM/(RT)`. Alterando `M`, só ρ muda. Alterando `T`, µ vai junto
(~T^0,7), o Reynolds muda, e a rodada deixa de isolar a variável — passa a
responder à pergunta térmica, não à do Marcus.

> Não altere `µ` em nenhum dos dois casos. Ela fica em **9,5e-5 Pa·s** nos três.

---

## 2. ⚠️ A armadilha da entrada — vazão MÁSSICA, não velocidade

O processo entrega **1 820 kg/h**. Se você trocar ρ e **deixar** `Velocity Magnitude`
em 13,59 m/s, você não variou a densidade a vazão fixa — variou a **vazão mássica**
em ∓5 %, que é outro estudo (e nele a eficiência não muda nada).

**Duas saídas, escolha uma:**

**(a) Trocar o tipo da `Inlet` para `Mass Flow Rate`** — melhor, porque o STAR
recalcula a velocidade sozinho e o erro fica impossível:

| | valor |
|---|---|
| 100 % | **0,505556** kg/s |
| 50 % | **0,252778** kg/s |

**(b) Manter `Velocity Inlet` e digitar a velocidade certa** em cada caso:

| cenário | ρ | **v_i 100 %** | **v_i 50 %** |
|---|---|---|---|
| −5 % | 3,7487 | **14,309** m/s | **7,155** m/s |
| base | 3,9460 | 13,594 m/s | 6,797 m/s |
| +5 % | 4,1433 | **12,946** m/s | **6,473** m/s |

### O que NÃO muda na entrada
| campo | valor | por quê |
|---|---|---|
| `Turbulence Intensity` | **0,0417** (100 %) · **0,0455** (50 %) | `I = 0,16·Re^(−1/8)` e **Re não muda** |
| `Turbulent Length Scale` | inalterado | é geométrico |
| `Turbulent Viscosity Ratio` | inalterado | idem |

---

## 3. Escoamento — o que rodar e o que conferir

Rode **steady até convergir**, exatamente como a Rodada 8. Energia pode ficar
ligada: com densidade constante ela é **acoplada em um sentido só** (a temperatura
não realimenta o momento), então não altera nada na eficiência. **Deixe como está** —
a regra da campanha é mudar uma variável por vez.

### O critério de aceite do campo — registre ANTES

| | ΔP previsto | tolerância |
|---|---|---|
| −5 % · 100 % | **2 058,5 Pa** | ±3 % |
| +5 % · 100 % | **1 862,5 Pa** | ±3 % |
| −5 % · 50 % | **492,6 Pa** | ±3 % |
| +5 % · 50 % | **445,7 Pa** | ±3 % |

Se o ΔP medido cair dentro disso, a lei `ΔP ∝ 1/ρ` está confirmada e o
`ξ` é o mesmo nos três — que é a evidência direta de que o campo adimensional
não mudou. **Esse é o primeiro resultado da rodada, antes de qualquer partícula.**

---

## 4. Lagrangeano — sim, uma classe só, e é a de 10 µm

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

## 5. ⚠️ "Um passo só" — quase

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

## 6. Ordem de execução

1. **Um caso só primeiro:** −5 % a 100 %. Confira o ΔP contra os 2 058,5 Pa.
   Se não bater em ±3 %, **pare** — o setup está errado, não a física.
2. Lagrangeano 10 µm, 5 iterações. Compare com os 80,3 % previstos.
3. Se fechou, os outros três casos em sequência.
4. Me passe as 4 medições de ΔP e as 4 de η que eu fecho a tabela e o slide.

---

## 7. O que a rodada NÃO vai mostrar — e por que está tudo bem

A eficiência **global** (a que o Marcus vai ver) não muda visivelmente, porque
90,86 % da massa está acima de 61 µm, em η = 100 % nos três cenários. A variação
máxima é **0,3 ponto**, e ela vive inteira nos 9,14 % de fundo de peneira.

Isso não torna a rodada inútil — ao contrário. Ela produz o argumento de que
**±5 % em ρ não é variável crítica**, medido e não apenas deduzido. E o
contraste com os **7 pontos** de incerteza da granulometria dos finos é o
melhor gancho que temos para o pedido de difração a laser.
