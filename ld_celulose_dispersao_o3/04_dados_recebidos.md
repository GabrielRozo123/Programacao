# 04 — Dados recebidos do cliente

> Log da Etapa 2 do cronograma. Cada lote de documento entra aqui com data, o que foi extraído
> e o que **continua faltando**.

---

## Lote 1 — 29/09/2026 · manuais dos ventiladores + NR-15

| documento | conteúdo |
|---|---|
| `CVC99D0014` | Manual do ventilador LX 816.95.00 SON2T — tags **1219-24-910 / 920** (2 un.) |
| `CVC99D0015` | Manual do ventilador HL 4S 871.92.00 SPN2T — tag **1219-24-930** (1 un.) |
| `CVC99D0016` | Manual do ventilador HL 4S 871.92.00 SPN2T — tag **1219-24-940** (1 un.) |
| `NR-15 Anexo 11` | Tabela de limites de tolerância |

Identificação comum: fabricante **Howden South America**, via **Valmet**, PV NB0215,
cliente final **LD Celulose**, planta **Amadeus**, **Indianópolis-MG**, fabricação **2020**.

### 1.1 Pontos de operação — lidos das curvas de desempenho

| | **LX 816.95.00** (910/920) | **HL 4S 871.92.00** (930/940) |
|---|---|---|
| Vazão | **10,5 m³/s = 37 800 m³/h** | **4,2 m³/s = 15 120 m³/h** |
| Pressão estática | 1 670 Pa | 2 400 Pa |
| Potência no eixo | 28 kW | 16,3 kW |
| Rotação | 1 775 rpm | 1 770 rpm |
| Área de descarga | 0,3105 m² | 0,1337 m² |
| **Velocidade de descarga** | **33,8 m/s** | **31,4 m/s** |
| Densidade da curva | 0,9002 kg/m³ | 1,0148 kg/m³ |
| Temperatura do gás (curva de torque) | 35 °C | — |

**Capacidade total instalada:** 105 840 m³/h com os quatro em operação.

### 1.2 ⭐ A velocidade de descarga muda o prognóstico

Em `02_metodo_e_analise_previa.md` §5 o critério de *downwash* era `v_saída / v_vento > ~1,5`.
Abaixo disso o vento derruba a pluma na esteira do prédio e a altura da chaminé não adianta.

| vento | razão (LX 816, 33,8 m/s) |
|---|---|
| 1,5 m/s (noturno estável) | **22×** |
| 5 m/s (diurno típico) | **6,8×** |
| 10 m/s (forte) | 3,4× |

**Folga larga em toda a faixa**, inclusive no cenário noturno estável, que é o crítico.
Há *plume rise* por momento em todos os casos.

> ⚠️ **Válido apenas se a descarga for vertical.** Se for grelha horizontal na parede, 33 m/s
> vira jato rasante e o efeito se inverte. **A direção da descarga continua sendo o dado que
> decide o estudo** e não está nestes manuais — ver §1.5.

### 1.3 ⭐ O primeiro número real do projeto

A cadeia que estava solta na pendência nº 1 fecha por outro caminho: a vazão de O₃ que
corresponde a cada concentração no ar extraído.

Com `1 ppm de O₃ a 25 °C = 1,962 mg/m³`:

| vazão extraída | @ 0,08 ppm | @ 0,2 ppm | @ 0,5 ppm |
|---|---|---|---|
| 1 × LX 816 (37 800 m³/h) | 5,9 g/h | 14,8 g/h | 37,1 g/h |
| **2 × LX 816 (75 600 m³/h)** | 11,9 g/h | **29,7 g/h** | 74,2 g/h |
| 4 ventiladores (105 840 m³/h) | 16,6 g/h | 41,5 g/h | 103,8 g/h |

**Comparação com a régua gaussiana** (§2 do `02`): para atingir 0,2 ppm a 100 m no caso
noturno estável, **com fonte no solo**, seriam necessários **0,54 kg/h = 540 g/h**.

A liberação no ponto de alarme (≈ 30 g/h) é **~18× menor** — e isso **antes** de creditar a
descarga vertical a 33,8 m/s, que joga a pluma para cima.

> **Leitura preliminar:** o cenário de exaustor em operação normal provavelmente **não** gera
> contorno de isolamento relevante. O caso que deve dimensionar o estudo é o **off-gás** ou a
> **PSV**. Isso reordena a prioridade dos 26 cenários.
>
> ⚠️ **[SUPOSTO]** que os LX 816 são os contínuos, e que o ar extraído está no setpoint.
> Os dois precisam de confirmação. A ordem de grandeza, porém, é robusta.

