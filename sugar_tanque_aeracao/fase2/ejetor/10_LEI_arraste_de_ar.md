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
