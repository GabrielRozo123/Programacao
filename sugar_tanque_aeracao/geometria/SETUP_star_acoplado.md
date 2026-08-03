# Setup STAR-CCM+ — domínio acoplado (boundaries · derived parts · reports · scenes)

> Para `ACOPLADO_aerador_reator_ejetor_fluido.step` · malha 5,16 M células.
> **Todas as coordenadas em METROS.**

---

# 1. BOUNDARIES (8)

| # | Nome | Como identificar | Tipo | Valores |
|---|---|---|---|---|
| 1 | **`xarope_in`** | único disco **Ø0,2027** com normal **+Z**, em **z = 2,8245** | **Velocity Inlet** | **1,12 m/s** · VF: xarope=1, ar=0 · T operação |
| 2 | **`ar_in_1`** | disco **Ø0,0158** em x = **−0,325**, normal **+Y**, z = 2,2085 | **Pressure Inlet** | **1 kgf/cm² = 98.067 Pa (man.)** · VF: ar=1 |
| 3 | **`ar_in_2`** | idem em x = **0,025** | idem | idem |
| 4 | **`ar_in_3`** | idem em x = **0,375** | idem | idem |
| 5 | **`ar_in_4`** | idem em x = **0,725** | idem | idem |
| 6 | **`superficie_aerador`** | disco **Ø2,032** em **z = 1,220** | **Pressure Outlet** | 0 Pa · backflow VF ar=1 |
| 7 | **`superficie_reator`** | disco **Ø5,08** no topo do reator | **Pressure Outlet** | 0 Pa · backflow VF ar=1 |
| 8 | **`paredes`** | **todo o resto** | **Wall** no-slip | |

> ⚠️ **A boca da lança NÃO é boundary.** Ela é interior — o CFD calcula o que sai. É o ganho do
> acoplado: no modelo antigo você tinha que prescrever VF de ar e tamanho de bolha ali.

**Dica para achar rápido:** as 4 portas de ar são os únicos discos de **1,96 cm²** do modelo;
a entrada de xarope é o único de **322,7 cm²** com normal +Z.

---

# 2. DERIVED PARTS

## 2.1 Medição — o que o ejetor entrega ⭐
| Nome | Tipo | Definição |
|---|---|---|
| **`plano_boca`** | Section → Plane | ponto (0, 0, **−5,2465**) · normal (0,0,1) |
| **`boca_L1..L4`** | Cylinder | eixo (x, −0,440, −5,25) a (x, −0,440, −5,24) · r = **0,032** · x = −0,325 / 0,025 / 0,375 / 0,725 |

## 2.2 Medição — o que acontece no bico
| Nome | Tipo | Definição |
|---|---|---|
| **`plano_saida_bico`** | Section → Plane | ponto (0, 0, **1,8408**) · normal (0,0,1) |
| `plano_garganta` | Section → Plane | ponto (0, 0, **1,8655**) · normal (0,0,1) |
| `plano_porta_ar` | Section → Plane | ponto (0, 0, **2,2085**) · normal (0,0,1) |

## 2.3 Visualização
| Nome | Tipo | Definição |
|---|---|---|
| **`corte_vertical`** | Section → Plane | ponto (0,200, −0,440, 0) · normal **(0,1,0)** — corta as 4 lanças no comprimento |
| `corte_XZ_reator` | Section → Plane | ponto (0,196, −6,278, 0) · normal (0,1,0) |
| **`ar_no_tanque`** | **Threshold** | scalar **Volume Fraction of Ar** · `All Above` · **0,01** ⭐ |
| `bolha_fina` | Threshold | scalar **Sauter Mean Diameter** · `All Below` · **2,0e-4** (200 µm) |

---

# 3. REPORTS ⭐ *(os que respondem o estudo)*

## 3.1 O ar entra? — nas portas
| Report | Tipo | Parts | Scalar |
|---|---|---|---|
| `mdot_ar_1..4` | **Phase Mass Flow** | `ar_in_1..4` | fase **Ar** |
| **`Qar_total`** | **Expression** | | `(${mdot_ar_1}+${mdot_ar_2}+${mdot_ar_3}+${mdot_ar_4})/1.2*3600` → **m³/h** |

