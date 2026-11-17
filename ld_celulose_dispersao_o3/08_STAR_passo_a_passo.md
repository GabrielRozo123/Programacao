# 08 — STAR-CCM+ do zero: volume de ar → malha → física (passo a passo)

> 21/10/2026. Substitui o fluxo anterior (3D-CAD + domínio separado + Subtract + Surface Wrapper), que ficou confuso e
> colava frestas. Arquivos com coordenadas ficam em `_privado/`. Física: `07_checklist_CFD.md` §3–5.
> Por que sem wrapper: `star_ccm_tutoriais/09_Surface_Wrapper_referencia.md`.

---

## 0. Arquivos (gerados por `geometria/gen_volume_fluido.py`)
| arquivo | o que é |
|---|---|
| `volume_ar_LD.stl` | **o volume de ar inteiro**: domínio de 16 lados MENOS os obstáculos, fechado, em **metros**, 87 superfícies nomeadas |
| `refino_r80_h70.stl`, `refino_r300_h120.stl` | cilindros de refino (controles volumétricos) |

Superfícies do `volume_ar_LD.stl`: `S01…S16` (laterais, S01 = 0° = +y, horário), `Solo`, `Topo`, uma por obstáculo
(nome da tabela) e `Saida_910`, `Saida_920`, `Saida_930`, `Saida_940` (só a face de saída de cada exaustor).

## 1. Simulação nova e importação
1. *File → New Simulation* (paralelo).
2. *File → Import → Import Surface Mesh* → `volume_ar_LD.stl`.
   - *Import Mode*: **Create New Part**; *Units*: **m**; *Mark Feature Edges* ligado (ângulo ~30°).
   - Os nomes vêm dos blocos `solid` do STL (cada um vira um part surface), como já aconteceu com o domínio nomeado.
3. Repetir para os dois `refino_*.stl` (*Create New Part*, m). Eles **não** vão para região — são só formas de refino.
4. Conferir: *Geometry → Parts → volume_ar_LD → Surfaces*: 87 superfícies; clique direito no part →
   *Repair Surface…* → diagnóstico: **0 free edges, 0 non-manifold, 0 pierced faces**.
   - *Face quality* com milhares de faces é **esperado**: o STL vem da triangulação do CAD (triângulos longos no solo e
     nos cilindros) — é exatamente o que o Surface Remesher refaz. Não consertar no Repair.
   - *Face proximity* (~50) = espessuras e vãos reais (laje 0,85 m, cobertura 0,6 m, vão tanque–laje 0,8 m) ao lado de
     triângulos enormes; clicar no número para ver onde estão. Leitura completa: `star_ccm_tutoriais/10_Surface_Repair_referencia.md`.
   - As saídas dos exaustores são faces **rentes** à face do exaustor (sem degrau); um degrau de 2 cm gerava
     *Face proximity* e exigiria células de 1–2 cm.

## 2. Região e contornos
1. *Geometry → Parts* → clique direito em `volume_ar_LD` → *Assign Parts to Regions*:
   - **Create a Region for Each Part** e **Create a Boundary for Each Part Surface** → região única (renomear para `Ar`)
     com um contorno por superfície.
2. Tipos de contorno (por cenário de vento, mudam só S01–S16):
   | contorno | tipo |
   |---|---|
   | setores com u·n < 0 (vento entrando) | *Velocity Inlet* (perfil de CLA por Field Function) |
   | setores com u·n > 0 | *Pressure Outlet* |
   | `Topo` | *Wall* com tensão de cisalhamento prescrita (*Shear Stress Specification*, Richards & Hoxey) ou *Symmetry* — decidir no domínio vazio |
   | `Solo` | *Wall* rugosa (*Roughness Height* ks) |
   | obstáculos | *Wall* lisa |
   | `Saida_9x0` | *Mass Flow Inlet* (vazão do manual, escalar passivo do exaustor = 1) |

## 3. Malha (Automated Mesh no part `volume_ar_LD`)
1. *Operations → New → Mesh → Automated Mesh* → *Input Parts*: `volume_ar_LD`.
2. Meshers: **Surface Remesher** + **Trimmed Cell Mesher** + **Prism Layer Mesher**. (Sem Surface Wrapper.)
**Malha 1 (grossa, para testar o pipeline e o domínio vazio)** — estimativa ~3,5–5 milhões de células:
longe 8 m (~0,7 M), cilindro R300 a 3 m (~1,2 M), cilindro R80 a 1 m (~1,4 M), + refino junto aos obstáculos.
A malha fina do estudo de independência sai desta dividindo os tamanhos por ~1,5.

