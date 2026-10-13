# Tutorial 02 — Eulerian: Wall Boiling

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: 🟡 seções 1–5 lidas (visão geral, User Field Functions, Physics Models, Phases, Phase
> Interactions — 13/10/2026). Restante a receber.

---

## 0. Por que este tutorial

O tutorial 01 ensinou o **acoplamento** (CHT + RPI). Este ensina o **RPI sozinho, bem validado**:
um tubo aquecido com dados experimentais clássicos, montado inteiro com **Field Functions
parametrizadas**. É o tutorial para aprender a *confiar* (ou não) no modelo de ebulição na parede.

## 1. O caso — Bartolomei (1967), 45 bar

| item | valor |
|---|---|
| Geometria | tubo vertical, **D = 15,4 mm**, trecho aquecido **L = 2,0 m** |
| Trechos não aquecidos | *leader* (antes) e *trailer* (depois) — escoamento desenvolvido e saída limpa |
| Pressão | **45 bar** (Tsat = 530,59 K = 257,4 °C) |
| Fluxo de calor na parede | **q″ = 570 kW/m²** (imposto) |
| Fluxo mássico | **G = 900 kg/m²·s** |
| Temperatura de entrada | **470,63 K** → **60 K de sub-resfriamento** |
| Regime | ebulição **sub-resfriada** → início da saturada perto da saída |

**Conceitos que o tutorial usa:**
- **IB (*Incipient Boiling*)** — primeira bolha na parede (parede acima de Tsat, líquido ainda frio).
- **NVG / OSV (*Net Vapor Generation* / *Onset of Significant Void*)** — ponto em que as bolhas
  deixam de recondensar logo após se desprenderem e a fração de vazio começa a crescer de fato.
- Entre IB e NVG: vapor só colado à parede; depois do NVG: vazio cresce rápido mesmo com o líquido
  médio ainda sub-resfriado.

**Validação declarada:** a série de Bartolomei cobre **30–150 bar**; a concordância do STAR é
descrita como *"adequada, não boa"*.

> 💡 **Leitura de engenharia:** o erro típico do RPI está em **alguns kelvin de superaquecimento de
> parede** e na posição do NVG. Isso é pequeno quando o efeito que se quer medir é grande (ex.: parede
> **molhada × seca**, dezenas de kelvin) e é grande quando se quer prever a fração de vazio local
> com precisão. **Usar o RPI para diferenças grosseiras de regime, não para detalhes finos de vazio.**

### A régua deste caso (calculada com CoolProp, IAPWS-IF97)

Balanço de energia 1D antes de rodar — o resultado do STAR tem de bater com isso:

| grandeza | valor |
|---|---|
| h_fg a 45 bar | 1 675,7 kJ/kg |
| Título de equilíbrio na entrada | **x_in = −0,167** (pela entalpia) |
| Velocidade de entrada | **1,035 m/s** (ρ = 869,8 kg/m³ a 470,63 K e 45 bar) |
| dx/dz = 4q″/(G·h_fg·D) | 0,0982 m⁻¹ |
| **x = 0 (líquido médio saturado)** | **z ≈ 1,70 m** (de 2,0 m aquecidos) |
| Título de equilíbrio na saída | **x_out ≈ +0,029** |
| **OSV (Saha-Zuber, Pe = 1,1×10⁵)** | ΔT_sub,OSV ≈ 19,7 K → **z ≈ 1,11 m** |

Temperatura média do líquido (monofásico equivalente): 488,9 K em 0,5 m · 506,6 K em 1,0 m ·
523,8 K em 1,5 m · Tsat em 1,70 m.

> ⚠️ **Discrepância a conferir:** o tutorial usa **InletDensity = 832,06 kg/m³**, mas a IAPWS dá
> **869,8 kg/m³** a 470,63 K e 45 bar (832,06 corresponde a ~500,7 K). Como a velocidade de entrada é
> calculada como G/ρ, isso muda a velocidade em ~4,5 % — **mas não muda a vazão mássica** se a
> densidade do líquido no material for a mesma 832,06 (G = ρ·v se conserva). Conferir quando chegar
> a seção de propriedades dos materiais. **Lição:** a densidade usada para converter G em velocidade
> tem de ser **a mesma** que o material usa, senão a vazão mássica imposta sai errada.

