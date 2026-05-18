# FIORA IC

## Memorial Descritivo de Geometria — v3.0

**Biorreator Anaeróbio de Alta Carga — Projeto Piloto 50 m³**

Versão **3.0** | Data: 18/Mai/2026 | **CONFIDENCIAL — Tecnologia Patenteada**

| | |
|---|---|
| **Documento** | Memorial Descritivo de Geometria — FIORA IC |
| **Projeto** | Estudo CFD — Reator Anaeróbio de Alta Carga — Piloto |
| **Cliente** | Gerir Gestão e Instrução — Vinícius Alberoni |
| **Executor CFD** | CAEXPERTS — Ricardo Barbosa de Barros |
| **Referência** | Proposta R1 \| Stage 1 \| Stage 2 \| Conversas técnicas 14–18/Mai/2026 |
| **Versão** | 3.0 — Geometria Final Validada com Manifold de Distribuição |
| **Script CAD** | `FIORA_IC_geometry_v5_11.py` (CadQuery → 6 arquivos STEP) |

**PROPÓSITO:** Este documento consolida, em formato técnico formal, todas as informações de geometria do reator FIORA IC obtidas a partir dos croquis do inventor, dos áudios, mensagens de alinhamento técnico (14–18/Mai/2026), do Relatório Stage 2 e das revisões iterativas v5.6 → v5.11 do CAD. Substitui a v2.0. Destina-se à CAEXPERTS como fonte única de referência para construção do modelo CAD e setup da simulação CFD.

---

## 📋 CHANGELOG v3.0 (sobre v2.0)

| Item | v2.0 | v3.0 | Origem |
|---|---|---|---|
| **Separadores: quantidade de Λ por nível** | 1 conjunto Λ por nível (8 placas total) | **2/4/4/4 conjuntos Λ** (28 placas total) | Vinícius — croqui + áudio 17/05 |
| **Saídas DN50** | 4 furos (níveis 20/40/60/95%) | **3 furos (20/40/60%)** — o 95% descarrega INTERNAMENTE no domo | Vinícius — áudio 17/05 |
| **Cota nominal do separador** | Centro/pico do Λ | **Borda inferior das placas** (pico fica acima) | Fix de conflito vertical com eletrodos |
| **Cota da saída de efluente** | z=14,20 m | **z=14,30 m** (bem no topo, 3 cm abaixo do cilindro) | Vinícius — áudio 17/05 |
| **Tubo de retorno DN100** | Cilindro vertical único, base em z=1,0 m | **Tubo principal + manifold de 4 ramais DN50** em z=0,15 m | Vinícius — áudio 17/05 + croqui 18/05 |
| **Bug Λ invertido (V em vez de Λ)** | — | **Corrigido na v5.9** (sinais de tilt invertidos) | Validação visual no STAR-CCM+ |
| **Conflito Sep. 20% × Eletrodos** | Não detectado | **Corrigido na v5.10** (cota = borda inferior) | Validação visual no STAR-CCM+ |
| **Função de verificação automática de folgas** | — | **`_check_clearances()`** no início do script | Esta versão |

---

## 1. Visão Geral do Reator

Mantido idêntico à v2.0 (parâmetros de processo gerais não mudaram).

| Parâmetro Geral | Valor Confirmado | Fonte |
|---|---|---|
| Volume útil (V) | 50 m³ | Proposta R1 / Stage 1 |
| Relação H/D | 7 | Stage 1 / Vinícius |
| Diâmetro interno (D) | 2,09 m | Calculado: D = ∛(4V/7π) |
| Altura útil (H) | 14,6 m | Calculado: H = 7 × D |
| Área da seção transversal | 3,43 m² | A = π/4 × D² |
| Temperatura de operação | 35 °C | Stage 1 / Stage 2 §2 |
| Pressão de operação | 1,5 kgf/cm² (147,1 kPa) | Stage 1 |
| Substrato | Vinhaça de cana-de-açúcar | Stage 1 |
| DQO afluente (projeto) | 25.000 mg/L | Stage 1/2 |
| Vazão afluente (Q_af) | 50 m³/d | Stage 1 |
| Recirculação líquida | 7 × Q_af = 350 m³/d | Stage 1 |
| Recirculação gasosa | 40% do biogás de topo | Vinícius — áudio 15/05 17:12 |

