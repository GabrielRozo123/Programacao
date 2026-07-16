# 06 — Setup passo-a-passo no STAR (Sim 1 e Sim 2)

> Você já tem a física do processo montada; este guia foca no que é **novo/específico** das 2 rodadas:
> importar a geometria, montar os **loops de BC** (chiller e recirc) e os **monitores de estratificação**.
> Geometrias: `geometria/cerveja_sim1_fluido.step` e `..._sim2_fluido.step` (DN150, importar em **mm**).

## A. Física (checar — você já deve ter)
- **Monofásico** (solução hidroalcoólica 70/30, ρ=932,65 kg/m³), **Implicit Unsteady** (transiente).
- **Gravity ON** + **densidade dependente da T** (Boussinesq se ΔT pequeno, ou ρ(T) tabela) — **é o motor
  da estratificação**. Sem isso, não estratifica.
- **Energy:** Segregated Fluid Temperature. Turbulência: baixo-Re com **termo de empuxo em k** (ou laminar,
  ver Rayleigh). Paredes do tanque: adiabáticas ou com perda (a combinar).
- **Condição inicial:** óleo/solução uniforme a **+5 °C**.

## B. SIM 1 — só o loop do chiller (comece por aqui)
Bocais: `succao_chiller` (1,35 m) e `retorno_chiller` (fundo). O chiller **remove calor**: pega a solução na
sucção, resfria, e devolve a **−5 °C**.

1. **Retorno do chiller (fundo)** → **Mass Flow Inlet**
   - ṁ = ρ·Q = 932,65 × (12/3600) = **3,11 kg/s** · **Static Temperature = −5 °C** (fixo).
2. **Sucção do chiller (1,35 m)** → **Velocity Inlet apontando pra FORA** (extração), v = Q/A = **0,19 m/s**
   (DN150). Fecha o balanço de massa (3,11 entra no fundo, 3,11 sai a 1,35 m). Como sai, usa a T de montante.
3. **Controle "chiller desliga a −5 °C":** monitor da **T média do tanque** (Volume Average); quando atingir
   −5 °C, zera as vazões (via field function condicional na ṁ, ou para a rodada). *(Combinar o critério.)*
4. **Rodar transiente** até estabilizar / atingir a meta.

## C. SIM 2 — adiciona o loop de recirculação (é onde te oriento ao vivo)
Mantém o loop do chiller (B) **e** adiciona a bomba de recirc (12 m³/h, **soma** — 2 bombas). Bocais:
`recirc_captacao` (fundo) e `recirc_retorno` (topo). **Loop ADIABÁTICO** (a bomba não troca calor):

1. **Recirc retorno (topo)** → **Mass Flow Inlet**, ṁ = 3,11 kg/s, **Static Temperature = T da captação** ↓↓
2. **Recirc captação (fundo)** → **Velocity Inlet pra FORA**, 0,19 m/s (extrai).
3. **O acoplamento de energia (o pulo do gato):**
   - **Report** = *Mass-Flow-Averaged Temperature* na superfície `recirc_captacao` →
   - vira **Field Function** →
   - usa essa field function como a **Static Temperature** do `recirc_retorno`.
   - Assim a água recirculada carrega a **própria T** (fundo→topo) → energia conservada. Sem isso, injetaria
     uma T arbitrária e o balanço térmico furaria.
4. Os **dois pares de BC operam juntos** — nada especial na malha.

> ⚠️ Diferença entre os loops: **chiller = remove calor** (retorno a −5 °C fixo); **recirc = adiabático**
> (retorno na T da captação). É essa a única diferença de setup entre eles.

## D. Monitores / pós (a MÉTRICA da estratificação)
- **ΔT topo–fundo no tempo:** dois *Probes* (ou Volume Average de fatias) — um perto do **topo** (~1,5 m),
  um perto do **fundo** (~0,1 m) → plotar `T_topo − T_fundo` vs tempo. **É o número que decide.**
- **Perfil vertical de T** (Line Probe no eixo, do fundo ao topo) em instantes.
- **Cena de temperatura** (plano vertical) — mostra visualmente a estratificação e o efeito do bocal a 1,35 m.
- (Opcional) tempo até **homogeneizar** (ΔT < critério).

## E. O que o estudo responde ao cliente
- **Sim 1:** subir a sucção (0,85→1,35 m) **reduz a estratificação?** (compara ΔT topo-fundo com o preliminar.)
- **Sim 2:** a **recirc fundo→topo** homogeneíza mais? (compara ΔT topo-fundo Sim 1 × Sim 2.)

## Pendências que não bloqueiam
- Altura exata dos bocais da recirc (adotado fundo ~0,1 m / topo ~1,5 m).
- Confirmar condições de processo (pergunta 5) e o formato preferido da métrica (pergunta 6).
