# 09 — ACHADO CRÍTICO: o ar não entra no ponto de operação informado

> Resultado do CFD (VOF, nó nativo 7×Ø9), 2 kgf/cm² de ar. Verificado por balanço de massa convergido
> + conta analítica independente. **É o achado que redefine o estudo do ejetor.**

## Bottom line
No ponto de operação informado — **130 m³/h ÷ 4 lanças** (32,5 m³/h/lança), xarope **6,5 Pa·s (~85 °Bx)**,
**bico nativo 7×Ø9** — **o ar NÃO entra**. A pressão do xarope a montante do bico é **~3,04 MPa ≈ 30 bar
≈ 31 kgf/cm²**; o suprimento de ar é **1–3 kgf/cm²** → **10–30× fraco demais**. O xarope tampa a porta de ar.

## Números
| Grandeza | Valor |
|---|---|
| p a montante do bico (CFD, Ar_in = wall) | **3,04 MPa (31 kgf/cm²)** |
| Conta analítica (Hagen-Poiseuille, Ø9, 45 mm, 20 m/s, 6,5 Pa·s) | ~2,6 MPa → **mesma ordem ✅** |
| Suprimento de ar | 0,098 / 0,196 / 0,294 MPa (1/2/3 kgf) |
| Défice | ar é **~10–30×** menor que a contrapressão |
| Balanço de massa | convergido (~3e-5 kg/s) → resultado confiável |

## Causa física e o CATCH-22
Xarope viscoso (6,5 Pa·s) por furos Ø9 = perda de carga enorme (domina o viscoso, ∝ vazão).
**Conflito de projeto:** cisalhar fino (bolha <300 µm) exige **alta velocidade no furo → alta pressão →
o ar não entra**. **Cisalhamento e auto-aspiração de ar brigam entre si** neste bico.

## Envelope (estimativa)
p ∝ vazão (viscoso). Para o ar de 3 kgf entrar (p ≤ 0,294 MPa), a vazão teria que cair para
**~3 m³/h/lança (~10× menos)** — e aí o cisalhamento cai 10× (bolha maior). Ou seja: **ou aera com bolha
grossa a baixa vazão, ou cisalha fino sem conseguir puxar ar.**

## A reframe do estudo
A pergunta deixa de ser "quão fina é a bolha" e passa a ser **"em que condição o ar entra"**.

## O que confirmar com o cliente (Ito) — antes de conclusão final
1. **Pressão real da bomba** (se ~30 bar, o xarope passa; o ar ainda não entra a montante).
2. **Vazão real por bico** — 130 m³/h é tudo pelos bicos ou há bypass/recirculação?
3. **Ar = soprador (1–3 kgf) ou compressor de alta**?
4. **Ponto de injeção do ar** — a montante (alta P, como no CAD) ou num ponto de baixa P?

## Ressalva (protege a análise)
Baseado **nos dados do próprio cliente** (vazão, μ, geometria nativa). Se algum input mudar (vazão por bico,
μ de operação, holes 4×Ø15), o número muda — por isso os 4 pontos acima. O **mecanismo** (contrapressão
barra o ar) é robusto; o **valor exato** depende dos inputs a confirmar.
