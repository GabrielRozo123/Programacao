# Quando misturar melhor resfria pior

**Um estudo CFD de estratificação térmica num tanque de 3.500 L mostrou que adicionar uma bomba de recirculação dobra o tempo de resfriamento. O resultado contraria a intuição — e a simulação explica exatamente por quê.**

---

## O pedido

A GreyLogix opera um tanque de solução hidroalcoólica resfriada por chiller externo. A solução sai do tanque, passa pelo trocador, volta mais fria. O objetivo de processo é simples de enunciar: manter o líquido frio **e homogêneo**.

Um estudo preliminar já havia caracterizado o problema. O tanque estratificava: o fluido frio, mais denso, afundava e se acumulava no fundo, enquanto uma camada quente estagnada permanecia no topo — o clássico *warm lid*. O resfriamento ficava lento e desigual, e havia um efeito operacional pior que a lentidão: **o sensor de saída enganava o operador.** Ele lia frio, porque estava posicionado onde o frio se acumulava, enquanto boa parte do volume continuava quente.

A pergunta que chegou para esta rodada tinha duas partes:

1. Elevar a sucção do chiller de 0,85 m para 1,35 m reduz a estratificação?
2. Acrescentar uma bomba de recirculação de 12 m³/h ajuda a homogeneizar?

A segunda pergunta parecia ter resposta óbvia. Bomba de recirculação mistura; misturar elimina gradiente; portanto, melhor. A primeira parte disso se confirmou. A conclusão que parecia decorrer dela, não.

## A régua: por que a mistura perfeita é o benchmark certo

Antes de rodar qualquer caso, vale montar a referência analítica. Com paredes adiabáticas — o tanque é inox 304 com 100 mm de isolamento, e o ganho térmico estimado fica abaixo de 2% da capacidade do chiller — e temperatura de retorno fixa em −5 °C, todo o problema colapsa numa equação de balanço:

```
M·cp·dT/dt = ṁ·cp·(T_retorno − T_sucção)
```

que reorganizada vira:

```
dT/dt = −(1/τ)·(T_sucção + 5),    τ = V/Q = 3,52 m³ / (12 m³/h) = 1.055 s
```

Essa equação carrega o estudo inteiro, e por um motivo específico: **`T_sucção` é o único grau de liberdade.** A vazão está fixa, a temperatura de retorno está fixa, o volume está fixo. Tudo que a geometria faz, ela faz através de uma coisa só — a temperatura do líquido que chega na sucção do chiller.

Se o tanque estivesse perfeitamente misturado, a sucção veria a temperatura média e o resfriamento seria exponencial puro:

```
T(t) = −5 + 10·e^(−t/τ)
```

Isso dá **99% resfriado em cerca de 4.900 s**, ou 82 minutos. É o benchmark do reator de mistura perfeita (CSTR). Dois números de consistência antes de seguir: o duty inicial previsto por essa álgebra é **113,5 kW**, contra **115 kW** medidos no CFD (1,4% de diferença); e a energia total a remover é **119,5 MJ**, idêntica nos três casos, porque todos partem de +5 °C e terminam em −5 °C com paredes adiabáticas. O que muda entre eles não é quanto calor sai — é o **ritmo**.

## Três configurações, três regimes de escoamento

O modelo é transiente (Δt = 1 s), monofásico, com empuxo governado pela dependência da densidade com a temperatura:

```
ρ(T) = 1082,88 − 0,55·T   [kg/m³, T em K]
```

São 5 kg/m³ de diferença entre −5 °C e +5 °C. Parece pouco. É o motor de tudo que acontece a seguir. Turbulência k-ε Realizable, paredes adiabáticas, condição inicial de +5 °C uniforme, chiller devolvendo a −5 °C com 12 m³/h.

| Caso | Configuração | Regime que emergiu |
|---|---|---|
| **Baseline** | sucção a 0,85 m (posição original) | curto-circuito |
| **Sim 1** | sucção a 1,35 m | deslocamento |
| **Sim 2** | sucção a 1,35 m + recirculação de 12 m³/h | mistura |

### Baseline — o curto-circuito

