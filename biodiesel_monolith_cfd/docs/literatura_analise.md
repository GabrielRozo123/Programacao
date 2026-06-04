# Análise Crítica da Literatura — CFD de Reator Monolítico para Biodiesel
**Gabriel Rozo | FEQ/UNICAMP | Mestrado 2025–2027**  
**Orientadores:** Prof. Dr. Raphael | Prof. Dr. Dirceu Noriler

---

## 1. Mapa do Estado da Arte — O que a Literatura Cobre

### 1.1 Geometria e Escala do Reator (Pasta 01)

As teses da University of Bath fornecem o único benchmark direto para reator monolítico com washcoat para biodiesel. Os parâmetros geométricos extraídos são:

| Parâmetro | Valor Bath (2015) | Valor Bath (2017) | Adotado no CFD |
|---|---|---|---|
| Suporte | Cordierita | Cordierita | Cordierita |
| Densidade celular | 61 células/cm² | 62 células/cm² | ~400 CPSI |
| Dh (hidráulico) | 1,1 mm | ~1,1 mm | **1,1 mm** |
| Espessura washcoat | ~10–50 µm | ~10–50 µm | BC de parede (sem resolver internamente) |
| T operação | 120°C | 120°C | **120°C (393 K)** |
| P operação | 8 bar | 8 bar | **8 bar** |
| Razão molar MeOH:óleo | 6:1 | 6:1 | **6:1** |

**Justificativa do canal representativo 2D:** O monólito tem simetria periódica → simular 1 canal com BC de simetria nas laterais. Custo computacional: ~1000× menor que o monólito completo. Referência: hipótese padrão da literatura (Hayes & Kolaczkowski, 1997; Groppi et al., 1995).

---

### 1.2 Regime Hidrodinâmico — Confirmação Analítica (Pasta 03)

Antes de qualquer CFD, confirmar o regime:

```
Re = ρ·u·Dh / μ

Dados (mistura óleo/MeOH a 120°C):
  ρ  ≈ 870 kg/m³
  μ  ≈ 6×10⁻³ Pa·s   (óleo de canola a 120°C — reduzido vs. 25°C)
  Dh = 1,1×10⁻³ m
  u  ≈ 1–5×10⁻³ m/s  (vazão típica de reboiler monolítico)

→ Re ≈ 0.16–0.80  ← Regime de Stokes. Laminar. Sem turbulência.
```

**ΔP analítico (Hagen-Poiseuille, canal plano 2D):**
```
ΔP = 12·μ·L·u / Dh²

Para L = 50 mm, u = 1 mm/s:
  ΔP = 12 × 6×10⁻³ × 0.05 × 1×10⁻³ / (1,1×10⁻³)²
     = 3.6×10⁻⁶ / 1.21×10⁻⁶
     ≈ 3 Pa   → virtualmente zero vs. 8 bar de operação ✓
```

**Comprimento de entrada (desenvolvimento do perfil):**
```
L_hid = 0,05 · Re · Dh ≈ 0,05 × 0,5 × 1,1 mm ≈ 0,028 mm

→ O perfil de Poiseuille é atingido a < 0,1 mm da entrada.
  Para L = 50 mm, o canal opera 99,9% em regime desenvolvido.
  Isso simplifica a análise e a Fase 1 se torna quase uma verificação algébrica.
```

---

### 1.3 Cinética — O Ponto Crítico (Pasta 02)

**⚠️ GAP IDENTIFICADO — CRÍTICO:**

| Referência | Tipo de catálise | Tipo de cinética | Aplicável ao projeto? |
|---|---|---|---|
| Noureddini & Zhu (1997) | **Homogênea** (NaOH) | 2ª ordem simples | ❌ Não diretamente |
| ZnAl₂O₄ (TBD, ~2018) | Heterogênea sólido | LHHW | ✅ Mas referência incompleta |
| Bath 2015 (SrO) | Heterogênea sólido | Não informado no README | ❓ Buscar na tese |
| Bath 2017 (Zn-prolina) | Heterogênea sólido | Não informado no README | ❓ Buscar na tese |

**O que o projeto precisa:** expressão LHHW do tipo:

```
         k · C_TG · C_MeOH
r = ──────────────────────────────────────      [mol/m²_wall/s]
     (1 + Ka·C_TG + Kb·C_MeOH + Kp·C_FAME)²

k = A · exp(-Ea / R·T)    [m⁴/(mol·s)]
Ka, Kb, Kp               [m³/mol]
```

**Ação necessária antes da Fase 2:**
1. Localizar parâmetros LHHW para o catalisador escolhido (SrO ou Zn-prolina)
2. Se não houver LHHW na literatura para o catalisador exato, usar Noureddini & Zhu com fator de efetividade η de washcoat (abordagem pseudo-homogênea — defensável na dissertação)

---

### 1.4 Transferência de Massa — O Risco Oculto (Pasta 04/05)

**Número de Schmidt:**
```
Sc = μ / (ρ · D_TG)
   = 6×10⁻³ / (870 × 2×10⁻¹⁰)
   ≈ 34 500   ← Sc >> 1 (transporte de massa MUITO mais lento que momento)
```

