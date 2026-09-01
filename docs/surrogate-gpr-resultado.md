# Surrogate GPR de `pureza_topo` — resultado e leitura

Treinado no AI4Tech Suite sobre os 1000 pontos auditados. Kernel **Matérn**
(ν = 1,5), Optuna desligado (o GPR ajusta o kernel por verossimilhança
marginal), 800 treino / 200 teste, 11,8 s.

## Métricas

| | |
|---|---|
| R² teste | **0,9961** |
| R² treino | 1,0000 |
| MAE | 0,0777 ponto percentual |
| RMSE | 0,1698 ponto |
| Erro máximo | **1,748 pontos** |
| MAPE | 0,08 % |

R² de treino exatamente 1,0000 é esperado: com nugget de 1e-7 o GPR
**interpola** os pontos de treino. O número honesto é o de teste.

## ⚠️ Por que 0,08 % de MAPE não quer dizer o que parece

A pureza média do conjunto é 97,2 %. Então 0,08 % de MAPE são **0,078 ponto
percentual** — parece excelente.

Mas a decisão econômica não está na média. Está no **degrau de 99,5 %**, onde
0,1 ponto de erro muda o preço do produto em US$ 200/t.

Quantos projetos ficam na zona de dúvida:

| Tolerância | Projetos a menos disso do limite |
|---|---|
| 0,078 ponto (MAE) | **46 de 1000** (4,6 %) |
| 0,170 ponto (RMSE) | **107 de 1000** (10,7 %) |
| 1,748 pontos (erro máx.) | 577 de 1000 (57,7 %) |

E dos **174** projetos que atingem grau polímero, **24 estão a menos de um erro
típico acima do limite** — poderiam ser rebaixados por engano.

**O modelo é excelente para prever pureza e tem uma zona cega de ±0,17 ponto
para decidir grau de produto.** As duas coisas são verdade ao mesmo tempo.

## A saída não é um modelo melhor — é usar a incerteza

O GPR é o único dos 12 modelos que devolve intervalo de confiança. Isso permite
trocar a pergunta: em vez de "qual a pureza?", perguntar "**dá para decidir o
grau com segurança?**"

```
se (previsão − 2σ) ≥ 99,5  →  grau polímero, com confiança
se (previsão + 2σ) <  99,5  →  grau químico, com confiança
caso contrário              →  NÃO DECIDA — rode o modelo rigoroso
```

Isso converte o surrogate de **oráculo** em **triador**: ele resolve sozinho os
casos fáceis, que são a maioria, e encaminha os duvidosos para a coluna do
DWSIM. O ganho de velocidade continua enorme, e o risco de classificar errado
vai para perto de zero.

É também a resposta para a etapa de otimização: o otimizador vai naturalmente
empurrar as soluções para a fronteira de 99,5 %, que é justamente onde o
surrogate é menos confiável. **Sem a regra de triagem, o Pareto sairia povoado
de projetos que o modelo acha que passam e que não passam.**