> **Alvo do Ito: 40 m³/h.** No ejetor isolado deu **0,04 m³/h** (1000× menos).

## 3.2 O que sai da lança? ⭐ *o resultado do estudo*
| Report | Tipo | Parts | Scalar |
|---|---|---|---|
| **`VF_ar_boca`** | Surface Average | `plano_boca` | Volume Fraction of Ar |
| **`SMD_boca`** | Surface Average | `plano_boca` | **Sauter Mean Diameter** |
| `v_boca` | Surface Average | `plano_boca` | Velocity Magnitude |
| `SMD_boca_L1..L4` | Surface Average | `boca_L1..L4` | SMD — *compara as 4 lanças* |

## 3.3 A física do bico
| Report | Tipo | Parts |
|---|---|---|
| `v_bico` | Surface Average · Velocity Magnitude | `plano_saida_bico` |
| `P_garganta` | Surface Average · **Absolute Pressure** | `plano_garganta` |
| **`P_porta_ar`** | Surface Average · **Absolute Pressure** | `plano_porta_ar` |

> ⭐ **`P_porta_ar` é o report-chave do diagnóstico.** Se ela ficar **acima** de
> 98.067 Pa (man.), o ar **não tem como entrar** — e isso confirma numericamente a causa
> geométrica (porta 318 mm a montante da contração).

## 3.4 Aeração no tanque
| Report | Tipo | Parts |
|---|---|---|
| **`holdup_aerador`** | Volume Average · VF de Ar | região do aerador |
| `holdup_reator` | Volume Average · VF de Ar | região do reator |
| `SMD_aerador` | Volume Average · SMD | aerador |
| **`frac_flotavel`** | Volume Integral do threshold `bolha_fina` ÷ volume total de ar | |

## 3.5 Controle
| Report | Tipo |
|---|---|
| `mdot_xarope_in` | Mass Flow em `xarope_in` → deve dar **≈ 46,9 kg/s** (130 m³/h × 1300) |
| `balanco_massa` | Expression: entradas − saídas ≈ 0 |

**Crie monitor + plot de todos** (`botão direito → Create Monitor and Plot from Report`).

---

# 4. SCENES

| # | Cena | Displayer | Scalar |
|---|---|---|---|
| 1 | **`VF_ar`** ⭐ | `ar_no_tanque` (threshold) + geometria com **Opacity 0,15** | Volume Fraction of Ar |
| 2 | **`SMD`** | `corte_vertical` | Sauter Mean Diameter · escala 0 a 3e-3 |
| 3 | `velocidade` | `corte_vertical` | Velocity Magnitude |
| 4 | **`bico_zoom`** | `corte_vertical`, câmera em z ≈ 1,85 | Velocity Magnitude · **mostra o jato dos 7 furos** |
| 5 | `pressao_ejetor` | `corte_vertical`, faixa z 1,8 a 2,6 | **Absolute Pressure** — mostra se há depressão na porta |

> A cena **5** é a que explica o problema visualmente: se a porta de ar estiver numa zona
> **vermelha** (pressão alta) em vez de azul, o Marcus e o Ito enxergam a causa sem equação.

---

# 5. Critérios de aceite / o que olhar

| Report | Se der… | Significa |
|---|---|---|
| **`Qar_total`** | ≈ 40 m³/h | ✅ o ejetor funciona |
| | ≪ 1 m³/h | ❌ confirma o achado do ejetor isolado |
| **`P_porta_ar`** | > 98 kPa man. | ❌ **o ar não pode entrar** — causa geométrica confirmada |
| **`SMD_boca`** | < 200 µm | ✅ bolha flotável |
| | ~1–2 mm | ❌ mesma conclusão do estudo anterior |
| `holdup_aerador` | — | quanto ar fica retido no tanque |
| `balanco_massa` | < 1 % | pré-requisito para acreditar em qualquer número acima |

---

