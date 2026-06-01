# Plano de Estudos — CFD para HAZOP e Segurança de Processos

Progressão do mais simples ao mais complexo.
Cada etapa produz um resultado validável e publicável.

---

## Contexto Industrial

O HAZOP (Hazard and Operability Study) identifica **qualitativamente** os desvios perigosos
em processos industriais. O CFD converte esses desvios em **consequências quantificadas**:
extensão da nuvem de gás, irradiância de chamas, sobrepressão de explosões.

Juntos formam a base do QRA (Quantitative Risk Assessment) — exigido por normas como
API 752, API 753, EN 1473, NLPG C2 e resolução ANP 43/2007 no Brasil.

---

## Step 1 — Dispersão de Gás: Vazamento de GLP em Área Aberta (2D/3D, RANS)

**Cenário HAZOP:** Desvio "Mais fluxo do que o pretendido" → ruptura de tubulação de GLP.
**Física dominante:** Dispersão turbulenta, empuxo (gás mais leve que o ar).

**O que se valida:**
| Grandeza | Referência |
|----------|-----------|
| Extensão da nuvem (LFL/UFL) | Dados experimentais TNO (Yellow Book) |
| Perfil de concentração | Modelo gaussiano de Pasquill-Gifford |
| Tempo de formação da nuvem explosiva | Norma EN 60079-10 |

**Setup STAR-CCM+:**
- Domínio: 50×50×20 m (área aberta)
- Fonte: orifício de vazamento (massa específica GLP: C3H8/C4H10)
- Turbulência: k-ε Realizable (dispersão atmosférica)
- Espécies: transporte de escalares passivos → concentração molar
- Saída: mapa de isossuperfícies LFL (2,1% vol) e UFL (9,5% vol)

---

## Step 2 — Jet Fire: Tocha de Vazamento Pressurizado Ignicionado

**Cenário HAZOP:** Vazamento pressurizado + fonte de ignição imediata.
**Física dominante:** Combustão turbulenta, radiação térmica (DO model).

**O que se valida:**
| Grandeza | Referência |
|----------|-----------|
| Comprimento da chama | Correlação API 521 / Chamberlain (1987) |
| Irradiância na superfície alvo | Modelo de ponto fonte vs. CFD |
| SEP (Specific Emissive Power) | Dados experimentais Scandpower |

**Setup:**
- Modelo de combustão: Eddy Dissipation (ED) ou Flamelet
- Radiação: Discrete Ordinates (DO) + WSGGM para CO₂/H₂O
- Outputs: mapa de irradiância [kW/m²], contornos 4/12,5/37,5 kW/m²
  (limites de dano para equipamentos e pessoas — API 521)

---

## Step 3 — Pool Fire: Incêndio de Poça de Líquido Inflamável

**Cenário HAZOP:** Derramamento de líquido inflamável + ignição.
**Física dominante:** Vaporização, combustão, radiação + convecção.

**O que se valida:**
| Grandeza | Referência |
|----------|-----------|
| Taxa de queima (m"_burn) | Correlação de Burgess et al. |
| Temperatura máxima da chama | Dados experimentais |
| Fluxo de calor para tanque vizinho (domino effect) | API 2030 |

---

## Step 4 — Dispersão em Área Confinada: Módulo Offshore

**Cenário HAZOP:** Vazamento em módulo fechado de plataforma offshore.
**Física dominante:** Acúmulo de gás, ventilação forçada/natural.

**O que se valida:**
- Volume explosivo (LFL–UFL) em função da ventilação
- Estratificação do gás (CH4 sobe, C3H8 afunda)
- Comparação com FLACS (software de referência da indústria offshore)

**Relevância industrial:** Base para definição de detectores de gás (posicionamento)
conforme NFPA 72 e ATEX/IECEx.

---

## Step 5 — VCE: Explosão de Nuvem de Vapor (Sobrepressão)

**Cenário HAZOP:** Nuvem de gás inflamável + ignição retardada.
**Física dominante:** Deflagração, propagação de chama, onda de pressão.

**O que se valida:**
| Grandeza | Referência |
|----------|-----------|
| Sobrepressão de pico | Método BST (Baker-Strehlow-Tang) |
| Impulso | TNT equivalente |
| Distância segura | Curvas de dano API 752/753 |

**Software de comparação:** FLACS (Gexcon) — padrão da indústria para VCE.

---

## Tabela-Resumo da Progressão

| Step | Cenário HAZOP | Física | Complexidade |
|------|--------------|--------|-------------|
| 1 | Ruptura de tubulação — nuvem GLP | Dispersão turbulenta | Baixa |
| 2 | Vazamento pressurizado ignicionado | Jet fire + radiação | Baixa–Média |
| 3 | Derramamento líquido inflamável | Pool fire + combustão | Média |
| 4 | Vazamento em módulo offshore | Confinamento + ventilação | Média |
| 5 | Nuvem explosiva + ignição retardada | VCE + onda de choque | Alta |

---

## Normas e Referências Regulatórias

- **API 752 / API 753** — Gestão de risco de explosão em instalações de processo
- **API 521** — Sistemas de alívio de pressão e despressurização
- **EN 1473** — Instalações de GNL — projeto e construção
- **NFPA 59A** — Standard for the Production, Storage, and Handling of LNG
- **ISO 31000** — Gestão de riscos
- **ANP Resolução 43/2007** — Gerenciamento de riscos em instalações de E&P (Brasil)
- **TNO Yellow Book** — Methods for the calculation of physical effects (referência padrão europeia)
- **SFPE Handbook** — Society of Fire Protection Engineers (incêndios)
