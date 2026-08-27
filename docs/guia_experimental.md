# Guia experimental

Tradução do método em decisões de bancada. O que medir, em que faixa, e
por quê — na ordem em que as decisões aparecem.

---

## Antes de qualquer cinética: os ensaios de exclusão

Não adianta discriminar mecanismos sobre dados disfarçados por transporte
ou por desativação. Três ensaios, e são rápidos:

**1. Independência da velocidade em relação à hidrodinâmica.**
Repita a mesma condição em duas ou três velocidades superficiais (ou
rotações, em batelada). Se a conversão por tempo espacial mudar, há
limitação de filme externo. Aumente a velocidade até a conversão parar de
responder, e trabalhe acima disso.

**2. Independência em relação à espessura do washcoat.**
O análogo do teste de tamanho de partícula, que em monolito se faz com
cargas diferentes de washcoat. Se a velocidade *por grama de catalisador*
cair com o aumento da espessura, há limitação interna. Este é o ensaio que
mais gente pula, e o que mais compromete resultados.

**3. Estabilidade.**
Uma corrida longa na condição mais severa, com balanço de massa fechado.
Queda de atividade indica lixiviação da fase ativa (comum em CaO, que
forma gliceróxido de cálcio solúvel) ou envenenamento por ácidos graxos
livres e água. Se houver, meça o metal em solução — desativação aparece
como desvio sistemático nos resíduos, e a ferramenta vai atribuí-la a um
termo de inibição inexistente.

Rode `python -m biokin transport` com a sua geometria e uma estimativa da
velocidade observada para saber, antes da bancada, se os ensaios 1 e 2 são
mesmo necessários naquela faixa.

---

## Faixa experimental

### Temperatura

**Pelo menos três níveis**, cobrindo 25–30 K. Dois níveis dão uma reta de
Arrhenius sem grau de liberdade para julgá-la; e para estimar entalpias de
adsorção junto com energias de ativação a faixa precisa ser larga.

Nota franca: mesmo com 30 K e 3 % de ruído, as entalpias de adsorção saem
com intervalo de confiança de ±40 a 60 kJ/mol na validação sintética. As
energias de ativação, essas saem bem (±13 kJ/mol). Se o objetivo incluir
`ΔH_ads` confiável, precisa de mais temperaturas ou de medida
independente (calorimetria, TPD).

### Razão molar metanol:óleo

**Pelo menos três níveis, com espalhamento grande** — 3:1 (estequiométrico),
9:1 e 20:1 é melhor que 6:1, 9:1 e 12:1.

É a variável que mais discrimina. Os denominadores LHHW diferem entre si
justamente em como respondem à cobertura por metanol: em `K_M·C_M ≪ 1` a
lei parece de primeira ordem em metanol para todos os mecanismos; só em
cobertura alta as famílias se separam. Trabalhar só em 6:1–12:1 é ficar na
região onde todos os modelos concordam.

### Conversão

**Chegue acima de 80 % em pelo menos algumas corridas.** A inibição por
glicerol só se manifesta quando há glicerol. Na validação sintética,
`K_ads_G·C_G` só se torna comparável a `K_ads_M·C_M` acima de ~70 % de
conversão — abaixo disso o termo é invisível e o modelo sem inibição
ajusta igualmente bem.

### Corridas com produto na alimentação

**São as mais informativas, e quase ninguém faz.**

Numa corrida que parte de óleo puro, glicerol e éster crescem juntos:
correlação de 0,99. Suas constantes de adsorção entram no denominador como
uma única combinação e não podem ser separadas por método nenhum.

Duas ou três corridas com glicerol adicionado de saída (0,2–0,5 mol/L) e
duas com éster adicionado (0,5–1,5 mol/L) resolvem. Na validação
sintética, duas bastam para o diagnóstico de colinearidade passar de
reprovado a aprovado.

É também o ensaio que responde à pergunta prática do processo: **remover
glicerol continuamente aumenta a taxa?** Se `K_ads_G` for grande, sim — e
isso justifica um reator de membrana ou decantação intermediária.

---

## O que medir

| espécie | como | por quê |
|---|---|---|
| TG, DG, MG | CG (EN 14105) ou HPLC-SEC | **os intermediários são o que discrimina.** DG e MG passam por máximo, e a posição e altura desse máximo dependem da razão entre as constantes das três etapas |
| Éster (FAME) | CG (EN 14103) | resposta principal, e a mais precisa |
| Glicerol | CG ou enzimático | necessário para o termo de inibição |
| Metanol | dispensável | recuperado pelo balanço com o éster |

