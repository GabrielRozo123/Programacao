# Fase 3 · Aerador com 16 lanças — boundaries no STAR-CCM+

Arquivo: `aerador_16lancas_fluido.step` · 1 sólido · 36 faces · 19,991 m³ · mm.

## 1. Topologia (a mesma do STEP original de 3 lanças)

Cada lança é **um cilindro subtraído do fluido**, com exatamente duas faces:
a lateral (parede) e o disco da ponta (injetor). Não é um tubo — não há parede
interna nem externa, não há face de topo, nada sobressai da superfície livre.
O escoamento *dentro* da lança não é resolvido pelo CFD: o fluido entra pelo
disco da ponta com a pressão total imposta, e o ΔP interno é a álgebra
(`algebra_lancas.py`).

## 2. Inventário de faces — gabarito de seleção

| grupo | faces | como identificar | área de cada |
|---|---|---|---|
| `aerador.injetores` | 16 | discos planos, normal +z, em z = −5450 (5) e z = −4660 (11) | **3 087,6 mm²** |
| `aerador.lancas` | 16 | cilindros R = 31,35 | 1 313 842 (5) / 1 158 230 (11) mm² |
| `aerador.topo` | 1 | plano em z = +1220 | **3 193 526 mm²** |
| `aerador.parede` | 3 | casco R = 1016, cone do fundo, disco em z = −5892 | 35 672 207 / 6 812 461 / 209 117 mm² |

Os injetores são ~1 000× menores que qualquer outra face — não há como confundir.
No STAR: `Parts → Surfaces → Faces` → botão direito → **`Split by Patch`**, e depois
agrupar pelas áreas acima com `Combine`. Em seguida `Assign Parts to Regions` com
**`Create a Boundary for Each Part Surface`**.

## 3. Condições de contorno

> **Conceito confirmado pelo Marcus (14/08):** as lanças sopram **ar puro**, como na
> primeira simulação. A campanha é de três pressões de suprimento — 1, 2 e 3 kgf/cm².
> A rodada de mistura xarope+ar (VF 0,235) foi descartada.

| boundary | tipo | valores |
|---|---|---|
| `aerador.injetores` | **Stagnation Inlet** | Total Pressure **98 066,5 / 196 133 / 294 200 Pa** · **VF ar = 1,0** · xarope = 0 |
| `aerador.topo` | Pressure Outlet | 0 Pa · **Backflow Specification → Scalars = Extrapolated** |
| `aerador.lancas` | Wall | no-slip |
| `aerador.parede` | Wall | no-slip |

`Scalars = Extrapolated` não é detalhe: o `Q_ar_in` é o resultado da campanha, e ele só
fecha contra o `mx_ar_topo` se o refluxo não inventar ar que nunca passou pelas lanças.
Com `Specified`, o ar reflui também com o **Sauter Mean Diameter prescrito** — bolhas
já coalescidas voltariam renascidas no diâmetro de injeção, enviesando o histograma
justamente na cauda que interessa.

**Física:** Laminar (sem k-ε — ver §5), Gravity, EMP, S-Gamma, Ar como **Ideal Gas**
(expande ~1,9× subindo do injetor à superfície).

**Inicialização:** `VF Xarope = 1,0` (tanque cheio de xarope) e `VF Ar = 1e-3` — o
seed de ar é numérico, 0,02 m³ em 20 m³, e existe só para condicionar a equação de
momento da fase ar onde ela some (a fase fantasma que deu 4583 m/s no ejetor).

`aerador.lancas` separado de `aerador.parede` de propósito: é nele que se lê o
`Wall Shear Stress` que sustenta o argumento do arranjo (ver §4).

## 4. Arranjo — o que o novo layout entrega

| | anel interno | anel externo |
|---|---|---|
| nº de lanças | 5 | 11 |
| raio (a partir do eixo do aerador) | 375 mm | 770 mm |
| cota de descarga | z = −5450 | z = −4660 |
| submergência | 6 670 mm | 5 880 mm |
| folga mínima à parede do cone | 72,6 mm | 70,0 mm |

Descarga **escalonada**: o fundo é cônico (r = 1016 em z = −4368,6 caindo para
r = 259,5 em z = −5892), então o anel externo não pode descer tanto quanto o
interno. Cada anel para na cota mais funda que o cone permite, com 50 mm de folga
mais 40 mm de margem, verificado ponto a ponto ao longo de toda a lança.

