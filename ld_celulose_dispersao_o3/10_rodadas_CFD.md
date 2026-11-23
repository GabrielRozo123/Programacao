# 10 — Inventário das rodadas de CFD

> Lista única de tudo o que foi rodado, com a configuração, a situação e onde estão os dados. Os valores de concentração e
> as coordenadas ficam em `_privado/rodadas_resultados.md` e `_privado/notas_interior_O3.md` (fora do git).
> Setup comum: Standard k-ε (Cμ 0,09, σε 1,225), High y⁺, modelo ABL do STAR nas entradas e no Topo, solo com rugosidade em
> duas zonas (`r_solo`), rampa de 300 it. nas vazões, média nas iterações a partir da it. 1500 (`08` §V1).

## Calibração
| rodada | o que testou | situação |
|---|---|---|
| Domínio vazio 1–4 | homogeneidade do perfil de vento (Richards & Hoxey) | ✅ aprovado na rodada 4 (16/11); `resultados/dominio_vazio_r4/` |

## Casos com os prédios (malha de 7,06 M células, salvo indicação)
| caso | vento de | velocidade a 10 m | exaustão | iterações (média) | situação | arquivo STAR |
|---|---|---|---|---|---|---|
| V1a | NNE 22,5° | 1,9 m/s (típico) | emergência (910–940 + chaminé) | 2500 (1442–2500) | ✅ | `LD_V1_oficial` |
| V1b | NNE | 1,9 m/s | normal (930/940 + chaminé) | 2500 (1500–2500) | ✅ | `LD_V1b_normal` |
| ENE | ENE 67,5° | 2,9 m/s (média do setor) | normal | 2500 | ✅ | `LD_ENE_normal` |
| ENE emergência | ENE | 2,9 m/s | emergência | 2500 | ✅ | `LD_ENE_emergencia` |
| Leste | E 90° | 1,7 m/s (média do setor) | normal | 3500 (1500–3500) | ✅ | `LD_E_normal` |
| Leste emergência | E | 1,7 m/s | emergência | 3500 | ✅ (910/920/940 pelo campo instantâneo, validado) | `LD_E_emergencia` |
| NE | NE 45° | 3,2 m/s (média do setor) | normal | 2500 | ✅ | `LD_NE_normal` |
| V2 | NNE | 13,6 m/s (rajada máxima medida) | normal | 2500 | ✅ | `LD_V2_normal` |
| V3 (rodou em emergência) | NNE | 1,1 m/s (fraco; perfil neutro) | emergência | 3500 | ✅ | `LD_V3_emergencia` |
| **V3 normal** | NNE | 1,1 m/s | normal | 3500 | ✅ (recomeçado em 23/11 depois da queda da WS3) | `LD_V3_normal_v2` |
| **Leste fraco** | E | 1,1 m/s | normal | 2500 (1500–2500) | ✅ médias estáveis em ±1 % | `LD_E_fraco_normal` |
| Malha fina | ENE | 2,9 m/s | emergência | 2500 | ✅ 16,3 M células; independência de malha (`08`) | `LD_ENE_normal_malhafina` (é emergência) |

Para cada caso concluído existem em `_privado/`: CSV dos máximos médios no Plano_z1.5 (`<caso>_medias_…csv`), grade de 2 m
dos campos médios a 1,5 m (`<caso>_grade_2m.npz`), mapas (`<caso>_chamine_ppm_1.5m.png`, `<caso>_930_diluicao_1.5m.png`,
e `<caso>_910_…` nos casos de emergência) e, quando exportada, a tabela dos 10 receptores. As tabelas XYZ completas do
plano (25–55 MB cada) ficam com o Gabriel; os mapas e áreas se refazem a partir delas com
`_privado/inventarios/analise_plano.py <tabela> <pasta> <caso>` e `mapas_V1a.py <pasta> <caso>`.

## Vídeos
| vídeo | situação |
|---|---|
| V1a, linhas de corrente (exaustores e chaminé) | ✅ `_privado/V1a_linhas_de_corrente.mp4` |
| Leste em emergência, linhas de corrente (redemoinho a barlavento) | ✅ `_privado/Leste_emergencia.mp4` (23/11) |
| Leste fraco, linhas de corrente (operação normal) | ✅ `_privado/E_fraco_linhas_de_corrente.mp4` (23/11) |

## Cortes verticais (pedido do Marcus, 23/11)
Leste fraco, planos normais a y, mesma escala (0,2 a 10 ppm, log, corte abaixo do mínimo): pela chaminé (y = 5,5), pela SDCD
(y = 14,5), pelo CCM (y = −20), vista 3D dos três e corte de velocidade com LIC pela boca da 930 (y = 14,13, 0 a 3 m/s).
Prints e versões anotadas em `_privado/cortes_verticais/`; anotação com `_privado/inventarios/slides_FUP2/anota_planos*.py`.
O ENE fica para o relatório (normal [0.3827, −0.9239, 0]; origens na chaminé, em E5 e na SDCD).

## Apresentações
| reunião | arquivo | como refazer |
|---|---|---|
| Andamento nº 2, resultados parciais (23/11, 14h) | `_privado/LD_O3_FUP2_23-11.pptx` (23 slides, 3 vídeos, cortes verticais do Leste fraco) | `_privado/inventarios/slides_FUP2/`: `mapas_slides.py` (mapas de slide, exaustores 930+940 somados), `figs_extra.py`, `build_deck.py` (modelo CAEXPERTS) |

## Pendentes
- Sensibilidade ao Sc_t (0,5 / 0,9, escoamento congelado) — para o relatório final.
- Fuga pequena pela chaminé (confirmar a conta inversa dos eventos) — sugestão, sem aval (L9).
- V3 com atmosfera estável completa — decisão do Marcus.
- Modelo interno do prédio de O₃ — aguardando o documento da LD com aberturas e tomadas dos exaustores (L13).

## Lições de operação (para não repetir)
- Conferir o `Vel_ABL` e a `ustar` em todo *Save As* antes de inicializar (Leste fraco começou com vetor constante).
- Médias: criar cada *Field Mean Monitor* pelo menu, não por cópia (a cópia cria "Mean of O3_930 2" com nome errado).
- Os monitores que fazem a média (ícone fx) começam na 1500; os "… Monitor" de report começam em 0.
- Conferir no arquivo de partida se a 910/920 estão como parede (normal) ou entrada (emergência): a malha fina e o V3
  rodaram em emergência por causa disso.