# 6. ⚠️ PRIMEIRO: o domínio é UMA região fundida

Não existe "região do aerador" separada. Para os reports de volume, crie **derived parts de volume**:

| Nome | Tipo | Start | End | Radius |
|---|---|---|---|---|
| **`vol_aerador`** | **Cylinder** | (0.200, −0.440, **−5.892**) | (0.200, −0.440, **1.220**) | **1.016** |
| `vol_reator` | Cylinder | (0.196, −6.278, −6.171) | (0.196, −6.278, 1.479) | 2.540 |

*(o cilindro do aerador tem 23,06 m³ geométricos e o sólido real 20,18 — ele cobre com folga,
e as células fora do fluido simplesmente não existem)*

---

# 7. FIELD FUNCTIONS auxiliares (criar antes dos reports)

| Nome | Definição | Para que |
|---|---|---|
| **`ar_vol`** | `${VolumeFractionAr} * ${Volume}` | volume **de ar** em cada célula |
| **`SMD_x_ar`** | `${SauterMeanDiameter} * ${VolumeFractionAr} * ${Volume}` | para média ponderada |

> ⚠️ **Ajuste os nomes** conforme aparecem no seu autocompletar — dependem de como a fase de ar
> foi nomeada (ex.: `VolumeFractionofAr`, `Ar_VolumeFraction`).

---

# 8. OS 4 REPORTS PEDIDOS

## 8.1 `holdup_aerador` — quanto ar fica retido
```
Tipo   : Volume Average
Scalar : Volume Fraction of Ar
Parts  : vol_aerador
```
**Unidade:** fração (0 a 1). Multiplique por 100 para %.
**Referência:** aeração industrial típica fica em **2 a 10 %**.

## 8.2 `SMD_aerador` — tamanho médio de bolha ⭐
**Não use Volume Average direto** — ele média sobre células SEM ar e o número perde sentido.
Use a **média ponderada pelo ar**:

| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `int_SMDxAr` | **Volume Integral** | `SMD_x_ar` | `vol_aerador` |
| b | `int_Ar` | **Volume Integral** | `ar_vol` | `vol_aerador` |
| c | **`SMD_aerador`** | **Expression** | `${int_SMDxAr} / ${int_Ar}` | |

**Referência (estudo anterior, lanças passivas): SMD = 2,53 mm.**

## 8.3 `frac_flotavel` — a resposta do estudo ⭐⭐
Fração do **AR** que está em bolhas menores que 200 µm.

**1)** Derived part:
```
Threshold `bolha_fina` : scalar = Sauter Mean Diameter
                         All Below · 2.0e-4 m
                         Input Parts = vol_aerador
```
**2)** Reports:

| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `ar_fino` | Volume Integral | `ar_vol` | **`bolha_fina`** |
| b | `ar_total` | Volume Integral | `ar_vol` | `vol_aerador` |
| c | **`frac_flotavel`** | **Expression** | `${ar_fino} / ${ar_total}` | |

**Referência anterior: ~0 %.** É este número que diz se o ejetor resolve o problema.

## 8.4 `balanco_massa` — pré-requisito de credibilidade
| # | Report | Tipo | Parts |
|---|---|---|---|
| a | `m_xarope` | Mass Flow | `xarope_in` |
| b | `m_ar_tot` | Expression | `${mdot_ar_1}+${mdot_ar_2}+${mdot_ar_3}+${mdot_ar_4}` |
| c | `m_sai_aer` | Mass Flow | `superficie_aerador` |
| d | `m_sai_rea` | Mass Flow | `superficie_reator` |
| e | **`balanco_massa`** | Expression | `(abs(${m_xarope})+abs(${m_ar_tot})-abs(${m_sai_aer})-abs(${m_sai_rea})) / abs(${m_xarope})` |

**Aceite: < 1 %.** `m_xarope` tem de dar **46,9 kg/s**.
> **Não interprete nenhum dos outros três reports enquanto este não fechar.**

---

# 9. HISTOGRAMA de tamanho de bolha ⭐

