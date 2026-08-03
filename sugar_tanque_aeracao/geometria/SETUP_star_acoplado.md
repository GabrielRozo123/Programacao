# Setup STAR-CCM+ — domínio acoplado (boundaries · derived parts · reports · scenes)

> Para `ACOPLADO_aerador_reator_ejetor_fluido.step` · malha 5,16 M células.
> **Todas as coordenadas em METROS.**

---

# 1. BOUNDARIES (8)

| # | Nome | Como identificar | Tipo | Valores |
|---|---|---|---|---|
| 1 | **`xarope_in`** | único disco **Ø0,2027** com normal **+Z**, em **z = 2,8245** | **Velocity Inlet** | **1,12 m/s** · VF: xarope=1, ar=0 · T operação |
| 2 | **`ar_in_1`** | disco **Ø0,0158** em x = **−0,325**, normal **+Y**, z = 2,2085 | **Pressure Inlet** | **1 kgf/cm² = 98.067 Pa (man.)** · VF: ar=1 |
| 3 | **`ar_in_2`** | idem em x = **0,025** | idem | idem |
| 4 | **`ar_in_3`** | idem em x = **0,375** | idem | idem |
| 5 | **`ar_in_4`** | idem em x = **0,725** | idem | idem |
| 6 | **`superficie_aerador`** | disco **Ø2,032** em **z = 1,220** | **Wall** | ⭐ **`Shear Stress Specification = Slip`** |
| 7 | **`superficie_reator`** | disco **Ø5,08** em **z = 1,220** | **Pressure Outlet** | 0 Pa · backflow VF ar=1 |
| 8 | **`paredes`** | **todo o resto** | **Wall** no-slip | |

> ### ⭐ Decisão do Marcus: "o topo do aerador é wall" — implementada literalmente
>
> **`Wall` + `Shear Stress Specification = Slip`** = aproximação **rigid-lid** de superfície livre
> plana. Método clássico e nomeado. Slip (e não no-slip) porque no-slip frearia artificialmente
> a circulação superficial do aerador.
>
> **Por que NÃO usar `Outlet` + `Phase Impermeable`:** essa opção só aparece no tipo `Outlet`
> (flow-split), não em `Pressure Outlet` — verificado no software. E `Outlet` flow-split
> misturado com `Pressure Outlet` na mesma região tem semântica de *split ratio* ambígua.
> Risco desnecessário: ver abaixo por que não precisamos dele.
>
> #### Por que o gás preso sob a tampa NÃO é problema — topologia + duas contas
>
> Bounding boxes dos 4 sólidos de `sugar_dominio_fluido_completo.step`:
>
> | sólido | V | Z |
> |---|---|---|
> | reator | 139,86 m³ | −6431 a **+1220** |
> | passagem | 4,35 m³ | −4850 a −250 |
> | **aerador** | 20,18 m³ | −5892 a **+1220** |
> | canal do topo | 5,31 m³ | −211 a **+1084** |
>
> ⚠️ **As duas superfícies livres estão na MESMA cota z = 1220.** *(correção: o doc dizia 1479
> para o reator.)*
>
> ⚠️ O canal do topo termina em **z = 1084 — 136 mm ABAIXO da superfície livre**. É um duto
> submerso. Logo **não existe via de escape lateral para o gás do aerador**.
>
> **Conta 1 — tempo de encher o bolsão:** π/4·2,032²·0,136 = **0,441 m³**. No Caso B o ar na
> superfície (expandido a 1 atm) seria ~10,6 m³/h → **150 s**. Rodadas de 3–5 s ⇒ margem 30×.
>
> **Conta 2 — a bolha sequer chega lá.** Stokes no xarope:
> `v = (ρl−ρg)·g·d²/18µ = 1300·9,81·(2,5e-3)²/(18·6,5) =` **0,68 mm/s** (Re_bolha = 3,4e-4 ✅).
> Subir os 6,5 m da boca até a superfície leva **9.500 s ≈ 2,6 h**. Em 5 s de rodada
> **não chega gás nenhum ao teto do aerador**.
>
> *(Esse 0,68 mm/s é também a explicação física de por que o estudo anterior não achou flotação.)*
>
> **Limite declarado:** vale até ~30 s de tempo físico. A rodada longa de holdup (30–60 s) exige
> revisitar. O report `ar_retido` (§8.4c) monitora isso em tempo real.
>
> **O topo do REATOR é a única saída de líquido** — é ele que fecha o balanço. Velocidade de
> saída = 0,036 m³/s ÷ 20,3 m² ≈ **1,8 mm/s**: sorvedouro lento demais para distorcer o aerador.
>
> *Pendência adiada (combinado com o Marcus/Ito): a sucção da bomba não está no domínio.
> O caminho de retorno global do tanque é, portanto, aproximado. Os entregáveis que NÃO dependem
> disso — o ar que entra e a bolha na boca — são governados pela cabeça do ejetor e pela lança.*

