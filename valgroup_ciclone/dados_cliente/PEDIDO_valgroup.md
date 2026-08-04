# Pedido de informações à Valgroup — ciclone de char

> Redigido para o Marcus encaminhar. Ordenado por **impacto no dimensionamento**, com a
> justificativa de cada item. Base: planilha "Dimensionamento de Ciclone Lapple" (abas
> *Distribuição de Tamanhos* e *Dimensionamento via DT (LN)*) e áudio de 04/08/2026.

---

## 1. 🔴 Vazão mássica real do gás — **1900 kg/h ou ~720 kg/h?**
A planilha usa **1900 kg/h**. Nossa base de projeto vinha de 800 kg/h de alimentação menos
80 kg/h de particulado → **720 kg/h**.

**Por que importa:** é o item de maior impacto de todos. A vazão define o diâmetro do ciclone.

| cenário | Q (m³/h) | **D_c** |
|---|---|---|
| 720 kg/h | 182,5 | **163 mm** |
| 1900 kg/h | 481,5 | **265 mm** |

⇒ **É o equipamento inteiro que muda.** Precisamos do valor medido, e de onde ele é medido.

---

## 2. 🔴 Massa específica da PARTÍCULA de char (não a do leito)
A planilha usa **776,75 kg/m³**. Esse valor é a densidade **aparente/bulk** — inclui os vazios
entre as partículas.

> A própria planilha sinaliza isso: na tabela *"Valores Usuais na Aplicação de Ciclones"* a faixa
> declarada é **1500 a 3000 kg/m³**, e o valor de projeto usado (776,75) está **abaixo do mínimo**.

**Por que importa:** o diâmetro de corte varia com `d* ∝ 1/√ρ_s`. Passar de 777 para 1500 kg/m³
reduz o corte em **1,39×** — o ciclone separa partículas bem mais finas do que a planilha prevê.
Usar a bulk **subestima a inércia da partícula** e leva a um projeto conservador na direção errada.

**O que pedimos:** picnometria a gás (hélio) da amostra de char. Ela dá a densidade **esquelética**
(limite superior). O valor de projeto fica entre a esquelética e a bulk — informe as duas, se tiver.

---

## 3. 🟡 Viscosidade do gás — fonte do valor 1,0×10⁻⁴ Pa·s
A planilha usa **1,0e-4 Pa·s**. Para vapor de hidrocarbonetos C7–C15 a 340–400 °C, o valor típico
é **1,5–3,0e-5 Pa·s** — cerca de **4× menor**.

**Por que importa:** `d* ∝ √µ`. Um fator 4 em µ é um fator **2** no diâmetro de corte.

**O que pedimos:** a origem do valor (medido? tabela? qual fluido de referência?). Se for
estimativa, calculamos pela composição do GC-MS (Wilke/Chung) e reconciliamos.

---

## 4. 🟡 Temperatura no ponto exato do ciclone
A planilha usa **400 °C**. O SCADA (TT-209, Caixa de Dragagem) mostra média de **~343 °C**,
oscilando entre 330 e 378 °C.

**Por que importa:** define ρ e µ do gás, e a margem ao ponto de orvalho dos pesados
(~230–250 °C), que é o critério para não depositar tar na parede.

**O que pedimos:** confirmar **onde** o ciclone entra na linha — antes ou depois da caixa de
dragagem — e qual sensor representa esse ponto.

---

## 5. 🟠 Distribuição de tamanhos ABAIXO de 61 µm — o fundo de peneira

### O achado
Na aba *Distribuição de Tamanhos*, a última linha é o **fundo de peneira**: o material que passou
pela malha de 61 µm. São **9,14 % da massa**, e a planilha atribui a essa fração o diâmetro
**d# = 61 µm** — a própria abertura da peneira.

Isso significa que tudo entre 61 µm e submicrométrico está sendo tratado como 61 µm.

### Quanto vale
Eficiência global do ciclone conforme o fundo esteja realmente em:

| d real do fundo | 61 µm | 20 µm | 10 µm | 5 µm | 3 µm |
|---|---|---|---|---|---|
| **η_global** | **99,3 %** | 98,3 % | 96,1 % | 93,0 % | **91,5 %** |

**7,8 pontos percentuais de amplitude, vindos de uma única faixa não medida.**

### Por que ajustar melhor a distribuição não resolve
Testamos os três modelos da planilha contra o próprio dado bruto, na fração que passa em 75 µm:

| | fração < 75 µm |
|---|---|
| **dado bruto (peneira)** | **9,1 %** |
| modelo RRB (n=0,613 · D63,2=68,4 µm) | 65,3 % |
| modelo LN (D50=239 µm · σ=4,48) — o escolhido | 22,0 % |

Os três divergem entre si por um fator de **7** exatamente na faixa fina. Não é falha do ajuste:
os três foram ajustados aos **mesmos seis pontos**, e **nenhum deles tem um ponto abaixo de
61 µm**. Seleção por R² não distingue modelos numa região onde não há dado.

### O que pedimos — e é barato
**Difração a laser (ou Coulter/sedimentação) na fração que passou a peneira de 61 µm**, da
amostra que vocês **já têm**. Não é preciso coletar material novo nem enfrentar a contaminação
por parafina do material carreado.

Se o fundo de peneira não tiver sido guardado, a análise na amostra integral também serve.

> **Ressalva que declaramos:** a amostra é do char **coletado**, cuja cauda fina já está
> empobrecida (os finos são justamente os que escapam). O resultado dará então um **piso** para a
> fração de finos da alimentação e um **limite superior** rigoroso para a eficiência — que é
> muito mais do que temos hoje, mas não é a PSD da alimentação.

---

## 6. 🟠 Qual separador existe hoje na linha?
Ciclone? Cabeçote? Nada, só a tubulação?

**Por que importa:** conhecendo a curva de eficiência η(d) do separador atual, a PSD da
alimentação é reconstruível a partir da PSD do coletado por
```
f(d) = c(d) / η(d)
```
— retrocálculo clássico de classificação. É a única rota que dá a alimentação real **sem** ter de
amostrar o carreado contaminado.

**O que pedimos:** geometria e condições operacionais do que existe hoje (ou confirmação de que
não há separador).

---

## Resumo — o que é crítico

| # | Item | Bloqueia |
|---|---|---|
| 1 | Vazão mássica de gás | o **diâmetro** do ciclone |
| 2 | ρ da partícula (não bulk) | o **diâmetro de corte** |
| 3 | Viscosidade do gás | o **diâmetro de corte** |
| 4 | T no ponto do ciclone | ρ, µ e a margem ao orvalho |
| 5 | PSD abaixo de 61 µm | a **eficiência garantida** |
| 6 | Separador atual | reconstrução da alimentação |

**Os itens 1 a 3 mudam o equipamento. O item 5 muda o número que podemos garantir.**
