# 13 — Quantificação analítica (a álgebra por trás dos gráficos)

> O "porquê" físico que sustenta os gráficos Sim 1/Sim 2 × CSTR. Tudo sai de **uma** equação de balanço.

## 1. Equação-mãe (balanço de energia no tanque)
Paredes adiabáticas → o tanque só troca calor pelo chiller (pega ṁ na sucção a `T_sucção`, devolve a `T_ret=−5 °C`):

```
M·cp·dT/dt = ṁ·cp·(T_ret − T_sucção)      →      dT/dt = −(1/τ)·(T_sucção + 5)
```

com **τ = M/ṁ = V/Q = 3,51/(12/3600) = 1053 s** (tempo de residência). **`T_sucção` é o único grau de liberdade.**
*(A recirc é adiabática → não entra: injeta no topo a mesma T que pega no fundo, `ṁ·cp·(T_ret−T_capta)≈0`.)*

## 2. Benchmark CSTR (mistura perfeita) → `T_sucção = T_bulk`
```
dT/dt = −(1/τ)(T+5)      →      T(t) = −5 + 10·e^(−t/τ)
```
Decaimento **exponencial**. 99% resfriado (`T=−4,9 °C`): `t = τ·ln(100) = 4,605·τ = 4849 s`.
- **Duty inicial:** `Q₀ = ṁ·cp·10 = 3,107·3652·10 = 113,5 kW` (vs −115 kW medido ✔).
- **Energia total:** `E = M·cp·10 = 932·3,51·3652·10 = 119,5 MJ` — **igual nos 3 casos** (conservação); muda só o ritmo.

## 3. Os 3 regimes (tudo é `T_sucção` vs `T_bulk`)
| Caso | Mecanismo | `T_sucção` vs `T_bulk` | −4,9 °C | ×τ |
|---|---|---|---|---|
| **Sim 1** (sucção 1,35 m) | **deslocamento** (frio no fundo, puxa quente do topo) | `>` bulk | **3040 s** | 2,9 τ |
| CSTR ideal | mistura perfeita | `=` bulk | 4849 s | 4,61 τ |
| **Sim 2** (+ recirc) | **mistura** (recirc homogeneíza) | `≈` bulk | **4930 s** | 4,68 τ |
| Baseline (sucção 0,85 m) | **curto-circuito** (re-aspira o frio do fundo) | `<` bulk | ~7500 s | ~7 τ |

- **Sim 1 bate o CSTR (−37%)** porque a estratificação estável mantém a sucção quente → `(T_sucção+5)` alto → duty alto.
  Piso teórico do deslocamento ≈ **1 τ** (pistão).
- **Sim 2 assenta no CSTR** porque a recirc destrói a estratificação → `T_sucção→T_bulk`. Joga fora a eficiência do deslocamento.
- **Baseline é pior que o CSTR** porque a sucção baixa re-aspira o frio (`T_sucção<T_bulk` → duty mínimo).

## 4. O "Δ em mC" (prova da recirc adiabática)
`mC = milicelsius = 0,001 °C` (zoom de 1000× — em °C a linha pareceria zero reto).
Gráfico: `Δ = T_retorno − T_captação`. Adiabático ⇒ `Δ = 0` (devolve no topo a mesma T do fundo).
- **Medido:** média **+6,8 mC**, picos ±461 mC só nas oscilações iniciais (que amortecem).
- O **+6,8 mC não é vazamento** — é o **atraso de 1 passo de tempo**: `T_retorno(t) = T_capta(t−Δt)`, um tiquinho mais quente na descida.
- **Impacto:** `E_recirc = ṁ·cp·∫Δ dt = +0,38 MJ = +0,3 %` dos 119,5 MJ → **desprezível** → recirc **adiabática** ✔.

## 5. Versão pro cliente (sem EDO)
> O resfriamento segue uma **lei exponencial** com constante de tempo **τ = volume/vazão = 1053 s**. A **mistura
> perfeita** é o benchmark: 99% em **~4850 s**. A **Sim 1 supera** isso (**3040 s**) — o frio no fundo e a sucção
> alta criam um **deslocamento**. A **Sim 2 (recirc) mistura** e por isso **volta ao benchmark** (**4930 s**).
> **A recirc troca velocidade por uniformidade** — e o CFD quantifica os dois lados.

## Fontes numéricas
`figuras/tres_casos_vs_cstr.png` · `figuras/sim2_adiabatica.png` · dados em `12_verificacao_transiente.md`.
