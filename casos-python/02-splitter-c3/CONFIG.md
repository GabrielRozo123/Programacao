# Caso 02 — Splitter propeno/propano (C3 splitter)

Coluna binária propeno/propano em **modo rating**: fixados os estágios e as
especificações de operação, o modelo devolve purezas, cargas térmicas,
dimensionamento e economia anual. Modo rating porque é assim que a coluna
rigorosa do DWSIM se comporta — o que permite comparar ponto a ponto.

Este é o gêmeo rápido do caso DWSIM descrito em
[`docs/dwsim-splitter-c3.md`](../../docs/dwsim-splitter-c3.md).

## Por que o C3 splitter

É a separação onde o surrogate tem o maior retorno possível. Com α ≈ 1,12 a
coluna precisa de 150–250 estágios e refluxo de 12–20: a versão rigorosa é
lenta e o NSGA-III quer dezenas de milhares de avaliações. Aqui o surrogate
deixa de ser enfeite e passa a ser o que **viabiliza** a otimização.

E a economia tem um degrau real: propeno grau polímero (≥ 99,5 % mol) vale
US$ 1150/t, grau químico US$ 950/t, e fora de especificação vira GLP a
US$ 550/t. O ótimo encosta na especificação por cima — que é exatamente o
dilema de projeto de uma unidade de verdade.

## Caso base (valores padrão)

| Grandeza | Valor | Comentário |
|---|---|---|
| Pureza de topo | 99,55 % mol | grau polímero, **por 0,05 ponto** |
| Pureza de fundo | 97,20 % mol propano | GLP |
| Recuperação de propeno | 99,05 % | |
| Refervedor / condensador | 42,1 MW | dominante no OPEX |
| T topo / T fundo | 44,2 / 52,4 °C | água de resfriamento no limite |
| Diâmetro | 4,44 m | |
| Altura | 145 m em 3 cascos | splitters reais são cascos em série |
| N/Nmin | 2,24 | faixa típica 1,5–2,5 |
| R/Rmin | 1,21 | faixa típica 1,1–1,5 |
| CAPEX instalado | 40,8 MUSD | |
| OPEX | 11,7 MUSD/ano | ~96 % é vapor |
| Lucro | 65,6 MUSD/ano | α calibrado contra o DWSIM |

## Duas decisões de modelagem que valem para qualquer caso

**Alimentação como fração, não como número de prato.** Se `estagio_alim` e
`N_estagios` forem variáveis independentes, o DOE gera combinações com
alimentação acima do topo. Usando `pos_alimentacao` ∈ [0,3; 0,7] como fração de
N, *toda* combinação é viável.

**Corte relativo ao propeno alimentado, não a D/F.** Com `D/F` fixo e `z_propeno`
variando, boa parte do domínio vira projeto impossível — com `z = 0,60` e
`D/F = 0,82` a pureza de topo não passa de 73 %, faça o que fizer. Definindo
`corte = D/(F·z)`, a recuperação fica entre 97 % e 99,9 % **para qualquer
composição de alimentação**:

| corte | z=0,60 | z=0,75 | z=0,90 |
|---|---|---|---|
| 0,975 | 96,9 % | 97,4 % | 97,5 % |
| 0,990 | 98,4 % | 98,9 % | 99,0 % |
| 1,000 | 99,3 % | 99,9 % | 100,0 % |

A lição é geral: **reparametrizar é mais barato que descartar pontos**. Num DOE
de 500 rodadas na nuvem, a diferença entre as duas formulações são centenas de
simulações jogadas fora.

## Variáveis de entrada

| Name | Cell | Unit | Type | Default | Min | Max | Step |
|---|---|---|---|---|---|---|---|
| N_estagios | `N_estagios` | - | Discrete | 200 | 100 | 260 | 10 |
| pos_alimentacao | `pos_alimentacao` | - | Continuous | 0.5 | 0.3 | 0.7 | — |
| razao_refluxo | `razao_refluxo` | - | Continuous | 15 | 8 | 24 | — |
| corte | `corte` | - | Continuous | 0.995 | 0.97 | 0.999 | — |
| pressao | `pressao` | bar | Continuous | 18 | 14 | 22 | — |
| z_propeno | `z_propeno` | - | Continuous | 0.75 | 0.6 | 0.9 | — |
| F_alimentacao | `F_alimentacao` | kmol/h | Fixed | 1000 | — | — | — |

## Variáveis de saída

