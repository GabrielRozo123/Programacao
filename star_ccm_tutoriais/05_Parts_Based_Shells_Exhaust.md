# Tutorial 05 — Parts-Based Shells: Exhaust Pipe

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Heat Transfer*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: ✅ tutorial completo lido (seções 1–10: visão geral, geometria no 3D-CAD, attached shells,
> wrapper e contatos, regiões e interfaces, malha, modelos, contornos, cena, execução — 13/10/2026).

---

## 0. Por que este tutorial

Parede fina (tubo, chapa, duto) malhada como sólido exige várias células na espessura, e a malha
explode quando há muitos tubos longos. **Shell** = a parede vira **uma camada de células**, com a
espessura como **propriedade**. O STAR resolve a condução **ao longo** da parede e **através** dela
sem malhar a espessura. É o caminho para modelar **muitos tubos finos** em 3D.

## 1. O caso

| item | valor |
|---|---|
| Geometria | sistema de escapamento: tubos de parede fina, **2 entradas** e **4 saídas** |
| Física | gás quente entra pelas entradas e aquece a parede; ar externo em volta |
| Parede | **shell** (camada única de células) |
| Regiões | **3:** ar externo (fluido) · gás de escape (fluido) · parede (*shell region*) |
| Interfaces | **4:** ar ↔ gás (nas saídas) · gás ↔ shell · ar ↔ shell · **hub** shell ↔ shell |
| O que se estuda | distribuição de temperatura ao longo da parede |

Fluxo de trabalho: **CAD no 3D-CAD → limpeza → attached shells → surface wrapper → contatos →
regiões e interfaces → física → malha → solução**.

## 2. Preparar a geometria no 3D-CAD

### 2.1 Diagnóstico
1. *Color Mode* → **Distinguish Bodies** (cada corpo com uma cor).
2. Botão direito no modelo → **Check Validity** → *Output*: "All bodies of model are valid."

### 2.2 Fechar as bocas (entradas e saídas)
1. Selecionar as arestas livres em volta da boca. **Duplo clique numa aresta livre seleciona todas as
   arestas livres conectadas.**
2. Botão direito → **Fill Surface** → OK.
3. Renomear as faces criadas: `Inlet 1`, `Inlet 2`, `Outlet 1`–`Outlet 4`.

### 2.3 Achar corpos que se interpenetram (*clash*)
*Show Filter* → *Selection Mode* = modelo inteiro → *Input Type* = Bodies → condição
**Clash + Body Pair + is + Interference** → *Search*. Resultado em tabela (*Create > Table*) mostra os
pares em conflito.

### 2.4 Fechar uma fresta entre dois corpos (*Bridge Surface*)
Entre os corpos 1 e 3 há uma **fresta**, e parte do corpo 1 **invade** o corpo 3. Receita:
1. *Show Only* nos dois corpos.
2. **Plano de corte:** aresta do corpo 1 → *Reference Geometry > Plane from Curve* (*Fitting Plane*) →
   *Plane by Transformation* com translação em z (−0,095 m) → **Boolean > Slice** do corpo 1
   (*Keep Side = Front*).
3. Segundo plano deslocado (−0,015 m) → *Slice* do corpo 3 (*Keep Side = Back*).
   Os cortes removem a sobreposição e deixam **bordas limpas** dos dois lados.
4. Selecionar as arestas livres dos dois lados da fresta → **Bridge Surface** com *Tangent to Faces*
   (origem e destino) e **Sew Bodies** → OK.
5. *Restore > Hidden Bodies* → *Close 3D-CAD*.

> 💡 **Receita geral de reparo de CAD:** *Check Validity* → fechar bocas (*Fill Surface*) → procurar
> **interferências** (*clash*) → cortar o que se sobrepõe (*Slice*) → ligar as bordas (*Bridge
> Surface* + *Sew*). É a lista do que fazer com CAD de fabricante antes de qualquer malha.

## 3. Attached shells

Um *shell part* tem **duas superfícies — frente e verso** — e cada uma pode receber **condição de
contorno própria**.

1. `3D-CAD Models > Exhaust Pipe > New Geometry Part` → OK.
2. **Bocas como partes "normais"**, não shell (vão virar contornos de escoamento): em cada corpo,
   selecionar a face (`Inlet 1` etc.) → **Create New Part From Surfaces** → renomear.
   (Corpo 1: Inlet 1 · Corpo 4: Outlet 1–2 · Corpo 8: Inlet 2 · Corpo 12: Outlet 3–4.)
3. `Operations > New > Surface Preparation > Attached Shells Creator` → *Input Parts* = todos os
   corpos, *Part Surfaces* = todas → executar.
4. **Volume de ar externo:** `Parts > New Shape Part > Block` de [−2, −1, −1] a [4, 1, 1] m →
   renomear `Fluid Volume` → **Split by Angle** nas superfícies → renomear as faces de entrada e saída
   (`Inlet`, `Outlet`).

