# Relatório Técnico Preliminar — Projeto Sugar (Usina Colombo)

> Resumo técnico consolidado, organizado pelos objetivos do Ito. Status: **REATOR 100% FECHADO**
> (torque/potência/Np/Nq finais via rodada dedicada steady MRF). **AERADOR: comparação de pressão
> 1 vs 2 kgf/cm² feita** (caso 2 provisório, não estacionário) → conclusão: **pressão não é a
> alavanca; o gargalo é breakup suprimido pela viscosidade (6,5 Pa·s)**. Caso 3 de baixa prioridade.
> Data: 2026-07-08 (dados exportados em CSV e processados em Python; conclusões submetidas a
> revisão adversarial independente — 4 lentes + crítico de completude — antes da publicação).

---

## 🟢 REATOR — Objetivo: Potência do agitador (<25kW) + Nq/Np — ✅ FECHADO

### Resultados FINAIS (rodada dedicada em MRF regime permanente, convergida — iter 2320)

| Item | Valor | Nota técnica |
|---|---|---|
| Geometria do impelidor | Duplo hidrofólio, **3 pás/estágio (6 total)**, Ø800mm, eixo Ø69,85mm | Corrigido em 04/07 a partir do desenho real Agimix AGX-PBW800 |
| Rotação | 109,3 rpm (11,446 rad/s) | Dado real do redutor Macopema MP05 + motor WEG 15cv |
| **Torque (2 estágios)** | **355,66 N·m** | Steady convergido (achatado desde ~iter 200) |
| **Potência** | **4,07 kW** | P = \|T\|×ω. **84% abaixo da meta de 25kW** ✓ |
| **Np total (2 estágios)** | **1,522** | Np = P/(ρN³D⁵) |
| **Np por estágio** | **0,76** | ÷2 válido para potência (grandeza somada no eixo); estágios ~independentes (espaçamento 3,56m = 4,4×D) |
| **Nq (número de vazão)** | **0,345** | Nq = \|Q\|/(ND³), Q=−0,321 m³/s no plano de descarga (z=−4,50, r≤0,4). **Sem ÷2** — plano mede 1 impelidor |
| **Reynolds do impelidor** | **≈ 242** | Re = ρND²/μ — **regime de TRANSIÇÃO** |

**Coerência do torque (3 determinações independentes):** transiente limpo (15-20s) = −374 N·m
(Np/est 0,80); steady iter 547 = −360 N·m (0,77); **steady final = −356 N·m (0,76)**. Os três
convergem dentro de ~5% — a potência (~4,1 kW) e o Np (~0,76-0,80) são sólidos. O valor steady
final é o definitivo (totalmente convergido, sem sensibilidade de passo de tempo).

**Posicionamento físico do Nq:** cai **entre o laminar (Nq~0,214) e o turbulento (0,55-0,73)** —
exatamente onde um número de vazão em Re≈242 (transição) deve estar. Não é um valor de catálogo;
é o valor real desta geometria neste regime, que só o CFD entrega.

**Sobre o Np vs literatura (com o cuidado devido):** o valor turbulento de catálogo para
hidrofólio é Np≈0,8/impelidor (AIChE CEP) — nosso 0,76-0,80 fica na mesma ordem. Mas esse
benchmark é a assíntota turbulenta (Re>10⁴); em Re≈242 (transição) Np tipicamente fica acima do
platô turbulento. A proximidade é encorajadora, não uma "validação exata" — o número defensável
é o do CFD, reportado junto com o Re.

### Notas metodológicas (correções aplicadas em revisão adversarial)

- **Nq NÃO é dividido por 2** (errata de versão anterior): diferente do torque (somado no eixo),
  o plano de medição é um disco na altura de UM impelidor — o valor já é "por estágio".
- **O Nq exigiu rodada dedicada em regime permanente.** Na rodada transiente acoplada, o Q não
  convergia (crescia com o spin-up da circulação de tanque inteiro, turnover ≈80s), enquanto o
  torque já estava estável. O steady MRF converge a circulação desenvolvida diretamente.
- **Plano de descarga** posicionado logo abaixo do impelidor (z=−4,50, ~0,25×D abaixo do centro),
  não no centerplane (que integra descarga+entranhamento e infla o valor rumo ao nº de circulação).

---

## 🟣 AERADOR — Objetivo: distribuição de bolhas + diagnóstico da aeração deficiente + pressão otimizada

