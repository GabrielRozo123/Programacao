# Domínio fluido — válvula borboleta Bray 2-Cx, DN 100

Geometria CAD para estudo de cavitação em válvula borboleta estrangulada.

## Base dimensional

Manual técnico de vendas **Bray 2-Cx** (`PT_TSM_2Cx_20251030_01`), corpo wafer PN 10, DN 100 — válvula
borboleta revestida em PTFE para indústria química.

| Dimensão | Valor | Fonte |
|---|---|---|
| Face a face (B) | **52 mm** | catálogo p. 12 — confere com EN 558 Série 20 |
| Diâmetro da haste (ØG) | **16 mm** | catálogo p. 12, detalhe da haste |
| Corda do disco na face (K) | 88 mm | catálogo p. 12, nota 3 |
| Diâmetro de passagem | **100 mm** | ⚠ **não publicado** — ver calibração |

O revestimento em PTFE (espessura mínima 3 mm, catálogo p. 4) reduz o furo em relação ao nominal, mas
o catálogo não publica o valor. O corpo é tratado como **furo cilíndrico reto**, que é o que o
revestimento produz na prática.

### Calibração do furo — ❌ descartada

A ideia original era ajustar `D_BORE` até reproduzir os 909 m³/h publicados. **Isso está errado** — ver
a seção de resultados abaixo. O déficit de perda de carga não está no furo, e aumentar o furo o
pioraria. Com `D_BORE = 100 mm` o coeficiente de perda implícito no catálogo é **K = 0,194**,
plausível para borboleta de disco fino em abertura total.

---

## Resultados — 90°, monofásico permanente, água a 20 °C

Vazão de referência 70,7 m³/h (2,50 m/s). Tomadas de pressão a **2D montante / 6D jusante**
(IEC 60534-2-3), como `Surface Average` de `Static Pressure` em section planes.

### Independência de malha

| Custom Size no bloco | ΔP | Kv | vs catálogo (909) | F_L |
|---|---|---|---|---|
| 1,5 mm | 628 Pa | 892 m³/h | −1,9% | 0,30 |
| 1,0 mm | 667 Pa | 866 m³/h | −4,8% | 0,32 |

Variação de **3,0%** entre os dois níveis, **afastando-se** do catálogo. Malha não convergida — e o
Kv bruto é enganoso, porque inclui o atrito do tubo entre as tomadas.

### Tara: separando tubo de válvula

Rodada idêntica com `tubo_reto_tara.step` (sem disco, sem haste), mesma malha de 1,0 mm, mesmo bloco
de refino, mesmas sondas. Ver `gerar_tara.py`.

| | Medido | Referência | Desvio |
|---|---|---|---|
| ΔP total (com disco) | 667 Pa | — | |
| ΔP tara (só tubo) | **312 Pa** | 374 Pa (Colebrook, tubo liso) | **−17%** |
| **ΔP válvula** | **355 Pa** | 605 Pa (catálogo) | **−41%** |

```
K_CFD      = 355 / 3121 = 0,114
K_catálogo = 605 / 3121 = 0,194
```

### O catálogo publica Kv da válvula sozinha

Não é declarado no manual. Resolvido por plausibilidade: se o Kv de 909 fosse bruto (incluindo o
atrito das 8D entre tomadas), a válvula real teria K = (605 − 374)/3121 = **0,074** — baixo demais
para qualquer borboleta em abertura total, onde disco e haste deixam 10–15% de bloqueio e os valores
de manual (Idelchik, Crane TP-410, Miller) ficam entre 0,2 e 0,6.

### Decisão: abandonar 90° como ponto de calibração

Abertura total é o **pior caso possível** para este estudo e o menos relevante: a perda da válvula tem
a mesma ordem do atrito do tubo, é governada por camada limite, e não cavita nunca. O caso foi
transferido para **30°**, onde o ΔP é 300 vezes maior e o atrito do tubo cai para 0,2% do sinal.

O diagnóstico abaixo fica registrado como justificativa da mudança.

### Estado em 90°: dois erros independentes

| Erro | Magnitude | Causa | Correção |
|---|---|---|---|
| Atrito de tubo | −17% | y+ de buffer (5,5 a 13,1) | camada prismática |
| Perda de forma da válvula | −41% | parcialmente o mesmo y+; resto é geometria do disco | pendente |

O y+ medido cai na faixa 5–30, onde o tratamento All y+ interpola entre sublayer resolvida e função
de parede — a região de menor confiabilidade. Subir para y+ > 30 **não é viável**: a jusante do disco
há zonas separadas com tensão de parede tendendo a zero (y+ mínimo de 0,77 na sim com válvula).

Correção em curso: 18 camadas prismáticas, razão 1,3, primeira célula **0,019 mm** (y+ ≈ 1), aplicada
às **duas** sims. A tara serve de gabarito porque tem resposta analítica — só quando ela bater com os
374 Pa da Colebrook é que o déficit residual da válvula pode ser atribuído à geometria.

