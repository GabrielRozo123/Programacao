# BICO do EJETOR — v3 (a partir do desenho NATIVO cotado)

> Gerado por `gen_bico_v3.py`. Fonte: desenhos cotados Sugar&Azucar (recebidos 22/07/2026),
> carimbo **"BOM P/ FABRICAÇÃO"**. Substitui o v2 (que era engenharia reversa do IGES degradado).
> **Os desenhos do cliente NÃO entram no git** — aqui só ficam as cotas (fatos) e a nossa geometria.

## 1. O que os desenhos revelaram (mapa do sistema)

Há **dois** subsistemas distintos no cliente (Colombo – Santa Albertina, "Clarificação de Xarope"):

| Desenho | Peça | O que é |
|---|---|---|
| **CSA01-110-000** | TANQUE DE AERAÇÃO (montagem) | Vaso Ø800 int. (Ø819 ext.), corpo 2210 mm + cone 600 mm (63,4°), saída 8". Tampa com **3× tubo aerador** a 120° (PCD Ø680). 621,7 kg. |
| **CSA01-110-001** | TUBO AERADOR | Lança **simples** 1" Sch10S × 2800 mm + flange/tampa. É o aerador da **Fase 1** (3 conjuntos). |
| **CSA01-300-000** | EJETOR (conjunto) Rev 01 | **O upgrade.** Manifold 8" com **4 lanças** 2½" (Ø350 entre eixos, vão 1400 mm), válvulas borboleta/esfera, reduções 4"→2½"→2". Termina em **4 bicos** (item 1). **527,3 kg.** |
| **CSA01-300-001** | BICO Ø15mm Rev 00 | O **bico multifuro** — desenho de peça dedicado (o mais novo). INOX A-316. |

> O que interessa para o CFD de microbolha (Trilho 2) é **o bico** e o jato que ele forma.
> O manifold de 527 kg é contexto, não alvo de simulação.

## 2. ⚠️ DISCREPÂNCIA que o Ito precisa confirmar (a única decisão pendente)

O **corpo** do bico é idêntico nos dois desenhos; muda **só o padrão de furos**:

| | Furos de vazão | PCD | Padrão | Área aberta | Fonte | Data |
|---|---|---|---|---|---|---|
| **A (governa)** | **4 × Ø15** | Ø24 | 90° | **707 mm²** | CSA01-300-**001** (peça) | **22/07/2023** |
| B (variante) | 7 × Ø9 | Ø27 | hex 6+1 | 445 mm² | CSA01-300-**000** (conjunto) | 13/03/2023 |

- O desenho **de peça (‑001) é 4 meses mais novo e é o que governa** → adotei **4×Ø15 como default**.
- Consequência física relevante: **4×Ø15 tem +59% de área** que 7×Ø9 → para a mesma vazão, **menor
  velocidade no furo → bolha MAIOR**. Isso é o oposto do objetivo (microbolha). Vale **confirmar com o
  Ito qual é o vigente** — se o rumo é furo menor/mais rápido, a variante 7×Ø9 (ou menor) vai na direção certa.
- Entreguei **os dois STEP** para não travar; é trocar um flag no script.

## 3. Cotas do bico (corpo comum) — CORTE A-A / D-D, ESC 1:1

- Cabeça **Ø50 × 27 mm** (topo) · encaixe **Ø43 × 18 mm** (base) · **total 45 mm**.
- Chanfro da base **Ch.1,5×45°** · quebra do topo **~Ch.1×45°**.
- Barra de origem **Ø50 × 45 mm**, **INOX A-316** (item 1; 0,7 kg bruto → ~0,35 kg usinado).
- Furos de vazão **passantes** (topo→base), com pequeno rebaixo 45° na entrada (Det. B/E).
- **4 furos Ø7 radiais a 90° PARA FIXAÇÃO** (parafuso cab. chata int., item 19) — defasados dos furos de
  vazão; no CFD são **tampados** (não entram no domínio de fluido).
