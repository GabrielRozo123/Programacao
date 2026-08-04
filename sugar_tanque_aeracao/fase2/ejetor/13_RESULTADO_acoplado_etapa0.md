# ETAPA 0 — resultado do domínio ACOPLADO, monofásico estacionário

> `ACOPLADO_aerador_reator_ejetor_fluido.step` · 5,16 M células · monofásico · laminar · steady
> Portas de ar como `Wall`; topo do aerador `Wall`+Slip; topo do reator `Pressure Outlet` 0 Pa.
> Setup completo em `geometria/SETUP_star_acoplado.md` §17.3.

---

## 1. Validação — na ordem, cada um habilita o seguinte

| # | Report | Medido | Esperado | Veredito |
|---|---|---|---|---|
| 1 | `mx_in` | **−43,43 kg/s** | −46,9 (com ρ=1300) | ✅ ver §1.1 |
| 2 | `v_bico` | **20,55 m/s** | 20,32 axial | ✅ +1,1 % |
| 3 | `P_ramal_port` vs `P_porta_ar` | 2,79529e6 vs 2,79584e6 | iguais | ✅ **0,02 %** |
| 4 | `P_porta_ar` | **2,79584e6 Pa abs** | 2,48e6 (Poiseuille) | ✅ +12,7 % |

### 1.1 A densidade — por que `mx_in` deu 7,4 % abaixo
```
43,43 / (1,12 m/s × 0,032273 m²) = 1201 kg/m³
```
A sim está com **ρ ≈ 1200**, não 1300. Confirmado independentemente pelo `v_bico`:
com ρ=1200, Q = 0,036192 m³/s → 20,32 m/s axial nos 28 furos, contra 20,55 de magnitude medida
(+1,1 %, que é a diferença esperada entre média de magnitude e média axial).
Com ρ=1300 a discrepância seria de 8,7 % e a massa **não conservaria**.

⇒ **A vazão volumétrica está correta: 130,3 m³/h.** ✅

⇒ **E não afeta o resultado de pressão:** em laminar `Δp = 32µLv/D²` **não depende de ρ**.
A densidade só entra na hidrostática (0,82 bar de 27).

### 1.2 Coerência interna
`P_ramal_port` (plano no ramal 4") e `P_porta_ar` (face da boundary, fundo cego de 250 mm)
diferem em **550 Pa = 0,02 %** — exatamente como tem de ser num fundo cego horizontal
com líquido parado.

### 1.3 Validação cruzada com o analítico
A previsão de Poiseuille (`SETUP_star_acoplado.md` §14.2) dava **2,48e6 Pa abs**.
O CFD 3D deu **2,796e6** — **+12,7 %**, e na direção certa: a conta à mão ignorava efeitos de
entrada, a perda na contração 4"→2" e a distribuição no coletor de 7 furos.

> **Dois métodos independentes concordando dentro de 13 %.**

---

## 2. ⭐ O RESULTADO

| | Pa abs | bar man. |
|---|---|---|
| **Pressão do xarope na porta de ar** | **2.795.840** | **26,9** |
| Suprimento de ar (1 kgf/cm²) | 199.392 | 0,98 |
| **DÉFICIT** | **2.596.448** | **26,0** |

**Razão: 14,0×.** O ar não tem como entrar.

---

## 3. ⭐ Mover a porta de ar NÃO resolve — o número

```
P_porta_ar − P_garganta = 2,79584e6 − 2,74645e6 = 49.390 Pa = 0,49 bar
```

Esse é o ganho **total** de levar a porta dos atuais 318 mm a montante até **dentro da garganta**
— a posição de eductor correta.

| | |
|---|---|
| ganho de reposicionar a porta | **0,49 bar** |
| déficit a vencer | **26,0 bar** |
| **recuperação** | **1,9 %** |

> **A porta no lugar errado é real, mas NÃO é a causa raiz.** A causa é a **viscosidade**:
> a 6,5 Pa·s tudo é Poiseuille, o atrito domina qualquer efeito de Bernoulli, e nenhum
> reposicionamento de porta muda isso.
>
> Isso preempta a objeção mais natural — *"então é só mudar a porta de lugar"*.

---

## 4. A resposta à pendência nº 1 com o Ito

`P_bomba` = **2.795.770 Pa abs = 26,9 bar man.**

É a **pressão de descarga que a bomba precisaria ter** para entregar 130 m³/h por este ejetor.
Era a pergunta nº 1 de `REUNIAO_ITO_prep.md` — agora respondida pelo modelo em vez de perguntada.

> **Desdobramento:** se a bomba real da Colombo fizer 4–5 bar, os **130 m³/h nunca existiram**.
> A vazão real seria muito menor — o que **reconcilia com o vácuo que o Ito observa**
> (`11_LEI_MESTRA_P_vs_v.md` §12: *"se o Ito realmente observa vácuo, a vazão real não pode
> ser 130 m³/h"*).

---

## 5. Pendências desta rodada
- [ ] Resíduos caíram ≥ 3 ordens?
- [ ] Rodar até ~300 iterações (fechou com 40 — pouco para 5,16 M células) e confirmar
      que `P_porta_ar` não se move
- [ ] `Mass Flow` em `superficie_reator` = **+43,43 kg/s** (fecha o balanço)
- [ ] Confirmar a densidade no material: 1200 ou 1300?

## 6. Próximo passo natural
Report de **pressão logo abaixo da saída do bico** (plano em z = 1,8395, dentro da lança Ø62,7):
dá a pressão no ponto **mais favorável possível** de todo o caminho de entrega. Se nem ali a
pressão cair abaixo de 199.392 Pa abs, fica demonstrado que **nenhuma** relocação de porta
funciona — a versão inatacável do §3.
