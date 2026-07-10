# Achado: steady vs transiente no Aerador (investigação motivada pelo Marcus)

O Marcus pediu para rodar em regime permanente (steady), acoplando os dois tanques,
apoiado no tutorial da Siemens (Hibiki's Bubble Column, que roda EMP+S-Gamma steady).
Testamos com rigor. Resultado:

## Método
- Start frio steady → **diverge** (blow-up em ~60 iter) — sensível a chute inicial.
- Steady inicializado do **transiente já convergido** → **converge** (oscilação amortecida).
  Depois estendemos a física multifásica para reator+MRF (domínio todo multifásico).

## Resultados (caso 3, 3 kgf/cm²)
### Reator — steady OK
- Torque steady convergido: **-369,9 N·m** (osc. ±1,7). Validado: -355,7 (MRF) / -374 (transiente).
- Dentro de ~4% → **o reator pode ser steady** (Np/Nq/torque confiáveis).

### Aerador — steady ERRADO
| Métrica | Transiente (correto) | Steady (errado) |
|---|---|---|
| SMD médio | 2,53 mm | 1,22 mm |
| moda | 1,90 mm | 1,10 mm |
| D10 | 1,43 mm | 0,13 mm |
| D50 | 2,32 mm | 0,85 mm |
| D90 | 3,57 mm | 2,81 mm |
| **<200µm (flotável)** | **~0%** | **8,6%** |

- O steady dá bolha **~2× menor** e prevê **8,6% de fração flotável (FALSO)** — o transiente dá ~0%.
- Figura: `../apresentacao/comp_transiente_vs_steady.png`.

## Por quê
Breakup/coalescência são inerentemente transientes. O steady converge um campo de S-Gamma que
não captura o crescimento temporal da bolha — fica preso no tamanho de formação (fino) e não
coalesce até ~2,5 mm como o transiente. Resultado: bolha fina demais e flotável falso.

## Conclusão
**Reator → steady OK. Aerador → transiente OBRIGATÓRIO.** O steady no aerador daria ao cliente a
conclusão errada (que a aeração funciona). Metodologia original confirmada por teste direto.

## Desacoplamento (bônus da mesma investigação)
Com o domínio todo multifásico, o ar continua **confinado às lanças** (cena de VF) e o torque do
reator não muda → o ar não chega ao reator. Desacoplamento demonstrado, não assumido.
