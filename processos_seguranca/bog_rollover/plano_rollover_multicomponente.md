# Plano — Rollover Multicomponente LNG (La Spezia fiel)

> A física VERDADEIRA do rollover do La Spezia: composição-dependente.
> Caminho B "de verdade". Escala de bancada (6,76 L), mas com LNG multicomponente.
> Atualizado: 2026-06-29.

---

## Por que multicomponente

O rollover do La Spezia é dirigido por **COMPOSIÇÃO**: a camada de baixo é LNG mais pesado
(mais etano/propano/N₂), fica densa e **permanece estável embaixo mesmo aquecendo**, até a
densidade cruzar → flip abrupto. O análogo puramente térmico (N₂) NÃO consegue isso porque
aquecer reduz densidade e desestabiliza (Rayleigh-Bénard). A composição é a "âncora" que
mantém o fundo denso durante o atraso → e o flip vem quando ela é vencida.

## Mudança de fluido e temperatura
- LNG = **metano-dominado** → temperatura de operação **~111 K** (CH₄ satura a 111,7 K @ 1 atm),
  NÃO 77 K (isso era N₂).
- Componentes (binário representativo): **Metano (CH₄, leve/volátil) + Etano (C₂H₆, pesado/pouco volátil)**.
  - Opcional incluir N₂ depois (driver de alguns rollovers reais).

## Composição das camadas (representativa; refinar com dados se disponíveis)
| Camada | CH₄ | C₂H₆ | Característica |
|---|---|---|---|
| Topo (leve) | ~95% mol | ~5% mol | menos densa (estável em cima) |
| Fundo (pesada) | ~88% mol | ~12% mol | mais densa (âncora compositional) |

A diferença de etano (~7% mol) dá a diferença de densidade inicial (~%) que estabiliza.

## Modelos no Star-CCM+
- Fases VOF: **líquida multicomponente** (CH₄+C₂H₆) + **vapor multicomponente**.
- Phase Interaction: **Evaporation/Condensation** (Raoult's law) — agora correto, pois exige
  fases multicomponente! (era o que rejeitamos para N₂ puro). Saturation Pressure por
  componente via **Antoine** ou **Wagner**.
- **Multi-Component** material nas fases (frações mássicas/molares de CH₄ e C₂H₆).
- Densidade da mistura: f(T, composição) — regra de mistura ou EOS (Peng-Robinson se disponível).
- Transporte de espécies: resolvido por fase.
- Turbulência: k-ε Realizable Two-Layer + Buoyancy Production = Thermal Stratification (mantém).
- Min Allowable Temperature: **50 K** (mantém, operação 111 K bem acima).

## Propriedades necessárias (a montar)
Metano (CH₄) líquido @ ~111 K:
- M = 16,04 kg/kmol ; ρ ≈ 422 kg/m³ ; Lv ≈ 510 kJ/kg ; T_sat(1atm)=111,7 K
Etano (C₂H₆) líquido @ ~111 K (subresfriado; NBP=184,6 K):
- M = 30,07 kg/kmol ; ρ ≈ 640 kg/m³ (mais denso → "pesado") ; pouco volátil a 111 K
Pressões de saturação: Antoine/Wagner para CH₄ e C₂H₆ (CH₄ volátil, C₂H₆ quase não evapora a 111 K).
[Refinar todos os valores com tabela NIST ao montar.]

## Mecanismo esperado
1. Estratificação estável: fundo denso (mais etano), topo leve. Atraso longo.
2. Heat leak aquece o fundo; densidade do fundo cai; metano evapora preferencialmente na
   interface entre camadas → composição do fundo muda.
3. Densidades cruzam → **overturn abrupto** → V_max dispara, T/composição homogeneízam,
   **surto de BOG** (pico de P_ullage). = La Spezia.

## Escopo (honesto)
Maior build do projeto: materiais novos (CH₄/C₂H₆ a 111 K), VLE multicomponente, espécies,
densidade de mistura. Geometria/malha/AMR/monitores reaproveitados. Construir passo a passo.

## Sequência
1. Trocar física p/ multicomponente; criar componentes CH₄ + C₂H₆ (líquido e vapor)
2. Propriedades (NIST) de cada componente; densidade de mistura f(T,x)
3. Phase Interaction: Evaporation/Condensation + p_sat (Antoine) por componente
4. IC: duas camadas por COMPOSIÇÃO (field function de fração) + T ~111 K
5. Heat flux (lateral, realista) ; manter turbulência + numérica estável
6. Monitores: V_max, P_ullage, T(z), e fração de C₂H₆(z) (a composição que inverte)
7. Rodar → caçar o flip compositional
