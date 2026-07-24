# 10 — A LEI do arraste de ar (álgebra calibrada por CFD)

> Derivado de 2 pontos de CFD a **1 kgf/cm²** (bico nativo 7×Ø9, xarope 6,5 Pa·s).
> Responde: **qual v_xarope dá a velocidade de ar de 1,3–2 m/s que o Ito pede?** → **nenhuma.**

## 1. A descoberta: o bico passa VAZÃO TOTAL CONSTANTE

| v_xarope (4") | v_ar (CFD) | Q_xarope | Q_ar | **Q_TOTAL** | α (vazio) |
|---|---|---|---|---|---|
| 0,020 m/s | 0,151 m/s | 592 L/h | 619 L/h | **1211 L/h** | 51% |
| 0,010 m/s | 0,225 m/s | 296 L/h | 923 L/h | **1219 L/h** | 76% |

**Q_total varia 0,7%** enquanto o ar dobra. Interpretação física: com a porta de ar (1½", grande) sem
restrição, a pressão no ponto de injeção fica **fixada em ≈ P_ar**; o bico então passa a vazão que
corresponde a esse ΔP. **O ar só ocupa o espaço que o xarope deixa vago.**

## 2. A LEI (álgebra fechada)

```
v_ar = ( Q_tot − A_4 · v_xarope ) / A_ar          Q_tot = Q_tot(P_ar, bico)

a 1 kgf/cm²:   v_ar = 0,296 − 7,209 · v_xarope      [m/s]
```
Ajuste: erro de **0,4–0,7%** nos dois pontos de CFD.

- **Corte** (ar para de entrar): v_x = **0,041 m/s** (analítico independente dava 0,046 ✅)
- **Teto absoluto a 1 kgf** (xarope = 0): **v_ar = 0,296 m/s**
- ⚠️ **Previsão a validar:** v_x = 0,005 m/s → **v_ar = 0,260 m/s**. *(2 pontos definem uma reta; este 3º
  ponto confirma o modelo. Rodar antes de fechar com o cliente.)*

## 3. A resposta à pergunta do Ito

**Meta: ar a 1,3–2,0 m/s. Teto físico a 1 kgf: 0,296 m/s.**
→ a meta está **4,4× a 6,8× acima** do máximo alcançável — **mesmo com vazão de xarope ZERO**.

Pressão de ar necessária (Q ∝ ΔP no laminar), **ainda com xarope ~zero**:
| meta v_ar | P_ar necessária |
|---|---|
| 1,3 m/s | **431 kPa ≈ 4,4 kgf/cm²** |
| 2,0 m/s | **663 kPa ≈ 6,8 kgf/cm²** |

## 4. ❌ RETRATAÇÃO — a "janela vazia" estava ERRADA

> Numa versão anterior deste doc eu afirmei que o ar **subiria** de volta pelo tubo (bolha de Taylor a
> 0,284 m/s) e que existiria uma "janela vazia" de 7×. **Isso está errado.** O Gabriel observou na
> simulação que **o ar desce claramente até o bico** — e ele está certo.

**Onde errei:** assumi que o ar formaria uma **bolha de Taylor** (ocupando todo o tubo Ø102). A velocidade
de subida escala com **d²** (Stokes), então o tamanho manda:

| d da bolha | v_subida | vs xarope a 10 mm/s |
|---|---|---|
| 2 mm | 0,4 mm/s | **desce** |
| 5 mm | 2,7 mm/s | **desce** |
| 10 mm | 11 mm/s | limiar |
| ≥20 mm | 44–284 mm/s | subiria |

O ar entra como **jato/dedo contínuo** pela porta (com quantidade de movimento própria), não como bolhas
grandes soltas — e o escoamento **acelera** na direção do bico (10 → 18 → 39 mm/s na redução → **758 mm/s
dentro dos furos**), arrastando tudo para baixo.

**Pior: eu ignorei meu próprio dado.** O `Q_tot = Q_xarope + Q_ar` ficou **constante (0,7%)** nos dois casos
— isso só fecha em **regime permanente com todo o ar saindo pelo bico**. Se o ar subisse, ele **acumularia**
(o `Xarope_in` é velocity inlet, não deixa sair) e o hold-up cresceria sem parar. **O dado já dizia que o ar
desce; eu não cruzei essa informação.** Lição: cruzar conclusão nova com o balanço de massa antes de publicar.

## 5. Conclusão para o cliente (corrigida)

O ar **entra e chega ao bico** — mas só num regime muito distante do projeto:

- Na vazão de projeto (v_x=1,10 m/s / 130 m³/h) o ar **não entra**: contrapressão ~30 bar vs 1–3 kgf.
- Na vazão em que entra (v_x < 0,041 m/s, ~24× menor), o ar chega ao bico e é cisalhado ✅ —
  **mas a velocidade de ar satura em 0,296 m/s**, contra a meta de 1,3–2,0 m/s do Ito (4,4–6,8× abaixo).

**O limite não é o transporte do ar — é a pressão.** Para ter simultaneamente vazão de processo e ar na
velocidade-alvo, faltam pressão de ar e/ou área de passagem no bico.

### Alavancas (o que mudaria o quadro)
1. **Furos maiores** (4×Ø15 já dá +59% de área → contrapressão cai ~; recalcular) ou mais furos.
2. **Pressão de ar maior** (≥4,4 kgf/cm² = compressor, não soprador).
3. **Injetar o ar a JUSANTE do bico** (na região de baixa pressão), não a montante.
4. **Reduzir a viscosidade** (temperatura/diluição) — a contrapressão é ∝ μ.

*(1) e (3) são as mais baratas. Vale rodar o 4×Ø15 no mesmo domínio para quantificar.*

---

# 6. ✅ VALIDAÇÃO (3º ponto) e a FÓRMULA DE PROJETO

## 6.1 O 3º ponto: previ 0,260 · saiu ~0,30 (erro 16%)
Rodada a v_x=0,005 **parou em t=0,031 s ainda decaindo** (as outras rodaram até 0,2 e 0,52 s).
Duas extrapolações independentes concordam: **v_ar_∞ ≈ 0,30 m/s**
(analogia com o decaimento do caso 0,010 → 0,301 · ajuste exponencial da cauda → 0,302, τ=8,3 ms).
⚠️ **Rodar até ~0,2 s para confirmar.**

A lei linear (Q_tot constante) **subestima** em 16% no extremo → Q_tot **não** é exatamente constante.

## 6.2 O que os 3 pontos revelam: a viscosidade EFETIVA é a do xarope puro
| v_x | α (vazio) | Q_tot | **μ_efetiva** |
|---|---|---|---|
| 0,020 | 51% | 336 mL/s | 7,30 Pa·s |
| 0,010 | 76% | 339 mL/s | 7,25 Pa·s |
| 0,005 | 89% | 384 mL/s | 6,39 Pa·s |

**μ_efetiva ≈ 6,5 Pa·s = a do xarope PURO, mesmo com 89% de ar.** O ar **não alivia** a resistência —
o xarope molha a parede do furo e **manda sozinho** na perda de carga (escoamento segregado/anular,
não mistura homogênea). Por isso a vazão total quase não muda.

## 6.3 A FÓRMULA DE PROJETO (1º princípios, validada)
```
Q_tot = P_ar · N · π · D⁴ / (128 · μ · L)        v_ar_max = Q_tot / A_ar
```
Para 7×Ø9 @1 kgf: **378 mL/s → v_ar_max = 0,331 m/s** — bate com o CFD (336–384 mL/s). ✅

**A alavanca é D⁴** (diâmetro do furo à QUARTA potência).

## 6.4 🎯 O ACHADO: o bico **4×Ø15 do desenho de peça ALCANÇA a meta**
`N·D⁴`: 7×Ø9 = 45.927 · **4×Ø15 = 202.500** → **4,41× mais vazão**

| | 7×Ø9 (modelo 3D) | **4×Ø15 (desenho de peça)** |
|---|---|---|
| **teto de v_ar @1 kgf** | 0,33 m/s ❌ | **1,46 m/s ✅ (meta 1,3–2,0)** |
| vazão que deixa o ar entrar | 5,4 m³/h total | **24,0 m³/h total** |
| contrapressão @ vazão de projeto | 23,4 bar | **5,3 bar** |

> **A divergência dos dois desenhos NÃO é detalhe — é a diferença entre bater e não bater a meta do Ito.**
> E o **4×Ø15 é o desenho MAIS NOVO** (22/07/2023 vs 13/03/2023): tudo indica que a revisão foi feita
> **exatamente para resolver isso**. Precisamos confirmar **qual bico está instalado**.

## 6.5 O que ainda não fecha
Mesmo com 4×Ø15, na **vazão de projeto** (32,5 m³/h/lança) a contrapressão é **5,3 bar** — ainda acima
de 1–3 kgf. Para o ar entrar, a vazão precisa cair para **6 m³/h/lança (24 total)** — 5,4× menos que 130.
**Confirmar com o Ito a vazão real de operação por lança.**
