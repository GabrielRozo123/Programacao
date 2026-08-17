# Aeração de xarope por lanças submersas — análise fluidodinâmica computacional

**Cliente:** Ito · **Projeto:** aerador de xarope · **Fase 3**
**Elaboração:** CAEXPERTS · **Ferramenta:** Simcenter STAR-CCM+

---

## 1. Sumário executivo

Avaliou-se, por CFD multifásico euleriano, o desempenho de um aerador de xarope com
lanças submersas de descarga aberta, com liberdade de definição quanto ao número, à
altura e ao diâmetro das lanças. O arranjo simulado emprega **16 lanças de Ø 62,7 mm**
distribuídas em dois anéis concêntricos com cotas de descarga escalonadas.

**Três conclusões:**

1. **Na região das descargas o ar forma cavidades de alta fração de vazio**, e não
   uma nuvem de bolhas dispersa: no volume alcançado pelo ar a fração de vazio média
   é de 47,7 %. Trata-se de caracterização do **transitório inicial** junto aos
   bicos; o presente estudo não caracteriza a distribuição em regime permanente
   (ver §10.4).

2. **A meta de 0,2 mm de diâmetro de bolha é inalcançável com descarga aberta, e não
   depende do arranjo das lanças.** Com Ø 62,7 mm, o número de Bond vale 898: o
   destacamento é governado pela instabilidade de Rayleigh-Taylor, que fixa o tamanho
   em **13 a 23 mm** independentemente do diâmetro da descarga. Alterar quantidade,
   altura ou disposição das lanças não atua sobre esse mecanismo.

3. **O caminho técnico existe e é específico:** furos de diâmetro inferior ao
   comprimento capilar do xarope (2,09 mm), **operados em regime de jato**
   (We_gás > 2). Furo pequeno isoladamente não basta — a lei de Tate impõe um piso
   de 1,7 a 3 mm no regime de borbulhamento.

---

## 2. Objetivo e escopo

O cliente indicou como meta de projeto diâmetro de bolha inferior a 0,2 mm, e
concedeu liberdade para modificação do número de lanças, da cota de descarga e do
diâmetro. Foram objetivos da análise:

- caracterizar a distribuição de ar no volume do aerador;
- avaliar o diâmetro de bolha resultante e sua evolução ao longo do percurso;
- verificar se algum arranjo de lanças conduz à meta de 0,2 mm;
- indicar, caso negativo, o caminho técnico que conduziria.

Não fez parte do escopo o projeto detalhado de um novo sistema de transporte de ar.

---

## 3. Geometria e arranjo

Domínio: aerador cilíndrico Ø 2 032 mm com fundo cônico, **19,993 m³** de volume de
fluido, 7,11 m de altura útil.

| | anel interno | anel externo |
|---|---|---|
| número de lanças | 5 | 11 |
| raio a partir do eixo | 375 mm | 770 mm |
| cota de descarga | −5 450 mm | −4 660 mm |
| submergência | 6 670 mm | 5 880 mm |
| folga mínima à parede do cone | 72,6 mm | 70,0 mm |

**Descarga escalonada.** O fundo cônico reduz o raio disponível de 1 016 mm em
z = −4 368,6 para 259,5 mm em z = −5 892. O anel externo, portanto, não pode descer
tanto quanto o interno. Cada anel foi levado à cota mais profunda que o perfil do cone
permite, com 50 mm de folga construtiva mais 40 mm de margem, verificados ponto a
ponto ao longo de todo o comprimento de cada lança.

Diâmetro de descarga Ø 62,7 mm em todas as 16 lanças. A obstrução total introduzida no
domínio é de 49 402 mm², ou **1,5 % da seção transversal do aerador**.

---

## 4. Modelo numérico

| item | especificação |
|---|---|
| solver | Eulerian Multiphase (EMP) segregado, transiente implícito |
| distribuição de tamanho | S-Gamma com quebra e coalescência ativas |
| turbulência | k-ε (ver §10 quanto à aplicabilidade) |
| gravidade | ativa · pressão de referência 101 325 Pa |
| malha | trimmed, base 50 mm, refino a 12,5 mm nas 16 descargas |
| volume de refino | 0,251 m³ (1,26 % do domínio), 16 cilindros de R = 100 mm |

**Propriedades:** xarope ρ = 1 350 kg/m³, µ = 6,5 Pa·s, σ = 0,058 N/m;
ar ρ ≈ 2,1 kg/m³ na cota de descarga.

