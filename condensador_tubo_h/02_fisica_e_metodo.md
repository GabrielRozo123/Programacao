# 02 — Física e método

## Modelos físicos (herdados do tutorial de ebulição, adaptados)
Base: o tutorial VOF "Boiler" do STAR-CCM+ (2D). Modelos:
- **2 fases:** H2O (líquido) + H2O (G) (vapor da base de dados STAR).
- **Two Dimensional**, **Implicit Unsteady**.
- **Multiphase → Volume of Fluid (VOF)** + **Segregated Flow**.
- **Turbulência:** k-ε Realizable Two-Layer, All y+ Wall Treatment.
- **Segregated Multiphase Temperature** (equação de energia — dá o campo de T).
- **Gravity** (motor do escoamento do filme de condensado).

## A virada ebulição → condensação
| Item | Ebulição (tutorial) | Condensação (nosso) |
|---|---|---|
| Parede térmica | quente, T_wall = 540 K > T_sat | **tubo frio, T_wall < T_sat** |
| Condição inicial VF | líquido [1,0] | **vapor [0,1]** |
| Fenômeno | vapor nasce na parede | **condensado nasce no tubo, escorre por gravidade** |
| Modelo de fase | VOF Boiling → **Rohsenow** (q″ de parede) | **modelo de condensação** (ver abaixo) |
| Resto (2D, VOF, energia, k-ε, gravidade, dt) | — | **igual** |

## Modelo de mudança de fase — condensação → **DECIDIDO: VOF Evaporation/Condensation**
Fonte: docs STAR "Modeling Evaporation and Condensation", "Setting Up...", "Model Reference (VOF)".

O STAR-CCM+ oferece o modelo **Evaporation/Condensation (VOF)** — condensação na **interface livre**
líquido-gás, e ele é ideal para o nosso caso:

- **Limitado por difusão / hidrodinâmico:** as fases ficam em **equilíbrio na interface** (interface
  na saturação) e a força motriz é a **difusão de espécie**. Ou seja, é da família "interfacial" — o
  **`h` emerge** do campo resolvido, **sem coeficiente de ajuste tipo Lee**. A "calibração" vira, na
  prática, **resolução de malha** do filme e da camada-limite (a validação vs Nusselt confirma isso,
  não um fator-fudge).
- **Multicomponente com espécie inerte NATIVA:** exige fases multicomponentes; o gás precisa de
  **≥1 componente inerte**. **Essa espécie inerte É o gás não-condensável (NCG).** Consequência
  enorme para o flagship:
  - **Fase 1 (validação):** fração de inerte mínima (~1e-3 a 1e-4; 0 também é válido) → condensação
    limitada só pela **condução no filme** = regime de Nusselt.
  - **Fase 2 (NCG):** aumentar a fração do inerte (ar) → o modelo captura a **resistência difusiva
    na interface** sozinho, degradando o `h`. **Mesmo modelo, só muda a fração de inerte.**
- **Equilíbrio por lei de Raoult**; **pressão de saturação** por Antoine / Wagner / Polinômio / Tabela;
  **calor latente** automático via *Heat of Formation*.
- **Under-Relaxation Factor** da taxa de evaporação (numérico) para estabilizar.
- Requer: VOF-VOF Phase Interaction, fase primária = líquido multicomponente, secundária = gás
  multicomponente.

**Extensão (Fase 3, banco de tubos):** modelo de **filme fino (Fluid Film condensation)** — não
resolve o filme, viabiliza o custo do banco/inundação.

## Definição do `h` — a decisão de método mais importante
Fonte: doc STAR "What Methods Are Available for Exchanging Heat Transfer Coefficients?"

O STAR oferece **quatro** definições de `h`, que diferem pela **temperatura de referência**:

| Field function STAR | T de referência | Observação |
|---|---|---|
| **Local Heat Transfer Coefficient** (padrão) | T da célula vizinha à parede (T_c) | **depende de malha** |
| **Specified y+ HTC** | T avaliada num y+ fixo | **mais independente de malha** |
| **Heat Transfer Coefficient** | **T de referência (bulk) definida pelo usuário** | h = q″/(T_ref − T_wall) |
| **Virtual Local HTC** | — (não requer modelo de energia) | aproximação |

### Nossa escolha
Para condensação, o `h` de engenharia é, por definição:
```
h  =  q″_parede / (T_sat − T_parede)
```
Logo usamos o field function **"Heat Transfer Coefficient" com a T de referência (bulk) = T_sat**.
Isso dá o `h` que o Nusselt prevê e que o projetista usa — e **evita** a dependência de malha do
"Local HTC" (cuja referência é a célula vizinha).
- **Cuidado (do próprio doc):** essa definição pode dar `h` negativo se T_ref for mal escolhida;
  com T_ref = T_sat e parede fria (T_wall < T_sat), o denominador é sempre positivo. OK.
- **Robustez de malha:** reportar também o **Specified y+ HTC** como verificação de independência
  de malha.

### Extração no pós-processamento
- `h(θ)` local: report de superfície do field function acima ao longo da circunferência do tubo.
- `h_méd`: `Q_total / (A_tubo · (T_sat − T_parede))` (report integral de fluxo de calor / área / ΔT).
