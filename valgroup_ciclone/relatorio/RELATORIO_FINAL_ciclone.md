# Ciclone de separação de char — Relatório técnico

**Cliente:** Valgroup · Unidade de pirólise de r-PET
**Objeto:** dimensionamento e verificação por CFD de ciclone para retenção de char na corrente de gás de pirólise
**Análise:** Simcenter STAR-CCM+ · RANS + rastreamento Lagrangeano
**Data:** agosto de 2026

---

# 1. Sumário executivo

| item | resultado |
|---|---|
| **Geometria** | Stairmand alta eficiência · **D_c = 307 mm** |
| **Queda de pressão** | **19,6 mbar** a 100 % · **4,7 mbar** a 50 % *(limite 40 mbar)* |
| **Folga de pressão** | **51 %** no modelo base · **32 %** no cenário mais conservador |
| **Temperatura de parede** | **378,5 °C** a 100 % · **363,7 °C** a 50 % |
| **Diâmetro de corte** | **6,84 µm** a 100 % · **9,90 µm** a 50 % |
| **Eficiência global** | **92,9 % a 100,0 %** — o intervalo depende de dado ainda não medido |
| **Emissão de char** | **0 a 5,7 kg/h** (de 80 kg/h alimentados) |

**O intervalo da eficiência global não vem do modelo.** Ele vem de a granulometria disponível ter
sido obtida por **peneiramento**, técnica que não resolve abaixo de 61 µm. Essa fração representa
**9,14 % da massa** e é onde ocorre praticamente toda a perda de um ciclone. Uma análise por
**difração a laser** nessa fração fecha o intervalo — é o único item pendente com esse poder.

---

# 2. Base de projeto

