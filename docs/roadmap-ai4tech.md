# Roadmap — projetos com DWSIM + AI4Tech Suite

Seis projetos em ordem crescente de ambição. Cada um foi escolhido para
exercitar um recurso que **poucas ferramentas têm** — não adianta usar uma
plataforma de PSE para fazer o que uma planilha já faz.

Legenda de esforço: 🟢 fim de semana · 🟡 algumas semanas · 🔴 projeto de fôlego

---

## P1 · CSTR não-isotérmico: multiplicidade, ignição e operabilidade 🟢

**Backend:** Python Case — [já pronto neste repositório](../casos-python/01-cstr-nao-isotermico/CONFIG.md)

O reator admite três estados estacionários para a mesma entrada, o que torna o
mapa entrada → saída descontínuo na fronteira de ignição.

**O que ele prova, e que um caso linear nunca provaria:**

- Pearson ≈ 0 onde HSIC e ξ de Chatterjee acusam dependência forte. É o
  contra-exemplo definitivo para quem faz triagem de variáveis só com matriz de
  correlação.
- Surrogates divergem: XGBoost tende a acertar o degrau (é feito de degraus),
  MLP tende a suavizá-lo, GPR fica com incerteza alta exatamente ali — e a
  incerteza do GPR está *certa*.
- O Williams Plot marca a fronteira de ignição como alta alavancagem. É o
  diagnóstico dizendo "aqui eu não sei o que estou fazendo", que é o
  comportamento que a gente quer de um modelo.
- O AOS fica não-convexo, o único cenário em que o índice de operabilidade de
  Georgakis realmente informa algo.

**Entregável:** relatório comparando os três surrogates na região de ignição.

---

## P2 · Splitter propeno/propano no DWSIM: surrogate para otimização econômica 🟡

**Backend:** DWSIM Case · **em andamento** — [guia de montagem](dwsim-splitter-c3.md), [roteiro passo a passo](passo-a-passo-splitter-c3.md) e [gêmeo rápido em Python](../casos-python/02-splitter-c3/CONFIG.md) prontos

Uma coluna rigorosa leva segundos por avaliação; o NSGA-II quer dezenas de
milhares. Aí está a razão de existir do surrogate — não é enfeite, é o que
viabiliza a otimização.

**Caminho:**

1. DOE Box-Behnken ou CCD (poucas variáveis, superfície suave — não desperdice
   pontos com LHS aqui). Variáveis: razão de refluxo, número de estágios,
   estágio de alimentação, pressão.
2. Surrogate: comece por Polynomial/RSM — se um polinômio de segunda ordem já
   der R² alto, use-o e economize; se não der, suba para GPR.
3. NSGA-III sobre CAPEX (estágios, diâmetro) × OPEX (vapor do refervedor) ×
   pureza de topo.
4. Pareto → VIKOR e PROMETHEE II.
5. **A parte honesta:** pegue os 5 melhores pontos do Pareto e rode-os na
   coluna rigorosa do DWSIM. Se o surrogate errou, o relatório precisa dizer
   quanto. Essa validação cruzada é o que separa o trabalho sério da
   demonstração bonita.

**Cuidado com estágios:** número de estágios é `Discrete` com passo 1. Se você
marcar como `Continuous`, o otimizador vai propor 12,7 estágios e o DWSIM vai
arredondar por conta própria — e o surrogate terá aprendido uma superfície que
não existe.

---

## P3 · Teorema π de Buckingham: redescobrir correlações adimensionais 🟢

**Backend:** Python Case ou DWSIM Case (trocador casco-tubo)

Gere dados variando ρ, μ, k, Cp, D, v e aplique a análise de Buckingham π da
suite. Os grupos adimensionais **emergem dos dados**: Reynolds, Prandtl,
Nusselt. Depois ajuste `Nu = a·Re^b·Pr^c` e compare com Dittus-Boelter
(`a=0,023, b=0,8, c=0,4`).

Este é o projeto mais bonito da lista do ponto de vista didático: é machine
learning **com a física dentro**, não em cima dela. E é um material de aula ou
de vídeo praticamente pronto.

**Variação instigante:** injete um erro sistemático nos dados de entrada e veja
se a análise dimensional ainda recupera os grupos corretos. Análise dimensional
é notavelmente robusta — vale mostrar isso.

---

## P4 · Triagem de variáveis em flowsheet grande: Morris → Sobol 🟡

**Backend:** DWSIM Case (absorção de CO₂ com MEA, ou unidade de tratamento de gás)

O problema real de quem simula de verdade: 20 ou mais variáveis manipuláveis,
simulação lenta, quota mensal finita. Rodar LHS em 20 dimensões é desperdício.

**Estratégia em três estágios — cada um custa uma ordem de grandeza menos que o
seguinte faria sozinho:**

