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

## RODADA 2 — 50% da vazão ✅

| | valor |
|---|---|
| v_i | 7,62 m/s |
| **ΔP (CFD)** | **642,8 Pa = 6,43 mbar** |
| ΔP (analítico) | 733,2 Pa = 7,33 mbar |
| **Erro** | **12,3 %** ✅ |

**Escalonamento:** ΔP(100%)/ΔP(50%) = **4,39** (teórico v² = 4,00).
**ξ extraído:** 6,17 (100%) → **5,61** (50%) — cai suavemente com o Reynolds, **fisicamente esperado**.

> ✅ **DOIS pontos validados.** O modelo deixou de ser "acertou num ponto" e virou **curva**.

### Resumo da validação
| Carga | v_i | ΔP CFD | ΔP analítico | erro | ξ |
|---|---|---|---|---|---|
| **100%** | 15,23 m/s | **2.823,9 Pa** | 2.928,9 | **3,6%** | 6,17 |
| **50%** | 7,62 m/s | **642,8 Pa** | 733,2 | **12,3%** | 5,61 |

Ambos **muito abaixo** do limite de 40 mbar. A 50% sobra folga enorme (84%).

---

## RODADA 3 — 100% da vazão **COM ENERGIA** (gás ideal + CHT) ✅

**Contexto:** primeira tentativa com `Ideal Gas` deu **ΔP = 381 Pa** (contra 2.823,9 do constant-density).
**Causa:** `Molecular Weight` ficou no default do ar (**28,96**) → ρ = 0,621 em vez de 3,946
(**6,35× baixo**). Diagnóstico previu 444 Pa; observado 381 → confirmado.
**Correção:** `Molecular Weight = 184,0 kg/kmol` (o gás de pirólise, não ar).

| | valor |
|---|---|
| **ΔP (CFD, gás ideal, M=184)** | **2.893,98 Pa = 28,94 mbar** (it. 9.526) |
| ΔP (constant density) | 2.823,9 Pa |
| ΔP (analítico Stairmand ξ=6,4) | 2.928,9 Pa |
| **Erro × analítico** | **−1,2 %** ✅ *(melhor que os 3,6 % do constant-density)* |
| **ξ extraído** | **6,32** (tabelado: 6,40) |
| Limite do cliente | 40 mbar → **folga de 28 %** ✅ |

> A energia **subiu** o ΔP em 2,5 % (o gás resfria junto à parede → densifica localmente).
> Confirma a previsão de que a térmica **não invalida** a validação hidrodinâmica.

### 🌡️ Temperatura de parede — a pergunta do Lucas, respondida

| | valor |
|---|---|
| **T_parede (CFD)** | **654,142 K = 381,0 °C** (it. 8.882) |
| Estimativa analítica prévia (sem isolamento) | ~356 °C |
| **Ponto de orvalho dos pesados (C12–C15)** | ~250 °C |
| **MARGEM** | **+131 °C** ✅ |

> ✅ **Sem condensação.** E a estimativa analítica (356 °C) errou por só 25 °C para menos —
> ou seja, era **conservadora**, como deveria ser.

### Resumo das três rodadas
| Rodada | Modelo | v_i | **ΔP CFD** | analítico | erro | ξ |
|---|---|---|---|---|---|---|
| 1 · 100 % | K-ω SST, ρ const | 15,23 m/s | 2.823,9 Pa | 2.928,9 | 3,6 % | 6,17 |
| 2 · 50 % | K-ω SST, ρ const | 7,62 m/s | 642,8 Pa | 733,2 | 12,3 % | 5,61 |
| **3 · 100 %** | **K-ω SST + energia (ideal, M=184)** | 15,23 m/s | **2.893,98 Pa** | 2.928,9 | **1,2 %** | **6,32** |

> 🏁 **ETAPA A (hidrodinâmica + térmica) ENCERRADA E VALIDADA.**
> A base está pronta para receber as partículas.

### 📌 Armadilha registrada (nº 5)
**`Ideal Gas` sem ajustar `Molecular Weight`** → o STAR usa o default do ar (28,96) e a densidade sai
errada por um fator, silenciosamente. **Sempre setar M junto com o modelo de gás ideal.**
Aqui: **M = 184 kg/kmol**.

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
- [x] **2.** Gás steady 50% → **2º ponto validado (12,3%)** ✅
- [x] **3.** **Energia/CHT** → **ΔP 1,2% · T_parede 381 °C > orvalho 250 °C** ✅
- [ ] **4.** Lagrangeano 100% e 50% → **curva de eficiência η × d** ⭐ *(entregável principal)* ← **AGORA**
- [ ] **5.** Transiente (URANS + Curvature Correction) → PVC e seu efeito nos finos
- [ ] **6.** RSM → confirmar/refinar o campo de swirl
- [ ] **7.** Espessura de parede (corrosão HCl + erosão) + decisão de isolamento
- [ ] **8.** Erosão → mapa de desgaste (char com 21% de minerais)

---

## ▶️ RODADA 4 (a rodar) — 50 % da vazão **COM ENERGIA**

**Por que ela é necessária e não é redundante:** a 50 % o tempo de residência **DOBRA**
(0,48 → 0,96 s) e o coeficiente de troca interno **CAI** (h ∝ Re^0,8 → ×0,57). O gás fica mais
tempo trocando calor e troca com um filme mais fraco → **a parede esfria**.
**O caso de 50 % é o caso GOVERNANTE para a pergunta do orvalho**, não o de 100 %.

Setup: **só mudar `Inlet → Velocity Magnitude` de 15,23 para 7,62 m/s** e a intensidade
turbulenta (0,041 → 0,045). Tudo o mais permanece. Reiniciar do campo convergido a 100 %.

### Previsões (registradas ANTES de rodar — falseáveis)
| | previsto |
|---|---|
| **ΔP** | **655–670 Pa** (642,8 do constant-density × 1,025 da energia = **659 Pa**) |
| **T_parede** | **355–370 °C** (queda de ~15–25 °C vs os 381 °C a 100 %) |
| Queda de T do gás ao longo do ciclone | ~6 °C (era ~5 °C a 100 %) |

> ✅ Se a T_parede cair para essa faixa → **margem sobre o orvalho continua > 100 °C** e a
> resposta ao Lucas fica fechada **nos dois extremos de operação**: *não condensa em nenhum ponto
> do turndown*. Aí sim o isolamento vira decisão de eficiência energética, não de integridade.
>
> ⚠️ Se cair **abaixo de 300 °C**, o quadro muda: o isolamento deixa de ser opcional e passa a ser
> requisito de projeto. Vale a pena saber disso **antes** de gastar o Lagrangeano.
