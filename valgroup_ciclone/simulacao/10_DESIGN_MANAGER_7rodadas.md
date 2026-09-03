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

## 13. O macro Java — o ponto de inserção existe e resolve os dois problemas

Quatro pontos de inserção: `Before Update Model` · `Before Meshing` · `Before Running`
· **`Before Results`**.

> *"**Before Results** — if you want to perform the actions **after the Simcenter
> STAR-CCM+ solver completes**, and before any results are returned to Design Manager."*

E a doc traz o nosso padrão como exemplo literal: *"modify the run settings, extend the
number of iterations in the stopping criteria, and then **re-run the solver**… Using
this technique you can perform two runs… for a single design."*

### A arquitetura

```
Solver Block (padrão)   → converge o campo gasoso, Lagrangeano CONGELADO
   ↓
macro em Before Results → descongela o Lagrangeano
                          injeta as 8 classes
                          ajusta o critério de parada da fase de rastreio
                          roda
                          ⚠️ VERIFICA e lança exceção se parcelas ativas = 0
   ↓
Result Block (padrão)   → grava ΔP, η, ξ, balanco_010, v_i
```

### A guarda vai dentro do macro

> *"If a macro throws an error during execution, the corresponding design is **marked as
> a failure**. The error message includes the name of the macro file in which the failure
> occurred."*

Isso **converte a falha silenciosa em falha detectada**. Se o macro checar a contagem de
parcelas ativas e lançar exceção quando for zero, o design sai marcado como erro em vez
de devolver η = 0 com aparência de sucesso (§7).

Com o `balanco_010` como Constraint, ficam **dois portões independentes**:
o macro pega o solver congelado; o constraint pega perda de parcela em voo.

### Como adicionar

`[design study] > Settings > Macro Files > New` → selecionar o `.java` →
`Macro Insertion Point = Before Results`. Vários macros são permitidos por estudo.

O `.java` se produz gravando os passos no próprio STAR-CCM+ (`Recording a Macro`).

---

## 14. A tabela de designs — CSV pronto

Formato documentado:

```
Design#, Name, <param1>, <param2>, ...
```

`Design#` e `Name` são opcionais. **O cabeçalho de cada coluna tem de bater exatamente
com o nome do parâmetro** no estudo.

Arquivo gerado: **`designs_7rodadas.csv`** (nesta pasta)

```
Design#,Name,MW_gas,mu_gas,mdot_gas
1,A_100,130.5939,1.100000e-05,0.505556
2,B_100,83.9532,1.400000e-05,0.505556
3,C_100,51.3047,1.700000e-05,0.505556
4,A_050,130.5939,1.100000e-05,0.252778
5,B_050,83.9532,1.400000e-05,0.252778
6,C_050,51.3047,1.700000e-05,0.252778
7,canto_pior_dstar,130.5939,1.700000e-05,0.505556
```

Unidades: `MW_gas` kg/kmol · `mu_gas` Pa·s · `mdot_gas` kg/s. Os Global Parameters têm
de estar declarados nessas unidades, senão o CSV entra com número certo e grandeza errada.

`MW = ρ·RT/P` com R = 8314,4621 J/(kmol·K), T = 673,15 K, P = 120 000 Pa
(fator 46,64067). Verificado nos dois sentidos: os sete MW devolvem exatamente
2,8 / 1,8 / 1,1 kg/m³.

**Importar:** `[design study] > Design Table` → `Import CSV…`. Alternativas: `Add Row`
manual ou `From Sweep…` (este último **não** usar — é o que gera as 9).

---

## 15. Montagem do estudo, passo a passo

1. `Design Studies > New`, renomear
   ⚠️ No Windows o **caminho inteiro, incluindo este nome, não pode passar de 260
   caracteres**. Pasta de projeto profunda quebra aqui.
2. No nó do estudo: `Study Type = Manual` · `Simulation = [sim de referência]` ·
   `Evaluation Method = **Simulation**` (não `Surrogates` — não temos surrogate)
3. **`Simulation Effect = Solver` nos três parâmetros** — a doc manda fazer isto
   *antes* de selecionar os input parameters (§10)
4. `Input Parameters`: arrastar `MW_gas`, `mu_gas`, `mdot_gas` do nó `Parameters` do sim
   de referência, ou `botão direito > Edit`
5. `Design Table` → `Import CSV…` → `designs_7rodadas.csv`
6. `Responses`: arrastar os reports. Depois, por response:
   - **η global** → `Is Objective` ✔ · `Objective Properties > Goal = Maximum`
   - **ΔP** → `Is Constraint` ✔ · `Constraint Properties > Type = Maximum` · valor **4000**
   - **`balanco_010`** → `Is Constraint` ✔ · faixa 0,99–1,01
   - ξ, v_i, η de 10 µm → Information Only
7. *(opcional)* `Responses > Create User Response` — expressão sobre responses já
   existentes. Útil para a folga: `1 - dP/4000`. Vira coluna na tabela de saída.
8. `Scenes` e `Plots`: arrastar do sim; definir `Export Formats` (preferir `.sce` a
   hardcopy, por causa da memória de GPU) e `Compression Level`