| Estágio | Método | Custo típico | Pergunta que responde |
|---|---|---|---|
| 1 | Plackett-Burman / Fatorial Fracionado | ~24 runs | Quais variáveis não fazem *nada*? |
| 2 | Morris (elementary effects) | ~100 runs | Quais têm efeito não-linear ou interagem? |
| 3 | LHS só nas 5–6 sobreviventes | ~500 runs | Dados para o surrogate |
| 4 | Sobol **sobre o surrogate** | grátis | Índices de 1ª e 2ª ordem |

O truque do estágio 4: índices de Sobol exigem dezenas de milhares de
avaliações, inviável no simulador rigoroso. Sobre o surrogate, custa segundos.

**Este é o projeto que mais ensina economia de quota** — e economia de quota é
exatamente o que separa quem usa a ferramenta em produção de quem só brinca.

---

## P5 · Gêmeo digital leve: surrogate como caso de primeira classe 🟡

**Backend:** DWSIM Case → exportar `surrogate_model.zip` → Surrogate Case

Treine o surrogate do flowsheet inteiro, exporte o `.zip` e crie um **Surrogate
Case** na plataforma. A partir daí a simulação roda em microssegundos, sem
worker e sem quota de nuvem.

**O que isso destrava:**

- Análise what-if ao vivo, durante uma reunião.
- Envelope operacional completo: milhares de cenários para mapear onde a planta
  pode operar.
- Pré-otimização barata: encontre a região promissora no surrogate, refine só
  ela no modelo rigoroso.
- Um modelo que roda em microssegundos cabe dentro de um laço de controle
  preditivo — que é a porta de entrada para MPC baseado em surrogate.

**A disciplina que este projeto exige:** todo surrogate tem domínio de validade.
Documente as faixas de treino junto com o `.zip` e trate extrapolação como erro,
não como resultado. O Williams Plot existe exatamente para isso.

---

## P6 · Operabilidade de Georgakis num sistema de mistura 🔴

**Backend:** Python Case (blending) ou DWSIM Case

A otimização responde "qual é o melhor ponto?". A operabilidade responde a
pergunta que a operação de fato faz: **"quais faixas de entrada me garantem o
produto na especificação?"**

- **AOS** — tudo que o processo consegue produzir.
- **DOS** — tudo que o cliente aceita.
- **OI** — quanto do DOS está dentro do AOS. Se OI < 1, nenhum controlador
  resolve: o problema é de projeto, não de controle. Essa conclusão vale ouro.
- **Mapeamento inverso** — dada a especificação, as faixas de entrada viáveis.

É o módulo mais distintivo da suite e o menos explorado por aí. Um estudo bem
feito aqui é material de publicação, não só de portfólio.

---

## Regras de bolso

### Escolha do DOE

| Situação | Método | Por quê |
|---|---|---|
| Triagem, muitas variáveis | Plackett-Burman, Fatorial Fracionado | Custo mínimo para separar o que importa |
| Treinar surrogate | LHS ou Sobol | Cobertura uniforme do interior do domínio |
| Superfície de resposta suave | Box-Behnken, CCD | Feitos para ajustar quadráticas |
| Variáveis discretas ou faixas irregulares | D-Optimal | Otimiza o critério sobre o espaço que existe de fato |
| Reproduzir condições reais de planta | Custom / upload de Excel | Dado histórico vale mais que dado sintético |

Erro comum: Full Factorial com 6 variáveis. São 729 pontos em 3 níveis, e ainda
assim o interior do domínio fica vazio. LHS com 200 pontos cobre melhor.

### Quota e workers

- Valide **sempre** localmente antes de subir (`ferramentas/validar_caso.py`).
  Descobrir um erro de unidade depois de 500 runs na nuvem dói.
- Worker local para lotes grandes de DWSIM; nuvem para o que precisa de
  paralelismo ou roda enquanto você faz outra coisa.
- Surrogate Case não consome quota de simulação — mais uma razão para o P5.

### Higiene de modelagem

- Saída constante no DOE = variável inútil para surrogate. O validador local
  avisa antes de a quota ser gasta.
- Sempre reserve um conjunto de teste **fora** da validação cruzada. K-fold
  ajusta hiperparâmetro; ele não estima erro de generalização honestamente
  quando o Optuna já otimizou em cima dele.
- Registre a semente do DOE. Sem semente, nenhum resultado é reproduzível.
- Compare o surrogate com o modelo rigoroso **nos pontos ótimos**, não só no
  conjunto de teste. É lá que ele vai ser usado, e é lá que ele costuma falhar.

---

## Ordem sugerida

**P1** e **P2** (em andamento) → **P3** (rápido e bonito) → **P4** (a disciplina que faz
diferença) → **P2** (o caso econômico completo) → **P5** → **P6**.
