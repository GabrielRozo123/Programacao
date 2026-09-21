# 01 — Contexto e as duas propostas

## Cliente e partes
- **Cliente:** Nexus Soluções em Engenharia LTDA — CNPJ 43.814.863/0001-05
- **Contato:** Douglas Costa · engenharia@nexus-engenharia.com
- **Responsável comercial CAEXPERTS:** Ricardo Barbosa de Barros
- **Equipe técnica prevista:** Marcus (senior) + Gabriel (CFD)

## O pedido
E-mail de 21/09/2026: a Nexus enviou os dados de processo do reator anóxico e pediu cotação
para modelagem CFD do misturador hiperbólico, explicitamente em **duas alternativas**:

> *"uma com design e otimização por vocês; e outra com design por nossa conta e modelagem com
> sugestões de melhorias por vocês."*

Ou seja, o cliente já chegou com a estrutura comercial definida. As propostas A e B respondem
exatamente a isso.

## As duas opções

| | **Opção A — Design e otimização** | **Opção B — Modelagem do design Nexus** |
|---|---|---|
| Quem projeta o misturador | **CAEXPERTS** | **Nexus** |
| Prazo | **25 dias úteis** | **17 dias úteis** |
| Etapa 1 | Pré-dimensionamento por correlações + geometria paramétrica + malha + física | Tratamento do CAD recebido + malha + física |
| Etapa 2 | Caso base na condição crítica | Avaliação do design Nexus (vazões mín. e máx.) |
| Etapa 3 | **DOE/otimização** (Ø, altura, rotação) + defletores | Diagnóstico + **até 3 variantes** de melhoria |
| Etapa 4 | Verificação RBM + DTR + relatório + reunião | Relatório comparativo + reunião |
| Entregáveis | Relatório .ppt + **CAD .step do design otimizado** | Relatório .ppt (sem CAD) |
| Horas Gabriel | 102 h | 76 h |
| Horas Marcus | 18 h | 11 h |

### O que distingue tecnicamente
A diferença não é só de escopo comercial — é de **método**:

- A **Opção A** tem geometria **paramétrica** e exploração automatizada do espaço de projeto
  (Design Manager / HEEDS). Produz uma janela de viabilidade, não um ponto.
- A **Opção B** parte de um CAD fixo e testa **até 3 variantes** definidas por julgamento.
  Responde "este design atende?" e "o que dá para melhorar?", mas não mapeia o espaço.

Para os critérios deste projeto — onde a suspeita é que a janela viável seja estreita
(ver `03_metodo_cfd_e_analise_previa.md`, §1) — a Opção A é a que de fato responde à pergunta
de projeto. A Opção B responde a uma pergunta de verificação.

## Status comercial
- **21/09/2026** — Propostas A e B montadas pelo Gabriel, enviadas ao **Marcus para revisão**.
- Valores e cronograma detalhado ficam nas planilhas (**não versionadas** — ver nota no `README.md`).

## Fora de escopo (ambas as opções)
Dimensionamento mecânico/estrutural (eixo, mancais, redutor, suportação), seleção de motor,
detalhamento para fabricação e simulação de outras unidades do processo.
A Opção B exclui adicionalmente a otimização paramétrica automatizada e o redesenho do misturador.
