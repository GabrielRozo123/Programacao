# 05 — Limpeza do CAD da planta: critérios para o modelo CFD

> Etapa 1 do cronograma (geometria). Recebido em 15/10/2026: montagem completa da planta em
> Solid Edge. Este documento define **o que fica, o que sai e o que vira forma simplificada**,
> com base na literatura de CFD atmosférico e de simplificação de CAD.
> Sem layout, coordenadas ou geometria do cliente (ver README) — só método e critérios.

---

## 0. O que recebemos

- A montagem é a **planta inteira**: silos e tanques altos, torres, prédios, estruturas metálicas,
  plataformas, escadas, tubulação, **guindastes** e **estacas de fundação abaixo do solo**.
- O arquivo `.cfg` enviado é a **configuração de exibição** do Solid Edge (quais ocorrências
  aparecem, e um espaço para "zonas"). **Não tem geometria nem nomes de peças.** A geometria está nos
  arquivos de montagem e peça (`.asm` / `.par`).
- Pela estrutura do `.cfg` há da ordem de **40 mil registros de exibição**. Se cada um for uma
  ocorrência, a montagem tem dezenas de milhares de peças. **A limpeza tem de ser feita por regra
  (categoria, tamanho, zona), não peça a peça.**

### 0.1 Segundo envio (19/10/2026) — Parasolid `.x_t` "menor" + imagens do Navisworks

**O `.x_t` não tem geometria.** São 12 kB com só a **árvore da montagem** (≈ 25 componentes) e
nenhuma superfície, aresta ou sólido. O que dá para ler:

| achado | leitura |
|---|---|
| Nomes `#F-C-1219`, `#F-E-1219`, `#F-I-1219`, `#F-M-1213…1216`, `#F-M-1219`, `#RC-1210`, `#RF-1210`, `Building`, `Building_sub_0…7`, `FRMWORK_CANALETAS_ALCALINAS`, `AIDGROUP` | convenção de **AVEVA E3D/PDMS** (FRMWORK, AIDGROUP) → o modelo de origem é de projeto de planta, convertido. O número é a **área** da planta: os exaustores têm tag **1219-24-9x0** → **área 1219 = planta de ozônio** [inferência a confirmar] |
| Uma única translação, de **dezenas de km** em x e y e ~1 km em z | o modelo está em **coordenadas da planta**, longe da origem. O Parasolid só modela dentro de uma caixa de **1 km (±500 m) em torno da origem** (cabeçalho: tamanho 1e3) → geometria fora dela **não é exportada / fica inválida**. **Causa provável do `.x_t` vazio.** |
| `CANALETAS_ALCALINAS` | canaletas no piso → **remover** (categoria 12, §4) |

**Correção (no Solid Edge, antes de exportar):** mover a montagem para que o **prédio de O₃ fique na
origem** (registrar o vetor usado, para voltar às coordenadas da planta depois), conferir a
**unidade** (mm × m) e exportar de novo. Melhor ainda — **filtrar na fonte**: pedir ao cliente uma
exportação do AVEVA/Navisworks só das **áreas em torno da 1219, num raio de ~300 m**, sem tubulação
e sem internos (ver mensagem em `03` §9). O Navisworks *Freedom* é só visualizador — **não exporta
geometria**; a exportação tem de sair do software de projeto.

**Das imagens do Navisworks (Marcus):**
- O prédio de O₃ é um **volume revestido** (caixa alta), colado a vasos verticais altos e a uma área
  coberta com equipamentos e exaustores. Há um **caminhão-tanque** estacionado (veículo → remover).
- **Dentro** há os **misturadores** e a tubulação de alimentação. **Já houve trinca nessa tubulação e
  liberação de O₃**; nesse tipo de vazamento **os exaustores são acionados**. → O cenário de
  vazamento real é **interno**: o O₃ sai para a atmosfera **pelas descargas dos exaustores**. Para o
  CFD externo, o interior do prédio sai inteiro (categoria 3) e a fonte é a **descarga dos
  exaustores** — confirma a §4, item 10, como o detalhe mais importante do modelo.

