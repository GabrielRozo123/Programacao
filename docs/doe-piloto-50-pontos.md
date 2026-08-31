# DOE piloto — 50 pontos no Python Case

Primeiro lote rodado no AI4Tech Suite, em 31/08/2026. LHS, semente 42,
execução na plataforma. Dados brutos em
[`dados/doe-piloto-50-pontos.csv`](../dados/doe-piloto-50-pontos.csv).

## Aferição

| | |
|---|---|
| Convergência | **50 / 50** (`convergiu` e `Solved`) |
| Tempo por run | ~0,5 s (contra 22 ms local — overhead de subprocesso e rede) |
| Reprodução local | **1150 valores** (50 × 23), **zero divergências** |
| Pior erro relativo | 3,6 × 10⁻¹³ — arredondamento IEEE 754 |

O servidor reproduz o modelo bit a bit em todo o espaço de projeto, não só nos
defaults. É a consequência prática da decisão de zero dependências: sem numpy
nem scipy, não há versão de biblioteca para divergir entre ambientes.

**Dimensionamento do DOE de verdade:** a 0,5 s/run, 1000 pontos levam ~8 min.

## O espaço varrido

| Saída | Mín | Média | Máx |
|---|---|---|---|
| `pureza_topo` (%) | 86,11 | 97,51 | 99,97 |
| `recuperacao` (%) | 84,58 | 96,00 | 99,35 |
| `Q_refervedor` (MW) | 19,57 | 42,71 | 66,40 |
| `lucro` (MUSD/ano) | −78,69 | 20,40 | 85,65 |

Grau do produto: **11 polímero · 37 químico · 2 GLP**. Refrigeração exigida em
16 dos 50. Espaço rico, com o degrau de grau bem representado — bom material
para treinar surrogate.

## ⚠️ O achado: `z_propeno` é distúrbio, não variável de decisão

O melhor ponto do DOE rende 85,6 MUSD/ano. Mas ele está em `z_propeno = 0,897`,
o extremo rico da faixa — **e ninguém escolhe a composição da alimentação.**
Ela vem da unidade a montante.

Correlação com o lucro neste DOE:

| Entrada | Pearson | Spearman |
|---|---|---|
| **`z_propeno`** | **0,479** | **0,576** |
| `pos_alimentacao` | 0,349 | 0,274 |
| `N_estagios` | 0,274 | 0,223 |
| `razao_refluxo` | 0,269 | 0,087 |
| `pressao` | −0,184 | −0,215 |
| `corte_pct` | 0,072 | 0,114 |

`z_propeno` domina tudo. O DOE não está dizendo "este é o melhor projeto" —
está dizendo "alimentação rica dá mais dinheiro", o que é verdade e é inútil.

### E o projeto vencedor é frágil

O mesmo projeto do run 31, sob alimentações diferentes:

| `z_propeno` | Pureza de topo | Lucro | Grau |
|---|---|---|---|
| 0,600 | 98,508 % | **−6,24** | químico |
| 0,700 | 98,894 % | 4,89 | químico |
| 0,750 | 99,066 % | 10,47 | químico |
| 0,800 | 99,233 % | 16,05 | químico |
| 0,8975 | 99,571 % | **85,65** | **polímero** |

O projeto só atinge grau polímero **quando a alimentação por acaso está rica**.
Na composição nominal de 0,75 ele rende 10,47 MUSD/ano, e com alimentação pobre
dá prejuízo. É exatamente o tipo de projeto que ganha a otimização e fracassa na
operação.

### Como tratar isso

- **No DOE e no surrogate:** manter `z_propeno` variável. O surrogate precisa
  aprender o efeito dela para a análise de robustez.
- **Na otimização:** `z_propeno` **não pode ser variável de decisão**. Fixar na
  composição nominal (0,75) e otimizar as demais, ou otimizar uma métrica
  robusta — pior caso na faixa, por exemplo.
- **Na operabilidade:** esta é literalmente a pergunta do framework de
  Georgakis. *Para quais composições de alimentação este projeto se mantém em
  especificação?* É mapeamento inverso do DOS (`pureza ≥ 99,5 %`) para o
  espaço de entrada. O módulo Operability existe para isso.

