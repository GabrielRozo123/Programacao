# Passo a passo — Splitter C3 no DWSIM 10.2.3.0 + AI4Tech Suite

Roteiro para fazermos juntos. Cada passo termina num **✋ CHECKPOINT**: você me
manda o resultado e eu ajusto o que vier antes de seguir.

Referência: [guia conceitual](dwsim-splitter-c3.md) ·
[gêmeo em Python](../casos-python/02-splitter-c3/CONFIG.md)

---

## Passo 0 — Preparar a simulação

1. **File → New Simulation** (simulação em estado estacionário).
2. Abra **Simulation Settings** (botão na barra superior).
3. Aba **Compounds**: procure e marque
   - `Propylene` (propeno)
   - `Propane` (propano)
4. Aba **Property Packages**: adicione **Peng-Robinson (PR)**.
5. Aba **System of Units**: escolha um conjunto com **bar** para pressão,
   **kmol/h** para vazão molar e **K** ou **°C** para temperatura. Só para
   evitar conversão mental depois.
6. Salve como `splitter_c3.dwxmz`.

Sem checkpoint — é só preparação.

---

## Passo 1 — Medir a volatilidade relativa ✋

Este é o passo mais importante antes de qualquer coluna, e leva meia hora.

**Por quê.** A coluna precisa de ~200 estágios. Nessa faixa, o número de
estágios é extremamente sensível a α: pela equação de Fenske, `N_min` é
proporcional a `1/ln(α)`. Com α = 1,12, `ln(α) = 0,1133`; com α = 1,10,
`ln(α) = 0,0953`. **Dois por cento em α mudam o número mínimo de estágios em
19 %.** Escolher o pacote termodinâmico no chute aqui custa dezenas de pratos.

### O que fazer

1. Arraste uma **Material Stream** para o flowsheet.
2. Abra as propriedades da corrente e defina:
   - Composição: `Propylene` 0,75 e `Propane` 0,25 (fração molar)
   - Vazão molar: 1000 kmol/h
   - **Flash Spec: Pressure and Vapour Fraction (PVF)**
   - Pressão: **18 bar**
   - Vapour Fraction: **0,5**
3. Rode (**Solve**).
4. Nos resultados da corrente, abra as composições **por fase** e anote as
   frações molares de propeno na fase **vapor** (`y`) e na fase **líquida** (`x`).

### Calcular α

```
α = (y_propeno / x_propeno) / (y_propano / x_propano)
```

Com fração de vapor 0,5 e alimentação 75/25, espere `y` um pouco acima de 0,75
e `x` um pouco abaixo — a diferença é pequena justamente porque α é baixo.
Use todas as casas decimais que o DWSIM mostrar: com α ≈ 1,1 a conta é
sensível a arredondamento.

### Repita em três pressões e dois pacotes

Preencha esta tabela — é ela que eu preciso:

| Pacote | P (bar) | y propeno | x propeno | α calculado | T de equilíbrio (°C) |
|---|---|---|---|---|---|
| Peng-Robinson | 14 | | | | |
| **Peng-Robinson** | **18** | **0,75937** | **0,74063** | **1,105152** | **45,0796** |
| Peng-Robinson | 22 | | | | |
| SRK | 14 | | | | |
| SRK | 18 | | | | |
| SRK | 22 | | | | |

Para trocar de pacote: **Simulation Settings → Property Packages**, adicione
**Soave-Redlich-Kwong (SRK)** e associe a corrente a ele (ou troque o pacote
padrão do flowsheet) e rode de novo.

### ✋ CHECKPOINT 1

Me mande a tabela preenchida. Com ela eu:

- **recalibro a correlação α(P) do modelo Python** contra o seu DWSIM — hoje
  ela usa `α = 1,221 − 0,0058·P`, ajustada a valores de literatura, e prevê
  α = 1,117 a 18 bar. Quero o número da sua máquina no lugar;
- comparo PR e SRK e a gente decide o pacote com um critério, não com opinião;
- confiro se a temperatura de equilíbrio bate com o meu Antoine (previsão:
  44,2 °C a 18 bar para propeno quase puro — no seu caso a mistura é 75/25,
  então espere um pouco mais alto).

**Este é um resultado publicável por si só**: "sensibilidade do projeto de um
splitter C3 à escolha do pacote termodinâmico".

---

## Passo 2 — Coluna com 50 estágios ✋

Ainda não vamos para 200. Uma coluna de α baixo com 200 estágios raramente
converge do zero.

1. Na paleta **Columns**, arraste uma **Distillation Column** (coluna
   rigorosa, não a Shortcut).
2. Configure:

| Parâmetro | Valor |
|---|---|
| Número de estágios | **50** |
| Condensador | Total |
| Refervedor | Kettle / parcial |
| Estágio de alimentação | 25 |
| Pressão no condensador | 18 bar |
| Pressão no refervedor | **18 bar** (perda de carga zero por enquanto) |
| Método de solução | **Inside-Out** |

3. Conecte a corrente de alimentação no estágio 25, e crie as correntes de
   destilado, de fundo e as duas correntes de energia.
4. **Especificações** — de operação, não de pureza:

| Especificação | Valor |
|---|---|
| Condensador | Reflux Ratio = **15** |
| Refervedor | Distillate Molar Flow = **746 kmol/h** |

   Especificação de pureza numa coluna de α ≈ 1,1 é muito mais difícil de
   convergir. Além disso, para o DOE do AI4Tech elas são melhores: com
   especificação de operação **todo ponto do DOE converge**, enquanto com
   especificação de pureza há combinações simplesmente inalcançáveis.

