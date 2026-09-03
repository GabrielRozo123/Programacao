# Análise do Memorial de Propriedades do Gás — Daniel Vozza (Valgroup), Rev01

> **Documento recebido:** *"Memorial de Cálculo — Propriedades do Gás de Pirólise na
> Entrada do Ciclone"*, Daniel B. S. Vozza (Eng. Químico, r-PET/Valgroup), 03/09/2026.
> Status declarado: **preliminar**, composição real por GC do NCG pendente.
>
> **Pedido do Marcus (11:58):** *"conversei com o Daniel e falamos sobre a necessidade
> de uma análise de sensibilidade da viscosidade e da massa específica. Ele mandou 2
> ranges em um doc. Peço para vc revisar e me retornar com as suas considerações, mas
> acho pertinente rodarmos as 9 simulações pedidas"*.

---

## 1. O que o memorial traz

**Método:** ρ por gás ideal; µ por estados correspondentes (Lucas, Poling 5ª ed.) com
regra de Wilke para a mistura; validado contra NIST (erro < 3 % em CH₄, CO₂, N₂).
Condições: T = 350–400 °C, P ≈ 1,2 bar abs, carga poliolefínica (PE/PP), 100 % vapor.

| cenário | MM (g/mol) | ρ (kg/m³) | µ (×10⁻⁵ Pa·s) |
|---|---|---|---|
| **A** — rico em óleo vapor | 120 | 2,6 – 2,8 | 1,11 – 1,20 |
| **B** — intermediário | 77 | 1,66 – 1,79 | 1,33 – 1,43 |
| **C** — gás-dominante | 52 | 1,10 – 1,19 | 1,56 – 1,67 |

Faixas propostas para o grid: ρ = 1,1 / 1,8 / 2,8 · µ = 1,1 / 1,4 / 1,7 (×10⁻⁵).

**Aritmética conferida:** `ρ = PM/RT` reproduz as três linhas dentro do arredondamento.
Ex.: cenário A a 673,15 K → 120 000 × 120/(8 314 × 673,15) = 2,573; a 623,15 K → 2,780. ✅

---

## 2. Onde isso põe o que já rodamos

| | rodado | faixa do Daniel | posição |
|---|---|---|---|
| ρ | **3,946 kg/m³** | 1,1 – 2,8 | **41 % acima do teto** |
| µ | **9,5e-5 Pa·s** | 1,1e-5 – 1,7e-5 | **5,6× acima do teto** |

As duas estão fora, e é importante notar **em que direção cada uma empurra**:

- no **diâmetro de corte**, `d* ∝ √(ρ·µ)` — as duas empurram no mesmo sentido, e o
  nosso par (3,946 · 9,5e-5) dá um `ρµ` **12 vezes maior** que o cenário A. Nosso d*
  é ~3,5× o real: as entregas são **pessimistas por larga margem**.
- na **queda de pressão**, a vazão mássica é fixa, então `ΔP ∝ 1/ρ` e a µ não entra.
  Rodar com ρ alto foi **otimista**. É aí que mora o problema.

---

## 3. A viscosidade está encerrada — e a favor da nossa posição

O memorial fecha a divergência levantada em `NOTA_viscosidade_gas.md`:

| fonte | µ (Pa·s) |
|---|---|
| planilha Lapple dos colegas (rodado) | 9,5e-5 |
| nossa recomendação | 2,5e-5 |
| Chapman-Enskog nosso (M = 184, 673 K) | ~1,3e-5 |
| **Daniel — Lucas + Wilke** | **1,1e-5 – 1,7e-5** |

Três estimativas independentes (a nossa por faixa típica, a nossa por Chapman-Enskog,
a dele por Lucas/Wilke) caem na mesma década. O 9,5e-5 é o único fora.

E o Daniel chega **abaixo** da nossa recomendação de 2,5e-5, que a gente já tinha
escolhido no topo da faixa para ser conservador. A convergência é mais forte do que
pedimos.

---

## 4. A reconciliação da massa molar — o achado que fecha o círculo

O **M = 184 kg/kmol** que vínhamos usando **nunca foi medido**. Foi retrocalculado do
ρ = 3,946 da planilha da Valgroup (`dados_recebidos_15jul.md` §1):

