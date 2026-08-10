# Apresentação — Ciclone de separação de char · Valgroup

> Dez slides a partir do `relatorio/RELATORIO_FINAL_ciclone.md`.
> Figuras indicadas onde carregam a mensagem.

---

# SLIDE 1 — O que foi feito

## Título
**Dimensionamento e verificação por CFD do ciclone de char**

- Ciclone **Stairmand alta eficiência**, dimensionado para a corrente de gás de pirólise
- Verificação em **CFD 3D** (Simcenter STAR-CCM+): escoamento, troca térmica e rastreamento
  de partícula
- **Duas condições de operação**: 100 % e 50 % da vazão nominal
- Resultado entregue: **queda de pressão**, **temperatura de parede** e **curva de eficiência
  de coleta por tamanho de partícula**

> 🖼️ *Figura: render da geometria do ciclone*

---

# SLIDE 2 — A geometria

## Título
**Stairmand HE · D_c = 307 mm**

| cota | mm |
|---|---|
| Diâmetro do corpo | **307** |
| Entrada (a × b) | 153,5 × 61,4 |
| Duto de saída de gás | 153,5 |
| Altura total | 1.228 |
| Saída de pó | 115 |

**Por que 307 e não 290:**

| cenário de modelo de turbulência | D_c = 290 | **D_c = 307** |
|---|---|---|
| base | 31,3 mbar | **19,6 mbar** |
| conservador | 37,0 mbar | 23,1 mbar |
| mais conservador | **43,5 mbar** 🔴 excede | **27,2 mbar** ✅ |

> Aumentar 6 % no diâmetro custa **≤ 4 pontos** de eficiência em 10 µm e converte uma folga
> negativa em **32 %**.

---

# SLIDE 3 — Queda de pressão ⭐

## Título
**19,6 mbar — folga de 51 % sobre o limite**

| carga | v entrada | **ΔP** |
|---|---|---|
| **100 %** | 13,59 m/s | **19,6 mbar** |
| **50 %** | 6,80 m/s | **4,7 mbar** |

| | |
|---|---|
| Limite de projeto | 40 mbar |
| **Folga** | **51 %** |
| Folga no cenário mais conservador de turbulência | **32 %** |

> A margem foi verificada contra o cenário de modelo que **mais** superestima a perda.
> O ciclone atende em todos eles.

---

# SLIDE 4 — Temperatura de parede

## Título
**A parede opera entre 305 e 397 °C**

| carga | T_parede medida |
|---|---|
| 100 % | **378,5 °C** |
| 50 % | **363,7 °C** |

**A condição de 50 % é a governante:** o tempo de residência dobra e a troca interna cai — o gás
troca calor por mais tempo através de um filme mais fraco, e a parede esfria.

**Projeção conforme o isolamento** (modelo calibrado, dispensa nova simulação):

| | isolada | **sem isolamento** |
|---|---|---|
| 100 % | 397 °C | 340 °C |
| **50 %** | 394 °C | **305 °C** |

> ⚠️ O critério de comparação — o **ponto de orvalho** — depende da composição real da corrente,
> que está em revisão. Ver slide 10.

---

# SLIDE 5 — Curva de eficiência de coleta ⭐

## Título
**Diâmetro de corte: 6,8 µm a plena carga**

> 🖼️ **FIGURA PRINCIPAL:** `curva_eta_x_d.png` — 20 pontos medidos, duas cargas

| d (µm) | η · 100 % | η · 50 % |
|---|---|---|
| 5 | 31 % | 26 % |
| **10** | **79 %** | **50 %** |
| 20 | 100 % | 95 % |
| ≥ 50 | 100 % | 100 % |

| | d\* |
|---|---|
| 100 % de vazão | **6,84 µm** |
| 50 % de vazão | **9,90 µm** |

**Em turndown a perda se concentra entre 5 e 20 µm** — fora dessa janela é praticamente nula.

---

# SLIDE 6 — Verificação do modelo

## Título
**Três verificações independentes**

| # | verificação | resultado |
|---|---|---|
| **1** | Razão dos diâmetros de corte entre as duas cargas, **CFD × solução analítica** | **2,4 %** |
| **2** | Temperatura de parede a 50 % **prevista antes de medir** | **0,3 °C** |
| **3** | Sensibilidade ao modelo de dispersão turbulenta | **0,19 ponto** |

> A verificação **1** é a mais relevante: o modelo discorda da correlação clássica em 17 % no
> *valor* do corte, mas concorda em 2,4 % em *como* a separação responde à vazão.
> **Um erro de modelagem raramente preserva a derivada.**

