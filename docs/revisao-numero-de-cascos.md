# Revisão final — o custo que o modelo não vê

Duas perguntas ficaram em aberto no fecho do estudo. Esta resolve as duas.

## 1. O teto do DOE custou alguma coisa? Não.

`N_estagios` encostou em 260, o teto da faixa amostrada, o que levantava a
suspeita de que o ótimo verdadeiro estivesse além. Varrendo com o gêmeo, à
pureza fixa de 99,72 % e achando o refluxo mínimo em cada caso:

| N | R mínimo | Q refervedor | Altura | Cascos | Lucro |
|---|---|---|---|---|---|
| 220 | 16,94 | 47,4 MW | 159 m | 3 | 63,08 |
| **240** | **16,25** | **45,6 MW** | **173 m** | **3** | **63,44** |
| 260 | 15,69 | 44,1 MW | 187 m | 4 | 63,49 |
| 280 | 15,28 | 43,0 MW | 201 m | 4 | 63,60 |
| **300** | 14,95 | 42,1 MW | 215 m | 4 | **63,67** |
| 350 | 14,32 | 40,5 MW | 251 m | 5 | 63,42 |
| 400 | 13,88 | 39,3 MW | 286 m | 5 | 63,21 |
| 500 | 13,35 | 37,9 MW | 357 m | 6 | 62,29 |

O ótimo está em N = 300, com **63,67** contra 63,49 do teto — ganho de
**0,18 MUSD/ano, 0,3 %**. A curva vira e cai depois disso.

**Não vale rodar outro DOE.** A resposta anterior estava a três décimos de por
cento do ótimo, e a faixa de 100 a 260 era adequada.

## 2. Mas o modelo aponta para uma coluna que ninguém constrói

O custeio calcula o casco por diâmetro e altura, e divide em cascos quando passa
de 60 m. O que ele **não** custeia é tudo que vem junto com mais um casco:

- fundação e estrutura do casco adicional;
- tubulação de interligação de grande diâmetro entre os cascos;
- bombeamento do líquido de um casco ao outro — cerca de 50 m de elevação;
- área de terreno, acessos e estrutura de manutenção.

Nada disso entra em `CUSTO_CASCO`.

### O ponto de equilíbrio do quarto casco

| | Melhor com 3 cascos | Melhor com 4 cascos |
|---|---|---|
| Configuração | N = 240 · R = 16,25 | N = 300 · R = 14,95 |
| Lucro | 63,44 MUSD/ano | 63,67 MUSD/ano |

O quarto casco vale **0,23 MUSD/ano**. Anualizando pelo fator de recuperação de
capital (0,1315), ele só se paga se custar menos que:

$$\\frac{0{,}23}{0{,}1315} = 1{,}72 \\text{ MUSD de capital adicional}$$

Fundação, estrutura, interligação de grande diâmetro e bombeamento entre cascos
custam realisticamente **de 3 a 8 MUSD**. O quarto casco **não se paga.**

> **O modelo aponta para colunas mais altas do que se constrói porque não paga o
> preço de dividi-las.** É uma limitação de escopo do custeio, não um erro de
> cálculo — e o remédio é reconhecê-la, não refinar o otimizador.

Splitters C3 reais têm 2 a 3 cascos. Com 4 já se está no limite do praticável.

## Projeto final revisado

| Parâmetro | Valor |
|---|---|
| Estágios teóricos | **240** (241 no DWSIM) |
| Estágio de alimentação | **159** (0,664 × 240) |
| Razão de refluxo | **16,25** |
| Corte | 99,90 % |
| Pressão | 16,62 bar |
| Pureza de topo | 99,72 % |
| Recuperação de propeno | 99,62 % |
| Carga do refervedor | 45,58 MW |
| Altura | 173 m em **3 cascos** |
| Lucro | **63,44 MUSD/ano** |

Robustez na faixa de alimentação:

| z propeno | 0,60 | 0,70 | 0,75 | 0,80 | 0,90 |
|---|---|---|---|---|---|
| Pureza de topo | **99,53** | 99,67 | 99,72 | 99,77 | 99,87 |

Mantém grau polímero em toda a faixa.

Contra o projeto anterior de 260 estágios e 63,52 MUSD/ano, a revisão troca
**0,08 MUSD/ano de lucro nominal por um casco a menos** — uma coluna que se
constrói, em vez de uma que o modelo prefere.
