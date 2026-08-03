# Setup de MALHA — domínio acoplado aerador + reator + ejetor

> Para `ACOPLADO_aerador_reator_ejetor_fluido.step` (1 sólido, 169,353 m³).
> Estimativa: **~15 M células** + prismas → **~19 M**.

---

## 1. Shape Parts a criar (`Geometry → Parts → New Shape Part`)

### ⭐ VC1 — BICOS + jato · **4 Cilindros** *(o mais crítico)*
| | Start | End | Radius |
|---|---|---|---|
| cil. 1 | (−325, −440, **1641**) | (−325, −440, **1900**) | **35 mm** |
| cil. 2 | (25, −440, 1641) | (25, −440, 1900) | 35 mm |
| cil. 3 | (375, −440, 1641) | (375, −440, 1900) | 35 mm |
| cil. 4 | (725, −440, 1641) | (725, −440, 1900) | 35 mm |

Cobre: contração 4"→2" (z 1866–1891) · **bico 7×Ø9** (z 1841–1866) · **200 mm de jato** abaixo.

### VC2 — LANÇAS · **4 Cilindros**
| | Start | End | Radius |
|---|---|---|---|
| cil. 1–4 | (x, −440, **−5246,5**) | (x, −440, **1641**) | **40 mm** |

com x = −325 · 25 · 375 · 725

### VC3 — DESCARGA no aerador · **1 Cilindro**
| Start | End | Radius |
|---|---|---|
| (200, −440, **−5350**) | (200, −440, **−4200**) | **700 mm** |

Cobre a pluma dos 4 jatos ao entrar no tanque.

### VC4 — CABEÇA DO EJETOR · **1 Block**
| Corner 1 | Corner 2 |
|---|---|
| (−400, −520, **1890**) | (800, −180, **2830**) |

Cobre header 8" · ramais 4" · **4 portas de ar 1/2"** · entrada de xarope.

---

## 2. Automated Mesh — controles padrão

```
Meshers:  Surface Remesher · Polyhedral Mesher · Advancing Layer Mesher
```

| Parâmetro | Valor | Por quê |
|---|---|---|
| **Base Size** | **30 mm** | alvo do volume do tanque |
| Target Surface Size | 100 % da base | |
| **Minimum Surface Size** | **3,3 % (= 1,0 mm)** | ⚠️ **tem de caber no furo Ø9** |
| **Surface Curvature** | **72 pts/circle** | resolve os furos e as circunferências |
| Surface Growth Rate | 1,3 | |
| **Volume Growth Rate** | **1,1** | conservador → transição suave, menos célula ruim |
| Number of Prism Layers | **3** | ver §4 |
| Prism Layer Stretching | 1,2 | |
| **Prism Layer Total Thickness** | **RELATIVE, 20 % da base** | ⚠️ **relativo, não absoluto** — senão o prisma de 12 mm não cabe na célula de 1 mm do bico |

---

## 3. Volumetric Controls (`Automated Mesh → Volumetric Controls → New`)

| Control | Parts | Custom Size | Células |
|---|---|---|---|
| **`VC1_bicos`** | 4 cilindros VC1 | **1,0 mm** (3,3 % da base) | ~4,0 M |
| `VC2_lancas` | 4 cilindros VC2 | **4,0 mm** (13 %) | ~2,2 M |
| `VC3_descarga` | cilindro VC3 | **10 mm** (33 %) | ~1,8 M |
| `VC4_cabeca` | bloco VC4 | **8,0 mm** (27 %) | ~0,8 M |
| *(base)* | resto | 30 mm | ~6,2 M |

Em cada control: marque **Surface Remesher** e **Volume Mesh** (para o refino valer nos dois).

### Verificação de resolução
| região | célula | dimensão local | células no diâmetro |
|---|---|---|---|
| **furo do bico Ø9** | 1,0 mm | 9 mm | **9** ✅ |
| garganta Ø42,8 | 1,0 mm | 42,8 mm | 43 ✅ |
| lança Ø62,7 | 4,0 mm | 62,7 mm | **16** ✅ |
| **porta de ar Ø15,8** | 8,0 mm | 15,8 mm | **2** ⚠️ |

> ⚠️ **A porta de ar de Ø15,8 fica com só 2 células no diâmetro com o VC4 a 8 mm.**
> Se a vazão de ar for uma resposta importante, **crie um VC5 só nas 4 portas**:
> 4 cilindros r = 15 mm, de (x, −440, 2208,5) a (x, −190, 2208,5), célula **1,5 mm**.
> Custo: desprezível (~0,05 M).

---

## 4. Nota sobre camadas de prisma

O xarope tem **µ = 6,5 Pa·s**. Números de Reynolds:

| seção | v | Re |
|---|---|---|
| lança Ø62,7 | 2,92 m/s | **≈ 37** |
| furo do bico Ø9 | 20,27 m/s | **≈ 36** |

**O ejetor inteiro é LAMINAR.** Não há camada-limite turbulenta para resolver — as 3 camadas de prisma servem só para o gradiente viscoso junto à parede, e **thickness relativo** evita que elas quebrem a malha fina do bico.

*(No reator, com o impelidor, a situação é outra — mas ali a base de 30 mm já é adequada.)*

---

## 5. Ordem de execução recomendada
1. Criar os **10 shape parts** (9 cilindros + 1 bloco)
2. Criar o Automated Mesh com os controles padrão
3. Criar os **4 (ou 5) volumetric controls**
4. **Gerar só a malha de superfície primeiro** — conferir se os furos Ø9 ficaram com ~9 células
5. Só então gerar o volume

> 💡 **Nomeie as boundaries ANTES de malhar.** O prism layer mesher não cria prismas em flow
> boundaries — se você malhar com tudo ainda `Wall`, sobram prismas nas entradas.
> *(lição do tutorial do ciclone)*
