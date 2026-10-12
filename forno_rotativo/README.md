# Tambor rotativo de pirólise em batelada

O notebook simula, no Google Colab, uma batelada inteira num **tambor rotativo aquecido por fora**, do partida até o carvão. A carga é **lixo marinho misto** (resíduo pós-consumo da Baía de Guanabara) e o tambor tem o tamanho do equipamento da UFRJ/IVIG mostrado no vídeo (classe Beston BLJ-3, Ø 1,4 m × 4,9 m, com aletas).

O modelo junta combustão na fornalha, troca térmica, movimento da carga, cinética de nove componentes do lixo, carvão e coque, condensador e o gás da própria pirólise voltando para o queimador. O vídeo final é um time-lapse da batelada com o **gráfico se atualizando ao vivo**.

Na carga, cada pedaço do DEM **muda de fase** ao longo da batelada: o lixo solto amolece, gruda, funde numa poça viscosa, craqueia e vira carvão. Um segmento mostra a **taxa de pirólise de cada componente** se desenhando junto com essa transição. As **chamas** da LES são renderizadas pela emissão da fuligem e pela quimiluminescência ao longo da linha de visada.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GabrielRozo123/Programacao/blob/claude/nifty-franklin-fkhhua/forno_rotativo/tambor_pirolise_colab.ipynb)

Tudo vem de **literatura aberta e catálogos**; não há dados de projeto, de clientes ou de empresas.

## O caso padrão

| | |
|---|---|
| Tambor | Ø 1,40 m × 4,90 m, aço 12 mm, 6 aletas retas de 120 mm, 0,8 rpm (Fr ≈ 5·10⁻⁴, regime de rolamento) |
| Carga | 1 t úmida (15 % de água): PEBD 25, PEAD 15, PP 20, PS/EPS 12, PET 6, PVC 2, borracha 3, celulósicos 8, areia/conchas/sal 9 % (seco), solta até 65 % do tambor |
| Fornalha | câmara sob o tambor, 2 queimadores (465 kW), gases subindo pelos corredores; GLP na partida, depois o gás da própria pirólise |
| Controle | parede média do tambor a 500 °C ("500 graus" do vídeo), rampa de partida de 2,5 K/min, alarme do casco a 650 °C |

Resultado de referência (modelo da batelada):

| Caso | Duração | Óleo | Gás | Carvão + cinzas | GLP | Gás excedente para o flare | Casco no ponto mais quente |
|---|---|---|---|---|---|---|---|
| **Girando a 0,8 rpm** | 6,0 h | 57 % da carga úmida (574 kg) | 12 % | 13 % | ~44 kg (2,0 GJ/t) | ~2 GJ | ~550 °C |
| **Parado** | > 14 h | — | — | — | — | — | ~650 °C (limite de alarme) |

No tambor parado ainda sobram 6,6 % de carga sem converter depois de 14 h. A mancha quente sob a chama ultrapassa o limite de serviço do aço.

Outras rotações e aletas:

| Caso | Duração |
|---|---|
| 0,4 rpm | 6,3 h |
| 2 rpm | 5,7 h |
| Sem aletas | 6,6 h |

As aletas encurtam a batelada em 8,5 % (Suzuki et al. mediram de 7 a 26 %).

## Modelo

| Bloco | O que é |
|---|---|
| `feed.py` | Carga em pseudocomponentes, com a lei cinética de cada um: cisão aleatória (poliolefinas, PS), 1ª ordem (PET, borracha), P2 → F3 (PVC, com HCl), Shafizadeh–Chin (celulósicos) e platô de 100 °C para a água. Também tem os rendimentos por produto (gás, óleo, cera, aromáticos, oxigenados, alcatrão, água, HCl, carvão), a fusão com o volume aparente desabando, a condutividade com radiação nos poros e a TGA. |
| `batch.py` | Batelada em fatias axiais (detalhes abaixo). |
| `furnace.py` | Fornalha zonal de Hottel por fatia: câmara, dois corredores e topo, cada um com gás bem misturado e nó de refratário; WSGG (Smith et al. 1982); perda pelo isolamento. |
| `furnace_les.py`, `combustion.py` | LES 3D de baixo Mach da fornalha: β-PDF do equilíbrio (Cantera) e defeito de entalpia com radiação do gás e da fuligem. A pressão é resolvida só no fluido, com o tambor imerso, e a projeção usa a continuidade discreta (massa fechada por construção). |
| `dem.py` | DEM em GPU: esferas macias com mola tangencial com histórico e resistência ao rolamento. Casco, tampas e aletas são superfícies analíticas que giram. Mede o ângulo dinâmico, o arco coberto, o tempo de contato, as cortinas, o índice de Lacey e o torque. |
| `phasedem.py` | DEM com mudança de fase, acoplado em uma via à batelada (detalhes abaixo). |
| `flames.py` | Chamas com base física a partir dos quadros 3D da LES (detalhes abaixo). |
| `validation.py` | Escada de validação, descrita na seção seguinte. |
| `scene.py`, `timelapse.py`, `compare.py`, `story.py`, `video.py` | Corte da fornalha com o tambor (chamas, casco colorido pela temperatura, carga do DEM com a poça de fundido), gráfico ao vivo, segmento das taxas de pirólise, parado × girando, segmentos do DEM e das chamas, cartões e montagem em HD. |