**Arquitetura funcional (de baixo para cima):**
- **Zona de mistura inferior** (0–0,5 m): alimentação por 6 bocais + recirculação líquida por 4 ramais DN50 + recirculação gasosa por 12 difusores no fundo
- **Zona eletroativa** (0,25–2,65 m): 2 pares de eletrodos A/C
- **Zona hidrogênica** (2,92–8,76 m): 3 níveis de separadores Λ (sep. 20/40/60%) com saídas DN50 laterais
- **Zona metanogênica** (13,87 m): 1 nível de separador Λ (sep. 95%) com saída interna direta para o domo
- **Zona de separação final** (14,30 m): saída lateral DN100 de efluente
- **Câmara de biogás** (domo convexo, ápice em 14,60 m): saída central DN100 de biogás

---

## 2. Corpo Principal do Reator

### 2.1 Cilindro
Idêntico à v2.0: D=2,09 m × H=14,6 m × Aço inox liso (parede infinitamente fina no CFD).

### 2.2 Topo Convexo
Idêntico à v2.0: domo toroesférico convexo, h=D/8=0,261 m, R_sph=2,221 m, joelho R=0,209 m (fillet ASME).

### 2.3 Saída Central de Biogás
DN100 central no ápice do domo (z=14,60 m). BC = Pressure Outlet.

### 2.4 Saída Lateral de Efluente ★ ATUALIZADO v3.0 ★

| Parâmetro | Valor | Fonte |
|---|---|---|
| Diâmetro nominal | DN100 | Vinícius — 16/05 18:04 |
| **Cota (z do fundo)** | **14,30 m** ★ subiu de 14,20 m | Vinícius — áudio 17/05: "bem no topo mesmo" |
| Posição angular | 180° | Adotado — oposto às DN50 |
| Função | Controle do nível operacional | Vinícius |
| BC no CFD | Pressure Outlet | — |

---

## 3. Sistema de Entrada — Bocais Tangenciais

Mantido conforme v2.0. **Confirmações finais Vinícius:**

| Parâmetro | Valor | Fonte |
|---|---|---|
| Número de bocais | 6 | Stage 1 / Vinícius |
| Espaçamento angular | 60° | Croqui 2 |
| Azimutes | 0°, 60°, 120°, 180°, 240°, 300° | Croqui 2 |
| Altura do centro | 0,25 m do fundo | Stage 1 |
| Inclinação vertical | 7,0° ascendente | Vinícius 16/05 18:04 |
| Ângulo horizontal (com radial) | 80° (caso base C0) | Vinícius 16/05 18:04 |
| Sentido de rotação | Anti-horário visto de cima | Vinícius 16/05 18:04 |
| Diâmetro nominal | DN80 (80 mm) | Vinícius — confirmado |
| Comprimento do stub | 0,30 m | Estimativa CFD |
| Vazão por bocal | 66,7 m³/d = 7,7×10⁻⁴ m³/s | Calculado |
| Cenários de sensibilidade | 70° / 75° / 85° + caso base 80° | Vinícius |

**Alimentação real:** chega ao reator por **1 tubo único paralelo ao fundo** que se ramifica internamente em 6 bocais (Vinícius 18/05). No CFD os 6 bocais são modelados individualmente atravessando a parede (simplificação aceitável — face externa = Velocity Inlet).

---

## 4. Separadores Trifásicos Internos ★ TOTALMENTE REESCRITO v3.0 ★

### 4.1 Quantidade e disposição (Vinícius — croqui + msg 17/05)

| Nível | % Altura | Cota nominal* | Quantidade de Λ | Total de meias-placas |
|---|---|---|---|---|
| Sep. 1 (inferior) | 20% | 2,92 m | **2 Λ** | 4 |
| Sep. 2 (intermediário) | 40% | 5,84 m | **4 Λ** | 8 |
| Sep. 3 (superior) | 60% | 8,76 m | **4 Λ** | 8 |
| Sep. 4 (topo) | 95% | 13,87 m | **4 Λ** | 8 |
| **TOTAL** | — | — | **14 Λ** | **28 placas** |

