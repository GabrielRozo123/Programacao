# Quando misturar melhor resfria pior

> **Dek / subtítulo:** Um cliente nos pediu para avaliar se uma bomba de recirculação ajudaria a homogeneizar a temperatura de um tanque resfriado por chiller. A resposta foi sim — e o tanque passou a levar o dobro do tempo para resfriar. Este é o estudo que explica por quê.

---

Existe uma intuição de engenharia que quase sempre funciona: se um tanque está estratificado, misture. Bomba de recirculação, agitador, jato de retorno bem posicionado — qualquer coisa que injete quantidade de movimento e quebre o gradiente térmico.

Quase sempre.

Em um estudo recente para a **GreyLogix**, simulamos exatamente essa modificação em um tanque de solução hidroalcoólica resfriada por chiller externo. A recirculação eliminou a estratificação por completo — o gradiente entre topo e fundo foi a zero. E o tempo de resfriamento **dobrou**.

Não é erro de simulação. É física, e ela cabe em uma equação.

## O problema que motivou o estudo

O sistema é simples de descrever. Um tanque vertical de 3.500 L com fundo cônico armazena a solução; uma bomba retira líquido por um bocal lateral, envia ao chiller e devolve mais frio pelo fundo. A meta de processo é manter a solução fria **e homogênea**.

Um estudo preliminar já havia caracterizado o que acontecia na prática. O fluido frio, mais denso, afundava e se acumulava no fundo, enquanto uma camada quente estagnada permanecia no topo — o clássico **warm lid**. Duas consequências operacionais:

- **O resfriamento ficava lento e desigual.**
- **O sensor de saída enganava o operador.** Ele lia frio, porque estava exatamente onde o frio se acumulava, enquanto boa parte do volume continuava quente.

Esse segundo ponto é o mais perigoso dos dois. Um instrumento que mede corretamente a variável errada é pior que um instrumento descalibrado, porque ninguém desconfia dele.

A GreyLogix então nos trouxe duas perguntas:

1. **Elevar a sucção do chiller** de 0,85 m para 1,35 m reduz a estratificação?
2. **Acrescentar uma bomba de recirculação** de 12 m³/h ajuda a homogeneizar?

## Antes de simular: construir a régua

Um resultado de CFD sem referência é um número solto. Antes de rodar qualquer caso, montamos o benchmark analítico.

As paredes do tanque são inox 304 com 100 mm de isolamento — o ganho térmico pelo ambiente fica abaixo de 2% da capacidade do chiller, o que autoriza tratá-las como adiabáticas. Com isso, e com o chiller devolvendo a uma temperatura fixa de −5 °C, todo o problema colapsa em um único balanço de energia:

```
M·cp·dT/dt = ṁ·cp·(T_retorno − T_sucção)
```

que reorganizado vira:

```
dT/dt = −(1/τ)·(T_sucção + 5)

τ = V/Q = 3,52 m³ ÷ 12 m³/h = 1.055 s
```

Essa equação carrega o estudo inteiro, por um motivo que vale isolar:

> **`T_sucção` é o único grau de liberdade do problema.** A vazão está fixa. A temperatura de retorno está fixa. O volume está fixo. Tudo o que a geometria faz, ela faz através de uma variável só — a temperatura do líquido que chega à sucção do chiller.

Se o tanque estivesse **perfeitamente misturado**, a sucção veria a temperatura média e o resfriamento seria uma exponencial pura:

```
T(t) = −5 + 10·e^(−t/τ)
```

O que dá **99% resfriado em cerca de 4.900 segundos**, ou 82 minutos. Esse é o benchmark do reator de mistura perfeita (CSTR), e é contra ele que os três casos foram medidos.

Dois números de consistência antes de seguir. O duty inicial previsto por essa álgebra é **113,5 kW**; o CFD mediu **115 kW** — 1,4% de diferença. E a energia total a remover é **119,5 MJ**, idêntica nos três casos, porque todos partem de +5 °C, terminam em −5 °C e têm paredes adiabáticas. O que muda entre eles não é *quanto* calor sai. É o **ritmo**.

## O modelo

Simulação transiente em **Simcenter STAR-CCM+**, passo de tempo de 1 s, monofásica, com empuxo governado pela dependência da densidade com a temperatura:

```
ρ(T) = 1082,88 − 0,55·T   [kg/m³, T em K]
```