**Condições de contorno:** descargas como *stagnation inlet* com pressão total de
1 kgf/cm² e fração volumétrica de ar unitária; superfície livre como saída de pressão
com extrapolação de escalares no refluxo; demais superfícies como parede sem
escorregamento.

**Verificação de malha.** A integral de volume da malha resultou em 19,9931 m³ contra
19,991 m³ da geometria — desvio de **0,01 %**. O cone e o casco foram capturados sem
perda geométrica.

---

## 5. Resultados — distribuição do ar

Instante final da simulação, correspondente a **0,18 s de tempo físico**. Fração de
vazio média no domínio: **5,099 %**, equivalente a **1,019 m³** de ar.

> ⚠️ Os valores desta seção caracterizam o **transitório inicial** de formação das
> plumas junto às descargas. Não descrevem a distribuição em regime permanente, pela
> razão detalhada em §10.4: o tempo simulado é curto frente ao tempo de ascensão das
> bolhas, e o diâmetro adotado na condição de contorno (1,0 mm) é inferior ao previsto
> analiticamente para a descarga aberta (13 a 23 mm, §7.1). Ambos os fatores atuam no
> sentido de subestimar o transporte vertical.

| critério | volume | fração do tanque |
|---|---|---|
| xarope alcançado pelo ar (α > 0,01 %) | 3,082 m³ | 15,4 % |
| xarope efetivamente aerado (α > 1 %) | 2,137 m³ | 10,7 % |
| **xarope não atingido** | 16,911 m³ | **84,6 %** |
| fração de vazio média no volume aerado | — | **47,7 %** |

A faixa de transição entre os dois primeiros critérios ocupa apenas 0,945 m³: **69 %
do volume alcançado já se encontra acima de 1 % de fração de vazio.** A frente de ar
é nítida, sem zona de diluição progressiva — o ar desloca o xarope em vez de se
dispersar nele, **na região e no intervalo observados**.

### 5.1 Evolução temporal na região das descargas

| | instante intermediário | instante final |
|---|---|---|
| volume alcançado | 10,6 % | 15,4 % |
| volume aerado | 7,1 % | 10,7 % |
| **fração de vazio dentro do volume aerado** | **32,6 %** | **47,7 %** |

O volume aerado cresceu 50 % no intervalo, e a fração de vazio no seu interior cresceu
46 % simultaneamente.

Em um processo de dispersão, a fração de vazio interna diminuiria conforme o volume
aerado se expandisse, pois o mesmo inventário de ar passaria a ocupar mais xarope.
Observa-se o oposto: as cavidades crescem e adensam ao mesmo tempo. **Na vizinhança
das descargas, portanto, o ar desloca o xarope em vez de se misturar a ele.**

Ressalva: o intervalo compreende 0,09 s, muito inferior ao tempo característico de
ascensão de bolha (§10.4). A tendência caracteriza a formação das cavidades junto aos
bicos, e não permite extrapolação para o comportamento do tanque em regime.

A visualização de fração volumétrica em escala logarítmica confirma a leitura:
observam-se cavidades coerentes, com α tendendo à unidade, ancoradas na ponta de cada
lança, e não uma nuvem de bolhas distribuída pelo volume.

---

## 6. Resultados — diâmetro de bolha

Diâmetro médio de Sauter medido no volume que contém ar:

| | valor |
|---|---|
| mínimo | 0,816 mm |
| máximo | **1,000201 mm** |
| valor imposto na condição de contorno | 1,000 mm |

O máximo excede o valor de entrada em **2 × 10⁻⁴ mm**. Em termos práticos, **a
coalescência é nula** neste sistema ao longo de todo o percurso simulado.

O desvio para baixo (mínimo de 0,816 mm) corresponde a quebra ocorrida na região de
descarga, e deve ser lido com a ressalva de §10.

---

## 7. Por que a meta de 0,2 mm não é atingível

O diâmetro da bolha neste sistema é fixado **na formação**, junto à descarga. Uma vez
formada, a bolha não se altera de modo apreciável — o que é sustentado por quatro
verificações independentes:

| mecanismo | grandeza | valor | consequência |
|---|---|---|---|
| quebra turbulenta inercial | escala de Kolmogorov | 42,7 mm | bolha 43× menor; kernel nulo |
| quebra por cisalhamento viscoso | Ca crítico (Hinch & Acrivos, λ = 2,8×10⁻⁶) | ≈ 270 | inatingível |
| quebra por oscilação de forma | número de Morton | 6,6 × 10⁴ | regime *wobbling* inacessível |
| coalescência | variação medida de SMD | +2 × 10⁻⁴ mm | desprezível |

