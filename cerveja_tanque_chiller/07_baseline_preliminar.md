# 07 — Baseline do estudo PRELIMINAR (para comparar a estratificação)

> Extraído da apresentação já entregue ao cliente (`Cerveja_1.pdf`). São os números da **estratificação
> observada** — a referência contra a qual o novo cenário (sucção 1,35 m ± recirc) será comparado.

## Config do preliminar (o que muda pro novo cenário)
- **Frio entra POR BAIXO nos dois** (retorno no fundo) — **config CONSISTENTE** (Gabriel, que rodou, confirmou;
  o slide dizia "teto" mas a rodada foi por baixo). ✅ **Ponto de comparação válido.**
- **O que MUDA do preliminar p/ o novo:** (1) o **tanque** (GRANDE ~69 m³ / z≈5,3 m → **TAG 3.500 L, 1,53 m**);
  (2) a **altura da saída pro chiller (sucção)**.
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

## Como usar na comparação
- O preliminar é a **evidência do problema** (estratificação severa: ΔT ~7,5 °C, resfriamento 9× mais lento).
  É a "estratificação observada" que o cliente cita. **Config consistente (frio por baixo)** → comparação válida.
- **Nota:** entre preliminar e novo mudam **duas coisas** (tanque + altura da sucção). Então o novo mostra o
  efeito **combinado** dos dois. Se quiser isolar SÓ o efeito da altura da sucção, roda também o TAG 3.500 L com
  a sucção antiga (0,85 m) → baseline do mesmo tanque → Sim 1 (1,35 m) → Sim 2 (+recirc). O `gen_sim_steps.py`
  tem `Z_SUC_BASE=850` pronto. *(Opcional — o cliente pode aceitar a comparação direta com o preliminar.)*
- **Métrica:** **ΔT topo–fundo no tempo** (monitor `Delta_T_Estratificacao`) + **tempo até homogeneizar / −5 °C**.
  E lembra: **T_topo é a referência** (zona estagnada), não o T_outlet (que engana).

## Dado reutilizável
**ρ(T) = 1082,88 − 0,55·T [kg/m³, T em K]** — confirma que é esse o Polynomial Density no teu Sim 1 (deve ser,
veio do preliminar).
