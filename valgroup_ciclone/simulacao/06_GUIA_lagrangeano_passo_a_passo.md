# 06 — GUIA passo a passo do LAGRANGEANO (STAR-CCM+) — Ciclone Valgroup

> Escrito para quem está montando fase Lagrangeana pela primeira vez.
> Pré-requisito: **Etapa A encerrada** (gás + energia validados — ver `05_RESULTADOS.md`).

---

# PARTE 0 — O conceito (leia antes de clicar)

## 0.1 Euler × Lagrange
| | Euleriano | **Lagrangeano** |
|---|---|---|
| Como enxerga a fase | um **campo** (fração volumétrica em cada célula) | **partículas individuais** seguidas uma a uma |
| Equação | conservação numa malha fixa | 2ª lei de Newton por partícula: `m·dv/dt = ΣF` |
| Bom quando | fase dispersa **densa** (α > 10 %) | fase dispersa **diluída** ⭐ |

**No nosso caso:** α_sólido = **1,16e-4** (0,0116 %) → **diluído** → **Lagrangeano é o modelo certo**.
*(É por isso que DEM foi descartado: DEM resolve colisão partícula-partícula, que aqui é irrelevante.)*

## 0.2 A palavra mais importante: **PARCEL** (parcela)
O STAR **não** segue 10¹² partículas reais. Ele segue **parcelas** — cada parcela é um "pacote"
de N partículas idênticas (mesmo d, mesma velocidade, mesma posição) que viajam juntas.

```
você informa:  ṁ = 0,002778 kg/s  e  d = 10 µm
o STAR calcula: quantas partículas reais isso dá por segundo
                e distribui esse total entre as parcelas que ele lança
```

**Consequência prática:** o número de parcelas é **estatística**, não física. Poucas parcelas = η
com ruído. No nosso caso o `Part Injector` lança **1 parcela por face da boundary `Inlet`**
(≈ 340 faces com a malha atual) → **~340 parcelas por injetor**. É estatística suficiente.

## 0.3 Acoplamento (one-way × two-way)
| | o que faz | custo |
|---|---|---|
| **One-way** | o gás empurra a partícula. A partícula **não** afeta o gás. | barato ⚡ |
| **Two-way** | a partícula devolve quantidade de movimento (e calor) ao gás | caro, precisa iterar |

**Nossa razão de carga:** 80 kg/h de sólido ÷ 1820 kg/h de gás = **4,4 %** → efeito pequeno, mas real.

> 🎯 **Estratégia:** montar e validar em **ONE-WAY** (o campo de gás fica congelado, cada passada
> leva minutos). Só no fim ligar **Two-Way** e ver se a η se move. Se mover <2 %, one-way basta e
> você tem isso documentado como verificação.

---

# PARTE 1 — Preparar o arquivo (não perca o que já convergiu!)

1. `File → Save As…` → **`ciclone_100_energia_CONVERGIDO.sim`** ← guarda o que você já tem
2. `File → Save As…` → **`ciclone_100_lagrangeano.sim`** ← é neste que você vai trabalhar

> Nunca monte o Lagrangeano por cima do único arquivo convergido. Se algo der errado, você
> perde 9.500 iterações.

---

# PARTE 2 — Ativar o modelo

`Continua → Physics 1 → Models → botão direito → Select Models…`

Na caixa **Optional Models**, marque:
```
☑ Lagrangian Multiphase
```
Feche. Vai aparecer o nó **`Physics 1 → Models → Lagrangian Multiphase`**.

---

# PARTE 3 — Criar a fase e escolher os modelos dela

`Physics 1 → Models → Lagrangian Multiphase → Lagrangian Phases → botão direito → New`

Aparece `Phase 1`. **Renomeie para `char_010um`** (vamos usar uma fase por classe — explico na Parte 7).

`char_010um → Models → botão direito → Select Models…`

| Group Box | Marque | Por quê |
|---|---|---|
| **Particle Type** | **Material Particles** | traz junto *Spherical Particles* e *Pressure Gradient Force* |
| **Material** | **Solid** | é char sólido |
| **Equation of State** | **Constant Density** | |
| **Optional Particle Forces** | ☑ **Drag Force** | o arrasto do gás — é o que carrega a partícula |
| | ☑ **Gravity** ⚠️ | **não está no tutorial.** Sem ela a queda no cone sai errada |
| | ☑ **Turbulent Dispersion** ⚠️ | **não está no tutorial.** Sem ela os finos são captados demais |
| **Track Sampling** | ☑ Track File | para a cena de trajetórias depois |
| **Optional Models** | *(deixe Two-Way DESmarcado por ora)* | ver §0.3 |

> ⚠️ **Gravity precisa existir no continuum também.** Confira que `Physics 1 → Models` tem
> **`Gravity`** ativo e que `Reference Values → Gravity` = **(0, 0, −9,81)** — o eixo do ciclone é Z,
> e o cone aponta para −Z.

---

# PARTE 4 — Propriedades da partícula

`char_010um → Models → Solid → [nome do material] → Material Properties`

| Propriedade | **Valor** | Comentário |
|---|---|---|
| **Density → Constant** | **1500 kg/m³** | ⚠️ densidade da **PARTÍCULA**. Os **776,75** da planilha são **bulk** (com vazios entre grãos) — usar bulk **subestima a inércia** e joga a eficiência para baixo artificialmente |
| Specific Heat | 1000 J/kg·K | só importa se você quiser a troca térmica partícula–gás (opcional) |

`char_010um → Models → Drag Force`
- **Drag Coefficient Method = `Schiller-Naumann`**
  > Válido para Re_p < 1000. O nosso: **Re_p = 0,02 a 37** ✓ folgado.

---

# PARTE 5 — Condições de contorno **da fase** (≠ as do gás!)

`Regions → [sua região] → Boundaries → [cada boundary] → Physics Conditions → Lagrangian Specification`

Ou pelo caminho da fase: `char_010um → Boundary Conditions`

| Boundary | **Mode** | Significa |
|---|---|---|
| `Walls` | **Rebound** — Normal **0,8** · Tangencial **0,9** | a partícula quica e perde energia |
| **`outlet_dust`** | **Escape** ⭐ | **partícula que sai por aqui = CAPTURADA** |
| `Outlet_gas` | **Escape** | partícula que sai por aqui = **PERDIDA** (emissão) |
| `Inlet` | Escape | (não vai acontecer, o fluxo é de entrada) |

## 🚨 A confusão nº 1 dos iniciantes
**`outlet_dust` é `Wall` para o GÁS e `Escape` para a PARTÍCULA — ao mesmo tempo.**
Não é contradição: na planta existe uma **válvula rotativa (airlock)** ali. Ela é **selada para o gás**
(se virar Pressure Outlet, o gás foge pelo fundo, o vórtice não fecha e a eficiência sai errada)
mas **deixa o pó passar**. São duas configurações independentes, em nós diferentes da árvore.

## Sobre o coeficiente de restituição
O tutorial usa **1,0** = quique perfeitamente elástico → a partícula volta para o gás →
**subestima a captura**. Char contra aço fica em **0,7–0,9**. Vamos com **0,8/0,9** e depois
rodar **1,0** como teste de sensibilidade — a diferença entra no relatório como **incerteza declarada**.

---

# PARTE 6 — O injetor

`Injectors → botão direito → New` → renomeie para **`inj_010um`**

## 6.1 Aba principal do injetor
| Campo | Valor |
|---|---|
| **Type** | **Part Injector** |
| **Inputs / Part** | boundary **`Inlet`** |
| **Lagrangian Phase** | **`char_010um`** |

## 6.2 `inj_010um → Conditions`
| Campo | Valor |
|---|---|
| **Flow Rate Specification** | **Mass Flow Rate** |
| **Flow Rate Distribution Method** | **Per Injector** |
| **Velocity Specification Method** | **Magnitude + Direction** |
| **Particle Size Specification** | **Particle Diameter** (constante) |

## 6.3 `inj_010um → Values`
| Campo | **100 %** | **50 %** |
|---|---|---|
| **Particle Diameter** | **1,0e-5 m** | idem |
| **Mass Flow Rate** | **0,002778 kg/s** | **0,001389 kg/s** |
| **Velocity → Magnitude** | **15,23 m/s** | **7,62 m/s** |
| **Velocity → Direction** | **[0, −1, 0]** | idem |
| **Static Temperature** | **673,15 K** (400 °C) | idem |

> 📐 **Por que a direção é (0, −1, 0):** a boundary `Inlet` é a face retangular em **y = +435 mm**
> (bbox Y de −145 a +435). O duto tangencial entra no corpo caminhando no sentido de **Y decrescente**.
> Se você inverter o sinal, as partículas são injetadas **para fora do domínio** e somem na hora —
> sintoma clássico: "injetei e não apareceu nada".

> 💡 **Por que 0,002778 kg/s:** 80 kg/h ÷ 3600 = 0,02222 kg/s de particulado **total**, dividido
> pelas **8 classes** = 0,002778 kg/s cada. Assim cada classe carrega a mesma massa e a curva η×d
> sai bem amostrada.

---

# PARTE 7 — 🎯 Como separar a eficiência POR CLASSE (a parte que dá nó)

**O problema:** o report `Lagrangian Mass Flow` mede a massa que atravessa uma boundary **por FASE**,
não por injetor. Se você puser os 8 injetores na **mesma fase**, o report em `outlet_dust` te dá
**um número só** — a captura global — e você **perde a curva η×d**, que é o entregável.

## ✅ A solução: **uma FASE por classe de tamanho**

