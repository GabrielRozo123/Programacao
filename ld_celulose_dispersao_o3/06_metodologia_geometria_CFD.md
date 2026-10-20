# 06 — Como a geometria do CFD foi obtida a partir do CAD da planta

> Nota metodológica (20/10/2026) para a equipe CAEXPERTS. Explica **o que** foi feito com o CAD da LD
> Celulose, **por que** e **com base em quê**. Serve de base para o capítulo de geometria do relatório.
> Sem coordenadas nem layout do cliente (ficam em `_privado/`). Critérios detalhados: `05_limpeza_CAD_criterios.md`.

---

## 1. O problema

O cliente enviou o modelo 3D de **projeto da planta** (origem AVEVA/E3D, convertido para Solid Edge): dez
subconjuntos (civil, estrutura metálica, mecânica, elétrica, instrumentação) com **mais de 40 mil peças** —
estacas, fundações, tubulação, válvulas, escadas, guarda-corpos, parafusos, guindastes de montagem, interiores
de equipamentos. Esse nível de detalhe serve para construir a planta, **não para simular o vento**: a maior parte
das peças é menor que a célula da malha, fica enterrada ou dentro de equipamentos fechados, e só criaria problemas
de malha.

Limpar peça a peça no Solid Edge levaria semanas e dependeria de reposicionar objetos à mão.

## 2. O princípio (literatura)

O nível de detalhe da geometria vem **da pergunta do estudo e da malha**, não do CAD:

1. **Só entra o que o vento "vê"** — nada enterrado, interno ou temporário.
2. **Só entra o que a malha resolve** — objeto menor que ~2 células não é representado; vira problema de malha.
3. **O detalhe cai com a distância da fonte** — perto dela a geometria define esteira e recirculação; longe, só os
   volumes grandes importam (ou viram rugosidade do terreno).

Base: diretrizes de CFD atmosférico **COST Action 732** (Franke et al., 2007) e **AIJ** (Tominaga et al., 2008);
**Ricci et al. (2017)**, que mostram que a simplificação geométrica pesa mais no resultado do que as condições de
entrada e o modelo de turbulência; **Liu et al. (2018)** sobre a influência dos vizinhos (abrigo e canalização);
**Thakur et al. (2009)** sobre simplificação de CAD para simulação; e a abordagem de **porosidade / resistência
distribuída** (FLACS; Ahmed et al., 2016) para aglomerados de objetos pequenos.

**Zonas de detalhe** em torno do prédio de O₃:
| zona | alcance | detalhe |
|---|---|---|
| Z0 — fonte | ~3H do prédio | prédio, terraço e **descargas reais dos exaustores**; vizinhos como volumes simples |
| Z1 — interesse | ~300 m (alcance dos limiares de concentração) | prédios como caixas, silos e torres como cilindros |
| Z2 — entorno | até a borda do domínio | só volumes grandes, ou rugosidade do terreno |

## 3. O que foi feito

### 3.1 Ler o CAD **com os nomes**, fora do Solid Edge
- Cada subconjunto foi exportado em **STEP** (compactado em RAR dividido para transferência).
- O STEP foi lido com **OpenCascade** (biblioteca de CAD aberta, via Python), preservando a árvore e o **nome de
  cada peça**. Para cada peça: nome, caixa envolvente em coordenadas da planta, maior dimensão, nº de faces.
- Resultado: **inventários em planilha** de cada subconjunto (de 192 a 25 mil peças cada), com as posições
  originais exatas — sem reposicionar nada à mão.

### 3.2 Classificar por **nome + tamanho + posição**
A nomenclatura de projeto (AVEVA) é informativa e foi usada como regra:
| padrão no nome | o que é | decisão |
|---|---|---|
| `PILE`, `BLOCK_P`, `BASES`, `FUND`, `TUB-AP`… | fundações e estacas (abaixo do piso) | sai |
| `FITTING`, `SCTN`, `FRMWORK`, `BEANS`, `COLUMNS`, `PANEL` (grades) | estrutura, conexões, perfis | sai (treliça ≈ transparente ao vento) |
| `ESCADA`, `HANGER`, `PS-…` (suportes), `AIDGROUP` (aterramento) | acessórios | sai |
| `CRANE` | guindastes de montagem (até 74 m) | sai (temporários) |
| `GWALL`, `STWALL`, lajes | envoltória de prédios | fica |
| tags de equipamento `1xxx-yy-zzz` | tanques, silos, torres, exaustores | fica, se grande e na zona |

