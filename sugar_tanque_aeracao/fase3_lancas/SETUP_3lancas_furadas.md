# SETUP — Aerador com 3 lanças perfuradas (opção B) · Fase 3 · Ito

> Geometria: `aerador_3lancas_furadas_fluido.step` — 20,2721 m³ · **163 faces**.
> Ponto de operação: **opção B** — 40 m³/h de ar mantidos, 98,2 m/s no furo.
> Objetivo do Ito: reduzir o SMD para 0,2 mm e distribuir o ar no tanque.

---

## 0. ⚠️ IMPORTAÇÃO — a armadilha que invalida tudo

O furo de 1,0 mm ocupa **1,57° de arco** no cilindro Ø73. A tesselação padrão do
STAR usa ~5° por faceta: **o furo inteiro cabe dentro de uma faceta e desaparece**,
sem erro nenhum.

```
Import Surface Mesh → Tessellation Density = VERY FINE
```

**Confirme depois de importar:** 163 faces, sendo 144 cilindros de R = 0,5 mm.
Se vier menos, a importação comeu os furos — reimporte.

---

## 1. Contornos

| contorno | quantas faces | tipo |
|---|---|---|
| `aerador.casco` | 1 (+ fundo cônico) | Wall |
| `aerador.topo` | 1, em z = 1220 | superfície livre |
| `lanca.parede_ext` | 3 · cilindro R 36,5 | Wall |
| `lanca.parede_int` | 3 · cilindro R 31,34 | Wall |
| `lanca.tampa` | 3 · disco no fundo | Wall |
| **`lanca.furos`** | **144 · cilindro R 0,5** | Wall ⭐ *surface size aqui* |
| **`lanca.inlet`** | 3 · disco Ø62,68 em z = 1220 | **Mass Flow Inlet** |

> A topologia mudou de propósito em relação às rodadas anteriores: **o interior da
> lança está no domínio fluido**. O ar entra pelo topo e se distribui sozinho entre
> os 48 furos, em vez de a distribuição ser imposta pela condição de contorno.

---

## 2. Cilindros de refino — coordenadas

Monte como `Part → Cylinder` e use em `Volumetric Control`.

**Um cilindro por lança, três no total.** Cada um envolve os 48 furos inteiros.

| lança | Start X | Start Y | Start Z | End X | End Y | End Z | Radius | **célula** |
|---|---|---|---|---|---|---|---|---|
| 1 | 200.0 | -745.0 | -5265.0 | 200.0 | -745.0 | -5115.0 | **75.0** | **2,0 mm (4 %)** |
| 2 | 464.4 | -288.0 | -5265.0 | 464.4 | -288.0 | -5115.0 | **75.0** | **2,0 mm (4 %)** |
| 3 | -64.4 | -288.0 | -5265.0 | -64.4 | -288.0 | -5115.0 | **75.0** | **2,0 mm (4 %)** |

Ø150 × 150 mm: cobre de 18,5 mm abaixo da tampa a 86,5 mm acima do anel superior.

### Por que não há cilindro de pluma

```
Re do jato = ρ_xarope · v · d / µ = 1350 · 98,2 · 0,001 / 6,5 = 20
```

**O jato de ar é viscoso e morre em poucos diâmetros.** Num líquido tipo água o Re
seria 98 000 e a pluma exigiria um segundo nível de refino a jusante. Neste xarope
não há near-field distante a resolver — o cilindro de Ø150 já contém tudo o que
acontece.

⚠️ **End X = Start X e End Y = Start Y.** Foi o que deixou o cilindro inclinado da
outra vez.

### Mais um controle, sem cilindro

O interior da lança tem Ø62,68 — **não cabe uma célula da malha base de 50 mm**.
Crie um `Volumetric Control` sobre a própria *part* das lanças (ou um cilindro
Ø70 de z = −5240 a 1220) com **12 mm (24 %)**.

---

## 3. Malha

| | |
|---|---|
| modelo | Trimmed + Prism Layer |
| **Base Size** | **50 mm** |
| **Surface Size em `lanca.furos`** | **0,25 mm absoluto** ⭐ |
| Surface Growth Rate | 1,3 |
| Prism | 2 camadas nas paredes das lanças; **desligue nos furos** |

**O refino fino sai do surface size, não de controle volumétrico.** São 144 furos —
montar um controle por furo é inviável e desnecessário: o trimmer refina sozinho a
partir da superfície e cresce até o cilindro de 2 mm.

