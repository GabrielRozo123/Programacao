# Método

Documento de fundamentação: o que cada etapa faz, por que faz assim, e o
que a conclusão significa (e não significa).

---

## 1. O problema

A metanólise de um triglicerídeo é uma sequência de três reações
reversíveis:

```
TG + M ⇌ DG + E        (R1)
DG + M ⇌ MG + E        (R2)
MG + M ⇌ G  + E        (R3)
```

Nenhuma delas é elementar sobre um catalisador sólido. Cada uma envolve
adsorção, uma ou mais transformações na superfície e dessorção. A
consequência prática: **a equação de velocidade não pode ser escrita a
partir da estequiometria.** Ela depende de qual etapa é lenta, de quais
espécies ocupam os sítios, e de quantos tipos de sítio existem.

O procedimento clássico — Hougen e Watson, sistematizado por Boudart e por
Froment — é postular um mecanismo, escolher uma etapa determinante,
assumir quase-equilíbrio nas demais, e derivar a lei correspondente. É
correto e é tedioso. Feito à mão, a análise raramente passa de três ou
quatro candidatos, e a escolha de quais três costuma refletir o que o
grupo já publicou antes.

Este pacote automatiza a derivação e amplia a varredura.

---

## 2. Derivação simbólica

Um mecanismo é declarado como uma lista de etapas elementares:

```python
Step("ads_M", {"M": 1, "*": 1}, {"M*": 1})           # metanol → metóxido
Step("sr",    {"M*": 1, "A": 1}, {"B": 1, "E": 1, "*": 1})
```

Escolhida a etapa determinante, o derivador:

1. escreve a relação de quase-equilíbrio de cada uma das demais etapas,
   `K_i · Π(reagentes) = Π(produtos)`, com atividades de superfície
   representadas pelas coberturas `θ`;
2. resolve essas relações **em cadeia** — a cada passo procura uma equação
   com exatamente uma cobertura ainda desconhecida e a isola;
3. fecha o balanço de sítios, `θ_v + Σθ_i = 1`, obtendo a fração de sítios
   vagos;
4. escreve a velocidade da etapa determinante e substitui as coberturas.

Para o Eley-Rideal via metóxido com inibição por glicerol, isso devolve

$$ r = \frac{k\,K_M\left(C_A C_M - \dfrac{C_B C_E}{K_{eq}}\right)}{1 + K_M C_M + K_G C_G} $$

que é a forma de livro-texto. Para Langmuir-Hinshelwood mono-sítio com
reação superficial determinante, o denominador vem ao quadrado; para
dual-sítio, vem como produto de dois balanços. O derivador não sabe disso
de antemão — são consequências do procedimento.

### Consistência termodinâmica

Este ponto merece destaque porque é onde muita análise publicada
escorrega.

As constantes de equilíbrio das etapas de um ciclo catalítico não são
independentes. Se as etapas somam a reação global, então

$$ K_{eq} = \prod_i K_i $$

O pacote **verifica** que as etapas somam a reação global (`Mechanism.validate`)
e **impõe** essa relação, eliminando a constante da etapa determinante em
favor de `K_eq`. A consequência é que a lei derivada se anula exatamente
quando o quociente reacional atinge `K_eq`.

Uma lei que não tem essa propriedade não descreve uma reação reversível —
descreve uma função ajustável com aparência de mecanismo. O teste
`test_velocidade_anula_no_equilibrio` verifica isso para toda família e
toda escolha de etapa determinante.

### Constantes partilhadas

Nas três reações consecutivas, `K_ads_M` é a mesma constante: é a mesma
molécula, no mesmo sítio, no mesmo catalisador. O mesmo vale para o
glicerol e o éster. Só `k`, `K_eq` e as constantes de reação superficial
são específicas de cada etapa.

Sem essa partilha, o modelo LHHW completo teria três denominadores
independentes e vinte e tantos parâmetros — e nenhum conjunto realista de
dados o identificaria. Com ela, a rede completa do Eley-Rideal tem **oito
parâmetros**, dos quais três são constantes de equilíbrio que
normalmente se fixam.

