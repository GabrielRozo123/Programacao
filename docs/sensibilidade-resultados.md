# Análise de sensibilidade — resultados e verificação

Random Forest com permutation importance sobre o DOE de 1000 pontos, no módulo
Analysis da suite. Índices S₁ (efeito direto) e Sₜ (direto + interações).

## Os índices

| Entrada | `Q_refervedor` R²=0,999 | `pureza_topo` R²=0,994 | `lucro` R²=0,965 |
|---|---|---|---|
| `razao_refluxo` | **82,6 %** | **65,5 %** | **37,3 %** |
| `z_propeno` | 15,0 % | 21,1 % | **39,3 %** |
| `pressao` | 1,9 % | 6,7 % | 10,8 % |
| `N_estagios` | 0,1 % | 3,6 % | 5,8 % |
| `pos_alimentacao` | 0,1 % | 2,4 % | 5,2 % |
| `corte_pct` | 0,2 % | 0,7 % | 1,6 % |

## ✅ Verificação analítica

Para `Q_refervedor` o modelo é uma fórmula fechada:

```
Q = (R+1) · (corte/100) · z · F · λ(P) / 3600
```

Em logaritmo isso vira uma soma, então a variância se decompõe em parcelas
quase independentes — e dá para calcular à mão a partir do próprio DOE:

| Termo | Var(ln) | Previsto | Medido (S₁) |
|---|---|---|---|
| `razao_refluxo` | 0,082627 | **83,9 %** | 82,6 % |
| `z_propeno` | 0,013588 | **13,8 %** | 15,0 % |
| `pressao` (via λ) | 0,002166 | **2,2 %** | 1,9 % |
| `corte_pct` | 0,000072 | **0,1 %** | 0,2 % |

A decomposição analítica reproduz os índices do Random Forest. **O método está
correto e o R² de 0,999 é confiável.**

E o mais bonito: `N_estagios` e `pos_alimentacao` **não aparecem na fórmula**, e
a suite atribuiu 0,1 % a cada um. Ela redescobriu, **só dos dados**, que
estágios não compram energia — que é exatamente o que a escada no DWSIM mediu:
40 895 → 40 933 → 40 947 → 40 953 kW de N = 50 a N = 200.

## ⚠️ Índice baixo não é variável sem importância

`corte_pct` aparece com 0,2 % em `Q_refervedor`. Isso **não** significa que ela
não importe fisicamente. Derivadas locais no ponto base:

| Perturbação de −1 % | Efeito em Q |
|---|---|
| `razao_refluxo` | −0,937 % |
| `corte_pct` | **−1,000 %** |
| `z_propeno` | **−1,000 %** |
| `N_estagios` | 0,000 % |
| `pos_alimentacao` | 0,000 % |

Os três têm sensibilidade relativa praticamente **idêntica** — Q é proporcional
aos três. A diferença está na faixa amostrada:

| Variável | Faixa | Fator |
|---|---|---|
| `razao_refluxo` | 8 → 24 | **3,00×** |
| `z_propeno` | 0,60 → 0,90 | 1,50× |
| `corte_pct` | 97,0 → 99,9 | **1,03×** |

**O índice de Sobol mede contribuição à variância na faixa amostrada, não
importância física.** Ampliar a faixa de uma variável aumenta o índice dela sem
mudar nada no processo. Nunca descarte uma variável só pelo índice — verifique
se a faixa é representativa antes.

## 🎯 A interação que confirma a fragilidade

Em quase todos os pares S₁ ≈ Sₜ, ou seja, efeitos aditivos sem interação. Com
uma exceção:

| | S₁ | Sₜ | Diferença |
|---|---|---|---|
| `z_propeno` → `lucro` | 39,3 % | **46,9 %** | **+7,6 pontos** |

Sₜ acima de S₁ significa que a variável age **em combinação** com outras. E o
mecanismo é conhecido: se um projeto atinge grau polímero depende do
*par* (projeto, composição da alimentação) — não de cada um isolado.

É exatamente a fragilidade que encontramos por força bruta, avaliando os 1000
projetos sob cinco alimentações: 41 % dos projetos "grau polímero" perdiam o
grau numa alimentação pobre. **A análise de sensibilidade detectou o mesmo
fenômeno, por um caminho totalmente independente, como termo de interação.**

## O R² conta uma história

| Saída | R² | Leitura |
|---|---|---|
| `Q_refervedor` | 0,999 | fórmula fechada, suave |
| `pureza_topo` | 0,994 | não-linear mas contínua |
| `lucro` | **0,965** | **degrau de preço em 99,5 %** |

O Random Forest tem mais dificuldade justamente com `lucro`, e a causa é a
descontinuidade do preço. **É o aviso para a fase de surrogate:** `lucro` é o
alvo difícil, e o modelo que aprender o degrau ganha.

## O que isso define para a otimização

- **`razao_refluxo` é a alavanca de projeto**, dominante em tudo (37 % a 83 %).
- **`z_propeno` é o distúrbio dominante**, e interage — precisa entrar como
  cenário, não como variável de decisão.
- **`N_estagios` e `pos_alimentacao` são fracos** (3 % a 6 %). Combinado com o
  ótimo achatado da varredura analítica — de N = 250 a 400 o lucro varia menos
  de 0,6 % — isso confirma que o número de estágios sai de restrição de altura
  e layout, não de otimização econômica.
- **`corte_pct` merece faixa mais larga** num DOE futuro, se quisermos medir o
  efeito dela de verdade.

O problema de decisão é, na prática, **quase unidimensional**: escolher o
refluxo, dado um número de estágios ditado por restrição construtiva, e depois
verificar robustez contra a alimentação.