> ⚠️ **A boca da lança NÃO é boundary.** Ela é interior — o CFD calcula o que sai. É o ganho do
> acoplado: no modelo antigo você tinha que prescrever VF de ar e tamanho de bolha ali.

**Dica para achar rápido:** as 4 portas de ar são os únicos discos de **1,96 cm²** do modelo;
a entrada de xarope é o único de **322,7 cm²** com normal +Z.

---

# 2. DERIVED PARTS

## 2.1 Medição — o que o ejetor entrega ⭐
| Nome | Tipo | Definição |
|---|---|---|
| **`plano_boca`** | Section → Plane | ponto (0, 0, **−5,2465**) · normal (0,0,1) |
| **`boca_L1..L4`** | Cylinder | eixo (x, −0,440, −5,25) a (x, −0,440, −5,24) · r = **0,032** · x = −0,325 / 0,025 / 0,375 / 0,725 |

## 2.2 Medição — o que acontece no bico
| Nome | Tipo | Definição |
|---|---|---|
| **`plano_saida_bico`** | Section → Plane | ponto (0, 0, **1,8408**) · normal (0,0,1) |
| `plano_garganta` | Section → Plane | ponto (0, 0, **1,8655**) · normal (0,0,1) |
| `plano_porta_ar` | Section → Plane | ponto (0, 0, **2,2085**) · normal (0,0,1) |

## 2.3 Visualização
| Nome | Tipo | Definição |
|---|---|---|
| **`corte_vertical`** | Section → Plane | ponto (0,200, −0,440, 0) · normal **(0,1,0)** — corta as 4 lanças no comprimento |
| `corte_XZ_reator` | Section → Plane | ponto (0,196, −6,278, 0) · normal (0,1,0) |
| **`ar_no_tanque`** | **Threshold** | scalar **Volume Fraction of Ar** · `All Above` · **0,01** ⭐ |
| `bolha_fina` | Threshold | scalar **Sauter Mean Diameter** · `All Below` · **2,0e-4** (200 µm) |

---

# 3. REPORTS ⭐ *(os que respondem o estudo)*

## 3.1 O ar entra? — nas portas
| Report | Tipo | Parts | Scalar |
|---|---|---|---|
| `mdot_ar_1..4` | **Phase Mass Flow** | `ar_in_1..4` | fase **Ar** |
| **`Qar_total`** | **Expression** | | `(${mdot_ar_1}+${mdot_ar_2}+${mdot_ar_3}+${mdot_ar_4})/1.2*3600` → **m³/h** |

> **Alvo do Ito: 40 m³/h.** No ejetor isolado deu **0,04 m³/h** (1000× menos).

## 3.2 O que sai da lança? ⭐ *o resultado do estudo*
| Report | Tipo | Parts | Scalar |
|---|---|---|---|
| **`VF_ar_boca`** | Surface Average | `plano_boca` | Volume Fraction of Ar |
| **`SMD_boca`** | Surface Average | `plano_boca` | **Sauter Mean Diameter** |
| `v_boca` | Surface Average | `plano_boca` | Velocity Magnitude |
| `SMD_boca_L1..L4` | Surface Average | `boca_L1..L4` | SMD — *compara as 4 lanças* |

