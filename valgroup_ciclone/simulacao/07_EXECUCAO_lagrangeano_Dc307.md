# 07 — EXECUÇÃO do Lagrangeano no **Dc = 307 mm**

> Folha de execução. O conceito e as 16 armadilhas estão no `06_GUIA` (escrito para o Dc = 290);
> aqui está **só o que muda** + o método oficial verificado nos PDFs da Siemens.
> Campo base: **Rodada 8** (k-ω steady, `Outlet`, parede convectiva) — convergido nos dois pontos.

---

# 1. O MÉTODO OFICIAL — KB000033060, verificado na fonte

```
E = 1 − (MFR_inlet − MFR_bottom) / MFR_inlet   =   MFR_bottom / MFR_inlet
```

## 1.1 O que a KB exige

| # | requisito | por quê |
|---|---|---|
| 1 | O fundo é **`Wall`** com condição **`Escape`** para a fase Lagrangeana | *"as soon as the particles touch the wall, they disappear from the domain, and mass and momentum are removed"* |
| 2 | Field function `Incident Mass Flux of Phase` | disponível quando o modelo Lagrangeano está ativo · unidades **kg/m²·s** |
| 3 | **Boundary Sampling ligado** | sem ele o `Incident Mass Flux` não é preenchido |
| 4 | Report do tipo **`Sum`** (não Surface Average, não Lagrangian Mass Flow) | soma face a face |

## 1.2 A field function — atenção ao `$$`

```
mdot_bottom = $IncidentMassFluxPhase1 * mag($$Area)
```

- ⚠️ **`$$Area` com DOIS cifrões** — `Area` é vetor (normal da face). `mag()` devolve a área escalar.
- ⚠️ **`Phase1` é o nome da SUA fase.** Se a fase se chama `char_010um`, a função é
  `$IncidentMassFluxchar_010um`. Confira no autocompletar.

## 1.3 Os reports por classe

| # | Report | Tipo | Parts | Definição |
|---|---|---|---|---|
| 1 | `mdot_bottom_010` | **Sum** | **`outlet_dust`** | scalar = `mdot_bottom` |
| 2 | **`eta_010`** | Expression | — | `${mdot_bottom_010} / 2.7778e-3` |
| 3 | `mdot_gas_010` | Lagrangian Mass Flow | `Outlet_gas` | fase `char_010um` |
| 4 | `balanco_010` | Expression | — | `(${mdot_bottom_010} + abs(${mdot_gas_010})) / 2.7778e-3` |

> **`balanco_010` é o detector de fraude.** Tem de dar **1,00 ± 0,01**. Se der menos, há parcela
> presa no domínio (ver §3, `Maximum Residence Time`) — e a eficiência sai **falsamente baixa**
> sem nenhum aviso.

---

# 2. TRACK FILE — o que a referência diz (e o que nos custou tempo)

Do `Track File Model Reference`:

- *"A **temporary** track file is created while the simulation runs. You are **required to save the
  simulation** so that this temporary track file is moved to a final file... **Only the final file**
  can be brought into Simcenter STAR-CCM+ for analysis."*
- **`Auto-Load` vem DESLIGADO por padrão.**
- Gravação automática (não precisa selecionar): `Parcel Index` · `Time` (ou **`Particle Residence
  Time`** em steady) · `Particle Count` (ou **`Particle Flow Rate`** em steady) · `Parcel Centroid`
- Uma parcela grava entrada em: injeção · cruzamento de face interna · **interação com face de
  contorno** · colisões · depleção

⚠️ **A armadilha nº12 que já nos pegou:** mais de um `.trk` na pasta. O STAR carrega o que você
apontar, não o mais recente. **Apague os antigos antes de rodar.**

---

# 3. PRÉ-VOO — as 6 que realmente morderam nesta campanha

| # | verificar | sintoma se errar |
|---|---|---|
| 1 | **Lagrangian Solver NÃO está `Frozen`** | ⛔ nenhum erro, **todos os reports devolvem zero corretamente** |
| 2 | **`outlet_dust` = `Wall`** (gás) com **`Escape`** (fase Lagrangeana) | se for `Outlet`, injeta 37–52 % de vazão parasita pelo ápice |
| 3 | **`Maximum Residence Time`** ≥ **10 s** | parcelas deletadas em voo → η falsamente baixa, sem aviso |
| 4 | **`Maximum Sub-Steps`** alto o bastante | mesma coisa: parcela morre antes de chegar ao fundo |
| 5 | **Restituição tangencial = 1,0** | com 0,9 a parcela para em ~18 ms sob 203 g e nunca alcança o fundo |
| 6 | **Boundary Sampling ligado** | `Incident Mass Flux` fica vazio → Sum devolve zero |