## 1. O princípio: o nível de detalhe vem da pergunta e da malha

O estudo quer as **concentrações de O₃ junto ao solo** (contornos de 0,2 · 0,5 · 3 ppm, até
~300 m da fonte, `02` §6) e os efeitos que só o CFD captura: **esteira e recirculação do prédio de
O₃, downwash da descarga dos exaustores, canalização entre estruturas** (`02` §8). Daí três regras:

1. **Só entra o que o vento "vê".** O que está enterrado, dentro de equipamentos fechados ou é
   temporário não altera o escoamento externo.
2. **Só entra o que a malha consegue resolver.** Um objeto menor que ~2 células não é representado
   pela malha; ele só cria problema de malha (faces minúsculas, células ruins) sem mudar o resultado.
3. **O detalhe diminui com a distância da fonte.** Perto da fonte, a geometria define a esteira e o
   downwash; longe, só os volumes grandes importam, e o resto pode virar **rugosidade**.

### O que a literatura sustenta

| referência | o que diz | uso aqui |
|---|---|---|
| **COST Action 732** — Franke et al. (2007), *Best Practice Guideline* | domínio dimensionado pela altura do maior prédio **da região de interesse**; razão de bloqueio < 3 % | define o domínio e o "H" de referência (`02` §9.1) |
| **AIJ** — Tominaga et al. (2008), JWEIA 96 | diretrizes para o tamanho da **região de interesse** em torno do prédio-alvo | zona Z0/Z1 |
| Liu et al. (2018), *Building and Environment* | prédios vizinhos mudam muito o escoamento no alvo (**abrigo e canalização**); simplificar demais o entorno altera o resultado. Citado como sugerindo detalhe num raio de **≥ 3× a dimensão do alvo** [a confirmar no texto completo] | raio da zona Z0 |
| **Ricci et al. (2017)**, JWEIA 170, 238–255 | geometria mais detalhada melhorou a concordância com o túnel de vento (FAC1.3 22 % melhor numa direção); estudo associado: **a simplificação geométrica pesa mais que as condições de entrada e o modelo de turbulência** | justifica investir tempo na limpeza e fazer **uma sensibilidade** |
| Pađen, García-Sánchez, Ledoux et al. (2022), *Frontiers in Built Environment*; TU Delft (City4CFD) | **dentro da área de interesse** os prédios são reconstruídos explicitamente; **fora**, a geometria é parametrizada (rugosidade). Níveis de detalhe LoD1 (prisma de teto plano) → LoD2 (forma do telhado) | zonas Z1/Z2 |
| **Thakur, Banerjee & Gupta (2009)**, *Computer-Aided Design* 41(2), 65–80 | taxonomia de simplificação de CAD para simulação: operadores de **superfície**, de **volume**, de **feições explícitas** (furos, arredondamentos) e de **redução de dimensão**; toda simplificação gera um **"erro de defeaturing"** | vocabulário e checklist da limpeza |
| Método **PDR** (porosidade / resistência distribuída) — FLACS; Hanna et al. (avaliação do FLACS, MUST/Kit Fox) | obstáculos **menores que a célula** entram como **porosidade + arrasto + geração de turbulência**, não como geometria | racks de tubulação e estruturas treliçadas |
| Ahmed et al. (2016), *J. Loss Prev. Process Ind.* | abordagem **híbrida**: objetos médios e grandes com malha ajustada ao corpo; **aglomerados de objetos pequenos → bloco poroso**; validada em escala real (Spadeadam) | exatamente a nossa estratégia para racks |
| Hanna, Hansen, Ichard & Strimaitis (2009), *Atmos. Environ.* 43(2), 262–270 | CFD (FLACS) em sítio **industrial**: as estruturas retêm gás nas esteiras e mudam a dispersão perto da fonte | por que o campo próximo precisa das estruturas |

> **Limitação honesta:** as diretrizes (COST, AIJ) não trazem uma lista do tipo "remova peças menores
> que X mm". Os **limiares numéricos** da §3 são **critério nosso**, derivado da resolução da malha e
> das regras acima — e serão **verificados** pela sensibilidade da §6.

