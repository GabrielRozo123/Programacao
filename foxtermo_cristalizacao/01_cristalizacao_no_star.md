# Aprendizado — Como o STAR-CCM+ trata a CRISTALIZAÇÃO

> Base: doc oficial STAR-CCM+ 21.02 (*Crystallization*, *Modeling Crystallization*, *Modeling Particulate
> Flows*). Objetivo: saber **o que dá pra fazer**, **o que é preciso**, e **o que pedir ao Álvaro**.

## 1. Os dois modelos (o STAR distingue)
| Modelo | Dirigido por | Exemplo | **Nosso caso (óleo de palma)** |
|---|---|---|---|
| **Solute crystallization** | **concentração** (supersaturação): soluto dissolvido no solvente; T cai → C > C_sat → cristaliza | fármacos, açúcar | parcial |
| **Melt crystallization** | **temperatura** (sub-resfriamento): líquido esfria abaixo do ponto de fusão; admixturas baixam a T_sat e mudam a composição do cristal | gelo na água, dessalinização | **✅ é o nosso** |

**Cristalização do óleo de palma = MELT crystallization.** O óleo esfria e a **fração de alto ponto de fusão
(estearina) cristaliza**, deixando a líquida (oleína). As admixturas (a oleína) **baixam a T de saturação** e
o **cristal tem composição diferente do fundido** — exatamente o que o modelo *melt* trata.

## 2. O framework (é EMP + Balanço Populacional)
Cristalização no STAR é **Eulerian Multiphase (EMP)** com:
1. **Fase LÍQUIDA** (Multi-Component Liquid) — no melt: componente líquido + **admixtura**.
2. **Fase CRISTAL** (Particle) — com **Population Balance (PSD)**: **AMUSIG (classes)** ou **S-Gamma**.
3. **Phase Interaction** líquido↔cristal → **Interphase Mass Transfer** com o modelo de cristalização.
4. **Equação de Balanço Populacional (PBE):** transporta a distribuição de tamanho dos cristais (número por
   tamanho). Fontes: **nucleação** (nascimento de cristais) + **crescimento** (G, mudança de fase na superfície).
5. **Balanço de massa e energia por partícula:** o fluxo de massa à superfície = taxa de crescimento; calor
   vem do líquido e do interior; **entalpia de cristalização (calor latente)** via *Heat of Formation*
   (tem de ser **consistente** entre a fase líquida e a fase cristal).

**Crescimento (melt):** G = f(**sub-resfriamento** = T_sat(admixtura) − T), com prefator e expoente empíricos.

## 3. A reologia do slurry (crítico p/ óleo de palma)
À medida que cristaliza, os cristais ficam **suspensos no óleo** → a mistura **engrossa** (vira pasta). O STAR
tem **Suspension Rheology** (viscosidade função da fração sólida) — **exige regime LAMINAR**. Isso importa
muito: como no xarope do Ito, a **viscosidade dispara** e a mistura fica difícil. Interações partícula-partícula:
**Granular/Solid Pressure** (limitam a fração sólida máxima / empacotamento).

## 4. Setup (resumo dos passos)
1. **Fase líquida:** Multi-Component Liquid · Segregated Fluid Temperature · Non-reacting · (EOS) · Wall Distance.
   Componentes: **líquido + admixtura** (melt). Propriedades por componente.
2. **Fase cristal:** Particle · Segregated Fluid Temperature · **Particle Size Distribution (AMUSIG ou S-Gamma)** ·
   Wall Distance. **Heat of Formation** (calor latente) consistente com a fase líquida.
3. **Phase Interaction** líquido↔cristal → modelo de cristalização (melt) + nucleação.
4. **(+ nosso)** **MRF do agitador** + **transferência de calor conjugada** (óleo↔parede da serpentina↔água) +
   **Suspension Rheology (laminar)** + **ρ(T)/μ(T)** do óleo.

## 5. O QUE ISSO SIGNIFICA PRO FOXTERMO (escopo)
A cristalização completa (nucleação + crescimento + PBE + reologia de slurry + calor latente + MRF + CHT) é
**cara e pesada em dados**. Duas rotas (já no `00_proposta_tecnica.md`), agora com base técnica:

- **ROTA A (base, recomendada p/ começar):** **resfriamento + CHT + μ(T) forte**, **SEM** a cinética de
  cristalização. Entrega o que o Álvaro pediu — **as velocidades na serpentina** + o campo térmico + zonas
  mortas. Barata, robusta, e **não depende de dados de cinética que o cliente pode não ter**.
- **ROTA B (avançada):** o framework acima (EMP + melt crystallization + PBE + suspension rheology). Dá a
  **própria cristalização** (fração sólida, PSD, calor latente). **Só vale se o Álvaro precisar disso E tiver
  os dados de cinética/reologia.**

## 6. Dados a PEDIR ao Álvaro (refinado pela física do modelo)
**Sempre (Rota A e B):**
- Geometria: tanque, **serpentina** (Ø tubo, passo, nº voltas, Ø hélice, material), **agitador** (tipo, Ø, nº pás, rotação(ões)).
- Óleo de palma: **ρ(T) e μ(T)** (curvas!), faixa de T (entrada → cristalização).
- Água da serpentina: vazão, T entrada/saída, DN.
- Regime: **transiente** (batelada de resfriamento) ou permanente?

**Adicional se for Rota B (cristalização de verdade):**
- **T de cristalização/fusão** e **calor latente** (entalpia de cristalização) da estearina.
- **Curva de fração sólida × T** (quanto cristaliza a cada temperatura).
- **Cinética de nucleação e crescimento** (prefator/expoente) — **empírica, geralmente de ensaio**; é o elo
  mais difícil. **Perguntar se têm esses dados** — se não, fica **Rota A**.
- **Reologia do slurry:** μ em função da fração sólida.

> **Recomendação de proposta:** cotar a **Rota A como base** (entrega as velocidades pedidas) e a **Rota B
> como opção/adicional**, condicionada à existência dos dados de cinética/reologia. Isso protege o prazo e
> deixa claro ao cliente o que cada nível entrega.

## Fonte
Doc STAR-CCM+ 21.02: *Crystallization* (teoria: PBE, nucleação, crescimento, solute×melt), *Modeling
Crystallization* (setup), *Modeling Particulate Flows* (EMP base, granular/solid pressure, suspension rheology).
