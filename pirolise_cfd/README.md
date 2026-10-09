# Reator de pirólise de plástico em 3D

Simulação de um **reator agitado contínuo de pirólise** no Google Colab: o plástico pós-consumo
(poliolefinas HDPE, LDPE e PP) entra derretido, vindo de uma extrusora, e é craqueado a ~400 °C em
vapores de óleo e cera. O notebook resolve, em GPU, o escoamento turbulento do fundido em torno de uma
fita helicoidal dupla, a temperatura e a química do polímero, valida o modelo contra a literatura e
termina num vídeo HD com o resultado logo nos primeiros segundos.

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GabrielRozo123/Programacao/blob/claude/nifty-franklin-fkhhua/pirolise_cfd/pirolise_reator_colab.ipynb)

Tudo vem de **literatura aberta** (composição de resíduos, reologia, cinética, correlações de mistura e de
troca térmica); não há dados de projeto, de clientes ou de empresas.

## O caso padrão

| | |
|---|---|
| Vaso | 0,8 m de diâmetro, líquido até 0,8 m (0,40 m³), sem chicanas, camisa aquecida |
| Agitador | dupla fita helicoidal, D/T = 0,90 (folga de 40 mm), passo = D, 30 rpm (opção: âncora) |
| Carga (F3) | HDPE 60 / LDPE 5 / PP 35 % (resíduo de São Carlos, Matos 2006, renormalizado), 1 % de cinzas, entra a 300 °C |
| Operação | parede a 480 °C (modo B: a vazão é resultado, com controle de nível) ou vazão imposta (modo A) |

Resultado de referência do reator ideal 0-D (h de Nagata ≈ 290 W/m²K): fundido a ~405 °C, ~160 kg/h,
~55 kW pela camisa, residência ~1,5 h, viscosidade do seio ~4 mPa s (Re ≈ 4·10⁴, turbulento).

## Modelo

* **Escoamento** (`flow.py`): Navier–Stokes incompressível no referencial que gira com a fita (o problema
  fica estacionário num vaso sem chicanas); malha MAC uniforme, advecção conservativa upwind de 3ª ordem,
  RK2 com projeção (Poisson direto por diagonalização), fronteiras imersas por forçamento direto.
* **Turbulência** (`turbulence.py`): k-ω SST (Menter 2003) com correção de rotação/curvatura
  (Smirnov–Menter), lei de Spalding e função térmica de Kader. Na parede curva do vaso, uma camada de
  deslizamento co-rotativa com o líquido junto à parede e a tensão ρu_τ² aplicada na área real: numa malha
  cartesiana, a parede em escada que gira no referencial da fita empurraria o fluido como dentes de
  engrenagem, e esse torque espúrio não cai com o refinamento.
* **Reologia** (`rheology.py`): Cross com deslocamento térmico, η₀ ∝ Mw^3,6 acima de Mc (Raju) e ramo de
  ceras (POLYWAX) abaixo; mistura logarítmica entre polímeros.
* **Cinética** (`kinetics.py`): cisão aleatória (L = 2) com E de Aboulkas et al. (2010) e A calibrado aos
  picos de DTG a 10 K/min; Kissinger e Westerhout como verificação.
* **Química no reator** (`chemistry.py`, `reactor.py`): por polímero, massa Y, número de cadeias Z e três
  classes de comprimento (fechamento do balanço populacional); vapor quando as cadeias ficam mais curtas que
  o corte de ebulição (Riazi); calor de pirólise por DSC; temperatura e espécies em regime permanente sobre o
  escoamento médio (transporte conservativo, continuação pseudo-transiente + BiCGSTAB em GPU), controle de
  nível e balanços de massa e energia fechados.
* **Reator ideal 0-D**: o mesmo modelo químico num tanque perfeitamente misturado; dá a curva de capacidade
  e a referência para o CFD.

## Validação (`validation.py`)

| Nível | Verificações |
|---|---|
| L1 componentes | Couette newtoniano e de lei de potência (testes); Kp laminar da fita (269 ± 20 %, abaixo do limite de Couette 653); h × Nagata (± 30 %); balanços de massa e energia |
| L2 química | picos de DTG (consenso e Westerhout 1997); PET a 2 K/min; Kissinger; deslocamento por duplicação da taxa; k isotérmico de Westerhout; densidades ISO 1133; ceras POLYWAX |
| L3 sistema | CFD × 0-D com o mesmo h (T ± 3 K, vazão ± 10 %); volatilização por massa retida (Murata 2002); faixas de produtos |

Na malha de 48 células no diâmetro, o Kp laminar da fita dá ~309 (32 células: 326 — converge para o alvo
com o refinamento) e o balanço de torque fecha em 0,1 %.

Rodada de referência no preset `teste` (40 células, CPU, carga F3, parede a 480 °C): ~190 kg/h, fundido a
~410 °C, ~65 kW pela camisa, balanços de massa e energia fechando em ~1 %, 23 de 24 verificações no alvo. A que
fica fora é o coeficiente interno: ~375 W/m²K contra ~280 de Nagata (avaliado com as propriedades do próprio
CFD), +35 %. É o viés conhecido da lei de parede na malha grossa — o líquido junto à parede gira um pouco mais
que o real, porque o balanço de torque ainda tem um resíduo — e ele cai com o refinamento (num caso de teste,
h passou de 380 para 364 W/m²K de 32 para 48 células). Os presets de GPU usam 96 e 128 células.

## Conteúdo

| Caminho | O que é |
|---|---|
| `pirolise_reator_colab.ipynb` | Notebook do Colab, autocontido (o pacote é gravado por células `%%writefile`) |
| `pyrokit/` | Pacote: geometria, escoamento, turbulência, escalares, reologia, cinética, química, reator, validação, figuras, renderização 3D e vídeo |
| `video_roteiro.json` | Textos do vídeo (editáveis), com campos `{...}` preenchidos pela rodada |
| `docs/design_brief_en.md`, `docs/parameters.json` | Síntese da pesquisa: hipóteses, equações, parâmetros e fontes |
| `tests/` | Testes dos solvers e das identidades (`pytest -q`) |
| `build_notebook.py` | Regenera o notebook (e `scripts/rodar_local.py`, as mesmas células em sequência) |

## Uso

No Colab: abra o notebook, escolha *Ambiente de execução → GPU T4* e execute tudo. Presets: `teste`
(40 células no diâmetro, para CPU), `gpu` (96) e `gpu_fino` (128). Na célula de parâmetros: carga, temperatura
da parede, rotação, agitador, autor e LinkedIn (aparecem no vídeo). Saídas em `saida/`: figuras, imagens 3D,
`pirolise_reator.mp4` (~1 min), `pirolise_reator_curto.mp4` (~25 s), `capa.png` e o texto sugerido para o post.

## Limitações

Superfície livre plana e vapor que sai onde é gerado (sem bolhas nem espuma); seletividade de gás calibrada
para tanque agitado; sem craqueamento secundário na fase vapor; fechamento em três classes no lugar do
balanço populacional completo; malha cartesiana com fronteira imersa (o erro de parede cai com o
refinamento — use `gpu_fino` para números finais).