O `batch.py` tem estes elementos:

- casco por setores girando pela fornalha;
- carga girando com o modelo de penetração (1/h = 1/h_contato + 1/h_pen, t_c = 2ε/Ω);
- aletas como aletas térmicas e cortina;
- carga parada como pilha que só conduz (camadas, condução implícita);
- radiosidade entre o casco exposto e a superfície da carga (cordas cruzadas);
- espaço livre pistonado com craqueamento secundário (cera → óleo → gás + aromáticos + coque; alcatrão → gás/coque);
- condensador;
- reciclo do gás para o queimador e controle PI.

As escalas de tempo são separadas:

- contato ~ms;
- chama ~s;
- volta do tambor 75 s;
- casco ~5 min;
- batelada ~6 h.

Por isso cada bloco roda no seu relógio. Uma CFD-DEM acoplada da batelada inteira levaria dezenas de horas só de DEM.

### Mudança de fase da carga (`phasedem.py`)

O DEM percorre a batelada inteira com o relógio comprimido: algumas voltas representam as ~6 h. A cada passo ele lê da batelada a temperatura da carga e a fração não reagida de cada componente. Cada pedaço carrega o seu material e a sua massa real.

| Material | O que acontece com o pedaço |
|---|---|
| Plásticos que fundem (PE, PP, PS, PET) | A fração fundida f_m(T) sai da faixa de fusão de cada polímero, com ±8 K de dispersão entre pedaços. O volume aparente desaba do solto para o denso (o isopor primeiro, ~1,2 h). O pedaço fica pegajoso (coesão crescente com f_m). Com f_m ≥ 0,85 ele sai do DEM e entra numa **poça de fundido**. |
| Poça | Massa por polímero, com empuxo e arrasto de Stokes sobre os pedaços imersos. A viscosidade η(T, conversão) segue a cisão aleatória (M_n cai com a conversão, η ∝ M_n^3,4, com piso de cera): ~10³ Pa·s logo após a fusão, ~3 mPa·s depois do craqueamento. A superfície inclina com a viscosidade, ~atan(μΩR/ρgH²): o fundido viscoso sobe com a parede, e o craqueado fica plano no fundo. |
| Carvão | Grânulos nascem na poça conforme o rendimento de carvão de cada polímero. |
| Papel e madeira, borracha, PVC | Não fundem: encolhem e escurecem até o carvão (rendimento e retração por material). |
| Areia e conchas | Inertes. |

A sequência que sai do modelo: o isopor desaba (~1,2 h), a poça se forma (2,2–2,6 h, η ~10³ Pa·s, inclinada no lado que sobe), o craqueamento afina o fundido e a poça se aplaina (~3 h), e no fim sobram carvão e areia (~6 h). O PET é o último sólido a fundir. As fontes estão em `docs/brief_mudanca_de_fase.md`.

A batelada também registra a **taxa de reação de cada componente** em kg/h (uma DTG no tempo da batelada). A ordem dos picos: água ~100 °C → PVC 263 → celulósicos 342 → borracha 359 → PS 381 → PET 385 → PP 393 → PE 406 °C.

### Chamas (`flames.py`)

