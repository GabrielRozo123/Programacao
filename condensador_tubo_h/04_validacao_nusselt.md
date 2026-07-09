# 04 — Validação: teoria de Nusselt (tubo horizontal)

## O `h` analítico (Nusselt, 1916 — condensação filmwise laminar)
Para condensação filmwise laminar de vapor saturado num **tubo horizontal** de diâmetro D, com a
parede a T_parede e o vapor a T_sat (ΔT = T_sat − T_parede):

```
h_méd = 0,728 · [ ρ_l (ρ_l − ρ_v) g h_fg k_l³ / ( μ_l D ΔT ) ]^(1/4)
```

- `h_fg` calor latente; `k_l, μ_l, ρ_l` propriedades do líquido (avaliar na T de filme
  T_f = (T_sat + T_parede)/2); `ρ_v` densidade do vapor; `g` gravidade.
- **Correção de sub-resfriamento do filme** (Rohsenow): usar `h_fg' = h_fg + 0,68 c_pl ΔT`.
- `h_local(θ)` varia com a posição angular θ (fino no topo, engrossa até desprender embaixo):
  o filme é mais fino no topo (h maior) e mais espesso na base (h menor).

## Como validamos
1. Rodar o **tubo limpo** (vapor puro) no ponto de operação.
2. Extrair `h_méd` (STAR "Heat Transfer Coefficient" com T_ref = T_sat) e `h(θ)`.
3. Comparar com o Nusselt acima (número fechado) e com o perfil `h(θ)` esperado.
4. **Critério:** se `h_méd,CFD` bate o Nusselt dentro de ~5–15% e o perfil `h(θ)` reproduz a
   forma (topo > base), o modelo (e o coeficiente do modelo de condensação) está **calibrado e
   validado**. Só então avançamos para NCG.

## Regime — checar antes
- Nusselt vale para filme **laminar**. Verificar o Reynolds do filme `Re_δ = 4 Γ/μ_l` (Γ = vazão
  de condensado por unidade de comprimento). Se laminar (Re_δ < ~1800), Nusselt aplica direto;
  se não, usar correlação turbulenta de filme.

## Âncoras de literatura (a consolidar na revisão)
- **Nusselt (1916)** — teoria filmwise (tubo horizontal e placa vertical).
- **Rohsenow** — correção de sub-resfriamento do h_fg.
- Dados experimentais de vapor condensando em tubo horizontal (a fixar na revisão).
- **NCG (Fase 2):** Rose; Dehbi; Sparrow & Minkowycz — degradação do `h` com gás não-condensável.