Com a sucção a 0,85 m, o chiller **re-aspira o frio que ele mesmo acabou de injetar no fundo**. A camada quente do topo fica fora do alcance e só esfria por acúmulo, conforme a frente fria sobe. A temperatura que chega na sucção é **menor** que a média do tanque, então `(T_sucção + 5)` é pequeno e o duty despenca.

Resultado: **~7.500 s**, cerca de 2 horas. **52% mais lento que a mistura perfeita.**

Este é o diagnóstico do problema original. A posição da sucção não estava apenas subótima — estava trabalhando contra o próprio chiller.

### Sim 1 — o deslocamento

Subindo a sucção para 1,35 m, a física muda de natureza. O frio denso entra pelo fundo e enche o tanque de baixo para cima, num regime de *filling box*. A sucção, agora mais alta, **toca a camada quente do topo** e a entrega ao chiller.

A assinatura disso aparece nos monitores: durante os primeiros 700 s, a temperatura de saída **segura em +5 °C** enquanto o bulk já está caindo. A sucção está puxando líquido que ainda não foi resfriado. A estratificação cresce até um pico de **9,6 °C** entre topo e fundo. Quando a frente fria alcança a cota de 1,35 m, a temperatura de saída despenca — exatamente no pico do gradiente — e o ΔT colapsa.

Resultado: **3.040 s**, cerca de 51 minutos. **38% mais rápido que a mistura perfeita.**

E aqui está o primeiro resultado que merece atenção: **a mistura perfeita não é o ótimo.** É um teto que o deslocamento supera. A estratificação, neste arranjo, não é o inimigo — é o mecanismo que mantém `T_sucção` acima da média e, portanto, o duty do chiller no máximo.

### Sim 2 — a mistura

Acrescentando o circuito de recirculação — captação pelo dreno central no ápice do cone, retorno pela tampa — a estratificação **desaparece**. O ΔT topo-fundo vai essencialmente a zero. Do ponto de vista de uniformidade, é o melhor resultado possível.

Resultado: **6.140 s**, 1 h 42 min. **25% mais lento que a mistura perfeita, e o dobro do tempo do Sim 1.**

## Por que a recirculação atrasa

Volte à equação. A taxa de resfriamento é `ṁ·cp·(T_sucção + 5)`.

- **Estratificado (Sim 1):** a sucção alta puxa o líquido mais quente do tanque. `T_sucção > T_bulk` → duty máximo.
- **Homogeneizado (Sim 2):** a sucção passa a ver a média. `T_sucção ≈ T_bulk` → duty igual ao do CSTR.

A recirculação não remove calor — ela apenas redistribui. Ao destruir a estratificação, ela joga fora a vantagem do deslocamento e empurra o sistema de volta para o limite de mistura perfeita. **Uniformidade e velocidade estão em conflito direto neste arranjo, e o conflito não é acidental: é a mesma variável, `T_sucção`, servindo aos dois objetivos em sentidos opostos.**

Há ainda um detalhe que colocou o Sim 2 *abaixo* do teto do CSTR, em vez de exatamente nele. O retorno da recirculação entra pela tampa a r ≈ 665 mm e desce; a sucção do chiller está a 1,35 m, do mesmo lado do tanque e próxima em cota. Parte do fluido já resfriado retorna à sucção antes de varrer o fundo, o que puxa `T_sucção` ligeiramente **abaixo** da média — e o duty junto. A constante de tempo efetiva medida no CFD foi de 1.315 s contra os 1.055 s do CSTR ideal, e cresce ainda mais na cauda, sinal de que existe uma fração de volume (a região do cone) com troca mais lenta.

## Como sabemos que não é um erro de simulação

Resultado contraintuitivo exige mais prova que resultado esperado. Foram três verificações independentes antes de o achado virar conclusão:

**Fechamento de energia.** O resíduo do balanço no Sim 2 corrigido ficou em **−0,0023 W**, ou 2×10⁻⁸ % da potência trocada. Os três casos removem os mesmos 119,5 MJ.

**A recirculação é mesmo adiabática.** Se ela estivesse trocando calor por algum artefato numérico, a comparação entre os casos seria inválida. Sobrepondo a temperatura de captação e a de retorno ao longo de todo o transiente, a diferença média foi de **+6,8 milicelsius** — sete milésimos de grau. E mesmo isso tem explicação: é o atraso de um passo de tempo, com o retorno carregando o valor da captação do instante anterior. A energia espúria integrada dá +0,38 MJ, **0,3% dos 119,5 MJ** removidos. A recirculação mistura e não troca calor.