\* **Cota nominal = borda inferior das placas externas** (cota mais baixa do conjunto). O pico do Λ fica acima dessa cota, em `z_base + W/2 × sin(tilt)`. **Esta interpretação foi consolidada na v3.0** após detecção de conflito com os eletrodos na v2.0.

### 4.2 Disposição geométrica

Os Λs de cada nível são **paralelos entre si**, com eixo dos picos alinhado ao longo do eixo Y. Distribuídos uniformemente ao longo do eixo X, ocupando toda a seção transversal do reator. Cada Λ tem largura horizontal W_Λ = D / N (onde N é o número de Λs do nível).

| Nível | W_Λ | Queda vertical (W/2 × sin(tilt)) | Pico em z (frame absoluto) |
|---|---|---|---|
| Sep. 1 (20%, 2 Λ, tilt 47,5°) | 1,045 m | 0,385 m | **3,305 m** |
| Sep. 2 (40%, 4 Λ, tilt 52,5°) | 0,523 m | 0,207 m | 6,047 m |
| Sep. 3 (60%, 4 Λ, tilt 57,5°) | 0,523 m | 0,220 m | 8,980 m |
| Sep. 4 (95%, 4 Λ, tilt 57,5°) | 0,523 m | 0,220 m | 14,090 m |

### 4.3 Parâmetros construtivos

| Parâmetro Construtivo | Especificação |
|---|---|
| Espessura das placas | 8 mm |
| Geometria | Meia-placa esquerda + direita → perfil Λ (pico para cima, abertura para baixo) |
| Borda externa | Clipada ao contorno cilíndrico do reator (intersecção booleana) |
| Saída de cada conjunto Λ | Tubo DN25 individual conectado ao DN50 coletor por nível (não modelado no CFD interno) |
| **Saída do nível 20/40/60%** | 1× DN50 lateral por nível (3 furos totais na parede) |
| **Saída do nível 95%** | **Direta INTERNA para câmara de gás do domo** (sem furo lateral) |
| BC no CFD | Baffle No-slip (ambos os lados) |

### 4.4 Formato Λ — verificação

★ Importante: as placas formam **Λ com pico para cima** (e não V com abertura para cima). Validado visualmente no STAR-CCM+ após correção de sinais de rotação na v5.9. A câmara superior interna do Λ captura o gás ascendente — função correta do separador trifásico.

---

## 5. Sistema de Tubulação ★ TOTALMENTE REESCRITO v3.0 ★

### 5.1 Tubo de Retorno DN100 com Manifold de 4 Ramais DN50

A v3.0 introduz uma mudança importante: o tubo de retorno **não descarrega mais em um único ponto** no fundo, mas se ramifica em **4 ramais DN50 horizontais** logo acima do fundo, distribuindo o líquido recirculado em 4 pontos.

| Parâmetro | Valor | Fonte |
|---|---|---|
| **Tubo principal vertical** | DN100, parede 4 mm | Vinícius |
| Cota inferior do tubo principal | **0,15 m** do fundo ★ Vinícius 18/05 17:06 | Áudio "Até 15 cm do fundo" |
| Cota superior do tubo principal | 14,29 m (logo abaixo da borda do domo) | Adotado |
| **Manifold (junção dos 4 ramais)** | em z=0,15 m | Vinícius — croqui 18/05 |
| **Ramais (4×)** | DN50, parede 4 mm | Vinícius — confirmado 18/05 17:06 |
| Comprimento de cada ramal | 0,70 m (vai do eixo a r=0,7 m) | Vinícius — confirmado |
| Azimutes dos ramais | 45°, 135°, 225°, 315° | Vinícius — confirmado |
| Final dos ramais | Descarga livre (sem coletor terminal) | Vinícius — confirmado |
| BC no CFD | Baffle No-slip (tubo principal + ramais como sólido único) | — |
| Velocity Inlet | Apenas no topo do tubo principal | Q=350 m³/d, direção −Z |

**Conservação de área hidráulica:** 4 × A(DN50) = π × (0,025)² × 4 = 7,85 ×10⁻³ m² ≈ A(DN100) = π × (0,05)² = 7,85 ×10⁻³ m². ✓

**Justificativa do manifold (Vinícius 18/05):** distribuir o líquido recirculado em 4 pontos reduz o risco de zona morta no centro do fundo, promove melhor mistura com a alimentação dos bocais e com a recirculação gasosa dos difusores.