> **A pergunta de rotina desta campanha:** *"este valor é calculado ou prescrito neste lugar?"*
> Já pegou o `P_porta_ar` devolvendo 98.067 Pa e a `T_parede` devolvendo 400 °C.

---

# 4. O QUE MUDA do Dc = 290 para o Dc = 307

| parâmetro | Dc = 290 | **Dc = 307** |
|---|---|---|
| `Inlet → Velocity Magnitude` (100 %) | 15,23 m/s | **13,59 m/s** |
| idem (50 %) | 7,62 m/s | **6,80 m/s** |
| `Turbulence Intensity` 100 % / 50 % | 0,041 / 0,045 | **0,0417 / 0,0455** |
| entrada a × b | 145 × 58 mm | **153,5 × 61,4 mm** |
| ṁ por classe (100 %) | 2,7778e-3 kg/s | *(mantém)* |
| ṁ por classe (50 %) | 1,389e-3 kg/s | *(mantém)* |

**Tudo o mais do `06_GUIA` vale sem alteração** — o injetor, as fases por classe, os modelos.

---

# 5. AS CLASSES E AS PREVISÕES

Uma **fase Lagrangeana por classe** (é o único jeito de separar η por tamanho — `06_GUIA` Parte 7).

Diâmetro de corte por Lapple, com as propriedades da planilha
(**ρ_s = 776,75 · µ = 9,5e-5**, decisão do Marcus até virem as medidas):

```
d* = √[ 9·µ·b / (2π·Ne·v_i·(ρ_s − ρ)) ]        b = 0,2·Dc = 61,4 mm · Ne = 6
```

| | **100 %** | **50 %** |
|---|---|---|
| **d\*** | **11,5 µm** | **16,3 µm** |

## Previsões de η por classe — registrar ANTES de rodar

| d (µm) | **η 100 %** | **η 50 %** |
|---|---|---|
| 1 | 0,8 % | 0,4 % |
| 2 | 2,9 % | 1,5 % |
| 5 | 15,9 % | 8,6 % |
| **10** | **43,1 %** | **27,3 %** |
| **20** | **75,2 %** | **60,1 %** |
| 50 | 95,0 % | 90,4 % |
| 75 | 97,7 % | 95,5 % |
| 150 | 99,4 % | 98,8 % |

> Lapple é **referência, não gabarito**. Espera-se o CFD **abaixo** de Lapple nos finos (o modelo
> não captura reentrenimento nem a camada-limite de parede) e **acima** nos grossos.
> Divergência > 15 pontos numa classe intermediária ⇒ investigar antes de aceitar.

---

# 6. ⭐ A CONVERSÃO QUE IMUNIZA A CURVA

A trajetória depende de ρ_p, d e µ **só** através do tempo de relaxação:

```
τ_p = ρ_p·d² / (18·µ)        ⇒   η = f(τ_p)   apenas
```

Válido porque estamos em Stokes pleno (Re_p ~ 1e-4 a 2e-2) e porque, a Re ≈ 1,7e5, o ξ do
ciclone é praticamente independente de Reynolds — o campo de gás quase não muda com µ.

**Portanto a curva rodada com um par (ρ_s, µ) serve para qualquer outro:**

```
d_equivalente = d · √[ (ρ_novo/ρ_ref) · (µ_ref/µ_novo) ]
```

| cenário | ρ_s | µ | fator | **d\* a 100 %** |
|---|---|---|---|---|
| **planilha (o que vamos rodar)** | 776,75 | 9,5e-5 | 1,000 | **11,5 µm** |
| ρ_s corrigido | 1500 | 9,5e-5 | 1,389 | 8,3 µm |
| µ corrigido | 776,75 | 2,5e-5 | 1,949 | 5,9 µm |
| **ambos corrigidos** | 1500 | 2,5e-5 | **2,707** | **4,2 µm** |

⇒ **Quando a Valgroup devolver µ e ρ_s, é pós-processamento — não é rodada nova.**
E as duas correções pendentes empurram na direção **favorável**.

## Como apresentar
Plote **η × d** com o eixo secundário em **número de Stokes**, e a tabela acima ao lado.
O cliente vê que o resultado não depende dos números que ele ainda vai confirmar.

---

