# Proposta CAEXPERTS — Permutador e Fracionadora de Coque (Petrobras)

> Registro de **fatos técnicos** da proposta (17/07/2026, válida 30 dias). **Não** inclui dados
> cadastrais/bancários nem valores comerciais (ficam só no `.docx` mestre com o Marcus/Ricardo).
> Interlocutor: **Rui** (Petrobras). Contato comercial CAEXPERTS: Ricardo Barros.

## Motivação
O sistema de resfriamento e descarga do fundo da torre fracionadora de coque apresenta:
1. **Empenamento (flambagem) dos tubos do resfriador** — deformações permanentes ligadas à combinação de
   carregamentos térmicos, mecânicos e hidráulicos; influência de demisters, níveis operacionais e sobrepressão.
2. **Obstrução do fluxo de finos de coque** — acúmulo de material granular e entupimentos na descarga.

Abordagem: **CFD + FEA** (resfriador) e **DEM** (finos) para achar a causa raiz e avaliar melhorias virtualmente.

## Escopo

### 4.1 — Resfriador: CFD + FEA (5 etapas descritas no texto)
1. **Início** — recebimento de dados, premissas, adequação do CAD, kick-off.
2. **CFD da condição atual** — malha, BCs, propriedades; cenários (nível, sobrepressão, demisters) →
   campos de velocidade/pressão/temperatura (carregamentos).
3. **Avaliação estrutural FEA** — tensões, deformações, fadiga; origem do empenamento (flambagem).
4. **Melhorias** — alternativas estruturais/operacionais (incl. remover 1 ou os 2 demisters), validadas em FEA + CFD.
5. **Finalização** — relatório técnico consolidado + recomendações.

### 4.2 — Finos: DEM (5 etapas)
1. **Início** — dados, geometria, propriedades das partículas, **calibração DEM** (dado Petrobras ou literatura), kick-off.
2. **Condição atual** — fluxo dos finos; zonas mortas, acúmulo, mecanismos de obstrução.
3. **Alternativas de melhoria** — geometria, inclinação, revestimentos de menor atrito, aeração.
4. **Avaliação comparativa** — novas simulações DEM comparando configurações.
5. **Consolidação** — relatório + CAD da configuração recomendada.

## Entregáveis
- **Relatório CFD+FEA do Resfriador** (metodologia, causa do empenamento, melhorias validadas) + **CAD** da config recomendada.
- **Relatório DEM dos Finos** (calibração, condição atual, comparação de alternativas) + **CAD básico** da config recomendada.

## Cronograma
| Escopo | Duração | Etapas (dias) |
|---|---|---|
| Resfriador (CFD+FEA) | **63 dias** | 7 · 14 · 14 · 14 · 7 · 7  → **6 etapas** |
| Finos (DEM) | **56 dias** | 7 · 7 · 14 · 21 · 7  → **5 etapas** |

Início oficial no dia subsequente ao recebimento dos dados. Reuniões = técnicas (não são marcos de aprovação).

## Fora de escopo (resumo)
Levantamentos/inspeções em campo · ensaios experimentais · instrumentação/medição · projetos executivos e
desenhos de fabricação · fabricação/montagem/comissionamento · análises não previstas · ART/laudos legais.

## ⚠️ Revisão (pontos passados ao Marcus em 17/07)
| # | Ponto | Onde | Ação |
|---|---|---|---|
| 1 | **Escopo 4.1 tem 5 etapas, cronograma do Resfriador tem 6** (63 dias) — falta descrever a Etapa 6 | Escopo 4.1 × Cronograma 6.1 | **Substantivo** — reconciliar (provável: falta 1 etapa no texto, pois 63 dias já assumem 6) |
| 2 | Numeração **"6.1" duplicada** (a de Finos deveria ser "6.2") | Cronograma | Corrigir |
| 3 | Destinatário **"Para:"** não identifica o Rui/Petrobras (aparece o contato da própria CAEXPERTS) | Cabeçalho | Preencher o destinatário |
| 4 | Signatário inconsistente: **"Ricardo Barbosa De Barros - CEO"** (topo) × **"Ricardo Barros - Diretor"** (assinatura) | Cabeçalho × assinatura | Padronizar nome/cargo |
| 5 | Falta espaço: `"077Agência"` | Dados bancários | Cosmético |

**Conferências que bateram:** somas dos dias (63 e 56) ✓ · total comercial = soma dos dois escopos ✓ · data da validade ✓.
Conteúdo técnico (motivação, objetivos, escopo, premissas, fora de escopo, ganhos) **coerente e bem redigido**.
