# Dimensionamento final + plano de CFD — Ciclone Valgroup

> Condição confirmada (Gabriel/Marcus, pós-apresentação da matriz): **suspensão 1900 kg/h − 80 kg/h de
> particulado → GÁS 1820 kg/h**. Rodadas a **100% e 50%** da vazão nominal, **steady** e depois **transiente**,
> com **CHT**. Base: planilha Lapple dos colegas + Peçanha cap.3 / Cremasco cap.6,8.

## 1. Condição de projeto
| | 100% | 50% |
|---|---|---|
| Gás | 1820 kg/h | 910 kg/h |
| **Q (a 400°C, ρ=3,946)** | **461,2 m³/h** (0,1281 m³/s) | **230,6 m³/h** |
| Sólido (char) | 80 kg/h | 40 kg/h |

*(SCADA TT-209 indica operação ~343°C → ρ=4,31 → Q=422 m³/h. Projetar a 400°C é **conservador** para ΔP.)*

## 2. Geometria dimensionada (v_i = 15,2 m/s)

| | **LAPPLE** (convencional) | **STAIRMAND** (alta eficiência) |
|---|---|---|
| **Dc (corpo)** | **259 mm** | **290 mm** |
| Entrada a × b | 130 × 65 mm | 145 × 58 mm |
| Saída de gás De | 130 mm | 145 mm |
| Vortex finder S | 162 mm | 145 mm |
| Altura cilíndrica h | 519 mm | 435 mm |
| **Altura total H** | **1037 mm** | **1160 mm** |
| Saída de pó B | 65 mm | 109 mm |
| Espiras Ne | 5 | 6 |

### Desempenho (turndown — mesmo ciclone, vazão reduzida)
| Família | carga | v_i | **d\*** | **ΔP** | η global* |
|---|---|---|---|---|---|
| Lapple | 100% | 15,2 m/s | 12,2 µm | **36,7 mbar** | 98,6% |
| Lapple | 50% | 7,6 m/s | 17,3 µm | 9,2 mbar | 97,4% |
| **Stairmand** | 100% | 15,2 m/s | **10,6 µm** | **29,3 mbar** | 98,9% |
| **Stairmand** | 50% | 7,6 m/s | 15,0 µm | 7,3 mbar | 98,0% |

\* sobre a PSD da amostra **EXTRAÍDA** (grossa) — o char **CARREADO** é mais fino, então η real é **menor**.

### 📌 Recomendação: **STAIRMAND**
Corta **mais fino** (10,6 vs 12,2 µm) **com MENOS perda de carga** (29,3 vs 36,7 mbar) — o Lapple fica a
apenas 8% do limite de 40 mbar, sem margem. O Stairmand dá **27% de folga**. Como o ponto fraco do projeto
são os **finos <75 µm**, a família de alta eficiência é a escolha certa.

### Turndown (o achado da rodada de 50%)
A 50% da vazão o **ΔP cai a 25%** (v²) mas o **d\* piora 41%** (∝1/√v) — o ciclone **perde eficiência nos
finos** justamente na carga baixa. **É por isso que a rodada de 50% importa:** define o limite inferior
de operação. *(A η global cai pouco porque a PSD extraída é grossa; com a PSD do carreado a queda será maior.)*

## 3. Sensibilidade — os inputs da planilha são CONSERVADORES
| ρ_s | µ | d\* | η |
|---|---|---|---|
| 776,8 (bulk, planilha) | 9,5e-5 (planilha) | 12,2 µm | 98,6% |
| 1500 (partícula est.) | 2,5e-5 (HC típico) | **4,5 µm** | 99,8% |

- **ρ_s = 776,75 é a densidade BULK** (com vazios) — o correto é a da **partícula** (minerais Ti/Si/Fe ↑ → 1500–2200).
- **µ = 9,5e-5 é alto** para vapor de HC a 400°C (típico 1,5–3e-5).
- **Ambos empurram o d\* para cima** → o dimensionamento da planilha é **conservador**. ✅ Bom para projeto,
  mas vale corrigir para saber a margem real.

