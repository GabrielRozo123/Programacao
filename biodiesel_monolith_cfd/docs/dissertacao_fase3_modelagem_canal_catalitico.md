# Modelagem CFD de um canal monolítico de parede catalítica para transesterificação heterogênea

**Fase 3 — rascunho para a dissertação**
Gabriel Rozo · FEQ/UNICAMP
Orientação: Prof. Dr. Raphael Soeiro Suppino · Prof. Dr. Dirceu Noriler

---

## Resumo

Construiu-se um modelo CFD tridimensional pseudo-bidimensional de um canal
individual de reator monolítico com parede recoberta por washcoat de CaO, operando
na metanólise de óleo de soja a 65 °C. A reação heterogênea foi implementada como
condição de contorno de fluxo de espécies na parede, acoplada ao transporte
convectivo-difusivo no seio do fluido, sem resolver explicitamente o interior do
washcoat — cuja resistência interna entra por um fator de efetividade calculado
pelo módulo de Thiele.

O resultado central é que, com a cinética do catalisador real, o número de
Damköhler de parede vale **Da = 0,74**, colocando o sistema em **regime misto**,
em que resistência cinética e resistência ao transporte externo são da mesma
ordem. Esse valor foi obtido de forma independente em duas malhas e duas
composições de alimentação, concordando dentro de 2%. A conversão por passe é de
**1,42%**, e o comprimento de entrada mássica do canal é **69 vezes maior que seu
comprimento físico**, o que limita estruturalmente a conversão de um único passe.

---

## 1. Formulação

### 1.1 Domínio e hipóteses

O canal é representado por um paralelepípedo de 50 × 1,1 × 0,05 mm, com condição
de simetria nas duas faces normais a *z*. A malha contém uma única célula nessa
direção, de modo que o domínio se comporta como um canal plano bidimensional,
mantendo-se porém a formulação tridimensional do solver. A parede superior
(`Top_Wall`) é catalítica; a inferior é parede lisa inerte.

As hipóteses adotadas são:

1. Escoamento laminar, incompressível e isotérmico a 65 °C.
2. Propriedades físicas constantes (§1.5), de modo que o campo de velocidade fica
   desacoplado do campo de concentrações.
3. Reação restrita à superfície da parede recoberta; o washcoat não é discretizado.
4. Mistura diluída em termos de transporte: difusão descrita pela lei de Fick com
   difusividades efetivas iguais para todas as espécies (§1.5 e Nota I).
5. Cinética irreversível de primeira ordem em triglicerídeo, com metanol em excesso.

### 1.2 Equações governantes

Continuidade e quantidade de movimento, com ρ e μ constantes:

```
∇·u = 0
ρ (∂u/∂t + u·∇u) = −∇p + μ ∇²u
```

Transporte das N = 4 espécies (TG, MeOH, FAME, GL), com Yᵢ a fração mássica:

```
∂(ρYᵢ)/∂t + ∇·(ρ u Yᵢ) = ∇·(ρ Dᵢ ∇Yᵢ)          i = 1 … N
```

sem termo fonte volumétrico: toda a reação entra pela condição de contorno.
O solver impõe ΣYᵢ = 1 por normalização, o que tem consequências discutidas na
Nota I.

### 1.3 Reação e condição de contorno catalítica

A transesterificação global é

```
TG + 3 MeOH  →  3 FAME + GL
```

Em excesso de metanol (razão molar 6:1), a taxa é tratada como de primeira ordem
aparente em TG, com constante por massa de catalisador obtida de Melo (2023) para
CaO suportado em biochar a 65 °C:

```
k_cat = 5,302 × 10⁻⁵  m³ · kg_cat⁻¹ · s⁻¹
```

A quantidade de catalisador por área de parede é

```
w = ρ_wc · δ_wc = 1700 × 10 × 10⁻⁶ = 1,70 × 10⁻²  kg_cat · m⁻²
```

e a taxa superficial, já corrigida pela resistência interna ao washcoat, é

```
r_w = η · k_cat · w · C_TG|parede                [kmol · m⁻² · s⁻¹]
```

onde C_TG|parede = ρ Y_TG|parede / M_TG.

Os fluxos mássicos de cada espécie na parede seguem a estequiometria:

```
J_TG   = −M_TG   · r_w   = −872,00 · r_w
J_MeOH = −3 M_MeOH · r_w = − 96,12 · r_w
J_FAME = +3 M_FAME · r_w = +876,00 · r_w
J_GL   = +M_GL   · r_w   = + 92,09 · r_w
```