### 5.2 Saídas DN50 dos Separadores ★ ATUALIZADO v3.0 ★

| Parâmetro | Valor | Fonte |
|---|---|---|
| **Quantidade** | **3** (apenas dos níveis 20/40/60%) | Vinícius 17/05 |
| Diâmetro | DN50 (50 mm) | Vinícius |
| Posição angular | Todos a 0° | Stage 1 / Vinícius |
| Cotas | 2,92 / 5,84 / 8,76 m do fundo | Definição dos separadores |
| **Saída do separador 95%** | **NÃO existe DN50 lateral** | Vinícius 17/05: "sai direto no separador gás-líquido de metano" — INTERNA ao reator |
| BC no CFD | Pressure Outlet (P_rel = 0) | — |

---

## 6. Módulo Eletroativo — Eletrodos Ânodo/Cátodo

Idêntico à v2.0, mas com **verificação de folga formal** após detectar conflito na v5.9:

| Parâmetro | Valor | Fonte |
|---|---|---|
| Número de placas | 4 (2 ânodos + 2 cátodos) | Vinícius 15/05 |
| Dimensões | H 2,4 m × L 0,52 m × esp. 8 mm | Vinícius |
| Área eletroativa total | 5,0 m² | Vinícius |
| Gap face-a-face | 30 mm máximo (centro-a-centro = 38 mm) | Vinícius 15/05 16:50 |
| Posição angular | Par 1: 0° / Par 2: 180° | Adotado |
| Posição radial | 65% × R = 0,68 m do centro | Adotado |
| Cota base | 0,25 m do fundo | Vinícius |
| Cota topo | 2,65 m do fundo | Calculado |
| **Folga até Sep. 20% (base das placas)** | **270 mm** ✓ | ★ Verificado v3.0 (era −115 mm na v5.9 antes da correção) |

🚨 Parâmetros elétricos (próxima etapa). Caso base: sólidos inertes.

---

## 7. Fases Sólidas — Biochar e Lodo Granular

Mantido v2.0. Não modelado como geometria CAD — fases dispersas em E-E + KTGF.

---

## 8. Difusores de Microbolhas

Mantido v2.0 — 12× DN250 no fundo, 6 setores × 2 difusores, vazão 2–4 Nm³/h, bolha 1–3 mm, gás CH₄ 65% / CO₂ 34% / H₂S 1%.

---

## 9. Módulo de Bioestimulação Magnética (Próxima Etapa)

Mantido v2.0 — fora de escopo no caso base.

---

## 10. Cenários M30/M60 — Módulo Externo (Stage 2)

Mantido v2.0 — externo ao domínio CFD, entra como modificação de k_app,A via Φ.

---

## 11. Arquivos CAD — Resumo Executivo ★ ATUALIZADO v3.0 ★

Executar o script **`FIORA_IC_geometry_v5_11.py`** (CadQuery) para gerar os **6 arquivos STEP**:

| Arquivo STEP | Corpos | Conteúdo |
|---|---|---|
| `FIORA_IC_v5_11_fluid_domain.step` | 1 sólido | Cilindro + domo + DN100 biogás topo + **3 furos DN50** laterais + DN100 efluente lateral |
| `FIORA_IC_v5_11_return_tube.step` | 1 sólido | **Tubo DN100 principal + 4 ramais DN50 horizontais** (manifold a z=0,15 m) |
| `FIORA_IC_v5_11_separators.step` | 28 placas | 2/4/4/4 Λ — pico para cima |
| `FIORA_IC_v5_11_nozzles.step` | 6 sólidos | Bocais DN80 80°+7° anti-horário |
| `FIORA_IC_v5_11_electrodes.step` | 4 sólidos | 2 pares A/C, gap 30 mm |
| `FIORA_IC_v5_11_diffusers.step` | 12 sólidos | DN250 stubs para Imprint (deletar após) |

---

## 12. Operações no STAR-CCM+

### 12.1 Pipeline 3D-CAD
1. **Unite** `fluid_domain` + `nozzles` → 6 canais Velocity Inlet
2. **Imprint** `fluid_domain` + `diffusers` → 12 faces circulares no fundo
3. **Delete** corpos `diffusers` após imprint
4. NÃO unir `return_tube`, `separators`, `electrodes` (ficam como baffles/walls)