- "6,3" no desenho = **rugosidade Ra 6,3 µm** (não é cota).

## 3b. ⚠️ Furo RETO × CÔNICO — cruzamento desenho × IGES (resolvido)

O Ito descreveu no vídeo um **"furo cônico" que acelera o ar (subsônico→sônico)** e **suga o ar por
depressão** (efeito eductor). Isso **não bate** com o desenho de fabricação. Cruzei as duas fontes:

- **Desenho (CSA01-300-001, alta resolução):** as paredes do furo de vazão são **paralelas de topo a base
  → Ø15 RETO**. O cone "45°/22°/Ø7" do Det. B tem **eixo radial** = **escareado do parafuso cab. chata
  (item 19) de fixação**, não é furo de vazão.
- **IGES do conjunto (cruzamento independente):** dos **272 furos** do tamanho de vazão, **todos com
  conicidade 0–2° (retos)**. Os **únicos cones** são **4× Ø7 radiais a 36° de meia-abertura** = os
  **escareados dos parafusos de fixação**, um por lança. **As duas fontes concordam.**

**Conclusão:** o bico **as-built é RETO Ø15**. O **"furo cônico" do Ito é a PROPOSTA** (o que ele quer) —
que é **exatamente a recomendação do Trilho 1** (bocal convergente → jato rápido → cisalhamento/atomização).

### Proposta cônica (Trilho 1) — quantificada
Modelei a proposta: furo **Ø15 reto** convergindo a **Ø7 na saída** num cone de **meia-abertura 22°**
(o próprio 22° do desenho → cone de ~10 mm). Ganho, na mesma vazão:

| | Área de saída (4 furos) | Velocidade de saída | Cisalhamento (∝ U/d) |
|---|---|---|---|
| RETO Ø15 | 707 mm² | 1,0× (base) | 1,0× |
| CÔNICO Ø15→Ø7 | 154 mm² | **≈ 4,6×** | **≈ 9,8×** |

> É o **número que prova pro Ito**, quantitativamente, por que o cônico bate o reto para microbolha.
> Ø de saída e ângulo são **premissa** (22° do desenho) — o Ito crava os valores finais.

## 3c. ✅ RESOLVIDO: por onde o AR entra (revisão adversarial de 5 leitores + medição em pixel)

Rodada de verificação (5 leitores independentes dos desenhos nativos + síntese, 23/07). **Unânime, alta confiança:**

- **O ar NÃO entra pelos furos laterais Ø7 do bico.** Ele entra **no TOPO de cada lança**, pela
  **VÁLVULA ESFERA 1½" (item 18, qtd 4 = 1/lança)** + **CONECTOR 1½" (item 5)**, **teada RADIALMENTE
  na parede da GARGANTA 2" Sch160 (item 11)**, logo após a **REDUÇÃO 4"→2" (item 9)**. A garganta acelera
  o xarope (venturi) → depressão → **aspira o ar** ("puxado por vácuo" do Ito) → o **bico cisalha em microbolha**.
- **Os furos Ø7 laterais são ASSENTOS DE PARAFUSO** ("PARA FIXAÇÃO"), **cegos**: medição em pixel do
  **Det. E (2:1, 23,6 px/mm)** → Ø7 entra **3,9 mm** (bate com a cota "4") e sobra **3,0 mm de metal maciço**
  até o furo de vazão (parede contínua, sem quebra). **Item 19 = 8× parafuso cab. chata ¼"-20 = 2/bico**;
  "**SOLDAR SOMENTE POR FORA**" fecha a junta. Os **45°/22°** são **ângulos do escareado**, não inclinação do
  eixo — o eixo do Ø7 é **radial**. (Isso corrige meu modelo `bico_eductor_arlateral_*`, que angulava 22°.)

### 🔑 A reconciliação com o vídeo (ninguém errou a física)
O Ito falou "**quatro furinhos**" e "**entra pelas laterais**". **Bate** — só que os "quatro furinhos" são as
**quatro válvulas 1½" laterais (uma por lança)**, teadas na **lateral do TUBO** (garganta), **não** os Ø7 do
bico. O mecanismo (venturi aspira o ar) é exatamente o que ele descreveu. **Erramos só a peça, não a física.**

