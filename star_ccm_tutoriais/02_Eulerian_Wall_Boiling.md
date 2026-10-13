# Tutorial 02 — Eulerian: Wall Boiling

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: 🟡 seções 1–10 lidas (visão geral, User Field Functions, Physics Models, Phases, Phase
> Interactions, Material Properties, Phase Interaction Properties, Reference Values, Boundary
> Conditions, Initial Conditions — 13/10/2026). Restante (malha, solver, resultados) a receber.

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
| Velocidade de entrada | **1,08 m/s** = G/ρ com ρ na temperatura média (832 kg/m³) — ver §6 |
| dx/dz = 4q″/(G·h_fg·D) | 0,0982 m⁻¹ |
| **x = 0 (líquido médio saturado)** | **z ≈ 1,70 m** (de 2,0 m aquecidos) |
| Título de equilíbrio na saída | **x_out ≈ +0,029** |
| **OSV (Saha-Zuber, Pe = 1,1×10⁵)** | ΔT_sub,OSV ≈ 19,7 K → **z ≈ 1,11 m** |

Temperatura média do líquido (monofásico equivalente): 488,9 K em 0,5 m · 506,6 K em 1,0 m ·
523,8 K em 1,5 m · Tsat em 1,70 m.

> ✅ **InletDensity = 832,06 kg/m³ não é erro.** A IAPWS dá 869,8 kg/m³ *na entrada* (470,63 K), mas
> o tutorial avalia a densidade do líquido na **temperatura média entre entrada e saturação**
> (500,6 K → 832,2 kg/m³) e usa a **mesma** densidade no material e na conversão G → velocidade.
> Assim a vazão mássica imposta sai exata. Receita completa em §6.

> 💡 O título de entrada `cp·(T_in − Tsat)/h_fg` só bate com o exato pela entalpia (**−0,167**) se o
> cp for o **cp secante** da §6 (com cp local daria −0,160 na entrada ou −0,177 na saturação).

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
| `InletDensity` | 832,06 kg/m³ (líquido na temperatura média — §6) |
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
- Propriedades: §6.

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

Métodos e coeficientes de cada modelo: §7.

### S-Gamma × Kurul-Podowski (tutorial 01)
| | Kurul-Podowski (01) | S-Gamma (02) |
|---|---|---|
| diâmetro de bolha | correlação com o sub-resfriamento local | **transportado** (quebra/coalescência) |
| custo | baixo | maior (equações extras + limites dMin/dMax) |
| quando usar | sub-resfriado, vazio baixo | vazio crescendo, bolhas mudando de tamanho ao longo do caminho |

> 💡 Começar sempre pelo **Kurul-Podowski** (mais robusto) e passar ao **S-Gamma** só se o tamanho
> de bolha mudar a resposta que interessa.

## 6. Propriedades dos materiais — a receita do líquido sub-resfriado

As propriedades ficam **para depois de escolher todos os modelos**: algumas só aparecem quando um
modelo as exige.

**Vapor e interface: constantes na saturação.** Vale porque a pressão é alta e não se espera
secagem da parede: o vapor fica em Tsat.

**Líquido: constante, mas escolhida para fechar o balanço de energia.** O líquido sai de 60 K
sub-resfriado até Tsat, e ρ e cp variam bastante nesse caminho. O tutorial resolve com duas regras:

```
cp_L  = (h_L,SAT − h_L,IN) / (T_SAT − T_IN)          ← cp "secante"
ρ, μ, k do líquido  na  T_média = (T_IN + T_SAT)/2
v_IN  = G / ρ_L                                       ← mesma ρ do material
```

Com `Heat of Formation = h_L,SAT` e `Standard State Temperature = T_SAT`, o STAR calcula
`h(T) = h_L,SAT + cp·(T − T_SAT)`. Com o cp secante, **h(T_IN) sai exata** e o calor necessário para
levar o líquido à saturação fica certo, mesmo com cp constante.

