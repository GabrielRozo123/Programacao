# Relatório Técnico Preliminar — Projeto Sugar (Usina Colombo)

> Resumo técnico consolidado, organizado pelos objetivos do Ito. Status: **REATOR 100% FECHADO**
> (torque/potência/Np/Nq finais via rodada dedicada steady MRF). **AERADOR caso 1 (1 kgf/cm²)
> CARACTERIZADO** (distribuição de bolha do campo desenvolvido); casos 2 e 3 kgf/cm² pendentes.
> Data: 2026-07-07 (dados exportados em CSV e processados em Python; conclusões submetidas a
> revisão adversarial independente antes da publicação).

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

**Caso 1: 1 kgf/cm² (98.070 Pa gauge) — ✅ CARACTERIZADO (rodada de ~31s físicos, campo desenvolvido)**

| Item | Valor | Nota técnica |
|---|---|---|
| Física | EMP (Xarope+Ar) + Phasic Turbulence + S-Gamma (Breakup+Coalescence) + Implicit Unsteady | RANS permanente diverge nesse regime — transiente é obrigatório |
| **Ar entra na boundary?** | **Sim, confirmado** | VF=1,0 no Stagnation Inlet + mancha real de VF na ponta da lança |
| **Dispersão pelo tanque** | **Praticamente nula** | Sondas de meio/topo em zero numérico a rodada inteira; recirculação longe do jato ~µm/s; ar confinado à vizinhança das lanças |
| **SMD — distribuição do domínio** (ponderada por VF de Ar) | **média 2,39 mm · moda/mediana 2,16 mm · D10–D90 1,67–3,16 mm** | Distribuição madura (histograma). A bolha nasce ~1,5mm na boca do injetor e **cresce por coalescência** para ~2,4mm no volume |
| **Fração < 200µm (a meta)** | **≈ 0% (0,000000%)** | Confirmado pelo histograma e pelo report `Percentual_Bolha_Flotavel` (~3,4×10⁻⁶%) |
| **Holdup de gás** | **~0,94 L em 20.170 L (0,005%)** | Ar confinado à região dos injetores |
| Margem de pressão vs. hidrostática | ~13–14% de folga | Submersão 6,47m → hidrostática ≈85,6 kPa vs. 98,07 kPa configurados |

**Diagnóstico (2 causas simultâneas, mesma raiz física — viscosidade 6,5 Pa·s):**
1. **Bolha ~8× maior que a meta E que o floco.** A bolha típica (~2,4mm) é ~8× a meta de 200µm
   e, criticamente, ~8× maior que o próprio floco (200–400µm). O kick-off do Ito definiu que
   *"a bolha deve ser menor que o floco"* para grudar e flotar — aqui é o oposto, o que inviabiliza
   geometricamente a adesão bolha-floco (essência da flotação).
2. **Sem dispersão**: o jato não gera circulação de tanque; o ar fica confinado à vizinhança
   das lanças, sem varrer o volume onde estão os flocos.

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
- [ ] Rodar Aerador a 2 kgf/cm² (196.130 Pa · Clear Solution, só multifásico, mesmo critério)
- [ ] Rodar Aerador a 3 kgf/cm² (294.200 Pa)
- [ ] Comparar os 3 casos e recomendar pressão otimizada
- [ ] Consolidar relatório final