5. **Solve**.

Com 50 estágios a pureza vai ficar **bem abaixo** de 99,5 % — é esperado e não
é erro. O objetivo aqui é só a coluna fechar o balanço e convergir.

### Se não convergir

- Reduza o fator de amortecimento para 0,5–0,7 e aumente o limite de iterações.
- Tente **Napthali-Sandholm** (correção simultânea) no lugar do Inside-Out.
- Confira se a alimentação está em líquido saturado (fração de vapor = 0).
- Comece com refluxo menor (R = 8), converja, e suba para 15.

### ✋ CHECKPOINT 2

Me diga: convergiu? Em quantas iterações e quanto tempo? Qual pureza de topo e
de fundo deu? Se não convergiu, me mande a mensagem de erro.

---

## Passo 3 — Subir para 200 estágios em degraus ✋

Agora sim. **Não pule direto.** A cada passo, a solução convergida vira a
estimativa inicial do próximo:

| Etapa | Estágios | Alimentação | Refluxo |
|---|---|---|---|
| 3.1 | 100 | 50 | 15 |
| 3.2 | 150 | 75 | 15 |
| 3.3 | 200 | 100 | 15 |

Resolva a cada mudança antes de fazer a próxima. Só depois de convergir com
200 estágios, introduza a perda de carga: ~0,003 bar por prato, ou seja, cerca
de **0,7 bar** entre o topo e o fundo. Reconverja.

### Referência de chegada

Com N = 200, alimentação no estágio 100, R = 15, D = 746 kmol/h a 18 bar, o
modelo Python dá:

| Grandeza | Python (atalho) | Seu DWSIM |
|---|---|---|
| Propeno no topo | 99,55 % mol | |
| Propano no fundo | 97,20 % mol | |
| Carga do refervedor | 42,1 MW | |
| T topo | 44,2 °C | |
| T fundo | 52,4 °C | |
| Vazão de vapor no topo | 11 940 kmol/h | |

**A diferença entre as colunas não é defeito — é resultado.** O modelo Python
assume α constante, fluxo molar constante e perda de carga nula; o DWSIM não
assume nada disso. Medir o tamanho do erro do atalho é parte do projeto, e é
o que justifica a etapa de validação cruzada lá na frente.

### ✋ CHECKPOINT 3

Me mande a coluna "Seu DWSIM" preenchida, **e o tempo de uma solução**. O tempo
por run define toda a estratégia do DOE: se for 3 segundos, 500 pontos levam
25 minutos e dá para rodar na nuvem; se for 30 segundos, são 4 horas e vamos de
worker local com DOE menor.

---

## Passo 4 — Inventário de variáveis ✋

Aqui resolvemos a sua pergunta sobre o campo **Cell**.

1. Abra a aba **Script Manager**.
2. Crie um script novo.
3. Cole o conteúdo de
   [`ferramentas/dwsim_inventario.py`](../ferramentas/dwsim_inventario.py).
4. Execute e copie a saída do painel de mensagens.

O script percorre todos os objetos do flowsheet e imprime, para cada um: o
nome interno, a tag visível e todos os identificadores de propriedade (formato
`PROP_MS_0`, `PROP_CO_3` etc.), com valor e unidade.

### Conferência pelo caminho gráfico

Independente do script, o DWSIM tem um jeito visual de descobrir a mesma coisa:

1. Vá na aba **Spreadsheet**.
2. **Clique com o botão direito** numa célula → **Select Object/Property**.
3. Escolha o objeto e a propriedade nas listas.
4. O DWSIM escreve sozinho a fórmula. Exemplo real do seu 10.2.3.0:

```
=GETPROPVAL("MAT-9c4e4e77-638c-40c3-8607-0cd1fbd38802";"PROP_MS_0";"C")
```

São três argumentos — **objeto ; propriedade ; unidade** — e o objeto vem com
**GUID, não com a tag**. Confirmado também: `PROP_MS_0` é a temperatura.

> ⚠️ Se você apagar e redesenhar uma corrente, o GUID muda e toda referência a
> ela quebra. Monte o flowsheet inteiro antes de coletar os identificadores.

### ✋ CHECKPOINT 4

Me mande:

1. A saída do script (ou pelo menos os blocos da coluna e das correntes).
2. Uma fórmula `GETPROPVAL` gerada pelo botão direito, como exemplo.
3. Um print do **Edit modal** do DWSIM Case no AI4Tech, mostrando como ele pede
   o campo Cell — se houver seletor de objetos, o formato aparece ali e é ele
   que manda.

Com isso eu monto a tabela completa de variáveis de entrada e saída, no formato
exato da sua versão, pronta para colar.

---

## Depois dos checkpoints

5. Criar o DWSIM Case no AI4Tech e rodar um DOE de 50 pontos só para validar o
   encanamento.
6. DOE de verdade no worker local, com as faixas escolhidas pelo modelo Python.
7. Analysis → Surrogate → Validation → Optimization → MCDM.
8. Validação cruzada dos melhores pontos do Pareto na coluna rigorosa.

---

## Comece por aqui

**Passo 0 e Passo 1.** Faça o flash e me mande a tabela de α. É meia hora de
trabalho, já é resultado próprio, e me deixa recalibrar o modelo Python contra
a sua máquina antes de investirmos tempo na coluna.
