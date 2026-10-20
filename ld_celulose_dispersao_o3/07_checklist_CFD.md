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
| Geometria por primitivas — **40 sólidos**, escala correta (mm no STEP) | ✅ | `_privado/geometria_cfd_preliminar.step` |
| Prédio das prensas fechado (confirmado) + laje em balanço | ✅ | Otávio |
| Galpão (casinha F-C-1216) | ✅ | |
| Nota metodológica e check-up item a item | ✅ | `06` · `_privado/checkup_geometria_CFD.md` |
| Estruturas altas entre 100 e 300 m (montagem completa) | ❓ | print de planta com escala; senão → rugosidade |
| Uniões no STAR (blocos do prédio de O₃, prensas + máquinas) | ⬜ | *Boolean Unite* ou surface wrapper |

## 3. Domínio — **circular** (cilíndrico)

**Por quê:** são 6 cenários de vento em direções diferentes. Num domínio retangular, cada direção pede
girar a geometria e **refazer a malha**. Num **cilindro centrado na fonte**, a malha é **uma só**: muda-se só
o vetor de entrada e quais setores da lateral são entrada ou saída. Além de economizar tempo, **a malha é idêntica entre
cenários**, o que torna as comparações limpas (a diferença entre cenários não vem da malha).

**O que a literatura diz:**
- COST 732 / AIJ dão as distâncias em função de H para domínios **retangulares alinhados ao vento**: 5H a
  montante, 15H a jusante, 5H lateral, topo 6H, bloqueio < 3 %. Para o cilindro, a leitura é: **raio ≥ distância
  a montante exigida**, e o lado a jusante tem de acomodar a esteira e a região de interesse.
- Domínios cilíndricos (ou poligonais) são usados para estudos multidirecionais justamente para fixar a malha;
  a prática é **dividir a lateral em setores** e, para cada direção, ativar os setores de barlavento como entrada
  e os de sotavento como saída (literatura de vento urbano com domínio cilíndrico; relatos de prática em CFD
  Online — **a validar com o teste de domínio vazio**).
- Estudos de conforto de pedestres consideram ~12 direções suficientes; aqui são **6 cenários definidos pela
  meteorologia**, não uma rosa completa.

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
| Lateral, dividida em **setores** (ex.: 12 de 30° ou 16 de 22,5°) | setores de barlavento = **Velocity Inlet** com perfil de CLA; de sotavento = **Pressure Outlet**; trocar por cenário sem remalhar |
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
2. ⬜ Montar o cilindro e os setores no STAR; **teste do domínio vazio** com o perfil de CLA.
3. ⬜ Importar a geometria (40 sólidos), unir, malha base, checar qualidade.
4. ⬜ Caso base (vento típico) com os 4 escalares → convergência, malha, sensibilidades.
5. ⬜ Os 6 cenários de vento → relatórios.
