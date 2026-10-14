# Pré-dimensionamento de ciclos de refrigeração — visi-coolers (CAExperts × IMBERA)

Rotina em Python (Google Colab) que pré-dimensiona o sistema de refrigeração de um refrigerador comercial de
bebidas a partir de **COP, capacidade (litros ou garrafas de 600 mL), temperatura ambiente e temperatura alvo**.
As saídas (compressor, condensador, evaporador, capilar, carga de fluido) são as entradas do modelo de sistema
no **Simcenter Amesim**.

## Como usar

**No Colab:** abra `PreDimensionamento_Refrigeracao_Colab.ipynb` (*Arquivo → Abrir notebook → GitHub*) e rode
*Ambiente de execução → Executar tudo*. O notebook é autocontido: grava o pacote `predimref` com `%%writefile`
e instala o CoolProp.

**Como biblioteca (integração com o Amesim):**

```python
from predimref import EntradasProjeto, dimensionar

res = dimensionar(EntradasProjeto(COP=2.0, T_ambiente_C=32, T_alvo_C=2.5, volume_interno_L=200))
print(res.resumo())                      # relatório legível
amesim = res.para_dict()["amesim"]       # parâmetros em SI por componente
res.exportar_json("resultado.json")
```

Dependências do núcleo: `numpy`, `scipy`, `CoolProp` (matplotlib só para gráficos, pandas só no notebook).

## Exemplo — 200 L, 32 °C, alvo 2,5 °C, COP 2,0, R290 (premissas padrão)

| Item | Resultado |
|---|---|
| Garrafas de 600 mL que cabem | 108 (não 333: 333 garrafas exigem ≈ 611 L) |
| Carga térmica de projeto | 218 W (743 Btu/h); governa o regime de uso diário |
| Ciclo | T_evap −7,5 °C / T_cond 45 °C, razão de pressão 4,09, η_global implícito 0,52 |
| Compressor | 109 W elétricos, 2,21 cm³ a 3500 rpm; ≈ 198 W em EN 12900 MBP |
| Condensador | 3 fileiras × 5 tubos × 0,30 m (tubo 3/8"), 4,5 m de tubo, 1,87 m² externos |
| Evaporador | 4 fileiras × 5 tubos × 0,35 m (tubo 3/8"), 7,0 m de tubo, 1,56 m² externos |
| Capilar | 0,028" (0,711 mm) × 2,17 m, não blocado |
| Carga de R290 | ≈ 109 g |
| Consumo estimado | ≈ 2,2 kWh/dia |

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
├── tests/                     56 testes (pytest)
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
| Produto | c_p de Choi & Okos (1986); pull-down e reposição diária |
| Ciclo | COP verificado contra Carnot e contra o ciclo com compressão isentrópica; η_global, η_is, calor de carcaça |
| Condensação | Shah (2022) → Shah (2013) para hidrocarbonetos (regimes I/II/III); alternativa Chato (1962) |
| Ebulição | Gungor & Winterton (1987) com estratificação e secagem; alternativa Liu & Winterton (1991) |
| Lado do ar | Wang, Chi & Chang (2000) + aleta de Schmidt (1949); ΔP de Kays & London |
| Queda de pressão | Müller-Steinhagen & Heck + aceleração (Rouhani-Axelsson), acoplada ao ciclo |
| Capilar | HEM: flash isentálpico, integração em pressão, blocagem pela linha de Fanno |
| Carga de fluido | ρ in situ com fração de vazio de Rouhani-Axelsson + linhas, carcaça e óleo |

## Verificação e validação

* Balanço de energia e de exergia fecham a 10⁻⁹; destruição de exergia ≥ 0 em todos os componentes.
* Trocadores: independência de malha (< 1 % entre 20 e 60 segmentos por zona); balanço do ar trecho a trecho.
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
| | reposição | 50 % das garrafas/dia | |
| | pull-down | carga cheia em 24 h | |
| | utilização máx. | 70 % | folga para degelo/controle |
| Ciclo | ΔT evaporador / condensador | 10 K / 13 K | prática de visi-coolers |
| | SA / SR | 5 K / 3 K | sistemas com capilar |
| | η_eletromecânica | 0,72 | motor × mecânico de herméticos pequenos |
| Compressor | rotação | 3500 rpm | 2 polos, 60 Hz (México, Colômbia) |
| Trocadores | condensador | 3/8", 3 fileiras, aleta 2,5 mm, 2 m/s | |
| | evaporador | 3/8", 4 fileiras, aleta 5 mm, 1,5 m/s | passo largo para geada |
| Capilar | série | polegadas (0,026"–0,080") | mercado latino-americano |

## Limitações conhecidas

* Pré-dimensionamento em regime permanente. Transitórios (pull-down real, ciclagem, degelo) ficam para o Amesim.
* O compressor é um modelo genérico (espaço morto + η constante). Substituir pelo mapa do compressor escolhido.
* O capilar é adiabático e sem metaestabilidade. Com trocador interno (capilar soldado à sucção), ajustar em protótipo.
* Correlações de tubo liso, sem óleo. Geada só como resistência de incrustação.
* A carga térmica depende fortemente das premissas de uso: **calibrar com ensaio de um produto IMBERA existente**
  (fuga térmica reversa, pull-down e consumo) antes de usar comercialmente.