## 4. Surface wrapper e contatos

1. **Zip Edges** (costurar as frestas entre shells): partes = todos os *attached shells* + bocas →
   *Zip Mode* = **New Description – Discrete** (o único modo que aceita shells) → *Execute*.
2. **Surface Wrapper (All Parts)** → gera o **volume de ar externo**:
   - partes: shells + `Fluid Volume` + bocas;
   - ligar **Create Weak Contacts With Input Parts** e **Link Output Part Name**;
   - *Base Size* = **0,025 m**;
   - controle customizado para o `Fluid Volume`: alvo **200 %** e mínimo **100 %** do base (ar
     longe do tubo pode ser grosso).
3. **Surface Wrapper (Exhaust)** → gera o **volume de gás interno**: partes = shells + bocas; mesmas
   opções; *Base Size* = **0,02 m**.
4. **Contact Creator** entre os dois wrappers → *Execute*.

> 💡 **Dois wrappers = dois volumes de fluido** a partir da mesma casca: um "por fora" (com o bloco)
> e um "por dentro" (só a casca + bocas). Os **contatos fracos** guardam a informação de quem toca
> quem, que vira interface depois. **Malha fina onde importa** (tubo, 2 cm) e **grossa longe** (ar,
> 5 cm).

## 5. Regiões e interfaces

### Regiões
| região | origem | contornos |
|---|---|---|
| **Fluid** (ar externo) | *Surface Wrapper (All Parts)* → *Set New Region* | `Fluid Wall` (default renomeado) · `Inlet` = **Velocity Inlet** · `Outlet` = **Pressure Outlet** |
| **Exhaust Gas** | *Surface Wrapper (Exhaust)* → *Set Region > New* | `Inlets` (Inlet 1 + 2) = **Mass Flow Inlet** · `Outlets` (Outlet 1–4) = **Wall** |
| **Shells** | `Regions > New > Shell Region` → *Parts* = todos os attached shells | — |

> 💡 **As saídas do gás são "Wall" de propósito:** o gás sai do tubo **para dentro do volume de ar**
> através de uma **interface fluido–fluido**. Não há contorno de saída no tubo — o escoamento continua
> no ar externo. Técnica para jato/descarga num ambiente.

### Interfaces (criadas à mão)
| interface | como | tipo |
|---|---|---|
| **Fluid / Exhaust Gas** | multi-seleção das duas regiões → *Create Interface > Contact-Mode Boundary Interface* → *Contacts*: só os 4 `Outlet` | contato (passagem de escoamento nas saídas) |
| **Fluid / Shells** | idem → *Contacts*: todos | **Mapped Contact Interface** |
| **Exhaust Gas / Shells** | idem → *Contacts*: todos | **Mapped Contact Interface** |
| **Shells / Shells Hub** | `Interfaces > New Hub Interface > Part Entity-Mode` → *Part Entities*: todos os shells | **hub**: troca de calor **entre** as partes de shell |

> 💡 **Mapped Contact** liga fluido e shell mesmo com malhas que não coincidem (o valor é mapeado
> de um lado para o outro). **Hub interface** é o que deixa o calor **conduzir de uma peça de shell
> para a vizinha** — sem ela, cada peça seria uma ilha térmica.

## 6. Malha

Três operações *Automated Mesh*, uma por tipo de volume:

| operação | partes | malhadores | controles |
|---|---|---|---|
| **Automated Mesh (Fluid)** — ar externo | *Surface Wrapper (All Parts)* | Surface Remesher · **Trimmed Cell** (com **Perform Mesh Alignment**) · Prism Layer | base **0,025 m** · **4 prismas**, estiramento **1,3**, espessura total **25 %** do base · controle no `Fluid Volume`: alvo **500 %**, mínimo **300 %** |
| **Automated Mesh (Exhaust)** — gás interno | *Surface Wrapper (Exhaust)* | Surface Remesher · **Polyhedral** · Prism Layer | base **0,02 m** · mesmos prismas |
| **Automated Mesh (Shell)** — parede | todos os *attached shells* | **Quadrilateral Mesher** | base **0,02 m** |

- As duas operações de volume em **Mesher Execution Mode = Parallel** (malham ao mesmo tempo).
- `Mesh > Generate Volume Mesh` → progresso na *Output* → cena de malha para conferir.

> 💡 **Trimmed por fora, poliédrico por dentro.** Trimmed (hexaédrico cortado) é barato e alinhado
> para volume grande e "vazio" (caixa de ar, longe da parede: 12,5 cm). Poliédrico se adapta melhor à
> geometria curva e cheia de ramificações do tubo. **Escolher o malhador pela geometria de cada volume.**

> 💡 **Shell = malha de superfície (quadriláteros), não de volume.** A espessura não é malhada.