## 2. Zonas de detalhe (concêntricas, em torno do prédio de O₃)

Como são 6 cenários de vento em direções diferentes, as zonas são **círculos** em torno da fonte,
não retângulos a jusante.

| zona | extensão | nível de detalhe | o que representa |
|---|---|---|---|
| **Z0 — fonte** | prédio de O₃ + vizinhos num raio de **~3H** (H = altura do prédio de O₃; com 15–20 m → **~50–60 m**) | **alto (≈ LoD2)**: forma do telhado, platibandas, casas de máquinas, **dutos e bocais de descarga dos exaustores com direção, altura e área reais**, aberturas relevantes | esteira, recirculação, downwash, campo próximo dos jatos |
| **Z1 — região de interesse** | até **~300 m** (alcance do contorno de 0,2 ppm, `02` §6) | **médio (≈ LoD1)**: prédios como caixas, silos/tanques/torres como cilindros, racks densos como **blocos porosos** | canalização, abrigo, esteiras dos grandes volumes |
| **Z2 — entorno** | de ~300 m até a borda do domínio (5H montante, 15H jusante — COST) | **baixo**: só volumes grandes como caixas/cilindros, ou **nada** (vira **rugosidade z₀** no solo e no perfil de entrada) | condição de chegada do vento |

## 3. Critério de tamanho (ligado à malha)

Tamanho de célula **previsto** [estimativa — confirmar quando a malha for montada]: Z0 ~0,5 m ·
Z1 ~1–2 m · Z2 ~4–8 m. Regra, com `d` = maior dimensão do objeto e `Δ` = célula local:

| condição | ação |
|---|---|
| `d < 2Δ` | **remover** (isolado) — ou incluir no bloco poroso se fizer parte de um aglomerado |
| `2Δ ≤ d < 10Δ` | **substituir por primitiva** (caixa ou cilindro envolvente) |
| `d ≥ 10Δ` | **manter a forma** (simplificada: sem furos, arredondamentos, chanfros, flanges) |

Limiares resultantes (arredondados):

| zona | remover se menor que | primitiva até | forma mantida acima de |
|---|---|---|---|
| Z0 | **~1 m** | ~5 m | ~5 m |
| Z1 | **~3 m** | ~15 m | ~15 m |
| Z2 | **~10 m** | — | só volumes grandes |

## 4. Critério por categoria (vale em todas as zonas)

| # | categoria | ação | por quê |
|---|---|---|---|
| 1 | **Abaixo do solo**: estacas, blocos de fundação, tubulação enterrada, poços | **remover tudo** | não há ar |
| 2 | **Temporários**: guindastes, andaimes, veículos, contêineres de obra | **remover** [confirmar com o cliente que são de montagem] | não são da planta em operação; lança treliçada é transparente ao vento |
| 3 | **Internos** de equipamentos fechados (tanques, silos, torres, prédios) | **remover** — manter só a casca externa | o vento não entra |
| 4 | **Acessórios pequenos**: guarda-corpos, escadas, grades de piso, eletrocalhas, válvulas, flanges, instrumentos, suportes, parafusos, bocais pequenos | **remover** | abaixo do limiar de tamanho em qualquer zona |
| 5 | **Tubulação isolada** | **remover** (diâmetros típicos < limiar) | sub-malha |
| 6 | **Rack de tubulação denso / feixe de dutos** | **bloco poroso** com resistência de arrasto (§5) | aglomerado bloqueia o vento, mas cada tubo é sub-malha (PDR / Ahmed et al.) |
| 7 | **Estrutura treliçada aberta** (pórticos, torres de escada, plataformas) | **remover** se aberta; **bloco poroso** se muito densa; **sólido** se tiver fechamento lateral | o que conta é a área frontal bloqueada |
| 8 | **Silos, tanques, torres, chaminés** | **cilindro** (teto cônico se o cone for grande); sem bocais, escadas ou anéis | volumes que fazem esteira |
| 9 | **Prédios** | **caixa** (LoD1); em Z0, forma do telhado e volumes de cobertura (LoD2) | idem |
| 10 | **Exaustores do prédio de O₃ (fontes)** | **manter com detalhe**: posição, altura, direção e área da descarga | são as condições de contorno do estudo (`04` §1.2) |
| 11 | **Tomadas de ar de HVAC e áreas ocupadas** | **marcar** (superfície nomeada), mesmo pequenas | são **receptores** — onde medir a concentração |
| 12 | **Solo** | plano (ou topografia, se vier), sem meio-fios, canaletas, bases pequenas | rugosidade real entra pelo z₀ (`02` §9.3) |

