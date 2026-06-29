# Propriedades — LNG binário (Metano CH₄ + Etano C₂H₆)

> Para o rollover multicomponente. Metano e etano EXISTEM no banco do Star-CCM+
> (Material Databases > Standard) — provavelmente não precisaremos digitar tudo,
> mas estas são as referências para sanity-check. Estado: ~111 K (LNG saturado).
> Valores de referência (~NIST). Atualizado: 2026-06-29.

---

## Metano (CH₄) — componente LEVE / volátil
Líquido saturado @ 111,67 K (NBP, 1 atm):
| Propriedade | Valor | Unidade |
|---|---|---|
| Massa molar | 16,043 | kg/kmol |
| Densidade líq. | 422,6 | kg/m³ |
| Viscosidade líq. | 1,17e-4 | Pa·s |
| cp líq. | 3480 | J/(kg·K) |
| Condutividade líq. | 0,186 | W/(m·K) |
| Calor latente (NBP) | 510 | kJ/kg |
| Tensão superficial | 0,0138 | N/m |
| T crítica / P crítica | 190,56 K / 4,599 MPa | |
| Psat @ 111,67 K | 101,325 | kPa (=1 atm, NBP) |

## Etano (C₂H₆) — componente PESADO / pouco volátil (a âncora)
Líquido subresfriado @ ~111 K (NBP = 184,55 K — bem acima):
| Propriedade | Valor | Unidade |
|---|---|---|
| Massa molar | 30,069 | kg/kmol |
| Densidade líq. (~111 K) | ~650 | kg/m³ (≈1,5× metano → "pesado") |
| Viscosidade líq. | ~6e-4 | Pa·s (frio, viscoso) |
| cp líq. | ~2300 | J/(kg·K) |
| Condutividade líq. | ~0,25 | W/(m·K) |
| Calor latente (NBP) | 489 | kJ/kg |
| T crítica / P crítica | 305,32 K / 4,872 MPa | |
| Psat @ ~111 K | ~0,01–0,1 | kPa (quase NÃO evapora → não-volátil) |

## Pressão de saturação — Antoine (log₁₀ P[bar] = A − B/(T[K]+C))
| Componente | A | B | C | Validade |
|---|---|---|---|---|
| Metano | 3,9895 | 443,028 | −0,49 | 91–190 K |
| Etano | 4,50706 | 791,3 | −6,422 | 131–200 K (extrapolar p/ 111 K → Psat ínfima) |

(O banco do Star já traz curvas de p_sat; usar as embutidas se disponíveis.)

---

## Por que essa dupla funciona para o rollover
- **Metano:** volátil a 111 K (evapora) → controla o BOG e a "weathering".
- **Etano:** ~1,5× mais denso e quase não evapora a 111 K → é a **âncora compositional**
  que mantém a camada de baixo densa enquanto ela aquece (o que faltava no térmico puro).
- Camada de fundo com mais etano = densa e estável; ao aquecer + metano evaporar
  preferencialmente, a densidade cruza → **flip** (La Spezia).

## Composições das camadas (representativas)
| Camada | CH₄ (mol) | C₂H₆ (mol) |
|---|---|---|
| Topo (leve) | 95% | 5% |
| Fundo (pesada) | 88% | 12% |

## Densidade de mistura
ρ_mix = f(T, x) — usar regra de mistura do Star (ou Peng-Robinson se disponível).
Mais etano → mais densa. Aquecer → menos densa. Os dois efeitos competem → rollover.
