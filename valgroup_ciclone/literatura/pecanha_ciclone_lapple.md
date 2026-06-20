# Peçanha — Sistemas Particulados Diluídos: Ciclone Lapple

**Fonte:** Ricardo A. Peçanha, *Sistemas Particulados — Operações Unitárias Envolvendo Partículas e Fluidos*, Cap. 3  
**Seções extraídas:** 3.2 (Eficiência de Coleta e Diâmetro de Corte) + 3.4 (Ciclones)

---

## 1. Eficiência de Coleta

### Eficiência Global (η̄)
```
η̄ = ∫₀¹ η(yₐ) dyₐ        [eq. 3.22]
```
- η̄: eficiência global (adimensional, 0–1)
- η(yₐ): eficiência individual em função da frequência acumulada da alimentação
- **Procedimento prático:** para cada faixa granulométrica i da PSD do char, calcular η_i(d_p), ponderar pela fração mássica Δyₐ,i e somar.

### Eficiência Individual (η_i)
Para o ciclone Lapple [eq. 3.90]:
```
η_i = 1 / (1 + (D' / d_p)²)
```
- D' = diâmetro de corte (m) — ver seção 3 abaixo
- d_p = diâmetro da partícula (m)
- Quando d_p = D': η_i = 0.5 (definição de D')
- Quando d_p >> D': η_i → 1 (partícula grande, coletada)
- Quando d_p << D': η_i → 0 (partícula fina, passa)

### Diâmetro de Corte (d* ou D')
```
d* = D'/d_p  tal que  η_i = 0.5
```
Métricas complementares:
- d₂₅: diâmetro com η_i = 0.25
- d₇₅: diâmetro com η_i = 0.75
- **Índice de Afiação (SI)** [eq. 3.23]: SI = d₂₅ / d₇₅  (ideal: SI = 1)

---

## 2. Geometria do Ciclone Lapple (Figura 3.20)

Todas as dimensões em função do **diâmetro do corpo (D_c)**:

| Dimensão | Símbolo | Proporção | Descrição |
|---|---|---|---|
| Largura da entrada | B_c | D_c / 4 | dimensão transversal do duto de entrada |
| Altura da entrada | H_c | D_c / 2 | dimensão axial do duto de entrada |
| Diâmetro do vortex finder | D_e | D_c / 2 | tubo de saída do gás limpo |
| Profundidade do vortex finder | S_c | D_c / 8 | inserção do tubo dentro do corpo |
| Comprimento do cilindro | L_c | 2 · D_c | câmara cilíndrica superior |
| Comprimento do cone | Z_c | 2 · D_c | câmara cônica inferior |
| Saída de sólidos | J_c | ≈ D_c / 4 | descarga de poeira/char |
| Altura total | H_total | ≈ 4 · D_c | L_c + Z_c |

> **D_c é o único parâmetro livre.** Uma vez calculado D_c, toda a geometria está definida.

---

## 3. Equações do Modelo Lapple

### Variáveis de entrada necessárias

| Variável | Símbolo | Unidade | Status Valgroup |
|---|---|---|---|
| Viscosidade do gás | μ | Pa·s | ⚠️ aguardando composição |
| Densidade do gás | ρ | kg/m³ | ⚠️ aguardando composição |
| Densidade do char | ρ_s | kg/m³ | ⚠️ aguardando dado |
| Vazão volumétrica | Q | m³/s | ⚠️ aguardando composição |
| Nº de espiras efetivas | N_e | — | ≈ 5 (padrão Lapple) |

### Diâmetro de corte D' [eqs. 3.86–3.89]

Primeiro, diâmetro mínimo coletável (partícula na posição mais desfavorável, η = 1):
```
D_min = √(18μ B_c³ / (π · N_e · Q · (ρ_s − ρ)))     [eq. 3.86]
```

Diâmetro de corte (D_min/D' = √2):
```
D' = D_min / √2 = √(9μ B_c³ / (π · N_e · Q · (ρ_s − ρ)))     [eq. 3.88]
```

Como B_c = D_c/4:
```
D' = √(9μ (D_c/4)³ / (π · N_e · Q · (ρ_s − ρ)))
```

### Velocidade de entrada (verificar faixa Perry)
```
v_i = Q / (B_c × H_c)
```
**Faixa válida:** 6 ≤ v_i ≤ 21 m/s (Perry, 1984)  
- < 6 m/s → eficiência muito baixa  
- > 21 m/s → ressuspensão das partículas coletadas

### Queda de pressão (estimativa)
```
ΔP = ξ · (ρ/2) · v_i²
```
- ξ ≈ 8 para ciclone Lapple padrão (adimensional, varia com geometria)
- **Restrição Valgroup:** ΔP ≤ 40 mbar (≈ 16 pol H₂O) → verificar

---

## 4. Procedimento de Dimensionamento

1. **Calcular ρ e μ do gás** via Peng-Robinson a T=450°C, P=1.2 bar (aguardando composição)
2. **Converter vazão:** ṁ_gás = 800 kg/h → Q = ṁ/ρ [m³/s]
3. **Escolher D_c** (iterativo): começar com D_c estimado, calcular v_i, verificar faixa 6–21 m/s
4. **Calcular D'** com a eq. 3.88
5. **Para cada fração do char** (PSD do peneiramento):
   - d_p = diâmetro representativo da fração
   - η_i = 1 / (1 + (D'/d_p)²)
6. **Calcular η̄** global = Σ (η_i × Δm_i / m_total)
7. **Verificar ΔP** → se > 40 mbar, redimensionar
8. **Calcular geometria completa** com as proporções da Tabela acima

---

## 5. Hipóteses do Modelo Lapple (limitações → justificam CFD)

- **Sem turbulência:** assume escoamento espiral laminar e ordenado. Na realidade, turbulência ressuspende finos já coletados → **η real < η Lapple**
- **Sem mistura radial:** partícula entra em B_c/2 da parede (pior caso), mas assume trajetória determinística. Na realidade, partículas pequenas são arrastadas de volta pelo vórtice interno.
- **N_e fixo:** o número de espiras efetivas é estimado geometricamente. O CFD mostra que o escoamento real desvia da espiral perfeita.
- **Sem bypass:** parte do gás entra direto no vortex finder sem espiralar (short-circuit). O Lapple ignora isso.
- **Conclusão:** Lapple → limite superior de eficiência. CFD (Star-CCM+, fase discreta) → eficiência realista com turbulência e ressuspensão.

---

## 6. Faixa de Aplicação (Perry, 1984)

- Partículas: **5–200 μm** com densidade suficiente
- Ciclones operam com **baixas quedas de pressão** (tipicamente 3–5 in H₂O)
- **Char Valgroup:** fração carreada concentrada abaixo de 150 μm → ciclone pode ter dificuldade com a fração < 75 μm (~9.4% da amostra) → possível necessidade de estágio secundário