Em seguida, cada equipamento foi agrupado pelo seu **tag**, com a caixa envolvente do conjunto, a altura e a
**distância ao prédio de O₃** — e mantido ou descartado pelos critérios de zona e tamanho.

> Um achado típico do método: **suportes de tubulação a 20–58 m de altura** (que saem) revelaram **torres altas
> coladas no prédio de O₃** antes mesmo de abrir o subconjunto delas.

### 3.3 Reconstruir por **primitivas**, nas posições originais
Os objetos que ficam foram reconstruídos como **caixas e cilindros** (diâmetro e altura do inventário) por um
script que lê uma tabela (uma linha por objeto) e gera um **STEP limpo**: sólidos fechados, sem interferências,
nomeados, em metros e com origem local no prédio de O₃ (evita o limite de 1 km do Parasolid e problemas de
precisão com coordenadas de dezenas de km).

### 3.4 As fontes, com a geometria real
As **descargas dos 4 exaustores** foram lidas da geometria real dos bocais (face, área e normal) e **conferidas
contra os manuais** (área do flange × vazão/velocidade de descarga). Entram como faces nomeadas — os contornos de
vazão no STAR. Resultado: 2 descargas **horizontais** (LX 816) e 2 **verticais sob a cobertura** do terraço
(HL 4S) — informação que muda o comportamento da pluma e não estava nos documentos.

### 3.5 O interior do prédio fica de fora — de propósito
O cenário de vazamento (trinca na alimentação dos misturadores) acontece **dentro** do prédio; os exaustores
levam o O₃ para fora. Como o estudo é de dispersão **externa**, a fonte entra **na descarga dos exaustores**, com
concentração = vazão de O₃ vazada ÷ vazão de exaustão (mistura completa no ambiente).

## 4. Resultado

| | antes | depois |
|---|---|---|
| peças | > 40 mil (10 subconjuntos, ~4 GB de STEP) | **38 sólidos** nomeados |
| geometria | facetada, com frestas, enterrados, interferências | fechada, estanque, sem interferências |
| coordenadas | da planta (dezenas de km da origem) | locais (metros, origem no prédio de O₃) |
| fontes | não identificadas | 4 descargas reais, direção e área conferidas |

O que ficou: prédio de O₃ (corpo, bloco alto, terraço coberto, sala de transformadores), os 4 exaustores, 7 torres de
29–58 m na face oeste, silos e tanques do entorno, prédio das prensas (com as máquinas sobre a laje), peneiramento,
prédio elétrico, sala elétrica e dois tanques grandes ao sul.

## 5. Verificação e limitações (para o relatório)
- **Rastreabilidade:** cada objeto do modelo é uma linha de tabela ligada ao tag e ao inventário de origem.
- **Verificação prevista:** área frontal por direção de vento (impressa pelo gerador) e **uma rodada de
  sensibilidade geométrica** (Z1 simplificada × mais detalhada) num cenário de vento.
- **Limitações declaradas:** cilindros e caixas envolventes (sem bocais, plataformas, tubulação externa);
  estruturas treliçadas desprezadas (racks densos podem virar blocos porosos se a sensibilidade indicar);
  estruturas a mais de ~100 m dependem da montagem completa ou entram como rugosidade.
- **Pendências:** prédio das prensas aberto ou fechado embaixo; estruturas altas entre 100 e 300 m; tamanho do
  domínio (H do entorno ≈ 58 m); quais exaustores operam em cada cenário.

## 6. Ferramentas (no repositório)
- `geometria/inventario_STEP_colab.ipynb` — inventário de STEP com nomes (Google Colab).
- `geometria/limpar_step.py` — limpeza automática por regras de nome e cota.
- `geometria/gen_geometria_cfd.py` — geometria por primitivas a partir de tabela.