**Metodologia (comum aos casos de pressão):** EMP (Xarope+Ar) + Phasic Turbulence + S-Gamma
(breakup+coalescência) + Implicit Unsteady. Produção a **Δt=0,01s, 1ª ordem no tempo** (arranque
a 0,001s p/ absorver o impulso da nova pressão, depois rampa até 0,01s). O **SMD do domínio** é a
média ponderada por VF de ar (histograma). Ar confirmado entrando (VF=1,0 no Stagnation Inlet).

**Comparação de pressão — 1 vs 2 kgf/cm²**

| Métrica | Caso 1 · 1 kgf/cm² (98.070 Pa) | Caso 2 · 2 kgf/cm² (196.130 Pa) | Leitura |
|---|---|---|---|
| Estado | ✅ convergido (~31s) | ⚠️ **provisório** (~38s; perto-injetor ainda caía −16µm/s) | caso 2 não estacionário |
| SMD médio (domínio) | 2,392 mm | 2,437 mm *(indicativo)* | ~igual (+1,9%, dentro da incerteza) |
| Moda / mediana | 2,165 / 2,165 mm | 1,864 / 2,235 mm | pico desce |
| **D10 (ponta pequena)** | 1,669 mm | **1,492 mm** | pressão empurra a ponta pequena p/ baixo |
| D90 (cauda grande) | 3,156 mm | 3,534 mm | cauda engorda |
| Desvio-padrão | 0,581 mm | 0,784 mm | distribuição alarga (+35%) |
| **Fração <200µm (meta)** | **≈0%** | **≈0%** (1,26×10⁻⁶%, estável) | métrica-chave já convergida nos dois |
| Dispersão (meio/topo) | nula | nula | ar confinado aos injetores nos dois |

**O que a pressão faz e não faz:** entre 1 e 2 kgf/cm² a distribuição **se reestrutura** — a ponta
pequena desce (D10 e moda caem) e a cauda grande engorda (D90 sobe), **sem deslocar a média nem
gerar fração flotável resolvível**. Mais pressão dá mais quebra na formação, mas não fecha o gap de
ordem de grandeza até a meta. *(A leitura correta pro objetivo é a **cauda <200µm / D10**, não a
média — flotação depende da ponta pequena.)*

**Diagnóstico — causa-raiz (revisado após verificação adversarial):**
1. **Bolha ~12× a meta.** A bolha típica (~2,4mm) é **~12× a meta de 200µm** e **~6–12× o floco
   (200–400µm)**; até o D10 (~1,5mm) é ~7–8× a meta. Requisito do Ito: bolha **menor** que o floco
   para aderir e flotar — aqui é o oposto, o que inviabiliza geometricamente a adesão bolha-floco.
2. **O gargalo é breakup SUPRIMIDO, não coalescência.** A viscosidade de 6,5 Pa·s **resiste à
   deformação da interface** (exige cisalhamento/Weber muito maior para quebrar) e o bulk tem baixa
   turbulência — a bolha fica travada no tamanho de formação do orifício. *(A viscosidade, aliás,
   **inibe** coalescência via drenagem lenta de filme; o tamanho grande vem da falta de quebra, não
   do excesso de fusão — correção de uma versão anterior deste relatório.)*
3. **Sem dispersão.** Em 6,5 Pa·s o Re da pluma é baixíssimo: o jato não gera circulação de tanque
   e o ar fica confinado aos injetores, sem varrer o volume onde estão os flocos.

**Conclusão da comparação de pressão:** **a pressão de injeção NÃO é a alavanca.** Dobrar 1→2 kgf/cm²
não muda o essencial (bolha ~2,4mm, flotável ~0%, sem dispersão). A alavanca física real é **(a)
reduzir a viscosidade** (temperatura/diluição do xarope) e/ou **(b) aumentar o cisalhamento na
formação** (geometria do injetor / venturi). O caso 3 (3 kgf/cm²) é de baixa prioridade — extrapola
o mesmo comportamento sem fechar o gap.

**Ressalvas (rigor técnico):** caso 2 provisório (não estacionário — deltas finos são indicativos);
Δt=0,01s + 1ª ordem **sem estudo de convergência em passo de tempo**; resolução de malha near-injector
a verificar (o SMD do S-Gamma é contínuo, mas os termos-fonte de breakup são mesh-sensíveis); "sem
dispersão" observado até a parada (a pluma precisaria subir ~6,47m, especialmente no caso 2 ainda em
desenvolvimento).

