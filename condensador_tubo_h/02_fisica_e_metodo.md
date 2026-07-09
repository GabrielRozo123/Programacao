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

## Modelo de mudança de fase — condensação
Assim como o Rohsenow precisa de coeficientes empíricos (C_qw, n_p) de uma tabela superfície-fluido,
o modelo de condensação terá o **seu** parâmetro — escolhê-lo/justificá-lo é o cerne de "formular o
h". Famílias esperadas nas opções do STAR (a classificar quando a lista chegar — `06_pendencias.md`):
1. **Interfacial / limitada por transferência de calor** — a interface fica presa em T_sat; o `h`
   **emerge** do campo térmico resolvido. Mais honesta para medir `h`.
2. **Coeficiente (tipo Lee):** ṁ = C·α·ρ·(T_sat−T)/T_sat — tem **C de ajuste** a calibrar (senão
   domina artificialmente); calibração feita justamente pela validação vs Nusselt.
3. **Filme fino / parede (Fluid Film condensation):** não resolve o filme → carta para o **banco
   de tubos** (Fase 3).

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
