# Valgroup — Separação Gás-Sólido (Ciclone)

**Cliente:** Daniel Bacellar Souza Vozza — Valgroup Brasil  
**Engenheiro:** Gabriel Hernandez Rozo — CAExperts  
**Objetivo:** Avaliar e dimensionar sistema de separação de partículas de char de gás quente de hidrocarbonetos

---

## Status Atual

**KICKOFF REALIZADO — aguardando dados do cliente**

---

## Dados Conhecidos (da reunião)

| Dado | Valor | Status |
|---|---|---|
| Temperatura do gás | 400–450°C | confirmado |
| Pressão do gás | 1.2 bar | confirmado |
| Vazão mássica total | ~800 kg/h | confirmado |
| Teor de char | ~10% → ~80 kg/h | confirmado |
| Perda de carga máxima | 16 pol H₂O (~40 mbar) | confirmado |
| Sólido a separar | Char (biomassa) | confirmado |
| Downstream finos | Condensador casco-tubo | confirmado |
| Downstream pesados | Tanque buffer → óleo | confirmado |
| Segunda opção | Quench tower (kuenti) | mencionado |
| **Densidade do gás ρ** | **3,946 kg/m³** (400°C, 1,2 bar abs) | ⚠️ estimativa do cliente — "não 100% confiantes" |
| "Dor" principal | Estimar massa específica do gás | ↑ endereçado (com ressalva) |

### Granulometria do Char (amostra biomassa 3072-1/2025.0, coleta 17/07/2025)

| Peneira | % Massa Retida |
|---|---|
| 12,5 mm | 2,78% |
| 4,75 mm | 3,77% |
| 1 mm | 9,51% |
| 0,425 mm | 12,10% |
| 0,150 mm | 25,79% |
| 0,075 mm | 36,91% |
| Fundo (< 0,075 mm) | 9,41% |

> **Atenção:** este é o char EXTRAÍDO na saída. O char CARREADO (o que interessa separar) tende a ser **mais fino** — concentrado principalmente abaixo de 150 μm.

### Composição e propriedades do char (relatório ComBio 3072-1/2025.0, 25/08/2025)

| Propriedade | Valor | Implicação p/ o projeto |
|---|---|---|
| Umidade | 4,64% b.u. | baixa — favorável a via seca (ciclone) |
| PCS (base seca) | 3.481 kcal/kg | contexto energético |
| **Densidade aparente** | **776,75 kg/m³** | *bulk* (com vazios); **falta ρ_s (densidade real da partícula)** p/ Lapple |
| **Titânio** | **14,91%** | TiO₂ (pigmento do r-PET) → char **mais denso e ABRASIVO** |
| Sílica | 3,46% | + densidade, + abrasão |
| Ferro | 3,18% | + densidade |
| **Cloro** | **2,78% (27.800 mg/kg)** | ⚠️ **HCl a 450°C → CORROSÃO** (seleção de material) |
| Enxofre / Nitrogênio | 0,45% / 0,55% | corrosão/emissão (menor) |

> **2 achados que a matriz/dimensionamento precisam absorver:**
> 1. **Minerais ~21% (Ti+Si+Fe):** o char **não é carbono fofo** — é denso e mineral. **ρ_s alto FAVORECE
>    o ciclone** (partícula pesada separa melhor → entra na eq. de Lapple), mas é **abrasivo** (erosão do
>    ciclone → material/espessura de parede).
> 2. **Cloro 2,78%:** a 450°C forma **HCl** → corrosão. Reforça a **via seca** (ciclone) sobre as úmidas
>    (quench/scrubber, onde HCl + água = ácido agressivo, e o líquido a filtrar fica corrosivo).

---

## Dimensionamento Preliminar (Lapple) — `dimensionamento/dimensionamento_lapple.py`

Com **ρ_gás = 3,946 kg/m³** (cliente) e ṁ_gás ≈ 720 kg/h → **Q ≈ 182,5 m³/h**. Estimativas ⚠️ para
μ (2,5e-5 Pa·s) e ρ_s (1500 kg/m³) a confirmar.

| Grandeza | Valor preliminar | Nota |
|---|---|---|
| **D_c (corpo)** | **≈ 163 mm** | ciclone único (H_total ≈ 653 mm) |
| v_i (entrada) | 15,2 m/s | dentro de 6–21 ✅ (n=1, sem bateria) |
| **d\* (corte)** | **≈ 3,6 µm** | robusto: 2,8–4,4 µm na sensibilidade μ/ρ_s |
| **ΔP** | **36,5 mbar** | < 40 do projeto ✅ (mas **perto do limite**) |
| **η global (amostra extraída)** | **≈ 99,9%** | **Lapple = LIMITE SUPERIOR** |
| Pot. soprador | ~264 W | pequeno |

