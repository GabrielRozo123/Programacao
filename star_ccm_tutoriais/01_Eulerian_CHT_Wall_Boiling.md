# Tutorial 01 — Eulerian: Conjugate Heat Transfer Wall Boiling

> Fonte: *Simcenter STAR-CCM+ 2602 User Guide › Tutorials › Multiphase Flow*.
> Notas e comentários de engenharia nossos — **resumo, não cópia** da documentação.
> Status: ✅ tutorial completo lido (seções 1–9, 13/10/2026).

---

## 0. Por que este tutorial

É o caso da documentação mais próximo de **"temperatura de parede de um tubo com água fervendo do
outro lado"**: ebulição na parede (**RPI**, via Eulerian Multiphase) **acoplada** à condução no sólido
(CHT). A temperatura do metal **sai da solução acoplada** — não é imposta. É exatamente a grandeza que
alimenta um FEA térmico de feixe tubular.

## 1. O caso

| item | valor |
|---|---|
| Aplicação | vareta de combustível nuclear (BWR6), primeiro metro de um canal de 3,7 m |
| Regime | **ebulição sub-resfriada em escoamento** ascendente |
| Pressão | **71,7 bar** (Tsat = 560,65 K = 287,5 °C) |
| Fluxo médio na parede | **524 900 W/m²** |
| Malha | **2D axissimétrica**, fornecida pronta |
| Regiões | **3:** combustível (sólido) · revestimento (sólido) · refrigerante (fluido bifásico) |
| Folga combustível–revestimento | tratada como **resistência de contato** empírica (espessura somada ao combustível) |

> 💡 **Técnica reaproveitável:** uma camada fina de propriedades mal conhecidas (folga, incrustação,
> depósito) entra como **resistência de contato na interface**, sem malhar a camada. É o jeito de
> representar **fouling** em CHT.

## 2. Modelos físicos — um contínuo por região

### Refrigerante (fluido bifásico)
| grupo | modelo |
|---|---|
| Espaço | Axisymmetric (desligar *Two-Dimensional* antes) |
| Tempo | Steady |
| Material | **Multiphase** (+ Multiphase Interaction, automático) |
| Modelo multifásico | **Eulerian Multiphase (EMP)** |
| Regime | Turbulent |
| Turbulência EMP | **Phasic Turbulence** |
| Opcionais | **Gravity** · **Phase Coupled Fluid Energy** |

### Sólidos (revestimento e combustível)
| grupo | modelo |
|---|---|
| Espaço / Tempo | Axisymmetric · Steady |
| Material | Solid |
| Energia | **Segregated Solid Energy** |
| Equação de estado | Constant Density |

**Um contínuo por material sólido:** cria-se um, copia-se (*Copy / Paste* em *Continua*) e renomeia —
os modelos são iguais, só as propriedades mudam. Depois atribui-se cada contínuo à sua região.

> 📌 **Nota da nossa experiência (ciclone Valgroup):** aqui o sólido usa **Segregated Solid Energy**
> (volumes finitos), não *Finite Element Solid Energy*. É o caminho padrão para CHT com EMP e evita a
> instabilidade que tivemos com o solver FE (URF = 1,0).

## 3. Propriedades dos sólidos (constantes)

| material | ρ [kg/m³] | cp [J/kg·K] | k [W/m·K] |
|---|---|---|---|
| UO₂ (combustível) | 10 420 | 327,7 | 2,586 |
| Zircaloy (revestimento) | 6 579 | 314,5 | 15,61 |

Procedimento: renomear o material padrão (*Al*) em `Continua > [contínuo] > Models > Solid` e editar
`Material Properties > Density / Specific Heat / Thermal Conductivity > Constant`.

> Para aço em feixes tubulares a ~250–350 °C: aço carbono k ≈ 40–45 W/m·K, inox austenítico
> k ≈ 18–20 W/m·K. Com a parede fina, constante basta — a queda de temperatura no metal é pequena.

## 4. Fases e modelos de fase

Duas fases criadas em `Coolant > Models > Multiphase > Phases`: **Liquid** e **Vapor**. Mesma receita
para as duas:

1. Material: *Liquid* (ou *Gas*) → RANS entra sozinho.
2. **Desligar** *Auto-select recommended models* → escolher **K-Epsilon → Standard K-Epsilon**
   (Wall Distance vem junto).
3. **Religar** *Auto-select* → **High y+ Wall Treatment** (automático) · **Constant Density** ·
   **Segregated Fluid Temperature**.
4. Renomear o material para `H2O (l)` / `H2O (g)`.