### 7.1 A formação em descarga aberta

O comprimento capilar do xarope vale `√(σ/ρg)` = **2,09 mm**. A descarga de Ø 62,7 mm
opera trinta vezes acima desse valor, o que corresponde a **número de Bond igual a
898**.

Nessa condição o destacamento deixa de ser governado pelo diâmetro do orifício. A
interface é larga demais para ser sustentada pela borda e se comporta como uma
superfície plana, fragmentando-se pela **instabilidade de Rayleigh-Taylor** no seu
próprio comprimento de onda natural (Apêndice A):

| | |
|---|---|
| comprimento de onda crítico `2π√(σ/ρg)` | **13,1 mm** |
| comprimento de onda de crescimento mais rápido `2π√(3σ/ρg)` | **22,8 mm** |

**Diâmetro de bolha esperado na descarga atual: 13 a 23 mm** — aproximadamente setenta
vezes a meta de 0,2 mm.

### 7.2 Consequência para o arranjo das lanças

Como o tamanho é fixado por um comprimento de onda que depende apenas das propriedades
do fluido, **nenhuma variável de arranjo o modifica**: nem o número de lanças, nem a
cota de descarga, nem a disposição em anéis, nem a submergência. Essas variáveis atuam
sobre a distribuição espacial do ar, não sobre o diâmetro com que ele se forma.

Trata-se de uma limitação de mecanismo, não de otimização.

---

## 8. Recomendação técnica

O único ponto de atuação sobre o diâmetro é a **geometria da descarga**, sujeita a
duas condições que precisam ser satisfeitas simultaneamente.

### 8.1 Condição 1 — furo abaixo do comprimento capilar

Com furo pequeno, o destacamento retorna ao regime governado pela lei de Tate,
`d_b = (6σd_o/ρg)^(1/3)`:

| furo | Bond | regime de formação | diâmetro de bolha |
|---|---|---|---|
| 0,2 mm | 0,01 | Tate | 1,74 mm |
| 0,5 mm | 0,06 | Tate | 2,36 mm |
| 1,0 mm | 0,23 | Tate | 2,97 mm |
| 2,0 mm | 0,91 | Tate (limite) | 3,75 mm |
| 5,0 mm | 5,7 | Rayleigh-Taylor | — |
| **62,7 mm (atual)** | **898** | **Rayleigh-Taylor** | **13 a 23 mm** |

A dependência é **cúbica**: reduzir o furo de 1,0 para 0,2 mm — cinco vezes — diminui
a bolha apenas de 2,97 para 1,74 mm. Existe portanto um **piso da ordem de 1,7 a
3 mm** que o diâmetro do furo, isoladamente, não ultrapassa.

### 8.2 Condição 2 — velocidade de jato

Para descer abaixo desse piso é necessário abandonar o regime de borbulhamento e
entrar em **regime de jato**, o que ocorre acima de `We_gás = ρ_g v² d_o / σ ≈ 2`.

Na descarga atual, a velocidade é de 0,225 m/s e o número de Weber do gás vale
**0,115** — duas ordens de grandeza abaixo da transição. O sistema opera integralmente
em borbulhamento.

### 8.3 Condição 3 — uniformidade de distribuição entre furos

Esta condição restringe fortemente o número de furos, e não pode ser omitida.

A perda de carga através do furo precisa **dominar** a variação hidrostática ao longo
do trecho perfurado; caso contrário o ar sai preferencialmente pelos furos superiores,
onde a contrapressão é menor. O critério usual de projeto de spargers é

    ΔP_furo ≥ 4 × ΔP_hidrostático ao longo do trecho perfurado

Como a perda de carga no furo cresce com o quadrado da velocidade, e a velocidade é
inversamente proporcional ao número de furos, **furos demais inviabilizam a
distribuição**. Para 1,0 mm de furo em dois anéis distanciados de 15 mm:

| nº de furos por lança | velocidade | ΔP no furo | ΔP hidrostático | razão |
|---|---|---|---|---|
| 119 | 7,4 m/s | 158 Pa | 596 Pa | **0,3** ✗ |
| 80 | 11,1 m/s | 356 Pa | 397 Pa | 0,9 ✗ |
| **48** | **18,4 m/s** | **990 Pa** | **199 Pa** | **5,0** ✓ |