**A hipótese alternativa foi testada e refutada.** A explicação concorrente para "o caso mais misturado é mais lento" seria vazamento de calor pelas paredes em algum dos casos. A ponta do balanço limita qualquer vazamento a menos de 0,07 kW, contra os 115 kW de duty. Não é isso.

## O trade-off que o cliente recebeu

| | **Sim 1** — só elevar a sucção | **Sim 2** — + recirculação |
|---|---|---|
| Estratificação (ΔT topo-fundo) | 9,6 °C, transitório | **≈ 0 °C** |
| 99% resfriado | **3.040 s** (~51 min) | 6.140 s (~1 h 42) |
| Regime | deslocamento | mistura |

E a recomendação, que não é um número e sim uma escolha de projeto:

- **Prioridade em tempo de batelada** → Sim 1. Elevar a sucção de 0,85 para 1,35 m resfria **2,5× mais rápido que a configuração original** e resolve o problema que motivou o estudo.
- **Prioridade em uniformidade térmica** → acrescentar a recirculação, ao custo de dobrar o tempo.

Em qualquer cenário, **elevar a sucção é ganho garantido**. A recirculação é um nível adicional de uniformidade, e só se paga se o processo exigir ausência de gradiente.

## Duas lições de método

Vale registrar duas coisas que deram errado no caminho, porque elas dizem mais sobre como se conduz um estudo de CFD do que os resultados bonitos.

**Um monitor frágil quase produziu um achado falso.** No baseline, o monitor de ΔT topo-fundo travou em 10 °C e parecia indicar estratificação permanente. Não era. A sonda de temperatura do topo estava configurada como *Maximum report*, que retorna a célula mais quente da região. Na zona acima de 0,85 m, onde o escoamento é fraquíssimo, **uma única célula presa perto da parede ficou retida na temperatura inicial de +5 °C** — e o máximo agarrou essa outlier, ignorando que 99,99% do topo já estava a −5 °C. A Line Probe ao longo do eixo mostrou o tanque uniforme a −5,0 °C, variando na sétima casa decimal.

A regra que ficou: *Maximum* e *Minimum report* nunca devem ser usados para representar "a temperatura num ponto". Point Probe, Volume Average de uma fatia fina ou Line Probe — nunca um extremo.

**Uma geometria errada mudou o número, mas não a conclusão.** A primeira versão do circuito de recirculação foi modelada com dois bocais laterais. O diagrama do fabricante mostrava outra coisa: captação pelo dreno central no ápice do cone, retorno vertical pela tampa. Refazendo, o Sim 2 passou de "reduz a estratificação pela metade, na velocidade da mistura perfeita" para "elimina a estratificação, 25% mais lento que a mistura perfeita".

O resultado mudou nos dois eixos — e a conclusão **ficou mais forte**, não mais fraca. Os dois lados do trade-off foram para os extremos: a uniformidade deixou de ser parcial e virou total; o custo deixou de ser nulo e virou mensurável. A mensagem central, *a recirculação entrega uniformidade e não velocidade*, saiu mais nítida da correção do que estava antes dela.

## O que o CFD entregou aqui

Não foi uma imagem bonita de contorno de temperatura. Foi um **trade-off quantificado** que não estava disponível por intuição, por correlação de projeto ou por medição no equipamento existente — porque a configuração alternativa ainda não existe fisicamente.

O cliente perguntou se a recirculação ajudaria a homogeneizar. A resposta é sim, completamente. A pergunta que ele não tinha feito, e que o estudo respondeu junto, é quanto isso custa em tempo de batelada. São 51 minutos contra 1 h 42.

Com os dois números na mesa, a decisão deixa de ser técnica e passa a ser de processo — que é exatamente onde ela deve estar.

---

*Estudo conduzido pela CAEXPERTS em Simcenter STAR-CCM+. Modelo transiente monofásico com empuxo, k-ε Realizable, paredes adiabáticas. Diâmetro da linha de recirculação adotado como DN65 (não cotado no diagrama de referência).*
