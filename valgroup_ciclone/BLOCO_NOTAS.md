# 📝 Bloco de notas — Valgroup (uso interno)

> Pontos levantados por nós que **ainda não foram passados ao Marcus**. Combinado em 13/10/2026:
> soltar aos poucos, para não sobrecarregar a conversa. Ao passar um item, mover para
> "Já passado" com a data.

---

## ✅ Desenho R01 recebido (06/11/2026) — geometria da rodada gerada

Arquivos do cliente: `Ciclone_DC307_3_vistas_R01.dwg` + PNG, `Criterios_e_observacoes_R01.txt`, memorial
`MC_VP_T-202 Rev.00` (ASME VIII Div.1) e apresentação do memorial. O cliente informou também que o
responsável anterior (Henrique) saiu e o Matheus pode atrasar outras informações.

**O que o desenho define (diâmetros INTERNOS):**
| item | desenho R01 | modelo anterior |
|---|---|---|
| corpo / cone | DI 307, H 460,5 / cone 767,5 | igual |
| entrada | 153,5 × 61,4, **cantos R15**, reto **307 preservado** (= 460,5 a partir do plano do eixo) | igual, cantos vivos |
| transição | **retângulo → círculo centrada, L = 100**, e = 4,75; semiângulo 24,9° em planta | — |
| tubo de entrada | **6" SCH40S, DI 154,08**, ponta de 50 mm (sem flange) | — |
| saída de gás | 6" SCH40S, DI 154,08, e 7,11, L 307 c/ flange | DI 153,5, e 4,75 |
| saída de pó | **4" SCH40S, DI 102,26**, e 6,02, L 153,5 → **muda a base do cone** (semiângulo 7,12° → 7,60°) | DI 115,13 |
| tampo | **12,70 mm** | 4,75 |

**Geometria gerada:** `simulacao/ciclone_Dc307_t4p75_Lr460_D154_Lt100_R01_ASSEMBLY.step` (fluido 87,16 L, sólido
11,0 L ≈ 87 kg de aço, ambos válidos, nenhuma face < 50 mm²). Comando no cabeçalho do `gen_ciclone_cht.py`.

**Decisões / pontos de atenção:**
- A transição **contrai** no sentido do escoamento (área do retângulo = 0,505 × a do tubo; laterais −24,9°, topo/fundo −0,2°):
  não há risco de descolamento por expansão. Com 1 820 kg/h, 400 °C, 1,2 bar, MM 130,594 (ρ = 2,800 kg/m³, Q = 0,1806 m³/s):
  **9,68 m/s no tubo 6" → 19,16 m/s no retângulo** (pdin 131 → 514 Pa); com R15 seriam 19,56 m/s (+2 %).
  ⚠️ **ΔP estático medido a partir da entrada do tubo** sai ~380 Pa maior só pela aceleração (514 − 131 Pa), sem ser perda:
  comparar com o estudo anterior **no mesmo plano** (seção do duto retangular) ou em **pressão total**.
- Revisão geométrica de 06/11 (medida no STEP × desenho): todas as cotas conferem, incluindo envelope em planta 768,75 e
  altura entre faces 1 701,2 (a saída de gás foi para **319,7 mm acima do teto interno = 307 acima do tampo de 12,7**, `--l-out`).
  Orientação conferida: em planta o duto fica acima do centro, como no desenho (mesmo sentido de giro do modelo anterior).
- **Cantos R15 não modelados** (cantos vivos, como no estudo anterior) para isolar o efeito da transição. R15 reduz a área
  da entrada em ~2 % → v_i +2 %, ΔP ~+4 %. Pode entrar numa rodada seguinte.
- **Tubo a montante: só a ponta real de 50 mm** (`--l-tubo 50 --l-tubo-solido 50`), com a entrada de massa na face dela —
  mesma filosofia do modelo anterior (condição de contorno no bocal do próprio ciclone). Uma extensão de 5·D (770 mm) foi testada e
  descartada a pedido do Gabriel (06/11): não existe no desenho, e a contração 2:1 da transição já uniformiza o perfil que chega ao
  duto. Se a Valgroup informar o que vem antes (reto ou curva), dá para estender com `--l-tubo` (a opção `--l-tubo-solido` limita o
  aço à ponta real). Fluido 73,96 L · sólido 8,46 L ≈ 67 kg.