### 8.4 Ponto de projeto recomendado

| | |
|---|---|
| diâmetro do furo | **1,0 mm** |
| furos por lança | **48** — 2 anéis de 24 |
| passo circunferencial | 9,6 mm (ligamento 8,6 mm) |
| passo axial entre anéis | 15 mm |
| velocidade no furo | **18,4 m/s** |
| número de Weber do gás | **12,3** (exige > 2) ✓ |
| ΔP no furo | 990 Pa |
| razão de uniformidade | **5,0** (exige ≥ 4) ✓ |
| total no aerador | **768 furos** |
| pressão de suprimento | ≈ 0,91 kgf/cm² mais perdas de linha |

Alternativa com furo de 0,5 mm: 96 furos por lança em 2 anéis de 48, a 36,8 m/s, com
We = 24,6 e razão de uniformidade de 19,9. Produz bolha menor, ao custo de furo mais
difícil de executar e de maior sensibilidade a entupimento.

**Requisito construtivo indispensável: a ponta da lança deve ser fechada com tampa
cega.** A saída aberta de Ø 62,7 mm tem **82 vezes** a área somada dos 48 furos; sem o
fechamento, praticamente todo o ar escoa por ela e a perfuração não produz efeito
algum.

### 8.5 Número de lanças

Com descarga perfurada, o número total de furos do aerador é **fixado pela vazão de ar
e pela velocidade de jato**, e independe de quantas lanças o distribuem:

    N × n = Q_ar / (v · A_furo) = 0,01111 / (18,4 × 7,854×10⁻⁷) = 769 furos

Dobrar o número de lanças reduz à metade os furos de cada uma. O diâmetro de bolha, a
velocidade no furo e a vazão total permanecem inalterados. **O número de lanças
redistribui, não modifica.**

| N lanças | furos por lança | por anel | passo circunferencial | área servida | espaçamento |
|---|---|---|---|---|---|
| 8 | 96 | 48 | 4,8 mm ✗ | 0,405 m² | 637 mm |
| 11 | 70 | 35 | 6,6 mm | 0,295 m² | 543 mm |
| **16 (adotado)** | **48** | **24** | **9,5 mm** | **0,203 m²** | **450 mm** |
| 20 | 38 | 19 | 11,9 mm | 0,162 m² | 403 mm |
| 24 | 32 | 16 | 14,3 mm | 0,135 m² | 368 mm |

**Limite inferior: N ≥ 11.** Com dois anéis num tubo de Ø 73 mm e passo circunferencial
mínimo de 6 mm (ligamento de 5 mm), cabem no máximo 76 furos por lança. Abaixo de onze
lanças a perfuração exigida não é executável.

Acima desse limite não existe penalidade técnica em aumentar N — apenas custo de
tubulação e de válvula de retenção adicional. Adota-se **16 lanças**, arranjo já
verificado geometricamente contra o perfil do cone (§3), com passo circunferencial
confortável de 9,5 mm.

### 8.6 Efeito sobre o transporte vertical

A adoção de furo pequeno reduz o diâmetro de bolha e, com isso, **reduz também a
velocidade de ascensão** — efeito que precisa ser considerado no balanço da decisão.

Abaixo de Eötvös ≈ 2 a bolha permanece esférica e vale o regime de Stokes; acima, ela
deforma em calota e o arrasto cai acentuadamente, sendo necessária a correlação de
Grace. As duas faixas de interesse situam-se em lados opostos dessa transição:

| diâmetro | Eötvös | velocidade de ascensão | percurso de 7,1 m em |
|---|---|---|---|
| 1 mm (furo perfurado, jato) | 0,2 | 0,1 mm/s | 17,4 h |
| 3 mm (furo perfurado, Tate) | 2,1 | 1,0 mm/s | 116 min |
| 13 mm (descarga aberta, mínimo) | 38,6 | 85,8 mm/s | **83 s** |
| 23 mm (descarga aberta, máximo) | 120,8 | 162,1 mm/s | **44 s** |

A diferença entre as duas configurações é de aproximadamente **três ordens de
grandeza** na velocidade de ascensão.

**Consequência de projeto.** A descarga perfurada oferece ganho expressivo de área
interfacial específica (`a = 6α/d`, cerca de uma ordem de grandeza), porém às custas
do transporte vertical do ar. A descarga aberta apresenta o comportamento inverso.
Trata-se de um compromisso entre **área de contato** e **distribuição espacial**, e
não de uma melhoria em todos os aspectos.