**Por que o corte é mais fino que a correlação prevê:** a correlação de Lapple adota **6 voltas
efetivas** — valor tabelado. O campo resolvido no CFD corresponde a **8,8 voltas**, dentro da
faixa de 5 a 10 reportada na literatura para ciclones de alta eficiência.

---

# SLIDE 7 — Eficiência global ⭐

## Título
**Com a granulometria disponível: 100 %**

A análise granulométrica fornecida tem estas faixas:

| faixa | fração |
|---|---|
| 61 a 12.500 µm *(seis faixas)* | **90,86 %** |
| **abaixo de 61 µm — fundo de peneira** | **9,14 %** |

**Todas as faixas medidas caem na região onde a eficiência é 100 %.**

> ⇒ **Toda a resposta do estudo depende dos 9,14 % de fundo de peneira**, cuja distribuição
> interna não foi determinada.

---

# SLIDE 8 — O que decide o número ⭐

## Título
**A eficiência garantida depende de uma medição que falta**

| se o fundo de peneira estiver em | eficiência global | char arrastado |
|---|---|---|
| 61 µm *(hipótese da planilha)* | 100,0 % | 0 kg/h |
| 20 µm | 100,0 % | 0,4 kg/h |
| 10 µm | 98,1 % | 3,6 kg/h |
| 5 µm | 93,7 % | 5,4 kg/h |
| **1 µm** | **92,9 %** | **5,7 kg/h** |

**Piso de 92,9 %** em qualquer cenário e em qualquer carga.

> A caracterização atual é por **peneiramento**, que não resolve abaixo de 61 µm. É justamente
> nessa faixa que ocorre a perda de um ciclone.
>
> **Uma análise por difração a laser nessa fração fecha o intervalo.** É o único item com esse
> poder.

---

# SLIDE 9 — Segundo estágio

## Título
**Dois ciclones em série: +1,6 ponto por todo o orçamento de pressão**

| cenário | 1 estágio | 2 em série | ganho |
|---|---|---|---|
| fundo em 1 µm | 92,9 % | 94,5 % | **+1,6 pt** |
| fundo em 5 µm | 93,7 % | 95,7 % | +2,0 pt |

| | ΔP |
|---|---|
| 1 estágio | 19,6 mbar |
| **2 em série** | **39,2 mbar** — folga de **2 %** |
| 2 em série, cenário conservador | **54,4 mbar** 🔴 **excede em 36 %** |

**Por que o ganho é pequeno:** 90,86 % da massa **já é capturada em 100 %**. Apenas os 9,14 %
de fundo estão em disputa.

> **A decisão sobre segundo estágio deve vir depois da difração a laser.** Se o fundo estiver
> acima de 15 µm, o estágio único já entrega ~100 %.

---

# SLIDE 10 — O que precisamos

## Título
**Seis informações para fechar o projeto**

| # | item | decide |
|---|---|---|
| **1** | **Difração a laser na fração < 61 µm** | a eficiência garantida e o segundo estágio |
| **2** | **Composição da corrente (C1–C40)** na saída do reator | o ponto de orvalho e o isolamento |
| **3** | **Meta de eficiência** exigida pelo processo | se o projeto atual basta |
| 4 | Viscosidade do gás — origem do valor 1,0×10⁻⁴ Pa·s | o diâmetro de corte |
| 5 | Massa específica da partícula, por picnometria | o diâmetro de corte |
| 6 | Histórico de incrustação no trecho | risco operacional |

> **Sobre o item 4:** a 400 °C, o metano puro — o hidrocarboneto de maior viscosidade da série —
> fica em ~2×10⁻⁵ Pa·s, e o nitrogênio em ~3×10⁻⁵. Vale conferir a unidade na fonte.
>
> **Sobre o item 5:** a planilha adota 776,75 kg/m³, que é a densidade **do leito**. A própria
> tabela de valores usuais dela declara a faixa **1.500 a 3.000**.

---

# Notas para quem apresenta (não vai no slide)

- **Slides 3, 5, 7 e 8 são o núcleo.** Se o tempo apertar, são esses.
- **O slide 6 é o que dá autoridade ao resto.** As três verificações não são comparação com
  correlação — são o modelo se auditando. Vale gastar um minuto nele.
- **Os slides 7 e 8 formam um par.** O 7 dá a boa notícia (100 % com o dado medido) e o 8
  mostra que ela repousa numa hipótese não medida. Apresentar um sem o outro distorce.
- **Itens 4 e 5 do slide 10 são delicados** — apontam divergência com a planilha do cliente.
  Ambos estão redigidos para que o **documento deles** faça o argumento, não nós.
- **O item 3 (meta de eficiência) nunca foi definido** e não depende de medição nenhuma.
  Sem ele, não há critério para decidir segundo estágio.
