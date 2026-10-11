# Tambor rotativo de pirólise em batelada: base de projeto do modelo (v2)

Síntese da pesquisa feita para o caso do equipamento da UFRJ/IVIG, com cinco frentes:

- reator real;
- carga e cinética;
- dinâmica da batelada;
- fornalha;
- arquitetura numérica.

Os resultados brutos de cada frente, com fontes e trechos lidos, estão em `pesquisa/pesquisa_tambor_batelada.json`. Este documento substitui o brief v1 (`brief_forno_rotativo.md`, forno contínuo pequeno) no que se refere ao tambor em batelada.

Níveis de evidência:

- **[TC]** lido no texto completo;
- **[S]** fabricante ou fonte secundária;
- **[D]** derivado por cálculo;
- **[H]** hipótese de projeto.

## 1. O reator real e o caso de referência

O equipamento do vídeo é o Laboratório de Pesquisa Aplicada em Descarbonização e Pirólise de Resíduos (LDP) do IVIG/COPPE/UFRJ, na Ilha do Fundão. É um **tambor rotativo em batelada da Beston**: o IVIG diz "baseado em sistemas tipo BLJ-16", mas o tamanho no vídeo corresponde à unidade compacta **BLJ-3** [S, TC].

Medidas pelo vídeo, com o operador como escala:

- boca do tambor ≈ 1,25 m;
- porta ≈ 1,0–1,1 m;
- diâmetro interno ≈ 1,3–1,4 m.

Do vídeo:

- 500 °C;
- cerca de 70 % de óleo;
- 6 a 8 h desde a carga;
- óleo, carvão e gás, que vai para queima controlada no flare e/ou para aproveitamento energético.

| Item | Caso de referência (modelo) | Base |
|---|---|---|
| Tambor | Ø 1,40 m × 4,90 m, horizontal, aço 12 mm | Beston BLJ-3 [S]; vídeo [D] |
| Aletas | 6 retas, 0,12 m (≈ D/12); variante sem aletas | pedido do usuário; Suzuki 6 × 200 mm em 1 m [TC] |
| Rotação | 0,8 rpm (varredura 0 / 0,4 / 2 rpm), Fr ≈ 5·10⁻⁴ | Ma & Zhong 0,4–0,8 r/min [TC]; Beston BST-J 0–2 rpm [S] |
| Carga | 1 t úmida de lixo marinho misto, enchimento solto ≤ 2/3 | BLJ-3 0,5–1,2 t/dia, 1 batelada/dia [S]; Ma & Zhong [TC] |
| Fornalha | câmara sob o tambor, 2 queimadores (465 kW no total), gases sobem pelos corredores e saem no topo | Beston [S, não verificado]; Sihai 3 × 300 000 kcal/h para 2,6 × 6,6 m [S] |
| Combustível | GLP na partida; depois o gás não condensável (GNC) da própria pirólise | Beston; Pairan; Bangladesh [TC/S] |
| Controle | parede média do tambor a 500 °C, rampa de partida de 2,5 K/min, alarme do casco a 650 °C | "500 graus" (UFRJ) [H] |

## 2. Carga e cinética

A composição seca de projeto [H] é:

- PEBD 25 e PEAD 15;
- PP 20;
- PS/EPS 12;
- PET 6;
- PVC 2;
- borracha 3;
- celulósicos 8;
- inertes 9 % (areia, conchas e sal);
- umidade de 15 % (base úmida).

Essa composição fica dentro das faixas dos rejeitos de cooperativa do Rio (Cruz 2024 [TC]) e das contagens de praias da Guanabara (Baptista Neto & Fonseca 2011). Também estão prontas duas variantes: "plástico triado" e "rejeito Rio".