## 3.3 A física do bico
| Report | Tipo | Parts |
|---|---|---|
| `v_bico` | Surface Average · Velocity Magnitude | `plano_saida_bico` |
| `P_garganta` | Surface Average · **Absolute Pressure** | `plano_garganta` |
| **`P_porta_ar`** | Surface Average · **Absolute Pressure** | `plano_porta_ar` |

> ⭐ **`P_porta_ar` é o report-chave do diagnóstico.** Se ela ficar **acima** de
> 98.067 Pa (man.), o ar **não tem como entrar** — e isso confirma numericamente a causa
> geométrica (porta 318 mm a montante da contração).

## 3.4 Aeração no tanque
| Report | Tipo | Parts |
|---|---|---|
| **`holdup_aerador`** | Volume Average · VF de Ar | região do aerador |
| `holdup_reator` | Volume Average · VF de Ar | região do reator |
| `SMD_aerador` | Volume Average · SMD | aerador |
| **`frac_flotavel`** | Volume Integral do threshold `bolha_fina` ÷ volume total de ar | |

## 3.5 Controle
| Report | Tipo |
|---|---|
| `mdot_xarope_in` | Mass Flow em `xarope_in` → deve dar **≈ 46,9 kg/s** (130 m³/h × 1300) |
| `balanco_massa` | Expression: entradas − saídas ≈ 0 |

**Crie monitor + plot de todos** (`botão direito → Create Monitor and Plot from Report`).

---

# 4. SCENES

| # | Cena | Displayer | Scalar |
|---|---|---|---|
| 1 | **`VF_ar`** ⭐ | `ar_no_tanque` (threshold) + geometria com **Opacity 0,15** | Volume Fraction of Ar |
| 2 | **`SMD`** | `corte_vertical` | Sauter Mean Diameter · escala 0 a 3e-3 |
| 3 | `velocidade` | `corte_vertical` | Velocity Magnitude |
| 4 | **`bico_zoom`** | `corte_vertical`, câmera em z ≈ 1,85 | Velocity Magnitude · **mostra o jato dos 7 furos** |
| 5 | `pressao_ejetor` | `corte_vertical`, faixa z 1,8 a 2,6 | **Absolute Pressure** — mostra se há depressão na porta |

> A cena **5** é a que explica o problema visualmente: se a porta de ar estiver numa zona
> **vermelha** (pressão alta) em vez de azul, o Marcus e o Ito enxergam a causa sem equação.

---

# 5. Critérios de aceite / o que olhar

| Report | Se der… | Significa |
|---|---|---|
| **`Qar_total`** | ≈ 40 m³/h | ✅ o ejetor funciona |
| | ≪ 1 m³/h | ❌ confirma o achado do ejetor isolado |
| **`P_porta_ar`** | > 98 kPa man. | ❌ **o ar não pode entrar** — causa geométrica confirmada |
| **`SMD_boca`** | < 200 µm | ✅ bolha flotável |
| | ~1–2 mm | ❌ mesma conclusão do estudo anterior |
| `holdup_aerador` | — | quanto ar fica retido no tanque |
| `balanco_massa` | < 1 % | pré-requisito para acreditar em qualquer número acima |

---

# 6. ⚠️ PRIMEIRO: o domínio é UMA região fundida

Não existe "região do aerador" separada. Para os reports de volume, crie **derived parts de volume**:

| Nome | Tipo | Start | End | Radius |
|---|---|---|---|---|
| **`vol_aerador`** | **Cylinder** | (0.200, −0.440, **−5.892**) | (0.200, −0.440, **1.220**) | **1.016** |
| `vol_reator` | Cylinder | (0.196, −6.278, −6.431) | (0.196, −6.278, **1.220**) | 2.540 |

*(o cilindro do aerador tem 23,06 m³ geométricos e o sólido real 20,18 — ele cobre com folga,
e as células fora do fluido simplesmente não existem)*

---

# 7. FIELD FUNCTIONS auxiliares (criar antes dos reports)

