# kilnkit — Brief de projeto: simulação validada de forno rotativo de pirólise de resíduos plásticos (Colab, PyTorch, 1 GPU T4)

Brief do engenheiro-líder, 10/10/2026. Base: as sete linhas de pesquisa (A designs, B leito, C calor, D química, E gás/modelagem, F validação, G lifters, H estático/vedação/acionamento) e os quatro relatórios de verificação adversarial em texto completo. Onde um relatório de verificação corrigiu uma linha de pesquisa, vale a versão corrigida.

**Legenda de evidência**
- **[TC]**: lido no texto completo, ou álgebra exata.
- **[R]**: só resumo.
- **[S]**: secundário, vendedor ou resumo de busca. **[R] e [S] significam "faixa da literatura (não verificado no texto completo)".**
- **[D]**: derivado aqui por cálculo, com as entradas declaradas (scripts em `scratchpad/briefK/ref.py`, `ref2.py`, `kilnB/htcalc.py`, `vBCs/chk.py`, `vDE/chk.py`, `hv_calc/*.py`).
- **[C]**: calibrado por nós; não é valor de literatura.
- **[H]**: hipótese de projeto.
- **[U]**: estimativa a medir.

---

## 0. Decisão em uma página

**O que vamos construir:** um gêmeo digital quasi-3D de um forno rotativo contínuo, aquecido indiretamente (eletricamente, por zonas), para flocos de PE/PP, com carreador de calor sólido (areia) e freeboard resolvido em 3D. Três casos:
- **Caso A, principal, piloto validável:** D 0,50 m × L 4,0 m.
- **Caso B, tambor batelada "óleo combustível + negro de fumo":** 2,6 × 6,6 m, 0,4 rpm. É o palco de maior impacto para o duelo estático × rotativo e para segurança.
- **Caso C, industrial (Hamm):** 2,8 × 20 m, para escala e vídeo.

**Por quê:**
1. **Física dominante.** No forno indireto, a transferência de calor por contato com a parede coberta domina [4] [TC], e a radiação parede livre → superfície do leito é da mesma ordem a 450-650 °C [D]. A convecção do gás é menor (2-10 W/m²K) [9][10] [TC]. Isso é resolvível por correlações validadas mais um campo 2D do leito.
2. **Química.** O vapor fica minutos no freeboard: 85-300 s no piloto [D] e 1-6 min em Hamm [D]. O craqueamento secundário é decidido pela temperatura do freeboard e da parede, não pela rotação. É aí que o 3D agrega valor.
3. **Custo.** CFD-DEM do forno inteiro não cabe no T4 (seção 4.1). O precedente validado de modelo quasi-3D (1D axial + 2D transversal) é o de Boateng & Barr [21][22]. A arquitetura "leito + parede + CFD do freeboard acoplados iterativamente" é a de Marias [71] e Mujumdar & Ranade [72].
4. **Mensagem para o público de CFD.** Mostrar com números quais alegações da KINTEK [1] se sustentam:
   - Aquecimento estático é ruim: **sim**.
   - Rotação melhora a troca térmica: **sim, mas modestamente**.
   - Lifters fazem a carga cascatear: **só com sólidos de escoamento livre**.
   - Remoção rápida de vapor reduz o craqueamento: **não por causa da rotação**.

---

## 1. O reator e o papel da rotação

### 1.1 O equipamento

O forno é um cilindro de aço levemente inclinado (1-3° na prática clássica [8] [TC]). Ele gira sobre anéis de rolamento apoiados em roletes, com acionamento por coroa ou fricção (fricção apenas em tambores ≤ ~1,8 m [54] [TC]). Recebe calor pela casca: zonas elétricas, como as 5 zonas até 1050 °C de Mines Albi [75] [TC], ou mufla/camisa de gases de combustão, como Hamm [46] e Suzuki [2] [TC].

Outros componentes:
- **Vedação** dinâmica nas extremidades: labirinto, lâminas simples ou duplas purgadas com N₂, fole com anel de grafite [54][76] [TC].
- **Alimentação** por rosca com tremonha purgada [2] [TC].
- **Saída de vapores** na extremidade quente.
- **Descarga de sólidos** (char/negro de fumo, metais, carreador).
- **Internos** opcionais: lifters retos, curvos ou de duas seções; tiras longitudinais; correntes ou esferas; carreador de calor; insert central [50].

### 1.2 O que a rotação faz, em números

1. **Renovação transversal do leito.**
   - No regime de rolamento, a camada passiva sobe em rotação de corpo rígido e o material retorna por uma camada ativa fina. Para pellets de PE (3,63 mm, 960 kg/m³) num tambor de 0,96 m, essa camada tem 14-38 % da profundidade do leito, com velocidade superficial de 1,7-7,5 × ωR e cisalhamento de 6,6-17,5 s⁻¹ [21] Tab. 4.2 [TC].
   - O leito é revirado cerca de 3 vezes por revolução e o transporte transversal é advectivo (Pe alto) [21] [TC].
   - Fora da camada ativa o leito se comporta como leito fixo: a parede é a região mais quente e o núcleo superior a mais fria [6] §3.4 [TC], [4] [TC].
   - Num tambor liso, a homogeneização térmica até ΔT ≤ 5 K leva cerca de 59 s (cerca de 6 revoluções) a 6 rpm, F 20 %, esferas de vidro de 2 mm. A 1 rpm chega a cerca de 600 s [5] [TC].
2. **Contato com a parede.**
   - O tempo de contato é t_c = 2ε/ω, com ε o semi-ângulo de enchimento. Ele não depende do diâmetro [6][4] [TC].
   - No Caso A (F ≈ 11 %, ε ≈ 48°, 2 rpm), t_c ≈ 8 s [D]. Quanto menor t_c, maior o coeficiente de penetração.
3. **Transporte axial.** Inclinação mais rotação dão τ ∝ L√θ/(S·D·N) (Sullivan [7] Eq. 6 [TC]), ou a EDO de Saeman/Kramers [9] Eq. 1 [TC]. Medido num piloto de 0,21 × 4,2 m (cavacos de madeira): MRT de 31,8-109,4 min com 1-2° e 2-4 rpm [8] Tab. 2 [TC].

### 1.3 Alegações KINTEK [1] × literatura

A página [1] foi lida. É qualitativa, sem números, e não cita lifters pelo nome; descreve "levantar e derramar através da atmosfera mais quente".

| Alegação KINTEK | Evidência numérica | Veredito |
|---|---|---|
| Aquecimento estático gera camada de parede superaquecida/carbonizada e centro frio | Penetração de calor numa camada estática de flocos (α 1,25-3,5e-7 m²/s): 0,1 m em 7,9-22 h; 0,2 m em 32-89 h; 0,3 m em 71-200 h [D, verificado]. Patente US 11,987,756: forno indireto ou rosca → "excessive char yield originating from the fluid near the hotter wall" [51] [TC]. Hedlund: tambor batelada **parado** com queimadores por baixo; a parede ultrapassou a temperatura de autoignição do gás [52] [TC]. Leito fixo de plástico: taxa de aquecimento cai de 19,7 para 12,1 °C/min e o fundido drena para o fundo [61] [TC]. Boateng reproduz os gradientes radiais de um forno parado [21] [TC] | **Suportada** |
| Agitação dinâmica → aquecimento uniforme | É uniforme só em relação ao estático. Leito rolante = leito fixo mais camada ativa fina [6][4] [TC]. Homogeneizar leva ~6 rev [5] [TC]. Tiras de 2 mm multiplicam h_ws por 2,2-3,1× em pó coesivo [6] [TC]. Carreadores aumentam muito a taxa de aquecimento de partículas plásticas [29] [R] | **Parcial** (a uniformidade vem de mistura e internos, não da rotação em si) |
| Melhor transferência de calor e massa | h(6 rpm)/h(1 rpm) medido = 1,2-2,4, não √6 = 2,45 [4] [TC]. Suzuki: 2,7→4,0 rpm dá 38,6→43,4 W/m²K (+12 %); seis lifters de 200 mm dão +15-17 %; os dois juntos, +30 % (50,1 W/m²K) [3] [TC]. Contraexemplos: Chaudhuri, efeito "mínimo" da rpm [25] [TC]; Zhang 2022, "not obvious" [29] [R]; CIESC 2014, 3 r/min **inibiu** a troca na secagem e pré-pirólise a baixa taxa de aquecimento [64] [R]; pó coesivo deslizante, sem efeito da rpm [6] [TC]. Em contínuo, mais rpm encurta τ (Saeman) | **Suportada, magnitude modesta (+10-30 %)**, com compromisso residência × coeficiente |
| Transporte contínuo por inclinação + rotação | Sullivan/Saeman [7][9] [TC]; dados de Colin [8] [TC] | **Suportada** |
| Lifters elevam e derramam a carga pela atmosfera quente | Modelos de lifter valem só para sólidos de escoamento livre, "not to highly cohesive solids, sticky and wet materials" [18] [TC]. Em plástico fundido, lifters não seguram carga e incrustam. Os fornos de plástico publicados usam carreador: Zhang 2020 [30] [R], Beckmann [13] [TC], Haloclean [79] [S]. No forno de Suzuki (41 % de enchimento), os lifters atuam como misturadores, não formam cortina [G, TC] | **Válida antes da fusão e para char/carreador; não para a zona de fundido** |
| Remoção rápida de vapores → menos craqueamento secundário | A rotação não remove vapor; purga e tiragem removem. A residência do vapor no forno é de **minutos**: piloto 85-300 s [D]; Hamm 64-383 s por forno [D, verificado]. Leito fixo: 1,65-3,76 s [40] [TC]. A 650-700 °C, k_O ≈ 0,1-0,8 s⁻¹ (Opção B [C]). A 750 °C o vapor já virou gás leve em 1,6 s [37] [TC]. A medida que funciona é reduzir o volume quente: o insert central de 20 cm × 230 cm cortou a residência do vapor "by nearly half" [50] [TC]. Lifters aumentaram o gás num forno de pneus [82] [R, fraco] | **Não suportada como formulada (marketing)**; reformular como "residência e temperatura do vapor quente" |
| Trade-offs: desgaste, vedação anaeróbica, energia do motor | Lâminas de vedação e bandas de desgaste trocadas a cada 1-2 anos; torque de partida até 250 %; recuo do forno em queda de energia [55] [TC]. Arrasto de selo sobrecarregou o acionamento no PREPP [57] [TC]. Explosão de Hedlund (purga interrompida; 40 kPa de N₂ só levam o O₂ a 15 %) [52] [TC]. Motor: < 1 % da potência térmica (3,2-3,4 kW contra ~1,05 MW de queimadores no tambor de 10 t [D]) | **Suportada**; o custo do motor é desprezível, a vedação é o risco real |
| Produtos: óleo combustível e negro de fumo | Carbono fixo: HDPE 0,01; LDPE 0; PP 0,16-1,22 % em massa [66] [S]. Os 30-40 % de "carbon black" anunciados refletem pneus, cargas e cinzas [49] [TC, alegação de vendedor]. Forno semi-piloto com plástico misto a 500 °C: óleo 40-45 % e char 5-7 % no texto, contra 43 % e 16 % no resumo [44] [TC, inconsistente] | **Parcial**: óleo sim; negro de fumo só com pneu ou cargas |

---

## 2. Casos de referência

### 2.1 Justificativa