| a 45 bar | Líquido (tutorial) | CoolProp | Vapor (tutorial) | CoolProp |
|---|---|---|---|---|
| Density [kg/m³] | `$InletDensity` = 832,06 | 832,23 (T média) | 22,7 | 22,70 |
| Dynamic Viscosity [Pa·s] | 1,177×10⁻⁴ | 1,1805×10⁻⁴ | 1,78×10⁻⁵ | 1,771×10⁻⁵ |
| **Heat of Formation** [J/kg] | **1 122 143** | 1 122 248 | **2 797 997** | 2 797 947 |
| Specific Heat [J/kg·K] | **4 648,3** (secante) | 4 670,8 (secante) | 4 227,9 | 4 227 |
| Standard State Temperature | `$SaturationTemperature` | 530,59 K | `$SaturationTemperature` | |
| Thermal Conductivity [W/m·K] | 0,6433 | 0,6407 | 0,0535 | 0,0526 |
| Molecular Weight | — | | 18,0 kg/kmol | |

Interface (`Liquid Vapor Interface > Multiphase Material`): **Boiling Temperature** por Field Function
= `$SaturationTemperature`; **Surface Tension** = 0,024292 N/m (CoolProp: 0,02409).

> ✅ **Tudo bate com a IAPWS em < 2 %.** O tutorial 01 segue **a mesma receita** (conferido:
> ρ = 745,65 ≈ 745,83 na T média; cp = 5 310 ≈ 5 332 secante para 9,1 K de sub-resfriamento).
> **Ferramenta:** `python3 props_agua_saturada.py 45 --tin 470.63 --G 900` gera a tabela inteira,
> inclusive cp secante, propriedades na T média e velocidade de entrada.

> ⚠️ **Detalhe do texto do tutorial:** nesta seção ele manda pôr a temperatura inicial do líquido em
> 461,0 K, mas na §10 o mesmo nó recebe `$InletTemperature` (470,63 K). Vale o último — o 461 K fica
> sobrescrito.

> ⚠️ **Quando a receita deixa de valer:** com secagem de parede o vapor **superaquece** e as
> propriedades do vapor na saturação ficam erradas. Ex.: vapor a 30–40 bar tem cp ≈ 3,6–4,0 kJ/kg·K
> na saturação e ≈ 2,5–2,8 kJ/kg·K a 300 °C (fator ~1,4). Nesse caso, propriedades do vapor
> **dependentes de T** (tabela/polinômio).

## 7. Propriedades da interação líquido–vapor

A escolha principal: **nucleação Hibiki-Ishii + diâmetro de desprendimento Kocamustafaogullari**,
combinação aplicável a água numa **faixa larga de pressões**. Os defaults (**Lemmert-Chawla +
Tolubinsky**) são mais simples, mas **podem precisar de recalibração** fora da pressão em que foram
ajustados.

| nó | método / valor | por quê |
|---|---|---|
| Boiling Mass Transfer Rate → Continuous Phase Nusselt | **Ranz-Marshall** | troca líquido → interface da bolha |
| → Disperse Phase Nusselt | **26,0** | troca interface → interior da bolha. Não é crítico (vapor ~ Tsat); 2 = resposta lenta, 26 = resposta rápida/mistura interna |
| Drag Force → Drag Coefficient | **Tomiyama** | escoamento de bolhas |
| → Drag Correction | Volume Fraction Exponent, expoente (contínua) **0,0** | sem redução de arrasto para bolhas pequenas e esféricas |
| Interaction Area Density | **Symmetric** | espera-se faixa **larga** de fração de vazio |
| Interaction Length Scale | Field Function `ClippedSauterMeanDiameter` | usa o diâmetro do S-Gamma, mas limitado a [dMin, dMax] para que soluções S-Gamma não convergidas no início não desestabilizem |
| Wall Bubble Nucleation → Nucleation Site Number Density | **Hibiki-Ishii** | faixa larga de pressão |
| → Bubble Departure Diameter | **Kocamustafaogullari** | idem |
| `Vapor > Models > Issa Turbulence Response` → Phase Interaction | `Liquid Vapor Interface` | liga a resposta turbulenta do vapor à interação |

> 💡 **Turbulent Dispersion é obrigatória com condensação.** Sem ela o gradiente de fração de vazio,
> que muda muito rápido na borda da nuvem de bolhas, é mal discretizado: aparecem velocidades
> estranhas na borda da nuvem e dificuldade de convergência.

> 💡 **Para a nossa faixa de pressão** (diferente da que calibrou os defaults), **usar
> Hibiki-Ishii + Kocamustafaogullari** como padrão. O tutorial 01 usou os modelos automáticos.

## 8. Valores de referência

| nó | valor |
|---|---|
| Gravity | `[−9,81, 0,0]` m/s² (eixo x = eixo do tubo, escoamento ascendente) |
| Reference Density | `$InletDensity` (densidade do **líquido**) |
| Reference Pressure | `$SystemPressure` |