---

## 3. Transporte: o modo de falha mais perigoso

Num monolito, o catalisador está num washcoat de dezenas de micrômetros
na parede do canal. Se a reação for rápida em relação à difusão nesse
filme, o reagente não chega ao interior e a velocidade observada é menor
que a intrínseca.

O problema não é a perda de atividade. É que a cinética observada fica
**deformada de maneira sistemática**:

- a ordem aparente tende a `(n+1)/2` — uma reação de segunda ordem parece
  de ordem 1,5;
- a energia de ativação aparente cai para cerca de metade da verdadeira;
- os termos de inibição do denominador ficam achatados.

Uma varredura de mecanismos sobre dados assim vai encontrar um vencedor
com excelente ajuste estatístico, intervalos de confiança estreitos, e
**mecanismo errado**. É o pior desfecho possível, porque não há sinal de
alarme na estatística.

Por isso o diagnóstico vem antes da cinética. O pacote calcula:

| critério | o que testa | limiar |
|---|---|---|
| Weisz-Prater | gradiente **dentro** do washcoat | < 0,15 |
| Mears | gradiente no **filme externo** | < 0,15 |
| Carberry | fração da força motriz gasta no filme | — |

com o coeficiente de filme vindo da correlação de Hawthorn para canal
quadrado laminar,

$$ Sh = Sh_\infty\left[1 + 0{,}095\,\frac{d_h}{L}\,Re\,Sc\right]^{0{,}45},
\qquad Sh_\infty = 2{,}98 $$

e a efetividade do washcoat pelo módulo de Thiele generalizado de Aris,

$$ \phi = \frac{L\,r(C_s)}{\sqrt{2 D_{ef}\displaystyle\int_0^{C_s} r(C)\,dC}},
\qquad \eta = \frac{\tanh\phi}{\phi} $$

A forma generalizada é o que permite aplicar o conceito a leis LHHW, em
que a "ordem" não é constante.

Se os critérios reprovarem, há três saídas: reduzir a espessura do
washcoat, aumentar a velocidade (o que reduz só a resistência externa), ou
regredir através do modelo de transporte (`mode="full"`), aceitando o custo
computacional e a incerteza adicional em `D_eff`.

---

## 4. Regressão em dois estágios

Uma regressão integral — que integra a rede de EDOs a cada avaliação de
resíduo — sobre 41 candidatos com dez parâmetros cada é proibitiva.
A saída é a que a prática experimental já consagrou:

**Estágio 1, diferencial.** Os perfis são suavizados por spline com
parâmetro escolhido por validação cruzada generalizada, e derivados. A
estequiometria dá as velocidades das três reações por mínimos quadrados:
`r = pinv(ν)·(dC/dt)/w`. Os modelos são então comparados diretamente
contra `dC/dt`, sem integrar nada. Custo: **décimos de segundo por
modelo**.

O resíduo dessa inversão é informativo por si só. Se `ν·r` não reproduz
`dC/dt`, os balanços materiais não fecham — há problema analítico antes de
qualquer discussão de mecanismo.

**Estágio 2, integral.** Os sobreviventes são reajustados por regressão
integral, **semeados pela solução diferencial**. Essa semeadura é o que
torna o estágio viável: partindo já na bacia de atração correta, a
regressão converge em segundos em vez de minutos.

O ranqueamento final sai do estágio integral, porque é ele que não herda o
ruído amplificado pela diferenciação.

### Condicionamento

Duas decisões evitam a maior parte dos problemas de convergência:

*Reparametrização centrada.* Estimar `k₀` e `Ea` da forma de Arrhenius crua
produz correlação próxima de 1 entre os dois, porque o fator
pré-exponencial é uma extrapolação para `1/T = 0`, longe dos dados. Usa-se

$$ k(T) = k(T_{ref})\exp\left[-\frac{E_a}{R}\left(\frac{1}{T}-\frac{1}{T_{ref}}\right)\right] $$

com `T_ref` no centro da faixa experimental.