| Componente | Lei | E (kJ/mol) | T(k = 10⁻³ s⁻¹) | Produtos por kg reagido | Fonte |
|---|---|---|---|---|---|
| PEBD / PEAD | cisão aleatória L = 2 | 215 / 238 | 417 / 429 °C | gás 0,10, óleo 0,55, cera 0,34, carvão 0,01 | Aboulkas 2010; picos de DTG |
| PP | idem | 179 | 402 °C | gás 0,12, óleo 0,60, cera 0,26, carvão 0,02 | idem |
| PS | idem | 180 | 370 °C | aromáticos 0,65, óleo 0,25, gás 0,05, carvão 0,05 | [S/H] |
| PET | 1ª ordem | 210 | 395 °C | carvão 0,15, oxigenados 0,40, gás CO/CO₂ 0,43 | Dubdub 2023 |
| PVC | P2 (HCl) → F3 (resíduo poliênico) | 75 → 140 | 251 °C | HCl 0,583; resíduo → aromáticos, gás, carvão | pesquisa R2 |
| Celulósicos | Shafizadeh–Chin (gás / alcatrão / carvão) | 88,6 / 112,7 / 106,5 | ≈ 340 °C | carvão ≈ 0,29 a 500 °C | Navarrete 2024 [TC] |
| Borracha | 3 componentes de 1ª ordem + negro de fumo 40 % | 33 / 124 / 162 | — | óleo, aromáticos, gás | Cherbański 2017 [TC] |
| Água | platô a 100 °C | — | — | vapor (fase aquosa) | — |

**Espaço livre.** Há duas reações de craqueamento:

- cera → óleo → gás + aromáticos + coque, com k_O = 10¹⁶ exp(−300 kJ/mol/RT) e k_cera = 3 k_O;
- alcatrão → gás ou coque (Shafizadeh–Chin secundário).

**Alvos de rendimento:**

| Fonte | Óleo | Gás | Sólido |
|---|---|---|---|
| Faussone 2022 (lixo marinho, 400 °C) | 45 | 26 | 26 |
| Fulgencio-Medrano 2022, filme real a 460 °C | 61 | 14 | 25 |
| Fulgencio-Medrano 2022, filme triado | 70,6 | 12,8 | 16,6 |

O "~70 %" do IVIG só é plausível para carga seca e triada, ou contando a água como óleo.

## 3. Dinâmica da batelada (alvos de validação)

**Duração.** Em tambores de várias toneladas o processo leva 8–10 h:

- Pairan: 2,6 × 7,5 m, 10 t, 8 h 40 min de processo;
- SK Innovation: 4,5 t de plástico, 10–12 h.

Os 6–8 h da UFRJ indicam uma carga menor, de cerca de 1 t [D].

**Sequência de queima.** É sempre a mesma: combustível auxiliar por cerca de 3 h, depois o gás próprio por cerca de 5 h (Pairan, Bangladesh). O gás próprio é suficiente a partir de 220–280 °C no termômetro de vapor (Ma & Zhong).

**Termômetros dos fabricantes.** Eles medem o **vapor na saída** (100 °C primeiro óleo; 250–300 °C pico; 350 °C máx), não a carga. O modelo separa as temperaturas da carga, do casco, do vapor e dos gases de combustão.

**Suzuki et al. 2008** [TC], batelada de resíduo em forno rotativo com camisa de gases:

- coeficiente parede-carga de 22 a 55 W/m²K ao longo da batelada;
- aletas encurtam a pirólise em 7–26 %;
- acima de cerca de 2 rpm o ganho é pequeno.

**Combustível auxiliar** (Beston [S]): GLP 50–55 kg/t, diesel 55–65 kg/t, ou 2,1–2,9 GJ/t.

## 4. Fornalha

- **Gás de pirólise das poliolefinas a 500 °C:** rico em CH₄, PCI ≈ 46 MJ/kg (caso A). A mistura com celulósicos tem PCI ≈ 30 MJ/kg (caso B). Z_st ≈ 0,06–0,09.
- **Troca de calor no corredor:** a convecção é pequena (Re ≈ 2400; 2–6 W/m²K) e o casco é aquecido sobretudo por radiação.
  - A emissividade do gás (WSGG de Smith et al. 1982, p_w/p_c = 1) fica entre 0,10 e 0,18.
  - O refratário a 700–800 °C dá 18–36 kW/m² num casco a 550 °C.
  - Medido (Suzuki): 11–16,5 kW/m² com gás de aquecimento a 700–800 °C.
