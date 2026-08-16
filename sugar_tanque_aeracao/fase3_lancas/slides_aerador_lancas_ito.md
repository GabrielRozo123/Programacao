# Conteúdo dos slides — Aerador com lanças (Fase 3 · Ito)

> 10 slides. Texto pronto para o template CAEXPERTS/Siemens.
> Cada slide traz: título, o que colocar na área visual, e o texto.

---

## Slide 1 — Capa

**Título:** Aeração de xarope por lanças submersas
**Subtítulo:** Análise fluidodinâmica computacional — Fase 3
**Rodapé:** CAEXPERTS · Simcenter STAR-CCM+

---

## Slide 2 — O que foi analisado

**Visual:** vista 3D do aerador com as 16 lanças, tanque transparente.

**Texto:**

Aerador Ø 2 032 mm · 19,99 m³ de xarope · 7,11 m de coluna

**16 lanças de Ø 62,7 mm** em dois anéis, com descarga escalonada:

| | anel interno | anel externo |
|---|---|---|
| lanças | 5 | 11 |
| raio | 375 mm | 770 mm |
| submergência | 6,67 m | 5,88 m |

O fundo cônico impede que os dois anéis desçam à mesma cota. Cada anel foi levado à
profundidade máxima que o perfil permite, com folga verificada ponto a ponto ao longo
de toda a lança.

**Nota de rodapé:** Obstrução introduzida no domínio: 1,5 % da seção do aerador.

---

## Slide 3 — Modelo

**Visual:** corte da malha na região das descargas, mostrando o refino.

**Texto:**

| | |
|---|---|
| solver | Eulerian Multiphase, transiente |
| distribuição de tamanho | S-Gamma com quebra e coalescência |
| malha | trimmed · base 50 mm · refino 12,5 mm nas descargas |
| propriedades | ρ 1 350 kg/m³ · **µ 6,5 Pa·s** · σ 0,058 N/m |

**Verificação de malha:** volume calculado 19,9931 m³ contra 19,991 m³ da geometria —
**desvio de 0,01 %**.

**Frase de destaque:** A viscosidade de 6,5 Pa·s — seis mil vezes a da água — é o que
governa todo o comportamento observado.

---

## Slide 4 — Como o ar se distribui

**Visual:** corte vertical de fração volumétrica de ar em **escala logarítmica**
(1e−4 a 1). É a imagem principal do deck.

**Texto:**

| critério | volume | % do tanque |
|---|---|---|
| xarope alcançado pelo ar | 3,08 m³ | 15,4 % |
| xarope efetivamente aerado (α > 1 %) | 2,14 m³ | 10,7 % |
| **xarope não atingido** | 16,91 m³ | **84,6 %** |
| fração de vazio dentro do volume aerado | — | **47,7 %** |

**Frase de destaque:** O ar ocupa 10,7 % do tanque, e onde está, está a 48 % de vazio.
São cavidades de gás — não uma nuvem de bolhas.

---

## Slide 5 — O ar concentra, não distribui

**Visual:** as duas cenas de fração de vazio lado a lado (instante intermediário e
final), mesma escala.

**Texto:**

| | intermediário | final |
|---|---|---|
| volume aerado | 7,1 % | 10,7 % |
| **vazio dentro do volume aerado** | **32,6 %** | **47,7 %** |

O volume aerado cresceu 50 %. A fração de vazio dentro dele cresceu 46 % **junto**.

**Frase de destaque:** Se houvesse dispersão, a fração interna cairia conforme o
volume crescesse — o mesmo ar em mais xarope. Ocorre o contrário: as cavidades crescem
e adensam simultaneamente.

---

## Slide 6 — Diâmetro de bolha medido

**Visual:** histograma de diâmetro médio de Sauter, ponderado por volume de ar.

**Texto:**

| | |
|---|---|
| SMD mínimo | 0,816 mm |
| **SMD máximo** | **1,000201 mm** |
| valor imposto na entrada | 1,000 mm |
| meta de projeto | **0,2 mm** |

O máximo excede o valor de entrada em **0,0002 mm**.

**Frase de destaque:** A coalescência é nula. A bolha atravessa todo o percurso sem
alterar o tamanho com que se formou.

---

## Slide 7 — Por que a bolha não diminui

**Visual:** tabela abaixo em destaque, sem imagem — é um slide de argumento.

**Texto:**

Quatro mecanismos poderiam reduzir a bolha. Todos estão fora de faixa neste xarope:

| mecanismo | grandeza | valor | resultado |
|---|---|---|---|
| quebra turbulenta | escala de Kolmogorov | 42,7 mm | bolha 43× menor — nulo |
| quebra por cisalhamento | Ca crítico | ≈ 270 | inatingível |
| oscilação de forma | número de Morton | 6,6 × 10⁴ | regime inacessível |
| coalescência | variação medida | +0,0002 mm | desprezível |

