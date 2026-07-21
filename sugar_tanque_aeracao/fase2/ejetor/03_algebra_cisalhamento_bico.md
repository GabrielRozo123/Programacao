# 03 — Álgebra fina: cisalhamento na BOCA da lança (bico do ejetor)

> Ito (reunião 21/07) perguntou o **efeito do diâmetro no cisalhamento** e quer **propor uma geometria na boca
> da lança** que favoreça a quebra da bolha. Escopo agora **confirmado**: a quebra é no **bico do ejetor**
> (não no impelidor do reator). Desenho do cliente: `CSA01-300` (bico) + `CSA01-110` (aerador).
> Dados: motriz ~130 m³/h (÷4 ejetores ÷7 bicos), **ar ~30 m³/h/ejetor**.

## 1. Cisalhamento no bico (o jato de xarope)
Velocidade no bico: `V = Q_bico/(π·d²/4)`, com `Q_bico = Q_total/(N_ejetores·N_bicos)`.
Cisalhamento característico (como na metodologia, γ̇~V/d):
```
γ̇ = V/d = 4·Q_bico / (π·d³)          →   γ̇ ∝ 1/d³   (vazão por bico fixa)
```
**Confere com o atual:** Q_bico≈1,3e-3 m³/s, d=9 mm → V≈20 m/s, **γ̇≈2.250–3.000 /s** ✓ (bate com a metodologia).

## 2. 🎯 O efeito do DIÂMETRO (resposta direta ao Ito)
**`γ̇ ∝ 1/d³`** — alavanca **forte**: reduzir o bico à **metade → 8× o cisalhamento.** (Menos bicos também sobe γ̇,
por mais vazão em cada um.) **MAS** — e aqui está a reviravolta — veja o §4.

## 3. O custo (pressão / potência)
`ΔP_bico ∝ ½ρV² ∝ ρ·Q²/d⁴`  →  bico à metade = **16× o ΔP**. Potência ∝ `Q³/d⁴`.
Ou seja: **γ̇ ∝ 1/d³, mas o custo ∝ 1/d⁴** — retorno decrescente (a mesma lei do impelidor: cisalhamento sobe com raiz da potência).

## 4. ⚠️ A REVIRAVOLTA — cisalhamento SIMPLES quase não quebra (λ→0)
A verificação da metodologia já provou: a razão de viscosidade `λ = µ_ar/µ_xarope ≈ 3×10⁻⁶ → 0`. Nesse limite a
bolha **RESISTE à quebra em cisalhamento SIMPLES** (`Ca_crit → ∞`, vira *tip-streaming*, não quebra). Então
**"furo mais fino" sozinho (só cisalhamento de parede) NÃO quebra a bolha de ar.** O diâmetro ajuda, mas **não é o
mecanismo**. O que quebra a bolha em λ→0 é o **cisalhamento EXTENSIONAL** (contração/elongação).

## 5. A geometria que FUNCIONA — bocal CONVERGENTE (extensão)
Uma **contração** na boca do bico gera escoamento **EXTENSIONAL** (o único que quebra em λ→0):
```
Taxa extensional:      ε̇ ≈ V_saída / L_contração          (mais abrupta = mais extensão)
Deformação de Hencky:  ε_H = ln(A_in/A_out) = 2·ln(D_in/d_out)   (mais contração = mais deformação)
Quebra se:             Ca_ext = µ·ε̇·a/σ  >  Ca_crit,ext (~0,1–1)   ← MUITO menor que o de cisalhamento!
E se:                  t_residência (≈ L/V) > tempo visco-capilar do fio (µ·R_fio/σ)
```
**Ou seja: a proposta não é "furo mais fino" — é um BOCAL CONVERGENTE na boca da lança** (contração D→d), que
transforma o jato em **fluxo extensional** e leva `Ca_ext` acima do crítico.

## 6. Os DOIS levers na boca do bico (a proposta completa)
| Lever | Papel | Escala | Custo |
|---|---|---|---|
| **Ø do furo de AR** ⬇️ | tamanho de **nascimento** da bolha | d_bolha,0 ∝ d_ar | ΔP_ar ↑ |
| **Contração do bico de XAROPE** (D_in/d_out) ⬆️ | **quebra** por extensão | ε_H = 2·ln(D/d) | ΔP ∝ 1/d⁴ |
| Comprimento da contração L ⬇️ | ε̇ = V/L maior (mais abrupta) | ε̇ ↑ | perda localizada / separação |
| Ø do bico (reto) d ⬇️ | γ̇ ∝ 1/d³ (só cisalh. simples — **fraco em λ→0**) | γ̇ ↑ | ΔP ∝ 1/d⁴ |
| Nº de bicos ⬇️ | mais vazão/bico → V ↑ | γ̇ ↑ | ΔP ↑ |

## 7. Cotas do desenho do cliente (a confirmar na leitura fina)
Do `CSA01-300` (CORTE D-D + PLANTA do bico):
- **Câmara ~Ø45 interno / Ø63 externo** (⚠️ corrige o v2 que assumiu Ø60 → **usar Ø45**).
- **7 bicos em hexágono** ✓ (confirma v2). Furos **Ø7 a 60° = FIXAÇÃO** (não são bico nem ar!).
- Chanfros na câmara: 45°/22°, Ch 1,5×45° e 1×45°.
- **Confirmar:** Ø exato do bico (bore) e Ø/nº dos furos de ar na leitura ampliada do PDF nativo.

## Veredito (a mensagem pro Ito)
1. **Diâmetro do bico:** alavanca forte no cisalhamento (`γ̇∝1/d³`) **mas cara** (`ΔP∝1/d⁴`) e — crucial — o
   cisalhamento **simples quase não quebra** a bolha de ar (λ→0).
2. **A geometria que funciona é uma CONTRAÇÃO (bocal convergente)** na boca da lança → cria o **cisalhamento
   EXTENSIONAL**, que é o mecanismo real de quebra. Parâmetros de projeto: **razão de contração e comprimento.**
3. O CFD (Passo 1 monofásico → classificar o tensor extensional; VOF → tamanho de nascimento) **quantifica** qual
   contração leva a bolha à faixa flotável no tempo de residência disponível — e se um passe basta.
