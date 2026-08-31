# P2 · Splitter C3 no DWSIM — montagem, convergência e integração com o AI4Tech

Guia para construir o splitter propeno/propano no DWSIM e ligá-lo ao AI4Tech
Suite como **DWSIM Case**. O gêmeo rápido em Python está em
[`casos-python/02-splitter-c3/`](../casos-python/02-splitter-c3/CONFIG.md) e
serve de referência para conferir se a coluna do DWSIM convergiu para algo
fisicamente sensato.

> **Sobre a versão.** Você mencionou que o DWSIM atualizou. Os nomes de menu
> abaixo seguem a organização usual do DWSIM Pro/Patreon Edition; se algum item
> tiver mudado de lugar na sua versão, o conceito continua o mesmo. Me diga a
> versão e eu ajusto o guia.

---

## Etapa A — a coluna sozinha

### A.1 Componentes e pacote termodinâmico

| Item | Escolha | Por quê |
|---|---|---|
| Componentes | Propylene (propeno) e Propane | binário puro, sem inertes |
| Pacote | **Peng-Robinson** | padrão da indústria para hidrocarbonetos leves sob pressão |
| Alternativa | SRK ou PR-SRK | compare: a diferença em α se traduz direto em número de estágios |

Vale um experimento de cinco minutos antes de qualquer coisa: monte um flash
bifásico a 18 bar com 75 % molar de propeno e compare o α (razão dos K-values)
entre PR e SRK. Como a coluna precisa de ~200 estágios, uma diferença de 1 % em
α desloca o número de estágios em dezenas. **Esse é o cálculo que justifica
escolher o pacote com cuidado**, e é um ótimo primeiro resultado para registrar.

### A.2 Corrente de alimentação

| Propriedade | Valor |
|---|---|
| Vazão molar | 1000 kmol/h |
| Composição | 75 % mol propeno, 25 % mol propano |
| Pressão | 18 bar |
| Condição térmica | líquido saturado (fração de vapor = 0) |

Alinhado com o caso base em Python, para que a comparação seja direta.

### A.3 Coluna de destilação rigorosa

| Parâmetro | Valor inicial |
|---|---|
| Número de estágios | **comece com 50** (não com 200 — ver A.4) |
| Condensador | total |
| Refervedor | parcial (conta como estágio) |
| Estágio de alimentação | metade da coluna |
| Pressão no condensador | 18 bar |
| Perda de carga | **zero no início**; introduza depois |
| Especificação do condensador | razão de refluxo = 15 |
| Especificação do refervedor | vazão molar de destilado = 746 kmol/h |
| Método de solução | **Inside-Out (Russell)** |

Duas especificações de **operação** (refluxo e vazão), não de pureza. Isso é
deliberado: especificação de pureza numa coluna de α baixo é muito mais difícil
de convergir. Troque para pureza só depois que a coluna estiver estável — e,
para o DOE do AI4Tech, mantenha as especificações de operação, porque assim
todo ponto do DOE converge.

### A.4 Convergência — a parte que dá trabalho

Uma coluna com α ≈ 1,12 e 200 estágios é genuinamente difícil. As composições
mudam pouquíssimo de prato a prato, e o solver passa perto do pinch a maior
parte da coluna. Ataque assim:

1. **Suba os estágios em degraus.** Converja com 50, depois 100, 150, 200,
   resolvendo de novo a cada passo. Cada solução convergida vira a estimativa
   inicial da próxima. Ir direto para 200 quase sempre falha.
2. **Use o Inside-Out.** Para binário próximo do pinch ele costuma ser o mais
   robusto. Se oscilar, tente Napthali-Sandholm (correção simultânea).
3. **Amortecimento.** Se as composições oscilarem entre iterações, reduza o
   fator de amortecimento para 0,5–0,7 e aumente o limite de iterações.
4. **Perda de carga por último.** Zero no início. Depois introduza ~0,003 bar
   por prato (≈ 0,7 bar em 235 pratos) e reconverja.
5. **Use a Shortcut Column como estimativa.** O DWSIM tem uma coluna de atalho
   (Fenske-Underwood-Gilliland). Rode-a primeiro para obter N e R aproximados —
   ou pegue `N_min`, `R_min` e `R_sobre_Rmin` direto das saídas do caso Python,
   que já os calcula.

**Referência de chegada.** Com N = 200, alimentação no meio, R = 15 e
D = 746 kmol/h a 18 bar, o modelo em Python dá:

| Grandeza | Python (atalho) |
|---|---|
| Propeno no topo | 99,85 % mol |
| Propano no fundo | 98,09 % mol |
| Refervedor | 42,1 MW |
| T topo / fundo | 44,2 / 52,4 °C |

Se o DWSIM devolver algo na mesma vizinhança, a coluna está montada certo. Se
divergir muito, o suspeito número um é o pacote termodinâmico, e o número dois
é o estágio de alimentação. **Registre a diferença**: ela é o erro do atalho, e
é um resultado do projeto, não um problema a esconder.