### 1.4 Contorno adicional a plotar

O **NR-15 Anexo 11** fixa para ozona **0,08 ppm** (0,16 mg/m³). Como valor numérico de
projeto, ele fica entre dois critérios que o cliente já usa, e vale entrar como mais um
contorno no pós-processamento:

| contorno | valor | origem |
|---|---|---|
| percepção | 0,01 ppm | cliente |
| **referência normativa** | **0,08 ppm** | NR-15 Anexo 11 |
| isolamento de área | 0,2 ppm | cliente |
| isolamento total | 0,5 ppm | cliente |
| off-gás | 3 ppm | cliente |

Em fração mássica, para o escalar passivo (`φ = ppm / 6,033 × 10⁵`):

| contorno | φ |
|---|---|
| 0,01 ppm | 1,658 × 10⁻⁸ |
| 0,08 ppm | 1,326 × 10⁻⁷ |
| 0,2 ppm | 3,315 × 10⁻⁷ |
| 0,5 ppm | 8,288 × 10⁻⁷ |
| 3 ppm | 4,973 × 10⁻⁶ |

### 1.5 🔴 O que os manuais NÃO trazem — pedir já

Os manuais remetem as condições de operação para a tabela **CARACTERÍSTICAS TÉCNICAS** do
**Desenho de Conjunto Geral**, que não veio no lote. São quatro desenhos:

| ventilador | desenho |
|---|---|
| 1219-24-910 / 920 | **CVC00P0015 / CVC00P0016** |
| 1219-24-930 | **CVC00P0017** |
| 1219-24-940 | **CVC00P0018** |

**É neles que está a geometria de descarga** — direção, altura e arranjo do bocal de saída.
Sem isso, o §1.2 fica como hipótese e não como resultado.

### 1.6 ⚠️ Duas inconsistências a confirmar

**a) Densidades de projeto diferentes no mesmo prédio.** As curvas usam 0,9002 kg/m³ (LX 816)
e 1,0148 kg/m³ (HL 4S 871). Ventiladores que extraem do mesmo ambiente deveriam compartilhar
a condição.

**b) A densidade de 0,9002 kg/m³ não fecha com o sítio.** A 35 °C (temperatura indicada na
curva de torque), 0,9002 kg/m³ corresponde a **≈ 80 kPa**. Indianópolis-MG está a ~900 m,
onde a atmosfera dá **≈ 91 kPa** e ρ ≈ 1,03 kg/m³.

Pode ser margem de projeto do fabricante, mas **a vazão volumétrica real depende disso** —
e a vazão é o que entra na conta do §1.3.

---

## O que ainda falta

Do `03_pendencias_e_perguntas.md`, seguem abertos e agora com prioridade revista:

| # | item | status |
|---|---|---|
| 🔴 | Desenhos CVC00P0015 a P0018 — **geometria de descarga** | novo, crítico |
| 🔴 | Quais ventiladores são contínuos e quais disparam a 0,2 ppm | novo |
| 🔴 | Vazão de O₃ do **off-gás** e das **PSVs** | aberto — agora é o caso dimensionante |
| 🟠 | Série horária de vento com timestamp | aberto |
| 🟠 | Topografia num raio de ~1 km | aberto |
| 🟠 | Rugosidade / uso do solo no entorno | aberto |
| 🟡 | Volume interno do prédio e trocas de ar | aberto — fecha a conta do §1.3 |
| 🟢 | Modelo 3D da planta | aberto — Etapa 1 |
| 🟢 | Mapa de áreas ocupadas e tomadas de ar de HVAC | aberto |
| 🟢 | Sensores já instalados | aberto |

Faltam ainda **uma planilha e um PDF** que o cliente sinalizou que viriam.

---

## Efeito no plano de trabalho

O §1.3 reordena a prioridade dos 26 cenários. Se a leitura preliminar se confirmar:

1. **Off-gás e PSV viram os cenários principais** — são as liberações de vazão alta.
2. **Exaustor em operação normal vira cenário de referência**, não de dimensionamento.
3. O eixo de **estabilidade atmosférica** continua sendo o que mais amplia o resultado
   (fator 9× em vazão de fonte, §3 do `02`).

Isso deve ser apresentado na reunião da Etapa 2, porque muda a distribuição das 26 rodadas.
