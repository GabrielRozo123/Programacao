# 14 — Resultado do Sim 2 **CORRIGIDO** (recirculação conforme o diagrama do cliente)

> Domínio: `geometria/cerveja_sim2_CORRIGIDO_fluido.step` (**3.516 L** — bate com a TAG de 3.500 L).
> Correção da recirculação (ver `geometria/gen_sim2_corrigido.py` e o diagrama EGISA 055.2254):
> **saída = dreno central no ápice do cone** · **entrada = vertical pela tampa, r ≈ 665 mm**
> (a versão anterior usava dois bocais **laterais**, z=100 e z=1430 — estava errada nos dois).
> Chiller inalterado: sucção lateral z=1350 mm · retorno lateral z=50 mm · 12 m³/h · −5 °C.

---

## 1. Resultados da rodada

| Métrica | **Sim 2 CORRIGIDO** | Sim 2 antigo (geometria errada) |
|---|---|---|
| **Pico de estratificação ΔT (topo−fundo)** | **≈ 0 °C** (some) | 4,7 °C @ ~500 s |
| **T_bulk = −4,90617 °C (99% resfriado)** | **6.140 s** | 4.930 s |
| T_bulk = −4,9928 °C (cauda) | 10.310 s | — |
| Fechamento do balanço de energia | **−0,0023 W** (resíduo 2e−8 %) | −72 W |

## 2. O benchmark de mistura perfeita (CSTR)

```
τ = V/Q = 3.516 L ÷ (12 m³/h = 3,333 L/s) = 1.054,8 s
T(t) = −5 + 10·e^(−t/τ)
```

| | tempo p/ −4,90617 °C |
|---|---|
| **CSTR ideal** (mistura perfeita) | **4.925 s** |
| **Sim 2 CORRIGIDO (CFD)** | **6.140 s** |
| **Atraso** | **+24,7 %** |

**τ efetivo do CFD = 1.315 s** (vs 1.055 do CSTR) → **razão 1,25**.
Na cauda o τ_eff sobe ainda mais (≈1.424 s em 10.310 s) → **não é um CSTR puro**: existe uma
fração de volume com troca mais lenta (zona do cone / periferia junto à parede).

## 3. ⚠️ O que MUDA em relação ao que estava nos slides

A geometria antiga dava um Sim 2 que **coincidia com a mistura perfeita** (4.930 s vs 4.849 s).
Com a geometria correta isso **deixa de ser verdade**:

| | antigo (errado) | **corrigido** |
|---|---|---|
| Estratificação | reduz pela metade (9,6 → 4,7 °C) | **elimina (→ 0)** |
| Velocidade | ≈ mistura perfeita | **~25 % mais lento que a mistura perfeita** |

**A conclusão do estudo não se inverte — ela fica MAIS FORTE e mais limpa:**
> *A recirculação entrega **uniformidade**, não velocidade.* Agora com os dois lados no extremo:
> a estratificação **desaparece** (não só cai pela metade) e o preço é **+25 % de tempo**.

## 4. Por que ficou mais lento que o CSTR (mecanismo)

A taxa de resfriamento é `ṁ·cp·(T_sucção + 5)` — **quem manda é a T_sucção** (lateral, z=1,35 m).
- Homogeneizando, a sucção vê ~T_bulk → duty cai → tende ao limite CSTR (esse é o teto).
- **Ficar ABAIXO do teto** indica que o jato da recirc (entrada pelo topo, r=665 mm, descendo)
  **curto-circuita parcialmente** com a sucção lateral do chiller a 1,35 m, que está próxima em
  cota e do mesmo lado do tanque: parte do fluido já resfriado volta à sucção antes de varrer o
  fundo → a T_sucção fica um pouco **abaixo** da T_bulk → duty menor → mais lento.
- Isso é **consistente** com o τ_eff crescente na cauda (a zona lenta é o cone/fundo).

> Ou seja: a recirc corrigida **mistura muito bem** (ΔT→0) mas **paga** com um leve curto-circuito
> térmico na região da sucção.

## 5. Estado de validação

| Checagem | Status |
|---|---|
| Volume do domínio × TAG (3.500 L) | ✅ 3.516 L (0,5 %) |
| Sólido único, `isValid()` | ✅ |
| Fechamento de energia | ✅ −0,0023 W (2e−8 %) |
| Enquadramento entre os limites físicos | ✅ deslocamento (Sim 1, ~2.500 s) < CSTR (4.925 s) < **Sim 2 corr. (6.140 s)** < baseline 0,85 m (~7.500 s) |

⚠️ **Incerteza declarada:** `DN_REC = 65 mm` da linha de recirculação é **suposto** (não cotado no
diagrama). Afeta a velocidade do jato de entrada — e portanto o grau de curto-circuito do §4.
Confirmar com o cliente antes da entrega final.
