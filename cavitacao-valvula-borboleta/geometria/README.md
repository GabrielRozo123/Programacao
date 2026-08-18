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

### Calibração do furo

O diâmetro de passagem é o parâmetro geométrico mais incerto e o que mais afeta o Kv. Procedimento:

1. Rodar o caso de **90°** e calcular o Kv resultante
2. Ajustar `D_BORE` até reproduzir os **909 m³/h** publicados
3. Os **outros seis ângulos passam a ser previsão**, não ajuste

Um ponto para fixar a geometria, seis para validar. Com `D_BORE = 100 mm` o coeficiente de perda
implícito é **K = 0,19**, plausível para borboleta de disco fino em abertura total.

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