> *"o ρ = 3,946 do cliente implica MW ≈ 168 (a 340 °C) / 184 (a 400 °C). O GC dá 124."*

Agora:

| fonte de MM | valor | natureza |
|---|---|---|
| retrocálculo do ρ da planilha | 184 | **circular** — não é medida |
| **GC-MS head-space** | **124** | medido; é **piso** (head-space perde pesados) |
| **Daniel, cenário A** | **120** | literatura, reconstrução independente |
| Daniel, cenário B | 77 | literatura |
| Daniel, cenário C | 52 | literatura |

**O GC-MS e a estimativa do Daniel batem entre si (124 vs 120), por caminhos
totalmente independentes.** O 184 é o ponto fora da curva, e é o único que não vem
de medida nem de literatura.

Isso é informação que o Daniel provavelmente não tem — vale passar.

---

## 5. O achado central: a queda de pressão vira o critério de projeto

A vazão mássica é fixa (1 820 kg/h). Então `v_i = ṁ/(ρA)` e:

$$\Delta P = \frac{\xi\,\rho\,v_i^2}{2} = \frac{\xi\,\dot m^2}{2\,\rho\,A^2} = \frac{7\,717}{\rho} \ \text{[Pa]}$$

com ξ = 5,364 medido (invariante em seis condições: 5,360 / 5,364 / 5,369 a 100 %),
ṁ = 0,50556 kg/s, A_in = 9,4249e-3 m². Confere no ponto base: 7 717/3,946 = **1 956 Pa**,
exatamente o medido.

### Impondo o limite de 40 mbar (4 000 Pa)

$$\boxed{\rho_{min} = \frac{7\,717}{4\,000} = 1{,}93\ \text{kg/m³}}$$

O critério em ρ é **independente da temperatura**. Traduzido para massa molar ele
depende de T: `M_min = ρ_min·RT/P` = **90 g/mol a 400 °C**, **83 g/mol a 350 °C**.

| | ρ do grid | MM implicada a 400 °C | v_i a 100 % | **ΔP a 100 %** | vs. 40 mbar |
|---|---|---|---|---|---|
| rodado | 3,946 | 184,0 | 13,6 m/s | 1 956 Pa | ✅ 51 % de folga |
| **A** | 2,8 | 130,6 | 19,2 m/s | **2 756 Pa** | ✅ 31 % de folga |
| **B** | 1,8 | 84,0 | 29,8 m/s | **4 287 Pa** | ❌ **7 % acima** |
| **C** | 1,1 | 51,3 | 48,8 m/s | **7 015 Pa** | ❌ **75 % acima** |

> ⚠️ Os ρ do grid (1,1 / 1,8 / 2,8) são os **extremos das faixas de cada cenário ao
> longo de 350–400 °C**, não os valores a 400 °C. Por isso a MM implicada na coluna
> acima não coincide com os 120 / 77 / 52 nominais do memorial. Testando cada cenário
> nas duas pontas de T:

| cenário | MM | ρ a 400 °C | ρ a 350 °C | passa em ρ ≥ 1,93? |
|---|---|---|---|---|
| A | 120 | 2,573 | 2,780 | ✅ nas duas pontas |
| B | 77 | 1,651 | 1,783 | ❌ nas duas pontas |
| C | 52 | 1,115 | 1,204 | ❌ nas duas pontas |
| **GC-MS** | **124** | **2,659** | **2,872** | ✅ **nas duas pontas** |

A conclusão não depende da temperatura assumida.

**A 50 % de vazão nenhum cenário viola** (ΔP = 1 846/ρ → 660 / 1 026 / 1 679 Pa). O
problema é exclusivo da vazão plena.

### Por que a gente passa

Os dois indícios independentes apontam para o cenário A:

- o GC-MS deu **124 g/mol**, e é **piso** — o head-space (incubação a 70 °C) perde os
  pesados, então o valor real é ≥ 124;
- o próprio Daniel escreve: *"A 350–400 °C a literatura favorece MM alto"* e
  *"o craqueamento é brando: predominam gases C₁–C₄ com fração relevante de vapores de
  óleo pesado (elevando o MM médio)"*.