### A.5 Diâmetro e custo

O DWSIM não dimensiona a coluna sozinho para custeio. Duas opções:

- Ler `Q_refervedor` e a vazão de vapor do DWSIM e aplicar as correlações de
  Souders-Brown e de custo já implementadas no caso Python.
- Fazer o custeio fora, no módulo de análise, a partir das saídas do DWSIM.

Para a otimização multiobjetivo, o mínimo necessário do DWSIM é: pureza de
topo, pureza de fundo, carga do refervedor e vazão de vapor no topo.

---

## Integração com o AI4Tech Suite

### Variáveis de entrada a expor

| Variável | Onde fica no DWSIM |
|---|---|
| Razão de refluxo | especificação do condensador |
| Vazão de destilado | especificação do refervedor |
| Pressão do condensador | parâmetro da coluna |
| Composição da alimentação | corrente de alimentação |
| Vazão de alimentação | corrente de alimentação |

**Número de estágios e estágio de alimentação são o ponto delicado.** São
parâmetros estruturais: dependendo da versão, podem não estar expostos como
variável manipulável pelo AI4Tech. Confira no wizard. Se não estiverem:

- Rode um DOE para cada configuração estrutural (por exemplo N = 150, 180, 200,
  220) e junte os resultados, tratando N como variável categórica.
- Ou deixe a estrutura fixa e otimize só a operação — que é, aliás, o problema
  real de quem já tem a coluna construída.

### O campo Cell

No wizard do DWSIM Case, cada variável precisa de uma referência ao objeto do
flowsheet. **Não vou chutar a sintaxe** — ela mudou entre versões e a suite
costuma oferecer um seletor de objetos e propriedades. Use o seletor, e se ele
mostrar o caminho em texto, me mande um exemplo que eu monto a tabela completa
no formato certo.

### Custo de execução, e como não desperdiçar quota

Uma coluna rigorosa de 200 estágios leva alguns segundos por avaliação. Um DOE
de 500 pontos pode levar de vinte minutos a algumas horas. Duas consequências:

- **Use o Remote Worker local** para o lote grande. Deixe a nuvem para o que
  precisa de paralelismo.
- **Trabalhe em multifidelidade**, que é o que este repositório permite:

| Etapa | Modelo | Custo | Serve para |
|---|---|---|---|
| 1 | Python (3 ms/run) | grátis | Varrer 5000 pontos, entender a topologia, escolher as faixas |
| 2 | DWSIM rigoroso | horas | DOE menor e bem posicionado, 200–300 pontos |
| 3 | Surrogate do DWSIM | µs | Otimização com dezenas de milhares de avaliações |
| 4 | DWSIM rigoroso | minutos | Validar os melhores pontos do Pareto |

Escolher as faixas do DOE com o modelo barato antes de gastar o caro é a
diferença entre um estudo eficiente e um desperdício de quota.

---

## Etapa B — expandir para um trecho de processo

Quando a coluna estiver dominada, vale crescer. Duas direções, ambas reais:

### B.1 Bomba de calor por recompressão de vapor

Condensador a 44 °C, refervedor a 52 °C: **8 K de diferença**. Comprimir o
vapor de topo até que condense contra o fundo elimina quase todo o vapor de
baixa pressão e boa parte da água de resfriamento.

Flowsheet: coluna + compressor + trocador casco-tubo servindo de condensador e
refervedor ao mesmo tempo + válvula de expansão. É um circuito fechado com
interação forte — e portanto um problema de otimização de verdade: troca-se
OPEX de vapor por OPEX de eletricidade mais CAPEX de compressor. Muitos
splitters C3 modernos operam exatamente assim.

**É o que eu recomendo como Etapa B**: acrescenta só três equipamentos, mas
muda completamente a estrutura econômica do problema.

### B.2 Depropanizador alimentando o splitter

Duas colunas em série: o depropanizador separa o corte C3 dos C4+, e o splitter
separa propeno de propano. Introduz interação entre colunas — a especificação
de fundo do depropanizador determina a alimentação do splitter.

Mais realista como trecho de unidade, mas mais lento de convergir. Bom como
terceiro passo.

---

## Ordem sugerida

1. Flash a 18 bar, comparando α entre PR e SRK. Meia hora, e já é resultado.
2. Coluna com 50 estágios convergindo com especificações de operação.
3. Subir para 200 estágios em degraus.
4. Comparar com a tabela de referência da seção A.4 e registrar a diferença.
5. Criar o DWSIM Case no AI4Tech e rodar um DOE pequeno (50 pontos) só para
   validar o encanamento.
6. DOE de verdade no worker local, com as faixas escolhidas pelo modelo Python.
7. Surrogate, otimização, MCDM, e validação cruzada dos melhores pontos.
