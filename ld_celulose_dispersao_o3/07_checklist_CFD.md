# 07 — Checklist do CFD: o que temos e o que falta (geometria → domínio → malha → física → relatórios)

> 20/10/2026. Documento de controle da execução. Física e malha seguem `02_metodo_e_analise_previa.md` (§1, §7, §9),
> o escalar passivo segue `star_ccm_tutoriais/00_Passive_Scalar.md`. Sem coordenadas (ver `_privado/`).

Legenda: ✅ feito · 🟡 em andamento / parcial · ⬜ a fazer · ❓ depende de terceiros

---

## 1. Dados de entrada
| item | status | observação |
|---|---|---|
| Escopo, limiares (3 · 0,5 · 0,2 · 0,08 ppm), cronograma | ✅ | `01` |
| Régua gaussiana (alcances, efeito da estabilidade e da altura) | ✅ | `02` §2–5 |
| Análise meteorológica Zeus + 6 cenários de vento | ✅ | planilha + `cenarios_meteo.py` |
| Ventiladores: vazões, velocidades de descarga | ✅ | `04` §1 |
| **Direção e área das descargas** (lidas do CAD, conferidas com manuais) | ✅ | `04` (20/10) |
| Vazões de O₃ no vazamento (Q_peq, Q_gr) — **bloqueia os cenários de fonte** | ❓ | L1 · cliente |
| Quais exaustores operam em cada cenário (contínuos × emergência) | ❓ | L2 · cliente via Marcus |
| 0° da estação = norte verdadeiro? norte da planta? altura do anemômetro | ❓ | L3 · cliente |
| Aval dos cenários 5–6 (vento fraco estável) | ❓ | L6 · Marcus |
| Rugosidade do entorno (z₀ a montante, por setor) | ⬜ | definir com imagem aérea (Davenport–Wieringa) |

## 2. Geometria
| item | status | observação |
|---|---|---|
| Critérios de limpeza com base na literatura | ✅ | `05` |
| Inventários com nomes de todos os subconjuntos relevantes | ✅ | F-C/F-M/F-E 1213–1219, RC/RF-1210, F-C-1216 |
| Geometria por primitivas — **69 sólidos** (inclui 22 pilares e 2 vigas das prensas), escala correta (mm) | ✅ | `_privado/geometria_cfd_preliminar.step` |
| **Domínio prisma de 16 lados** R 600 m × 350 m, **16 setores** nomeados + refinos R 80/300 m | ✅ | `geometria/gen_dominio_cilindrico.py --stl` → `_privado/` (STL em metros) |
| **Volume de ar em STL único** (domínio − 69 sólidos, 87 superfícies nomeadas, estanque) | ✅ | `geometria/gen_volume_fluido.py` → `_privado/volume_ar_LD.stl`; fluxo no STAR: `08` |
| Frestas corrigidas: tanque 1213-21-004 × laje (5 cm → 0,8 m), placa de descarga 910 × exaustor (2 mm → 0) | ✅ | 21/10 |
| Prédio das prensas = **mesa de concreto aberta embaixo** (laje ~11 m); variante fechada para sensibilidade | ✅ | revisão com o Otávio (21/10) |
| Varredura de equipamentos esquecidos (tanque 1213-21-003 e outros 5) | ✅ | 21/10 |
| Galpão (casinha F-C-1216) | ✅ | |
| Nota metodológica e check-up item a item | ✅ | `06` · `_privado/checkup_geometria_CFD.md` |
| Estruturas altas entre 100 e 300 m (montagem completa) | ❓ | print de planta com escala; senão → rugosidade |
| Uniões (blocos do prédio de O₃, prensas + máquinas) | ✅ | feitas no script (fusão antes da subtração) |

## 3. Domínio — **prisma de 16 lados** (cilindro "poligonal")

