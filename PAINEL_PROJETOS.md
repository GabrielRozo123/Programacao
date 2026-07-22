# 🗼 PAINEL DE CONTROLE — Projetos CFD (Gabriel / CAEXPERTS)

> **Torre de controle.** Bata o olho aqui pra saber onde está tudo. Atualizado: **2026-07-21**.
> Cada projeto tem seu `STATUS.md`/`README.md` detalhado — este painel é o **resumo de uma olhada**.

## Semáforo (uma linha por projeto)
| Projeto | Cliente | 🚦 | Onde está |
|---|---|---|---|
| 🧪 **Ito** (sugar) | CAEXPERTS | 🟢 | **Impelidor FECHADO** (9,9 kW, Nq=0,32). **Ejetor Trilho 1 (analítico) feito** — proposta do bico justificada. Falta STEP nativo p/ o CFD. |
| 🌀 **Valgroup** (ciclone) | CAEXPERTS | 🟡 | Setup CFD verificado + geometria. **Travado: reconciliar vazão 800 vs 1900** + orvalho. |
| 🍺 **Cerveja** (chiller) | GreyLogix | ✅ | **CONCLUÍDO** (até 2ª ordem). 3 sims verificadas + álgebra + **página** + **PPTX**. Slides entregues pelo Gabriel. Achado: recirc **uniformiza, não acelera**. |
| 🌴 **FOXTERMO** (cristalização) | novo (Álvaro) | 🔵 | Proposta + estudo prontos. **Falta comercial (Marcus) + dados do Álvaro.** |

---

## 🧪 ITO — Aeração + Reator + Ejetor  (`sugar_tanque_aeracao/`)
- **✅ Impelidor FECHADO** (Nq 21/07): **P=9,90 kW** (40% do orçamento de 25 kW), **Nq=0,32**, **bombeamento +37%**
  → upgrade viável. Tabela: `fase2/impelidor_parametrico/tabela_final_impelidor.md`.
- **✅ Ejetor — Trilho 1 (analítico) fechado** (reunião 21/07, feedback positivo): σ=0,058 (literatura); a quebra é
  **extensão/atomização** (λ→0, cisalhamento simples não quebra); **<300 µm exige JATEAMENTO** e o **ar supersônico
  já está nele**; **bolha↓ = jato↑** (furo menor/bico convergente, justificado por literatura). **Proposta do bico entregue.**
- **👉 Próximo:** **CFD do ejetor (Trilho 2)** quando a geometria nova fechar; fechar a conta do Ø do furo.
- **⏳ Esperando (Ito):** **STEP/Parasolid nativo** + desenho cotado (DWG→IGES degradou); confirmar o que contrai + Ø exatos.
- **📄 Chave:** **`fase2/ejetor/00_RESUMO_EJETOR.md`** (índice) · `STATUS.md`

## 🌀 VALGROUP — Ciclone gás-sólido  (`valgroup_ciclone/`)
- **✅ Feito:** matriz de decisão revisada (**ciclone +11**), Lapple preliminar (D_c≈163mm), **geometria STEP**,
  **setup CFD verificado** (RSM+fase discreta+térmica), **composição do gás analisada** (GC-MS: HC C7–C15).
- **👉 Próximo:** **reconciliar com o Marcus a vazão de gás (800 vs 1900 kg/h)** — muda D_c 163↔265mm! Depois: **calcular o orvalho (VLE)** com a composição, e montar o CFD.
- **⏳ Esperando:** **PSD do char CARREADO** (Marcus) · confirmar µ, ρ_s (partícula, não bulk), T operação (~343 vs 400).
- **📄 Chave:** `dados_cliente/dados_recebidos_15jul.md` · `simulacao/aprendizado_tutorial_ciclone.md` · `dimensionamento/`

## 🍺 CERVEJA — Tanque Chiller (estratificação)  (`cerveja_tanque_chiller/`)  ✅ CONCLUÍDO
- **✅ Estudo completo e verificado:** 3 sims (baseline 0,85 m · Sim 1 1,35 m · Sim 2 +recirc), verificação por
  **3 lentes adversariais + benchmark CSTR** (`10`, `12`). **Achado:** recirc **uniformiza** (ΔT 9,6→4,7 °C) mas
  **não acelera** (assenta no limite CSTR); Sim 1 **bate a mistura em −37%** (deslocamento). Recirc adiabática (+0,3%).