## 5. Bloco poroso para racks e estruturas densas

Mesma ferramenta do tutorial STAR 06 (`star_ccm_tutoriais/06_Porous_Resistance_Isotropic.md`):
região porosa com resistência **inercial** de arrasto de dossel,

```
P_i ≈ ½ · ρ · C_D · a          [kg/m⁴]        P_v ≈ 0
a   = área frontal dos tubos/perfis por unidade de volume do bloco   [m⁻¹]
C_D ≈ 1,0–1,2 (cilindros e perfis)
```

Ex.: rack com 20 tubos de 0,2 m de diâmetro numa seção de 6 m × 4 m: a ≈ 20·0,2/(6·4) ≈ 0,17 m⁻¹ →
P_i ≈ ½·1,2·1,0·0,17 ≈ **0,10 kg/m⁴**. Resistência **direcional** se o rack for alongado (menor ao
longo dos tubos). Se a área frontal do aglomerado for pequena frente ao entorno, **remover**.

## 6. Como verificar que a limpeza não mudou o resultado

1. **Contagem**: corpos antes × depois, por categoria — vira tabela de rastreabilidade do relatório.
2. **Área frontal por direção de vento** (projeção) em Z1, antes × depois: mudança **< ~10 %**
   [critério nosso]. Fora disso, algo grande foi removido por engano.
3. **Uma sensibilidade de geometria** (Ricci et al. 2017 mostram que é o que mais pesa): um cenário de
   vento rodado com Z1 "limpo" e com Z1 "mais detalhado"; comparar a concentração nos receptores.
4. **Volume fechado e sem interferências** antes de exportar (*Check Validity* / busca de
   interferências — tutorial STAR 05) — o *surface wrapper* do STAR fecha frestas pequenas, mas não
   deve ser usado para "consertar" uma montagem de dezenas de milhares de peças.

## 7. Fluxo de trabalho no Solid Edge (Gabriel + Otávio)

1. **Trabalhar sobre cópia** da montagem; o original fica intacto para consulta.
2. **Identificar primeiro:** o prédio de O₃ e os 4 exaustores (tags 1219-24-910/920/930/940). Daí
   saem o centro e os raios das zonas.
3. **Remoções em massa por categoria** (§4, itens 1–5): primeiro tudo abaixo da cota do solo, os
   guindastes e os internos. É aqui que cai a maior parte das peças.
4. **Selecionar por zona**: o `.cfg` tem um espaço para **zonas** — o Solid Edge permite definir
   regiões (caixas) para mostrar/selecionar só as peças dentro delas [conferir o comando na versão de
   vocês]. Criar Z0 e Z1.
5. **Selecionar por nome/propriedade** (busca no PathFinder: "ESTACA", "GUARDA", "ESCADA", "GRADE",
   "VÁLVULA", "FLANGE"...) — depende da nomenclatura do cliente.
6. **Simplificar** o que fica: remover furos, arredondamentos e chanfros; ou desenhar a primitiva
   envolvente (caixa/cilindro) por cima e apagar o detalhado.
7. **Nova configuração de exibição "CFD"** para registrar o que ficou visível.
8. **Exportar** em **Parasolid (.x_t)** ou STEP. O 3D-CAD do STAR lida bem com Parasolid.
9. **No STAR:** *Check Validity*, busca de interferências, wrapper com tamanho mínimo por zona
   (tutorial 05), conferir unidades na importação (*Mesh > Diagnostics*).

