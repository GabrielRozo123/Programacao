# Surrogate — o plano para o splitter C3

## A decisão que vale mais que a escolha do algoritmo

**Não treine um surrogate para `lucro`.**

`lucro` não é uma resposta física — é uma conta feita sobre as respostas
físicas. Reconstruí os 1000 pontos do DOE a partir de `pureza_topo`,
`pureza_fundo`, `custo_total` e das entradas, aplicando a regra de preço:

```
erro máximo da reconstrução: 1,3 × 10⁻¹³ MUSD/ano
```

Exato. Não há nada de físico ali para aprender.

Treinar um surrogate para `lucro` obriga o modelo a aprender **duas** coisas ao
mesmo tempo:

1. a física da coluna — suave, e é o que ele sabe fazer;
2. o degrau de preço em 99,5 % — descontínuo, e é o que o atrapalha.

Foi exatamente por isso que o R² da análise de sensibilidade caiu de 0,999 e
0,994 para **0,965 justamente no `lucro`**. O modelo não é ruim; a pergunta
está mal posta.

### A arquitetura correta

```
entradas  →  [ surrogate ]  →  pureza_topo, pureza_fundo,
                               Q_refervedor, diametro
                                        ↓
                            [ regra de preço + custeio ]
                                        ↓
                                    lucro
```

**Aprenda a física, calcule a economia.** O degrau fica exato porque é uma
regra conhecida, não uma função estimada. E a interpretação melhora: quando o
lucro previsto errar, dá para dizer se foi erro de pureza, de energia ou de
dimensionamento.

Princípio geral: **não peça a um modelo de ML que aprenda aquilo que você
sabe calcular.**

## Os alvos, e a dificuldade de cada um

| Alvo | Natureza | Dificuldade |
|---|---|---|
| `Q_refervedor` | fórmula fechada, suave | trivial |
| `diametro` | função suave de Q e P | fácil |
| `pureza_topo` | não-linear, contínua | média |
| `pureza_fundo` | não-linear, contínua | média |

Não impressione ninguém com R² = 0,999 em `Q_refervedor`: ele é o produto
`(R+1)·corte·z·λ(P)`, e qualquer modelo acerta. **O alvo que mede a qualidade
do surrogate é `pureza_topo`.**

## 🔬 Symbolic Regression em `Q_refervedor` — o teste perfeito

Antes dos modelos convencionais, rode **Symbolic Regression** só em
`Q_refervedor`. Nós sabemos a resposta exata:

```
Q = (R+1) · (corte/100) · z · F · λ(P) / 3600
```

Se a regressão simbólica devolver algo proporcional a `(R+1)·corte·z`, ela
**redescobriu a fórmula a partir dos dados** — e você fica com uma equação
legível em vez de uma caixa-preta. É o experimento mais bonito do módulo, e
tem gabarito para conferir.

## Modelos a comparar em `pureza_topo`

| Modelo | Por que testar |
|---|---|
| 🎯 **GPR** | Devolve **incerteza** junto com a previsão. Perto do degrau, saber que o modelo não sabe vale mais que a previsão |
| 🧠 **MLP** | Aproximador suave — deve ir bem numa função contínua |
| 🌲 **XGBoost** | Feito de degraus. Compare com o MLP: quem lida melhor com a fronteira de grau? |

Ative o **Optuna** para os três, com K-fold. Mas leia a ressalva abaixo.

## ⚠️ K-fold com Optuna não é estimativa honesta de erro

O Optuna escolhe hiperparâmetros **otimizando o erro de validação cruzada**.
Depois disso, esse erro deixa de ser uma estimativa imparcial — foi ele o alvo
da otimização.

**Gere um conjunto de teste de verdade:** volte ao Simulator, rode um segundo
DOE com **LHS, 200 pontos, seed 7** (diferente da 42 do treino), baixe o
`.xlsx` e use como validação externa. São ~2 minutos e transformam "o modelo
parece bom" em "o modelo erra X %".

## Validação: o que olhar

**MAPE Analysis** — não olhe só o valor global. Em `pureza_topo` o MAPE vai
parecer ótimo porque quase todos os valores estão entre 83 % e 100 %: errar 0,5
ponto num valor de 99 vira 0,5 % de MAPE. **O que importa é o erro absoluto em
ponto percentual, na faixa de 99,4 a 99,6 %.** Um erro de 0,1 ponto ali muda o
preço do produto em US$ 200/t.

**Williams Plot** — a aposta: a região de alta alavancagem vai coincidir com a
fronteira de grau, onde só temos 63 dos 1000 pontos. Se confirmar, o remédio é
um DOE complementar concentrado em 99,3–99,7 % de pureza, e não trocar de
modelo.

## Depois

Com o surrogate validado, o caminho é **SHAP** e **PDP** para confirmar que ele
aprendeu a física certa — as importâncias devem bater com a análise de
sensibilidade que já rodamos — e depois **Optimization**, com `z_propeno` como
cenário e não como variável de decisão.
