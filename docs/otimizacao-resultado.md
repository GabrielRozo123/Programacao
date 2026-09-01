# Otimização NSGA-II — resultado e validação

100 soluções de Pareto, maximizando `recuperacao` e minimizando `Q_refervedor`,
com `z_propeno` fixo em 0,75 e três restrições. Cada solução foi **reavaliada no
modelo rigoroso** — a validação que a própria documentação da suite recomenda.

## ⚠️ O otimizador explorou o surrogate

**54 das 100 soluções preveem pureza acima de 100 %** — até 100,25 %. O GPR é
ilimitado: não sabe que fração molar não passa de 1. O otimizador descobriu essa
brecha e foi direto para ela.

E o viés é sistemático:

| | Conjunto de teste | Frente de Pareto |
|---|---|---|
| Erro típico em `pureza_topo` | 0,078 ponto | **0,292 ponto** |

**Quatro vezes pior.** Não porque o modelo piorou — porque o otimizador
*procurou* onde ele é otimista. Um otimizador sobre surrogate não amostra o
espaço: ele busca ativamente as regiões onde o modelo promete mais, que são
exatamente as regiões onde o modelo erra para cima.

> **Regra geral:** o erro de um surrogate medido num conjunto de teste aleatório
> **subestima** o erro que ele terá no ótimo. Validar o resultado no modelo
> rigoroso não é zelo — é parte do método.

Consequência: **45 das 100 soluções violam a restrição de pureza na realidade**
(99,474 % a 99,700 %, contra o mínimo de 99,7 exigido). Restaram **55**.

## As restrições estruturais se sustentaram

| Restrição | Violações reais |
|---|---|
| `pureza_topo` ≥ 99,7 | **45** |
| `R_sobre_Rmin` ≥ 1,1 | 0 |
| `T_condensador` ≥ 40 | 0 |

As duas que vieram de análise (Williams Plot e limiar de refrigeração) foram
respeitadas sem exceção. Só a que depende da precisão do surrogate falhou.

## 🎯 Onde o otimizador parou — e por quê

| Variável | Média no Pareto | Posição na faixa |
|---|---|---|
| `N_estagios` | 259,99 | **100 % — colado no teto** |
| `corte_pct` | 99,887 | **99,6 % — colado no teto** |
| `pos_alimentacao` | 0,664 | 90,9 % |
| `razao_refluxo` | 15,98 | 49,9 % |
| **`pressao`** | **16,621** | 32,8 % |

**A pressão parou em 16,62 bar.** O limiar de refrigeração que calculamos ao
reancorar as constantes de Antoine contra o DWSIM é **16,61 bar**.

O otimizador desceu a pressão — porque menos pressão significa maior α e menos
energia — até encostar exatamente nessa restrição. **A calibração termodinâmica
determinou o ótimo econômico.** Se o Antoine tivesse ficado com o viés de
+0,52 °C, o ótimo teria saído em 16,42 bar, e o projeto operaria com o
condensador fora da faixa da água de resfriamento.

`N_estagios` colado em 260 é o teto do DOE: **a faixa limitou a resposta, não a
física.** Um DOE futuro deve ir além de 300.

## O melhor projeto não é o mais lucrativo

Aplicando o teste de robustez — a mesma coluna sob cinco composições de
alimentação:

| N | R | P (bar) | Lucro | Pureza em z = 0,60 | |
|---|---|---|---|---|---|
| 260 | 15,55 | 16,62 | **63,62** | 99,50 % | ❌ perde grau |
| 260 | **15,66** | **16,62** | **63,52** | **99,52 %** | ✅ robusto |
| 260 | 15,70 | 16,62 | 63,48 | 99,52 % | ✅ |
| 260 | 15,76 | 16,62 | 63,42 | 99,54 % | ✅ |

**A solução de maior lucro é a única das cinco que perde grau polímero com
alimentação pobre.** Ela está em 99,50 % — exatamente sobre o degrau.

A escolha correta é a **segunda**: custa **0,10 MUSD/ano** e sobrevive a toda a
faixa de alimentação. Cem mil dólares por ano de seguro contra um risco de
cinquenta milhões.

## O caminho completo

| Projeto | Lucro (MUSD/ano) |
|---|---|
| Original — N = 200, R = 15 | **15,68** (nem faz grau polímero) |
| Varredura analítica — N = 300, R = 16,28 | 62,67 |
| Melhor robusto do DOE — N = 260, R = 16,30 | 62,11 |
| **NSGA-II validado — N = 260, R = 15,66, P = 16,62** | **63,52** |

O ganho de +1,5 MUSD/ano sobre a varredura analítica veio inteiramente da
**pressão**: 16,62 em vez de 18 bar. Nenhuma das análises anteriores tinha
mexido nela — foi o otimizador multiobjetivo que encontrou.

## Projeto final recomendado

| Parâmetro | Valor |
|---|---|
| Estágios teóricos | 260 (+ condensador → 261 no DWSIM) |
| Estágio de alimentação | 173 (0,664 × 260) |
| Razão de refluxo | 15,66 |
| Corte | 99,90 % |
| Pressão | 16,62 bar |
| Pureza de topo | 99,72 % (99,52 % no pior cenário) |
| Recuperação | 99,62 % |
| Carga do refervedor | 44,0 MW |
| Lucro | 63,52 MUSD/ano |

**Próximo passo obrigatório:** montar este ponto no DWSIM e confirmar. Todo o
resultado acima passou pelo gêmeo em Python — que tem erro conhecido de 0,006
ponto contra a coluna rigorosa, mas em cinco configurações apenas.
