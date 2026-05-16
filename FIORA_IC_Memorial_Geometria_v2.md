# FIORA IC

## Memorial Descritivo de Geometria — v2.0

**Biorreator Anaeróbio de Alta Carga — Projeto Piloto 50 m³**

Versão **2.0** | Data: 16/Mai/2026 | **CONFIDENCIAL — Tecnologia Patenteada**

| | |
|---|---|
| **Documento** | Memorial Descritivo de Geometria — FIORA IC |
| **Projeto** | Estudo CFD — Reator Anaeróbio de Alta Carga — Piloto |
| **Cliente** | Gerir Gestão e Instrução — Vinícius Alberoni |
| **Executor CFD** | CAEXPERTS — Ricardo Barbosa de Barros |
| **Referência** | Proposta R1 \| Stage 1 \| Stage 2 \| Conversas técnicas 14–16/Mai/2026 |
| **Versão** | 2.0 — Geometria Final Validada para Malha |
| **Script CAD** | `FIORA_IC_geometry_v5_6.py` (CadQuery → 6 arquivos STEP) |

**PROPÓSITO:** Este documento consolida, em formato técnico formal, todas as informações de geometria do reator FIORA IC obtidas a partir dos croquis do inventor, dos áudios, mensagens de alinhamento técnico (14–16/Mai/2026) e do Relatório Stage 2. Substitui a v1.0 — corrige a interpretação do topo, adiciona saídas de biogás e efluente, atualiza difusores, bocais e o pipeline de operações no STAR-CCM+. Destina-se à CAEXPERTS como fonte única de referência para construção do modelo CAD e setup da simulação CFD.

---

## 📋 CHANGELOG v2.0 (sobre v1.0)

| Item | v1.0 (16/05 manhã) | v2.0 (16/05 noite) | Fonte da atualização |
|---|---|---|---|
| Topo do reator | Calota **côncava** | Calota **CONVEXA** (domo toroesférico) | Vinícius — mensagem 16/05 18:04: "saída centralizada no eixo, no ponto mais alto" só é consistente com convexo |
| Saída central de biogás no topo | Não especificada | **DN100, central, no ápice do domo** | Vinícius — 16/05 18:04 |
| Saída lateral de efluente | "Lateral próxima ao topo" (sem cota) | **DN100, z=14,20 m, az=180°, independente** | Vinícius — 16/05 18:04 |
| Inclinação dos bocais | 7,5° (valor médio da faixa) | **7,0°** (valor exato) | Vinícius — 16/05 18:04 |
| Ângulo tangencial dos bocais | Não especificado | **80° em relação à radial** (anti-horário confirmado) | Vinícius — 16/05 18:04 |
| Diâmetro do bocal | DN80 (estimativa) | **DN80 confirmado** | Vinícius — 16/05 18:04 |
| Difusores de microbolhas | 4× DN60 na parede lateral em z=1,75 m | **12× DN225/DN250 no FUNDO, 6 setores × 2** | Vinícius — 16/05 16:50 |
| Composição do gás recirculado | Não especificada | **CH₄ 65% / CO₂ 34% / H₂S 1% / H₂ traço** | Vinícius — 16/05 18:04 |
| Arquivos CAD | 5 STEP | **6 STEP** (inclui `diffusers` p/ Imprint) | Atualização CAD |
| Operações no STAR-CCM+ | — | **Seção 12 nova**: pipeline Unite/Imprint/Boundary | Esta versão |

---

## 1. Visão Geral do Reator

O FIORA IC é um biorreator anaeróbio de alta carga com arquitetura IC (Internal Circulation) modificada, operando em modo de fluxo ascendente. O reator trata vinhaça de cana-de-açúcar para produção de biogás (H₂ e CH₄) através de duas zonas funcionais distintas em série: zona hidrogênica inferior (fermentação escura) e zona metanogênica superior.

