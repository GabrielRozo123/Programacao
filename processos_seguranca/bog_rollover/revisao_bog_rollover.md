# BOG / Rollover Criogênico — Revisão para Estudo CFD de Segurança

> Tema: relacionar **segurança de processos** com **CFD** via geração de Boil-Off Gas (BOG),
> estratificação térmica e rollover em tanques criogênicos.
> Objetivo: estudo "bacana", original (fugir do clichê de dispersão de gás) e com
> custo computacional equilibrado.
> Atualizado: 2026-06-27

---

## 1. Por que é um bom tema de SEGURANÇA

Em tanque criogênico (LNG, LN₂, LH₂), o calor que vaza pela isolação evapora líquido →
gera **BOG**. Se o tanque é enchido com líquido de densidade diferente (ex.: enchimento por
baixo com LNG mais pesado/quente), formam-se **camadas estratificadas**. Quando as densidades
se equalizam, as camadas **invertem subitamente (rollover)** → surto de vapor que pode
exceder a pressão de projeto → **sobrepressão, abertura de alívio / venting, dano ao teto**.

### Caso fundador: La Spezia, 1971
- Tanque de **50.000 m³**, enchimento por baixo com LNG mais pesado que o "heel" envelhecido.
- **36 h** após o enchimento: sobrepressão súbita acima da pressão de projeto.
- **~186 toneladas** de gás natural ventadas em **< 16 h**; teto levemente danificado; sem ignição.
- É o incidente que colocou rollover no mapa da segurança de LNG.
- Gancho de segurança do estudo: estratificação → rollover → surto de BOG vs. capacidade de
  alívio (API 521).

---

## 2. Níveis de modelagem vs. custo computacional

| Nível | Modelo | Captura | Custo |
|---|---|---|---|
| A | Monofásico líquido, 2 camadas miscíveis (Δρ), Boussinesq | overturn do rollover, T(z,t) | baixo (≈ chiller) |
| B | A + interface como parede c/ fluxo de calor + ullage lumped | BOG rate, auto-pressurização | médio |
| **C** | **VOF + mudança de fase (Lee/Schrage) na interface** | **evaporação resolvida, BOG real** | **alto** |

**Decisão atual: Nível C**, viabilizado por **malha adaptativa** (refino só na interface
líquido-vapor) para reduzir custo. Validar primeiro no caso pequeno de LN₂ (abaixo).

---

## 3. Casos de validação com dimensões REAIS

### 3.1 Seo & Jeong (2010) — LN₂ bancada ⭐ (caso barato de validação)
**É o caso ideal para a máquina** — domínio minúsculo, axissimétrico, dados de P(t) publicados.
- Geometria: **cilíndrica vertical**, aço inox 304
- **Diâmetro = 201 mm**
- **Altura = 213 mm**
- **Volume interno = 6,75 L**
- Fluido: **nitrogênio líquido (LN₂)**
- Variáveis testadas: vários **heat leaks** e **frações de líquido** (fill level)
- Achado-chave: fill inicial **< 35%** → pressão sobe acentuadamente (forte sensibilidade)
- Uso: validar o modelo de mudança de fase (curvas de auto-pressurização) antes de escalar.

### 3.2 Hasan, Lin & Van Dresar (NASA Lewis, 1991) — LH₂ (caso intermediário)
- Geometria: **elipsoidal**, razão eixo maior/menor = 1,2
- **Diâmetro maior = 2,2 m**
- **Volume = 4,89 m³**
- Fluido: **hidrogênio líquido (LH₂)**
- Fill level: **83–84%** (por volume)
- Fluxo de calor na parede: **0,35 / 2,0 / 3,5 W/m²** (baixo)
- Achado: taxa de subida de pressão e estratificação crescem com o fluxo de calor;
  no maior fluxo, taxa > 3× a homogênea.
- Uso: caso de escala maior, validação de estratificação sob heat flux controlado.

### 3.3 Industrial / La Spezia (aplicação final)
- Tanque cilíndrico de grande porte (~50.000 m³) — só depois de validar nos pequenos.
- Aqui entra a narrativa de segurança (venting, sobrepressão).

---

## 4. Mapeamento para tutoriais do Star-CCM+

Plano: combinar dois tutoriais de **Multiphase Flow → VOF**:

1. **VOF: Boiling** — núcleo da física: mudança de fase líquido↔vapor na interface
   (mecanismo de geração de BOG). Fornece o modelo de evaporação/condensação.
2. **VOF: Tank Sloshing with Adaptive Meshing** — geometria de tanque + **malha adaptativa**
   na superfície livre. É o que torna o Nível C pagável: refina só onde a interface está.

Boiling = "o quê" (phase change). Sloshing+AMR = "como pagar barato" (malha adaptativa).

---

## 5. Escopo enxuto proposto

- **Caso de validação:** tanque LN₂ de Seo & Jeong (D=201 mm, H=213 mm, 6,75 L)
- **Geometria:** 2D-axissimétrico primeiro (baratíssimo) → 3D só se necessário
- **Física:** VOF + mudança de fase (Lee/Schrage), malha adaptativa na interface
- **BCs:** parede com fluxo de calor (heat leak), inicialização estratificada (2 camadas, Δρ/ΔT)
- **Validação:** comparar curva P(t) de auto-pressurização com dados de Seo & Jeong
- **Resultado de segurança:** tempo até rollover, pico de T na interface, surto de BOG vs.
  capacidade de alívio (referência API 521)

---

## 6. Fontes

- La Spezia e mecanismos de rollover (IChemE): https://www.icheme.org/media/15495/paper-43.pdf
- CFD Analysis of Stratification and Rollover — Industrial-Scale LNG Tank (ACS I&EC Res):
  https://pubs.acs.org/doi/abs/10.1021/acs.iecr.0c02546
- Predicting LNG rollovers using CFD (ScienceDirect):
  https://www.sciencedirect.com/science/article/abs/pii/S0950423019301871
- Seo & Jeong (2010) — Analysis of self-pressurization of cryogenic fluid storage tank
  (thermal diffusion model), Cryogenics:
  https://www.sciencedirect.com/science/article/abs/pii/S0011227510000603
- Hasan, Lin & Van Dresar (NASA, 1991) — Self-pressurization of a flightweight LH₂ tank:
  https://ntrs.nasa.gov/citations/19910011011
- Numerical study of pressure build-up in vertical cryogenic tanks (ScienceDirect):
  https://www.sciencedirect.com/science/article/abs/pii/S1359431119320344
- Validation of cryogenic propellant tank self-pressurization (NASA NTRS):
  https://ntrs.nasa.gov/citations/20220018755
