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
| Nº de espiras efetivas | N_e | — | **5** (padrão Lapple; faixa: 2 ≤ N_e ≤ 10) |

### Diâmetro de corte D' — Avaliação (D_c conhecido) [eqs. 3.86–3.89]

Diâmetro mínimo coletável (η = 1, partícula na posição mais desfavorável):
```
D_min = √(18μ B_c³ / (π · N_e · Q · (ρ_s − ρ)))     [eq. 3.86]
```

Diâmetro de corte (D_min / D' = √2):
```
D' = √(9μ B_c³ / (π · N_e · Q · (ρ_s − ρ)))          [eq. 3.88]
```

Forma adimensional com N_e = 5 e B_c = D_c/4 [eq. 3.92]:
```
D' / D_c = 0.0946 · √(μ D_c / (Q · (ρ_s − ρ)))
```

### Velocidade de entrada

```
U_θ0 = v_i = Q / (B_c × H_c)
```
**Faixa válida (Perry, 1984):** 20 ≤ U_θ0 ≤ 70 ft/s  →  6.1 ≤ v_i ≤ 21.3 m/s  
Valor recomendado: **U_θ0 ≈ 50 ft/s ≈ 15.2 m/s**
- < 6 m/s → eficiência muito baixa
- > 21 m/s → ressuspensão das partículas coletadas

### Queda de pressão [eqs. 3.93–3.98]

Shepherd & Lapple determinaram **ξ = 8** para as proporções da Fig. 3.20:
```
ΔP_c = 8 · (ρ · U_θ0²) / 2          [Pa, SI]
```
ou equivalentemente:
```
ΔP_c ≈ 0.002 · ρ_c · U²_θ0          [lbm/ft², com U em ft/s]
ΔP_c ≈ 0.024 · ρ_c · U²_θ0          [ft de coluna d'água, com U em ft/s]
```
**Restrição Valgroup:** ΔP ≤ 40 mbar (≈ 16 pol H₂O) → verificar após calcular v_i.

#### Onde medir ΔP (Figura 3.23)
```
ΔP_c = p_A − p_P
```
- **p_A**: pressão estática no duto de **alimentação** (entrada tangencial)
- **p_P**: pressão estática na saída do **vortex finder** (passante — gás limpo)

> **Star-CCM+:** dois monitores "Area Average → Static Pressure":
> um na face de entrada e outro na face de saída do vortex finder.
> ΔP = Report_entrada − Report_saída_vortex_finder.

#### Potência do soprador [eq. 3.100]
```
Pot_sop = ΔP_c · Q / Rend
```
- Rend = 0.6–0.8 (motor-soprador industrial típico)

---

## 4. Projeto do Ciclone Lapple (seção 3.4.3) — D_c a partir de d* alvo

Para **dimensionar** (dado d* desejado, encontrar D_c), inverter a eq. 3.88 via B_c [eq. 3.101]:
```
B_c = √(N_e · (ρ_s − ρ) · Q · (d*)² / (9μ))
```
Como B_c = D_c / 4:
```
D_c = 4 · √(N_e · (ρ_s − ρ) · Q · (d*)² / (9μ))
```

**Procedimento de projeto (2 passos — Peçanha seção 3.4.3):**

**Passo 1 — Estimativa inicial de d*:**
- Adotar um d* inicial com base na PSD da alimentação (DT_A)
- Regra prática: começar com d* = D_min (η ≈ 1 para todos os tamanhos)
- Calcular D_c → verificar v_i → ajustar

**Passo 2 — Refinamento com a curva η(d_p):**
- Com D_c calculado, obter D' pela eq. 3.88
- Calcular η_i para cada fração da PSD do char
- Calcular η̄ global → verificar se atende ao requisito do processo
- Se não atender: reduzir D_c (menor D_c → menor D' → capta partículas mais finas, mas ↑ v_i e ↑ ΔP)

---

## 5. Procedimento de Cálculo Completo (Valgroup)

1. **Calcular ρ e μ do gás** via Peng-Robinson a T=450°C, P=1.2 bar (aguardando composição)
2. **Converter vazão:** ṁ_gás = 800 kg/h → Q = ṁ/ρ [m³/s]
3. **Definir d* alvo** com base na PSD do char carreado (quando chegar)
4. **Calcular D_c** pela eq. 3.101 inversa com N_e = 5
5. **Verificar v_i:** se fora de 6–21 m/s, ajustar com múltiplos ciclones em paralelo
6. **Calcular D'** pela eq. 3.88 e montar tabela de η_i por fração granulométrica
7. **Calcular η̄** global = Σ (η_i × Δm_i / m_total)
8. **Verificar ΔP** ≤ 40 mbar → se exceder, rever v_i ou usar ciclone maior
9. **Definir geometria completa** com as proporções da Tabela (seção 2)
10. **Gerar STEP** com script CadQuery para importação no Star-CCM+

---

## 5. Procedimento Iterativo Completo de Projeto (seção 3.4.3 — 5 passos)

> Usado quando η̄ alvo é especificado e d* é incógnita.

**Passo 1 — Valor inicial de d*:**
Adotar D_i* com base na DT_A (distribuição de alimentação). Como regra prática, estimar d* = D₅₀ da PSD do char carreado.

**Passo 2 — Curva η(d_p) da distribuição:**
Supor que a DT_A é conhecida (tabela ou modelo LN/RRB/GGS). Usar a eq. 3.90 para calcular η_i para cada d_p da PSD.

**Passo 3 — Diagrama η vs y_A:**
Lançar diagrama cartesiano de η (eixo vertical) vs y_A obtidos da DT_A. Traçar curva do tipo "curva francesa" (sigmoidal).

**Passo 4 — Calcular η̄_c (calculada):**
Aplicar a fórmula do Cálculo Integral (áreas iguais, seção 3.3.2):
```
η̄_c = ∫₀¹ η(y_A) dy_A         [eq. 3.103]
```
Caso existam partículas menores que D_min na alimentação [eq. 3.102]:
```
η̄_c = ∫₀^y_Amin η(y_A) dy_A
```
(y_Amin = fração acumulada correspondente a D_min, onde η = 0.99)

**Passo 5 — Comparar η̄_c vs η̄_desejada:**
```
Se η̄_c ≥ η̄_min  →  D_i* correto → calcular B_c pela eq. 3.101 → geometria pela Fig. 3.20
Se η̄_c < η̄_min  →  reduzir D_i* e reiniciar do Passo 1
```

---

## 6. Modelo Log-Normal para DT_A + Figura 3.24

Quando a distribuição de alimentação for Log-Normal, a equação explicitável é [eq. 3.104–3.107]:
```
d_p = d* · √(η / (1 − η))         [invertendo eq. 3.90]

y_A = ½ · [1 + erf(u)]             [CDF Log-Normal, eq. 3.105]

erf(u) = (2/√π) · ∫₀ᵘ exp(−t²) dt  [eq. 3.106]

u = ln(d_p / D₅₀) / (√2 · ln σ)    [eq. 3.107]
```
- σ = desvio padrão geométrico da distribuição
- D₅₀ = diâmetro médio da alimentação

**Figura 3.24 — η̄ vs D₅₀/d* com parâmetro σ (Massarani, 1984):**

Para U_θ0 = 50 ft/s, com DT_A descrita pelo modelo LN:
- Curvas de σ = 1.0 → 4.5 mostradas
- Eixo x: D₅₀/d* (1 a 9)
- Eixo y: η̄ (0.5 a 1.0)

> **Uso prático Valgroup:** Uma vez calculado d* (do D_c escolhido), calcular D₅₀/d* com o D₅₀ do char carreado, e ler η̄ diretamente do gráfico para o σ correspondente — sem integração numérica.

---

## 7. Ciclones em Paralelo (Bateria) [eq. 3.108]

Quando um único ciclone resulta em v_i fora da faixa 6–21 m/s, usar n ciclones em paralelo:
```
n = Q / (U_θ0 · B_c · H_c)
```
- n geralmente não é inteiro → arredondar para cima
- n > n_real → cada ciclone recebe Q/n_real > Q/n → U_θ0 aumenta ligeiramente
- U_θ0 > 50 ft/s → d* menor → eficiência melhor, mas ΔP sobe

> **Relevância Valgroup:** Com Q relativamente baixo (~720 kg/h de gás a 450°C), pode ser que um único ciclone Lapple resulte em D_c muito pequeno (v_i muito alta). Verificar se n = 2 ou 4 ciclones menores em paralelo são melhores que um único grande.

---

## 8. Equações Finais da Bateria — Projeto com n ciclones e d* fixo

Equações derivadas para n' ciclones em paralelo com d* garantido:

**Novo U_θ0 da bateria** [eq. 3.110]:
```
U_θ0 = Q / (2·n'·B_c²)
```
(porque H_c' = 2B_c para cada ciclone da bateria)

**d' em função de n e B_c** [eq. 3.112]:
```
d' = √(9μ·n'·B_c³ / (π·Q·N_e·(ρ_s − ρ)))
```

**B_c a partir de d* alvo e n' ciclones** [eq. 3.113 — equação mestra de projeto]:
```
B_c = ∛(π·Q·N_e·(ρ_s − ρ)·(d*)² / (9μ·n'))
```
→ D_c = 4·B_c → todas as outras dimensões pela Fig. 3.20.

> **Ponto-chave:** qualquer valor inteiro de n' pode ser usado mantendo d* fixo. A escolha de n' é então um problema de espaço físico, custo e logística de manutenção — não de eficiência.

**Figuras 3.25 e 3.26 — η̄ vs D₅₀/d* para modelos RRB e GGS:**
- Fig. 3.25: parâmetro = n (expoente RRB): curvas para n = 0.5, 0.7, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0
- Fig. 3.26: parâmetro = m (expoente GGS): curvas para m = 0.5 → 3.5
- Uso idêntico ao da Fig. 3.24 (LN): entrar com D₅₀/d* e ler η̄ para o expoente de dispersão da PSD

---

## 9. Hipóteses do Modelo Lapple (limitações → justificam CFD)

- **Sem turbulência:** assume escoamento espiral laminar e ordenado. Na realidade, turbulência ressuspende finos já coletados → **η real < η Lapple**
- **Sem mistura radial:** partícula entra em B_c/2 da parede (pior caso), mas assume trajetória determinística. Na realidade, partículas pequenas são arrastadas de volta pelo vórtice interno.
- **N_e fixo:** o número de espiras efetivas é estimado geometricamente. O CFD mostra que o escoamento real desvia da espiral perfeita.
- **Sem bypass:** parte do gás entra direto no vortex finder sem espiralar (short-circuit). O Lapple ignora isso.
- **Conclusão:** Lapple → limite superior de eficiência. CFD (Star-CCM+, fase discreta) → eficiência realista com turbulência e ressuspensão.

### Pontos específicos onde o CFD supera o Lapple (Valgroup)

| Fenômeno | Lapple | CFD (Star-CCM+) |
|---|---|---|
| N_e efetivo | fixo = 5 | calculado do campo de velocidades (tipicamente 3–4 na prática) |
| Curva η_i(d_p) | S-curve idealizad (eq. 3.90) | grade efficiency real: deslocada para direita, menos afiada |
| Ressuspensão | ignorada | capturada pela turbulência near-wall e reentrada de partículas |
| Bypass (short-circuit) | ignorado | visível no campo de pressão e trajetórias Lagrangianas |
| ΔP | analítico (ξ=8) | campo de pressão 3D com efeitos helicoidais (erro tipico 10–30%) |
| Temperatura | entra via ρ e μ | gradiante térmico parede-gás afeta camada limite onde char precisa sedimentar |
| Partículas <20 μm | trajetória determinística | dispersão estocástica turbulenta → finos escapam mais do que Lapple prevê |

---

## 9. Faixa de Aplicação (Perry, 1984)

- Partículas: **5–200 μm** com densidade suficiente
- Ciclones operam com **baixas quedas de pressão** (tipicamente 3–5 in H₂O)
- **Char Valgroup:** fração carreada concentrada abaixo de 150 μm → ciclone pode ter dificuldade com a fração < 75 μm (~9.4% da amostra) → possível necessidade de estágio secundário
