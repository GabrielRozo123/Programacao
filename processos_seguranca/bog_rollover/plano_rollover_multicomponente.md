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

## Condições iniciais (composição em FRAÇÃO MÁSSICA)
Conversão molar→mássica:
| Camada | CH₄ mol | C₂H₆ mol | C₂H₆ massa | ρ (~111K) |
|---|---|---|---|---|
| Topo (leve) | 95% | 5% | 0,090 | ~436 kg/m³ |
| Fundo (pesada) | 88% | 12% | 0,204 | ~455 kg/m³ |
Δρ compositional ≈ 19 kg/m³ (~4%) = âncora estável.

- Líquido `Species Mass Fraction` C₂H₆ (field function):
  `($${Position}[2] < 0.085) ? 0.204 : 0.090`  (metano = complemento)
- Vapor `Species Mass Fraction` C₂H₆ ≈ 0,01 (ullage quase puro metano)
- `Static Temperature` = 111 K constante (estratificação é por composição, não T)
- Volume Fraction = VOF Wave (líquido até z=170mm)
- Heat flux: Fundo = 1000 W/m²; lateral/topo adiabáticas
- Aceleradores: AMR Trigger Freq=5, Δt máx=0,05s
- Gatilho: fundo aquece ~14 K (vence o Δρ compositional) → flip. Atraso ~30-40 min físicos.

## ⚠️ EXIGÊNCIA do Evaporation/Condensation — componente INERTE no gás
Erro na 1ª init: "Inert gas component missing". O modelo Evaporation/Condensation
(difusão de condensáveis através de um gás carreador) **exige ≥1 componente inerte
não-condensável no gás**. (Por isso não serve p/ fluido puro — precisa de carreador.)

Correção: adicionar **Nitrogênio (N₂)** ao GÁS (só no gás; NÃO no líquido, NÃO na
Connectivity). N₂ é fisicamente ok para LNG (constituinte real, não-condensável a 111K).
- N₂ gás: MW=28,0134; μ=7,6e-6; cp=1040; k=0,0105; Std State T=111,67K; HoF=0 (inerte)
- Composição vapor com 3 componentes [Metano, Etano, N₂] = [0,9899, 0,01, 0,0001]
  (N₂ a 1e-4 — desprezível, só satisfaz o modelo; mass frac 0 também é válido)
- Connectivity permanece [Metano↔Metano, Etano↔Etano] (N₂ fora).

## Scenes/Reports
- Scene nova: **Ethane Mass Fraction** (a composição que inverte)
- Mantém: Temperatura, BOG (VF vapor), Velocidade; P_ullage, V_max, T_bulk
- Report novo: Volume Average de C₂H₆ mass fraction no threshold líquido

## ⚠️ Instabilidade de partida (non-finite residual na iteração 2)
Erro: "A non-finite residual (Fase Líquida) ... SegregatedVofSolver ... overflow".
Causa: multicomponente (VLE Raoult) + gás ideal + arranque = MUITO stiff. Δt=0,05s
(acelerador) é grande demais p/ o arranque → evaporação estoura num passo.
Correção:
- Δt máx → **1e-3 s** (acelerar só DEPOIS de estável, como no N₂)
- Evaporation/Condensation **Under-Relaxation Factor 1.0 → 0.2** (suaviza mass transfer)
- Se persistir: Δt 1e-4, Inner Iters 20, conferir consistência composição/P/T inicial.
Lição: phase-change multicomponente em tanque fechado é ainda mais stiff que o N₂.

## ⚠️ Cascata de divergência no arranque → decisão: LAMINAR
Sequência de falhas no startup: VOF (fix: Δt 1e-3, Evap URF 0.2) → momentum
(fix: Reference Density 4.6→1.76 LNG vapor, Δt 1e-4, Velocity URF 0.5) →
turbulência (μ_t limitado em ~todas as células + AMG diverge).
Causa da turbulência: k-ε com Buoyancy Production=Thermal Stratification reage
violentamente aos gradientes íngremes das interfaces (líquido-vapor E camadas de
composição) → produção de turbulência gigante.
Decisão pragmática: **rodar LAMINAR** (multicomponente). Laminar demonstra o
mecanismo compositional (VLE+empuxo); turbulência só refina taxas de mistura.
Reativar k-ε depois, com campo já estabelecido (startup laminar→turbulento) e TVR baixo.
Ajustes finais do arranque: Laminar + Δt 1e-4 + Ref Density 1.76 + Evap URF 0.2.

## ⚠️→✅ Tanque VENTADO (Pressure Outlet no topo) — resolve AMG + mais fiel
Mesmo laminar, o AMG (solver de pressão) divergia: tanque fechado com líquido
quase incompressível + bolha de gás compressível é mal-condicionado p/ o solver
segregado (nível de pressão flutua). Solução (ideia do usuário):
- **Topo: Wall → Pressure Outlet** (101325 Pa, backflow T~111K, comp. metano-rica).
- Dá condição de Dirichlet de pressão → Poisson bem-posto → AMG converge.
- MAIS realista: tanques LNG ventam BOG; o perigo do La Spezia foi o surto de BOG
  superar o venting (186 t). Assinatura do rollover passa a ser a **vazão de BOG no
  respiro** (Report Mass Flow no Topo, monitor BOG_vent) — que dispara no overturn.