| Parâmetro Geral | Valor Confirmado | Fonte |
|---|---|---|
| Volume útil (V) | 50 m³ | Proposta R1 / Stage 1 |
| Relação H/D | 7 | Stage 1 / Confirmado Vinícius |
| Diâmetro interno (D) | 2,09 m | Calculado: D = ∛(4V/7π) |
| Altura útil (H) | 14,6 m | Calculado: H = 7 × D |
| Área da seção transversal | 3,43 m² | A = π/4 × D² |
| Temperatura de operação | 35 °C | Stage 1 / Stage 2 §2 |
| Pressão de operação | 1,5 kgf/cm² (147,1 kPa) | Stage 1 |
| Substrato | Vinhaça de cana-de-açúcar | Stage 1 |
| DQO afluente (projeto) | 25.000 mg/L (faixa 20–30 mil) | Stage 1/2 |
| Vazão afluente (Q_af) | 50 m³/d (faixa 33–50 m³/d) | Stage 1 / Stage 2 §3 |
| Recirculação líquida | 7 × Q_af = 350 m³/d | Stage 1 / Confirmado Vinícius |
| Recirculação gasosa | 40% do biogás de topo | Vinícius — áudio 15/05 17:12 |

**Arquitetura funcional (de baixo para cima):**
- Zona de alimentação + leito granular (0–20% da altura): entrada tangencial, lodo granular, biochar, eletrodos eletroativos, difusores de microbolhas no fundo
- Zona de fermentação / separação intermediária (20–60%): separadores trifásicos 1, 2 e 3 coletando H₂/CO₂
- Zona de polimento / metanogênese (60–95%): separador trifásico 4 coletando CH₄/CO₂/H₂S
- Zona de separação final e saída de efluente (95–100%): câmara de biogás no domo + saída lateral de efluente

---

## 2. Corpo Principal do Reator

### 2.1 Geometria do cilindro

| Elemento | Valor | Fonte/Observação |
|---|---|---|
| Forma | Cilindro vertical circular | Stage 1 |
| Diâmetro interno | 2,09 m | Calculado |
| Altura útil (total) | 14,6 m | Calculado |
| Altura do trecho cilíndrico | 14,339 m | H − TOP_DEPTH |
| Material (referência) | Aço inoxidável | Padrão industrial |
| Espessura de parede (CFD) | Não modelada (parede infinitamente fina) | Simplificação CFD |
| Rugosidade interna | 0 (aço liso) | Padrão CFD |

### 2.2 Topo do reator — calota toroesférica CONVEXA ★ CORRIGIDO v2.0 ★

O topo do reator é uma calota toroesférica **convexa** (domo bulging para cima). A interpretação da v1.0 como "côncava" foi revisada após a resposta do Vinícius em 16/05 18:04, que confirma "saída centralizada no eixo vertical do reator, no ponto mais alto da tampa" — geometricamente consistente apenas com domo convexo (cujo ponto mais alto é o ápice central, sobre o eixo).

| Parâmetro | Valor | Fonte/Observação |
|---|---|---|
| Tipo | Calota toroesférica convexa | Vinícius — mensagem 16/05 18:04 |
| Altura do domo (acima do cilindro) | D/8 = 0,261 m | Padrão ASME |
| Raio esférico equivalente (R_sph) | 2,221 m | Derivado: R = (R²+h²)/(2h) para profundidade exata |
| Raio do joelho (R_knuckle) | 0,10 × D = 0,209 m | ASME padrão — fillet aplicado no CAD |
| Topo do trecho cilíndrico | z = 14,339 m do fundo | H − TOP_DEPTH |
| Ápice do domo | z = 14,600 m do fundo | Topo absoluto, sobre o eixo Z |

> ✅ Topo convexo confirmado. O ápice do domo está no eixo central, em z=14,6 m. Saída de biogás localizada exatamente nesse ponto.

### 2.3 Saída central de biogás (NOVO v2.0)

| Parâmetro | Valor | Fonte |
|---|---|---|
| Diâmetro nominal | DN100 (100 mm) | Vinícius — 16/05 18:04 |
| Posição | Central, sobre o eixo Z, no ápice do domo | Vinícius — 16/05 18:04 |
| Função | Saída de biogás separado para sistema externo | Câmara de gás no topo |
| BC no CFD | Pressure Outlet (P_rel = 0) | — |