> 💡 **Reference Density = líquido** tira a hidrostática do campo de pressão resolvido. A solução parte
> de pressão e vazio **zero** sem precisar inicializar um campo hidrostático. Mesma escolha do
> tutorial 01 — padrão para qualquer caso com líquido dominante.

## 9. Condições de contorno

| fronteira | fase | grandeza | valor |
|---|---|---|---|
| **Wall** | — | Thermal Specification | **Heat Flux** = Field Function `WallHeatFluxIterationRamp` |
| **In** | Líquido | Static Temperature | `$InletTemperature` |
| | | Turbulence Intensity / Viscosity Ratio | **0,01 / 200** |
| | | Velocity Magnitude | `InletVelocity` → Laboratory → componente *i* |
| | | Volume Fraction | 1,0 |
| | Vapor | Sauter Mean Diameter | 0,001 m |
| | | Static Temperature | `$SaturationTemperature` |
| | | Velocity Magnitude | `InletVelocity` (*i*) — mesma do líquido |
| | | Volume Fraction | 0,0 |
| **Out** | Líquido | Static Temperature (refluxo) | `$InletTemperature` |
| | | Turbulence Intensity / Viscosity Ratio | 0,01 / 10 |
| | | Volume Fraction | 1,0 |
| | Vapor | Sauter Mean Diameter / T / VF | 0,001 m / `$SaturationTemperature` / 0,0 |

- A turbulência na entrada foi escolhida para **bater com a condição inicial** (0,01 / 200).
- Vapor sempre na **Tsat**; líquido sub-resfriado — cada fase com sua temperatura (como no 01).
- Diferença para o 01: lá a semente de vapor na entrada era 10⁻⁴; aqui é **0,0**.

## 10. Condições iniciais

| fase | grandeza | valor |
|---|---|---|
| Líquido | Static Temperature | `$InletTemperature` |
| | Turbulence Specification | Intensity + Viscosity Ratio: 0,01 / 200, Velocity Scale 1,0 m/s |
| | Velocity | Field Function vetorial `InletVelocity` |
| | Volume Fraction | 1,0 |
| Vapor | Size Distribution Specification | Sauter Mean Diameter = 0,001 m |
| | Static Temperature | `$SaturationTemperature` |
| | Velocity | `InletVelocity` |
| | Volume Fraction | 0,0 |

> 📌 **Fração zero não existe para o solver:** as equações de fase não resolvem com fração
> identicamente nula, então nas condições de contorno e iniciais o código usa **10⁻¹²** no lugar de 0.
> Junto com o *Minimum Volume Fraction* 10⁻²⁰ da §3, é o que deixa o vapor "nascer" da parede.

> 💡 **Inicialização = entrada** (velocidade, temperatura, turbulência) + vazio zero + rampa de fluxo.
> Campo inicial monofásico e frio; a ebulição aparece aos poucos com a rampa.

---

## Checklist reaproveitável (até aqui)
- [ ] Parâmetros do caso como Field Functions escalares; contornos referenciam os nomes.
- [ ] Líquido sub-resfriado com propriedades constantes: **cp secante**, ρ/μ/k na **T média**
      (`props_agua_saturada.py --tin`).
- [ ] Densidade usada para G → velocidade **igual** à do material.
- [ ] Heat of Formation = entalpias de saturação; Standard State Temperature = Tsat (as duas fases).
- [ ] Nucleação **Hibiki-Ishii + Kocamustafaogullari** fora da pressão de calibração dos defaults.
- [ ] Interaction Area Density **Symmetric** se a faixa de vazio for larga.
- [ ] **Turbulent Dispersion** ligada sempre que houver condensação.
- [ ] Reference Density = líquido; Reference Pressure = pressão do sistema.
- [ ] Rampa da fonte de calor por iteração (~200 iterações).
- [ ] Minimum Volume Fraction 10⁻²⁰ no EMP.
- [ ] `ThermodynamicQuality` como Field Function e plot junto da fração de vazio.
- [ ] Monitorar `WallDryoutAreaFraction`.
- [ ] Tratamento de parede coerente com a malha + teste da 1ª célula.
- [ ] Régua 1D (CoolProp) antes de rodar: x = 0, OSV (Saha-Zuber), título de saída.

## Seções seguintes
*(a receber: malha, solver, execução e comparação com Bartolomei)*
