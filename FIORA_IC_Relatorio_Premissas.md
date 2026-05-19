# RELATÓRIO DE PREMISSAS TÉCNICAS

## Estudo CFD/DEM — Biorreator FIORA IC | Piloto 50 m³

**Documento:** RPT-FIORA-PREM-001 — Rev. A
**Data de emissão:** 18 de maio de 2026
**Classificação:** CONFIDENCIAL — Tecnologia Patenteada
**Linha de baseline:** Geometria CAD v5.11 | Memorial Geometria v3.0 | Planilha Setup v4.0

| Campo | Conteúdo |
|---|---|
| **Projeto** | Estudo CFD de Reator Anaeróbio de Alta Carga — Projeto Piloto |
| **Cliente** | Gerir Gestão e Instrução — Vinícius Alberoni |
| **Executor CFD** | CAEXPERTS — Creative Solutions Engenharia e Consultoria LTDA |
| **Gerente do projeto** | Marcus *(CAEXPERTS)* |
| **Engenheiro CFD responsável** | Gabriel Rozo |
| **Diretor técnico** | Ricardo Barbosa de Barros |
| **Proposta comercial** | Proposta CAEXPERTS de 29/04/2026 — Valor R$ 17.562,00 (incluindo desconto especial 12,5%) |
| **Cronograma contratual** | 37 dias úteis (Etapa 1: 10 d \| Etapa 2: 10 d \| Etapa 3: 20 d) |
| **Software base** | Simcenter STAR-CCM+ (SIEMENS Digital Industries Software) |
| **Software auxiliar (CAD)** | CadQuery 2.x (Python) |

---

## 1. Sumário Executivo

