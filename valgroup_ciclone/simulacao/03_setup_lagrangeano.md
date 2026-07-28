# Setup LAGRANGEANO — partículas de char no ciclone

> Após estudar o tutorial Siemens "Lagrangian: Particle-Laden Flow" (duto em cotovelo).
> **Boa notícia: a carga do tutorial (α = 0,010%) é a MESMA ordem da nossa (α = 0,0116%)** →
> o fluxo de trabalho dele é **diretamente aplicável**, e o **Two-Way Coupling** está justificado.

## 1. Selecionar os modelos

### No Continuum (`Physics 1`)
`Optional Models → **Lagrangian Multiphase**`

### Criar a fase
`Models → Lagrangian Multiphase → Lagrangian Phases → botão direito → New → **Free-stream Phase**`

| Group Box | Modelo |
|---|---|
| Enabled | Residence Time *(pré-selecionado)* |
| **Particle Type** | **Material Particles** → *Pressure Gradient Force* e *Spherical Particles* entram sozinhos |
| Material | **Solid** |
| Equation of State | **Constant Density** |
| **Optional Particle Forces** | **Drag Force** ⬅ + **`Gravity`** (ver §2) |
| Track Sampling | Track File |
| **Optional Models** | **Two-Way Coupling** |

### Propriedades da fase
| Nó | Valor |
|---|---|
| `Solid → [material] → Density → Constant` | **1500 kg/m³** ⚠️ (a da **partícula**, não os 776,75 da planilha, que é *bulk*) |
| `Drag Force → Drag Coefficient Method` | **Schiller-Naumann** |
| Track File Vectors | Parcel Centroid · Particle Velocity |

## 2. ⚠️ O que o tutorial NÃO tem e nós PRECISAMOS

O tutorial é um cotovelo simples. O ciclone exige **4 adições**:

| # | Adição | Por quê |
|---|---|---|
| 1 | **Turbulent Dispersion** | ⭐ Sem ela os finos são captados demais (trajetória "limpa"). É **o modelo que define a cauda fina da curva de eficiência**. |
| 2 | **Gravity** (Optional Particle Forces) | O tutorial despreza. No ciclone a partícula **cai na moega** — sem gravidade a captura no cone sai errada. |
| 3 | **BC de parede por boundary** (§4) | O tutorial usa rebote perfeito em tudo. Precisamos de **Escape** na saída de pó. |
| 4 | **Erosion** (opcional) | Char com **21% de minerais** (Ti 14,9 + Si 3,5 + Fe 3,2) → mapa de desgaste no cone. |

## 3. ✅ Checagens que validam as escolhas

**Modelo de arrasto — Schiller-Naumann é adequado:**
| d (µm) | v_rel | **Re_p** |
|---|---|---|
| 1 | 0,5 m/s | 0,02 |
| 10 | 2 m/s | 0,83 |
| 100 | 5 m/s | 20,8 |
| 150 | 6 m/s | 37,4 |

Re_p de **0,02 a ~37** → Schiller-Naumann cobre até Re_p ~1000. ✅

**Número de Stokes (o adimensional que governa a captura):**
`Stk = ρ_s·d²·v_i / (18·µ·D_c)`
| d (µm) | Stk | leitura |
|---|---|---|
| 1 | 4,6e-5 | escapa |
| 5 | 1,2e-3 | escapa |
| **10,6** | **5,2e-3** | **zona de corte** ⬅ nosso d* |
| 20 | 1,8e-2 | capta |
| 100 | 4,6e-1 | capta |

**Stk50 ≈ 5e-3** — bate com a faixa típica de ciclones (5e-3 a 1e-2). ✅ *Confirma o dimensionamento analítico por um caminho independente.*

## 4. Condições de contorno das PARTÍCULAS
| Boundary | Modo | Significado |
|---|---|---|
| **`outlet_dust`** | **Escape** | ⭐ **partícula CAPTURADA** (vai para a moega) |
| **`outlet_gas`** | **Escape** | partícula **PERDIDA** (arrastada com o gás) |
| **`walls`** | **Rebound** | coef. restituição normal ~0,8 · tangencial ~0,9 |

> **A eficiência sai daí:** `η = massa que sai por outlet_dust / massa injetada`.
> ⚠️ Se `outlet_dust` ficar Rebound, as partículas ricocheteiam para sempre e a eficiência não fecha.

## 5. Injetores — a curva de eficiência por faixa

**Estratégia: 1 injetor por classe de tamanho**, com **massa igual** em cada.
Assim a eficiência de cada classe sai direto, sem pós-processar distribuição.

- Tipo: **Part Injector** na boundary `inlet`
- Velocidade: igual à do gás (**15,23 m/s** a 100%; 7,62 a 50%)
- Massa por injetor: **0,022222 / N kg/s** (100%) · **0,011111 / N** (50%)
- Com **8 classes** → **0,002778 kg/s** cada (100%)

**Classes sugeridas (µm):** `1 · 2 · 5 · 10 · 20 · 50 · 75 · 150`
*(concentra pontos em 1–20 µm, que é onde a curva vira — o d* é 10,6)*

> **Alternativa:** injetor único com distribuição **Rosin-Rammler**. Os colegas já ajustaram a
> amostra extraída: **n = 0,6127 · D63,2 = 68,4 µm**. Útil para a η **global**, mas a curva por
> faixa fica mais limpa com injetores separados.

## 6. Relatórios da eficiência
Para cada classe, criar report de **massa por boundary** (Lagrangian → Mass Flow):
```
η_classe = m_dot(outlet_dust) / m_dot(injetado)
```
Plotar **η × d** = a **curva de eficiência de coleta** — o entregável principal do estudo.

## 7. ⚠️ Ressalva que vai para o relatório
A PSD que temos é da **amostra EXTRAÍDA** (grossa). O char **CARREADO** é **mais fino** →
a **η global real será MENOR** que a calculada sobre a amostra extraída.
**A curva por faixa (η × d) não sofre disso** — por isso ela é o entregável certo:
quando a PSD do carreado chegar (pendente com o Marcus), basta **integrar a curva** contra ela.