A soma dos coeficientes vale −0,03 kg por kmol de TG consumido, ou 3 × 10⁻⁵ da
massa envolvida, o que decorre apenas do arredondamento das massas molares e é
desprezível frente à tolerância do solver. **Essa soma deve ser verificada antes
de qualquer simulação**: coeficientes que não se cancelam injetam ou removem massa
total na parede, e o solver a redistribui pela normalização de ΣYᵢ (Nota I).

### 1.4 Resistência interna ao washcoat

A difusão dentro da camada porosa é tratada pelo módulo de Thiele para placa plana:

```
φ = δ_wc √(k_v / D_h)
η = tanh(φ) / φ
```

Com a difusividade efetiva no poro D_h extraída da faixa reportada por Fonseca
(2026) para CaO e CaO/Al₂O₃ (3 × 10⁻¹³ a 4,4 × 10⁻¹² m² s⁻¹) e δ_wc = 10 µm,
obtém-se φ = 1,44 e

```
η = 0,62
```

Ou seja, 38% da atividade nominal do washcoat é perdida por limitação difusional
interna nessa espessura. Como η decresce monotonicamente com δ_wc enquanto a
massa de catalisador cresce linearmente, existe uma espessura além da qual
acrescentar washcoat deixa de compensar. A análise indica **δ_wc ≲ 10 µm** como
faixa de trabalho — recomendação repassada à equipe de impregnação.

### 1.5 Propriedades físicas

| Propriedade | Valor | Observação |
|---|---|---|
| ρ | 868 kg m⁻³ | constante |
| μ | 1,05 × 10⁻² Pa s | constante |
| Dᵢ (todas) | 7,0 × 10⁻¹¹ m² s⁻¹ | **iguais entre si — ver Nota I** |
| T | 65 °C | isotérmico |
| ū | 1,0 × 10⁻³ m s⁻¹ | velocidade média |

Composição de entrada, razão molar MeOH:TG de 6:1:

```
Y_TG = 872/(872 + 6 × 32,04) = 0,8194        Y_MeOH = 0,1806
```

A igualdade imposta entre as difusividades não é uma simplificação cosmética: é
condição necessária para que a formulação de Fick conserve massa neste problema,
pelas razões expostas na Nota I.

---

## 2. Implementação numérica

### 2.1 Malha

Malha trimmer com base de 50 µm (igual à espessura em *z*, forçando uma célula
nessa direção), com camadas prismáticas nas duas paredes:

```
Número de camadas           15
Espessura total             200 µm
Razão de crescimento        1,2
Primeira camada             ≈ 2,8 µm
Total                       88.000 células
```

O controle `Gap Fill Percentage` deve ser elevado ao máximo permitido (50%): com
o padrão de 25%, as camadas prismáticas das duas paredes somam 36% do vão de
1,1 mm e são silenciosamente reduzidas pelo mesher.

O refino junto à parede é indispensável. Com Sc = 1,7 × 10⁵, o gradiente de fração
mássica na parede é

```
∂Y/∂n = J/(ρD) ≈ 3,9 × 10³ m⁻¹
```

o que corresponde a uma variação de ΔY ≈ 0,20 ao longo de uma célula de 50 µm —
40% do valor de parede. Sem camadas prismáticas o valor de face lido pela
condição de contorno é uma extrapolação sem significado, e o balanço global de
massa apresenta desvios de dezenas de pontos percentuais já nos primeiros
segundos de simulação.

### 2.2 Verificação do campo de velocidade

A queda de pressão calculada é 5,463 Pa, contra 5,207 Pa da solução analítica de
Poiseuille plano (ΔP = 12 μ ū L / H²), diferença de 4,9%.

Registre-se que **ΔP não serve como indicador de qualidade de malha neste
problema**: a solução desenvolvida é um perfil parabólico, que um esquema de
volumes finitos de segunda ordem integra exatamente em qualquer malha. Obteve-se
ΔP idêntico a sete dígitos em malhas com e sem camadas prismáticas. O valor
confirma que o campo de velocidade está correto e convergido, mas é insensível ao
refino.

### 2.3 Marcha temporal