São 5 kg/m³ de diferença entre −5 °C e +5 °C. Parece pouco. É o motor de tudo o que acontece daqui em diante. Turbulência k-ε Realizable, paredes adiabáticas, condição inicial de +5 °C uniforme, chiller devolvendo a −5 °C com 12 m³/h.

Três configurações:

| Caso | Configuração | Regime que emergiu |
|---|---|---|
| **Baseline** | sucção a 0,85 m (posição original) | curto-circuito |
| **Sim 1** | sucção a 1,35 m | deslocamento |
| **Sim 2** | sucção a 1,35 m + recirculação de 12 m³/h | mistura |

## Baseline: o chiller trabalhando contra si mesmo

Com a sucção a 0,85 m, o chiller **re-aspira o frio que ele mesmo acabou de injetar no fundo**. O líquido percorre um caminho curto entre o retorno e a captação, e a camada quente do topo fica fora do alcance — ela só esfria por acúmulo, conforme a frente fria sobe lentamente.

Em termos da equação: `T_sucção < T_bulk`, então `(T_sucção + 5)` é pequeno e o duty despenca.

**Resultado: ~7.500 s, cerca de 2 horas. 52% mais lento que a mistura perfeita.**

Este é o diagnóstico do problema original. A posição da sucção não estava apenas subótima — estava ativamente sabotando o desempenho do chiller.

## Sim 1: a estratificação como aliada

Elevando a sucção para 1,35 m, a física muda de natureza. O frio denso entra pelo fundo e enche o tanque de baixo para cima, em um regime de *filling box*. A sucção, agora mais alta, **toca a camada quente do topo** e a entrega ao chiller.

<!-- VÍDEO 1 — arquivo: 02_velocidade_sem_recirculacao.mp4 · poster: poster_02_velocidade_sem_recirc.png -->
> **Campo de velocidade e linhas de corrente, sem recirculação.** O retorno frio entra pelo fundo e o escoamento sobe pela parede até a sucção, no alto. É o caminho longo — e é ele que faz o chiller enxergar o líquido mais quente do tanque.

A assinatura desse mecanismo aparece nos monitores: durante os primeiros 700 s, a **temperatura de saída segura em +5 °C** enquanto a média do tanque já está caindo. A sucção está puxando líquido que ainda não foi resfriado. A estratificação cresce até um pico de **9,6 °C** entre topo e fundo.

Quando a frente fria alcança a cota de 1,35 m, a temperatura de saída despenca — exatamente no pico do gradiente — e o ΔT colapsa.

<!-- VÍDEO 2 — arquivo: 01_temperatura_sem_recirculacao.mp4 · poster: poster_01_temperatura_sem_recirc.png -->
> **Campo de temperatura, sem recirculação.** A frente fria sobe do fundo como um pistão, consumindo a camada quente de baixo para cima. Repare que a interface se mantém nítida durante boa parte do transiente.

**Resultado: 3.040 s, cerca de 51 minutos. 38% mais rápido que a mistura perfeita.**

E aqui está o primeiro resultado que merece atenção:

> **A mistura perfeita não é o ótimo.** É um teto — e o deslocamento o supera. A estratificação, neste arranjo, não é o inimigo: é o mecanismo que mantém `T_sucção` acima da média e, portanto, o duty do chiller no máximo.

## Sim 2: a recirculação faz o que prometeu, e cobra por isso

Acrescentando o circuito de recirculação — captação pelo dreno central no ápice do cone, retorno pela tampa — a estratificação **desaparece**. O ΔT entre topo e fundo vai essencialmente a zero. Do ponto de vista de uniformidade, é o melhor resultado possível: o tanque inteiro na mesma temperatura, em qualquer instante.

<!-- VÍDEO 3 — arquivo: 03_temperatura_com_recirculacao.mp4 · poster: poster_03_temperatura_com_recirc.png -->
> **Campo de temperatura, com recirculação.** Compare com o vídeo anterior: não há frente nítida. O tanque resfria como um bloco, uniformemente — e mais devagar.

<!-- VÍDEO 4 — arquivo: 04_velocidade_com_recirculacao.mp4 · poster: poster_04_velocidade_com_recirc.png -->
> **Campo de velocidade, com recirculação.** O segundo circuito injeta quantidade de movimento suficiente para quebrar a estratificação antes que ela se estabeleça.

**Resultado: 6.140 s, 1 h 42 min. 25% mais lento que a mistura perfeita — e o dobro do tempo do Sim 1.**