Diâmetro: **Ø62,7 mm** — o interno de 2½" Sch40. Como a lança é um cilindro único,
esse diâmetro é ao mesmo tempo a área de escoamento no injetor e a obstrução no
domínio; adotar o interno mantém a vazão por lança coerente com a álgebra.
A obstrução total é 16 × 3 087,6 = 49 402 mm², ou 1,5 % da seção do aerador.

Diâmetro **Ø62,7 mm** (interno de 2½" Sch40) em todas as 16. Obstrução total
16 × 3 087,6 = 49 402 mm², ou 1,5 % da seção do aerador.

## 5. Margem de sopro — resultado que sai da aritmética, antes da CFD

Com lança de ar, o que governa é a hidrostática que o ar precisa vencer:

| anel | submergência | hidrostática |
|---|---|---|
| interno (5 lanças, z = −5450) | 6,67 m | **0,901 kgf/cm²** |
| externo (11 lanças, z = −4660) | 5,88 m | **0,794 kgf/cm²** |

| suprimento | margem interno | margem externo | desequilíbrio |
|---|---|---|---|
| **1 kgf/cm²** | 9 732 Pa (**9,9 %**) | 20 195 Pa (20,6 %) | **2,08×** |
| 2 kgf/cm² | 107 799 Pa (55,0 %) | 118 261 Pa (60,3 %) | 1,10× |
| 3 kgf/cm² | 205 865 Pa (70,0 %) | 216 328 Pa (73,5 %) | 1,05× |

A 1 kgf/cm² o anel interno opera a menos de 10 % de margem — a 0,10 kgf/cm² de não
soprar — e o anel externo recebe o dobro de pressão motriz. A partir de 2 kgf/cm² os
dois anéis equalizam. **A descarga escalonada só é um problema na pressão mais baixa.**

## 6. Por que Laminar, e não k-ε

A rodada com k-ε divergiu com `non-finite residual (Tdr of Xarope)` em
`star.keturb.KeTurbSolver`, precedida de `Turbulent viscosity limited on 9.072.257
cells`. Não é ajuste de solver — é o modelo fora do domínio de validade:

| escala | v | L | Re |
|---|---|---|---|
| jato no injetor | 0,956 m/s | 62,7 mm | **12,4** |
| tanque inteiro | 14,8 mm/s | 2,032 m | **6,2** |

Sem produção, k → 0 e ε → 0 juntos, e `ν_t = C_µ k²/ε` vira 0/0 — literalmente a
divisão por zero da mensagem. Com Laminar as duas equações somem e a rodada fica
mais rápida.

Efeito colateral coerente: os kernels de quebra turbulenta do S-Gamma ficam sem
fonte, e o modelo passa a fazer só coalescência. É exatamente o que o argumento de
Grace já dizia (λ = µ_ar/µ_xarope ≈ 2,8e−6 ⇒ Ca crítico diverge, cisalhamento não
quebra bolha nesse xarope).

## 7. Não existe regime permanente — critério de parada

Só entra ar; nada de xarope entra. O ar não sobe (17 h para bolha de 1 mm, 430 h
para 0,2 mm), então acumula. Como o domínio é rígido e o xarope é incompressível,
para o ar caber o xarope sai pelo topo. Na máquina real o **nível sobe** — representar
isso exigiria VOF ou malha móvel.

Monitor obrigatório: `V_xarope` = Volume Integral de `Volume Fraction of Xarope` na
região. Começa em 19,99 m³.

| tempo físico (a Q_ar = 40 m³/h) | xarope deslocado |
|---|---|
| 60 s | 3,3 % |
| 120 s | 6,7 % |
| 600 s | 33 % |

**Pare quando `V_xarope` < 19,0 m³ (perda de 5 %)** — algo entre 1 e 3 min de tempo
físico. É tempo de sobra: a pluma e o histograma amadurecem no primeiro minuto.

⚠️ Não usar `Phase Impermeable` no xarope. Com xarope preso e domínio rígido, o ar
também não poderia acumular — o solver seria forçado a expulsá-lo na mesma taxa em
que entra, atravessando 7 m instantaneamente. Deixar o xarope sair é o artefato
menos errado, e o `V_xarope` diz até quando ele é aceitável.
