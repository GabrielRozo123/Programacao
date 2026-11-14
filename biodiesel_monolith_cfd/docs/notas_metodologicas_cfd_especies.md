# Notas metodológicas — transporte de espécies com reação de parede em CFD

**Dois modos de falha silenciosa encontrados na Fase 3**
Gabriel Rozo · FEQ/UNICAMP

Ambos têm a mesma assinatura perversa: **resíduos convergidos, soma de frações
mássicas igual a 1, fluxos de parede coerentes, campos visualmente plausíveis —
e balanço global de massa errado por ordens de grandeza.** Nenhum dos dois é
detectável pelos indicadores que o solver oferece por padrão. Registro aqui
porque custaram, somados, cerca de seis semanas e oito corridas completas.

---

## Nota I — A lei de Fick com difusividades desiguais não conserva massa

### O problema

Num modelo multicomponente de N espécies, a formulação de Fick escreve o fluxo
difusivo de cada espécie como

```
j_i = −ρ D_i ∇Y_i
```

A conservação da massa total exige que a soma dos fluxos difusivos se anule:

```
Σ j_i = −ρ Σ D_i ∇Y_i = 0
```

Como ΣY_i = 1 implica Σ∇Y_i = 0, essa condição é satisfeita **se e somente se
todos os D_i forem iguais**. Com difusividades distintas, Σ D_i ∇Y_i ≠ 0 em
geral, e a soma das frações mássicas deriva de 1 a cada passo de tempo.

O solver então renormaliza — e é aqui que o erro se torna invisível. A
renormalização distribui o desvio **proporcionalmente a Y_i**. A espécie
majoritária absorve quase todo o erro, e as minoritárias quase nada.

### Como se manifestou

No sistema estudado, o triglicerídeo responde por 82% da massa e o metanol tem
difusividade cerca de 97 vezes maior (moléculas de tamanhos muito distintos).
A consequência:

```
Erro no balanço de massa do TG:     374 %
Soma das frações mássicas:          1,0000000 (o solver garante)
Resíduos:                           convergidos
Fluxos de parede reportados:        corretos
```

Todos os indicadores usuais indicavam saúde. O erro só apareceu no balanço
integral por espécie.

### Correção

Igualar todas as difusividades a um valor efetivo único:

```
D_i = 7,0 × 10⁻¹¹ m² s⁻¹   para TG, MeOH, FAME e GL

Erro no balanço:  374 %  →  0,013 %
```

A perda física é real e deve ser declarada: a seletividade difusional entre
espécies é suprimida. Em sistemas onde a razão entre difusividades é grande *e*
o transporte difusivo controla a seletividade, a formulação correta é
Maxwell-Stefan (`Multi-component Diffusion = On` no Star-CCM+), que satisfaz a
restrição de soma por construção. Ela exige difusividades binárias para todos os
pares, raramente disponíveis para sistemas de triglicerídeos.

No presente caso a simplificação é defensável: o reagente limitante é o TG, o
metanol está em excesso de 6:1, e o que se deseja medir é a competição entre
cinética de parede e transporte externo do TG — não a seletividade entre espécies.

### Teste de detecção

Comparar, por espécie, a taxa de variação do inventário no domínio com a integral
do fluxo na fronteira:

```
d/dt ∫ρY_i dV   vs.   ∮ J_i dA  +  ṁ(Y_i,in − Y_i,out)
```

Equivalentemente, e de forma mais sensível, verificar a razão estequiométrica
entre produtos e reagentes. No sistema TG + 3 MeOH → 3 FAME + GL:

```
(dM_FAME/dt) / (dM_TG/dt)  =  876/872  =  1,004587
```

Esse número é uma restrição exata, independente da malha, do passo de tempo e do
estado de convergência. Qualquer desvio além de ~0,1% indica violação da
conservação entre espécies. Após a correção, mediu-se 1,00455–1,00462 em todas
as janelas de todas as corridas.

---

## Nota II — A média ponderada por vazão na saída é imprópria para conversão em escoamento laminar com reação de parede

### O problema

O instinto natural é obter a conversão pela composição de saída:

```
X = (Y_in − Y_out) / Y_in
```

com Y_out dado pelo *Mass Flow Average* na fronteira de saída — que é, por
definição, a grandeza correta:

```
Ȳ_out = ∫ Y ρ u·n dA / ∫ ρ u·n dA
```