### 2.4 Saída lateral de efluente (NOVO v2.0)

| Parâmetro | Valor | Fonte |
|---|---|---|
| Diâmetro nominal | DN100 (100 mm), **independente do DN50 do separador 95%** | Vinícius — 16/05 18:04 |
| Cota (z do fundo) | **14,20 m** (14 cm abaixo do topo do cilindro) | Vinícius: "10–15 cm abaixo da borda superior operacional" |
| Posição angular | 180° (diametralmente oposta aos DN50 dos separadores) | Adotado — distribuição equilibrada |
| Função | Controle do nível operacional de líquido; descarga do efluente tratado | Vinícius — 16/05 18:04 |
| BC no CFD | Pressure Outlet (P_rel = 0) | — |

---

## 3. Sistema de Entrada — Bocais Tangenciais ★ ATUALIZADO v2.0 ★

A alimentação entra por 6 bocais tangenciais na base. Vazão total de entrada = alimentação (50 m³/d) + recirculação líquida (350 m³/d) = 400 m³/d, dividida pelos 6 bocais.

| Parâmetro | Valor | Fonte |
|---|---|---|
| Número de bocais | 6 | Stage 1 / Croqui 1 e 2 |
| Espaçamento angular | 60° (= 360°/6) | Croqui 2 |
| Azimutes | 0°, 60°, 120°, 180°, 240°, 300° | Croqui 2 |
| Altura do centro | 0,25 m do fundo | Stage 1 |
| **Inclinação vertical** | **7,0° ASCENDENTE** | **Vinícius 16/05 18:04 — valor exato** |
| **Ângulo horizontal (com a radial)** | **80° (caso base)** | **Vinícius 16/05 18:04** |
| **Sentido de rotação** | **Anti-horário visto de cima — CONFIRMADO** | **Vinícius 16/05 18:04** |
| Diâmetro nominal | DN80 (80 mm) — confirmado | Vinícius 16/05 18:04 |
| Comprimento do bocal (stub) | 0,30 m | Estimativa CFD |
| Vazão por bocal | 400 ÷ 6 = 66,7 m³/d = 7,7×10⁻⁴ m³/s | Calculado |
| Velocidade no bocal | ~0,15 m/s | Calculado |
| Reynolds no bocal | ~14.000 (turbulento) | Calculado |

### 3.1 Cenários de sensibilidade — ângulo horizontal (NOVO v2.0)

| Cenário | NOZZLE_TANG_ANGLE | Caracterização | Inclinação vertical |
|---|---|---|---|
| **C0 (base)** | 80° | Quase tangencial, swirl forte | 7,0° |
| C1 | 75° | Swirl forte, leve componente radial | 7,0° |
| C2 | 70° | Mais radial, swirl menor, melhor distribuição | 7,0° |
| C3 | 85° | Mais tangencial, swirl agressivo | 7,0° |

Os 3 cenários alternativos (C1–C3) serão rodados após o caso base como análise de sensibilidade, conforme orientação Vinícius 16/05 18:04.

---

## 4. Separadores Trifásicos Internos

4 conjuntos de separadores em diferentes alturas. Cada conjunto é composto por 2 meias-placas inclinadas (esquerda + direita), formando perfil "Λ" com abertura central para passagem do tubo DN100.

| Nível | Altura do Fundo | % da Altura | Ângulo (Placa) | Função Principal |
|---|---|---|---|---|
| Sep. 1 (inferior) | 2,92 m | 20% | 47,5° | Separação H₂ — limite zona hidrogênica |
| Sep. 2 (intermediário) | 5,84 m | 40% | 52,5° | Separação H₂ — zona intermediária |
| Sep. 3 (superior) | 8,76 m | 60% | 57,5° | Separação H₂ — topo zona fermentativa |
| Sep. 4 (topo) | 13,87 m | 95% | 57,5° | Separação CH₄/CO₂ — zona metanogênica |