Este relatório consolida o conjunto formal de **premissas técnicas, geométricas, operacionais, físico-químicas e numéricas** adotadas para o estudo CFD/DEM do biorreator anaeróbio de alta carga FIORA IC. Todas as premissas estão **rastreáveis a fontes documentais**: cláusulas da proposta contratual, conversas técnicas registradas com o cliente Vinícius Alberoni (14–18/05/2026), Relatório Técnico Stage 2 fornecido pelo cliente, Memorial Descritivo de Geometria v3.0 e revisão de literatura científica (D'Bastiani et al., 2023 — *Water Research* v.242).

O caso base é uma simulação **trifásica (líquido + gás + sólidos granulares)** em geometria 3D completa do reator de 50 m³, com vazão de alimentação de 50 m³/d, recirculação líquida de 7×, recirculação gasosa de 40% do biogás de topo, em regime permanente seguido de transiente, abordagem Euleriana-Euleriana com modelo granular cinético (KTGF) e turbulência k-ε realizable.

O escopo entregue inclui: caracterização hidrodinâmica global, análise de zonas mortas e curto-circuito hidráulico, eficiência de captura de gás pelos separadores trifásicos, distribuição multifásica, e relatório técnico final. **O cálculo do KPI kg H₂/kg DQO solicitado pelo cliente será atendido via pós-processamento** dos campos CFD entregues, alimentando a planilha Excel do cliente que já possui modelo cinético calibrado por experiência de campo.

---

## 2. Objetivo do Estudo CFD

Conforme proposta contratual de 29/04/2026:

> *Realizar simulações CFD/DEM multifásicas de um reator anaeróbio de alta carga, como apoio técnico à definição do projeto-piloto. O estudo visa caracterizar o comportamento hidrodinâmico global do reator, identificar zonas mortas e regiões de baixa circulação, avaliar a eficiência da separação trifásica com foco em retenção de biomassa e direcionamento de fluxo gasoso.*

### 2.1 Objetivos específicos
1. Caracterizar o **perfil hidrodinâmico** (velocidades, swirl, recirculação interna IC).
2. Quantificar **eficiência relativa de captura de biogás** em cada nível de separador trifásico.
3. Identificar **zonas mortas**, curto-circuito hidráulico e regiões de baixa circulação.
4. Avaliar **distribuição espacial das fases** (líquida, gasosa e granular).
5. Estimar a **perda de carga** total e por região.
6. Fornecer subsídios para **recomendação técnica de projeto-piloto**.
7. Suportar **estimativa de produção de H₂ e CH₄** via pós-processamento (planilha do cliente).

---

## 3. Premissas Gerais do Reator

| # | Premissa | Valor | Fonte | Justificativa |
|---|---|---|---|---|
| P-001 | Volume útil | 50 m³ | Proposta contratual; Stage 1 | Especificação contratual |
| P-002 | Relação H/D | 7 | Stage 1; confirmado Vinícius 15/05 15:39 | Padrão de IC reactors |
| P-003 | Diâmetro interno | 2,090 m | Calculado D = ∛(4V/7π) | Derivado de P-001/P-002 |
| P-004 | Altura útil total | 14,600 m | Calculado H = 7×D | Derivado |
| P-005 | Temperatura de operação | 35 °C | Stage 1 e Stage 2 §2 | Condição mesofílica |
| P-006 | Pressão operacional absoluta | 1,5 kgf/cm² (147,1 kPa) | Stage 1 | Especificação cliente |
| P-007 | Substrato | Vinhaça de cana-de-açúcar | Stage 1 | Aplicação alvo |
| P-008 | DQO afluente (base) | 25.000 mg/L | Stage 2 §2 (faixa 20.000–30.000) | Valor médio da faixa |
| P-009 | Vazão afluente (Q_af) | 50 m³/d | Stage 1 | Operação contínua |
| P-010 | Fator de recirculação líquida | 7 × Q_af = 350 m³/d | Stage 1; Vinícius 15/05 | Arquitetura IC |
| P-011 | Fração de recirculação gasosa | 40% do biogás de topo | Vinícius — áudio 15/05 17:12 | Estratégia de mistura |
| P-012 | Material das paredes | Aço inox (parede infinitamente fina no CFD) | Padrão industrial | Simplificação aceitável |
| P-013 | Rugosidade interna | 0 (aço liso) | Padrão CFD | Simplificação conservadora |

---

## 4. Premissas Geométricas

Geometria baseada no Memorial Descritivo v3.0 e implementada via script Python (CadQuery) `FIORA_IC_geometry_v5_11.py`, gerando 6 arquivos STEP.

### 4.1 Corpo principal
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-001 | Forma do corpo | Cilindro vertical circular | Stage 1 |
| P-G-002 | Topo | Calota toroesférica **CONVEXA** (domo) | Vinícius 16/05 18:04 |
| P-G-003 | Altura do domo | D/8 = 0,261 m | Padrão ASME; Vinícius 16/05 |
| P-G-004 | Raio esférico equivalente do domo | 2,221 m | Derivado: R = (R²+h²)/(2h) |
| P-G-005 | Raio do joelho (toroesférico) | 0,10×D = 0,209 m | ASME padrão; aplicado como fillet |

### 4.2 Saídas (outlets)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-006 | Saída de biogás (topo) | DN100, central, no ápice do domo (z=14,60 m) | Vinícius 16/05 18:04 |
| P-G-007 | Saída lateral de efluente | DN100, z=14,30 m, az=180° | Vinícius 17/05 — "bem no topo" |
| P-G-008 | Saídas DN50 dos separadores | **3 furos** (níveis 20/40/60%), todos a az=0° | Vinícius 17/05 |
| P-G-009 | Saída do separador 95% | **Interna direta** para câmara de gás do domo (sem furo lateral) | Vinícius 17/05 |

### 4.3 Bocais de alimentação tangencial
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-010 | Número de bocais | 6 | Stage 1; Croqui 2 |
| P-G-011 | Espaçamento angular | 60° (azimutes 0/60/120/180/240/300°) | Croqui 2 |
| P-G-012 | Diâmetro nominal | DN80 (80 mm) | Vinícius 16/05 18:04 |
| P-G-013 | Comprimento do stub | 0,30 m | Estimativa CFD |
| P-G-014 | Inclinação vertical | 7,0° ascendente | Vinícius 16/05 18:04 (valor exato) |
| P-G-015 | Ângulo horizontal com a radial (caso base) | 80° | Vinícius 16/05 18:04 |
| P-G-016 | Sentido de rotação tangencial | Anti-horário (visto de cima) | Vinícius 16/05 18:04 |
| P-G-017 | Cota do centro dos bocais | 0,250 m do fundo | Stage 1 |

### 4.4 Separadores trifásicos internos
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-018 | Quantidade de níveis | 4 (a 20%, 40%, 60% e 95% da altura) | Stage 1 |
| P-G-019 | Quantidade de conjuntos Λ por nível | 2 / 4 / 4 / 4 (totalizando 14 Λ = 28 meias-placas) | Vinícius — croqui 17/05 |
| P-G-020 | Ângulo de inclinação por nível | 47,5° / 52,5° / 57,5° / 57,5° | Stage 1 |
| P-G-021 | Cota nominal = borda inferior das placas | 2,920 / 5,840 / 8,760 / 13,870 m | Convenção CAD v5.10 (resolve conflito eletrodos) |
| P-G-022 | Espessura das placas | 8 mm | Padrão construtivo |
| P-G-023 | Disposição | Λs paralelos ao longo de X, com gap de passagem do DN100 central | CAD v5.11 |
| P-G-024 | Saída individual de cada Λ | DN25 (não modelado no CFD interno) | Vinícius 17/05 |
| P-G-025 | Formato | Λ (pico para cima, abertura para baixo) — captura gás na câmara superior | Convenção física |

### 4.5 Sistema de tubulação — Retorno DN100 com manifold
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-026 | Tubo principal vertical | DN100, parede 4 mm, eixo no centro do reator | Vinícius 15/05 16:00 |
| P-G-027 | Cota superior do tubo principal | 14,29 m (logo abaixo da borda do domo) | Adotado |
| P-G-028 | Cota inferior do tubo principal (= manifold) | 0,15 m do fundo | Vinícius 18/05 17:06 |
| P-G-029 | Manifold de distribuição | 4 ramais horizontais DN50 | Vinícius — croqui 18/05 |
| P-G-030 | Azimutes dos ramais | 45° / 135° / 225° / 315° | Vinícius 18/05 |
| P-G-031 | Comprimento de cada ramal | 0,70 m (vai do eixo até r=0,7 m) | Vinícius 18/05 |
| P-G-032 | Descarga dos ramais | Aberta (descarga livre) | Vinícius 18/05 |
| P-G-033 | Conservação de área hidráulica | 4 × A(DN50) = A(DN100) ✓ | Princípio de continuidade |

### 4.6 Eletrodos eletroativos (módulo eletroquímico — caso base = sólido inerte)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-034 | Número de placas | 4 (2 ânodos + 2 cátodos) | Vinícius 15/05 |
| P-G-035 | Dimensões da placa | H 2,4 m × L 0,52 m × espessura 8 mm | Vinícius |
| P-G-036 | Área eletroativa total | 5,0 m² | Vinícius |
| P-G-037 | Gap face-a-face | 30 mm (centro-a-centro = 38 mm) | Vinícius 15/05 16:50 |
| P-G-038 | Posição angular | Par 1 a 0°, Par 2 a 180° | Adotado — simetria diametral |
| P-G-039 | Posição radial | 65% × R = 0,68 m do centro | Adotado |
| P-G-040 | Cota base | 0,25 m do fundo | Vinícius |
| P-G-041 | Modelagem no caso base | No-slip Wall (sólido inerte, sem eletroquímica) | Escopo do caso base |

### 4.7 Difusores de microbolhas
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-G-042 | Número de difusores | 12 | Vinícius 16/05 16:50 |
| P-G-043 | Tipo | Disco de bolha fina | Vinícius |
| P-G-044 | Diâmetro nominal | DN225–DN250 (adotado DN250 no CAD) | Vinícius |
| P-G-045 | Localização | No fundo (z=0), entre os bocais | Vinícius |
| P-G-046 | Disposição | 6 setores azimutais × 2 difusores por setor (interno r=0,35 m + externo r=0,80 m) | Vinícius |
| P-G-047 | Vazão unitária | 2–4 Nm³/h (total 24–48 Nm³/h) | Vinícius |
| P-G-048 | Diâmetro de bolha gerada | 1–3 mm operacional (adotado d₃₂ = 2 mm no CFD) | Vinícius / Notas L1 |
| P-G-049 | Pressão do blower | ~2,0 kgf/cm² | Vinícius |

### 4.8 Verificações de folga (rastreabilidade)
Todas as folgas críticas foram verificadas automaticamente por função `_check_clearances()` no script CAD v5.11:

| Par de componentes | Folga | Status |
|---|---|---|
| Topo eletrodos × base inferior Sep. 20% | 270 mm | ✅ |
| Pico Sep. 95% × saída efluente lateral | 210 mm | ✅ |
| Manifold (4 ramais) × topo dos bocais | 57 mm (vertical) | ✅ |
| Ramais az=45° × Eletrodo az=0° | 297 mm (radial XY) | ✅ |
| DN100 retorno × Λs centrais (vale) | 102 mm | ✅ (passa pelo vale) |
| Difusores externos × parede | 245 mm | ✅ |
| Difusores internos × DN100 central | 300 mm | ✅ |

---

## 5. Premissas Operacionais (Condições de Contorno)

### 5.1 Vazões
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-O-001 | Vazão de alimentação total inferior | 400 m³/d (50 alimentação + 350 recirculação) | Derivado de P-009/P-010 |
| P-O-002 | Vazão por bocal | 400 ÷ 6 = 66,7 m³/d = 7,71×10⁻⁴ m³/s | Calculado |
| P-O-003 | Velocidade média no bocal DN80 | 0,154 m/s | A_DN80 = π×(0,04)² |
| P-O-004 | Reynolds no bocal | ~17.000 (turbulento) | ρ·V·D/μ |
| P-O-005 | Vazão de recirculação líquida (Velocity Inlet DN100 topo) | 350 m³/d, direção −Z | Vinícius |
| P-O-006 | Vazão volumétrica total de biogás recirculado | 24–48 Nm³/h (faixa Vinícius) | P-G-047 × 12 |
| P-O-007 | Vazão por difusor | (40% × Q_biogás_total) ÷ 12 | A definir após estimativa Q_biogás |

### 5.2 Composição do biogás recirculado
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-O-008 | Fração molar CH₄ | 65% | Vinícius 16/05 18:04 |
| P-O-009 | Fração molar CO₂ | 34% | Vinícius |
| P-O-010 | Fração molar H₂S | 1% | Vinícius |
| P-O-011 | Fração de H₂ | Traço (≈0%) | Vinícius |
| P-O-012 | Massa molar média (M_mix) | 25,7 g/mol | Calculado |
| P-O-013 | Densidade na P/T operacional | ~1,48 kg/Nm³ | ρ = P·M/(R·T), gás ideal |

### 5.3 Boundary Conditions consolidadas
| # | Superfície | Tipo BC | Valor / Especificação | Fase |
|---|---|---|---|---|
| BC-01 | 6× faces externas dos bocais | Velocity Inlet | 7,71×10⁻⁴ m³/s/bocal, T=35 °C, anti-horário | Líquido |
| BC-02 | Face topo do DN100 (retorno) | Velocity Inlet | 350 m³/d, direção −Z, T=35 °C | Líquido |
| BC-03 | 12× faces dos difusores (no fundo) | Mass Flow Inlet | ṁ = (40%×Q_biogás)/12, T=35 °C, d_bolha=2 mm | Gás (composição P-O-008..011) |
| BC-04 | Furo central topo (DN100) | Pressure Outlet | P_rel = 0 (referência) | Multifásico |
| BC-05 | Furo lateral z=14,30 m (DN100) | Pressure Outlet | P_rel = 0 | Líquido |
| BC-06 | 3× furos DN50 nas paredes | Pressure Outlet | P_rel = 0 | Multifásico |
| BC-07 | Parede cilíndrica + domo + fundo | No-slip Wall | Rugosidade = 0 | — |
| BC-08 | 28 meias-placas dos separadores | Baffle No-slip | Ambos os lados | — |
| BC-09 | Parede anelar DN100 + 4 ramais | Baffle No-slip | Tubo principal + ramais como sólido único | — |
| BC-10 | 4 placas dos eletrodos | No-slip Wall | Sólido inerte | — |

---

## 6. Premissas de Modelagem Físico-Química

### 6.1 Abordagem multifásica
| # | Premissa | Valor | Fonte / Justificativa |
|---|---|---|---|
| P-F-001 | Abordagem multifásica | Euleriana-Euleriana (EMP — Eulerian Multiphase) | D'Bastiani 2023 (revisão dominante); Notas L1 |
| P-F-002 | Modelo granular (fase sólida) | KTGF (Kinetic Theory of Granular Flow) | Wang 2010; D'Bastiani 2021 — não usa DEM |
| P-F-003 | Justificativa do não-uso de DEM | DEM para grânulos de 1–3 mm em reator de 50 m³ implica bilhões de partículas — inviável computacionalmente | D'Bastiani 2023 (revisão): nenhum dos 24 papers usa DEM para granular |

### 6.2 Fase líquida (fase contínua primária)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-F-004 | Fluido de referência | Vinhaça (≈ água a 35 °C) | Aproximação CFD aceitável |
| P-F-005 | Densidade ρ_L | 995 kg/m³ | Água a 35 °C; vinhaça típica 995–1010 |
| P-F-006 | Viscosidade dinâmica μ_L | 7,2×10⁻⁴ Pa·s | Água a 35 °C |
| P-F-007 | Fração volumétrica inicial α_L | 0,92 | 1 − α_G − α_S |

### 6.3 Fase gasosa (biogás)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-F-008 | Composição (caso base) | CH₄ 65% / CO₂ 34% / H₂S 1% / H₂ traço | Vinícius |
| P-F-009 | Densidade ρ_G na operação | ~2,5 kg/m³ (corrigir após validação) | P/RT × M_mix |
| P-F-010 | Viscosidade dinâmica μ_G | 1,2×10⁻⁵ Pa·s | Estimativa CH₄/CO₂ |
| P-F-011 | Diâmetro médio de bolha (d₃₂) | 2 mm | Vinícius (1–3 mm) / Notas L1 |
| P-F-012 | Fração volumétrica inicial α_G | 0,05 (5%) | Estimativa exploratória |

### 6.4 Fases sólidas dispersas (não geometria CAD)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-F-013 | Lodo granular — diâmetro | 2,0 mm | D'Bastiani 2021 (faixa 1–3 mm) |
| P-F-014 | Lodo granular — densidade aparente | 1.460 kg/m³ (limite superior; sensibilidade 1.050) | Wang 2009/2010 |
| P-F-015 | Lodo granular — α_inicial no leito inferior | 0,35 (zona z < 8,76 m) | Wang 2010 |
| P-F-016 | Lodo granular — packing limit | 0,63 | Padrão esferas |
| P-F-017 | Lodo granular — coef. restituição | 0,90 | Típico biológico |
| P-F-018 | Biochar — diâmetro | 3,0 mm | Vinícius 15/05 |
| P-F-019 | Biochar — densidade aparente | 500 kg/m³ | Vinícius |
| P-F-020 | Biochar — dosagem | 5,0 g/L (α≈1,0%) | Vinícius |
| P-F-021 | Biochar — porosidade interna | 65% | Vinícius |
| P-F-022 | Biochar — esfericidade | 0,65 | Vinícius |

### 6.5 Modelo de turbulência
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-F-023 | Modelo de turbulência | **k-ε realizable** | Cisneros 2021; Wu 2011; D'Bastiani 2023 — dominante na literatura |
| P-F-024 | Intensidade turbulenta no inlet | I = 0,16 × Re^(−1/8) ≈ 5,5% | Correlação padrão |
| P-F-025 | Wall treatment | Wall Function | y⁺ alvo: 30–300 |
| P-F-026 | Justificativa (não k-ω SST) | Cisneros 2021 — k-ε realizable teve melhor concordância com PIV em geometrias cilíndricas | Notas L1 |

---

## 7. Premissas Cinéticas (Pós-Processamento)

**Importante:** o caso base CFD entrega **campos hidrodinâmicos**. O KPI **kg H₂/kg DQO** será calculado em **pós-processamento**, alimentando a planilha Excel calibrada do cliente.

### 7.1 Regiões funcionais (Stage 2 §8)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-C-001 | Zona A (hidrogênica) | z = 0 → 8,76 m (0–60% da altura) | Stage 2 §8 |
| P-C-002 | Zona B (metanogênica) | z = 8,76 → 13,87 m (60–95%) | Stage 2 §8 |
| P-C-003 | Zona de separação final | z = 13,87 → 14,60 m | Adotado |

### 7.2 Constantes cinéticas (Stage 2 §10, §13)
| # | Premissa | Valor | Fonte |
|---|---|---|---|
| P-C-004 | k_app,A (Região A) | 0,30 h⁻¹ (faixa 0,20–0,50) | Stage 2 §10 |
| P-C-005 | k_app,B (Região B) | 0,08 h⁻¹ (faixa 0,05–0,15) | Stage 2 §13 |
| P-C-006 | Rendimento prático CH₄ | 0,30 Nm³ CH₄/kg DQO removida (faixa 0,25–0,32) | Stage 2 §13 |
| P-C-007 | Fator estequiométrico H₂ (f_H₂) | EXPLORATÓRIO (sensibilidade 0,02–0,05) | Stage 2 §11 |
| P-C-008 | pH Região A | 5,2–5,5 | Stage 2 §9.1 |
| P-C-009 | pH Região B | 6,8–7,3 | Stage 2 §9.2 |

### 7.3 Field Functions de zoneamento (STAR-CCM+)
- `Zone_A` = `($$Position[2] < +1,46) && ($$Position[2] > −7,30) ? 1 : 0`
- `Zone_B` = `($$Position[2] >= +1,46) && ($$Position[2] < +6,57) ? 1 : 0`

### 7.4 Reports de pós-processamento entregues
1. Volume útil real por zona (descontando zonas mortas)
2. Distribuição vertical de fases (lodo, gás, líquido)
3. Vazão de gás coletada em cada DN50
4. Tempo médio de residência por zona (DTR via passive scalar)
5. Cisalhamento médio sobre o leito (relevante para retenção granular)
6. Volume de zonas mortas (`|V| < 1 mm/s`)
7. KPI consolidado: vazões mássicas em todos os inlets/outlets para balanço

---

## 8. Premissas de Discretização Numérica

### 8.1 Malha
| # | Premissa | Valor | Justificativa |
|---|---|---|---|
| P-N-001 | Mesher | Polyhedral + Prism Layer + Surface Remesher | Padrão STAR-CCM+ multifásico |
| P-N-002 | Base size | ~50 mm (≈ D/40) | Compromisso resolução vs custo |
| P-N-003 | Camadas de prismas | 5–8 camadas, total ~10 mm | Resolução de camada limite |
| P-N-004 | Growth ratio (prismas) | 1,3 | Padrão |
| P-N-005 | y⁺ alvo | 30 (faixa 30–300) | Wall Function de k-ε |
| P-N-006 | Refinamento local — bocais | 10 mm | Resolver jato turbulento |
| P-N-007 | Refinamento local — eletrodos | 15 mm | Gap 30 mm preservado |
| P-N-008 | Refinamento local — difusores | 15 mm | Faces de 250 mm |
| P-N-009 | Refinamento local — separadores | 20 mm | Bordas finas (8 mm) |
| P-N-010 | Estimativa total de células | 2–5 milhões | Literatura: D'Bastiani 2021 cita ~2,3M para IC reactor |
| P-N-011 | Independência de malha | GCI (Grid Convergence Index) | D'Bastiani 2021 — método padrão |

### 8.2 Solver e regime
| # | Premissa | Valor | Justificativa |
|---|---|---|---|
| P-N-012 | Regime inicial | Steady-state | Convergência inicial |
| P-N-013 | Regime principal | Transiente após steady | Notas L1 — captura dinâmica multifásica |
| P-N-014 | Time step (transiente) | 0,01–0,05 s | Pan et al. 2017: Δt=0,02 s |
| P-N-015 | Tempo simulado mínimo | ≥ 1×TRH = 24 h (longo prazo: 5×TRH) | Convergência das fases |
| P-N-016 | Critério de convergência | Resíduos < 10⁻⁴ (continuidade/momento) | Padrão CFD multifásico |
| P-N-017 | Monitoramento de convergência | V_up médio Δ<1% em 100 iter; α_G Δ<2% | Estabilidade estatística |

---

## 9. Cenários de Simulação

Conforme matriz consolidada (Planilha de Setup v4.0, Aba 11):

| ID | Caso | Variação | Origem |
|---|---|---|---|
| **C0** | **Caso base** | Geometria v5.11, 80°, 7°, sem módulo externo | Vinícius |
| C0_M30 | Base + M30 | Φ=1,10 sobre k_app,A | Stage 2 §14 |
| C0_M60 | Base + M60 | Φ=1,18 sobre k_app,A | Stage 2 §14 |
| C1 | Sensibilidade bocal | NOZZLE_TANG_ANGLE = 75° | Vinícius |
| C2 | Sensibilidade bocal | NOZZLE_TANG_ANGLE = 70° | Vinícius |
| C3 | Sensibilidade bocal | NOZZLE_TANG_ANGLE = 85° | Vinícius |
| C0_DQO_min | Sensibilidade carga | DQO = 20.000 mg/L | Stage 2 §2 |
| C0_DQO_max | Sensibilidade carga | DQO = 30.000 mg/L | Stage 2 §2 |
| C0_kapp_min | Sensibilidade cinética (só pós) | k_app,A = 0,20 h⁻¹ | Stage 2 §10 |
| C0_kapp_max | Sensibilidade cinética (só pós) | k_app,A = 0,50 h⁻¹ | Stage 2 §10 |

**Total:** 4 casos com mudança geométrica (re-gerar CAD), 4 com mudança apenas de setup, 2 só em pós-processamento.

---

## 10. Limitações e Hipóteses Adotadas

### 10.1 Simplificações geométricas
- LIM-01: Espessura de parede do reator não modelada (parede infinitamente fina).
- LIM-02: Tubo único de alimentação que se ramifica em 6 bocais (Vinícius 18/05) modelado como 6 bocais individuais atravessando a parede — simplificação CFD aceitável.
- LIM-03: Tubos DN25 individuais de cada conjunto Λ não modelados (gás coletado sobe naturalmente).
- LIM-04: Difusores reais (placas porosas) modelados apenas como faces de Mass Flow Inlet (sem geometria de microfuros).

### 10.2 Simplificações físico-químicas
- LIM-05: Biochar e lodo granular **não possuem geometria CAD** — modelados como fases sólidas dispersas em E-E + KTGF.
- LIM-06: Diâmetro de bolha tratado como d₃₂ único (2 mm); modelo de PBM não implementado no caso base.
- LIM-07: Reator considerado **isotérmico** a 35 °C (consistente com toda a literatura revisada — D'Bastiani 2023).
- LIM-08: **Sem acoplamento direto CFD–biocinética** no caso base. Cinética aplicada em pós-processamento.
- LIM-09: Eletrodos modelados como **sólidos inertes** (sem eletroquímica, sem campo magnético) — próxima etapa do projeto.

### 10.3 Premissas sobre composição
- LIM-10: Composição do biogás recirculado considerada **constante** (CH₄ 65 / CO₂ 34 / H₂S 1) ao longo da simulação.
- LIM-11: Densidade do biogás calculada por **gás ideal** na P/T operacional.

### 10.4 Validação
- LIM-12: **Sem reator físico construído ainda** — validação será **indireta**, comparando padrões de escoamento e DTR contra dados PIV da literatura (D'Bastiani 2021) em geometrias similares.
- LIM-13: KPIs de produção (H₂, CH₄) tratados como **variáveis de resposta exploratórias**, não como valores garantidos (alinhado a Stage 2 §17–§18).

---

## 11. Riscos Técnicos e Mitigação

| ID | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | Custo computacional do transiente trifásico exceder cronograma | Média | Alto | Iniciar steady-state; transiente apenas após convergência |
| R-02 | Falta de validação experimental (sem piloto físico) | Alta | Médio | Validação indireta via PIV de literatura; explicitar em Stage 2 §18 |
| R-03 | Cliente solicitar acoplamento CFD-cinética dentro do escopo | Média | Alto | Mitigação contratual: KPI H₂/DQO entregue via planilha do cliente (pós-proc.); aditivo se necessário |
| R-04 | Imprecisão das constantes k_app | Alta | Médio | Cenários de sensibilidade C0_kapp_min/max |
| R-05 | Conflitos geométricos não detectados | Baixa | Alto | Mitigado por `_check_clearances()` automatizado no CAD v5.10+ |
| R-06 | Geometry Check do STAR-CCM+ falhar | Baixa | Médio | Tolerâncias revisadas; fillet do joelho em try/except |
| R-07 | Composição do biogás real diferir significativamente | Baixa | Baixo | Sensibilidade já planejada (Stage 2 §7) |

---

## 12. Rastreabilidade de Fontes

### 12.1 Documentos do cliente
| Doc | Conteúdo | Status |
|---|---|---|
| Stage 1 | Premissas iniciais (D, H, V, separadores, eletrodos) | Aplicado |
| Stage 2 (16309384-Relatorio_Tecnico_CFD_Stage_2) | DQO, vazões, cinética, cenários C0/M30/M60 | Aplicado |
| Notas L1 (75e2fc2b-Notas_L1_Vinicius) | Revisão D'Bastiani 2023 — decisões de setup CFD | Aplicado |
| Memorial Vinícius v1.0 | Especificações geométricas iniciais | Substituído por v3.0 |

### 12.2 Conversas técnicas com Vinícius (14–18/05/2026)
| Data/Hora | Conteúdo | Decisões aplicadas |
|---|---|---|
| 15/05 15:38 | Áudio — geometria geral, topo, IC | Topo, bocais |
| 15/05 16:09 | Mensagem — calota toroesférica | Topo (interpretação revisada) |
| 15/05 16:46 | D/8 = 0,261 m | TOP_DEPTH |
| 15/05 16:50 | Eletrodos gap 30 mm; 12 difusores DN225/250 | P-G-037; P-G-042..049 |
| 15/05 17:05 | Áudio — sistema completo de tubulação IC | P-G-026 |
| 15/05 17:12 | Áudio — 40% recirculação gasosa | P-011 |
| 16/05 18:04 | Mensagem extensa — topo convexo, saídas DN100, bocais 7°/80°, composição gás | P-G-002 a P-G-009; P-G-014..016; P-O-008..011 |
| 17/05 (áudio) | Saída de efluente bem no topo; DN50 só 3; Λ 2/4/4/4; DN100 a 15 cm | P-G-007; P-G-008; P-G-019 |
| 18/05 (áudio + croqui) | Manifold de 4 ramais | P-G-029..033 |
| 18/05 17:06 | Confirmação final 5 itens manifold | P-G-028 a P-G-032 |

### 12.3 Documentos técnicos gerados (entregáveis intermediários)
| Doc | Versão | Conteúdo |
|---|---|---|
| `FIORA_IC_geometry_v5_11.py` | v5.11 (final) | Script CadQuery — geometria CAD |
| `FIORA_IC_v5_11_*.step` | 6 arquivos | Geometria STEP para STAR-CCM+ |
| `FIORA_IC_Memorial_Geometria_v3.docx` | v3.0 | Memorial Descritivo de Geometria |
| `FIORA_IC_Setup_CFD_v4.xlsx` | v4.0 | Planilha de Setup CFD (13 abas) |
| **`FIORA_IC_Relatorio_Premissas.docx`** | **Rev. A** | **Este documento** |

### 12.4 Referências científicas
| Ref | Citação |
|---|---|
| L1 | D'Bastiani, C.; Kennedy, D.; Reynolds, A. (2023). *CFD simulation of anaerobic granular sludge reactors: A review.* Water Research, v.242, 120220. DOI: 10.1016/j.watres.2023.120220 |
| L2 | Wang, Y. et al. (2010). EGSB reactor CFD — biohidrogênio acoplado |
| L3 | D'Bastiani, C. et al. (2021). UASB três fases — validação PIV |
| L4 | Wu, B. (2015). Shear rate em reatores granulares — papel do biogás |
| L5 | Cisneros et al. (2021). Comparação k-ε realizable vs k-ω SST |
| L6 | Pan et al. (2017). EGSB — ângulo de separador trifásico |

---

## 13. Aprovação e Controle de Revisões

| Rev | Data | Autor | Aprovador | Mudanças |
|---|---|---|---|---|
| **A** | 18/05/2026 | Gabriel Rozo | (aguardando Marcus) | Emissão inicial |

| Função | Nome | Assinatura | Data |
|---|---|---|---|
| Engenheiro CFD | Gabriel Rozo | _______________ | _____/_____/_____ |
| Gerente de Projeto | Marcus | _______________ | _____/_____/_____ |
| Diretor Técnico | Ricardo Barbosa de Barros | _______________ | _____/_____/_____ |
| Aprovação Cliente | Vinícius Alberoni | _______________ | _____/_____/_____ |

---

## 14. Anexos (Documentos de Referência)

- **Anexo A:** Memorial Descritivo de Geometria v3.0 — `FIORA_IC_Memorial_Geometria_v3.docx`
- **Anexo B:** Planilha de Setup CFD v4.0 — `FIORA_IC_Setup_CFD_v4.xlsx` (13 abas)
- **Anexo C:** Script CAD CadQuery — `FIORA_IC_geometry_v5_11.py`
- **Anexo D:** Arquivos STEP (6×) — `FIORA_IC_v5_11_*.step`
- **Anexo E:** Relatório Stage 2 — fornecido pelo cliente
- **Anexo F:** Notas de Revisão de Literatura L1 (D'Bastiani 2023)

---

**FIORA IC — Relatório de Premissas Técnicas Rev. A — 18/05/2026**

*CONFIDENCIAL — Tecnologia Patenteada. Reprodução proibida sem autorização expressa.*