**Medir só o teor de éster é o erro mais caro.** O pacote funciona com
isso — resíduos são calculados só nas espécies medidas — mas o poder
discriminatório cai muito. Vários mecanismos produzem curvas de éster
quase idênticas e perfis de DG/MG bem diferentes.

**Amostragem:** 7 a 9 pontos por corrida, mais densos no início. A
informação cinética está na curvatura inicial; pontos no platô final
custam o mesmo e informam menos.

---

## Planejamento mínimo

Um conjunto que sustenta a discriminação, com **cerca de 20 corridas**:

| bloco | corridas | condições |
|---|---|---|
| grade térmica | 9 | 3 temperaturas × 3 razões molares (3:1, 9:1, 20:1) |
| dopagem com glicerol | 3 | `C_G0` = 0,2 / 0,35 / 0,5 mol/L, condição central |
| dopagem com éster | 2 | `C_E0` = 0,5 / 1,5 mol/L, condição central |
| carga de catalisador | 2 | metade e o dobro da carga central |
| réplicas | 3 | condição central, em dias diferentes |
| exclusão de transporte | 2–3 | velocidades e espessuras de washcoat |

As réplicas em dias diferentes são o que dá a estimativa honesta do erro
experimental — sem ela, o `sigma` do planejamento de Box-Hill é chute, e
os critérios de informação comparam modelos numa escala arbitrária.

Depois da primeira rodada, rode

```bash
python -m biokin design meus_dados.csv
```

e deixe o critério de Box-Hill escolher os próximos ensaios. Ele leva em
conta o que os dados já mostraram: se dois modelos empataram, ele aponta a
condição em que eles mais divergem *relativamente à incerteza com que cada
um prevê*.

---

## Constantes de equilíbrio

**Fixe-as.** Longe do equilíbrio — que é onde se opera — o termo reverso
quase não influencia a velocidade, e tentar estimar `K_eq` a partir de
dados cinéticos produz intervalos de confiança de várias ordens de
grandeza que contaminam a comparação entre modelos. Na validação
sintética, `ln K_eq` sai com intervalo de ±16 quando estimado junto.

Duas fontes:

- **termodinâmica**, a partir de energias de Gibbs de formação;
- **experimental**, corridas longas até composição estacionária, na faixa
  de temperatura de interesse. São poucas corridas e servem para todos os
  modelos.

Depois passe `--keq K1 K2 K3` na linha de comando.

---

## Lendo o relatório

A saída da varredura tem sete seções. O que olhar em cada uma:

1. **Transporte** — se alguma corrida reprovar, pare aqui. O resto do
   relatório descreve cinética aparente.

2. **Dados diferenciais** — o erro de fechamento estequiométrico é um
   controle de qualidade analítica. Acima de 20 %, verifique os balanços de
   massa antes de discutir mecanismo. O diagnóstico de colinearidade
   aparece aqui.

3. **Rede neural** — teto de desempenho. Compare com o R² do melhor
   modelo mecanístico.

4. **Forma funcional descoberta** — a estrutura que a regressão esparsa
   extrai sem enumerar mecanismos. Concorda com o vencedor da varredura?
   Discordância é sinal de que o catálogo pode estar incompleto.

5. **Triagem diferencial** — ranqueamento rápido de todos os candidatos.

6. **Regressão integral** — o ranqueamento que vale. Olhe a coluna
   "situação": modelos reprovados pelos critérios termodinâmicos aparecem
   com o número de violações. Olhe a razão de evidência entre o primeiro e
   o segundo: abaixo de 3, os dados não decidem.

7. **Próximos experimentos** — se o topo estiver empatado, é daqui que sai
   a próxima rodada.

---

## O que a ferramenta não decide

Uma discriminação bem-sucedida elimina candidatos incompatíveis com os
dados. **Não demonstra um mecanismo.** Nenhum ajuste de dados macroscópicos
demonstra.

O que confirma espécies de superfície é evidência direta: DRIFTS *in situ*
mostrando a banda do metóxido, TPD quantificando sítios básicos, XPS antes
e depois da reação, cálculos DFT das barreiras das etapas postuladas.

O papel do que está aqui é diferente e complementar: reduzir o espaço de
mecanismos plausíveis de dezenas a dois ou três, dizer com que confiança
essa redução se sustenta, e apontar o experimento que separaria os
finalistas. Apresentado assim — e não como "o programa descobriu o
mecanismo" — é uma contribuição defensável.
