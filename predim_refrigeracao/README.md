# Pré-dimensionamento de ciclos de refrigeração — visi-coolers (CAExperts × IMBERA)

Rotina em Python (Google Colab) que pré-dimensiona o sistema de refrigeração de um refrigerador comercial de
bebidas a partir de **COP, capacidade (litros ou garrafas de 600 mL), temperatura ambiente e temperatura alvo**,
com a **eficácia dos trocadores** como entrada ajustável (padrão 0,65). As saídas (compressor, condensador,
evaporador, capilar, carga de fluido) são as entradas do modelo de sistema no **Simcenter Amesim**.

A rotina é o *step-down* do modelo do Amesim: gera, em regime permanente, parâmetros físicos e coerentes entre si
para montar o modelo. As curvas de pull-down, consumo, fuga térmica e água drenada saem do próprio Amesim.

## Como usar

**No Colab:** abra `PreDimensionamento_Refrigeracao_Colab.ipynb` (*Arquivo → Abrir notebook → GitHub*) e rode
*Ambiente de execução → Executar tudo*. O notebook é autocontido: grava o pacote `predimref` com `%%writefile`
e instala o CoolProp.

**Como biblioteca (integração com o Amesim):**

```python
from predimref import EntradasProjeto, dimensionar

res = dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32, T_alvo_C=2.5, volume_interno_L=200,
                                  eficacia_condensador=0.65, eficacia_evaporador=0.65))
print(res.resumo())                      # relatório legível
amesim = res.para_dict()["amesim"]       # parâmetros em SI por componente
res.exportar_json("resultado.json")
```

Dependências do núcleo: `numpy`, `scipy`, `CoolProp` (matplotlib só para gráficos, pandas só no notebook).

## Exemplo — 200 L, 32 °C, alvo 2,5 °C, COP 2,0, R290, ε = 0,65 nos dois trocadores (premissas padrão)

| Item | Resultado |
|---|---|
| Garrafas de 600 mL que cabem | 108 (não 333: 333 garrafas exigem ≈ 611 L) |
| Carga térmica de projeto | 218 W (745 Btu/h); governa o regime de uso diário; UR interna de equilíbrio 57 % |
| Ciclo | T_evap −7,5 °C / T_cond 45 °C, razão de pressão 4,09, η_global implícito 0,52 |
| Compressor | 109 W elétricos, 2,22 cm³ a 3500 rpm; ≈ 198 W em EN 12900 MBP |
| Condensador (ε = 0,65) | 6 fileiras a 1,28 m/s; 5,58 m de tubo 3/8" no projeto; construtiva (+10 %) 6 × 4 tubos × 0,256 m = 6,14 m; 109 m³/h de ar no projeto |
| Evaporador (ε = 0,65) | 6 fileiras a 0,50 m/s; 11,6 m de tubo 3/8" no projeto; construtiva 6 × 7 tubos × 0,305 m = 12,79 m; 89 m³/h; ar insuflado −4 °C |
| Capilar | 0,028" (0,711 mm) × 2,16 m, não blocado |
| Carga de R290 | ≈ 145 g (135 g com as serpentinas de projeto) |
| Consumo estimado | ≈ 2,2 kWh/dia |

### Eficácia dos trocadores

ε é a do lado do ar referida à saturação (definição usual para condensadores e evaporadores, refrigerante
bifásico com C → ∞): ε = (T_ar,saída − T_ar,entrada)/(T_sat − T_ar,entrada). Com a carga e o ΔT de aproximação
fixados pelo ciclo, ε define a vazão de ar (Ċ_ar = Q_sens/(ε ΔT)) e, com ela, o NTU que a geometria precisa ter
(na zona bifásica ε_zona ≤ 1 − e^(−NTU_zona); no condensador a ε global inclui o ar aquecido no dessuperaquecimento e
não segue essa relação — UA, NTU e ε por zona também são exportados). A rotina resolve a velocidade de face, escolhe o
nº de fileiras (≤ 6) e calcula o comprimento de tubo. ε não muda o ciclo: troca ventilador por trocador. Efeito no
exemplo acima (vazões e comprimentos da serpentina de projeto):

| ε | Condensador (fileiras × V, tubo, ar) | Evaporador (fileiras × V, tubo, ar, ar insuflado) | Carga R290 |
|---|---|---|---|
| 0,45 | 5 × 2,07 m/s, 4,1 m, 157 m³/h | 6 × 1,23 m/s, 6,9 m, 129 m³/h, −2,0 °C | 111 g |
| 0,55 | 6 × 1,80 m/s, 4,7 m, 128 m³/h | 6 × 0,79 m/s, 8,8 m, 106 m³/h, −3,0 °C | 124 g |
| 0,65 | 6 × 1,28 m/s, 5,6 m, 109 m³/h | 6 × 0,50 m/s, 11,6 m, 89 m³/h, −4,0 °C | 145 g |
| 0,75 | 6 × 0,89 m/s, 6,9 m, 94 m³/h | 6 × 0,31 m/s, 16,6 m, 78 m³/h, −5,0 °C | 179 g |