- **✅ Entregáveis:** álgebra (`13`), **página HTML** (`apresentacao_cerveja.html`), **PPTX** (`Cerveja_Estudo_3casos.pptx`)
  + 4 figuras. **Gabriel finalizou os slides.**
- **⏳ Pendências OPCIONAIS (não reabrem):** integrar ∫duty→119,5 MJ nos 3 casos; T_bulk completo do baseline;
  sensibilidade Δt/Courant. *(Só se voltar o assunto com a GreyLogix.)*
- **📄 Chave:** `11_sintese_estudo.md` · `12_verificacao_transiente.md` · `13_quantificacao_analitica.md`

## 🌴 FOXTERMO — Cristalização de óleo de palma  (`foxtermo_cristalizacao/`)
- **✅ Feito:** repo + **proposta técnica** (Rota A base / Rota B avançada, 4 cenários) + **aprendizado de
  cristalização no STAR** (melt, EMP+PBE, reologia de slurry, elo agitador↔cristalização).
- **👉 Próximo:** **Marcus monta o comercial** (prazo/valor); **pedir os dados ao Álvaro** (lista pronta no repo).
- **⏳ Esperando:** dados do Álvaro (geometria, ρ(T)/µ(T), e — p/ Rota B — cinética/reologia).
- **📄 Chave:** `00_proposta_tecnica.md` · `01_cristalizacao_no_star.md`

---

## ✅ O QUE FAZER AGORA (prioridade)
1. **🧪 Ito:** impelidor ✅ e ejetor Trilho 1 ✅ — **esperar o STEP/x_t nativo do cadista** p/ o CFD do ejetor (Trilho 2).
2. **🌀 Valgroup:** falar com o **Marcus** — reconciliar a **vazão (800 vs 1900)**.
3. **🌴 FOXTERMO:** **pedir os dados ao Álvaro** + Marcus montar o comercial.
4. ~~🍺 Cerveja~~ — **✅ CONCLUÍDO** (até 2ª ordem da GreyLogix).

## 📨 QUEM DEVE O QUÊ (esperando de terceiros)
| De quem | O quê | Projeto |
|---|---|---|
| **Marcus** | Reconciliar vazão 800 vs 1900 · PSD char carreado · comercial FOXTERMO | Valgroup, FOXTERMO |
| **Cadista do Ito** | **STEP/Parasolid (.x_t) nativo** + desenho cotado do ejetor (DWG→IGES degradou) | Ito (ejetor) |
| **Álvaro (FOXTERMO)** | Geometria, ρ(T)/µ(T), cinética/reologia | FOXTERMO |
| **Pedro/EGISA** | Confirmar condições de processo/métrica (não bloqueia) | Cerveja |

## 🧠 "NÃO ESQUECER" (lições e pegadinhas do que já resolvemos)
- **MRF (Ito):** rotação vai na **REGIÃO** (Reference Frame), **não** nas pás. Report de torque = **todas** as faces.
- **Ejetor (Ito):** **laminar** (Re~40); λ→0 → cisalhamento simples **não quebra**, só **extensão/atomização**; a
  "1,3–2 m/s" é o **tubo** (não a bolha); **<300 µm exige JATEAMENTO** (We≫350) — ar supersônico já está nele; **bolha↓=jato↑** (d∝1/U).
- **Valgroup:** condensação é de **PAREDE**, não do bulk (resposta ao Humberto). RSM, não K-ω. Vazão 800 vs 1900 **é o nó**.
- **Cerveja:** bomba de recirc = **par de BCs** (sem malhar); recirc **adiabática** (T da captação → retorno).
- **Sensor de ponto (STAR):** ❌ **nunca Maximum/Minimum report** (agarra célula parada → falso ΔT) — use
  **Point Probe** ou **Volume Average**. A **Line Probe** é a fonte confiável (pegou o probe bugado do baseline 0,85).
- **Cerveja (contraintuitivo):** com frio no fundo + sucção alta, **misturar NÃO resfria mais rápido** — a
  estratificação faz resfriamento por **deslocamento** (mais eficiente); a recirc homogeneíza → tende ao **CSTR**
  (mais lento). Recirc entrega **uniformidade**, não velocidade. Verificado por benchmark CSTR (τ=V/Q).
- **FOXTERMO:** cristalização óleo palma = **melt**; a **rotação do agitador muda a TAXA de cristalização** (Armenante-Kirwan).
- **Git:** commitar só **fatos** (nunca PDFs proprietários do cliente).
