# Revisão de Literatura — Flotação de Xarope por Ar Disperso (Venturi)

> Base técnica para o projeto Sugar (clarificação de xarope por flotação com ejetor
> venturi). Confirma o processo descrito no kick-off. Atualizado: 2026-07-01.

## 1. Processo: Fosfatação-Flotação (sugar refining)
- **Fosfatação:** adiciona-se **ácido fosfórico + cal (lime)** ao xarope → forma **floco de
  fosfato de cálcio** que adsorve impurezas (cor, coloides, turbidez).
- **Flotação:** injeta-se **ar** (micro-bolhas) → bolhas aderem aos flocos → flotam para a
  superfície → skim → xarope clarificado.
- Confirmado na literatura e em patentes (US 8,486,473 / US 9,163,293 — melhoria da
  clarificação por fosfatação de licores/xaropes).
- Estudo Sugar Tech (2023): micro-nano bolhas em 2 estágios purificam xarope de açúcar
  bruto → **descoloração 55,8%, remoção de turbidez 83,5%** (com MgO + ácido fosfórico).

## 2. Ar Disperso (DAF disperso) vs Ar Dissolvido
- **Ar dissolvido (DAF clássico):** pressuriza a água/licor, satura com ar, despressuriza →
  micro-bolhas. Requer energia de pressurização.
- **Ar disperso (nosso caso):** **gerador venturi/eductor** dispersa o ar diretamente —
  **NÃO precisa pressurizar** o fluido todo. Vantagem clara (economia).
- Nosso ejetor = gerador venturi de ar disperso.

## 3. Geração de micro-bolhas por VENTURI (mecanismo)
- Líquido motriz acelera na **garganta** (área ↓ → velocidade ↑ → pressão estática ↓,
  Bernoulli).
- Ar é **sugado/injetado** por perfurações na zona de baixa pressão e **arrastado** como bolhas.
- Na **expansão (difusor)**, a energia cinética cai e a pressão sobe → a bolha é **fragmentada**
  (reduz a ~1/20 do volume) → **bolhas < 300 µm** (geradores típicos: 30–300 µm).
- Tamanho da bolha depende de: velocidade superficial do gás, vazão da bomba de recirculação,
  geometria do venturi.

## 4. CFD de geradores venturi (precedentes → valida nossa abordagem)
- CFD (ANSYS Fluent / Star-CCM+) usado para projetar e otimizar venturis de bolhas.
- Modelos: multifásico **Euler-Euler ou VOF + population balance** (distribuição de tamanho
  de bolha), turbulência k-ε ou LES.
- Estuda-se: **diâmetro de bolha, gas holdup, fluxo de área superficial de bolha** — que
  governam a eficiência de flotação (colisão-adesão-arraste dos flocos).
- Há trabalhos de **otimização geométrica** do venturi por CFD + experimento.
- Existe até estudo específico de **venturi de duplo bocal** para aeração.

## 5. O DESAFIO do nosso caso: meio VISCOSO (65 poise)
- A maioria da literatura é água (μ~1 cP). Nosso xarope: **65 poise = 6,5 Pa·s (~6500× água)**.
- Subida de bolha (Stokes) no xarope: 100 µm → **~4 mm/HORA** (vs 5,4 mm/s na água).
- Implicações:
  - Fragmentação da bolha no venturi é mais difícil (alta viscosidade resiste ao cisalhamento).
  - Bolha quase não sobe → flotação depende do agregado floco-bolha e da agitação.
  - **Temperatura (75°C)** reduz μ → viabiliza o processo.
- É aqui que o CFD agrega mais valor: prever tamanho de bolha, holdup e mistura **no meio
  viscoso real**, onde correlações de água falham.

## 6. Implicações para o CFD (nosso escopo)
1. **Venturi/ejetor:** multifásico gás-líquido (VOF ou Euler + population balance) com
   **viscosidade real (65 poise)** → prever tamanho de micro-bolha gerado.
2. **Tanque aerador:** distribuição de bolhas, gas holdup, mistura, zonas mortas; efeito do
   impelidor (hydrofoil duplo) e da geometria (headspace, cone).
3. **Otimização:** bocal/venturi, tipo de impelidor, para maximizar bolhas finas e mistura
   no meio viscoso.

## Fontes
- Micro-nano bubble two-stage flotation of raw sugar syrup (Sugar Tech 2023):
  https://link.springer.com/article/10.1007/s12355-023-01357-x
- Dispersed air flotation using venturi microbubble generator (ScienceDirect):
  https://www.sciencedirect.com/science/article/abs/pii/S0961953419303289
- Fosfatação — patentes US 8,486,473 e US 9,163,293
- CFD of sparger-type venturi for two-phase flotation (ResearchGate):
  https://www.researchgate.net/publication/328052756
- Geometrical optimization of venturi microbubble generator (CFD + exp):
  https://www.academia.edu/53404404
- Parametric analysis of venturi microbubble generator & fragmentation (ScienceDirect):
  https://www.sciencedirect.com/science/article/pii/S1944398625001328