> ⚠️ **Corrigido em 13/10/2026 (após o tutorial 02).** Aqui o tutorial usa **High y+ Wall
> Treatment**, mas isso **não é exigência do RPI** — o tutorial 02 roda ebulição na parede com
> **Two-Layer All y+**. O que vale: com High y+, a primeira célula tem de ficar na camada log
> (y+ ≳ 30) — **não refinar demais junto à parede**; com All y+, há mais liberdade. Em qualquer caso,
> **testar a sensibilidade do superaquecimento de parede ao tamanho da 1ª célula** (o RPI usa a
> temperatura do líquido junto à parede). Ver `02_Eulerian_Wall_Boiling.md` §4.

### O truque do calor latente
As propriedades são **constantes na saturação**, e o calor latente entra pela diferença dos
**Heat of Formation** das duas fases, com **Standard State Temperature = Tsat** nas duas:

| a 71,7 bar | Líquido | Vapor |
|---|---|---|
| Density | 745,65 kg/m³ | 37,52 kg/m³ |
| Dynamic Viscosity | 9,253×10⁻⁵ Pa·s | 1,9034×10⁻⁵ Pa·s |
| **Heat of Formation** | **1 276 100 J/kg** | **2 770 300 J/kg** |
| Specific Heat | 5 310 J/kg·K | 5 440 J/kg·K |
| Standard State Temperature | 560,65 K | 560,65 K |
| Thermal Conductivity | 0,574 W/m·K | 0,06514 W/m·K |

h_v − h_l = **1 494 kJ/kg** = calor latente a 71,7 bar. Os "calores de formação" são as **entalpias
de saturação IAPWS** — verificamos com CoolProp (erro < 0,02 %).

**Ferramenta:** [`props_agua_saturada.py`](props_agua_saturada.py) gera essa tabela em qualquer
pressão (`python3 props_agua_saturada.py 30 40`). Exemplos:

| pressão | Tsat | h_l (Heat of Formation) | h_v (Heat of Formation) | h_fg | σ |
|---|---|---|---|---|---|
| 30 bar a | 507,00 K | 1 008 345 J/kg | 2 803 153 J/kg | 1 795 kJ/kg | 0,02962 N/m |
| 40 bar a | 523,50 K | 1 087 492 J/kg | 2 800 821 J/kg | 1 713 kJ/kg | 0,02575 N/m |

> O tutorial usa ρ_l = 745,65 e cp_l = 5 310, diferentes da saturação exata (736,7 e 5 437). **Explicado
> pelo tutorial 02 (§6):** ρ, μ, k na **temperatura média** entre entrada (551,55 K) e Tsat, e cp
> **secante** `(h_l,sat − h_l,in)/(Tsat − T_in)`. Conferido: 745,83 kg/m³ e 5 332 J/kg·K. Para ebulição
> saturada (sem sub-resfriamento), use os valores de saturação; com entrada sub-resfriada,
> `python3 props_agua_saturada.py <p> --tin <T_in>`.

## 5. Interação entre fases

`Coolant > Models > Multiphase Interaction > Phase Interactions > New > Liquid > Vapor
(Continuous-Dispersed)` — **líquido contínuo, vapor disperso** (bolhas). Renomear para
*Liquid Vapor Interface*.

| modelo | o que faz |
|---|---|
| **Turbulent Dispersion Force** (+ Virtual Mass, automático) | espalha as bolhas pela turbulência |
| **Interphase Mass Transfer → Boiling/Condensation** | troca de massa líquido↔vapor no volume |
| **Wall Boiling** (+ Wall Bubble Nucleation e Wall Transient Conduction/Quenching, automáticos) | partição de fluxo na parede (RPI): convecção + evaporação + quenching |

Ajustes:

| nó | valor | por quê |
|---|---|---|
| Interaction Length Scale → Method | **Kurul-Podowski** | diâmetro de bolha função do sub-resfriamento local |
| Boiling Mass Transfer Rate → Continuous Phase Nusselt Number | **Ranz-Marshall** | troca de calor líquido→interface da bolha (interface na Tsat) |
| Multiphase Material → Boiling Temperature | 560,65 K | Tsat da pressão do sistema |
| Multiphase Material → Surface Tension | 0,01725 N/m | |
| Drag Force → Drag Coefficient | **Tomiyama** | bolha pequena, baixa viscosidade |

## 6. Interface sólido–sólido: resistência de contato

`Interfaces > Fuel-Cladding > Physics Values > Contact Resistance` = **1,761×10⁻⁴ m²·K/W** (constante).
Equivale a um coeficiente de **~5 680 W/m²·K** através da folga.

