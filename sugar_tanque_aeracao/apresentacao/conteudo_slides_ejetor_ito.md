# Conteúdo para os slides — Ejetor acoplado (apresentação Ito)

> Para colar no `Marcos Ito - Sugar.pptx` a partir do slide 17.
> Fonte: `fase2/ejetor/14_NOTA_ejetor_acoplado.md` e `13_RESULTADO_acoplado_etapa0.md`.

---

## SLIDE 1 — O que foi feito

**Título:** Ejetor acoplado ao aerador — modelo único
**Subtítulo:** Eliminando a separação entre os dois modelos anteriores

- **Ejetor, aerador e reator num só domínio de CFD** — antes eram modelos separados, com a
  interface entre eles arbitrada
- Perfil interno do ejetor **levantado cota a cota no CAD** e conferido contra a lista de peças:
  coletor 8" Sch40 · ramais 4" Sch40 · garganta 2" **Sch160** (Ø 42,8 mm) · bico 7×Ø9 em PCD Ø27
  · linha de ar **1/2"** (Ø 15,8 mm)
- As 3 lanças anteriores substituídas por **4 conjuntos ejetor + lança**, mantidas a cota de
  descarga (6,47 m de submergência) e as proporções do CAD
- Domínio: **169,4 m³** · malha de **5,16 milhões de células** · refino de 1,0 mm nos bicos

> 🖼️ *Figura: vista do domínio acoplado (cena `bico_zoom` ou corte vertical)*

---

## SLIDE 2 — A pergunta e o método

**Título:** O ar consegue ser aspirado?
**Subtítulo:** A resposta não depende da modelagem de bolhas

- A questão se decide comparando **duas pressões**: a do xarope na cota da porta de ar × a de
  suprimento do ar comprimido
- Isso **não requer modelo multifásico** → análise conduzida em regime **monofásico, laminar e
  estacionário**, o que elimina incertezas de modelagem e permite **verificação analítica**
- O regime laminar não é simplificação — é o regime:

| trecho | bocal 8" | ramal 4" | garganta 2" | **furos Ø9** | lança |
|---|---|---|---|---|---|
| **Re** | 47 | 23 | 56 | **38** | 38 |

- **Máximo do domínio: Re = 56**, contra Re ≈ 2300 de transição. Não há turbulência a modelar.

---

## SLIDE 3 — Verificação do modelo

**Título:** Quatro verificações independentes

| # | Verificação | Resultado |
|---|---|---|
| 1 | Vazão imposta na entrada de xarope | **130,3 m³/h** ✅ |
| 2 | Velocidade nos furos do bico | **20,55 m/s** — geométrico 20,3 ✅ |
| 3 | Pressão na porta × pressão no ramal | diferença de **0,02 %** ✅ |
| 4 | **Comparação com solução analítica** | CFD 13 % acima do previsto ✅ |

> ⭐ **A verificação 4 é a mais relevante.** A solução de Poiseuille, calculada de forma
> totalmente independente do CFD, prevê 23,8 bar. O CFD 3D devolveu 26,9 bar.
>
> **Dois métodos independentes convergem para o mesmo resultado.**

---

## SLIDE 4 — Resultado principal ⭐

**Título:** No ponto de projeto, o ar não entra
**Subtítulo:** 130 m³/h de xarope · ar a 1 kgf/cm²

| | bar (man.) |
|---|---|
| Pressão do xarope na porta de ar | **26,9** |
| Pressão de suprimento do ar | **0,98** |
| **Déficit** | **26,0** |

- A pressão do xarope na porta é **14 vezes** a do ar disponível
- Nessa condição o escoamento na linha de ar é **no sentido inverso** — xarope entrando na
  tubulação de ar

> 🖼️ *Figura: cena `pressao_ejetor`, range 1,0e5 a 2,5e6 Pa. A porta de ar aparece em vermelho.*

---

## SLIDE 5 — Mudar a porta de lugar não resolve ⭐

**Título:** Nenhum ponto de injeção do circuito é viável
**Subtítulo:** Quatro posições, todas medidas

| ponto de injeção | pressão local (bar man.) | recupera |
|---|---|---|
| porta atual — ramal 4" | **26,9** | — |
| garganta do cone | 26,4 | 1,9 % |
| **logo a jusante do bico** *(posição de eductor correta)* | **9,09** | 68 % |
| boca de descarga da lança | 0,69 | — |
| *ar disponível* | *0,98* | |

- A porta está hoje **318 mm a montante** da contração, onde a pressão é máxima. A posição está
  incorreta — mas corrigi-la recupera 68 % e **ainda deixa a pressão 9,3× acima** do ar