### Estimativa

| região | células |
|---|---|
| entorno dos 144 furos (surface size) | 7,2e5 |
| REFINO_LANCA (3×) | 9,9e5 |
| interior das lanças | 3,5e4 |
| tanque na base de 50 mm | 1,6e5 |
| **total com transições** | **≈ 2,9e6** |

### ✅ Malha gerada — resultado real

| | |
|---|---|
| **células** | **4 436 386** *(53 % acima da estimativa — normal)* |
| validade topológica | sem células de volume negativo |
| face validity < 0,95 | **10 células** (0,000 %) |
| volume change < 1e-2 | **82 células** (0,002 %), mínimo 1,86e-3 |
| extensões | 2,032 × 2,032 × 7,112 m, centro (0,200; −0,440) ✅ |

### ⭐ A verificação que os relatórios de qualidade NÃO fazem

Validade e extensão continuariam perfeitas com os 144 furos fechados. O teste é a
**área do contorno `lanca.furos`** (`Report → Sum` de `Area: Magnitude`):

| | |
|---|---|
| nominal `144 · π · 1,0 · 5,16` | 2,3343e-3 m² |
| **medido na malha** | **2,2653e-3 m²** |
| desvio | **−2,96 %** |

O desvio é o polígono inscrito: o círculo do furo está com **7 a 8 segmentos retos**
(7 lados dão 96,7 % do perímetro, 8 dão 97,5 %). É a discretização funcionando, não
defeito.

**Use a área EFETIVA no pós-processamento**, não a nominal:

| | nominal | **efetivo** |
|---|---|---|
| área de garganta | 113,10 mm² | **109,75 mm²** |
| velocidade no furo | 98,2 m/s | **101,2 m/s** |
| ΔP no furo | 28 223 Pa | **29 969 Pa** *(vai com 1/A²)* |
| We do gás | 333 | **353** |

Nenhuma conclusão muda — segue fundo em regime de jato, uniformidade folgando por
fator 140. Refinar para recuperar 3 % multiplicaria por ~4,6 as células do entorno
dos furos.

Se apertar, duas saídas na ordem: cilindro para **Ø120 × 120** (→ 2,1e6) ou célula
para **3,125 mm** (→ 1,8e6). Reduzir o cilindro é preferível a engrossar a célula.

Contra as ~4e5 da rodada de 16 lanças. É 5× maior, não 50×.

---

## 4. Física

Igual às rodadas anteriores, exceto onde marcado.

| | |
|---|---|
| solver | **Eulerian Multiphase**, transiente, implícito |
| fases | `Xarope` (contínua) · `Ar` (dispersa) |
| xarope | ρ **1350** kg/m³ · µ **6,5** Pa·s · σ **0,058** N/m |
| ar | gás ideal |
| distribuição de tamanho | **S-Gamma** com **Breakup** e **Coalescence** *(seleções separadas)* |
| turbulência | ver §4.2 |
| gravidade | ligada · Reference Density = 1350 |

### 4.1 Entrada de ar — `lanca.inlet`

40 m³/h medidos **no furo**, onde a pressão absoluta é 186 964 Pa (1,870 bar).

| T do xarope | ρ do ar | **ṁ total** | **ṁ por lança** |
|---|---|---|---|
| 60 °C | 1,955 kg/m³ | 21,72 g/s | **7,240 g/s** |
| 70 °C | 1,898 kg/m³ | 21,09 g/s | **7,029 g/s** |
| 80 °C | 1,844 kg/m³ | 20,49 g/s | **6,830 g/s** |

⚠️ **Confirmar a temperatura de operação com o Ito.** Entre 60 e 80 °C a vazão
mássica varia 6 %.

`Backflow Specification → Scalars = Extrapolated`.

### 4.2 SMD prescrito na entrada — **1,0 mm**

Use **o mesmo valor das rodadas de 3 lanças com descarga aberta**.

> Esta rodada mede **distribuição**, não diâmetro de bolha. Mantendo o SMD igual ao
> das rodadas anteriores, a **única** variável que mudou é a geometria da descarga —
> e o efeito da perfuração sobre a distribuição fica isolado.
>
> O diâmetro de bolha real em `We = 333` **não sai de correlação nenhuma** — a lei de
> Tate vale só em borbulhamento. Ele vem da rodada VOF de um furo
> (`dominio_1furo_vof.step`). Se o VOF devolver valor muito diferente de 1,0 mm,
> esta rodada é refeita com ele.