> 💡 **Atalho que acelera muito:** exportar a **lista de peças (BOM)** da montagem para Excel — nome,
> quantidade e, se possível, massa ou dimensões. Com ela, monto um script que **classifica as peças
> pelas regras das §3–4** e devolve a lista do que apagar, por categoria.

---

### 7.1 Roteiro prático no Solid Edge (montagem aberta em 19/10)
A montagem abre com os sólidos. Árvore de topo: `#F-C-1219`, `#F-E-1219`, `#F-I-1219`,
`#F-M-1213…1216`, `#F-M-1219`, `#RC-1210`, `#RF-1210` (cada uma com `Building.asm` dentro).

0. **Cópia da pasta inteira** no Windows Explorer antes de mexer (apagar dentro de subconjunto
   regrava o `.asm` do subconjunto).
1. **Inventário:** no PathFinder, desligar o olho de **um** subconjunto por vez e anotar o que some
   (palpite a confirmar: C = civil/estrutura, E = elétrica, I = instrumentação, M = mecânica/equipamentos
   e tubulação; o número é a área).
2. **Ocultar ≠ apagar:** primeiro **ocultar** o que sai (olho), conferir a vista, só depois apagar
   (selecionar no PathFinder → *Delete*). Apagar uma ocorrência **não** apaga o arquivo da peça.
3. **Achar por nome:** caixa *Type to find components* do PathFinder.
4. **Medir:** aba *Inspect* → medir altura do prédio de O₃ e distâncias (define H e as zonas).
5. **Exportar em STEP** (*Save As* → STEP) em vez de `.x_t`: o STEP não tem a caixa de 1 km do
   Parasolid. A translação para perto da origem pode ser feita depois, no STAR. Se algum componente
   estiver **inativo** (ícone apagado), ativar antes de exportar — inativo não é exportado.

## Referências
- Franke, J. et al. (2007). *Best Practice Guideline for the CFD Simulation of Flows in the Urban
  Environment* — COST Action 732.
- Tominaga, Y. et al. (2008). AIJ guidelines for practical applications of CFD to pedestrian wind
  environment around buildings. *J. Wind Eng. Ind. Aerodyn.* 96, 1749–1761.
- Liu, S. et al. (2018). Influence of surrounding buildings on wind flow around a building predicted
  by CFD simulations. *Building and Environment*.
- Ricci, A. et al. (2017). Local-scale forcing effects on wind flows in an urban environment: impact
  of geometrical simplifications. *J. Wind Eng. Ind. Aerodyn.* 170, 238–255.
- Pađen, I., García-Sánchez, C., Ledoux, H. (2022). Towards automatic reconstruction of 3D city
  models tailored for urban flow simulations. *Frontiers in Built Environment* 8:899332.
- Biljecki, F., Ledoux, H., Stoter, J. (2016). An improved LOD specification for 3D building models.
  *Computers, Environment and Urban Systems*.
- Thakur, A., Banerjee, A.G., Gupta, S.K. (2009). A survey of CAD model simplification techniques for
  physics-based simulation applications. *Computer-Aided Design* 41(2), 65–80.
- Ahmed, K. et al. (2016). Body-fitted grids with porous blockage for congested process geometries
  (Spadeadam validation). *J. Loss Prev. Process Ind.* [título exato a conferir]
- Hanna, S.R., Hansen, O.R., Ichard, M., Strimaitis, D. (2009). CFD model simulation of dispersion
  from chlorine railcar releases in industrial and urban areas. *Atmos. Environ.* 43(2), 262–270.
- Hanna, S.R., Hansen, O.R., Dharmavaram, S. (2004). FLACS CFD air quality model performance
  evaluation with Kit Fox, MUST, Prairie Grass, and EMU observations. *Atmos. Environ.* 38.
- Blocken, B. (2015). Computational Fluid Dynamics for urban physics: importance, scales,
  possibilities, limitations and ten tips and tricks. *Building and Environment* 91, 219–245.
