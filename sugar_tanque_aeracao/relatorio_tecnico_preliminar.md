# Relatório Técnico Preliminar — Projeto Sugar (Usina Colombo)

> Resumo técnico consolidado, organizado pelos objetivos do Ito. Status: rodada 1 concluída
> (t=21,2s físicos, caso 1 kgf/cm² do Aerador + Reator acoplado). Torque/Potência/Np FECHADOS;
> SMD do Aerador em banda provisória (falta confirmar estacionariedade); Nq requer rodada
> dedicada em regime permanente. Casos 2 e 3 kgf/cm² pendentes.
> Data: 2026-07-06 (dados da rodada exportados em CSV e processados em Python; conclusões
> submetidas a revisão adversarial independente antes da publicação).

---

## 🟢 REATOR — Objetivo: Potência do agitador (<25kW) + Nq/Np

### Resultados FECHADOS (convergidos, janela t=16–21,3s, n=2185 amostras)

| Item | Valor | Nota técnica |
|---|---|---|
| Geometria do impelidor | Duplo hidrofólio, **3 pás/estágio (6 total)**, Ø800mm, eixo Ø69,85mm | Corrigido em 04/07 a partir do desenho real Agimix AGX-PBW800 |
| Rotação | 109,3 rpm (11,446 rad/s) | Dado real do redutor Macopema MP05 + motor WEG 15cv |
| **Torque (2 estágios)** | **374,31 ± 0,91 N·m** | Deriva entre janelas de 5s: <0,5% e caindo → convergido. (Valor anterior 383,66 era leitura pontual prematura) |
| **Potência** | **4,284 kW** | P = \|T\|×ω. **83% abaixo da meta de 25kW** ✓ |
| **Np total (2 estágios)** | **1,602** | Np = P/(ρN³D⁵) |
| **Np por estágio** | **0,801** | ÷2 é convenção válida para potência (grandeza somada no eixo); assume estágios ~independentes (espaçamento 3,56m = 4,4×D, favorável) |
| **Reynolds do impelidor** | **≈ 242** | Re = ρND²/μ — **regime de TRANSIÇÃO** |

**Sobre a comparação com literatura (leia com o cuidado devido):** o valor turbulento de
catálogo para hidrofólio é Np≈0,8/impelidor (AIChE CEP) — nosso 0,801 coincide notavelmente.
Porém esse benchmark é a **assíntota turbulenta (Re>10⁴)**, e estamos em Re≈242 (transição),
onde Np tipicamente fica **acima** do platô turbulento. A coincidência é encorajadora como
ordem de grandeza, mas não deve ser vendida como "validação exata" — o número defensável é o
do CFD, reportado junto com o Re do regime. Correlações de catálogo não se aplicam com rigor
em transição, o que reforça a necessidade do CFD para esta geometria.

### ⚠️ ERRATA — Nq (corrige versão anterior deste relatório)

A versão anterior reportava "Nq≈1,01 total, ≈0,505 por estágio". **Dois erros identificados
em revisão adversarial:**

1. **O ÷2 do Nq era conceitualmente errado.** Diferente do torque (somado no eixo, 2 estágios),
   o plano de medição de Q é um disco na altura do impelidor **inferior** — mede a descarga de
   **UM** impelidor. O valor já é "por estágio"; dividir por 2 subestimava o Nq por um fator 2.
2. **O Q daquela leitura (e desta rodada inteira) não está convergido.** O torque converge em
   poucas rotações (depende do campo local na pá), mas o Q cresceu monotonicamente a rodada
   inteira (−1,01 m³/s em t=4–6s → −1,75 m³/s em t=18–20s, deriva ~2,6%/s no fim). Torque
   estável + Q subindo prova que o crescimento do Q é o **spin-up da circulação de tanque
   inteiro** (turnover ≈80s; foram simulados 21s) passando fluxo de retorno/entranhamento
   crescente pelo plano — não é bombeamento novo do impelidor. Além disso, um plano no
   **centro** do impelidor integra descarga+entranhamento e tende ao número de **circulação**
   (Nqc ≈ 1,8×Nq para impelidores axiais), inflando o valor vs. o Nq de descarga da literatura.

**Conclusão honesta: o Nq NÃO pode ser finalizado desta rodada transiente.**
Caminho definido para o Nq final: **rodada dedicada do Reator sozinho em MRF regime
permanente** (converge a circulação desenvolvida diretamente, sem spin-up), com:
- plano de medição **logo abaixo** do impelidor, no jato de descarga (não no centerplane);
- sem ÷2;
- benchmark contra dados de **regime de transição** (reportando Re≈242 junto);
- sanity check de balanço de massa (fluxo líquido por um plano de tanque inteiro → 0).

---

## 🟣 AERADOR — Objetivo: distribuição de bolhas + diagnóstico da aeração deficiente + pressão otimizada

**Caso 1: 1 kgf/cm² (98.070 Pa gauge) — rodada de 21,2s físicos concluída**

| Item | Valor | Nota técnica |
|---|---|---|
| Física | EMP (Xarope+Ar) + Phasic Turbulence + S-Gamma (Breakup+Coalescence) + Implicit Unsteady | RANS permanente diverge nesse regime — transiente é obrigatório |
| **Ar entra na boundary?** | **Sim, confirmado** | VF=1,0 no Stagnation Inlet + mancha real de VF na ponta da lança |
| **Dispersão pelo tanque** | **Praticamente nula em 21s** | Sondas de meio/topo em zero numérico a rodada inteira; recirculação longe do jato ~µm/s |
| **SMD perto do injetor** | **PROVISÓRIO: banda 1,4–1,6mm** | Cresceu até crista ~1595µm (t≈17,5s), depois caiu 3s seguidos (queda acelerando: −34/−20/−47 µm/s). Um único ponto de virada em ~13s de registro **não caracteriza estacionariedade** (razão deriva/ruído = 3,0× → sinal ainda dominado por tendência). Confirmar com +5–10s de rodada |
| **% de bolha "boa" (<200µm)** | **1,84×10⁻⁶ % (estável)** | Zero na prática — nenhuma fração relevante do ar em bolhas flotáveis |
| **Holdup de gás** | **0,94 L em 20.170 L (0,005%)** | Ainda acumulando em t=21s (report pontual de Volume de Ar Total) |
| Margem de pressão vs. hidrostática | ~13–14% de folga | Submersão 6,47m → hidrostática ≈85,6 kPa vs. 98,07 kPa configurados |

**Diagnóstico (2 causas simultâneas, mesma raiz física — viscosidade 6,5 Pa·s):**
1. **Bolha ~7× maior que a meta**: coalescência leva o SMD à banda de ~1,5mm perto do injetor
   (meta: <200µm) — nesse tamanho, a bolha é maior que o próprio floco (200–400µm), o que
   desfavorece geometricamente a adesão bolha-floco, essência do processo de flotação.
2. **Sem dispersão**: o jato não gera circulação de tanque; o ar fica confinado à vizinhança
   das lanças.

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
- [ ] Estender caso 1 kgf/cm² +5–10s físicos p/ confirmar banda do SMD (1,4–1,6mm)
- [ ] Rodada dedicada do Reator (steady MRF) p/ Nq final — plano de descarga abaixo do
      impelidor, sem ÷2, benchmark de transição
- [ ] Rodar Aerador a 2 kgf/cm² (mesmo critério de parada)
- [ ] Rodar Aerador a 3 kgf/cm²
- [ ] Comparar os 3 casos e recomendar pressão otimizada
- [ ] Consolidar relatório final