**Por quê:** os 6 cenários iniciais (3 campos de vento) estão na direção dominante (NNE), mas outras direções podem ser
pedidas (norte da estação a confirmar, B5; segunda direção mais frequente). Num domínio retangular, cada direção pede
girar a geometria e **refazer a malha**. Num **cilindro centrado na fonte**, a malha é **uma só**: muda-se só
o vetor de entrada e quais setores da lateral são entrada ou saída. Além de economizar tempo, **a malha é idêntica entre
cenários**, o que torna as comparações limpas (a diferença entre cenários não vem da malha).

### 3.1 Por que polígono, e não cilindro liso nem esfera (21/10)

**"10°" não é o tamanho do setor.** É o limiar do *Split by Angle* do STAR (ângulo entre faces vizinhas acima
do qual a superfície é separada). Dois lados vizinhos de um 16-gono se encontram a **22,5°**, e lateral × solo/topo a
**90°**; qualquer limiar entre 0 e 22,5° separa os 16 lados + solo + topo. Os **setores têm 22,5°** — a rosa
dos ventos meteorológica de 16 rumos (N, NNE, NE…). No STL entregue os 18 contornos já vêm nomeados (S01–S16, Solo, Topo).

**Polígono × cilindro liso**
| | cilindro liso | prisma de 16 lados |
|---|---|---|
| Separar a lateral em setores | a superfície não tem arestas — o *Split by Angle* não acha onde cortar (aconteceu: os arcos se fundiram numa face só) | arestas de 22,5° → separa sozinho |
| Entrada ou saída por cenário | normal varia ponto a ponto dentro do setor | **uma normal por lado** → classifica pelo sinal de **u·n**, sem ambiguidade dentro do lado |
| Tamanho | R 600 m | raio inscrito 588,5 m (−1,9 %) — desprezível frente aos critérios do COST |
| Malha | — | a mesma; o trimmer corta as células na borda nos dois casos |

**Por que não esfera (nem cúpula)**
- A esfera é o domínio de "campo distante" da aerodinâmica externa (avião, carro em túnel virtual): **corrente livre
  uniforme e nenhuma parede**. A camada limite atmosférica é o oposto: tem **solo** (parede rugosa, ks) e um
  **perfil vertical** U(z), k(z), ε(z).
- A CLA horizontalmente homogênea (Richards & Hoxey, 1993) exige **solo plano**, perfil imposto em **faces
  verticais** e um **topo horizontal** com tensão de cisalhamento prescrita ou velocidade do perfil (Richards &
  Hoxey, 1993; Hargreaves & Wright, 2007; Blocken et al., 2007). Numa esfera/cúpula a parede curva mistura
  "lateral" e "topo": não há onde impor o perfil de forma consistente e a homogeneidade (teste do domínio vazio) não se sustenta.
- Na cúpula a altura fica presa ao raio (600 m em vez dos ~350 m = 6H necessários) → células gastas onde não há nada.
- As diretrizes de vento em torno de prédios (COST 732 — Franke et al., 2007; AIJ — Tominaga et al., 2008) são
  escritas para domínios de **solo plano, laterais verticais e topo plano**; o cilindro/polígono setorizado é a
  extensão multidirecional disso. Não encontramos diretriz de CFD atmosférico que use esfera.