- **Motivo:** o ar precisa ser injetado **antes da lança** para ser entregue. E a lança sozinha
  custa **11 bar**

| trecho | bar |
|---|---|
| bico 7×Ø9 | ~13,0 |
| **lança Ø62,7 × 7,09 m** | **11,0** |

> Existe um ponto onde o ar entraria: os **últimos 22 cm da lança**. Ali não há comprimento
> remanescente para cisalhar — o equipamento vira um **sparger**, com bolha grossa.

---

## SLIDE 6 — Por quê: a viscosidade

**Título:** A energia que geraria a sucção vira calor

- Um eductor funciona convertendo **energia cinética do jato em depressão** (Bernoulli)
- No xarope a 6,5 Pa·s, medimos essa conversão:

| | bar |
|---|---|
| recuperação de pressão **ideal** (½ρ·Δv²) | 2,48 |
| recuperação **medida** | **0,68** |
| **dissipado por viscosidade** | **73 %** |

- A 6,5 Pa·s todo o circuito é **Poiseuille laminar** — a perda por atrito domina e o efeito de
  Bernoulli não chega a se estabelecer
- **É a causa raiz.** A posição da porta agrava; a viscosidade inviabiliza

---

## SLIDE 7 — Pressão requerida da bomba

**Título:** O que o sistema exigiria para operar como projetado

- Para entregar **130 m³/h** através deste ejetor, a bomba precisa desenvolver **26,9 bar** na
  descarga

| trecho | bar |
|---|---|
| bico — 7 furos Ø9 mm | ~13,0 |
| lança — Ø62,7 × 7,09 m | 11,0 |
| demais trechos e hidrostática | ~2,9 |

---

## SLIDE 8 — As duas condições de operação ⭐

**Título:** O que o resultado significa na planta

**(a)** A bomba desenvolve ~27 bar e entrega 130 m³/h
→ o ar **não entra**, e não há aeração pelo ejetor

**(b)** A bomba desenvolve uma pressão usual de processo (4 a 6 bar)
→ a vazão real é **substancialmente menor** que 130 m³/h, e a pressão na porta cai junto

- A condição **(b)** é **compatível com o vácuo observado por vocês** na linha de ar: vácuo
  requer pressão local abaixo da atmosférica, o que só ocorre a vazões muito inferiores à de projeto
- **As duas informações não se contradizem** — juntas indicam que a **vazão real de operação é
  menor que a de projeto**

---

## SLIDE 9 — Informações para fechar a análise

**Título:** O que precisamos da Ito

| # | Informação | Por quê |
|---|---|---|
| 1 | **Curva ou pressão de descarga da bomba** | define onde o sistema realmente opera |
| 2 | **Vazão medida de xarope**, se houver instrumento | diz qual das duas condições é a real |
| 3 | **Vazão de ar medida**, se houver | permite calibrar em vez de prescrever |
| 4 | **Pressão medida na linha de ar** junto à válvula | confirma ou refuta o vácuo, com número |

---

## SLIDE 10 — Premissas e limitações

- Vazão de xarope **imposta** em 130 m³/h (informação Ito, 15/07). A bomba não está modelada
- Xarope: µ = 6,5 Pa·s · ρ = 1350 kg/m³ · isotérmico
  *(a pressão calculada **independe da densidade** — em laminar depende só da viscosidade)*
- Posição radial das 4 lanças: fileira centrada no eixo do aerador. O CAD de conjunto não define
  a orientação
- Superfícies livres tratadas como tampa rígida; a sucção da bomba não integra o domínio
- Análise monofásica: quantifica **se** o ar entra, não o tamanho de bolha resultante

---

# ⚠️ NOTA PARA O GABRIEL — não vai para o slide

Os números acima são os da rodada **monofásica convergida e validada** (P = 26,9 bar).

A rodada **EMP** deu 30,18 bar — **+12 %**. A explicação aritmética mais provável é que a
monofásica rodou a **v = 1,00 m/s** e a EMP a 1,12 m/s (`30,18 × 1,00/1,12 = 26,95`, contra
26,94 medido).

**Falta ler `mx_in` na EMP:**
- **−48,8 kg/s** → a EMP está no ponto de projeto e **todos os números destes slides sobem 12 %**
  (26,9 → 30,2 · déficit 26,0 → 29,2 · razão 14× → 15,6× · 9,09 → 10,2)
- **−43,4 kg/s** → as duas estão na mesma vazão e a diferença é outra coisa

**Nenhuma conclusão muda** — só ficam mais desfavoráveis ao ejetor. Mas confira antes de
apresentar, porque a nota afirma 130 m³/h explicitamente.
