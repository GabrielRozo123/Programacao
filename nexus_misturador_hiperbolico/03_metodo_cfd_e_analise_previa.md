# 03 — Método CFD e análise de envelope (antes de simular)

> Mesma lógica que funcionou no ciclone Valgroup e no tanque chiller da GreyLogix: **montar a régua
> analítica antes de rodar**, para saber se o resultado do CFD faz sentido e onde está o conflito real.

---

## 1. O conflito real do projeto

Os quatro critérios não têm o mesmo peso. Colocando-os na mesma escala:

| Critério | Empurra para | Custo |
|---|---|---|
| 2 — v ≥ 0,3 m/s no fundo | **mais** potência | — |
| 3 — potência ≤ 4,5 W/m³ | **menos** potência | — |
| 4 — sem vórtice | menos rotação / defletores | defletores custam potência |
| 1 — mistura completa | qualquer agitação razoável | pouco exigente aqui |

**O critério 1 provavelmente não é o que amarra.** Com tempo de residência de 1,13 h (68 min)
na vazão máxima e tempo de mistura esperado de ordem de minutos para um tanque de 48 m³ com
agitação contínua, a razão é de uma a duas ordens de grandeza — o reator se comporta como CSTR
com folga. O que realmente pode não fechar é **2 contra 3**.

> **Hipótese central do estudo (a confirmar no CFD):** existe uma janela viável de
> (diâmetro do hiperboloide, altura de instalação, rotação) que entrega 0,3 m/s no fundo
> dentro de 4,5 W/m³ — e ela deve ficar na **parte alta** da faixa de potência.

## 2. Escopo de potência e rotação — pré-dimensionamento

Usando a forma clássica de número de potência, `P = Np · ρ · N³ · D⁵`:

**[SUPOSTO]** `Np ≈ 0,4` e `D_hiperboloide = 1,6 m` (metade do diâmetro do tanque).
São valores de escopo — o `Np` real sai do torque na Etapa 2.

| | Potência | Rotação | Velocidade de ponta |
|---|---|---|---|
| Piso (1,3 W/m³ = 62,7 W) | 62,7 W | **14,8 rpm** | 1,24 m/s |
| Teto (4,5 W/m³ = 216,9 W) | 216,9 W | **22,3 rpm** | 1,87 m/s |

Três leituras:

- **A faixa de potência mapeia em 15–22 rpm**, bem na parte baixa dos 10–60 rpm informados
  pelo cliente. Quem amarra é a **potência**, não a rotação.
- Para atingir 0,3 m/s no fundo, a razão exigida entre velocidade no fundo e velocidade de ponta
  é de **0,24 no piso de potência** e **0,16 no teto**. A primeira é exigente; a segunda é plausível
  para um hiperboloide bem posicionado. **Reforça que a janela viável fica na parte alta da faixa.**
- Reynolds de agitação ≈ **9,5 × 10⁵** → plenamente turbulento, longe de qualquer efeito de
  transição. `Np` pode ser tratado como constante na faixa.

> ⚠️ Toda esta seção é **escopo de ordem de grandeza**, não previsão. Serve para saber se o
> CFD saiu num lugar razoável e para orientar os limites do DOE. `Np` para misturador
> hiperbólico não é bem estabelecido na literatura aberta.

## 3. ⭐ A recomendação de modelagem que muda o custo do DOE

As duas propostas dizem **"modelo multifásico Euleriano (líquido + flocos como fase dispersa)"**.
Vale reconsiderar, e a conta é curta.

**Tempo de relaxação do floco:**

```
τ_p = ρ_p · d² / (18 µ) = 1040 × (100e−6)² / (18 × 1e−3) = 5,8 × 10⁻⁴ s
```

**Tempo característico do escoamento:** D/v_ponta = 1,6 / 1,87 = 0,86 s

```
Stokes = τ_p / τ_f ≈ 7 × 10⁻⁴
```

**O floco acompanha a água praticamente sem escorregamento.** A física que importa aqui
**não é separação inercial** — é o equilíbrio entre **sedimentação** e **ressuspensão turbulenta**.

| Abordagem | Custo | Adequação |
|---|---|---|
| Euleriano completo (2 fases, 2 campos de velocidade) | alto | superdimensionado para St ≈ 7e−4 |
| **Mixture / drift-flux** (1 campo + escalar de sólidos com velocidade de deriva) | **~3× mais barato** | padrão da área de saneamento; captura sedimentação vs ressuspensão |