9. `Settings > Macro Files > New` → macro do Lagrangeano, `Before Results` (§13)
10. `Auto Save` no nó do projeto (§11)

O **badge de aviso** no nó do estudo some quando a montagem está completa e correta.
Enquanto estiver lá, falta coisa.

---

## 16. Validar antes de rodar

O badge de aviso (⚠) no nó do estudo significa que a montagem está incompleta.

`botão direito no [design study] > **Validate Study**` → abre a janela **Validation
Warnings**, com `Message` e `Source` de cada aviso. Clicar num aviso **seleciona o nó
de origem na árvore**. A validação é dinâmica: some sozinho quando resolvido.

Reabrir: `Window > Validation > [projeto]`, ou o ícone de aviso no canto inferior direito.

⚠️ *"The warning badging tool can not dynamically validate a design study as long as
another design study is running in the same Design Manager Project."* Validar **antes**
de disparar qualquer coisa.

---

## 17. Rodar localmente — parâmetros de execução

### `[design study] > Settings > Run Settings`

| propriedade | o que fazer |
|---|---|
| **`Simultaneous Jobs`** | designs em paralelo |
| **`Compute Processes`** | cores por design |
| **`Save Simulation Files`** | quais designs guardam o `.sim` ← **alavanca de disco** |
| `Save Log files` | ligado por padrão, manter |
| **`Output Auxiliary File Types`** | *"output files whose extensions you do not specify are **deleted**"* |
| **`Design Reuse`** | **deixar DESLIGADO** — ver abaixo |
| `Clear History` | apagar histórico computacional |

⚠️ *"check that you have enough cores available (**simultaneous jobs × compute
processes**)"*. Conferir os cores da WS3 antes.

**Estratégia de execução recomendada**, casando com o reuso de malha (§6) e com a
checagem de baseline (§11, etapa 6): rodar o **design 1 sozinho** primeiro — ele é o
único que precisa malhar, e é onde se confere o baseline. Depois soltar os 2–7 em
paralelo, todos reusando a malha em cache.

### ⚠️ `Design Reuse` — desligado nesta rodada

> *"activates the initialization of new designs using results from previous successful
> designs."*

Economizaria iteração, mas **enviesa a medida que este estudo existe para fazer**. A
pergunta é se ξ continua 5,364 num Reynolds sete vezes maior (§7 das previsões). Um
design que herda o campo do anterior e não converge por completo herda junto o estado
dele — e some com a atribuição.

Além disso o salto entre designs é grande: de A para C a velocidade de entrada vai de
19,2 para 48,8 m/s. Não é vizinhança, é extrapolação.

Ligar só numa segunda campanha, se o tempo apertar — e aí sabendo o que mudou.

### `Compute Resource`

`Type = **Direct**` (máquina local) · `STAR-CCM+ Command Line Options` para opções de
licença, ex. `-power`.

### Disparar

- Um estudo: `botão direito no [design study] > **Run Study**`
- Todos em sequência: `botão direito em Design Studies > Run All Studies`
- Em lote: `starccm+ -batch run [RAIZ]/[PROJETO].dmprj`
  (`-dmnoshare` ativa o esquema *Unlicensed Design Manager Server*; omitir usa o padrão.
  Aspas obrigatórias se o caminho tiver espaço.)

⚠️ **Salvar o `.dmprj` antes de rodar** — sem isso ele abre diálogo e aborta.

---

## 18. Estrutura de saída e disco

| pasta | conteúdo |
|---|---|
| `Design_Exploration` | raiz do projeto: `.dmprj`, `.sim` de referência, `.java` |
| `Design_Manager_Project` | artefatos, criada em tempo de execução |
| `Design_Study_n` | uma por estudo |
| **`Design_m`** | **uma por design: `.sim` completo, `.log`, `.sce`/`.png`** |
| `.mdxruntime` | temporária, apagada no fim |

**São sete cópias do ciclone convergido.** Antes de rodar:

- redirecionar a pasta de artefatos para um disco grande — *"customize the location of
  the project artifact directory… particularly useful when you run low on disk space"*
- restringir `Save Simulation Files` aos designs que realmente precisam do `.sim`

Depois de re-rodar um estudo, os artefatos antigos ficam **órfãos e continuam ocupando
espaço**: `botão direito no [design manager project] > **Clean Project Artifacts**`.

Para abrir a pasta de um design: `botão direito na linha da Output Table > Show Design
Details` → link em `Design Artifact`.

---

## 19. Acompanhar a rodada

`Design Sets > All > **Open Output Table**` — tabela ao vivo com `State`, responses e
`Performance` de cada design.

Assim que um design conclui, dá para inspecionar sem esperar o resto: `botão direito na
linha > Open Scenes > [scene]` ou `Open Plots > [plot]`.

**Project plots atualizam ao vivo:** *"Once a design simulation completes, a new data
point appears in the plot."*

> 💡 Montar **antes de rodar** o plot de **ΔP × ρ**. A hipérbole `ΔP = 7 717/ρ` se
> desenha ponto a ponto, e a linha dos 4 000 Pa mostra na hora se o cenário B fica
> dentro ou fora — que é a única das sete previsões que eu não sei antecipar.

