# Projeto LD Celulose — Dispersão Atmosférica de O₃

Estudo CFD de dispersão de ozônio a partir do laboratório/prédio de geração de O₃,
para **delimitação de área de isolamento** e **posicionamento de sensores**.
Cliente **LD Celulose** (via CAEXPERTS).

> **Status (2026-09-28):** reunião de abertura realizada. Cronograma de 45 dias acordado.
> **Lote 1 recebido (29/09):** manuais dos 4 ventiladores do prédio de O₃ + NR-15 Anexo 11.
> Ver `04_dados_recebidos.md`. Vazão de fonte do off-gás e das PSVs ainda em aberto.

## Índice
| Doc | Conteúdo |
|---|---|
| [`01_escopo_e_criterios.md`](01_escopo_e_criterios.md) | O problema, os limiares de concentração e o cronograma |
| [`02_metodo_e_analise_previa.md`](02_metodo_e_analise_previa.md) | Escolhas de modelagem + **a régua analítica feita antes de simular** |
| [`03_pendencias_e_perguntas.md`](03_pendencias_e_perguntas.md) | O que falta do cliente + log datado de respostas |
| [`04_dados_recebidos.md`](04_dados_recebidos.md) | **Dados recebidos**, o que foi extraído deles e o que ainda falta |

## Resumo em uma frase
Mapear até onde e em que concentração o O₃ liberado pelo prédio de geração se dispersa pela
planta sob as condições de vento reais do sítio, para definir **raio de isolamento** e
**onde instalar os sensores**.

## ⭐ Os dois achados da análise prévia

**1. O O₃ é escalar passivo.** A 3 ppm a diferença de densidade para o ar é 2 × 10⁻⁶ — a nuvem
não tem flutuabilidade própria. Isso torna o transporte **linear na vazão da fonte**, e
colapsa a matriz de cenários: uma rodada por condição meteorológica serve para **todos** os
limiares e **todas** as vazões, por escala.

**2. A condição que governa não é vento forte — é vento fraco com atmosfera estável.** A conta
de pluma gaussiana dá um fator de ~14 entre a classe D diurna e a classe F noturna. Se a
estabilidade não entrar como eixo da matriz de cenários, o estudo subestima em uma ordem de
grandeza justamente o caso que define o isolamento.

Detalhes em `02_metodo_e_analise_previa.md`.

## ⚠️⚠️ Nota sobre este repositório — LER ANTES DE ACRESCENTAR MATERIAL

**O repositório é PÚBLICO.**

Este projeto é diferente dos outros nesse aspecto. Ele combina, sobre uma planta industrial
identificada:
- o **layout 3D** da planta
- os **pontos de liberação** de um gás tóxico
- as **concentrações que disparam isolamento de área**
- onde ficam **as pessoas**

Essa combinação não deve viver em repositório público. **Aqui ficam apenas o método, as
decisões de modelagem e as perguntas ao cliente.** Layout, coordenadas de emissão, vazões de
fonte, modelo 3D e dados meteorológicos brutos **não entram** — ficam no compartilhamento
interno da CAExperts.

> **Ação pendente:** decidir com o Marcus se este projeto deve migrar para repositório privado
> antes da Etapa 1. A mesma pergunta já estava aberta para a Nexus, mas aqui ela é mais séria.

## Como este repositório é mantido
Padrão dos outros projetos: cada dado novo do cliente entra em `03_pendencias_e_perguntas.md`
com data, e é propagado para o doc temático. Suposições ficam marcadas como **[SUPOSTO]**
até confirmação.
