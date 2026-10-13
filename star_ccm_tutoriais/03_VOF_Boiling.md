# Tutorial 03 — VOF: Boiling

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: 🟡 seções 1–5 lidas (visão geral, Converting to a Two-Dimensional Mesh, Scaling the Mesh,
> Selecting the Physics Models, Setting the Material Properties — 13/10/2026). Restante a receber.

---

## 0. Por que este tutorial

Os tutoriais 01 e 02 são **Eulerianos**: as bolhas são menores que a célula e o vapor é uma "fração"
misturada ao líquido. Este é **VOF**, em que a **interface líquido–vapor é resolvida** pela malha.
É o caminho para quando a fronteira entre as fases é **maior que a célula**: superfície livre, filme
de vapor, bolsões e golfadas.

Objetivo declarado do tutorial: mostrar o fluxo de trabalho de ebulição com mudança de fase e **o efeito
dos parâmetros do modelo de ebulição na quantidade de calor trocada**.

## 1. O caso

| item | valor |
|---|---|
| Geometria | a mesma do tutorial *VOF: Gravity-Driven Flow*, **escalada por 0,1** → bocal de ~50 mm |
| Domínio (após escala) | x ∈ [−0,4; 0,5] m · y ∈ [0; 0,4] m · **2D** |
| Entrada (esquerda) | água a **1 m/s** e **350 K** |
| Saída (direita) | **370 K**, pressão atmosférica |
| Parede inferior | **temperatura fixa de 540 K** |
| Demais paredes | adiabáticas |

### A régua deste caso — em que regime de ebulição ele está?

A 1 atm, Tsat = 373,1 K. A parede a 540 K está **167 K acima da saturação**. Para situar na curva de
ebulição (água, 1 atm, CoolProp):

| grandeza | valor |
|---|---|
| Fluxo crítico (Zuber, CHF) | **≈ 1,1 MW/m²** |
| Rohsenow (C_sf = 0,013) a ΔT = 10 / 20 / 30 K | 0,14 / 1,1 / 3,8 MW/m² |
| → fim da ebulição nucleada | ΔT ≈ **20 K** (Rohsenow alcança o CHF) |
| Fluxo mínimo (Zuber/Berenson) | ≈ 19 kW/m² |
| **Rohsenow extrapolado a ΔT = 167 K** | **≈ 650 MW/m²** — 580× o CHF, **fisicamente impossível** |

> ⚠️ **Leitura de engenharia:** com 167 K de superaquecimento a física real é **transição/ebulição em
> filme** (parede coberta por vapor), não ebulição nucleada. Uma correlação de ebulição nucleada
> aplicada sem limite daria um fluxo absurdo. No VOF, o filme de vapor pode **aparecer sozinho**: se a
> célula junto à parede encher de vapor, a troca passa a ser por condução no vapor. **A conferir nas
> próximas seções:** que modelo de ebulição o tutorial usa, como trata esse regime e quanto calor
> sai. Comparar sempre o fluxo médio na parede com o CHF e o fluxo mínimo acima.

## 2. Malha 3D → 2D

O STAR converte uma malha 3D "fina" (uma camada de células) em 2D. **Requisitos:**
1. Malha **alinhada com o plano X-Y**.
2. Uma fronteira **plana em Z = 0**.

Se a malha não atender, primeiro reposicionar a região (*Transform*: translação/rotação).

Procedimento:
1. `Scenes > New > Mesh` (para ver o resultado).
2. `Mesh > Convert to 2D...` → marcar **Delete 3D Regions After Conversion** → OK.
3. Apagar o contínuo 3D antigo (`Continua > Physics 1 > Delete`). A conversão cria um novo,
   `Physics 1 2D`, já com *Two Dimensional*.

> Cenas 2D não giram com o mouse (vista fixa em z).

> 💡 **Técnica a reaproveitar:** para estudar uma **seção transversal** (ex.: corte de um feixe de
> tubos), modelar o corte como extrusão fina no CAD, com uma face em z = 0, gerar a malha e converter
> para 2D. Sai mais barato e mais limpo que montar o 2D à mão.

## 3. Escala da malha

