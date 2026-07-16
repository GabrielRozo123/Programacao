# Execução no STAR — impelidor novo (onde paramos)

> Nota de recall da Fase 2 / impelidor. Última atualização: 2026-07-14 (noite).
> Arquivo do STAR: **`Marcos_Ito_Bolhas_segunda_fase.sim`** (cópia dedicada da Fase 2).

## O design novo (decisão do Ito via Marcus)
Sem sweep (projeto barato) — **um design novo** com todos os incrementos juntos, vs a base da Fase 1:
| | Base (Fase 1) | **Novo** |
|---|---|---|
| Diâmetro | Ø800 (D/T=0,157) | **Ø880 (D/T=0,173)** |
| Ângulo das pás | 30° | **31,5°** (+5%) |
| Nº de pás | 3 | **4** (+1) |
| Rotação | 109,3 rpm | **120,2 rpm** (+10% = **12,59 rad/s**) |
| P / Nq / Np/est | 4,07 kW / 0,345 / 0,76 | *a rodar* |

Geometria: `impelidor_NOVO_D880_ang31.5_4pas_POSICIONADO.step` (1 corpo fundido, já no eixo do reator
(327,−6282), estágios em z=−4296/−740, ponta 446 mm < 550 do MRF).

## ✅ Já feito no STAR
1. **Import** do STEP posicionado → veio como **1 corpo** ("Impelidor"). *(Não precisou Unite — o STEP já sai fundido.)*
2. **Subtract Bodies:** Target=**MRF**, Tool=**Impelidor**, Keep Tool ⬜, Precise, Face Names ✅ → vazio do impelidor no MRF, **limpo**.
3. **Named Faces:** `impelidor.cubo`, `impelidor.eixo`, `impelidor.pas` (+`impelidor.pas 2`), `mrf.interface` intacta.
4. **Update/Close 3D-CAD** → Parts religaram sozinhos.
5. **Rotação:** Motions → Rotation → Rotation Rate = **12,59 rad/s** ✅.
6. Salvo como `..._segunda_fase.sim`.

## 👉 Próximo (amanhã, 15/07)
1. **Re-malhar** (Operations com ⚠️): **Malha MRF + Malha do Reator** (afetados pelo impelidor novo).
2. **Checar boundary do impelidor:** Regions → MRF → Boundaries — confirmar que `impelidor.*` viraram a
   **parede do impelidor** (não caíram em Default) e que **mrf.interface** existe.
3. **Rodar STEADY MRF MONOFÁSICO do reator** (como a rodada dedicada da Fase 1 que deu 4,07 kW).
   **NÃO** rodar o multifásico transiente só p/ torque.
4. **Extrair:** Torque no impelidor → **P = T·ω** (ω=12,59). Np e Nq.
   - Np = P/(ρ·N³·D⁵), N=2,003 rev/s, **D=0,880 m** (mudou! antes 0,800). Nq = Q/(N·D³).
5. **Comparar** com a base (4,07 kW / 0,345 / 0,76). Meta: **P < 25 kW**.

## ✅ RESULTADO (16/07) — rodada concluída
**Torque = −786,6 N·m** (convergido, ~600 it). Campo de velocidades correto (dois jatos do impelidor duplo, ~4,1 m/s).

| Grandeza | Base (Fase 1) Ø800/3pás/109,3rpm | **NOVO Ø880/31,5°/4pás/120,2rpm** |
|---|---|---|
| Torque | −355,7 N·m | **−786,6 N·m** |
| **Potência P = T·ω** | 4,07 kW | **9,90 kW** (2,43×) |
| Np/estágio | 0,76 | **~0,86** (sobe com 4 pás) |
| Nq | 0,345 | *pendente (report de vazão)* |
| Meta P < 25 kW | ✅ | **✅ (9,9 kW, folga grande)** |

**Leitura:** o impelidor maior/mais rápido/4 pás **~2,4× a potência**, mas **bem dentro da meta <25 kW** — melhora o
bombeamento sem estourar. Falta o **Nq** (Surface Integral da vazão através do impelidor, como na Fase 1).

### 🔑 Lições do setup (2 bugs resolvidos)
1. **Report de torque:** tem de somar **todas** as faces do impelidor (cubo+eixo+pás), senão subconta.
2. **MRF (o principal):** a rotação vai na **REGIÃO** (`Motion Specification → Reference Frame = rotativo, 12,59 rad/s`),
   **NÃO** nas paredes das pás (Wall Relative Rotation nelas = 0; elas giram com o frame). Só o **eixo no reator
   estático** (`reator.haste`) precisa de Wall Relative Rotation explícito. *(Rotating-wall numa pá só faz película
   viscosa fina, não bombeia — foi o "torque −8 / velocidade 0,01" que assustou.)*

## ⚠️ Heads-ups
- Output deu *"Zero-area face(s); area adjusted for 108 faces in Dominio.Reator"* — STAR corrigiu sozinho
  (faces-sliver); só ficar de olho se a malha reclamar perto do reator.
- Estimativa analítica: P ≈ 2–3× a base → **~8–12 kW** (ainda < 25 kW). CFD crava o real.

## 🔑 Decisão importante (registrada)
**O impelidor NÃO exige transiente de bolha.** Impelidor está no REATOR; bolhas estão no AERADOR
(ejetor); os tanques são **desacoplados**. Logo o steady MRF monofásico é o **entregável completo** do
impelidor. O "transiente das bolhas" pertence ao **EJETOR** — estudo separado (`../ejetor/`), sim novo,
esperando a **vazão da bomba motriz** do cliente.