| Parâmetro Construtivo | Especificação |
|---|---|
| Espessura das placas | 8 mm |
| Área livre hidráulica | 75–80% da seção transversal (Stage 1) |
| Gap central (para DN100) | DN100 + folga = ~0,13 m de raio livre |
| Geometria | Meia-placa esquerda + meia-placa direita → perfil Λ |
| Borda externa | Clipada ao contorno cilíndrico do reator (intersecção booleana) |
| Saída de cada separador | 1 × DN50 (uma por nível) na parede lateral, **todas a azimute 0°** |
| BC no CFD | Baffle No-slip (ambos os lados) |
| Material | Aço inoxidável |

---

## 5. Sistema de Tubulação — Retorno DN100

Tubo único DN100 descendo pelo centro do reator. Componente central da circulação interna (IC).

### 5.1 Arquitetura (Vinícius — áudio 15/05 17:05)
- Separadores 20%/40%/60%: cada um drena por DN50 → juntam externamente → DN100 externo → Separador bifásico A → líquido retorna em DN50
- Separador 95%: drena por DN50 → Separador bifásico B → líquido retorna em DN50
- Ambos os retornos (DN50 de A + DN50 de B) → juntam → **DN100 ÚNICO** que desce pelo centro do reator → fundo

| Parâmetro | Valor | Fonte |
|---|---|---|
| Diâmetro externo | DN100 (100 mm) | Vinícius — 15/05 16:00 |
| Espessura de parede | 4 mm | Padrão tubulação |
| Diâmetro interno | 92 mm | Calculado |
| Posição | Centro do reator (eixo de simetria) | Arquitetura IC |
| Cota inferior | z = 1,0 m do fundo | Vinícius — arquitetura IC |
| Cota superior | z = 14,29 m do fundo (logo abaixo da borda do domo) | Adotado para não conflitar com domo |
| Função | Retorno de líquido separado → base do reator | Arquitetura IC |
| Entrada do tubo | Topo (conecta ao retorno externo) → Velocity Inlet no CFD | — |
| Saída do tubo | Fundo do reator (mistura com alimentação) → Interface com domínio principal | — |
| BC no CFD | Baffle No-slip (modelado como cilindro anelar de parede fina) | — |

### 5.2 Saídas DN50 dos separadores

| Parâmetro | Valor | Fonte |
|---|---|---|
| Quantidade | 4 (uma por separador) | — |
| Diâmetro | DN50 (50 mm) | Vinícius — 15/05 15:54 |
| **Posição angular** | **Todos a 0° (simplificação CFD)** | Stage 1 |
| Cotas | 2,92 / 5,84 / 8,76 / 13,87 m do fundo | Vinculadas aos separadores |
| BC no CFD | Pressure Outlet (P_rel = 0) | — |

---

## 6. Módulo Eletroativo — Eletrodos Ânodo/Cátodo

4 placas retangulares (2 ânodos + 2 cátodos) na zona inferior do reator, abaixo do primeiro separador (20%). Modeladas como **sólidos inertes (No-slip Wall)** no caso base CFD — sem acoplamento eletroquímico nesta etapa.

| Parâmetro | Valor | Fonte |
|---|---|---|
| Número total de placas | 4 (2 ânodos + 2 cátodos) | Vinícius — módulo eletroativo 15/05 |
| Área por placa | 1,25 m² (H 2,4 m × L 0,52 m) | Vinícius — tabela 15/05 |
| Área eletroativa total | 5,0 m² | Vinícius — tabela 15/05 |
| Espessura | 8 mm | Padrão eletrodo industrial |
| Gap ânodo–cátodo | **Máximo 30 mm — adotado face-a-face** (centro-a-centro = 38 mm) | Vinícius — 15/05 16:50 |
| Arranjo | 2 pares (Par 1 + Par 2) | Derivado |
| Posição angular | Par 1: 0° / Par 2: 180° | Adotado — simetria diametral |
| Posição radial | 65% do raio = 0,68 m do centro | Adotado |
| Cota base | 0,25 m do fundo | Vinícius — "abaixo do 1° separador" |
| Cota topo | 2,65 m do fundo | 0,25 + 2,40 |
| Folga até Sep. 20% (2,92 m) | 0,27 m | Verificado |