| Name | Cell | Unit | Papel |
|---|---|---|---|
| pureza_topo | `pureza_topo` | % mol | **restrição** (≥ 99,5) |
| pureza_fundo | `pureza_fundo` | % mol | resposta |
| recuperacao | `recuperacao` | % | **objetivo** (maximizar) |
| grau_produto | `grau_produto` | - | diagnóstico (2/1/0) |
| Q_refervedor | `Q_refervedor` | MW | **objetivo** (minimizar) |
| Q_condensador | `Q_condensador` | MW | resposta |
| T_condensador | `T_condensador` | °C | resposta |
| T_refervedor | `T_refervedor` | °C | resposta |
| precisa_refrig | `precisa_refrig` | - | **restrição** (= 0) |
| diametro | `diametro` | m | resposta |
| altura_total | `altura_total` | m | resposta |
| n_cascos | `n_cascos` | - | diagnóstico |
| N_min | `N_min` | - | diagnóstico (Fenske) |
| R_min | `R_min` | - | diagnóstico (Underwood) |
| R_sobre_Rmin | `R_sobre_Rmin` | - | diagnóstico |
| CAPEX | `CAPEX` | MUSD | resposta |
| CAPEX_anual | `CAPEX_anual` | MUSD/ano | resposta |
| OPEX | `OPEX` | MUSD/ano | **objetivo** (minimizar) |
| custo_total | `custo_total` | MUSD/ano | resposta |
| lucro | `lucro` | MUSD/ano | **objetivo** (maximizar) |
| convergiu | `convergiu` | - | diagnóstico |

## Validação local

```bash
python3 ferramentas/validar_caso.py casos-python/02-splitter-c3/simulate.py --n 300
```

Resultado esperado: 300/300 convergidos, ~3 ms por run. O DOE varre pureza de
81 % a 100 %, lucro de −82 a +95 MUSD/ano e cerca de 30 % dos projetos
exigindo refrigeração — sinal de sobra para treinar surrogate e otimizar.

> **α calibrado contra o DWSIM.** A volatilidade relativa usada aqui está
> ancorada numa medição real: flash PVF a 18 bar no DWSIM 10.2.3.0 com
> Peng-Robinson deu α = 1,105152. A correlação anterior, só de literatura,
> dava 1,1166 — 1,04 % acima, o que inflava a pureza de topo do caso base de
> 99,55 % para 99,85 % e escondia que o projeto está na borda da especificação.
> A inclinação da correlação ainda é de literatura: falta medir a 14 e 22 bar.

## Roteiro na plataforma

1. **DOE** — LHS com 500 pontos. Não use Full Factorial: com 6 variáveis ativas
   e `N_estagios` discreto, o fatorial explode sem cobrir o interior.
2. **Analysis** — a pergunta interessante é `pressao → lucro`. Espere
   correlação linear fraca: o efeito da pressão é não-monotônico, porque baixar
   a pressão aumenta α (menos estágios) mas empurra o condensador para
   refrigeração. HSIC e ξ de Chatterjee enxergam isso; Pearson não.
3. **Surrogate** — treine sobre `pureza_topo`, `Q_refervedor` e `lucro`.
   `lucro` é o alvo difícil: tem degrau nos limites de 99,5 % e 92 % de pureza.
   Compare quem aprende o degrau.
4. **Validation** — Williams Plot, procurando os pontos na fronteira de grau.
5. **Optimization** — NSGA-II com dois objetivos: maximizar `lucro`, minimizar
   `Q_refervedor`. Restrições: `pureza_topo ≥ 99,5` e `precisa_refrig = 0`.
6. **MCDM** — TOPSIS sobre o Pareto, variando os pesos entre lucro e energia.
7. **Validação cruzada** — leve os 5 melhores pontos do Pareto para o DWSIM
   rigoroso e meça o erro do atalho. Esta etapa é o que separa o estudo sério
   da demonstração bonita.

## Limitações declaradas

Nenhuma destas hipóteses vale exatamente — e é por isso que o DWSIM existe
neste projeto:

- α constante ao longo da coluna, corrigido só pela pressão. O valor rigoroso
  varia com a composição.
- Fluxo molar constante (CMO): ignora o balanço de energia estágio a estágio.
- Perda de carga desprezada. Numa coluna de 145 m com 235 pratos, a perda real
  é de vários bar e altera α no fundo.
- Custos são estimativas fatoradas de ordem de grandeza, úteis para **comparar**
  alternativas. Viabilidade exige estimativa formal.

## Extensões

- Condição térmica da alimentação `q` como variável: pré-aquecer troca carga do
  refervedor por área de trocador.
- **Bomba de calor por recompressão de vapor.** O condensador está a 44 °C e o
  refervedor a 52 °C — 8 K de diferença. Comprimir o vapor de topo para aquecer
  o fundo elimina quase todo o vapor de baixa. É assim que muitos splitters C3
  modernos operam, e o payback costuma ser de poucos anos. Como projeto de
  otimização, é excelente: troca-se OPEX de vapor por OPEX de eletricidade mais
  CAPEX de compressor.
- Coluna de parede dividida, se houver um terceiro componente na alimentação.
