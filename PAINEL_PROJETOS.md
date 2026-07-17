# 🗼 PAINEL DE CONTROLE — Projetos CFD (Gabriel / CAEXPERTS)

> **Torre de controle.** Bata o olho aqui pra saber onde está tudo. Atualizado: **2026-07-17**.
> Cada projeto tem seu `STATUS.md`/`README.md` detalhado — este painel é o **resumo de uma olhada**.

## Semáforo (uma linha por projeto)
| Projeto | Cliente | 🚦 | Onde está |
|---|---|---|---|
| 🧪 **Ito** (sugar) | CAEXPERTS | 🟢 | Fase 1 entregue. Impelidor rodado; **fechando torque/Nq**. Ejetor: falta σ. |
| 🌀 **Valgroup** (ciclone) | CAEXPERTS | 🟡 | Setup CFD verificado + geometria. **Travado: reconciliar vazão 800 vs 1900** + orvalho. |
| 🍺 **Cerveja** (chiller) | GreyLogix | 🟢 | **3 sims fechadas + verificadas** (baseline, Sim 1, Sim 2 recirc). Achado: recirc **uniformiza** (ΔT ½) mas **não acelera** (é trade-off). Faltam checagens de robustez. |
| 🌴 **FOXTERMO** (cristalização) | novo (Álvaro) | 🔵 | Proposta + estudo prontos. **Falta comercial (Marcus) + dados do Álvaro.** |

---

## 🧪 ITO — Aeração + Reator + Ejetor  (`sugar_tanque_aeracao/`)
- **✅ Feito:** Fase 1 fechada e **apresentada** (reator OK; aerador — *pressão não é a alavanca*). Fase 2:
  **impelidor novo Ø880/31,5°/4pás/120,2rpm RODADO** → T=−786,6 N·m → **P=9,90 kW** (2,43× base, <25 kW), Np/est~0,86.
  Ejetor: metodologia fechada+verificada; vazão motriz **130 m³/h** confirmada.
- **👉 Próximo (VOCÊ):** fechar torque/Nq (report de vazão) → **me mandar o Q** que eu calculo o Nq e a tabela.
- **⏳ Esperando:** **σ ar-xarope** (você busca correlação de *xarope de cana*, tem Brix+densidade).
- **📄 Chave:** `STATUS.md` · `fase2/impelidor_parametrico/execucao_star.md` · `fase2/ejetor/01_metodologia_cfd_ejetor.md`

## 🌀 VALGROUP — Ciclone gás-sólido  (`valgroup_ciclone/`)
- **✅ Feito:** matriz de decisão revisada (**ciclone +11**), Lapple preliminar (D_c≈163mm), **geometria STEP**,
  **setup CFD verificado** (RSM+fase discreta+térmica), **composição do gás analisada** (GC-MS: HC C7–C15).
- **👉 Próximo:** **reconciliar com o Marcus a vazão de gás (800 vs 1900 kg/h)** — muda D_c 163↔265mm! Depois: **calcular o orvalho (VLE)** com a composição, e montar o CFD.
- **⏳ Esperando:** **PSD do char CARREADO** (Marcus) · confirmar µ, ρ_s (partícula, não bulk), T operação (~343 vs 400).
- **📄 Chave:** `dados_cliente/dados_recebidos_15jul.md` · `simulacao/aprendizado_tutorial_ciclone.md` · `dimensionamento/`

## 🍺 CERVEJA — Tanque Chiller (estratificação)  (`cerveja_tanque_chiller/`)
- **✅ Feito:** 6 perguntas respondidas; **2 simulações definidas**; **2 STEPs** (DN150) + guia; **Sim 1 RODADO e
  analisado** (`08_resultado_sim1.md`): pico ΔT 9,6 °C @12 min → **homogeneíza em ~33 min**, **T_bulk −5 °C atingido**;
  estratificação **transitória** (vs persistente do preliminar), sensor de saída **converge** no fim.
- **✅ Baseline 0,85 m** (`09_...md`): homogeneíza, mas ~3× mais lento (curto-circuito). *(Pegou probe bugado — lição.)*
- **✅ Sim 2 recirc RODADO + VERIFICADO** (`10_resultado_sim2.md`, 3 lentes adversariais → coerente): recirc **reduz
  o pico de ΔT pela metade** (9,6→4,7 °C) MAS **resfria ~2× mais devagar** (armazenamento térmico estratificado —
  misturar destrói o deslocamento). **Recirc = uniformidade, não velocidade** (trade-off pro cliente).