**Por que contínuo e indireto:**
- É a configuração das plantas de referência europeias e japonesas: Hamm, Burgau, Schwel-Brenn e Mitsui R21 [46] [TC], [A, S].
- A atmosfera anaeróbica fica separada do aquecimento.
- Os dados de transferência de calor de sistema existentes são de fornos indiretos: Suzuki [2][3], Hwan [16] e Beckmann [13] [TC].
- Em regime permanente, o 1D + 2D é estacionário no referencial lagrangiano e barato.

**Por que carreador e não lifters na zona de fundido:**
- Os modelos de lifter não se aplicam a material pegajoso [18] [TC].
- Filmes e incrustações bloqueiam a troca térmica na parede, a ponto de exigir raspadores [A, S].
- O precedente contínuo verificado é areia + PE na razão 9:1 (90 + 10 kg/h) [13] [TC].
- Alumina e esferas suprimem a aglomeração [78] [R].

Mantemos lifters só onde o sólido escoa livremente: na zona final (char + carreador), o que dá a imagem KINTEK com física correta. Uma variante "KINTEK literal" com lifters no forno todo e sem carreador entra como contraexemplo quantitativo.

**Por que o Caso B (batelada):**
- É o desenho comercial mais vendido para "óleo + negro de fumo" [49][58][59].
- Opera a 0,4 rpm com até 2/3 de enchimento.
- O contraste estático × rotativo e o risco de segurança (Hedlund [52]) são dramáticos.
- Como é transiente e axialmente quase uniforme (L/D ≈ 2,5), basta o 2D, que é barato.

### 2.2 Caso A: piloto contínuo indireto (principal)

| Item | Base | Faixa / variantes | Fonte e status |
|---|---|---|---|
| D interno × L aquecido | 0,50 m × 4,0 m (L/D 8), 4 zonas de 1 m | D 0,21-1,0 m | [H]. Análogos: Hwan, forno indireto com lifters, D 0,498 × 3,98 m [16] [TC]; Colin 0,21 × 4,2 m [8] [TC]; Hamm L/D 7,1 [46] [TC] |
| Parede | Aço 310S, 10 mm, sem refratário | 8-25 mm | [H]; Suzuki SUS310S 25 mm [2] [TC] |
| Inclinação | 1,0° | 0,5-3° | [8] [TC] (1-3° "classicamente") |
| Rotação | 2 rpm (Fr = 1,1e-3, rolamento) | 0 (estático), 0,5, 1, 3, 4, 6 | [8] 1-5 rpm; [44] 2 rpm; [3] 2,7-4 rpm [TC] |
| Represa de descarga | 50 mm | 0-80 mm | [H] |
| Enchimento | 9-12 % médio (Saeman) | 5-20 % | [D]; alvo industrial 10-20 % [4] [TC]; Hamm ~15 % [46] [TC] |
| Internos | Carreador de areia de quartzo d_p 0,5 mm (0,2-1), recirculado. Parede lisa nos 3,2 m iniciais. **6 lifters retos de 50 mm** nos 0,8 m finais (char + carreador) | **A-L**: lifters 6×50 mm no forno todo, sem carreador (KINTEK literal). **A-0**: sem internos, sem carreador. **A-T**: tiras de 2 mm [6]. Esferas de aço 1-1,5 mm [S] | Altura D/12-D/8 [56] [S]. Suzuki: H_l/H_w > 0,45 e espaçamento L_l/L_w < 1 (o resumo diz > 1, mas é erro tipográfico) [3] [TC]. Com H_w ≈ 80 mm, isso dá ≥ 36 mm e ≥ 4 lifters [D] |
| Alimentação | 20 kg/h de flocos PE/PP 50/50, 3-10 mm, ρ_b ≈ 350 kg/m³ | 10-60 kg/h. Contaminantes: PVC 0-2 %, PET 0-5 %, papel 0-10 % | [H]. ρ_b de regrind 250-500 [S]; fluff de Hamm 60-250 [46] [TC]. **Não usar 610 kg/m³**: é pellet de biomassa [86] |
| Carreador | 180 kg/h (9:1 em massa), entra a 350 °C (recirculação quente) | 0:1, 3:1, 9:1; 25 °C (configuração Beckmann) | Razão [13] [TC]; temperatura [H] |
| Aquecimento | Elétrico. Setpoints de parede 450/600/600/600 °C (Modo A: T_w prescrita; Modo B: potência prescrita) | Zonas 2-4 em 550-700 °C | [H]. Beckmann escalonou 300/400/500/500 °C [13] [TC]; Suzuki 555 e 630 °C [2] [TC]; Hamm casca ~750 °C com processo ~500 °C [46] [TC] |
| Temperatura alvo do leito | 480-520 °C no fim da zona 2 | | Hamm ~500 °C [46] [TC]; o polímero não passa de ~550-600 °C mesmo com o ambiente a 900 °C [36] [TC] |
| Purga | N₂ 1,5 Nm³/h, co-corrente | 0,5-5 Nm³/h; insert central (variante) | Escala de Beckmann: 0,8 Nm³/h para 10 kg/h de PE [13] [TC] [D] |
| Pressão e selos | +50 a +200 Pa; selos de lâmina dupla purgados com N₂ | −200 a +500 Pa | 0,0010-0,030 psi ≈ 7-207 Pa [50] [TC]; Kern: "a few mbar" abaixo da atmosfera [47] [TC]; [54][76] [TC] |
| Residência dos sólidos | Saeman 32-35 min; corrigida 26-35 min | 15-60 min | [D]. Saeman superestima o MRT em 4-25 % em sólidos lamelares [8] [D]. Sullivan: 27 min [D] |
| Residência do vapor (V/Q) | 85-300 s (M 0,05-0,30 kg/mol); velocidade na saída 0,01-0,05 m/s | 64-450 s na varredura de N₂ | [D] |
| Escoamento no freeboard | Re_ω ≈ 500; Gr ≈ 2,6e7 (ΔT 100 K); estratificação estável (topo quente) → laminar | | [D] |
| Carga térmica | ~20 kW de processo (plástico 12,8 kW a 2,3 MJ/kg + areia 350→500 °C 7,5 kW), mais 3-5 kW de perdas. Fluxo médio ~4 kW/m² | Areia fria: 37 kW, 5,8 kW/m² | [D]. Fluxo máximo medido 11-16,5 kW/m² [2] [TC] |
| Acionamento | 0,03-0,2 kW | | [D]; CE Raymond/Perry [56] [S]; torque do centro de gravidade |
| Rendimentos esperados (PE/PP limpos) | São saída do modelo. Condensáveis 60-90 % e gás 8-35 %, fortemente dependentes da temperatura do freeboard (500-580 °C) [C]. Char < 2 % mais cinzas e cargas | | Âncoras: HDPE semi-batelada a 500 °C, residência de vapor 1,5-1,7 min: líquido 89,3 / gás 10,0 % [35] [TC]. Forno semi-piloto a 500 °C: óleo 40-45 % (gás por diferença, inclui perdas) [44] [TC]. Plantas chinesas: óleo 43-52 % [49] [vendedor] |

Notas do Saeman [D]:
- Com 1°, represa de 50 mm e q_v = 0,12-0,17 m³/h: a 2 rpm, F = 9,0-11,6 % e τ = 32-35 min; a 3 rpm, F = 6,8-8,6 % e τ = 24-27 min.
- Só plástico (variante A-L/A-0) a 20 kg/h: F = 2,8-5,5 % com represa de 50-80 mm. É um leito raso, típico de piloto sem carreador.

### 2.3 Caso B: tambor batelada "óleo combustível + negro de fumo"

| Item | Valor | Fonte |
|---|---|---|
| Tambor | 2,6 × 6,6 m; Q245R/Q345R de 16-20 mm | Doing DY-1-10 / Sihai LJ-10 [58][49] [vendedor] |
| Rotação | 0,4 rpm (0,4-0,8); Fr = 2,3e-4 a 0,4 rpm [D] | [49] [TC] |
| Enchimento máximo | 2/3 do volume ("para girar suavemente") | [49] [TC] |
| Carga | 10 t de pneus, ou 8-10 t de fardos de plástico | [58][59] [vendedor] |
| Aquecimento | Queimadores por baixo, camisa de gases; 3 × 300 000 kcal/h ≈ 1,05 MW | [58] [vendedor] |
| Acionamento | Motor de 5,5 kW (total instalado 19-20,5 kW). Correlação: 3,2-3,4 kW a 0,4 rpm | [58][49]; [D] |
| Ciclo | Aquecimento 8-10 h; 16-20 h no total | [S] (não visto na página do vendedor) |
| Pressão | "Normal" (Doing) ou +0,03 bar (planta de Bangladesh) | [49] [TC]; [85] [R] |
| Orçamento térmico | Demanda de pneus 1,41-2,16 kJ/g, ou 14-22 GJ por batelada [88] [R]. Contato a 25-40 W/m²K: 0,16-0,25 MW. Radiação parede livre → leito: 0,25-0,45 MW | [D, verificado] |
| Rendimentos | Pneus (vendedor): 45 % óleo / 30 % negro de fumo / 10 % gás [49]. Piloto de pneus 550→680 °C: char 49,1→48,9 %, óleo 38,1→31,8 %, gás 2,4→10,8 % [68] [S]. Plástico limpo: char ≈ cinzas + cargas | |
| Incidente de referência | P4O (Dinamarca): forno batelada de 10 m × 2,5 m, 7 t de fardos, explosão 30 min após a ignição; purga interrompida após 2 min | [52] [TC] |

### 2.4 Caso C: industrial (escala e vídeo)

Hamm [46] [TC]:
- D_eff 2,8 m, L aquecido 20 m, 2 fornos de 6,65 t/h, enchimento ~15 %, ~90 min.
- Processo ~500 °C com casca ~750 °C.
- Gás natural 29,2 GJ/h (10,8 % da entrada), ou seja, ~2,2 MJ/kg bruto e ~1,5 MJ/kg líquido [D].
- N₂ 20 m³/h.
- A alimentação é CDR/RDF, não plástico puro.
- Limite de projeto de forno indireto: ~3 m × 22 m [90] [S].

Rodamos 1D + 2D completos; o 3D fica opcional, em malha grossa, com SST, porque Gr ≈ 2e9 [D].

---

## 3. Fenômenos e modelos escolhidos

### 3.1 Transporte de sólidos e profundidade do leito

**Modelo:** EDO de Saeman/Kramers [9] Eq. 1 [TC]:

dh/dz = tan θ · [3 q_v/(4π n R³) · (2h/R − h²/R²)^(−3/2) − tan β / sin θ]

- z é medido a partir da descarga; n em rev/s; condição de contorno h(0) = h_represa (ou ≈ d_p).
- O fator 1/cos β é desprezível abaixo de 5° [TC].
- **q_v(z) varia**: perde massa por devolatilização, o plástico funde e preenche os vazios do carreador. A regra de volume é: fundido absorvido nos vazios do carreador até ε_v ≈ 0,4 [H].
- θ dinâmico: areia de quartzo 32,4° [19] [TC]; esferas de PP 30,3-35,5° (mistura PP/vidro) [89] [TC]; cavacos lamelares 42° [8] [TC]; pellets de PE com repouso estático de 25° [21] [TC]. Base do carreador: 33°.
- **Viés conhecido:** num conjunto lamelar, Saeman superestima o MRT em +4 a +25 % e Sullivan erra em −13 a +13 % [8] [D, verificado].

**Dispersão axial:** fluxo pistonado por padrão. Pe medido:
- 361-645 em Colin 2015 [8] [TC];
- ~2000 em Thammavong (L/D 19) [10] [TC];
- 71-77 em Hwan, com lifters segmentados [16] [TC].

