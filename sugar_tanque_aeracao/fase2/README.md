# Fase 2 (Ito) — Estudo paramétrico + Ejetor

Segunda parte do projeto Sugar/Ito, aberta após a **apresentação (14/07/2026)** — feedback **positivo**.
O Ito pediu duas frentes:

| Frente | O que | Pasta |
|---|---|---|
| **A. Paramétrico do agitador** | Varrer **diâmetro, ângulo das pás, nº de pás** → potência/Np/Nq (Design Manager) | [`impelidor_parametrico/`](impelidor_parametrico/) |
| **B. Ejetor venturi** | Simular o **gerador de microbolhas** e prever o tamanho da bolha no meio viscoso | [`ejetor/`](ejetor/) |

## A. Paramétrico (Design Manager)
- **CAD paramétrico pronto:** [`impelidor_parametrico/`](impelidor_parametrico/) — pitched-blade com
  `D`, `ângulo`, `nº de pás` varriáveis; caso-base Agimix Ø800/30°/3 pás.
- **Dificuldade das variáveis:** rotação (rpm) é trivial (global parameter); **diâmetro e ângulo**
  exigem geometria paramétrica (o CAD deste repo resolve isso).
- **Custo:** varrer **só no reator** (MRF permanente). Aerador transiente fica de fora do sweep.
- **Plano de estudo DM:** tutorial "Design Sweep of a Static Mixer" (fluxo base) → aplicar na rotação →
  Part-Replacement / 3D-CAD paramétrico para D e ângulo → "Pareto Optimization" se quiser o ótimo.

## B. Ejetor venturi
- **O equipamento:** venturi (convergente–garganta–difusor). Xarope motriz acelera na garganta →
  pressão cai → ar (furos ~1 mm) é sugado/injetado → **cisalhamento** fragmenta em microbolhas → difusor
  → lança → tanque. Geometria/medidas em [`../geometria/dimensoes_ejetor_medidas.md`](../geometria/dimensoes_ejetor_medidas.md)
  e domínio fluido `../geometria/eductor_dominio_fluido_v1.step`.
- **Por que importa:** as lanças passivas dão bolha ~1,2–2,4 mm (viscosidade suprime a quebra). O ejetor
  tem **garganta de alto cisalhamento** — é o device que **pode** de fato quebrar a bolha até a faixa de
  flotação (<200–300 µm). É a **alavanca real** que identificamos na Fase 1.
- **Metodologia de CFD:** ver [`ejetor/01_metodologia_cfd_ejetor.md`](ejetor/01_metodologia_cfd_ejetor.md)
  (montada por análise multi-abordagem + literatura + verificação adversarial).

## ⚠️ Esclarecimento (recorrente): impelidor × ejetor são tanques DIFERENTES
Verificado no **CAD montado** (`../geometria/sugar_dominio_fluido_completo.step`, referência única,
volumes batem com o projeto). Ver figura [`prova_impelidor_so_reator.png`](prova_impelidor_so_reator.png).
- 🟣 **AERADOR** (fluido 20,2 m³, eixo y=−0,44 m): **ejetor + 3 lanças. SEM impelidor.** É onde se fazem as microbolhas.
- 🟢 **REATOR** (fluido ~140 m³, eixo y=−6,282 m): **impelidor duplo (MRF, 4,4 m³) + baffles.** É a agitação/potência.
- O impelidor **não** move o ejetor: o venturi é alimentado por **bomba motriz dedicada** (linha "xarope motriz").
- "Aumentar o impelidor" (pedido do Ito) = estudo paramétrico do **reator** (não mexe no ejetor).

## O achado do "fabricante sobrenatural" (registro)
Fabricante das lanças alega bolha **5 µm** no nascimento; CFD dá **~1,2 mm** (~240×). Não é erro do CFD:
o tamanho de nascimento é propriedade do **fluido+escoamento**, não da lança — os 5 µm são poro/água e
não sobrevivem ao xarope de 6,5 Pa·s. **Reforça** que a alavanca é a viscosidade/cisalhamento, não a lança.

## Log
- **2026-07-14** — Fase 2 aberta. CAD paramétrico do impelidor construído e verificado (ponta em D/2 p/
  qualquer ângulo). Achado do 5 µm registrado.
- **2026-07-14** — **Metodologia do ejetor FECHADA** (`ejetor/01_metodologia_cfd_ejetor.md`), a partir de
  análise multi-abordagem (4 filosofias de CFD) + literatura. **Achado central:** o ejetor é **laminar**
  (Re~10–90) → sem quebra turbulenta; quebra (se houver) é viscosa/extensional. Recomendação: **dois passos**
  (monofásico laminar → EMP+S-Gamma transiente) **+ âncora VOF**, com quebra por strain-rate/Ca (não ε).
- **2026-07-14** — **Verificação adversarial** das 6 afirmações-alicerce (§11 do doc). Veredito:
  `SUPPORTED_WITH_CAVEAT` — metodologia sólida, 10 refinamentos aplicados. **Maior risco (honesto):** o venturi
  pode não gerar microbolha flotável em 6,5 Pa·s num único passe (sucesso provável depende de recirculação).
  Ar dos furos é compressível/choked (não laminar); d_max é TETO ~55–170 µm, não SMD.
- **2026-07-14** — Confusão impelidor×aerador RESOLVIDA (prova geométrica; Marcus confirmou por call).
- **2026-07-14** — **Impelidor novo decidido** (Ito via Marcus): Ø880/31,5°/4pás/120,2 rpm — 1 design vs base
  (sem sweep). STEP posicionado gerado (1 corpo fundido). **No STAR:** import→subtract→named faces→rotação
  12,59 rad/s feitos; salvo `Marcos_Ito_Bolhas_segunda_fase.sim`. **Falta:** malhar→steady MRF→torque→P/Np/Nq.
  Detalhe em [`impelidor_parametrico/execucao_star.md`](impelidor_parametrico/execucao_star.md).