`Plots → New Plot → Histogram`

| Propriedade | Valor |
|---|---|
| **Parts** | **`vol_aerador`** |
| **X-Axis Scalar** | **Sauter Mean Diameter** |
| **Number of Bins** | **40** |
| **Range** | Manual: **0 a 4.0e-3 m** |
| **⭐ Weighting Function** | **`ar_vol`** |

## ⚠️ A ponderação é o ponto crítico
Sem ponderar, o histograma conta **células** — e a maioria das células do aerador **não tem ar
nenhum**. O resultado seria a distribuição espacial da malha, não da bolha.

> Ponderando por **`ar_vol` (= VF de ar × volume da célula)**, cada barra passa a significar
> **"quanto VOLUME DE AR existe nessa faixa de tamanho"** — que é a distribuição física.
>
> *É a mesma advertência da KB000033031 da Siemens sobre histogramas de parcels: "the histograms
> are weighted with particle count" para mostrar a distribuição de partículas e não de parcelas.*

## Leitura
Da curva acumulada saem **D10 · D50 · D90**, comparáveis direto com o estudo anterior:

| | lanças passivas (anterior) | ejetor (este estudo) |
|---|---|---|
| SMD médio | 2,53 mm | ? |
| moda | 1,90 mm | ? |
| D10 | 1,43 mm | ? |
| D50 | 2,32 mm | ? |
| D90 | 3,57 mm | ? |
| **<200 µm** | **~0 %** | **?** ⭐ |

---

# 10. SCENES — configuração detalhada

## Cena 1 — `VF_ar` ⭐ *(a principal)*
```
Scenes → New Scene → Scalar
  Displayer 1 (o ar):
     Parts        = ar_no_tanque   (threshold VF_ar > 0,01)
     Scalar Field = Volume Fraction of Ar
     Color Map    = blue-red balanced
     Range        = Manual 0 a 0,3
     Contour Style= Smooth Filled
  Displayer 2 (o contorno):
     New Displayer → Geometry
     Parts        = superfície do tanque (todas as boundaries de parede)
     Opacity      = 0,15
     Color        = cinza
```

## Cena 2 — `SMD` no corte
```
Scalar Scene
  Parts        = corte_vertical
  Scalar Field = Sauter Mean Diameter
  Range        = Manual 0 a 3.0e-3
  Color Map    = blue-red balanced
  + Geometry displayer com Opacity 0,15
```
> Coloque uma **linha de referência em 2,0e-4** no color bar (o alvo de 200 µm) — assim se
> enxerga na hora se alguma região atinge a meta.

## Cena 3 — `velocidade`
```
Parts = corte_vertical · Scalar = Velocity Magnitude
Range = Manual 0 a 25 m/s   (o bico dá ~20 m/s)
```

## Cena 4 — `bico_zoom` ⭐ *(mostra o jato)*
```
Parts  = corte_vertical
Scalar = Velocity Magnitude · Range 0 a 25
Câmera : Focal Point (0.025, -0.440, 1.855)
         Position    (0.025, -0.940, 1.855)
         Parallel Scale = 0.06     ← enquadra ~120 mm
```
Mostra os 7 jatos saindo dos furos Ø9 e a esteira até a lança.

## Cena 5 — `pressao_ejetor` ⭐⭐ *(a que explica a causa)*
```
Parts  = corte_vertical
Scalar = Absolute Pressure
Range  = Manual 195000 a 260000 Pa      (1 kgf/cm² man. = 199.392 Pa abs)
Câmera : Focal Point (0.025, -0.440, 2.20)
         Position    (0.025, -1.200, 2.20)
         Parallel Scale = 0.45          ← enquadra do bico ao header
+ Anotação de texto na cota da porta de ar
```
> **A imagem que fecha meses de discussão:** se a porta de ar aparecer em **vermelho/laranja**
> (pressão ACIMA de 199.392 Pa) em vez de azul, fica visível que **o ar não tem como entrar** —
> sem precisar de uma equação. Some com a Cena 4 e você tem a explicação completa em duas figuras.