3. *Default Controls*: Base Size **8 m**; **Maximum Cell Size 8 m (absoluto — o padrão do STAR é 10 000 % do base = 800 m!)**; Target Surface Size 100 %; Minimum Surface Size **0,25 m** (absoluto);
   Surface Growth Rate 1,3; Number of Prism Layers **3**; Prism Layer Total Thickness **1,0 m**; Prism Layer Stretching 1,2.
4. *Custom Controls → Surface Control* (um controle por grupo, selecionando os part surfaces):
   | controle | superfícies | target / mínimo | prismas |
   |---|---|---|---|
   | `Saidas` | `Saida_*` | 0,05 / 0,02 m (≥ 8–10 células na largura) | desligados |
   | `PredioO3` | `O3_*`, `exaustor_*` | 0,25 / 0,05 m | desligados |
   | `Obstaculos` | todos os demais obstáculos | 0,5 / 0,1 m | desligados (frestas de 0,8 m) |
   | `Externo` | `S01–S16`, `Topo` | 8 m (= base) | desligados |
   | `Solo` | `Solo` | padrão | **3 camadas, 1,0 m** (1ª célula > ks — revisar após o domínio vazio) |
5. *Custom Controls → Volumetric Control* (Surface Remesher **e** Trimmer marcados, tamanho absoluto):
   `refino_r80_h70` → **1 m**; `refino_r300_h120` → **3 m**.
6. *Execute* → número de células, *Mesh → Diagnostics* (volume negativo = 0; face validity ≥ 0,95; volume change > 1e-3)
   e uma cena de corte (plano z = 1,5 m e plano vertical pelo prédio de O₃).

**Malha 1 executada (21/10):** 6,56 M células, topologicamente válida, face validity 1,0 em 100 %, volume change mínimo
0,011 (> 1e-3). Acima da estimativa por causa das transições de tamanho (8 → 3 → 1 m) e do refino nos obstáculos.

## 3b. A fonte (o "vazamento")
O vazamento acontece **dentro** do prédio (`06` §3.5) e os exaustores levam o O₃ para fora → a fonte entra **nas
faces `Saida_*`**, com o ar do exaustor marcado por um escalar passivo.
1. *Physics*: Passive Scalar com **4 componentes** (`O3_910`, `O3_920`, `O3_930`, `O3_940`), Sc_t 0,7, clip em 0.
2. Cada `Saida_9x0` = *Mass Flow Inlet*: ṁ = ρ·Q do manual (LX 816: 10,5 m³/s; HL 4S: 4,2 m³/s); escalar **do próprio
   exaustor = 1**, os outros = 0; turbulência na saída: intensidade 5–10 %, comprimento ~0,07·D_h.
3. φ = fração de ar de exaustão no ponto → **ppm = φ · C_exaustão**, com C_exaustão = vazão de O₃ vazada ÷ vazão do exaustor.
   Como é linear, a vazão real de O₃ (pendência A1 do cliente) entra só no pós-processamento.
4. ⚠️ A face do CAD (0,27 m² nos LX 816) é menor que a área do manual (0,3105 m²) → mesma vazão sai a ~39 m/s em vez de
   33,8 m/s. Manter a vazão (é o que dilui) e declarar; sensibilidade de momento se a pluma subir demais.

## 4. Antes dos cenários
1. **Domínio vazio:** mesmo procedimento com o domínio sem obstáculos (`dominio_16setores_NOMEADO_m.stl`) → perfis U e k
   na saída = entrada.
2. Caso base, sensibilidades, cenários — `07_checklist_CFD.md` §6–8.

## 4b. Teste do domínio vazio — registro (27/10)
Malha: domínio de 16 lados sem obstáculos, base 8 m, refino 3 m até 30 m de altura, 1 prisma de 2,5 m no solo → 4,8 M células.
Perfil: Richards & Hoxey, 1,9 m/s a 10 m, z₀ = 0,03 m, vento de NNE; entradas S15–S05 + paralelos S06/S14 + Topo (perfil
imposto no topo, Blocken 2007); saídas S07–S13. Solo rugoso: ks = 9,793·z₀/C = 1,16 m (C = 0,253 do STAR; κ = 0,42 também
no perfil).