### 12.2 Boundaries (★ ATUALIZADO v3.0 ★)

| Boundary | Tipo | Quantidade | Notas |
|---|---|---|---|
| `Inlet_Nozzle_01..06` | Velocity Inlet | 6 | 66,7 m³/d cada, líquido |
| `Inlet_DN100_top` | Velocity Inlet | 1 | 350 m³/d, dir −Z, líquido |
| `Inlet_Diffuser_01..12` | Mass Flow Inlet | 12 | gás (CH₄ 65/CO₂ 34/H₂S 1) |
| `Outlet_Biogas` (centro topo) | Pressure Outlet | 1 | P_rel=0, gás |
| `Outlet_Effluent` (lateral z=14,30) | Pressure Outlet | 1 | P_rel=0, líquido |
| **`Outlet_DN50_20/40/60`** | Pressure Outlet | **3** ★ era 4 | P_rel=0, multifásico |
| `Wall_Reactor` | No-slip Wall | 1 | parede + domo + fundo |
| `Baffle_Separator` | Baffle | 28 placas | Λ ambos os lados |
| `Baffle_DN100` (principal + 4 ramais) | Baffle | 1 corpo único | ambos os lados |
| `Wall_Electrode_A1/A2/C1/C2` | No-slip Wall | 4 | sólido inerte |

### 12.3 Geometry Check
Tools > Geometry Check → **zero erros**. Pontos de atenção:
- Junção cilindro/domo (fillet do joelho)
- 12 faces criadas pelo Imprint
- Manifold de 4 ramais (junção tubo principal × ramais)

---

## 13. Verificações de Folga Críticas ★ NOVA v3.0 ★

Função `_check_clearances()` no script CAD verifica automaticamente. **Resultados:**

| Par de Componentes | Cota A | Cota B | Folga | Status |
|---|---|---|---|---|
| Topo eletrodos × Borda inf. Sep. 20% | 2,650 m | 2,920 m | **+270 mm** | ✅ |
| Topo bocais × Manifold (4 ramais) | 0,268 m | 0,150 m | −118 mm† | ⚠️ ver nota |
| Pico Sep. 95% × Saída efluente lateral | 14,090 m | 14,300 m | **+210 mm** | ✅ |
| Ramais az=45° × Eletrodo az=0° (radial XY) | — | — | **+297 mm** | ✅ |
| Ramais (r=0,7 m) × Parede (r=1,045 m) | — | — | **+345 mm** | ✅ |
| Ramais (z=0,15 m) × Difusores (z=0,025 m) | — | — | **+100 mm** | ✅ |
| DN100 principal (r=50 mm) × Λs centrais | — | — | **+102 mm** (vale entre Λs) | ✅ |

† **Nota sobre manifold × bocais:** o manifold está abaixo dos bocais (z=0,15 m vs z=0,25 m), mas em **azimutes diferentes** (ramais a 45/135/225/315°, bocais a 0/60/120/180/240/300°). A folga angular mínima é de 15°, e a distância radial entre o ponto mais próximo do ramal e o ponto mais próximo do bocal é > 300 mm. Sem conflito 3D real.

---

## 14. Histórico de Versões da Geometria CAD

| Versão | Data | Principais mudanças |
|---|---|---|
| v5.1–v5.5 | 15–16/05 | Iteração inicial: separadores, bocais, topo, difusores |
| v5.6 | 16/05 18:04 | Topo CONVEXO + saída biogás + efluente + bocais 7° |
| v5.7 | 17/05 | 2/4/4/4 Λ + 3 DN50 + DN100 até fundo |
| v5.8 | 18/05 | Manifold de 4 ramais DN50 (sugestão Vinícius) |
| v5.9 | 18/05 | Fix bug: Λ pico para cima (era V invertido) |
| v5.10 | 18/05 | Cota separador = borda inferior + verificações de folga |
| **v5.11** | **18/05 17:06** | **Manifold a 0,15 m do fundo (confirmação final Vinícius)** |

---

**FIORA IC — Memorial Descritivo de Geometria v3.0 — 18/Mai/2026 | CONFIDENCIAL — Tecnologia Patenteada**