### 4.3 Turbulência

Ligada. Lembre que em EMP é **por fase**: `Eulerian Phases → Xarope → Models`.
Desligar no continuum não basta — foi o que causou a divergência da vez passada.

---

## 5. ⚠️ Passo de tempo — o ponto caro da opção B

98,2 m/s atravessando células de 0,25 mm é uma combinação severa:

| região | célula | Δt para CFL = 1 |
|---|---|---|
| **furo** | 0,25 mm | **2,5e-6 s** |
| cilindro de refino | 2 mm | 2,0e-5 s |
| tanque na base | 50 mm | 5,1e-4 s |

Com o Δt = 1e-3 das rodadas anteriores, o CFL local no furo seria **393**.

**Não tente resolver o transiente do jato.** Ele atinge regime quase-permanente em
microssegundos; o que interessa é o acúmulo de ar, em segundos. Estratégia:

| fase | Δt | passos | para quê |
|---|---|---|---|
| arranque | **1e-5 s** | ~500 | estabelecer os 144 jatos |
| transição | **1e-4 s** | ~2 000 | ar preenche a banda perfurada |
| produção | **5e-4 s** | até parar | desenvolvimento da pluma |

Inner iterations: **8 a 10**. Vigie os resíduos na troca de patamar — é ali que
diverge, se for divergir.

### O que esperar em tempo físico

A bolha de 1 mm sobe a **0,113 mm/s** em xarope de 6,5 Pa·s (Stokes) — leva **883 s**
para subir 100 mm. As rodadas anteriores pararam em 0,18 s e por isso o relatório
diz que elas caracterizam a **formação**, não o regime.

Aqui é a mesma limitação. O que esta rodada pode entregar com honestidade:

| entregável | tempo físico necessário |
|---|---|
| distribuição do ar entre os 144 furos | **~0,05 s** ✅ |
| forma e coalescência dos jatos junto à banda | ~0,2 s ✅ |
| pluma subindo 100 mm | ~900 s ✗ inviável |
| distribuição no tanque em regime | horas ✗ inviável |

**Registre isso no relatório desde já**, com a mesma nota de rodapé das rodadas
anteriores. É a limitação física do fluido, não do modelo.

---

## 6. Reports a criar antes de rodar

| report | tipo | para quê |
|---|---|---|
| `mdot_por_furo` | Surface Integral de fluxo em `lanca.furos` | ⭐ **verificar a uniformidade** |
| `P_interior_lanca` | Surface Average de pressão em `lanca.parede_int` | ΔP interno |
| `alpha_medio` | Volume Average de VF de ar | inventário |
| `V_aerado` | Volume Integral com threshold α > 1 % | comparável às rodadas anteriores |
| `SMD_hist` | Histograma de d32 ponderado por volume de ar | binning **0,70 a 1,02** |

> No histograma, **não fixe o mínimo em 0,99**. Foi o erro que escondeu a cauda da
> vez passada; o mínimo real era 0,7283.

### Previsões a registrar ANTES

| | previsto |
|---|---|
| velocidade no furo | **98,2 m/s** |
| razão de uniformidade ΔP_furo / ΔP_hidro | **142** ⇒ vazão praticamente igual nos 144 furos |
| ΔP através do furo | ≈ 28 200 Pa |
| pressão de suprimento | ≈ **1,16 kgf/cm²** |
| dispersão de vazão entre furos | **< 2 %** |

Se a dispersão entre furos vier bem acima de 2 %, há erro de montagem — não física.

---

## 7. Se ficar pesado demais

O Marcus autorizou cair para uma lança. **Atenção: com 1 lança a opção B não
fecha.** 48 furos a 40 m³/h dariam **295 m/s** — Mach 0,8, fora de qualquer
premissa nossa.

Com uma lança só, a vazão teria de cair para **≈ 13,6 m³/h** (34 % do projeto) para
manter o furo em ~100 m/s. Isso vira demonstração de mecanismo, não ponto de
projeto — e precisa ser dito assim no relatório.

**Alternativa melhor que reduzir para 1 lança:** manter as 3 e representar os furos
como *manchas de entrada* na parede externa, sem túnel. Perde-se a distribuição
interna (que de todo modo folga por fator 142), a malha cai para ~4e5 e o Δt sobe
para 1e-3. Vale se o tempo de máquina apertar.