```
u_τ = V·√(f/8) = 2,50 · √(0,0150/8) = 0,108 m/s
y⁺ = 1  →  centroide a 9,3 µm  →  1ª camada ≈ 0,019 mm
```

Não executada — o caso migrou para 30°, onde o problema não se manifesta.

---

## ✅ Validação em 30° — monofásico permanente

Bloco de refino reposicionado (`1,5 mm`, cantos `[-0.070, -0.060, -0.060]` a
`[0.250, 0.060, 0.060]`), ~890 k células. Stagnation Inlet 5,0 bar abs, Pressure Outlet 4,0 bar abs.

| Grandeza | Valor |
|---|---|
| p1 (2D montante) | 498 199 Pa |
| p2 (6D jusante) | 400 335 Pa |
| ΔP | **97 864 Pa = 0,979 bar** |
| ṁ (Outlet) | 14,446 kg/s |
| Q | **52,10 m³/h** |
| **Kv** | **52,67 m³/h** |
| **Kv de catálogo** | **54** |
| **Desvio** | **−2,5%** |

σ = (498 199 − 2 339)/97 864 = **5,07** — bem acima de qualquer cavitação, portanto o monofásico é
legítimo neste ponto e a validação é limpa.

### Por que 30° valida e 90° não

| Ângulo | K_CFD | K_catálogo | Desvio |
|---|---|---|---|
| 90° | 0,114 | 0,194 | **−41%** |
| **30°** | **57,7** | **54,8** | **+5,3%** |

Mesma geometria, mesmo solver, mesma malha. Em 90° a perda é uma diferença pequena entre números
grandes, governada por camada limite — o pior caso para CFD RANS. Em 30° é arrasto de forma sobre
obstáculo rombudo com escoamento massivamente separado, que é o regime que o método resolve bem.

O desvio de 2,5% é da ordem da sensibilidade de malha medida em 90° (3,0% entre 1,5 e 1,0 mm).
Nenhum ajuste de geometria é necessário.

### Nota sobre a área livre projetada

Pico de velocidade observado: 7,13 m/s, contra 1,84 m/s no tubo — razão 3,87, ou área efetiva de
passagem ≈ 26% do tubo, contra os **16,8%** da fórmula `1 − (D_disc/D_bore)²·cos θ`. A fresta é
atravessada em ângulo e sua área real é ~1,5× a projetada. A fórmula é do memorial e nunca entrou no
solver; fica registrada como estimativa conservativa.

---

## Varredura de cavitação — protocolo

Stagnation Inlet fixo em 5,0 bar abs, Pressure Outlet varrido. Ver `../ponto_de_operacao.py` para a
curva analítica de referência (IEC 60534-2-1).

| Rodada | p2 [bar abs] | Física | Partindo de |
|---|---|---|---|
| 0 | 4,0 | monofásica | inicialização |
| 1 | 4,0 | **MMP + Schnerr-Sauer** | rodada 0 |
| 2–7 | 3,5 → 3,0 → 2,5 → 2,0 → 1,5 → 1,0 | MMP + Schnerr-Sauer | a anterior |
| 8 | 4,5 | MMP + Schnerr-Sauer | rodada 1 |

**A rodada 1 é verificação, não produção.** Em σ = 5,07 não há cavitação, então o solver multifásico
tem de reproduzir exatamente os 14,446 kg/s da rodada 0 com fração de vapor nula. Se reproduzir, a
montagem multifásica está verificada.

⚠️ **Nunca inicializar do zero com Schnerr-Sauer ativo.** O arranque da rodada 0 mergulhou para
−0,3 MPa por volta da iteração 8 antes de estabilizar. Em monofásico é inofensivo; com o modelo de
cavitação ligado, pressão negativa transitória gera vapor no domínio inteiro e o solver não se
recupera. Daí a descida em degraus.

Registrar por ponto: ṁ, p1, p2, p_mín (Volume Minimum de Static Pressure) e volume total de vapor.

```
F_L² = ΔP / (p1 − p_mín)
```

---

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `gerar_valvula.py` | Script paramétrico (cadquery ≥ 2.8) com memorial de cálculo |
| `valvula_borboleta_DN100_XXgraus.step` | Domínio fluido, um por ângulo (30° a 90°) |
| `previa_XXgraus.svg` | Vistas em corte da região da válvula |

Todos os STEP em **metros** (`SI_UNIT($,.METRE.)`), verificado na gravação — o script aborta se sair
em milímetros.

## Verificação após importação

| Item | Esperado |
|---|---|
| Sólidos | 1 |
| Faces | 7 |
| Volume do fluido | **11 700,3 cm³** |
| Comprimento | 1,500 m |
| Furo | 100 mm |

---

## As 7 faces