**Número de Damköhler (diagnóstico do regime):**
```
Da = r_max · Dh / (D_TG · C₀)

Para r_max ~ 10⁻⁵ mol/(m²·s), Dh = 1,1 mm, D = 2×10⁻¹⁰ m²/s, C₀ ~ 500 mol/m³:
  Da ≈ 10⁻⁵ × 1,1×10⁻³ / (2×10⁻¹⁰ × 500)
     ≈ 0.11   → Regime cinético (boa notícia: a cinética limita, não a difusão)
```

> **Se Da >> 1:** o modelo LHHW na parede não captura a física real — precisaria de modelo de difusão no washcoat (modelo de pellet). Para Da < 1, a BC de Surface Reaction no STAR-CCM+ é fisicamente correta.

**⚠️ Isso precisa ser calculado com os parâmetros cinéticos reais quando disponíveis.**

---

### 1.5 Termoquímica (Pasta 05)

**ΔHrxn da transesterificação:**
```
TG + 3 MeOH → 3 FAME + GL

Da literatura:
  ΔHrxn ≈ +5 a +15 kJ/mol_TG  (fracamente endotérmica)
  CONFIRMAR com: NIST WebBook (entalpias de formação) ou
                 Freedman et al. (1986), JAOCS 63:1375
```

**Impacto no CFD:**
```
Fonte de calor na parede:  q_rxn = ΔHrxn · r_LHHW   [W/m²]

Para r ~ 10⁻⁵ mol/(m²·s) e ΔH ~ 10 000 J/mol:
  q ≈ 0.1 W/m²  → gradiente de T ao longo do canal é PEQUENO
```

> A reação é fracamente endotérmica. Isso é bom: a Fase 1 (hidrodinâmica) domina o comportamento, e o efeito térmico da Fase 2 será uma perturbação, não uma reorganização total do escoamento.

---

## 2. Lacunas Bibliográficas — O que Falta

| # | Lacuna | Impacto | Ação |
|---|--------|---------|------|
| 1 | Parâmetros LHHW para catalisador heterogêneo específico | **CRÍTICO** para Fase 2 | Buscar artigo ZnAl₂O₄ + teses Bath |
| 2 | ΔHrxn confirmado da transesterificação heterogênea | Alto (Source Term de energia) | NIST + Freedman (1986) |
| 3 | Difusividade D_TG em MeOH a 120°C | Médio (transporte de massa) | Correlação de Wilke-Chang |
| 4 | Propriedades físicas mistura óleo/MeOH a 120°C, 8 bar | Médio (material properties CFD) | Perry's + DIPPR |
| 5 | Referências CHT em microcanais laminares | Baixo (Fase 2 validação) | Papéis de Groppi, Hayes |
| 6 | Autores e DOIs completos (BibTeX TBDs) | Baixo (mas necessário na dissertação) | Identificar todos os TBDs |

---

## 3. Hierarquia de Referências para a Dissertação

```
PILAR 1 — Geometria e Hipóteses
  └── Teses Bath (2015, 2017)  ← único benchmark direto monólito + biodiesel

PILAR 2 — Cinética
  └── Noureddini & Zhu (1997)  ← base mecanística (homogênea, mas fundacional)
  └── Artigo ZnAl₂O₄ (TBD)    ← LHHW heterogêneo (CRÍTICO — localizar)
  └── Pinheiro & Larimi (2024) ← benchmark CFD + reação heterogênea recente

PILAR 3 — CFD em Microcanais
  └── Pinheiro & Larimi (2024) ← estado da arte mais próximo
  └── MDPI Energies (2024)     ← revisão recente de tecnologias

PILAR 4 — Transferência de Calor/Massa
  └── Correlações de Nu e Sh para canal laminar (Nu = 7.54)
  └── Análise de Damköhler (a desenvolver na dissertação)

PILAR 5 — Metodologia CFD
  └── Tutorial STAR-CCM+: Surface Chemistry
  └── Tutorial STAR-CCM+: CHT
```

---

## 4. Próximas Ações por Prioridade

### Imediato (antes de rodar qualquer simulação):
- [ ] Completar referência ZnAl₂O₄ — é o coração da Fase 2
- [ ] Confirmar ΔHrxn (NIST ou Freedman 1986)
- [ ] Calcular D_TG/MeOH via Wilke-Chang (ver script em `/scripts/`)

### Curto prazo (Fase 1 — hidrodinâmica):
- [ ] Construir geometria 2D (canal retangular: Dh = 1,1 mm, L = 50 mm)
- [ ] Rodar cold flow no STAR-CCM+ e validar vs. Poiseuille analítico
- [ ] Documentar independência de malha (GCI)

### Médio prazo (Fase 2 — reação):
- [ ] Implementar Surface Reaction LHHW como Field Function
- [ ] Adicionar Multi-Component Liquid (TG, MeOH, FAME, GL)
- [ ] Acoplar CHT (Fluid Temperature)
- [ ] Analisar perfil axial de conversão e temperatura
