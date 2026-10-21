# 03 — Pendências e perguntas ao cliente

> Log datado. Cada resposta recebida entra aqui com data e é propagada para o doc temático.

---

## 🔴 BLOQUEANTE — sem isto não há estudo

### 1. Vazão mássica de O₃ de cada cenário de liberação
**Tudo escala com ela** (§1 do `02`). Sem esse número, o estudo produz campos relativos,
não concentrações.

| caminho | o que precisamos |
|---|---|
| Exaustores | vazão do ventilador × concentração de O₃ no ar interno |
| PSVs | vazão de alívio na pressão de set, e duração do sopro |
| Off-gás | vazão da corrente × concentração de O₃ |

### 2. Concentração de O₃ na corrente liberada
Em branqueamento, o gerador entrega tipicamente **6 a 14 % em massa de O₃ em O₂**.

Isso importa por dois motivos:
- se a liberação for essa mistura, o jato **na fonte** é levemente denso (O₂ tem MM 32 contra
  29 do ar) e com momento alto a 10 bar — o **campo próximo** pode precisar de tratamento
  diferente do campo distante, mesmo com o escalar sendo passivo longe dali
- define a conversão entre vazão da corrente e vazão de O₃

---

## 🟠 Define premissas da Etapa 2

### 3. Dados meteorológicos — com timestamp horário
O portal mostrado na reunião (Zeus Agro) tem série horária de 01/01/2026 a 28/08/2026.
Precisamos de **velocidade + direção + hora do dia**, porque a **estabilidade atmosférica** se
infere disso (Pasquill-Turner). Se houver **cobertura de nuvens** ou **radiação solar**, melhor
ainda — o portal mostrava uma caixa "Radiação solar" desmarcada.

> Sem estabilidade, o estudo perde o cenário que governa — fator de 9× em vazão de fonte
> (§3 do `02`).

### 4. Rugosidade / uso do solo no entorno
A planta é sítio industrial, mas o entorno da LD Celulose é agrícola. **Distâncias mudam de
2 a 4×** conforme a escolha (§4 do `02`). Precisamos definir com o cliente o raio a partir do
qual o terreno deixa de ser industrial.

### 5. Os limiares de 0,2 e 0,5 ppm são instantâneos ou média em janela?
Muda o pós-processamento: campo médio vs percentil de uma série. **[A CONFIRMAR]** com a
equipe de segurança.

---

## 🟡 Dados de equipamento

### 6. Folha de dados dos exaustores contínuos — pedido do Marcus
Para modelar a interface de ventilação. **O que muda o resultado não é a vazão:**

| dado | por que importa |
|---|---|
| vazão (m³/h) | diluição na saída |
| **⭐ direção da descarga** | vertical para cima vs grelha horizontal **muda tudo** |
| **⭐ altura acima do solo** | de 5 para 15 m o pico no solo cai 9× (§5 do `02`) |
| diâmetro / área de saída | velocidade de saída → plume rise e downwash |
| curva vazão × pressão | permite o exaustor responder à contrapressão do vento |

### 7. Exaustores de emergência (2 un., disparam a 0,2 ppm)
Mesma folha de dados. **São cenário próprio**, não variação — mudam vazão *e* ponto de emissão.

### 8. PSVs
Cota exata (o ponto mais alto do prédio), diâmetro de saída, direção da descarga, pressão de
set e vazão de alívio. Se descarregam para chaminé ou direto para a atmosfera.

---

## 🟢 Geometria e contexto

### 9. Modelo 3D da planta — ✅ recebido em 15/10 (montagem completa, Solid Edge)
Veio a **planta inteira** (inclui guindastes e estacas). Critérios de limpeza em
`05_limpeza_CAD_criterios.md`. Para executar a limpeza, falta confirmar com o cliente:
- **onde está o prédio de O₃ e os 4 exaustores** dentro da montagem (nomes das ocorrências);
- se os **guindastes** são só de montagem (temporários) — esperado: sim, removê-los;
- **cota do solo acabado** (para cortar tudo que está abaixo);
- se possível, a **lista de peças (BOM)** exportada em Excel — acelera a classificação.

**19/10 — o `.x_t` enviado veio sem geometria** (só a árvore; modelo em coordenadas da planta, fora
do limite de 1 km do Parasolid). Mensagem sugerida ao cliente:

> Recebemos o modelo, obrigado. O arquivo .x_t chegou só com a estrutura da montagem, sem os
> sólidos — o modelo está em coordenadas da planta, muito longe da origem, e o formato Parasolid
> descarta a geometria nesse caso. Vocês conseguiriam exportar a partir do software de projeto
> (AVEVA/E3D ou o que gerou o Navisworks), em STEP ou Parasolid, **só a área do prédio de ozônio
> (1219) e as estruturas num raio de ~300 m**, **sem tubulação, internos e acessórios**, com a
> origem transladada para perto do prédio de ozônio (e nos informando o vetor de translação)?
> Também precisamos da **cota do piso acabado** e da confirmação de que os guindastes do modelo são
> temporários.

### 10. Onde estão as pessoas
Áreas ocupadas, passarelas, salas de controle e **tomadas de ar de HVAC**. O critério do
estudo é exposição humana; sem esse mapa, os contornos não viram recomendação.

### 11. Sensores existentes
Posição e tipo dos que já estão instalados. O entregável é "onde instalar" — melhor saber o
que já existe antes de recomendar.

---

## ⭐ Perguntas consolidadas — 20/10/2026 (antes de montar o CFD)

### Para o cliente (via Marcus)
**A. Fonte (bloqueia os cenários)**
1. Vazamento na alimentação dos misturadores (o caso da trinca): vazão de O₃ estimada [kg/h] — um valor típico e um
   pior caso — e a concentração de O₃ na corrente (% em massa em O₂).
2. Nesse vazamento, quais exaustores ligam (910/920, 930/940 ou todos), em quanto tempo e com que lógica
   (detector a 0,2 ppm?). Quais operam continuamente em operação normal?
3. As PSVs dos geradores (topo dos 1219-20-110/210/310): descarregam dentro do prédio ou para fora? Pressão de set e
   vazão de alívio.
4. Os desenhos CVC00P0015–P0018 (tabela de características técnicas) — para confirmar vazão e condição de operação
   dos ventiladores; e a densidade de projeto (0,90 × 1,01 kg/m³ nas curvas).

**B. Meteorologia e terreno**
5. Estação Zeus: o 0° de direção é o norte verdadeiro? Qual a altura do anemômetro? Qual o ângulo do norte de
   projeto da planta em relação ao norte verdadeiro?
6. Uso do solo no entorno (agrícola, mata, área urbana) e topografia num raio de ~1 km — imagem aérea ou mapa basta.

**C. Critérios e receptores**
7. Os limiares (3 · 0,5 · 0,2 ppm e 0,08 ppm da NR-15) são valores instantâneos ou médias numa janela de tempo?
8. Onde ficam as pessoas no entorno do prédio de O₃ (áreas ocupadas, passarelas, salas de controle) e as tomadas
   de ar de HVAC; posição e tipo dos sensores de O₃ já instalados.

**D. Geometria (confirmação)**
9. O prédio das prensas (mesa de concreto com as prensas na laje a ~11 m) é **aberto embaixo** ou tem **fechamento
   lateral** (paredes/telhas)? No modelo 3D recebido não há fechamento — pode faltar uma disciplina (arquitetura/
   fechamentos) na exportação. Se houver fechamento, até que altura e em quais faces?

### Para o Marcus (decisões internas)
1. **Domínio:** cilíndrico centrado no prédio de O₃ (uma malha para as 6 direções), raio ~600 m, altura ~350 m,
   bloqueio ~2,5 %. O COST pediria ~870 m a jusante (H ≈ 58 m das torres): ok seguir com ~600 m + teste de
   sensibilidade num cenário?
2. **Cenários 5–6 (vento fraco, estável, classe F):** modelar a estratificação (perfis de estabilidade + empuxo) ou
   rodar neutro com vento fraco e declarar a limitação? Muda prazo.
3. **Matriz final de cenários:** 6 ventos × combinações de exaustores. Com um escalar por exaustor, o campo de vento
   é rodado 6 vezes e as combinações saem por superposição — confirmar quais combinações reportar.
4. **Escopo:** estudo externo; o interior do prédio fica de fora (fonte = descargas). Confirmar com o cliente que não
   esperam posição de detectores internos.
5. **Prazo:** a geometria está pronta; a Etapa 1 estourou alguns dias por causa do CAD. Ajustar o cronograma?
6. Repositório: migrar o projeto para privado (L8)?

## Log de respostas

| data | item | resposta |
|---|---|---|
| — | — | *(aguardando)* |
- **15/10/2026** — CAD da planta inteira recebido (Solid Edge). Critérios de limpeza: `05`.