A sensibilidade usa Pe de 70 a 2000. Para RTD: modelo de dispersão com condições de Danckwerts.

**Verificação embutida (Sullivan = Saeman raso):** os coeficientes (180/π²)·sin θ e 1,77·√θ coincidem a 35° e diferem até 13 % entre 25° e 45° [D, verificado].

**Zona de fundido sem carreador** (variante A-L/A-0): Saeman não vale. O plástico fundido e craqueado forma uma piscina de superfície plana com filme de parede; o transporte é por gravidade sobre a represa. Usamos um modelo de vertedouro com nível hidrostático [H] e marcamos a célula com a flag "líquido".

### 3.2 Regimes transversais (Froude) e geometria do leito

- **Froude:** Fr = ω²R/g [23] [TC].
- **Rolamento:** 1e-4 < Fr < 1e-2 (Mellmann) ou 5e-4 < Fr < 2e-2 (Henein), ambos via Santos 2016 [23] [TC]. As faixas de deslizamento, avalanche ("slumping"), cascata e catarata da tabela de Mellmann **não foram verificadas**.
- **Transição avalanche → rolamento:** depende de d/D. O Fr crítico vai de ~0 a 1,6e-3 [R].
- O código **avisa** quando o caso sai do rolamento, mas não troca de modelo automaticamente.
- Valores: Caso A a 2 rpm, Fr = 1,1e-3; Caso B a 0,4 rpm, Fr = 2,3e-4 [D].

**Geometria do segmento circular:**
- F = (ε − sin ε cos ε)/π; corda 2R sin ε; arco coberto 2εR [4] Eq. 1 [TC].
- Atenção às convenções: Nafsun usa semi-ângulo e n em s⁻¹; Moumin usa ângulo total e n em rpm [TC]. **Uma convenção só no código: semi-ângulo ε e ω em rad/s.**

**Camada ativa** (modelo cinemático do leito rolante):
- A camada passiva gira como corpo rígido.
- O fluxo de retorno pela camada ativa é igual ao fluxo passivo através da vertical, Q = (ω/2)[R² − (R cos ε + δ)²] [D, identidade cinemática].
- Espessura δ(x) parabólica, com δ₀/H calibrado em Boateng: 0,14-0,38 [21] [TC].
- Perfil de velocidade linear na camada ativa, o que dá u_s.
- Difusividade granular D_g = c·d_p²·γ̇, com c calibrado no tempo de mistura de Nafsun 2015 [5] [C].

**Deslizamento:** o carreador a 5 % de enchimento desliza em bloco e rola acima de 10 %, segundo Gao & Bao [S, não verificado]. Para pó coesivo sem internos, Moumin mediu h 2,5-6× abaixo dos modelos [6] [TC]. A flag de deslizamento aplica um fator ×1/3 em h_ws [H], ancorado na sobreestimativa de ~3-5× que Herz 2015 relata para avalanche e deslizamento, via [6] [S].

### 3.3 Lifters e cortina (zona final e variante A-L)

**Modelo geométrico de Sunkara** [18] Eqs. 3.19-3.45 [TC]:
- Retenção por lifter f_F(δ) em três regiões.
- Taxa de cascateamento m_F/(ρ_b ω π R² L) = −df_F/dδ.
- Ângulo cinético de Schofield-Glikin com sinal "+" no denominador [17][18] [TC]: tan γ = [μ cos α + Fr(r_H/R)(cos δ − μ sin δ)] / [cos α − Fr(r_H/R)(sin δ + μ cos δ)]. A diferença para o sinal "−" é menor que 0,5° em Fr de forno.
- Altura de queda h_F/R por setor, tempo de queda t_F = (1/ω)·√(2 Fr h_F/R), área da cortina A_cs/(LR) = 3π(ρ_b/ρ_s)(D/d_p) f_cs [18] Eqs. 3.84-3.99 [TC].
- Ângulo final de descarga δ_L = 90° + α + γ_L [18] [TC].

**Carga de projeto:**
- Baker modificado por Karali: H_tot = 1,38 (2ΣH_i − H_FUF) [17] [TC].
- Correlação de Karali para f_design, RMSD ±3,4 pontos [17] [TC].
- Enchimento de projeto: 5-15 %, medido 4,5-14,8 % [17] [TC]. **15-20 % é sobrecarga** (a linha G estava errada nesse ponto).
- Com 6 lifters de 50 mm em D 0,5 m o tambor fica sobrecarregado: leito rolante de fundo mais cortina parcial, o que é aceitável e realista.

**Avanço axial por cascata:** X ≈ h_queda·sin β (com o termo de arrasto do gás) [17] Eqs. 5.9-5.26 [TC].

**Troca térmica da cortina:**
- Ranz-Marshall para o gás, com a forma de Le Guen [20] [TC]. Atenção: a tabela imprime k_s; Ranz-Marshall usa k_g.
- Radiação da parede livre com fator de blindagem ε_c = 1 − exp(−1,5 φ δ/d_p) [H, Beer-Lambert].
- O Ua volumétrico de secadores (237 G^0,67/D) **não se aplica**: vale para gás quente direto [G, TC].

**Validade:** só sólidos de escoamento livre [18] [TC]. Na variante A-L, quando T > T_m − 10 K, o lifter passa a "pegajoso": retenção zero, índice de incrustação acumulado e resistência de filme na parede (3.5).

### 3.4 Transferência de calor: caminhos, correlações, constantes e validade

| Caminho | Modelo escolhido | Constantes | Validade e magnitude esperada |
|---|---|---|---|
| Parede coberta → leito | Série: 1/h_ws = 1/h_c + 1/h_pen, com h_pen = 2√(kρc/(π t_c)) e t_c = 2ε/ω [4] Eqs. 2-3; [6] Eqs. 2.3-2.4 [TC]. No 2D usamos uma **camada de parede sub-malha 1D** (32 nós, 8 mm) que reproduz a penetração exatamente quando o tempo de contato é finito e a condução estática quando ω = 0 | Carreador fino: h_c = k_g/(χ d_p) com **χ = 0,1** (Li) ou 0,085 (Sullivan-Sabersky) [6] Tab. 1 [TC]. A faixa 0,096-0,198 só aparece em fonte secundária. **Não usar** o ajuste χ(d_p) de Colin acima de 2 mm: daria 2,35 a 4 mm [TC]. Flocos: h_c ≈ 90 W/m²K (50-250), retrocalculado da argila expandida [D]. Esferas: Schlünder-Mollekopf completo, com constantes em [6] Tab. 1/App. A.1 [TC] | Carreador a 2 rpm: h_pen ≈ 250, série ≈ 200 W/m²K [D]. Faixa de validação: areia 81-122 (1 rpm) e 198-298 (6 rpm) [4]; 136,5 (1 rpm, F 10 %) [6] [TC]. Flocos: h_pen ≈ 105, série ≈ 50 W/m²K [D], contra argila expandida 27-41 / 36-54 [4] [TC]. Fundido sem filme de gás: h_pen ≈ 250 [D] |
| Parede coberta com filme fundido ou char | Resistência adicional δ_f/k_m. δ_f limitado pelo arrasto, h* = √(μU/(ρg)) [D, verificado] | k_m 0,15-0,26 W/mK [S] | δ = 2 mm → 100 W/m²K; δ = 5 mm → 40 W/m²K [D]. O valor "~1000 W/m²K para fundido em forno" é de segunda mão e **não será usado** |
| Tscheng-Watkinson (parede-leito) | **Só sensibilidade**: h = 11,6 (k/(Rγ))·(ωR²γ/a)^0,3, com ω em rad/s [6] Tab. 1; [11] Eq. 2.20 [TC] | | As formas secundárias divergem por 2π a 4π² no argumento (1,7-3× em h). Argumento fora do limite (~1e4) para leito plástico [S]. Wes (superior) e Tscheng (inferior) delimitam a faixa dos modelos [6] [TC] |
| Parede livre ↔ superfície do leito ↔ cortina ↔ (gás) | Radiosidade 2D por seção (cinza difusa). ~48 elementos de parede, 8 de corda e lâminas de cortina. Fatores de forma por cordas cruzadas, ou ray-casting por SDF quando há lifters. Trocas axiais além de 1 D são desprezíveis [12] [TC] | ε_w = 0,88 (aço 347 oxidado 0,87-0,91 [14] [R]; aço oxidado 0,9 [9] [TC]). ε_leito = 0,9 (char 0,9-1 [12] [TC]; sem medida para plástico, é lacuna). Gás transparente na base; ε_g de 0 a 0,3 como sensibilidade, com L_m = 0,95(D − H) [12] [TC]. Gás cinza: erro < 20 % se ε > 0,8 [12] [TC]. O gás de pirólise não é cinza [13] [TC] | h_rad de corpo negro: 96 (550/400 °C), 116 (600/450), 139 (650/500 °C) W/m²K [D]. Mesma ordem do contato: **os dois são obrigatórios** |
| Gás ↔ parede e gás ↔ leito | 3D: resolvido (laminar no piloto). 1D: Seghir-Ouali Nu_gw = 0,01963 Re^0,9285 + 8,5101e-6 Re_w^1,4513 (Re 0-3e4; Re_w 1,6e3-2,77e5) [7] Eq. 27 [TC]. Gás-leito por Tscheng, Nu_gb = 0,46 Re^0,535 Re_w^0,104 η^−0,341 [11] [TC], **recortado** (fora de 1600 < Re < 7800, faixa vinda de fonte secundária) | | 2-10 W/m²K (h_sg medido 2,2-4,8 [10]; 10 assumido [9] [TC]). A sensibilidade de Patisson mostra efeito de segunda ordem [9] Tab. I [TC] |
| Casca | Nó radial concentrado com massa térmica. Campo 2D (θ, z) desenrolado com condução axial e circunferencial | Aço 310S: k ≈ 19 W/mK [H] | Penetração regenerativa de 4-12 mm a 1-6 rpm [D]. A casca de aço é quase isotérmica na circunferência (efusividade ~9100 contra ~265 do leito) [D]. Suzuki: ΔT entre a superfície interna e o ponto interno da parede = 6,5-8,5 °C [2] [TC] |
| Aquecimento externo | Zonas elétricas: radiação aquecedor → casca, com controle por setpoint (Modo A) ou potência (Modo B). Alternativa: camisa de gases com T_gás 700-800 °C [2] [TC] e h_camisa [H] | Aquecedor 750/600 °C: capacidade 17,5-23,3 kW/m² [D] | Fluxo sustentável na casca 5-20 kW/m², limitado pelo U parede-leito, não pelo aquecedor [D]. Medido: 11 e 16,5 kW/m² [2] [TC] |
| Perdas | Isolamento: 200 mm a k 0,08 → ~0,24 kW/m²; 150 mm a k 0,10 → ~0,40 kW/m² [D]. Mais as extremidades e os selos | Convecção externa 3-40 W/m²K (vento de 1-28 m/s), 17 medido; emissividade da casca 0,9 [9] [TC] | Valor impresso de 0,26 W/m²K para convecção natural em [9] é implausível: **não usar** |

**Partição esperada:** no forno indireto o contato domina [4] [TC]; a radiação cresce com a temperatura e com a cortina. No Caso B, radiação 0,25-0,45 MW contra contato 0,16-0,25 MW [D]. No Caso A base, por metro: contato ≈ 0,42 m²/m × 200 W/m²K ≈ 84 W/(m·K); radiação ≈ 0,37 m/m × ~85 W/m²K ≈ 31 W/(m·K). O ΔT parede-leito médio fica em ~45 K com carreador quente e ~80 K com carreador frio [D].

