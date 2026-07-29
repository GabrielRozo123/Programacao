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