| rodada | modelo | U saída × entrada | k saída ÷ teórico (10–70 m) | veredito |
|---|---|---|---|---|
| 1 | Realizable k-ε Two-Layer, All y+ | ≤ 2 % | **0,69–0,74** (1000 it) | k decai ~30 % → reprovado |
| 2 | **Standard k-ε, High y+, σε = 1,225** (Richards & Hoxey: σε = κ²/((C2ε−C1ε)√Cμ)) | ≤ 2 % | 0,75–0,80 | melhorou, ainda > 15 % |

| 3 | idem 2, com **Maximum Cell Size do trimmer = 8 m** (antes 800 m, padrão) → 5,36 M células | ≤ 1,5 % | saída 0,76–0,79 · **centro (fonte) 0,83–0,86** | malha não era a causa; **aceito** (ver abaixo) |

Critério: vento ±3 %, k ±15 % entre entrada e saída. Lição: o Realizable não preserva o perfil de R&H (Cμ variável).

**Decisão (29/10), substituída pela rodada 4 (§4c, 16/11):** o perfil que interessa é o **incidente na fonte** (centro do domínio), não o da borda de saída
(Blocken et al., 2007). No centro: U a ±1 % e k 14–17 % abaixo do teórico entre 10 e 50 m. O k decai a partir do solo
(maior perto do chão, some no topo), assinatura do tratamento de parede rugosa (Hargreaves & Wright, 2007), não da malha
nem das constantes. **Aceito com registro no relatório:** k menor → menos mistura → concentrações **conservadoras**; a
sensibilidade de Sc_t (0,5–0,9) cobre essa incerteza de difusão. Melhoria possível, se necessário: termos-fonte de
Parente et al. (2011) para k-ε consistente com a CLA.
**Setup validado para V1/V2:** Standard k-ε, σε = 1,225, High y+, solo rugoso ks = 9,793·z₀/0,253, perfil de R&H na entrada
e no topo, Maximum Cell Size 8 m.

## 4c. Rodada 4 do domínio vazio — modelo ABL do STAR (planejada, 16/11)
Ativar *Atmospheric Boundary Layer* (Standard k-ε, Ref. Speed 1,9 m/s, Ref. Height 10 m, z₀ 0,03 m, κ 0,42) e eliminar o
corte da rugosidade (o Output mostrava a rugosidade limitada em 268 738 faces do Solo). Plano inicial era Cμ = 0,013 /
σε = 3,22; revisto abaixo. Ver `star_ccm_tutoriais/11_Atmospheric_Boundary_Layer_referencia.md`.

**Montagem (16/11), revista com o manual (*Setting Up ABL* + *Wall Treatment Models Reference*):**
- A chave do *Roughness Limiter* **não existe** nesta versão: o método *Rough* sempre limita a rugosidade pela distância da
  1ª célula. O *Rough Displaced Origin* não limita, mas não tem B/C e a receita do ABL não vale para ele → fica *Rough*.
- 268 738 faces ≈ **o Solo inteiro** (1,10 km² ÷ 268 738 ≈ 4,1 m² por face, células de 2 m: o trimmer arredonda os 3 m do
  `Refino_Solo` para 8/2² = 2 m) → o centro da 1ª célula estava **abaixo do ks em todo o solo**. A espessura do prisma estava
  certa (2,5 m, absoluta): suspeita no **número de camadas** (padrão 2) ou no prisma não gerado.
- **Rugosidade corrigida:** r = E·z₀/C = 9 × 0,03 / 0,253 = **1,07 m** (a fórmula com 9,793 é do Fluent).
- **Cμ fica 0,09 / σε 1,225** (o manual sugere 0,03–0,11; no equilíbrio νt = κ·u*·z não depende de Cμ). Rodada 4 muda só
  entrada ABL + limitador, para isolar a causa do k baixo.
- Entradas e Topo: *Turbulence Specification* K+Epsilon; *Velocity Specification* Magnitude + Direction; Magnitude, k e ε
  com Method **Atmospheric Boundary Layer**; direção [−0,3827, −0,9239, 0].
- Inicial: *Turbulent Viscosity Ratio* 1E10 (manual); conferir o limite máximo da razão de viscosidade (νt/ν chega a
  ~1,3 milhão no topo).