- A LES grava quadros 3D de T, fração de volume de fuligem f_v e liberação de calor.
- A fuligem emite e absorve ao longo da linha de visada (κ = 1862 f_v T). A cor e o brilho saem do espectro de Planck com ε_λ ∝ λ^−1,39, integrado nas funções de cor CIE 1931.
- A base azul (CH*, C₂*) segue a liberação de calor da química rápida.
- T, f_v e q são interpolados numa grade ~3 cm antes da emissão. Como o brilho cresce ~T^20, a borda da chama fica fina em vez de quadrada.
- Câmera HDR: compressão da faixa dinâmica, tone mapping ACES e bloom.
- Duas vistas: o corte (ao longo do eixo) e a lateral (os dois queimadores, com o casco iluminado pela chama).

## Validação

Na rodada de referência (preset `teste`), **29 de 29** verificações ficam dentro do alvo.

| Nível | Verificações |
|---|---|
| N1 componentes | Picos de DTG e T(k = 10⁻³ s⁻¹) de cada polímero; emissividade do gás; regime, ângulo e arco coberto do DEM; mistura em uma volta; DEM com mudança de fase (massa contra a batelada, volume ocupado, ordem dos picos de taxa, viscosidade do fundido antes e depois do craqueamento); conservação de massa da LES; balanços de massa e energia da batelada |
| N2 processo | Coeficiente parede-carga (Suzuki 2008: 22–55 W/m²K); ganho das aletas (7–26 %); ganho pequeno acima de ~1 rpm; duração (UFRJ: 6–8 h); combustível auxiliar (Beston: 2,1–2,9 GJ/t); eficiência da fornalha; queima autossuficiente; rendimentos (Faussone 2022; Fulgencio-Medrano 2022) |
| N3 sistema | Parado × girando: batelada muito mais longa e casco acima do limite do aço |

## Conteúdo

| Caminho | O que é |
|---|---|
| `tambor_pirolise_colab.ipynb` | Notebook do Colab, autocontido (o pacote é gravado por células `%%writefile`) |
| `tamborkit/` | Pacote: carga e cinética, batelada, fornalha (zonas e LES), DEM, validação, cena, time-lapse e vídeo |
| `video_roteiro.json` | Textos do vídeo (editáveis), com campos `{...}` preenchidos pela rodada |
| `docs/brief_tambor_batelada.md` | Base de projeto (pesquisa sintetizada); `docs/pesquisa/` traz os resultados brutos com fontes |
| `docs/brief_mudanca_de_fase.md` | Base do DEM com mudança de fase: fusão, pegajosidade, poça, viscosidade do fundido e carvão, com fontes |
| `tests/` | Testes (`pytest -q`, 10 testes, ~2 min em CPU) |
| `build_notebook.py` | Regenera o notebook e `scripts/rodar_local.py` |

## Uso

No Colab, abra o notebook, escolha *Ambiente de execução → GPU T4* e execute tudo.

Presets:

- `teste`: CPU, malhas e DEM mais grossos, DEM a 3× a rotação real;
- `gpu`.

Na célula de parâmetros:

- carga (lixo marinho, plástico triado, rejeito de cooperativa do Rio);
- massa e umidade;
- rotação;
- número de aletas;
- temperatura da parede;
- autor.

Saídas em `saida/`:

- figuras;
- `tambor_pirolise.mp4` (completo) e `tambor_pirolise_curto.mp4`;
- `capa.png`;
- `resultados.json`;
- o texto sugerido para o post.

## Limitações

- **Carga girando:** é bem misturada na seção de cada fatia. O DEM mostra mistura em poucas voltas.
- **Fusão:** na batelada entra como colapso do volume aparente, sem escoamento do fundido entre fatias.
- **DEM:** usa esferas macias numa fatia periódica, com acoplamento em uma via (a batelada dita a temperatura e a conversão; o DEM não devolve nada). A poça é um inventário com superfície plana inclinada, não um fluido resolvido. As faixas de fusão, a retração e a coesão são hipóteses de ordem de grandeza.
- **Chamas:** a LES representa um estado de queima com GLP. O detalhe abaixo da malha é um efeito visual.
- **Fornalha:** a LES representa um estado de queima e trata o refratário como rerradiante. O modelo zonal conduz a batelada.
- **Química:** não acompanha o cloro no óleo.

Próximo passo: medir no equipamento da UFRJ as temperaturas da carga e da parede durante uma batelada.