## 4. 🎯 Escolha do modelo multifásico: **LAGRANGEANO**, não DEM nem Euleriano

**O critério é a fração volumétrica de sólidos:**
```
Q_gás = 0,1281 m³/s      Q_sólido = 80/3600/1500 = 1,48e-5 m³/s
α_sólido = 1,16e-4  =  0,0116 %          razão mássica = 0,044 kg/kg
```

| Faixa (Elghobashi) | Acoplamento | Modelo |
|---|---|---|
| α < 1e-6 | 1 via | Lagrangeano |
| **1e-6 < α < 1e-3** | **2 VIAS** ← **estamos aqui (1,2e-4)** | **Lagrangeano** |
| α > 1e-3 | 4 vias (colisões) | DEM |

**Por que NÃO DEM:** (a) a α=0,01% **não há colisão partícula-partícula relevante** — DEM resolveria um
fenômeno que não existe aqui; (b) DEM rastreia partícula **real**: a 10 µm seriam **2,8×10¹⁰ partículas/s** —
inviável por ordens de grandeza. O Lagrangeano usa **parcelas** (representantes estatísticos).

**Por que NÃO Euleriano-Euleriano:** funciona, mas é **pior para eficiência de coleta** — borra a trajetória
individual (que é justamente o que define captura vs escape) e exigiria **uma equação de momento por faixa
granulométrica**. O Lagrangeano dá a **curva de eficiência por tamanho** direto, injetando classes.

> **✅ SETUP: Lagrangian Multiphase (fase discreta) · acoplamento 2 vias · RSM · + CHT**

## 5. Plano de execução no STAR

### Turbulência: **RSM (Reynolds Stress)** — obrigatório
O escoamento em ciclone é **swirl altamente anisotrópico**. k-ε e k-ω **falham** (subestimam o vórtice e
superestimam a difusão turbulenta) → eficiência errada. RSM é o padrão para ciclones.

### Sequência
| # | Rodada | Objetivo |
|---|---|---|
| 1 | **Steady RSM 100%** (só gás) | campo médio, ΔP, verificação de malha |
| 2 | **Steady RSM 50%** (só gás) | ΔP e campo na carga reduzida |
| 3 | **+ Lagrangeano** nas duas | **curva de eficiência por faixa** (injeta classes de tamanho) |
| 4 | **+ CHT** | **temperatura de parede > orvalho (~250°C)** |
| 5 | **Transiente (URANS RSM)** 100% e 50% | **PVC** (vórtice precessante) → afeta captura dos finos |

### CHT — o que checar
Requisito do e-mail do Lucas: **evitar condensação**. O orvalho dos pesados (C12–C15, naftaleno) fica em
**~230–250°C** a 1,2 bar. Com gás a 343–400°C, a margem no bulk é confortável, **mas os pontos frios**
(ápice do cone, parede sem isolamento) podem se aproximar. **Modelar a parede (sólido) + isolamento** e
verificar **T_parede > 250°C** em todo ponto.

### Partículas (Lagrangeano)
- Injetar **classes de tamanho** (ex.: 1, 2, 5, 10, 20, 50, 75, 150 µm) → curva de eficiência
- ρ_s = **1500** (partícula, não bulk) — rodar 776,75 como sensibilidade
- Parede: **rebote** (com coef. de restituição) no corpo; **escape/trap** na saída de pó
- **Erosão:** ativar modelo (Ti 14,9% + Si 3,5% = char **abrasivo**) → mapa de desgaste do cone

## 6. Pendências
- ⏳ **PSD do char CARREADO** (mais fino que a extraída) — Marcus. **É o que define a η real.**
- 🟡 **ρ_s da partícula** (medir ou estimar por composição mineral)
- 🟡 **µ do gás** — calcular da composição GC-MS (Wilke/Chung) e encerrar a divergência 9,5e-5 × 2,5e-5
- 🟡 **T de projeto**: 400°C (planilha) × 343°C (SCADA) — confirmar onde entra o ciclone
- **Material:** Cl 2,78% → **HCl a 340°C** (corrosão) + minerais 21% (**abrasão**) → seleção de liga + sobre-espessura