- **Vortex finder:** o desenho não cota o mergulho interno; mantido S = 153,5 mm (0,5·Dc). Confirmar.
- Mudaram **três coisas** em relação ao modelo antigo (transição, saída de pó 102,26, bocais/tampo reais): a comparação
  de η e ΔP com o estudo anterior mistura os efeitos. Se precisar separar, rodar também a base com saída de pó 102,26 sem
  transição.
- Medir ΔP **estático e total** nos mesmos planos (fecha a pendência 3 400 × 2 910 Pa).
- Inserção de 8 mm (253,5 × 161,4, R30) é reforço externo da abertura: não entra no fluido.

### Montagem do caso R01 no STAR (06/11) — `ciclone_307_100_FEA_geometria_nova.sim` (cópia do caso FEA_Espessura)
- Nomes: fluido `inlet` · `outlet_gas` · `outlet_dust` · `walls`; sólido `Pontas` (3 anéis das pontas, adiabáticos) · `Externa`
  (convecção h = 10, 25 °C). As faces molhadas do sólido ficam em `Externa` e passam para a interface.
- 3D-CAD → Part com *Create Part Contacts from Coincident Entities* (21 pares) → *Assign Parts to Regions* com contact-mode
  interfaces. **Ligar cada região ao seu continuum** (a cópia deixou o `Aço_304L` sem região).
- ⚠️ **Interface tem de ser *Mapped Contact Interface***: o sólido usa FE Solid Energy; *Contact Interface* (in-place) dá
  "Type star.common.ContactInterface … is incompatible" na inicialização.
- Malha: 1 678 427 células. Tabelas do Simas reapontadas: `Carga_mecanica` → interface lado fluido [0]; `Campo_termico` →
  fronteiras do sólido. `char_PSD_CDF` fica gravada no .sim (CSV copiado para a pasta do .sim por segurança).
- Reports de ΔP: `DeltaP`/`DeltaP_total` entre `corte_duto` e `outlet_gas` (comparável ao estudo anterior) e
  **`DeltaP_equipamento_total`** = p_total(`inlet`) − p_total(`outlet_gas`), o número contra os 40 mbar. O `Pressure Drop 1`
  (inlet → outlet_gas) fica para conferir se o report nativo usa pressão total (deve bater) ou estática (~380 Pa a mais).
- Execução: fase 1 escoamento + energia com o lagrangeano congelado; fase 2 congela fluxo/energia e roda as partículas.
  Referência do caso anterior: ΔP estático 3 400 Pa · calor 5,15 kW · parede 350–398 °C · η 96,25 %.