Em escoamento laminar com reação de parede, **essa média é numericamente frágil,
e por um motivo estrutural**: o fluido mais empobrecido é o mais lento.

No perfil de Poiseuille, u → 0 na parede, exatamente onde a depleção é máxima.
A ponderação por vazão, que é fisicamente correta, atribui peso quase nulo à
região que carrega toda a informação de conversão. No perfil medido:

```
distância da parede    Y_TG      u (mm/s)     peso relativo
      11 µm           0,4506     0,0594          4 %
     660 µm           0,8194     1,4400        100 %
```

A 11 µm da parede o TG caiu 45%, mas a velocidade é 4% da do núcleo. O sinal
existe, mas é pequeno — e fica à mercê de qualquer contaminação.

### Como se manifestou

A fronteira de saída (Pressure Outlet) carrega um array de composição especificada,
usado quando há entrada de fluido. Essa composição contaminou os valores de face
empregados na média:

```
Array de composição do Outlet         0,8194
Mass Flow Average reportado           0,81893      ← 0,06 % abaixo do array
Média calculada do perfil medido      0,81066
Exigido pelo balanço global           0,80867
```

O report tinha tipo correto (*Mass Flow Average*), campo correto
(*Mass Fraction of TG*) e parte correta (*Canal: Outlet*). Foi recriado do zero
e reproduziu o mesmo valor. Ainda assim subestimava o déficit convectivo por um
**fator 19**:

```
déficit pelo report    2,24 × 10⁻¹¹ kg s⁻¹
déficit pelo perfil    4,17 × 10⁻¹⁰ kg s⁻¹
```

Consequência prática: o balanço global apresentava 96% do fluxo de parede sem
explicação, e o modelo — que estava correto — foi sucessivamente suspeitado de
erro de malha, de convergência interna e de discretização temporal ao longo de
quatro corridas completas.

### Diagnóstico que resolveu

Duas grandezas medidas implicavam espessuras incompatíveis de camada-limite:

```
Y médio do domínio  = 0,79744   →  δ médio no canal ≈ 134 µm
Y médio da saída    = 0,81893   →  δ em x = L       ≈  39 µm
```

A camada-limite **cresce** monotonicamente com x. Não pode ser três vezes mais
fina na saída do que a média do canal. Essa contradição, entre duas grandezas
ambas medidas, foi o que indicou o alvo — depois de três hipóteses erradas
construídas por dedução a partir de grandezas integradas.

A confirmação veio de uma sonda de linha transversal (*Line Probe*), com a média
ponderada por vazão calculada por integração numérica do perfil. O perfil
concordou com o balanço, não com o report.

O painel (c) da figura `results/fig4_camada_limite_x49mm.pdf` mostra o mecanismo
diretamente: a contribuição local à média ponderada, u·(Y_in − Y), tem máximo a
**66 µm da parede**, e não na parede. A região onde a conversão de fato ocorre é
justamente a que menos pesa na média.

### Prática recomendada

```
1. Calcular conversão pela integral do fluxo de parede:
      X = |∮J dA| / (ṁ · Y_in)
   É a grandeza diretamente ligada ao que se quer medir e não depende de
   médias ponderadas em fronteiras.

2. Para o termo convectivo do balanço, integrar um perfil medido por sonda
   de linha, não usar o Mass Flow Average de fronteira.

3. Manter o array de composição do Outlet idêntico ao do Inlet. Isso não
   elimina o problema, mas evita que uma composição defasada o agrave.
   (Array defasado já havia custado uma corrida anterior, por injeção de
   composição antiga em refluxo local.)

4. Diante de um balanço que não fecha, suspeitar da instrumentação antes de
   suspeitar do modelo — e medir o campo, não deduzir a partir de integrais.
```

### Lição de método

As três hipóteses que falharam (resolução de malha, convergência das iterações
internas, discretização temporal) foram todas construídas por dedução a partir
de grandezas integradas. A hipótese correta veio de **confrontar duas medidas
independentes que não podiam ser ambas verdadeiras**, e a confirmação veio de
medir o campo diretamente.

Grandezas integradas escondem o mecanismo por construção: elas somam sobre a
região onde o fenômeno acontece. Quando um balanço global falha, o caminho curto
é medir o perfil, não refinar a dedução.

---

*Novembro/2026 | Gabriel Rozo — FEQ/UNICAMP*
