# 🗼 PAINEL DE CONTROLE — Projetos CFD (Gabriel / CAEXPERTS)

> **Torre de controle.** Bata o olho aqui para saber onde está tudo e **o que está pendente com quem**.
> **Atualizado: 2026-10-13.** Cada projeto tem seu `README.md` detalhado — este painel é o resumo.
> 🔒 Projetos com material confidencial (Petrobras) aparecem aqui só em nível de status.

## Semáforo
| projeto | cliente | 🚦 | onde está |
|---|---|---|---|
| 🌀 **Ciclone — FEA/CHT** | Valgroup | 🟡 | CHT entregue (P, T na parede → Simas, que já mapeou). **Aguardando desenho** da transição redondo-retangular na entrada. Gerador de CAD já preparado. |
| 💨 **Dispersão de O₃** | LD Celulose | 🟡 | Etapa 2 (premissas). Planilha meteorológica entregue (Marcus gostou). **Aguardando dados do cliente.** |
| 🔥 **Resfriador + finos (DEM)** | Petrobras RNEST | 🟡 | Contratação em andamento (convite previsto para a semana de 20/10). Estudo de tutoriais de ebulição em curso. Detalhes no bloquinho privado. |
| 🌊 **Misturador hiperbólico** | Nexus | ⚪ | E-mail de perguntas aguardando revisão do Marcus (desde 21/09). Sem resposta registrada. |
| 🍺 **Tanque chiller** | GreyLogix | ✅ | Concluído. Post do blog entregue ao Otávio. Restam ajustes menores. |
| 🧪 Aeração + ejetor | Ito | ⚪ | Sem atualização desde 02/08 (ver histórico abaixo). |
| 🌴 Cristalização | FOXTERMO | ⚪ | Sem atualização desde 02/08 (ver histórico abaixo). |

---

## ✅ PENDÊNCIAS ABERTAS — o que não pode ser esquecido

### 🌀 Valgroup — `valgroup_ciclone/` · notas internas em `BLOCO_NOTAS.md`
| # | pendência | com quem |
|---|---|---|
| V1 | **Desenho da transição redondo-retangular** → gerar STEP (`gen_ciclone_cht.py --l-ret --d-tubo --l-trans`), rodar CHT, passar T e P ao Simas, avaliar eficiência | Valgroup → Gabriel |
| V2 | **Comparar as duas cenas de erosão** (residência 60 s × 2 s) — pedido feito em 30/09, resultado nunca reportado | Gabriel |
| V3 | **ΔP estático × total:** criar reports com `Pressure` em Inlet/Outlet_gas — fecha 3 400 × 2 910 Pa e o envelope em k-ω | Gabriel |
| V4 | Opcional: rodada a 120 s para ver se η = 96,25 % ainda cai | Gabriel |
| V5 | Particulado **10 ou 80 kg/h** (erosão escala linear) | Marcus / Valgroup |
| V6 | Grau do aço **304 ou 304L** · **arranjo de apoios** do ciclone (dimensiona o FEA térmico) | Marcus / Valgroup |
| V7 | 4º slide da apresentação (envelope de ΔP) — aprovação | Marcus |

### 💨 LD Celulose — `ld_celulose_dispersao_o3/`
| # | pendência | com quem |
|---|---|---|
| L1 | **Vazões de vazamento** pequeno e grande (Q_peq, Q_gr) — bloqueia os cenários | Cliente |
| L2 | Desenhos **CVC00P0015 a P0018** (geometria de descarga dos exaustores) · quais ventiladores são contínuos | Cliente |
| L3 | Estação Zeus: o **0° é norte verdadeiro?** · ângulo do norte de projeto da planta · altura do anemômetro | Cliente |
| L4 | Densidades de projeto das curvas dos ventiladores (0,9002 × 1,0148 kg/m³) | Cliente |
| L5 | Faltam **1 planilha e 1 PDF** do lote 1 | Cliente |
| L6 | Aval dos **cenários 5–6** (vento fraco estável) | Marcus |
| L7 | CAD: `.x_t` de 19/10 veio **sem geometria** (coordenadas da planta fora do limite do Parasolid) → pedir ao cliente exportação da área 1219 + raio ~300 m, transladada para perto da origem (texto em `03` §9). Depois: limpeza pelos critérios de `05` | Cliente → Gabriel + Otávio |
| L8 | Decidir se o projeto migra para repositório privado | Marcus |

### 🔥 Petrobras — `petrobras_coqueamento/` (🔒 detalhes só no bloquinho privado)
| # | pendência | com quem |
|---|---|---|
| P1 | Reunião sobre o escopo DEM (14/10, tarde) | Marcus |
| P2 | Proposta formal pelo convite — incluir **quantidade de cenários**, **conjunto mínimo de dados** e **ART**; dimensionar o custo da parte multifásica (ver bloquinho privado) | Marcus / Gabriel |
| P3 | Lista de perguntas técnicas ao Rui (pronta, 20 itens) | Gabriel → Rui |
| P4 | Pontos técnicos internos para alinhar com calma (seção 4 do bloquinho) | Gabriel ↔ Marcus |
| P5 | Tutoriais STAR: **lotes 1 e 2 completos** (01–08, ver `star_ccm_tutoriais/`). Pendente: **teste de bancada** (1 tubo em shell) no STAR | Gabriel |

### 🌊 Nexus — `nexus_misturador_hiperbolico/`
| # | pendência | com quem |
|---|---|---|
| N1 | Revisão do e-mail de perguntas e envio ao Douglas | Marcus |

### 🍺 GreyLogix — `cerveja_tanque_chiller/`
| # | pendência | com quem |
|---|---|---|
| G1 | Parágrafo da "régua" reduzido + correção do "Volte à equação" → chegar ao Otávio | Gabriel |
| G2 | Regerar `tres_casos_vs_cstr.png` (precisa do CSV bruto) | Gabriel |

---

## 📚 Biblioteca de tutoriais do STAR — `star_ccm_tutoriais/`
Notas genéricas e reutilizáveis + ferramentas (ex.: `props_agua_saturada.py`).

---

# Histórico — painel de 02/08/2026
> Ito, Cerveja e FOXTERMO abaixo estão **sem atualização desde 02/08**. As linhas do Valgroup abaixo
> são da fase de dimensionamento e já foram superadas (ver pendências acima).


## Semáforo (uma linha por projeto)
| Projeto | Cliente | 🚦 | Onde está |
|---|---|---|---|
| 🧪 **Ito** (sugar) | CAEXPERTS | 🟡 | **Impelidor FECHADO** ✅ (9,9 kW, +37%). **Ejetor: CFD encerrado** — sucção existe mas é **1000× fraca**; causa geométrica (porta de ar a montante do bico). **Aguarda Ito.** |
| 🌀 **Valgroup** (ciclone) | CAEXPERTS | 🟢 | **ΔP e T_parede ENTREGUES** ✅ (29–35 mbar vs limite 40 · parede 381/367 °C, **não condensa**). Rodando **transiente RST**. Falta **curva η×d**. 📄 `NOTA_TECNICA_parcial.md` |
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