🚨 Parâmetros elétricos (tensão, corrente) são para próxima etapa. No caso base, eletrodos são sólidos inertes.

---

## 7. Fases Sólidas Internas — Biochar e Lodo Granular

Biochar e lodo granular **NÃO possuem geometria CAD**. Representados como fases sólidas dispersas em abordagem Euleriana-Euleriana (E-E) com KTGF.

| Fase Sólida | d₅₀ [mm] | ρ aparente [kg/m³] | Parâmetros |
|---|---|---|---|
| Lodo granular | 2,0 | 1.460 | SST ≈ 70 g/L \| α_inicial = 0,35 na zona inferior \| d: padrão literatura \| ρ: Wang et al. 2009/2010 |
| Biochar vegetal | 3,0 | 500 | Dosagem 5,0 g/L \| α ≈ 1,0% \| Esfericidade 0,65 \| Porosidade interna 60–70% \| ρ_real = 1.500 kg/m³ |

---

## 8. Difusores de Microbolhas ★ ATUALIZADO v2.0 ★

40% do biogás coletado no topo é recirculado por blower dedicado e injetado no fundo do reator através de **12 difusores de disco DN225/DN250** (adotado DN250 no CAD), distribuídos em **6 setores entre os bocais**, com **2 difusores por setor** em disposição radial (1 interno + 1 externo).

| Parâmetro | Valor | Fonte |
|---|---|---|
| Tipo | Difusores de bolha fina, tipo disco | Vinícius — 16/05 16:50 |
| Quantidade | **12** | Vinícius — 16/05 16:50 |
| Diâmetro nominal | **DN225/DN250** (adotado DN250 no CAD) | Vinícius — 16/05 16:50 |
| Localização | **No FUNDO, entre os tubos de alimentação** | Vinícius — 16/05 16:50 |
| Disposição azimutal | 6 setores em az = 30°, 90°, 150°, 210°, 270°, 330° (entre os bocais a 0/60/120/180/240/300°) | Adotado |
| Disposição por setor | 2 difusores radiais: 1 interno (r=0,35 m) + 1 externo (r=0,80 m) | Adotado |
| Vazão operacional por difusor | 2–4 Nm³/h | Vinícius — 16/05 16:50 |
| Vazão total recirculada | 24–48 Nm³/h | Calculado (12 × unitária) |
| Diâmetro das bolhas geradas | 1–3 mm (adotado d₃₂ = 2 mm no CFD) | Vinícius — 16/05 16:50 / Notas L1 |
| Pressão do blower | ~2,0 kgf/cm² (contrapressão = coluna líquida + sólidos + perdas hidráulicas) | Vinícius — 16/05 16:50 |
| Composição do gás recirculado | **CH₄ 65% / CO₂ 34% / H₂S 1% / H₂ traço** | Vinícius — 16/05 18:04 |
| Densidade do gás (calculada) | ρ ≈ 1,075 kg/Nm³ | Calculado da composição |
| Forma de modelagem CFD | **Discos atravessam o fundo** → Imprint no STAR-CCM+ → 12 faces circulares no fundo → **Mass Flow Inlet** | Esta versão |

---

## 9. Módulo de Bioestimulação Magnética (Próxima Etapa)

🚨 Módulo **externo** ao domínio CFD, **fora do escopo** do caso base atual.

| Parâmetro | Valor |
|---|---|
| Intensidade do campo | 30 mT (campo estático) |
| Tempo de exposição | 30 s |
| Modelagem CFD | Requer módulo MHD — próxima etapa |

---

## 10. Cenários M30/M60 — Módulo Externo de Condicionamento (Stage 2)

Conforme Relatório Stage 2 §14, podem ser avaliados cenários com módulo externo de condicionamento da recirculação líquida. **Externo ao domínio CFD** — entra apenas como modificação do kapp,A via fator empírico Φ.

| Cenário | Tempo médio de exposição | Volume útil estimado | Fator empírico Φ |
|---|---|---|---|
| C0 | — | — | 1,00 (sem módulo) |
| M30 | 30 s | 100–150 L | 1,10 |
| M60 | 60 s | 200–250 L | 1,18 |