### Cálculos analíticos — tempo de subida por empuxo (Bird, Armstrong & Hassager, Ex. 1.4-2)

Para bolha de gás (superfície móvel, V=(1/3)ρgR²/μ) em xarope Newtoniano (ρ=1350, μ=6,5):

| Diâmetro | V de subida | Tempo p/ subir 6,47m |
|---|---|---|
| 200 µm (meta de projeto) | 0,0068 mm/s | **≈265 h ≈ 11 dias** |
| 1,0 mm | 0,17 mm/s | ≈10,6 h |
| **1,5 mm (banda medida no CFD)** | **0,37 mm/s** | **≈4,8 h** |
| 2,0 mm | 0,68 mm/s | ≈2,6 h |
| 3,0 mm | 1,53 mm/s | ≈1,2 h |

**Achado central para o Ito:** mesmo que o ejetor produzisse perfeitamente as microbolhas de
200µm do projeto, elas levariam **~11 dias** para subir o tanque por empuxo próprio neste
xarope. Microbolha em meio de 65 poise **não flota sozinha** — o processo depende
inteiramente de (a) adesão ao floco e (b) transporte convectivo (circulação), que a 1 kgf/cm²
é praticamente inexistente. A "aeração deficiente" observada em campo tem **causa estrutural
na viscosidade**, não apenas operacional — e é quantificável: qualquer solução precisa atacar
transporte (circulação/vazão de ar) e não apenas o tamanho de bolha.

**Cross-check de consistência física** (mesma ref., §2.6): fenômenos como bolha em "lágrima"
e esteira negativa são exclusivos de fluidos viscoelásticos e **não devem aparecer** no xarope
Newtoniano — se vídeo real da planta mostrar esses formatos, revisitar a hipótese reológica
da suspensão floco+xarope.

**Pendente:** casos de **2 kgf/cm² (196.130 Pa)** e **3 kgf/cm² (294.200 Pa)**. Expectativa
(a confirmar): folga sobre a hidrostática de ~129% e ~244% → mais quantidade de movimento no
jato → melhor dispersão e possivelmente menor coalescência local. A comparação dos 3 casos
fundamenta a recomendação de pressão otimizada.

---

## 🔗 Achado unificador — o mesmo fator explica os dois tanques

O Reynolds do impelidor do Reator (~242, transição) e o comportamento do Aerador (jato
laminarizado, sem dispersão, coalescência dominante) derivam da **mesma viscosidade de
6,5 Pa·s**. Nenhum dos dois tanques poderia ser dimensionado com confiança por correlação de
catálogo — em transição as correlações não se aplicam, e o CFD é a fonte primária dos números.

---

## Metodologia de parada (alinhada com gerência em 06/07)

- **Inviável** esperar a dispersão completa via CFD direto: à taxa observada (~3,3–4,0 h de
  máquina por segundo físico), simular as ~2,6–265h físicas de subida de bolha levaria de
  **meses a anos** de computação contínua — não é critério de parada viável.
- **Critério adotado por caso**: rodar até a região do injetor atingir estacionariedade
  estatística (SMD parar de derivar sistematicamente), fechando a caracterização local via
  CFD; completar o transporte/flotação com o **cálculo analítico ancorado no SMD convergido**
  (tabela acima). Mesma lógica nos 3 casos de pressão → comparação justa.

## Próximos passos
- [x] Rodada dedicada do Reator (steady MRF) p/ Nq final → **Nq=0,345, Np/est=0,76, P=4,07 kW**
- [x] Caso 1 kgf/cm² caracterizado → **SMD médio 2,39mm, <200µm ≈ 0%**
- [x] Caso 2 kgf/cm² (provisório) + comparação 1×2 → **pressão não muda o essencial**
- [ ] **Convergir o caso 2** (rodar até o probe perto-injetor achatar) p/ fechar os deltas finos
- [ ] (Baixa prioridade) Caso 3 a 3 kgf/cm² — só se exigirem os 3 pontos, com dt fino
- [ ] **Alavanca real**: estudar redução de viscosidade (temperatura/diluição) e/ou geometria do injetor
- [ ] Verificar resolução de malha near-injector (piso do breakup) e convergência em Δt
- [ ] Consolidar relatório final