- Mantém: Laminar, Δt 1e-4, Reference Density 1.76, Evap URF 0.2, heat flux fundo 1000.

## ⚠️ ARMADILHA — densidades da VOF Wave herdadas do N₂
A Flat VOF Wave guardava Light/Heavy Fluid Density do caso N₂:
Light=4,6 e Heavy=806,6 kg/m³. Ela usa essas densidades p/ a PRESSÃO HIDROSTÁTICA
inicial → com líquido a 806,6 (≈2× o LNG real ~445), o campo de pressão inicial fica
inconsistente → desbalanço gigante no 1º passo → cascata de divergência.
Correção: Heavy Fluid Density → **445** kg/m³ (líquido LNG ~111K), Light → **1.76**
(vapor metano). Sempre conferir as densidades da VOF Wave ao trocar de fluido.

## ⚠️ BUG da composição — field function do metano copiada errada
Sintoma: C2H6_liq ≈ 0,495 (esperado ~0,147). Causa: a FF do metano era cópia da do
etano ("etane_2") com `>` em vez de `<`, mas mantendo os VALORES do etano (0,204/0,090).
→ metano e etano davam 0,204/0,090 cada → soma 0,294 (≠1) → Star normaliza → ~0,5/0,5.
Correção: FF do metano = **`1.0 - ${Mass_fraction_initial_etane}`** (complemento garantido)
ou explícita `($${Position}[2] < 0.085) ? 0.796 : 0.910`. Ou: especificar só o etano e
deixar o metano como remainder. Após corrigir, C2H6_liq deve dar ~0,147.
(O threshold quebrado também contribuía, mas o bug real era a composição.)

## ⚠️ Divergência de ENERGIA (T→5000K) + turbulência de novo
Sintoma: "Maximum Temperature limited to 5000 on 12316 cells" + "Turbulent viscosity
limited" + non-finite Energy. A turbulência (k-ε) estava ativa de novo e arrastou a
energia; T disparou ao limite default (5000 K).
Correções:
- **Laminar** (confirmar — "turbulent viscosity limited" = k-ε ligado; ele explode nas
  interfaces, já visto).
- **Maximum Allowable Temperature 5000 → 200 K** (clamp criogênico; operação 111K,
  impede excursão a 5000K que envenena ideal gas/evaporação). Espelha o Min=50K.
- Δt → 1e-5 s ; Evaporation/Condensation Under-Relaxation 0.2 → 0.1.

## ✅ MARCO — rollover multicomponente RODANDO e estável
Após a saga de debugging, o caso multicomponente roda estável com composição correta:
- C2H6_liq ≈ 0,148 (= média esperada das camadas 0,09/0,204) ✓
- Scene Etano mostra as 2 camadas (fundo ~0,20 denso, topo ~0,09 leve) ✓
- Estável (laminar, User Defined EOS, Max Temp 200K, Δt 1e-5, Evap URF 0.1)

Lista de fixes que destravaram (resumo da saga):
1. Min Allowable Temp 50K (clamp criogênico)  2. VOF Wave Vertical Direction [0,0,1]
3. Densidade líquida = User Defined EOS (mistura ideal, composição+T) — Polynomial era
   só f(T); e o default [0,1;0,2;0,3] era lixo (~3700 kg/m³)  4. N2 inerte no gás
   (exigência do Evap/Cond)  5. Topo Pressure Outlet (AMG + realista)  6. VOF Wave
   densidades LNG (445/1.76, não 806.6/4.6)  7. FF do metano = complemento do etano
   8. Reference Density 1.76  9. Max Allowable Temp 200K  10. Laminar (k-ε explodia)
   11. Δt 1e-5 + Evap URF 0.1 (arranque stiff)

Próximo: subir Δt gradualmente (1e-5→1e-4→1e-3→1e-2) p/ alcançar a escala do rollover
(minutos); monitor Evap_CH4 (geração de BOG); caçar o flip (V_max, BOG_vent, homogeneização).

## Sequência
1. Trocar física p/ multicomponente; criar componentes CH₄ + C₂H₆ (líquido e vapor)
2. Propriedades (NIST) de cada componente; densidade de mistura f(T,x)
3. Phase Interaction: Evaporation/Condensation + p_sat (Antoine) por componente
4. IC: duas camadas por COMPOSIÇÃO (field function de fração) + T ~111 K
5. Heat flux (lateral, realista) ; manter turbulência + numérica estável
6. Monitores: V_max, P_ullage, T(z), e fração de C₂H₆(z) (a composição que inverte)
7. Rodar → caçar o flip compositional