**U de comparação:** Suzuki define k_m-w = q_m/(A_m (T_parede − T_resíduo)) **por área interna total** [2] [TC]. O modelo reporta o mesmo indicador, além do h local por área coberta, para comparar grandezas iguais.

### 3.5 Aquecimento, fusão e aglomeração do plástico

**Método entálpico** por partícula e por célula:
- T_m: LDPE 114,2 °C e PP 154,5 °C (DSC) [81]; HDPE 125-135 °C; PS com T_g ~100 °C [S].
- ΔH_f: PE 218 J/g e PP 80 J/g [43] [S].
- cp do sólido e do fundido: 2,0/2,7 (PE), 1,9/2,6 (PP), 1,4/2,0 (PS) kJ/kgK [H, mesma base da rodada anterior].

**Condutividades:**
- PP sólido 0,280 W/mK (MTPS, 26 °C), faixa 0,1-0,3 [80] [TC].
- Fundido 0,15-0,26 [S].
- Leito de flocos 0,08-0,12 W/mK (Zehner-Schlünder, 0,05-0,14) [D]. Análogo medido: argila expandida 0,12 [4] [TC].
- Difusividade do fundido de Yanez (6,92e-7 / 5,53e-7 m²/s): 4-6× acima do usual, **não usar como base** [81].

**Partícula:** o modelo concentrado só vale para d < 2 mm; acima de 4 mm, ΔT interno > 10 K [32] [R]. Flocos de 3-10 mm entram como parcelas lagrangianas com condução radial 1D de 8 nós.

**Estado de fase por célula:** granular / pegajoso / líquido, a partir de T, conversão e μ do módulo de reologia já existente.
- A janela pegajosa é 1e1-1e4 Pa·s [H].
- Índice de aderência: S = φ_fundido × 𝟙(μ na janela) × (tempo de contato com a parede).
- Mapa de risco de anel e incrustação.
- **Não existe modelo validado de aglomeração em forno.** O mais próximo é uma ponte líquida em leito fluidizado (MFiX) [E, R]. O mapa é um indicador, não uma previsão.

**Com carreador:** o fundido reveste a areia e o leito continua granular, desde que o volume de fundido fique abaixo dos vazios (~0,4). Coesão: θ +5 a +10° [H], para sensibilidade.

**Limite de bulbo úmido:** o polímero não passa de ~550-600 °C mesmo com o ambiente acima de 900 °C [36] [TC]. Isso é coerente com Hamm (processo 500 °C, casca 750 °C) [46].

### 3.6 Cinética primária e energia

**Base: RS-L2 do código existente** [C]:
- HDPE, LDPE, PP, PS: E = 238/215/179/180 kJ/mol e A = 5,2e14 / 1,92e13 / 6,98e10 / 4,1e11 s⁻¹, calibrados aos picos de DTG de 475/465/455/420 °C a 10 K/min.
- E vem de Aboulkas 2010 [42]: resumo apenas, acesso fechado.
- Forma: dx/dt = k(1 − x); α = x²; integrar em x.

**Alternativa só com literatura: Westerhout de primeira ordem** [33] Tab. 4 [TC]:
- HDPE 1,9e13 / 220; LDPE 1,0e15 / 241; PP 3,2e15 / 244; PS 3,3e13 / 204 (s⁻¹ / kJ/mol).
- Ajustados a 400-450 °C (PS a 365-400 °C).
- O RCD de PS é 1,3e14 / 219 (Tab. 5). Não confundir com o valor de primeira ordem.
- t90 do HDPE: 15,7 min a 450 °C e 1,48 min a 500 °C (extrapolado) [D, verificado]. Os dois conjuntos concordam em 10-30 % [D].
- Misturas são aditivas (LDPE/PP a 425 °C) [33] [TC].
- Spread de mecanismos para HDPE: até 7× [77] [R].

**Contaminantes:**
- **PVC** [41] [TC]:
  - Etapa I (P2): 75 kJ/mol, A = 2,98e4 s⁻¹ (1,79e6 min⁻¹ na lei final). Precisa de semente α₀ = 1e-4. Libera 0,583 kg de HCl por kg de PVC.
  - Etapa II (F3): 140 kJ/mol, A = 8,07e7 s⁻¹.
  - Ea da etapa I na literatura: 49-190 kJ/mol.
  - Cl na alimentação de Hamm: 0,1-3,0 % em massa [46] [TC].
- **PET:** primeira ordem, E 210, A 2,59e13, char 0,15 [C, rodada anterior].
- **Papel:** pseudo-biomassa com char 0,3-0,4 a 500 °C no forno [44] [TC]; cinética genérica [H].

**Energia:**
- Calor de pirólise: PE 920 ± 120, PP 1310 ± 70, PS 1000 ± 90 kJ/kg [43] [S]. Spread do HDPE: 670-1375. Li 2026 usa 542 kJ/kg (DSC) nas etapas de cera do PP [31] [TC]. Usamos Stoliarov na base e 542 como sensibilidade.
- Energia total de 25 °C até 480 °C: HDPE 2,28, LDPE 2,22, PP 2,49, PS 1,87 MJ/kg [D]. Isso fica dentro de 10 % dos totais de Stoliarov [S].
- **Não usar** os "4.600 kJ/kg" de Beckmann: o número é ambíguo [13].

**Split primário de voláteis das poliolefinas:** G 0,10 / O (C5-C20) 0,55 / W (C21+) 0,35 [C]. Âncoras: Pires (gás 8-10 %, C13+ ~90 % do líquido) [35] [TC] e Baird [R]. PS gera um lump rico em estireno (0,65 [S]).

**Opção para PP, rede em fase líquida de Lechleitner** [34] Eqs. 2-6 e [31] Tab. 2 [TC]:
- k1: W → óleo de fuso, 2,0e2 s⁻¹ / 80 kJ/mol.
- k2: W → leves, 1,0e5 / 100.
- k3: W → G, 5,0e14 / 249.
- HDPE: k2 1,0e47 / 700 e k6 (leves → G) 1,0e18 / 300. Os autores chamam os caminhos de 700 kJ/mol de implausíveis.
- Li 2026 mostra a sensibilidade: com o leito subindo de 505 para 525 °C, o óleo leve cai de 67,4 para 56,7 % e o gás sobe de 29,6 para 40,9 % [31] [TC].

### 3.7 Craqueamento secundário (fase gás)

**Esquema do freeboard** (Opção B, [C]):
- W → O, com k_W = 3 k_O.
- O → (1 − φ_A) G + φ_A A, com k_O = 1,0e16 exp(−300 kJ mol⁻¹/RT).
- φ_A = 0 até 600 °C, subindo linearmente até 0,3 a 700 °C.
- k_O = 9,2e-4 / 0,0113 / 0,106 / 0,79 / 4,8 s⁻¹ a 550 / 600 / 650 / 700 / 750 °C [D, verificado].

**Âncoras:**
- Nenhum aumento de gás entre 500 e 550 °C com ~96 s de residência de vapor (Pires [35] [TC]): o modelo dá 8,4 % de conversão.
- "Ampla gama de produtos" a 625 °C / 1,4 s: o modelo dá 4,9 %.
- "Majoritariamente gás + aromáticos" a 675 °C / 5,6 s (Gracida-Alvarez [38] [R]): o modelo dá 81 %.
- Iniciação alílica CRECK 0,8e16 exp(−71000/RT), com unidades inferidas como cal/mol (≈297 kJ/mol) [36] [TC].
- A 750 °C o vapor já é gás leve em 1,6 s [37] [TC]. **A citação de van Wyk usada por Li 2026 não justifica desprezar a fase gás**.
- A Opção A (1,3e12 exp(−230/RT)) dá 27 % a 550 °C / 96 s e contradiz Pires: **descartada**.

**Especiação do gás por temperatura:**
- HDPE: etileno dominante a 700-800 °C, CH₄ acima de 900 °C [39] [TC].
- PP: propileno + CH₄ [39] [TC].
- C₂H₄ no máximo 40-50 % em massa num segundo estágio a 700-1000 °C [36] [TC].
- Pós-processamento opcional com o mecanismo CRECK de PE (155 espécies, 3558 reações) [36].

**Consequência para o forno:** com o vapor residindo por minutos, o craqueamento é decidido pela **temperatura do gás junto à parede quente e no freeboard**. O 3D resolve isso.

### 3.8 Fase gasosa e freeboard

- **Equações:** Navier-Stokes low-Mach com densidade variável (ρ = pM/RT). Na base piloto o escoamento é laminar: Re_ω ≈ 500 e Gr ≈ 2,6e7, com o topo quente e o leito frio embaixo, o que dá estratificação estável [D]. No industrial (Gr ~2e9) usamos k-ω SST, já existente.
- **Escalares:** N₂, W, O, G, A, H₂O, HCl, T e a **idade média do gás**, ∂(ρa)/∂t + ∇·(ρua) = ∇·(ρD∇a) + ρ. É a técnica padrão de CFD [U, verificar referência]. Uma idade ponderada pelo vapor dá a residência local.
- **Fontes:** o fluxo de vapor por z sai da corda do leito (superfície plana inclinada no ângulo dinâmico, com velocidade tangencial u_s); na zona de lifters, há fontes volumétricas na cortina.
- **Purga e saída:** N₂ co-corrente, saída no topo da extremidade de descarga mais o duto. Não há dado quantitativo para comparar saída co-corrente e contracorrente (lacuna).
- **Insert central** (variante): cilindro fechado de 20 cm × 230 cm que corta a residência do vapor "nearly half" [50] [TC]. Sem ele: mais gás, grumos e alimentação pegajosa.
- **Mapa de risco de deposição de cera:** ponto de orvalho e ponto de fluidez do lump pesado (corte de Riazi do código existente) comparados com T da parede e do duto. A incrustação de condensadores e dutos é documentada só de forma qualitativa [E, S].

### 3.9 Vedação, entrada de ar e inertização

**Selos:** vazamento relativo segundo a FEECO [54] [TC]:
- labirinto ≫ 5 %;
- lâmina simples ≪ 3-5 %;
- lâmina dupla ≪ 1-3 %;
- fole ≪ 1 %.

"Vazamento relativo" não é definido pela FEECO, então **não serve como condição de contorno**. Usamos um modelo de orifício por selo: ṁ_ar = C_d·A_folga·√(2ρ|Δp|) quando Δp < 0 (entra ar); quando Δp > 0, sai a purga. A_folga vem de cenários por tipo de selo [H]. Lâmina dupla purgada: o N₂ escoa para fora e o O₂ não entra [76] [TC].

**Faixas de pressão na literatura:**
- +7 a +207 Pa [50] [TC];
- "a few mbar" abaixo da atmosfera [47] [TC];
- −125 Pa no PREPP [57] [TC];
- 3 kPa de selo dinâmico na Beston [59] [vendedor].

**Limites de O₂:**
- NFPA 69 (LOC atualizado, N₂): H₂ 4,6; CO 5,1; CH₄ 11,1; C₂H₄ 8,5; C₃H₈ 10,7 % vol [53] [TC].
- Limite monitorado = 0,6 × 4,6 = **2,76 % de O₂**; não monitorado = 1,84 %.
- A meta de patente de ≤ 1 % é de um reator vertical de bandejas [H, TC].
- LOC do gás de pirólise a 520 °C talvez de ~3 % [52] [S].

