# [Sugar] — Tanque de Aeração + Tanque Reator + Ejetor

> Projeto CAExperts para Usina Colombo (kick-off 2026-07-01). Clarificação de xarope
> por fosfatação-flotação: floco de fosfato de cálcio formado no Reator, flotado por
> micro-bolhas de ar geradas por ejetor venturi no Aerador.
> Atualizado: 2026-07-04.

---

## Contatos
| Papel | Pessoa |
|---|---|
| Cliente (Usina Colombo) | **Marcos Eduardo Katsuda Ito** (Marcus Ito) — marcos.ito@sugareazucar.com |
| CAExperts (gerente) | **Marcus Castro Neves** |
| CAExperts (engenheiro/CFD) | **Gabriel Rozo** |
| Fabricante do agitador | **Agimix Soluções e Equipamentos Industriais** (Pedido 23610) |

## Fluido — xarope (Brix 70)
| Propriedade | Valor |
|---|---|
| Densidade | 1350 kg/m³ |
| Viscosidade | **65 poise = 6,5 Pa·s** (⚠️ não confundir com 6,5 poise) |
| Temperatura | 75 °C |

## Escopo — 2 tanques, simulados separadamente

### 🟢 Reator (agitação — formação de flocos)
- **Entregável**: relatório de potência do agitador (**meta <25 kW**, brief do Marcus gerente)
  + Nq/Np otimizado a partir dos resultados de CFD (pedido do Ito por e-mail)
- Geometria: casca cilíndrica ID 5,08m + cone + 5 baffles + defletor, medidos do CAD real
- Impelidor: **duplo hydrofoil Ø800mm, eixo Ø69,85mm, 109,3 rpm** (dados reais do fabricante
  Agimix, folha `M0000_SIST._AGITAÇÃO_AGX-PBW800_AISI304`)
- **Correção importante (04/07)**: impelidor reconstruído com **3 pás por estágio (6 total)**,
  não 8 como na primeira versão — confirmado pela vista em planta/isométrica do desenho
  técnico da Agimix. Número de pás afeta diretamente o Número de Potência (Np), correção
  necessária antes de fechar o relatório de potência.
- Física: MRF (Moving Reference Frame) em regime permanente, monofásico (só xarope)
- Status: geometria corrigida e re-subtraída no 3D-CAD; **pendente regenerar malha final
  e rodar até convergência** com o impelidor de 3 pás antes de extrair potência/torque e
  calcular Nq/Np

### 🟣 Aerador (flotação — micro-bolhas)
- **Entregável**: distribuição de tamanho de bolha (S-Gamma) e diagnóstico de por que a
  aeração real está "deficiente"; achar regime de pressão de ar otimizado
- Geometria: casca cilíndrica ID 2,032m + cone + **3 injetores/lanças reais** (Ø84,8mm,
  medidos do conjunto ejetor), sem agitador/MRF (só o jato dos injetores movimenta o fluido)
- Física: Eulerian Multiphase (Xarope + Ar) + Phasic Turbulence (K-Epsilon) + **S-Gamma**
  (Breakup + Coalescence, Interaction Length Scale = Sauter Mean Diameter) + **Implicit
  Unsteady** (RANS estacionário não converge nesse regime — ver histórico abaixo)
- Boundary conditions: `aerador.injetores` = Stagnation Inlet (Total Pressure gauge);
  `aerador.topo` = Phase Permeable (Ar permeável / Xarope impermeável), com **Shear Stress
  Specification = Slip** do lado do Xarope (crítico — ver histórico)
- **3 casos a rodar**: 1 / 2 / 3 kgf/cm² de ar → **98070 / 196130 / 294200 Pa** (gauge)

#### Histórico de estabilização (divergências resolvidas, 04/07)
Esse caso teve várias rodadas de divergência numérica antes de estabilizar — documentando
pra não repetir o mesmo caminho:
1. Steady-state divergia sempre (S-Gamma + EMP + turbulência acoplados são fisicamente
   transientes — jato mergulhando em líquido muito viscoso, não existe "equilíbrio"
   estacionário de verdade)
2. → Trocado para **Implicit Unsteady**, resolveu a divergência de base
3. Malha no injetor estava grosseira (Volumetric Control criado mas sem o "Customize
   Isotropic Size" marcado — o refino nunca esteve realmente ativo). Corrigido: refino
   ~8mm nos 3 injetores
4. `Shear Stress Specification` do Xarope em `aerador.topo` estava em **No-Slip**
   (parede rígida) — fisicamente errado pra uma superfície livre, e com viscosidade de
   6,5 Pa·s isso gerava cisalhamento artificial enorme, disparando o Tdr (dissipação
   turbulenta) do Xarope. Corrigido para **Slip**.
5. Com malha + Slip corrigidos: sistema estável, testado incrementando Δt de 0,001s até
   **0,01s sem divergir**

#### Achados preliminares (ainda não definitivos — tempo físico simulado curto)
- **Sauter Mean Diameter concentrado em ~1,2–1,5mm** — acima da meta de <200µm (a
  confirmar com mais tempo físico rodado, esse é só o resultado até ~iteração 2000)
- **Velocidade de circulação muito baixa** nas 3 sondas (Perto Injetor / Meio Tanque /
  Perto Topo) — ordem de **µm/s**, sugerindo que a circulação em massa no tanque é
  fraquíssima, quase toda a movimentação fica restrita à pluma imediata do jato. Isso
  pode ser a explicação real da "aeração deficiente" reportada pelo Ito — não (só)
  tamanho de bolha, mas falta de transporte pelo volume do tanque
- Pendente: deixar rodar bastante mais tempo físico (circulação lenta = precisa de muito
  tempo pra amostrar o tanque todo), configurar time-average (Field Mean Monitor +
  Sliding Sample Window) uma vez que o Δt final esteja fixado e o warm-up completo, e
  então rodar os 3 casos de pressão com o mesmo critério de warm-up+produção

## Ferramentas de monitoramento montadas
- 3 Point Probes no eixo do Aerador (x=0,20 / y=-0,44): Perto Injetor (z=-5,0), Meio
  Tanque (z=-2,0), Perto Topo (z=+1,0)
- Reports/plots agrupados por grandeza: VF de Ar, Sauter Mean Diameter, Velocidade —
  cada um com as 3 sondas juntas pra comparar por altura
- Histogram Plot nativo (Sauter Mean Diameter × Volume Fraction of Ar) — visualização
  direta da distribuição de bolha pedida pelo Ito
- Reports: `Percentual_Bolha_Flotavel`, `Volume_Ar_Total`, `Volume_Ar_Bolha_Boa`, `Torque`

## Pendências gerais
- [ ] Reator: regenerar malha com impelidor de 3 pás, rodar até convergência, extrair
      potência/torque, calcular Nq/Np
- [ ] Aerador: rodar caso 1 kgf/cm² até estabilização estatística (warm-up + produção
      com time-average)
- [ ] Aerador: repetir para 2 e 3 kgf/cm² com o mesmo critério de tempo
- [ ] Comparar os 3 casos e recomendar regime de pressão otimizado pro Ito
- [ ] Consolidar relatório final (potência Reator + Nq/Np + distribuição de bolhas
      Aerador nos 3 casos)