### Resultado R01, fase 1 (escoamento + calor, k-ω SST, 8 449 it) — 07/11
| grandeza | R01 | caso anterior (CHT Dc307) |
|---|---|---|
| **ΔP total do equipamento** (p_total `inlet` 6" → `outlet_gas`) | **3 745 Pa = 37,4 mbar** (±30 Pa de oscilação do vórtice) | — (não medido) |
| ΔP estático no duto (`corte_duto` → `outlet_gas`) | *pedir o valor* | 3 400 Pa |
| calor pela `Externa` | **5,43 kW** | 5,15 kW (+5 %: transição, ponta e tampo de 12,7) |
| calor pela interface | 5,27 kW → **desequilíbrio 2,9 %** (antes 1,2 %); a interface mapeada não é estritamente conservativa | |
| parede | **356–391 °C** | 350–398 °C |

Leitura: 6" na entrada e na saída → ΔP total ≈ estático de flange a flange; a transição quase não acrescenta perda
(estimativa pelo caso anterior: 3 400 + 514 − 131 ≈ 3 780 Pa de duto a saída em pressão total). **Contra 40 mbar a
margem é de 6 %, e isto é k-ω:** com o fator RST do relatório final (×1,18 a ×1,39) vai a **44–52 mbar**. Mesmo recado
do caso anterior (`11_CHT` §2), agora no equipamento real — levar ao Marcus.

### ΔP da R01 — fechamento (07/11, reports `R01_`, k-ω SST)
| medida | valor |
|---|---|
| p estática `inlet` (6", área) | 4 051 Pa |
| p total `inlet` (vazão) | 4 180 Pa (= estática + ½ρv² de 9,68 m/s, 131 Pa ✔) |
| p estática `outlet_gas` (área) | −2 Pa |
| p total `outlet_gas` (vazão) | 763 Pa → o gás sai com **redemoinho** (dinâmica ≈ 23 m/s contra 9,7 m/s axial) |
| p estática `corte_duto` (y = 0,3 m, área) | 3 247 Pa · vazão pelo plano 0,5047 kg/s ✔ |
| p total `corte_duto` (vazão) | 4 526 Pa ⚠️ maior que na entrada → **não usar**: perfil muito irregular/refluxo no duto logo após a transição deixa a média ponderada por vazão mal condicionada |

**ΔP oficial = estático de flange a flange (`inlet` → `outlet_gas`) = 4 053 Pa = 40,5 mbar (k-ω).** Com 6" nas duas
pontas, é também a perda total contando o redemoinho de saída como perdido (ele se dissipa na tubulação a jusante;
Hoffmann & Stein). Total com redemoinho "recuperado" = 3 418 Pa (34,2 mbar) é só limite inferior.
- Parte do ciclone (estático duto → saída): 3 249 Pa contra 3 400 Pa do caso anterior (−4 %) → o ciclone não mudou.
- O acréscimo vem da entrada: queda estática ponta → duto = 804 Pa, dos quais ~383 Pa são aceleração inevitável (6" →
  retângulo, 9,7 → 19,2 m/s) e **~420 Pa** vêm da transição curta (L = 100, lados a 25°) deixando o jato irregular.
- **Contra 40 mbar: 40,5 mbar já em k-ω**; com o fator RST do relatório final (×1,18–1,39) → ~48–56 mbar.
- Pendência V3 (estático × total) **fechada** com estes números.
- Sugestão: rodada de sensibilidade com transição mais longa (ex.: L = 300 mm, lados ~9°) para medir quanto dos ~420 Pa
  se recupera — o gerador faz em segundos (`--l-trans 300`).

### Exportação para o Simas (07/11)
- Tabelas XYZ herdadas da cópia do .sim saíram com **1.797e+308 (sem valor)** em todas as colunas: estavam com
  *Representation = Latest Surface* / configuração da simulação antiga. **Solução: criar tabelas XYZ novas** (solução na
  *Volume Mesh*). Com interface mapeada, as faces ficam nas fronteiras originais: mecânico em `walls` (fluido), térmico
  em `Externa` + `Pontas` (sólido).
- Conferido: temperatura ~658–663 K (385–390 °C) no lado interno do tampo, coerente com a faixa 356–391 °C.
- Nota enviada junto: sistema de coordenadas (origem no eixo, z = 0 na face interna do tampo, duto em +y, SI), condições
  (400 °C, 1 820 kg/h, h = 10 W/m²K a 25 °C, pontas adiabáticas), pressão manométrica relativa a 1,2 bar abs
  (atmosfera: Absolute Pressure − 101 325), pendências de material (304 × 304L) e apoios.

### Partículas da R01 — primeira rodada (09/11) inválida para η
- `mdot_gas_XXX` herdado apontava para o `inlet` (corrigido para `outlet_gas`).
- Rodada com **Maximum Residence Time = 2 s** → η = 99,73 %: **viesado**, igual à verificação de 2 s do caso anterior
  (99,75 %). O η válido exige **60 s** (caso anterior: 96,25 %, 632 770 sub-passos) — ver `11_CHT` §5.
- **Achado novo:** 1,0×10⁻⁴ kg/s (**3,6 % do injetado**) saem **de volta pelo `inlet`** — partículas que quicam nas paredes
  convergentes da transição (25°) e atravessam a face de entrada a só 50 mm. Não existia no modelo antigo (entrada no
  duto reto). Correção: condição da fase lagrangeana no `inlet` = **Rebound** (o escoamento a montante as devolveria),
  e conferir que a saída pelo `inlet` vai a ~0 na rodada de 60 s.

## Pendentes — transição redondo-retangular na entrada (pedido de 13/10/2026)

**Pedido do Marcus:** a Valgroup quer encurtar o duto retangular de entrada ao mínimo do desenho
deles e colocar uma transição redondo-"quadrado". Adaptar o CAD, rodar de novo o escoamento,
passar ao Simas T e P nesse trecho e ver se a transição afeta a eficiência.

**Estado:** aguardando o desenho. O `simulacao/gen_ciclone_cht.py` já aceita a transição por
parâmetros (`--l-ret --d-tubo --l-trans --l-tubo --dx-tubo --dz-tubo --t-tubo`), testado.

1. **Eficiência — expectativa: sem impacto relevante.** d50 de 2–3 µm contra char a partir de
   ~61 µm: margem de 19× no pior cenário. A transição piora o perfil de entrada, não nessa ordem.

2. **O "mínimo possível" tem dois limites:**
   - **Geométrico:** a parede interna do duto só sai do casco em y ≈ 132 mm (medido do plano do
     eixo do ciclone). A transição não pode começar antes.
   - **Escoamento:** com tubo menor que 153,5 mm, a transição abre na vertical; acima de ~7,5°
     por lado, descola. Transição mínima: 4" Sch40 → ~195 mm · 5" Sch40 → ~95 mm ·
     6" Sch40 → sem restrição (só estreita).
   - Descolamento mexe no ΔP e na pressão local para o Simas, não na eficiência.

3. **"Redondo-quadrado":** a nossa entrada é **153,5 × 61,4 mm (2,5:1)**, não quadrada. Confirmar
   no desenho se a seção se mantém — se mudar, o ciclone muda (velocidade, ΔP, eficiência).

4. **Conferir no desenho:** Ø interno do tubo · comprimento da transição e do duto retangular (e
   de onde é medido) · eixo do tubo centrado ou não · espessura da transição · o que vem antes
   (reto ou curva).

5. **Cuidados na nova rodada:**
   - ΔP nos **mesmos planos** do modelo antigo, em **estática e total** — fecha também a
     pendência 3 400 × 2 910 Pa.
   - Lagrangeano com os mesmos ajustes. Com ~1 200 parcelas, η = 96,25 % tem ruído de
     ±0,55 pp (1σ): diferenças < ~1 pp não são separáveis do ruído. Se precisar, mais parcelas.
   - Conferir MM, µ e T de entrada do gás antes de rodar.
   - **Plano B de malha (só se precisar):** se o sólido de 4,75 mm der problema na transição
     (faces estreitas, cunhas), a parede pode ir como **shell** — espessura como propriedade, uma
     camada de células (tutorial STAR 05, `star_ccm_tutoriais/05_Parts_Based_Shells_Exhaust.md`).
     O Simas receberia T na superfície média. Não trocar se o sólido continuar funcionando.

## Anteriores — confirmar com o Gabriel se já foram passados

6. **Envelope de ΔP em k-ω.** Todo o envelope de 29–74 mbar foi levantado em k-ω; o relatório
   final (§5.1) diz que o k-ω subestima 18–39 %. Ver `simulacao/11_CHT_FEA_espessura_4p75.md` §2.
   Depende de fechar a convenção estática × total (item 5).

7. **Grau do aço:** e-mail diz AISI 304, memorial diz SA-240 304L. O Simas usou 304L
   (conservador). Confirmar com a Valgroup.

8. **Arranjo de apoios do ciclone** — sem ele o caso térmico do FEA não fecha.

9. **Particulado 10 × 80 kg/h** — a erosão escala linearmente; não exige re-rodar.

## Já passado

| data | item |
|---|---|
| — | — |
