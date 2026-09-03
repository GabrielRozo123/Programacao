# Viscosidade do gás — os dois valores, para validação com a Valgroup

> Pedido do Marcus (Teams, 4:13 PM): *"Me passa o valor que vc rodou e o valor que
> vc fala que eh o correto pra eu avaliar e validar com eles"*.
>
> Consolida o que já estava disperso em `PEDIDO_valgroup.md` §3,
> `dados_recebidos_15jul.md` §3 e `07_EXECUCAO_lagrangeano_Dc307.md` §9.2.

---

## 1. Os dois valores

| | valor | origem |
|---|---|---|
| **rodado** | **9,5e-5 Pa·s** | planilha Lapple dos colegas da Valgroup |
| **recomendado** | **2,5e-5 Pa·s** | faixa típica 1,5–3,0e-5 para vapor de HC C7–C15 a 340–400 °C |

Razão entre os dois: **3,8×**.

⚠️ A planilha traz **1,0e-4 Pa·s** no cabeçalho e **9,5e-5** no cálculo. São o mesmo
ponto — se o cliente citar 1,0e-4, não é uma terceira fonte.

---

## 2. Impacto

O diâmetro de corte vai com a raiz da viscosidade:

$$d^* \propto \sqrt{\mu} \qquad Re \propto 1/\mu \qquad \Delta P \ \text{quase independente}$$

Na condição rodada (ρ_s = 1500 kg/m³, 100 % de vazão, Dc = 307 mm):

| | rodado (9,5e-5) | corrigido (2,5e-5) |
|---|---|---|
| **diâmetro de corte d\*** | **8,28 µm** | **4,25 µm** |
| Reynolds na entrada | 173 341 | 658 714 |
| perda de carga | 1 955,6 Pa (medido) | ~1 910 Pa (previsto, a medir) |

`Re = ṁ·D/(A·µ)` com ṁ = 0,50556 kg/s, D = 0,307 m, A_in = 9,4249e-3 m².

---

## 3. A direção é favorável — e isso é o ponto de comunicação

Com a viscosidade correta o ciclone captura **o dobro de finura**. Tudo que já foi
entregue está na base do cliente e é, portanto, o **pior caso**.

Se eles validarem o 2,5e-5, o resultado **melhora**. Vale dizer isso explicitamente:
a incerteza é unilateral e a favor deles, não é uma acusação de erro.

---

## 4. O que se pede ao cliente

> Qual a origem do 9,5e-5 — medido, tabela, ou qual fluido de referência?

Se for estimativa, fechamos pela composição do GC-MS que eles já enviaram, por
**Wilke/Chung**, e a divergência encerra.

---

## 5. Reserva argumentativa (não enviar)

O 2,5e-5 é o **topo** da faixa, escolhido para ser conservador. Chapman-Enskog com
M = 184 kg/kmol a 673 K, σ ≈ 7,5 Å e ε/k ≈ 500 K:

$$\mu = 2{,}669\text{e-}6\,\frac{\sqrt{MT}}{\sigma^2\Omega} = 2{,}669\text{e-}6\,\frac{351{,}9}{56{,}25 \times 1{,}26} \approx 1{,}3\text{e-}5\ \text{Pa·s}$$

Ou seja, o valor real provavelmente é **ainda menor** que a nossa recomendação. Se
alguém contestar o 2,5e-5 por ser baixo demais, o argumento vai no sentido contrário.

---

## 6. A temperatura move ρ e µ juntos — e eles quase se cancelam

Marcus perguntou depois a massa específica rodada: **3,946 kg/m³**. Esse valor
**não está em disputa** (nossa planilha e a dos colegas coincidem) e não é hipótese
independente — sai de gás ideal com três inputs do cliente:

$$\rho = \frac{PM}{RT} = \frac{120\,000 \times 184}{8\,314 \times 673{,}15} = 3{,}946\ \text{kg/m³}$$

(1,2 bar · 400 °C · M = 184 kg/kmol)

O que pode mexer nesse número não é a densidade, é a **temperatura**: o TT-209 marca
**~343 °C**, não 400 (`PEDIDO_valgroup.md` §4).

| | 400 °C (rodado) | 343 °C (TT-209) | variação |
|---|---|---|---|
| ρ | 3,946 kg/m³ | **4,310 kg/m³** | **+9,2 %** |
| µ (∝ T^0,7) | — | — | **−6,0 %** |
| **d\*** (∝ √(ρµ)) | — | — | **+1,3 %** |

Os +9,2 % em ρ são **maiores que os ±5 % já testados**, mas a µ cai junto e o
diâmetro de corte, que vai com `√(ρ·µ)`, praticamente não se move.

**Consequência para a hierarquia das pendências:** a temperatura é mais alavancada
que a densidade isolada, porque move as duas propriedades — e move em sentidos
opostos. Confirmar **onde o ciclone entra na linha** encerra ρ e µ de uma vez.

---

## 7. Não muda o escopo

A rodada planejada continua sendo **uma só**: ρ −5 % + µ = 2,5e-5, com as previsões
já registradas antes de rodar — ξ ≈ 4,98 · ΔP ≈ 1 910 Pa · d\* = 3,42 µm ·
Re = 658 703.
