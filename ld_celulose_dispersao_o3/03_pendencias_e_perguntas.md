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

### 9. Modelo 3D da planta
Na reunião apareceu um modelo 3D navegável (Navisworks). Se o cliente liberar, economiza a
Etapa 1 inteira. Precisamos do prédio de O₃ e de **todas as estruturas num raio de ~300 m**
(§6 do `02`) — as que ficam fora não afetam o campo próximo.

### 10. Onde estão as pessoas
Áreas ocupadas, passarelas, salas de controle e **tomadas de ar de HVAC**. O critério do
estudo é exposição humana; sem esse mapa, os contornos não viram recomendação.

### 11. Sensores existentes
Posição e tipo dos que já estão instalados. O entregável é "onde instalar" — melhor saber o
que já existe antes de recomendar.

---

## Log de respostas

| data | item | resposta |
|---|---|---|
| — | — | *(aguardando)* |