Depois de montar `char_010um` inteirinha e validada:

1. `Lagrangian Phases → char_010um → botão direito → Copy`
2. `Lagrangian Phases → botão direito → Paste` (8 vezes)
3. Renomeie: `char_001um`, `char_002um`, `char_005um`, `char_010um`, `char_020um`, `char_050um`, `char_075um`, `char_150um`
4. Idem para os injetores (copiar/colar) — em cada um mude **só** `Particle Diameter` e a `Lagrangian Phase` de destino

Assim **uma única rodada** te dá os 8 pontos da curva.

| Fase / Injetor | Particle Diameter |
|---|---|
| `char_001um` | 1,0e-6 m |
| `char_002um` | 2,0e-6 m |
| `char_005um` | 5,0e-6 m |
| `char_010um` | 1,0e-5 m |
| `char_020um` | 2,0e-5 m |
| `char_050um` | 5,0e-5 m |
| `char_075um` | 7,5e-5 m |
| `char_150um` | 1,5e-4 m |
| **soma** | ṁ total = **0,02222 kg/s = 80 kg/h** ✓ |

*(Alternativa, se copiar/colar fase der problema na sua versão: rode **uma classe por vez**, mudando
o diâmetro e anotando o η. Com one-way e campo congelado cada passada leva minutos. Dá o mesmo
resultado, só é mais manual.)*

---

# PARTE 8 — 🚨 O AJUSTE MAIS CRÍTICO: Maximum Residence Time

`Solvers → Lagrangian Multiphase → Steady → **Maximum Residence Time**`

| | valor |
|---|---|
| Default / tutorial | **0,1 s** |
| Residência do GÁS no nosso ciclone | **V/Q = 61,8 L ÷ 128,1 L/s = 0,48 s** |
| **NOSSO valor** | ⚠️ **10 s** |

**Por que isso destrói o resultado se ficar errado:** 0,1 s é **1/5 da residência do gás**. A partícula
seria **deletada pelo solver antes de chegar ao fundo** — e o STAR **não avisa**. Você obteria uma
eficiência artificialmente baixa e nada indicaria erro. É a armadilha silenciosa clássica.

E as partículas ficam **muito mais tempo** que o gás: elas descem em espiral pela parede, quicam,
e as finas ficam presas em recirculações. **10 s ≈ 21× a residência do gás** é folga honesta.

### ✔️ Verificação obrigatória depois de rodar
Confira quantas parcelas terminaram por **limite de tempo** (aparece no log do solver / report de
parcelas). **Se for mais que uns poucos %, aumente o Maximum Residence Time e rode de novo.**

---

# PARTE 9 — Reports, monitores e a curva

Para **cada fase**, crie **dois** reports:

`Reports → botão direito → New Report → Lagrangian Mass Flow`

| Report | Parts | Phase |
|---|---|---|
| `mdot_dust_010um` | boundary **`outlet_dust`** | `char_010um` |
| `mdot_gas_010um` | boundary **`Outlet_gas`** | `char_010um` |

```
η(d) = ṁ(outlet_dust) / ṁ(injetado)          ← a eficiência da classe
```

### Balanço de massa das parcelas (a checagem de sanidade)
```
ṁ(outlet_dust) + ṁ(Outlet_gas)  ≈  ṁ(injetado) = 0,002778 kg/s
```
Se **não fechar**, é porque parcelas estão sendo **deletadas** (Maximum Residence Time curto — Parte 8)
ou injetadas na direção errada (Parte 6.3). **Não interprete η nenhum antes de esse balanço fechar.**

---

# PARTE 10 — Rodar, na ordem certa

## Passo 1 — validação com UMA classe (não monte as 8 antes disso)
Monte só a fase **`char_050um`** (d = 5,0e-5 m) e rode.

| | esperado |
|---|---|
| **η(50 µm)** | **> 95 %** — 50 µm é ~6,5× o diâmetro de corte, tem que ser captado |
| Balanço de massa | fecha em ±2 % |
| Parcelas mortas por tempo | ~0 % |

> ❌ **Se η(50 µm) NÃO for alta, PARE.** Tem erro de setup. Reveja, nesta ordem:
> (1) `outlet_dust` está **Escape** para a fase? (2) direção do injetor é (0,−1,0)?
> (3) Maximum Residence Time é 10 s? (4) densidade é 1500 e não 776,75?
> Não adianta montar 8 classes por cima de um setup errado.

## Passo 2 — a classe difícil
Troque para **`char_010um`** (10 µm ≈ o diâmetro de corte). Espere **η intermediária, na faixa de 55–70 %**.
Se der ~0 % ou ~100 %, algo está errado (o corte não pode ser um degrau).

## Passo 3 — produção
Só então crie as 8 fases (Parte 7), rode, e plote **η × d** — **o entregável principal**.

## Passo 4 — Two-Way Coupling
`char_XXX → Models → Select Models → ☑ Two-Way Coupling`, rode de novo, compare.
Se a η mexer <2 %, registre: *"acoplamento bidirecional verificado, efeito desprezível"*. Isso é
uma verificação a favor do relatório, não um retrabalho.

## Passo 5 — repetir a 50 % (v_i = 7,62 m/s, ṁ = 0,001389 kg/s por classe)

---

# PARTE 11 — 📊 As previsões (para você comparar e saber se está certo)

Diâmetro de corte analítico, **com ρ_p = 1500** (o valor que estamos usando no CFD):

| | d* (corte) |
|---|---|
| **100 %** (v_i = 15,23 m/s) | **≈ 7,6 µm** |
| **50 %** (v_i = 7,62 m/s) | **≈ 10,8 µm** |

Eficiência por classe pelo modelo de Lapple `η = 1/(1 + (d*/d)²)`:

| d (µm) | **η @ 100 %** | **η @ 50 %** |
|---|---|---|
| 1 | 1,7 % | 0,9 % |
| 2 | 6,5 % | 3,3 % |
| 5 | 30 % | 18 % |
| **10** | **63 %** | **46 %** |
| 20 | 87 % | 77 % |
| **50** | **98 %** | **96 %** |
| 75 | 99,0 % | 98,0 % |
| 150 | 99,7 % | 99,5 % |

> ⚠️ **Não espere bater exatamente.** Lapple é um modelo de 1951 com "número de voltas efetivas"
> tabelado — o CFD é que é a resposta. O que interessa é: **a curva do CFD tem que ter a mesma
> FORMA e o joelho na mesma região (5–15 µm)**. Se o CFD der o corte em 1 µm ou em 80 µm, é setup errado.
>
> Espera-se que o **CFD dê η um pouco MENOR que Lapple nos finos** — porque o CFD tem
> **Turbulent Dispersion**, que joga finos de volta para o núcleo. Isso é físico e desejável.

---

# PARTE 12 — Cena de trajetórias (para a apresentação)

1. `Scenes → New Scene → Geometry`
2. Superfície do corpo → **Opacity 0,3** (para ver por dentro)
3. `Displayers → botão direito → New Displayer → **Particle Tracks**`
4. `Parts` = as fases Lagrangeanas · `Scalar Field` = **Particle Diameter** (ou Velocity Magnitude)
5. Rodar como animação → mostra as grossas descendo em espiral pela parede e as finas escapando
   pelo vortex finder

> É a imagem que **explica a eficiência para o cliente sem uma equação**. Vale ouro na apresentação
> à Valgroup — lado a lado com a curva η×d.

---

# 📌 Resumo — as 5 armadilhas deste caso
1. **`outlet_dust` como outlet para o gás** → o gás foge pelo fundo. **Wall p/ gás + Escape p/ partícula.**
2. **Maximum Residence Time curto** → partícula deletada antes de ser capturada, **sem aviso**. **10 s.**
3. **ρ_s = 776,75 (bulk)** → subestima a inércia. **Use 1500 (partícula).**
4. **Sem Turbulent Dispersion** → finos captados demais. **Ligar.**
5. **`Ideal Gas` sem `Molecular Weight`** → o STAR usa o default do ar. **M = 184 kg/kmol.**

---

# PARTE 13 — Distribuição de tamanho (Rosin-Rammler) × classes monodispersas

O STAR oferece, no injetor, `Conditions → Particle Size Specification`, a opção de injetar uma
**distribuição** em vez de um diâmetro fixo — a **Rosin-Rammler** é a mais usada
(`R(d) = exp(−(d/d′)ⁿ)` = fração mássica **acima** de d; parâmetros: *Reference Size* d′ e *Exponent* n).

## ❌ Para o NOSSO entregável, NÃO usar distribuição. Três motivos.

**1. Você perderia justamente a curva.**
O report `Lagrangian Mass Flow` integra **por fase**. Injetando uma distribuição numa fase, o
`outlet_dust` devolve **um número só** — a captura global. A curva **η × d** simplesmente não existe
nesse resultado. E a curva é o entregável.

**2. η(d) é propriedade do CICLONE; η_global é propriedade da ALIMENTAÇÃO.**
A curva de grade depende só de geometria + escoamento. Medida uma vez, serve para **qualquer** PSD:
```
η_global = Σ fᵢ · η(dᵢ)        ← conta de planilha, segundos
```
Com a distribuição embutida no CFD, cada PSD nova = **uma rodada nova**.