**Partida:**
- Diluição perfeita: 2,0 trocas de volume até 2,76 % e 3,0 trocas até 1 % [D].
- Com 1,5 Nm³/h frio no freeboard de 0,70 m³: ~85 min até 1 % [D]. Recomendar purga de partida de ≥ 10 Nm³/h.
- O 3D mostra zonas mortas.
- Pressurização não substitui purga: 40 kPa → 15 % de O₂ [52] [TC].

### 3.10 Potência de acionamento

**CE Raymond/Perry** (via NPTEL [56] [S], exemplo reproduzido): P[W] = N·(0,2562·d·w + 0,01038·D′·W + 0,00543·W), com N em rpm, d e D′ (anel ≈ d + 0,61 m) em m, w (carga viva) e W (total girante) em kg.

**Torque do centro de gravidade:** T = m·g·r_cg·sin θ, com r_cg = 2R sin³ε / [3(ε − sin ε cos ε)] [D].

Partida: ×2,5 [55] [TC]. Somar o arrasto dos selos, que no PREPP sobrecarregou o acionamento [57].

**Resultados:**
- Caso A: 0,03-0,2 kW [D].
- Caso B: 3,2-3,4 kW a 0,4 rpm e 6,4-6,7 kW a 0,8 rpm; motores de vendedor 4-5,5 kW [D, verificado].
- Plantas: 800 kW para um forno de 6 m × 60 m a 3 rpm [S, TC].

Fica sempre abaixo de ~1 % da potência térmica.

---

## 4. Arquitetura do modelo no Colab (T4)

### 4.1 Decisão contra as alternativas

| Opção | Custo no T4 | Veredito |
|---|---|---|
| CFD-DEM 3D do forno inteiro | Star-CCM+ (Lund): ~2000 partículas, 66-448 mil células, **21,6/32,5/46,2 h em 64 núcleos para 15 s** físicos [28] [TC]. KIT: "about one day" para poucos segundos em 3D [31] [TC]. O processo dura 30-90 min (60-180 revoluções) | **Rejeitada** no Colab. Entra como benchmark para a equipe Star-CCM+ (4.7, 5) |
| DEM em fatia periódica na GPU | ~5,7e6 partícula-passos/s num código CUDA otimizado (incerteza 2-3×) [D]; PyTorch puro, 3-10× mais lento [U]. Fatia de 34 mil esferas: ~15 s físicos (~1,5 rev) em 30 min [D]. Em plásticos o caminho dominante é o gap de gás, e não só Hertz [74] [R] | **Opcional** (calibração e visual), fora do caminho crítico |
| Euleriano granular (KTGF, dois fluidos) | Viável em 2D (Yin 2016 [73] [R]). Mas o leito rolante é denso e lento, de regime friccional quase-estático; a camada ativa fina exige malha fina; e não há fechamento para partícula revestida de fundido | **Rejeitada**. μ(I) fica como opção futura [U] |
| **Quasi-3D (1D axial + fatias 2D lagrangianas) + freeboard 3D + correlações validadas** | 1D em segundos; 2D em 5-12 min; 3D em 10-25 min [U] | **Escolhida**. Precedentes: Boateng & Barr [21]; Marias [71]; Mujumdar & Ranade [72]; Babler, 1D validado em 9 corridas piloto [70] [R] |

### 4.2 O que fica em 3D, 2D, 1D ou correlação

**L1, espinha 1D axial (z, 400 células, dz = 10 mm):**
- Saeman com q_v(z).
- Balanços de massa por componente: polímeros, fundido, carreador, char, HCl.
- Energia do leito em média de seção, que é substituída pela fatia 2D no acoplamento.
- Casca concentrada e zonas de aquecedores.
- Gás em fluxo pistonado, como fallback e estimativa inicial.
- Radiação 2D por célula axial.
- Regime, flags de estado e Sullivan para checagem.
- Transiente no Caso B (dt = 1 s), regime permanente no A e no C.

**L2, fatias transversais 2D lagrangianas (Boateng quasi-3D):**
- Cada fatia viaja com os sólidos (t ↔ z(t) pelo 1D).
- Grade cartesiana com máscara SDF: 192² para D 0,5 m (dx 2,6 mm); 256² para D 2,6 m (dx 10 mm).
- Resolve energia, conversão por componente, fração fundida e estado.
- Campo de velocidade:
  - (i) **granular**: cinemático do leito rolante (3.2), calibrado em Boateng/Nafsun;
  - (ii) **piscina de fundido**: escoamento de Stokes/NS 2D estacionário resolvido com o solver MAC/Brinkman em modo 2D, com corda livre de tensão, recalculado quando μ muda mais de 3×;
  - (iii) **estático**: u = 0.
- Camada de parede sub-malha 1D.
- Contorno superficial: radiação mais convecção, mais fluxo de vapor.
- Na zona de lifters: holdup e parcelas de cortina de Sunkara.
- As fatias são processadas em lote num único tensor (configurações × rpm).

**L3, casca 2D (θ, z) desenrolada:** 256 × 400; implícita; mapa de ciclo regenerativo.

**L4, freeboard 3D:** MAC + Brinkman (cilindro girante, corda do leito, lifters, dutos); low-Mach; escalares estacionários; craqueamento; idade; risco de cera.

**L5, correlações e submodelos 0D:** contato (série), Seghir-Ouali, Tscheng (sensibilidade), Sunkara, Karali, Schofield-Glikin, Saeman e Sullivan, selos e O₂, acionamento, perdas.

**Partículas para o vídeo:** 2e5 a 1e6 traçadores cinemáticos (camada passiva, camada ativa com passeio aleatório, cortina balística com arrasto, avanço axial do 1D), coloridos por T e fração fundida amostradas das fatias. **O vídeo informa que não é DEM.**

### 4.3 Acoplamento (Picard externo, como no tanque agitado)

0. O 1D roda com correlações e produz h(z), F(z), T_w, T_b e T_g iniciais (segundos).
1. Fatias 2D em lote, conduzidas por T_w(z(t)) e pelos fluxos radiativos. Devolvem fluxos de parede, T superficial e taxa de vapor por espécie em função de z.
2. Casca 2D mais zonas: Modo A (T_w de setpoint, devolve potência) ou Modo B (potência, devolve T_w).
3. Freeboard 3D: entra com as fontes na corda e na cortina; devolve T_g, composição, craqueamento, fluxo convectivo e idade.
4. Repetir 1-3 até os KPIs (T_b de saída, conversão, Q por zona, split de produtos, máximo de T_w − T_b) variarem menos de 0,5 %. Esperado: 2-4 iterações.

Fechamento de energia < 1 %. O acoplamento térmico é obrigatoriamente bidirecional: o acoplamento unidirecional aquece as partículas "unreasonably fast" [28] [TC].

### 4.4 Numérica e presets

- **2D:** advecção semi-lagrangiana (CFL 2-4) ou TVD van Leer. Difusão implícita (Crank-Nicolson, um solver FD em 2D). Cinética rígida integrada por exponencial exata célula a célula.
- **3D:**
  - Projeção low-Mach com Poisson de coeficiente variável por PCG, pré-condicionado pelo solver FD de coeficiente constante do flarekit. Variante rápida: divisão de Dodd-Ferrante [U, verificar].
  - Brinkman implícito com máscaras supersampleadas 4³. Sólidos com ≥ 2,5 células: lifters engrossados para 20 mm.
  - Pseudo-transiente até regime estatístico, seguido de escalares estacionários (Ψtc + BiCGSTAB, código existente).
  - Para o vídeo, um transiente curto de 2-3 revoluções com lifters móveis.

| Preset | 1D | 2D (por fatia; nº de fatias) | 3D (piloto) | Memória [U] |
|---|---|---|---|---|
| teste | 200 | 96²; 6 | 32×32×256 (0,26 M; dx 16 mm) | < 1 GB |
| **gpu (T4)** | 400 | 192²; 12-16 | **64×64×512 (2,1 M; dx ≈ 8 mm)** | ~3-5 GB |
| gpu_fino (T4) | 800 | 256²; 12 | 80×80×640 (4,1 M; dx 6,3 mm) | ~7-9 GB |
| industrial (Caso C) | 800 | 256²; 8 | 80×80×576 (3,7 M; dx 35 mm, SST) | ~6-8 GB |

Estudo de malha com GCI (Celik 2008) no 3D (48/64/85 na seção) e no 2D (128/192/256).

### 4.5 Tempo de execução estimado (T4) [U]

| Etapa | Tempo |
|---|---|
| Setup, benchmark e verificação N0 | 3-5 min |
| 1D: base mais varreduras (~50 casos em lote) | 1-2 min |
| Fatias 2D do Caso A: 12-16 fatias, ~35 min físicos (~70 rev a 2 rpm, dt 0,02-0,05 s) | 4-8 min |
| Caso B: 2 fatias (estática e rotativa), 10 h físicas a 0,4 rpm | 3-5 min |
| Freeboard 3D (gpu), 3 iterações de Picard | 12-25 min |
| Render SDF e vídeo 1080p de 90 s | 8-12 min |
| **Produção completa** | **~35-55 min** (preset teste ≤ 10 min) |

### 4.6 Reaproveitamento do código do tanque agitado (reactorkit/flarekit → kilnkit)

| Existente | Uso no kilnkit |
|---|---|
| `geometry.py` (SDFs) | Cilindro inclinado, lifters, anéis de rolamento e roletes (render), corda do leito, dutos; exportação STL para o Star-CCM+ |
| `flow.py` (MAC, RK2, Brinkman, Poisson FD, SST) | Freeboard 3D low-Mach (PCG + FD); piscina 2D de Stokes |
| `scalars.py` (Ψtc, BiCGSTAB, TVD) | Espécies, idade e T no freeboard; advecção-difusão das fatias |
| `kinetics.py` (RS-L2) | Primária mais Westerhout, PVC, PET e Opção B (nova) |
| `rheology.py` | μ para a flag de estado e para o filme de parede |
| `props.py` (Riazi, propriedades, guard) | Ponto de orvalho e de fluidez da cera; propriedades |
| `freeboard.py` | Passa a ser o módulo 3D principal |
| `render.py`/`hd.py` (ray-marching SDF, vídeo) | Cenas 1-8 (seção 6); fatores de forma 2D por ray-casting |
| `validation.py` (PASS/FAIL) | Escada da seção 5 |
| **Novos módulos** | `kiln1d.py` (Saeman, espinha, casca), `slice2d.py`, `wallsub.py`, `radiation2d.py`, `flights.py` (Sunkara/Karali), `seals.py` (O₂/NFPA), `drive.py`, `lagrange.py` (parcelas e traçadores) |

Ordem do notebook:
1. Setup/benchmark
2. Alimentações
3. 1D
4. N0
5. N1
6. Fatias e estático × rotativo
7. 3D base
8. Varreduras (T_w, rpm, N₂, insert, carreador × lifters)
9. Caso B
10. Caso C
11. Malha
12. Figuras e vídeo

### 4.7 Protocolo quantitativo "estático × rotativo"

**P1, fatias do Caso A.** Mesmo histórico T_w(t), mesma carga e mesma composição. Configurações:
- ω = 0 (estático);
- "rotação sem mistura": corpo rígido sem camada ativa, para separar rotação de mistura;
- 0,5 / 1 / 2 / 3 / 6 rpm;
- com e sem carreador.

**P2, Caso B.** Mesma potência de queimador (1,05 MW, com teto) e também mesma T_w máxima. Comparar o tambor girando a 0,4 rpm com o parado.

