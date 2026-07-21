# Tabela final — Impelidor NOVO vs Original (orientada aos objetivos do Ito)

> Fecha a caracterização do impelidor da Fase 2. Nq convergido em 21/07 (Surface Integral achatou).

## 🎯 Os objetivos do Ito (recall — nunca esquecer)
1. **Flotação:** gerar microbolha < 200-300 µm p/ flotar impurezas. → *aerador/ejetor* (Fase 1: **pressão não
   é a alavanca**; alavanca = viscosidade + cisalhamento na formação; ejetor em estudo).
2. **Impelidor (ESTE estudo):** o novo design entrega **mais mistura no reator** — e cabe no **orçamento de
   potência (< 25 kW)** do acionamento?

## ❓ Por que rodamos com o impelidor novo?
Ito decidiu (via Marcus) testar um impelidor **turbinado** — todos os incrementos juntos:
**Ø800→880 · 30°→31,5° · 3→4 pás · 109→120 rpm** — tudo somado para **bombear/misturar mais**.
O **risco:** potência escala com **N³·D⁵** — mais diâmetro + mais rpm + mais pás pode **estourar o motor (25 kW)**.
**O CFD responde ANTES da compra do equipamento:** (a) cabe no orçamento de 25 kW? (b) quanto ganha de mistura
vs o atual? → decisão de hardware **embasada, não no chute**.

## Tabela (não-dimensional + o que o Ito enxerga)
| Grandeza | Original Ø800/3pás/30°/109 rpm | **NOVO Ø880/4pás/31,5°/120 rpm** | Δ |
|---|---|---|---|
| **P — Potência** ⭐ | 4,07 kW | **9,90 kW** | **+143% (2,43×)** |
| **Meta P < 25 kW** ⭐ | ✅ | ✅ **folga 60%** (usa 40% do motor) | — |
| **Q — bombeamento** ⭐ | 1.158 m³/h | **1.588 m³/h** | **+37%** |
| **Tempo de circulação** (V≈125 m³) | ~6,5 min | **~4,7 min** | **−27% (mistura mais rápida)** |
| Np/estágio (nº de potência) | 0,76 | 0,86 | +13% |
| Nq (nº de bombeamento) | 0,345 | 0,32 | −7% |
| Nq/Np (eficiência de bombeamento) | 0,45 | 0,37 | **−18%** |
| Velocidade de ponta | 4,58 m/s | 5,54 m/s | +21% |
| Reynolds (Re=ρND²/µ, µ=6,5 Pa·s) | ~233 | ~310 | transição/laminar (viscoso) |

⭐ = as linhas que respondem os objetivos do Ito.

## 📖 Leitura pro Ito (a mensagem)
1. **✅ Cabe no motor, com FOLGA.** 9,9 kW = **40% do orçamento** de 25 kW. Zero risco de estourar — o novo
   impelidor **pode ser instalado** sem trocar acionamento.
2. **✅ Mistura melhora concretamente:** **+37% de bombeamento** (1.158→1.588 m³/h) → o reator **homogeneíza
   ~27% mais rápido** (circulação 6,5→4,7 min).
3. **⚠️ O custo:** a mistura extra sai a um **custo de potência desproporcional** (Nq/Np cai 18% → menos
   eficiente por kW). Mas como sobra orçamento, é um **trade seguro** — mais mistura por mais potência, dentro do limite.
4. **Regime viscoso** (Re ~230-310, transição): o xarope a 6,5 Pa·s mantém a mistura no regime **laminar/transição**
   — normal, e coerente com a física dominada por viscosidade que aparece no aerador/ejetor.

**Veredito:** o upgrade é **viável e melhora a mistura** — a decisão "vale +37% de mistura por +143% de potência?"
é de **processo (Ito)**, mas o CFD garante que **não há risco de potência** e quantifica o ganho. Objetivo do
impelidor: **respondido.** ✅

> **Nota de escopo:** este impelidor é do **REATOR** (agitação, monofásico). As **bolhas** são do **AERADOR/
> ejetor** — tanque separado (Fase 1 + estudo do ejetor). Não se rodou "com bolhas" no reator porque ele **não
> é aerado**; o steady MRF monofásico é o entregável **completo** do impelidor.