*Escala logarítmica.* `k` e `K` são positivos por construção. Estimar
`ln k` e `ln K` impõe isso sem barreiras artificiais e equaliza a
sensibilidade entre parâmetros de ordens de grandeza distintas.

*Múltiplas partidas.* A superfície de mínimos quadrados de modelos LHHW é
notoriamente multimodal. Uma única partida encontra um mínimo local, e o
ranqueamento passa a refletir a sorte do chute inicial. O pacote amostra
partidas por sequência de Sobol e retém o melhor mínimo.

---

## 5. Discriminação

Ajustar bem não basta. Um modelo com sete parâmetros quase sempre ajusta
melhor que um com três, e o "vencedor" escolhido só pela soma de quadrados
é o mais flexível, não o mais verdadeiro. Três filtros independentes:

### Parcimônia

AICc — a correção de amostra pequena é a regra, não a exceção, em estudos
cinéticos de bancada. Os pesos de Akaike convertem diferenças de AICc em
probabilidades relativas:

$$ w_i = \frac{\exp(-\Delta_i/2)}{\sum_j \exp(-\Delta_j/2)} $$

**O que esses pesos são:** probabilidade de cada modelo ser o melhor
*entre os examinados*.

**O que não são:** probabilidade de ser verdadeiro. Se o mecanismo real
não está no catálogo, o peso vai inteiro para o menos ruim.

### Admissibilidade físico-química

Regras de Boudart, na forma refinada por Vannice. Verificadas:

- adsorção é exotérmica: `ΔH_ads < 0`;
- adsorção reduz a entropia: `ΔS_ads < 0`, com
  `ΔS_ads = R ln K_ref + ΔH_ads/T_ref`;
- a perda de entropia não excede a entropia disponível da espécie livre;
- energia de ativação positiva;
- `J'J` suficientemente condicionada para que os parâmetros signifiquem
  algo.

> A regra estrita de Vannice para o limite superior de `−ΔS_ads` é de fase
> gasosa. Em fase líquida a molécula já perde graus de liberdade
> translacionais ao solvatar, e o pacote usa um limite mais frouxo,
> configurável em `ENTROPY_BOUNDS_J_MOL_K`.

Este é, na prática, o filtro que mais elimina candidatos — e o que mais
convence uma banca, porque não depende de escolha de critério estatístico.
Na validação sintética, as famílias Langmuir-Hinshelwood ajustam tão bem
quanto a verdadeira, mas são reprovadas por produzirem entropias de
adsorção de −487 J/(mol·K), fisicamente impossíveis, e `cond(J'J) ~ 10²⁰`.

### Estrutura dos resíduos

Um modelo correto deixa resíduos sem padrão. Autocorrelação ao longo do
tempo (Durbin-Watson fora de 1,5–2,5) indica forma funcional errada mesmo
com SSE baixo.

---

## 6. Onde o aprendizado de máquina entra — e onde não

Vale ser explícito, porque é a parte mais fácil de vender mal.

**Não** se trata de treinar uma rede para "prever o mecanismo". Não há
conjunto de treinamento com mecanismos rotulados, e uma rede treinada em
dados de conversão não tem como distinguir mecanismos que produzem
conversões idênticas. Três usos legítimos:

### Teto de desempenho

Uma rede neural ajustada às velocidades extraídas dá o melhor ajuste
alcançável por uma função flexível sem estrutura mecanística. Se o melhor
modelo LHHW empata com ela, a forma mecanística está capturando tudo o que
há nos dados. Se perde por muito, falta estrutura ao mecanismo — ou o que
sobra é ruído, e a rede está decorando.

### Descoberta da forma funcional

Toda lei LHHW é `r = N(C)/D(C)^q`. O que distingue mecanismos é *quais*
termos aparecem em `D` e com que expoente. A regressão racional esparsa
estima isso diretamente, sem enumerar mecanismos.

O truque, na linha do SINDy para não linearidades racionais: para `q = 1`
o problema fica linear depois de multiplicar pelo denominador,

$$ r = \sum_i a_i f_i(C) - \sum_j b_j\,r\,g_j(C) $$

