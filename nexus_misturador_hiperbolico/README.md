# Projeto Nexus — Misturador Hiperbólico (reator anóxico)

Estudo CFD de misturador hiperbólico para reator anóxico de lodos ativados.
Cliente **Nexus Soluções em Engenharia** (via CAEXPERTS). Contato: **Douglas Costa**.

> **Status (2026-09-21):** propostas A e B montadas pelo Gabriel, **em revisão com o Marcus**.
> Dados de processo recebidos e consolidados. Nenhuma simulação iniciada.
> Ver `04_pendencias_e_perguntas.md` para o que falta do cliente.

## Índice
| Doc | Conteúdo |
|---|---|
| [`01_contexto_e_propostas.md`](01_contexto_e_propostas.md) | Cliente, o pedido, e as duas opções comerciais (A e B) |
| [`02_dados_e_criterios.md`](02_dados_e_criterios.md) | Dados de processo do reator, do misturador e do lodo + os 4 critérios de projeto |
| [`03_metodo_cfd_e_analise_previa.md`](03_metodo_cfd_e_analise_previa.md) | Escolhas de modelagem + **análise de envelope feita antes de simular** |
| [`04_pendencias_e_perguntas.md`](04_pendencias_e_perguntas.md) | Perguntas ao cliente + log datado de respostas |

## Resumo em uma frase
Dimensionar (Opção A) ou avaliar (Opção B) um misturador hiperbólico em um reator
cilíndrico de **48,2 m³** (Ø 3,2 m × 6,0 m útil), de modo a manter **≥ 0,3 m/s junto ao fundo**
com **potência específica de 1,3 a 4,5 W/m³**, sem vórtice e aproximando um reator de mistura completa.

## O achado da análise prévia
O orçamento de potência inteiro é de **217 W** (4,5 W/m³ × 48,2 m³). O conflito real do projeto
não é entre mistura e tempo de residência — é entre o **critério 2 (velocidade no fundo)** e o
**critério 3 (teto de potência)**. Ver `03_metodo_cfd_e_analise_previa.md`.

## ⚠️ Nota sobre este repositório
**O repositório é público.** As planilhas de proposta (`Opção A` e `Opção B`) **não foram
versionadas aqui** — elas contêm CNPJ, endereços, a tabela de HH interna da CAEXPERTS e os
valores por consultor. Os dados técnicos de processo estão nos `.md`, mas convém decidir se
este projeto deve viver em repositório público antes de acrescentar mais material do cliente.

## Como este repositório é mantido
Padrão dos outros projetos: cada dado novo do cliente entra em `04_pendencias_e_perguntas.md`
com data, e é propagado para o doc temático correspondente. Suposições ficam marcadas
como **[SUPOSTO]** até confirmação.
