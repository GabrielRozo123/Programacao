# 07 — Baseline do estudo PRELIMINAR (para comparar a estratificação)

> Extraído da apresentação já entregue ao cliente (`Cerveja_1.pdf`). São os números da **estratificação
> observada** — a referência contra a qual o novo cenário (sucção 1,35 m ± recirc) será comparado.

## ⚠️ Config do preliminar (atenção — NÃO é idêntica ao novo cenário)
- **Tanque:** o **GRANDE** (~69 m³, altura de líquido até z≈5,3 m). *(O novo é o TAG 3.500 L, 1,53 m.)*
- **Inlet (frio −5 °C) no TETO** · **Outlet no ápice do cone** (fundo). *(O novo: retorno no fundo, sucção a 1,35 m.)*
- ρ(T) = **1082,88 − 0,55·T** [kg/m³, T em K] · Gravidade −9,81 z · Paredes adiabáticas · **T_inicial +5 °C** ·
  Δt=1 s · k-ε Realizable.

## Resultados do preliminar (a "estratificação observada")
| Métrica | Valor |
|---|---|
| **Estratificação (ΔT topo–fundo)** | **~7,5 °C** após 20 h (fundo z≈0,5m **−4 °C** · topo z≈5,3m **+3,5 °C**) |
| Padrão | **Filling-box / warm lid** — o frio (−5°C, denso) **afunda** e preenche de baixo p/ cima; camada quente **estagnada no topo** |
| Curto-circuito | **NÃO** (o outlet retorna frio porque a base esfria primeiro, não por bypass) |
| Eficiência | **~9× mais lento** que CSTR: T_bulk = −0,5 °C após 20 h (vs −4,7 °C do modelo bem-misturado, τ=5,8 h) |
| Tempo p/ −5 °C | **>40 h** (extrapolado) |
| Sensor de controle | **T_outlet engana** (−4,3 °C ≠ bulk −0,5 °C). **T_topo é a referência correta** (zona estagnada, última a esfriar) |

## Como usar na comparação (honestamente)
- O preliminar é a **evidência do problema** (estratificação severa, resfriamento lento). É a referência que
  o cliente chama de "estratificação observada".
- ⚠️ **Não é comparação 1:1** — o preliminar é o tanque **grande** (5,3 m) e config de bocais **diferente**; o
  ΔT absoluto (7,5 °C) não transfere direto pro tanque pequeno (1,53 m, menos altura pra estratificar).
- **Comparação limpa (recomendado):** rodar também o **TAG 3.500 L com a sucção ANTIGA (0,85 m)** como baseline
  do mesmo tanque → depois **Sim 1 (1,35 m)** → **Sim 2 (+recirc)**. Assim mede-se a **redução real** na mesma
  geometria. *(O `gen_sim_steps.py` tem `Z_SUC_BASE=850` pronto pra gerar esse baseline.)*
- **Métrica de comparação:** **ΔT topo–fundo no tempo** (o teu monitor `Delta_T_Estratificacao`) + **tempo
  até homogeneizar / atingir −5 °C**.

## Dado reutilizável
**ρ(T) = 1082,88 − 0,55·T [kg/m³, T em K]** — confirma que é esse o Polynomial Density no teu Sim 1 (deve ser,
veio do preliminar).