Aplicação: `kapp,A,mod = kapp,A × Φ`. Apenas na Região A.

---

## 11. Arquivos CAD — Resumo Executivo ★ ATUALIZADO v2.0 ★

Executar o script **`FIORA_IC_geometry_v5_6.py`** (CadQuery) para gerar os **6 arquivos STEP**:

| Arquivo STEP | Corpos | Conteúdo / Observação |
|---|---|---|
| `FIORA_IC_v5_6_fluid_domain.step` | 1 sólido | Cilindro D=2,09 m H=14,6 m + **DOMO CONVEXO** (D/8) + **furo DN100 central biogás** + 4 furos DN50 (az 0°) + **furo DN100 efluente lateral** (z=14,20 m, az 180°) |
| `FIORA_IC_v5_6_return_tube.step` | 1 sólido | Tubo DN100 anelar (parede 4 mm) — **baffle interno** no STAR-CCM+ |
| `FIORA_IC_v5_6_separators.step` | 8 sólidos | 2 meias-placas × 4 níveis — clipadas ao cilindro por intersecção booleana |
| `FIORA_IC_v5_6_nozzles.step` | 6 sólidos | Bocais DN80 tangenciais 80° + inclinação 7° ascendente, anti-horário — atravessam a parede |
| `FIORA_IC_v5_6_electrodes.step` | 4 sólidos | 2 pares A/C, gap 30 mm face-a-face — sólidos inertes |
| `FIORA_IC_v5_6_diffusers.step` | 12 sólidos | 12 discos DN250 no fundo — **ferramenta de Imprint** (deletar após criar as faces) |

---

## 12. Operações no STAR-CCM+ (NOVO v2.0)

Pipeline completo após importar os 6 arquivos STEP no STAR-CCM+.

### 12.1 Operações Booleanas no módulo 3D-CAD

| Ordem | Operação | Alvo | Comando | Resultado |
|---|---|---|---|---|
| 1 | **Unite** | `fluid_domain` + `nozzles` | Right-click no 3D-CAD Model > Unite Bodies | Cria 6 canais contínuos de Velocity Inlet |
| 2 | **Imprint** | `fluid_domain` + `diffusers` | Right-click > Imprint Bodies | Cria 12 faces circulares no fundo (Ø 250 mm) |
| 3 | **Delete** | Bodies `diffusers` | Botão direito > Delete | Stubs cumpriram seu papel |
| 4 | **Não unir** | `return_tube`, `separators`, `electrodes` | — | Permanecem como corpos separados (baffles/walls) |

### 12.2 Criação de Parts e Regions

1. Geometry > 3D-CAD Models > **New Geometry Parts from CAD Model**
2. Assign Parts to Regions → criar **uma Region única** (`Reactor_Fluid`) a partir do `fluid_domain` Part
3. Para cada baffle (`return_tube`, `separators`, `electrodes`) marcar **"Create Boundaries from Part Surfaces"** com tipo Baffle ou Wall

### 12.3 Renomeação de Boundaries

| Boundary | Nome | Tipo BC | Valor |
|---|---|---|---|
| 6× faces externas dos bocais | `Inlet_Nozzle_01..06` | **Velocity Inlet** | Q = 66,7 m³/d/bocal, T = 35 °C, fase líquida |
| Face topo do `return_tube` | `Inlet_DN100_top` | **Velocity Inlet** | Q = 350 m³/d, direção −Z, T = 35 °C |
| 12× faces circulares no fundo | `Inlet_Diffuser_01..12` | **Mass Flow Inlet** | ṁ = (40% × Q_biogás)/12, T = 35 °C, gás (65% CH₄ / 34% CO₂ / 1% H₂S / traço H₂), d_bolha = 2 mm |
| Face central no topo do domo | `Outlet_Biogas` | **Pressure Outlet** | P_rel = 0, abertura primária para gás |
| Face DN100 lateral em z=14,20 m | `Outlet_Effluent` | **Pressure Outlet** | P_rel = 0, controla nível operacional |
| 4× furos DN50 nos separadores | `Outlet_DN50_20/40/60/95` | **Pressure Outlet** | P_rel = 0, multifásico |
| Parede cilíndrica + domo + fundo | `Wall_Reactor` | **No-slip Wall** | Rugosidade = 0 |
| Faces dos `separators` | `Baffle_Separator_01..08` | **Baffle No-slip** | Ambos os lados |
| Parede ext. + int. do `return_tube` | `Baffle_DN100` | **Baffle No-slip** | Separa fluxo ↓ (dentro) de ↑ (fora) |
| Faces dos `electrodes` | `Wall_Electrode_A1/A2/C1/C2` | **No-slip Wall** | Sólido inerte (caso base) |