- Critério antes de rodar: 1 iteração e **nenhuma** linha "Roughness limited" no *Output*.
- **1ª iteração (16/11):** "Roughness limited" **sumiu** ✅ (1 camada + r = 1,07 m). Apareceu "Turbulent viscosity limited on
  4 271 414 cells in Ar": na 1ª iteração é efeito da condição inicial (razão 1E10 em tudo). O que não pode é o limite
  máximo do solver (*K-Epsilon Turbulent Viscosity → Maximum Ratio*, se for 1E5) cortar o perfil: νt/ν = κ·u*·z/ν passa de
  1E5 a partir de ~26 m e chega a ~1,3E6 no topo → **Maximum Ratio 1E7**. Ao convergir, a linha tem de sumir.
- **Iterações 38–48:** com Maximum Ratio 1E7 o aviso de viscosidade sumiu ✅, mas a velocidade foi a **29 m/s** em bolhas
  (o perfil não passa de 3,06 m/s no topo) e apareceu "Reversed flow" em 200–1100 faces de cada saída S07–S13 ❌.
  Causa provável: a razão de viscosidade inicial 1E10 do manual deixa ε ≈ 0 no começo, o k dispara e cria um transiente
  espúrio. **Correção:** condição inicial em equilíbrio (*Turbulence Specification* K + Epsilon com `k_ABL` e `eps_ABL`,
  velocidade `Vel_ABL`), *Clear Solution* e rodar de novo. Critério: nas primeiras 20 iterações a cena fica em 0–3,06 m/s, sem
  "Reversed flow" nem "viscosity limited". Se deformar mesmo assim, o problema está nas condições de contorno (direção do
  vento nas entradas e no Topo).
- **Reinício em equilíbrio (16/11):** inicialização 1,23 m/s no centro da 1ª célula (teoria 1,23) a 3,06 m/s no topo;
  25 iterações com **máximo estável em 3,0587 m/s**, sem "Reversed flow" nem "viscosity limited", resíduos caindo ✅.
  Os resíduos normalizados parecem altos (~0,1 no momento) porque a normalização usa os resíduos das primeiras iterações,
  que já são pequenos quando o campo começa em equilíbrio. O critério é o perfil (U ±3 %, k ±15 %), não o resíduo.

**Resultado da rodada 4 (1000 iterações, 16/11) — APROVADO** · figura e CSVs em `resultados/dominio_vazio_r4/`
(`resultados/plot_dominio_vazio.py` refaz a figura).
| | rodadas 1–3 | **rodada 4** |
|---|---|---|
| U saída ÷ entrada | ≤ 2 % | **−1,5 % na 1ª célula; ±0,7 % de 10 m para cima** |
| k ÷ teórico, 10–70 m (centro / saída) | 0,69–0,86 | **0,976–0,999 / 0,974–1,003** |
| k ÷ teórico acima de 100 m | — | 1,000 |
- **Causas do k baixo nas rodadas 1–3** (corrigidas juntas, sem separar o peso de cada uma): rugosidade cortada em todo o Solo
  (1ª célula abaixo do ks) e, provavelmente, a razão de viscosidade turbulenta podada pelo limite do solver acima de ~26 m.
  Não era o Realizable × Standard sozinho, nem a malha.
- Restam dois desvios locais, **iguais na entrada, no centro e na saída** (o perfil é homogêneo, só não é idêntico ao
  teórico no 1º metro):
  - U na 1ª célula (centro a 1,25 m) = 1,16 m/s contra 1,23 do perfil (−5 %): z₀ efetivo ≈ 0,036 m na lei de parede;
  - k na 2ª célula (2,5–4,5 m) = +19 %: o gradiente entre a 1ª e a 2ª célula fica maior e gera mais produção. É o pico de k
    junto ao solo descrito com funções de parede rugosas (Blocken et al., 2007).
- **Setup validado para o V1:** Standard k-ε (Cμ 0,09, σε 1,225), High y⁺; modelo ABL nas entradas e no Topo (Magnitude +
  Direction); Solo *Rough*, r = 1,07 m, prisma único de 2,5 m; Maximum Ratio da viscosidade turbulenta 1E7; condição inicial
  em equilíbrio (`Vel_ABL`, `k_ABL`, `eps_ABL`); Maximum Cell Size 8 m. Isso substitui a "Decisão (29/10)" de §4b.