## Por que a recirculação atrasa

Volte à equação. A taxa de resfriamento é `ṁ·cp·(T_sucção + 5)`.

- **Estratificado (Sim 1):** a sucção alta puxa o líquido mais quente do tanque. `T_sucção > T_bulk` → duty máximo.
- **Homogeneizado (Sim 2):** a sucção passa a ver a média. `T_sucção ≈ T_bulk` → duty igual ao da mistura perfeita.

A recirculação **não remove calor** — ela apenas redistribui. Ao destruir a estratificação, joga fora a vantagem do deslocamento e empurra o sistema de volta para o limite de mistura perfeita.

> Uniformidade e velocidade estão em conflito direto neste arranjo. E o conflito não é acidental: é a mesma variável, `T_sucção`, servindo aos dois objetivos em sentidos opostos.

Há ainda um detalhe que colocou o Sim 2 *abaixo* do teto da mistura perfeita, em vez de exatamente nele. O retorno da recirculação entra pela tampa e desce; a sucção do chiller está a 1,35 m, do mesmo lado do tanque e próxima em cota. Parte do fluido já resfriado volta à sucção antes de varrer o fundo, o que puxa `T_sucção` ligeiramente **abaixo** da média — e o duty junto. A constante de tempo efetiva medida no CFD foi de **1.315 s**, contra os 1.055 s do CSTR ideal, e cresce ainda mais na cauda: sinal de que existe uma fração de volume, na região do cone, com troca mais lenta.

## Como sabemos que não é um erro de simulação

Um resultado contraintuitivo exige mais prova que um resultado esperado. Fizemos três verificações independentes antes de transformar o achado em conclusão.

**Fechamento de energia.** O resíduo do balanço no Sim 2 ficou em **−0,0023 W**, ou 2×10⁻⁸ % da potência trocada. Os três casos removem exatamente os mesmos 119,5 MJ.

**A recirculação é mesmo adiabática.** Se ela estivesse trocando calor por algum artefato numérico, a comparação entre os casos seria inválida. Sobrepondo as temperaturas de captação e de retorno ao longo de todo o transiente, a diferença média foi de **+6,8 milicelsius** — sete milésimos de grau. E mesmo isso tem explicação: é o atraso de um passo de tempo, com o retorno carregando o valor da captação do instante anterior. A energia espúria integrada dá +0,38 MJ, **0,3%** dos 119,5 MJ removidos.

**A hipótese alternativa foi testada e refutada.** A explicação concorrente para "o caso mais misturado é o mais lento" seria vazamento de calor pelas paredes em algum dos casos. O balanço limita qualquer vazamento a menos de 0,07 kW, contra 115 kW de duty. Não é isso.

## O trade-off entregue ao cliente

| | **Sim 1** — só elevar a sucção | **Sim 2** — + recirculação |
|---|---|---|
| Estratificação (ΔT topo–fundo) | 9,6 °C, transitório | **≈ 0 °C** |
| 99% resfriado | **3.040 s** (~51 min) | 6.140 s (~1 h 42) |
| Regime de escoamento | deslocamento | mistura |

A recomendação não é um número. É uma escolha de projeto:

- **Prioridade em tempo de batelada** → elevar a sucção, sem recirculação. Resfria **2,5× mais rápido que a configuração original**.
- **Prioridade em uniformidade térmica** → acrescentar a recirculação, ao custo de dobrar o tempo.

Em qualquer cenário, **elevar a sucção de 0,85 m para 1,35 m é ganho garantido** — resolve o problema que motivou o estudo. A recirculação é um nível adicional de uniformidade, e só se paga se o processo exigir ausência de gradiente.

## Duas lições de método

Vale registrar duas coisas que deram errado no caminho, porque elas dizem mais sobre como se conduz um estudo de CFD do que qualquer imagem bonita de contorno.

### Um monitor frágil quase produziu um achado falso

No baseline, o monitor de ΔT topo–fundo travou em 10 °C e parecia indicar estratificação permanente. Não era.

A sonda do topo estava configurada como *Maximum report*, que retorna a célula mais quente da região. Na zona acima de 0,85 m, onde o escoamento é fraquíssimo, **uma única célula presa perto da parede ficou retida na temperatura inicial de +5 °C** — e o máximo agarrou essa outlier, ignorando que 99,99% do topo já estava a −5 °C. Uma Line Probe ao longo do eixo mostrou o tanque uniforme a −5,0 °C, variando na sétima casa decimal.

