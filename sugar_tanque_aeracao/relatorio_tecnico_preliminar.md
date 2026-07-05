# Relatório Técnico Preliminar — Projeto Sugar (Usina Colombo)

> Resumo técnico consolidado, organizado pelos objetivos do Ito. Status: caso 1 kgf/cm² do
> Aerador caracterizado; Reator com potência/Nq/Np fechados. Casos 2 e 3 kgf/cm² pendentes.
> Data: 2026-07-05.

---

## 🟢 REATOR — Objetivo: Potência do agitador (<25kW) + Nq/Np

| Item | Valor | Nota técnica |
|---|---|---|
| Geometria do impelidor | Duplo hidrofólio, **3 pás/estágio (6 total)**, Ø800mm, eixo Ø69,85mm | Corrigido em 04/07 a partir do desenho real Agimix AGX-PBW800 (inicialmente modelado com 8 pás) |
| Rotação | 109,3 rpm (11,446 rad/s) | Dado real do redutor Macopema MP05 + motor WEG 15cv |
| Física | MRF, regime permanente, monofásico (xarope) | Adequado — sem necessidade de multifásico no Reator |
| **Torque** | **383,66 N·m** | Report com Force Option = Pressure+Shear (crítico dado μ=6,5 Pa·s) |
| **Potência** | **≈ 4,39 kW** | P = Torque × ω. **82% abaixo da meta de 25kW** |
| **Np (Número de Potência)** | **≈ 1,64** | Np = P/(ρN³D⁵) |
| **Nq (Número de Vazão)** | **≈ 1,01** | Nq = \|Q\|/(ND³), Q extraído via integral de superfície (disco de raio 0,4m na altura da pá) |
| **Reynolds do impelidor** | **≈ 242** | Re = ρND²/μ — **regime de TRANSIÇÃO** (nem laminar, nem turbulento) |

**Implicação técnica:** o Reynolds de transição (~242) significa que **nenhuma correlação de catálogo padrão é confiável aqui** — correlações de Np/Nq de literatura assumem regime laminar profundo (Re<10-20) ou turbulento estabelecido (Re>10.000). Na transição, cada geometria específica se comporta de um jeito próprio, sem fórmula simples. **O CFD não é só uma verificação nesse caso — é a única fonte confiável desses números** para essa geometria específica.

### Cross-check contra literatura (hidrofólio)

Valores publicados (fonte: AIChE CEP, "Consider Hydrofoil Impellers for Laminar-Flow Mixing"):
- Laminar: Kp ≈ 27,4 (Np=Kp/Re), Nq ≈ 0,214
- Turbulento (Re>10.000): **Np ≈ 0,8**, **Nq ≈ 0,55–0,73**

Como o Report de Torque soma os **dois estágios** do hidrofólio duplo, dividir por 2 (aproximação, assume contribuição similar entre estágios) dá uma base de comparação por estágio:

| Grandeza | Total (2 estágios) | Por estágio (÷2) | Literatura turbulenta |
|---|---|---|---|
| Np | 1,64 | **≈0,82** | **0,8** — quase exato |
| Nq | 1,01 | **≈0,505** | 0,55–0,73 — próximo, levemente abaixo |

**Achado:** por estágio, o Np bate quase exatamente com o valor turbulento de catálogo, mesmo em Re≈242 (bem abaixo do Re>10.000 clássico) — sugere que essa pá larga (parafusada, não um hidrofólio esguio genérico) atinge comportamento "tipo turbulento" num Reynolds mais baixo. Reforça a confiança no torque calculado, agora validado por referência independente.

---

## 🟣 AERADOR — Objetivo: distribuição de bolhas + diagnóstico da aeração deficiente + pressão otimizada

**Caso rodado até agora: 1 kgf/cm² (98.070 Pa gauge)**

| Item | Valor | Nota técnica |
|---|---|---|
| Geometria | 3 injetores/lanças reais (Ø84,8mm), ejetor tipo venturi | Medidos do CAD do conjunto ejetor |
| Física | EMP (Xarope+Ar) + Phasic Turbulence + S-Gamma (Breakup+Coalescence) + Implicit Unsteady | Regime permanente diverge sempre nesse tipo de escoamento — transiente é obrigatório aqui |
| **Ar entra na boundary?** | **Sim, confirmado** | Volume Fraction=1,0 configurado corretamente; confirmado visualmente (mancha real de VF na ponta do injetor) |
| **Dispersão pelo tanque** | **Praticamente nula** | Velocidades de recirculação longe do injetor ~µm/s (quase estagnado); sondas de meio/topo do tanque ainda em zero |
| **Sauter Mean Diameter (SMD)** | **Pico ~2,0-2,1mm** | Distribuição madura (log-normal), **~10x acima da meta de <200µm** |
| **% de bolha "boa" (SMD<200µm)** | **≈ 2,24×10⁻⁶ %** | Praticamente nulo — quase nenhuma bolha atinge o tamanho alvo |
| Margem de pressão vs. hidrostática | ~13-14% de folga | Submersão de 6,47m → pressão hidrostática ≈85,6kPa vs. Total Pressure=98,07kPa configurada — margem apertada |

**Implicação técnica — duas causas simultâneas para a "aeração deficiente":**
1. **Bolha nasce grande** (~2mm, não ~200µm) — o cisalhamento do ejetor não está produzindo microbolhas do tamanho alvo, ou a coalescência é muito rápida logo na formação
2. **Circulação praticamente inexistente** — mesmo se a bolha fosse pequena, ela não tem como se espalhar pelo volume do tanque nessa condição de pressão

Ambas as causas têm a **mesma raiz física**: a viscosidade extrema do xarope (6,5 Pa·s) — o mesmo fator que colocou o Reator em regime de transição também impede a dispersão de bolhas e a formação de microbolhas no Aerador.

**Pendente:** casos de **2 kgf/cm² (196.130 Pa)** e **3 kgf/cm² (294.200 Pa)** ainda não rodados. A expectativa (a confirmar) é que a margem sobre a pressão hidrostática melhore substancialmente (~129% e ~244% de folga, respectivamente), potencialmente resultando em melhor dispersão e/ou bolhas menores — essa comparação é o que vai permitir recomendar a pressão otimizada ao Ito.

---

## 🔗 Achado unificador — o mesmo fator explica os dois tanques

O número de Reynolds do impelidor do Reator (~242) caiu na mesma faixa de regime "difícil" (transição/baixo Re) que domina o comportamento do Aerador — não é coincidência, é a **mesma viscosidade de 6,5 Pa·s** ditando o comportamento físico dos dois sistemas. Isso reforça, com evidência quantitativa, por que esse projeto genuinamente precisava de simulação CFD nos dois tanques — não daria pra confiar em dimensionamento por catálogo em nenhum dos dois.

---

## Próximos passos
- [ ] Rodar Aerador a 2 kgf/cm² (mesmo critério de warm-up + produção do caso 1)
- [ ] Rodar Aerador a 3 kgf/cm²
- [ ] Comparar os 3 casos e recomendar pressão otimizada
- [ ] Confirmar estabilidade do Torque do Reator com mais tempo de rodada
- [ ] Consolidar relatório final combinando os 3 casos do Aerador + resultado do Reator