| Nome | Definição | Para que |
|---|---|---|
| **`ar_vol`** | `${VolumeFractionAr} * ${Volume}` | volume **de ar** em cada célula |
| **`SMD_x_ar`** | `${SauterMeanDiameter} * ${VolumeFractionAr} * ${Volume}` | para média ponderada |

> ⚠️ **Ajuste os nomes** conforme aparecem no seu autocompletar — dependem de como a fase de ar
> foi nomeada (ex.: `VolumeFractionofAr`, `Ar_VolumeFraction`).

---

# 8. OS 4 REPORTS PEDIDOS

## 8.1 `holdup_aerador` — quanto ar fica retido
```
Tipo   : Volume Average
Scalar : Volume Fraction of Ar
Parts  : vol_aerador
```
**Unidade:** fração (0 a 1). Multiplique por 100 para %.
**Referência:** aeração industrial típica fica em **2 a 10 %**.

## 8.2 `SMD_aerador` — tamanho médio de bolha ⭐
**Não use Volume Average direto** — ele média sobre células SEM ar e o número perde sentido.
Use a **média ponderada pelo ar**:

| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `int_SMDxAr` | **Volume Integral** | `SMD_x_ar` | `vol_aerador` |
| b | `int_Ar` | **Volume Integral** | `ar_vol` | `vol_aerador` |
| c | **`SMD_aerador`** | **Expression** | `${int_SMDxAr} / ${int_Ar}` | |

**Referência (estudo anterior, lanças passivas): SMD = 2,53 mm.**

## 8.3 `frac_flotavel` — a resposta do estudo ⭐⭐
Fração do **AR** que está em bolhas menores que 200 µm.

**1)** Derived part:
```
Threshold `bolha_fina` : scalar = Sauter Mean Diameter
                         All Below · 2.0e-4 m
                         Input Parts = vol_aerador
```
**2)** Reports:

| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `ar_fino` | Volume Integral | `ar_vol` | **`bolha_fina`** |
| b | `ar_total` | Volume Integral | `ar_vol` | `vol_aerador` |
| c | **`frac_flotavel`** | **Expression** | `${ar_fino} / ${ar_total}` | |

**Referência anterior: ~0 %.** É este número que diz se o ejetor resolve o problema.

## 8.4 BALANÇO DE MASSA — pré-requisito de credibilidade

> ### ⚠️ Convenção de sinal
> No STAR-CCM+ a normal da face aponta para **FORA** da região.
> **Entrada é NEGATIVA, saída é POSITIVA.** O balanço é *"a soma de tudo dá zero"* — **sem `abs()`**.
>
> **Correção da versão anterior deste doc:** a expressão usava `abs()` em cada termo. Isso quebra
> no **Caso A**, onde ESPERAMOS fluxo reverso nas portas de ar (xarope subindo pela linha):
> com `abs()`, uma saída seria contada como entrada e o balanço fecharia **falsamente**.
>
> **Verificação no passo 1:** `m_xarope_in` deve ler **−46,9 kg/s**. Se ler +46,9, a convenção
> está invertida na sua instalação — troque os sinais. **Não avance sem conferir.**

### Bloco 1 — balanço TOTAL
| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `m_xarope_in` | **Mass Flow** | | `xarope_in` |
| b | `m_ar_in_1..4` | **Mass Flow** ⚠️ *mistura, NÃO Phase* | | `ar_in_1` … `ar_in_4` |
| c | `m_rea_out` | **Mass Flow** | | `superficie_reator` |
| d | **`balanco_massa`** | **Expression** | | `(${m_xarope_in}+${m_ar_in_1}+${m_ar_in_2}+${m_ar_in_3}+${m_ar_in_4}+${m_rea_out}) / abs(${m_xarope_in})` |

> ⚠️ Em (b) tem de ser **`Mass Flow`** e não `Phase Mass Flow`: o balanço precisa da massa da
> **mistura** — e é exatamente ali que o xarope pode sair pela linha de ar.
>
> `superficie_aerador` **não entra** no balanço: agora é `Wall`.

**Aceite: |`balanco_massa`| < 1 %.**

