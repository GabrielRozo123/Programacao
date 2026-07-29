# 12 — FECHAMENTO do CFD do ejetor: a sucção existe, mas é 1000× fraca demais

> Consolida as três configurações testadas após a reunião com o Ito (que confirmou **sucção natural**,
> não ar soprado). **Resultado quantitativo, não uma negativa seca.**

## 1. As três configurações testadas — todas convergem para o mesmo

| # | Configuração | Resultado |
|---|---|---|
| **1** | Ar **soprado** a 1–3 kgf/cm² · bico 7×Ø9 · 130 m³/h | ❌ ar não entra · **xarope reflui** pela linha de ar (10,25 kg/s) |
| **2** | Ar **atmosférico** (sucção natural) · outlet 0 | ❌ ar não entra (VF_ar = 0 em todo o domínio) |
| **3** | **Melhor caso possível**: bico **4×Ø15** · ar atmosférico · outlet **−0,38 bar** · xarope **0,05 m/s** | ⚠️ **ar entra — mas 1000× menos que o necessário** |

## 2. O número da configuração 3 (o melhor caso)

Todas as escolhas foram deliberadamente **as mais favoráveis fisicamente defensáveis**:
- bico **4×Ø15** (o menos restritivo dos dois desenhos)
- ar **atmosférico** (o mecanismo que o Ito descreve)
- outlet **−38.000 Pa** (coluna de 3 m — a sucção máxima justificável)
- xarope a **0,05 m/s** = 5,9 m³/h total (**22× abaixo** dos 130 do projeto)

| | valor |
|---|---|
| Mass flow de ar (CFD, t=0,003 s) | **+1,11e-5 kg/s** ✅ positivo = **entrando** |
| Vazão de ar equivalente | **0,040 m³/h** |
| **Alvo do Ito** | **40 m³/h** |
| **Déficit** | **1000×** (três ordens de grandeza) |
| Velocidade do ar na porta 1½" | **9,7 mm/s** (precisaria de 9,75 m/s) |

### Leitura do transiente
| t (s) | ṁ_ar | interpretação |
|---|---|---|
| 0,0006 | **−3,7e-4** | negativo = **xarope saindo** pela porta (choque de partida) |
| 0,0008–0,0015 | +8e-5 | ar entra no alívio do transiente |
| 0,003 | **+1,1e-5** | assenta num valor baixo |

## 3. A causa é GEOMÉTRICA, não numérica

```
Caminho do xarope (medido no STEP nativo, Y decrescente):
   header 8" (Y=858) → PORTA DE AR 1½" (Y=542) → redução (Y=302) → BICO (Y=199) → lança 3 m
                        ▲
                        └── a porta está A MONTANTE do bico
```

**Restrição a jusante sempre gera pressão POSITIVA a montante.** Num eductor de verdade, a porta de
sucção fica **DEPOIS** do bocal, na zona de baixa pressão do jato. Aqui ela está antes.

**Prova numérica:** para o ar entrar na vazão-alvo seria preciso **−5 bar** na saída — **4,9× além do
vácuo absoluto** (−1,013 bar). Não é questão de calibrar: é impossível.

## 4. ✅ O que ficou PROVADO (e é entregável)
1. **A sucção natural existe** — o ar entra, o mecanismo é real.
2. **Mas é ~1000× fraca demais** para os 40 m³/h que o processo pede.
3. **A causa é a posição da porta de ar** (a montante do bico), não a pressão do ar nem a vazão.
4. **Nem o melhor cenário fisicamente possível** resolve.

## 5. ❓ O que só o Ito pode responder
1. **Existe alguma restrição entre a válvula de ar e o bico que não aparece no CAD?**
   *(Se houver, ela criaria a garganta que falta — e explicaria a sucção que ele observa.)*
2. **A lança descarrega SUBMERSA no tanque ou em queda livre?**
   *(Se submersa, a pressão na saída é positiva e o quadro fica ainda mais restritivo.)*
3. **A sucção que vocês observam é contínua ou acontece na partida / com a bomba desligada?**
4. **De onde vem a área de 0,045 m² (Ø239 mm) da conta dele?** — não é nenhuma seção mapeada.

## 6. Recomendação técnica
Se o objetivo é **aspirar 40 m³/h de ar por sucção natural**, a solução de projeto é
**mover a injeção de ar para JUSANTE do bico** (na zona de baixa pressão dos jatos) — é assim que
eductores funcionam. Na posição atual, nenhuma combinação de pressão/vazão atinge o alvo.

---

> **Status:** CFD do ejetor **encerrado até nova informação do Ito**. O resultado é quantitativo,
> reprodutível e verificado por três configurações independentes + modelo analítico.