Com tubo 3/8" e um circuito, o fluxo mássico de refrigerante é baixo (G ≈ 14 kg/m²s) e o lado interno limita o NTU
por fileira; por isso ε alto pede serpentinas fundas e face lenta. `alternativas_fileiras(res, "condensador")`
mostra todas as opções (fileiras × velocidade × comprimento × ventilador). A eficácia estrita Q/Q_max
(Q_max termodinâmico) também é exportada, caso o componente do Amesim use essa definição.

**Duas serpentinas por trocador.** A *de projeto* (sem margem), com a vazão de ar requerida, entrega exatamente a
capacidade e as temperaturas do ciclo: é a que reproduz `amesim.alvo_validacao`. A *construtiva* tem a margem de área
(10 %), o mesmo nº de fileiras e de tubos por fileira e o comprimento do passe ajustado; na mesma velocidade de face tem
a mesma ε com 10 % mais vazão e UA, e num modelo de sistema condensa abaixo de T_cond e evapora acima de T_evap
(é a folga). O bloco `amesim` traz as duas, além da umidade do ar de entrada, do UA úmido e seco do evaporador, das
linhas, do óleo e da carga separada em circuito, gás na carcaça e refrigerante dissolvido no óleo.

## Estrutura

```
predim_refrigeracao/
├── PreDimensionamento_Refrigeracao_Colab.ipynb   notebook (gerado por ferramentas/gerar_notebook.py)
├── predimref/
│   ├── propriedades.py        CoolProp (HEOS) + psicrometria
│   ├── correlacoes/           monofásico, bifásico, lado do ar
│   ├── gabinete.py            litros↔garrafas e carga térmica
│   ├── ciclo.py               estados, COP × Carnot, rendimentos, exergia
│   ├── compressor.py          deslocamento, η_v, ponto de catálogo
│   ├── trocador.py            condensador/evaporador por zonas e segmentos
│   ├── capilar.py             modelo homogêneo com blocagem
│   ├── carga_fluido.py        massa de refrigerante e limites para HC
│   ├── projeto.py             orquestração (ciclo ↔ trocadores ↔ capilar)
│   ├── relatorio.py           resumo, JSON, bloco "amesim"
│   └── graficos.py            P-h, T-s, perfis, mapa de COP
├── tests/                     testes automatizados (pytest)
├── validacao/                 capilar × Li et al. (1990)
└── ferramentas/gerar_notebook.py
```

Depois de alterar qualquer módulo: `python ferramentas/gerar_notebook.py` (regera o notebook) e `python -m pytest`.

## Métodos (detalhes e equações no notebook, seção 2)

| Etapa | Método |
|---|---|
| Propriedades | Equações de estado de referência via CoolProp/HEOS; ar úmido ASHRAE RP-1485 |
| Transmissão | Resistências em série + fatores de forma de arestas/cantos (Incropera, Tab. 4.1) + pontes térmicas |
| Infiltração | Gosney & Olama (1975)/ASHRAE, limitada ao volume de ar livre do gabinete |
| Umidade interna | balanço água da infiltração = água removida pela serpentina (superfície efetiva, Lewis = 1; Braun, Klein & Mitchell 1989) |
| Produto | c_p de Choi & Okos (1986); pull-down e reposição diária |
| Ciclo | COP verificado contra Carnot e contra o ciclo com compressão isentrópica; η_global, η_is, calor de carcaça |
| Condensação | Shah (2022) → Shah (2013) para hidrocarbonetos (regimes I/II/III); alternativa Chato (1962) |
| Ebulição | Gungor & Winterton (1987) com estratificação e secagem; alternativa Liu & Winterton (1991) |
| Lado do ar | Wang, Chi & Chang (2000) + aleta de Schmidt (1949); ΔP de Kays & London |
| Queda de pressão | Müller-Steinhagen & Heck + aceleração (Rouhani-Axelsson), acoplada ao ciclo |
| Capilar | HEM: flash isentálpico, integração em pressão, blocagem pela linha de Fanno |
| Carga de fluido | ρ in situ com fração de vazio de Rouhani-Axelsson + linhas, carcaça e óleo |

## Verificação e validação

* Balanço de energia e de exergia fecham a ~10⁻⁸ (arredondamento do CoolProp); destruição de exergia ≥ 0 em todos os
  componentes.