- **👉 Próximo:** checagens de robustez (recirc adiabática, fechamento de energia, T_sucção vs bulk, Δt/Courant);
  depois **montar a comparação pro cliente** (Pedro/GreyLogix).
- **⏳ Esperando (não bloqueia):** altura exata dos bocais recirc; confirmar condições/métrica (Pedro).
- **📄 Chave:** `06_setup_sim_star.md` · `geometria/cerveja_sim1_fluido.step` + `_sim2_`

## 🌴 FOXTERMO — Cristalização de óleo de palma  (`foxtermo_cristalizacao/`)
- **✅ Feito:** repo + **proposta técnica** (Rota A base / Rota B avançada, 4 cenários) + **aprendizado de
  cristalização no STAR** (melt, EMP+PBE, reologia de slurry, elo agitador↔cristalização).
- **👉 Próximo:** **Marcus monta o comercial** (prazo/valor); **pedir os dados ao Álvaro** (lista pronta no repo).
- **⏳ Esperando:** dados do Álvaro (geometria, ρ(T)/µ(T), e — p/ Rota B — cinética/reologia).
- **📄 Chave:** `00_proposta_tecnica.md` · `01_cristalizacao_no_star.md`

---

## ✅ O QUE FAZER AGORA (prioridade)
1. **🧪 Ito:** rodar o report de vazão do impelidor → mandar o **Q** (fecha o Nq).
2. **🍺 Cerveja:** Sim 1 ✅ fechado — rodar o **Sim 2 (recirc)** e comparar com o Sim 1.
3. **🌀 Valgroup:** falar com o **Marcus** — reconciliar a **vazão (800 vs 1900)**.
4. **🌴 FOXTERMO:** **pedir os dados ao Álvaro** + Marcus montar o comercial.

## 📨 QUEM DEVE O QUÊ (esperando de terceiros)
| De quem | O quê | Projeto |
|---|---|---|
| **Marcus** | Reconciliar vazão 800 vs 1900 · PSD char carreado · comercial FOXTERMO | Valgroup, FOXTERMO |
| **Ito / literatura** | σ ar-xarope (você busca: xarope de cana) | Ito (ejetor) |
| **Álvaro (FOXTERMO)** | Geometria, ρ(T)/µ(T), cinética/reologia | FOXTERMO |
| **Pedro/EGISA** | Confirmar condições de processo/métrica (não bloqueia) | Cerveja |

## 🧠 "NÃO ESQUECER" (lições e pegadinhas do que já resolvemos)
- **MRF (Ito):** rotação vai na **REGIÃO** (Reference Frame), **não** nas pás. Report de torque = **todas** as faces.
- **Ejetor (Ito):** é **laminar** (Re~40) → sem quebra turbulenta; quebra por cisalhamento **extensional**.
- **Valgroup:** condensação é de **PAREDE**, não do bulk (resposta ao Humberto). RSM, não K-ω. Vazão 800 vs 1900 **é o nó**.
- **Cerveja:** bomba de recirc = **par de BCs** (sem malhar); recirc **adiabática** (T da captação → retorno).
- **Sensor de ponto (STAR):** ❌ **nunca Maximum/Minimum report** (agarra célula parada → falso ΔT) — use
  **Point Probe** ou **Volume Average**. A **Line Probe** é a fonte confiável (pegou o probe bugado do baseline 0,85).
- **Cerveja (contraintuitivo):** com frio no fundo + sucção alta, **misturar NÃO resfria mais rápido** — a
  estratificação faz resfriamento por **deslocamento** (mais eficiente); a recirc homogeneíza → tende ao **CSTR**
  (mais lento). Recirc entrega **uniformidade**, não velocidade. Verificado por benchmark CSTR (τ=V/Q).
- **FOXTERMO:** cristalização óleo palma = **melt**; a **rotação do agitador muda a TAXA de cristalização** (Armenante-Kirwan).
- **Git:** commitar só **fatos** (nunca PDFs proprietários do cliente).