### 12.4 Verificação geométrica

**Tools > Geometry Check** → deve dar **zero erros**. Pontos críticos:
- Junção cilindro/domo (fillet do joelho aplicado?)
- 12 faces criadas pelo Imprint (alguma degenerada?)
- 6 cilindros dos bocais com `Unite` bem-sucedido?

### 12.5 Mapa consolidado de Boundary Conditions

| # | Superfície | Tipo BC | Fase | Valor |
|---|---|---|---|---|
| 1 | 6 faces externas bocais | Velocity Inlet | Líquido | Q_total = 400 m³/d ÷ 6 |
| 2 | Face topo DN100 | Velocity Inlet | Líquido | Q = 350 m³/d, dir −Z |
| 3 | 12 difusores | Mass Flow Inlet | Gás | 40% × Q_biogás_total ÷ 12 |
| 4 | 4 furos DN50 paredes | Pressure Outlet | Multifásico | P_rel = 0 |
| 5 | Furo central topo (DN100) | Pressure Outlet | Multifásico | P_rel = 0 (saída biogás) |
| 6 | Furo lateral topo (DN100) | Pressure Outlet | Líquido | P_rel = 0 (saída efluente) |
| 7 | Parede + domo + fundo | No-slip Wall | — | Rugosidade = 0 |
| 8 | 8 placas separadores | Baffle | — | No-slip ambos lados |
| 9 | Parede DN100 (anelar) | Baffle | — | No-slip |
| 10 | 4 placas eletrodos | No-slip Wall | — | Sólidos inertes |

### 12.6 Próxima etapa — Volume Mesh

| Item | Recomendação |
|---|---|
| Mesher | Polyhedral + Prism Layer + Surface Remesher |
| Base size | ~50 mm (D/40) |
| Prism layers | 5–8 camadas, total ~10 mm, growth 1,3, y⁺ alvo ~30 |
| Refinamento local | Bocais (10 mm), eletrodos (15 mm), difusores (15 mm), separadores (20 mm) |
| Tamanho mínimo | ~5 mm |
| Total estimado | 2–5 milhões de células |

---

## 13. Histórico de Versões da Geometria CAD

| Versão | Data | Principais mudanças |
|---|---|---|
| v5.1 | 15/05 | Versão inicial — separadores clipados, bocais |
| v5.2 | 16/05 | Topo convexo (tentativa), correção de bocais, gap eletrodos |
| v5.3 | 16/05 | Topo côncavo (interpretação v1.0 do memorial), DN100 baffle, DN50 todos a 0° |
| v5.4 | 16/05 | Difusores como ferramenta de Imprint (4× DN60 na parede) |
| v5.5 | 16/05 | Difusores reespecificados: 12× DN250 no fundo (Vinícius 16:50) |
| **v5.6** | **16/05 18:04** | **Topo revertido para CONVEXO + saída biogás topo + saída efluente lateral + bocais 7°/80° + composição gás** |
| v5.6.1 | 16/05 | Fix bug do `sphere.cut` (box pequeno demais — bola esférica fantasma no topo) |
| v5.6.2 | 16/05 | Fix posição da saída de efluente (estava no domo, movida para parede cilíndrica) |

---

**FIORA IC — Memorial Descritivo de Geometria v2.0 — 16/Mai/2026 | CONFIDENCIAL — Tecnologia Patenteada**