### Bloco 2 — balanço só do XAROPE *(o rigoroso)*
O balanço total não fecha exatamente em transiente se o ar acumula (gás é compressível).
O do xarope fecha sempre.

| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `mx_in` | **Phase Mass Flow** | Xarope | `xarope_in` |
| b | `mx_out` | **Phase Mass Flow** | Xarope | `superficie_reator` |
| c | **`mx_fuga_ar`** | **Phase Mass Flow** | Xarope | `ar_in_1..4` *(soma os 4)* |
| d | **`balanco_xarope`** | **Expression** | | `(${mx_in}+${mx_out}+${mx_fuga_ar}) / abs(${mx_in})` |

> ⭐ **`mx_fuga_ar` vale como diagnóstico por si só.** Positivo = xarope saindo pela linha de ar:
> a demonstração numérica mais direta de que a pressão na porta está acima do suprimento de ar.
> É a versão em número do que a **Cena 5** mostra em imagem.

### Bloco 3 — balanço do AR *(quanto fica retido)*
| # | Report | Tipo | Scalar | Parts |
|---|---|---|---|---|
| a | `mdot_ar_1..4` | **Phase Mass Flow** | Ar | `ar_in_1..4` |
| b | `m_ar_out` | **Phase Mass Flow** | Ar | `superficie_reator` |
| c | **`ar_retido`** | **Expression** | | `-(${mdot_ar_1}+${mdot_ar_2}+${mdot_ar_3}+${mdot_ar_4}+${m_ar_out})` |

**`ar_retido` [kg/s] = taxa de acúmulo de ar no domínio.** É o report que verifica na prática
a estimativa dos 150 s de bolsão (§1): enquanto for pequeno, o `Wall` com slip está justificado.

`Qar_total` (§3.1) continua usando os `mdot_ar_1..4` do Bloco 3 — sem mudança.

> **Não interprete `SMD_boca`, `frac_flotavel` nem `holdup_aerador` enquanto os Blocos 1 e 2
> não fecharem.**

---

# 9. HISTOGRAMA de tamanho de bolha ⭐

`Plots → New Plot → Histogram`

| Propriedade | Valor |
|---|---|
| **Parts** | **`vol_aerador`** |
| **X-Axis Scalar** | **Sauter Mean Diameter** |
| **Number of Bins** | **40** |
| **Range** | Manual: **0 a 4.0e-3 m** |
| **⭐ Weighting Function** | **`ar_vol`** |

## ⚠️ A ponderação é o ponto crítico
Sem ponderar, o histograma conta **células** — e a maioria das células do aerador **não tem ar
nenhum**. O resultado seria a distribuição espacial da malha, não da bolha.

> Ponderando por **`ar_vol` (= VF de ar × volume da célula)**, cada barra passa a significar
> **"quanto VOLUME DE AR existe nessa faixa de tamanho"** — que é a distribuição física.
>
> *É a mesma advertência da KB000033031 da Siemens sobre histogramas de parcels: "the histograms
> are weighted with particle count" para mostrar a distribuição de partículas e não de parcelas.*

## Leitura
Da curva acumulada saem **D10 · D50 · D90**, comparáveis direto com o estudo anterior:

| | lanças passivas (anterior) | ejetor (este estudo) |
|---|---|---|
| SMD médio | 2,53 mm | ? |
| moda | 1,90 mm | ? |
| D10 | 1,43 mm | ? |
| D50 | 2,32 mm | ? |
| D90 | 3,57 mm | ? |
| **<200 µm** | **~0 %** | **?** ⭐ |

---

# 10. SCENES — configuração detalhada

## Cena 1 — `VF_ar` ⭐ *(a principal)*
```
Scenes → New Scene → Scalar
  Displayer 1 (o ar):
     Parts        = ar_no_tanque   (threshold VF_ar > 0,01)
     Scalar Field = Volume Fraction of Ar
     Color Map    = blue-red balanced
     Range        = Manual 0 a 0,3
     Contour Style= Smooth Filled
  Displayer 2 (o contorno):
     New Displayer → Geometry
     Parts        = superfície do tanque (todas as boundaries de parede)
     Opacity      = 0,15
     Color        = cinza
```