**Frase de destaque:** O diâmetro é decidido no instante da formação, junto ao bico. E
nada depois disso o altera.

---

## Slide 8 — O que fixa o diâmetro na formação

**Visual:** esquema simples — dois orifícios lado a lado, um pequeno com bolha
ancorada na borda, um grande com interface plana se fragmentando em ondas.

**Texto:**

Comprimento capilar do xarope: `√(σ/ρg)` = **2,09 mm**
Descarga atual: **Ø 62,7 mm** → **número de Bond = 898**

Acima do comprimento capilar, a interface é larga demais para a borda do furo
sustentar. Ela se comporta como superfície plana e se fragmenta pela instabilidade de
**Rayleigh-Taylor**, no comprimento de onda próprio do fluido:

| | |
|---|---|
| comprimento de onda crítico | 13,1 mm |
| comprimento de onda dominante | 22,8 mm |

**Diâmetro esperado: 13 a 23 mm** — setenta vezes a meta.

**Frase de destaque:** Como o tamanho vem de um comprimento de onda que só depende do
fluido, **nenhum arranjo de lanças o altera** — nem quantidade, nem altura, nem
disposição.

---

## Slide 9 — O caminho técnico

**Visual:** as duas tabelas.

**Texto:**

**Condição 1 — furo abaixo do comprimento capilar**

| furo | Bond | regime | bolha |
|---|---|---|---|
| 0,2 mm | 0,01 | Tate | 1,74 mm |
| 1,0 mm | 0,23 | Tate | 2,97 mm |
| **62,7 mm (atual)** | **898** | **Rayleigh-Taylor** | **13–23 mm** |

A dependência é cúbica — reduzir o furo cinco vezes reduz a bolha menos de duas. Há um
**piso de 1,7 a 3 mm** em borbulhamento.

**Condição 2 — velocidade de jato** (`We_gás > 2`)

Descarga atual: 0,225 m/s, `We_gás` = **0,115** — duas ordens abaixo da transição.

**Condição 3 — uniformidade** (`ΔP furo ≥ 4 × ΔP hidrostático`)

| furos por lança | velocidade | ΔP furo | ΔP hidro | razão |
|---|---|---|---|---|
| 119 | 7,4 m/s | 158 Pa | 596 Pa | 0,3 ✗ |
| **48** | **18,4 m/s** | **990 Pa** | **199 Pa** | **5,0** ✓ |

Furos demais derrubam a velocidade, e o ar passa a sair só pelos de cima.

**Frase de destaque:** Furo pequeno não basta. É preciso furo pequeno, **em regime de
jato**, e **em número limitado** para que a distribuição se mantenha uniforme.

---

## Slide 10 — Conclusões e recomendação

**Texto:**

**O que a análise mostra**

1. As 16 lanças produzem 16 plumas individualizadas, sem fusão entre vizinhas.
2. A aeração ocorre em **regime de segregação**: 84,6 % do xarope não é atingido, e o
   ar forma cavidades a 48 % de vazio.
3. A meta de **0,2 mm não é atingível com descarga aberta**, e a limitação é de
   mecanismo, não de arranjo.

**Recomendação** *(ver figura da lança)*

| | |
|---|---|
| furo | **Ø 1,0 mm** |
| furos por lança | **48** — 2 anéis de 24, passo 9,6 mm |
| velocidade no furo | 18,4 m/s · We = 12,3 · razão de uniformidade 5,0 |
| total no aerador | 768 furos |
| pressão de suprimento | ≈ 0,91 kgf/cm² + perdas |

**Dois requisitos construtivos**

1. **Tampa cega na ponta.** A saída aberta de Ø 62,7 mm tem **82×** a área dos 48
   furos — sem fechá-la, o ar sai todo por ali e a perfuração não faz efeito.
2. **Válvula de retenção por lança.** Capilaridade de **232 Pa** contra **88 334 Pa**
   de coluna: com o ar desligado, o xarope entra e entope os furos.

**Sobre o número de lanças**

O total de furos é fixo: `N × n = Q/(v·A) = 769`, qualquer que seja N. Mais lanças
apenas redistribuem — não mudam bolha, vazão nem velocidade. Mínimo **N = 11** (abaixo
disso os furos não cabem); adotado **16**, já verificado contra o cone.

**Próximo passo de projeto**

Os 84,6 % não atingidos **não** são falta de cobertura lateral — com 16 lanças o
espaçamento é 450 mm e as plumas se tocam. É ausência de transporte vertical, e mais
lanças não corrigem. A alavanca é o **número de cotas de descarga**: 6 a 9 níveis
cobririam a coluna, com grupos de lanças de comprimentos distintos e alimentação
independente por nível.

---

## Rodapé técnico (aplicar em todos os slides de resultado)

> *Os diâmetros de Sauter referem-se à população de bolhas presente no domínio. A
> vazão de ar é resultado da simulação, não dado de entrada.*