A quantificação desse compromisso exigiria rodadas com o diâmetro de bolha ajustado a
cada configuração e tempo físico compatível com a ascensão (§10.4), o que não integra
o escopo do presente estudo. Recomenda-se como continuidade natural.

---

## 9. Restrição construtiva

A pressão capilar que impede a entrada do xarope em um furo de 1 mm vale `4σ/d` =
**232 Pa**. A pressão hidrostática na cota de descarga é de **88 334 Pa** —
**380 vezes maior**.

Com o suprimento de ar interrompido, o xarope penetra nos furos e os obstrui. Qualquer
lança perfurada neste serviço exige **válvula de retenção individual por lança** ou
pressurização permanente da linha de ar.

Trata-se de requisito de operação, não de detalhe construtivo, e deve constar da
especificação desde o início.

---

## 10. Limitações do modelo e interpretação dos resultados

> Os diâmetros médios de Sauter reportados caracterizam o **inventário de bolhas
> presente no domínio** no instante da medição. A vazão de ar efetivamente admitida
> pelas lanças é **resultado** da simulação — decorre da pressão total imposta na
> descarga e da contrapressão local — e não constitui dado de entrada do modelo. Os
> valores de SMD devem ser lidos em conjunto com a vazão de ar correspondente.

Três observações complementam essa ressalva.

**Sensibilidade da vazão à pressão de suprimento.** Com descarga aberta não há
restrição no bocal, e a vazão de ar torna-se hipersensível à pressão de linha:
variações de poucos por cento alteram a vazão em ordens de grandeza. Em operação real,
a vazão de ar é determinada pelo soprador, e não pela lança. A campanha em pressão,
portanto, caracteriza a ausência de restrição da descarga, e não a vazão de processo.

**Aplicabilidade do modelo de turbulência.** O número de Reynolds do lado do xarope
situa-se entre 6 e 470 em todas as escalas relevantes, contra transição em torno de
2 300. O escoamento é laminar. O modelo k-ε empregado opera fora de sua faixa de
calibração e produz dissipação turbulenta superior à potência de aeração física do
sistema. Em consequência, **a quebra de bolha observada na região de descarga
(SMD mínimo de 0,816 mm) deve ser considerada um limite superior otimista**, não uma
previsão. As conclusões deste relatório não dependem desse valor.

**Tempo físico e diâmetro adotado — §10.4.** O intervalo simulado é de 0,18 s. O
diâmetro imposto na condição de contorno é de 1,0 mm, para o qual a velocidade de
ascensão vale 0,1 mm/s — o percurso da coluna de 7,11 m demandaria 17,4 h. Em 0,18 s
uma bolha percorre 0,02 mm. **A simulação, portanto, não pode caracterizar a
distribuição vertical do ar**, e os percentuais de volume atingido de §5 devem ser
lidos como fotografia do transitório de formação das plumas.

Acrescente-se que 1,0 mm é inferior ao diâmetro previsto analiticamente para a
descarga aberta — 13 a 23 mm por Rayleigh-Taylor (§7.1) —, faixa na qual a bolha
deforma (Eötvös entre 39 e 121) e ascende entre 44 e 83 s. A condição de contorno
adotada subestima, portanto, o transporte vertical por cerca de três ordens de
grandeza. A caracterização da distribuição em regime exigiria nova rodada com o
diâmetro coerente e tempo físico da ordem de um minuto.

**Diâmetro de bolha como entrada.** No modelo euleriano, o diâmetro é transportado a
partir do valor imposto na condição de contorno, e não calculado a partir da física de
formação. A previsão de 13 a 23 mm de §7 provém de análise analítica independente
(Rayleigh-Taylor), não do resultado numérico. Uma determinação direta exigiria
simulação com interface resolvida de uma única descarga — estudo de escopo reduzido,
recomendado caso o valor absoluto seja requerido.

---

## 11. Conclusões

1. O arranjo de 16 lanças distribui o ar em 16 plumas individualizadas, em dois anéis
   e duas cotas, sem fusão entre plumas vizinhas.

2. Junto às descargas o ar forma **cavidades de alta fração de vazio** (47,7 % no
   volume alcançado), e não uma nuvem dispersa. A distribuição do ar no tanque em
   regime permanente **não foi caracterizada** neste estudo (§10.4).

