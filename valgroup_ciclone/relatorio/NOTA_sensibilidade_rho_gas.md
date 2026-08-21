# Nota técnica — Variação de ±5 % na massa específica do gás

> Pedido do cliente (Marcus): impacto na **eficiência** de coleta, nas duas cargas
> do turndown. Gerado por `dimensionamento/sensibilidade_rho_gas.py`.
> **Não exige nova rodada de CFD** — ver §2.

---

## 1. O que está fixo decide o resultado

O processo entrega **1 820 kg/h de gás**. A vazão mássica é a âncora, não a
volumétrica. Disso decorre tudo:

| grandeza | relação | efeito de ρ |
|---|---|---|
| velocidade de entrada | `v_i = ṁ/(ρ·A)` | **∝ 1/ρ** |
| Reynolds | `Re = ṁ·D/(A·µ)` | **independente de ρ** |
| perda de carga | `ΔP = ξ·½ρv_i²` | **∝ 1/ρ** |
| número de Stokes | `St = ρ_p d² v_i/(18µD_c)` | **∝ 1/ρ** |

**A consequência que sustenta o método:** como `Re` não muda, o campo
*adimensional* é idêntico nos três cenários — mesmo vórtice, mesmo número
efetivo de voltas. Só a **escala** de velocidade muda.

---

## 2. Por que não é preciso rodar de novo

Se a forma do escoamento não muda e só a escala muda, a curva η×d não muda de
forma: ela **desliza em d**, pela equivalência de Stokes.

```
η_novo(d) = η_ref( d / √(ρ_novo/ρ_ref) )        d* = d*_ref · √(ρ_novo/ρ_ref)
```

Gás **mais denso** → `v_i` menor → `St` menor → **corte mais grosso, η menor**.

A curva medida (20 classes, CFD Lagrangeano) é reaproveitada com esse mapa e
convoluída com a PSD da Valgroup. Uma rodada nova reproduziria exatamente isto.

---

## 3. Escoamento

| cenário | ρ (kg/m³) | v_i 100 % | v_i 50 % | ΔP 100 % | ΔP 50 % | Re |
|---|---|---|---|---|---|---|
| −5 % | 3,749 | 14,31 m/s | 7,15 m/s | **20,59 mbar** | 4,93 mbar | 173 343 |
| base | 3,946 | 13,59 m/s | 6,80 m/s | 19,56 mbar | 4,68 mbar | 173 343 |
| +5 % | 4,143 | 12,95 m/s | 6,47 m/s | 18,62 mbar | 4,46 mbar | 173 343 |

O pior caso de **perda de carga** é o gás **mais leve** (20,59 mbar, ainda com
49 % de folga contra o limite de 40 mbar). O pior caso de **eficiência** é o gás
mais denso. Os dois extremos são opostos — não há cenário que piore os dois.

---

## 4. Diâmetro de corte

| cenário | d\* a 100 % | d\* a 50 % | variação |
|---|---|---|---|
| −5 % | 6,67 µm | 9,65 µm | −2,5 % |
| base | **6,84 µm** | **9,90 µm** | — |
| +5 % | 7,01 µm | 10,14 µm | +2,5 % |

±5 % em ρ move o corte apenas **±2,5 %** — a raiz quadrada amortece pela metade.

---

## 5. Eficiência global — a resposta

A PSD peneirada tem 90,86 % da massa **acima de 61 µm**, região onde η = 100 %
nos três cenários. Só os **9,14 % de fundo de peneira** (< 61 µm, sem
distribuição interna medida) podem responder a ρ. Varrendo onde esse fundo
possa estar:

**100 % de vazão**

| fundo em | η −5 % | η base | η +5 % | amplitude |
|---|---|---|---|---|
| 61 µm | 100,00 % | 100,00 % | 100,00 % | 0,00 pt |
| 20 µm | 100,00 % | 100,00 % | 99,98 % | 0,02 pt |
| 15 µm | 99,81 % | 99,79 % | 99,69 % | 0,12 pt |
| 10 µm | 98,20 % | 98,09 % | 97,92 % | 0,28 pt |
| **7 µm** | 95,74 % | 95,55 % | 95,42 % | **0,32 pt** ← máximo |
| 5 µm | 93,86 % | 93,72 % | 93,70 % | 0,16 pt |
| 1 µm | 92,93 % | 92,93 % | 92,93 % | 0,00 pt |

**50 % de vazão**

| fundo em | η −5 % | η base | η +5 % | amplitude |
|---|---|---|---|---|
| 61 µm | 100,00 % | 100,00 % | 100,00 % | 0,00 pt |
| 20 µm | 99,55 % | 99,54 % | 99,43 % | 0,12 pt |
| 15 µm | 98,39 % | 98,28 % | 98,11 % | 0,28 pt |
| **10 µm** | 95,65 % | 95,47 % | 95,37 % | **0,29 pt** ← máximo |
| 7 µm | 94,00 % | 93,88 % | 93,84 % | 0,16 pt |
| 5 µm | 93,30 % | 93,25 % | 93,25 % | 0,05 pt |
| 1 µm | 93,18 % | 93,19 % | 93,19 % | 0,00 pt |

### Conclusão

> **A eficiência global varia no máximo 0,3 ponto percentual** em toda a faixa
> de ±5 % de ρ, nas duas cargas. Em termos de emissão, isso é **0,2 kg/h** de
> char sobre um particulado de 80 kg/h.
>
> Para comparação, a incerteza da **distribuição do fundo de peneira** vale
> **7 pontos** (92,9 % a 100,0 %) — vinte vezes mais. A massa específica do gás
> **não é uma variável crítica** deste projeto; a granulometria dos finos é.

A amplitude cai a zero nos dois extremos porque lá a curva é plana: acima de
20 µm já está saturada em 100 %, e abaixo de 3 µm está no patamar de ~22 % da
deposição turbulenta. A sensibilidade só existe no **joelho** da curva, entre 5
e 15 µm.

---

## 6. Duas ressalvas para o cliente

**a) A especificação da rerrodada, se houver.** Se alguém verificar isto
variando a vazão **volumétrica** em vez da mássica, o resultado responde a outra
pergunta: `v_i` fica constante, `St` fica constante e a eficiência **não muda
nada**; em compensação `ΔP ∝ ρ` e o pior caso de perda de carga inverte para
+5 %. Qualquer verificação precisa ser especificada em **kg/h**.

**b) A origem física da variação.**

- Se ρ varia por **composição** (massa molar), µ praticamente não muda e vale o
  que está acima: `d* ∝ √ρ`, ±2,5 %.
- Se ρ varia por **temperatura** (ρ ∝ 1/T a pressão fixa), µ sobe com T (~T^0,7)
  e os dois efeitos se **opõem**: `d* ∝ √(ρ·µ)`. Para −5 % em ρ via
  temperatura, T sobe 5,3 %, µ sobe ~3,7 %, e o corte se move apenas
  **−0,8 %** em vez de −2,5 %. A variação térmica é ainda menos sensível.

Em nenhuma das duas leituras a conclusão de §5 muda.