## Cena 2 — `SMD` no corte
```
Scalar Scene
  Parts        = corte_vertical
  Scalar Field = Sauter Mean Diameter
  Range        = Manual 0 a 3.0e-3
  Color Map    = blue-red balanced
  + Geometry displayer com Opacity 0,15
```
> Coloque uma **linha de referência em 2,0e-4** no color bar (o alvo de 200 µm) — assim se
> enxerga na hora se alguma região atinge a meta.

## Cena 3 — `velocidade`
```
Parts = corte_vertical · Scalar = Velocity Magnitude
Range = Manual 0 a 25 m/s   (o bico dá ~20 m/s)
```

## Cena 4 — `bico_zoom` ⭐ *(mostra o jato)*
```
Parts  = corte_vertical
Scalar = Velocity Magnitude · Range 0 a 25
Câmera : Focal Point (0.025, -0.440, 1.855)
         Position    (0.025, -0.940, 1.855)
         Parallel Scale = 0.06     ← enquadra ~120 mm
```
Mostra os 7 jatos saindo dos furos Ø9 e a esteira até a lança.

## Cena 5 — `pressao_ejetor` ⭐⭐ *(a que explica a causa)*
```
Parts  = corte_vertical
Scalar = Absolute Pressure
Range  = Manual 195000 a 260000 Pa      (1 kgf/cm² man. = 199.392 Pa abs)
Câmera : Focal Point (0.025, -0.440, 2.20)
         Position    (0.025, -1.200, 2.20)
         Parallel Scale = 0.45          ← enquadra do bico ao header
+ Anotação de texto na cota da porta de ar
```
> **A imagem que fecha meses de discussão:** se a porta de ar aparecer em **vermelho/laranja**
> (pressão ACIMA de 199.392 Pa) em vez de azul, fica visível que **o ar não tem como entrar** —
> sem precisar de uma equação. Some com a Cena 4 e você tem a explicação completa em duas figuras.

---

# 11. PLANO DE RODADA

## 11.1 Física

| Item | Valor | Por quê |
|---|---|---|
| **Gravidade** | `(0, 0, −9,81)` ⚠️ **LIGADA** | sem empuxo o estudo de bolha não tem sentido |
| Reference Pressure | 101.325 Pa | |
| **Reference Density** | **0** | pressão de trabalho = manométrica real → `P_porta_ar` lê direto contra 98.067 Pa |
| **Regime** | **LAMINAR** | Re: lança 37 · furo do bico 36 · reator ~300–400 |
| Turbulent Dispersion | **OFF** | não há turbulência |
| Multifásico | EMP + Multiphase Segregated Flow + **S-Gamma** (quebra + coalescência) | |
| Arraste | Schiller-Naumann (ou Tomiyama) | |
| Tempo | **Implicit Unsteady**, 2ª ordem | S-Gamma é intrinsecamente transiente |

> ⚠️ **Se ρ_ref = 0 não for aceito:** use 1300 kg/m³, e então `ar_in_1..4` tem de ser prescrito
> como **88.763 Pa**, não 98.067 — a porta está 0,7295 m acima da referência
> (98.067 − 1300·9,81·0,7295 = 88.763).

> ⚠️ **Não use k-ε/k-ω.** Em Re ~40 o modelo gera µ_t espúrio que suprime justamente o gradiente
> viscoso que quebra a bolha — e a quebra é o que estamos medindo.

## 11.2 Solver

| Item | Valor |
|---|---|
| **Adaptive Time-Step** | CFL médio 1 · CFL máx 10 · Δt ∈ [2e-5 ; 5e-4] s |
| Iterações internas | 6–8 |
| URF velocidade | 0,5 |
| URF pressão | 0,25 |
| URF fração volumétrica | 0,4 |
| URF S-Gamma | 0,6 |

## 11.3 Partida limpa
1. Inicializar: VF ar = 0 em todo o domínio · velocidade 0 · pressão 0
2. Rodar os **primeiros ~0,05 s com as 4 `ar_in` como `Wall`** (só xarope, estabelece o campo)
3. Trocar para `Pressure Inlet` 98.067 Pa e seguir