**Os 90 g/mol viram o critério de aceitação a checar contra o GC do NCG.**

### Duas consequências de engenharia se o gás vier leve

Não são captadas por ΔP nem por d*, e valem menção no relatório:

1. **Velocidade de entrada.** 48,8 m/s no cenário C está muito acima da prática usual
   (15–25 m/s). Acima de ~30 m/s a re-entranhamento degrada a coleta — a previsão de
   d* fica **otimista** ali.
2. **Erosão.** Char é abrasivo e a taxa vai com ~v³. De 13,6 para 48,8 m/s são **46×**.

---

## 6. Sobre as 9 simulações

### O grid 3×3 contém 6 combinações que não existem

É o próprio memorial que diz (p. 2):

> *"ρ e μ variam em sentidos opostos com a composição (mais óleo pesado → ρ↑ e μ↓).
> Pares fisicamente coerentes para 3 corridas: (ρ=2,8; μ=1,1) · (ρ=1,8; μ=1,4) ·
> (ρ=1,1; μ=1,7)."*

Ele sugere o 3×3 apenas para *bracketing* de pior caso. Mas o grid cheio **infla a
incerteza reportada**:

| | `ρ·µ` mín | `ρ·µ` máx | razão em `ρ·µ` | **razão em d\*** |
|---|---|---|---|---|
| 3 pares coerentes | 1,87e-5 | 3,08e-5 | 1,65 | **1,28×** |
| grid 3×3 completo | 1,21e-5 | 4,76e-5 | 3,93 | **1,98×** |

O grid cheio faz o diâmetro de corte parecer variar por um **fator 2**, quando a
física acoplada entrega **1,28**. É superestimar a incerteza em mais de 3× no
intervalo — e o cliente lê isso como falta de confiança no resultado.

Além disso: **o pior caso de ΔP já está nos 3 pares** (é ρ mínimo, e µ não entra em
ΔP). Só o pior caso de d* exige um canto incoerente.

### Matriz recomendada — 6 rodadas, cobrindo mais que as 9

| # | cenário | ρ | µ | vazão |
|---|---|---|---|---|
| 1 | A · 100 % | 2,8 | 1,1e-5 | 1 820 kg/h |
| 2 | B · 100 % | 1,8 | 1,4e-5 | 1 820 kg/h |
| 3 | C · 100 % | 1,1 | 1,7e-5 | 1 820 kg/h |
| 4 | A · 50 % | 2,8 | 1,1e-5 | 910 kg/h |
| 5 | B · 50 % | 1,8 | 1,4e-5 | 910 kg/h |
| 6 | C · 50 % | 1,1 | 1,7e-5 | 910 kg/h |
| **7** | **canto de pior d\*** | **2,8** | **1,7e-5** | 1 820 kg/h |

> ✅ **Matriz aprovada pelo Marcus** (14:07): *"3 a 100 % de vazão, 3 a 50 % de vazão e
> uma considerando maior densidade e maior viscosidade. Por mais que não exista, fecha
> o cenário da eficiência"*.

### ⚠️ Qual rodada fecha qual pior caso

O Marcus descreveu a 7ª como fechando *"eficiência e queda máxima de pressão"*. Ela
fecha só a primeira. **`ΔP ∝ 1/ρ`, então densidade máxima é queda MÍNIMA.**

| pior caso | rodada | valor |
|---|---|---|
| **pior eficiência** (maior `ρ·µ` ⇒ maior d\*) | **7** — ρ = 2,8 · µ = 1,7e-5 | **d\* = 2,44 µm** |
| **pior queda de pressão** (menor ρ) | **3** — ρ = 1,1 · 100 % | **ΔP = 7 015 Pa** |

A ΔP da rodada 7 é 2 756 Pa — a **menor** das três densidades. Corrigir antes de
comunicar ao Daniel.

### Ressalva do Marcus, procedente

A afirmação analítica de que "a eficiência melhora em todos os cenários" vale enquanto
não houver re-entranhamento. No cenário C a entrada vai a **48,8 m/s**, acima da faixa
(~30 m/s) em que re-entranhamento começa a degradar a coleta. **A eficiência tem que
ser medida, não escalada** — é o que as rodadas 3 e 6 vão mostrar.

