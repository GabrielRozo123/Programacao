# Design Manager — as 7 rodadas de sensibilidade ρ × µ

> Base: documentação Simcenter STAR-CCM+ 21.02.007-R8 (páginas *Design Manager*,
> *Study Types*, *Study Inputs*, *Study Outputs*, *AI Reduced Order Models*).
> Matriz aprovada pelo Marcus em `dados_cliente/ANALISE_memorial_Vozza_rev01.md` §6.

---

## 1. Tipo de estudo: `Manual`

| tipo | o que faz | serve? |
|---|---|---|
| **Manual** | *"define a set of designs using **tabulated data**, where each design is a certain combination of input parameter values"* | ✅ **é o nosso** |
| Sweep | *"creates a **full factorial** design sweep that goes through **all combinations**"* | ❌ devolve as 9 |
| Smart Sweep | varredura com critério de parada, para mapas de compressor | ❌ |
| DOE / Optimization / Adaptive Sampling / Robustness | escolhem os pontos por algoritmo | ❌ e exigem licença |

**Achado:** as 9 simulações propostas pelo memorial são exatamente o que um `Sweep`
produz — fatorial completo 3 ρ × 3 µ. Não foram escolha física; são a forma padrão da
ferramenta. As nossas 7 são um subconjunto deliberado, e por isso exigem `Manual`.

### Licenciamento

> *"CAD robustness studies and **performance assessment** studies do not require
> specific licensing; **design optimization** studies are only available with
> Simcenter STAR-CCM+ Intelligent Design Exploration licensing."*

`Manual` é performance assessment ⇒ **não precisa da licença Intelligent Design
Exploration**. ⚠️ A licença do **Design Manager em si** é separada — confirmar que a
CAEXPERTS tem antes de planejar prazo.

---

## 2. Inputs — têm de ser Global Parameters

Só três tipos de objeto são aceitos como input: *3D-CAD Design Parameters*, *CAD
Client Design Parameters* e **Global Parameters**. Os nossos três são todos do terceiro
tipo (a doc cita explicitamente *"Boundary physics values—such as inlet velocities"*).

| parâmetro | objeto no sim de referência | alavanca |
|---|---|---|
| `MW_gas` | Molecular Weight do gás ideal | define ρ = PM/RT |
| `mu_gas` | Dynamic Viscosity (Constant) | define µ |
| `mdot_gas` | Mass Flow Rate no inlet | 100 % vs 50 % |

**Trabalho de preparação:** criar os três Global Parameters e **apontar os valores da
física e do contorno para eles** — hoje estão digitados direto. Sem isso o Design
Manager não tem o que modificar.

### ⚠️ `Simulation Effect` — o item de maior impacto

> *"For each parameter, you specify whether changing the parameter value would require
> a change in the mesh."*

Os três parâmetros são **puramente físicos** — nenhum mexe na geometria nem na malha.
Configurados assim, o Design Manager **reusa a malha nas 7 rodadas**.

Se ficarem marcados como afetando a malha, ele remalha **4,4 milhões de células sete
vezes** e o tempo de malha domina o estudo. Conferir antes de disparar.

### ⚠️ Detecção de duplicatas

> *"Design Manager uses a tolerance of 1.0E-16 to compare two floating-point numbers…
> Two designs are considered duplicate if all their design parameters are considered
> equal."*

Consequência direta: **a vazão tem de ser parâmetro.** Se for trocada na mão entre os
blocos de 100 % e 50 %, as rodadas 1 e 4 (mesmos ρ e µ) viram duplicata e uma é
descartada. Mesmo para 2/5 e 3/6.

---

## 3. A tabela de designs

`ρ = PM/RT` com P = 120 000 Pa e T = 673,15 K ⇒ `MW = ρ·RT/P = ρ × 46,64`.

| # | alvo | **MW_gas** (kg/kmol) | **mu_gas** (Pa·s) | **mdot_gas** (kg/s) | ρ resultante |
|---|---|---|---|---|---|
| 1 | A · 100 % | **130,59** | 1,1e-5 | 0,505556 | 2,8 |
| 2 | B · 100 % | **83,95** | 1,4e-5 | 0,505556 | 1,8 |
| 3 | C · 100 % | **51,30** | 1,7e-5 | 0,505556 | 1,1 |
| 4 | A · 50 % | 130,59 | 1,1e-5 | **0,252778** | 2,8 |
| 5 | B · 50 % | 83,95 | 1,4e-5 | 0,252778 | 1,8 |
| 6 | C · 50 % | 51,30 | 1,7e-5 | 0,252778 | 1,1 |
| 7 | canto pior d\* | 130,59 | **1,7e-5** | 0,505556 | 2,8 |

**Nota de modelagem:** a densidade é variada pela **massa molar a T fixa**, não pela
temperatura. Isso isola a incerteza de *composição*, que é o que o memorial do Vozza
descreve — mesma convenção do estudo de ρ (`09_RODADA_sensibilidade_rho.md`). A
incerteza de temperatura é um eixo separado, ainda aberto.

---

## 4. Outputs

Responses vêm de **Reports do sim de referência**. Cada estudo exige pelo menos um.
Três papéis possíveis: *Information Only*, *Objective*, *Constraint*.

| response | report de origem | papel |
|---|---|---|
| **ΔP** | queda de pressão entrada→saída | **Constraint ≤ 4 000 Pa** |
| **η global** | eficiência de coleta | **Objective (maximizar)** |
| η da classe de 10 µm | | Information Only |
| ξ (número de Euler) | `2ΔP/(ρv_i²)` | Information Only — **é a checagem de consistência** |
| v_i | velocidade de entrada | Information Only — vigiar re-entranhamento acima de ~30 m/s |

### O critério dos 40 mbar vira coluna automática

> *"Designs that satisfy all constraints are called **feasible**. If any constraint is
> not satisfied, the design is called **infeasible**."*

Declarando ΔP ≤ 4 000 Pa como constraint, a tabela de saída marca as rodadas **2 e 3
como infeasible** sozinha. O critério que derivamos analiticamente vira resultado
nativo da ferramenta — bem mais forte de mostrar ao cliente do que uma conta nossa.

⚠️ *"While a study is running, no change of responses on the fly is considered. The
design study must be stopped and resumed."* Definir todos os responses **antes** de
disparar. Se um constraint mudar depois, usar `[design study] > Update Metrics`.

### Scenes e plots

São escritos por design automaticamente, em `.sce` (interativo) ou `.png`. Vale
exportar a scene do vórtice e o plot η×d de cada rodada — sai pronto para o relatório.

---

## 5. AI ROM — não agora

Precisa de **duas** licenças (Intelligent Design Exploration + PhysicsAI `sc_gdl`), e
7 designs são poucos demais para treinar.

Registrado para o futuro: *"you can also import simulation files run previously
(outside of Design Manager) into a manual study."* Se um dia houver volume de rodadas
(as 7 + as 6 do estudo de ρ + o que vier do GC), dá para semear um ROM sem refazer nada.

---

## 6. O que estes cinco documentos NÃO cobrem

Faltam as páginas de procedimento. Em ordem de utilidade:

1. **`Setting Up Simulation Effect for Simulation Parameters`** — citada mas não
   incluída; é o item de maior impacto no tempo de máquina
2. **`Global Parameters`** — como criar e como apontar um valor de física para um
3. **Manual study / Design Table** — como se preenche a tabela (importa CSV?)
4. **`Design Manager Licensing`** — o que a CAEXPERTS precisa ter
5. Como criar o projeto do Design Manager e apontá-lo para o sim de referência
   (execução: sequencial vs concorrente, serial vs paralelo, alocação de recursos)