**KPIs, com mesma definição para todas as corridas:**
1. Não uniformidade: σ_T(t) e ΔT_max = T_max − T_min no leito.
2. Fração de massa acima de 450 °C e abaixo de T_m em função do tempo.
3. t90 da fatia (conversão de 90 %).
4. **Superaquecimento de parede** T_w − T̄_b para o mesmo fluxo. Referência [D]: com h 20-40 W/m²K a 5 kW/m², a parede fica 125-250 K acima do leito girando; com o leito estático, a camada de condução cresce em horas.
5. **Índice de carbonização na parede:** ∫ m(T > 550 °C) dt na camada de 5 mm junto à parede. Ligação qualitativa com [51].
6. h_ws efetivo e U (base Suzuki) em função da rpm, comparados com Nafsun (h(6)/h(1) = 1,2-2,4) e Suzuki (+12 %).
7. Partição contato/radiação.
8. No Caso B: T_w máxima da casca contra a temperatura de autoignição do gás, como paralelo a Hedlund.

**Contínuo:** curva de conversão na saída e F em função da rpm com alimentação fixa. Mais rpm aumenta h (∝ n^0,2-0,5) mas reduz τ (∝ 1/n), o que mostra a interação documentada em Babler [70] [R].

**Benchmark que o público pode reproduzir no Star-CCM+** [28] [TC]:
- Tambor de 300 × 65 mm, parede a 773 K, 6 rpm, N₂ 350 ± 10 mL/min, LDPE de 2,5 mm (2000 partículas/s durante 1 s).
- T média das partículas a 100 s: ~600 K (Zhang 2022, de segunda mão) contra ~540 K (Lund).
- Nosso modelo de fatia com parcelas deve cair na faixa de 540-600 K.

---

## 5. Escada de validação (só dados verificados como alvo)

**N0, verificação de código.** Tudo PASS/FAIL automático.

| Teste | Alvo | Tolerância |
|---|---|---|
| Balanços de massa e energia (1D; acoplado) | Fechamento | < 0,1 %; < 1 % |
| Saeman: profundidade normal e ordem do integrador | Analítico | < 1e-4 relativo |
| Sullivan = Saeman raso | Coeficientes (180/π²) sin θ e 1,77√θ | Exato a 35°; ≤ 13 % em 25-45° [D] |
| Camada sub-malha × erfc semi-infinita | Analítico | < 1 % |
| Penetração × coluna "Wes" de Nafsun Tab. 2 | Reproduzida em 1-3 % [4] [TC, D] | ≤ 3 % (5 de 6 materiais) |
| Radiação: soma dos fatores de forma; duas superfícies | 1; analítico | < 1e-6; < 1 % |
| Modelo mínimo de Le Guen sem radiação | Relaxação exponencial (Eq. 9) [20] [TC] | < 1 % |
| Fatia 2D | Rotação rígida de escalar; difusão analítica | < 1 % |
| Cinética | Isotérmica exp(−kt); picos de DTG 475/465/455/420 °C | 1e-6; ±2 K |
| Idade do gás num tubo | Abdy: 1,76 s a 500 °C e 4 L/min (V = 3,04e-4 m³) [40] [TC] | < 2 % |
| 3D | Couette rotativo laminar / spin-up; GCI | < 1 %; GCI < 5 % |

**N1, componentes.**

| Componente | Dataset | Alvo | Tolerância |
|---|---|---|---|
| Transporte axial | Colin 2015 Tab. 2, 8 corridas (D 0,21 m, L 4,2 m, 1-2°, 2-4 rpm, 4-8 kg/h, θ 42°) [8] [TC] | MRT 31,8-109,4 min; hold-up 5,2-18,1 %; σ/τ < 10 % | MRT ±25 % (Saeman: viés de +4 a +25 %); Sullivan ±13 % |
| RTD | Colin (Pe 361-645) [8]; Thammavong (τ 37-47 min, Pe ~2000, 3 rpm, 2°, 2,5 kg/h) [10] [TC] | Pe e σ | Ordem de grandeza; σ/τ ±30 % |
| Regime | Faixas de Fr de Mellmann e Henein [23] [TC] | Rolamento previsto em 5e-4 < Fr < 1e-2 com F > 10 % | Aviso coerente |
| Cinemática transversal | Boateng Tab. 4.2, pellets de PE (3,3/8,5/15/29 % de enchimento; 0,9-5,2 rpm) [21] [TC] | Camada ativa em % da profundidade; u_s/(ωR) | ±20 %; ±25 % [U] |
| Mistura térmica | Nafsun 2015: ~59 s a 6 rpm, F 20 %, vidro 2 mm, ΔT ≤ 5 K [5] [TC] | Tempo de mistura | ±30 % |
| Contato parede-leito | Nafsun 2014 Tab. 2: 6 materiais, 1 e 6 rpm, F 20 % [4]; Moumin: areia 136,5 (64-184) W/m²K a 1 rpm, F 10 % [6] [TC] | h_ws | Dentro da faixa medida ±20 %. Tendências: dh/dn > 0, dh/dF < 0, dh/dd_p < 0 |
| Efeito de tiras | Moumin: ×2,2/2,9/3,1 a 1/2/3 rpm (F 5 %) em pó coesivo [6] [TC] | Fator | ±30 % |
| Lifters, carga e queda | Karali: f_design 4,8-14,8 % no tambor de 0,5 m; queda 28,2-31,0 cm a 3 rpm [17] [TC] | f_design; h_queda | ±15 %; ±15 % |
| Lifters, troca térmica | Bongo Njeng: retangular > sem lifters > reto, 45-1132 W/m²K [15] [TC] | Ordenação e faixa | Tendência mais ±50 % |
| Calcinador (DEM/contínuo) | Chaudhuri: tubo de 6 in, alumina, 10-30 rpm, parede a 100 °C; efeito "mínimo" da rpm [25] [TC] | Curvas de aquecimento quase iguais | Tendência |
| Cinética TGA | Westerhout Tab. 4: t90 do HDPE 15,7 min a 450 °C [33] [TC] | RS-L2: 14,8 min | ±30 % |
| Aquecimento limitado (fundido estático) | Pires: 30 min a 450 °C → 80,09 % não convertido, contra 98,8 % previsto pela cinética [35] [TC] | Conversão ≪ cinética | Tendência (histórico térmico da amostra não reportado) |
| Leito fixo | Durdevic: 19,7 → 12,1 °C/min com plástico; queda da taxa em 419-483 °C [61] [TC] | Taxa de aquecimento | ±25 % |
| Craqueamento no freeboard | Opção B contra Pires (≤ 10 % a 550 °C / 96 s), Gracida-Alvarez (~81 % a 675 °C / 5,6 s), van Wyk (gás leve a 750 °C / 1,6 s) | Conversão do lump O | Qualitativo (âncoras) |
| Sensibilidade de modelo | Patisson Tab. I [9] [TC] | Sinais de ∂T/∂ε, ∂T/∂h | Tendência |

**N2, sistema.**

| Caso | Dataset | Alvo | Tolerância |
|---|---|---|---|
| **Suzuki 2008** (batelada externa, SUS310S, ID 1 m × 1,5 m) [2][3] [TC] | k_m-w de 22→55 W/m²K (555 °C) e 27→55 (630 °C); fluxo pico ~11 e 16,5 kW/m². Médias: 38,6 (2,7 rpm), 43,4 (4,0 rpm), 45,3 (6 × 200 mm), 50,1 (ambos). Tempo de pirólise 42 / 30 / 31 min. Resíduo simulado: papel 30, madeira 25, PE 15, PP 15, PS 5, grão 10 % + 10 % de umidade | Média de k_m-w; pico de fluxo; tempos | ±25 %; ±20 %; ±20 %. Sinal e ±50 % nos incrementos de lifter e rpm. Papel, madeira e grão entram com cinética genérica [H], o que fica marcado |
| **Hwan 2009** (indireto, 0,498 × 3,98 m, lifters de 0,08 m) [16] [TC] | U gás de combustão → leito 31→35 W/m²K; enchimento 14-17 %; MRT ~15 min | U; MRT | ±25 % (carvão; geometria igual à do Caso A) |
| Beckmann 2003 (areia 90 + PE 10 kg/h, parede 300/400/500/500 °C, N₂ 0,8 Nm³/h) [13] [TC] | Perfis só em figura | Tendência de T_leito(z) | Qualitativo (digitalizar) |
| Bhatt 2026 (SS304, 1360 × 355 mm, 2 rpm, 500 °C, 20 °C/min, 90 min, N₂ 5 L/min) [44] [TC] | Óleo 40-45 % | Óleo | ±7 pontos. Char **não** entra como alvo (inconsistente) |
| Lab Zhang/Lund [28] [TC] | T média das partículas a 100 s | 540-600 K | Dentro da faixa |
| Pichler 2021 (13 851 casos 1D) [62] [TC] | Código contra código: altura do leito, MRT, temperaturas | | 10 %; 20 K |
| Hamm (Caso C) [46] [TC] | Processo ~500 °C com casca 750 °C; ~1,5-2,2 MJ/kg; F 15 %; 90 min | Plausibilidade | ±25 % (alimentação diferente) |
| Kern (Dürnrohr) [47] [TC] | Gás de aquecimento 800-1000 °C; parede > 650 °C; saída 350-650 °C | Plausibilidade de camisa | Qualitativo |

**Não usados como alvo** (não verificados ou errados):
- ganho de gás do PP com T segundo Kodera e a geometria da bancada [48];
- "57,6 % de óleo a 625 °C" de Zhang 2020 (ausente do resumo; nenhuma fonte encontrada);
- gás de HDPE de 32,6 → 56,3 % de Liu/Dai/Li [67] (o artigo existe; os números não foram vistos);
- ótimo de 4 r/min;
- números de Li A.M. 1999;
- Zhou 2025 [63] (só tendência; h com definição desconhecida);
- 74-107 W/m²K da patente;
- tempo de mistura de "2 revoluções" de Wes;
- 70-75 % da potência gastos no movimento do material (Liu 2016).

---

## 6. Saídas para o evento

**Figuras (PNG 300 dpi e versão para slide, rótulos em PT-BR):**
1. Placar das alegações KINTEK: tabela da seção 1.3 com o número-chave de cada linha.
2. **Estático × rotativo** (P1): mapas 2D de T e fração fundida a 2, 5, 10 e 20 min; σ_T(t); conversão(t); superaquecimento de parede.
3. h_ws e U em função da rpm: modelo contra Nafsun (6 materiais), Moumin e Suzuki (38,6 → 50,1).
4. Perfis axiais do Caso A: T_w, T_b, T_g, h(z) e F(z), conversão, mapa de estado (granular/pegajoso/líquido), fluxo por zona.
5. Casca desenrolada (θ, z) com a assinatura regenerativa.
6. Freeboard 3D: idade do vapor (s), isossuperfície de cera, T_g, linhas de corrente; zona de craqueamento junto à parede quente.
7. **Split de produtos** (óleo, cera, gás, aromáticos, char) em função de T_parede (550-700 °C), da purga de N₂ (0,5-5 Nm³/h) e do insert central.
8. Compromisso da rpm em contínuo: τ, F e h em função de n, e conversão na saída.
9. Carreador × lifters × sem internos: U, índice de aderência e incrustação, mapa da cortina.
10. Sankey de energia: contato, radiação, convecção, perdas e carreador. Comparação com Hamm (~1,5-2,2 MJ/kg).
11. Inertização: O₂ em função do vazamento e de Δp, com a linha de 2,76 % (NFPA 69); purga de partida; nota sobre Hedlund (40 kPa → 15 %).
12. Acionamento: Perry, CG e vendedor; motor < 1 % da potência térmica.
13. Painel de validação: PASS/FAIL por nível, com fonte e tolerância.
14. Caso B: T_w máxima e conversão em função do tempo para tambor parado e girando.