### ⚠️ O que os desenhos NÃO fecham (perguntar ao Ito)
1. **Sentido do escoamento** (qual header 8" é entrada/saída) — nunca rotulado (só a nota "ALTERADO ENTRADA E SAIDA PARA ø8").
2. A **aspiração é inferida da geometria**, não escrita — a válvula 1½" não tem mangueira/soprador desenhado
   (poderia ser respiro/dreno). **A pergunta única que fecha tudo:** *"os seus 'quatro furinhos' são as 4 válvulas
   1½" laterais (uma por lança), ou vocês furaram o Ø7 do bico passante de fato (desvio do desenho)?"*
3. **Co-localização:** leitura mais forte (relatórios 1&3) = bico **junto à garganta** (item 11 = 0,20 m/4 ≈
   50 mm/lança = o próprio suporte do bico); leitura alternativa = bico 3 m abaixo. Não muda a zona de bolha.

### Geometria corrigida
`dominio_fluido_no_aeracao.step` (`gen_no_aeracao.py`) — **nó compacto**: 4" → redução 4"→2" (venturi) →
garganta 2" **[porta de ar 1½" lateral]** → bico 4×Ø15 → descarga. Válido, 2,37 L. **É a zona da física da
bolha, agora com o ar no lugar certo.** (Supersede `bico_eductor_arlateral_*` — ar no bico estava errado.)

## 3d. ✅✅ STEP NATIVO recebido (cadista Brendo, 23/07) — confirma TUDO

`00__CONJUNTO_EJETOR.stp` — sólido **analítico limpo** (490 sólidos; 2594 cil., 2850 cones, 16 esferas =
válvulas). Medições diretas (`gen_no_nativo.py` extrai da lança X=0):

- **Layout:** header 8" ao longo de **X** · lanças 2½" ao longo de **Y** (4 lanças a X=0/350/700/1050) ·
  **portas de ar 1½" ao longo de Z (laterais)**. A seta do Brendo aponta a **válvula 1½" lateral** →
  *"a única entrada que tem é essa"*. **Confirma o ar pela lateral do TUBO.** ✅
- **Furos Ø7 do bico:** 16 no total, eixos **radiais (X/Z)** = **4 por bico, FIXAÇÃO**. ✅ (nem passam pelo Y)
- **BICO nativo = 7 × Ø9 (r4,5) hexagonal, PCD Ø27** (1 central + 6 a r13,5) — **medido exato**.
  ⚠️ O desenho de peça CSA01-300-001 trazia **4×Ø15**; o **modelo nativo do conjunto usa 7×Ø9**.
  → **perguntar ao Ito qual é o de produção.** (O nó paramétrico troca 7×Ø9 ↔ 4×Ø15 num flag.)
- **Topologia da lança (medida):** 8" → 4" (r51,15) → borboleta → **AR 1½" (Y≈542)** → redução 27,9° →
  **BICO 7×Ø9 (Y≈174–224)** → borboleta → 4" → redução 22° → **2½" (r31,4) × 3 m** → redução → 8" inferior.
  O bico é uma **placa multiorifício inline** (não descarrega em tanque aberto); o ar é injetado a montante.

### Geometria (do nativo)
`dominio_fluido_no_NATIVO_7furos.step` (`gen_no_nativo.py`) — **nó de aeração** com cotas exatas do STEP:
4" (r51,15) + ar 1½" (r19,05) lateral + redução 4"→assento(Ø52) + **bico 7×Ø9 PCD Ø27** + descarga Ø120.
Válido, 2,37 L. **É a zona da física da bolha, com toda cota conferida contra o sólido nativo.**
(STEP nativo do cliente **NÃO** vai pro git.)

## 4. Como o bico monta (caminho do fluido)

`lança 2½" → redução 4"→2" → tubo 2" Sch160 (ID ≈ 49,25 mm) → BICO → xarope`

