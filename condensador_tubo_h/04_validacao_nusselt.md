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

## Alvo numérico — ponto de operação FIXADO (T_sat=100°C, D=25,4mm)
Água a T_f=87,5°C (ρl=967, μl=3,24e-4, kl=0,673, cpl=4205); vapor a 100°C (ρv=0,598, hfg=2257 kJ/kg):

| ΔT | h_Nusselt | q | Re_filme |
|---|---|---|---|
| 10 K | 12,2 kW/m²·K | 122 kW/m² | 52 (laminar) |
| **25 K** | **9,7 kW/m²·K** | **243 kW/m²** | 103 (laminar) |
| 30 K | 9,3 kW/m²·K | 279 kW/m² | 117 (laminar) |

**Caso-base: ΔT=25 K → h_Nusselt ≈ 9,7 kW/m²·K.** Re de filme laminar (Nusselt vale).

**Achado (importante p/ o flagship):** o experimental (MDPI, vapor atmosférico em tubo horizontal)
deu **~5,5 kW/m²·K** — bem abaixo do Nusselt (~9,7). Essa diferença é, muito provavelmente,
**assinatura de NCG** (condensadores reais rodam abaixo de Nusselt por causa do ar). Logo:
- **CFD vapor puro** deve reproduzir **Nusselt ~9,7** (valida o modelo);
- **CFD + NCG** deve **cair rumo aos ~5,5** experimentais (quantifica a degradação — Fase 2).

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
