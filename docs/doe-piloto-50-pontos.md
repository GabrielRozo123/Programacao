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
