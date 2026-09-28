# 02 — Método CFD e análise de envelope (antes de simular)

> Mesma lógica que funcionou no ciclone Valgroup (Lapple) e no tanque chiller da GreyLogix:
> **montar a régua analítica antes de rodar**, para saber a ordem de grandeza esperada,
> dimensionar a matriz de cenários e ter com o que comparar o CFD.
> Script: [`regua_pluma_gaussiana.py`](regua_pluma_gaussiana.py)

---

## 1. ⭐ A decisão de modelagem que define o custo do projeto

### O O₃ é escalar passivo
A 3 ppm, a diferença de densidade da nuvem para o ar é de **2 × 10⁻⁶**. A nuvem não tem
flutuabilidade própria — é arrastada pelo vento como um traçador.

Sem modelo de gás denso. Um **escalar passivo transportado** resolve. E daí vêm três
consequências, sendo a terceira a que muda o cronograma:

1. O **campo de vento não depende da fonte** — roda uma vez por condição meteorológica.
2. O transporte do escalar é **linear na vazão da fonte**.
3. Portanto:

```
C(x) = Q · f(x)
```

`f(x)` é o campo de uma **fonte unitária**. Resolvido uma vez, **todos os limiares**
(0,01 · 0,2 · 0,5 · 3 ppm) e **todas as vazões de vazamento** saem por escala, sem re-rodar.

> **A matriz de cenários é, portanto, indexada por
> (direção × velocidade × estabilidade × ponto de emissão)** — nunca por limiar nem por vazão.
> Os 26 cenários da Etapa 4 devem ser contados assim.

### Estratégia de execução proposta
1. **Campo de vento** — RANS estacionário, k-ε Realizable, perfil de camada limite atmosférica
   na entrada. Uma rodada por condição meteorológica.
2. **Congela o escoamento.** Resolve o escalar passivo para cada fonte.
   Cada fonte adicional custa quase nada.

É a mesma lógica do campo congelado do Lagrangeano no ciclone.

---

## 2. A régua — pluma gaussiana com coeficientes de Briggs

```
C(x,0,0) = Q / (π · u · σy · σz) · exp(−H² / 2σz²)
```

Conversão: **1 ppm de O₃ a 25 °C = 1,962 mg/m³**

### Distância até cada limiar
**[SUPOSTO]** Q = 1 g/s (3,6 kg/h) · fonte no solo · terreno urbano/industrial.
*A vazão real da fonte é a pendência nº 1. Como C é linear em Q, basta reescalar.*

| cenário | 0,01 ppm | 0,2 ppm | 0,5 ppm | 3 ppm |
|---|---|---|---|---|
| D · 5 m/s (diurno típico) | 407 m | **86 m** | 54 m | 22 m |
| D · 3 m/s (diurno fraco) | 535 m | 112 m | 70 m | 29 m |
| E · 2 m/s (transição) | 1 432 m | 237 m | 145 m | 57 m |
| **F · 1,5 m/s (noturno estável)** | **1 745 m** | **278 m** | 169 m | 66 m |

---

## 3. ⚠️ A premissa que está faltando no cronograma — estabilidade atmosférica

A Etapa 3 fala em **"vento típico"**. Mas **o pior caso de dispersão não é vento forte — é
vento fraco com atmosfera estável** (inversão noturna, classe F de Pasquill). É quando a nuvem
não se dilui e viaja longe concentrada.

### O tamanho do efeito

| | distância até 0,2 ppm | vazão que já basta para 0,2 ppm a 100 m |
|---|---|---|
| D · 5 m/s | 86 m | 4,80 kg/h |
| D · 3 m/s | 112 m | 2,88 kg/h |
| E · 2 m/s | 237 m | 0,71 kg/h |
| **F · 1,5 m/s** | **278 m** | **0,54 kg/h** |

**Fator de 3,2× em distância e de 9× em vazão de fonte** entre o caso típico e o noturno
estável. Um vazamento que é inofensivo às 14 h isola a área às 3 h da manhã.

> **A estabilidade tem que ser um eixo da matriz de cenários**, não nota de rodapé.
>
> ⚠️ O dado meteorológico da planta (velocidade e direção horária) **provavelmente não traz
> estabilidade**. Ela se infere de hora do dia + velocidade + cobertura de nuvens (método de
> Pasquill-Turner). Pedir os dados **com timestamp horário** para poder fazer isso.

---

## 4. ⚠️ Segunda premissa: rugosidade do terreno

| cenário | rural | urbano/industrial | razão |
|---|---|---|---|
| D · 5 m/s | 197 m | 86 m | 2,3× |
| D · 3 m/s | 259 m | 112 m | 2,3× |
| E · 2 m/s | 517 m | 237 m | 2,2× |
| F · 1,5 m/s | 1 086 m | 278 m | 3,9× |

