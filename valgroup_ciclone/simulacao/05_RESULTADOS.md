# RESULTADOS — CFD do Ciclone Valgroup

> Registro acumulativo das rodadas. Geometria: **Stairmand Dc=290 mm** ·
> Malha: **486.990 células** (Face Validity 100% em 1,0 · Volume Change mín 1,1e-2)
> Condição: gás **1820 kg/h** (= 1900 − 80 de particulado) a 400°C / 1,2 bar · ρ=3,946 · µ=9,5e-5

---

## RODADA 1 — 100% da vazão, só gás, K-Omega SST steady ✅

| | valor |
|---|---|
| v_i (entrada) | 15,23 m/s |
| Convergência | ~6.400 iterações, ΔP plano |
| **ΔP (CFD)** | **2.823,9 Pa = 28,24 mbar** |
| ΔP (analítico Stairmand ξ=6,4) | 2.928,9 Pa = 29,29 mbar |
| **Erro CFD × analítico** | **3,6 %** ✅ |
| Limite do cliente | 40 mbar → **folga de 29%** ✅ |

**Checagem cruzada — o fator de perda:**
`ξ_CFD = ΔP/(½ρv_i²) =` **6,17** vs **6,40** tabelado para Stairmand HE
→ a geometria se comporta como um Stairmand de verdade.

**Campo de Total Pressure:** padrão clássico e correto — alta pressão no **anel externo**,
**núcleo de baixa pressão** no eixo e no vortex finder (mín. −251 Pa), gradiente radial forte.

> **Valida de uma vez:** geometria · malha · BCs · modelo físico · **e o dimensionamento analítico**.

---

## RODADA 2 — 50% da vazão ⏳
| | previsão | CFD |
|---|---|---|
| v_i | 7,62 m/s | — |
| ΔP | **733 Pa (7,33 mbar)** | *(a preencher)* |

*Faixa de aceite: 650–800 Pa. Se cair aí, temos **dois pontos** validados — o modelo vira curva, não ponto.*

---

## 🌡️ E a TEMPERATURA? (pergunta do Gabriel — resposta com número)

**Sim, vamos fazer CHT — mas depois, e por bons motivos.**

### 1. A temperatura NÃO invalida o que já rodamos
| Cenário | Perda de calor | Queda de T do gás |
|---|---|---|
| **Sem** isolamento (U≈10 W/m²K) | 5,20 kW | **5,1 °C** |
| **Com** lã mineral (U≈3) | 1,56 kW | 1,5 °C |

O gás cai **poucos graus** (a residência é só **0,48 s**) → a densidade muda **<1%** →
**o ΔP praticamente não muda.** ✅ **A validação de 3,6% continua valendo.**

### 2. O CHT responde outra pergunta — a do Lucas
Não é sobre ΔP, é sobre **condensação**: *"a parede fica acima do ponto de orvalho (~250°C)?"*

Estimativa preliminar (h_int≈75 W/m²K pelo swirl forte):
| Cenário | T_parede estimada |
|---|---|
| Sem isolamento | **~356 °C** ✅ |
| Com isolamento | ~390 °C ✅ |

→ **Margem confortável** mesmo sem isolamento. **Mas** o CFD com CHT é que crava os
**pontos frios locais** (ápice do cone, flanges, saída de pó) — que a conta global não vê.

### 3. Por que CHT depois e não agora
| Motivo | |
|---|---|
| **Precisa da espessura de parede** | ainda a calcular (corrosão HCl + erosão do char mineral) |
| **Precisa decidir isolamento** | decisão de projeto ainda aberta |
| **É outro entregável** | eficiência de coleta (Lagrangeano) é o principal |
| **Sequência correta** | hidrodinâmica ✅ → partículas → térmica |

---

## 📋 Sequência do estudo
- [x] **1.** Gás steady 100% → **ΔP validado (3,6%)** ✅
- [ ] **2.** Gás steady 50% → 2º ponto de validação
- [ ] **3.** Lagrangeano 100% e 50% → **curva de eficiência η × d** ⭐ *(entregável principal)*
- [ ] **4.** Transiente (URANS + Curvature Correction) → PVC e seu efeito nos finos
- [ ] **5.** RSM → confirmar/refinar o campo de swirl
- [ ] **6.** **CHT** → T_parede > orvalho (~250°C) + espessura de parede
- [ ] **7.** Erosão → mapa de desgaste (char com 21% de minerais)