o que permite selecionar termos por mínimos quadrados com limiarização
sequencial. A linearização pondera cada ponto por `D(C)` e enviesa os
coeficientes — por isso a seleção linear é só o primeiro passo, e os
coeficientes finais são reajustados sobre o resíduo verdadeiro
`r − N/D^q`.

Sobre dados de composição bem distribuída, o método recupera a lei
geradora — numerador, os termos corretos do denominador, e o expoente —
excluindo os falsos. Sobre dados de uma única trajetória reacional, não:
veja a seção seguinte.

### Planejamento de experimentos

O critério de Box-Hill maximiza a redução esperada da entropia de Shannon
sobre as probabilidades dos modelos, levando em conta tanto a discrepância
entre previsões quanto a incerteza de cada previsão (método delta sobre a
covariância dos parâmetros). Um ponto onde os modelos discordam muito mas
ambos preveem com enorme incerteza discrimina pouco — o Box-Hill sabe
disso; o critério ingênuo de máxima divergência não.

---

## 7. Colinearidade: o limite que nenhum método vence

Numa corrida que parte de óleo puro, glicerol e éster crescem juntos: são
proporcionais entre si em toda a trajetória. Na validação sintética a
correlação entre os dois chega a 0,99, com VIF acima de 250.

Quando isso acontece, `K_ads_G·C_G` e `K_ads_E·C_E` entram no denominador
como uma única combinação. **Nenhum método consegue atribuir a inibição a
um ou a outro** — nem regressão mecanística, nem rede neural, nem
regressão esparsa. Não é limitação de técnica; é ausência de informação no
dado.

A varredura mecanística *parece* resolver, porque a estequiometria e a
partilha de constantes entre as três reações fornecem estrutura adicional.
Mas a distinção fica apoiada nessa estrutura, não nos dados — e cai junto
se a estrutura estiver errada.

A saída é experimental: alimentar glicerol (ou éster) desde o início em
algumas corridas, quebrando a proporcionalidade. O pacote diagnostica a
colinearidade (`biokin.ml.surrogate.collinearity_report`), avisa no
relatório, e inclui condições dopadas na grade de candidatos do
planejamento. Na validação sintética, duas corridas dopadas bastam para
restaurar a separabilidade.

Este é o tipo de conclusão que a ferramenta existe para produzir: não "o
mecanismo é X", mas "com estes dados, X e Y são indistinguíveis, e o
experimento que os separa é este".

---

## 8. Referências

- Boudart, M.; Djéga-Mariadassou, G. *Kinetics of Heterogeneous Catalytic
  Reactions*. Princeton University Press, 1984.
- Froment, G. F.; Bischoff, K. B.; De Wilde, J. *Chemical Reactor Analysis
  and Design*, 3ª ed. Wiley, 2011. — derivação LHHW e discriminação.
- Vannice, M. A. *Kinetics of Catalytic Reactions*. Springer, 2005. —
  critérios de admissibilidade de parâmetros.
- Box, G. E. P.; Hill, W. J. Discrimination among mechanistic models.
  *Technometrics* 9 (1967) 57.
- Burnham, K. P.; Anderson, D. R. *Model Selection and Multimodel
  Inference*, 2ª ed. Springer, 2002. — pesos de Akaike.
- Aris, R. *The Mathematical Theory of Diffusion and Reaction in Permeable
  Catalysts*. Clarendon, 1975. — módulo de Thiele generalizado.
- Hawthorn, R. D. Afterburner catalysts: effects of heat and mass transfer.
  *AIChE Symp. Ser.* 70 (1974) 428. — Sherwood em monolito.
- Kaheman, K.; Kutz, J. N.; Brunton, S. L. SINDy-PI. *Proc. R. Soc. A* 476
  (2020) 20200279. — regressão racional esparsa.
- Dossin, T. F.; Reyniers, M.-F.; Marin, G. B. Kinetics of heterogeneously
  MgO-catalyzed transesterification. *Appl. Catal. B* 61 (2005) 35.
- Kouzu, M.; Hidaka, J. Transesterification of vegetable oil into biodiesel
  catalyzed by CaO. *Fuel* 93 (2012) 1.
