# Tambor rotativo de pirólise em batelada

O notebook simula, no Google Colab, uma batelada inteira num **tambor rotativo aquecido por fora**, do partida até o carvão. A carga é **lixo marinho misto** (resíduo pós-consumo da Baía de Guanabara) e o tambor tem o tamanho do equipamento da UFRJ/IVIG mostrado no vídeo (classe Beston BLJ-3, Ø 1,4 m × 4,9 m, com aletas).

O modelo junta combustão na fornalha, troca térmica, movimento da carga, cinética de nove componentes do lixo, carvão e coque, condensador e o gás da própria pirólise voltando para o queimador. O vídeo final é um time-lapse da batelada com o **gráfico se atualizando ao vivo**.

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
| `validation.py` | Escada de validação, descrita na seção seguinte. |
| `scene.py`, `timelapse.py`, `compare.py`, `story.py`, `video.py` | Corte da fornalha com o tambor (chamas da LES, casco colorido pela temperatura, carga do DEM com z-buffer), gráfico ao vivo, parado × girando, segmentos do DEM e das chamas, cartões e montagem em HD. |

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

## Validação

Na rodada de referência (preset `teste`), **29 de 29** verificações ficam dentro do alvo.

| Nível | Verificações |
|---|---|
| N1 componentes | Picos de DTG e T(k = 10⁻³ s⁻¹) de cada polímero; emissividade do gás; regime, ângulo e arco coberto do DEM; mistura em uma volta; conservação de massa da LES; balanços de massa e energia da batelada |
| N2 processo | Coeficiente parede-carga (Suzuki 2008: 22–55 W/m²K); ganho das aletas (7–26 %); ganho pequeno acima de ~1 rpm; duração (UFRJ: 6–8 h); combustível auxiliar (Beston: 2,1–2,9 GJ/t); eficiência da fornalha; queima autossuficiente; rendimentos (Faussone 2022; Fulgencio-Medrano 2022) |
| N3 sistema | Parado × girando: batelada muito mais longa e casco acima do limite do aço |

## Conteúdo

| Caminho | O que é |
|---|---|
| `tambor_pirolise_colab.ipynb` | Notebook do Colab, autocontido (o pacote é gravado por células `%%writefile`) |
| `tamborkit/` | Pacote: carga e cinética, batelada, fornalha (zonas e LES), DEM, validação, cena, time-lapse e vídeo |
| `video_roteiro.json` | Textos do vídeo (editáveis), com campos `{...}` preenchidos pela rodada |
| `docs/brief_tambor_batelada.md` | Base de projeto (pesquisa sintetizada); `docs/pesquisa/` traz os resultados brutos com fontes |
| `tests/` | Testes (`pytest -q`, 8 testes, ~1 min em CPU) |
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
- **Fusão:** entra como colapso do volume aparente, sem escoamento do fundido entre fatias.
- **DEM:** usa esferas macias numa fatia periódica, em dois estados (lixo solto e carvão).
- **Fornalha:** a LES representa um estado de queima e trata o refratário como rerradiante. O modelo zonal conduz a batelada.
- **Química:** não acompanha o cloro no óleo.

Próximo passo: medir no equipamento da UFRJ as temperaturas da carga e da parede durante uma batelada.