**Recomendação:** usar **drift-flux (mixture)** para o escalar de sólidos.
É o que a literatura de CFD de ETE usa, e é o que torna o **DOE da Etapa 3 viável** —
com Euleriano completo + VOF, cada ponto de projeto fica caro demais para varrer três variáveis.

**Sugestão de estratégia para o DOE (Opção A):**
1. **Triagem** — monofásico + MRF, sem VOF, com a velocidade no fundo e o torque como respostas.
   Barato, varre o espaço (diâmetro × altura × rotação) inteiro.
2. **Verificação** — só os finalistas rodam com drift-flux + VOF, que é onde os critérios 3 e 4
   de fato se decidem.

É a mesma lógica do estudo do ciclone: campo congelado para a varredura, física completa só nos
pontos que importam.

## 4. Velocidade de sedimentação — o número que define a ressuspensão

Por Stokes, para um floco isolado de 100 µm:

```
v_s = (ρ_p − ρ_f) · g · d² / (18 µ) = 40 × 9,81 × (100e−6)² / (18 × 1e−3) = 0,218 mm/s  (0,78 m/h)
```

Mas **lodo ativado não sedimenta como partícula isolada**: sedimenta em zona (hindered settling),
e a taxa vem do IVL, não do diâmetro. Com IVL de 50 a 170 mL/g e SST de 2,5 a 4,6 kg/m³,
a velocidade de sedimentação em zona é tipicamente **uma ordem de grandeza maior** que o Stokes acima.

**Consequência para a modelagem:** a velocidade de deriva do drift-flux deve vir de uma
**correlação de sedimentação em zona calibrada pelo IVL** (Vesilind ou Takács), não do Stokes.
É uma escolha de modelo a registrar e declarar no relatório.

> **[A CONFIRMAR]** com o Douglas: o IVL de projeto, e se há dado de velocidade de
> sedimentação medida. Pergunta 4 em `04_pendencias_e_perguntas.md`.

## 5. ⚠️ Um achado nos dados que vale levar ao cliente

Da planilha:
- **Entrada:** DN 100, **cota 6,3 m**
- **Altura útil (nível do líquido):** **6,0 m**
- **Saída:** DN 100, cota 6,0 m

A entrada está **30 cm acima do nível do líquido**. Isso é um **jato em queda livre**, e a conta:

| vazão | velocidade no DN 100 | velocidade de impacto (com a queda de 0,3 m) |
|---|---|---|
| 6,6 m³/h | 0,22 m/s | ~2,4 m/s |
| 42,6 m³/h | 1,44 m/s | ~2,8 m/s |

**Jato em queda com esse impacto arrasta ar para dentro do líquido.** E o critério 3 existe
justamente para evitar oxigênio no reator anóxico.

> **A pergunta que isso levanta:** a fonte dominante de aeração pode não ser o misturador —
> pode ser o arranjo da entrada. Se for o caso, otimizar o misturador para ficar abaixo de
> 4,5 W/m³ resolve o problema errado.

Além disso, **entrada e saída estão ambas no topo** (6,3 e 6,0 m), a poucos centímetros uma da
outra em cota. Isso é risco direto de **curto-circuito** — e explica por que o ensaio de DTR
entrou no escopo das duas propostas. Vale confirmar a **posição angular em planta** das duas
(pergunta 2): se estiverem próximas também em planta, o curto-circuito é quase certo e é um
achado independente do misturador.

## 6. Modelo numérico proposto (consolidado)

| Item | Escolha | Observação |
|---|---|---|
| Regime | Estacionário (MRF) na triagem; RBM transiente na verificação | conforme proposta |
| Turbulência | k-ε Realizable ou k-ω SST | **[A DEFINIR]** — SST resolve melhor a parede do fundo, que é onde o critério 2 é medido |
| Fase sólida | **Drift-flux (mixture)** com velocidade de deriva por Vesilind/Takács | ver §3 e §4 |
| Superfície livre | VOF, só nos casos finalistas | critérios 3 e 4 |
| Reologia | Newtoniano | adequado até ~5 kg/m³ de SST; **[A CONFIRMAR]** se há dado reológico |
| Potência | Torque no eixo × ω | de onde sai `Np` real |
| DTR | Escalar passivo com pulso na entrada | Etapa 4 |
| Malha | Estudo de independência na Etapa 1 | y+ compatível com o modelo de parede escolhido |