- O **encaixe Ø43** entra no tubo **2" Sch160**; travado pelos 4 parafusos radiais Ø7.
- O bico é, na prática, uma **placa multiorifício / bocal**: todo o fluxo passa pelos furos.
- **Razão de contração** tubo→furos: 2" (área ≈ 1905 mm²) → furos:
  - 4×Ø15: **≈ 2,7:1** · 7×Ø9: **≈ 4,3:1** (bate com o "~2:1" que o Ito mencionou p/ o 4×Ø15).

## 5. STEP entregues (mm, sólido válido)

| Arquivo | O que é | Vol. |
|---|---|---|
| `bico_4furos_D15_CSA01-300-001.step` | **Sólido do bico — ATUAL (4×Ø15)** | 44,2 cm³ |
| `bico_7furos_D9_CSA01-300-000.step` | Sólido do bico — variante (7×Ø9) | 56,4 cm³ |
| `bico_4furos_conico_D15-D7_PROPOSTA.step` | **Proposta T1**: furos convergindo Ø15→Ø7 (22°) | 47,3 cm³ |
| `dominio_fluido_bico_4furos.step` | **Volume de FLUIDO p/ CFD (reto)**: plenum 2" (⌀49,25×40) + 4 furos + descarga (⌀120×120) | 1465 cm³ |
| `dominio_fluido_conico_D15-D7.step` | **Volume de FLUIDO p/ CFD (cônico)** — mesmo domínio, furos convergentes | 1462 cm³ |

**Convenção (z-up):** z=0 face da base Ø43 (**lado do tubo = entrada**); z=45 face de topo Ø50
(**descarga no xarope = saída**). Trocar sentido no STAR é trivial.

### 5b. Domínio da LANÇA INTEIRA (o ejetor completo) — `gen_lanca_dominio.py`

`dominio_fluido_lanca_completa.step` — volume interno de **1 lança** (das 4), fiel ao caminho do fluido:

`motriz 4" → VENTURI (redução 4"→2½") → PORTA DE AR 1½" (item 18/5, ~50 abaixo do venturi) →
lança 2½" × 3000 → redução 2½"→2" → BICO 4×Ø15 → descarga (Ø120)`

- **Válido**, 14,6 L, **3722 mm** de altura. Marcos (z, mm): venturi 392–482 · porta de ar 532 ·
  topo do bico 3557 · descarga 3602.
- **É o ejetor venturi auto-aspirante:** a redução acelera o motriz → depressão → **suga o ar** pela
  válvula 1½" → mistura descendo os 3 m → o bico atomiza. (Confirma a descrição do Ito.)
- **Premissas** (spools retos e cotas finas de redução/porta de ar = fitting padrão; não mudam a física):
  redução 4"→2½" ~90 mm, ar 1½" ID 40,9 a ~50 mm do venturi. Ito crava se quiser.
- **Nota de malha:** razão de aspecto ~50:1 (3 m de tubo entre 2 zonas ativas). Para rodar, o melhor é
  **partir em 2 domínios** (cabeça/venturi p/ entranhamento · bico p/ formação de bolha) e acoplar pelo
  tubo — mas o STEP inteiro está aqui como pediu, e dá pra malhar direto se quiser o quadro completo.

## 6. Próximo (a discutir a modelagem no STAR)

- Domínio de fluido pronto p/ malhar. Sugestão de setup: **Passo 1 monofásico** (xarope, laminar Re~40) p/
  cravar velocidade/ΔP nos furos → **Passo 2 VOF/EMP** com o ar p/ ver formação de jato/bolha.
- Fechar a **conta do Ø do furo** p/ velocidade/We alvo com **30 m³/h/ejetor** (Trilho 1 já dá a direção).
- Confirmar com o Ito: **(a)** padrão de furo vigente (§2), **(b)** vazão real por ejetor (ar + motriz),
  **(c)** se o alvo é simular o bico **como está** ou já a **proposta** (furo menor/bico convergente).
