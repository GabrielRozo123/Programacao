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