**3. 🚨 O motivo decisivo: a nossa PSD é INCERTA.**
A amostra que a Valgroup mandou é do char **extraído (fundo)** — 28 % dela é **>1 mm**, que
fisicamente **não pode** ser arrastada a 1,03 m/s (v_terminal 1,3–13,4 m/s). O que temos é uma
**estimativa** (reponderação pelo corte de arraste ~346 µm).
> Embutir uma PSD estimada dentro do CFD **contamina um resultado sólido com um input frágil**.
> Mantendo separado: a incerteza fica **isolada numa linha de planilha**, e quando a PSD real
> chegar, a resposta se atualiza **sem CFD nenhum**.

## ✅ Quando a distribuição É útil (depois, não agora)
1. **Rodada de confirmação:** injetar a PSD real e verificar que η_global(CFD) ≈ Σfᵢ·η(dᵢ).
   Valida a própria convolução.
2. **Cena de trajetórias para o cliente:** uma nuvem com dispersão realista de tamanhos.
3. **Erosão:** o desgaste é dominado pela cauda grossa, que a distribuição amostra naturalmente.

## 📐 Se/quando for usar: os parâmetros da nossa PSD estimada
Ajuste Rosin-Rammler sobre a estimativa do char arrastado
(150–425 µm → 35,8 % · 75–150 → 51,2 % · 20–75 → 13,1 %):

| Campo no STAR | Valor |
|---|---|
| **Reference Size (d′)** | **1,486e-4 m** (148,6 µm) |
| **Exponent (n)** | **2,88** |

## ⚠️ E a leitura que esses números já entregam
Convoluindo com Lapple: **η_global ≈ 99,3 % @100 %** e **98,6 % @50 %** (emissão 0,54 e 1,15 kg/h).

Parece ótimo — **e é exatamente por isso que é preciso desconfiar**: toda a PSD estimada está
**acima de 20 µm**, ou seja, **muito acima do corte de 7,6 µm**. O ciclone captura tudo isso com
folga, e o número global fica **insensível à física** que estamos simulando.
**Toda a ação da curva está ABAIXO de 20 µm — exatamente onde não há dado amostrado.**

> ➜ **Entregar a CURVA η(d) como resultado** (robusta) e a **η_global como cenário declarado**
> (frágil, depende da PSD). E manter a pendência aberta com a Valgroup:
> **PSD amostrada NA CORRENTE GASOSA**, não no char extraído.

*(Script: `dimensionamento/convolucao_eficiencia.py` — troca a PSD e recalcula.)*

---

# PARTE 14 — Relatórios e cenas (o que medir e o que mostrar)

## 14.1 Os QUATRO reports por classe (não dois)

`Reports → botão direito → New Report`

| # | Tipo | Nome | Configuração |
|---|---|---|---|
| 1 | **Lagrangian Mass Flow** | `mdot_dust_050` | Parts = **`outlet_dust`** · Phase = `char_050um` |
| 2 | **Lagrangian Mass Flow** | `mdot_gas_050` | Parts = **`Outlet_gas`** · Phase = `char_050um` |
| 3 | **Expression** | **`eta_050`** | `abs(${mdot_dust_050}) / 2.7778e-3` |
| 4 | **Expression** | **`balanco_050`** | `(abs(${mdot_dust_050}) + abs(${mdot_gas_050})) / 2.7778e-3` |

### ⚠️ O `abs()` não é preciosismo — é o erro nº 1 aqui
O `Lagrangian Mass Flow` é assinado pela **normal da boundary**. Dependendo da orientação, a massa
**saindo** aparece **negativa**. Se você dividir sem `abs()`, obtém uma eficiência **negativa** e
acha que quebrou tudo — quando o resultado estava certo.
> **Antes de montar as expressões:** rode e olhe os dois reports crus. Anote o sinal de cada um.
> Se ambos vierem negativos, o `abs()` resolve. Se vierem com **sinais opostos**, PARE — significa
> que uma das boundaries está deixando partícula **entrar**, e aí há erro de BC.

### O `balanco_050` é o seu detector de fraude
```
balanco_050 = 1,00  → toda a massa injetada foi contabilizada ✅
balanco_050 < 1,00  → há parcela SUMINDO
```
**Massa que some = parcela deletada** (Maximum Residence Time curto) **ou ainda em voo**
(não convergiu). Nos dois casos o `eta` está **subestimado**.

> 🚨 **Regra:** não interprete `eta` nenhum enquanto `balanco` não estiver em **0,98–1,02**.
> Um η de 60% com balanço de 0,70 não quer dizer "60% de eficiência" — quer dizer que 30% da massa
> evaporou do modelo.

## 14.2 Monitores
Em **cada** um dos 4 reports: botão direito → **`Create Monitor and Plot from Report`**.

O que você quer ver: `eta_050` **estabilizando num platô**, igual ao ΔP estabilizou. Se ele ainda
sobe no fim da rodada, faltam iterações (ou parcelas ainda em voo).

## 14.3 Cena de trajetórias

1. `Scenes → New Scene → **Geometry**`
2. Superfície do corpo → `Opacity` = **0,3** (para enxergar por dentro)
3. `Displayers → botão direito → New Displayer → **Particle Tracks**`
4. `Parts` = a fase `char_050um` (ou o track file gerado)
5. `Scalar Field` → escolha conforme a mensagem:

| Colorir por | O que isso mostra |
|---|---|
| **Particle Diameter** | ⭐ a separação por tamanho — grossas na parede, finas no núcleo |
| **Residence Time** | quem fica preso em recirculação (as vermelhas são as problemáticas) |
| Velocity Magnitude | o campo de aceleração no vórtice |

> Se a lista de `Parts` vier **vazia**: o `Track File` não estava marcado nos modelos da fase quando
> você rodou. Remarque e rode de novo — as trajetórias não são recuperáveis a posteriori.

### 🎯 A imagem que vende o resultado
Duas classes na **mesma cena**: **50 µm** (desce em espiral colada na parede até o `outlet_dust`) e
**5 µm** (sobe pelo vortex finder e escapa). Lado a lado, isso **explica a curva de eficiência sem
uma única equação** — vale mais que qualquer slide de texto na apresentação à Valgroup.

## 14.4 O gráfico final η × d
Não vale a pena montar no STAR (são 8 fases, cada uma com o seu report). Colete os 8 valores de
`eta` e plote fora — eixo **d em escala log**, η linear, as duas cargas (100% e 50%) sobrepostas,
e a **curva de Lapple tracejada** por trás para comparação.
> Esse gráfico **é** o entregável principal do estudo.

---

# PARTE 15 — ⚠️ CORREÇÃO: o método OFICIAL da Siemens para a eficiência

