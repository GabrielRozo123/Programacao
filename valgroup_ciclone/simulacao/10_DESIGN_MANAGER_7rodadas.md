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

## 6. Reuso de malha — confirmado para `Manual`

> *"The following design study types permit mesh caching and reuse: Sweep, DOE (2 Level
> and 3 Level only), **Manual**. In addition, designs must share the same **Geometry**
> and **Meshing** parameters. When these conditions apply, a design that qualifies need
> only run the **Solver Block** and **Result Block**."*

As nossas 7 só variam parâmetros de física. **Malha calculada uma vez, reusada seis.**

O Design Manager reordena a execução para isso: os designs que precisam malhar começam
primeiro, os que reusam esperam o cache ficar pronto.

---

## 7. Lagrangeano — a rodada é em duas etapas, e isso exige macro

Questionamento do Marcus: *"eu acho que o DM não faz LMP."*

**Nada nas oito páginas restringe modelo de física.** O Design Manager lança o STAR-CCM+
em batch, modifica parâmetros, roda e grava reports — é agnóstico ao modelo. As únicas
restrições de física documentadas são para o solver Adjoint (otimização SQP) e para o
AI ROM, nenhum dos quais está no nosso caminho.

**Mas o problema real é outro, e o instinto do Marcus aponta para ele.** A nossa rodada
é de duas etapas (`07_EXECUCAO_lagrangeano_Dc307.md`): converge o campo gasoso com o
solver Lagrangeano **congelado**, depois descongela e rastreia as 5 082 parcelas. O
bloco padrão do Design Manager roda a simulação **uma vez**, até o critério de parada.

**Saída documentada:** macro Java no Solver Block.

> *"you can customize the simulation run by inserting **Java macros** that contain
> additional setup for the simulation… four types of macros can be inserted into
> different blocks of the workflow."*

### ⚠️ O risco de falha silenciosa

Armadilha nº 1 do nosso próprio doc de execução:

> *"Lagrangian Solver NÃO está `Frozen`* — ⛔ nenhum erro, **todos os reports devolvem
> zero corretamente**"

Automatizado, isso produz **7 designs marcados como concluídos com sucesso e η = 0**.
Não há erro para o Design Manager detectar.

**Blindagem:** declarar o `balanco_010` (detector de fraude, tem de dar 1,00 ± 0,01)
como **Constraint**. Qualquer design com balanço quebrado sai marcado *infeasible*
automaticamente na tabela de saída. Transforma a nossa checagem manual em porta
automática.

### Outra parada abrupta a conhecer

> *"The design study will stop when the **baseline design fails**"* — se houver ao menos
> um objetivo com `Baseline Normalization`. Com a η global declarada como Objective,
> uma falha do baseline **aborta o estudo inteiro**. Rodar o baseline sozinho primeiro.

---

## 8. Análise dos resultados

Três objetos de pós-processamento, sincronizados entre si (selecionar um design em um
atualiza os outros):

| objeto | serve para |
|---|---|
| **Output Tables** | tabela com Design# · State · responses · Performance · parâmetros |
| **Snapshots** | comparação lado a lado das scenes/plots exportadas de cada design |
| **Design Plots** | XY, coordenadas paralelas e pizza cruzando todos os designs |

**Design Sets** predefinidos que interessam: `Feasible` (atende todos os constraints —
é onde o critério de 40 mbar aparece sozinho), `Error`, `Successful`, `All`.

Para o relatório: um XY plot de **ΔP × ρ** sobre os 7 designs mostra a hipérbole
`ΔP = 7 717/ρ` medida, com a linha dos 4 000 Pa cortando entre os cenários A e B.
É o gráfico que fecha o argumento com o cliente.

---

## 9. Execução

Local ou cluster; sequencial ou concorrente; serial ou paralelo. Para cluster há dois
modos, e o **pré-alocação** é descrito como *"most efficient usage for the following
study types: **Manual**, Sweep, DOE, and Robustness and Reliability"* — reserva as
licenças antes e ninguém as toma no meio. ⚠️ Só Linux.

Workflow oficial (7 passos): montar o sim de referência → criar o projeto → montar o
estudo → *(opcional: surrogate)* → rodar → monitorar → analisar.

⚠️ *"no update is done once the study starts running"* — parâmetros e responses são
passados ao HEEDS no início. Mudança exige parar e retomar.

---

## 10. ⚠️ `Simulation Effect` — o padrão trabalha contra nós