**Terreno rural dá distâncias 2 a 4× maiores.** A planta em si tem rugosidade de sítio
industrial, mas **o entorno da LD Celulose é agrícola** — e a nuvem que sai da planta cai
justamente em terreno aberto. Isso é uma decisão de premissa da Etapa 2, não um detalhe
de setup.

No CFD isso entra como o **z₀ do perfil de entrada** e como a rugosidade de parede do solo.

---

## 5. ⭐ A recomendação que pode resolver o problema sem isolar nada

Efeito da altura de descarga (classe D, 5 m/s, Q = 1 g/s):

| altura da descarga | pico de O₃ no solo | 0,2 ppm alcança |
|---|---|---|
| 5 m | **0,837 ppm** | 82 m |
| 10 m | 0,209 ppm | 60 m |
| **15 m** | **0,093 ppm** | **não atinge** |
| 20 m | 0,052 ppm | não atinge |
| 30 m | 0,023 ppm | não atinge |

**Subir a descarga de 5 para 15 m derruba o pico no solo de 0,84 para 0,093 ppm — abaixo do
limiar de isolamento.** Mesma vazão, mesma fonte.

> Se o arranjo atual descarrega baixo ou horizontalmente, **a recomendação ao cliente pode ser
> "elevar a descarga", e não "isolar uma área maior".** Isso muda o valor do estudo: sai de
> mapa de consequência para recomendação de engenharia.

⚠️ **Mas atenção ao downwash.** Chaminé alta só funciona se a razão `v_saída / v_vento` for
maior que ~1,5. Abaixo disso o vento derruba a pluma na esteira do prédio e a altura não
adianta nada. **Esse é exatamente o efeito que a gaussiana não captura e o CFD captura** —
é um dos argumentos centrais para o estudo existir.

---

## 6. ⭐ Escopo do domínio — como fazer 26 cenários caberem em 21 dias

Diretrizes de CFD para dispersão em torno de prédios (**COST Action 732** / **AIJ**) pedem o
domínio dimensionado pela altura H do obstáculo dominante: 5H a montante, **15H a jusante**,
5H lateral e no topo.

- H = prédio de O₃ (~15–20 m) → domínio ~400 × 200 × 100 m. **Viável.**
- H = torres da planta (~50 m) → domínio de 1 km, dezenas de milhões de células. **Inviável
  em 21 dias.**

### A saída: separar campo próximo de campo distante

Olhando de novo a tabela de §2, **todos os limiares que importam para isolamento ficam
dentro de ~300 m**:

| limiar | alcance máximo (F · 1,5 m/s) | ferramenta |
|---|---|---|
| 3 ppm | 66 m | **CFD** |
| 0,5 ppm | 169 m | **CFD** |
| 0,2 ppm | 278 m | **CFD** |
| 0,01 ppm | **1 745 m** | gaussiana / modelo integral |

> **Proposta:** CFD num domínio de ~500 m a jusante, que cobre com folga os contornos de
> 3 · 0,5 · 0,2 ppm — exatamente os que definem isolamento de área e posicionamento de
> sensores. O contorno de 0,01 ppm, que está a 1,7 km, sai do **modelo analítico**, onde os
> prédios já não importam e a gaussiana é a ferramenta certa.
>
> Isso mantém o CFD tratável **e** entrega a escada de limiares completa. É uma decisão a
> defender na apresentação da Etapa 2.

---

## 7. Modelo numérico proposto (consolidado)

| item | escolha | observação |
|---|---|---|
| Regime | Estacionário (RANS) para exaustor e off-gás | contínuos |
| | **Transiente** para as PSVs | é sopro — importa o histórico, não o campo médio |
| Turbulência | **k-ε Realizable** | recomendado pelas diretrizes COST/AIJ para CLA |
| Espécie O₃ | **escalar passivo** | ver §1 |
| Entrada | perfil logarítmico de camada limite atmosférica + k e ε consistentes | z₀ conforme §4 |
| Solo | parede rugosa compatível com z₀ | consistência entre perfil e parede é o erro clássico |
| Exaustores | **interface de ventilação** com curva do ventilador | pedido do Marcus — ver `03` |
| Decaimento do O₃ | desprezado | meia-vida ≫ tempo de trânsito; conservador e correto |
| Domínio | ~500 m a jusante | ver §6 |

> **Nota sobre RANS:** subestima a dispersão lateral em relação ao real. Isso é **conservador**
> para a concentração na linha de centro, e deve ser declarado no relatório como tal.

---

## 8. O que o CFD faz que a régua não faz

A gaussiana já dá as distâncias em terreno livre. **O CFD existe para os prédios:**

- **recirculação na esteira** — a nuvem pode ser sugada para baixo e ficar presa a sotavento
- **efeito canyon** entre estruturas — corredores de alta concentração
- **aprisionamento em pátios fechados** e sob estruturas
- **downwash** na descarga dos exaustores (§5)
- **campo próximo** (< 10 m), dominado pelo momento do jato

**É exatamente nesses lugares que os sensores têm que ir** — e é isso que justifica o estudo
para o cliente.
