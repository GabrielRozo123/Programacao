# Defensabilidade do projeto — o que já está verificado e o que falta

> Checklist para sustentar o dimensionamento diante de um cliente / revisor externo.

---

# 1. Por que RST (e não k-ε / k-ω) — a literatura

## 1.1 O problema é a hipótese de Boussinesq
Modelos de **viscosidade turbulenta** (k-ε, k-ω, SST) assumem que o tensor de Reynolds é
proporcional à taxa de deformação média, com **um escalar** νt. Isso implica turbulência
**isotrópica** — a mesma "viscosidade" em todas as direções.

**Num vórtice isso é falso por construção.** As tensões normais radial, tangencial e axial são
muito diferentes entre si, e é justamente o **transporte radial anisotrópico de momento angular**
que define o perfil de velocidade tangencial (vórtice livre fora, vórtice forçado no núcleo).

## 1.2 O que a literatura mediu
**Hoekstra, Derksen & Van Den Akker (1999)** — comparação contra **LDA experimental**:
| Modelo | Resultado |
|---|---|
| **k-ε** | previu **apenas o vórtice interno** — contradiz a estrutura de **dois vórtices** medida |
| **RNG k-ε** | melhora significativa |
| **RSM (LRR-G)** | **melhor comportamento** ✅ |

> *"Generally, **at least a second-order closure is needed** to capture the anisotropy and achieve
> realistic simulations."*

E a **Best Practices da própria Siemens** (KB000040310):
> *"An **anisotropic** turbulence model is **required**… Standard k-ε models and other models based on
> assumptions of **isotropic turbulence are not suitable** as they tend to **over predict the turbulent
> viscosity** and exaggerate the forced vortex. In STAR-CCM+, the **Reynolds Stress Transport (RST)**
> is most appropriate… The **Elliptic Blending** model is the preferred model."*

## 1.3 Isso explica exatamente o que MEDIMOS
| Nossa observação | O que a literatura prevê |
|---|---|
| k-ω puro: **ξ = 2,5** contra 6,40 tabelado | νt superestimado → momento angular super-difundido → swirl fraco |
| k-ω puro: **PVC morrendo** em vez de se sustentar | dissipação excessiva mata a instabilidade |
| k-ω + Curvature Correction: **v_max = 1,73× o vórtice livre** | a CC é um **remendo** que super-corrige |

> **Não foi tentativa e erro — foi o modo de falha documentado.**

## 1.4 A hierarquia
```
k-ε           ← inadequado (só o vórtice interno)
k-ω / SST     ← mesma família isotrópica
RNG k-ε       ← melhora
k-ω + CC      ← remendo; instável em vórtice confinado
RSM / RST     ← ✅ padrão para entrega de engenharia
LES           ← melhor, mas exige malha e custo muito maiores
```
**RST não é exótico — é o mínimo aceitável para ciclone em contexto profissional.**

---

# 2. ✅ Verificações de projeto JÁ FEITAS

| # | Verificação | Critério | Nosso | ✓ |
|---|---|---|---|---|
| 1 | **Proporções geométricas** | Stairmand HE | exatas (a=0,5Dc · b=0,2Dc · De=0,5Dc · S=0,5Dc · h=1,5Dc · H=4Dc · B=0,375Dc) | ✅ |
| 2 | **Velocidade de entrada** | 50–90 ft/s (15,2–27,4 m/s) | **15,23 m/s = 50 ft/s** — piso da faixa, **conservador** | ✅ |
| 3 | **ΔP × limite do cliente** | < 40 mbar | **28,4 ± 0,6 mbar** → folga **29 %** | ✅ |
| 4 | **ΔP CFD × analítico** | mesma ordem | **erro 1,2–4,8 %** | ✅ |
| 5 | **Fator de perda ξ** | 6,40 tabelado (Stairmand HE) | **6,09–6,32** | ✅ |
| 6 | **Turndown 50 %** | atender também a 50 % | **6,5 mbar**, folga 84 % | ✅ |
| 7 | **Comprimento natural do vórtice** (Alexander) | l < altura do ciclone | **0,719 m < 1,160 m** → sobra **296 mm** de zona quiescente | ✅ |
| 8 | **Diâmetro de corte × PSD** | d\* ≪ menor fração relevante | **d\* = 7,6 µm** vs PSD toda **> 20 µm** | ✅ |
| 9 | **T_parede × ponto de orvalho** | > 250 °C | **381 °C @100 %** e **367 °C @50 %** | ✅ |
| 10 | **Incerteza numérica** | declarada | **±3,8 %** medida em 3 rodadas | ✅ |
| 11 | **Modelo de turbulência** | anisotrópico | **RST Elliptic Blending** | 🔄 rodando |