**Prática com domínio cilíndrico/setorizado (fontes de prática, menos fortes que as diretrizes):**
- domínio cilíndrico evita remalhar para cada direção, o retangular precisaria ser realinhado
  ([Rakenteiden Mekaniikka](https://rakenteidenmekaniikka.journal.fi/article/download/119848/76572/266557));
- lateral em setores (ex.: 12 × 30°) com entrada/saída escolhida por direção na mesma malha
  ([AMS, conferência](https://ams.confex.com/ams/pdfpapers/126911.pdf));
- geometria centrada para permitir qualquer direção, com o alerta de que a troca entrada/saída nas bordas
  tangentes pode dar instabilidade ([arXiv 2505.14703](https://arxiv.org/pdf/2505.14703), preprint) → por isso o
  teste do domínio vazio e a checagem das bordas tangentes (§6);
- ~12 direções costumam bastar em conforto de pedestres (Hågbo & Giljarhus,
  [Frontiers 2022](https://doi.org/10.3389/fbuil.2022.858067)); aqui 16 setores ≥ 12, e os 6 cenários vêm da meteorologia.

**Detalhe prático:** o domínio entra no STAR como **STL em metros** (não STEP/Parasolid), porque o Parasolid só aceita
corpos dentro de uma caixa de 1 km (±500 m) e o domínio tem 1,2 km de diâmetro.

**O que a literatura diz:**
- COST 732 / AIJ dão as distâncias em função de H para domínios **retangulares alinhados ao vento**: 5H a
  montante, 15H a jusante, 5H lateral, topo 6H, bloqueio < 3 %. Para o cilindro, a leitura é: **raio ≥ distância
  a montante exigida**, e o lado a jusante tem de acomodar a esteira e a região de interesse.
- Domínios cilíndricos (ou poligonais) são usados para estudos multidirecionais justamente para fixar a malha;
  a prática é **dividir a lateral em setores** e, para cada direção, ativar os setores de barlavento como entrada
  e os de sotavento como saída (literatura de vento urbano com domínio cilíndrico; relatos de prática em CFD
  Online — **a validar com o teste de domínio vazio**).
- Estudos de conforto de pedestres consideram ~12 direções suficientes; aqui são **6 cenários (3 campos de vento)
  definidos pela meteorologia**, não uma rosa completa.

**Dimensionamento proposto** [a fechar com o Marcus — H do entorno ≈ 58 m]:
| item | regra | valor |
|---|---|---|
| Raio | região de interesse (~300 m) + margem a montante ≥ 5H (~290 m) | **~600 m** |
| Altura | 6H | **~350 m** |
| Bloqueio | área frontal máx. ~10 500 m² / (2R · altura) | **~2,5 %** ✔ (< 3 %) |
| Jusante | 15H (~870 m) **não** cabe → aceitar ~600 m e **testar** domínio maior em 1 cenário | sensibilidade |

**Contornos:**
| superfície | condição |
|---|---|
| Lateral, dividida em **16 setores de 22,5°** (S01 = 0°, sentido horário) | setores de barlavento = **Velocity Inlet** com perfil de CLA; de sotavento = **Pressure Outlet**; trocar por cenário sem remalhar |
| Topo | velocidade e turbulência do perfil no topo, ou **tensão de cisalhamento prescrita** (Richards & Hoxey) — escolher pelo teste do domínio vazio |
| Solo | parede rugosa com *Roughness Height* ks (≈ 30·z₀ ou 9,793·z₀/Cs), 1ª célula > ks |
| Prédios e equipamentos | parede lisa (no-slip) |
| Descargas dos exaustores | **Mass Flow Inlet** (vazão do manual), com escalar passivo = 1 |

> ⚠️ Nos setores **tangentes** ao vento (laterais), a escolha entre entrada e saída é sensível. Prática: dividir em
> setores pequenos e classificar pelo sinal de **u·n**. Verificar no domínio vazio que não aparece recirculação
> espúria nessas bordas.

## 4. Malha
| item | proposta |
|---|---|
| Tipo | **trimmed** (hexaédrica) + **prismas** no solo e nas paredes (tutorial STAR 05/06) |
| Descargas dos exaustores | ≥ 8–10 células na largura (0,36–0,52 m → **~0,05 m**) |
| Zona Z0 (prédio, terraço, torres) | **~0,5 m**; ≥ 10 células nas frestas (COST) — frestas de 3–5 m entre torres e prédio pedem ~0,3 m |
| Cobertura do terraço (jato que bate a 2,4 m) | ~0,1–0,2 m na região entre descarga e cobertura |
| Caminho da pluma (refino volumétrico a jusante, por cenário ou anel) | ~1 m até 300 m |
| Longe | 4–8 m; taxa de crescimento ≤ 1,2–1,3 |
| Solo | 1ª célula > ks; y⁺ na faixa das funções de parede (30–500) |
| Independência de malha | 3 malhas (fator ~1,5) num cenário; GCI nos receptores |

## 5. Física no STAR-CCM+
| item | escolha | fonte |
|---|---|---|
| Regime | **Steady RANS** (exaustores contínuos); transiente só se houver PSV (sopro) | `02` §7 |
| Escoamento | Segregated Flow, **densidade constante** (ar ~1,18 kg/m³) | atmosférico, baixo Mach |
| Turbulência | **k-ε Realizable** (COST/AIJ); conferir homogeneidade — alternativa **k-ε padrão com constantes de Richards & Hoxey** | `02` §7, §9 |
| Perfil de entrada | Richards & Hoxey: U(z) = u*/κ·ln((z+z₀)/z₀); k = u*²/√Cμ; ε = u*³/(κ(z+z₀)) — por Field Function com o ângulo do cenário | `02` §9.2 |
| Rugosidade | z₀ do perfil (terreno a montante) ≠ ks do solo do domínio | `02` §9.3 |
| **Escalar passivo** (O₃) | Passive Scalar, **clip abaixo de 0**, Sc_t = **0,7** (sensibilidade 0,5–0,9), **fonte normalizada = 1** em cada descarga → superposição linear para qualquer vazão | `00_Passive_Scalar` |
| Conversão | ppm = φ · C_desc · (M_ar/M_O₃) · 10⁶, com C_desc = vazão de O₃ ÷ vazão do exaustor | `00`, `04` §1.3 |
| Um escalar por exaustor | 4 escalares (910, 920, 930, 940) num único campo de vento → combina-se depois conforme o cenário (quais ligam) | superposição |
| Decaimento químico | desprezado (conservador) | `02` §7 |
| **Estabilidade (cenários 5–6, classe F)** | ⚠️ em aberto: perfis de Monin-Obukhov + empuxo (Boussinesq, gravidade, temperatura) **ou** neutro com vento fraco declarado como limitação | decidir com o Marcus (L6) |

## 6. Verificação antes dos cenários
| teste | critério |
|---|---|
| **Domínio vazio** (sem prédios) | perfis U, k na saída = entrada (homogeneidade horizontal) — calibra ks e o topo |
| Setores de entrada/saída do cilindro | sem recirculação espúria nas bordas tangentes |
| Balanço de massa e de escalar | Σ escalar que sai = Σ que entra pelas descargas |
| Malha | 3 níveis, GCI |
| Domínio | 1 cenário com domínio maior (jusante) |
| Geometria | 1 cenário com Z1 mais detalhada (Ricci 2017) |
| Sc_t | 0,5 / 0,7 / 0,9 num cenário |

## 7. Relatórios e pós
| item | como |
|---|---|
| Contornos de concentração a **1,5 m** (altura de respiração) | plano z = 1,5 m, escala fixa, linhas de 3 · 0,5 · 0,2 · 0,08 ppm |
| Isossuperfícies 3D dos limiares | por cenário |
| Pontos receptores (sondas) | áreas ocupadas, tomadas de ar de HVAC, sensores existentes (L-pendências 10–11 do `03`) |
| Linhas de corrente a partir das descargas | mostram captura pela esteira (downwash) |
| Tabela de alcance de cada limiar × cenário | comparação com a régua gaussiana |
| Recomendação de **posição de sensores** | onde a pluma chega primeiro / com maior concentração |
| Monitores de convergência | resíduos + escalar em 5–10 sondas + balanço de escalar |

## 8. Próximos passos (ordem)
1. ❓ Respostas: Marcus (domínio, estabilidade, operação dos exaustores) e cliente (vazões de O₃, norte).
2. 🟡 STAR do zero com `volume_ar_LD.stl` (`08`): importar → região "Ar" → contornos → malha (sem wrapper).
3. ⬜ **Teste do domínio vazio** com o perfil de CLA; malha base, checar qualidade.
4. ⬜ Caso base (vento típico) com os 4 escalares → convergência, malha, sensibilidades.
5. ⬜ Os 6 cenários de vento → relatórios.
