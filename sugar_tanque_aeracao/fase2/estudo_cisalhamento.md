# Estudo do cisalhamento — o que favorece? (pergunta do Ito, 21/07)

> **Pergunta do Ito na reunião:** *"Quais condições/parâmetros favorecem mais o cisalhamento?"* + *"vale gastar
> mais potência para cisalhar mais?"* (tem folga: 9,9 kW << 25 kW). Este doc é a **álgebra** que responde.

## Por que cisalhamento é a palavra da vez
A quebra da bolha é governada pela **tensão viscosa** `τ = µ·γ̇` vencendo a de Laplace (nº de capilaridade
`Ca = µ·γ̇·a/σ`). **Mais taxa de cisalhamento γ̇ → mais quebra → bolha menor → melhor flotação.** A Fase 1
provou: a viscosidade (6,5 Pa·s) **suprime** a quebra; a alavanca é **γ̇** (cisalhamento), não a pressão.

## As leis de escala (a base)
| Grandeza | Escala | Nota |
|---|---|---|
| Cisalhamento **médio** | `γ̇ ≈ k_s·N` (Metzner-Otto, k_s≈11) | ∝ **rotação N** apenas |
| Cisalhamento de **ponta** (onde quebra) | `γ̇_max ∝ v_ponta = π·D·N` | ∝ **tip speed (D·N)** |
| **Potência** (viscoso→transição) | `P ∝ µ·N²·D³` (laminar) … `ρ·N³·D⁵` (turbulento) | Re~300 → entre os dois |

*(Estamos em Re ~ 300 — transição/laminar viscoso. Os expoentes ficam entre os dois limites, mas as conclusões
qualitativas abaixo valem nos DOIS regimes.)*

## Otimização — máximo cisalhamento a potência FIXA (25 kW)
Fixando `P` (laminar): `N²·D³ = const`. Substituindo:
- **γ̇_médio ∝ N ∝ D^(−1,5)** → cresce quando **D diminui**.
- **v_ponta ∝ D^(−0,5)** → idem.

**Ou seja: a potência fixa, um impelidor MENOR e MAIS RÁPIDO cisalha MAIS** (concentra a energia numa zona de
alto cisalhamento, em vez de espalhar em circulação). *(No turbulento a dependência é ainda mais forte, `D^(−5/3)`.)*

## 🎯 Resposta direta — os 3 parâmetros
| Parâmetro | Para MAIS cisalhamento | Por quê |
|---|---|---|
| **Rotação N** | ⬆️ **aumentar** | `γ̇ ∝ N` direto — a alavanca mais direta (mas P ∝ N²–N³, custa) |
| **Diâmetro D** | ⬇️ **diminuir** (a potência fixa) | menor D concentra a energia em cisalhamento, não em bombeamento |
| **Ângulo das pás** | ➡️ **mais radiais** (pás mais retas/verticais) | radial cisalha; axial (hidrofólio) bombeia |

## "Vale gastar mais potência?" — Sim, mas com RETORNO DECRESCENTE
A geometria fixa, `γ̇ ∝ N` e `P ∝ N²` (laminar) a `N³` (turbulento) → **`γ̇ ∝ √P` a `P^⅓`**.
Folga 9,9 → 25 kW = **2,5×** de potência → só **~1,4–1,6× mais cisalhamento** (acelerando). **Vale, mas não é
linear** — dobrar o cisalhamento pede ~4× a potência. *(Bom argumento pro Ito: a folga ajuda, mas não é mágica.)*

## ⚖️ O TRADE-OFF central (o insight que fecha a história)
**Cisalhamento** (pequeno · rápido · radial) **×** **Circulação/bombeamento** (grande · lento · axial) = **OPOSTOS.**
O impelidor atual (Ø880, 4 pás, 31,5°, tipo **axial/hidrofólio**) é **pró-FLUXO** (Nq alto, bom pra misturar).
**Para cisalhar mais, vai no sentido OPOSTO:** menor, mais rápido, pás mais radiais — ao custo de menos circulação.
*(Não dá pra maximizar os dois; é escolher onde no espectro fluxo↔cisalhamento operar.)*

## ⚠️ A pergunta de ESCOPO que decide TUDO (confirmar com o Ito)
**Onde a bolha quebra — no impelidor (reator) ou no ejetor (venturi)?**
- A Fase 1 apontou a quebra na **FORMAÇÃO (injetor/venturi)** → o cisalhamento que importa é o do **EJETOR**, não
  o do impelidor do reator (tanque separado, sem bolha).
- **A MESMA álgebra vale no ejetor:** `γ̇_garganta = 2·v/D_garganta` → **garganta menor + velocidade maior = mais
  cisalhamento** (e é o parâmetro nº 1 da parametrização do ejetor, §7 da metodologia).
- **Se** o processo for um tanque **agitado + aerado** (impelidor e ar juntos) → aí sim o cisalhamento do impelidor
  quebra a bolha, e a parametrização (D↓, N↑, radial) é direta.

**→ Perguntar ao Ito:** o cisalhamento pra quebrar a bolha é no **ejetor** (onde ela nasce) ou o impelidor
**agita o mesmo tanque** que é aerado? Isso decide **qual device otimizar** (mesma física, device diferente).

## Próximo passo (quando confirmado o device)
- Se **ejetor:** varrer `D_garganta` e `v` (já previsto na metodologia) → curva γ̇ × geometria → tamanho de bolha.
- Se **impelidor:** varrer `D`, `N`, ângulo a `P ≤ 25 kW` → mapa de γ̇ (médio e de ponta) → identificar o ponto
  de máximo cisalhamento dentro do orçamento, mostrando o trade-off com o Nq (circulação).