A regra que ficou: *Maximum* e *Minimum report* **nunca** devem representar "a temperatura em um ponto". Point Probe, Volume Average de uma fatia fina ou Line Probe — nunca um extremo.

### Uma geometria errada mudou o número, mas não a conclusão

A primeira versão do circuito de recirculação foi modelada com dois bocais laterais. O diagrama do fabricante mostrava outra coisa: captação pelo dreno central no ápice do cone, retorno vertical pela tampa. Refazendo, o Sim 2 passou de *"reduz a estratificação pela metade, na velocidade da mistura perfeita"* para *"elimina a estratificação, 25% mais lento que a mistura perfeita"*.

O resultado mudou nos dois eixos — e a conclusão **ficou mais forte**, não mais fraca. Os dois lados do trade-off foram para os extremos: a uniformidade deixou de ser parcial e virou total; o custo deixou de ser nulo e virou mensurável.

## O que o CFD entregou aqui

Não foi uma imagem bonita de contorno de temperatura. Foi um **trade-off quantificado** que não estava disponível por intuição, por correlação de projeto nem por medição no equipamento existente — porque a configuração alternativa ainda não existe fisicamente.

O cliente perguntou se a recirculação ajudaria a homogeneizar. A resposta é sim, completamente. A pergunta que ele não tinha feito, e que o estudo respondeu junto, é **quanto isso custa em tempo de batelada**: 51 minutos contra 1 h 42.

Com os dois números na mesa, a decisão deixa de ser técnica e passa a ser de processo — que é exatamente onde ela deve estar.

---

*Estudo conduzido pela CAEXPERTS em Simcenter STAR-CCM+: modelo transiente monofásico com empuxo, turbulência k-ε Realizable, paredes adiabáticas. O diâmetro da linha de recirculação foi adotado como DN65, por não estar cotado no diagrama de referência.*

**Tem um equipamento cujo comportamento térmico você precisa entender antes de modificá-lo? [Fale com a nossa equipe.]**

---
---

## Notas de publicação — NÃO PUBLICAR

### Ordem dos vídeos no post

| Posição | Arquivo | Poster | Seção |
|---|---|---|---|
| Vídeo 1 | `02_velocidade_sem_recirculacao.mp4` | `poster_02_velocidade_sem_recirc.png` | Sim 1 — a estratificação como aliada |
| Vídeo 2 | `01_temperatura_sem_recirculacao.mp4` | `poster_01_temperatura_sem_recirc.png` | Sim 1 — a estratificação como aliada |
| Vídeo 3 | `03_temperatura_com_recirculacao.mp4` | `poster_03_temperatura_com_recirc.png` | Sim 2 — a recirculação faz o que prometeu |
| Vídeo 4 | `04_velocidade_com_recirculacao.mp4` | `poster_04_velocidade_com_recirc.png` | Sim 2 — a recirculação faz o que prometeu |

Todos os quatro já têm a marca CAEXPERTS gravada no quadro. Publicar com `autoplay muted loop playsinline` e o poster correspondente — são clipes curtos e sem áudio, funcionam melhor em loop silencioso.

Os vídeos 2 e 3 são o par mais forte do post: mesma variável (temperatura), configurações opostas. Se a plataforma permitir, vale exibi-los **lado a lado** em vez de sequencialmente.

### Figura pendente

O post ganharia muito com o gráfico dos três casos contra a curva de mistura perfeita. **A figura existente está desatualizada** (`figuras/tres_casos_vs_cstr.png` mostra o Sim 2 colado na curva do CSTR — versão anterior à correção da geometria). Refazer com o T_bulk(t) do Sim 2 corrigido antes de publicar.

### SEO

- **Title tag:** Quando misturar melhor resfria pior — estudo CFD de estratificação térmica
- **Meta description:** Simulação CFD em STAR-CCM+ mostra que adicionar recirculação a um tanque resfriado por chiller elimina a estratificação, mas dobra o tempo de resfriamento. O estudo explica o mecanismo.
- **Tags:** CFD, STAR-CCM+, estratificação térmica, transferência de calor, chiller, simulação transiente, mistura

### Pendências antes de publicar

1. Confirmar com a GreyLogix o uso do nome e dos dados de processo no blog.
2. Refazer a figura dos três casos (ver acima).
3. Definir o link do CTA final.