A regra geral vale para qualquer caso: **separe variáveis de decisão de
distúrbios antes de otimizar.** Um otimizador não conhece a diferença — ele
usa o que estiver na lista, e devolve com prazer um projeto que só funciona
com sorte.

---

# DOE de treino — 1000 pontos

LHS, semente 42. Dados em
[`dados/doe-1000-pontos.csv`](../dados/doe-1000-pontos.csv).

## Auditoria

| | |
|---|---|
| Convergência | **1000 / 1000** |
| Valores reproduzidos localmente | **23 000** (1000 × 23) |
| Divergências acima de 1 × 10⁻⁹ | **0** |
| Pior erro relativo | 7,5 × 10⁻¹³ |
| Tempo | ~8 min na plataforma · 22 s local |

Conjunto de treino com procedência auditada linha a linha.

## Cobertura

| Saída | Mín | Média | Máx |
|---|---|---|---|
| `pureza_topo` (%) | 83,03 | 97,22 | 99,99 |
| `Q_refervedor` (MW) | 17,18 | 43,06 | 78,80 |
| `lucro` (MUSD/ano) | −81,60 | 16,17 | 90,35 |

Grau: **174 polímero · 758 químico · 68 GLP**. Refrigeração em 32,6 %.

Densidade em torno do degrau de grau — a região que decide o dinheiro:

| Faixa de pureza | Pontos |
|---|---|
| 98,0 – 99,0 % | 198 |
| 99,0 – 99,4 % | 117 |
| **99,4 – 99,5 %** | **32** |
| **99,5 – 99,6 %** | **31** |
| 99,6 – 100 % | 143 |

63 pontos na janela crítica, equilibrados dos dois lados. O surrogate tem
material para aprender o degrau — não muito, mas suficiente. Se o Williams Plot
acusar alavancagem alta ali, o remédio é um DOE complementar concentrado nessa
faixa.

## Onde Pearson engana

| Entrada | Saída | Pearson | Spearman | Diferença |
|---|---|---|---|---|
| `z_propeno` | `lucro` | 0,580 | **0,756** | 0,176 |
| `corte_pct` | `recuperacao` | 0,252 | **0,363** | 0,111 |
| `pos_alimentacao` | `pureza_topo` | 0,146 | **0,248** | 0,102 |
| `N_estagios` | `pureza_topo` | 0,178 | **0,257** | 0,079 |

Spearman acima de Pearson indica relação monótona **não-linear** — exatamente o
regime em que HSIC e o ξ de Chatterjee, no módulo Analysis, mostram serviço que
a correlação linear não mostra.

## 🎯 O resultado que muda o projeto

Peguei os 1000 projetos e avaliei cada um sob cinco composições de alimentação
(0,60 · 0,70 · 0,75 · 0,80 · 0,90):

| | |
|---|---|
| Atingem grau polímero **no ponto amostrado** | **174** |
| Atingem grau polímero **em toda a faixa** | **102** |

**41 % dos projetos "grau polímero" são grau polímero por sorte da
alimentação.** Numa alimentação pobre eles caem para grau químico e o produto
perde US$ 200/t.

Os três melhores projetos robustos, avaliados na alimentação nominal:

| N | Alim. | R | corte % | P (bar) | Pior pureza | Lucro |
|---|---|---|---|---|---|---|
| 260 | 0,697 | 16,30 | 98,93 | 17,19 | 99,615 % | **62,11** |
| 250 | 0,678 | 18,14 | 99,81 | 16,85 | 99,807 % | 61,50 |
| 250 | 0,651 | 21,64 | 99,70 | 20,75 | 99,661 % | 61,13 |

Convergem com a varredura analítica feita antes do DOE (N ≈ 275–300,
R ≈ 16,3–17,8, lucro ≈ 61–63 MUSD/ano) — dois métodos independentes chegando
ao mesmo lugar.

E comparam com o "melhor" ponto do DOE piloto, de 85,6 MUSD/ano: aquele
projeto rendia mais **só porque a alimentação amostrada estava rica**, e dava
prejuízo de 6,24 MUSD/ano numa alimentação pobre. **Robustez custa cerca de
25 MUSD/ano de lucro aparente — e vale cada centavo**, porque o lucro aparente
não existe.