# 7. ORDEM DE EXECUÇÃO

1. **Uma classe só** (10 µm, a mais próxima do corte) → validar o `balanco` = 1,00 ± 0,01
2. Se fechar, **as 8 classes** a 100 %
3. **Repetir a 50 %** (v_i = 6,80 · ṁ = 1,389e-3 por classe)
4. Curva η × d nos dois pontos de carga
5. Convolução com a faixa de PSD (`dimensionamento/sensibilidade_finos.py`)

> **Não monte as 8 classes antes de o passo 1 fechar.** Se o balanço não der 1,00 numa classe,
> não vai dar em nenhuma — e você terá gasto 8× o tempo para descobrir.


---

# 8. ⭐ REFORMULAÇÃO — medir a FUGA, não a coleta

> Substitui o §1 (método da KB000033060) **nesta geometria**. O §1 continua correto
> em geral; ele falha aqui por um motivo específico, registrado abaixo.

## 8.1 Por que o método da KB não fecha neste ciclone
A KB mede a coleta no fundo: `E = MFR_bottom / MFR_inlet`, com o fundo em `Escape`.
Isso pressupõe que a partícula **chega ao fundo**.

**Aqui ela não chega.** Medido: partícula de 50 µm com `Wall = Rebound` fica presa em **quina**
(teto e junção cilindro-cone) — 5.075 de 5.082 parcelas ainda ativas em 50.000 sub-steps e 2,5 s
de voo, com `Turbulent Dispersion` ATIVA. A causa é mecânica:

```
centrífuga a 830 g → empurra contra a parede
Rebound (rest. normal 0,9) → devolve
ciclo se fecha em fração de ms → partícula fica presa deslizando
e em quina a velocidade axial do gás é ~zero → nada a transporta
```

Não há valor de restituição que conserte: o que ocorre de verdade na parede é o **strand**
(corda densa descendo por atrito e gravidade), física que o rastreamento de partícula isolada
não reproduz.

E `Wall = Escape` em tudo resolve o travamento mas **cria coleta falsa** no duto de entrada, no
teto e na externa do vortex finder — justamente onde os FINOS transitam, que é onde mora a resposta.

## 8.2 A formulação que dispensa o problema
```
η = 1 − |mdot_gas| / mdot_inj
```
**Tudo o que não sai pelo gás foi retido.**

| classe | comportamento | resultado |
|---|---|---|
| **50 µm** | trava na parede, não escapa | η = 100 % ✅ |
| **5 µm** | escapa pelo vortex finder | medido direto ✅ |

A partícula presa deixa de ser problema: **não é preciso saber onde ela parou, só que não saiu
com o gás** — e fisicamente ela não sairia, está no strand. Duto, teto e vortex finder ficam
todos em `Rebound` e não coletam nada indevidamente. **A questão do split da `Walls` evapora.**

## 8.3 Setup completo

### Parâmetro (1, global)
`Tools → Parameters → New → Scalar` · **`mdot_inj` = 2,7778e-3 kg/s** *(a 50 % → 1,389e-3)*

### Reports — por classe
| # | Report | Tipo | Definição |
|---|---|---|---|
| 1 | `mdot_gas_XXX` | **Lagrangian Mass Flow** | Parts = `Outlet_Gas` · Phase = `char_XXXum` |
| 2 | ⭐ **`eta_XXX`** | **Expression** | `1 - abs(${mdot_gas_XXX}) / ${mdot_inj}` |
| 3 | `mdot_dust_XXX` | **Sum** | `mdot_face_XXX` · Parts = `Outlet_dust` — **só diagnóstico** |

### Boundaries
| boundary | Mode |
|---|---|
| `Walls` e as 5 do split | **Rebound** — default do tipo, **sem override** |
| `Outlet_dust` · `Outlet_Gas` · `Inlet` | Escape |

### Solver
Maximum Sub-Steps **150.000** · Max Residence Time 10 s · Verbosity **High** ·
Tracking Integration **2nd-order** · Active Parcel Fraction Cut-off 0,0 ·
Maximum Courant **1,0** · Parcel Streams **11**

## 8.4 Como ler a fração ainda ativa
Ela **não invalida** o η — diz onde você está:

| ainda ativas no fim | leitura |
|---|---|
| < 2 % | η cravado |
| alto **e** partículas nos anéis de parede (cena) | normal no grosso — parede é coleta, o η já as conta como retidas ✅ |
| alto **e** partículas circulando no miolo | número mole — mais sub-steps |

