# Módulo Analysis — o que rodar, e o que ignorar

São 18 métodos de Deep Analysis mais o dashboard interativo. Para o splitter C3,
**quatro** respondem perguntas que ainda não temos resposta. O resto ou já foi
respondido no DOE, ou não se aplica.

## ⚠️ Antes de tudo: só 8 das 23 saídas carregam informação

O `simulate()` devolve 23 saídas, mas muitas são derivadas umas das outras:

| Situação | Saídas |
|---|---|
| Constante | `convergiu` |
| Duplicata exata (\|r\| > 0,9999) | `Q_condensador` ≡ `Q_refervedor` · `CAPEX_anual` ≡ `CAPEX` · `T_refervedor` ≡ `T_condensador` |
| Função de **uma** entrada só | `T_condensador` ← `pressao` (r = 0,9992) · `altura_total` ← `N_estagios` (r = 0,99999) |
| Soma de outras | `custo_total` = `CAPEX_anual` + `OPEX` |
| Diagnóstico, não resposta | `alfa_topo`, `alfa_fundo`, `N_min`, `R_min`, `R_sobre_Rmin`, `n_cascos`, `grau_produto`, `precisa_refrig` |

**Use este subconjunto em todas as análises:**

- **Entradas (6):** `N_estagios`, `pos_alimentacao`, `razao_refluxo`,
  `corte_pct`, `pressao`, `z_propeno`
- **Saídas (8):** `pureza_topo`, `pureza_fundo`, `recuperacao`,
  `Q_refervedor`, `diametro`, `OPEX`, `CAPEX`, `lucro`

Um heatmap 23×23 com essas redundâncias vira uma parede de vermelho que não
informa nada — e pior, dá a impressão de que tudo está correlacionado com tudo.

## As quatro que valem

### 1. Sensitivity Analysis — a mais importante

**Pergunta:** das 6 entradas, quais realmente governam o resultado?

Rode com saídas `lucro`, `pureza_topo` e `Q_refervedor` simultaneamente. Ele usa
Random Forest com permutation importance para índices tipo Sobol (S₁/Sₜ).

**Confira o R² do surrogate interno antes de acreditar nos índices.** Se estiver
baixo, o Random Forest não aprendeu a função e a importância não significa nada.

Isso define diretamente o problema de otimização: variável sem efeito é
dimensão desperdiçada no espaço de busca.

### 2. Correlation Strength — onde a correlação linear mente

**Pergunta:** quanto Pearson subestima a dependência real?

Compara Pearson, Spearman, Kendall, HSIC e ξ de Chatterjee lado a lado. Olhe o
par **`z_propeno` → `lucro`**, onde já medimos:

| Método | Valor |
|---|---|
| Pearson | 0,580 |
| Spearman | 0,756 |

HSIC e ξ devem ficar bem acima dos dois. É o argumento visual de por que fazer
triagem de variáveis só com matriz de correlação engana — e é resultado
apresentável por si só.

### 3. Clusterization — a estrutura emerge sozinha?

**Pergunta:** os três graus de produto aparecem sem serem informados?

K-Means com auto-k sobre `pureza_topo`, `lucro` e `Q_refervedor`. Se ele
encontrar **k = 3** e os clusters baterem com polímero / químico / GLP, é
confirmação de que o degrau de preço domina a estrutura dos dados — e um aviso
ao surrogate de que ele terá de aprender uma descontinuidade.

### 4. PCA — quantas dimensões existem de verdade?

**Pergunta:** com 6 entradas, quantas componentes explicam 90 % da variância?

Se forem 3, a otimização é bem mais fácil do que parece. O biplot também mostra
quais variáveis andam juntas.

## Duas armadilhas

### ❌ Não "limpe" os outliers

O Outlier Detection vai marcar os **68 pontos de grau GLP** como anômalos. Eles
não são erro de medição — são **projetos ruins**, e o DOE convergiu 1000/1000.

Se você usar o botão de limpar, ensina o surrogate que projetos ruins não
existem. Ele fica incapaz de reconhecer a região que precisa evitar, e a
otimização vai propor exatamente ela.

Distinga sempre: **outlier estatístico ≠ dado errado.**

### ❌ Não rode Buckingham π aqui

Ele é para descobrir grupos adimensionais a partir de quantidades físicas com
dimensão — Re, Nu, Pr. Nossas entradas são número de estágios, razão de refluxo
e frações molares: já adimensionais ou estruturais. Não há π para encontrar.

Guarde o método para o projeto P3 do roadmap, que é feito para ele.

## O que pular, e por quê

| Método | Por quê |
|---|---|
| EDA Profiling Report | Útil como documentação no fim, não como exploração agora |
| Distribution Analysis | Saber se `lucro` é Weibull não muda decisão nenhuma |
| Wasserstein | Compara distribuições entre variáveis — não é a nossa pergunta |
| Multicollinearity (VIF) | Entradas vêm de LHS, são quase ortogonais por construção. VIF ≈ 1 garantido |
| ANOVA | A Sensitivity Analysis já cobre, com menos hipóteses |
| Correlation Network | Bonito, mas com 6 entradas o heatmap já diz tudo |

## Depois

Com a sensibilidade em mãos, vá para o **Surrogate**. Treine sobre
`pureza_topo`, `Q_refervedor` e `lucro` — `lucro` é o alvo difícil, por causa do
degrau de grau.
