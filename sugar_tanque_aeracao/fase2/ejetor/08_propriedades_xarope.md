# 08 — Propriedades do XAROPE de cana (para o CFD do ejetor)

> Pesquisa de literatura (2026-07). Marca o que o **setup atual USA** (isotérmico, densidade constante,
> laminar, VOF) vs o que fica **inerte** (só entraria se ligar térmico/compressível).

## Tabela de propriedades

| Propriedade | Valor p/ o CFD | Faixa de literatura (cana/sacarose) | Usada agora? |
|---|---|---|---|
| **Densidade ρ** | **1300 kg/m³** (cliente) | 1120–1350 (satur. ~1327) | ✅ **SIM** |
| **Viscosidade dinâmica μ** | **6,5 Pa·s** (cliente) | **típico 0,0014–0,166 Pa·s** ⚠️ | ✅ **SIM** |
| **Tensão superficial σ (ar–xarope)** | **0,058 N/m** | puro 0,06–0,08 · técnico/impuro 0,05–0,07 | ✅ **SIM** (na interação) |
| Massa molecular | ~342 g/mol (sacarose) / N/A | sacarose 342,3 | ❌ não (líquido incompressível) |
| Velocidade do som | ~1650 m/s | 1500–1700 (sobe com Brix) | ❌ não (ρ constante) |
| Calor específico cp | ~2,8 kJ/kg·K | 2,4–3,8 | ❌ só se térmico |
| Condutividade térmica k | ~0,38 W/m·K | 0,26–0,46 | ❌ só se térmico |

## ⚠️ ALERTA CRÍTICO — a viscosidade de 6,5 Pa·s

O xarope de cana **de processo** fica em **1,4–166 mPa·s** (0,0014–0,166 Pa·s). O nosso **6,5 Pa·s = 6500 mPa·s**
está **~40× a 4000× acima** dessa faixa. Isso só acontece em xarope **quase saturado / altíssimo Brix
(~73–78 °Bx)** e/ou **frio** (bate com ρ=1300 ≈ saturação).

**Por que isso importa MUITO:** a viscosidade **cai pela metade a cada +10 °C**. Se os 6,5 Pa·s foram medidos
a, digamos, 20 °C, e o processo roda a 60 °C → a viscosidade **real de operação** seria ~**0,8 Pa·s** (8× menor).
E o **Reynolds do furo escala com 1/μ**:
- μ=6,5 → **Re≈37 (laminar)** → toda a nossa metodologia (sem quebra turbulenta, VOF, extensão).
- μ=0,8 → **Re≈300** → **transicional/turbulento** → **muda a física** (kernels turbulentos passam a valer!).

👉 **Perguntar ao Ito/cliente:** (1) a **temperatura** em que 6,5 Pa·s foi medido, (2) a **temperatura real
de operação**, (3) o **°Bx** do xarope. Sem isso, o número de μ (e todo o regime) fica no ar.

### ✅ RESOLVIDO (Ito, via Gabriel, 23/07)
- **μ = 6,5 Pa·s é DADO MEDIDO no processo deles** (a 75 °C) → **governa** (medido > correlação genérica).
- **°Bx > 70** (o "70" era limite inferior; real ~**85 °Bx**). A ~85 °Bx / 75 °C, **6,5 Pa·s é coerente** com a
  literatura (a 20 °C seria ~0,49 Pa·s só a 70 °Bx; a ~85 °Bx sobe muito, e a viscosidade a 75 °C ainda fica na
  casa de vários Pa·s). **Sem inconsistência.**
- **Conclusão:** mantém **μ=6,5 Pa·s, ρ=1300, Re≈37 → LAMINAR**. Metodologia (VOF laminar, sem kernel
  turbulento) **confirmada, sem ressalva**. O alerta valeu como verificação; o dado medido fecha.

## Notas
- **σ:** o xarope técnico tem **impurezas surfactantes** (gorduras, gomas) que **abaixam** σ vs sacarose pura.
  0,058 N/m é prático e conservador. Já temos sweep **0,045–0,072** no doc `02` se quiser sensibilidade.
- **μ:** é **Newtoniano** até ~alto Brix; massecuite/supersaturado vira não-Newtoniano — a 6,5 Pa·s ainda tratamos
  como Newtoniano (ok), mas se o cliente disser que é massecuite, reavaliar (Ostwald/Bingham).

## Fontes
- Rheology & fluid dynamics of sugarcane juice — ScienceDirect (S1369703X1000313X)
- Thermal & rheological properties of juices/syrups (jaggery) — ScienceDirect (S0960308519308946)
- Surface tension behaviour of pure and technical sucrose solutions — ResearchGate (291563831)
- Velocity & absorption of sound in aqueous sugar solutions — IOPscience (0370-1301/67/1/310)
- Sugar Species Model — SysCAD documentation