## 8.5 📌 Armadilha nº17 — trocar de instrumento antes de consertar a medição
Perdemos uma tarde tentando fazer a partícula chegar ao fundo (split da boundary, modos por
superfície, identificação por área) para poder usar a fórmula da KB. **A fórmula é que não servia
a esta geometria.**

> Quando o instrumento não alcança a grandeza, **a primeira pergunta é se existe outra grandeza
> equivalente que o instrumento alcança** — não como adaptar a geometria da medição.
> Aqui: fuga e coleta são complementares, e a fuga é medível sem ambiguidade.


---

# 9. ⚠️ CORREÇÃO — a densidade da partícula é **1500**, não 776,75

Confirmado no material da fase Lagrangeana. **Toda a §5 (previsões com ρ_s = 776,75) está
superada por esta seção.**

## 9.1 Validação — CFD × Lapple no diâmetro de corte
Primeira classe medida: **5 µm a 100 % → η = 31,34 %** (150.000 sub-steps · 19 de 5.082
parcelas ativas no fim = 0,37 % ⇒ **η = 31,3 ± 0,4**).

Invertendo a curva de Lapple para achar o corte implícito no CFD:
```
0,3134 = 1/(1+(d*/5)²)   →   d* = 7,40 µm
```

| | d\* |
|---|---|
| **CFD (implícito)** | **7,40 µm** |
| Lapple com ρ_s = 1500 | **8,28 µm** |
| **concordância** | **11 %** ✅ |
| *(Lapple com ρ_s = 776,75)* | *11,51 µm — 64 %, incompatível* |

E o η direto: Lapple(1500) prevê 26,7 % em 5 µm contra **31,3 % medidos** — 4,6 pontos acima,
**na direção esperada**: a retenção de parede conta as presas como retidas, e Lapple embute
reentranhamento.

> **Dois métodos independentes dentro de 11 % no diâmetro de corte.** Mesmo padrão de validação
> que fechou o ΔP (13 %) e a térmica (0,3 °C).

## 9.2 Não refazer a 776,75 — conversão de Stokes
```
d_equivalente = d · √[ (ρ_novo/1500) · (9,5e-5/µ_novo) ]
```
| cenário | ρ_s | µ | **d\* a 100 %** |
|---|---|---|---|
| **RODADO** | **1500** | **9,5e-5** | **8,28 µm** |
| planilha (bulk) | 776,75 | 9,5e-5 | 11,51 µm |
| µ corrigido | 1500 | 2,5e-5 | 4,25 µm |
| ambos corrigidos | 2000 | 2,5e-5 | 3,68 µm |

**E 1500 é o valor mais defensável.** O 776,75 da planilha é densidade **aparente do leito** —
inclui vazios e subestima a inércia. A própria tabela de "Valores Usuais" da planilha declara
a faixa **1500–3000**, e o valor usado como projeto está **abaixo do mínimo dela**.

## 9.3 Previsões corrigidas (Lapple, ρ_s = 1500)
d\* = **8,28 µm** a 100 % · **11,70 µm** a 50 %

| d (µm) | **η 100 %** | η 50 % |
|---|---|---|
| 1 | 1,4 % | 0,7 % |
| 2 | 5,5 % | 2,8 % |
| **5** | **26,7 %** → **medido 31,3 %** ✅ | 15,4 % |
| 10 | 59,3 % | 42,2 % |
| 20 | 85,4 % | 74,5 % |
| 50 | 97,3 % | 94,8 % |
| 75 | 98,8 % | 97,6 % |
| 150 | 99,7 % | 99,4 % |

## 9.4 Sub-steps por classe — o critério é a FRAÇÃO ATIVA, não o número
| classe | comportamento | sub-steps |
|---|---|---|
| 1 · 2 µm | escapam rápido | ~50.000 |
| **5 · 10 · 20 µm** | perto do corte, espiralam | **150.000** |
| 50 · 75 · 150 µm | **travam na parede — a fração ativa NUNCA cai** | **20.000** |

⚠️ **Nas grossas não espere a fração cair.** O η já está determinado cedo porque `mdot_gas` para
de crescer depois de ~1 s. Rodar 150.000 com 5.082 parcelas ativas seria 7,6e8 de trabalho
para não mudar nada — é a maior economia de tempo disponível nesta campanha.

**Regra geral:** rodar até a fração ativa cair abaixo de **1 %**; nas classes que travam, até
`mdot_gas` estabilizar (~20.000).