> *"By default, 3D-CAD and CAD Client parameters have Simulation Effect set to
> `Geometry`, and **global parameters have Simulation Effect set to `Unknown`**."*
>
> *"**Unknown**: Implies the parameter affects **everything** (geometry, meshing, and
> solver)."*
>
> *"If all of the simulation parameters affect meshing (that is, `Unknown`, `Geometry`
> or `Meshing` for **every** parameter), **there is no possibility of reusing a mesh so
> caching is disabled**."*

Os nossos três parâmetros são Global Parameters. **No padrão, os três entram como
`Unknown` e o cache é desabilitado** — o estudo remalharia 4,4 M de células sete vezes.

| Simulation Effect | significa |
|---|---|
| `Unknown` | afeta tudo — **é o padrão de global parameter** |
| `Geometry` | afeta geometria (⇒ malha e solver) |
| `Meshing` | afeta malha (⇒ solver) |
| **`Solver`** | **afeta só o solver** ← é o nosso |

**Ação:** `Simulations > [sim de referência] > Parameters > Simulation Parameters >
[parâmetro]` → `Simulation Effect = Solver`, nos três (`MW_gas`, `mu_gas`, `mdot_gas`).

Com isso, *"only the solve and result blocks are re-executed during a study run."*

---

## 11. Procedimento de montagem, em ordem

### Etapa 1 — no `.sim` de referência (tudo antes de criar o projeto)

> *"You can **not** create these objects in the Design Manager project. Instead, you
> must go to the reference simulation directly."*

1. Criar os **Global Parameters** `MW_gas`, `mu_gas`, `mdot_gas`
2. Apontar Molecular Weight, Dynamic Viscosity e Mass Flow Rate **para eles** (hoje os
   valores estão digitados direto)
3. Garantir que existam os **Reports**: ΔP · η global · η da classe de 10 µm · ξ ·
   v_i · **`balanco_010`**
4. Preparar as **scenes/plots** a exportar por design (vórtice, η×d)
5. Salvar e fechar

### Etapa 2 — criar o projeto

Duas vias: botão direito na raiz do `.sim` → `Create Design Manager Project`; ou
`Create a File` → Type `Design Manager Project` → `Read Reference Simulation…`.

⚠️ *"Design Manager requires that the Design Manager project is located in the **same
file folder** of the reference simulation."* Arquivo `.dmprj`.

### Etapa 3 — corrigir o `Simulation Effect` (§10)

**Antes de qualquer outra coisa.** É o passo que decide o tempo de máquina do estudo.

### Etapa 4 — montar o estudo

Tipo **`Manual`**, tabela de 7 linhas (§3). Responses com os papéis de §4 —
`balanco_010` e ΔP como **Constraints**.

### Etapa 5 — ligar o `Auto Save`

No nó do projeto. *"You are strongly advised to activate this option. If the Design
Manager project crashes for any reason, you can resume the project from the completed
designs."* Custa desempenho, mas perder o design 6 de 7 custa mais.

### Etapa 6 — rodar o baseline sozinho antes

Duas razões: falha do baseline **aborta o estudo inteiro** (§7), e é onde se detecta o
solver Lagrangeano congelado antes de queimar sete rodadas.

---

## 12. 🔁 A armadilha do `Update`

Depois de qualquer uma destas mudanças no `.sim`, é obrigatório salvar, fechar e dar
**botão direito no `[reference simulation]` → `Update`**:

- criar ou remover parâmetro, report, scene ou plot
- **mudar valor de parâmetro**
- renomear qualquer um deles

Para o resto (trocar o campo escalar de uma scene, por exemplo) não precisa.

Esquecer o `Update` faz o estudo rodar com a definição velha, **sem aviso**. É o
mesmo padrão de falha silenciosa do solver congelado — e as duas juntas produziriam
sete designs "bem-sucedidos" e sem sentido.

---

## 13. O que os doze documentos ainda NÃO cobrem

Faltam as páginas de procedimento. Em ordem de utilidade:

1. **`Customizing the Workflow Using Java Macros`** — continua em primeiro. Sem ela não
   há como orquestrar as duas etapas do Lagrangeano (§7)
2. **`Global Parameters`** — como criar e como apontar um valor de física para um
   (etapa 1 do procedimento, §11)
3. **Manual study / Design Table** — como se preenche a tabela de 7 linhas; aceita CSV?
4. **`Responses`** — como declarar Objective vs Constraint e fixar o limite de 4 000 Pa
5. **`Design Manager Licensing`** — o que a CAEXPERTS precisa ter

Em segundo plano: `Creating Design Plots` e o tutorial *Design Manager: Design **Sweep**
of a Static Mixer* (o de sweep, não o de otimização — é o mais próximo do nosso caso).

✅ Já resolvido: `Setting Up Simulation Effect` (§10), workflow de projeto (§11),
`Update` (§12).