* Trocadores: malha — com o padrão de 40 segmentos na zona bifásica o comprimento fica a ≤ 0,15 % do obtido com 240,
  inclusive no modo de eficácia (em que V se reajusta); as zonas monofásicas convergem com 5 (padrão 8); balanço do ar
  trecho a trecho; eficácia alvo atingida a 10⁻³; ε ≤ 1 − e^(−NTU) (desigualdade de Jensen) no evaporador só bifásico;
  pinch por perda de carga e alvo de ε inatingível (acima ou abaixo) rejeitados com mensagem própria (com aumento
  automático de circuitos quando a causa é a perda de carga); Q = ε Ċ_ar ΔT na serpentina de projeto exportada.
* Umidade: no equilíbrio, a água removida pela serpentina (superfície efetiva, Lewis = 1) iguala a da infiltração e
  o ξ de projeto é o latente dessa remoção (teste `test_balanco_umidade_lewis`).
* Eficiência de aleta de Schmidt dentro de 3 % da solução exata (Bessel) da aleta anular.
* Capilar contra Li et al. (1990), R12, D = 0,66 mm, L = 1,5 m (`python validacao/validacao_capilar_li1990.py`):

| Caso | Vazão medida | HEM McAdams | HEM Cicchitti | HEM Dukler |
|---|---|---|---|---|
| T_in 31,4 °C, P_in 9,67 bar | 1,130 g/s | −2,9 % | −4,3 % | −2,2 % |
| T_in 23,4 °C, P_in 7,17 bar | 0,844 g/s | −1,2 % | −3,5 % | +0,1 % |

* Correlação de Wang (2000): com o termo 0,158 ln[N(Fp/Dc)^0,41] em P3 (omitido em algumas transcrições), j fica
  contínuo de N=1 para N=2 e quase independente de N em Re alto, como nos dados; sem ele, j cairia 4–5× de 1 para
  6 fileiras (teste `test_wang_j_fisicamente_coerente`).

## Premissas padrão (todas editáveis)

| Grupo | Premissa | Valor | Justificativa |
|---|---|---|---|
| Garrafa | envelope | 65 × 239 mm | garrafa genérica de 600 mL — **medir a garrafa do cliente** |
| Gabinete | fator de ocupação | 0,55 | prateleiras, folgas, caixa do evaporador |
| | espuma PU | k = 0,022 W/m·K, 50–60 mm | PU com ciclopentano |
| | porta de vidro | U = 2,0 W/m²K | vidro duplo low-e com moldura |
| | gaxeta | ψ = 0,10 W/m·K | literatura 0,05–0,2; calibrar |
| Uso | aberturas | 100/dia × 8 s | loja de conveniência típica |
| | UR interna | equilíbrio (calculada) | `umidade_interna="fixa"` usa `UR_interna` |
| | reposição | 50 % das garrafas/dia | |
| | pull-down | carga cheia em 24 h | |
| | utilização máx. | 70 % | folga para degelo/controle |
| Trocadores | eficácia ε (cond. e evap.) | 0,65 | definida pela equipe (ajustável pelo usuário) |
| Ciclo | ΔT evaporador / condensador | 10 K / 13 K | prática de visi-coolers |
| | SA / SR | 5 K / 3 K | sistemas com capilar |
| | η_eletromecânica | 0,72 | motor × mecânico de herméticos pequenos |
| Compressor | rotação | 3500 rpm | 2 polos, 60 Hz (México, Colômbia) |
| Trocadores | condensador | 3/8", aleta 2,5 mm, V preferida 2 m/s | fileiras e V resolvidas para ε |
| | evaporador | 3/8", aleta 4,23 mm (6 FPI), V preferida 1,5 m/s | passo largo para geada |
| Capilar | série | polegadas (0,026"–0,080") | mercado latino-americano |

## Limitações conhecidas

* Pré-dimensionamento em regime permanente. Transitórios (pull-down real, ciclagem, degelo) ficam para o Amesim.
* O compressor é um modelo genérico (espaço morto + η constante). Substituir pelo mapa do compressor escolhido.
* O capilar é adiabático e sem metaestabilidade. Com trocador interno (capilar soldado à sucção), ajustar em protótipo.
* Correlações de tubo liso, sem óleo. Geada só como resistência de incrustação.
* A carga térmica depende fortemente das premissas de uso. A conferência é feita contra o modelo do Amesim: com as
  serpentinas `projeto_sem_margem` e a vazão requerida ele deve reproduzir `amesim.alvo_validacao` (Q_evap, W_el, ṁ,
  T_evap, T_cond); com as `construtiva_com_margem`, T_cond menor e T_evap maior são esperados (folga de área).
