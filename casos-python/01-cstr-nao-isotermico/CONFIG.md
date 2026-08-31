# Caso 01 — CSTR não-isotérmico com camisa de resfriamento

Reação `A → B`, irreversível, primeira ordem, exotérmica, em reator de mistura
perfeita com troca térmica por camisa. Parâmetros do CSTR clássico de Seborg,
Edgar, Mellichamp & Doyle. Unidades: minuto, litro, mol, joule, kelvin.

## Por que este caso foi escolhido como o primeiro

O balanço de energia admite **até três estados estacionários** para a mesma
combinação de entradas. No ponto nominal (`q=100, V=100, CAf=1.0, Tf=350,
Tc=300, UA=5e4`) existem exatamente três:

| Ramo | T (K) | Conversão | Estabilidade |
|---|---|---|---|
| Frio (partida a frio) | 324,5 | 12,3 % | estável |
| Intermediário | ≈ 350 | ≈ 50 % | **instável** |
| Ignitado | 369,7 | 79,1 % | estável |

O estado de 350 K que aparece nos livros-texto é justamente o **instável** — é
por isso que este reator é o exemplo canônico de controle de processos.

Para nós, o que importa é a consequência prática: o mapa entrada → saída é
não-linear e, na fronteira de ignição, **descontínuo**. Isso exercita de
verdade cada módulo da suite, em vez de só produzir gráficos bonitos:

| Módulo | O que este caso revela |
|---|---|
| Analysis | Pearson quase nulo onde HSIC e ξ de Chatterjee acusam dependência forte |
| Surrogate | MLP, XGBoost e GPR reagem de formas bem diferentes ao degrau de ignição |
| Validation | Pontos na fronteira de ignição aparecem como alta alavancagem no Williams Plot |
| Optimization | Conflito real entre conversão, custo de resfriamento e margem térmica |
| Operability | O AOS fica **não-convexo** — o cenário em que o índice de Georgakis diz algo |

## Convenção de estado estacionário

Quando há multiplicidade, `simulate()` devolve como ponto de operação o ramo
alcançável **a partir de partida fria** (menor raiz estável) — o comportamento
físico de um reator que sobe da temperatura ambiente. O ramo ignitado vem em
saídas separadas (`T_ramo_quente`, `X_ramo_quente`, `salto_ignicao`), para que o
degrau possa ser estudado explicitamente em vez de virar ruído.

## Variáveis de entrada

Cole no wizard de variáveis do Python Case. A coluna **Cell** é a chave do
dicionário e precisa bater exatamente com o código.

| Name | Cell | Unit | Type | Default | Min | Max |
|---|---|---|---|---|---|---|
| q | `q` | L/min | Continuous | 100 | 50 | 150 |
| V | `V` | L | Continuous | 100 | 80 | 150 |
| CAf | `CAf` | mol/L | Continuous | 1 | 0.5 | 2 |
| Tf | `Tf` | K | Continuous | 350 | 300 | 370 |
| Tc | `Tc` | K | Continuous | 300 | 280 | 340 |
| UA | `UA` | J/(min.K) | Continuous | 50000 | 30000 | 80000 |

## Variáveis de saída

| Name | Cell | Unit | Papel |
|---|---|---|---|
| T_reator | `T_reator` | K | resposta |
| CA_saida | `CA_saida` | mol/L | resposta |
| conversao | `conversao` | % | **objetivo** (maximizar) |
| produtividade | `produtividade` | mol/min | **objetivo** (maximizar) |
| Q_resfriamento | `Q_resfriamento` | kW | **objetivo** (minimizar) |
| margem_termica | `margem_termica` | K | **restrição** (≥ 0) |
| n_estados | `n_estados` | - | diagnóstico |
| T_ramo_quente | `T_ramo_quente` | K | diagnóstico |
| X_ramo_quente | `X_ramo_quente` | % | diagnóstico |
| salto_ignicao | `salto_ignicao` | K | diagnóstico |
| runaway | `runaway` | - | **restrição** (= 0) |
| convergiu | `convergiu` | - | diagnóstico |

> As saídas de diagnóstico existem para a análise, não para virar alvo de
> surrogate. `convergiu` é constante enquanto tudo funciona — o validador local
> avisa sobre isso, e o aviso é esperado aqui.

## Antes de subir: valide localmente

```bash
python3 ferramentas/validar_caso.py casos-python/01-cstr-nao-isotermico/simulate.py --n 200 --csv doe_local.csv
```

O caso roda em cerca de **1 ms por ponto**, então um DOE de 2000 pontos leva
poucos segundos na sua máquina. Vale gastar quota da nuvem só depois que o
comportamento estiver entendido localmente.

## Roteiro sugerido na plataforma

1. **Projects** — `＋ New ▾ → 🐍 New Python Case`, suba o `simulate.py` e
   cadastre as variáveis das tabelas acima.
2. **Simulator → Single Run** — rode nos valores padrão e confira contra a
   tabela dos três ramos, acima. É a validação de que o upload deu certo.
3. **Simulator → Batch** — LHS com 500 a 1000 pontos. LHS, e não Full
   Factorial: com 6 entradas, um fatorial completo de 3 níveis já pede 729
   pontos e ainda assim cobre mal o interior do domínio.
4. **Analysis** — comece por Pearson × Spearman × HSIC × ξ de Chatterjee sobre
   `Tc → conversao`. É o argumento visual de por que correlação linear engana.
   Depois: PCA, clustering (os ramos frio e ignitado tendem a se separar
   sozinhos) e detecção de outliers.
5. **Surrogate** — treine ao menos MLP, XGBoost e GPR sobre `conversao` e
   `Q_resfriamento`. Ative o Optuna. A pergunta interessante: qual deles
   aprende o degrau de ignição sem alucinar no meio?
6. **Validation** — MAPE por faixa, Williams Plot (procure a fronteira de
   ignição na região de alta alavancagem), SHAP e PDP.
7. **Optimization** — NSGA-II com três objetivos: maximizar `conversao`,
   minimizar `Q_resfriamento`, maximizar `margem_termica`. Restrição:
   `runaway = 0`. O Pareto tende a ter um joelho bem visível.
8. **MCDM** — TOPSIS e VIKOR sobre o Pareto, variando os pesos. Compare com
   PROMETHEE II: soluções diferentes vencem com métodos diferentes, e entender
   por quê é metade do aprendizado.
9. **Operability** — AOS no plano `conversao × Q_resfriamento`, DOS como
   "conversão ≥ 70 % e Q ≤ 60 kW", e o índice OI. Depois o mapeamento inverso:
   que faixas de `Tc` e `CAf` garantem essa especificação?

## Ideias de extensão

- Trocar a política de partida fria por partida quente e comparar os Paretos.
- Incluir custo de utilidade e preço do produto para transformar o
  multiobjetivo em lucro líquido, e ver se o ótimo econômico é perigosamente
  próximo da fronteira de runaway.
- Reproduzir o mesmo reator no DWSIM (CSTR + cinética de Arrhenius) e comparar
  ponto a ponto — o gêmeo digital do gêmeo digital.