3. **A meta de 0,2 mm não é atingível com descarga aberta**, e a limitação é de
   mecanismo, não de arranjo. Com Bond = 898, o diâmetro é fixado por Rayleigh-Taylor
   em 13 a 23 mm, independentemente do número, da altura ou da disposição das lanças.

4. Uma vez formada, a bolha **não se reduz**: quebra turbulenta, quebra por
   cisalhamento e quebra por oscilação de forma estão todas fora de faixa neste
   xarope, e a coalescência medida é nula.

5. O caminho técnico para reduzir a bolha é **furo abaixo de 2 mm operado em regime
   de jato**, com a restrição de entupimento de §9 tratada em projeto. Registra-se que
   a redução do diâmetro aumenta a área interfacial e **reduz a velocidade de
   ascensão** (§8.6): trata-se de compromisso, não de melhoria integral.

---

## Apêndice A — a instabilidade de Rayleigh-Taylor

Quando um gás é injetado sob um líquido, a interface entre ambos é instável: o fluido
pesado repousa sobre o leve, e a gravidade tende a inverter a configuração. Qualquer
ondulação da interface tende a crescer.

Duas forças disputam essa ondulação:

- a **gravidade**, que amplifica a perturbação, com intensidade proporcional a
  `Δρ·g/k` — mais eficaz em comprimentos de onda longos;
- a **tensão superficial**, que resiste à curvatura e amortece a perturbação, com
  intensidade proporcional a `σ·k²` — mais eficaz em comprimentos de onda curtos.

A taxa de crescimento de uma perturbação de número de onda `k = 2π/λ` obedece a

    n² ∝ k · [ Δρ·g − σ·k² ]

O crescimento ocorre apenas enquanto o colchete é positivo, isto é, `k < √(Δρg/σ)`.
Em comprimento de onda, isso define o **comprimento de onda crítico**

    λ_c = 2π·√(σ / Δρ·g) = 13,1 mm

Abaixo de λ_c a tensão superficial prevalece e a ondulação se extingue; acima, a
gravidade prevalece e ela cresce. Maximizando a taxa de crescimento em relação a `k`
obtém-se o **comprimento de onda de crescimento mais rápido**, que é o que se
manifesta fisicamente:

    λ_m = √3 · λ_c = 2π·√(3σ / Δρ·g) = 22,8 mm

**Aplicação ao dimensionamento.** O parâmetro que separa os regimes é o comprimento
capilar, `l_c = √(σ/ρg)` = 2,09 mm — a escala em que tensão superficial e gravidade se
equivalem.

Em descarga **pequena** (d_o ≪ l_c), a bolha permanece ancorada à borda do orifício e
destaca quando o empuxo supera a tensão superficial que a retém. Esse é o balanço da
lei de Tate, e o tamanho fica atrelado ao diâmetro do furo.

Em descarga **grande** (d_o ≫ l_c), a interface é ampla demais para ser sustentada
pela borda. Comporta-se como superfície plana e se fragmenta no seu próprio
comprimento de onda natural. O tamanho da bolha passa a ser λ e **deixa de depender do
diâmetro da descarga**.

A descarga analisada tem d_o = 62,7 mm contra l_c = 2,09 mm — Bond = 898, plenamente
no segundo regime.

---

## Apêndice B — grandezas empregadas

| grandeza | expressão | valor |
|---|---|---|
| comprimento capilar | `√(σ/ρg)` | 2,09 mm |
| número de Bond | `(d_o/l_c)²` | 898 (descarga atual) |
| número de Morton | `gμ⁴/(ρσ³)` | 6,6 × 10⁴ |
| escala de Kolmogorov | `(ν³/ε)^(1/4)` | 42,7 mm (ε de projeto) |
| Ca crítico (Hinch & Acrivos) | `0,054·λ^(−2/3)` | ≈ 270 |
| lei de Tate | `(6σd_o/ρg)^(1/3)` | válida para Bond ≪ 1 |
| transição para regime de jato | `We_g = ρ_g v²d_o/σ ≈ 2` | atual: 0,115 |
| velocidade terminal de Stokes | `Δρ g d²/(18µ)` | 0,17 mm/s para d = 1 mm |

**Propriedades adotadas:** xarope ρ = 1 350 kg/m³ · µ = 6,5 Pa·s · σ = 0,058 N/m ·
ar ρ ≈ 2,1 kg/m³ na cota de descarga.