---

## 20. Parar, abortar, retomar

| ação | comportamento |
|---|---|
| **`Stop Study`** | impede novos designs de começar; **os que já rodam terminam** |
| **`Abort Study`** | **mata** as simulações em andamento |
| `Abort All Studies` | idem, em todos os estudos do projeto |

**Retomar:** `Run Study`. Ele *"automatically detects the completed designs and runs the
remaining design simulations"*.

**Abortar em lote:** criar um arquivo chamado **`DM_ABORT`** na pasta de execução (no
Windows um `.txt` vazio basta; no Linux `touch DM_ABORT`). O nome é customizável.

### ⚠️ `Auto Save` é requisito, não recomendação

> *"Design Manager can **only** resume from the last completed design **if** the Design
> Manager project is automatically saved when each design simulation completes. For this
> reason, you are advised to **always** activate the Auto Save option."*

Sem ele, queda no design 5 significa recomeçar do 1.

---

## 21. Re-rodar

### Estudo inteiro (quando mudou tipo, parâmetro, response, scene ou run settings)

`botão direito no [design study] > **Clear Study**` → ajustar → `File > Save` →
`Run Study`.

⚠️ *"Clearing a design study **does not remove** the Design Manager output files from
the disk."* Os artefatos velhos ficam e os novos ganham subscritos. Apagar a pasta do
estudo à mão, ou usar `Clean Project Artifacts` (§18).

### Só os que falharam

`Design Sets > **Error** > Rerun Designs` — ou selecionar linhas na Output Table (ou
pontos num plot) e `Rerun Designs`.

### 🔒 A restrição que obriga a acertar de primeira

> *"You **can** add and remove **responses** in the design study before you re-run
> selected designs. Adding and removing **parameters** is not supported."*

**Report esquecido tem conserto** — adiciona o response e re-roda os designs.
**Parâmetro esquecido não tem** — o estudo teria de ser refeito.

Por isso `MW_gas`, `mu_gas` e `mdot_gas` precisam estar corretos já na etapa 1 (§11).

⚠️ *"re-running a baseline design can change the performance value of other designs."*

### `Valid Minimum` / `Valid Maximum`

Se um design falhou por cair fora da faixa válida de um response, mudar a faixa faz o
design ser *"re-evaluated with the new range **without actually re-running the
simulations**"*.

---

## 22. `Update Metrics` — o limite de 40 mbar fica editável

> *"After running the design studies, you can modify constraints and assess the impact
> of the change on results **without re-running the design study**… select `Update
> Metrics` to recompute these values and update related plots and charts."*

`botão direito no [design study] > **Update Metrics**`.

**É o argumento mais forte para codificar os 4 000 Pa como Constraint em vez de conferir
na mão.** O limite é especificação de cliente e pode mudar: se a Valgroup disser que são
50 mbar, ou se o Daniel questionar a origem do número, muda-se o valor da constraint e a
coluna *feasible/infeasible* se recalcula na hora. As sete rodadas de CFD ficam
preservadas.

Vale o mesmo para a faixa do `balanco_010`.

Para propagar **novo plot ou scene** a todos os designs já rodados: `Update Results`
(pós-processamento assíncrono).

---

## 23. O que os vinte e sete documentos ainda NÃO cobrem

Faltam as páginas de procedimento. Em ordem de utilidade:

1. **`Global Parameters`** — como criar e como apontar um valor de física para um.
   **É a única lacuna que ainda bloqueia**: sem ela a etapa 1 (§11) não sai do papel,
   e §21 mostra que parâmetro errado não tem conserto depois
2. **`Recording a Macro` / `Scripting the Application`** — a sintaxe Java para
   descongelar o solver Lagrangeano e para lançar a exceção da guarda (§13)
3. **`Constraint Properties`** e **`Objective Properties`** — os detalhes de `Type` e
   `Goal` (§15, passo 6)
4. **`Design Manager Licensing`** — o que a CAEXPERTS precisa ter, e o que muda com
   `-dmnoshare`
5. **`Creating XY Plots`** — para montar o gráfico ΔP × ρ antes de rodar (§19)

Em segundo plano: `Run Settings Reference`, `Output Table Reference`, e o tutorial
*Design Manager: Design **Sweep** of a Static Mixer*.

✅ Resolvido: tipos de estudo (§1), inputs (§2), reuso de malha (§6), Lagrangeano e
macros (§7, §13), análise (§8), `Simulation Effect` (§10), projeto e procedimento
(§11), `Update` (§12), CSV (§14), montagem (§15), validação (§16), execução (§17),
disco (§18), monitoramento (§19), parar/retomar (§20), re-rodar (§21),
`Update Metrics` (§22).

**Não se aplicam ao nosso caso:** `Substituting Geometry Parts in a Study` (não trocamos
peça), `Seeding a Study with Predefined Designs` (é para semear otimização), `Setting Up
a Smart Sweep Study` (mapa de compressor) e `Setting up a Gradient-Based Optimization
Study` (SQP — exige licença Intelligent Design Exploration e compatibilidade com o
solver Adjoint).