- **Eficiência da fornalha:** 45–65 %, com os fumos saindo a 600–750 °C [D].
- **Limite do aço:** Q345R ≤ 475 °C de serviço. A mancha quente sob a chama deve ser vigiada.

## 5. Arquitetura numérica (Colab, GPU T4)

| Bloco | Método | Papel |
|---|---|---|
| Batelada (horas) | Fatias axiais; casco por setores girando pela fornalha; carga girando bem misturada na seção com troca pelo modelo de penetração (1/h = 1/h_contato + 1/h_pen, t_c = 2ε/Ω); carga parada como pilha que só conduz (camadas lagrangianas, condução implícita); radiosidade entre setores expostos e a superfície (cordas cruzadas); secagem, fusão (colapso do volume aparente), cinética, espaço livre pistonado com craqueamento, condensador, reciclo do GNC e controle PI | Números do processo e gráfico ao vivo |
| Fornalha (zonas) | Hottel: câmara + 2 corredores + topo por fatia, gás bem misturado e nó de refratário, WSGG | Fluxo no casco a cada passo |
| Fornalha (LES 3D) | Baixo Mach, β-PDF do equilíbrio (Cantera), defeito de entalpia com radiação do gás e da fuligem; pressão resolvida só no fluido e projeção na continuidade discreta (massa fechada por construção) | Chamas, campo de T e distribuição do calor no casco |
| Carga (segundos) | DEM em GPU: esferas macias, mola tangencial com histórico, resistência ao rolamento, aletas e casco como superfícies analíticas girando | Movimento real e grandezas do modelo térmico: ângulo, arco coberto, tempo de contato, cortinas, mistura |

Separação de escalas (pesquisa R5):

- contato ~ms;
- chama ~s;
- volta do tambor 75 s;
- vapor 1–4 min;
- casco 3–10 min;
- batelada 6–8 h.

Uma CFD-DEM acoplada da batelada inteira é inviável: são 6–60 h só de DEM, e o Star-CCM+ leva 21–46 h por 15 s em 64 núcleos (Belcher 2026). Por isso cada bloco roda no seu relógio e entra nos outros como mapa quase estacionário.

## 6. Referências principais

- IVIG/COPPE/UFRJ, páginas "Pirólise" e "LDP" (2025–2026). Beston: BLJ-3, FAQ e página do reator.
- Ma J., Zhong Q. (2018/2019) *Comparison of Chinese Pyrolysis Processes*, WTERT/Columbia.
- Suzuki T. et al. (2008) J. Therm. Sci. Technol. 3:523 e 3:532.
- Faussone G.C., Cecchi T. (2022) Sustainability 14:1235.
- Fulgencio-Medrano L. et al. (2022) Polymers 14:553.
- Cruz D.S. (2024) Dissertação PPGPDS/UFRRJ.
- Navarrete Cereijo G. et al. (2024) Energies 17:4982.
- Cherbański R. et al. (2017) Chem. Process Eng. 38:363.
- Aboulkas A. et al. (2010) Energy Convers. Manag. 51:1363.
- Calero M. et al. (2023) Chem. Eng. Sci. 271:118569.
- Smith T.F., Shen Z.F., Friedman J.N. (1982) J. Heat Transfer 104:602.
- CPCB (2021) relatório ao NGT (Pairan Pyrolysis).
- Jo S. et al. (2025) US 12,296,504 B2 (SK Innovation).
- Tscheng S.H., Watkinson A.P. (1979) Can. J. Chem. Eng. 57:433.
- Schlünder E.U., Mollekopf N. (1984) Chem. Eng. Process. 18:93.
- Cundall P.A., Strack O.D.L. (1979) Géotechnique 29:47.
- Ai J. et al. (2011) Powder Technol. 206:269.
- Henein H. et al. (1983) Metall. Trans. B 14:191.
- Belcher E.C. (2026) Lund MSc thesis (CFD-DEM em Star-CCM+).