A malha importada está **10× grande**:
1. `Mesh > Scale Mesh` → região `Default_Fluid 2D` → **Scale Factor = 0,1** → *Apply*.
2. *Reset View* na barra de visualização.
3. `Mesh > Diagnostics` → conferir a extensão: x ∈ [−0,4; 0,5], y ∈ [0; 0,4], z = 0.

> 💡 **Hábito a criar:** depois de importar qualquer geometria, rodar **Mesh > Diagnostics** (ou
> conferir as *bounding boxes*) e comparar com a dimensão esperada. Erro de unidade (mm × m) é o erro
> mais barato de pegar e o mais caro de descobrir no fim. O *Scale Mesh* corrige sem refazer a malha.

## 4. Modelos físicos

Um contínuo, uma região (as duas fases ocupam o mesmo domínio). Renomear `Physics 1 2D` → `Boiler`.

| grupo | modelo |
|---|---|
| Espaço | **Two Dimensional** (já vem da conversão) |
| Tempo | **Implicit Unsteady** |
| Material | **Multiphase** (+ Multiphase Interaction, automático) |
| Modelo multifásico | **Volume of Fluid (VOF)** (+ Segregated Flow, Gradients) |
| Regime | Turbulent → RANS |
| Turbulência | K-Epsilon → **Realizable K-Epsilon Two-Layer** (+ Wall Distance, **Two-Layer All y+**) |
| Opcionais | **Segregated Multiphase Temperature** · **Gravity** |

### VOF × Euleriano (EMP) — as diferenças que importam

| | **VOF** (este tutorial) | **Euleriano** (tutoriais 01 e 02) |
|---|---|---|
| interface | **resolvida** pela malha | **não resolvida** — bolhas menores que a célula |
| quantidade de movimento | **uma** velocidade para a mistura | uma velocidade **por fase** (deslizamento entre fases) |
| energia | **uma** temperatura por célula (*Segregated Multiphase Temperature*) | uma temperatura **por fase** (*Phase Coupled Fluid Energy*) |
| tempo | **transiente** | permanente possível |
| custo | malha fina na interface + passo de tempo pequeno | malha mais grossa, mas mais equações e modelos de interação |
| serve para | superfície livre, filme, bolsões, golfadas | nuvem de bolhas, ebulição nucleada em feixe ou tubo |

> ⚠️ **Consequência da temperatura única:** numa célula com interface, líquido sub-resfriado e vapor
> saturado **não podem ter temperaturas diferentes**. Para ebulição **sub-resfriada com bolhas
> pequenas** o Euleriano é o modelo certo; o VOF serve quando as estruturas de vapor são grandes.

## 5. Materiais (fases)

`Boiler > Models > Multiphase > Phases`:

| fase | material | equação de estado |
|---|---|---|
| `H2O` | Liquid | Constant Density |
| `H2O (G)` | Gas → **Replace with** `Material Databases > Standard > Gases > H2O (Water)` | Constant Density |

O tutorial diz que **as propriedades padrão servem** para este caso.

> ⚠️ **Em projeto real, conferir sempre.** As propriedades padrão do banco são de uma condição de
> referência (a água líquida padrão é da ordem de 997 kg/m³, típica de ~25 °C). Para água a 350–373 K
> a densidade real é 958–974 kg/m³. Para pressão diferente da atmosférica, gerar as propriedades com
> `props_agua_saturada.py` (receita do tutorial 02).

---

## Checklist reaproveitável (até aqui)
- [ ] Antes de escolher o modelo: **qual a escala da interface?** Maior que a célula → VOF; menor →
      Euleriano.
- [ ] Situar o caso na **curva de ebulição** (Rohsenow, CHF de Zuber, fluxo mínimo) antes de rodar.
- [ ] Seção 2D: extrusão fina no plano X-Y com face em z = 0 → *Convert to 2D* → apagar o contínuo 3D.
- [ ] `Mesh > Diagnostics` depois de importar: conferir dimensões e unidades (*Scale Mesh* se preciso).
- [ ] VOF: *Implicit Unsteady* + *Segregated Multiphase Temperature* + *Gravity*.
- [ ] Propriedades padrão do banco **não** são de saturação: conferir ou substituir.

## Seções seguintes
*(a receber)*