O eixo de **vazão** substitui os cantos impossíveis porque o estudo anterior mostrou
que **50 % é a condição governante da eficiência**: η da classe de 10 µm cai de
79,1 % para 50,5 %. Um grid 3×3 só a 100 % perderia isso.

**Implementação:** a alavanca é a `Molecular Weight` do gás ideal (184 → 120 / 77 / 52)
mais a `Dynamic Viscosity`, como em `09_RODADA_sensibilidade_rho.md`.

---

## 7. Previsões registradas ANTES de rodar

Mesma disciplina do estudo de ρ (dez previsões registradas, dez confirmadas).

`ΔP = 7 717/ρ` a 100 % · `1 846/ρ` a 50 % · `d* = 6,84·√(ρµ/3,7487e-4)` µm a 100 % ·
`9,90·√(…)` a 50 % · `Re = 0,155207/(9,4249e-3·µ)`

| # | ρ | µ | **v_i** | **Re** | **ΔP** | **d\*** |
|---|---|---|---|---|---|---|
| 1 | 2,8 | 1,1e-5 | 19,16 m/s | 1 497 000 | **2 756 Pa** | **1,96 µm** |
| 2 | 1,8 | 1,4e-5 | 29,80 m/s | 1 176 000 | **4 287 Pa** | **1,77 µm** |
| 3 | 1,1 | 1,7e-5 | 48,76 m/s | 969 000 | **7 015 Pa** | **1,53 µm** |
| 4 | 2,8 | 1,1e-5 | 9,58 m/s | 748 500 | **660 Pa** | **2,84 µm** |
| 5 | 1,8 | 1,4e-5 | 14,90 m/s | 588 000 | **1 026 Pa** | **2,57 µm** |
| 6 | 1,1 | 1,7e-5 | 24,38 m/s | 484 500 | **1 679 Pa** | **2,21 µm** |
| **7** | 2,8 | 1,7e-5 | 19,16 m/s | 968 700 | **2 756 Pa** | **2,44 µm** ← pior |

**A previsão mais frágil, e a que mais importa checar:** a invariância de ξ. Ela foi
provada entre Re = 173 mil e 173 mil (a ρ variava, mas Re não). Aqui Re salta para
0,5–1,5 **milhão**. ξ em ciclone é dominado pela geometria e cai pouco com Re, então
as previsões de ΔP devem ser **levemente conservadoras** — mas se ξ cair mais que
~7 %, o cenário B volta para dentro dos 40 mbar. **Rodar o #2 primeiro.**

**Previsão qualitativa:** a eficiência **sobe** em todos os seis casos (d* cai de 6,84
para ~1,5–2,0 µm a 100 %). Não projeto η numericamente — a curva CFD tem que medir.

---

## 8. Perguntas ao cliente

1. **🔴 Os 1 820 kg/h são vazão mássica medida, ou vieram de medição volumétrica
   multiplicada por ρ = 3,946?** Decide tudo. Se for a segunda, uma composição mais
   leve reduz ṁ junto e o critério dos 90 g/mol não se aplica.
2. **A composição do reator é a mesma na entrada do ciclone?** O memorial assume
   100 % vapor sem condensação de óleo. Confirmar contra a T real do ponto.
3. **T do ponto do ciclone** — segue aberta (TT-209 ≈ 343 °C vs 400 °C assumido,
   `PEDIDO_valgroup.md` §4). O memorial já usa 350–400 °C, mais próximo do SCADA.

---

## 9. Efeito nas pendências

| pendência | status após o memorial |
|---|---|
| viscosidade do gás | ✅ **encerrada** — 1,1–1,7e-5, três métodos convergentes |
| massa específica | 🔄 **reaberta e agora crítica** — vira critério de ΔP |
| composição / massa molar | 🟡 GC (124) e Daniel A (120) convergem; aguarda GC do NCG |
| vazão mássica de gás | 🔴 **promovida a crítica** — ver pergunta 1 |
| granulometria dos finos | 🟠 continua sendo a maior incerteza da **eficiência** (7 pontos) |