## 7. Modelos físicos

Dois contínuos: renomear `Physics 1` → **Fluid** e criar **Solid Shells**. `Regions > Shells >
Physics Continuum = Solid Shells`. **O contínuo Fluid serve às duas regiões de gás** (ar externo e
gás de escape — mesmo material, mesma física).

| contínuo | modelos | inicial |
|---|---|---|
| **Fluid** | 3D · Steady · Gas · **Segregated Flow** · **Ideal Gas** · **Segregated Fluid Temperature** · Turbulent → Realizable k-ε Two-Layer, All y+ | 25 °C · velocidade [1, 0, 0] m/s |
| **Solid Shells** | 3D · Steady · Solid · **Segregated Solid Energy** · Constant Density | 25 °C |

Par de solvers coerente (Segregated ↔ Segregated Solid Energy), como visto no tutorial 04.

**Conferir as ligações entre shells:** cena de geometria → botão direito em
`Interfaces > Shells/Shells Hub > Initialize` → selecionar o nó → as junções entre peças ficam
destacadas.

> ⚠️ **O tutorial não define espessura nem material do shell** — ficam os valores padrão (material
> sólido padrão do STAR e espessura padrão da região). Em projeto real, **definir explicitamente** a
> espessura da parede (valor físico na região de shell) e o material. É o tipo de default que passa
> despercebido e muda o resultado.

## 8. Condições de contorno

| região | fronteira | valores |
|---|---|---|
| Exhaust Gas | **Inlets** (Mass Flow Inlet) | **0,05 kg/s** · **Total Temperature 450 °C** |
| Fluid | **Inlet** (Velocity Inlet) | 25 °C · **1,0 m/s** (vento cruzado) |
| Fluid | Outlet (Pressure Outlet) | 25 °C (só refluxo) |

> 💡 **Régua:** o calor máximo que o gás pode perder é `ṁ·cp·(450 − 25) ≈ 0,05 × 1 003,6 × 425 ≈
> 21 kW` (se saísse à temperatura ambiente; cp constante padrão do STAR para o ar). O calor reportado na parede tem de ficar **abaixo** disso,
> e a temperatura média de saída do gás fecha o balanço: `Q = ṁ·cp·(T_entrada − T_saída)`.

## 9. Cena

*Scalar Scene* → renomear `Shells Temperature` → *Parts* = região **Shells** → vista +Z (Up +Y).
Outline desligado · **Smooth Blended** · Temperature em **°C** · mapa **cool-warm** · ajustar altura
de título e rótulos da barra de cores.

## 10. Execução em paralelo

1. Salvar e fechar → abrir de novo com `File > Load` → **Parallel on Local Host**, **Compute
   Processes = 4** → escolher o `.sim`.
2. `Stopping Criteria > Maximum Steps = 500` → *Run*.

> 💡 O paralelismo é escolhido **ao abrir** o arquivo (número de processos), não dentro da simulação.
> 500 iterações é o limite do tutorial, não um critério de convergência: em caso real, parar por
> **balanço de energia fechado e monitores planos**.

---

## Checklist reaproveitável
- [ ] CAD: *Check Validity* → *Fill Surface* nas bocas → busca de **interferências** → *Slice* +
      *Bridge Surface* (+ *Sew*) nas frestas.
- [ ] Faces que serão contornos de escoamento → partes **normais**, não shell.
- [ ] *Attached Shells Creator* nos corpos de parede fina; lembrar que o shell tem **frente e verso**.
- [ ] *Zip Edges* em modo **New Description – Discrete** antes do wrapper.
- [ ] Um surface wrapper por volume de fluido; contatos fracos ligados; malha fina perto da parede,
      grossa longe.
- [ ] *Contact Creator* entre os wrappers.
- [ ] Interfaces: fluido ↔ shell = **Mapped Contact**; shell ↔ shell = **Hub**; descarga de um fluido
      no outro = interface só nas faces de saída.
- [ ] Malhador por volume: trimmed (caixa grande), poliédrico (geometria complexa), quadriláteros
      (shell); prismas na parede; operações em paralelo.
- [ ] Um contínuo pode servir a várias regiões com a mesma física.
- [ ] *Initialize* a hub interface e conferir as junções na cena.
- [ ] **Definir espessura e material do shell** — não confiar no default.
- [ ] Régua de energia: `ṁ·cp·ΔT` máximo e balanço na saída.
- [ ] **Teste de bancada antes do caso real:** um tubo em shell com condições conhecidas, comparado
      com resistências térmicas em série. Mostra se o shell considera a **diferença entre as áreas
      interna e externa** (no tubo de 25,4 × 2,11 mm, Do/Di = 1,2: ignorar isso erra o calor em 6–9 %;
      corrige-se multiplicando h_i por Di/Dm e h_o por Do/Dm, Dm = diâmetro médio).