- No V1, conferir no *Output* que não volta "Roughness limited" perto da planta (cilindro R80 com células de 1 m ao lado do
  prisma de 2,5 m).

## V1 com os prédios — montagem (17/11)
1. *Save As* da simulação do domínio vazio aprovada (`LD_V1_oficial`): física, field functions, reports e solver herdados.
2. *Import Surface Mesh* do `volume_ar_LD.stl` v4 → *Assign Parts to Regions* → **Use Existing Region (Ar)** + *Create a
   Boundary for Each Part Surface*. O STAR cria um contorno por superfície **com prefixo do part** (inclusive cópias de
   S01–S16, Solo, Topo). Correção: religar os 18 contornos antigos (que guardam as condições) às superfícies novas pelo
   *Part Surfaces*, apagar as cópias vazias e tirar o domínio vazio da região → 90 contornos.
3. Malha (mesma base validada no domínio vazio): Base 8 m, Maximum Cell Size 8 m, prisma único de 2,5 m no Solo,
   `Refino_Solo` (3 m → células de 2 m até 30 m em todo o domínio). Controles novos:
   | controle | superfícies / forma | tamanho | prismas |
   |---|---|---|---|
   | `Externo` | S01–S16, Topo (religar às superfícies novas) | 8 m | — |
   | `Saidas` | 5 `Saida_*` | alvo 0,03 / mín. 0,015 m (≥ 10 células na chaminé de 12") | desligados |
   | `PredioO3` | `O3_*`, `exaustor_*`, `chamine_offgas_*` | 0,25 / 0,05 m | desligados |
   | `Obstaculos` | demais obstáculos | 0,5 / 0,1 m | desligados |
   | `R80` | cilindro R 80 m, h 70 m (shape part) | 1 m | — |
   | `R300` | cilindro R 300 m, h 120 m (shape part) | **4 m** (abaixo de 30 m vale o 2 m do `Refino_Solo`) | — |
   Estimativa ~7 M células. Com R300 a 3 m (= 2 m no trimmer, que só usa base/2ⁿ) seriam ~10 M.
4. Conferir na 1ª iteração que não aparece "Roughness limited" perto da planta.

**Malha executada (17/11): 7 064 089 células** (estimativa 7 M).

**Contornos e fontes do V1a (tudo ligado: emergência + alívio da chaminé)**
- S01–S16, Solo, Topo: herdados do domínio vazio. Obstáculos: *Wall* lisa (padrão), escalar *Zero Flux*.
- Passive Scalar com 5 componentes, nesta ordem: `O3_910`, `O3_920`, `O3_930`, `O3_940`, `O3_chamine`; *Clip Below Min* 0;
  Sc_t 0,7; convecção de 2ª ordem.
- Fontes (*Mass Flow Inlet*, direção normal à face = +x, Leste); ṁ = ρ·Q com **ρ = 1,06 kg/m³** (densidade constante do
  ar no continuum, condição do local):
  | contorno | Q | ṁ | velocidade na face | turbulência (I / L) | escalar |
  |---|---|---|---|---|---|
  | Saida_910 / 920 | 10,5 m³/s (LX 816) | **11,13 kg/s** | ~39 m/s (0,270 m²) | 5 % / 0,03 m | próprio = 1 |
  | Saida_930 / 940 | 4,2 m³/s (HL 4S) | **4,45 kg/s** | ~25 m/s (0,171 m²) | 5 % / 0,03 m | próprio = 1 |
  | Saida_chamine | 2 300 kg/h | 0,639 kg/s | ~8,3 m/s (0,073 m²; real ~7,2 m/s, gás 15 % mais denso) | 5 % / 0,02 m | próprio = 1 |
- Malha: válida, sem volume negativo, face validity 1,0 em 100 %, volume change mínimo 0,011.

**Leitura dos escalares (conversão para ppm)**
- φᵢ = fração mássica, no ponto, do gás que saiu da fonte i (1 na boca, dilui a jusante).
- Exaustores (gás ≈ ar): **ppm = φᵢ · C_exaustão,i**, com C_exaustão = vazão de O₃ vazada no prédio ÷ vazão do exaustor
  (pendência A1). Enquanto não chega: mapas de **diluição 1/φ** e "concentração máxima admissível na descarga" para não
  passar de 0,01 / 0,2 / 0,5 / 3 ppm em cada receptor (C_máx = limiar/φ).
- Chaminé (13 % em massa de O₃ em O₂): ppm = φ · 0,13 · (28,96/48) · 10⁶ = **78 400 · φ**. Limiares em φ: 0,01 ppm →
  1,3e-7; 0,2 → 2,6e-6; 0,5 → 6,4e-6; 3 → 3,8e-5.
- Superposição: ppm total = Σ φᵢ·Cᵢ, só entre escalares do **mesmo** campo de velocidade.
- Receptores (sondas a 1,5 m): SDCD, CCM, prensas e os 6 eventos marcados pela LD (coordenadas em `_privado/`).
- Checagem: balanço de cada escalar (fluxo que sai pelas saídas = ṁ da fonte × 1).

**1ª iteração do V1 (17/11):** escalares e reports funcionando, cenas em log10. "Roughness limited on **12 682 faces**" no
Solo: é a área da planta, onde as células junto ao chão são de 1 m ou menores e o centro da 1ª célula fica abaixo de
r = 1,07 m. Fora dela, nenhuma face é limitada (prisma de 2,5 m).
- **Decisão proposta:** rugosidade em duas zonas, por field function no *Roughness Height* do Solo:
  `r_solo = (sqrt(pow($$Position[0]-15.5,2)+pow($$Position[1]-15.7,2)) < 150) ? 0.18 : 1.07`
  - fora de R 150 m: z₀ = 0,03 m (terreno, mesmo do perfil de entrada validado) → r = 1,07 m;
  - dentro de R 150 m (todos os obstáculos modelados, o mais distante a ~133 m): **z₀ = 0,005 m** (piso pavimentado,
    classe "smooth" de Davenport–Wieringa) → r = 9 × 0,005 / 0,253 = 0,18 m.
  - É a recomendação de Blocken et al. (2007): rugosidade consistente com o perfil a montante e a do chão real na zona
    central, onde os prédios estão explícitos. Troca o corte do limitador (dependente da malha) por uma escolha declarada.
- Máximo de velocidade na 1ª iteração 48,7 m/s (jato esperado ~39 m/s na 910/920): acompanhar; se não cair, conferir a
  área das `Saida_*` remalhadas.

**Pós-processamento do V1 (pontos, cortes e cenas)** · coordenadas em `_privado/receptores_V1.csv`
- 10 *Point Probes*: SDCD, CCM, prensas (piso e 2º nível) e os 6 eventos E1–E6 lidos da planta marcada pela LD (±1 m);
  todos conferidos fora dos obstáculos (o mais próximo a 1 m de uma fachada).
- Planos: horizontais a z = 1,5 m (respiração) e z = 6 m (altura das descargas); verticais **ao longo do vento** pelas
  descargas e pela chaminé (normal horizontal ⟂ ao vento NNE: [0,9239; −0,3827; 0]).
- Cenas: U a 1,5 m; cada escalar a 1,5 m em **escala log** (1e-7 a 1e-1); escalares dos exaustores e da chaminé nos
  cortes verticais.
- Convergência: 5 reports "máximo de cada escalar nos 10 receptores" + monitor; no fim, tabela XYZ dos receptores com os
  5 escalares exportada em CSV para as tabelas de diluição e ppm.
- Operação normal (V1b): cópia com 910/920 desligados (só 930/940 + chaminé), porque os jatos de 12 kg/s mudam o
  escoamento local e a superposição dos escalares só vale dentro do mesmo campo de velocidade.

## Geometria v4 (16/11)
`volume_ar_LD.stl` com as **4 descargas horizontais para Leste** (+x) e a **chaminé do off-gás** (12", topo do bloco alto,
saída horizontal para Leste a ~21,5 m) → 90 superfícies, fontes `Saida_910/920/930/940` e `Saida_chamine`.
A tabela de objetos foi **reconstruída** do STL anterior (a pasta `_privado` se perdeu no reinício do ambiente); as 83
superfícies comuns conferem com a versão anterior a menos de 2 mm.

## Plano B (se o remesher reclamar)
Wrapper no mesmo part, com *Proximity Refinement* e *Contact Prevention* (2 grupos: `laje_prensas` × tanques sob a
laje; pilares × tanques), *Minimum Size* ≈ 0,8 m. Ver `09_Surface_Wrapper_referencia.md`.