*Evita o pulso inicial de ar num campo parado — é onde este tipo de caso costuma divergir.*

## 11.4 ⭐ Quando cada report passa a valer

| t físico | Válido a partir daqui | Escala de tempo que manda |
|---|---|---|
| **~0,5 s** | `P_porta_ar` · `v_bico` · Cena 5 | difusão de momento no ramal 4": R²/ν = 0,5 s |
| **~1,0 s** | `Qar_total` · `mdot_ar_1..4` | varredura da cabeça: 0,073 m³ ÷ 0,036 m³/s = 2,0 s |
| **~3,0 s** | `SMD_boca` · `VF_ar_boca` · **histograma** | trânsito na lança: 7,087 m ÷ 2,924 m/s = **2,42 s** |
| ~30–60 s | `holdup_aerador` · `frac_flotavel` | recirculação no tanque |

> ⚠️ **`SMD_boca` antes de ~3 s é lixo** — a boca ainda entrega o xarope da inicialização.

**Primeira parada sugerida: `Maximum Physical Time = 1,0 s`.**

---

# 12. OS DOIS CASOS

O ponto de projeto **não gera bolha nenhuma** (o ar não entra) — logo não responde sozinho à
pergunta do Ito. São necessários dois casos.

| | **Caso A — projeto** | **Caso B — cruzamento** |
|---|---|---|
| `xarope_in` | **1,12 m/s** (130 m³/h) | **0,046 m/s** (5,4 m³/h) |
| Base | vazão da bomba confirmada (Ito, 15/07) | limiar do bico 7×Ø9 as-built, `fase2/ejetor/10_LEI_arraste_de_ar.md` |
| Entrega | Cena 5 + `Qar_total` ≈ 0 → **prova 3D de que o ar não entra** | `SMD_boca` · `frac_flotavel` · histograma |
| Custo | alto | baixo (vazão 24× menor → Δt bem maior) |

## 12.1 Resultado ESPERADO do Caso A

*(já deduzido em `fase2/ejetor/11_LEI_MESTRA_P_vs_v.md` — serve para reconhecer sucesso, não bug)*

| Report | Esperado |
|---|---|
| `mdot_xarope_in` | **46,9 kg/s** ✅ |
| **`P_porta_ar`** | **~20–26 bar man.** (contrapressão do bico + atrito laminar da lança) |
| **`Qar_total`** | **≈ 0**, possivelmente **negativo** (xarope subindo pela linha de ar) |
| `SMD_boca` | indefinido — não há ar |

> **Fluxo reverso nas 4 `ar_in` É O RESULTADO, não um erro.** A porta de ar está ~24× abaixo
> da pressão local do xarope.

---

# 13. CHECAGENS DE 30 SEGUNDOS ANTES DO RUN

1. **Nenhum solver `Frozen`** — foi a armadilha mais cara do ciclone (nenhum erro, todos os
   reports devolvem zero corretamente).
2. **`superficie_aerador` = `Wall` com `Shear Stress Specification = Slip`** (não no-slip).
3. **Gravidade ligada** e apontando em **−Z**.
4. **VC1 = 1,0 mm ABSOLUTO**, não % da base. A base caiu de 30 mm → 100 mm; se os volumetric
   controls estiverem em porcentagem, VC1 virou 3,3 mm e o furo Ø9 ficou com **2,7 células**
   em vez de 9. *(A malha de 5,16 M é consistente com 1,0 mm absoluto — VC1 sozinho dá ~4,0 M —
   mas confirme no nó.)*
5. **`m_xarope_in` = −46,9 kg/s** no primeiro passo (negativo = entrando). Se der outro número,
   a BC está errada antes de qualquer física — e se der **+**46,9, a convenção de sinal da sua
   instalação é a oposta: inverta os sinais das expressões de balanço (§8.4).
6. **Não interprete nada** enquanto `balanco_massa` ou `balanco_xarope` > 1 %.