---

# 3. ⏳ Verificações que AINDA FALTAM

| # | Verificação | Por que importa | Estado |
|---|---|---|---|
| A | **Curva η × d (CFD)** | é o entregável principal | setup pronto |
| B | **Velocidade de saltação (Kalen & Zenz)** | `v_i/v_s = 1,25` → eficiência máxima · `= 1,36` → **começa re-entrainment** | ⚠️ **fazer com a referência em mãos** — a correlação usa constante dimensional em unidades inglesas; não calcular de memória |
| C | **Espessura de parede** | corrosão (HCl) + erosão (char com 21 % de minerais) | não iniciado |
| D | **Mapa de erosão** | char mineral (Ti 14,9 + Si 3,5 + Fe 3,2 %) | checkbox na fase Lagrangeana |
| E | **PSD na corrente gasosa** | a amostra atual é do char **extraído** (28 % > 1 mm, não arrastável a 1,03 m/s) | ⚠️ **pendência com a Valgroup** |
| F | **Decisão de isolamento** | agora é eficiência energética, não integridade | aberta |

---

# 4. 📚 Referências para sustentar o relatório

## Projeto de ciclone
- **Hoffmann, A.C. & Stein, L.E. — _Gas Cyclones and Swirl Tubes: Principles, Design and Operation_** (Springer). **É a referência da área.**
- Coulson & Richardson, _Chemical Engineering_, Vol. 2 — procedimento de dimensionamento
- Perry's Chemical Engineers' Handbook — seção de separação gás-sólido
- Cooper & Alley, _Air Pollution Control: A Design Approach_ — método de Lapple
- Stairmand, C.J. (1951) — as proporções HE
- Alexander, R.McK. (1949) — comprimento natural do vórtice
- Kalen & Zenz — velocidade de saltação e velocidade de máxima eficiência

## CFD de ciclone
- **Hoekstra, Derksen & Van Den Akker (1999)** — LDA × k-ε × RNG × RSM
- Boysan, Ayers & Swithenbank (1982) — o clássico que mostrou a falha do k-ε
- **Powder Technology — _"Comparison of boundary conditions for predicting the collection efficiency
  of cyclones"_** — compara *bottom trap* × *cone and bottom trap* × *tangential lift-off*
- Siemens KB000040310 — _Best Practices for Cyclone Separators_
- Siemens KB000033060 — método oficial de eficiência Lagrangeana

---

# 5. 🎯 O que torna um projeto defensável
Não é acertar o número. É:
1. **Método rastreável** — proporções de referência, não invenção
2. **Verificação cruzada** — CFD × analítico × tabelado (fizemos três)
3. **Incerteza declarada** — ±3,8 %, medida e não estimada
4. **Limites físicos checados** — vórtice livre, comprimento de vórtice, orvalho
5. **Premissas explícitas** — ρ_p = 1500 (não os 776,75 de bulk), PSD estimada, convenção de captura
6. **Pendências nomeadas** — a PSD na corrente gasosa está registrada como pendência do cliente

> **Um projeto com incerteza declarada e pendências nomeadas é mais forte que um projeto com
> um número único e nenhuma ressalva.** É isso que separa cálculo de faculdade de engenharia
> de verdade.