**Vídeo HD (1080p, H.264, ~90-120 s, renderizador SDF):**
- **C1, exterior (8 s):** tambor inclinado sobre anéis e roletes, zonas de aquecimento em brilho térmico, rotação, purga.
- **C2, corte longitudinal (15 s):** entrada com carreador e flocos fundindo; leito rolante; últimos 0,8 m com lifters derramando char e carreador pela atmosfera quente. Traçadores coloridos por T e fração fundida; legenda "cinemática calibrada, não DEM".
- **C3, tela dividida estático × rotativo (20 s):** fatias 2D com relógio; frente quente presa à parede contra leito renovado; contador de superaquecimento.
- **C4, freeboard (15 s):** linhas de caminho coloridas pela idade do vapor; a cera "acende" ao tocar a parede de 650-700 °C; contador de produtos.
- **C5, casca desenrolada (8 s):** ciclo regenerativo e fluxo por zona.
- **C6, tambor batelada, 10 h em 20 s:** fardos, piscina de fundido, vapor de óleo, T da casca; versão parada com alarme de superaquecimento e de O₂.
- **C7, controles (10 s):** medidores do split de produtos respondendo a T_w, rpm e N₂.
- **C8, slide de checagem cruzada com o Star-CCM+ (5 s):** benchmark de Lund/Zhang com as condições e o alvo de 540-600 K.

---

## 7. Riscos, lacunas e hipóteses

### 7.1 O que não foi lido em texto completo (usar como faixa, não como alvo)

- **Cinética e energia:** Ea de Aboulkas (base do RS-L2; resumo retido pela editora); calores de DSC de Stoliarov & Walters (servidor da FAA com erro 503).
- **Plantas e fornos de plástico:** Kodera 2021 (bancada, rendimentos, geometria de 200 kg/h); Zhang 2020 FPT e Zhang 2022 CEJ; números de Liu/Dai/Li 2026; Kulas 2021 (dados TSMR para calibrar a Opção B); Gracida-Alvarez (só o resumo).
- **Mecânica do leito:** tabela completa de Mellmann 2001 (bandas de avalanche, cascata e catarata); Henein 1983; correlação de enchimento na descarga de Specht 2010 (F0 = 1,75·Bd^0,5, com Bd indefinido); Wes 1976; Emady 2016; dados T4/A11 de Barr e Tscheng; original de Tscheng 1979 (unidade de n); Komossa 2015.
- **Contato e lifters:** Herz 2012 (IJHMT e CES); Seidenbecher, dissertação (só o artigo GM 2022 foi lido).
- **Outros:** Babler 2017, Mujumdar & Ranade, Marias 2003/2005 e Yin 2016 (resumo ou página do autor); Islam 2013, Gamboa 2023 e Syamsiro 2019 (resumos); páginas de vendedores (são alegações).

### 7.2 Valores julgados errados ou corrigidos (não usar na forma original)

- "Ótimo de enchimento de 15-20 % para lifters": o correto é 5-15 %.
- "31-35 W/m²K em forno indireto sem internos": é U de gás de combustão → leito, **com** lifters (Hwan).
- "Lifters +30 %": lifters sozinhos dão +15-17 %; +30 % só com 4 rpm junto.
- "Retas em √n" para h_ws: errado.
- 610 kg/m³ "pellet plástico": é pellet de biomassa.
- Residência do vapor em Hamm de 20-35 s: o correto é 1-6 min.
- "73 min medidos" em Pires: é extrapolação de modelo.
- χ = 0,59 a 4 mm: o ajuste dá 2,35; não extrapolar.
- Tscheng com n em rev/s: usar ω em rad/s.
- Mines Albi 1000 °C: o correto é 1050 °C.
- Eficiência de 67 % "da palha": é DDGS; palha = 0,55.
- Rendimentos de pneu "15/40/45 ± (Porto)": atribuição errada.
- Matriz 1/3/6 rpm atribuída a Zhang 2020: provavelmente é de Herz 2012.
- "4.600 kJ/kg" de Beckmann: ambíguo.
- Aquecimento a 200 °C/s com carreador: implausível.
- h_cwa = 0,26 W/m²K em Patisson: implausível.
- h_bg nominal de Le Guen (102,83) fora da própria faixa de validade. h_sw de Le Guen só vale para ω = 3,5-10 rad/s, logo é extrapolado em fornos reais.
- "Ethylene first" em Pohl vale só para HDPE.
- A1 do PVC: usar 1,79e6 min⁻¹ (lei final), não 1,81e6.

### 7.3 Hipóteses de modelagem (declarar no vídeo e no relatório)

- Regime de rolamento com corda plana inclinada no ângulo dinâmico.
- Sólidos em fluxo pistonado (Pe ≥ 300 na base).
- Fatia lagrangiana sem troca axial entre fatias.
- Radiação local à seção, cinza e difusa; gás transparente na base.
- Fundido absorvido nos vazios do carreador; coesão representada por +Δθ.
- Sem modelo de aglomeração (só índice).
- Carreador recirculado a 350 °C.
- Split primário G/O/W e Opção B calibrados por nós.
- Papel, madeira e grão de Suzuki com cinética genérica.
- Propriedades de flocos e fundido em faixas de manual.
- Emissividade do leito plástico = 0,9 (não medida).
- Vazamento dos selos por orifício com área de cenário.

### 7.4 Riscos técnicos e mitigação

| Risco | Mitigação |
|---|---|
| 3D estoura o orçamento de tempo | Presets; regime permanente com escalares implícitos; checkpoints no Drive; o 3D é opcional no Caso C |
| Instabilidade no acoplamento | Sub-relaxação de 0,5 nos fluxos; Modo A primeiro |
| Zona pegajosa sem validação | Mostrar como risco/índice, nunca como previsão; variante A-L rotulada "contraexemplo" |
| Saeman inválido na piscina sem carreador | Troca para modelo de vertedouro, com flag |
| Calibração da química | Mostrar faixas (Opções A/B, φ_A) e pedir dados TSMR (Kulas) |
| Espalhamento dos modelos de contato (até 3×; compilações vão de 0,08 a 185 W/m²K) | Usar o modelo em série validado em Nafsun/Moumin e reportar banda ±20-50 % |
| Mensagem sobre a KINTEK | Citar a página só como referência de conceito, sem logotipo nem imagens deles; separar "física" de "marketing" |

---

## 8. Referências