> **Leitura honesta (2 ressalvas que mandam):**
> 1. Os ~99,9% são sobre a **amostra EXTRAÍDA** (grossa) e no **Lapple ideal**. O **char CARREADO é
>    mais fino** — se tiver massa relevante **<20 µm**, a captura real cai. **→ precisamos da PSD do char
>    carreado.**
> 2. **Lapple superestima** (ignora turbulência, ressuspensão, bypass). O **CFD (fase discreta)** dará a
>    eficiência realista — tipicamente **menor**, sobretudo nos finos. É onde o nosso estudo agrega valor.
>
> **ΔP perto de 40:** como ΔP ∝ ρ·v_i² e o ρ tem incerteza, vale margem — se ρ real for maior, ΔP sobe.
> **Condensação (email Lucas):** o ciclone é pequeno/compacto → residência curta → pouca perda térmica →
> **ajuda a manter acima do orvalho**. Confirmar o ΔT parede-gás no CFD.

---

## Dados Pendentes (solicitar à Valgroup)

### CRÍTICO
- [ ] Planilha de composição do gás (vista na reunião — Marcus vai enviar)
- [ ] Granulometria do char CARREADO (fração fina — distinta da amostra acima)
- [ ] Vazão volumétrica do gás (m³/h) ou densidade para converter da mássica
- [ ] Temperatura exata de entrada no separador (400°C ou 450°C?)

### IMPORTANTE
- [ ] Espaço físico disponível para o separador
- [ ] Material da rosca/tubulação (para seleção de material do ciclone a 450°C)
- [ ] Pressão downstream (saída do separador)
- [ ] Frequência de limpeza esperada

### COMPLEMENTAR
- [ ] Fotos do processo / layout atual
- [ ] Qualquer relatório de análise do gás
- [ ] Especificação dos condensadores downstream

---

## Escopo do Projeto

```
Fase 1: Literatura + Mapeamento de tecnologias
  → Revisão: ciclone, quench tower, filtro cerâmico, scrubber, ESP, settler
  → Tabela comparativa por critérios técnicos

Fase 2: Matriz de Decisão (formato Marcus)
  → Critérios com pesos (1=positivo, 0=neutro, -1=negativo)
  → Recomendação fundamentada da(s) melhor(es) tecnologia(s)

Fase 3: Dimensionamento
  → Propriedades do gás: ρ(T=450°C, P=1.2bar) via Peng-Robinson
  → Ciclone: método Lapple ou Stairmand
  → Validação: eficiência por faixa granulométrica

Fase 4: Simulação CFD
  → Star-CCM+ ou ANSYS Fluent
  → Fase discreta (partículas de char)
  → Eficiência de coleta por tamanho de partícula
  → Campo de velocidades e pressão

Fase 5: Apresentação à Valgroup
  → Resultados + recomendação final
```

---

## Arquivos

| Pasta | Conteúdo |
|---|---|
| `dados_cliente/` | planilha de gás, granulometria do char (quando chegar) |
| `literatura/` | revisão de tecnologias de separação gás-sólido |
| `matriz_decisao/` | planilha/script da matriz com pesos |
| `dimensionamento/` | cálculos do ciclone, propriedades do gás |
| `simulacao/` | geometria CFD, setup Star-CCM+ |

---

## Notas Técnicas

- **Massa específica do gás:** calcular com Peng-Robinson para mistura HC a 450°C/1.2bar. Essa é a "dor" que o Daniel mencionou — varia com composição e temperatura.
- **Baixa vazão + alta temperatura:** desfavorável para ciclone simples (Re baixo = eficiência menor para finos). Pode ser necessário ciclone de alta eficiência (tipo Stairmand) ou conjunto em série.
- **Risco de entupimento no buffer tank:** chars pegajosos a alta temperatura podem aglomerar. Considerar na matriz.
- **Finos abaixo de 75 μm (~9.41% + a fração carreada):** são os mais difíceis de capturar em ciclone convencional — podem precisar de estágio secundário (filtro cerâmico ou ESP).

### Email do cliente (Lucas Geronimi, Diretor — 25/06/2026) → traduzido em requisitos

> *"O ciclonamento evita a necessidade de filtração; o desafio é o dimensionamento correto do ciclone
> de forma a capturar as partículas e evitar a condensação do gás. Se forem estudar a quench, a solução
> de filtragem deve fazer parte."*

1. **Filtração é critério de decisão** → adicionado à matriz (peso 2): ciclone/via-seca **+1** (evita),
   quench/scrubber **−1** (exigem filtrar/tratar o líquido). Reforçou o ciclone (+9 → **+11/17**).
2. **Os DOIS desafios do ciclone (para o CFD):**
   - **(a) Capturar as partículas** — especialmente a fração fina <75 μm (o ponto fraco do ciclone).
     O CFD (fase discreta) quantifica a eficiência por faixa; o Lapple dá o limite superior.
   - **(b) Evitar a condensação do gás** — o ciclone tem de operar **acima do ponto de orvalho** dos
     hidrocarbonetos. **Requisito de projeto:** parede/gás acima do dew-point (senão condensa e "lava"
     o char, entope, e antecipa a condensação que é do condensador downstream). **→ Ponto térmico a
     checar no CFD** (gradiente parede-gás; ΔT de resfriamento no ciclone deve ser pequeno).
3. **Corrosão (Cl 2,78% → HCl a 450°C):** entra na **seleção de material** do ciclone (liga resistente a
   HCl a quente). Também **desfavorece as vias úmidas** (HCl aquoso = ácido) — coerente com a escolha do ciclone.