| Nome sugerido | Tipo | Área | Como identificar |
|---|---|---|---|
| `Inlet` | plano | 78,5 cm² | **x = −0,500 m** |
| `Outlet` | plano | 78,5 cm² | **x = +1,000 m** |
| `Pipe_Wall` | cilindro | 4708 cm² | a maior de todas |
| `Disc` | 2 esferas | 72,0 cm² cada | perto da origem, z ≷ 0 |
| `Stem` | 2 cilindros | 8,3 cm² cada | y ≈ ±39 mm |

Cinco grupos, sete faces. A haste aparece em dois pedaços porque o disco a atravessa pelo cubo — que
é o que acontece na válvula real.

**Plano de simetria em y = 0.** Para a varredura de Kv (regime permanente) vale cortar pela metade e
economizar metade do custo em cada um dos sete ângulos. Para o transiente de cavitação, rodar
completo — o desprendimento de nuvem pode ser assimétrico.

---

## Malha estimada

| Zona | δx | Células |
|---|---|---|
| Região do disco (2D) | 1,5 mm | ~465 000 |
| Restante do tubo | 4,0 mm | ~160 000 |
| **Total** | | **~625 000** |
| Com simetria em y = 0 | | ~312 000 |

Domínio de **5D a montante** e **10D a jusante**. O comprimento a jusante é generoso de propósito: é
lá que ocorre a recuperação de pressão, que é o que define o F_L.

---

## A validação: Kv publicado

O catálogo (p. 17) publica Kv em nove ângulos. Para DN 100:

| Ângulo | 90° | 80° | 70° | 60° | 50° | 40° | 30° | 20° | 10° |
|---|---|---|---|---|---|---|---|---|---|
| **Kv** [m³/h] | 909 | 702 | 435 | 247 | 153 | 94 | 54 | 23 | 3 |

Conversão: `Q [m³/h] = Kv · √(ΔP [bar] / densidade relativa)`

### Escopo: 30° a 90°

Abaixo de 30° o Kv passa a ser dominado pela **folga entre disco e sede** — geometria de vedação que
este modelo não representa. Os ângulos de 20° e 10° estão na tabela para referência, mas **não devem
ser simulados** com esta geometria.

---

## O achado que já está na tabela

Comparando a queda do Kv com a queda da área livre projetada:

| Ângulo | Queda de Kv | Queda de área | Razão |
|---|---|---|---|
| 90° | 1,0 | 1,0 | 1,00 |
| 70° | 2,1 | 1,5 | 1,40 |
| 50° | 5,9 | 2,6 | 2,27 |
| 30° | **16,8** | **5,9** | **2,83** |

A área livre cai por geometria. O **Kv cai quase três vezes mais rápido** — porque o coeficiente de
descarga também despenca: a passagem vira duas frestas em meia-lua com escoamento tortuoso.

É dessa diferença que nasce a cavitação. Mesma vazão, muito mais perda de carga, vena contracta
profunda.

### Em números de processo

Para **70,7 m³/h** de água (≈ 2,5 m/s em DN 100):

| Ângulo | ΔP |
|---|---|
| 90° | 6 mbar |
| 60° | 82 mbar |
| 40° | 0,57 bar |
| 30° | **1,71 bar** |
| 20° | **9,45 bar** |

A válvula é **PN 10**. Estrangulada a 20°, a perda de carga consome praticamente toda a pressão
nominal para passar a mesma vazão.

---

## Física no STAR-CCM+

```
Segregated Flow
Eulerian Multiphase (VOF ou Mixture)
   → Multiphase Interaction → Cavitação (Schnerr-Sauer)
Turbulência: Realizable k-ε Two-Layer, All y+
```

Entradas: **pressão de vapor** do líquido na temperatura de operação (água a 20 °C: 2 339 Pa),
densidade de núcleos e diâmetro inicial de bolha — estes dois são os parâmetros de sensibilidade.

### Condições de contorno

| Contorno | Tipo |
|---|---|
| `Inlet` | Velocity Inlet ou Mass Flow — fixar a vazão de serviço |
| `Outlet` | Pressure Outlet — **é esta que se varre** para produzir a curva |
| `Pipe_Wall`, `Disc`, `Stem` | Wall, sem escorregamento |

Fixando a vazão e baixando a contrapressão, você atravessa o regime de cavitação incipiente até o
escoamento estrangulado.

---

## O entregável que o catálogo não tem

O catálogo publica **Kv**. Ele **não publica F_L**, o fator de recuperação de pressão — que é
justamente o parâmetro que a IEC 60534 usa para prever cavitação.

```
F_L² = (p1 − p2) / (p1 − p_vc)
```

Extraindo a pressão mínima na vena contracta do CFD, você obtém o F_L em cada ângulo. Isso permite
responder a pergunta que o usuário da válvula realmente tem: **a partir de que abertura, e com que
pressão a montante, esta válvula cavita no meu processo?**

Validar contra o Kv publicado dá credibilidade. Entregar o F_L dá utilidade.