1. KINTEK, "Qual é a importância da rotação em um reator de forno rotativo de pirólise" (FAQ). https://pt.kintekfurnace.com/faqs/what-is-the-significance-of-rotation-in-a-pyrolysis-rotary-kiln-reactor [lido; qualitativo]
2. Suzuki T., Okazaki T., Yamamoto K., Nakata H., Fujita O. (2008) J. Thermal Sci. Technol. 3(3):523-531. https://www.jstage.jst.go.jp/article/jtst/3/3/3_3_523/_pdf [TC]
3. Suzuki T. et al. (2008) J. Thermal Sci. Technol. 3(3):532-539. https://www.jstage.jst.go.jp/article/jtst/3/3/3_3_532/_pdf [TC]
4. Nafsun A.I., Herz F., Specht E., Scherer V., Wirtz S. (2014) The contact heat transfer in rotary kilns and the effect of material properties, HEFAT2014. https://repository.up.ac.za/handle/2263/44635 [TC]
5. Nafsun A.I. et al. (2015) Experimental investigation of thermal bed mixing in rotary drums, HEFAT2015. https://repository.up.ac.za/handle/2263/55877 [TC]
6. Moumin G., Tescari S., Sattler C. (2021) IJHMT 177:121473. https://elib.dlr.de/145982/1/Moumin2021.pdf [TC]
7. Colin B. (2014) Tese, École des Mines d'Albi-Carmaux. https://theses.hal.science/tel-01162630v1 [TC]
8. Colin B., Dirion J.-L., Arlabosse P., Salvador S. (2015) Wood chips flow in a rotary kiln: experiments and modeling. https://hal.science/hal-01165159 [TC]
9. Patisson F. et al. (2000) Coal pyrolysis in a rotary kiln: Part II, Metall. Mater. Trans. B 31B:391-402. https://hal.science/hal-01411207v1 [TC]
10. Thammavong P. (2010) Tese, UPMC/CNAM. https://hal.science/tel-05119895v1 [TC]
11. Hared I.A. (2007) Tese, INP Toulouse. https://ut-toulouseinp.hal.science/tel-04619234v1 [TC]
12. Lebas E. (1995) Tese, INPL Nancy (pirólise de carvão em forno rotativo). URL não registrada; lida de cópia local (artigo companheiro: [9]) [TC]
13. Beckmann M., Fontana A., Gehrmann H.-J. (2003) Mathematical modeling and experimental investigation of the pyrolysis of waste in rotary kilns. https://tu-dresden.de/ing/maschinenwesen/ifvu/evt/ressourcen/dateien/Veroeffentlichungen/Beckmann_90-07/Be-68.pdf [TC]
14. Wade W.R. (1959) NASA memo, emissividade de metais oxidados. https://ntrs.nasa.gov/citations/19980228304 [R]
15. Bongo Njeng A.S. et al. (2018) Exp. Therm. Fluid Sci. 91:197-213. https://hal.science/hal-01624450/file/publiAlexWTSHTC_pourHAL.pdf [TC]
16. Hwan I.H. (2009) Tese, Curtin University. https://ndownloader.figshare.com/files/62348503 [TC]
17. Karali M.A. (2015) Tese Dr.-Ing., OVGU Magdeburg. https://d-nb.info/1076590195/34 [TC]
18. Sunkara K.R. (2013) Tese Dr.-Ing., OVGU Magdeburg. https://d-nb.info/1054420610/34 [TC]
19. Seidenbecher J., Herz F., Sunkara K.R., Mellmann J. (2022) Granular Matter 24:123. URL não registrada (Springer OA) [TC]
20. Le Guen L., Piton M., Hénaut Q., Huchet F., Richard P. (2017) Can. J. Chem. Eng. (arXiv:1612.05762). https://arxiv.org/pdf/1612.05762 [TC]
21. Boateng A.A. (1993) Tese, UBC. https://open.library.ubc.ca/collections/831/items/1.0078512 [TC]
22. Barr P.V. (1986) Tese, UBC. https://open.library.ubc.ca/collections/831/items/1.0058741 [TC]
23. Santos D.A. et al. (2016) Braz. J. Chem. Eng. 33(3). https://www.scielo.br/j/bjce/a/ytYHqkDk3fnz9nXfLrq9MTj/?format=html&lang=en [TC]
24. Lisboa M.H. et al. (2007) Braz. J. Chem. Eng. https://www.scielo.br/j/bjce/a/dGNdtNDQFjKfrJ7jHRfCF4L/ [TC]
25. Chaudhuri B., Muzzio F.J., Tomassone M.S. (2011) InTech, doi:10.5772/13536. https://www.intechopen.com/citation-pdf-url/13420 [TC]
26. Fang L. et al. (2021) Chrono::GPU, Processes 9:1813. https://par.nsf.gov/servlets/purl/10349475 [TC]
27. NVIDIA T4. https://www.nvidia.com/en-us/data-center/tesla-t4/ [TC]
28. Belcher E.C. (2026) Dissertação de mestrado, Lund (Star-CCM+ CFD-DEM). https://lup.lub.lu.se/student-papers/record/9229310/file/9232854.pdf [TC]
29. Zhang M. et al. (2022) Chem. Eng. J. 445:136686. https://research-repository.rmit.edu.au/articles/journal_contribution/Numerical_investigation_on_the_heat_transfer_of_plastic_waste_pyrolysis_in_a_rotary_furnace/27558666 [R]
30. Zhang Y.-T., Ji G., Chen C., Wang Y., Wang W., Li A. (2020) Fuel Process. Technol. 206:106455. https://www.sciencedirect.com/science/article/abs/pii/S0378382020301508 [R]
31. Li M., Zhang F. et al. (2026) Particuology 115:214-227. https://publikationen.bibliothek.kit.edu/1000194351 [TC]
32. Zhang F., Tavakkol S., Galeazzo F.C.C. et al. (2025) Particle-resolved simulation of a single plastic particle. https://publikationen.bibliothek.kit.edu/1000178201 [R]
33. Westerhout R.W.J. et al. (1997) Ind. Eng. Chem. Res. 36:1955-1964 (doi:10.1021/ie960501m). https://ris.utwente.nl/ws/files/6513651/kinetics_of_the_low-temperature.pdf [TC]
34. Lechleitner A.E. et al. (2021) Processes 9:34. https://mdpi-res.com/d_attachment/processes/processes-09-00034/article_deploy/processes-09-00034.pdf [TC]
35. Pires da Mata Costa L. (2025) Tese de doutorado, COPPE/UFRJ. https://portal.peq.coppe.ufrj.br/images/doc/27%2010%202025_DSc_Laura%20Pires.pdf [TC]
36. Locaspi A. et al., Faravelli T. (2025) Proc. Combust. Inst. 41:105912. https://re.public.polimi.it/retrieve/7deb1c71-eebb-4d38-8571-d8280869b0eb/1-s2.0-S1540748925001269-main.pdf [TC]
37. van Wyk S. et al. (2026) Fuel 407:137561. https://publications.tno.nl/publication/34645275/bczo0Vyw/wyk-2026-thermal.pdf [TC]
38. Gracida-Alvarez U. et al. (2018) Ind. Eng. Chem. Res. 57:1912 (doi:10.1021/acs.iecr.7b04362). https://digitalcommons.mtu.edu/michigantech-p/7803 [R]
39. Pohl V.M. et al., Deutschmann O. (2026) React. Chem. Eng. (doi:10.1039/d5re00442j). https://publikationen.bibliothek.kit.edu/1000190723/175165593 [TC]
40. Abdy C. et al. (2023) J. Cleaner Prod. 405 (AAM). https://publications.aston.ac.uk/id/eprint/44970/1/C_Abdy_Y_Zhang_J_Wang_et_al_AAM_Investigation_of_high_density_polyethylene_pyrolyzed_wax_for_asphalt_binder_modification.pdf [TC]
41. Al-Yaari M., Dubdub I. (2021) Pyrolytic behavior of PVC, Polymers. https://pmc.ncbi.nlm.nih.gov/articles/PMC8706959/ [TC]
42. Aboulkas A., El harfi K., El Bouadili A. (2010) Energy Convers. Manage. 51:1363. https://doi.org/10.1016/j.enconman.2009.12.017 [R]
43. Stoliarov S.I., Walters R.N. (2008) Polym. Degrad. Stab. 93:422. https://doi.org/10.1016/j.polymdegradstab.2007.11.022 [S]
44. Bhatt M. et al. (2026) RSC Adv., co-pirólise de RSU em forno rotativo semi-piloto (doi:10.1039/d6ra02636b). https://pmc.ncbi.nlm.nih.gov/articles/PMC13329883/ [TC]
45. Bhatt M. et al. (2026) RSC Adv. (doi:10.1039/d5ra08655h). https://pmc.ncbi.nlm.nih.gov/articles/PMC12927709/ [TC]
46. DGEngineering (2009) Hamm MW Pyrolysis Plant. https://dgengineering.de/download/open/Hamm-2009-EN.pdf [TC]
47. Kern S. et al. (2012) J. Anal. Appl. Pyrolysis 97:1-10. https://www.best-research.eu/files/publications/pdf/1-s2.0-S0165237012000988-main.pdf [TC]
48. Kodera Y., Yamamoto T., Ishikawa E. (2021) Fuel Commun. 7:100016. https://www.sciencedirect.com/science/article/pii/S2666052021000091 [R]
49. Ma J., Zhong Q., Comparison of Chinese pyrolysis processes (Columbia/WTERT). https://wtert.org/wp-content/uploads/2019/07/Research-paper_MaZhong-May14.pdf [TC; dados de vendedor]
50. US 11319493 B2. https://patents.google.com/patent/US11319493B2/en [TC]
51. US 11,987,756 (sobreaquecimento de parede e char). https://patents.google.com/patent/US11987756 (URL montada a partir do número; texto lido) [TC]
52. Hedlund F.H. (2023) Chem. Eng. Trans. 99:241-246. https://www.cetjournal.it/cet/23/99/041.pdf [TC]
53. NFPA 69, First Draft Report, ciclo F2023, Tab. C.1(a). https://docinfofiles.nfpa.org/files/AboutTheCodes/69/69_FDR_F2023.pdf [TC]
54. FEECO, The Rotary Dryer Handbook (e páginas sobre selos). https://feeco.com/wp-content/uploads/2022/07/The-FEECO-Rotary-Dryer-Handbook.pdf [TC]
55. Metso, Rotary kiln handbook (2025). https://www.metso.com/globalassets/qbank/handbook-rotary-kiln-5455-en.pdf [TC]
56. NPTEL, Chemical Engineering Design II, Módulo 4. https://archive.nptel.ac.in/content/storage2/courses/103103027/pdf/mod4.pdf [S]
57. OSTI EGG-M--89466, PREPP rotary kiln seals. https://www.osti.gov/servlets/purl/6306168 [TC]
58. Sihai Energy Technology, planta de pirólise de pneus. https://www.sihaienergytech.com/products/waste-tire-rubber-pyrolysis-plant.html [vendedor]
59. Beston Group, tyre pyrolysis plant. https://www.bestongroup.com/tyre-pyrolysis-plant/ [vendedor]
60. Henan Doing, FAQ de energia. https://m.wastetireoil.com/Pyrolysis_faq/Pyrolysis_Plant/energy_cost_of_running_tyre_pyrolysis_plant_project_1346.html [vendedor]
61. Durdevic M., Papuga S., Kolundzija A. (2024) Hem. Ind. 78(1):29-40. https://www.ache-pub.org.rs/index.php/HemInd/article/view/1078 [TC]
62. Pichler M. et al. (2021) Data in Brief 107603. https://pmc.ncbi.nlm.nih.gov/articles/PMC8633881/ [TC]
63. Zhou Z. et al. (2025) Waste Manag. (doi:10.1016/j.wasman.2025.115093). https://pubmed.ncbi.nlm.nih.gov/40929803/ [R]
64. Wang H. et al. (2014) CIESC Journal 65(12):4716. https://hgxb.cip.com.cn/EN/10.3969/j.issn.0438-1157.2014.12.010 [R]
65. Ma H. et al. (2025) Energies 18(15):4028. https://ideas.repec.org/a/gam/jeners/v18y2025i15p4028-d1712510.html [R]
66. Shah H.H. et al. (2023) Front. Chem. 10:960894. https://pmc.ncbi.nlm.nih.gov/articles/PMC9936530/ [S]
67. Liu C., Dai S., Li A. (2026) J. Environ. Chem. Eng. 14:122678 (só o registro bibliográfico). https://doi.org/10.1016/j.jece.2026.122678 [S]
68. Maganinho C. et al. (2025) J. Environ. Chem. Eng. 13:118667. https://repositorio-aberto.up.pt/bitstream/10216/176742/2/767760.pdf [TC; dados de pneus secundários]
69. Herz F., Hochschule Anhalt, "Rotary Drums". https://www.hs-anhalt.de/en/fachbereiche/department-7/research/research-groups/thermal-process-technology/projects-and-cooperations.html [S]
70. Babler M.U. et al. (2017) Appl. Energy 207:123-133. https://ideas.repec.org/a/eee/appene/v207y2017icp123-133.html [R]
71. Marias F., página "Pyrolysis of Aluminium Waste". https://marias.perso.univ-pau.fr/alrevetu_en.html [S]
72. Mujumdar K.S., Ranade V.V. (2008) Asia-Pac. J. Chem. Eng. https://repository.ias.ac.in/64727 [R]
73. Yin et al. (2016) Powder Technol. 287. https://faculty.dlut.edu.cn/1986011026/en/lwcg/781712/content/37121.htm [R]
74. Shi D., McCarthy J.J. (2005) AIChE, artigo 209h. https://skoge.folk.ntnu.no/prost/proceedings/aiche-2005/non-topical/Non%20topical/papers/209h.pdf [R]
75. IMT Mines Albi, página de pesquisa em torrefação. https://perso.imt-mines-albi.fr/~salvador/html/research_pages/Torrefaction.html [TC]
76. ispatguru, Characteristic features of rotary kilns. https://www.ispatguru.com/characteristic-features-of-rotary-kilns/ [TC]
77. Gascoin N. et al. (2012) Polym. Degrad. Stab. (resumo no HAL). https://hal.science/hal-00705543v1 [R]
78. Kim et al. (2018) J. Ind. Eng. Chem. 66 (esferas de alumina). https://pure.uos.ac.kr/en/publications/suppressed-char-agglomeration-by-rotary-kiln-reactor-with-alumina/ [R]
79. Hornung A., Seifert H. (2006) Rotary kiln pyrolysis of polymers containing heteroatoms (Haloclean). https://www.researchgate.net/publication/230266474_Rotary_Kiln_Pyrolysis_of_Polymers_Containing_Heteroatoms [S]
80. Thermtest, Thermal conductivity of polypropylene. https://thermtest.com/application/thermal-conductivity-of-polypropylene [TC]
81. Santos W.N. dos et al. (2005) Polímeros 15(4):289-295; Yanez et al. (2013) Ing. Investig. 33(2):5-8. https://scielo.br/j/po/a/t6KjDPpvRyKZTVQ3V3V5gLn/?lang=en [S/TC]
82. Syamsiro M. et al. (2019) IOP Conf. Ser.: Earth Environ. Sci. 245:012044. URL não registrada [R]
83. SimCem `kiln.hpp` e wally `rotary_kiln.py` (cópias locais em scratchpad/topicC_dl) [código]
84. Emady H.N. et al. (2016) Chem. Eng. Sci. https://doi.org/10.1016/j.ces.2016.05.022 [S]
85. Islam M.R. et al. (2013), planta comercial de pneus em Bangladesh. URL não registrada [R]
86. Jaworski T. et al. (2023) Sensors 23:6526. https://pmc.ncbi.nlm.nih.gov/articles/PMC10386271/ [TC]
87. Qasim et al. (2025) Ind. Eng. Chem. Res. (forno elétrico de 150 kW, Chalmers). URL não registrada [TC]
88. Gamboa et al. (2023), demanda térmica da pirólise de pneus. URL não registrada [R]
89. Effect of filling degree on particle segregation in a rotating drum (Sci. Rep.). https://pmc.ncbi.nlm.nih.gov/articles/PMC13438115/ [TC]
90. Gerlach D., "Rotary kiln = rotary kiln?" (LinkedIn). https://www.linkedin.com/pulse/rotary-kiln-dirk-gerlach [S]