| grandeza | valor | origem |
|---|---|---|
| Vazão mássica de gás | 1.820 kg/h | 1.900 − 80; confirmado em reunião |
| Massa específica do gás | 3,946 kg/m³ | cliente |
| Temperatura | 400 °C | planilha do cliente *(SCADA TT-209 indica ~343 °C — ver §9)* |
| Pressão | 1,2 bar | cliente |
| Vazão volumétrica | **461,2 m³/h** | calculada |
| Viscosidade do gás | 9,5×10⁻⁵ Pa·s | planilha do cliente *(sob verificação — §9)* |
| Particulado | 80 kg/h | cliente |
| Massa específica da partícula | **1.500 kg/m³** | ⚠️ **não** os 776,75 da planilha, que é densidade de leito |
| Limite de queda de pressão | 40 mbar (16" H₂O) | projeto |

> **Sobre a massa específica.** A planilha do cliente adota 776,75 kg/m³, que é a densidade
> **aparente do leito** — inclui os vazios entre partículas e subestima a inércia. A própria
> tabela de "Valores Usuais" daquela planilha declara a faixa **1.500 a 3.000 kg/m³**, e o valor
> utilizado está **abaixo do mínimo que ela mesma estabelece**. Adotou-se 1.500 kg/m³.

---

# 3. Geometria

**Família Stairmand de alta eficiência**, proporções clássicas sobre D_c = 307 mm:

| cota | símbolo | valor (mm) |
|---|---|---|
| Diâmetro do corpo | D_c | **307,0** |
| Altura da entrada | a | 153,5 |
| Largura da entrada | b | 61,4 |
| Diâmetro do duto de saída | D_e | 153,5 |
| Profundidade do vortex finder | S | 153,5 |
| Altura da parte cilíndrica | h | 460,5 |
| Altura total | H | 1.228,0 |
| Diâmetro da saída de pó | B | 115,1 |
| Voltas efetivas (tabela) | N_e | 6 |

Volume interno **73,30 L**. Velocidade de entrada **13,59 m/s** a 100 % e **6,80 m/s** a 50 %.

## 3.1 Por que 307 mm e não 290

O dimensionamento pela velocidade recomendada de 15,24 m/s conduz a D_c = 290 mm. Esse diâmetro
foi verificado e **reprovado no cenário mais conservador de modelo de turbulência**:

| cenário de modelo | D_c = 290 | **D_c = 307** |
|---|---|---|
| k-ω (piso) | 31,3 mbar | **19,6 mbar** |
| RST estacionário | 37,0 mbar | 23,1 mbar |
| RST, assíntota pessimista | **43,5 mbar** 🔴 estoura | **27,2 mbar** ✅ |

O aumento de 5,9 % no diâmetro custa **≤ 4 pontos percentuais** de eficiência em 10 µm e
**≤ 2 pontos** acima de 20 µm, e converte uma folga negativa em **32 %**.

---

# 4. Modelo numérico e verificação

## 4.1 Escoamento
| item | escolha |
|---|---|
| Regime | estacionário (steady) |
| Turbulência | k-ω SST |
| Energia | ativa, gás ideal |
| Saída de gás | **flow-split (`Outlet`)** — ver §4.2 |
| Saída de pó | **parede** — ver §4.2 |
| Parede | convecção · h_e = 10 W/m²·K · T_amb = 25 °C |

## 4.2 Duas decisões de contorno que mudaram o resultado

**(a) A saída de pó é parede, não saída de escoamento.** O ápice do cone situa-se no núcleo de
baixa pressão do vórtice (−239 Pa). Tratado como saída a 0 Pa, ele **injeta 37 a 52 % de vazão
parasita** para dentro do ciclone, a 5–11 m/s contra 21,5 mm/s de velocidade de sedimentação —
razão de 330×. Corrigido para parede, o desequilíbrio de massa caiu de 0,99 % para **0,004 %** e
o resíduo de continuidade de 1×10³ para 7,8×10⁻⁴.

**(b) A saída de gás é flow-split, não pressão prescrita.** Com pressão prescrita ocorria fluxo
reverso e o caso estacionário **não convergia** (razão 0,985). Com flow-split, o desvio-padrão da
queda de pressão vai a **exatamente zero** ao longo de 20.000 iterações.

## 4.3 Rastreamento Lagrangeano
| item | escolha |
|---|---|
| Acoplamento | uma via (carga mássica 4,4 %) |
| Arraste | esférico · dispersão turbulenta ativa |
| Injeção | **classes monodispersas**, uma fase por classe |
| Parcelas | 5.082 por classe *(erro estatístico 0,6 ponto)* |
| Parede lateral | rebote · restituição normal 0,9 · tangencial **1,0** |
| Saída de pó e de gás | escape |
| **Medida da eficiência** | **η = 1 − ṁ_gás,saída / ṁ_injetado** |

> **Sobre a medida.** A prática usual mede a coleta no fundo. Nesta geometria a partícula grossa
> **não alcança o fundo**: sob 830 g de aceleração centrífuga ela entra em regime de quiques
> sucessivos junto à parede — cada impacto devolve 90 % da velocidade normal, o intervalo entre
> impactos encolhe geometricamente e a soma converge em tempo finito com número infinito de
> quiques. O tempo de residência congela e a parcela nunca é contabilizada.
> **Mede-se então a fuga**, que é a grandeza complementar e é observável sem ambiguidade.

---

# 5. Queda de pressão

| carga | v_i | **ΔP** | ξ | v_max/v_i |
|---|---|---|---|---|
| **100 %** | 13,59 m/s | **1.955,6 Pa = 19,56 mbar** | 5,37 | 1,96 |
| **50 %** | 6,80 m/s | **467,5 Pa = 4,68 mbar** | 5,13 | 1,82 |

**Folga contra o limite de 40 mbar: 51 % a 100 % de vazão.**

A razão `v_max/v_i` entre 1,5 e 2,5 indica que o modelo de turbulência não está inflando nem
suprimindo o vórtice — critério que levou a descartar a formulação com correção de curvatura,
que produzia 2,91.

## 5.1 Envelope de incerteza do modelo
O k-ω amortece a precessão do núcleo do vórtice e, por isso, **subestima** a queda de pressão. O
envelope foi levantado no diâmetro de 290 mm por comparação com o modelo de tensões de Reynolds:

| cenário | ΔP a 100 % | folga |
|---|---|---|
| k-ω (medido) | 19,6 mbar | 51 % |
| RST estacionário (×1,18) | 23,1 mbar | 42 % |
| RST, assíntota pessimista (×1,39) | **27,2 mbar** | **32 %** |

---

# 6. Comportamento térmico

## 6.1 Medido
| carga | T_parede média | **T_parede mínima** |
|---|---|---|
| 100 % | **378,5 °C** | ⏳ *(previsto 328,9 °C)* |
| 50 % | **363,7 °C** | **290,5 °C** |

A 50 % de vazão o tempo de residência dobra e o coeficiente de troca interno cai com Re^0,8 — o
gás troca calor por mais tempo através de um filme mais fraco, **e a parede esfria**. A condição
de 50 % é, portanto, a **governante** para a questão de condensação.

### 6.1.1 ⚠️ O mínimo está 73 °C abaixo da média, e é ele que governa

O campo de temperatura não é uniforme. O valor mínimo situa-se no **ápice do cone**, na região
da saída de pó, e está **73,2 °C abaixo da média** na condição de 50 %.

Retro-calculando o coeficiente interno local a partir das duas medições:

| | T_parede | h_i local |
|---|---|---|
| média | 363,7 °C | 93,4 W/m²·K |
| **ápice do cone** | **290,5 °C** | **24,3 W/m²·K** — 26 % da média |

O resultado é coerente com a verificação independente de §4: o comprimento natural do vórtice
(Alexander) termina **296 mm acima da saída de pó**. Abaixo dessa cota o gás é quiescente, a
troca convectiva interna despenca e a parede se aproxima da temperatura ambiente.

**Para a questão de condensação, é este ponto que decide — não a média.**

## 6.2 Modelo de duas resistências — calibrado e verificado
```
T_parede = (h_i·T_gás + h_e·T_amb)/(h_i + h_e)

h_i(100 %) = 164,6 W/m²·K        h_i(50 %) = 93,35 W/m²·K
razão medida 0,567     ×     Re^0,8 esperado 0,574
```
A temperatura de 50 % foi **prevista em 364 °C antes de ser medida**; o valor medido foi
**363,7 °C**. Erro de **0,3 °C**.

## 6.3 Projeção — dispensa nova simulação
Projeção do modelo calibrado, agora aplicada tanto à média quanto ao ponto frio. O `h_e` de
parede nua foi resolvido de forma autoconsistente (o coeficiente de radiação depende da própria
temperatura de parede), o que corrige levemente para cima os valores antes reportados.

| cenário | 100 % média | 100 % frio | 50 % média | **50 % frio** |
|---|---|---|---|---|
| isolada (h_e ≈ 1,5) | 397 °C | 387 °C | 394 °C | **378 °C** |
| simulada (h_e = 10) | 378,5 °C | 328,9 °C | 363,7 °C | **290,5 °C** |
| nua, alumínio polido (ε = 0,05) | 377 °C | 329 °C | 362 °C | **295 °C** |
| **nua, aço oxidado (ε = 0,80)** | 345 °C | 270 °C | 317 °C | **230 °C** |

Note-se que o `h_e` externo **não depende da condutividade do metal**, e sim da **emissividade
da superfície**. O aço carbono oxidado ou pintado corresponde a ε ≈ 0,8; um revestimento
metálico polido reduz a emissividade em mais de uma ordem de grandeza e mantém a parede
aproximadamente **65 °C mais quente** sem qualquer isolamento térmico.

⇒ **A parede média opera entre 317 e 397 °C. O ápice do cone, entre 230 e 387 °C.**

### 6.3.1 Consequência para o isolamento

Comparando o ponto frio a 50 % contra as duas hipóteses de orvalho:

| ponto frio a 50 % | contra 250 °C | contra 343 °C (C20) |
|---|---|---|
| isolada | +128 °C ✅ | **+35 °C ✅** |
| nua, alumínio polido | +45 °C ✅ | −48 °C ❌ |
| **nua, aço oxidado** | **−20 °C ❌** | −113 °C ❌ |

**Revisão de recomendação.** Avaliado apenas pela temperatura média, o isolamento seria decisão
de eficiência energética. Avaliado pelo **ápice do cone**, deixa de ser: com a parede nua e
oxidada a região condensa mesmo na hipótese otimista de orvalho.

O trecho crítico, contudo, é pequeno — os **últimos ~300 mm do cone**, abaixo do fim do vórtice,
correspondendo a cerca de **15 % da área lateral**. Isolar somente esse trecho eleva o ponto frio
a 378 °C, o que cobre **as duas hipóteses de orvalho simultaneamente**, incluindo o C20.

**Recomendação: isolar o cone inferior e a saída de pó.** O corpo cilíndrico admite decisão por
eficiência energética.

## 6.4 ⚠️ O critério de comparação está em revisão
O ponto de orvalho foi inicialmente estimado em **230 a 250 °C** a partir de uma cromatografia
que indicava hidrocarbonetos C7 a C15. O cliente informou posteriormente que **aquela amostra era
de óleo** — a fração pesada já havia condensado e sido separada, e os leves não condensáveis
haviam seguido adiante. **A corrente real na saída do reator vai de C1 a C40**, e o n-eicosano
(C20) ferve a 343 °C.

**A medição térmica está completa e correta. O número contra o qual compará-la é que está
pendente.** Requer a composição real da corrente (§9).

> **Indício relevante:** o cliente relatou que o char arrastado sai **contaminado de parafina**.
> Isso indica que a fração pesada condensa na mesma região por onde o particulado transita — que
> é onde se instalaria o ciclone. Condensado somado a particulado fino é o mecanismo clássico de
> incrustação em ciclone, e merece verificação antes da construção.

---

# 7. Eficiência de coleta

Vinte pontos medidos: dez classes monodispersas em duas cargas.

| d (µm) | **η · 100 %** | **η · 50 %** | Δ turndown |
|---|---|---|---|
| 1 | 22,70 % | 25,44 % | +2,74 |
| 2 | 22,31 % | 24,52 % | +2,21 |
| 5 | 31,34 % | 26,19 % | −5,15 |
| 7 | 51,35 % | 33,08 % | −18,27 |
| **10** | **79,14 %** | **50,49 %** | **−28,65** |
| 15 | 97,70 % | 81,21 % | −16,49 |
| 20 | 99,98 % | 94,96 % | −5,02 |
| 50 · 75 · 150 | 100,00 % | 100,00 % | 0,00 |

| | **d\*** |
|---|---|
| 100 % de vazão | **6,84 µm** |
| 50 % de vazão | **9,90 µm** |

## 7.1 Verificação — o escalonamento com a vazão
| | razão d\* (50 %/100 %) |
|---|---|
| CFD | **1,447** |
| Solução analítica (Lapple) | **1,413** |
| **diferença** | **2,4 %** |

O modelo discorda da correlação em **17 %** no *nível* do diâmetro de corte, mas concorda em
**2,4 %** em *como* a separação responde à vazão. Um erro de modelagem raramente preserva a
derivada — a concordância na derivada é evidência mais forte que a concordância no valor.

## 7.2 Por que o corte é mais fino que a correlação prevê
A correlação de Lapple adota **N_e = 6 voltas efetivas**, valor **tabelado**, não calculado.
Invertendo a expressão a partir do resultado medido:

```
N_e = 6 × (8,28/6,84)² = 8,8 voltas
```

Valor dentro da faixa de 5 a 10 reportada na literatura para ciclones Stairmand de alta
eficiência. **O CFD resolve o swirl real em vez de assumi-lo.**

## 7.3 Duas feições físicas da curva

**(a) Patamar abaixo de 3 µm.** A eficiência estabiliza em ~22 % (100 %) e ~25 % (50 %). Nessa
faixa a captura deixa de ser governada por inércia e passa a ser **deposição turbulenta**, que
não depende do tamanho. O patamar foi verificado por sensibilidade: desligando o modelo de
dispersão turbulenta, a fuga em 1 µm variou **0,19 ponto** (77,30 % → 77,49 %) — **o patamar é
determinado pelo escoamento médio**, não pelo modelo de turbulência.

**(b) O turndown não degrada uniformemente.** A perda concentra-se entre 5 e 20 µm, atinge
**−28,7 pontos em 10 µm**, e **abaixo de 2,63 µm inverte de sinal**: reduzir a vazão **melhora**
a captura, porque o tempo de residência dobra e a deposição turbulenta depende de tempo.

**(c) Efeito *fishhook*.** Em ambas as cargas, η(1 µm) > η(2 µm) — +0,39 e +0,92 ponto. Abaixo do
regime inercial, quanto menor a partícula mais difusiva ela é e mais deposição sofre. A
significância individual é baixa (0,67 σ e 1,5 σ contra 0,6 ponto de erro estatístico), mas a
**consistência de sinal nas duas cargas** favorece feição real sobre ruído.

---

# 8. Eficiência global

A granulometria disponível, obtida por **peneiramento**, tem as seguintes faixas:

| faixa (µm) | fração |
|---|---|
| 4.750 – 12.500 | 2,78 % |
| 1.000 – 4.750 | 3,77 % |
| 425 – 1.000 | 9,51 % |
| 150 – 425 | 12,10 % |
| 75 – 150 | 25,79 % |
| 61 – 75 | 36,91 % |
| **abaixo de 61 µm (fundo de peneira)** | **9,14 %** ⚠️ |

**Todas as faixas medidas situam-se na região onde η = 100 %.** Logo:

```
η global, com o dado medido = 100,00 %
```

**Toda a resposta do estudo depende dos 9,14 % de fundo de peneira**, cuja distribuição interna
não foi medida:

| se o fundo estiver em | η global 100 % | η global 50 % | char arrastado |
|---|---|---|---|
| 61 µm *(hipótese da planilha)* | 100,00 % | 100,00 % | 0 kg/h |
| 20 µm | 100,00 % | 99,54 % | 0,4 kg/h |
| 15 µm | 99,79 % | 98,28 % | 1,4 kg/h |
| 10 µm | 98,09 % | 95,47 % | 3,6 kg/h |
| 5 µm | 93,72 % | 93,25 % | 5,4 kg/h |
| **1 µm** | **92,93 %** | **93,19 %** | **5,7 kg/h** |

⇒ **Piso de 92,9 % em qualquer cenário e em qualquer carga.**

> A curva medida **estreita** a incerteza em relação à estimativa por correlação (7,1 contra
> 8,8 pontos), porque possui o patamar de ~22 % na ponta fina enquanto a correlação tende a zero.

---

# 9. Segundo estágio — análise quantitativa

Foi avaliada a proposta de dois ciclones **em série**. Estágios em série multiplicam a
penetração: `η_total = 1 − (1−η₁)(1−η₂)`.

| cenário do fundo | 1 estágio | **2 em série** | ganho |
|---|---|---|---|
| 1 µm | 92,93 % | 94,54 % | **+1,6 pt** |
| 5 µm | 93,72 % | 95,69 % | +2,0 pt |
| 10 µm | 98,09 % | 99,60 % | +1,5 pt |

| | ΔP |
|---|---|
| 1 estágio | 19,6 mbar |
| **2 em série** | **39,2 mbar** *(limite 40 — folga de 2 %)* |
| 2 em série, cenário pessimista | **54,4 mbar** 🔴 **estoura em 36 %** |

**Conclusão:** o segundo estágio consome integralmente o orçamento de pressão para adicionar
**1 a 2 pontos** de eficiência. O ganho é pequeno porque **90,86 % da massa já é capturada em
100 %** — apenas os 9,14 % de fundo estão em disputa.

**Multiciclone em paralelo** (N unidades menores, mesma velocidade de entrada, mesma queda de
pressão) afina o corte com `d* ∝ N^(−1/4)`: N = 4 leva a 4,84 µm; N = 9 a 3,95 µm. Porém **abaixo
de 3 µm a captura não é governada pelo diâmetro de corte**, de modo que o ganho na ponta fina
também é limitado. Acrescenta-se o risco de obstrução dos ápices menores, relevante dado o
relato de parafina no char.

⇒ **A decisão sobre segundo estágio deve ser tomada após a difração a laser.** Se o fundo de
peneira situar-se acima de 15 µm, o estágio único já entrega ~100 % e o segundo não tem função.
Se situar-se em 1 a 2 µm, nenhum arranjo ciclônico resolve, e a discussão passa a ser de
tecnologia.

---

# 10. Premissas e limitações

1. **Medida de eficiência por fuga.** Partícula retida na parede é contabilizada como coletada —
   fisicamente correto (integra o *strand* descendente), mas **não representa reentranhamento**.
   Viés unidirecional, medido em **+2,7 pontos** em 50 µm sobre a correlação.
2. **Curva mais íngreme que a forma analítica.** A saturação em 100 % ocorre a partir de ~15 µm;
   curvas reais apresentam cauda. Viés otimista no trecho grosso, sem consequência prática, pois
   ali a eficiência já é ≥ 97 % por qualquer critério.
3. **Turbulência k-ω** amortece a precessão do núcleo do vórtice ⇒ **subestima a queda de
   pressão**. Envelope quantificado em §5.1 e adotado o cenário conservador na decisão de diâmetro.
4. **Dispersão turbulenta isotrópica.** Verificada por sensibilidade em 1 µm: variação de
   **0,19 ponto**. O patamar fino é determinado pelo escoamento médio.
5. **Massa específica da partícula 1.500 kg/m³** e **viscosidade do gás 9,5×10⁻⁵ Pa·s**. Ambos
   sob verificação. A curva é convertível para quaisquer outros valores sem nova simulação, pois
   a trajetória depende apenas do tempo de relaxação `τ_p = ρ_p d²/18µ`:
   `d_equivalente = d·√[(ρ_novo/1500)·(9,5×10⁻⁵/µ_novo)]`.
6. **Sensibilidade de malha** na região de entrada não quantificada.
7. **Ponto de orvalho** em revisão — ver §6.4.

---

# 11. Pendências

| # | item | bloqueia | prioridade |
|---|---|---|---|
| 1 | **Difração a laser na fração < 61 µm** | a eficiência garantida e a decisão de segundo estágio | 🔴 alta |
| 2 | **Composição da corrente (C1–C40)** na saída do reator | o ponto de orvalho e o critério térmico | 🔴 alta |
| 3 | **Viscosidade do gás** — origem do valor 1,0×10⁻⁴ Pa·s | o diâmetro de corte | 🟡 média |
| 4 | **Massa específica da partícula** por picnometria | o diâmetro de corte | 🟡 média |
| 5 | Histórico de incrustação/limpeza no trecho | risco operacional | 🟡 média |
| 6 | Meta de eficiência exigida pelo processo | decisão de segundo estágio | 🔴 alta |

> Sobre o item 3: a 400 °C, o metano puro — o hidrocarboneto de maior viscosidade da série —
> apresenta ~2×10⁻⁵ Pa·s, e o nitrogênio ~3×10⁻⁵. **Nenhuma mistura gasosa real atinge
> 1×10⁻⁴ Pa·s nessa temperatura.** Recomenda-se verificar a unidade da fonte.

---

# 12. Referências

- **Peçanha, R. P.** *Sistemas Particulados: Operações Unitárias Envolvendo Partículas e Fluidos.*
  Cap. 3 — Sistemas Particulados Diluídos.
- **Cremasco, M. A.** *Operações Unitárias em Sistemas Particulados e Fluidomecânicos.* Cap. 6 e 8.
- **Hoekstra, A. J.; Derksen, J. J.; Van Den Akker, H. E. A.** (1999). *An experimental and
  numerical study of turbulent swirling flow in gas cyclones.* Chemical Engineering Science,
  54(13–14), 2055–2065. **DOI: 10.1016/S0009-2509(98)00373-X**
- **Alexander, R. McK.** (1949). *Fundamentals of cyclone design and operation.* Proceedings of the
  Australasian Institute of Mining and Metallurgy.
- **Siemens Digital Industries Software.** *Simcenter STAR-CCM+ User Guide* — Best Practices:
  Cyclone Separators; artigo de base de conhecimento **KB000033060**.

---

*Documento gerado a partir do registro completo de simulações em `valgroup_ciclone/`.
Todos os valores citados são rastreáveis aos arquivos de resultado do repositório.*
