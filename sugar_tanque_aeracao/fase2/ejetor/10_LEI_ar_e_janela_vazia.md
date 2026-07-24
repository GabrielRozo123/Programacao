# 10 — A LEI do arraste de ar (álgebra calibrada por CFD) e a JANELA VAZIA

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

## 4. A JANELA VAZIA (o achado decisivo)

Duas condições precisam valer ao mesmo tempo — e **não se cruzam**:

| Condição | Requisito | Origem |
|---|---|---|
| **(a) o ar ENTRA** | v_xarope **< 0,041 m/s** | contrapressão do bico < P_ar |
| **(b) o ar é ARRASTADO até o bico** | v_xarope **> 0,284 m/s** | bolha de Taylor **sobe** a 0,284 m/s no tubo 4" (Nf=20,5 → Fr=0,283) |

**Gap de 7×.** Na faixa onde o ar entra, ele **sobe de volta pelo tubo** em vez de descer ao bico —
exatamente o que a cena `VF de Ar` mostra (dedo de ar subindo contra o escoamento).
A v_x=0,284 m/s (para arrastar), a contrapressão seria **6,3 bar** — 6× o suprimento de ar.

## 5. Conclusão para o cliente

Com **esta geometria** (bico 7×Ø9) e **este xarope** (6,5 Pa·s), o ejetor **não consegue** operar como
auto-aspirante: ou o ar não entra (vazão de projeto), ou entra mas não é levado ao bico (vazão baixa).
**Não é ajuste de operação — é limite físico da combinação bico × viscosidade × pressão de ar.**

### Alavancas (o que mudaria o quadro)
1. **Furos maiores** (4×Ø15 já dá +59% de área → contrapressão cai ~; recalcular) ou mais furos.
2. **Pressão de ar maior** (≥4,4 kgf/cm² = compressor, não soprador).
3. **Injetar o ar a JUSANTE do bico** (na região de baixa pressão), não a montante.
4. **Reduzir a viscosidade** (temperatura/diluição) — a contrapressão é ∝ μ.

*(1) e (3) são as mais baratas. Vale rodar o 4×Ø15 no mesmo domínio para quantificar.*