> 💡 O título de entrada depende da fórmula: o tutorial usa `cp·(T_in − Tsat)/h_fg` com cp constante
> (dá −0,160 com cp na entrada e −0,177 com cp na saturação); o exato pela entalpia é **−0,167**.
> Para a régua, **usar entalpias** (CoolProp), não cp constante.

## 2. User Field Functions — o caso inteiro parametrizado

O tutorial cria as funções por **macro Java** (`wb_setupFieldFunctions.java`), em três grupos.
**Técnica a copiar em todo projeto:** os parâmetros do caso viram Field Functions escalares e todo o
resto (contornos, fontes, pós) referencia esses nomes. Mudar de cenário = mudar um número.

### 2.1 Parâmetros do caso
| Field Function | valor / expressão |
|---|---|
| `EquivalentDiameter` | 0,0154 m |
| `HeatedLength` | 2,0 m |
| `SystemPressure` | 4,5×10⁶ Pa |
| `SaturationTemperature` | 530,59 K |
| `InletDensity` | 832,06 kg/m³ (ver discrepância acima) |
| `InletMassFlux` | 900 kg/m²·s |
| `InletTemperature` | 470,63 K |
| `InletVelocity` (vetor) | `[$InletMassFlux/$InletDensity, 0, 0]` |
| `WallHeatFlux` | 570 000 W/m² |

### 2.2 Funções do modelo
| Field Function | o que faz |
|---|---|
| `IterationsToFullPower` | 200 |
| `WallHeatFluxDistribution` | `($$Centroid[0] > 0 && $$Centroid[0] < $HeatedLength) ? $WallHeatFlux : 0.0` → aquece só o trecho de 0 a L; *leader* e *trailer* ficam adiabáticos **na mesma fronteira** |
| `WallHeatFluxIterationRamp` | rampa linear do fluxo de 0 a 100 % nas primeiras 200 iterações |
| `dMax`, `dMin` | 0,012 m e 1×10⁻⁶ m — limites do diâmetro de bolha |
| `ClippedSauterMeanDiameter` | diâmetro de Sauter do S-Gamma limitado a [dMin, dMax] |

> 💡 **Truque de robustez — rampa de fluxo por iteração.** Ligar 570 kW/m² de uma vez num campo
> monofásico frio produz vapor demais nas primeiras iterações e o EMP diverge. A rampa leva a solução
> de "água aquecida" para "água fervendo" suavemente. **Aplicar o mesmo a qualquer fonte de calor
> forte** (em CHT, rampar a temperatura do fluido quente em vez do fluxo).

> 💡 **Truque da distribuição por coordenada.** Um único contorno de parede com fluxo condicional à
> posição dispensa dividir a geometria em vários *boundaries*. Serve para aquecimento por trechos,
> faixas de nível, zonas de incrustação.

### 2.3 Funções de análise (pós-processamento)
| Field Function | definição (resumo) |
|---|---|
| `InletThermodynamicQuality` | `cp·(T_in − Tsat)/h_fg` |
| `ThermodynamicQuality` | `x_in + 4·q″·x / (G·h_fg·D)` — título de equilíbrio ao longo do tubo |
| `LiquidSubcooling` | `Tsat − T_líquido` |
| `WallSuperHeat` | `T_parede − Tsat` |
| `QuenchingHeatFlux` | parcela de *quenching* do RPI (já inclui `WallDryoutAreaFraction`) |
| `WallEvaporationRate` | taxa de evaporação na parede |
| `BulkCondensationRate` / `BulkEvaporationRate` | troca de massa no seio do líquido |

> 💡 **A régua dentro da simulação.** `ThermodynamicQuality` é o balanço de energia 1D escrito como
> Field Function. Plotar ao lado da fração de vazio média na seção mostra, no mesmo gráfico, onde o
> modelo põe vapor em relação ao que a termodinâmica de equilíbrio permite. **Fazer isso em todo caso
> com mudança de fase** — é a verificação mais barata que existe.

> ⚠️ **`WallDryoutAreaFraction` é a variável a vigiar.** Ela diz que fração da parede o modelo
> considera seca. Perto de 0 = RPI dentro do domínio de validade; crescendo = o modelo está saindo do
> regime de bolhas e entrando em secagem, onde o RPI não foi feito para prever temperatura de parede.