Solver implícito transiente, 30 iterações internas por passo. O erro de
discretização temporal escala linearmente com Δt (Euler implícito de primeira
ordem); mediu-se contribuição de ≈ 4,5 pontos percentuais no balanço com
Δt = 0,05 s, reduzida a ≈ 0,45 ponto com Δt = 0,005 s. Adotou-se Δt = 0,005 s na
partida, 0,02 s na marcha longa e refinamento final para 0,005 s antes da
extração dos resultados, quando dM/dt → 0 e o erro temporal desaparece por
construção.

---

## 3. Verificação do modelo

A verificação apoia-se em três testes independentes, todos necessários.

### 3.1 Consistência estequiométrica

A razão entre as taxas de acúmulo de FAME e de consumo de TG no domínio deve
igualar a razão mássica estequiométrica 876/872 = 1,004587. Mediu-se:

```
1,00455 a 1,00462   em todas as janelas temporais de todas as corridas
```

concordância de 0,009%, estável do primeiro ao último segundo. Esse teste detecta
violações da conservação de massa entre espécies e é o único que flagra o problema
descrito na Nota I.

### 3.2 Independência de malha

O resultado central foi obtido em duas configurações independentes:

| | Malha | Alimentação | C_w/C_b | Da |
|---|---|---|---|---|
| A | sem prismas, 50 µm uniforme | 4:1 molar | 0,578 | 0,730 |
| B | 15 camadas prismáticas, 1ª = 2,8 µm | 6:1 molar | 0,574 | 0,743 |

Malhas e composições distintas, concordância dentro de 2%.

### 3.3 Balanço global de massa

O teste definitivo é o balanço integral por espécie:

```
d/dt ∫ρY dV  =  ṁ (Y_in − Y_out)  +  ∮ J dA
```

com todos os termos medidos independentemente. Esse teste é o mais trabalhoso e
o mais importante: resíduos, somas de frações mássicas e fluxos de parede podem
estar todos aparentemente corretos enquanto o balanço falha por ordens de
grandeza (Notas I e II).

Fechamento obtido na configuração final:

```
∮J dA        = −5,545 × 10⁻¹⁰ kg s⁻¹    (parede)
d/dt ∫ρY dV  = −4,23 × 10⁻¹¹ kg s⁻¹
ṁ(Y_in−Y_out)= −4,17 × 10⁻¹⁰ kg s⁻¹     (de perfil medido em x = 49 mm)
```

Resíduo de ~20%, atribuível a dois efeitos identificados: a sonda está 1 mm a
montante da saída, não captando a reação no último milímetro de parede, e
dM/dt ainda vale 7,6% do fluxo em t = 150 s, de modo que o regime permanente não
foi plenamente atingido.

**O termo convectivo não pode ser obtido pelo Mass Flow Average de fração mássica
na saída.** Esse ponto é desenvolvido na Nota II; no presente trabalho ele
produziu erro de fator 19 e levou à rejeição indevida de um modelo correto ao
longo de quatro corridas.

---

## 4. Resultados

### 4.1 Regime de operação

O número de Damköhler de parede compara a taxa de reação à taxa máxima de
transporte externo:

```
Da = r_w(C_b) / (k_m C_b)
```

Para reação de primeira ordem na parede, a razão de concentrações em regime
permanente fornece Da diretamente:

```
C_w/C_b = 1/(1 + Da)      ⟹      Da = C_b/C_w − 1
```

Medida:

```
Y_TG|parede (média sobre a parede)  = 0,4574
Y_TG|domínio (média volumétrica)    = 0,7974
C_w/C_b                             = 0,574
──────────────────────────────────────────────
Da                                  = 0,74
```

**Regime misto.** Nem controle cinético (Da ≪ 1) nem controle por transporte
(Da ≫ 1): as duas resistências são da mesma ordem, e a concentração de
triglicerídeo na superfície catalítica é 43% menor que no seio do fluido.

Esse resultado inverte a conclusão obtida na Fase 2. Com o ZnAl₂O₄ de Allain et
al. (2015), extrapolado para as condições do canal, obtinha-se Da = 0,003 —
controle cinético absoluto, regime em que a geometria do monólito não cumpre
função alguma, pois não há gradiente a vencer. Com a cinética do CaO efetivamente
empregado no laboratório, o Da sobe mais de duas ordens de grandeza e o sistema
entra na faixa em que a razão área/volume do monólito passa a ser determinante.

### 4.2 Camada-limite de concentração

Perfil transversal medido em x = 49 mm, t = 150 s:

| Distância da parede | Y_TG | u (mm s⁻¹) |
|---:|---:|---:|
| 0 µm | 0,4147 | 0,0000 |
| 11 µm | 0,4506 | 0,0594 |
| 22 µm | 0,4875 | 0,1176 |
| 44 µm | 0,5398 | 0,2304 |
| 77 µm | 0,6490 | 0,3906 |
| 110 µm | 0,7320 | 0,5400 |
| 165 µm | 0,7953 | 0,7650 |
| 220 µm | 0,8113 | 0,9600 |
| 330 µm | 0,8191 | 1,2600 |
| 660 µm | 0,8194 | 1,4400 |

O perfil completo está em `results/perfil_camada_limite_x49mm.csv` e a figura
em `results/fig4_camada_limite_x49mm.pdf` (script: `scripts/plot_fase3_camada_limite.py`).

Espessura da camada empobrecida: **324 µm** (medida sobre os centroides de
célula, limiar Y_in − Y > 10⁻⁴), contra 179 µm previstos pela solução
de Lévêque para regime permanente,

```
δ_c(x) = (9 D x / γ)^{1/3} ,     γ = 6ū/H = 5,455 s⁻¹
```

A camada medida é mais espessa porque, em t = 150 s, o regime permanente ainda não
se estabeleceu junto à parede: o tempo de trânsito do fluido a 20 µm da parede é
de 458 s, e a 5 µm, de 1833 s. O tempo característico do problema não é o tempo de
residência médio (L/ū = 50 s) mas o tempo de trânsito na região lenta, uma a duas
ordens de grandeza maior.

### 4.3 Conversão por passe e limitação geométrica

```
X_TG = |∮J dA| / (ṁ · Y_in) = 5,545 × 10⁻¹⁰ / (4,774 × 10⁻⁸ × 0,8194) = 1,42 %
```

contra 1,5% estimado analiticamente antes da simulação, pela combinação de Lévêque
com a cinética de parede.

O valor baixo não é artefato: é consequência direta da relação entre o comprimento
do canal e o comprimento de entrada mássica. Com

```
D_h = 2H = 2,2 mm
Re  = ρ ū D_h / μ = 0,182
Sc  = μ / (ρ D)   = 1,73 × 10⁵
Pe  = Re·Sc       = 3,1 × 10⁴
```

o comprimento de entrada mássica vale

```
L_e ≈ 0,05 · D_h · Re · Sc = 3,46 m
```

contra os 50 mm do canal — **razão de 69**. A camada-limite de concentração nunca
chega a preencher a seção; em x = L ela ocupa 16% da altura pela estimativa de
Lévêque, e o núcleo deixa o canal essencialmente na composição de alimentação.

Essa é a conclusão de projeto mais consequente do trabalho. O número de Schmidt
elevado, próprio de óleos vegetais (ν/D ~ 10⁵), implica que **o canal curto opera
permanentemente na região de entrada**. Elevar a conversão por passe exige atuar
sobre Pe ou sobre L: canais mais longos, velocidade superficial menor, ou
reciclo. Aumentar a carga de catalisador, isoladamente, tem retorno decrescente —
já em Da = 0,74 o transporte externo responde por 43% da queda de concentração
disponível.

---

## 5. Pendências

```
□ Prolongar a marcha até ~400 s (dM/dt ainda vale 7,6 % do fluxo em 150 s)
□ Refazer a sonda de perfil em x = 49,9 mm para fechar os 20 % do balanço
□ Substituir 393,15 por ${Temperature} nas FFs de k quando houver Ea
   (executar teste de invariância antes)
□ Definir rota com a orientação: metílica (Melo, 65 °C, 6:1) ou
   etílica (Fonseca, 70 °C, 1:9)
□ Medir ρ_wc e δ_wc reais — o resultado é LINEAR no produto dos dois
□ Obter ρ e μ medidos da carga real do laboratório
□ Avaliar formulação de Maxwell-Stefan quando houver difusividades binárias
```

---

## Referências

- ALLAIN, F. et al. Development of a kinetic model for the transesterification
  of vegetable oil over ZnAl₂O₄. *Chemical Engineering Journal*, v. 283,
  p. 833–845, 2015.
- FONSECA, R. V. S. *Transesterificação etílica com catalisadores heterogêneos
  de CaO e CaO/Al₂O₃*. Dissertação — FEQ/UNICAMP, 2026.
- MELO, V. M. *Metanólise de óleo de soja com CaO suportado em biochar*.
  Dissertação — FEQ/UNICAMP, 2023.

---

*Novembro/2026 | Gabriel Rozo — FEQ/UNICAMP*
