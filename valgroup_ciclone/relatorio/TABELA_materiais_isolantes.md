# Materiais isolantes — exemplos para o slide (Valgroup · ciclone)

> Pedido do Marcus. Calculado pelo mesmo critério de resistências em série do bloco
> térmico (`slides_termica_orvalho.md`), na condição governante: **50 % de vazão,
> h_i = 93,4 W/m²·K no corpo**, gás a 400 °C, ambiente a 25 °C, chapa de aço carbono
> de 6 mm, jaqueta externa de alumínio (ε = 0,20).

---

## 1. O achado que simplifica a escolha

| configuração | k (W/m·K) | espessura | **T do metal** | T externa | perda |
|---|---|---|---|---|---|
| **sem isolamento** — aço oxidado | — | — | **317,8 °C** | 316,8 °C | 7 673 W/m² |
| **sem isolamento** — refletivo | — | — | **362,4 °C** | 361,9 °C | 3 510 W/m² |
| lã de rocha 50 mm | 0,055 | 50 mm | **396,3 °C** | 78,7 °C | 349 W/m² |
| silicato de cálcio 50 mm | 0,080 | 50 mm | **394,8 °C** | 93,5 °C | 482 W/m² |
| manta de aerogel 20 mm | 0,022 | 20 mm | **396,3 °C** | 78,7 °C | 349 W/m² |

> **Os três isolantes dão a mesma temperatura de metal: 395 a 396 °C.**
>
> O motivo: a resistência do isolante (0,6 a 0,9 m²·K/W) é **sessenta vezes** a
> resistência convectiva interna (1/93,4 = 0,011). Com qualquer isolante razoável o
> metal assume a temperatura do gás, e a espessura muda pouco.

**Consequência para o cliente:** a escolha do isolante **não é decidida pela
condensação** — qualquer um dos três resolve, com folga de 50 °C sobre a hipótese
mais severa de orvalho (343 °C). A escolha é decidida por espessura disponível,
segurança de contato e custo.

---

## 2. O critério que de fato diferencia — face externa

Superfície tocável deve ficar em **60 °C** (limite usual de contato).

| material | k | **espessura para 60 °C** | T do metal | T externa | perda |
|---|---|---|---|---|---|
| **lã de rocha** | 0,055 | **95 mm** | 397,9 °C | 59,4 °C | 196 W/m² |
| **silicato de cálcio** | 0,080 | **140 mm** | 397,9 °C | 59,1 °C | 194 W/m² |
| **manta de aerogel** | 0,022 | **40 mm** | 398,0 °C | 58,2 °C | 187 W/m² |

---

## 3. Os três, comparados

| | **lã de rocha** | **silicato de cálcio** | **manta de aerogel** |
|---|---|---|---|
| condutividade a 300 °C | 0,055 W/m·K | 0,080 W/m·K | 0,022 W/m·K |
| espessura para 60 °C externos | 95 mm | 140 mm | **40 mm** |
| temperatura máxima de serviço | ~650 °C | ~1 000 °C | ~650 °C |
| forma | manta flexível | placa rígida pré-moldada | manta fina flexível |
| custo relativo | **baixo** | médio | alto |
| **melhor para** | uso geral, superfície cilíndrica | onde precisa de resistência mecânica | **onde falta espaço** |

**Recomendação:** **lã de rocha, 95 mm**, para o corpo. É a solução padrão para esta
faixa de temperatura, a mais barata, e a espessura cabe sem conflito.

O **aerogel** só se justifica onde houver restrição de envelope — ele entrega o mesmo
com 40 mm, mas a um custo bem superior.

O **silicato de cálcio** entra se houver necessidade de resistência mecânica
(caminhamento, apoio) ou temperatura acima de 650 °C, que não é o caso aqui.

---

## 4. Onde aplicar — a configuração D continua valendo

Isso **não muda** a recomendação do bloco térmico:

| região | tratamento |
|---|---|
| **corpo do ciclone** (92 % da área) | **revestimento refletivo**, sem isolamento — mantém a parede a 362 °C, acima das duas hipóteses de orvalho |
| **trecho inferior** (8 % da área) | **isolamento** — é onde o gás fica quiescente e a parede cai a 290,5 °C |

Os 95 mm de lã de rocha se aplicam **aos 8 % inferiores**, não ao ciclone inteiro.

Isolar tudo levaria a parede a 396 °C em toda parte — funcionaria, mas custaria
isolamento em 100 % da área para resolver um problema que existe em 8 %.

---

## 5. Um ganho lateral que vale mencionar

A perda de calor cai de **7 673 W/m²** (aço oxidado) para **196 W/m²** com isolamento
— **redução de 39 vezes**. Se houver interesse em recuperação térmica a jusante ou
em manter a temperatura da corrente até o próximo equipamento, isso entra na conta.