> 💡 **Mesma técnica para incrustação (fouling)** na interface fluido–tubo. Ordem de grandeza: fatores
> TEMA para óleos e resíduos pesados ficam em **~10⁻³ m²·K/W** — 5 a 10× a folga do tutorial, e
> comparáveis à própria resistência do filme de óleo. A incrustação entra **sem malhar a camada**.

## 7. Fonte de calor e condições de contorno

| onde | o quê | valor |
|---|---|---|
| Região do combustível | Energy Source Option → **Volumetric Heat Source** | 2,26412×10⁸ W/m³ |
| Entrada — as duas fases | Velocity Magnitude | 2,0076 m/s (mesma nas duas) |
| Entrada | Volume Fraction | líquido **0,9999** · vapor **1×10⁻⁴** |
| Entrada | Static Temperature | líquido **551,55 K** (9,1 K sub-resfriado) · vapor **560,65 K** (Tsat) |
| Entrada e saída | Turbulence Intensity / Viscosity Ratio | 0,05 / **400** (líquido) · 0,05 / **200** (vapor) |
| Saída | Backflow Specification > Scalars | **Extrapolated** |

Fluxo mássico na entrada: G = 745,65 × 2,0076 ≈ **1 500 kg/m²·s**.

**Lições:**
- **Fração de vapor nunca zero** na entrada (semente de 10⁻⁴): estabilidade numérica do EMP.
- **Vapor entra na Tsat**, o líquido sub-resfriado — cada fase com sua temperatura.
- **Backflow extrapolado na saída:** a fração volumétrica de um eventual refluxo vem do interior, não
  é imposta.
- Em equipamento onde o calor vem de **outro fluido** (trocador), a fonte não é volumétrica nem fluxo
  fixo: é a região do fluido quente com sua própria entrada (vazão + temperatura).
- Onde o vapor **sai por uma superfície livre** (piscina, kettle), a saída não é um *pressure outlet*
  comum: o EMP tem condição de **degaseificação** — ver o tutorial *Eulerian: Aeration Tank Degassing*.

## 8. Condições iniciais e valores de referência

- **Condições iniciais = condições de entrada** em cada fase (velocidade, fração, temperatura,
  turbulência).
- No **axissimétrico do STAR o eixo é x**: velocidade `[2,0076, 0]` e **gravidade `[−9,81, 0]`**.
- `Reference Values`: **Reference Pressure = 7 170 000 Pa** (pressão absoluta do sistema) ·
  **Reference Density = 745,65 kg/m³** (densidade do **líquido**).

> 📌 **Da nossa experiência (ciclone Valgroup):** *Reference Pressure* e *Reference Density* são os
> dois campos mais fáceis de esquecer no default — e a pressão de referência errada desloca todo o
> campo de pressão absoluta.

## 9. Visualização

Cena dupla (*Dual Scene*): **temperatura** nos sólidos (escala fixa 550–1 350 K) + **fração
volumétrica de vapor** no fluido, monitoráveis durante a solução. Para geometria muito esbelta (1 m ×
milímetros), aplicar **Transform → Resize Domain** em todos os displayers.

> Útil também para tubos longos de trocador (6 m de comprimento × poucos centímetros de diâmetro).

---

## 10. ⚠️ Limites ao transpor para outros equipamentos

| tutorial | caso típico de feixe com ebulição externa (ex.: kettle) |
|---|---|
| ebulição **sub-resfriada em escoamento forçado** num canal | ebulição **saturada**, circulação **natural** em torno do feixe |
| fluxo imposto de **525 kW/m²** | fluxo de **dezenas de kW/m²**, vindo de um **fluido quente** no tubo (não um fluxo fixo) |
| fração de vazio moderada → **bolhas dispersas** | fração de vazio **alta** no feixe → bolhas grandes / *churn*: Tomiyama e Kurul-Podowski saem do domínio de validade |
| 2D axissimétrico (tubo vertical) | tubo **horizontal** parcialmente coberto: **não é axissimétrico** — o 2D natural é a **seção transversal do feixe** |

Consequências de setup:
- a fonte de calor deve ser o **fluido do lado dos tubos** (região fluida própria) ou uma condição de
  convecção com a temperatura do fluido quente — não um *heat flux* constante;
- para fração de vazio alta, olhar o tutorial **Eulerian Multiple Flow Regimes (PWR)**, que trata a
  transição de regimes;
- onde a água de alimentação entra **sub-resfriada**, o sub-resfriamento local volta a importar
  (Kurul-Podowski faz sentido ali).