> Fonte: Siemens KB **KB000033060** ("How can I calculate the efficiency in a Lagrangian Cyclone
> Separator?") e **KB000040310** ("Best Practices for Cyclone Separators").

## 15.1 O erro do meu método (Parte 14)
Eu mandei medir a captura com **`Lagrangian Mass Flow`** na boundary `outlet_dust`.
**A Siemens não usa esse report para o fundo — e por um motivo estrutural:**
`outlet_dust` é uma **WALL**. Report de vazão mede fluxo **atravessando** uma superfície, e por uma
parede não atravessa nada. A massa é removida pelo *Escape* da fase, não por fluxo.

## 15.2 O método oficial
1. Criar uma **Field Function** (User Field Function):
```
$IncidentMassFluxPhase1 * mag($$Area)
```
   `Incident Mass Flux of Phase` = fluxo de massa de partículas **incidindo** na face (kg/m²·s);
   `mag($$Area)` = área da face → o produto dá **kg/s por face**.
   *(Ajustar o nome da fase: `...Phase1` → o índice da nossa `char_050um`.)*

2. Criar um report **`Sum`** (não Lagrangian Mass Flow!) dessa field function,
   com **Parts = boundary `outlet_dust`** → esse é o **MFR_bottom**.

3. Eficiência por **Expression Report**:
```
η = 1 − (MFR_inlet − MFR_bottom) / MFR_inlet        ( = MFR_bottom / MFR_inlet )
```
   com **MFR_inlet = 0,0027778 kg/s** (o que injetamos).

4. ⚠️ **Ativar `Boundary Sampling`** nos modelos da fase — a KB diz explicitamente que é o que
   salva *"information at the boundaries"*. Eu tinha dito que não precisava. **Precisa.**

## 15.3 Balanço de massa (também da KB)
Field function **`injectedmass`** → report **`sumInjectedMass`** (Field Sum) → **Total Injected Mass**
= valor **Max** do field sum. E no `Outlet_gas`, um Field Sum de `Incident Mass Flux` mede a emissão.
Fecha o balanço com instrumentos do mesmo tipo nas duas pontas (melhor que misturar report de fluxo
com report de incidência).

---

# PARTE 16 — O que as Best Practices da Siemens confirmam e o que contrariam

## ✅ Confirmam o que fizemos
| Prática Siemens | Nosso caso |
|---|---|
| *"run a steady state solution first to get a stable flow field prior to Lagrangian injection"* | ✅ exatamente a nossa Etapa A |
| Refinar a **região central** (núcleo do vórtice precessante) | ✅ nosso volumetric control cilíndrico |
| **Mass Flow / Pressure Outlet** como BCs recomendadas | ✅ |
| LMP em vez de **DEM** quando α < 10 % | ✅ nosso α = 1,16e-4 |
| *"k-omega with curvature correction may be sufficient for simpler cases"* | ✅ sanciona o nosso caminho K-ω SST + CC |
| Critério de parada extra por velocidade **tangencial** estável | ⏳ vale adicionar |

## ⚠️ Contrariam / apontam melhoria
| Prática Siemens | Nós fizemos | Peso |
|---|---|---|
| **Trimmed mesher (hexaédrico)** — *"the best type of mesh for cyclones"*, células alinhadas ao escoamento, **minimiza difusão numérica** | **Polyhedral** (Surface Remesher + Polyhedral) | ⚠️ real, mas a nossa malha já validou ΔP em 1,2 % — não invalida, entra como **melhoria futura / teste de malha** |
| **RST (Reynolds Stress Transport)** com **Elliptic Blending** é *"most appropriate"*; modelos isotrópicos *"over predict turbulent viscosity and exaggerate the forced vortex"* | K-ω SST | ⚠️ já estava no plano (item 7). A KB **nomeia a variante**: **Elliptic Blending**, não o RST clássico |
| **Injeção Lagrangeana no TRANSIENTE** (*"prior to transient / Lagrangian injection"*, *"before running the unsteady simulation"*) | Lagrangeano **steady** | ⚠️ ver §16.1 |

## 16.1 Steady × transiente para o Lagrangeano — a decisão
A Siemens enquadra o ciclone Lagrangeano como **transiente**. O nosso steady com campo congelado é
uma primeira passada **legítima** (é o padrão da literatura para levantar curva de grade, e é ~50×
mais barato), **mas** ele não vê o **PVC** (vórtice precessante), que é justamente o que mexe nos
finos.

> **Plano:** levantar a curva η×d no **steady** (barato, 8 classes, tendência confiável) e depois
> **reproduzir 2 ou 3 classes no transiente** (5 µm, 10 µm, 50 µm). Se o η dos finos mudar muito,
> a curva final vai para o transiente. Isso transforma o custo em **verificação declarada** em vez
> de uma escolha não justificada.

---

# PARTE 17 — 🔴 CASO REAL: a armadilha nº1 aconteceu (e o que ela produz)

**Sintoma:** η(50 µm) ≈ **1 %** (deveria ser >95 %). Balanço de massa **fechando** em 0,983.
Trajetórias formando uma **panqueca no cilindro superior**, sem descer o cone.

**Diagnóstico:** `Regions → Ciclone → Boundaries → outlet_dust → Properties → **Type = Outlet**`.
Tinha de ser **`Wall`**.

## O mecanismo — e é o CONTRÁRIO do que se imagina
A intuição diz "se o fundo está aberto, o gás sai por baixo e leva o pó junto → η alta".
**Errado.** O ápice do cone fica **na zona do núcleo de baixa pressão** do vórtice
(a nossa própria cena de Total Pressure mostra mínimo de **−239 Pa**).

Um Pressure Outlet a **0 Pa** naquele ponto não deixa o gás sair — **faz o ambiente EMPURRAR gás
para dentro**:

| Gradiente no ápice | Jato **entrando** | Vazão parasita |
|---|---|---|
| 50 Pa | **5,0 m/s** | 168 m³/h |
| 100 Pa | **7,1 m/s** | 238 m³/h |
| 239 Pa | **11,0 m/s** | 368 m³/h |

E a velocidade de queda de uma partícula de 50 µm é **21,5 mm/s**.

> **Razão jato/queda ≈ 330×.** O jato ascendente parasita **aniquila** a sedimentação: a partícula
> chega ao cone, é soprada de volta para cima e sai pelo vortex finder.
> **É exatamente isso que a panqueca de trajetórias mostra** — elas não *escolhem* ficar no topo,
> elas **não conseguem descer**.

## Por que o balanço de massa fecha e engana
`balanco = 0,983` ✅ — porque **nenhuma massa foi perdida**: toda ela saiu, só que **pela porta
errada**. O balanço detecta parcela deletada, **não** detecta física errada.
> **Lição:** balanço fechado é condição **necessária**, não suficiente. Confira também se o
> **resultado é fisicamente possível** — 50 µm escapando 97 % num Stairmand não é.

## A correção e a verificação
1. `outlet_dust → Type` = **`Wall`**
2. `outlet_dust → Phase Conditions → char_050um → Mode` = **`Escape`** *(esse já estava certo)*
3. **Reconvergir o gás** — a BC mudou, o campo atual não vale. `ΔP tem de voltar a ~2.894 Pa.`
4. ⚠️ **Verificar a Etapa A:** se o ΔP com `Wall` **não** voltar aos 2.894 Pa, então os resultados
   da Etapa A foram obtidos com `Outlet` e precisam ser refeitos. Se voltar, a Etapa A está de pé.
5. Rodar 1 iteração Lagrangeana. **η(50 µm) esperado: 95–99 %.**

---

# PARTE 18 — 📖 O que a documentação oficial resolve (4 páginas do User Guide)

> Fontes: *Boundary Interaction Modes Reference* · *Setting a Phase Impermeable Boundary* ·
> *Solution Methodology* · *Particle Injection* (STAR-CCM+ 21.02 User Guide).

## 18.1 ❌ `Phase Impermeable` no `Outlet_gas` — REVERTER

**O que `Phase Impermeable` faz** (citação):
> *"particles **do not pass through** the boundary; instead they interact with the boundary **as if it
> were a wall**. Fluid in the continuous phase continues to pass through as normal."*

Ou seja: o gás sai, **a partícula bate numa parede**. É o oposto do que queremos na saída de gás.

**E não é necessário.** A tabela oficial de modos:

| Boundary Type | Material Particle Interaction Modes |
|---|---|
| **Pressure Outlet** | **Escape** *(único — automático)* |
| Velocity Inlet / Mass Flow Inlet / Outlet | Escape *(único)* |
| **Wall** | Bai-Gosman · Bai-ONERA · Composite · **Escape** · Ice Accretion · **Rebound\*** · Satoh · Splash · Stick · VOF/MMP Conversion |
| **Phase Impermeable** | Bai-Gosman · Bai-ONERA · Composite · **Escape** · **Rebound\*** · Satoh · Splash · Stick · Vaporize |

`*` = **default**

> **`Pressure Outlet` já tem Escape como único modo possível** — não existe nada para configurar,
> a partícula sai sozinha. Não há motivo para tornar a fronteira impermeável.
>
> 🚨 **E o risco é concreto:** o default do `Phase Impermeable` é **Rebound**. Se o Mode reverter
> (ou você esquecer de setar), as partículas **quicam de volta para dentro do ciclone** na saída de
> gás, nunca são contadas como emissão, e a **η fica artificialmente ALTA**. Erro na direção
> otimista — o pior tipo, porque o resultado "parece bom".

**Ação:** `Outlet_gas → Phase Conditions → char_050um → Type` = **de volta ao default** (permeável).

## 18.2 ✅ `outlet_dust` = Wall + Mode **Escape** — confirmado, mas ATENÇÃO ao default
A tabela mostra que `Wall` **aceita** Escape ✅ — mas o **default de Wall é Rebound**.
> **Escape em `outlet_dust` tem de ser setado à mão, sempre.** Se ficar no default, o pó quica no
> fundo e volta para o vórtice → **η artificialmente baixa**.

## 18.3 ✅ Para que serve o `Lagrangian Specification` (a dúvida que ficou aberta)
> *"Select the `Physics Conditions > Lagrangian Specification` node of the parent boundary and set
> **Method to `Specify for Boundary`**. The Physics Conditions and Physics Values manager nodes
> appear beneath the impermeable boundary node for the phase."*

É o **interruptor que expõe as opções por-boundary**. Sem `Specify for Boundary`, a boundary herda
a configuração da fase.

## 18.4 ✅ O MARCUS ESTÁ CERTO — e aqui está a citação

**Steady Procedure**, textual:
> *"The procedure in each iteration is: **Deactivate the Lagrangian Multiphase solution.** Generate the
> Lagrangian Multiphase solution by time-marching each parcel **until it has left the computational
> domain**, or has been removed, or until the user-specified maximum residence time is reached."*

**Cada iteração JOGA FORA a solução Lagrangeana anterior e a regenera do zero, do nascimento ao
Escape.** Não há acumulação entre iterações → **1 iteração após o campo convergir = a resposta
completa.** Exatamente o que o Marcus disse.

Dois detalhes que vêm de brinde:
1. *"These two steps are executed in each iteration of the steady solver, **before the flow solver**."*
   → o Lagrangeano de uma iteração usa o campo da **anterior**. Com campo convergido, indiferente.
2. *"the steady solution consists of Tracks... Cell fields... **Boundary fields such as incident mass
   flux**."* → **`Incident Mass Flux` é literalmente a solução steady do modelo.** Confirma que o
   método da KB (Parte 15) é o instrumento correto, e não uma gambiarra.

## 18.5 ⚠️ CORREÇÃO: o que `Parcel Streams` realmente é

Eu descrevi como "quantas parcelas por face". **A definição oficial é outra:**
> *"STAR-CCM+ generates parcel sizes by **dividing the distribution into ranges of equal mass**,
> volume, or number. **The number of ranges IS the number of parcel streams** for the injector."*
> *"Each parcel represents **a statistical sample**, one sample per parcel."*

| Caso | Parcel Streams |
|---|---|
| **`Particle Diameter = Constant`** (o nosso agora) | **1 basta** — só existe um tamanho para amostrar |
| **Distribuição** (Rosin-Rammler / Table CDF) | 🚨 **é a DISCRETIZAÇÃO da distribuição** |

> 🚨 **Armadilha nº6 (para a rodada de confirmação):** com uma distribuição e `Parcel Streams = 1`,
> o STAR divide a PSD em **UMA faixa** → você injeta **um tamanho só** e acha que injetou a
> distribuição. Use **20–50 streams** quando a PSD entrar.

## 18.6 📐 A CDF na forma que o STAR espera (para a rodada de confirmação)
> *"When the **mass flow rate** is specified, the CDF gives the fraction of the mass flow rate of the
> injector with a size **smaller** than d."*

⚠️ **UNDERSIZE.** A nossa Rosin-Rammler R(d) era **oversize** → a tabela precisa de **F = 1 − R**.
*(A RR do STAR é a forma Weibull `F(d)=1−exp(−(d/d′)ⁿ)`, então **d′=1,486e-4 m e n=2,88 servem
direto** — o cuidado é só com a tabela manual.)*

**Tabela pronta (dados brutos da PSD estimada, sem ajuste):**

| d [m] | CDF (massa undersize) |
|---|---|
| 2,00e-5 | 0,000 |
| 7,50e-5 | 0,131 |
| 1,50e-4 | 0,643 |
| 4,25e-4 | 1,000 |

*(A doc exige valores **estritamente crescentes** — sem duplicatas.)*

## 18.7 Nota sobre Two-Way Coupling (quando ligarmos)
> *"Two-way coupling assumes that the fluid cell volume is large compared to the particle size...
> a **two-grid procedure** clusters groups of contiguous cells."*

Nosso caso: célula ~5 mm × partícula 50 µm = razão **100:1 linear (10⁶ em volume)** → a hipótese
vale com folga enorme. **Não precisamos do two-grid.**

---

# PARTE 19 — 🔑 `Track File` × `Boundary Sampling`: são coisas DIFERENTES

> Este foi o bloqueio real para ler a eficiência. Fonte: blog VOLUPE (parceiro Siemens) +
> KB000040310. Explica também por que o report no `Outlet_gas` funcionava e o do `outlet_dust` não.

## 19.1 As duas opções de `Track Sampling` fazem coisas opostas

| | **Track File** | **Boundary Sampling** |
|---|---|---|
| O que grava | a **trajetória inteira** de cada parcela | o que acontece **quando a parcela toca uma boundary** |
| Onde vive | **arquivo em disco** | **na memória, durante a rodada** |
| Para que serve | **visualização** (cena de trajetórias) | **reports e monitores** ⭐ |
| Precisa salvar/carregar? | **sim** | **não** |

Citação (VOLUPE):
> *"Boundary sampling is a way of tracking Lagrangian parcels and their interaction with specific
> boundaries and can be used as an **alternative to using track files**. Contrary to using track files,
> the boundary sampling function allows you to **monitor the progression of particle properties as
> your simulation is running without having to save the simulation or loading track files**."*

> 🚨 **O `Track File` NÃO alimenta report nenhum.** Ele é um arquivo de desenho. O objeto
> `Particle Tracks` da árvore é um **leitor** desse arquivo — por isso clicar nele só redesenha
> linhas e nunca mexe num número.

## 19.2 Isso explica TODO o comportamento estranho que vimos

| Report | Boundary | Funcionou? | Por quê |
|---|---|---|---|
| `mdot_gas_050` | `Outlet_gas` (**Pressure Outlet** = fronteira de escoamento) | ✅ platô limpo em 0,0027 | há **fluxo atravessando**; o report de vazão mede isso nativamente |
| `mdot_dust_050` | `outlet_dust` (**Wall**) | ❌ ruído entre 0 e 1,2e-4 | por uma parede **não atravessa fluxo**. O dado de partícula na parede só existe **se Boundary Sampling estiver ligado** |

**Não era bug nem sorte: eram dois instrumentos diferentes, um deles desligado.**

## 19.3 A correção
1. `char_050um → Models → Select Models…` → **☑ `Boundary Sampling`**
   *(fica no group box `Track Sampling`, ao lado do `Track File` — pode deixar os dois ligados)*
2. Aparece um nó **`Boundary Sampling`** sob os modelos da fase → **selecionar as boundaries a
   amostrar**: `outlet_dust` ⭐ e `Outlet_gas`.
3. Agora o field function **`Incident Mass Flux of Phase`** tem dado nessas faces.
4. Criar a Field Function e o report **`Sum`** conforme a KB (Parte 15):
```
   User Field Function:  $IncidentMassFluxPhase1 * mag($$Area)      [kg/s por face]
   Report:  Sum  ·  Parts = outlet_dust                            = MFR_bottom
   η = MFR_bottom / 0,0027778
```
5. **`Step` ×1** (com Flow/Energy/Turbulence congelados) → o report tem valor.

## 19.4 A frase da Best Practices que já dizia isso
> *"By enabling **the particle tracks AND boundary sampling** the trajectory of particles in the domain
> **and information at the boundaries** would be saved."*

São **dois** itens para **duas** finalidades. Ligar só o Track File dá **trajetória sem número**.

## 19.5 📌 Armadilha nº7
**`Track File` ligado e `Boundary Sampling` desligado** → você enxerga as partículas, a cena fica
linda, e **nenhum report de captura funciona**. O sintoma é exatamente "vejo a trajetória mas não
consigo ler a eficiência".

---

# PARTE 20 — 🚨 O OUTRO limite de parada: `Maximum Sub-Steps`

> `Maximum Residence Time` **não é o único** critério que mata uma parcela. No mesmo painel
> (`Solvers → Lagrangian Multiphase → Steady`) existe **`Maximum Sub-Steps`**, default **20.000**.

## 20.1 Por que 20.000 sub-passos podem valer só 0,1 s de voo
A parcela é integrada com um **sub-passo LOCAL**, limitado pelo Courant **da célula em que ela está**:
```
dt = C · dx / v          tempo total de voo = N_sub_steps × dt
```

| célula dx | dt (C≈0,5, v=17 m/s) | voo com 20.000 sub-steps |
|---|---|---|
| 5,0 mm (núcleo) | 1,5e-4 s | 2,94 s |
| 1,0 mm | 2,9e-5 s | 0,59 s |
| 0,5 mm | 1,5e-5 s | 0,29 s |
| **0,2 mm** (prism layer) | 5,9e-6 s | **0,118 s** ⬅️ |
| 0,1 mm | 2,9e-6 s | 0,059 s |

**E é justamente aí que a nossa partícula viaja.** O tempo de relaxação da partícula de 50 µm é
**τ_p = 2,2 ms** — ela é jogada contra a parede quase instantaneamente e desce **dentro da camada de
prismas**, onde as células são finíssimas. O sub-passo despenca e os 20.000 acabam em ~0,1 s.

**Sintoma observado:** trajetórias param **no meio do ar** após ~2 voltas (≈0,107 s de arco),
sem tocar boundary nenhuma → bate com célula de 0,1–0,2 mm.

## 20.2 ⚠️ Por que isso engana mais que o Maximum Residence Time
São **dois critérios independentes**, e configurar um **não protege** contra o outro:

| Critério | Unidade | Intuitivo? |
|---|---|---|
| `Maximum Residence Time` | **segundos** | ✅ dá para estimar (residência do gás × N) |
| **`Maximum Sub-Steps`** | **contagem** | ❌ o tempo que ele compra **depende da malha** |

> Você pode setar 10 s corretamente e ainda assim a parcela morrer em 0,1 s — porque quem manda é
> o **produto** `N × dt`, e o `dt` é escolhido pelo solver célula a célula. **Refinar a malha
> ENCURTA o voo** para o mesmo `Maximum Sub-Steps`. É uma armadilha que piora quanto melhor
> for a sua malha.

## 20.3 A checagem decisiva (não é palpite)
Com `Verbosity = High` e `Sub-Step Reporting Frequency = 1000`, o STAR **escreve no `Output` o motivo
do encerramento de cada parcela**. Leia a mensagem: ela diz literalmente se foi
*maximum residence time* ou *maximum number of sub-steps*.
> **Sempre ler a mensagem antes de mexer no parâmetro.** Os dois sintomas são idênticos na cena.

## 20.4 A correção
```
Solvers → Lagrangian Multiphase → Steady → Maximum Sub-Steps = 500000   (de 20000)
```
Custo: só aumenta o **teto**. Parcela que sai do domínio encerra na hora; o limite só age em quem
ficaria preso mesmo.

**Se ficar lento**, a alavanca seguinte é o Courant do sub-passo (deixa o `dt` maior), mas isso
custa precisão — mexer só se necessário.

## 20.5 📌 Armadilha nº8
**`Maximum Sub-Steps` no default (20.000)** com malha refinada / prism layers finas → a parcela é
deletada **antes de atravessar o equipamento**, sem aviso, mesmo com `Maximum Residence Time` correto.
**Os dois têm de ser conferidos juntos.**

---

# PARTE 21 — ✅ DIAGNÓSTICO FECHADO: não é limite, é a ESTEIRA DE PAREDE

> Medição decisiva: trajetórias coloridas por **Particle Residence Time** (escala 0–10 s).
> Encerra a série de chutes das Partes 17/20.

## 21.1 O que a cena mostra
- Duto de entrada: **azul escuro** (t ≈ 0)
- Hélice no cilindro: azul → ciano → amarelo
- **Anel LARANJA/VERMELHO no fundo do cilindro** (≈ 10 s) ⬅️ a frente de onda em t = t_max
- Pontos alaranjados junto ao **teto/anel do vortex finder** (armadilha clássica de topo)

> ⭐ **As parcelas NÃO estão sendo deletadas cedo — elas sobrevivem os 10 s inteiros.**
> `Maximum Residence Time` (10 s) e `Maximum Sub-Steps` (500.000) estavam **certos**.
> O problema é outro: **elas descem devagar demais.**

## 21.2 A física: a partícula fica presa na subcamada
| medição | valor |
|---|---|
| Percorre o cilindro (435 mm) em | **~10 s** |
| **Velocidade de descida** | **43,5 mm/s** |
| Sedimentação em ar parado (50 µm) | 21,5 mm/s |
| **Razão** | **2,0×** |

> **A partícula está praticamente só SEDIMENTANDO.** O gás não a está transportando para baixo.
> (Referência: o **gás** atravessa o ciclone inteiro em **0,48 s** — a partícula está **~20× mais lenta**.)

**Por quê — a conta do quique:**
```
aceleração centrífuga junto à parede = v_t²/r = 17²/0,145 = 1.993 m/s²  =  203 g
```

| impacto normal | rebote (e=0,8) | excursão máxima |
|---|---|---|
| 0,5 m/s | 0,40 m/s | **0,04 mm** |
| 1,0 m/s | 0,80 m/s | **0,16 mm** |
| 2,0 m/s | 1,60 m/s | **0,64 mm** |

Sob **203 g**, o rebote não tira a parcela da parede: ela chacoalha dentro de **0,1–0,6 mm**, ou seja
**dentro da camada de prismas**, onde a velocidade do gás tende a **zero pelo no-slip**.
**Não há gás ali para carregá-la.** Ela desce por gravidade e só.

> Isso é **parcialmente físico** — pó real forma mesmo uma esteira lenta na parede do ciclone.
> O modelo `Rebound` com restituição alta **exagera** o aprisionamento, mas o mecanismo é real.

## 21.3 Correção — Plano A (tentar primeiro)
```
Solvers → Lagrangian Multiphase → Steady → Maximum Residence Time = 100 s
```
A 43,5 mm/s, descer os **1.160 mm** leva **27 s** — e isso é o **limite pessimista**, porque no cone
o raio diminui, a velocidade tangencial sobe e a parcela acelera. **100 s dá folga de 4×.**

**Critério:** se a η(50 µm) subir para 95–99 %, era só tempo de teto, e a física está correta.

## 21.4 Plano B — a definição de "captura na parede"
Se mesmo com 100 s elas não chegarem ao `outlet_dust`, adotar a convenção **padrão da literatura
de ciclones**: **partícula que toca a parede do CONE = capturada** (`Walls` do cone → Mode `Escape`).

| | prós | contras |
|---|---|---|
| Captura no `outlet_dust` (atual) | mede o trajeto real até a moega | depende de resolver a esteira de parede, que é cara e incerta |
| **Captura na parede** | robusta, barata, é o que a literatura usa | **ignora re-entrainment** → **superestima** η |

> Se for para o Plano B, **declarar a convenção no relatório** e rodar os dois para dar a **faixa**.
> Duas definições explícitas valem mais que um número sem definição.

## 21.5 📌 Armadilha nº9
**A esteira de parede.** Num Lagrangeano de ciclone, a partícula grossa não "voa" até o fundo — ela é
colada na parede por ~200 g e desce numa esteira **ordens de grandeza mais lenta que o gás**. Dimensionar
o `Maximum Residence Time` pela residência do **gás** (0,48 s × 20 = 10 s) **é insuficiente**:
tem de ser dimensionado pela **velocidade de descida da esteira**, que só se conhece **depois** de
uma primeira rodada. **Rode uma vez, meça a velocidade de descida na cena de residência, e só então
fixe o teto.**

---

# PARTE 22 — 🔑 As duas frases que destravam a leitura

> Fontes: *Track File Model Reference*, *Boundary Sampling Model Reference*,
> *Lagrangian Multiphase Solver Reference* (STAR-CCM+ User Guide).

## 22.1 Por que a cena "não atualiza" — o track file é TEMPORÁRIO até você salvar

> *"A **temporary** track file is created while the simulation runs. **You are required to SAVE the
> simulation** so that this temporary track file is moved to a final file having the same name as the
> simulation. **Only the final file can be brought into Simcenter STAR-CCM+ for analysis.**"*

E:
> **Auto-Load** — *"When activated, the track file is automatically reloaded whenever the file is written
> to hard disk by the Track File solver. **By default, this property is DEACTIVATED.**"*

**O ciclo obrigatório é de três passos, não dois:**
```
1. Step            → o solver escreve um track file TEMPORÁRIO
2. SALVAR a .sim   → o temporário vira o arquivo FINAL (.trk)
3. recarregar      → o Particle Tracks lê o final  ← só automático se Auto-Load = On
```

> 🚨 **Sem o passo 2 você fica olhando o track file da rodada ANTERIOR, indefinidamente.**
> Sintoma: você muda um parâmetro, dá Step, e a cena fica **idêntica** — inclusive a **legenda**.
> *(Foi o que aconteceu: `Maximum Residence Time` foi para 100 s e a legenda continuou 0–10 s.
> 10 s era o teto da rodada anterior — a cena era do arquivo velho.)*

**Correção:** `Tools → Track Files → [arquivo] → **Auto-Load = On**`, e **salvar após cada Step**.

## 22.2 Por que os reports leem zero — `Temporary Storage Retained`

Do *Lagrangian Multiphase Solver Reference*:
> **Temporary Storage Retained** — *"When On, **retains** or deactivates temporary storage at the end of
> the iteration… **These quantities become available as field functions during subsequent iterations**."*

**Por default o STAR DESCARTA os dados Lagrangeanos ao fim da iteração.** O field function
`Incident Mass Flux of Phase` fica sem dado no momento em que você roda o report — e o report
responde **zero**, corretamente, para "não há dado".

**Correção:** `Solvers → Lagrangian Multiphase → **Temporary Storage Retained = On**`

## 22.3 Como o Boundary Sampling realmente entrega o dado
> *"The Boundary Sampling model differs from the Track File model in that **it does not have a file
> associated with it. Sampled quantities are stored in memory**, and are accessed through **particle
> track PARTS that are added to the Particle Tracks node** when boundaries are added to the Boundaries
> property. **One particle track part is added for each boundary** selected."*

⭐ Ou seja: ao selecionar `outlet_dust` e `Outlet_gas` no Boundary Sampling, **nasceram duas novas
parts** sob `Particle Tracks`. **São ELAS que vão como `Parts` do report** — não a boundary.

E o modelo grava **automaticamente**, sem você pedir:
`Parcel Index` · `Particle Residence Time` (steady) · **`Particle Flow Rate`** (steady) · `Parcel Centroid`

### O caminho alternativo (independente do Incident Mass Flux)
`Particle Flow Rate` = **partículas por segundo** de cada parcela. Como o diâmetro é único:
```
m_particula = ρ_p · (π/6) · d³ = 1500 · (π/6) · (5e-5)³ = 9,817e-11 kg
Report: Sum
   Scalar = ${TrackParticleFlowRate} * 9.817e-11
   Parts  = [a particle track part do outlet_dust]
→ kg/s capturados
```
**Dois instrumentos independentes** para o mesmo número — se baterem, o resultado é sólido.

## 22.4 ⚠️ Consequência: o diagnóstico da Parte 21 precisa ser RECONFERIDO
A cena que embasou a conclusão da "esteira de parede a 43,5 mm/s" foi lida de um track file
**da rodada com teto de 10 s**. Era válida **para aquela rodada**, mas a conclusão só se sustenta
depois de reler com **track file fresco** (Auto-Load ligado + sim salva).
> **Primeiro consertar a leitura, depois reinterpretar a física.** Não dá para diagnosticar
> escoamento com instrumento congelado.

## 22.5 📌 Armadilha nº10
**Track file temporário + `Auto-Load` desligado** → a cena mostra a rodada anterior para sempre, e
você "corrige" parâmetros olhando um resultado velho. Combinada com a nº7 (Boundary Sampling
desligado) e a nº11 (`Temporary Storage Retained` desligado), formam o trio que faz o Lagrangeano
"rodar sem produzir nada".

---

# PARTE 23 — ✅ RETRATAÇÃO da Parte 21: estava tudo saudável, era o arquivo errado

**O que aconteceu:** existiam **DOIS** track files na pasta —
`ciclone_100_lagrangeano.trk` (velho) e `ciclone_100_lagrangeano_Copy.trk` (novo).
A cena estava apontada para o **velho**. Ao trocar o arquivo, a legenda de residência mudou de
**0–10 s** para **0–1,38 s**.

## 23.1 O número correto muda o diagnóstico por completo
| | valor |
|---|---|
| Residência do **gás** | 0,48 s |
| **Residência MÁXIMA das parcelas** | **1,38 s** |
| Razão partícula/gás | **2,9×** |
| Teto configurado | 100 s → **usado só 1,4 %** |

> ✅ **Nenhuma parcela está sendo morta pelo limite de tempo.**
> ✅ **2,9× a residência do gás é exatamente o esperado** para partícula grossa em espiral.
> ❌ **A "esteira de parede a 43,5 mm/s" da Parte 21 está RETRATADA** — foi calculada
> supondo 10 s de travessia, e os 10 s eram o **teto da rodada anterior**, lido de arquivo velho.

## 23.2 E por que as trajetórias "não descem o cone" na imagem
Se as parcelas terminam em 1,38 s sem bater no teto, **elas terminaram numa boundary de Escape**
— ou seja, **chegaram** ao `outlet_dust` ou ao `Outlet_gas`.
**As trajetórias no cone provavelmente estão ESCONDIDAS atrás da superfície opaca do cone.**

**Correção:** superfície do corpo → **`Opacity = 0,2`**.

## 23.3 📌 Armadilha nº12 — mais de um track file na pasta
Cada `Save As` gera um `.trk` com o nome do arquivo. Se você salvou com nomes diferentes ao longo
do estudo, sobram vários `.trk`, e o nó `Particle Tracks` fica apontado para **um deles**, não
necessariamente o mais recente.
> **Antes de interpretar qualquer cena de trajetória:** confira **qual arquivo** está carregado em
> `Tools → Track Files`, e confira a **data** dele. Foi o que produziu três diagnósticos errados
> em sequência (Partes 17, 20 e 21) — todos lidos de um arquivo congelado.

## 23.4 A lição metodológica
Passamos três rodadas ajustando parâmetros (`Maximum Residence Time`, `Maximum Sub-Steps`,
`Tracking Integration Method`) **olhando um resultado que não mudava porque não podia mudar**.
> **Regra:** quando uma mudança de parâmetro **não produz nenhuma mudança** no resultado, a primeira
> hipótese não é "o parâmetro não era esse" — é **"eu não estou olhando o resultado novo"**.
> Verificar a frescura do dado **antes** de reinterpretar a física.

---

# PARTE 24 — 📋 LISTA DEFINITIVA de reports e monitores (o que montar)

> Consolidada de: *Lagrangian Post-Processing Reference*, *Post-Processing Lagrangian Data*,
> KB000033060. Causa raiz de tudo que travou antes: **`Frozen` ligado no solver Lagrangeano**.

## 24.0 ⚙️ Antes de tudo — o estado dos solvers
| Nó | Valor |
|---|---|
| `Solvers → Lagrangian Multiphase → **Frozen**` | ❌ **DESMARCADO** ⬅️ era isto |
| `Solvers → Lagrangian Multiphase → Temporary Storage Retained` | ✅ **On** |
| `Solvers → Lagrangian Multiphase → Steady → Maximum Residence Time` | **100 s** |
| `Solvers → Lagrangian Multiphase → Steady → Maximum Sub-Steps` | **500.000** |
| `Solvers → Lagrangian Multiphase → Steady → Tracking Integration Method` | **2nd-order** |
| `Solvers → Segregated Flow / Segregated Energy / K-Omega` → **Frozen** | ✅ **MARCADOS** *(congela o gás)* |
| `Tools → Track Files → [arquivo] → Auto-Load` | ✅ **On** |

> ⚠️ **`Frozen` no Lagrangeano ≠ `Frozen` no escoamento.** Queremos o **gás congelado** e o
> **Lagrangeano livre**. Invertido, o solver não gera parcela nenhuma e **todo report responde zero
> corretamente** — sem nenhum aviso.

## 24.1 A constante que você vai usar
```
m_partícula (50 µm, ρ=1500) = 9,8175e-11 kg
ṁ injetado                   = 2,7778e-03 kg/s
```

## 24.2 Os reports — monte nesta ordem

### Grupo A — instrumento principal (método da KB)
Field function já criada ✅: `mdot_face` = `${IncidentMassFluxchar_050um} * mag($$Area)` · Dimensions **Mass/Time**

| # | Tipo | Nome | Scalar | Parts |
|---|---|---|---|---|
| 1 | **Sum** | **`MFR_bottom`** | `mdot_face` | boundary **`outlet_dust`** |
| 2 | **Sum** | **`MFR_top`** | `mdot_face` | boundary **`Outlet_gas`** |

> `Incident Mass Flux of <Phase>` — doc: *"computes the instantaneous mass flux of one Lagrangian
> phase interacting with a boundary (**hitting it or escaping through it**)"* → serve para **parede**
> e para **outlet**. É por isso que é o instrumento certo nos dois lados.

### Grupo B — as duas contas
| # | Tipo | Nome | Definição |
|---|---|---|---|
| 3 | **Expression** | **`eta_050`** ⭐ | `${MFR_bottom} / 2.7778e-3` |
| 4 | **Expression** | **`balanco_050`** | `(${MFR_bottom} + ${MFR_top}) / 2.7778e-3` |

### Grupo C — instrumento independente (cruzamento)
Usa as **particle track parts** que o Boundary Sampling criou sob `Particle Tracks` (uma por boundary).

| # | Tipo | Nome | Scalar | Parts |
|---|---|---|---|---|
| 5 | **Sum** | `check_bottom` | `${TrackParticleFlowRate} * 9.8175e-11` | *particle track part do `outlet_dust`* |
| 6 | **Maximum** | `t_res_max` | `Track: Particle Residence Time` | *particle track part do `outlet_dust`* |

> **#5 tem de bater com #1.** Dois caminhos independentes para o mesmo número.
> **#6** confirma que ninguém encosta no teto (`t_res_max` ≪ 100 s).

### Grupo D — nativo (já existe)
| # | Tipo | Nome | Config |
|---|---|---|---|
| 7 | **Particle Mass Flow** | `pmf_gas` | Phase `char_050um` · Parts `Outlet_gas` |

## 24.3 Monitores — **obrigatórios**, não opcionais
Doc: *"The stored data is for **ONE Lagrangian step**, so it is necessary to **monitor** the desired
values during the calculation."*

> 🚨 **O dado do Boundary Sampling vale UM passo.** Rodar o report "depois" pode pegar o intervalo
> vazio. **Crie monitor de todos os reports** (`botão direito → Create Monitor and Plot from Report`,
> Trigger = **Iteration**) e leia o **valor do monitor**, não o report avulso.

## 24.4 Critérios de aceite
| Report | Esperado | Se falhar |
|---|---|---|
| **`balanco_050`** | **0,98 – 1,02** | massa sumindo → revisar limites de parada |
| **`eta_050`** | **0,95 – 0,99** | ver Parte 21/23 |
| `t_res_max` | **≪ 100 s** (esperado ~1,4 s) | teto ativo → aumentar |
| `check_bottom` vs `MFR_bottom` | diferença < 5 % | instrumentos discordam → investigar |

**Valores de referência (η × ṁ):**
| η | MFR_bottom | MFR_top |
|---|---|---|
| **97,7 %** *(Lapple)* | **2,714e-03** | **6,39e-05** |
| 95 % | 2,639e-03 | 1,389e-04 |
| 90 % | 2,500e-03 | 2,778e-04 |
| 3 % | 8,33e-05 | 2,694e-03 |

## 24.5 📌 Armadilha nº13
**`Frozen` no solver Lagrangeano.** O solver não roda, nenhuma parcela é criada, o track file não é
reescrito, e **todos os reports respondem zero — que é a resposta correta para "não há dado"**.
Nenhuma mensagem de erro aparece. **Conferir `Frozen` é o primeiro passo de qualquer depuração
Lagrangeana**, antes de mexer em qualquer parâmetro físico.

---

# PARTE 25 — 💰 A economia do sub-passo: Courant, não força bruta

**Confirmado experimentalmente:** `Maximum Sub-Steps` **é** o limitante. Com **200.000** o voo chegou a
**13,4 s** (legenda de residência) e as trajetórias avançaram — mas ainda não descem o cone.

## 25.1 Não aumente N. Aumente o dt.
```
sub-passo médio medido = 13,4 s / 200.000 = 6,70e-5 s   (~1,14 mm por passo a 17 m/s)
```

| Caminho | Como | Custo |
|---|---|---|
| ❌ **Força bruta** | 30 s → 448.000 sub-steps | **2,2× CPU** |
| | 60 s → 896.000 | **4,5× CPU** |
| | 100 s → 1.493.000 | **7,5× CPU** |
| ✅ **Courant** | ×2 → 27 s com os mesmos 200.000 | **CPU igual** |
| | ×4 → 54 s | **CPU igual** |
| | ×8 → 107 s | **CPU igual** |

## 25.2 Os dois botões (Lagrangian Multiphase Solver Reference)
> **Maximum Courant Number** — *"provides an upper bound for the local time-step.
> **Reducing** this value can increase accuracy, at the expense of CPU time."*
> **Minimum Courant Number** — *"provides a **lower bound** for the local time-step."*

| Botão | O que faz | Por que importa aqui |
|---|---|---|
| **Maximum Courant Number ↑** | permite passos maiores em geral | ganho global de velocidade |
| **Minimum Courant Number ↑** ⭐ | **impede o dt de colapsar em célula minúscula** | ⭐ a parcela vive na **camada de prismas** (0,1–0,3 mm), dimensionada para o **y+ do GÁS** — resolução **100× mais fina do que a partícula precisa**. É ali que os sub-passos são queimados |

> 🎯 **A prism layer existe para resolver a camada-limite do gás.** Para a trajetória da partícula
> ela é **desperdício puro** de sub-passos. O `Minimum Courant Number` é o botão feito exatamente
> para isso: põe um **piso** no dt quando a célula é pequena demais para importar.

**Sugestão:** subir **Maximum Courant** para ~2–5 e **Minimum Courant** junto. Rodar e comparar a η
com a rodada de Courant baixo — se mudar <2 %, está documentado como verificação de convergência
temporal. *(Já estamos em `2nd-order`, que tolera passo maior.)*

## 25.3 ⭐ A alternativa estratégica: entregar a η como FAIXA
Em vez de brigar para resolver a esteira de parede, rodar **as duas convenções** e entregar o
intervalo. É o que a literatura de ciclones faz.

| Convenção | Config | Significado | Custo |
|---|---|---|---|
| **Captura na moega** *(atual)* | `Walls` **Rebound** + `outlet_dust` **Escape** | partícula tem de **chegar** ao fundo | caro — precisa resolver o quique na parede |
| **Captura na parede** | `Walls` → **Escape** | **tocou a parede = capturada** | **barato** — a parcela termina no 1º contato |

```
η(captura na parede)  ≥  η_real  ≥  η(captura na moega)
```
- **Limite superior:** ignora re-entrainment → otimista
- **Limite inferior:** parcela que fica presa na esteira e é deletada conta como perdida → pessimista

> **A rodada de "captura na parede" é rápida** (sem quique, sem esteira) e sozinha já dá o
> **limite superior** da curva η×d. Vale rodar **primeiro**: em minutos você tem a forma da curva
> e sabe se o joelho está em ~8 µm como o analítico prevê.

## 25.4 Ordem recomendada
1. **Courant ↑** (Max ~2–5, Min junto) → refaz a rodada atual com o mesmo CPU
2. Se ainda não descer: rodar **`Walls → Escape`** (captura na parede) → curva η×d **completa e rápida**
3. Voltar ao `Rebound` só para as 2–3 classes críticas → **a faixa**
4. Relatório: **declarar as duas convenções** e entregar o intervalo

## 25.5 📌 Sobre os reports ainda em zero / NaN
`Total: NaN — no data, incomplete computation` e `Outlet_gas = 0` são **coerentes** com o estado
atual: se as parcelas ainda são deletadas por sub-steps **antes** de tocar qualquer boundary de
Escape, **nenhuma** chega — nem embaixo nem em cima. Os reports estão certos; falta a parcela chegar.
> ⚠️ Notar também: o report saiu como *"Sum of User Field Function 1 **on Volume Mesh**"*.
> `Incident Mass Flux` é função de **BOUNDARY** — conferir se `Parts` está na boundary e não no volume.

---

# PARTE 26 — 🎯 CAUSA RAIZ: a restituição TANGENCIAL de 0,9 freia a partícula até parar

**Evidência (cena de parcelas coloridas por `Particle Velocity Magnitude`, 0,099–27,6 m/s):**
anel denso de parcelas **azul-escuro (~0,1–2 m/s)** colado à parede, enquanto o gás ali passa a
**15–27 m/s**. Elas **não estão descendo — estão freando.**
**Output:** `2180 parcel(s) reached maximum number of sub-steps`.

## 26.1 A aritmética do freio
Cada impacto remove **10 %** da velocidade tangencial (`e_t = 0,9`):

| queda para | impactos necessários |
|---|---|
| 50 % | **6,6** |
| **10 %** | **21,9** |
| 1 % | 43,7 |

E a **frequência de impacto** é altíssima, porque a centrífuga devolve a parcela imediatamente:
```
excursão após o quique  = 0,16 mm       (sob 203 g)
tempo de ida e volta    = 0,80 ms       → um impacto a cada 0,8 ms
tempo do arrasto para reacelerar (τ_p)  = 2,19 ms
```
> **Os impactos são 2,7× mais frequentes que a recuperação pelo arrasto.**
> O gás não consegue reacelerar a partícula entre um quique e o outro → **decaimento líquido**.
> **Em ~18 ms a parcela está a 10 % da velocidade.** Depois disso só chacoalha parada, queimando
> sub-steps até o limite. **É exatamente o anel azul da cena.**

## 26.2 ⚠️ Isso é ARTEFATO DE MODELO, não física
No ciclone real a partícula **desliza** pela parede continuamente reacelerada pelo gás. O modelo
`Rebound` com `e_t < 1` aplica uma perda tangencial **a cada impacto**, e com ~1.250 impactos por
segundo isso vira um freio que **não existe no equipamento**.

**Eu escolhi 0,8/0,9 argumentando "char contra aço".** O argumento vale para a componente
**NORMAL** (dissipação no choque). Para a **TANGENCIAL**, num escoamento rotativo com impacto
contínuo, 0,9 **drena sistematicamente a quantidade de movimento** — e o tutorial da Siemens usa
**1,0** justamente por isso.

## 26.3 ✅ A correção
`char_050um → Boundary Conditions → Walls → Physics Values`

| Coeficiente | antes | **agora** | por quê |
|---|---|---|---|
| **Normal Restitution** | 0,8 | **0,8** *(mantém)* | dissipação no choque é real |
| **Tangential Restitution** | 0,9 | **1,0** ⬅️ | evita o freio artificial acumulado |

> **Sensibilidade a rodar depois:** `e_t = 0,95` como caso intermediário. A diferença em η entra
> no relatório como **incerteza de modelo declarada**.

## 26.4 Sobre o número de parcelas (dúvida do Gabriel)
**2180 parcelas atingiram o limite** → há **pelo menos 2180 parcelas ativas**.
Para levantar curva de eficiência, **>100 já dá estatística**. **2180 é folgado.** ✅
*(A cena de "Local Instantaneous Data" mostra as parcelas **de um instante** — as que já terminaram
não aparecem, por isso parecem poucas.)*

## 26.5 📌 Armadilha nº14
**Restituição tangencial < 1 em escoamento rotativo.** Parece um refinamento físico ("char não é
elástico"), mas num ciclone a partícula impacta ~1.250×/s e a perda **acumula** até parar a
partícula. Sintoma: parcelas lentas coladas na parede, sub-steps esgotados, e nenhuma captura.
**Para a componente tangencial, comece em 1,0** e trate valores menores como estudo de sensibilidade
— **nunca como default.**

---

# PARTE 27 — ⚠️ BCs Lagrangeanas: `Walls` e `outlet_dust` são o MESMO TIPO

> Fontes: *Setting Default Lagrangian Phase Boundary Conditions* e *Setting Lagrangian Phase
> Boundary Conditions for a Specific Boundary*.

## 27.1 Existem DOIS níveis de configuração
| Nível | Onde | Alcance |
|---|---|---|
| **Default por TIPO** | `char_050um → Boundary Conditions → [Wall / Pressure Outlet / …]` | **todas** as boundaries daquele tipo |
| **Override por BOUNDARY** | `[boundary] → Physics Conditions → **Lagrangian Specification** → Method = **Specify for Boundary**` | só aquela boundary |

Doc:
> *"The properties of a boundary type sub-node define the interaction mode of the Lagrangian phase
> for boundaries of that type, **unless the mode is over-ridden at a specific boundary**."*
> *"**Specify for Boundary** — Specifies that specific boundary conditions are provided… A **Phase
> Conditions** sub-node is added as a child to the **Physics Values** node for this boundary."*

## 27.2 🚨 A armadilha do NOSSO caso
```
Walls        →  Type = Wall     →  queremos REBOUND
outlet_dust  →  Type = Wall     →  queremos ESCAPE
                       ↑
              MESMO TIPO. O default é UM SÓ.
```

> **Um dos dois OBRIGATORIAMENTE precisa de override.** Se `outlet_dust` estiver herdando o default
> do tipo `Wall` (que é **Rebound**), **o pó QUICA no fundo e volta para o vórtice** — e a
> eficiência sai perto de zero, sem nenhum aviso.

## 27.3 ✅ Checklist de verificação (uma a uma)

### `Walls` — deixe no DEFAULT do tipo
`char_050um → Boundary Conditions → **Wall** → Mode`
| | valor |
|---|---|
| Mode | **Rebound** |
| Normal Restitution Coefficient | **0,8** |
| **Tangential Restitution Coefficient** | **1,0** ⬅️ *(corrigido — ver Parte 26)* |

### `outlet_dust` — PRECISA de override ⭐
```
Regions → Ciclone → Boundaries → outlet_dust → Physics Conditions → Lagrangian Specification
    Method = **Specify for Boundary**            ⬅️ sem isto, o resto nem existe
→ aparece Phase Conditions → char_050um → Physics Conditions → Mode
    Active Mode = **Escape**                     ⬅️ = CAPTURADA
```
E no nível do gás: `outlet_dust → Type = **Wall**` *(não mexer)*

### `Outlet_gas` — nada a fazer
`Type = Pressure Outlet` → único modo possível para Material Particle é **Escape**, automático.
`Phase Conditions → char_050um → Type` deve estar em **`Pressure Outlet`**, **não** em
`Phase Impermeable`.

### `Inlet` — nada a fazer
`Type = Velocity Inlet` → único modo é **Escape**, automático.
`Phase Conditions → char_050um → Type` deve estar em **`Velocity Inlet`**, **não** em
`Phase Impermeable`.

## 27.4 O teste que confirma sem depender de report
Se `outlet_dust` estiver com **Escape**, as parcelas **desaparecem** ao chegar no ápice.
Se estiver herdando **Rebound**, elas **acumulam** ali e voltam a subir.
> **Olhe o ápice do cone na cena de parcelas.** Sumiram = Escape ✅ · Acumularam = herdou Rebound ❌

## 27.5 📌 Armadilha nº15
**Duas boundaries do mesmo TIPO com comportamentos Lagrangeanos opostos.** No ciclone isso é
inevitável: a saída de pó é `Wall` para o gás (airlock) mas `Escape` para a partícula, enquanto o
corpo é `Wall`+`Rebound`. **A que difere do default precisa de `Specify for Boundary` explícito.**
Herdar silenciosamente é o modo de falha.

## 27.6 Nota sobre "o escoamento de partícula não se desenvolveu"
Em **steady**, cada iteração **regenera a solução Lagrangeana inteira do zero** (Parte 18.4).
Não existe "desenvolvimento" ao longo das iterações.
> **N iterações = N realizações estatísticas independentes**, não N passos de desenvolvimento.
> Isso é útil (média para as classes finas, onde a dispersão turbulenta é estocástica),
> mas **uma** iteração já contém a resposta completa para as classes grossas.