### 2.4 As três parcelas do RPI (para ler os campos)
```
q″_parede = q″_convecção (líquido)  +  q″_quenching  +  q″_evaporação
```
`QuenchingHeatFlux` e `WallEvaporationRate × h_fg` mostram como o modelo reparte o fluxo. Na região
monofásica (antes do IB) tudo é convecção; depois do NVG a evaporação domina.

## 3. Modelos físicos

Mesmo conjunto do tutorial 01 para o fluido bifásico (EMP, Phasic Turbulence, Gravity, **Phase
Coupled Fluid Energy**, Steady), com uma adição:

| ajuste | valor | por quê |
|---|---|---|
| `Eulerian Multiphase > Minimum Volume Fraction` | **1×10⁻²⁰** | o vapor nasce de fração **zero**; o limite baixo evita que o solver "perca" a fase nos primeiros passos |

Não há sólido: o fluxo é **imposto** na parede (sem CHT). É a diferença central para o tutorial 01.

## 4. Fases

### Líquido
- Material Liquid; **desligar auto-select** e escolher **K-Epsilon → Realizable K-Epsilon Two-Layer**.
- Wall treatment: **Two-Layer All y+ Wall Treatment**.
- Constant Density, Segregated Fluid Temperature (como no 01).

### Vapor (renomear *Air* para *Steam*)
- Gas, **Turbulence Response** (modelo de **Issa** — a turbulência do vapor disperso é derivada da do
  líquido, sem equações próprias).
- **Particle Size Distribution → S-Gamma**, com **Pre-Integrated S-Gamma**: o diâmetro de bolha deixa
  de ser constante e passa a ser **transportado** (quebra e coalescência).
- Propriedades: definidas mais adiante no tutorial (a receber).

> ⚠️ **Correção de uma nota nossa anterior.** No tutorial 01 escrevemos que *"High y+ é exigência
> do RPI"*. **Não é:** este tutorial usa **Two-Layer All y+** com ebulição na parede. O que vale:
> **a malha junto à parede tem de ser coerente com o tratamento escolhido** e o resultado do RPI
> (superaquecimento de parede, posição do NVG) **deve passar por teste de sensibilidade da primeira
> célula** — o modelo usa a temperatura do líquido junto à parede e é conhecido por depender do
> tamanho dessa célula. Não assumir independência de malha.

## 5. Interações entre fases

Interação **Continuous-Dispersed** (líquido contínuo, vapor disperso), **auto-select desligado**:

| modelo | para quê |
|---|---|
| **Turbulent Dispersion** | espalhamento das bolhas pela turbulência do líquido |
| **Virtual Mass** | inércia do líquido arrastado pela bolha (importante em gás leve × líquido pesado) |
| **Interphase Mass Transfer → Boiling/Condensation** | condensação das bolhas no líquido sub-resfriado e evaporação no saturado |
| **Wall Boiling** (+ **Wall Bubble Nucleation**, **Quenching**) | o RPI propriamente dito |
| **S-Gamma Breakup and Coalescence** | fecha o balanço do diâmetro de bolha |

Arrasto, sustentação e os coeficientes de cada modelo: nas seções seguintes (a receber).

### S-Gamma × Kurul-Podowski (tutorial 01)
| | Kurul-Podowski (01) | S-Gamma (02) |
|---|---|---|
| diâmetro de bolha | correlação com o sub-resfriamento local | **transportado** (quebra/coalescência) |
| custo | baixo | maior (equações extras + limites dMin/dMax) |
| quando usar | sub-resfriado, vazio baixo | vazio crescendo, bolhas mudando de tamanho ao longo do caminho |

> 💡 Começar sempre pelo **Kurul-Podowski** (mais robusto) e passar ao **S-Gamma** só se o tamanho
> de bolha mudar a resposta que interessa.

---

## Checklist reaproveitável (até aqui)
- [ ] Parâmetros do caso como Field Functions escalares; contornos referenciam os nomes.
- [ ] Densidade usada para G → velocidade **igual** à do material.
- [ ] Rampa da fonte de calor por iteração (~200 iterações).
- [ ] Minimum Volume Fraction 10⁻²⁰ no EMP.
- [ ] `ThermodynamicQuality` como Field Function e plot junto da fração de vazio.
- [ ] Monitorar `WallDryoutAreaFraction`.
- [ ] Tratamento de parede coerente com a malha + teste da 1ª célula.
- [ ] Régua 1D (CoolProp) antes de rodar: x = 0, OSV (Saha-Zuber), título de saída.

## Seções seguintes
*(a receber)*
